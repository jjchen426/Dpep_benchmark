# pipeline_metrics_parallel.py 分析与优化方案

## 当前问题

### 1. PDB ID 匹配 Bug
`read_pdb_list()` 读取 PDB.list 的完整路径（如 `/path/to/3obq.pdb`）存入 `pdb_set`，
但在 `collect_metrics_for_output_dir` 中匹配时用的是 `re.sub(r"_\d+$", "", design_name)` 提取的纯 ID（如 `3obq`），
导致永远匹配不上，`parent_to_design_dirs` 始终为空。

**修复方案**：改用 JSON mapping 文件，用户显式指定设计目录名 → ref PDB 名的映射。

### 2. Biopython CIF 全量解析
`FastMMCIFParser.get_structure()` 每次解析整个 CIF 文件为完整的四级层次结构（Model→Chain→Residue→Atom），
但实际只需要 2 条链（肽链 + 对齐链）的 4 种骨架原子（N, CA, C, O）坐标。

**优化方案**：轻量级 mmCIF 解析，只提取目标链的骨架原子坐标，直接输出 numpy 数组。

### 3. Biopython Superimposer 对象开销
每样本创建新的 `Superimposer()`，内部操作 Biopython Atom 对象。

**优化方案**：numpy-only Kabsch 算法，输入输出均为 numpy 数组。

### 4. CSV 轮询 I/O
`collect_metrics_for_output_dir` 返回 DataFrame，但 `compute_success_rates` 重新从 CSV 读回。

**优化方案**：直接传递 DataFrame。

### 5. 多 cutoff 重复 groupby
`compute_success_rates` 对每个 cutoff 重复 `drop_duplicates().groupby()`。

**优化方案**：向量化计算。

## 现有代码结构
- `parse_args()` / `validate_args()` — 参数解析
- `read_pdb_list()` — 读 PDB.list（将被替换）
- `process_single_sample()` — 处理单个 sample 目录
- `process_parent_group()` — 处理一个 parent_complex 的所有 design dirs
- `_run_parent_groups()` — 并行分发 parent groups
- `collect_metrics_for_output_dir()` — 主流程
- `compute_success_rates()` — 统计成功率

## 目录结构参考
```
outputs/
  1a0n_1/                    # 设计目录
    seed-42_sample-0/        # sample 子目录
      1a0n_1_seed-42_sample-0_model.cif
      1a0n_1_seed-42_sample-0_confidences.json
      1a0n_1_seed-42_sample-0_summary_confidences.json
    seed-42_sample-1/
    ...
```
