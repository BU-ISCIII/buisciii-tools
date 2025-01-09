#CLEAN
if test -f all_samples_completo.txt; then rm all_samples_completo.txt; fi
if test -d A; then rm -rf A; fi
if test -d B; then rm -rf B; fi
if test -d AD; then rm -rf AD; fi
if test -d BD; then rm -rf BD; fi

cat ../samples_id.txt | while read sample; do
    RSVTYPE=$(ls ${sample}/*.fasta | cut -d '/' -f2 | cut -d '.' -f1 | cut -d '_' -f2 | sort -u)
    mkdir -p $RSVTYPE
    cat ${sample}/amended_consensus/${sample}.fa | sed 's/-/\//g' | sed "s/^>\([^/]*\)/>${RSVTYPE}\/\1/" | tee -a ${RSVTYPE}/${RSVTYPE}.txt all_samples_completo.txt > /dev/null
done
