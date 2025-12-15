#!/usr/bin/env python3
"""
Created on:  Thu 31 Oct 2023 23:40:18
Description: This script runs the MAFFT alignment algorithm on a given FASTA file and outputs the result in PHYLIP (.phy) format.
             The script supports both local and global alignment methods. The output path is optional; if not provided, it defaults to
             the input path with a .phy extension.
Usage:       python run_mafft.py -i /path/to/input.fasta [-o /path/to/output.phy] [-a local]
@author:     tsenoner
"""

import argparse
import os
import re
from pathlib import Path, PosixPath


# Function to run MAFFT
def run_mafft(
    input_fasta: PosixPath, alignment_type: str = "local", verbose: bool = False
) -> PosixPath:
    if alignment_type not in ["local", "global"]:
        raise Exception(f"Unknown alignment method: `{alignment_type}`")

    aligned_fasta = input_fasta.with_name(f"{input_fasta.stem}_aln.fasta")
    quiet_flag = "--quiet" if not verbose else ""

    command = (
        f"linsi {quiet_flag} {input_fasta} > {aligned_fasta}"
        if alignment_type == "local"
        else f"ginsi --distout {quiet_flag} {input_fasta} > {aligned_fasta}"
    )
    os.system(command)

    return aligned_fasta


# Function to convert FASTA to PHYLIP (.phy) format
def fasta_to_relaxed_phy_aligned(
    input_fasta: str, output_phy: str, lalign: bool = True
):
    sequences = {}
    special_chars = r"[ \(\):;,\[\]/\+']"
    with open(input_fasta) as f:
        sequence_name = None
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                sequence_name = line[1:]
                sequence_name = re.sub(special_chars, "_", sequence_name)
                sequences[sequence_name] = ""
            elif sequence_name:
                sequences[sequence_name] += line
            else:
                raise ValueError("Invalid FASTA format: sequence without a name.")

    if any(
        len(seq) != len(next(iter(sequences.values()))) for seq in sequences.values()
    ):
        raise ValueError("All sequences must have the same length.")

    with open(output_phy, "w") as f:
        f.write(f"{len(sequences)} {len(next(iter(sequences.values())))}\n")
        for name, sequence in sequences.items():
            padded_name = (
                name.ljust(max(len(name) for name in sequences) + 1) if lalign else name
            )
            f.write(f"{padded_name} {sequence}\n")


# Main pipeline function
def pipeline_mafft(
    input_fasta: str,
    output_phy: str,
    alignment_type: str = "local",
    verbose: bool = False,
) -> None:
    if not Path(input_fasta).exists():
        raise FileNotFoundError(f"Input file {input_fasta} does not exist.")

    aligned_fasta = run_mafft(
        input_fasta=Path(input_fasta),
        alignment_type=alignment_type,
        verbose=verbose,
    )
    fasta_to_relaxed_phy_aligned(input_fasta=str(aligned_fasta), output_phy=output_phy)


# Argparse for command-line options
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run MAFFT and convert FASTA to PHYLIP (.phy) format."
    )
    parser.add_argument(
        "-i", "--input", required=True, help="Path to the input FASTA file."
    )
    parser.add_argument(
        "-o",
        "--output",
        help=(
            "Path to the output PHYLIP (.phy) file. Optional; defaults to input"
            " path with .phy extension."
        ),
    )
    parser.add_argument(
        "-a",
        "--alignment",
        choices=["local", "global"],
        default="local",
        help="Alignment method to use. Default is 'local'.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print the output of the MAFFT process.",
    )

    args = parser.parse_args()
    output_phy = args.output if args.output else Path(args.input).with_suffix(".phy")

    pipeline_mafft(
        input_fasta=args.input,
        output_phy=output_phy,
        alignment_type=args.alignment,
        verbose=args.verbose,
    )
