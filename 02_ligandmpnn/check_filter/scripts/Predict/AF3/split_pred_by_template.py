#!/usr/bin/env python3
"""
将protenix的输入json文件转换成AlphaFold的输入文件
"""
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_template_data(template_data: Any) -> Dict[str, Any]:
    if isinstance(template_data, dict):
        return template_data

    if isinstance(template_data, list):
        if not template_data:
            raise ValueError("template.json 是空列表，无法提取模板")
        first_item = template_data[0]
        if not isinstance(first_item, dict):
            raise ValueError("template.json 列表首元素不是对象，无法作为模板")
        return first_item

    raise ValueError(
        f"template.json 顶层必须是对象或对象列表，当前类型: {type(template_data).__name__}"
    )


def map_job_to_template(
    job: Dict[str, Any], template: Dict[str, Any], seeds: List[int], template_needed_chains: List[int]
) -> Dict[str, Any]:
    template_sequences = template.get("sequences", [])
    out_sequences: List[Dict[str, Any]] = []

    for idx, seq_item in enumerate(job.get("sequences", [])):
        protein_chain = seq_item.get("proteinChain", {})
        msa = protein_chain.get("msa", {})
        msa_dir = msa.get("precomputed_msa_dir", "")
        msa_dir_path = Path(msa_dir)

        template_protein = {}
        if idx < len(template_sequences):
            template_protein = template_sequences[idx].get("protein", {})

        chain_index = idx + 1
        if 0 in template_needed_chains:
            templates_value: Any = []
        else:
            templates_value = None if chain_index in template_needed_chains else []

        out_sequences.append(
            {
                "protein": {
                    "sequence": protein_chain.get("sequence", ""),
                    "id": template_protein.get("id", chr(ord("A") + idx)),
                    "pairedMsaPath": str(msa_dir_path / "pairing.a3m"),
                    "unpairedMsaPath": str(msa_dir_path / "non_pairing.a3m"),
                    "templates": templates_value,
                }
            }
        )

    return {
        "name": job.get("name", template.get("name", "")),
        "modelSeeds": seeds,
        "dialect": template.get("dialect", "alphafold3"),
        "version": template.get("version", 2),
        "sequences": out_sequences,
    }


def split_pred(
    pred_path: Path,
    template_path: Path,
    outdir: Path,
    seeds: List[int],
    template_needed_chains: List[int],
) -> Path:
    pred_data = read_json(pred_path)
    template_raw = read_json(template_path)
    template_data = normalize_template_data(template_raw)

    if not isinstance(pred_data, list):
        raise ValueError("pred.json 顶层必须是列表")

    output_dir = outdir
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, job in enumerate(pred_data, start=1):
        if not isinstance(job, dict):
            raise ValueError(f"第 {i} 个 job 不是对象")

        converted = map_job_to_template(job, template_data, seeds, template_needed_chains)
        out_name = converted.get("name") or f"job_{i}"
        out_path = output_dir / f"{out_name}.json"

        with out_path.open("w", encoding="utf-8") as f:
            json.dump(converted, f, ensure_ascii=False, indent=4)
            f.write("\n")

    return output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将 pred.json 按 template.json 转换并拆分，每个 job 一个 json 文件"
    )
    parser.add_argument("--pred", required=True, help="pred.json 文件路径")
    parser.add_argument("--template", required=True, help="template.json 文件路径")
    parser.add_argument(
        "--seeds",
        required=True,
        nargs="+",
        type=int,
        help="模型随机种子，空格分隔，例如：--seeds 42 43 44",
    )
    parser.add_argument(
        "--outdir",
        required=True,
        help="输出目录（必填）",
    )
    parser.add_argument(
        "--template-needed-chains",
        required=True,
        nargs="+",
        type=int,
        help="控制 templates 字段：0 表示全部链为 []；1/2/... 表示对应链为 null，其余为 []，例如：--template-needed-chains 1",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pred_path = Path(args.pred).expanduser().resolve()
    template_path = Path(args.template).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    seeds = args.seeds
    template_needed_chains = args.template_needed_chains

    if any(i < 0 for i in template_needed_chains):
        raise ValueError("--template-needed-chains 只允许非负整数")

    if 0 in template_needed_chains and len(template_needed_chains) > 1:
        raise ValueError("当使用 0（全部不需要 templates）时，不能同时指定其它链序号")

    output_dir = split_pred(
        pred_path,
        template_path,
        outdir=outdir,
        seeds=seeds,
        template_needed_chains=template_needed_chains,
    )
    print(f"完成。输出目录: {output_dir}")


if __name__ == "__main__":
    main()
