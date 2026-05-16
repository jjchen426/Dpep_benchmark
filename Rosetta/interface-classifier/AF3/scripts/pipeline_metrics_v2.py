#!/usr/bin/env python3
# 2026.5.15
# junjiechen
# pipeline_metrics_v2.py
# 基于 pipeline_metrics_parallel.py 重构：
#   - JSON mapping 输入，用户显式指定设计目录 → ref PDB 的映射
#   - 轻量 mmCIF 解析（只提取目标链骨架原子），替代 Biopython FastMMCIFParser
#   - numpy Kabsch 替代 Biopython Superimposer
#   - 消除 CSV 回读，DataFrame 直接传入 success rate 计算


import argparse
import json
import os
import re
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from Bio.PDB import PDBParser


# ── 参数解析 ────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="并行计算 RMSD 指标并统计成功率 (v2)"
    )
    parser.add_argument("--mapping-json", type=Path, required=True,
                        help='JSON 映射文件: {"设计目录名": "ref PDB 名", ...}')
    parser.add_argument("--ref-pdb-base", type=Path, required=True,
                        help="参考 PDB 目录")
    parser.add_argument("--output-base", type=Path, required=True,
                        help="AlphaFold3 输出目录（其子目录为各设计目录）")
    parser.add_argument("--peptide-chain", type=str, required=True,
                        help="多肽链 ID，例如: B")
    parser.add_argument("--backbone-atoms", type=str, default="N,CA,C,O",
                        help="骨架原子名，逗号分隔。默认: N,CA,C,O")
    parser.add_argument("--sc-rmsd-cutoffs", type=str, default="1.0,1.5,2.0,2.5",
                        help="成功率统计用 scRMSD 阈值，逗号分隔")
    parser.add_argument("--pep-plddt-cutoff", type=float, default=70.0,
                        help="pep_pLDDT 阈值")
    parser.add_argument("--iptm-cutoff", type=float, default=0.7,
                        help="ipTM 阈值")
    parser.add_argument("--rmsd-filter-cutoff", type=float, default=2.5,
                        help="导出过滤文件时的 scRMSD 阈值")
    parser.add_argument("--summary-filename", type=str, default="metrics_summary.csv",
                        help="RMSD 汇总输出文件名")
    parser.add_argument("--filtered-filename-template", type=str,
                        default="metrics_filtered_scRMSD_le{cutoff}.csv",
                        help="过滤输出文件名模板")
    parser.add_argument("--success-rate-filename", type=str,
                        default="success_rates_by_parent_complex.csv",
                        help="成功率统计输出文件名")
    parser.add_argument("--num-workers", type=int, default=0,
                        help="并行进程数。0=自动 max(1, CPU核数-1)")
    parser.add_argument("--progress-every", type=int, default=20,
                        help="每完成多少个 ref group 打印一次进度")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> tuple[set[str], list[float], int]:
    if not args.mapping_json.exists():
        raise FileNotFoundError(f"mapping-json 不存在: {args.mapping_json}")
    if not args.ref_pdb_base.is_dir():
        raise NotADirectoryError(f"ref-pdb-base 不是目录: {args.ref_pdb_base}")
    if not args.output_base.is_dir():
        raise NotADirectoryError(f"output-base 不是目录: {args.output_base}")
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

    backbone_atoms = {a.strip() for a in args.backbone_atoms.split(",") if a.strip()}
    if not backbone_atoms:
        raise ValueError("--backbone-atoms 为空")

    cutoffs = []
    for val in args.sc_rmsd_cutoffs.split(","):
        val = val.strip()
        if val:
            cutoffs.append(float(val))
    if not cutoffs:
        raise ValueError("--sc-rmsd-cutoffs 不能为空")

    if args.num_workers < 0:
        raise ValueError("--num-workers 不能小于 0")
    if args.progress_every <= 0:
        raise ValueError("--progress-every 必须大于 0")

    cpu_count = os.cpu_count() or 1
    resolved_workers = max(1, cpu_count - 1) if args.num_workers == 0 else args.num_workers
    return backbone_atoms, cutoffs, resolved_workers


# ── 输入读取 ────────────────────────────────────────────────────────

def read_mapping_json(path: Path) -> dict[str, str]:
    """读取 JSON 映射文件: {设计目录名: ref PDB 名, ...}"""
    with path.open("r") as f:
        return json.load(f)


def parse_seed_sample(sample_name: str) -> tuple[int, int]:
    """从 'seed-42_sample-0' 解析出 (42, 0)"""
    seed_str, sample_str = sample_name.split("_sample-")
    return int(seed_str.replace("seed-", "")), int(sample_str)


# ── 轻量 mmCIF 解析 ────────────────────────────────────────────────

# 骨架原子的标准排列顺序，Kabsch 要求两套坐标严格按此顺序对齐
_ATOM_ORDER = ('N', 'CA', 'C', 'O')


def extract_backbone_coords(cif_path: str, chain_ids: set[str],
                            backbone_atoms: set[str],
                            atom_order: tuple[str, ...] = _ATOM_ORDER,
                            ) -> dict[str, np.ndarray]:
    """从 mmCIF 文件中提取指定链的骨架原子坐标（numpy 数组）。

    原子按残基索引升序排列，残基内按 *atom_order* 指定的顺序排列，
    确保与 ref PDB 提取的坐标逐原子对应，避免 Kabsch 因顺序错位而出错。

    返回 {chain_id: (N, 3) ndarray, ...}。
    """
    # 收集: {chain_id: {res_id: {atom_name: [x, y, z]}}}
    raw: dict[str, dict] = {cid: {} for cid in chain_ids}
    col_names: dict[int, str] = {}
    col_by_name: dict[str, int] | None = None
    in_atom_site = False

    with open(cif_path) as f:
        for line in f:
            line = line.rstrip()

            if line.startswith("loop_"):
                in_atom_site = False
                col_names = {}
                col_by_name = None
                continue

            if line.startswith("_atom_site."):
                in_atom_site = True
                name = line.split(None, 1)[0][len("_atom_site."):]
                col_names[len(col_names)] = name
                continue

            if line.startswith("_"):
                continue

            if not line or line.startswith("#"):
                if col_by_name is not None:
                    break
                in_atom_site = False
                continue

            if in_atom_site and col_names and not line.startswith("_"):
                if col_by_name is None:
                    col_by_name = {n: i for i, n in col_names.items()}

                fields = line.split()
                try:
                    chain = fields[col_by_name["label_asym_id"]]
                    if chain not in chain_ids:
                        continue
                    atom = fields[col_by_name["label_atom_id"]]
                    if atom not in backbone_atoms:
                        continue

                    # 优先用 auth_seq_id，其次 label_seq_id
                    res_col = col_by_name.get("auth_seq_id",
                               col_by_name.get("label_seq_id"))
                    if res_col is None:
                        res_id = 0
                    else:
                        try:
                            res_id = int(fields[res_col])
                        except (ValueError, TypeError, IndexError):
                            res_id = 0

                    x = float(fields[col_by_name["Cartn_x"]])
                    y = float(fields[col_by_name["Cartn_y"]])
                    z = float(fields[col_by_name["Cartn_z"]])
                except (KeyError, IndexError, ValueError):
                    continue

                res_dict = raw[chain].setdefault(res_id, {})
                res_dict[atom] = (x, y, z)

    # 按残基索引 + 原子顺序展平
    result: dict[str, np.ndarray] = {}
    for cid in chain_ids:
        coords: list[float] = []
        for res_id in sorted(raw[cid]):
            res_atoms = raw[cid][res_id]
            for name in atom_order:
                if name in res_atoms:
                    coords.extend(res_atoms[name])
        if coords:
            result[cid] = np.array(coords, dtype=float).reshape(-1, 3)
    return result


# ── numpy Kabsch ──────────────────────────────────────────────────

def kabsch_align_rmsd(pred_align: np.ndarray, ref_align: np.ndarray,
                      pred_pep: np.ndarray, ref_pep: np.ndarray) -> float:
    """用 Kabsch 将 pred_align 对齐到 ref_align，然后对 pred_pep 施加相同变换，
    计算 pred_pep 与 ref_pep 之间的骨架 RMSD。

    参数均为 (N, 3) 的 numpy 数组。
    """
    # 去质心
    pred_centroid = pred_align.mean(axis=0)
    ref_centroid = ref_align.mean(axis=0)
    pred_centered = pred_align - pred_centroid
    ref_centered = ref_align - ref_centroid

    # SVD 求旋转矩阵
    H = pred_centered.T @ ref_centered
    U, _S, Vt = np.linalg.svd(H)
    R = U @ Vt

    # 处理反射
    if np.linalg.det(R) < 0:
        U[:, -1] *= -1
        R = U @ Vt

    # 对多肽链施加旋转平移
    pep_centered = pred_pep - pred_centroid
    pep_aligned = pep_centered @ R + ref_centroid

    # 计算 RMSD
    diff = ref_pep - pep_aligned
    return round(float(np.sqrt(np.mean(np.sum(diff ** 2, axis=1)))), 4)


# ── 单样本处理 ──────────────────────────────────────────────────────

def extract_sample_metrics(conf_path: Path, summary_path: Path,
                           peptide_chain_id: str) -> tuple:
    """读取 confidences.json 和 summary_confidences.json，返回各项指标。"""
    with conf_path.open("r") as f:
        conf = json.load(f)

    b_chain_plddt = [
        float(p)
        for cid, p in zip(conf["atom_chain_ids"], conf["atom_plddts"])
        if cid == peptide_chain_id
    ]
    pep_plddt = round(float(np.mean(b_chain_plddt)), 4)
    plddt = round(float(np.mean(conf["atom_plddts"])), 4)

    with summary_path.open("r") as f:
        summary = json.load(f)

    iptm = round(float(summary["iptm"]), 4)
    ptm = round(float(summary["ptm"]), 4)
    pep_ptm = round(float(summary["chain_ptm"][1]), 4)
    ranking_score = round(float(summary["ranking_score"]), 4)
    pae_min = min(summary["chain_pair_pae_min"][0][1],
                  summary["chain_pair_pae_min"][1][0])

    ipae = round(float((summary["chain_pair_pae_min"][0][1] + summary["chain_pair_pae_min"][1][0]) / 2), 4)

    return pep_plddt, plddt, iptm, ptm, pep_ptm, pae_min, ipae, ranking_score


def get_sorted_backbone_coords(chain, backbone_atoms: set[str],
                               atom_order: tuple[str, ...] = _ATOM_ORDER,
                               ) -> np.ndarray:
    """从 Biopython Chain 中提取骨架原子坐标，按残基索引和 *atom_order* 排序。

    保证与 CIF 解析器的输出顺序完全一致，确保 Kabsch 计算的正确性。
    """
    coords: list[float] = []
    for residue in chain:
        for name in atom_order:
            if name in backbone_atoms and residue.has_id(name):
                x, y, z = residue[name].get_coord()
                coords.extend((x, y, z))
    return np.array(coords, dtype=float).reshape(-1, 3)


def get_first_non_target_chain(model, target_chain_id: str):
    for chain in model:
        if chain.id != target_chain_id:
            return chain
    raise KeyError(f"没有找到非目标链 (target={target_chain_id})")


# ── 分组处理（一个 ref 下的所有设计目录）────────────────────────────

def process_ref_group(ref_name: str, design_names: list[str],
                      output_base: str, ref_pdb_base: str,
                      peptide_chain_id: str, backbone_atoms: set[str],
                      ) -> tuple[list[tuple], int]:
    """处理共享同一个 ref 的所有设计目录。

    每个 ref PDB 只解析一次，之后对所有属于该 ref 的预测 sample 计算 RMSD。
    返回 (rows, sample_count)。
    """
    pdbparser = PDBParser(QUIET=True)

    # ── 解析 ref PDB ──
    ref_path = Path(ref_pdb_base) / f"{ref_name}.pdb"
    ref_struct = pdbparser.get_structure("ref", str(ref_path))
    ref_pep_chain = ref_struct[0][peptide_chain_id]
    ref_align_chain = get_first_non_target_chain(ref_struct[0], peptide_chain_id)
    align_chain_id = ref_align_chain.id

    ref_pep_coords = get_sorted_backbone_coords(ref_pep_chain, backbone_atoms)
    ref_align_coords = get_sorted_backbone_coords(ref_align_chain, backbone_atoms)

    rows: list[tuple] = []
    sample_count = 0

    for design_name in design_names:
        design_dir = Path(output_base) / design_name
        if not design_dir.is_dir():
            continue

        sample_dirs = sorted(
            d for d in design_dir.iterdir()
            if d.is_dir() and re.fullmatch(r"seed-\d+_sample-\d+", d.name)
        )

        for sample_dir in sample_dirs:
            sample_count += 1
            sample_name = sample_dir.name
            seed, sample_id = parse_seed_sample(sample_name)

            prefix = f"{design_name}_{sample_name}"
            cif_path = sample_dir / f"{prefix}_model.cif"
            conf_path = sample_dir / f"{prefix}_confidences.json"
            summary_path = sample_dir / f"{prefix}_summary_confidences.json"

            if not (cif_path.exists() and conf_path.exists() and summary_path.exists()):
                continue

            try:
                pep_plddt, plddt, iptm, ptm, pep_ptm, pae_min, ipae, ranking_score = \
                    extract_sample_metrics(conf_path, summary_path, peptide_chain_id)
            except (KeyError, json.JSONDecodeError, OSError) as e:
                print(f"  [跳过] {sample_dir.name}: JSON 读取失败 ({e})", flush=True)
                continue

            # 轻量 CIF 解析：只提取两链的骨架坐标
            coords = extract_backbone_coords(
                str(cif_path), {peptide_chain_id, align_chain_id}, backbone_atoms,
            )
            pred_pep_coords = coords.get(peptide_chain_id)
            pred_align_coords = coords.get(align_chain_id)

            if pred_pep_coords is None or pred_align_coords is None:
                continue
            if len(pred_pep_coords) != len(ref_pep_coords):
                continue
            if len(pred_align_coords) != len(ref_align_coords):
                continue

            sc_rmsd = kabsch_align_rmsd(
                pred_align_coords, ref_align_coords,
                pred_pep_coords, ref_pep_coords,
            )

            rows.append((design_name, seed, sample_id,
                         pep_plddt, plddt, iptm, ptm, pep_ptm,
                         pae_min, ipae, ranking_score, sc_rmsd))

    return rows, sample_count


# ── 主收集流程 ──────────────────────────────────────────────────────

def collect_metrics(mapping: dict[str, str], ref_pdb_base: Path,
                    output_base: Path, peptide_chain_id: str,
                    backbone_atoms: set[str],
                    rmsd_filter_cutoff: float,
                    summary_filename: str,
                    filtered_filename_template: str,
                    num_workers: int,
                    progress_every: int) -> pd.DataFrame:
    """收集所有设计目录的指标，写入 CSV，返回 DataFrame。"""
    # 按 ref_name 分组 → 同一个 ref 的设计目录一起处理
    ref_to_designs: dict[str, list[str]] = defaultdict(list)
    for design_name, ref_name in mapping.items():
        ref_to_designs[ref_name].append(design_name)

    group_items = sorted(ref_to_designs.items(), key=lambda x: x[0])
    total_groups = len(group_items)
    _t0 = time.perf_counter()
    print(f"ref groups 数量: {total_groups}", flush=True)
    print(f"并行进程数: {num_workers}", flush=True)

    all_rows: list[tuple] = []
    total_samples = 0
    completed = 0

    if num_workers == 1:
        for ref_name, design_names in group_items:
            t1 = time.perf_counter()
            rows, n_samples = process_ref_group(
                ref_name, design_names, str(output_base), str(ref_pdb_base),
                peptide_chain_id, backbone_atoms,
            )
            all_rows.extend(rows)
            total_samples += n_samples
            completed += 1
            if completed % progress_every == 0 or completed == total_groups:
                elapsed = time.perf_counter() - _t0
                print(f"进度: {completed}/{total_groups} ref groups 完成 "
                      f"({elapsed:.0f}s)", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(
                    process_ref_group, ref_name, design_names,
                    str(output_base), str(ref_pdb_base),
                    peptide_chain_id, backbone_atoms,
                ): ref_name
                for ref_name, design_names in group_items
            }
            for future in as_completed(futures):
                rows, n_samples = future.result()
                all_rows.extend(rows)
                total_samples += n_samples
                completed += 1
                if completed % progress_every == 0 or completed == total_groups:
                    elapsed = time.perf_counter() - _t0
                    print(f"进度: {completed}/{total_groups} ref groups 完成 "
                          f"({elapsed:.0f}s)", flush=True)

    result = pd.DataFrame(
        all_rows,
        columns=["complex", "seed", "id", "pep_plDDT", "plDDT",
                 "ipTM", "pTM", "pep_pTM", "pAE_min", "ipAE",
                 "ranking_score", "scRMSD"],
    )

    if not result.empty:
        result = result.sort_values(["complex", "seed", "id"]).reset_index(drop=True)

    result.to_csv(output_base / summary_filename, index=False, float_format="%.4f")

    # 过滤输出
    result_filtered = result[result["scRMSD"] <= rmsd_filter_cutoff].reset_index(drop=True)
    cutoff_token = str(rmsd_filter_cutoff).replace(".", "")
    result_filtered.to_csv(
        output_base / filtered_filename_template.format(cutoff=cutoff_token),
        index=False, float_format="%.4f",
    )

    print(f"成功写入行数: {len(result)}", flush=True)
    print(f"scRMSD ≤ {rmsd_filter_cutoff} 行数: {len(result_filtered)}", flush=True)

    return result


# ── 成功率统计 ──────────────────────────────────────────────────────

def get_parent_complex(complex_name: str) -> str:
    return re.sub(r"_\d+$", "", complex_name)


def compute_success_rates(df: pd.DataFrame, output_base: Path,
                          cutoffs: list[float],
                          pep_plddt_cutoff: float,
                          iptm_cutoff: float,
                          success_rate_filename: str) -> pd.DataFrame:
    """直接从 DataFrame 计算成功率（无需重新读 CSV）。"""
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
            stat[["parent_complex", "total_designs", "successful_designs",
                  "success_rate", "pep_plddt_cutoff", "iptm_cutoff", "scRMSD_cutoff"]]
        )

    success_rate_df = pd.concat(all_rows, ignore_index=True).sort_values(
        ["parent_complex", "scRMSD_cutoff"]
    )

    output_path = output_base / success_rate_filename
    success_rate_df.to_csv(output_path, index=False)
    print(f"成功率 CSV 已保存: {output_path}", flush=True)

    summary = (
        success_rate_df.groupby(["scRMSD_cutoff"], as_index=False)["success_rate"]
        .mean()
        .rename(columns={"success_rate": "mean_success_rate"})
    )
    print("\n不同 scRMSD 阈值下的平均成功率(%)：", flush=True)
    print(summary.to_string(index=False))

    return success_rate_df


# ── 入口 ────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    backbone_atoms, cutoffs, resolved_workers = validate_args(args)

    mapping = read_mapping_json(args.mapping_json)
    print(f"读取到 {len(mapping)} 个设计目录映射", flush=True)

    result = collect_metrics(
        mapping=mapping,
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

    if not result.empty:
        compute_success_rates(
            df=result,
            output_base=args.output_base,
            cutoffs=cutoffs,
            pep_plddt_cutoff=args.pep_plddt_cutoff,
            iptm_cutoff=args.iptm_cutoff,
            success_rate_filename=args.success_rate_filename,
        )
    else:
        print("无有效数据，跳过成功率统计", flush=True)


if __name__ == "__main__":
    main()
