#!/usr/bin/env bash

OUTPUT="irma_stats_flu.txt"

echo -e "sample_ID\tTotalReads\tMappedReads\t%MappedReads\tFlu_type\tReads_HA\tReads_MP\tReads_NA\tReads_NP\tReads_NS\tReads_PA\tReads_PB1\tReads_PB2" > "$OUTPUT"

while read -r in; do
    [[ -z "$in" ]] && continue

    SAMPLE_ID="$in"
    FILE="${in}/tables/READ_COUNTS.txt"

    if [[ -f "$FILE" ]]; then
        read -r TOTAL_READS MAPPEDREADS PCTMAPPED < <(
            awk -F'\t' '
                $1=="1-initial" {t=$2}
                $1=="3-match"   {m=$2}
                END {
                    t += 0
                    m += 0

                    if (t > 0) {
                        pct = (m / t) * 100
                    } else {
                        pct = 0
                    }

                    printf "%d %d %.2f\n", t, m, pct
                }
            ' "$FILE"
        )

        FLU_TYPE=$(paste \
            <(grep '4-[A-C]' "$FILE" | cut -f1 | cut -d_ -f1 | cut -d- -f2 | head -n1) \
            <(grep '4-[A-B]_HA' "$FILE" | cut -f1 | cut -d_ -f3 | cut -d- -f2) \
            <(grep '4-[A-B]_NA' "$FILE" | cut -f1 | cut -d_ -f3) \
            | tr '\t' '_' \
            | sed 's/_*$//'
        )

        HA=$(grep -m1 '4-[A-C]_HA' "$FILE" | cut -f2)
        MP=$(grep -m1 '4-[A-C]_MP' "$FILE" | cut -f2)
        NA=$(grep -m1 '4-[A-C]_NA' "$FILE" | cut -f2)
        NP=$(grep -m1 '4-[A-C]_NP' "$FILE" | cut -f2)
        NS=$(grep -m1 '4-[A-C]_NS' "$FILE" | cut -f2)
        PA=$(grep -m1 '4-[A-C]_PA' "$FILE" | cut -f2)
        PB1=$(grep -m1 '4-[A-C]_PB1' "$FILE" | cut -f2)
        PB2=$(grep -m1 '4-[A-C]_PB2' "$FILE" | cut -f2)
        HE=$(grep -m1 '4-C_HE' "$FILE" | cut -f2)

        if [[ -n "$HE" ]]; then
            printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
                "$SAMPLE_ID" \
                "$TOTAL_READS" \
                "$MAPPEDREADS" \
                "$PCTMAPPED" \
                "$FLU_TYPE" \
                "$HA" \
                "$MP" \
                "$NA" \
                "$NP" \
                "$NS" \
                "$PA" \
                "$PB1" \
                "$PB2" \
                "$HE" \
                >> "$OUTPUT"
        else
            printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
                "$SAMPLE_ID" \
                "$TOTAL_READS" \
                "$MAPPEDREADS" \
                "$PCTMAPPED" \
                "$FLU_TYPE" \
                "$HA" \
                "$MP" \
                "$NA" \
                "$NP" \
                "$NS" \
                "$PA" \
                "$PB1" \
                "$PB2" \
                >> "$OUTPUT"
        fi

    else
        echo "Sample $SAMPLE_ID doesn't have READ_COUNTS.txt file. Skipping"

        printf "%s\tNA\t0\t0.00\t\t\t\t\t\t\t\t\t\n" \
            "$SAMPLE_ID" \
            >> "$OUTPUT"
    fi

done < ../samples_id.txt

if awk -F'\t' '
    NR > 1 && NF >= 14 && $14 != "" {
        found = 1
    }
    END {
        exit(found ? 0 : 1)
    }
' "$OUTPUT"; then
    sed -i '1s/Reads_PB2$/Reads_PB2\tReads_HE/' "$OUTPUT"
fi