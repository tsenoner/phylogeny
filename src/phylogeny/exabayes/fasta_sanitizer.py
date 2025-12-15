#!/usr/bin/env python3
"""
Created on:  Thu 21 Sep 2023 20:11:18
Description: This script sanitizes FASTA files by cleaning headers and removing
             sequences with ambiguous residues.
Usage:       python fasta_sanitizer.py -f <fasta_file> [-v]
@author:     tsenoner
"""

import argparse
import logging
import re
from pathlib import Path

from pyfaidx import Fasta

# Constants
HEADER_CLEANER = re.compile(r"[\W\s]")
STANDARD_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY-")


def get_command_line_args() -> argparse.Namespace:
    """Parse and return command-line arguments."""
    parser = argparse.ArgumentParser(description="Sanitize FASTA files.")
    parser.add_argument(
        "-f",
        "--fasta_file",
        type=Path,
        required=True,
        help="Path to the FASTA file.",
    )
    parser.add_argument(
        "-d",
        "--remove_dash",
        required=False,
        action="store_true",
        default=False,
        help="Remove dashes in sequence",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging."
    )
    return parser.parse_args()


def configure_logging(verbose: bool) -> None:
    """Configure logging settings."""
    level = logging.INFO if verbose else logging.ERROR
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def clean_fasta_header(header: str) -> str:
    """Clean the FASTA header by replacing all non-alphanumeric characters and spaces with underscores."""
    return HEADER_CLEANER.sub("_", header)


def has_ambiguous_residues(sequence: str) -> tuple[bool, str]:
    """Check if a sequence contains ambiguous residues."""
    ambiguous_residues = set(sequence) - STANDARD_AMINO_ACIDS
    return bool(ambiguous_residues), ",".join(ambiguous_residues)


def read_fasta(file_path: Path) -> list[tuple[str, str]]:
    """Read FASTA entries from a file and return them as a list of (header, sequence) tuples."""
    with Fasta(str(file_path), read_long_names=True) as fasta_seq:
        return [(str(entry.name), str(entry)) for entry in fasta_seq]


def write_fasta(file_path: Path, entries: list[tuple[str, str]]) -> None:
    """Write a list of (header, sequence) tuples to a FASTA file."""
    with file_path.open("w") as outfile:
        for header, seq in entries:
            outfile.write(f">{header}\n{seq}\n")


def process_fasta(file_path: Path, remove_dash: bool) -> None:
    """Sanitize the FASTA file by cleaning headers and removing entries with ambiguous residues."""
    sanitized_entries = []

    for header, sequence in read_fasta(file_path):
        clean_header = clean_fasta_header(header)
        if remove_dash:
            sequence = sequence.replace("-", "")
        has_ambiguity, ambiguous_str = has_ambiguous_residues(sequence)

        if has_ambiguity:
            logging.warning(
                f"Removed '{header}' due to ambiguous residues: {ambiguous_str}."
            )
            continue

        sanitized_entries.append((clean_header, sequence))

    write_fasta(file_path, sanitized_entries)

    # Remove generated .fai index file
    fai_file_path = file_path.with_suffix(".fasta.fai")
    if fai_file_path.exists():
        fai_file_path.unlink()
        logging.info(f"Removed {fai_file_path}")


def main(file_path: Path, remove_dash: bool, verbose: bool) -> None:
    configure_logging(verbose)
    process_fasta(file_path, remove_dash)


if __name__ == "__main__":
    args = get_command_line_args()
    main(args.fasta_file, args.remove_dash, args.verbose)
