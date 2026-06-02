import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from Bio.PDB import PDBParser, FastMMCIFParser, Superimposer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="在当前AlphaFold3输出目录中计算RMSD指标并统计成功率"
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
        default="metrics_summary-seed42_43_44.csv",
        help="RMSD汇总输出文件名",
    )
    parser.add_argument(
        "--filtered-filename-template",
        type=str,
        default="metrics_filtered_scRMSD_le{cutoff}-seed42_43_44.csv",
        help="RMSD过滤输出文件名模板，支持占位符{cutoff}",
    )
    parser.add_argument(
        "--success-rate-filename",
        type=str,
        default="success_rates_by_parent_complex.csv",
        help="成功率统计输出文件名",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> tuple[set[str], list[float]]:
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

    return backbone_atoms, cutoffs


def read_pdb_list(pdb_list_path: Path) -> list[str]:
    with pdb_list_path.open("r") as f:
        return [line.strip() for line in f if line.strip()]


def parse_seed_sample(sample_name: str) -> tuple[int, int] | None:
    match = re.fullmatch(r"seed-(\d+)_sample-(\d+)", sample_name)
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


def get_backbone_atoms(chain, backbone_atoms: set[str]):
    return [atom for atom in chain.get_atoms() if atom.get_id() in backbone_atoms]


def get_first_non_target_chain(model, target_chain_id: str):
    for chain in model:
        if chain.id != target_chain_id:
            return chain
    return None


def compute_sc_rmsd(
    ref_chain,
    pred_chain,
    align_ref_chain,
    align_pred_chain,
    backbone_atoms: set[str],
) -> float | None:
    align_ref_atoms = get_backbone_atoms(align_ref_chain, backbone_atoms)
    align_pred_atoms = get_backbone_atoms(align_pred_chain, backbone_atoms)
    if len(align_ref_atoms) == 0 or len(align_pred_atoms) == 0:
        return None
    if len(align_ref_atoms) != len(align_pred_atoms):
        return None

    sup = Superimposer()
    try:
        sup.set_atoms(align_ref_atoms, align_pred_atoms)
    except Exception:
        return None
    rot, tran = sup.rotran

    ref_atoms = get_backbone_atoms(ref_chain, backbone_atoms)
    pred_atoms = get_backbone_atoms(pred_chain, backbone_atoms)
    if len(ref_atoms) == 0 or len(pred_atoms) == 0:
        return None
    if len(ref_atoms) != len(pred_atoms):
        return None

    ref_coords = np.array([atom.get_coord() for atom in ref_atoms], dtype=float)
    pred_coords = np.array([atom.get_coord() for atom in pred_atoms], dtype=float)
    pred_coords_aligned = pred_coords @ rot + tran

    diffs = ref_coords - pred_coords_aligned
    return round(float(np.sqrt(np.mean(np.sum(diffs**2, axis=1)))), 4)


def process_single_sample(
    sample_prefix: str,
    sample_dir: Path,
    structure_ref,
    chain_ref_pep,
    mmcifparser: FastMMCIFParser,
    peptide_chain_id: str,
    backbone_atoms: set[str],
) -> tuple[tuple | None, str | None]:
    sample_name = sample_dir.name
    parsed = parse_seed_sample(sample_name)
    if parsed is None:
        return None, "bad_sample_dir_name"
    seed, sample_id = parsed

    conf_json_path = sample_dir / f"{sample_prefix}_{sample_name}_confidences.json"
    summary_json_path = sample_dir / f"{sample_prefix}_{sample_name}_summary_confidences.json"
    cif_path = sample_dir / f"{sample_prefix}_{sample_name}_model.cif"
    if not (conf_json_path.exists() and summary_json_path.exists() and cif_path.exists()):
        return None, "missing_required_files"

    with conf_json_path.open("r") as f_json:
        conf_data = json.load(f_json)
    atom_chain_ids = conf_data.get("atom_chain_ids", [])
    atom_plddts = conf_data.get("atom_plddts", [])
    if len(atom_chain_ids) == 0 or len(atom_chain_ids) != len(atom_plddts):
        return None, "invalid_confidences_json"

    b_chain_plddt = [
        float(plddt)
        for chain_id, plddt in zip(atom_chain_ids, atom_plddts)
        if chain_id == peptide_chain_id
    ]
    if len(b_chain_plddt) == 0:
        return None, "missing_peptide_chain_plddt"
    pep_plddt = round(float(np.mean(b_chain_plddt)), 4)

    with summary_json_path.open("r") as f_json:
        summary_data = json.load(f_json)
    if "iptm" not in summary_data or "ranking_score" not in summary_data:
        return None, "invalid_summary_json"
    iptm = round(float(summary_data["iptm"]), 4)
    ranking_score = round(float(summary_data["ranking_score"]), 4)

    structure_pred = mmcifparser.get_structure("pred", str(cif_path))
    try:
        chain_pred_pep = structure_pred[0][peptide_chain_id]
    except KeyError:
        return None, "missing_peptide_chain_in_pred"

    align_chain_ref = get_first_non_target_chain(structure_ref[0], peptide_chain_id)
    align_chain_pred = get_first_non_target_chain(structure_pred[0], peptide_chain_id)
    if align_chain_ref is None or align_chain_pred is None:
        return None, "missing_align_chain"

    sc_rmsd = compute_sc_rmsd(
        chain_ref_pep,
        chain_pred_pep,
        align_chain_ref,
        align_chain_pred,
        backbone_atoms,
    )
    if sc_rmsd is None:
        return None, "rmsd_alignment_failed"

    return (
        sample_prefix,
        seed,
        sample_id,
        pep_plddt,
        iptm,
        ranking_score,
        sc_rmsd,
    ), None


def collect_metrics_for_output_dir(
    pdbs: list[str],
    pdbparser: PDBParser,
    mmcifparser: FastMMCIFParser,
    ref_pdb_base: Path,
    output_base: Path,
    peptide_chain_id: str,
    backbone_atoms: set[str],
    rmsd_filter_cutoff: float,
    summary_filename: str,
    filtered_filename_template: str,
) -> pd.DataFrame:
    if not output_base.is_dir():
        raise NotADirectoryError(f"输出目录不存在: {output_base}")

    rows = []
    matched_design_dirs = 0
    total_sample_dirs = 0
    skip_reasons: dict[str, int] = {}
    pdb_set = set(pdbs)
    ref_structure_cache: dict[str, tuple] = {}

    design_dirs = [d for d in output_base.iterdir() if d.is_dir()]
    for design_dir in sorted(design_dirs):
        design_name = design_dir.name
        parent_complex = re.sub(r"_\d+$", "", design_name)
        if parent_complex not in pdb_set:
            skip_reasons["parent_not_in_pdb_list"] = skip_reasons.get("parent_not_in_pdb_list", 0) + 1
            continue

        if parent_complex not in ref_structure_cache:
            ref_pdb_path = ref_pdb_base / f"{parent_complex}.pdb"
            if not ref_pdb_path.exists():
                skip_reasons["missing_ref_pdb"] = skip_reasons.get("missing_ref_pdb", 0) + 1
                continue
            structure_ref = pdbparser.get_structure("ref", str(ref_pdb_path))
            try:
                chain_ref_pep = structure_ref[0][peptide_chain_id]
            except KeyError:
                skip_reasons["missing_peptide_chain_in_ref"] = skip_reasons.get("missing_peptide_chain_in_ref", 0) + 1
                continue
            ref_structure_cache[parent_complex] = (structure_ref, chain_ref_pep)

        structure_ref, chain_ref_pep = ref_structure_cache[parent_complex]
        matched_design_dirs += 1

        sample_dirs = [
            d for d in design_dir.iterdir()
            if d.is_dir() and re.fullmatch(r"seed-\d+_sample-\d+", d.name)
        ]
        total_sample_dirs += len(sample_dirs)
        for sample_dir in sorted(sample_dirs):
            row, reason = process_single_sample(
                sample_prefix=design_name,
                sample_dir=sample_dir,
                structure_ref=structure_ref,
                chain_ref_pep=chain_ref_pep,
                mmcifparser=mmcifparser,
                peptide_chain_id=peptide_chain_id,
                backbone_atoms=backbone_atoms,
            )
            if row is not None:
                rows.append(row)
            else:
                skip_reasons[reason] = skip_reasons.get(reason, 0) + 1

    result = pd.DataFrame(
        rows,
        columns=["complex", "seed", "id", "pep_plddt", "iptm", "ranking_score", "scRMSD"],
    )

    result.to_csv(output_base / summary_filename, index=False)
    result_filtered = result[result["scRMSD"] <= rmsd_filter_cutoff].reset_index(drop=True)
    cutoff_token = str(rmsd_filter_cutoff).replace(".", "")
    result_filtered.to_csv(
        output_base / filtered_filename_template.format(cutoff=cutoff_token),
        index=False,
    )

    print(f"匹配到设计目录: {matched_design_dirs}")
    print(f"二级sample目录总数: {total_sample_dirs}")
    print(f"成功写入行数: {len(result)}")
    if skip_reasons:
        print(f"跳过原因统计: {skip_reasons}")

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
    if not summary_csv.exists():
        print(f"未找到文件: {summary_csv}")
        return pd.DataFrame()

    df = pd.read_csv(summary_csv)
    if df.empty:
        print(f"指标为空: {summary_csv}")
        return pd.DataFrame()

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
            (df["pep_plddt"] >= pep_plddt_cutoff)
            & (df["iptm"] >= iptm_cutoff)
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
        stat["success_rate"] = (stat["successful_designs"] / stat["total_designs"] * 100).round(2)
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
    backbone_atoms, cutoffs = validate_args(args)

    pdbs = read_pdb_list(args.pdb_list)
    pdbparser = PDBParser(QUIET=True)
    mmcifparser = FastMMCIFParser(QUIET=True)

    collect_metrics_for_output_dir(
        pdbs=pdbs,
        pdbparser=pdbparser,
        mmcifparser=mmcifparser,
        ref_pdb_base=args.ref_pdb_base,
        output_base=args.output_base,
        peptide_chain_id=args.peptide_chain,
        backbone_atoms=backbone_atoms,
        rmsd_filter_cutoff=args.rmsd_filter_cutoff,
        summary_filename=args.summary_filename,
        filtered_filename_template=args.filtered_filename_template,
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
