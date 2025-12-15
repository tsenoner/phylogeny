#!/usr/bin/env python3

import argparse
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class ExaBayesRunSummary:
    file_name: str
    last_gen: str
    last_asdsf: str
    last_msdsf: str
    last_time: str
    last_modified: str
    is_finished: bool
    runtime: str


def parse_exabayes_info(file_path: Path) -> ExaBayesRunSummary:
    """Parse an ExaBayes info file and extract relevant information."""
    content = file_path.read_text()
    file_name = file_path.name.replace("ExaBayes_info.", "")

    generations = re.findall(r"\[(\d+),([\d.]+)s\]", content)
    if generations:
        last_gen, last_time = generations[-1]
    else:
        last_gen, last_time = "N/A", "N/A"

    asdsf_msdsf = re.findall(
        r"standard deviation of split frequencies for trees \d+-\d+ "
        r"\(avg/max\):\s+([\d.]+)%\s+([\d.]+)%",
        content,
    )
    if asdsf_msdsf:
        last_asdsf, last_msdsf = asdsf_msdsf[-1]
    else:
        last_asdsf, last_msdsf = "N/A", "N/A"

    last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)

    # Check if the job is finished
    is_finished = check_if_finished(generations, last_modified, content)

    # Get birth date and calculate runtime
    birth_date, runtime = get_birth_date_and_runtime(file_path, last_modified)

    return ExaBayesRunSummary(
        file_name=file_name,
        last_gen=last_gen,
        last_asdsf=last_asdsf,
        last_msdsf=last_msdsf,
        last_time=last_time,
        last_modified=last_modified.strftime("%H:%M:%S %Y-%m-%d"),
        is_finished=is_finished,
        runtime=runtime,
    )


def get_birth_date_and_runtime(
    file_path: Path, last_modified: datetime
) -> tuple[datetime, str]:
    """Get birth date using stat command and calculate runtime."""
    try:
        stat_output = subprocess.check_output(
            ["stat", "-c", "%w", str(file_path)], text=True
        ).strip()
        time_string = stat_output.split(".")[0]
        birth_date = datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S")
        runtime = last_modified - birth_date
        return birth_date, format_timedelta(runtime)
    except (subprocess.CalledProcessError, ValueError):
        return datetime.fromtimestamp(0), "N/A"


def format_timedelta(td: timedelta) -> str:
    """Format timedelta to a human-readable string."""
    days = td.days
    hours, rem = divmod(td.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    if days > 0:
        return f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def check_if_finished(
    generations: list[tuple[str, str]], last_modified: datetime, content: str
) -> bool:
    """
    Check if the job is finished based on generation times, last modification time,
    and file content.
    """
    if "Converged/stopped after" in content:
        return True
    if len(generations) < 10:
        return False

    # Get the maximum time of the last 10 generations
    last_10_times = [float(time) for _, time in generations[-10:]]
    max_time = max(last_10_times)

    # Calculate the time difference between now and the last modification
    time_since_last_mod = datetime.now() - last_modified

    # If time since last mod is > 5 times max time of last 10 gens, consider finished
    return time_since_last_mod > timedelta(seconds=max_time * 5)


def summarize_exabayes_runs(directories: list[Path]) -> list[ExaBayesRunSummary]:
    """Summarize all ExaBayes runs in the given directories."""
    summary = []
    for directory in directories:
        for file_path in directory.rglob("ExaBayes_info.*"):
            summary.append(parse_exabayes_info(file_path))
    # Sort the summary first by status (RUN before FIN) and then by file name
    summary.sort(key=lambda x: (x.is_finished, x.file_name))
    return summary


def format_number(number: str) -> str:
    """Format number to human-readable format with 'k' for thousand and 'm' for million."""
    try:
        num = int(number)
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}m"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}k"
        else:
            return str(num)
    except ValueError:
        return number


def main():
    parser = argparse.ArgumentParser(
        description="Summarize ExaBayes runs from one or more directories."
    )
    parser.add_argument(
        "directories",
        type=Path,
        nargs="+",
        help="Paths to directories containing ExaBayes output folders",
    )
    args = parser.parse_args()

    # Validate directories
    invalid_dirs = [
        directory for directory in args.directories if not directory.is_dir()
    ]
    if invalid_dirs:
        parser.error(
            f"The following are not valid directories: "
            f"{', '.join(str(d) for d in invalid_dirs)}"
        )

    summary = summarize_exabayes_runs(args.directories)

    if not summary:
        print("No ExaBayes info files found in the provided directories.")
        return

    # Find the maximum length of each column for alignment
    headers = ExaBayesRunSummary(
        file_name="File Name",
        last_gen="NumGen",
        last_asdsf="ASDSF",
        last_msdsf="MSDSF",
        last_time="LastIncr",
        last_modified="LastModified",
        is_finished=False,
        runtime="Runtime",
    )
    max_name_len = max(len(item.file_name) for item in summary + [headers])
    max_gen_len = max(len(format_number(item.last_gen)) for item in summary + [headers])

    header = (
        f"{'File Name':<{max_name_len}}  "
        f"{'NumGen':>{max_gen_len}}  "
        f"{'ASDSF':>5}  "
        f"{'MSDSF':>5}  "
        f"{'LastIncr':>8}  "
        f"{'LastModified':<19}  "
        f"{'Runtime':>12}  "
        f"{'Status'}"
    )
    separator = (
        f"{'-' * max_name_len}  "
        f"{'-' * max(6, max_gen_len)}  "
        f"{'-' * 5}  "
        f"{'-' * 5}  "
        f"{'-' * 8}  "
        f"{'-' * 19}  "
        f"{'-' * 12}  "
        f"{'-' * 6}"
    )

    print(header)
    print(separator)

    for item in summary:
        formatted_gen = format_number(item.last_gen)
        status = "FIN" if item.is_finished else "RUN"
        print(
            f"{item.file_name:<{max_name_len}}  "
            f"{formatted_gen:>{max_gen_len}}  "
            f"{item.last_asdsf:>5}  "
            f"{item.last_msdsf:>5}  "
            f"{item.last_time:>7}s  "
            f"{item.last_modified:<19}  "
            f"{item.runtime:>12}  "
            f"{status:>6}"
        )


if __name__ == "__main__":
    main()
