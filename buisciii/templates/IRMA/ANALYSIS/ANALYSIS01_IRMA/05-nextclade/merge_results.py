import pandas as pd
from pathlib import Path

base_dir = Path(".")
output_file = "nextclade_combined.csv"

dfs = []

# Iterate over all nextclade.csv files
for csv_path in base_dir.glob("*/nextclade.csv"):
    df = pd.read_csv(csv_path, sep=";", dtype=str)
    dfs.append(df)

combined_df = pd.concat(dfs, ignore_index=True).fillna("NA")

combined_df.to_csv(output_file, sep=";", index=False)

print(f"✅ Combined file saved to: {output_file}")
