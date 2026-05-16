#!/usr/bin/env python3
"""Generate AlphaFold3 JSON input files from a CSV of chain sequences."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class ChainInfo:
    chain_id: str
    sequence: str


@dataclass(frozen=True)
class JobRow:
    name: str
    chains: list[ChainInfo]


def is_chain_header(header: str) -> bool:
    """A single letter A-Z or a-z is a chain ID header."""
    return bool(re.fullmatch(r"[A-Za-z]", header.strip()))


def parse_csv(path: Path) -> Iterator[JobRow]:
    """Yield JobRow from a CSV with chain-letter columns and optional name column."""
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return

        chain_cols = [h for h in reader.fieldnames if is_chain_header(h)]
        name_cols = [h for h in reader.fieldnames if not is_chain_header(h)]
        name_col = name_cols[0] if name_cols else None

        if not chain_cols:
            sys.exit("Error: No single-letter chain ID columns found in CSV header.")

        for idx, row in enumerate(reader, start=1):
            name = row.get(name_col, "").strip() if name_col else ""
            if not name:
                name = f"job_{idx}"

            chains = []
            for col in chain_cols:
                seq = row.get(col, "").strip()
                chains.append(ChainInfo(chain_id=col.upper(), sequence=seq))

            yield JobRow(name=name, chains=chains)


def build_json(
    job: JobRow, seeds: list[int], msa_dir: Path | None, use_templates: bool = False
) -> dict:
    """Build an AlphaFold3-compatible JSON dict for one job."""
    sequences = []
    templates_value: list | None = None if use_templates else []
    for chain in job.chains:
        protein: dict = {
            "sequence": chain.sequence,
            "id": chain.chain_id,
            "templates": templates_value,
        }
        if msa_dir is not None:
            msa_sub = msa_dir / job.name
            protein["pairedMsaPath"] = str(msa_sub / "pairing.a3m")
            protein["unpairedMsaPath"] = str(msa_sub / "non_pairing.a3m")
        else:
            protein["pairedMsa"] = ""
            protein["unpairedMsa"] = ""
        sequences.append({"protein": protein})

    return {
        "name": job.name,
        "modelSeeds": seeds,
        "dialect": "alphafold3",
        "version": 2,
        "sequences": sequences,
    }


def parse_seeds(raw: str) -> list[int]:
    """Parse comma-separated seed string into int list."""
    seeds = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            seeds.append(int(part))
        except ValueError:
            sys.exit(f"Error: Invalid seed value: '{part}'")
    return seeds if seeds else [42, 43, 44]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate AlphaFold3 JSON input files from a CSV of chain sequences."
    )
    parser.add_argument("--csv", type=Path, required=True, help="Input CSV file")
    parser.add_argument(
        "--prefix", type=str, required=True, help="Output filename prefix"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Output directory for JSON files",
    )
    parser.add_argument(
        "--msa-dir",
        type=Path,
        default=None,
        help="Base MSA directory (enables MSA path mode)",
    )
    parser.add_argument(
        "--seeds",
        type=str,
        default="42,43,44",
        help="Comma-separated list of model seeds (default: 42,43,44)",
    )
    parser.add_argument(
        "--templates",
        action="store_true",
        help="Enable template usage (templates: null). Default is no templates (templates: []).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.prefix:
        print("Error: --prefix cannot be empty.", file=sys.stderr)
        return 1

    seeds = parse_seeds(args.seeds)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    jobs = list(parse_csv(args.csv))
    if not jobs:
        print(
            "Warning: CSV contains no data rows. No JSON files generated.",
            file=sys.stderr,
        )
        return 0

    for idx, job in enumerate(jobs, start=1):
        data = build_json(job, seeds, args.msa_dir, args.templates)
        filename = f"{args.prefix}_{idx:04d}.json"
        out_path = args.output_dir / filename
        with out_path.open("w") as f:
            json.dump(data, f, indent=4)
        print(f"  {filename} <- {job.name}")

    print(f"Done: generated {len(jobs)} JSON file(s) in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
