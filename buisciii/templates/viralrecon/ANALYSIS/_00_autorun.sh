
# This script automates the succesive execution of multiple sbatch for viralrecon pipeline.

echo_bold() { echo -e "\e[1;37m$1\e[0m"; }
echo_red() { echo -e "\e[31m$1\e[0m"; }
echo_green() { echo -e "\e[32m$1\e[0m"; }

mkdir logs
date_str=$(date +"%Y%m%d")

default_nextflow_version="25.04.6"
default_singularity="singularity"

# Lets the user pick a specific module version from `module avail`, or just
# press Enter to accept the default (latest singularity / Nextflow 25.04.6).
select_module_version() {
    local search_pattern="$1" default_choice="$2" label="$3"
    local versions
    mapfile -t versions < <(module -t avail "$search_pattern" 2>&1 | grep -E "^${search_pattern}(/|$)" | sed 's/([^)]*)$//' | sort -Vu)

    if [[ ${#versions[@]} -eq 0 ]]; then
        echo_red "No ${label} modules found via 'module avail'; using default: ${default_choice}"
        echo "$default_choice"
        return
    fi

    echo_bold "Available ${label} versions:" >&2
    PS3="Select ${label} version [Enter = default: ${default_choice}]: "
    local choice
    select choice in "${versions[@]}"; do
        if [[ -z "$REPLY" ]]; then
            choice="$default_choice"
        fi
        if [[ -n "$choice" ]]; then
            break
        fi
        echo_red "Invalid selection, try again." >&2
    done
    echo "$choice"
}

nextflow_version=$(select_module_version "Nextflow" "Nextflow/${default_nextflow_version}" "Nextflow")
singularity_module=$(select_module_version "singularity" "$default_singularity" "Singularity")

module purge
module load "$nextflow_version" "$singularity_module"
modules_loaded=$(module -t list 2>&1 | grep -E "Nextflow|singularity")
if [[ $(echo "$modules_loaded" | grep -c -E "Nextflow|singularity") -eq 2 ]]; then
    echo_green "${nextflow_version} and ${singularity_module} modules successfully loaded."
else
    echo_red "Modules not loaded correctly. Exiting..."
    exit 1
fi

ls _01* | while read in; do
    ref=$(echo "$in" | sed 's/_viralrecon.sh//' | cut -d "_" -f4-)
    bash ${in}
    echo_bold "${ref} launched!"
    echo -e "$(date +"%Y-%m-%d_%H-%M-%S")\t-\t${ref} launched!" >> logs/viralrecon_autorun_${date_str}.log
    waiting_message=("Processing ${ref}.  " "Processing ${ref}.. " "Processing ${ref}...")
    index=0
    while :; do
        echo -ne "\r${waiting_message[$index]}"
        index=$(( (index + 1) % 3 ))
        if grep -q "Succeeded" "${ref}_${date_str}_viralrecon.log" 2>/dev/null || [[ $(grep -c "Pipeline completed successfully" "${ref}_${date_str}_viralrecon.log" 2>/dev/null) -ge 2 ]]; then
            echo_green "\n${ref} finished succesfully!"
            echo -e "$(date +"%Y-%m-%d_%H-%M-%S")\t-\t${ref} finished succesfully!" >> logs/viralrecon_autorun_${date_str}.log
            break
        elif grep -q "CANCELLED" "${ref}_${date_str}_viralrecon.log" 2>/dev/null; then
            echo_red "\n${ref} cancelled! Exiting."
            echo -e "$(date +"%Y-%m-%d_%H-%M-%S")\t-\t${ref} cancelled! Exiting" >> logs/viralrecon_autorun_${date_str}.log
            exit 1
        elif grep -q "nextflow.log" "${ref}_${date_str}_viralrecon.log" 2>/dev/null; then
            error_message=$(grep -m1 "ERROR" "${ref}_${date_str}_viralrecon.log")
            echo_red "\n$error_message"
            echo_red "${ref} failed!"
            echo -e "$(date +"%Y-%m-%d_%H-%M-%S")\t-\t${error_message}" >> logs/viralrecon_autorun_${date_str}.log
            echo -e "$(date +"%Y-%m-%d_%H-%M-%S")\t-\t${ref} failed!" >> logs/viralrecon_autorun_${date_str}.log
            break
        else
        sleep 1
        fi
    done
    echo
    sleep 15
done
echo_bold "Autorun execution FINISHED!"