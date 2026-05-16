#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import re
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


STANDARD_AA = {
    "ALA",
    "ARG",
    "ASN",
    "ASP",
    "CYS",
    "GLN",
    "GLU",
    "GLY",
    "HIS",
    "ILE",
    "LEU",
    "LYS",
    "MET",
    "PHE",
    "PRO",
    "SER",
    "THR",
    "TRP",
    "TYR",
    "VAL",
}

BACKBONE_ATOMS = {"N", "CA", "C", "O"}
EXCLUDED_ATOMS = {"OXT"}
DEFAULT_NUM_DESIGNS = 100
DEFAULT_CKPT_PATH = (
    "/home/junjiechen/1_work/original_soft/RFdiffusion2-main/"
    "rf_diffusion/model_weights/RFD_140.pt"
)
DEFAULT_RUN_INFERENCE = (
    "/home/junjiechen/1_work/original_soft/RFdiffusion2-main/"
    "rf_diffusion/run_inference.py"
)


@dataclass(frozen=True)
class SamplePaths:
    sample_id: str
    pdb_id: str
    hotspot_pdb: Path
    original_pdb: Path


@dataclass(frozen=True)
class SampleData:
    sample_id: str
    pdb_id: str
    hotspot_pdb: Path
    original_pdb: Path
    l_chain_length: int
    hotspot_labels: list[str]
    hotspot_atoms: dict[str, list[str]]
    ligand_names: list[str]


@dataclass(frozen=True)
class SampleError:
    sample_id: str
    hotspot_pdb: str
    original_pdb: str
    error_type: str
    error_message: str


def sample_id_from_hotspot_path(hotspot_path: Path) -> str:
    stem = hotspot_path.stem
    stem = re.sub(r"_hotspot$", "", stem)
    stem = re.sub(r"^ddg_", "", stem)
    return stem


def pdb_id_from_hotspot_path(hotspot_path: Path) -> str:
    parts = hotspot_path.stem.split("_")
    if len(parts) < 2:
        raise ValueError(f"Cannot infer pdb id from hotspot file name: {hotspot_path.name}")
    pdb_id = parts[1].strip()
    if len(pdb_id) != 4:
        raise ValueError(f"Invalid pdb id parsed from {hotspot_path.name}: {pdb_id}")
    return pdb_id


def original_pdb_path_for_sample(sample_id: str, minimized_dir: Path) -> Path:
    return minimized_dir / f"{sample_id}.pdb"


def output_prefix_for_sample(run_dir: Path, pdb_id: str) -> Path:
    return run_dir / "samples" / pdb_id / "sample"


def iter_pdb_records(pdb_path: Path) -> Iterable[dict[str, str]]:
    with pdb_path.open("r") as handle:
        for line in handle:
            if not line.startswith(("ATOM", "HETATM")):
                continue
            yield {
                "record": line[:6].strip(),
                "atom_name": line[12:16].strip(),
                "resname": line[17:20].strip(),
                "chain_id": line[21].strip(),
                "resseq": line[22:26].strip(),
                "icode": line[26].strip(),
            }


def residue_key(record: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        record["chain_id"],
        record["resseq"],
        record["icode"],
        record["resname"],
    )


def residue_label(chain_id: str, resseq: str, icode: str) -> str:
    suffix = icode if icode else ""
    return f"{chain_id}{resseq}{suffix}"


def atom_is_excluded(atom_name: str) -> bool:
    atom_name = atom_name.strip().upper()
    if atom_name in EXCLUDED_ATOMS:
        return True
    if atom_name in BACKBONE_ATOMS:
        return True
    if atom_name.startswith("H"):
        return True
    if len(atom_name) > 1 and atom_name[0].isdigit() and atom_name[1] == "H":
        return True
    return False


def parse_l_chain_length(original_pdb: Path, chain_id: str = "L") -> int:
    seen: set[tuple[str, str, str]] = set()
    count = 0
    for record in iter_pdb_records(original_pdb):
        if record["record"] != "ATOM":
            continue
        if record["chain_id"] != chain_id:
            continue
        if record["resname"] not in STANDARD_AA:
            continue
        key = (record["chain_id"], record["resseq"], record["icode"])
        if key in seen:
            continue
        seen.add(key)
        count += 1
    if count == 0:
        raise ValueError(f"No standard amino-acid residues found in chain {chain_id} of {original_pdb}")
    return count


def parse_hotspot_pdb(hotspot_pdb: Path, chain_id: str = "L") -> tuple[list[str], dict[str, list[str]], list[str]]:
    hotspot_order: OrderedDict[tuple[str, str, str, str], list[str]] = OrderedDict()
    ligand_names: set[str] = set()

    for record in iter_pdb_records(hotspot_pdb):
        if record["chain_id"] == chain_id and record["resname"] in STANDARD_AA:
            if record["record"] != "ATOM":
                continue
            key = residue_key(record)
            if key not in hotspot_order:
                hotspot_order[key] = []
            atom_name = record["atom_name"]
            if not atom_is_excluded(atom_name):
                hotspot_order[key].append(atom_name)
        elif record["chain_id"] != chain_id:
            if record["resname"] != "ORI":
                ligand_names.add(record["resname"])

    if not hotspot_order:
        raise ValueError(f"No L-chain hotspot residues found in {hotspot_pdb}")

    hotspot_labels: list[str] = []
    hotspot_atoms: dict[str, list[str]] = {}
    for (chain, resseq, icode, _resname), atom_names in hotspot_order.items():
        label = residue_label(chain, resseq, icode)
        unique_atoms: list[str] = []
        seen_atoms: set[str] = set()
        for atom_name in atom_names:
            if atom_name in seen_atoms:
                continue
            seen_atoms.add(atom_name)
            unique_atoms.append(atom_name)
        if not unique_atoms:
            raise ValueError(f"Hotspot residue {label} has no side-chain atoms in {hotspot_pdb}")
        hotspot_labels.append(label)
        hotspot_atoms[label] = unique_atoms

    return hotspot_labels, hotspot_atoms, sorted(ligand_names)


def build_sample_data(paths: SamplePaths) -> SampleData:
    l_chain_length = parse_l_chain_length(paths.original_pdb)
    hotspot_labels, hotspot_atoms, ligand_names = parse_hotspot_pdb(paths.hotspot_pdb)
    return SampleData(
        sample_id=paths.sample_id,
        pdb_id=paths.pdb_id,
        hotspot_pdb=paths.hotspot_pdb,
        original_pdb=paths.original_pdb,
        l_chain_length=l_chain_length,
        hotspot_labels=hotspot_labels,
        hotspot_atoms=hotspot_atoms,
        ligand_names=ligand_names,
    )


def discover_samples(hotspot_dir: Path, minimized_dir: Path) -> list[SamplePaths]:
    samples: list[SamplePaths] = []
    for hotspot_pdb in sorted(hotspot_dir.glob("*_hotspot.pdb")):
        sample_id = sample_id_from_hotspot_path(hotspot_pdb)
        pdb_id = pdb_id_from_hotspot_path(hotspot_pdb)
        original_pdb = original_pdb_path_for_sample(sample_id, minimized_dir)
        samples.append(SamplePaths(sample_id=sample_id, pdb_id=pdb_id, hotspot_pdb=hotspot_pdb, original_pdb=original_pdb))
    return samples


def format_ligand_arg(ligand_names: list[str]) -> str:
    ligand_str = ",".join(ligand_names)
    return f"inference.ligand=\\'{ligand_str}\\'"


def format_contigs_arg(sample: SampleData) -> str:
    hotspot_count = len(sample.hotspot_labels)
    designed_length = sample.l_chain_length - hotspot_count
    if designed_length < 0:
        raise ValueError(
            f"Invalid contig length for {sample.sample_id}: l_chain_length={sample.l_chain_length}, hotspot_count={hotspot_count}"
        )
    contig_body = ",".join([str(designed_length), *sample.hotspot_labels])
    return f"'contigmap.contigs=[\"{contig_body}\"]'"


def format_contig_atoms_arg(sample: SampleData) -> str:
    dict_literal = ",".join(
        f"'{label}':'{','.join(atom_names)}'" for label, atom_names in sample.hotspot_atoms.items()
    )
    return f'"contigmap.contig_atoms=\\"{{{dict_literal}}}\\""'


def format_command(
    sample: SampleData,
    *,
    output_prefix: Path,
    run_inference_path: Path,
    ckpt_path: str,
    num_designs: int,
) -> str:
    parts = [
        f"python {run_inference_path}",
        "--config-name=aa",
        f"inference.input_pdb={sample.hotspot_pdb}",
        f"inference.output_prefix={output_prefix}",
        "inference.contig_as_guidepost=True",
        f"inference.num_designs={num_designs}",
        format_ligand_arg(sample.ligand_names),
        format_contigs_arg(sample),
        format_contig_atoms_arg(sample),
        f"inference.ckpt_path={ckpt_path}",
    ]
    return " ".join(parts)


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_outputs(
    hotspot_dir: Path,
    minimized_dir: Path,
    run_dir: Path,
    *,
    num_designs: int,
    ckpt_path: str,
    run_inference_path: Path,
    cuda_visible_devices: str,
) -> tuple[list[str], list[dict[str, str]], list[dict[str, str]]]:
    run_dir.mkdir(parents=True, exist_ok=True)

    samples = discover_samples(hotspot_dir, minimized_dir)
    commands: list[str] = []
    manifest_rows: list[dict[str, str]] = []
    error_rows: list[dict[str, str]] = []

    for paths in samples:
        try:
            sample = build_sample_data(paths)
            output_prefix = output_prefix_for_sample(run_dir, sample.pdb_id)
            command = format_command(
                sample,
                output_prefix=output_prefix,
                run_inference_path=run_inference_path,
                ckpt_path=ckpt_path,
                num_designs=num_designs,
            )
            commands.append(command)
            manifest_rows.append(
                {
                    "sample_id": sample.sample_id,
                    "pdb_id": sample.pdb_id,
                    "hotspot_pdb": str(sample.hotspot_pdb),
                    "original_pdb": str(sample.original_pdb),
                    "output_prefix": str(output_prefix),
                    "l_chain_length": str(sample.l_chain_length),
                    "hotspot_count": str(len(sample.hotspot_labels)),
                    "hotspot_labels": ",".join(sample.hotspot_labels),
                    "ligand_names": ",".join(sample.ligand_names),
                    "contigs": ",".join([str(sample.l_chain_length - len(sample.hotspot_labels)), *sample.hotspot_labels]),
                    "contig_atoms": "|".join(
                        f"{label}:{','.join(atom_names)}" for label, atom_names in sample.hotspot_atoms.items()
                    ),
                    "status": "ok",
                    "error_message": "",
                }
            )
        except Exception as exc:  # noqa: BLE001
            error_rows.append(
                {
                    "sample_id": paths.sample_id,
                    "pdb_id": paths.pdb_id,
                    "hotspot_pdb": str(paths.hotspot_pdb),
                    "original_pdb": str(paths.original_pdb),
                    "output_prefix": str(output_prefix_for_sample(run_dir, paths.pdb_id)),
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
            )
            manifest_rows.append(
                {
                    "sample_id": paths.sample_id,
                    "pdb_id": paths.pdb_id,
                    "hotspot_pdb": str(paths.hotspot_pdb),
                    "original_pdb": str(paths.original_pdb),
                    "output_prefix": str(output_prefix_for_sample(run_dir, paths.pdb_id)),
                    "l_chain_length": "",
                    "hotspot_count": "",
                    "hotspot_labels": "",
                    "ligand_names": "",
                    "contigs": "",
                    "contig_atoms": "",
                    "status": "error",
                    "error_message": f"{type(exc).__name__}: {exc}",
                }
            )

    run_sh_path = run_dir / "run.sh"
    manifest_path = run_dir / "run_manifest.csv"
    errors_path = run_dir / "run_errors.csv"

    script_lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        'export PYTHONPATH="/home/junjiechen/1_work/original_soft/RFdiffusion2-main:$PYTHONPATH"',
        "export HYDRA_FULL_ERROR=1",
        f'export CUDA_VISIBLE_DEVICES="{cuda_visible_devices}"',
        "",
    ]
    script_lines.extend(commands)
    script_lines.append("")

    run_sh_path.write_text("\n".join(script_lines), encoding="utf-8")
    run_sh_path.chmod(0o755)

    write_csv(
        manifest_path,
        manifest_rows,
        [
            "sample_id",
            "pdb_id",
            "hotspot_pdb",
            "original_pdb",
            "output_prefix",
            "l_chain_length",
            "hotspot_count",
            "hotspot_labels",
            "ligand_names",
            "contigs",
            "contig_atoms",
            "status",
            "error_message",
        ],
    )
    write_csv(
        errors_path,
        error_rows,
        ["sample_id", "pdb_id", "hotspot_pdb", "original_pdb", "output_prefix", "error_type", "error_message"],
    )

    return commands, manifest_rows, error_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate RFdiffusion2 run.sh from hotspot PDBs")
    parser.add_argument(
        "--hotspot-dir",
        type=Path,
        default=Path("/home/junjiechen/1_work/250401-Dpepalign/Benchmark/RFdiffusion2/rfd2_hotspots"),
    )
    parser.add_argument(
        "--minimized-dir",
        type=Path,
        default=Path("/home/junjiechen/1_work/250401-Dpepalign/Benchmark/RFdiffusion2/minimized"),
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("/home/junjiechen/1_work/250401-Dpepalign/Benchmark/RFdiffusion2/run"),
    )
    parser.add_argument("--num-designs", type=int, default=DEFAULT_NUM_DESIGNS)
    parser.add_argument("--ckpt-path", type=str, default=DEFAULT_CKPT_PATH)
    parser.add_argument("--run-inference-path", type=Path, default=Path(DEFAULT_RUN_INFERENCE))
    parser.add_argument("--cuda-visible-devices", type=str, default="2")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    commands, manifest_rows, error_rows = generate_outputs(
        args.hotspot_dir,
        args.minimized_dir,
        args.run_dir,
        num_designs=args.num_designs,
        ckpt_path=args.ckpt_path,
        run_inference_path=args.run_inference_path,
        cuda_visible_devices=args.cuda_visible_devices,
    )

    print(f"Generated run.sh commands: {len(commands)}")
    print(f"Manifest rows: {len(manifest_rows)}")
    print(f"Error rows: {len(error_rows)}")
    print(f"run.sh: {args.run_dir / 'run.sh'}")
    print(f"run_manifest.csv: {args.run_dir / 'run_manifest.csv'}")
    print(f"run_errors.csv: {args.run_dir / 'run_errors.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())