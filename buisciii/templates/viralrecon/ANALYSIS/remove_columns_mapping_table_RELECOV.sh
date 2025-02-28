#!/bin/bash

output_file=$(echo processed_mapping_illumina_$(date '+%Y%m%d').tab)

# Removal of the first three columns of the mapping illumina tab file
cut --complement -f1-3 mapping_*.tab > $output_file
mv $output_file mapping_illumina_$(date '+%Y%m%d').tab

# Success message
if [ $? -eq 0 ]; then
    echo "Successfully removed the first three columns from the mapping_illumina file."
else
    echo "An error occurred."
fi
