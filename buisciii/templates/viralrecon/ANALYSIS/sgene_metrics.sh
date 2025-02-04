#!/bin/bash

# Define directories for variant analysis
input_fasta_dir=$(echo ./*_viralrecon_mapping/variants/ivar/consensus/bcftools)
input_bam_dir=$(echo ./*_viralrecon_mapping/variants/bowtie2)
input_vcf_dir=$(echo ./*_viralrecon_mapping/variants/ivar)
ref_file="../samples_ref.txt"
output_file="s_gene_combined_metrics.tsv"

# Check if the lablog file exists in the directory
if [ ! -f "lablog" ]; then
    echo "Error: The 'lablog' file was not found."
    exit 1
fi

# Extract FASTA and GFF file paths from the lablog file
FASTA=$(grep --only-matching --perl-regexp "(?<=--fasta\s)(\S+)" lablog)
GFF=$(grep --only-matching --perl-regexp "(?<=--gff\s)(\S+)" lablog)

# Verify that the paths were successfully extracted
if [ -z "$FASTA" ] || [ -z "$GFF" ]; then
    echo "Error: FASTA or GFF file paths were not found in the lablog file."
    exit 1
fi

SGENE_OUTPUT="sgene.fna"

# Extract S gene coordinates from the GFF file
echo "Searching for S gene coordinates in $GFF..."
read CHROM START END <<< $(awk '$3 == "gene" && /Name=S/ {print $1, $4, $5}' "$GFF")

if [[ -z "$START" || -z "$END" ]]; then
    echo "Error: S gene coordinates were not found in the GFF file."
    exit 1
fi

echo "S gene found at: $CHROM:$START-$END"

# Extract the S gene sequence using samtools faidx
echo "Extracting S gene sequence from $FASTA..."
samtools faidx "$FASTA" "$CHROM:$START-$END" > "$SGENE_OUTPUT"

# Verify that extraction was successful
if [ -s "$SGENE_OUTPUT" ]; then
    echo "Extraction successful. Saved as $SGENE_OUTPUT"
else
    echo "Error: S gene extraction failed."
    exit 1
fi

# Modify the header for better clarity
sed -i "s/>.*/>S_gene/" "$SGENE_OUTPUT"

echo "Extraction process completed. File generated: $SGENE_OUTPUT"

# Create output file with headers
echo -e "sample\tS-Gene_Ambiguous_Percentage\tAmbiguous_Positions\tS-Gene_Coverage_Percentage\tS-Gene_Frameshifts\tTotal_Unambiguous_Bases" > $output_file

declare -A ref_map
sed -i -e '$a\' "$ref_file"
while read -r sample ref genome; do
    ref_map["$sample"]=$ref
done < "$ref_file"

# Process fasta files
for fasta_file in $input_fasta_dir/*.consensus.fa; do
  sample_name=$(basename $fasta_file .consensus.fa)
  
  ref_genome=${ref_map["$sample_name"]}
  if [ -z "$ref_genome" ]; then
    echo "Warning: No reference found for sample $sample_name" >&2
    continue
  fi

  # Run BLASTn to obtain S gene coordinates in the consensus sequence
  blast_output=$(blastn -query "$SGENE_OUTPUT" -subject "$fasta_file" -outfmt "6 sstart send" | sort -k2,2nr | head -1)
  if [ -z "$blast_output" ]; then
    echo "Error: No BLAST hit found for sample $sample_name" >&2
    continue
  fi

  # Extract dynamic S gene coordinates
  s_gene_start=$(echo "$blast_output" | awk '{print $1}')
  s_gene_end=$(echo "$blast_output" | awk '{print $2}')
  s_gene_length=$((s_gene_end - s_gene_start + 1))
  
  echo "Sample: $sample_name | S-Gene Start: $s_gene_start | S-Gene End: $s_gene_end"

  # Retrieve the full consensus sequence
  full_sequence=$(grep -v '^>' "$fasta_file" | tr -d '\n')
  total_unambiguous_count=$(echo "$full_sequence" | grep -o '[ATCG]' | wc -l)

  # Calculate S-Gene Ambiguous Percentage
  s_gene_sequence=${full_sequence:$((s_gene_start-1)):s_gene_length}
  ambiguous_positions=()
  for ((i = 0; i < ${#s_gene_sequence}; i++)); do
    base=${s_gene_sequence:i:1}
    if [[ ! "$base" =~ [ATCG] ]]; then
      ambiguous_positions+=($((s_gene_start + i)))
    fi
  done
  ambiguous_bases=${#ambiguous_positions[@]}
  ambiguous_percentage=$(echo "scale=2; $ambiguous_bases / $s_gene_length * 100" | bc)
  ambiguous_positions_str=$(IFS=,; echo "${ambiguous_positions[*]}")

  # Calculate S-Gene Coverage Percentage
  bam_file="$input_bam_dir/${sample_name}.sorted.bam"
  depth_output=$(samtools depth -r "$ref_genome:$s_gene_start-$s_gene_end" "$bam_file" 2>/dev/null)
  covered_bases=$(echo "$depth_output" | awk '{if ($3 > 0) print $0}' | wc -l)
  coverage_percentage=$(echo "scale=2; $covered_bases / $s_gene_length * 100" | bc)

  # Count S-Gene Frameshifts
  vcf_file="$input_vcf_dir/consensus/${sample_name}.vcf.gz"
  indels=$(bcftools view -r "$sample_name:$s_gene_start-$s_gene_end" -i 'TYPE="indel"' "$vcf_file" 2>/dev/null | wc -l)

  echo -e "$sample_name\t$ambiguous_percentage\t$ambiguous_positions_str\t$coverage_percentage\t$indels\t$total_unambiguous_count" >> $output_file
done

echo "Process completed. File generated: $output_file"