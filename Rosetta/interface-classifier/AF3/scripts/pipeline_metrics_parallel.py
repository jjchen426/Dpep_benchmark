# 2026.3.24
# junjiechen
# 支持在当前AlphaFold3输出目录中并行计算RMSD指标并统计成功率


import argparse
import json
import os
import re
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from Bio.PDB import PDBParser, FastMMCIFParser, Superimposer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="在当前AlphaFold3输出目录中并行计算RMSD指标并统计成功率"
    )
    parser.add_argument("--inputs-base", type=Path, required=False, help="输入目录（预留参数，可不填）")
    parser.add_argument("--pdb-list", type=Path, required=True, help="PDB列表文件路径（用于限定可识别的设计父结构）")
    parser.add_argument("--ref-pdb-base", type=Path, required=True, help="参考PDB目录")
    parser.add_argument("--output-base", type=Path, required=True, help="当前AlphaFold3输出目录（其子目录为各设计目录）")
    parser.add_argument("--peptide-chain", type=str, required=True, help="多肽链ID，例如: B")
    parser.add_argument(
        "--backbone-atoms",
        type=str,
        default="N,CA,C,O",
        help="骨架原子名，逗号分隔。默认: N,CA,C,O",
    )
    parser.add_argument(
        "--sc-rmsd-cutoffs",
        type=str,
        default="1.0,1.5,2.0,2.5",
        help="成功率统计用scRMSD阈值，逗号分隔。默认: 1.0,1.5,2.0,2.5",
    )
    parser.add_argument("--pep-plddt-cutoff", type=float, default=70.0, help="pep_pLDDT阈值，默认70")
    parser.add_argument("--iptm-cutoff", type=float, default=0.7, help="ipTM阈值，默认0.7")
    parser.add_argument(
        "--rmsd-filter-cutoff",
        type=float,
        default=2.5,
        help="导出过滤文件时的scRMSD阈值，默认2.5",
    )
    parser.add_argument(
        "--summary-filename",
        type=str,
        default="metrics_summary.csv",
        help="RMSD汇总输出文件名",
    )
    parser.add_argument(
        "--filtered-filename-template",
        type=str,
        default="metrics_filtered_scRMSD_le{cutoff}.csv",
        help="RMSD过滤输出文件名模板，支持占位符{cutoff}",
    )
    parser.add_argument(
        "--success-rate-filename",
        type=str,
        default="success_rates_by_parent_complex.csv",
        help="成功率统计输出文件名",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=0,
        help="并行进程数。0表示自动使用 max(1, CPU核数-1)",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=20,
        help="每完成多少个parent_complex打印一次进度，默认20",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> tuple[set[str], list[float], int]:
    if args.inputs_base is not None and not args.inputs_base.exists():
        raise FileNotFoundError(f"inputs-base不存在: {args.inputs_base}")
    if not args.pdb_list.exists():
        raise FileNotFoundError(f"pdb-list不存在: {args.pdb_list}")
    if not args.ref_pdb_base.is_dir():
        raise NotADirectoryError(f"ref-pdb-base不是目录: {args.ref_pdb_base}")
    if not args.output_base.is_dir():
        raise NotADirectoryError(f"output-base不是目录: {args.output_base}")
    if not args.summary_filename.strip():
        raise ValueError("--summary-filename 不能为空")
    if not args.filtered_filename_template.strip():
        raise ValueError("--filtered-filename-template 不能为空")
    if "{cutoff}" not in args.filtered_filename_template:
        raise ValueError("--filtered-filename-template 必须包含 {cutoff} 占位符")
    if not args.success_rate_filename.strip():
        raise ValueError("--success-rate-filename 不能为空")

    peptide_chain = args.peptide_chain.strip()
    if not peptide_chain:
        raise ValueError("--peptide-chain 不能为空")

    backbone_atoms = {atom.strip() for atom in args.backbone_atoms.split(",") if atom.strip()}
    if not backbone_atoms:
        raise ValueError("--backbone-atoms 为空，请至少提供一个原子名")

    cutoffs: list[float] = []
    for val in args.sc_rmsd_cutoffs.split(","):
        val = val.strip()
        if not val:
            continue
        cutoffs.append(float(val))
    if not cutoffs:
        raise ValueError("--sc-rmsd-cutoffs 不能为空")

    if args.num_workers < 0:
        raise ValueError("--num-workers 不能小于0")
    if args.progress_every <= 0:
        raise ValueError("--progress-every 必须大于0")

    cpu_count = os.cpu_count() or 1
    resolved_workers = max(1, cpu_count - 1) if args.num_workers == 0 else args.num_workers
    return backbone_atoms, cutoffs, resolved_workers


def read_pdb_list(pdb_list_path: Path) -> list[str]:
    with pdb_list_path.open("r") as f:
        return [line.strip() for line in f if line.strip()]


def parse_seed_sample(sample_name: str) -> tuple[int, int]:
    seed_str, sample_str = sample_name.split("_sample-")
    return int(seed_str.replace("seed-", "")), int(sample_str)


def get_backbone_atoms(chain, backbone_atoms: set[str]):
    return [atom for atom in chain.get_atoms() if atom.get_id() in backbone_atoms]


def get_first_non_target_chain(model, target_chain_id: str):
    for chain in model:
        if chain.id != target_chain_id:
            return chain
    msg = f"no non-target chain found (target={target_chain_id})"
    raise KeyError(msg)


def compute_sc_rmsd_with_prepared_ref(
    ref_coords: np.ndarray,
    align_ref_atoms,
    pred_chain,
    align_pred_chain,
    backbone_atoms: set[str],
) -> float:
    align_pred_atoms = get_backbone_atoms(align_pred_chain, backbone_atoms)

    sup = Superimposer()
    sup.set_atoms(align_ref_atoms, align_pred_atoms)
    rot, tran = sup.rotran

    pred_atoms = get_backbone_atoms(pred_chain, backbone_atoms)
    pred_coords = np.array([atom.get_coord() for atom in pred_atoms], dtype=float)
    pred_coords_aligned = pred_coords @ rot + tran
    diffs = ref_coords - pred_coords_aligned
    return round(float(np.sqrt(np.mean(np.sum(diffs**2, axis=1)))), 4)


def process_single_sample(
    sample_prefix: str,
    sample_dir: Path,
    mmcifparser: FastMMCIFParser,
    peptide_chain_id: str,
    align_chain_id: str,
    backbone_atoms: set[str],
    align_ref_atoms,
    ref_coords: np.ndarray,
) -> tuple:
    sample_name = sample_dir.name
    seed, sample_id = parse_seed_sample(sample_name)

    conf_path = sample_dir / f"{sample_prefix}_{sample_name}_confidences.json"
    summary_path = sample_dir / f"{sample_prefix}_{sample_name}_summary_confidences.json"
    cif_path = sample_dir / f"{sample_prefix}_{sample_name}_model.cif"

    with conf_path.open("r") as f:
        conf_data = json.load(f)
    b_chain_plddt = [
        float(p)
        for cid, p in zip(conf_data["atom_chain_ids"], conf_data["atom_plddts"])
        if cid == peptide_chain_id
    ]
    pep_plddt = round(float(np.mean(b_chain_plddt)), 4)

    plddt = round(float(np.mean(conf_data["atom_plddts"])), 4)

    with summary_path.open("r") as f:
        summary_data = json.load(f)
    iptm = round(float(summary_data["iptm"]), 4)
    ptm = round(float(summary_data["ptm"]), 4)
    pep_ptm = round(float(summary_data["chain_ptm"][1]), 4)

    ranking_score = round(float(summary_data["ranking_score"]), 4)

    pae_min = min(summary_data["chain_pair_pae_min"][0][1], summary_data["chain_pair_pae_min"][1][0])
    ipae = (summary_data["chain_pair_pae_mean"][0][1] + summary_data["chain_pair_pae_mean"][1][0]) / 2

    structure = mmcifparser.get_structure("pred", str(cif_path))
    chain_pred_pep = structure[0][peptide_chain_id]
    align_chain_pred = structure[0][align_chain_id]

    sc_rmsd = compute_sc_rmsd_with_prepared_ref(
        ref_coords=ref_coords,
        align_ref_atoms=align_ref_atoms,
        pred_chain=chain_pred_pep,
        align_pred_chain=align_chain_pred,
        backbone_atoms=backbone_atoms,
    )

    return (sample_prefix,
            seed, 
            sample_id, 
            pep_plddt, 
            plddt, 
            iptm, 
            ptm, 
            pep_ptm, 
            pae_min, 
            ipae, 
            ranking_score, 
            sc_rmsd)


def process_parent_group(
    parent_complex: str,
    design_dir_paths: list[str],
    ref_pdb_base: str,
    peptide_chain_id: str,
    backbone_atoms: set[str],
) -> tuple[list[tuple], int, int]:
    pdbparser = PDBParser(QUIET=True)
    mmcifparser = FastMMCIFParser(QUIET=True)

    rows: list[tuple] = []
    matched_design_dirs = 0
    total_sample_dirs = 0

    ref_pdb_path = Path(ref_pdb_base) / f"{parent_complex}.pdb"
    structure_ref = pdbparser.get_structure("ref", str(ref_pdb_path))
    chain_ref_pep = structure_ref[0][peptide_chain_id]
    align_chain_ref = get_first_non_target_chain(structure_ref[0], peptide_chain_id)
    align_chain_id = align_chain_ref.id

    align_ref_atoms = get_backbone_atoms(align_chain_ref, backbone_atoms)
    ref_atoms = get_backbone_atoms(chain_ref_pep, backbone_atoms)
    ref_coords = np.array([atom.get_coord() for atom in ref_atoms], dtype=float)

    for design_dir_str in sorted(design_dir_paths):
        design_dir = Path(design_dir_str)
        design_name = design_dir.name
        matched_design_dirs += 1

        sample_dirs = [
            d for d in design_dir.iterdir()
            if d.is_dir() and re.fullmatch(r"seed-\d+_sample-\d+", d.name)
        ]
        total_sample_dirs += len(sample_dirs)

        for sample_dir in sorted(sample_dirs):
            rows.append(
                process_single_sample(
                    sample_prefix=design_name,
                    sample_dir=sample_dir,
                    mmcifparser=mmcifparser,
                    peptide_chain_id=peptide_chain_id,
                    align_chain_id=align_chain_id,
                    backbone_atoms=backbone_atoms,
                    align_ref_atoms=align_ref_atoms,
                    ref_coords=ref_coords,
                )
            )

    return rows, matched_design_dirs, total_sample_dirs


def _run_parent_groups(
    parent_items: list,
    ref_pdb_base: str,
    peptide_chain_id: str,
    backbone_atoms: set[str],
    num_workers: int,
):
    """Generator that yields results from parent groups, handling parallelism."""
    if num_workers == 1:
        for pc, dp in parent_items:
            yield process_parent_group(
                pc, dp, ref_pdb_base, peptide_chain_id, backbone_atoms,
            )
    else:
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(
                    process_parent_group, pc, dp, ref_pdb_base,
                    peptide_chain_id, backbone_atoms,
                ): pc
                for pc, dp in parent_items
            }
            for future in as_completed(futures):
                yield future.result()


def collect_metrics_for_output_dir(
    pdbs: list[str],
    ref_pdb_base: Path,
    output_base: Path,
    peptide_chain_id: str,
    backbone_atoms: set[str],
    rmsd_filter_cutoff: float,
    summary_filename: str,
    filtered_filename_template: str,
    num_workers: int,
    progress_every: int,
) -> pd.DataFrame:
    if not output_base.is_dir():
        raise NotADirectoryError(f"输出目录不存在: {output_base}")

    rows: list[tuple] = []
    matched_design_dirs = 0
    total_sample_dirs = 0
    pdb_set = set(pdbs)

    design_dirs = [d for d in output_base.iterdir() if d.is_dir()]
    parent_to_design_dirs: dict[str, list[str]] = defaultdict(list)
    for design_dir in sorted(design_dirs):
        design_name = design_dir.name
        parent_complex = re.sub(r"_\d+$", "", design_name)
        if parent_complex in pdb_set:
            parent_to_design_dirs[parent_complex].append(str(design_dir))

    parent_items = sorted(parent_to_design_dirs.items(), key=lambda x: x[0])
    total_parent_groups = len(parent_items)
    print(f"可处理parent_complex数量: {total_parent_groups}")
    print(f"并行进程数: {num_workers}")

    completed_groups = 0
    for group_rows, n_matched, n_samples in _run_parent_groups(
        parent_items, str(ref_pdb_base), peptide_chain_id, backbone_atoms, num_workers,
    ):
        rows.extend(group_rows)
        matched_design_dirs += n_matched
        total_sample_dirs += n_samples
        completed_groups += 1
        if completed_groups % progress_every == 0 or completed_groups == total_parent_groups:
            print(f"进度: {completed_groups}/{total_parent_groups} parent_complex 完成")

    result = pd.DataFrame(
        rows,
        columns=["complex", "seed", "id", "pep_plDDT", "plDDT", "ipTM", "pTM", "pep_pTM", "pAE_min", "ipAE", "ranking_score", "scRMSD"],
    )

    if not result.empty:
        result = result.sort_values(
            ["complex", "seed", "id"]
        ).reset_index(drop=True)

    result.to_csv(output_base / summary_filename, index=False, float_format="%.4f")
    result_filtered = result[result["scRMSD"] <= rmsd_filter_cutoff].reset_index(drop=True)
    cutoff_token = str(rmsd_filter_cutoff).replace(".", "")
    result_filtered.to_csv(
        output_base / filtered_filename_template.format(cutoff=cutoff_token),
        index=False,
        float_format="%.4f",
    )

    print(f"匹配到设计目录: {matched_design_dirs}")
    print(f"二级sample目录总数: {total_sample_dirs}")
    print(f"成功写入行数: {len(result)}")

    return result


def get_parent_complex(complex_name: str) -> str:
    return re.sub(r"_\d+$", "", complex_name)


def compute_success_rates(
    output_base: Path,
    cutoffs: list[float],
    pep_plddt_cutoff: float,
    iptm_cutoff: float,
    summary_filename: str,
    success_rate_filename: str,
) -> pd.DataFrame:
    summary_csv = output_base / summary_filename
    dtype = {
        "complex": "category",
        "seed": "int16",
        "id": "int8",
        "pep_plDDT": "float32",
        "plDDT": "float32",
        "ipTM": "float32",
        "pTM": "float32",
        "pep_pTM": "float32",
        "pAE_min": "float32",
        "ipAE": "float32",
        "ranking_score": "float32",
        "scRMSD": "float32",
    }
    df = pd.read_csv(summary_csv, dtype=dtype)

    df = df.copy()
    df["parent_complex"] = df["complex"].astype(str).map(get_parent_complex)

    design_counts = (
        df[["parent_complex", "complex"]]
        .drop_duplicates()
        .groupby("parent_complex", as_index=False)
        .agg(total_designs=("complex", "nunique"))
    )

    all_rows = []
    for cutoff in cutoffs:
        passed = df[
            (df["pep_plDDT"] >= pep_plddt_cutoff)
            & (df["ipTM"] >= iptm_cutoff)
            & (df["scRMSD"] <= cutoff)
        ]

        success_counts = (
            passed[["parent_complex", "complex"]]
            .drop_duplicates()
            .groupby("parent_complex", as_index=False)
            .agg(successful_designs=("complex", "nunique"))
        )

        stat = design_counts.merge(success_counts, on="parent_complex", how="left")
        stat["successful_designs"] = stat["successful_designs"].fillna(0).astype(int)
        stat["success_rate"] = (
            stat["successful_designs"] / stat["total_designs"] * 100
        ).round(2)
        stat["pep_plddt_cutoff"] = pep_plddt_cutoff
        stat["iptm_cutoff"] = iptm_cutoff
        stat["scRMSD_cutoff"] = cutoff

        all_rows.append(
            stat[[
                "parent_complex",
                "total_designs",
                "successful_designs",
                "success_rate",
                "pep_plddt_cutoff",
                "iptm_cutoff",
                "scRMSD_cutoff",
            ]]
        )

    success_rate_df = pd.concat(all_rows, ignore_index=True).sort_values(
        ["parent_complex", "scRMSD_cutoff"]
    )

    output_path = output_base / success_rate_filename
    success_rate_df.to_csv(output_path, index=False)
    print(f"CSV saved to: {output_path}")

    summary = (
        success_rate_df.groupby(["scRMSD_cutoff"], as_index=False)["success_rate"]
        .mean()
        .rename(columns={"success_rate": "mean_success_rate"})
    )
    print("\n不同scRMSD阈值下的平均成功率(%)：")
    print(summary.to_string(index=False))

    return success_rate_df


def main() -> None:
    args = parse_args()
    backbone_atoms, cutoffs, resolved_workers = validate_args(args)

    pdbs = read_pdb_list(args.pdb_list)

    collect_metrics_for_output_dir(
        pdbs=pdbs,
        ref_pdb_base=args.ref_pdb_base,
        output_base=args.output_base,
        peptide_chain_id=args.peptide_chain,
        backbone_atoms=backbone_atoms,
        rmsd_filter_cutoff=args.rmsd_filter_cutoff,
        summary_filename=args.summary_filename,
        filtered_filename_template=args.filtered_filename_template,
        num_workers=resolved_workers,
        progress_every=args.progress_every,
    )

    compute_success_rates(
        output_base=args.output_base,
        cutoffs=cutoffs,
        pep_plddt_cutoff=args.pep_plddt_cutoff,
        iptm_cutoff=args.iptm_cutoff,
        summary_filename=args.summary_filename,
        success_rate_filename=args.success_rate_filename,
    )


if __name__ == "__main__":
    main()