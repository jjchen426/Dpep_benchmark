import json
import os
import re
import subprocess
import time
from datetime import datetime
from itertools import product
from pathlib import Path

import pandas as pd


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"


def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if level == "INFO":
        print(f"[{timestamp}] {Colors.OKBLUE}[INFO]{Colors.ENDC} {message}")
    elif level == "SUCCESS":
        print(f"[{timestamp}] {Colors.OKGREEN}[SUCCESS]{Colors.ENDC} {message}")
    elif level == "WARNING":
        print(f"[{timestamp}] {Colors.WARNING}[WARNING]{Colors.ENDC} {message}")
    elif level == "ERROR":
        print(f"[{timestamp}] {Colors.FAIL}[ERROR]{Colors.ENDC} {message}")


def fail_or_warn(message, strict_mode=True):
    if strict_mode:
        log(message, "ERROR")
        raise RuntimeError(message)
    log(message, "WARNING")
    return False


def normalize_temp(temp_value):
    return (f"{float(temp_value):.4f}").rstrip("0").rstrip(".")


def safe_ckpt_name(ckpt_path):
    return Path(ckpt_path).stem.replace("/", "_")


def run_step(script_path, args, step_description):
    log(f"开始执行步骤: {step_description}")
    log("指令: " + " ".join(["bash", script_path] + args))

    if not os.path.exists(script_path):
        raise FileNotFoundError(f"找不到脚本文件: {script_path}")

    start_time = time.time()
    subprocess.run(["bash", script_path] + args, check=True, text=True, capture_output=False)
    elapsed_time = time.time() - start_time
    log(f"步骤 '{step_description}' 完成。耗时: {elapsed_time:.2f} 秒", "SUCCESS")
    return elapsed_time


def read_pipeline_list(pipeline_list_path):
    with open(pipeline_list_path, "r") as handle:
        raw = [line.strip() for line in handle if line.strip() and not line.strip().startswith("#")]
    return raw


def write_jobs_json(pdb_paths, json_path):
    payload = {p: "" for p in pdb_paths}
    with open(json_path, "w") as handle:
        json.dump(payload, handle, indent=2)


def extract_seq_rec_from_fa(fa_path):
    values = []
    with open(fa_path, "r") as handle:
        for line in handle:
            match = re.search(r"seq_rec=(\d+\.\d+)", line)
            if match:
                values.append(round(float(match.group(1)) * 100, 2))
    return values


def collect_seqrec_for_combo(combo_output_dir, target_pdb_set, dataset_name, method, temp, ckpt):
    rows = []
    combo_dir = Path(combo_output_dir)
    if not combo_dir.exists():
        return rows

    for fa_path in combo_dir.rglob("*.fa"):
        pdb_name = fa_path.stem
        if pdb_name not in target_pdb_set:
            continue
        seq_values = extract_seq_rec_from_fa(fa_path)
        for seq_value in seq_values:
            rows.append(
                {
                    "dataset": dataset_name,
                    "method": method,
                    "temperature": temp,
                    "checkpoint": ckpt,
                    "pdb": pdb_name,
                    "seq_rec": seq_value,
                    "fa_path": str(fa_path),
                }
            )
    return rows


def find_existing_pipeline_list_file(dataset_dir: Path):
    pipeline_list = dataset_dir / "pipeline.list"
    if pipeline_list.exists():
        return pipeline_list
    return None


def create_pipeline_list_if_missing(dataset_dir: Path):
    pipeline_list_path = dataset_dir / "pipeline.list"
    if pipeline_list_path.exists():
        return pipeline_list_path

    pdb_paths = sorted([str(p.resolve()) for p in dataset_dir.rglob("*.pdb") if p.is_file()])
    if len(pdb_paths) == 0:
        return None

    with open(pipeline_list_path, "w") as handle:
        handle.write("\n".join(pdb_paths) + "\n")
    log(f"已自动创建 pipeline.list: {pipeline_list_path}（{len(pdb_paths)} 条）", "SUCCESS")
    return pipeline_list_path


def resolve_or_create_pipeline_list(dataset_dir: Path):
    existing = find_existing_pipeline_list_file(dataset_dir)
    if existing is not None:
        return existing
    return create_pipeline_list_if_missing(dataset_dir)


def build_dataset_configs(database_root):
    dataset_configs = []
    for dataset_dir in sorted(Path(database_root).iterdir()):
        if not dataset_dir.is_dir():
            continue
        dataset_name = dataset_dir.name
        pipeline_list_path = resolve_or_create_pipeline_list(dataset_dir)
        dataset_configs.append(
            {
                "name": dataset_name,
                "dir": str(dataset_dir),
                "pipeline_list": str(pipeline_list_path) if pipeline_list_path else "",
            }
        )
    return dataset_configs


def methods_for_dataset(dataset_name):
    if "HETATM" in dataset_name.upper():
        return ["LigandMPNN-HETATM"]
    return ["LigandMPNN", "ProteinMPNN", "PeptideMPNN"]


def normalize_temperatures(temperatures):
    if not isinstance(temperatures, (list, tuple)) or len(temperatures) == 0:
        raise ValueError("temperatures 必须是非空列表，例如 [0.1, 0.2]")

    normalized = []
    for temp in temperatures:
        try:
            normalized.append(float(temp))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"温度值无效: {temp}") from exc
    return normalized


def normalize_weights_by_method(weights_by_method):
    if not isinstance(weights_by_method, dict) or len(weights_by_method) == 0:
        raise ValueError("weights_by_method 必须是非空字典")

    normalized = {}
    for method_name, ckpt_list in weights_by_method.items():
        if not isinstance(ckpt_list, (list, tuple)) or len(ckpt_list) == 0:
            raise ValueError(f"{method_name} 的权重列表不能为空")

        normalized_ckpts = []
        for ckpt in ckpt_list:
            ckpt_path = Path(str(ckpt)).expanduser().resolve()
            if not ckpt_path.exists():
                raise FileNotFoundError(f"checkpoint 不存在: {ckpt_path}")
            normalized_ckpts.append(str(ckpt_path))
        normalized[method_name] = normalized_ckpts

    return normalized


def validate_sampling_config(batch_size, number_of_batches):
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError("batch_size 必须是正整数")
    if not isinstance(number_of_batches, int) or number_of_batches <= 0:
        raise ValueError("number_of_batches 必须是正整数")


def validate_save_pdb_config(save_pdb):
    if isinstance(save_pdb, bool):
        return int(save_pdb)

    if isinstance(save_pdb, int) and save_pdb in (0, 1):
        return save_pdb

    if isinstance(save_pdb, str) and save_pdb.strip() in {"0", "1"}:
        return int(save_pdb.strip())

    raise ValueError("save_pdb 必须是 0 或 1")


def main(
    database_path,
    output_root,
    chains_to_design,
    temperatures,
    weights_by_method,
    batch_size,
    number_of_batches,
    save_pdb=0,
    dry_run=False,
):
    log("=== 启动多数据集 Benchmark Pipeline ===")

    if database_path is None or str(database_path).strip() == "":
        raise ValueError("必须手动传入 database_path，例如 '/path/to/database'")
    if output_root is None or str(output_root).strip() == "":
        raise ValueError("必须手动传入 output_root，例如 '/path/to/outputs'")
    if chains_to_design is None or str(chains_to_design).strip() == "":
        raise ValueError("必须手动传入 chains_to_design，例如 'L' 或 'A,B'")

    workspace_dir = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
    database_root = Path(database_path).expanduser().resolve()
    output_base = Path(output_root).expanduser().resolve()
    output_base.mkdir(parents=True, exist_ok=True)
    chains_to_design = str(chains_to_design).strip()
    temperatures = normalize_temperatures(temperatures)
    weights_by_method = normalize_weights_by_method(weights_by_method)
    validate_sampling_config(batch_size, number_of_batches)
    save_pdb = validate_save_pdb_config(save_pdb)
    strict_mode = True

    method_scripts = {
        "LigandMPNN": str(workspace_dir / "benchmark_ligandmpnn.sh"),
        "LigandMPNN-HETATM": str(workspace_dir / "benchmark_ligandmpnn.sh"),
        "ProteinMPNN": str(workspace_dir / "benchmark_proteinmpnn.sh"),
        "PeptideMPNN": str(workspace_dir / "benchmark_proteinmpnn.sh"),
    }

    if not database_root.exists():
        raise FileNotFoundError(f"database目录不存在: {database_root}")

    dataset_configs = build_dataset_configs(database_root)
    if len(dataset_configs) == 0:
        raise RuntimeError(f"database目录下没有可用数据集子目录: {database_root}")

    if dry_run:
        log("当前为 DRY_RUN 模式：仅生成 pipeline.list / jobs.json，并打印执行计划，不调用 MPNN", "WARNING")

    run_records = []
    seqrec_rows_all = []

    for dataset in dataset_configs:
        dataset_name = dataset["name"]
        log(f"=== 处理数据集: {dataset_name} ===")

        if not dataset["pipeline_list"]:
            fail_or_warn(f"{dataset_name} 缺少 pipeline.list 且未发现可用于自动生成的 .pdb 文件", strict_mode)
            continue

        pipeline_list_path = Path(dataset["pipeline_list"])
        if not pipeline_list_path.exists():
            fail_or_warn(f"缺少 pipeline.list: {pipeline_list_path}", strict_mode)
            continue

        pdb_abs_paths = read_pipeline_list(pipeline_list_path)
        if len(pdb_abs_paths) == 0:
            fail_or_warn(f"pipeline.list 为空: {pipeline_list_path}", strict_mode)
            continue

        missing_paths = [p for p in pdb_abs_paths if not os.path.isabs(p) or not Path(p).exists()]
        if len(missing_paths) > 0:
            fail_or_warn(f"pipeline.list 中存在无效路径，示例: {missing_paths[:3]}", strict_mode)
            continue

        target_pdb_set = {Path(p).stem for p in pdb_abs_paths}

        dataset_out_root = output_base / dataset_name
        dataset_out_root.mkdir(parents=True, exist_ok=True)

        jobs_json_path = dataset_out_root / f"{dataset_name}.json"
        write_jobs_json(pdb_abs_paths, jobs_json_path)

        candidate_methods = methods_for_dataset(dataset_name)
        enabled_methods = [
            m for m in candidate_methods if m in weights_by_method and len(weights_by_method[m]) > 0
        ]
        if len(enabled_methods) == 0:
            fail_or_warn(
                f"数据集 {dataset_name} 没有可运行的方法：候选={candidate_methods}，已配置={list(weights_by_method.keys())}",
                strict_mode,
            )
            continue

        log(f"数据集 {dataset_name} 候选方法: {candidate_methods}")
        log(f"数据集 {dataset_name} 实际运行方法(按权重过滤后): {enabled_methods}")

        for method in enabled_methods:
            method_script = method_scripts[method]
            input_json = str(jobs_json_path)

            for temp, ckpt in product(temperatures, weights_by_method[method]):
                temp_str = normalize_temp(temp)
                ckpt_name = safe_ckpt_name(ckpt)
                combo_name = f"temp_{temp_str}_ckpt_{ckpt_name}"
                combo_out_dir = dataset_out_root / method / combo_name

                record = {
                    "dataset": dataset_name,
                    "method": method,
                    "temperature": temp_str,
                    "checkpoint": ckpt,
                    "chains_to_design": chains_to_design,
                    "batch_size": batch_size,
                    "number_of_batches": number_of_batches,
                    "save_pdb": save_pdb,
                    "total_samples": batch_size * number_of_batches,
                    "input_json": input_json,
                    "output_dir": str(combo_out_dir),
                    "status": "FAILED",
                    "elapsed_sec": None,
                    "error": "",
                }

                if dry_run:
                    record["status"] = "DRY_RUN"
                    log(
                        f"[DRY_RUN] 计划执行: dataset={dataset_name}, method={method}, temp={temp_str}, ckpt={ckpt}, batch_size={batch_size}, number_of_batches={number_of_batches}, save_pdb={save_pdb}, input_json={input_json}",
                        "INFO",
                    )
                    run_records.append(record)
                    continue

                try:
                    elapsed = run_step(
                        script_path=method_script,
                        args=[
                            input_json,
                            str(combo_out_dir),
                            str(temp),
                            ckpt,
                            chains_to_design,
                            str(batch_size),
                            str(number_of_batches),
                            str(save_pdb),
                        ],
                        step_description=f"{dataset_name} | {method} | {combo_name}",
                    )
                    record["status"] = "SUCCESS"
                    record["elapsed_sec"] = round(elapsed, 2)

                    seq_rows = collect_seqrec_for_combo(
                        combo_output_dir=combo_out_dir,
                        target_pdb_set=target_pdb_set,
                        dataset_name=dataset_name,
                        method=method,
                        temp=temp_str,
                        ckpt=ckpt,
                    )
                    if len(seq_rows) == 0:
                        msg = f"未找到有效seq_rec记录: {dataset_name}/{method}/{combo_name}"
                        if strict_mode:
                            raise RuntimeError(msg)
                        log(msg, "WARNING")
                    seqrec_rows_all.extend(seq_rows)

                except Exception as exc:
                    record["error"] = str(exc)
                    log(
                        f"组合失败: dataset={dataset_name}, method={method}, temp={temp_str}, ckpt={ckpt} | {exc}",
                        "ERROR",
                    )
                    run_records.append(record)
                    if strict_mode:
                        run_df = pd.DataFrame(run_records)
                        run_df.to_csv(dataset_out_root / "run_metadata.csv", index=False)
                        raise
                    continue

                run_records.append(record)

        run_df = pd.DataFrame([r for r in run_records if r["dataset"] == dataset_name])
        run_df.to_csv(dataset_out_root / "run_metadata.csv", index=False)

        if dry_run:
            log(f"数据集 {dataset_name} 在 DRY_RUN 模式下跳过 seq_rec 统计", "WARNING")
            continue

        dataset_seq_rows = [r for r in seqrec_rows_all if r["dataset"] == dataset_name]
        if len(dataset_seq_rows) > 0:
            details_df = pd.DataFrame(dataset_seq_rows)
            details_path = dataset_out_root / "seqrec_details.csv"
            details_df.to_csv(details_path, index=False)

            summary_df = (
                details_df.groupby(["dataset", "method", "temperature", "checkpoint"], as_index=False)["seq_rec"]
                .agg(["count", "mean", "std", "min", "max"])
                .reset_index()
            )
            summary_path = dataset_out_root / "seqrec_summary.csv"
            summary_df.to_csv(summary_path, index=False)
            log(f"已写出统计结果: {summary_path}", "SUCCESS")
        else:
            log(f"数据集 {dataset_name} 无可用 seq_rec 记录", "WARNING")

    all_run_df = pd.DataFrame(run_records)
    all_run_path = output_base / "run_metadata_all.csv"
    all_run_df.to_csv(all_run_path, index=False)

    log(f"全局运行记录已写出: {all_run_path}", "SUCCESS")
    log("=== Pipeline 执行结束 ===", "SUCCESS")


BASE_DIR = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
MODEL_DIR = BASE_DIR / "model_params"

DATABASE_PATH = "/home/junjiechen/1_work/250401-Dpepalign/Benchmark/ligandmpnn/test_hyperparam/database"
OUTPUT_ROOT = "/home/junjiechen/1_work/250401-Dpepalign/Benchmark/ligandmpnn/test_hyperparam/outputs-peptidempnn"
DESIGN_CHAINS = "B"
TEMPERATURES = [0.1,0.2,0.3,0.4,0.5]
WEIGHTS_BY_METHOD = {
    # "LigandMPNN": [
    #     str(MODEL_DIR / "ligandmpnn_v_32_005_25.pt"),
    #     str(MODEL_DIR / "ligandmpnn_v_32_010_25.pt"),
    #     str(MODEL_DIR / "ligandmpnn_v_32_020_25.pt"),
    #     str(MODEL_DIR / "ligandmpnn_v_32_030_25.pt"),
    # ],
    # "LigandMPNN-HETATM": [
    #     str(MODEL_DIR / "ligandmpnn_v_32_005_25.pt"),
    #     str(MODEL_DIR / "ligandmpnn_v_32_010_25.pt"),
    #     str(MODEL_DIR / "ligandmpnn_v_32_020_25.pt"),
    #     str(MODEL_DIR / "ligandmpnn_v_32_030_25.pt"),
    # ],
    # "ProteinMPNN": [
    #     str(MODEL_DIR / "proteinmpnn_v_48_002.pt"),
    #     str(MODEL_DIR / "proteinmpnn_v_48_010.pt"),
    #     str(MODEL_DIR / "proteinmpnn_v_48_020.pt"),
    #     str(MODEL_DIR / "proteinmpnn_v_48_030.pt"),
    # ],
    "PeptideMPNN": [
        str(BASE_DIR / "PeptideMPNN_weight" / "epoch_last.pt"),
    ],
}
BATCH_SIZE = 10
NUMBER_OF_BATCHES = 1
SAVE_PDB = 0
DRY_RUN = False

main(
    database_path=DATABASE_PATH,
    output_root=OUTPUT_ROOT,
    chains_to_design=DESIGN_CHAINS,
    temperatures=TEMPERATURES,
    weights_by_method=WEIGHTS_BY_METHOD,
    batch_size=BATCH_SIZE,
    number_of_batches=NUMBER_OF_BATCHES,
    save_pdb=SAVE_PDB,
    dry_run=DRY_RUN,
)