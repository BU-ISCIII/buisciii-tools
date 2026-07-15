#!/usr/bin/env python3
"""Generate reusable SNP-distance matrices from Snippy/Gubbins outputs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


VALID_BASES = np.frombuffer(b"ACGT", dtype=np.uint8)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate core.tab, phylo.aln, and clean.core.aln distance matrices."
    )
    parser.add_argument(
        "snippy_dir", nargs="?", type=Path, default=Path("."),
        help="Snippy output directory (default: current directory)",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        help="matrix output directory (default: SNIPPY_DIR)",
    )
    return parser.parse_args()


def read_fasta_alignment(path: Path) -> tuple[list[str], list[str]]:
    names, sequences = [], []
    current_name = None
    current_sequence: list[str] = []
    with path.open() as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current_name is not None:
                    names.append(current_name)
                    sequences.append("".join(current_sequence).upper())
                current_name = line[1:].split()[0]
                if not current_name:
                    raise ValueError(f"Empty FASTA identifier at {path}:{line_number}")
                current_sequence = []
            elif current_name is None:
                raise ValueError(f"Sequence before first FASTA header at {path}:{line_number}")
            else:
                current_sequence.append(line)
    if current_name is not None:
        names.append(current_name)
        sequences.append("".join(current_sequence).upper())
    validate_sequences(path, names, sequences)
    return names, sequences


def read_core_tab(path: Path) -> tuple[list[str], list[str]]:
    with path.open(newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError(f"Empty core table: {path}")
        if header[:3] != ["CHR", "POS", "REF"] or len(header) < 4:
            raise ValueError(f"Unexpected core.tab header: {path}")
        names = header[3:]
        sequence_parts = [[] for _ in names]
        for line_number, row in enumerate(reader, 2):
            if len(row) != len(header):
                raise ValueError(f"Wrong column count at {path}:{line_number}")
            for index, call in enumerate(row[3:]):
                sequence_parts[index].append(call.upper())
    sequences = ["".join(parts) for parts in sequence_parts]
    validate_sequences(path, names, sequences)
    return names, sequences


def validate_sequences(path: Path, names: list[str], sequences: list[str]) -> None:
    if not names:
        raise ValueError(f"No sequences found in {path}")
    if len(names) != len(set(names)):
        raise ValueError(f"Duplicate sequence identifiers in {path}")
    lengths = {len(sequence) for sequence in sequences}
    if len(lengths) != 1:
        raise ValueError(f"Sequences have different lengths in {path}: {sorted(lengths)}")


def calculate_distances(sequences: list[str], chunk_size: int = 100_000) -> np.ndarray:
    """Count absolute differences with pairwise deletion of non-ACGT calls."""
    sequence_array = np.vstack(
        [np.frombuffer(sequence.encode("ascii"), dtype=np.uint8) for sequence in sequences]
    )
    sequence_count, alignment_length = sequence_array.shape
    distances = np.zeros((sequence_count, sequence_count), dtype=np.int64)
    for start in range(0, alignment_length, chunk_size):
        block = sequence_array[:, start:start + chunk_size]
        valid = np.isin(block, VALID_BASES)
        for first in range(sequence_count - 1):
            pair_valid = valid[first + 1:] & valid[first]
            different = (block[first + 1:] != block[first]) & pair_valid
            distances[first, first + 1:] += np.count_nonzero(different, axis=1)
    distances += distances.T
    return distances


def write_matrix(path: Path, names: list[str], distances: np.ndarray) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["Sample", *names])
        for name, values in zip(names, distances):
            writer.writerow([name, *(int(value) for value in values)])


def main() -> int:
    args = parse_args()
    snippy_dir = args.snippy_dir.resolve()
    output_dir = (args.output_dir or snippy_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    inputs = [
        ("core_tab", snippy_dir / "core.tab", "core_tab_snp_distances.tsv", read_core_tab),
        ("phylo", snippy_dir / "phylo.aln", "phylo_snp_distances.tsv", read_fasta_alignment),
        ("clean_core", snippy_dir / "clean.core.aln", "clean_core_snp_distances.tsv", read_fasta_alignment),
    ]
    metadata = {
        "method": "Absolute A/C/G/T differences with pairwise deletion of other calls",
        "matrices": {},
    }
    for key, source, output_name, reader in inputs:
        if not source.is_file():
            print(f"WARNING: input not found, skipping: {source}")
            continue
        names, sequences = reader(source)
        matrix_path = output_dir / output_name
        write_matrix(matrix_path, names, calculate_distances(sequences))
        metadata["matrices"][output_name] = {
            "source": str(source),
            "sample_count": len(names),
            "site_count": len(sequences[0]),
        }
        print(f"Wrote: {matrix_path}")
    metadata_path = output_dir / "snp_distance_matrices_metadata.json"
    with metadata_path.open("w") as handle:
        json.dump(metadata, handle, indent=2)
        handle.write("\n")
    print(f"Wrote: {metadata_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}")
        raise SystemExit(2)
