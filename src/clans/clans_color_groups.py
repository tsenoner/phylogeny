import argparse
from colorsys import rgb_to_hsv

import pandas as pd
from distinctipy import distinctipy


def generate_colors(num_unique_colors: int, seed: int = 42) -> list[str]:
    """Generate a list of distinct colors sorted by hue."""
    colorblind_type = "Normal"
    colors = distinctipy.get_colors(
        num_unique_colors, colorblind_type=colorblind_type, rng=seed
    )
    hex_colors = [
        "#" + "".join([f"{int(c * 255):02X}" for c in color]) for color in colors
    ]
    sorted_colors = sorted(
        hex_colors,
        key=lambda color: rgb_to_hsv(
            int(color[1:3], 16) / 255.0,
            int(color[3:5], 16) / 255.0,
            int(color[5:7], 16) / 255.0,
        )[0],
    )
    return sorted_colors


def read_features(filepath: str) -> dict[str, list[str]]:
    """Read the features from the given file and return the feature mapping."""
    df = pd.read_csv(filepath, sep=",", header=0)
    feature_mapping = df.groupby("Taxon_grouping")["identifier"].apply(list).to_dict()
    return feature_mapping


def modify_clans_file(
    input_path: str,
    output_path: str,
    feature_mapping: dict[str, list[str]],
    colors: list[str],
):
    """Modify the clans file based on the given feature mapping and colors."""
    with open(input_path) as clans_file:
        clans_data = clans_file.readlines()

    node_properties = [
        "nodes_size=10\n",
        "nodes_color=0;0;0;255\n",
        "nodes_outline_color=0;0;0;255\n",
        "nodes_outline_width=0.5\n",
    ]
    param_end_index = clans_data.index("</param>\n")
    for prop in reversed(node_properties):
        clans_data.insert(param_end_index, prop)

    seq_start_index = clans_data.index("<seq>\n") + 1
    seq_end_index = clans_data.index("</seq>\n")
    fasta_data = clans_data[seq_start_index:seq_end_index]
    header_to_index = {}
    current_index = 0
    for line in fasta_data:
        if line.startswith(">"):
            header_to_index[line.strip()[1:]] = current_index
            current_index += 1

    seqgroups_section = [
        "<seqgroups>\n",
        "category=Taxon_grouping\n",
        "nodes_size=10\n",
        "text_size=9\n",
        "nodes_outline_color=0;0;0;255\n",
        "nodes_outline_width=0.5\n",
        "is_bold=False\n",
        "is_italic=False\n",
    ]
    feature_to_color = dict(zip(feature_mapping, colors))
    for feature, color in sorted(feature_to_color.items()):
        rgba_color = (
            ";".join([str(int(color[j : j + 2], 16)) for j in (1, 3, 5)]) + ";255"
        )
        if feature in feature_mapping:
            seqgroup = [
                f"name={feature}\n",
                "size=10\n",
                "name_size=8\n",
                f"color={rgba_color}\n",
                "outline_color=0;0;0;255\n",
                "is_bold=True\n",
                "is_italic=False\n",
                "numbers="
                + ";".join(
                    map(str, [header_to_index[uid] for uid in feature_mapping[feature]])
                )
                + ";\n",
            ]
            seqgroups_section.extend(seqgroup)
    seqgroups_section.append("</seqgroups>\n")

    last_seq_index = len(clans_data) - 1 - clans_data[::-1].index("<pos>\n")
    for group in reversed(seqgroups_section):
        clans_data.insert(last_seq_index, group)

    with open(output_path, "w") as output_file:
        output_file.writelines(clans_data)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Modify the clans file based on features and colors."
    )
    parser.add_argument("features_file", type=str, help="Path to the features file.")
    parser.add_argument(
        "input_clans_file", type=str, help="Path to the input clans file."
    )
    parser.add_argument(
        "output_clans_file", type=str, help="Path to the output clans file."
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Seed for color generation."
    )

    return parser.parse_args()


def main(features_file, input_clans_file, output_clans_file, seed=42):
    feature_mapping = read_features(features_file)
    colors = generate_colors(len(feature_mapping), seed)
    modify_clans_file(input_clans_file, output_clans_file, feature_mapping, colors)


if __name__ == "__main__":
    args = parse_args()
    main(args.features_file, args.input_clans_file, args.output_clans_file, args.seed)
