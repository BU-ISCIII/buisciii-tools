find . -type f -name "variants_long_table.csv" | cut -d '/' -f1,2,3,4 | while read in
do
    mv ${in}/variants_long_table.csv ${in}/variants_long_table_dups.csv
    head -n1 ${in}/variants_long_table_dups.csv > ${in}/variants_long_table.csv
    grep -v 'SAMPLE' ${in}/variants_long_table_dups.csv | sort -u >> ${in}/variants_long_table.csv
done
