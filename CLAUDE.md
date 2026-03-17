# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python toolkit for phylogenetic analysis workflows: sequence alignment processing, tree construction (via ExaBayes on HPC), and visualization (CLANS, iTOL). Uses `uv` for dependency management and targets Python 3.12+.

## Common Commands

```bash
# Install dependencies
uv sync
uv sync --extra dev    # includes ruff and pytest

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_helper.py -v

# Lint and format
uv run ruff check src/
uv run ruff format src/

# Run a tool (all tools are standalone scripts)
uv run python src/phylogeny/process_alignments.py input_dir/ -r -v
```

## Architecture

The codebase is a collection of standalone CLI scripts, not a library with installable entry points. Each script in `src/` is invoked directly via `uv run python src/...`.

### Source Layout (`src/`)

- **`src/phylogeny/`** — Core alignment and tree processing tools
  - `process_alignments.py` — Main alignment processor (FASTA/NEXUS → PHYLIP), handles dedup, sanitization, type splitting
  - `nexus2tree.py` — Collapses low-support nodes in ExaBayes consensus trees
  - `run_mafft.py`, `merge_fasta_files.py`, `nexus2fasta.py` — Alignment utilities
  - `exabayes/` — ExaBayes-specific tools (sanitizer, info parsers, domain filter, GCC patcher)
- **`src/clans/`** — CLANS sequence similarity network visualization (parser, coloring)
- **`src/itol/`** — iTOL tree annotation file generation
- **`src/prot_family/`** — Protein family name standardization
- **`src/helper.py`** — DataFrame utilities

### Key Dependencies

- `dendropy` — Tree manipulation (NEXUS parsing, node collapsing, rerooting)
- `pandas` — Data handling throughout
- `distinctipy` — Automatic distinct color generation for visualization tools
- `pyfaidx` — FASTA indexing

## Code Style

- Ruff with line-length 88, double quotes, space indentation
- Lint rules: E, W, F, I, N, UP, B, C4, SIM (see `pyproject.toml` for ignores)
- `notebook/`, `data/`, `out/` directories are excluded from linting

## Workflow Context

The typical pipeline: FASTA → sanitize → align (MAFFT) → PHYLIP → ExaBayes (HPC/SLURM) → consensus trees → collapse nodes → visualize (iTOL/CLANS). HPC job scripts live in `docs/` (SLURM `.slurm` files).
