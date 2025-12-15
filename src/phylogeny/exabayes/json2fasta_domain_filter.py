#!/usr/bin/env python3
"""
Created on:  Thu 21 Sep 2023 17:43:29
Description: This script extracts specified domain sequences from a given JSON file
             and writes them to an output FASTA file. If no domain name is specified,
             it will include all sequences that do not contain fragment types.
Usage:       python json2fasta_domain_filter.py -j <input_JSON_file> -o <output_FASTA_file> [-d <domain_name>]
Options:
             -j, --json_file: Path to the input JSON file
             -o, --output_fasta: Path to the output FASTA file
             -d, --domain_name: (Optional) The name of the domain to extract
             -v, --verbose: Enable verbose logging
@author: tsenoner
"""

import argparse
import json
import logging


class Config:
    """Configuration constants."""

    NON_ADJACENT_RESIDUES = "Non-adjacent residues"
    NON_TERMINAL_RESIDUE = "Non-terminal residue"
    FRAGMENT_TYPES = [NON_ADJACENT_RESIDUES, NON_TERMINAL_RESIDUE]


def configure_logger(verbose: bool):
    """Configures logging settings."""
    log_level = logging.INFO if verbose else logging.ERROR
    logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)


def read_json(
    file_path: str,
) -> dict[str, str | list[dict[str, str | int]]] | None:
    """Read a JSON file and return its contents as a dictionary."""
    try:
        with open(file_path) as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON file: {file_path}")
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
    return None


def write_to_fasta(file_path: str, header_sequences: list[str]) -> None:
    """Writes sequences to a FASTA file."""
    with open(file_path, "w") as f:
        f.write("\n".join(header_sequences))


def has_fragments(entry: dict) -> bool:
    """Check if entry has fragments."""
    return any(
        feature["type"] in Config.FRAGMENT_TYPES for feature in entry["features"]
    )


def extract_fragments(
    entry: dict[str, list[dict[str, str]]],
) -> list[dict[str, str | int]]:
    """Extract fragment information from an entry."""
    return [
        {
            "type": feature.get("type"),
            "start": int(feature["location"]["start"]["value"]),
            "end": int(feature["location"]["end"]["value"]),
        }
        for feature in entry.get("features", [])
        if feature.get("type") in Config.FRAGMENT_TYPES
    ]


def extract_sequences(entry: dict, domain_name: str | None = None) -> list[str]:
    """Extracts sequences based on the given domain name or the absence of fragments."""
    if domain_name:
        return extract_domain(entry, domain_name)
    else:
        entry_id = entry.get("primaryAccession")
        if has_fragments(entry):
            logging.warning(f"Skipped {entry_id} due to fragments.")
        else:
            sequence = entry.get("sequence", {}).get("value")
            return [f">{entry_id}\n{sequence}"] if entry_id and sequence else []
    return []


def extract_domain(entry: dict, domain_name: str | None = None) -> list[str]:
    """Extracts specified domains and logs conflicts."""
    extracted_domains = []
    entry_id = entry.get("primaryAccession")
    sequence = entry.get("sequence", {}).get("value")

    if not entry_id or not sequence:
        logging.warning("Incomplete entry data. Skipping entry.")
        return extracted_domains

    for feature in entry.get("features", []):
        if feature.get("type") == "Domain" and domain_name in feature.get(
            "description", ""
        ):
            start = int(feature["location"]["start"]["value"])
            end = int(feature["location"]["end"]["value"])
            full_domain_name = feature.get("description")

            conflicts = [
                f"{frag['type']} (start: {frag['start']}, end: {frag['end']})"
                for frag in extract_fragments(entry)
                if frag["start"] <= end and frag["end"] >= start
            ]
            if conflicts:
                logging.warning(
                    f"Entry {entry_id}: {full_domain_name} (range:"
                    f" {start}-{end}): {', '.join(conflicts)}"
                )
                continue

            extracted_domains.append(
                f">{entry_id}_{full_domain_name}\n{sequence[start - 1 : end]}"
            )

    return extracted_domains


def get_command_line_args() -> argparse.Namespace:
    """Parse and return command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Extract sequences/domains from a UniProt JSON file and write to a"
            " FASTA file."
        )
    )
    parser.add_argument(
        "-j",
        "--json_file",
        type=str,
        required=True,
        help="Path to the input JSON file.",
    )
    parser.add_argument(
        "-o",
        "--output_fasta",
        type=str,
        required=True,
        help="Path to the output FASTA file.",
    )
    parser.add_argument(
        "-d",
        "--domain_name",
        type=str,
        help=(
            "The name of the domain to extract. If not provided, extracts all"
            " sequences without fragments."
        ),
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging."
    )
    return parser.parse_args()


def main(
    json_file: str,
    output_fasta: str,
    domain_name: str | None = None,
    verbose: bool = False,
) -> None:
    """Main function."""
    configure_logger(verbose)
    json_data = read_json(json_file)
    if json_data is None:
        return

    extracted_fasta_sequences = []
    for entry in json_data.get("results", []):
        extracted_fasta_sequences.extend(extract_sequences(entry, domain_name))

    write_to_fasta(output_fasta, extracted_fasta_sequences)


if __name__ == "__main__":
    args = get_command_line_args()
    main(args.json_file, args.output_fasta, args.domain_name, args.verbose)
