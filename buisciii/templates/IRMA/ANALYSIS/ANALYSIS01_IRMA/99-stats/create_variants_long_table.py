# =============================================================
# INTRODUCTION

# This script is conceived to create a table of all the reported variants for a set of flu samples.
# It takes into consideration the flu subtype and the segment of its genome when displaying the variants detected.
# =============================================================

# =============================================================
# EXAMPLE OF USE

# This python script has only one argument: the folder that contains the annotated variants, after running SnpEff and SnpSift.
# Example: python3 create_variants_long_table.py ../06-variant-calling/annotated_vcfs

# In the previous example, the folder being indicated has one folder per sample. Each sample folder contains, per flu segment, two files:
#   - an annotated .vcf file obtained after running SnpEff with its corresponding database.
#   - an .snpsift.txt file that contains the relevant information from the previously mentioned .vcf files.

# Therefore, in the folder being provided as argument, there have to be as many subfolders as samples being analysed as part of the service.
# Each subfolder has to contain, for each segment, both a .vcf file from SnpEff and a .txt file from SnpSift.
# =============================================================

# =============================================================
# OUTPUT

# The output of this script will be a .csv file called variants_long_table, which will report all the variants detected for each sample and each segment.
# =============================================================

import os
import numpy as np
import re
import glob
import pandas as pd
import argparse

# Read flu subtype info from samples_type_ref.txt
samples_type_file = os.path.abspath(os.path.join(".", "sample_type_ref.txt"))
sample_to_subtype = {}

with open(samples_type_file, "r") as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 2:
            sample, subtype = parts[0], parts[1]  # remove underscores if desired
            sample_to_subtype[sample] = subtype


# Function to process all .vcf files found in the provided folder as argument.
def parse_vcf(vcf_file, sample_to_subtype):
    records = []
    sample_name = re.sub(r"-(H\d+)-", "-", os.path.basename(os.path.dirname(vcf_file)))
    flu_subtype = sample_to_subtype.get(sample_name, "UNKNOWN")

    with open(vcf_file, "r") as f:
        for line in f:
            if line.startswith("#"):
                continue
            fields = line.strip().split("\t")
            chrom, pos, _, ref, alt, _, filter_, info, format_, sample_data = fields[
                :10
            ]

            # Extract DP from INFO field
            dp = next(
                (x.split("=")[1] for x in info.split(";") if x.startswith("DP=")), "0"
            )

            # Extract ALT_DP and AF from sample data
            sample_fields = sample_data.split(":")
            alt_dp = sample_fields[1] if len(sample_fields) > 1 else "0"
            try:
                ref_dp = int(float(dp)) - int(float(alt_dp))
            except ValueError:
                dp = 0
                alt_dp = 0
                ref_dp = 0
            af = sample_fields[-1] if sample_fields else "0"

            records.append(
                [
                    sample_name,
                    flu_subtype,
                    chrom,
                    pos,
                    ref,
                    alt,
                    filter_,
                    dp,
                    ref_dp,
                    alt_dp,
                    af,
                ]
            )

    return records


# Function to report the aminoacids from the HGVS_P column.
def three_letter_aa_to_one(hgvs_three):
    aa_dict = {
        "Ala": "A",
        "Arg": "R",
        "Asn": "N",
        "Asp": "D",
        "Cys": "C",
        "Gln": "Q",
        "Glu": "E",
        "Gly": "G",
        "His": "H",
        "Ile": "I",
        "Leu": "L",
        "Lys": "K",
        "Met": "M",
        "Phe": "F",
        "Pro": "P",
        "Pyl": "O",
        "Ser": "S",
        "Sec": "U",
        "Thr": "T",
        "Trp": "W",
        "Tyr": "Y",
        "Val": "V",
        "Asx": "B",
        "Glx": "Z",
        "Xaa": "X",
        "Xle": "J",
        "Ter": "*",
    }
    hgvs_one = hgvs_three
    for key in aa_dict:
        if key in hgvs_one:
            hgvs_one = hgvs_one.replace(str(key), str(aa_dict[key]))

    return hgvs_one


# Function to read info from the snpsift output file and return the revelant data into a table.
def snpsift_to_table(snpsift_file):
    table = pd.read_table(snpsift_file, sep="\t", header="infer")
    table = table.loc[:, ~table.columns.str.contains("^Unnamed")]
    old_colnames = list(table.columns)
    new_colnames = [x.replace("ANN[*].", "") for x in old_colnames]
    table.rename(columns=dict(zip(old_colnames, new_colnames)), inplace=True)
    table = table.loc[
        :, ["CHROM", "POS", "REF", "ALT", "GENE", "EFFECT", "HGVS_C", "HGVS_P"]
    ]

    for i in range(len(table)):
        for j in range(3, 8):
            if pd.isna(table.iloc[i, j]):
                table.iloc[i, j] = np.nan
            else:
                table.iloc[i, j] = str(table.iloc[i, j]).split(",")[0]

    # Amino acid substitution
    aa = []
    for index, item in table["HGVS_P"].items():
        hgvs_p = three_letter_aa_to_one(str(item))
        aa.append(hgvs_p)
    table["HGVS_P_1LETTER"] = pd.Series(aa)

    return table


# Function to process VCF and SnpSift files and merge data into a single CSV file.
def process_folder(folder, output_file):
    vcf_records = []

    # Process VCF files and collect records
    for vcf_file in glob.glob(os.path.join(folder, "**", "*.vcf"), recursive=True):
        records = parse_vcf(vcf_file, sample_to_subtype)
        vcf_records.extend(records)

    # Process SnpSift files and collect records
    snpsift_tables = []
    for txt_file in glob.glob(os.path.join(folder, "**", "*.txt"), recursive=True):
        table = snpsift_to_table(txt_file)
        snpsift_tables.append(table)

    # Merge VCF data into a DataFrame
    vcf_df = pd.DataFrame(
        vcf_records,
        columns=[
            "SAMPLE",
            "FLU_SUBTYPE",
            "CHROM",
            "POS",
            "REF",
            "ALT",
            "FILTER",
            "DP",
            "REF_DP",
            "ALT_DP",
            "AF",
        ],
    )
    vcf_df["POS"] = vcf_df["POS"].astype("int64")

    # Add clade information
    clade_path = os.path.abspath(
        os.path.join("..", "05-nextclade", "nextclade_combined.csv")
    )

    if os.path.exists(clade_path):
        clade_df = pd.read_csv(clade_path, sep=";", header=0)
        clade_df["SAMPLE_ID"] = (
            clade_df.iloc[:, 1]
            .str.replace("_HA", "", regex=False)
            .str.replace("/", "-")
        )
        clade_dict = dict(zip(clade_df["SAMPLE_ID"], clade_df.iloc[:, 2]))
        vcf_df["CLADE"] = vcf_df["SAMPLE"].map(clade_dict).fillna("NA")
    else:
        print(
            f"Warning: Clade file not found at {clade_path}. 'CLADE' column will be NA."
        )
        vcf_df["CLADE"] = "NA"

    # Combine all SnpSift tables into one DataFrame
    snpsift_df = pd.concat(snpsift_tables, ignore_index=True).drop_duplicates()
    snpsift_df["POS"] = snpsift_df["POS"].astype("int64")

    # Merge VCF and SnpSift data on CHROM and POS
    merged_df = pd.merge(
        vcf_df, snpsift_df, on=["CHROM", "POS", "REF", "ALT"], how="left"
    ).drop_duplicates()

    # Add CALLER column
    merged_df["CALLER"] = "IRMA"

    columns = [col for col in merged_df.columns if col not in ["CALLER", "CLADE"]] + [
        "CALLER",
        "CLADE",
    ]
    merged_df = merged_df[columns]

    # Save the merged table to a CSV file
    merged_df.to_csv(output_file, index=False)

    print(f"CSV file created: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process VCF and SnpSift files from a folder and merge them into one CSV."
    )
    parser.add_argument(
        "folder", help="Path to the folder containing VCF and SnpSift .txt files."
    )
    parser.add_argument(
        "--output",
        default="variants_long_table.csv",
        help="Output CSV file for merged data.",
    )
    args = parser.parse_args()

    process_folder(args.folder, args.output)
