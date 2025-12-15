#!/usr/bin/env python3
"""
Unified alignment processing script for phylogenetic analysis.

This script processes FASTA and NEXUS alignment files and converts them to
relaxed PHYLIP format with comprehensive logging and duplicate removal.

Features:
- Handles both FASTA and NEXUS formats
- Removes duplicate sequences
- Sanitizes sequence names (removes special characters)
- Maintains directory structure or splits by sequence type (dna/protein)
- Creates detailed processing logs
- Recursive or single-directory processing

Usage:
    # Process all files in directory, keep structure
    python process_alignments.py input_dir/

    # Process recursively
    python process_alignments.py input_dir/ --recursive

    # Split output by dna/protein
    python process_alignments.py input_dir/ --split-by-type

    # Custom output directory
    python process_alignments.py input_dir/ -o output_dir/

    # No duplicate removal
    python process_alignments.py input_dir/ --keep-duplicates

Author: tsenoner
Created: 2024-12-15
"""

import argparse
import re
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path


class AlignmentProcessor:
    """Process alignment files and convert to PHYLIP format."""

    # Special characters to replace in sequence names
    SPECIAL_CHARS = r"[ \(\):;,\[\]/\+']"

    # Valid file extensions
    VALID_EXTENSIONS = {".nex", ".nexus", ".fa", ".fasta", ".fas"}

    def __init__(
        self,
        remove_duplicates: bool = True,
        align_names: bool = True,
        verbose: bool = False,
    ):
        """
        Initialize the processor.

        Args:
            remove_duplicates: Whether to remove duplicate sequences
            align_names: Whether to pad sequence names for alignment
            verbose: Enable verbose output
        """
        self.remove_duplicates = remove_duplicates
        self.align_names = align_names
        self.verbose = verbose
        self.log_entries = []

    def clean_name(self, name: str) -> str:
        """Clean sequence name by replacing special characters with underscores."""
        return re.sub(self.SPECIAL_CHARS, "_", name)

    def parse_nexus(self, content: str) -> tuple[OrderedDict, str | None]:
        """
        Parse sequences from NEXUS format.

        Args:
            content: File content as string

        Returns:
            Tuple of (sequences dict, error message)
        """
        # Extract the MATRIX block
        matrix_match = re.search(r"MATRIX\s*([\s\S]*?);", content, re.IGNORECASE)
        if not matrix_match:
            return OrderedDict(), "No MATRIX block found in NEXUS file"

        matrix_content = matrix_match.group(1)
        sequences = OrderedDict()

        for line in matrix_content.strip().split("\n"):
            parts = line.strip().split()
            if len(parts) >= 2:
                # Join all parts except the last one as name, last part is sequence
                name = self.clean_name("_".join(parts[:-1]))
                sequence = parts[-1]
                sequences[name] = sequence

        return sequences, None

    def parse_fasta(self, content: str) -> tuple[OrderedDict, str | None]:
        """
        Parse sequences from FASTA format.

        Args:
            content: File content as string

        Returns:
            Tuple of (sequences dict, error message)
        """
        sequences = OrderedDict()
        current_name = None
        current_sequence = []

        for line in content.split("\n"):
            line = line.strip()
            if line.startswith(">"):
                if current_name:
                    sequences[current_name] = "".join(current_sequence)
                current_name = self.clean_name(line[1:])
                current_sequence = []
            elif line:
                current_sequence.append(line)

        if current_name:
            sequences[current_name] = "".join(current_sequence)

        return sequences, None

    def remove_duplicate_sequences(
        self, sequences: OrderedDict
    ) -> tuple[OrderedDict, list[str]]:
        """
        Remove duplicate sequences, keeping the first occurrence.

        Args:
            sequences: OrderedDict of sequence name -> sequence

        Returns:
            Tuple of (unique sequences, list of removed entry names)
        """
        unique_sequences = OrderedDict()
        removed_entries = []
        seen_sequences = set()

        for name, sequence in sequences.items():
            if sequence not in seen_sequences:
                unique_sequences[name] = sequence
                seen_sequences.add(sequence)
            else:
                removed_entries.append(name)

        return unique_sequences, removed_entries

    def write_phylip(self, sequences: OrderedDict, output_file: Path) -> str | None:
        """
        Write sequences to relaxed PHYLIP format.

        Args:
            sequences: OrderedDict of sequence name -> sequence
            output_file: Path to output file

        Returns:
            Error message if any, None otherwise
        """
        if not sequences:
            return "No sequences to write"

        # Validate all sequences have the same length
        seq_lengths = [len(seq) for seq in sequences.values()]
        if len(set(seq_lengths)) > 1:
            return f"Sequences have different lengths: {set(seq_lengths)}"

        num_sequences = len(sequences)
        seq_length = len(next(iter(sequences.values())))
        max_name_length = max(len(name) for name in sequences)

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open("w") as f:
            # Write header
            f.write(f"{num_sequences} {seq_length}\n")

            # Write sequences
            for name, sequence in sequences.items():
                if self.align_names:
                    padded_name = name.ljust(max_name_length + 2)
                else:
                    padded_name = name + " "
                f.write(f"{padded_name}{sequence}\n")

        return None

    def process_file(self, input_file: Path, output_file: Path) -> tuple[bool, str]:
        """
        Process a single alignment file.

        Args:
            input_file: Path to input file
            output_file: Path to output file

        Returns:
            Tuple of (success, log message)
        """
        try:
            content = input_file.read_text()
        except Exception as e:
            return False, f"Error reading {input_file.name}: {str(e)}"

        # Determine file type and parse
        if content.strip().upper().startswith("#NEXUS"):
            sequences, error = self.parse_nexus(content)
            file_type = "NEXUS"
        else:
            sequences, error = self.parse_fasta(content)
            file_type = "FASTA"

        if error:
            return False, f"Error parsing {input_file.name}: {error}"

        if not sequences:
            return False, f"No sequences found in {input_file.name}"

        # Remove duplicates if requested
        removed_entries = []
        if self.remove_duplicates:
            sequences, removed_entries = self.remove_duplicate_sequences(sequences)

        # Write to PHYLIP format
        error = self.write_phylip(sequences, output_file)
        if error:
            return False, f"Error writing {output_file.name}: {error}"

        # Build log message
        log_msg = f"Processing {input_file.name} ({file_type}):\n"
        if removed_entries:
            log_msg += f"  Removed {len(removed_entries)} duplicate sequence(s):\n"
            for entry in removed_entries:
                log_msg += f"    - {entry}\n"
        else:
            log_msg += "  No duplicate sequences found\n"

        log_msg += (
            f"  Converted {len(sequences)} sequence(s) to PHYLIP: {output_file.name}\n"
        )

        return True, log_msg

    def get_sequence_type(self, file_path: Path) -> str:
        """
        Determine if file contains DNA or protein sequences.
        Analyzes actual sequence content to detect nucleotide vs amino acid sequences.

        Args:
            file_path: Path to the file

        Returns:
            'dna' or 'protein'
        """
        # First check filename for explicit hints
        name_lower = file_path.name.lower()
        if "protein" in name_lower or "aa" in name_lower or "prot" in name_lower:
            return "protein"
        if "dna" in name_lower or "nucleotide" in name_lower or "cds" in name_lower:
            return "dna"

        # Analyze sequence content
        try:
            content = file_path.read_text()
            # Extract sequences (handle both FASTA and NEXUS)
            sequences = []
            if content.strip().upper().startswith("#NEXUS"):
                # Parse NEXUS
                matrix_match = re.search(
                    r"MATRIX\s*([\s\S]*?);", content, re.IGNORECASE
                )
                if matrix_match:
                    for line in matrix_match.group(1).strip().split("\n"):
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            sequences.append(parts[-1])
            else:
                # Parse FASTA
                current_seq = []
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith(">"):
                        if current_seq:
                            sequences.append("".join(current_seq))
                            current_seq = []
                    elif line:
                        current_seq.append(line)
                if current_seq:
                    sequences.append("".join(current_seq))

            if not sequences:
                return "protein"  # Default fallback

            # Analyze first few sequences
            sample_seqs = sequences[: min(3, len(sequences))]

            # Character sets for classification
            strict_nucleotides = set("ATGC")  # Only A, T, G, C (no ambiguous codes)
            all_amino_acids = set("ACDEFGHIKLMNPQRSTVWY")  # 20 standard amino acids
            protein_specific_chars = set(
                "EFILPQO"
            )  # Chars unique to proteins (O = rare 21st)

            total_chars = 0
            strict_nucleotide_chars = 0
            amino_acid_chars = 0
            protein_specific_chars_count = 0
            unique_chars = set()

            for seq in sample_seqs:
                seq_upper = (
                    seq.upper().replace("-", "").replace("X", "")
                )  # Remove gaps and unknowns
                total_chars += len(seq_upper)
                unique_chars.update(seq_upper)
                strict_nucleotide_chars += sum(
                    1 for c in seq_upper if c in strict_nucleotides
                )
                amino_acid_chars += sum(1 for c in seq_upper if c in all_amino_acids)
                protein_specific_chars_count += sum(
                    1 for c in seq_upper if c in protein_specific_chars
                )

            if total_chars == 0:
                return "protein"  # Default fallback

            # Calculate ratios
            strict_nucleotide_ratio = strict_nucleotide_chars / total_chars
            amino_acid_ratio = amino_acid_chars / total_chars
            char_diversity = len(unique_chars)

            # If we have ANY protein-specific amino acids, it's definitely protein
            if protein_specific_chars_count > 0:
                return "protein"

            # If >98% are valid amino acids but only ~25% are strict nucleotides, it's protein
            # (catches proteins with mostly A,C,D,G,H,K,M,N,R,S,T,V,W,Y)
            if amino_acid_ratio > 0.98 and strict_nucleotide_ratio < 0.30:
                return "protein"

            # If >98% of characters are STRICT nucleotides (A, T, G, C), it's DNA
            if strict_nucleotide_ratio > 0.98:
                return "dna"

            # If we have low diversity (≤4 unique chars) and >90% strict nucleotides, it's DNA
            if char_diversity <= 4 and strict_nucleotide_ratio > 0.90:
                return "dna"

            # If we have high diversity (>5 chars) and low strict nucleotide ratio, it's protein
            if char_diversity > 5 and strict_nucleotide_ratio < 0.90:
                return "protein"

            # Default to protein for phylogenetic analysis (safer for edge cases)
            return "protein"

        except Exception:
            # If we can't read/parse, default to protein
            return "protein"

    def process_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        recursive: bool = False,
        split_by_type: bool = False,
        keep_structure: bool = True,
    ) -> tuple[int, int]:
        """
        Process all alignment files in a directory.

        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            recursive: Process subdirectories recursively
            split_by_type: Split output into dna/protein subdirectories
            keep_structure: Maintain input directory structure in output

        Returns:
            Tuple of (successful conversions, failed conversions)
        """
        # Find all alignment files
        pattern = "**/*" if recursive else "*"

        files = []
        for ext in self.VALID_EXTENSIONS:
            files.extend(input_dir.glob(f"{pattern}{ext}"))

        if not files:
            print(f"No alignment files found in {input_dir}")
            return 0, 0

        successful = 0
        failed = 0
        all_logs = []

        for input_file in sorted(files):
            # Determine output path
            if keep_structure:
                # Maintain directory structure
                relative_path = input_file.relative_to(input_dir)
                if split_by_type:
                    seq_type = self.get_sequence_type(input_file)
                    output_file = (
                        output_dir / seq_type / relative_path.with_suffix(".phy")
                    )
                else:
                    output_file = output_dir / relative_path.with_suffix(".phy")
            else:
                # Flat structure
                if split_by_type:
                    seq_type = self.get_sequence_type(input_file)
                    output_file = (
                        output_dir / seq_type / input_file.with_suffix(".phy").name
                    )
                else:
                    output_file = output_dir / input_file.with_suffix(".phy").name

            # Process the file
            success, log_msg = self.process_file(input_file, output_file)

            if success:
                successful += 1
                if self.verbose:
                    print(
                        f"✓ {input_file.name} -> {output_file.relative_to(output_dir.parent)}"
                    )
            else:
                failed += 1
                print(f"✗ {input_file.name}: {log_msg}")

            all_logs.append(log_msg)

        # Write log file
        log_file = output_dir.parent / "processing_log.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_content = "Alignment Processing Log\n"
        log_content += f"Generated: {timestamp}\n"
        log_content += f"Input directory: {input_dir}\n"
        log_content += f"Output directory: {output_dir}\n"
        log_content += f"Processed: {successful + failed} files\n"
        log_content += f"Successful: {successful}\n"
        log_content += f"Failed: {failed}\n"
        log_content += "=" * 80 + "\n\n"
        log_content += "\n".join(all_logs)

        log_file.write_text(log_content)

        return successful, failed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Process alignment files (FASTA/NEXUS) and convert to PHYLIP format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process directory, keep structure
  %(prog)s input_dir/

  # Process recursively
  %(prog)s input_dir/ --recursive

  # Split output by dna/protein
  %(prog)s input_dir/ --split-by-type

  # Custom output directory
  %(prog)s input_dir/ -o custom_output/

  # Keep duplicates
  %(prog)s input_dir/ --keep-duplicates
        """,
    )

    parser.add_argument(
        "input_dir",
        type=Path,
        help="Input directory containing alignment files (.fasta, .fa, .nexus, .nex)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="Output directory (default: input_dir/../processed)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Process subdirectories recursively",
    )
    parser.add_argument(
        "-s",
        "--split-by-type",
        action="store_true",
        help="Split output into dna/ and protein/ subdirectories",
    )
    parser.add_argument(
        "--flat",
        action="store_true",
        help="Don't maintain directory structure, flatten all files to output root",
    )
    parser.add_argument(
        "--keep-duplicates",
        action="store_true",
        help="Don't remove duplicate sequences",
    )
    parser.add_argument(
        "--no-align-names",
        action="store_true",
        help="Don't pad sequence names with spaces",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Validate input directory
    if not args.input_dir.is_dir():
        print(f"Error: {args.input_dir} is not a valid directory")
        sys.exit(1)

    # Determine output directory
    output_dir = args.output_dir or args.input_dir.parent / "processed"

    # Create processor
    processor = AlignmentProcessor(
        remove_duplicates=not args.keep_duplicates,
        align_names=not args.no_align_names,
        verbose=args.verbose,
    )

    # Process files
    print(f"Processing alignments from: {args.input_dir}")
    print(f"Output directory: {output_dir}")
    if args.recursive:
        print("Mode: Recursive")
    if args.split_by_type:
        print("Splitting by sequence type (dna/protein)")
    print()

    successful, failed = processor.process_directory(
        args.input_dir,
        output_dir,
        recursive=args.recursive,
        split_by_type=args.split_by_type,
        keep_structure=not args.flat,
    )

    # Summary
    print()
    print("=" * 60)
    print("Processing complete!")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Log file: {output_dir.parent / 'processing_log.txt'}")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
