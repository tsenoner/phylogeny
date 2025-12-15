#!/usr/bin/env python3
"""
Created on:  Thu 31 Oct 2023 20:11:18
Description: This script processes FASTA sequences based on SignalP6 predictions. Sequences are either cut,
             kept, or removed based on SignalP6 output and user decisions. The script supports automated
             decision-making for sequences encountered in multiple runs.
Usage:       python parse_signalp6.py --fasta_input /path/to/input.fasta --signalp_output /path/to/signalp_output.gff3
             --fasta_output /path/to/output.fasta [--user_decisions /path/to/user_decisions.json]
@author:     tsenoner
"""

import argparse
import json

from pyfaidx import Fasta


def parse_signalp_output(file_path):
    signalp_dict = {}
    with open(file_path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            fields = line.strip().split("\t")
            seq_id = fields[0]
            cut_position = int(fields[4])
            try:
                probability = float(fields[5])
            except ValueError:
                print(
                    "Could not convert the probability value for sequence ID"
                    f" {seq_id}. Line: {line}"
                )
                continue
            signalp_dict[seq_id] = {
                "probability": probability,
                "cut_position": cut_position,
            }
    return signalp_dict


def get_user_decision(seq_id, seq, prob, user_decisions):
    if seq_id in user_decisions:
        return user_decisions[seq_id]
    print(f"Sequence ID: {seq_id}\nSequence: {seq}\nProbability: {prob}")
    while True:
        decision = input("Options: 'cut' (c), 'keep' (k), 'remove' (r): ").lower()
        decision = {"c": "cut", "k": "keep", "r": "remove"}.get(decision, decision)
        if decision in ["cut", "keep", "remove"]:
            user_decisions[seq_id] = decision
            return decision
        print("Input not recognized. Please enter a valid option.")


def process_fasta_sequences(
    input_fasta, signalp_dict, output_fasta, user_decisions_path=None
):
    user_decisions = {}
    if user_decisions_path:
        try:
            with open(user_decisions_path) as f:
                user_decisions = json.load(f)
        except FileNotFoundError:
            pass

    with open(output_fasta, "w") as out_f:
        fasta_sequences = Fasta(input_fasta, read_long_names=True)
        for seq_id in fasta_sequences:
            seq = str(fasta_sequences[seq_id])
            signalp_info = signalp_dict.get(seq_id, None)
            if signalp_info is None:
                continue

            prob = signalp_info["probability"]
            cut_position = signalp_info["cut_position"]
            new_seq = ""

            if prob >= 0.95:
                new_seq = seq[cut_position:]
            else:
                decision = get_user_decision(seq_id, seq, prob, user_decisions)
                if decision == "cut":
                    new_seq = seq[cut_position:]
                elif decision == "keep":
                    new_seq = seq
                else:
                    continue
            out_f.write(f">{seq_id}\n{new_seq}\n")

    if user_decisions_path:
        with open(user_decisions_path, "w") as f:
            json.dump(user_decisions, f, indent=4)


def main(fasta_input, signalp_output, fasta_output, user_decisions):
    signalp_dict = parse_signalp_output(signalp_output)
    process_fasta_sequences(fasta_input, signalp_dict, fasta_output, user_decisions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process FASTA sequences based on SignalP6 predictions."
    )
    parser.add_argument(
        "--fasta_input",
        "-f",
        type=str,
        required=True,
        help="Path to input FASTA file.",
    )
    parser.add_argument(
        "--signalp_output",
        "-s",
        type=str,
        required=True,
        help="Path to SignalP6 output file.",
    )
    parser.add_argument(
        "--fasta_output",
        "-o",
        type=str,
        required=True,
        help="Path to save the processed FASTA file.",
    )
    parser.add_argument(
        "--user_decisions",
        "-u",
        type=str,
        default=None,
        help="Path to save user decisions.",
    )
    args = parser.parse_args()
    main(
        args.fasta_input,
        args.signalp_output,
        args.fasta_output,
        args.user_decisions,
    )
