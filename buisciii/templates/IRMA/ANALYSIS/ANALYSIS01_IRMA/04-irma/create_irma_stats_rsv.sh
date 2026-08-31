#!/usr/bin/env bash

echo -e "Sample_ID\tTotalReads\tMappedReads\t%MappedReads\tRSV_type" > irma_stats_rsv.txt

while read -r in; do
    SAMPLE_ID="$in"
    FILE="${in}/tables/READ_COUNTS.txt"

    if [[ -f "$FILE" ]]; then
        read -r TOTAL_READS MAPPEDREADS PCTMAPPED < <(
            awk -F'\t' '
                $1=="1-initial" {t=$2}
                $1=="3-match"   {m=$2}
                END {
                    t+=0
                    m+=0
                    printf "%d %d %.2f\n", t, m, t>0 ? (m/t)*100 : 0
                }
            ' "$FILE"
        )

        RSV_TYPE=$(grep '4-RSV_' "$FILE" | cut -f1 | cut -d_ -f2)
    else
        echo "Sample $SAMPLE_ID doesn't have READ_COUNTS.txt file. Skipping"
        TOTAL_READS="NA"
        MAPPEDREADS=0
        PCTMAPPED="0.00"
        RSV_TYPE=""
    fi

    printf "%s\t%s\t%s\t%s\t%s\n" \
        "$SAMPLE_ID" \
        "$TOTAL_READS" \
        "$MAPPEDREADS" \
        "$PCTMAPPED" \
        "$RSV_TYPE" \
        >> irma_stats_rsv.txt

done < ../samples_id.txt