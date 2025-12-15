#!/bin/bash
#SBATCH --job-name=exabayes
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --chdir=/home/tobias/projects/animal_venoms/cap
#SBATCH --ntasks=16
#SBATCH --cpus-per-task=1
#SBATCH --nodes=1
#SBATCH --mem=64G
#SBATCH --partition=month-long-cpu

# Set the name of your phylip file
PHY_FILE=processed/CAP_Aculeata_240718.phy

# Extract the stem of the phylip file name
PHY_STEM=$(basename "$PHY_FILE" .phy)

# Create output directory
OUTPUT_DIR="exabayes/${PHY_STEM}"
mkdir -p "$OUTPUT_DIR"

# Create a config file for ExaBayes with updated settings
cat << EOF > "$OUTPUT_DIR/config.nex"
#NEXUS

begin RUN;
 [ RUN PARAMETERS ]
 numRuns 4
 numGen 200000

 [ MCMCMC ]
 numCoupledChains 4

 [ CONVERGENCE ]
 sdsfConvergence 0.001
end;
EOF

# Run ExaBayes
srun exabayes -f "$PHY_FILE" -m DNA -s 42 -n "${PHY_STEM}" -c "$OUTPUT_DIR/config.nex" -R 4 -C 4 -M 0 -w "$OUTPUT_DIR"

# Optionally, run some post-processing (uncomment if needed)
# cd "$OUTPUT_DIR"
# consense -f ExaBayes_topologies.${PHY_STEM}_run.* -n consensus
# postProcParam -f ExaBayes_parameters.${PHY_STEM}_run.* -n params