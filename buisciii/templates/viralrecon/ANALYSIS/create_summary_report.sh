#!/bin/bash

# Define fixed data variables
RUN=$(ls -l ../../RAW/ | cut -d'/' -f4 | sort -u | grep -v 'total' | head -n1 | rev | cut -d " " -f 2- | rev)
USER=$(pwd | cut -d '/' -f6 | cut -d '_' -f4)
HOST=$(pwd | cut -d '/' -f8 | cut -d '_' -f4 | tr '[:upper:]' '[:lower:]' | sed 's/.*/\u&/')

# Define header for output file
HEADER="run\tuser\thost\tVirussequence\tsample\ttotalreads\treadshostR1\treadshost\t%readshost\treadsvirus\t%readsvirus\tunmappedreads\t%unmapedreads\tmedianDPcoveragevirus\tCoverage>10x(%)\tVariantsinconsensusx10\tMissenseVariants\t%Ns10x\tLineage\tread_length\tanalysis_date"

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
    reads_host_x2=$(echo $((reads_hostR1 * 2)) )
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

    read_length=$(cat ${arr[1]}*/multiqc/multiqc_data/multiqc_fastqc.yaml | grep -A5 -E "'?${arr[0]}_1'?:$" | grep "Sequence length:" | tr "-" " " | rev | cut -d " " -f1 | rev)

    analysis_date=$(date '+%Y%m%d')

    # Introduce data row into output file
    echo -e "${RUN}\t${USER}\t${HOST}\t${arr[1]}\t${arr[0]}\t$total_reads\t$reads_hostR1\t$reads_host_x2\t$perc_host\t$reads_virus\t$reads_virus_perc\t$unmapped_reads\t$perc_unmapped\t$medianDPcov\t$cov10x\t$vars_in_cons10x\t$missense\t$ns_10x_perc\t$lineage\t$read_length\t$analysis_date" >> mapping_illumina_$(date '+%Y%m%d').tab
done
