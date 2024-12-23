#!/bin/sh
#SBATCH --ntasks 1
#SBATCH --cpus-per-task 2
#SBATCH --mem 4G
#SBATCH --time 2:00:00
#SBATCH --partition middle_idx
#SBATCH --output 20221205_mag.log
#SBATCH --chdir /scratch/bi/SRVCNM786_20221205_GENOMEORTHORNAVIRAE02_mdfernandez_S/ANALYSIS/20221205_ANALYSIS03_MAG

export NXF_OPTS="-Xms500M -Xmx4G"

nextflow run /data/ucct/bi/pipelines/nf-core-mag-2.1.1/workflow/main.nf \
          -c ../../DOC/mag.config \
          --input '00-reads/*_R{1,2}.fastq.gz' \
          --outdir 20221205_mag \
          --kraken2_db /data/ucct/bi/references/kraken/minikraken_8GB_20200312.tgz \
          --skip_busco --skip_spades --skip_spadeshybrid --skip_megahit --skip_prodigal --skip_binning \
          -resume
