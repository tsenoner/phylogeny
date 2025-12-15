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

# Check if the directory exists
if [ -d "$CURRENT_DIR" ]; then
    cd "$CURRENT_DIR"

    # Run consense
    consense -f ExaBayes_topologies.run-*.${DIR_STEM} -n ${DIR_STEM} -b 0.25 -t MRE

    echo "Consense completed for $DIR_STEM"
else
    echo "Directory $CURRENT_DIR does not exist. Skipping this job."
    exit 0
fi
