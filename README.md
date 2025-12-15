# Phylogeny Analysis Tools

A collection of tools for phylogenetic analysis, focusing on alignment processing, format conversion, and tree visualization.

## Main Tools

### 🔧 `process_alignments.py` - Unified Alignment Processor

**Location:** `src/phylogeny/process_alignments.py`

The main tool for processing alignment files. Handles FASTA and NEXUS formats, removes duplicates, and converts to PHYLIP format for phylogenetic analysis tools like ExaBayes.

**Features:**

- Supports FASTA (`.fasta`, `.fa`, `.fas`) and NEXUS (`.nexus`, `.nex`) formats
- Automatic duplicate sequence removal
- Sanitizes sequence names (removes special characters)
- Maintains directory structure or flattens output
- Can split output by sequence type (DNA/protein)
- Generates detailed processing logs
- Recursive directory processing

**Usage:**

```bash
# Basic usage - process directory
uv run python src/phylogeny/process_alignments.py input_dir/

# Process recursively with verbose output
uv run python src/phylogeny/process_alignments.py input_dir/ -r -v

# Split output by DNA/protein
uv run python src/phylogeny/process_alignments.py input_dir/ -s

# Custom output directory
uv run python src/phylogeny/process_alignments.py input_dir/ -o custom_output/

# Keep duplicates (no removal)
uv run python src/phylogeny/process_alignments.py input_dir/ --keep-duplicates

# Flatten directory structure
uv run python src/phylogeny/process_alignments.py input_dir/ --flat
```

**Options:**

- `-o, --output-dir`: Specify output directory (default: `input_dir/../processed`)
- `-r, --recursive`: Process subdirectories recursively
- `-s, --split-by-type`: Split output into `dna/` and `protein/` subdirectories
- `--flat`: Don't maintain directory structure
- `--keep-duplicates`: Don't remove duplicate sequences
- `--no-align-names`: Don't pad sequence names
- `-v, --verbose`: Enable verbose output

**Output:**

- `.phy` files in the processed directory
- `processing_log.txt` with detailed conversion information

---

### Other Tools

#### `fasta_sanitizer.py`

**Location:** `src/phylogeny/exabayes/fasta_sanitizer.py`

Cleans FASTA files by removing sequences with ambiguous residues.

```bash
uv run python src/phylogeny/exabayes/fasta_sanitizer.py -f input.fasta -v
```

#### `nexus2fasta.py`

**Location:** `src/phylogeny/nexus2fasta.py`

Converts NEXUS files to FASTA format removing gaps.

```bash
uv run python src/phylogeny/nexus2fasta.py input.nexus
```

#### `nexus2tree.py`

**Location:** `src/phylogeny/nexus2tree.py`

Processes NEXUS tree files from ExaBayes output.

#### `run_mafft.py`

**Location:** `src/phylogeny/run_mafft.py`

Runs MAFFT alignment and converts output to PHYLIP format.

```bash
uv run python src/phylogeny/run_mafft.py -i input.fasta -o output.phy -a local
```

#### `merge_fasta_files.py`

**Location:** `src/phylogeny/merge_fasta_files.py`

Merges multiple FASTA files and removes duplicates.

---

## Project Structure

```
phylogeny/
├── src/phylogeny/
│   ├── process_alignments.py    # Main alignment processor
│   ├── nexus2fasta.py            # NEXUS → FASTA converter
│   ├── nexus2tree.py             # Tree file processor
│   ├── run_mafft.py              # MAFFT alignment pipeline
│   ├── merge_fasta_files.py      # FASTA file merger
│   ├── parse_signalp6.py         # SignalP6 output parser
│   └── exabayes/
│       ├── fasta_sanitizer.py    # FASTA quality cleaner
│       └── parse_exabayes_info.py
├── data/                         # Data directories
└── tests/                        # Unit tests
```

---

## Workflow Examples

### Example 1: Process venom protein alignments

```bash
# Process all FASTA files recursively, split by type
uv run python src/phylogeny/process_alignments.py \
  data/animal_venom/cap_251215/raw \
  -o data/animal_venom/cap_251215/processed \
  -r -s -v
```

Output structure:

```
processed/
├── dna/
│   └── [subdirs with .phy files]
├── protein/
│   └── [subdirs with .phy files]
└── processing_log.txt
```

### Example 2: Process mixed NEXUS/FASTA files

```bash
# Process directory with both formats, keep structure
uv run python src/phylogeny/process_alignments.py \
  data/animal_venom/cap_240827/raw_data \
  -v
```

### Example 3: Clean and process workflow

```bash
# Step 1: Clean FASTA files
uv run python src/phylogeny/exabayes/fasta_sanitizer.py -f input.fasta -v

# Step 2: Convert to PHYLIP
uv run python src/phylogeny/process_alignments.py input_dir/
```

---

## ExaBayes Utilities

### Parse nexus/newick files from ExaBayes:

```bash
# Rename ExaBayes output files
for f in *; do
  if [[ $f == *Newick* ]]; then
    ext="newick"
  else
    ext="nexus"
  fi
  mv "$f" "$(echo "$f" | awk -F'.' -v ext="$ext" '{print $NF"."ext}')"
done
```

```bash
# Alternative renaming approach
for f in ExaBayes_*; do
  if [[ $f == *Newick* ]]; then
    mv "$f" "${f#ExaBayes_ConsensusExtendedMajorityRuleNewick.}.newick"
  elif [[ $f == *Nexus* ]]; then
    mv "$f" "${f#ExaBayes_ConsensusExtendedMajorityRuleNexus.}.nexus"
  fi
done
```

---

## Installation

This project uses `uv` for dependency management:

```bash
# Install dependencies
uv sync

# Run scripts
uv run python src/phylogeny/process_alignments.py --help
```

---

## Testing

```bash
# Run tests
uv run pytest tests/
```

---

## Recent Updates (2024-12-15)

- ✅ Created unified `process_alignments.py` script
- ✅ Removed redundant scripts:
  - `nexus2phy.py` (replaced by `process_alignments.py`)
  - `exabayes/fasta2phy.py` (replaced by `process_alignments.py`)
  - `aligned_fasta2phy.ipynb` (replaced by `process_alignments.py`)
  - Temporary batch conversion scripts
- ✅ Improved logging and error handling
- ✅ Added comprehensive command-line options

---

## Contributing

When adding new tools:

1. Follow the existing code structure
2. Add comprehensive docstrings
3. Include usage examples in this README
4. Add unit tests where applicable

---

## License

[Add your license information here]
