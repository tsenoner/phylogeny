import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter, MaxNLocator
from scipy.interpolate import interp1d


def parse_logs(file_paths):
    """Parse the logs from the ExaBayes info files."""

    # Initialize lists to hold the parsed data
    generations = []
    times = []
    avg_percentages = []
    max_percentages = []

    for file_path in file_paths:
        with open(file_path) as file:
            for line in file:
                gen_time_match = re.match(r"\[(\d+),([\d.]+)s\]", line)
                if gen_time_match:
                    generation = int(gen_time_match.group(1))
                    time = float(gen_time_match.group(2))
                    generations.append(generation)
                    times.append(time)

                split_frequencies_match = re.search(
                    r"standard deviation of split frequencies for trees [\d-]+ \(avg/max\):\s+([\d.]+)%\s+([\d.]+)%",
                    line,
                )
                if split_frequencies_match:
                    avg_percentage = float(split_frequencies_match.group(1))
                    max_percentage = float(split_frequencies_match.group(2))
                    avg_percentages.append(avg_percentage)
                    max_percentages.append(max_percentage)

    # Adjust lengths to match and create DataFrame
    adjusted_avg_percentages = [None] * len(generations)
    adjusted_max_percentages = [None] * len(generations)

    for i in range(len(avg_percentages)):
        adjusted_avg_percentages[i * 10] = avg_percentages[i]
        adjusted_max_percentages[i * 10] = max_percentages[i]

    for i in range(1, len(adjusted_avg_percentages)):
        if adjusted_avg_percentages[i] is None:
            adjusted_avg_percentages[i] = adjusted_avg_percentages[i - 1]
        if adjusted_max_percentages[i] is None:
            adjusted_max_percentages[i] = adjusted_max_percentages[i - 1]

    data = pd.DataFrame(
        {
            "generation": generations,
            "time": times,
            "avg_percentage": adjusted_avg_percentages,
            "max_percentage": adjusted_max_percentages,
        }
    )

    return data


def convert_time(time_in_seconds):
    """Convert time from seconds to 'Days-Hours' format."""
    days, seconds = divmod(int(time_in_seconds), 86_400)
    hours, seconds = divmod(seconds, 3_600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        time_formatted = f"{days}D-{hours}H"
    elif hours > 0:
        time_formatted = f"{hours}H-{minutes}M"
    elif minutes > 0:
        return f"{minutes}M-{seconds}S"
    else:
        return f"{seconds}S"
    return time_formatted


def human_readable_format(x, pos):
    """Convert numbers to a human-readable format with K, M, and B suffixes."""
    if x >= 1e9:
        return f"{x / 1e9:.1f}B"
    elif x >= 1e7:
        return f"{x / 1e6:.0f}M"
    elif x >= 1e6:
        return f"{x / 1e6:.1f}M"
    elif x >= 1e3:
        return f"{x / 1e3:.0f}K"
    return str(int(x))


def plot_data(data, output_path):
    """Plot the data and save the plot to the output path."""

    # Compute the cumulative sum of the time elapsed
    data["cumulative_time"] = data["time"].cumsum()

    # Create a new figure and set the size
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot the average and maximum percentages with logarithmic scale for y-axis
    ax1.plot(
        data["generation"],
        data["avg_percentage"],
        label="ASDSF (Average Percentage)",
    )
    ax1.plot(
        data["generation"],
        data["max_percentage"],
        label="MSDSF (Max Percentage)",
    )

    # customize y-axis
    ax1.set_yscale("log")
    ax1.grid(which="both", axis="y")
    formatter = FuncFormatter(lambda y, _: f"{y:.2g}%")
    ax1.yaxis.set_major_formatter(formatter)
    ax1.yaxis.set_minor_formatter(formatter)

    # Add labels
    ax1.set_xlabel("Generation")
    ax1.set_ylabel("Percentage (Log Scale)")

    # Create a second x-axis for cumulative time elapsed
    ax2 = ax1.twiny()
    ax2.set_xlim(ax1.get_xlim())
    ax2.plot(data["generation"], data["avg_percentage"], alpha=0)
    ax2.set_xlabel("Cumulative Time Elapsed")

    # --- Set the x-axis labels to 'Days-Hours' format using a FuncFormatter ---
    # Interpolation function for cumulative time
    f = interp1d(data["generation"], data["cumulative_time"])

    def get_value(x):
        return f(min(max(data["generation"].min(), x), data["generation"].max()))

    ax2.xaxis.set_major_formatter(
        FuncFormatter(lambda x, pos: convert_time(get_value(x)))
    )

    # Set formatter for ax1 x-axis to display generations in human readable format
    ax1.xaxis.set_major_formatter(FuncFormatter(human_readable_format))

    # set the number of ticks shown on the top and button x-axis
    ax1.xaxis.set_major_locator(MaxNLocator(nbins=11))
    ax2.xaxis.set_major_locator(MaxNLocator(nbins=11))

    # Add a legend
    ax1.legend()

    # Set the title
    plt.title(output_path.stem)

    # Save the plot
    plt.savefig(output_path)


def main():
    """Main function to parse the arguments and call the other functions."""
    parser = argparse.ArgumentParser(
        description="Parse ExaBayes info files and plot data."
    )
    parser.add_argument(
        "input_dir",
        type=str,
        help="Directory containing the ExaBayes info files.",
    )
    parser.add_argument(
        "output_dir",
        type=str,
        help="Directory to save the output plot files.",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for file_path in input_dir.glob("ExaBayes_info.*"):
        print(file_path)
        data = parse_logs([file_path])
        output_path = output_dir / f"{file_path.suffix[1:]}.png"
        plot_data(data, output_path)


if __name__ == "__main__":
    main()
