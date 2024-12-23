#!/bin/sh
#SBATCH --ntasks 1
#SBATCH --cpus-per-task 2
#SBATCH --mem 4G
#SBATCH --time 2:00:00
#SBATCH --partition middle_idx
#SBATCH --output RotavirusA_11segments_20221205_viralrecon.log
#SBATCH --chdir /scratch/bi/SRVCNM786_20221205_GENOMEORTHORNAVIRAE02_mdfernandez_S/ANALYSIS/20221205_ANALYSIS02_METAGENOMIC_HUMAN

export NXF_OPTS="-Xms500M -Xmx4G"

nextflow run /scratch/bi/pipelines/nf-core-viralrecon-2.5/workflow/main.nf \
          -c ./viralrecon_metagenomic.config \
          --input samplesheet_RotavirusA_11segments.csv \
          --outdir RotavirusA_11segments_20221205_viralrecon_mapping \
          --fasta /data/ucct/bi/references/virus/reoviridae/RotavirusA_11segments.fasta \
          --gff /data/ucct/bi/references/virus/reoviridae/RotavirusA_11segments.gff \
          --platform illumina \
          --protocol metagenomic \
          --kraken2_db "/data/ucct/bi/references/eukaria/homo_sapiens/hg38/UCSC/kraken2/kraken2_human.tar.gz" \
          --variant_caller ivar \
          --consensus_caller bcftools \
          --skip_pangolin \
          --skip_nextclade \
          --skip_asciigenome \
          --skip_abacas \
          --skip_plasmidid \
          -resume
