#!/bin/bash

# Download ExaBayes consensus nexus files from remote server and rename them

set -euo pipefail

# Show help
if [ "$#" -eq 1 ] && { [ "$1" = "-h" ] || [ "$1" = "--help" ]; }; then
  cat << EOF
Usage: $0 <remote_path> <local_output_dir>

Downloads ExaBayes_ConsensusExtendedMajorityRuleNexus.* files from remote
subdirectories and renames them (e.g., CAP_Domain_20 -> CAP_Domain_20.nexus).

Example:
  $0 /home/user/projects/cap/exabayes data/animal_venom/cap/nexus

EOF
  exit 0
fi

# Check arguments
if [ "$#" -ne 2 ]; then
  echo "Error: Requires 2 arguments. Run '$0 -h' for help"
  exit 1
fi

# Define variables
REMOTE_HOST="jcn"
REMOTE_PATH="$1"
LOCAL_OUTPUT="$2"
RSYNC_OPTS="-arzvh -P --info=progress2 --bwlimit=30720"

echo "Downloading ExaBayes consensus files from: ${REMOTE_HOST}:${REMOTE_PATH}"
echo "Output directory: ${LOCAL_OUTPUT}"
echo ""

# Create output directory if it doesn't exist
mkdir -p "${LOCAL_OUTPUT}"

# Create temporary directory for initial download
TEMP_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_DIR}" EXIT

# Download files to temp directory
echo "Downloading files..."
rsync ${RSYNC_OPTS} \
  --include='*/' \
  --include='ExaBayes_ConsensusExtendedMajorityRuleNexus.*' \
  --exclude='*' \
  "${REMOTE_HOST}:${REMOTE_PATH}/" \
  "${TEMP_DIR}/"

# Find and rename files
echo ""
echo "Renaming files..."
file_count=0
find "${TEMP_DIR}" -type f -name "ExaBayes_ConsensusExtendedMajorityRuleNexus.*" | while read -r file; do
  # Extract the basename
  basename=$(basename "${file}")
  # Remove the prefix "ExaBayes_ConsensusExtendedMajorityRuleNexus."
  new_name="${basename#ExaBayes_ConsensusExtendedMajorityRuleNexus.}"
  # Add .nexus extension
  new_name="${new_name}.nexus"

  # Copy to final destination with new name
  cp "${file}" "${LOCAL_OUTPUT}/${new_name}"
  echo "  ${basename} -> ${new_name}"
  ((file_count++))
done

echo ""
echo "Download and rename complete!"
echo "Files saved to: ${LOCAL_OUTPUT}"
