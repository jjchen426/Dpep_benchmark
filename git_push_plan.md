# Benchmark Git 整理 .gitignore 修改方案（最终版）

## 各目录处理

### 01_structure_prediction

```
archive/
├── oldpredict_summary/
│   ├── csv_summary/  → 提交
│   ├── exports/      → 提交
│   ├── figures/      → 忽略
│   ├── logs/         → 忽略
│   └── *.ipynb, *.md, *.csv → 提交
models/
├── alphafold3/
│   ├── scripts/   → 提交
│   ├── inputs/    → 提交（852 JSON, 3.4M）
│   ├── outputs/   → 忽略
│   ├── data/      → 提交（DockQ/ipSAE/summary, 15M）
│   └── test/      → 忽略
├── esmfold2/
│   ├── scripts/   → 提交
│   ├── outputs/   → 忽略
│   ├── data/      → 提交（9.6M）
│   └── test/      → 忽略
├── protenix/
│   ├── scripts/   → 提交
│   ├── inputs/    → 提交（178 JSON, 1.7M）
│   ├── outputs/   → 忽略
│   ├── data/      → 提交（11M）
│   └── test/      → 忽略
summary/
├── src/     → 提交
├── summary/ → 提交
```

### 02_ligandmpnn

```
test_xxx/
├── scripts/   → 提交
├── inputs/    → 提交（~11,800 JSON, 53M）
├── data/      → 提交（~40M）
├── outputs/   → 忽略（~55G）
├── src/       → 忽略
├── test/      → 忽略
```

### 03_clash_metrics

```
├── scripts/ → 提交
├── data/    → 提交（output.png）
```

### 04_RFdiffusion2 — 整体忽略 + 3个例外

```
整体忽略, 例外：
├── gen_rfd2_file.ipynb  → ？用户未提及，暂定忽略
├── alanine-scan/ddg_plot/ddg_heatmap.tar.gz → 提交
├── alanine-scan/ddg_files/**/job.list → 提交（170个）
```

### dataset — 只保留 00_compressed + 脚本

```
├── 00_compressed/       → 提交（6个.gz, 129M）
├── *.ipynb              → 提交
├── *.py                 → 提交
├── 其他所有子目录        → 忽略（~700M）
```

### dataset_for_predict — 完全忽略

### Rosetta — 完全忽略

## .gitignore 完整内容

```gitignore
# ============================================
# 全局排除
# ============================================
*.tsv *.log *.pdb *.cif *.gz *.a3m *.fasta *.fa *.out
*.sc *.mutfile *.ddg *.m8 *.pml *.params *.sample *.trb
*.db *.h5
**/model_params/
*.csv
__pycache__/
*.pyc
.ipynb_checkpoints/
.mypy_cache/

# ============================================
# 01_structure_prediction
# ============================================
/01_structure_prediction/**/outputs/
/01_structure_prediction/**/test/
/01_structure_prediction/archive/oldpredict_summary/figures/

# ============================================
# 02_ligandmpnn
# ============================================
/02_ligandmpnn/**/outputs/
/02_ligandmpnn/**/src/
/02_ligandmpnn/**/test/
/02_ligandmpnn/**/__pycache__/

# 恢复汇总结果
!/02_ligandmpnn/**/outputs/**/*.csv
!/02_ligandmpnn/**/outputs/**/*.png

# ============================================
# 04_RFdiffusion2 — 整体忽略 + 例外
# ============================================
/04_RFdiffusion2/
!/04_RFdiffusion2/alanine-scan/ddg_plot/ddg_heatmap.tar.gz
!/04_RFdiffusion2/alanine-scan/ddg_files/**/job.list

# ============================================
# dataset — 只保留 00_compressed + 脚本
# ============================================
/dataset/*
!/dataset/00_compressed/
!/dataset/*.ipynb
!/dataset/*.py

# ============================================
# dataset_for_predict — 完全忽略
# ============================================
/dataset_for_predict/

# ============================================
# Rosetta — 完全忽略
# ============================================
/Rosetta/

# ============================================
# 根目录
# ============================================
!/README.md
!/readme-agent.md
!/check.ipynb
```

## 执行

仅修改 `.gitignore` 文件本身，不涉及其他 git 操作。
