import subprocess
import sys
import os
import time
from datetime import datetime

# 定义颜色代码以便在终端中清晰显示状态
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def log(message, level="INFO"):
    """简单的日志打印函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if level == "INFO":
        print(f"[{timestamp}] {Colors.OKBLUE}[INFO]{Colors.ENDC} {message}")
    elif level == "SUCCESS":
        print(f"[{timestamp}] {Colors.OKGREEN}[SUCCESS]{Colors.ENDC} {message}")
    elif level == "ERROR":
        print(f"[{timestamp}] {Colors.FAIL}[ERROR]{Colors.ENDC} {message}")

def run_step(script_name, arg1, arg2, step_description):
    """
    执行单个Benchmark步骤的通用函数
    
    Args:
        script_name (str): bash脚本名称 (e.g., benchmark_ligandmpnn.sh)
        arg1 (str): 第一个参数 (e.g., 输入文件夹路径)
        arg2 (str): 第二个参数 (e.g., 输出文件夹或模式名称)
        step_description (str): 步骤描述，用于日志
    """
    log(f"开始执行步骤: {step_description} ...")
    log(f"指令: bash {script_name} {arg1} {arg2}")

    # 检查脚本是否存在
    if not os.path.exists(script_name):
        log(f"找不到脚本文件: {script_name}", "ERROR")
        sys.exit(1)

    start_time = time.time()
    
    try:
        # 使用 subprocess.run 执行 bash 命令
        # check=True 会在脚本返回非零状态码时抛出异常
        result = subprocess.run(
            ["bash", script_name, arg1, arg2],
            check=True,
            text=True,
            capture_output=False # 如果设为True，则不会实时打印子脚本输出
        )
        
        elapsed_time = time.time() - start_time
        log(f"步骤 '{step_description}' 完成。耗时: {elapsed_time:.2f} 秒", "SUCCESS")
        
    except subprocess.CalledProcessError as e:
        log(f"步骤 '{step_description}' 执行失败！退出代码: {e.returncode}", "ERROR")
        sys.exit(1)
    except Exception as e:
        log(f"发生未预期的错误: {str(e)}", "ERROR")
        sys.exit(1)

def main():

    data_set = "Colabfold-noise-0.5"

    log("=== 启动多肽设计 Benchmark Pipeline ===")
    
    # --- 步骤 1: LigandMPNN 标准设计 ---
    # 输入: Merged.json
    # 模式: LigandMPNN
    run_step(
        script_name="benchmark_ligandmpnn.sh",
        arg1=f"datasets/{data_set}/Merged.json",
        arg2=f"outputs/{data_set}/LigandMPNN",
        step_description="LigandMPNN Design (Standard)"
    )
    
    print("-" * 50)

    # --- 步骤 2: LigandMPNN-HETATM 设计 ---
    # 输入: Processed.json (注意输入源变更)
    # 模式: LigandMPNN-HETATM
    run_step(
        script_name="benchmark_ligandmpnn.sh",
        arg1=f"datasets/{data_set}/Processed.json",
        arg2=f"outputs/{data_set}/LigandMPNN-HETATM",
        step_description="LigandMPNN Design (Explicit HETATM)"
    )

    # print("-" * 50)

    # # --- 步骤 3: ProteinMPNN 设计 ---
    # # 输入: Merged.json
    # # 模式: ProteinMPNN
    # run_step(
    #     script_name="benchmark_proteinmpnn.sh",
    #     arg1=f"datasets/{data_set}/Merged.json",
    #     arg2=f"outputs/{data_set}/ProteinMPNN",
    #     step_description="ProteinMPNN Design (Baseline)"
    # )

    # print("-" * 50)
 

    # # --- 步骤 4：Rosetta 设计 ---
    # run_step (
    #     script_name="benchmark_rosetta.sh",
    #     arg1=f"datasets/{data_set}/PDB.list",
    #     arg2=f"outputs/{data_set}/Rosetta",
    #     step_description="Rosetta Design"
    # )

    log("=== 所有 Benchmark 步骤均已成功完成 ===", "SUCCESS")

if __name__ == "__main__":
    main()


