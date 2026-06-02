# 编写python脚本，循环执行benchmark_rosetta.sh脚本，提供的第一个参数为包含PDB文件相对路径的列表文件PepSet-noise/Merged_PDBs/6h7b.pdb，第二个参数为输出目录outputs/PepSet-noise
import sys
import os

noises = [0, 0.1, 0.2, 0.3, 0.4, 0.5]
for noise in noises:
    if noise == 0:
        base_input = "./datasets/PepSet/Merged_PDBs/4x2h.pdb"
        base_output = "./outputs/PepSet/Rosetta"
    else:
        base_input = f"./datasets/PepSet-noise-{noise}/Merged_PDBs/4x2h.pdb"
        base_output = f"./outputs/PepSet-noise-{noise}/Rosetta"
    os.system(f"bash benchmark_rosetta.sh {base_input} {base_output}")