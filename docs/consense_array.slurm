#!/bin/bash
#SBATCH --job-name=consense_array
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
#SBATCH --chdir=/home/tobias/projects/animal_venoms/cap

#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G

#SBATCH --partition=week-long-cpu
#SBATCH --array=1-16

# Get the list of ExaBayes output directories
EXABAYES_DIRS=(exabayes/*)

# Get the current directory based on the array task ID
CURRENT_DIR="${EXABAYES_DIRS[$SLURM_ARRAY_TASK_ID-1]}"

# Extract the stem of the directory name
DIR_STEM=$(basename "$CURRENT_DIR")

# Define the output file that will be produced by the consense command
OUTPUT_FILE="ExaBayes_ConsensusExtendedMajorityRuleNexus.${DIR_STEM}"

# Check if the directory exists
if [ -d "$CURRENT_DIR" ]; then
    cd "$CURRENT_DIR"

    # Check if the output file already exists
    if [ -f "$OUTPUT_FILE" ]; then
        echo "Output file $OUTPUT_FILE already exists. Skipping this job."
        exit 0
    else
        # Run consense if the output file does not exist
        consense -f ExaBayes_topologies.run-*.${DIR_STEM} -n ${DIR_STEM} -b 0.25 -t MRE

        echo "Consense completed for $DIR_STEM"
    fi
else
    echo "Directory $CURRENT_DIR does not exist. Skipping this job."
    exit 0
fi
