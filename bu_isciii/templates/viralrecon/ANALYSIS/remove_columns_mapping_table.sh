#!/bin/bash

output_file=$(echo processed_mapping_illumina_$(date '+%Y%m%d').tab)

# Removal of the first three columns of the mapping illumina tab file
cut --complement -f1-3 *.tab > output_file

# Success message
if [ $? -eq 0 ]; then
    echo "Successfully removed the first three columns from the mapping_illumina file and saved the output to $output_file."
else
    echo "An error occurred."
fi
