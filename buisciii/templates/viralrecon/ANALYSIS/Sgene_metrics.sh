#!/bin/bash

input_fasta_dir="./*_viralrecon_mapping/variants/ivar/consensus/bcftools"
input_bam_dir="./*_viralrecon_mapping/variants/bowtie2"
input_vcf_dir="./*_viralrecon_mapping/variants/ivar"
ref_file="../samples_ref.txt"
output_file="s_gene_combined_metrics.tsv"

echo -e "sample\tS-Gene_Ambiguous_Percentage\tAmbiguous_Positions\tS-Gene_Coverage_Percentage\tS-Gene_Frameshifts\tTotal_Unambiguous_Bases\tTotal_Ns_count" > $output_file

s_gene_start=21563
s_gene_end=25384
s_gene_length=$((s_gene_end - s_gene_start + 1))

declare -A ref_map
sed -i -e '$a\' ../samples_ref.txt
while read -r sample ref genome; do
    ref_map["$sample"]=$ref
done < "$ref_file"

for fasta_file in $input_fasta_dir/*.consensus.fa; do
  sample_name=$(basename $fasta_file .consensus.fa)
  
  ref_genome=${ref_map["$sample_name"]}
  if [ -z "$ref_genome" ]; then
    echo "Warning: No reference found for the sample $sample_name" >&2
    continue
  fi

  gen_s_region="$ref_genome:$s_gene_start-$s_gene_end"

  full_sequence=$(grep -v '^>' "$fasta_file" | tr -d '\n')
  total_unambiguous_count=$(echo "$full_sequence" | grep -o '[ATCG]' | wc -l)
  total_Ns_counts=$(echo "$full_sequence" | grep -o '[N]' | wc -l)

  # S-Gene Ambiguous Percentage
  sequence=$(grep -v '^>' "$fasta_file" | tr -d '\n')
  s_gene_sequence=${sequence:$((s_gene_start-1)):s_gene_length}
  ambiguous_positions=()
  for ((i = 0; i < ${#s_gene_sequence}; i++)); do
    base=${s_gene_sequence:i:1}
    if [ "$base" == "N" ]; then
      ambiguous_positions+=($((s_gene_start + i)))
    fi
  done
  ambiguous_bases=${#ambiguous_positions[@]}
  ambiguous_percentage=$(echo "scale=2; $ambiguous_bases / $s_gene_length * 100" | bc)
  ambiguous_positions_str=$(IFS=,; echo "${ambiguous_positions[*]}")

  # S-Gene Coverage Percentage
  bam_file="$input_bam_dir/${sample_name}.sorted.bam"
  depth_output=$(samtools depth -r $gen_s_region $bam_file 2>/dev/null)
  covered_bases=$(echo "$depth_output" | awk '{if ($3 > 0) print $0}' | wc -l)
  coverage_percentage=$(echo "scale=2; $covered_bases / $s_gene_length * 100" | bc)

  # S-Gene Frameshifts
  vcf_file="$input_vcf_dir/consensus/${sample_name}.vcf.gz"
  indels=$(bcftools view -r $gen_s_region -i 'TYPE="indel"' $vcf_file 2>/dev/null | wc -l)

  echo -e "$sample_name\t$ambiguous_percentage\t$ambiguous_positions_str\t$coverage_percentage\t$indels\t$total_unambiguous_count\t$total_Ns_counts" >> $output_file
done
