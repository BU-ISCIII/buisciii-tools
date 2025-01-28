import os
import re
import pandas as pd
from datetime import datetime
import glob
from collections import defaultdict

current_date = datetime.now().strftime('%Y%m%d')
input_directory_pattern = "./*_viralrecon_mapping/variants/ivar/consensus/bcftools/nextclade"
output_directory_pattern = "./*_viralrecon_mapping"
lineage_excel_pattern = '/data/ucct/bi/references/outbreakinfo/*_mutaciones_definitorias_linaje.csv'
pwd_directory = "./"

input_directories = glob.glob(input_directory_pattern)
lineage_excel_files = glob.glob(lineage_excel_pattern)
input_directory = input_directories[0]
lineage_excel = lineage_excel_files[0]

def create_output_directory(base_directory_pattern):
    """
    Creates a single 'LDM' directory inside the first directory matching the pattern.
    Returns the path of the created directory.
    """
    base_directories = glob.glob(base_directory_pattern)
    
    if not base_directories:
        raise FileNotFoundError(f"No directories matching the pattern were found: {base_directory_pattern}")
    
    base_dir = base_directories[0]
    ldm_dir = os.path.join(base_dir, "LDM")
    os.makedirs(ldm_dir, exist_ok=True)
    print(f"Created or existing directory {ldm_dir}")
    
    return ldm_dir

def normalize_string(s):
    """Normalize strings (remove spaces, convert to lowercase)."""
    if pd.isna(s):
        return ""
    return str(s).strip().lower()

def group_deletions(processed_data):
    """Group deletions by rank."""
    deletion_groups = defaultdict(list)
    
    for row in processed_data:
        if row['type'] == "aaDeletions":
            match = re.match(r"([a-z0-9]+):([a-z])?(\d+)-", row['mutation'])
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
                formatted_deletions.append({'mutation': f"{gene}:del{start}/{start}", 'type': 'deletion'})
            else:
                formatted_deletions.append({'mutation': f"{gene}:del{start}/{end}", 'type': 'deletion'})
    
    return formatted_deletions

def process_and_verify(input_file, lineage_excel, output_tsv, sample_name):
    df = pd.read_csv(input_file, sep=';')
    columns_of_interest = ['Nextclade_pango', 'aaSubstitutions', 'aaDeletions', 'aaInsertions']
    df = df[columns_of_interest].rename(columns={'Nextclade_pango': 'lineage'})
    
    processed_data = []
    for _, row in df.iterrows():
        lineage = normalize_string(row['lineage'])
        for mutation_type in ['aaSubstitutions', 'aaDeletions', 'aaInsertions']:
            if pd.notna(row[mutation_type]):
                mutations = row[mutation_type].split(',')
                for mutation in mutations:
                    processed_data.append({'lineage': lineage, 'type': mutation_type, 'mutation': normalize_string(mutation)})
    
    deletions = group_deletions(processed_data)
    processed_data.extend(deletions)
    
    lineage_df = pd.read_csv(lineage_excel, sep=',')
    lineage_df = lineage_df.iloc[:, [3, 0, 9]]
    lineage_df.columns = ['lineage', 'mutation', 'type']
    
    lineage_df['lineage'] = lineage_df['lineage'].apply(normalize_string)
    lineage_df['mutation'] = lineage_df['mutation'].apply(normalize_string)
    lineage_df['type'] = lineage_df['type'].apply(normalize_string)
    
    processed_df = pd.DataFrame(processed_data)
    processed_df = processed_df[processed_df['type'] != 'aaDeletions']
    
    results = []
    for _, row in processed_df.iterrows():
        mutation_csv = row['mutation']
        mutation_type = row['type']
        match = lineage_df[(lineage_df['mutation'] == mutation_csv) & (lineage_df['lineage'] == lineage)]
        
        if not match.empty:
            exists = 1
            linages_str = ""
        else:
            exists = 0
            linages_list = lineage_df[lineage_df['mutation'] == mutation_csv]['lineage'].unique().tolist()
            linages_str = ', '.join(linages_list) if linages_list else "not defined"

        results.append({
            'sample': sample_name,
            'mutation': mutation_csv,
            'lineage' : lineage,
            'type': mutation_type,
            'exists': exists,
            'LDM linages': linages_str if exists == 0 else None
        })
    
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_tsv, sep='\t', index=False) 
    print(f"Processed file stored in: {output_tsv}")

def process_directory(input_directory, lineage_excel, output_directory):
    csv_files = [f for f in os.listdir(input_directory) if f.endswith('.csv')]
    
    for csv_file in csv_files:
        sample_name = os.path.splitext(csv_file)[0]
        input_file = os.path.join(input_directory, csv_file)
        output_tsv = os.path.join(output_directory, f"{sample_name}_verified_mutations.tsv")
        
        process_and_verify(input_file, lineage_excel, output_tsv, sample_name)

def calculate_mutation_percentage(output_directory, tsv_file):
    """
    Calculates the percentage of mutations and updates the TSV file with the results.
    """

    excel_files = [f for f in os.listdir(output_directory) if f.endswith('.tsv')]
    
    tsv_path = os.path.join('./', tsv_file)
    try:
        tsv_df = pd.read_csv(tsv_path, sep='\t')
    except FileNotFoundError:
        raise FileNotFoundError(f"TSV file not found: {tsv_file} in current directory.")
    
    results = []
    
    for excel_file in excel_files:
        file_path = os.path.join(output_directory, excel_file)
        try:
            df = pd.read_csv(file_path, sep='\t')
            if 'sample' in df.columns:
                df['sample'] = df['sample'].astype(str)
                sample_name = df['sample'].iloc[0]
                total_mutations = len(df)
                count_ones = df['exists'].sum()
                percentage_ones = (count_ones / total_mutations) * 100

                results.append({
                    'sample': sample_name,
                    '% LDMutations': percentage_ones
                })
            else:
                print(f"The file {excel_file} does not contain the column 'sample'.")
        except Exception as e:
            print(f"Error processing file {excel_file}: {e}")
    
    results_df = pd.DataFrame(results)
    
    tsv_df['sample'] = tsv_df['sample'].astype(str)
    results_df['sample'] = results_df['sample'].astype(str)

    if 'sample' not in tsv_df.columns:
        raise KeyError(f"The column 'sample' is not found in the TSV file. Available columns: {tsv_df.columns.tolist()}")
    
    # Combinar los resultados con el archivo TSV
    merged_df = tsv_df.merge(results_df, on='sample', how='left')
    
    # Guardar el archivo combinado en un nuevo TSV
    updated_tsv_path = os.path.join('./', f'{current_date}_quality_control_report.tsv')
    merged_df.to_csv(updated_tsv_path, sep='\t', index=False)
    print(f"Updated TSV file saved in: {updated_tsv_path}")

output_directory = create_output_directory(output_directory_pattern)
process_directory(input_directory, lineage_excel, output_directory)
calculate_mutation_percentage(output_directory, 's_gene_combined_metrics.tsv')