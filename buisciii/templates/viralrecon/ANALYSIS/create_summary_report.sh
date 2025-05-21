#!/bin/bash

# Define fixed data variables
RUN=$(ls -l ../../RAW/ | cut -d'/' -f4 | sort -u | grep -v 'total' | head -n1 | rev | cut -d " " -f 2- | rev)
USER=$(pwd | cut -d '/' -f7 | cut -d '_' -f4)
HOST=$(pwd | cut -d '/' -f9 | cut -d '_' -f4 | tr '[:upper:]' '[:lower:]' | sed 's/.*/\u&/')

# Define header for output file
HEADER="run\tuser\thost\tVirussequence\tsample\ttotalreads\treadshostR1\treadshost\t%readshost\treadsvirus\t%readsvirus\tunmappedreads\t%unmappedreads\tmedianDPcoveragevirus\tCoverage>10x(%)\tVariantsinconsensusx10\tMissenseVariants\t%Ns10x\tLineage\tclade_assignment\tclade_assignment_software_database_version\tclade_assignment_date\tread_length\tanalysis_date"

# Print header to output file
echo -e $HEADER > mapping_illumina_$(date '+%Y%m%d').tab

# Loop through sample list and extract relevant data
cat samples_ref.txt | while read in
do
    # Sample and virus reference names
    arr=($in);

    # Extract data for each column
    total_reads=$(grep 'total_reads' ${arr[1]}*/fastp/${arr[0]}.fastp.json | head -n2 | tail -n1 | cut -d ':' -f2 | sed 's/,//g')

    reads_hostR1=$(cat ${arr[1]}*/kraken2/${arr[0]}.kraken2.report.txt | grep -v 'unclassified' | cut -f3 | awk '{s+=$1}END{print s}')

    if [ -f "../../RAW/${arr[0]}_R2.fastq.gz" ]; then
        # Paired-end reads
        reads_host_x2=$(echo $((reads_hostR1 * 2)) )
    else
        # Single-end reads
        reads_host_x2=$reads_hostR1
    fi

    perc_host=$(echo $(awk -v v1=$total_reads -v v2=$reads_host_x2 'BEGIN {print (v2*100)/v1}') )

    reads_virus=$(cat ${arr[1]}*/variants/bowtie2/samtools_stats/${arr[0]}.sorted.bam.flagstat | grep '+ 0 mapped' | cut -d ' ' -f1)

    unmapped_reads=$(echo $((total_reads - (reads_host_x2+reads_virus))) )
    perc_unmapped=$(echo $(awk -v v1=$total_reads -v v2=$unmapped_reads  'BEGIN {print (v2/v1)*100}') )

    ns_10x_perc=$(cat %Ns.tab | grep -w ${arr[0]} | grep ${arr[1]} | cut -f2)

    missense=$(LC_ALL=C awk -F, '{if($10 >= 0.75)print $0}' ${arr[1]}*/variants/ivar/variants_long_table.csv | grep ^${arr[0]}, | grep 'missense' | wc -l)

    vars_in_cons10x=$(zcat ${arr[1]}*/variants/ivar/consensus/bcftools/${arr[0]}.filtered.vcf.gz | grep -v '^#' | wc -l)

    lineage=$(cat ${arr[1]}*/variants/ivar/consensus/bcftools/pangolin/${arr[0]}.pangolin.csv | tail -n1 | cut -d ',' -f2)

    metrics=$(cat ${arr[1]}*/multiqc/summary_variants_metrics_mqc.csv | grep ^${arr[0]},)
    reads_virus_perc=$(echo "$metrics" | cut -d ',' -f5)
    medianDPcov=$(echo "$metrics" | cut -d ',' -f8)
    cov10x=$(echo "$metrics" | cut -d ',' -f10)

    read_length=$(cat ${arr[1]}*/multiqc/multiqc_data/multiqc_fastqc.yaml | grep -A5 -E "'?${arr[0]}+(_1)?'?:$" | grep "Sequence length:" | tr "-" " " | rev | cut -d " " -f1 | rev)

    analysis_date=$(ls -d *_mapping | grep -oP '\d{8}' | sed 's/\(....\)\(..\)\(..\)/\1-\2-\3/')

    clade=$(tail -n +2 ${arr[1]}*/variants/ivar/consensus/bcftools/nextclade/${arr[0]}.csv | cut -d ";" -f 3)
    clade_assignment_date=$analysis_date
    clade_assignment_software_database_version=$(cat *_viralrecon.log | grep 'nextclade_dataset_tag' | awk -F ': ' '{print $2}' | head -n 1)
    lineage_assignment_date_raw=$(cat $(ls -t ../../DOC/*viralrecon.config | head -n 1) | grep -A1 "pangolin" | grep "datadir" | sed -E 's/.*\/([0-9]{8})\/.*/\1/')
    lineage_assignment_date=$(echo $lineage_assignment_date_raw | sed 's/\(....\)\(..\)\(..\)/\1-\2-\3/')
    lineage_assignment_database_version=$(cat /data/ucct/bi/references/pangolin/$lineage_assignment_date_raw/*_pangolin.log | grep -oP 'pangolin-data updated to \K[^ ]+')

    # Only update pangolin CSV if the folder exists
    pangolin_dir=$(echo "${arr[1]}"*/variants/ivar/consensus/bcftools/pangolin)
    pangolin_file=$(echo "$pangolin_dir/${arr[0]}.pangolin.csv")
    if [[ -f "$pangolin_file" ]]; then
        header_line=$(head -n 1 "$pangolin_file")

        if ! echo "$header_line" | grep -q "lineage_assignment_date,lineage_assignment_database_version"; then
            # Update the .csv pangolin files if the lineage columns are missing
            temp_file="${arr[0]}_tmp.csv"
            touch $temp_file

            {
                IFS= read -r header
                echo "${header},lineage_assignment_date,lineage_assignment_database_version"
                IFS= read -r row
                echo "${row},$lineage_assignment_date,$lineage_assignment_database_version"
            } < $pangolin_file > $temp_file

            mv $temp_file $pangolin_file
        fi
    fi

    # Introduce data row into output file
    echo -e "${RUN}\t${USER}\t${HOST}\t${arr[1]}\t${arr[0]}\t$total_reads\t$reads_hostR1\t$reads_host_x2\t$perc_host\t$reads_virus\t$reads_virus_perc\t$unmapped_reads\t$perc_unmapped\t$medianDPcov\t$cov10x\t$vars_in_cons10x\t$missense\t$ns_10x_perc\t$lineage\t$clade\t$clade_assignment_software_database_version\t$clade_assignment_date\t$read_length\t$analysis_date" >> mapping_illumina_$(date '+%Y%m%d').tab
done
