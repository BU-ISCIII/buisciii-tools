#!/bin/sh
#SBATCH --ntasks 1
#SBATCH --cpus-per-task 2
#SBATCH --mem 8G
#SBATCH --time 8:00:00
#SBATCH --partition middle_idx
#SBATCH --output 20221205_assembly01.log
#SBATCH --chdir /scratch/bi/SRVCNM787_20221205_ASSEMBLY315_lherrera_S/ANALYSIS/20221205_ANALYSIS01_ASSEMBLY

export NXF_OPTS="-Xms500M -Xmx4G"

nextflow run /scratch/bi/pipelines/BU_ISCIII-bacterial-assembly/main.nf \
          -c ../../DOC/hpc_slurm_assembly.config \
          --input samplesheet.csv \
          --outdir ./ \
          --cut_mean_quality 20 \
          --qualified_quality_phred 20 \
          --gram + \
          --reference_outdir ../../REFERENCES \
	  --save_trimmed false \
          --kmerfinder_bacteria_database '/data/ucct/bi/references/kmerfinder/20190108_stable_dirs/bacteria' \
          --reference_ncbi_bacteria '/data/ucct/bi/references/bacteria/latest_db/assembly_summary_bacteria.txt' \
          -resume
