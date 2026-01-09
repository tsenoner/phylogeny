import argparse
import sys
from pathlib import Path

import dendropy


def prune_nodes(tree, node_annotation, bootstrap_threshold):
    """Collapse nodes that have a support value below the specified threshold."""
    for node in tree:
        if not node.annotations:
            continue
        prob_value = node.annotations.get_value(node_annotation)
        if prob_value is not None and float(prob_value) < bootstrap_threshold:
            node.edge.collapse()


def remove_leaf_annotations(tree):
    """Remove all node_annotations from all leaves."""
    for leaf in tree.leaf_nodes():
        for node_annotation in ["prob", "prob(percent)"]:
            if leaf.annotations.get_value(node_annotation) is not None:
                leaf.annotations.drop(name=node_annotation)


def reroot_tree(tree, reroot_taxon_label):
    """Reroot the tree on the specified taxon, if provided."""
    if reroot_taxon_label is None:
        return

    outgroup_node = tree.find_node_with_taxon_label(reroot_taxon_label)
    if outgroup_node:
        tree.to_outgroup_position(outgroup_node, update_bipartitions=False)
    else:
        print(
            f"Warning: Reroot taxon '{reroot_taxon_label}' not found in tree. "
            "Proceeding without rerooting."
        )


def save_tree(tree, output_path):
    """Save a tree to a file in Nexus format."""
    schema = output_path.suffix[1:]
    tree.write(
        path=output_path,
        schema=schema,
        suppress_rooting=False,
        suppress_annotations=False,
    )


def process_nexus_file(
    nexus_path, output_path, bootstrap_threshold, node_annotation, reroot_taxon_label
):
    """Load, process, and save a Nexus tree file."""
    print(f"Processing: {nexus_path.name}")
    tree = dendropy.Tree.get(path=nexus_path, schema="nexus")

    prune_nodes(tree, node_annotation, bootstrap_threshold)
    remove_leaf_annotations(tree)
    reroot_tree(tree, reroot_taxon_label)
    save_tree(tree, output_path)

    print(f"  -> Saved to: {output_path.name}")


def process_directory(
    input_dir, output_dir, bootstrap_threshold, node_annotation, reroot_taxon_label
):
    """Process all nexus files in a directory."""
    # Find all nexus files
    nexus_files = list(input_dir.glob("*.nexus")) + list(input_dir.glob("*.nex"))

    if not nexus_files:
        print(f"No nexus files found in {input_dir}")
        return 0, 0

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Found {len(nexus_files)} nexus file(s) to process")
    print(f"Bootstrap threshold: {bootstrap_threshold}%")
    print(f"Output directory: {output_dir}")
    print("-" * 60)

    successful = 0
    failed = 0

    for nexus_file in sorted(nexus_files):
        try:
            # Keep original filename with _pruned suffix
            output_file = output_dir / f"{nexus_file.stem}_pruned{nexus_file.suffix}"

            process_nexus_file(
                nexus_path=nexus_file,
                output_path=output_file,
                bootstrap_threshold=bootstrap_threshold,
                node_annotation=node_annotation,
                reroot_taxon_label=reroot_taxon_label,
            )
            successful += 1
        except Exception as e:
            print(f"ERROR processing {nexus_file.name}: {e}")
            failed += 1
        print()  # blank line between files

    print("-" * 60)
    print(f"Processing complete: {successful} successful, {failed} failed")

    return successful, failed


def main():
    parser = argparse.ArgumentParser(
        description="Collapse nodes in Nexus tree file(s) based on a bootstrap support threshold.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single file (output: file_collapsed50.nexus)
  %(prog)s file.nexus -b 50

  # Process directory (output: input_dir_processed/*.nexus)
  %(prog)s input_dir/ -b 50

  # Custom output directory for batch processing
  %(prog)s input_dir/ -o output_dir/ -b 50
        """,
    )
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to input Nexus file or directory containing Nexus files",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output directory (only for directory input). Default: input_dir_processed",
    )
    parser.add_argument(
        "-b",
        "--bootstrap_threshold",
        type=float,
        default=50.0,
        help="The bootstrap support threshold for collapsing (0-100). Default: 50.0",
    )
    parser.add_argument(
        "--node_annotation",
        type=str,
        default="prob(percent)",
        help="Node annotation to use. Default: 'prob(percent)'",
    )
    parser.add_argument(
        "--reroot-on",
        dest="reroot_taxon_label",
        type=str,
        default=None,
        help="The name of the taxon to reroot the tree on.",
    )
    args = parser.parse_args()

    input_path = Path(args.input_path)

    # Check if input is a file or directory
    if input_path.is_file():
        # Single file processing
        if args.output:
            print("Warning: -o/--output flag ignored for single file processing")

        threshold = int(args.bootstrap_threshold)
        output_file_name = f"{input_path.stem}_collapsed{threshold}{input_path.suffix}"
        output_path = input_path.with_name(output_file_name)

        try:
            process_nexus_file(
                nexus_path=input_path,
                output_path=output_path,
                bootstrap_threshold=args.bootstrap_threshold,
                node_annotation=args.node_annotation,
                reroot_taxon_label=args.reroot_taxon_label,
            )
            print("\nProcessing complete.")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif input_path.is_dir():
        # Directory processing
        if args.output:
            output_dir = Path(args.output)
        else:
            output_dir = input_path.parent / f"{input_path.name}_processed"

        successful, failed = process_directory(
            input_dir=input_path,
            output_dir=output_dir,
            bootstrap_threshold=args.bootstrap_threshold,
            node_annotation=args.node_annotation,
            reroot_taxon_label=args.reroot_taxon_label,
        )

        if failed > 0:
            sys.exit(1)
    else:
        print(f"Error: Input path '{input_path}' is neither a file nor a directory")
        sys.exit(1)


if __name__ == "__main__":
    main()
