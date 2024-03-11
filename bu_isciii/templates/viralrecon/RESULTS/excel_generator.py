import os
import argparse
import pandas as pd
from typing import List, Dict

# conda activate viralrecon_report
"""Standard usage: python excel_generator.py -r ./reference.tmp --merge_lineage_files"""
"""Single csv to excel usage: python excel_generator.py -s csv_file.csv"""
parser = argparse.ArgumentParser(
    description="Generate excel files from viralrecon results"
)
parser.add_argument(
    "-r",
    "--reference_file",
    type=str,
    help="File containing the references used in the analysis",
)
parser.add_argument(
    "-s",
    "--single_csv",
    type=str,
    default="",
    help="Transform a single csv file to excel format. Omit rest of processes",
)
parser.add_argument(
    "-l",
    "--merge_lineage_files",
    action="store_true",
    help="Merge pangolin and nextclade lineage tables",
)
args = parser.parse_args()


def concat_tables_and_write(csvs_in_folder: List[str], merged_csv_name: str):
    """Concatenate any tables that share the same header"""
    if len(csvs_in_folder) == 0:
        print(f"Could not find tables to merge over {merged_csv_name}")
        return
    with open(merged_csv_name, "wb") as merged_csv:
        with open(csvs_in_folder[0], "rb") as f:
            merged_csv.write(
                f.read()
            )  # This is the fastest way to concatenate csv files
        if len(csvs_in_folder) > 1:
            for file in csvs_in_folder[1:]:
                with open(file, "rb") as f:
                    next(f)  # this is used to skip the header
                    merged_csv.write(f.read())
    return merged_csv


def merge_lineage_tables(
    reference_folders: Dict[str, str], samples_ref_files: Dict[str, str]
):
    """Creates the tables for pangolin and nextclade"""
    for ref, folder in reference_folders.items():
        print("Merging results for either pangolin or nextclade in a single csv file")
        samples_for_ref = open(samples_ref_files[ref]).read().splitlines()
        if os.path.isdir(os.path.abspath(folder + "/pangolin")):
            pango_dir = os.path.join(folder, "pangolin")
            csvs_in_folder = [
                file.path
                for file in os.scandir(pango_dir)
                if os.path.basename(file).strip(".pangolin.csv") in samples_for_ref
            ]
            merged_csv_name = os.path.join(folder, str(ref + "_pangolin.csv"))
            concat_tables_and_write(
                csvs_in_folder=csvs_in_folder, merged_csv_name=merged_csv_name
            )
        else:
            print(f"No pangolin folder could be found for {ref}, omitting")

        if os.path.isdir(os.path.abspath(folder + "/nextclade")):
            nextcl_dir = os.path.join(folder, "nextclade")
            csvs_in_folder = [
                file.path
                for file in os.scandir(nextcl_dir)
                if os.path.basename(file).strip(".csv") in samples_for_ref
            ]
            merged_csv_name = os.path.join(folder, str(ref + "_nextclade.csv"))
            concat_tables_and_write(
                csvs_in_folder=csvs_in_folder, merged_csv_name=merged_csv_name
            )
        else:
            print(f"No nextclade folder could be found for {ref}, omitting")

    return


def excel_generator(csv_files: List[str]):
    for file in csv_files:
        if not os.path.exists(file):
            print(f"File {file} does not exist, omitting...")
            continue
        print(f"Generating excel file for {file}")
        output_name = os.path.splitext(os.path.basename(file))[0] + ".xlsx"
        # workbook = openpyxl.Workbook(output_name)
        if "nextclade" in str(file):
            table = pd.read_csv(file, sep=";", header=0)
        elif "illumina" in str(file):
            table = pd.read_csv(file, sep="\t", header=0)
            table["analysis_date"] = pd.to_datetime(
                table["analysis_date"].astype(str), format="%Y%m%d"
            )
        elif "assembly" in str(file) or ".tsv" in str(file) or ".tab" in str(file):
            table = pd.read_csv(file, sep="\t", header=0)
        else:
            try:
                table = pd.read_csv(file)
            except pd.errors.EmptyDataError:
                print("Could not parse table from ", str(file))
                continue
        table = table.drop(["index"], axis=1, errors="ignore")
        table.to_excel(output_name, index=False)
    return


def single_csv_to_excel(csv_file: str):
    try:
        excel_generator([csv_file])
    except FileNotFoundError as e:
        print(f"Could not find file {e}")


def main(args):
    if args.single_csv:
        # If single_csv is called, just convert target csv to excel and skip the rest
        print("Single file convertion selected. Skipping main process...")
        single_csv_to_excel(args.single_csv)
        exit(0)

    print(
        "Extracting references used for analysis and the samples associated with each reference\n"
    )
    with open(args.reference_file, "r") as file:
        references = [line.rstrip() for line in file]
        print(f"\nFound {len(references)} references: {str(references).strip('[]')}")

    reference_folders = {ref: str("excel_files_" + ref) for ref in references}
    samples_ref_files = {
        ref: str("ref_samples/samples_" + ref + ".tmp") for ref in references
    }

    if args.merge_lineage_files:
        # Merge pangolin and nextclade csv files separatedly and create excel files for them
        merge_lineage_tables(reference_folders, samples_ref_files)
        for reference, folder in reference_folders.items():
            print(f"Creating excel files for reference {reference}")
            csv_files = [
                file.path for file in os.scandir(folder) if file.path.endswith(".csv")
            ]
            excel_generator(csv_files)

    # Merge all the variant long tables into one and convert to excel format
    variants_tables = [
        table.path for table in os.scandir(".") if "variants_long_table" in table.path
    ]
    try:
        concat_tables_and_write(
            csvs_in_folder=variants_tables, merged_csv_name="variants_long_table.csv"
        )
    except FileNotFoundError as e:
        print(str(e))
        print("Merged variants_long_table.csv might be empty")

    # Create excel files for individual tables
    valid_extensions = [".csv", ".tsv", ".tab"]
    rest_of_csvs = [
        file.path
        for file in os.scandir(".")
        if any(file.path.endswith(ext) for ext in valid_extensions)
    ]
    link_csvs = [file for file in rest_of_csvs if os.path.islink(file)]
    broken_links = [file for file in link_csvs if not os.path.exists(os.readlink(file))]
    valid_csvs = [file for file in rest_of_csvs if file not in broken_links]
    excel_generator(valid_csvs)


if __name__ == "__main__":
    main(args)
