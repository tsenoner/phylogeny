import argparse
import os


def read_fasta(file_path):
    """Read a FASTA file and return a dictionary of sequences and headers."""
    sequences = {}
    header = None
    sequence = ""
    try:
        with open(file_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith(">"):
                    if header:
                        sequences[header] = sequence
                    header = line[1:]
                    sequence = ""
                else:
                    sequence += line
            if header:
                sequences[header] = sequence
        return sequences
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        exit(1)


def write_fasta(file_path, sequences):
    """Write sequences to a FASTA file."""
    try:
        with open(file_path, "w") as f:
            for header, sequence in sequences.items():
                f.write(f">{header}\n{sequence}\n")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


def merge_and_remove_duplicates(fasta_files):
    """Merge multiple FASTA files and remove duplicates."""
    all_sequences = {}
    removed_duplicates = set()

    for fasta_file in fasta_files:
        sequences = read_fasta(fasta_file)
        for header, sequence in sequences.items():
            if sequence in all_sequences.values():
                removed_duplicates.add((fasta_file, header))
            else:
                all_sequences[header] = sequence

    return all_sequences, removed_duplicates


def main(fasta_files, output):
    # Validate input files
    for fasta_file in fasta_files:
        if not os.path.exists(fasta_file):
            print(f"Error: File {fasta_file} does not exist.")
            exit(1)

    unique_sequences, removed_duplicates = merge_and_remove_duplicates(fasta_files)

    write_fasta(output, unique_sequences)

    print("Removed duplicates:")
    for fasta_file, header in removed_duplicates:
        print(f"File: {fasta_file}, Header: {header}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge multiple FASTA files into one, removing duplicates."
    )
    parser.add_argument("fasta_files", nargs="+", help="Input FASTA files to merge.")
    parser.add_argument("--output", required=True, help="Output FASTA file.")
    args = parser.parse_args()

    main(args.fasta_files, args.output)
