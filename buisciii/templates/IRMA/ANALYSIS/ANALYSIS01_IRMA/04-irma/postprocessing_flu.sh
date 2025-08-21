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
	echo $sample
    FLUSUBTYPE=$(grep -w ${sample} irma_stats_flu.txt | cut -f5 | cut -d '_' -f1,2)
    FLUTYPE=$(grep -w ${sample} irma_stats_flu.txt | cut -f5 | cut -d '_' -f1)
	valid_sample_name=0
	if [ $(echo "${sample}" | grep -o "-" | wc -l) == 3 ]; then
		# check and validate each item
		echo "sample name has three fields. Checking..."
		if [[ ' A B C D ' =~ "$(echo ${sample} | cut -d '-' -f 1)" ]]; then
			valid_sample_name=$((${valid_sample_name} + 1))
			printf "Flu type valid in sample name.\n"
		fi
		if [[ "$(echo ${sample} | cut -d '-' -f 4)" =~ ^[0-9]{4}$ ]]; then
			valid_sample_name=$((${valid_sample_name} + 1 ))
			printf "Year in sample name.\n"
		fi
	fi
	if [[ $valid_sample_name == 2 ]]; then
		sample_name=$(echo ${sample} | sed 's/-/\//g')
	else
		printf "Sample name could not be obtained from sample id. Looking for json data in DOC...\n"
		# expand glob to nothing if nothing matches
		shopt -s nullglob
		json_files=(../../../DOC/*_validate_batch_*.json)
		# disable and keep glob expansion as the default
		shopt -u nullglob

		if [[ ${#json_files[@]} -eq 1 ]]; then
			printf "json found ${json_files[0]}\n"
			# extract unique_sample_id
			unique_sample_id="${sample##*_}"
			echo $unique_sample_id
			IFS=$'\t' read -r collection_date state < <(
				jq -r --arg u "$unique_sample_id" '
					first(
						.[]
						| select(.unique_sample_id == $u)
						| [.sample_collection_date, .geo_loc_state]
						| @tsv
					)
				' "${json_files[0]}"
			)

			year=$(echo ${collection_date} | cut -d "-" -f 1)
			state=$(echo ${state} | tr ' ' '-')
			sample_name="${FLUTYPE}/${state}/${sample}/${year}"

		elif [[ ${#json_files[@]} -eq 0 ]]; then
			printf "No json found, using sample_id as it is for fasta header\n"
			sample_name="${FLUTYPE}/${sample}"
		else
			printf "More than one json file found, aborting"
			exit 1
		fi
	fi

	printf "Setting sample_name as ${sample_name}\n"

    if [ -z $FLUTYPE ]; then
        echo "Sample ${sample} doesn't have any fragment. Skipping"
    else
        mkdir -p $FLUSUBTYPE
        # grep -o makes only to print string coincidence in this case fragment number
        ls ${sample}/amended_consensus/*.fa | grep -oP '[0-9+](?=\.fa$)' | while read fragment; do
            if [ $fragment == 1 ]; then
                if [ $FLUTYPE == "B" ]; then
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/_1/_PB1/' | sed "s|^>.*_\([^_]\+\)$|>${sample_name}_\1|" | tee -a ${FLUSUBTYPE}/B_PB1.txt all_samples_completo.txt > /dev/null
                else
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/_1/_PB2/' | sed "s|^>.*_\([^_]\+\)$|>${sample_name}_\1|" | tee -a ${FLUSUBTYPE}/${FLUTYPE}_PB2.txt all_samples_completo.txt > /dev/null
                fi
            elif [ $fragment == 2 ]; then
                if [ $FLUTYPE == "B" ]; then
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/_2/_PB2/' | sed "s|^>.*_\([^_]\+\)$|>${sample_name}_\1|" | tee -a ${FLUSUBTYPE}/B_PB2.txt all_samples_completo.txt > /dev/null
                else
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/_2/_PB1/' | sed "s|^>.*_\([^_]\+\)$|>${sample_name}_\1|" | tee -a ${FLUSUBTYPE}/${FLUTYPE}_PB1.txt all_samples_completo.txt > /dev/null
                fi
            elif [ $fragment == 3 ]; then
                if [ $FLUTYPE == "B" ] || [ $FLUTYPE == "A" ]; then
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/_3/_PA/' | sed "s|^>.*_\([^_]\+\)$|>${sample_name}_\1|" | tee -a ${FLUSUBTYPE}/${FLUTYPE}_PA.txt all_samples_completo.txt > /dev/null
                else
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/_3/_P3/' | sed "s|^>.*_\([^_]\+\)$|>${sample_name}_\1|" | tee -a ${FLUSUBTYPE}/${FLUTYPE}_P3.txt all_samples_completo.txt > /dev/null
                fi
            elif [ $fragment == 4 ]; then
                if [ $FLUTYPE == "B" ] || [ $FLUTYPE == "A" ]; then
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/_4/_HA/' | sed "s|^>.*_\([^_]\+\)$|>${sample_name}_\1|" | tee -a ${FLUSUBTYPE}/${FLUTYPE}_HA.txt all_samples_completo.txt > /dev/null
                else
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/_4/_HE/' | sed "s|^>.*_\([^_]\+\)$|>${sample_name}_\1|" | tee -a ${FLUSUBTYPE}/${FLUTYPE}_HE.txt all_samples_completo.txt > /dev/null
                fi
            elif [ $fragment == 5 ]; then
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/_5/_NP/' | sed "s|^>.*_\([^_]\+\)$|>${sample_name}_\1|" | tee -a ${FLUSUBTYPE}/${FLUTYPE}_NP.txt all_samples_completo.txt > /dev/null
            elif [ $fragment == 6 ]; then
                if [ $FLUTYPE == "B" ] || [ $FLUTYPE == "A" ]; then
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/_6/_NA/' | sed "s|^>.*_\([^_]\+\)$|>${sample_name}_\1|" | tee -a ${FLUSUBTYPE}/${FLUTYPE}_NA.txt all_samples_completo.txt > /dev/null
                else
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/_6/_MP/' | sed "s|^>.*_\([^_]\+\)$|>${sample_name}_\1|" | tee -a ${FLUSUBTYPE}/${FLUTYPE}_MP.txt all_samples_completo.txt > /dev/null
                fi
            elif [ $fragment == 7 ]; then
                if [ $FLUTYPE == "B" ] || [ $FLUTYPE == "A" ]; then
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/_7/_MP/' | sed "s|^>.*_\([^_]\+\)$|>${sample_name}_\1|" | tee -a ${FLUSUBTYPE}/${FLUTYPE}_MP.txt all_samples_completo.txt > /dev/null
                else
                    cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/_7/_NS/' | sed "s|^>.*_\([^_]\+\)$|>${sample_name}_\1|" | tee -a ${FLUSUBTYPE}/${FLUTYPE}_NS.txt all_samples_completo.txt > /dev/null
                fi
            elif [ $fragment == 8 ]; then
                cat ${sample}/amended_consensus/*_${fragment}.fa | sed 's/_8/_NS/' | sed "s|^>.*_\([^_]\+\)$|>${sample_name}_\1|" | tee -a ${FLUSUBTYPE}/${FLUTYPE}_NS.txt all_samples_completo.txt > /dev/null
            else
                echo "The sample $sample has a segment with number $fragment, but I don't know which segment it is."
            fi
        done
    fi
done
