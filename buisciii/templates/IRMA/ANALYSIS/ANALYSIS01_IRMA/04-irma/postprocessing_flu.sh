#CLEAN
if test -f all_samples_completo.txt; then rm all_samples_completo.txt; fi
for dir in A_*; do
    if [ -d "$dir" ]; then
        rm -rf "$dir"
    fi
done
if test -d B; then rm -rf B; fi
if test -d C; then rm -rf C; fi
if test -d D; then rm -rf D; fi

cat ../samples_id.txt | while read sample; do
    FLUSUBTYPE=$(grep -w ${sample} irma_stats_flu.txt | cut -f5 | cut -d '_' -f1,2)
    FLUTYPE=$(grep -w ${sample} irma_stats_flu.txt | cut -f5 | cut -d '_' -f1)
    if [ -z $FLUTYPE ]; then
        echo "Sample ${sample} doesn't have any fragment. Skipping"
    else
        mkdir -p $FLUSUBTYPE
        ls ${sample}/amended_consensus/*.fa | cut -d '_' -f3 | cut -d '.' -f1 | while read fragment; do
            if [ $fragment == 1 ]; then
                if [ $FLUTYPE == "B" ]; then
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_1/_PB1/' | tee -a ${FLUSUBTYPE}/B_PB1.txt all_samples_completo.txt > /dev/null
                else
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_1/_PB2/' | tee -a ${FLUSUBTYPE}/${FLUTYPE}_PB2.txt all_samples_completo.txt > /dev/null
                fi
            elif [ $fragment == 2 ]; then
                if [ $FLUTYPE == "B" ]; then
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_2/_PB2/' | tee -a ${FLUSUBTYPE}/B_PB2.txt all_samples_completo.txt > /dev/null
                else
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_2/_PB1/' | tee -a ${FLUSUBTYPE}/${FLUTYPE}_PB1.txt all_samples_completo.txt > /dev/null
                fi
            elif [ $fragment == 3 ]; then
                if [ $FLUTYPE == "B" ] || [ $FLUTYPE == "A" ]; then
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_3/_PA/' | tee -a ${FLUSUBTYPE}/${FLUTYPE}_PA.txt all_samples_completo.txt > /dev/null
                else
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_3/_P3/' | tee -a ${FLUSUBTYPE}/${FLUTYPE}_P3.txt all_samples_completo.txt > /dev/null
                fi
            elif [ $fragment == 4 ]; then
                if [ $FLUTYPE == "B" ] || [ $FLUTYPE == "A" ]; then
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_4/_HA/' | tee -a ${FLUSUBTYPE}/${FLUTYPE}_HA.txt all_samples_completo.txt > /dev/null
                else
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_4/_HE/' | tee -a ${FLUSUBTYPE}/${FLUTYPE}_HE.txt all_samples_completo.txt > /dev/null
                fi
            elif [ $fragment == 5 ]; then
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_5/_NP/' | tee -a ${FLUSUBTYPE}/${FLUTYPE}_NP.txt all_samples_completo.txt > /dev/null
            elif [ $fragment == 6 ]; then
                if [ $FLUTYPE == "B" ] || [ $FLUTYPE == "A" ]; then
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_6/_NA/' | tee -a ${FLUSUBTYPE}/${FLUTYPE}_NA.txt all_samples_completo.txt > /dev/null
                else
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_6/_MP/' | tee -a ${FLUSUBTYPE}/${FLUTYPE}_MP.txt all_samples_completo.txt > /dev/null
                fi
            elif [ $fragment == 7 ]; then
                if [ $FLUTYPE == "B" ] || [ $FLUTYPE == "A" ]; then
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_7/_MP/' | tee -a ${FLUSUBTYPE}/${FLUTYPE}_MP.txt all_samples_completo.txt > /dev/null
                else
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_7/_NS/' | tee -a ${FLUSUBTYPE}/${FLUTYPE}_NS.txt all_samples_completo.txt > /dev/null
                fi
            elif [ $fragment == 8 ]; then
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_8/_NS/' | tee -a ${FLUSUBTYPE}/${FLUTYPE}_NS.txt all_samples_completo.txt > /dev/null
            else
                echo "The sample $sample has a segment with number $fragment, but I don't know which segment it is."
            fi
        done
    fi
done