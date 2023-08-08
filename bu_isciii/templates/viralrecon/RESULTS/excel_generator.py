import os
import argparse
import pandas as pd
from typing import List, Dict

# conda activate viralrecon_report
"""Usage: python excel_generator.py ./reference.tmp"""
parser = argparse.ArgumentParser(description="Generate excel files from viralrecon results")
parser.add_argument("reference_file", type=str, help="File containing the references used in the analysis")

args = parser.parse_args()

print(f"Extracting references used for analysis and the samples associated with each reference\n")
with open(args.reference_file, "r") as file:
    references = [line.rstrip() for line in file]
    print(f"\nFound {len(references)} references: {str(references).strip('[]')}")

reference_folders = {ref: str("excel_files_"+ref) for ref in references}
samples_ref_files = {ref: str("ref_samples/samples_"+ref+".tmp") for ref in references}

def concat_tables_and_write(csvs_in_folder: List[str], merged_csv_name: str):
    """Concatenate any tables that share the same header"""
    with open (merged_csv_name, "wb") as merged_csv:
        with open(csvs_in_folder[0], "rb") as f:
            merged_csv.write(f.read()) # This is the fastest way to concatenate csv files
        for file in csvs_in_folder[1:]:
            with open(file, "rb") as f:
                next(f) #this is used to skip the header
                merged_csv.write(f.read()) 
    return merged_csv

def merge_lineage_tables(reference_folders: Dict[str,str], samples_ref_files: Dict[str,str]):
    """Creates the tables for pangolin and nextclade"""
    for ref, folder in reference_folders.items():
        print("Merging results for either pangolin or nextclade in a single csv file")
        samples_for_ref = open(samples_ref_files[ref]).read().splitlines()
        if os.path.isdir(os.path.abspath(folder+"/pangolin")):
            pango_dir = os.path.join(folder,"pangolin")
            csvs_in_folder = [file.path for file in os.scandir(pango_dir) 
                if os.path.basename(file).split("_")[0] in samples_for_ref]
            merged_csv_name = os.path.join(folder,str(ref+"_pangolin.csv"))
            concat_tables_and_write(csvs_in_folder=csvs_in_folder, merged_csv_name=merged_csv_name)
        else:
            print(f"No pangolin folder could be found for {ref}, omitting")

        if os.path.isdir(os.path.abspath(folder+"/nextclade")):
            nextcl_dir = os.path.join(folder,"nextclade")
            csvs_in_folder = [file.path for file in os.scandir(nextcl_dir) 
                if os.path.splitext(os.path.basename(file))[0] in samples_for_ref]
            merged_csv_name = os.path.join(folder,str(ref+"_nextclade.csv"))
            concat_tables_and_write(csvs_in_folder=csvs_in_folder, merged_csv_name=merged_csv_name)
        else:
            print(f"No nextclade folder could be found for {ref}, omitting")
        
    return

def excel_generator(csv_files: List[str]):
    for file in csv_files:
        if not os.path.exists(file):
            print(f"File {file} does not exist, omitting...")
            continue
        print(f"Generating excel file for {file}")
        output_name = str(file.split(".csv")[0] + ".xlsx")
        #workbook = openpyxl.Workbook(output_name)
        if "nextclade" in str(file):
            pd.read_csv(file, sep=";", header=0).to_excel(output_name, index=False)
        elif "illumina" in str(file):
            table = pd.read_csv(file, sep="\t", header=0)
            table["analysis_date"] = pd.to_datetime(table["analysis_date"].astype(str), format='%Y%m%d')
            table.to_excel(output_name, index=False)
        elif "assembly" in str(file):
             pd.read_csv(file, sep="\t", header=0).to_excel(output_name, index=False)
        else:
            pd.read_csv(file).to_excel(output_name, index=False)
    return file

#Merge pangolin and nextclade csv files separatedly and create excel files for them
merge_lineage_tables(reference_folders, samples_ref_files)
for reference, folder in reference_folders.items():
    print(f"Creating excel files for reference {reference}")
    csv_files = [file.path for file in os.scandir(folder) if file.path.endswith(".csv")]
    excel_generator(csv_files)

#Merge all the variant long tables into one and convert to excel format
variants_tables = [table.path for table in os.scandir(".") if "variants_long_table" in table.path]
concat_tables_and_write(csvs_in_folder=variants_tables, merged_csv_name="variants_long_table.csv")
pd.read_csv("variants_long_table.csv").to_excel("variants_long_table.xlsx", index=False)

#Create excel files for individual tables
result_tables = ["mapping_illumina.csv", "assembly_stats.csv", "pikavirus_table.csv"]
excel_generator(result_tables)