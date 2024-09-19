#CLEAN
if test -f all_samples_completo.txt; then rm all_samples_completo.txt; fi
if test -d A_*; then rm -rf A_*; fi
if test -d B; then rm -rf B; fi
if test -d C; then rm -rf C; fi
if test -d D; then rm -rf D; fi

cat ../samples_id.txt | while read sample; do
    FLUSUBTYPE=$(ls ${sample}/*H*.fasta | cut -d '/' -f2 | cut -d '.' -f1 | cut -d '_' -f1,3 | sort -u)
    FLUTYPE=$(ls ${sample}/*H*.fasta | cut -d '/' -f2 | cut -d '.' -f1 | cut -d '_' -f1 | sort -u)
    mkdir -p $FLUSUBTYPE
    ls ${sample}/amended_consensus/*.fa | cut -d '_' -f3 | cut -d '.' -f1 | while read fragment; do
        if [ $fragment == 1 ]; then
            if [ $FLUTYPE == "B" ]; then
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_1/_PB1/' >> ${FLUSUBTYPE}/B_PB1.txt
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_1/_PB1/' >> all_samples_completo.txt
            else
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_1/_PB2/' >> ${FLUSUBTYPE}/${FLUTYPE}_PB2.txt
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_1/_PB2/' >> all_samples_completo.txt
            fi
        elif [ $fragment == 2 ]; then
            if [ $FLUTYPE == "B" ]; then
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_2/_PB2/' >> ${FLUSUBTYPE}/B_PB2.txt
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_2/_PB2/' >> all_samples_completo.txt
            else
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_2/_PB1/' >> ${FLUSUBTYPE}/${FLUTYPE}_PB1.txt
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_2/_PB1/' >> all_samples_completo.txt
            fi
        elif [ $fragment == 3 ]; then
            if [ $FLUTYPE == "B" ] || [ $FLUTYPE == "A" ]; then
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_3/_PA/' >> ${FLUSUBTYPE}/${FLUTYPE}_PA.txt
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_3/_PA/' >> all_samples_completo.txt
            else
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_3/_P3/' >> ${FLUSUBTYPE}/${FLUTYPE}_P3.txt
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_3/_P3/' >> all_samples_completo.txt
            fi
        elif [ $fragment == 4 ]; then
            if [ $FLUTYPE == "B" ] || [ $FLUTYPE == "A" ]; then
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_4/_HA/' >> ${FLUSUBTYPE}/${FLUTYPE}_HA.txt
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_4/_HA/' >> all_samples_completo.txt
            else
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_4/_HE/' >> ${FLUSUBTYPE}/${FLUTYPE}_HE.txt
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_4/_HE/' >> all_samples_completo.txt
            fi
        elif [ $fragment == 5 ]; then
            cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_5/_NP/' >> ${FLUSUBTYPE}/${FLUTYPE}_NP.txt
            cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_5/_NP/' >> all_samples_completo.txt
        elif [ $fragment == 6 ]; then
            if [ $FLUTYPE == "B" ] || [ $FLUTYPE == "A" ]; then
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_6/_NA/' >> ${FLUSUBTYPE}/${FLUTYPE}_NA.txt
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_6/_NA/' >> all_samples_completo.txt
            else
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_6/_MP/' >> ${FLUSUBTYPE}/${FLUTYPE}_MP.txt
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_6/_MP/' >> all_samples_completo.txt
            fi
        elif [ $fragment == 7 ]; then
            if [ $FLUTYPE == "B" ] || [ $FLUTYPE == "A" ]; then
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_7/_MP/' >> ${FLUSUBTYPE}/${FLUTYPE}_MP.txt
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_7/_MP/' >> all_samples_completo.txt
            else
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_7/_NS/' >> ${FLUSUBTYPE}/${FLUTYPE}_NS.txt
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_7/_NS/' >> all_samples_completo.txt
            fi
        elif [ $fragment == 8 ]; then
            cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_8/_NS/' >> ${FLUSUBTYPE}/${FLUTYPE}_NS.txt
            cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/-/\//g' | sed 's/_8/_NS/' >> all_samples_completo.txt
        else
            echo "The sample $sample has a segment with number $fragment, but I don't know which segment it is."
        fi
    done
done
