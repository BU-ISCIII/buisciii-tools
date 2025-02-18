#!/bin/bash

# Define directories for variant analysis
input_fasta_dir=$(echo ./*_viralrecon_mapping/variants/ivar/consensus/bcftools)
input_bam_dir=$(echo ./*_viralrecon_mapping/variants/bowtie2)
input_vcf_dir=$(echo ./*_viralrecon_mapping/variants/ivar)
ref_file="../samples_ref.txt"
output_file="s_gene_combined_metrics.tsv"
SGENE_OUTPUT="/data/ucct/bi/references/refgenie/alias/coronaviridae/fasta/NC_045512.2/sgene.fna"

# Create output file with headers
echo -e "sample\tS-Gene_Ambiguous_Percentage\tS-Gene_Coverage_Percentage\tS-Gene_Frameshifts\tTotal_Unambiguous_Bases\tTotal_Ns_count" > $output_file

# Read reference mappings into an associative array
declare -A ref_map
sed -i -e '$a\' "$ref_file"
while read -r sample ref genome; do
    ref_map["$sample"]=$ref
done < "$ref_file"

# Process FASTA files
for fasta_file in $input_fasta_dir/*.consensus.fa; do
  sample_name=$(basename $fasta_file .consensus.fa)
  
  ref_genome=${ref_map["$sample_name"]}
  if [ -z "$ref_genome" ]; then
    echo "Warning: No reference found for sample $sample_name" >&2
    continue
  fi

  # Run BLASTn to get S-gene coordinates in the consensus sequence
  blast_output=$(blastn -query "$SGENE_OUTPUT" -subject "$fasta_file" -outfmt "6 sstart send" | sort -k2,2nr | head -1)
  if [ -z "$blast_output" ]; then
    echo "Error: No BLAST hit found for sample $sample_name" >&2
    continue
  fi

  # Extract dynamic S-gene coordinates
  s_gene_start=$(echo "$blast_output" | awk '{print $1}')
  s_gene_end=$(echo "$blast_output" | awk '{print $2}')
  s_gene_length=$((s_gene_end - s_gene_start + 1))
  
  echo "Sample: $sample_name | S-Gene Start: $s_gene_start | S-Gene End: $s_gene_end"

  # Get the full consensus sequence
  full_sequence=$(grep -v '^>' "$fasta_file" | tr -d '\n')
  total_unambiguous_count=$(echo "$full_sequence" | grep -o '[ATCGN]' | wc -l)
  total_ns_count=$(echo "$full_sequence" | grep -o 'N' | wc -l)

  # Calculate S-Gene Ambiguous Percentage
  s_gene_sequence=${full_sequence:$((s_gene_start-1)):s_gene_length}
  ambiguous_positions=()
  for ((i = 0; i < ${#s_gene_sequence}; i++)); do
    base=${s_gene_sequence:i:1}
    if [[ ! "$base" =~ [ATCGN] ]]; then
      ambiguous_positions+=($((s_gene_start + i)))
    fi
  done
  ambiguous_bases=${#ambiguous_positions[@]}
  ambiguous_percentage=$(echo "scale=2; $ambiguous_bases / $s_gene_length * 100" | bc)
  ambiguous_percentage=$(printf "%.2f" "$ambiguous_percentage")

  # Calculate S-Gene Coverage Percentage
  bam_file="$input_bam_dir/${sample_name}.sorted.bam"
  depth_output=$(samtools depth -r "$ref_genome:$s_gene_start-$s_gene_end" "$bam_file" 2>/dev/null)
  covered_bases=$(echo "$depth_output" | awk '{if ($3 > 0) print $0}' | wc -l)
  coverage_percentage=$(echo "scale=2; $covered_bases / $s_gene_length * 100" | bc)
  coverage_percentage=$(printf "%.2f" "$coverage_percentage")

  # Count S-Gene Frameshifts
  vcf_file="$input_vcf_dir/consensus/${sample_name}.vcf.gz"
  indels=$(bcftools view -r "$sample_name:$s_gene_start-$s_gene_end" -i 'TYPE="indel"' "$vcf_file" 2>/dev/null | wc -l)

  # Save results to output file
  echo -e "$sample_name\t$ambiguous_percentage\t$coverage_percentage\t$indels\t$total_unambiguous_count\t$total_ns_count" >> $output_file
done

echo "Process completed. File generated: $output_file"