import argparse
import logging
from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)


def setup_logging(verbose: bool):
    """Configure logging based on the verbosity preference."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def read_clans_file(file_path: Path) -> list[str]:
    """Read and return the content of the CLANS file."""
    if not file_path.exists():
        logging.error(f"File {file_path} does not exist.")
        raise FileNotFoundError(f"File {file_path} not found.")

    try:
        with open(file_path) as clans_handle:
            return clans_handle.readlines()
    except Exception as e:
        logging.error(f"Failed to read the CLANS file: {e}")
        raise


def get_section_data(clans_data: list[str], tag: str) -> list[str]:
    try:
        start_index = clans_data.index(f"<{tag}>\n") + 1
        end_index = clans_data.index(f"</{tag}>\n") + 1
        return clans_data[start_index:end_index]
    except ValueError:
        logging.error(f"Section tag: {tag} not found in the CLANS data.")
        return []


def extract_headers(fasta_data: list[str]) -> pd.DataFrame:
    headers = [line.strip()[1:] for line in fasta_data if line.startswith(">")]
    return pd.DataFrame(headers, columns=["uid"])


def extract_coordinates(pos_data: list[str]) -> pd.DataFrame:
    coords = [list(map(float, line.strip().split()[1:-1])) for line in pos_data]
    return pd.DataFrame(coords, columns=["x", "y"])


def extract_groups(group_data: list[str]) -> dict:
    group = [
        line.strip().split("=")[1]
        for line in group_data
        if line.startswith(("name=", "numbers="))
    ]
    return {
        number: name
        for name, numbers in list(zip(group[::2], group[1::2]))
        for number in map(int, numbers.split(";")[:-1])
    }


def parse_clans_file(clans_file: str) -> pd.DataFrame:
    """Process and return the CLANS data in a structured DataFrame."""
    clans_data = read_clans_file(clans_file)

    df_uid = extract_headers(get_section_data(clans_data, "seq"))
    df_coord = extract_coordinates(get_section_data(clans_data, "pos"))
    group = extract_groups(get_section_data(clans_data, "seqgroups"))

    df = df_uid.join(df_coord)
    df["group"] = df.index.map(group)
    return df


def calculate_scores(df: pd.DataFrame) -> dict:
    """Calculate clustering scores for the given dataframe."""
    features = df[["x", "y"]]
    labels = df["group"]

    silhouette = silhouette_score(features, labels)
    davies_bouldin = davies_bouldin_score(features, labels)
    calinski_harabasz = calinski_harabasz_score(features, labels)

    return {
        "Silhouette": silhouette,
        "Davies_Bouldin": davies_bouldin,
        "Calinski_Harabasz": calinski_harabasz,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process and extract data from a CLANS file."
    )
    parser.add_argument(
        "file_path", type=Path, help="Path to the CLANS file to be processed."
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging for debugging purposes.",
    )
    return parser.parse_args()


def main(file_path):
    df = parse_clans_file(file_path)
    scores = calculate_scores(df=df)
    return scores


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.verbose)
    main(args.file_path)
