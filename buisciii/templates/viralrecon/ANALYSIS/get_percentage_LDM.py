import os
import re
import pandas as pd
import argparse
from datetime import datetime
import glob
from collections import defaultdict

# Get the current date in YYYYMMDD format
current_date = datetime.now().strftime("%Y%m%d")

# Define the input and output directory patterns and the lineage CSV file pattern
input_directory_pattern = (
    "./*_viralrecon_mapping/variants/ivar/consensus/bcftools/nextclade"
)
output_directory_pattern = "./*_viralrecon_mapping"
lineage_csv_outbreak_pattern = "/data/ucct/bi/references/outbreakinfo/filtrado_20250123_mutaciones_definitorias_linaje.csv"

# Find directories and files matching the given patterns
input_directories = glob.glob(input_directory_pattern)
lineage_csv_outbreak_files = glob.glob(lineage_csv_outbreak_pattern)
input_directory = input_directories[0]
lineage_csv_outbreak = lineage_csv_outbreak_files[0]

# Command line arguments
parser = argparse.ArgumentParser(
    description="Script to process defining lineage mutations."
)
parser.add_argument(
    "-other_lineages",
    type=int,
    default=0,
    help="If set to 1, returns other lineages even when exists == 1 (default is 0)",
)
args = parser.parse_args()
other_lineages_flag = args.other_lineages


def create_output_directory(base_directory_pattern):
    """
    Create an output directory (named 'LDM') inside the first directory that matches the given pattern.
    Raises a FileNotFoundError if no matching directory is found.
    """
    base_directories = glob.glob(base_directory_pattern)
    if not base_directories:
        raise FileNotFoundError(
            f"No directories matching the pattern were found: {base_directory_pattern}"
        )
    base_dir = base_directories[0]
    ldm_dir = os.path.join(base_dir, "LDM")
    os.makedirs(ldm_dir, exist_ok=True)
    return ldm_dir


def normalize_string(s):
    """
    Normalize the input string by stripping spaces, converting to lowercase.
    If the input is NaN, return an empty string.
    """
    if pd.isna(s):
        return ""
    return str(s).strip().lower()


def group_deletions(mutation_list):
    """
    Group deletions by gene and format them correctly.

    For each mutation in the list, it searches for the pattern 'GENE:residueX-'
    (e.g., "gene:AA123-"). Then, it groups contiguous deletion positions and
    formats them as 'GENE:delstart/end'.
    """
    deletion_groups = defaultdict(list)

    # Process each mutation in the list
    for mutation in mutation_list:
        # Look for the pattern 'GENE:residueX-' using regex
        match = re.match(r"([a-zA-Z0-9]+):([a-zA-Z]+)(\d+)-", mutation)
        if match:
            gene = match.group(1)
            position = int(match.group(3))
            deletion_groups[gene].append(position)

    formatted_deletions = []
    # Group positions by gene
    for gene, positions in deletion_groups.items():
        positions.sort()
        ranges = []
        start = end = positions[0]

        # Group contiguous positions into ranges
        for pos in positions[1:]:
            if pos == end + 1:
                end = pos
            else:
                ranges.append((start, end))
                start = end = pos
        ranges.append((start, end))

        # Format the deletions
        for start, end in ranges:
            if start == end:
                formatted_deletions.append(f"{gene}:del{start}/{start}")
            else:
                formatted_deletions.append(f"{gene}:del{start}/{end}")

    return formatted_deletions


def process_sample(input_file, lineage_csv_outbreak, output_tsv, sample_name):
    """
    Process a single sample file:
      - Reads the CSV file and extracts relevant mutation columns.
      - Normalizes the lineage and mutations.
      - Processes substitutions, insertions, and deletions (using group_deletions).
      - Reads the CSV with defining lineage mutations.
      - Marks which mutations are present in the sample.
      - Optionally, includes other lineages that share the same mutation.
      - Saves the resulting DataFrame as a TSV.
    """
    # Read the sample CSV file with ';' as delimiter
    df = pd.read_csv(input_file, sep=";")
    # Keep only relevant columns and rename 'Nextclade_pango' to 'lineage'
    df = df[
        ["Nextclade_pango", "aaSubstitutions", "aaDeletions", "aaInsertions"]
    ].rename(columns={"Nextclade_pango": "lineage"})

    # Normalize the lineage string from the first row
    sample_lineage = normalize_string(df.iloc[0]["lineage"])
    detected_mutations = []

    # Add substitutions and insertions
    for mutation_type in ["aaSubstitutions", "aaInsertions"]:
        if pd.notna(df.iloc[0][mutation_type]):
            mutations = df.iloc[0][mutation_type].split(",")
            detected_mutations.extend(normalize_string(m) for m in mutations)

    # Process deletions
    if pd.notna(df.iloc[0]["aaDeletions"]):
        deletions = df.iloc[0]["aaDeletions"].split(",")
        processed_deletions = group_deletions(deletions)
        print(processed_deletions)  # Debug: print the processed deletions
        detected_mutations.extend(normalize_string(d) for d in processed_deletions)

    # Read the CSV file containing defining lineage mutations
    lineage_df = pd.read_csv(lineage_csv_outbreak, sep=",")
    lineage_df = lineage_df.iloc[:, [3, 0, 9]]
    lineage_df.columns = ["lineage", "mutation", "type"]
    # Filter rows matching the sample's lineage (after normalization)
    lineage_df = lineage_df[
        lineage_df["lineage"].apply(normalize_string) == sample_lineage
    ]

    if lineage_df.empty:
        print(
            f"No defining mutations found for lineage {sample_lineage} in {sample_name}"
        )
        return None

    lineage_df["mutation"] = lineage_df["mutation"].apply(normalize_string)
    # Mark mutation as present (1) if it is in the detected mutations list, else 0
    lineage_df["exists"] = lineage_df["mutation"].apply(
        lambda m: 1 if m in detected_mutations else 0
    )

    # Read the full lineage CSV again to later find other lineages for each mutation
    lineage_all_df = pd.read_csv(lineage_csv_outbreak, sep=",")
    lineage_all_df = lineage_all_df.iloc[:, [3, 0, 9]]
    lineage_all_df.columns = ["lineage", "mutation", "type"]
    lineage_all_df["lineage"] = lineage_all_df["lineage"].apply(normalize_string)
    lineage_all_df["mutation"] = lineage_all_df["mutation"].apply(normalize_string)

    def get_other_lineages(mutation, sample_lineage):
        """
        For a given mutation and sample lineage, returns a comma-separated list
        of other lineages where the mutation is defining.
        """
        other = lineage_all_df[
            (lineage_all_df["mutation"] == mutation)
            & (lineage_all_df["lineage"] != sample_lineage)
        ]
        if other.empty:
            return ""
        else:
            return ",".join(sorted(other["lineage"].unique()))

    # Depending on the flag, either include all other lineages or only for mutations that were not detected
    if other_lineages_flag == 1:
        lineage_df["other_lineages"] = lineage_df.apply(
            lambda row: get_other_lineages(row["mutation"], sample_lineage), axis=1
        )
    else:
        lineage_df["other_lineages"] = lineage_df.apply(
            lambda row: (
                ""
                if row["exists"] == 1
                else get_other_lineages(row["mutation"], sample_lineage)
            ),
            axis=1,
        )

    # Save the processed mutations information as a TSV file
    lineage_df.to_csv(output_tsv, sep="\t", index=False)
    return lineage_df


def process_directory(input_directory, lineage_csv_outbreak, output_directory):
    """
    Process all CSV files in the given input directory.
      - For each CSV, process the sample using process_sample().
      - Compute a summary with the percentage of detected defining mutations.
      - Merge the summary with a pre-existing TSV file ('s_gene_combined_metrics.tsv') and save the result.
    """
    csv_files = [f for f in os.listdir(input_directory) if f.endswith(".csv")]
    summary_results = []

    for csv_file in csv_files:
        sample_name = os.path.splitext(csv_file)[0]
        input_file = os.path.join(input_directory, csv_file)
        output_tsv = os.path.join(
            output_directory, f"{sample_name}_verified_mutations.tsv"
        )

        lineage_df = process_sample(
            input_file, lineage_csv_outbreak, output_tsv, sample_name
        )

        if lineage_df is not None:
            detected_percentage = (lineage_df["exists"].sum() / len(lineage_df)) * 100
            summary_results.append(
                {"sample": sample_name, "% LDMutations": detected_percentage}
            )

    # Read the combined TSV file to merge with summary results
    try:
        tsv_df = pd.read_csv("./s_gene_combined_metrics.tsv", sep="\t")
    except FileNotFoundError:
        raise FileNotFoundError(
            "TSV file 's_gene_combined_metrics.tsv' not found in the current directory."
        )

    summary_df = pd.DataFrame(summary_results)
    summary_tsv = os.path.join(output_directory, f"{current_date}_mutation_summary.tsv")
    summary_df.to_csv(summary_tsv, sep="\t", index=False)
    print(f"Summary file saved: {summary_tsv}")

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


# Create the output directory and process the input directory
output_directory = create_output_directory(output_directory_pattern)
process_directory(input_directory, lineage_csv_outbreak, output_directory)
