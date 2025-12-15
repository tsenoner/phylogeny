import argparse
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
    print(f"Processing: {nexus_path}")
    tree = dendropy.Tree.get(path=nexus_path, schema="nexus")

    prune_nodes(tree, node_annotation, bootstrap_threshold)
    remove_leaf_annotations(tree)
    reroot_tree(tree, reroot_taxon_label)
    save_tree(tree, output_path)

    print(f"Saved collapsed tree to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Collapse nodes in a Nexus tree file based on a bootstrap support threshold."
    )
    parser.add_argument(
        "nexus_file",
        type=str,
        help="Path to the input Nexus file.",
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
        help="Node annotation to use. default: 'prob(percent)'",
    )
    parser.add_argument(
        "--reroot-on",
        dest="reroot_taxon_label",
        type=str,
        default=None,
        help="The name of the taxon to reroot the tree on.",
    )
    args = parser.parse_args()

    nexus_file = Path(args.nexus_file)

    if not nexus_file.is_file():
        print(f"Error: Input file not found at {nexus_file}")
        return

    threshold = int(args.bootstrap_threshold)
    output_file_name = f"{nexus_file.stem}_collapsed{threshold}{nexus_file.suffix}"
    output_path = nexus_file.with_name(output_file_name)

    process_nexus_file(
        nexus_path=nexus_file,
        output_path=output_path,
        bootstrap_threshold=args.bootstrap_threshold,
        node_annotation=args.node_annotation,
        reroot_taxon_label=args.reroot_taxon_label,
    )

    print("Processing complete.")


if __name__ == "__main__":
    main()
