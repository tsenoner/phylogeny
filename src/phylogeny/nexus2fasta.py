#!/usr/bin/env python3
"""
Created on:  Thu 31 Oct 2023 20:11:18
Description: This script converts NEXUS format files to FASTA format by reading the
             sequences in the data block and writing them to a new FASTA file.
Usage:       python nexus_to_fasta_converter.py /path/to/your/nexus/file.nex
@author:     tsenoner
"""

import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)


def read_nexus_file(nexus_path: Path) -> dict:
    """Read sequences from a NEXUS file."""
    sequences = {}
    in_data_block = False

    try:
        with nexus_path.open("r") as file:
            for line in file:
                line = line.strip()

                if line.lower() == "matrix":
                    in_data_block = True
                    continue

                if line == ";":
                    in_data_block = False
                    break

                if in_data_block:
                    parts = line.split()
                    if len(parts) == 2:
                        label, sequence = parts
                        sequences[label] = sequence
        logging.info(
            f"Successfully read the NEXUS file. It contains {len(sequences)} sequences."
        )
        return sequences
    except FileNotFoundError:
        logging.error(f"File not found: {nexus_path}")
        return {}
    except Exception as e:
        logging.error(f"An error occurred while reading the file: {str(e)}")
        return {}


def write_fasta_file(fasta_path: Path, sequences: dict) -> None:
    """Write sequences to a FASTA file."""
    try:
        with fasta_path.open("w") as file:
            for label, sequence in sequences.items():
                file.write(f">{label}\n{sequence.replace('-', '')}\n")
        logging.info(
            f"Successfully converted to FASTA format. The file has been saved as {fasta_path}."
        )
    except Exception as e:
        logging.error(f"An error occurred while writing the FASTA file: {str(e)}")


def main(nexus_path: Path) -> None:
    fasta_path = nexus_path.with_suffix(".fasta")
    sequences = read_nexus_file(nexus_path)

    if sequences:
        write_fasta_file(fasta_path, sequences)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert NEXUS file to FASTA format.")
    parser.add_argument(
        "nexus_path", type=Path, help="Path to the NEXUS file to be converted."
    )

    args = parser.parse_args()

    main(args.nexus_path)
