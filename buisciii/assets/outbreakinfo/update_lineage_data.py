import requests
import os
import pandas as pd

# URL Configuration
TAGS_URL = "https://api.github.com/repos/cov-lineages/pango-designation/tags"
CSV_URL = "https://raw.githubusercontent.com/cov-lineages/pango-designation/master/lineages.csv"
BASE_DIR = "lineages_data"


def get_latest_tag():
    """Fetches the latest published tag from the repository."""
    response = requests.get(TAGS_URL)
    if response.status_code == 200:
        tags = response.json()
        if tags:
            return tags[0]["name"]  # Latest available tag
    raise Exception("Failed to fetch repository tags.")


def clean_tag(tag):
    """Removes the leading 'v' if present to avoid duplicate names."""
    return tag.lstrip("v")


def get_local_versions():
    """Lists locally stored versions in subdirectories."""
    if not os.path.exists(BASE_DIR):
        return []
    return [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]


def download_new_version(tag):
    """Downloads the CSV file and stores it in a versioned subdirectory."""
    clean_version = clean_tag(tag)  # Clean the version to avoid "vv"
    version_dir = os.path.join(BASE_DIR, f"v{clean_version}")  # Version folder
    csv_path = os.path.join(version_dir, f"lineages_v{clean_version}.csv")
    excel_path = os.path.join(version_dir, f"Lineages_Mutations_v{clean_version}.xlsx")

    if clean_version in [clean_tag(v) for v in get_local_versions()]:
        print(f"⚠️ The latest version is already stored in {csv_path}.")
        update_latest_symlinks(csv_path, excel_path)
        return

    print(f"📥 Downloading new version to {csv_path}...")

    os.makedirs(version_dir, exist_ok=True)  # Create directory if it doesn't exist

    response = requests.get(CSV_URL)

    if response.status_code == 200:
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(f"# Version: {tag}\n")  # Add version as the first line
            f.write(response.text)  # Save CSV content
        print(f"✅ File saved at {csv_path}.")

        # 📌 🔥 Ensure Excel file is correctly generated 🔥 📌
        if os.path.exists(csv_path):
            print(f"📊 Generating Excel file: {excel_path} ...")
            generate_excel(csv_path, excel_path, tag)
        else:
            print(f"❌ ERROR: CSV file not found at {csv_path}.")

        update_latest_symlinks(csv_path, excel_path)
    else:
        print("❌ Error downloading the file.")


def generate_excel(csv_path, excel_path, version):
    """Generates an Excel file with unique lineages from the CSV and includes the version."""
    try:
        print(f"📂 Reading CSV: {csv_path}")

        df = pd.read_csv(csv_path, comment="#")  # Ignore version line
        print("📌 Detected columns in CSV:", df.columns)

        if "lineage" not in df.columns:
            print(
                "❌ ERROR: The 'lineage' column is missing in the CSV. Aborting Excel generation."
            )
            return

        unique_lineages = df["lineage"].dropna().unique()
        unique_df = pd.DataFrame(unique_lineages, columns=["Unique lineages"])

        # Create an Excel workbook with one sheet for lineages and another for the version
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            unique_df.to_excel(writer, sheet_name="Lineages", index=False)

            # Add the version in a second sheet
            wb = writer.book
            ws_version = wb.create_sheet(title="Metadata")
            ws_version.append(["Version", version])

            print(f"✅ Excel file generated at {excel_path} with version included.")

    except Exception as e:
        print(f"❌ ERROR generating Excel file: {e}")


def update_latest_symlinks(latest_csv_path, latest_excel_path):
    """Updates symbolic links 'latest.csv' and 'latest.xlsx'."""
    latest_csv_symlink = os.path.join(BASE_DIR, "latest.csv")
    latest_excel_symlink = os.path.join(BASE_DIR, "latest.xlsx")

    for symlink, target in [
        (latest_csv_symlink, latest_csv_path),
        (latest_excel_symlink, latest_excel_path),
    ]:
        if os.path.exists(symlink) or os.path.islink(symlink):
            os.unlink(symlink)  # Remove old symbolic link
        os.symlink(os.path.abspath(target), symlink)  # Create new symbolic link
        print(f"🔗 Symbolic link '{symlink}' now points to {target}")


if __name__ == "__main__":
    try:
        latest_tag = get_latest_tag()
        download_new_version(latest_tag)
    except Exception as e:
        print(f"❌ GENERAL ERROR: {e}")
