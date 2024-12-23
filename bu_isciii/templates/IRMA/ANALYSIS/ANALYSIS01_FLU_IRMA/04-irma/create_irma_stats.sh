
echo -e "sample_ID\tTotalReads\tMappedReads\tFlu_type\tReads_HA\tReads_MP\tReads_NA\tReads_NP\tReads_NS\tReads_PA\tReads_PB1\tReads_PB2" > irma_stats.txt

cat ../samples_id.txt | while read in 
do 
SAMPLE_ID=$(echo ${in})
TOTAL_READS=$(grep '1-initial' ${in}/tables/READ_COUNTS.txt | cut -f2)
MAPPEDREADS=$(grep '3-match' ${in}/tables/READ_COUNTS.txt | cut -f2)
PCTMAPPED=$(awk "BEGIN {printf \"%.2f\", ($MAPPEDREADS/$TOTAL_READS)*100}")
FLU_TYPE=$(paste <(grep '4-[A-C]_MP' ${in}/tables/READ_COUNTS.txt | cut -f1 | cut -d '_' -f1 | cut -d '-' -f2) <(grep '4-[A-B]_HA' ${in}/tables/READ_COUNTS.txt | cut -f1 | cut -d '_' -f3 | cut -d '-' -f2) <(grep '4-[A-B]_NA' ${in}/tables/READ_COUNTS.txt | cut -f1 | cut -d '_' -f3) | tr '\t' '_')
HA=$(grep '4-[A-C]_HA' ${in}/tables/READ_COUNTS.txt | cut -f2)
MP=$(grep '4-[A-C]_MP' ${in}/tables/READ_COUNTS.txt | cut -f2)
NA=$(grep '4-[A-C]_NA' ${in}/tables/READ_COUNTS.txt | cut -f2)
NP=$(grep '4-[A-C]_NP' ${in}/tables/READ_COUNTS.txt | cut -f2)
NS=$(grep '4-[A-C]_NS' ${in}/tables/READ_COUNTS.txt | cut -f2)
PA=$(grep '4-[A-C]_PA' ${in}/tables/READ_COUNTS.txt | cut -f2)
PB1=$(grep '4-[A-C]_PB1' ${in}/tables/READ_COUNTS.txt | cut -f2)
PB2=$(grep '4-[A-C]_PB2' ${in}/tables/READ_COUNTS.txt | cut -f2)
#In case of Influenza C in samples:
HE=$(grep '4-C_HE' ${in}/tables/READ_COUNTS.txt | cut -f2)
if [[ -n "$HE" ]]; then
    LINE=$(paste <(echo $SAMPLE_ID) <(echo $TOTAL_READS) <(echo $MAPPEDREADS) <(echo $FLU_TYPE) <(echo $HA) <(echo $MP) <(echo $NA) <(echo $NP) <(echo $NS) <(echo $PA) <(echo $PB1) <(echo $PB2) <(echo $HE))
else
    LINE=$(paste <(echo $SAMPLE_ID) <(echo $TOTAL_READS) <(echo $MAPPEDREADS) <(echo $FLU_TYPE) <(echo $HA) <(echo $MP) <(echo $NA) <(echo $NP) <(echo $NS) <(echo $PA) <(echo $PB1) <(echo $PB2))
fi

echo "$LINE" >> irma_stats.txt

done

ANY_C=$(grep "C_" irma_stats.txt)
if [[ -n "$ANY_C" ]]; then
    sed -i 's/Reads_PB2/Reads_PB2\tReads_HE/g' irma_stats.txt
fi
