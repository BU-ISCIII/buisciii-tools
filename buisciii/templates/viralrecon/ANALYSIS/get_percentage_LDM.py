import os
import re
import pandas as pd
import argparse
from datetime import datetime
import glob
from collections import defaultdict

# Get the current date in YYYYMMDD format
current_date = datetime.now().strftime("%Y%m%d")

# Define the input/output directory patterns and the lineage CSV file path
input_directory_pattern = (
    "./*_viralrecon_mapping/variants/ivar/consensus/bcftools/nextclade"
)
output_directory_pattern = "./*_viralrecon_mapping"
lineage_csv_outbreak_pattern = (
    "/data/ucct/bi/references/outbreakinfo/lineages_data/latest_mutations.csv"
)

# Locate directories and files matching the specified patterns
input_directories = glob.glob(input_directory_pattern)
lineage_csv_outbreak_files = glob.glob(lineage_csv_outbreak_pattern)
input_directory = input_directories[0]
lineage_csv_outbreak = lineage_csv_outbreak_files[0]

parser = argparse.ArgumentParser(
    description="Script to process defining lineage mutations."
)
parser.add_argument(
    "-other_lineages",
    type=int,
    choices=[0, 1],
    default=0,
    help="Include other lineages whether or not the mutation is in the sample. (1, 2)",
)
args = parser.parse_args()
other_lineages_flag = args.other_lineages


def create_output_directory(base_directory_pattern):
    base_directories = glob.glob(base_directory_pattern)
    if not base_directories:
        raise FileNotFoundError(
            f"No directories found matching the pattern: {base_directory_pattern}"
        )
    base_dir = base_directories[0]
    ldm_dir = os.path.join(base_dir, "LDM")
    os.makedirs(ldm_dir, exist_ok=True)
    return ldm_dir


def normalize_string(s):
    if pd.isna(s):
        return ""
    return str(s).strip().lower()


def classify_ldm(row):
    if row["in_lineage"] == "Yes" and row["in_sample"] == "Yes":
        return 1
    elif row["in_lineage"] == "Yes" and row["in_sample"] == "No":
        return 0
    elif row["in_lineage"] == "No" and row["in_sample"] == "Yes":
        return 2
    return None


def get_other_lineages(mutation, sample_lineage, lineage_all_df):
    other = lineage_all_df[
        (lineage_all_df["mutation"] == mutation)
        & (lineage_all_df["lineage"] != sample_lineage)
    ]
    return ",".join(sorted(other["lineage"].unique())) if not other.empty else ""


def group_deletions(mutation_list):
    deletion_groups = defaultdict(list)
    for mutation in mutation_list:
        match = re.match(r"([a-zA-Z0-9]+):([a-zA-Z]+)(\d+)-", mutation)
        if match:
            gene = match.group(1)
            position = int(match.group(3))
            deletion_groups[gene].append(position)

    formatted_deletions = []
    for gene, positions in deletion_groups.items():
        positions.sort()
        ranges = []
        start = end = positions[0]
        for pos in positions[1:]:
            if pos == end + 1:
                end = pos
            else:
                ranges.append((start, end))
                start = end = pos
        ranges.append((start, end))

        for start, end in ranges:
            if start == end:
                formatted_deletions.append(f"{gene}:del{start}/{start}")
            else:
                formatted_deletions.append(f"{gene}:del{start}/{end}")

    return formatted_deletions


def process_sample(input_file, lineage_csv_outbreak, output_tsv, sample_name):
    df = pd.read_csv(input_file, sep=";")
    df = df[
        ["Nextclade_pango", "aaSubstitutions", "aaDeletions", "aaInsertions"]
    ].rename(columns={"Nextclade_pango": "lineage"})
    sample_lineage = normalize_string(df.iloc[0]["lineage"])
    detected_mutations = set()

    for mutation_type in ["aaSubstitutions", "aaInsertions"]:
        if pd.notna(df.iloc[0][mutation_type]):
            mutations = map(normalize_string, df.iloc[0][mutation_type].split(","))
            detected_mutations.update(mutations)

    if pd.notna(df.iloc[0]["aaDeletions"]):
        deletions = group_deletions(df.iloc[0]["aaDeletions"].split(","))
        detected_mutations.update(map(normalize_string, deletions))

    ldm_df = pd.read_csv(lineage_csv_outbreak, sep=",", usecols=[0, 3, 9])
    ldm_df.columns = ["mutation", "lineage", "type"]
    ldm_df["lineage"] = ldm_df["lineage"].apply(normalize_string)
    ldm_df["mutation"] = ldm_df["mutation"].apply(normalize_string)
    ldm_mutations = set(ldm_df[ldm_df["lineage"] == sample_lineage]["mutation"])

    all_mutations = ldm_mutations.union(detected_mutations)

    output_df = pd.DataFrame({"mutations": list(all_mutations)})
    output_df["in_lineage"] = output_df["mutations"].apply(
        lambda m: "Yes" if m in ldm_mutations else "No"
    )
    output_df["in_sample"] = output_df["mutations"].apply(
        lambda m: "Yes" if m in detected_mutations else "No"
    )
    output_df["LDM"] = output_df.apply(classify_ldm, axis=1)
    output_df["in_other_lineage"] = output_df.apply(
        lambda row: (
            get_other_lineages(row["mutations"], sample_lineage, ldm_df)
            if row["LDM"] == 2 or (row["LDM"] == 1 and other_lineages_flag == 1)
            else ""
        ),
        axis=1,
    )
    output_df.insert(0, "lineage", sample_lineage)
    output_df.to_csv(output_tsv, sep="\t", index=False)
    return output_df


def process_directory(input_directory, lineage_csv_outbreak, output_directory):
    csv_files = [f for f in os.listdir(input_directory) if f.endswith(".csv")]
    summary_results = []

    for csv_file in csv_files:
        sample_name = str(os.path.splitext(csv_file)[0])
        input_file = os.path.join(input_directory, csv_file)
        output_tsv = os.path.join(
            output_directory, f"{sample_name}_verified_mutations.tsv"
        )

        lineage_df = process_sample(
            input_file, lineage_csv_outbreak, output_tsv, sample_name
        )
        if lineage_df is not None:
            has_ldm_info = (lineage_df["in_lineage"] == "Yes").any()
            if not has_ldm_info:
                detected_percentage = "Data Not Evaluable [NCIT:C186292]"
            else:
                valid_mutations = lineage_df[lineage_df["LDM"].isin([0, 1])]
                detected_percentage = (
                    (valid_mutations["LDM"].sum() / len(valid_mutations)) * 100
                    if len(valid_mutations) > 0
                    else 0.0
                )
            summary_results.append(
                {"sample": sample_name, "%LDMutations": detected_percentage}
            )

    summary_df = pd.DataFrame(summary_results)
    summary_tsv = os.path.join(output_directory, f"{current_date}_mutation_summary.tsv")
    summary_df.to_csv(summary_tsv, sep="\t", index=False)
    print(f"Summary file saved: {summary_tsv}")

    try:
        tsv_df = pd.read_csv(
            "./s_gene_combined_metrics.tsv", sep="\t", dtype={"sample": str}
        )
    except FileNotFoundError:
        raise FileNotFoundError(
            "TSV file 's_gene_combined_metrics.tsv' not found in the current directory."
        )

    # Ensure the 'sample' column is of type string in both DataFrames
    tsv_df["sample"] = tsv_df["sample"].astype(str)
    summary_df["sample"] = summary_df["sample"].astype(str)

    if "sample" not in tsv_df.columns:
        raise KeyError(
            f"The column 'sample' is not found in the TSV file. Available columns: {tsv_df.columns.tolist()}"
        )

    # Merge the summary results with the TSV DataFrame
    merged_df = tsv_df.merge(summary_df, on="sample", how="left")

    # Save the merged DataFrame to a new TSV file
    updated_tsv_path = os.path.join("./", f"quality_control_report_{current_date}.tsv")
    merged_df.to_csv(updated_tsv_path, sep="\t", index=False)
    print(f"Updated TSV file saved in: {updated_tsv_path}")


output_directory = create_output_directory(output_directory_pattern)
process_directory(input_directory, lineage_csv_outbreak, output_directory)
