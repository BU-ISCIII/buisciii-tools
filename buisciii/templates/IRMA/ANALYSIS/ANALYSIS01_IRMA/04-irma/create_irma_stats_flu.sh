#!/usr/bin/env bash

echo -e "sample_ID\tTotalReads\tMappedReads\t%MappedReads\tFlu_type\tReads_HA\tReads_MP\tReads_NA\tReads_NP\tReads_NS\tReads_PA\tReads_PB1\tReads_PB2" > irma_stats_flu.txt

cat ../samples_id.txt | while read in
do
    SAMPLE_ID=$(echo ${in})
    TOTAL_READS=""; MAPPEDREADS=""; PCTMAPPED=""; FLU_TYPE=""; HA=""; MP=""; NA=""; NP=""; NS=""; PA=""; PB1=""; PB2=""; HE=""; MAIN_HA=""; MAIN_NA=""
    COUNTS_FILE=${in}/tables/READ_COUNTS.txt
    SECONDARY_ASSEMBLY=0

    # Check if the sample has a secondary assembly and use its READ_COUNTS.txt if it exists
    if test -f ${in}/secondary_assembly/tables/READ_COUNTS.txt; then
        COUNTS_FILE=${in}/secondary_assembly/tables/READ_COUNTS.txt
        SECONDARY_ASSEMBLY=1
    fi

    if test -f ${COUNTS_FILE}; then
        TOTAL_READS=$(grep '1-initial' ${COUNTS_FILE} | cut -f2)
        MAPPEDREADS=$(grep '3-match' ${COUNTS_FILE} | cut -f2)
        PCTMAPPED=$(awk "BEGIN {printf \"%.2f\", ($MAPPEDREADS/$TOTAL_READS)*100}")
        FLU_TYPE=$(paste <(grep '4-[A-C]' ${COUNTS_FILE} | cut -f1 | cut -d '_' -f1 | cut -d '-' -f2 | head -n1 ) <(grep '4-[A-B]_HA' ${COUNTS_FILE} | cut -f1 | cut -d '_' -f3 | cut -d '-' -f2) <(grep '4-[A-B]_NA' ${COUNTS_FILE} | cut -f1 | cut -d '_' -f3) | tr '\t' '_' | sed 's/_*$//')
        HA=$(grep '4-[A-C]_HA' ${COUNTS_FILE} | cut -f2)
        MP=$(grep '4-[A-C]_MP' ${COUNTS_FILE} | cut -f2)
        NA=$(grep '4-[A-C]_NA' ${COUNTS_FILE} | cut -f2)
        NP=$(grep '4-[A-C]_NP' ${COUNTS_FILE} | cut -f2)
        NS=$(grep '4-[A-C]_NS' ${COUNTS_FILE} | cut -f2)
        PA=$(grep '4-[A-C]_PA' ${COUNTS_FILE} | cut -f2)
        PB1=$(grep '4-[A-C]_PB1' ${COUNTS_FILE} | cut -f2)
        PB2=$(grep '4-[A-C]_PB2' ${COUNTS_FILE} | cut -f2)
        #In case of Influenza C in samples:
        HE=$(grep '4-C_HE' ${COUNTS_FILE} | cut -f2)

        # For secondary assemblies, use the most abundant HA and NA in the main row.
        if [[ ${SECONDARY_ASSEMBLY} -eq 1 ]]; then
            MAIN_HA=$(grep '4-[A-C]_HA' ${COUNTS_FILE} | sort -t$'\t' -k2,2nr | head -n1)
            MAIN_NA=$(grep '4-[A-C]_NA' ${COUNTS_FILE} | sort -t$'\t' -k2,2nr | head -n1)

            if [[ -n "${MAIN_HA}" && -n "${MAIN_NA}" ]]; then
                HA=$(printf "%s\n" "${MAIN_HA}" | cut -f2)
                NA=$(printf "%s\n" "${MAIN_NA}" | cut -f2)
                FLU_PREFIX=$(grep '4-[A-C]' ${COUNTS_FILE} | cut -f1 | cut -d '_' -f1 | cut -d '-' -f2 | head -n1)
                HA_TYPE=$(printf "%s\n" "${MAIN_HA}" | cut -f1 | cut -d _ -f3)
                NA_TYPE=$(printf "%s\n" "${MAIN_NA}" | cut -f1 | cut -d _ -f3)
                FLU_TYPE=$(printf '%s_%s_%s' ${FLU_PREFIX} ${HA_TYPE} ${NA_TYPE} | sed 's/_*$//')
            fi
        fi

        if [[ -n "$HE" ]]; then
            LINE=$(paste <(echo $SAMPLE_ID) <(echo $TOTAL_READS) <(echo $MAPPEDREADS) <(echo $PCTMAPPED) <(echo $FLU_TYPE) <(echo $HA) <(echo $MP) <(echo $NA) <(echo $NP) <(echo $NS) <(echo $PA) <(echo $PB1) <(echo $PB2) <(echo $HE))
        else
            LINE=$(paste <(echo $SAMPLE_ID) <(echo $TOTAL_READS) <(echo $MAPPEDREADS) <(echo $PCTMAPPED) <(echo $FLU_TYPE) <(echo $HA) <(echo $MP) <(echo $NA) <(echo $NP) <(echo $NS) <(echo $PA) <(echo $PB1) <(echo $PB2))
        fi
    else
        echo "Sample $SAMPLE_ID doesn't have READ_COUNTS.txt file. Skipping"
        TOTAL_READS=NA
        MAPPEDREADS=0
        PCTMAPPED=0
        LINE=$(paste <(echo $SAMPLE_ID) <(echo $TOTAL_READS) <(echo $MAPPEDREADS) <(echo $PCTMAPPED))
    fi

    if [[ ${SECONDARY_ASSEMBLY} -eq 1 ]]; then
        # Report every influenza type independently in a secondary assembly.
        for FLU_PREFIX in $(grep '^4-[A-C]_' ${COUNTS_FILE} | cut -f1 | cut -d '_' -f1 | cut -d '-' -f2 | sort -u)
        do
            TYPE_MAPPEDREADS=$(grep "^4-${FLU_PREFIX}_" ${COUNTS_FILE} | cut -f2 | awk '{sum += $1} END {print sum + 0}')
            TYPE_PCTMAPPED=$(awk "BEGIN {printf \"%.2f\", (${TYPE_MAPPEDREADS}/${TOTAL_READS})*100}")
            MAIN_HA=$(grep "^4-${FLU_PREFIX}_HA" ${COUNTS_FILE} | sort -t$'\t' -k2,2nr | head -n1)
            MAIN_NA=$(grep "^4-${FLU_PREFIX}_NA" ${COUNTS_FILE} | sort -t$'\t' -k2,2nr | head -n1)
            TYPE_HA=$(printf "%s\n" "${MAIN_HA}" | cut -f2)
            TYPE_NA=$(printf "%s\n" "${MAIN_NA}" | cut -f2)
            TYPE_MP=$(grep "^4-${FLU_PREFIX}_MP" ${COUNTS_FILE} | cut -f2)
            TYPE_NP=$(grep "^4-${FLU_PREFIX}_NP" ${COUNTS_FILE} | cut -f2)
            TYPE_NS=$(grep "^4-${FLU_PREFIX}_NS" ${COUNTS_FILE} | cut -f2)
            TYPE_PA=$(grep "^4-${FLU_PREFIX}_PA" ${COUNTS_FILE} | cut -f2)
            TYPE_PB1=$(grep "^4-${FLU_PREFIX}_PB1" ${COUNTS_FILE} | cut -f2)
            TYPE_PB2=$(grep "^4-${FLU_PREFIX}_PB2" ${COUNTS_FILE} | cut -f2)
            TYPE_HE=$(grep "^4-${FLU_PREFIX}_HE" ${COUNTS_FILE} | cut -f2)
            TYPE_FLU_TYPE=${FLU_PREFIX}

            # Influenza A has HA and NA subtypes; B and C are reported by type.
            if [[ "${FLU_PREFIX}" == "A" && -n "${MAIN_HA}" && -n "${MAIN_NA}" ]]; then
                HA_TYPE=$(printf "%s\n" "${MAIN_HA}" | cut -f1 | cut -d _ -f3 | cut -d - -f2)
                NA_TYPE=$(printf "%s\n" "${MAIN_NA}" | cut -f1 | cut -d _ -f3)
                TYPE_FLU_TYPE=$(printf '%s_%s_%s' ${FLU_PREFIX} ${HA_TYPE} ${NA_TYPE})
            fi

            if [[ -n "${TYPE_HE}" ]]; then
                TYPE_LINE=$(paste <(echo $SAMPLE_ID) <(echo $TOTAL_READS) <(echo $TYPE_MAPPEDREADS) <(echo $TYPE_PCTMAPPED) <(echo $TYPE_FLU_TYPE) <(echo $TYPE_HA) <(echo $TYPE_MP) <(echo $TYPE_NA) <(echo $TYPE_NP) <(echo $TYPE_NS) <(echo $TYPE_PA) <(echo $TYPE_PB1) <(echo $TYPE_PB2) <(echo $TYPE_HE))
            else
                TYPE_LINE=$(paste <(echo $SAMPLE_ID) <(echo $TOTAL_READS) <(echo $TYPE_MAPPEDREADS) <(echo $TYPE_PCTMAPPED) <(echo $TYPE_FLU_TYPE) <(echo $TYPE_HA) <(echo $TYPE_MP) <(echo $TYPE_NA) <(echo $TYPE_NP) <(echo $TYPE_NS) <(echo $TYPE_PA) <(echo $TYPE_PB1) <(echo $TYPE_PB2))
            fi
            echo "$TYPE_LINE" >> irma_stats_flu.txt

            # Add the minor A HA and NA subtypes without repeating shared segments.
            if [[ "${FLU_PREFIX}" == "A" && -n "${MAIN_HA}" && -n "${MAIN_NA}" ]]; then
                MAIN_HA_NAME=$(printf "%s\n" "${MAIN_HA}" | cut -f1)
                MAIN_NA_NAME=$(printf "%s\n" "${MAIN_NA}" | cut -f1)

                grep "^4-${FLU_PREFIX}_HA_" ${COUNTS_FILE} | while IFS=$'\t' read NAME READS REST
                do
                    if [[ "${NAME}" != "${MAIN_HA_NAME}" ]]; then
                        TYPE=$(echo ${NAME} | cut -d '_' -f3 | cut -d '-' -f2)
                        PCT=$(awk "BEGIN {printf \"%.2f\", (${READS}/${TOTAL_READS})*100}")
                        printf '%s\t%s\t%s\t%s\t%s_%s\t%s\n' "$SAMPLE_ID" "$TOTAL_READS" "$READS" "$PCT" "$FLU_PREFIX" "$TYPE" "$READS" >> irma_stats_flu.txt
                    fi
                done

                grep "^4-${FLU_PREFIX}_NA_" ${COUNTS_FILE} | while IFS=$'\t' read NAME READS REST
                do
                    if [[ "${NAME}" != "${MAIN_NA_NAME}" ]]; then
                        TYPE=$(echo ${NAME} | cut -d '_' -f3)
                        PCT=$(awk "BEGIN {printf \"%.2f\", (${READS}/${TOTAL_READS})*100}")
                        printf '%s\t%s\t%s\t%s\t%s_%s\t\t\t%s\n' "$SAMPLE_ID" "$TOTAL_READS" "$READS" "$PCT" "$FLU_PREFIX" "$TYPE" "$READS" >> irma_stats_flu.txt
                    fi
                done
            fi
        done
    else
        echo "$LINE" >> irma_stats_flu.txt
    fi
done

ANY_C=$(cut -f5 irma_stats_flu.txt | grep -x C)
if [[ -n "$ANY_C" ]]; then
    sed -i 's/Reads_PB2/Reads_PB2\tReads_HE/g' irma_stats_flu.txt
fi