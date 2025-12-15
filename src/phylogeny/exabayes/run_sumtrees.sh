#!/bin/bash

# Description:
# This script automates the process of running 'sumtrees.py' to consense phylogenetic trees from multiple run files.
# It handles various operations like calculating the burn-in, processing run files, and monitoring the progress of 'sumtrees.py'.
# The script estimates the remaining time for the process to complete and provides real-time progress updates.
# It supports customizable options for the burn-in percentage, output file, minimum split frequency, and log file path.
# Users can choose to clean up intermediate files and also perform a dry run to see the commands without execution.

# Usage:
# Run the script with required and optional arguments to process phylogenetic tree files.
# Example: ./scriptname.sh -f /path/to/runfile -b 0.25 -o output.nexus -s 0.5 -l progress.log


# Load Conda environment
source /mnt/lsf-nas-1/os-shared/anaconda3/etc/profile.d/conda.sh
conda activate senoner_prot_hunt

# Enable strict error handling
set -e
set -u
set -o pipefail

# -------------------- DEFAULT VALUES --------------------
burn_in_percentage=0.25
min_split_freq=0.5
cleanup=true
dry_run=false

# -------------------- FUNCTIONS --------------------
# Function to display usage information
usage() {
    echo "Usage: $0 -f <file_path> [-b <burn_in_percentage>] [-o <output_file>] [-s <min_split_freq>] [-l <log_file>] [-n] [-d] [-h]"
    echo "  -f: Path to the run file. E.g. /path/to/ExaBayes_topologies.run-0.<identifier>"
    echo "  -b: Burn-in percentage (default is $burn_in_percentage)"
    echo "  -o: Output filename (default is '<base_path>/<identifier>.nexus')"
    echo "  -s: Minimum split frequency (default is $min_split_freq)"
    echo "  -n: No cleanup; retain created files"
    echo "  -l: Path to the log file where 'sumtrees.py' progress is saved (default is '<base_path>/<identifier>.log')"
    echo "  -d: Dry run; print the command without executing"
    echo "  -h: Display this help and exit"
    exit 1
}

# Function to parse command-line options
parse_args() {
    while getopts 'f:b:o:s:l:ndh' flag; do
        case "${flag}" in
        f) file_path="${OPTARG}" ;;
        b) burn_in_percentage="${OPTARG}" ;;
        o) output_file="${OPTARG}" ;;
        s) min_split_freq="${OPTARG}" ;;
        l) log_file="${OPTARG}" ;;
        n) cleanup=false ;;
        d) dry_run=true ;;
        h) usage ;;
        *) usage ;;
        esac
    done
}

# Function to check command dependencies
check_cmd_dependencies() {
    for cmd in bc grep sed sumtrees.py; do
        if ! command -v $cmd &>/dev/null; then
            echo "Error: Required command '$cmd' is not installed."
            exit 1
        fi
    done
}

# Function to validate arguments
validate_args() {
    local file_path=$1
    local burn_in_percentage=$2

    # Validate file path
    if [ -z "$file_path" ]; then
        echo "Error: File path is required."
        usage
    elif [ ! -f "$file_path" ]; then
        echo "Error: File not found at '$file_path'."
        usage
    fi

    # Validate burn-in percentage
    if ! [[ $burn_in_percentage =~ ^0(\.[0-9]+)?$|^1(\.0+)?$ ]]; then
        echo "Error: Burn-in percentage must be a number between 0 and 1."
        usage
    fi
}

# Function to calculate burn-in
calculate_burn_in() {
    local count=$1
    echo "scale=0; ($count * $burn_in_percentage + 0.99)/1" | bc
}

# Function to process run files
process_run_files() {
    local base_path=$1
    local file_extension=$2
    local dry_run=$3
    local run
    for run in "${runs[@]}"; do
        local run_nr=$(basename "$run" | sed -n 's/.*run-\([0-9]*\).*/\1/p')
        local new_file="${base_path}/${file_extension}_run-${run_nr}.nexus"
        processed_runs+=("$new_file")

        if [ "$dry_run" = false ] && [ ! -f "$new_file" ]; then
            # Replace 'tree gen.X.{0} =' with 'tree gen.X. ='
            sed '/^\ttree/s/{0}//' "$run" > "$new_file"
            echo "Created modified file: $new_file"
        fi
    done
}

# Function to estimate and display remaining time
monitor_progress() {
    local pid=$1
    local start_time=$2
    local total_trees=$3
    local temp_file=$4
    local -a last_offsets=(0 0 0)
    local -a last_times=($start_time $start_time $start_time)
    local current_time
    local current_offset
    local progress
    local average_rate
    local remaining_time

    while kill -0 "$pid" 2>/dev/null; do
        sleep 60  # Check every 60 seconds

        # Read the latest progress from the temp file
        progress=$(tail -n 10 "$temp_file" | grep 'tree at offset' | tail -1)
        current_offset=$(echo "$progress" | grep -oP 'tree at offset \K\d+')

        if [[ "$current_offset" != "" && "$current_offset" -ne "${last_offsets[2]}" ]]; then
            current_time=$(date +%s)

            # Update the history of offsets and times
            last_offsets=("${last_offsets[1]}" "${last_offsets[2]}" "$current_offset")
            last_times=("${last_times[1]}" "${last_times[2]}" "$current_time")

            # Calculate average rate (offset change per second)
            local offset_change=$((last_offsets[2] - last_offsets[0]))
            local time_change=$((last_times[2] - last_times[0]))
            if [[ $time_change -gt 0 ]]; then
                average_rate=$(echo "$offset_change / $time_change" | bc -l)
                remaining_time=$(echo "($total_trees - ${last_offsets[2]}) / $average_rate" | bc -l)

                # Convert remaining_time to days, hours, minutes, and seconds
                local days=$(echo "$remaining_time / 86400" | bc)
                local hours=$(echo "($remaining_time % 86400) / 3600" | bc)
                local minutes=$(echo "($remaining_time % 3600) / 60" | bc)
                local seconds=$(echo "$remaining_time % 60" | bc)
                # Convert seconds to an integer
                seconds=$(printf "%.0f" "$seconds")

                # Format the time string
                local time_string=""
                [[ $days -gt 0 ]] && time_string+="${days}d "
                [[ $hours -gt 0 || -n "$time_string" ]] && time_string+="${hours}h "
                [[ $minutes -gt 0 || -n "$time_string" ]] && time_string+="${minutes}m "
                time_string+="${seconds}s"

                # Get the current time in a readable format
                local current_time=$(date +"%Y-%m-%d %H:%M:%S")

                echo "$current_time - ${last_offsets[2]} / $total_trees trees. ETA: $time_string"
            fi
        fi
    done
}


# Function to run sumtrees.py and monitor progress
run_consense() {
    local burn_in_trees=$1
    local min_split_freq=$2
    local output_file=$3
    local log_file=$4
    local dry_run=$5
    shift 5
    local run_arr=("$@")

    sumtrees_command="sumtrees.py -i nexus -b $burn_in_trees -f $min_split_freq -p -s consensus -e median-length -o $output_file -F nexus --no-meta-comments -M ${run_arr[@]} -r"

    if [ "$dry_run" = true ]; then
        echo "Dry run: $sumtrees_command"
    else
        # Start sumtrees.py in the background and redirect output to log file
        echo "Running command: $sumtrees_command"
        eval $sumtrees_command > "$log_file" 2>&1 &
        local sumtrees_pid=$!

        local start_time=$(date +%s)
        monitor_progress $sumtrees_pid $start_time $total_trees $log_file

        wait $sumtrees_pid
        local end_time=$(date +%s)
        local total_execution_time=$((end_time - start_time))
        echo "Total execution time: $total_execution_time seconds"

        if [ "$cleanup" = true ]; then
            cleanup
        else
            echo "Cleanup skipped; created files retained."
        fi
    fi
}

# Function to clean up created files
cleanup() {
    if [ "$dry_run" = false ]; then
        echo "Cleaning up created files..."
        for file in "${processed_runs[@]}"; do
            rm -f "$file"
        done
    fi
}

# -------------------- MAIN --------------------
# prepare arguments and check if everything required is available.
parse_args "$@"
check_cmd_dependencies
validate_args $file_path $burn_in_percentage

# get all runs
base_path=$(dirname "$file_path")
file_extension="${file_path##*.}"
file_pattern=$(basename "$file_path" | sed 's/run-[0-9]*/run-*/')

# Find and process run files
runs=($(ls $base_path/$file_pattern 2>/dev/null))
if [ ${#runs[@]} -eq 0 ]; then
    echo "Error: No run files found matching the pattern."
    exit 1
fi

# Calculate total number of trees and burn-in trees
total_trees=$(grep -c $'^\ttree' "${runs[0]}")
burn_in_trees=$(calculate_burn_in $total_trees)

# Remove the `{0}` in every tree line
# declare -a processed_runs
processed_runs=()
process_run_files $base_path $file_extension $dry_run

# Run the consense operation
output_file="${base_path}/${file_extension}.nexus"
log_file="${base_path}/${file_extension}.log"
run_consense $burn_in_trees $min_split_freq $output_file $log_file $dry_run ${processed_runs[@]}