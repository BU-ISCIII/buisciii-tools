echo -e "Sample_ID\tTotalReads\tMappedReads\t%MappedReads\tRSV_type" > irma_stats_rsv.txt

cat ../samples_id.txt | while read in 
do 
SAMPLE_ID=$(echo ${in})
TOTAL_READS=$(grep '1-initial' ${in}/tables/READ_COUNTS.txt | cut -f2)
MAPPEDREADS=$(grep '3-match' ${in}/tables/READ_COUNTS.txt | cut -f2)
PCTMAPPED=$(awk "BEGIN {printf \"%.2f\", ($MAPPEDREADS/$TOTAL_READS)*100}")
RSV_TYPE=$(grep '4-RSV_' ${in}/tables/READ_COUNTS.txt | cut -f1 | cut -d '_' -f2)
echo -e "${SAMPLE_ID}\t${TOTAL_READS}\t${MAPPEDREADS}\t${PCTMAPPED}\t${RSV_TYPE}" >> irma_stats_rsv.txt
done
