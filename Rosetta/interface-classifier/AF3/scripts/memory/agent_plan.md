# pipeline_metrics_v2.py 实现方案

## 目标
基于 `pipeline_metrics_parallel.py`，修复 PDB 匹配 bug 并引入算法优化，输出为新文件 `pipeline_metrics_v2.py`。

## 新增 JSON 输入方案

### `--mapping-json` 参数
替代 `--pdb-list`，接收 JSON 文件格式：
```json
{"1a0n_1": "1a0n", "1a0n_2": "1a0n", "3obq_1": "3obq"}
```

### 流程变化
1. 读 JSON → `{design_name: ref_name, ...}`
2. 按 `ref_name` 分组（同一 ref 的 design dirs 一起处理，复用 ref PDB 解析结果）
3. 每组：解析一次 ref PDB → 遍历所有 design dirs → 遍历所有 samples
4. 不再需要 `re.sub(r"_\d+$", "", design_name)` 匹配

## 保留的原有参数
- `--ref-pdb-base` — ref PDB 目录
- `--output-base` — AF3 输出目录
- `--peptide-chain` — 肽链 ID（默认 B）
- `--backbone-atoms` — 骨架原子
- `--sc-rmsd-cutoffs` / `--pep-plddt-cutoff` / `--iptm-cutoff` / `--rmsd-filter-cutoff`
- 输出文件名参数
- `--num-workers` / `--progress-every`

## 算法优化

### 1. 轻量 mmCIF 解析（替代 FastMMCIFParser）
- 按行读取 CIF，找到 `_atom_site` loop 的列定义
- 记录 `label_asym_id`（链ID）、`label_atom_id`（原子名）、`Cartn_x/y/z` 的列索引
- 遍历数据行，只提取目标链的骨架原子坐标
- 返回 `{chain_id: {backbone_atom: np.array([x,y,z]), ...}, ...}`

### 2. numpy Kabsch（替代 Superimposer）
- 输入两个 numpy 数组（N×3）
- 减去质心 → SVD 求旋转矩阵 → 处理反射 → 旋转坐标 → 计算 RMSD

### 3. 直接传 DataFrame
- `collect_metrics()` 返回 DataFrame 直接传入 `compute_success_rates()`

### 4. 向量化 success rate
- 预计算所有 cutoffs 的过滤条件，一次性 groupby

## 修改的文件

### 新建: `pipeline_metrics_v2.py`
完整新脚本，包含所有上述优化。

### 修改: `process.ipynb`
更新调用命令，将 `--pdb-list` 替换为 `--mapping-json`。

## 验证
1. 准备一个简单的 mapping JSON（手动挑选少量设计目录）
2. 运行 `pipeline_metrics_v2.py` 验证输出
3. 确认 `metrics_summary.csv`、`success_rates*` 等输出文件正确生成
