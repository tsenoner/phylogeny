#!/bin/bash
#Github: https://github.com/inbalpaz/CLANS
# conda activate clans_2_0


# Create the out directory if it doesn't exist

OUT_DIR="out/clans"
mkdir -p ${OUT_DIR}

# Loop from 1 to 100
for num in {1..100}; do
    output_file="${OUT_DIR}/100k_$num.clans"

    # If the output file already exists, skip this iteration
    if [ -f "$output_file" ]; then
        echo "Output file $output_file already exists. Skipping..."
        continue
    fi

    cmd="python -m clans -nogui -load data/ICK/240116_xibalbin/ick.clans -dorounds 100000 -saveto $output_file -cluster2d -pval 1e-$num"
    echo "Executing: $cmd"
    echo "----------"
    $cmd
done