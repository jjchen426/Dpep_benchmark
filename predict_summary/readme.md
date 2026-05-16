# 2026.03.26
## junjiechen


# eval_af3_ptx.ipynb 使用说明（逐单元详解）

本文档详细解释 `eval_af3_ptx.ipynb` 中每一个代码单元的功能、输入输出、运行方式、可配置参数及常见问题，帮助你稳定复现实验流程。

---

## 1. Notebook 目标与整体流程

该 Notebook 的核心目标是：

1. 从多种方法（AlphaFold3 / Protenix 不同配置）结果目录收集 `metrics_summary.csv`。
2. 做统一的质量控制（每个 `(method, parent_pdb)` 必须为 15 个样本）。
3. 生成分 PDB 与全局（Top1 / Oracle / <=2.5Å）scRMSD 可视化结果。
4. 以模板风格导出全局 CSV（方法为行，先 Oracle 列块，再 Rank1 列块），并额外导出 `scRMSD<=2.5Å` 过滤版。

推荐执行顺序：**Cell 1 → Cell 2 → Cell 3 → Cell 4 → Cell 5**（本 Notebook 全为代码单元）。

---

## 2. 运行前准备

### 2.1 环境依赖

Notebook 依赖以下 Python 包：

- `pandas`
- `seaborn`
- `matplotlib`
- 标准库：`pathlib`, `datetime`, `shutil`

### 2.2 数据前提

- 每个方法目录下按父 PDB 组织数据，且存在：
  - `<method_root>/<parent_pdb>/metrics_summary.csv`
- `pdb_list_path` 指向的 `PDB.list` 文件存在且内容合法。
- `metrics_summary.csv` 至少需包含：
  - `complex`, `seed`, `id`, `scRMSD`
- 若要生成 Top1 全局图，还需要 `ranking_score` 列。

### 2.3 输出目录规则

Cell 1 会自动创建以下目录（基于 notebook 当前工作目录）：

- `logs/`
- `figures/`
- `exports/`
- `exports/<YYYYMMDD>/`
- `csv_summary/`
- `csv_summary/<YYYYMMDD>/`

其中 `<YYYYMMDD>` 来自 `run_tag` 前 8 位。

---

## 3. Cell 1：参数区与全局初始化

### 3.1 功能

Cell 1 完成全局配置和基础初始化：

1. 导入所需库。
2. 定义模型输入路径字典 `model_roots`（键为方法名，值为目录路径）。
3. 定义 `pdb_list_path` 与 QC 规则 `required_samples_per_group=15`。
4. 设置绘图参数（字号、横坐标旋转等）和测试模式。
5. 生成 `run_tag` 与日期子目录。
6. 定义并调用 `load_pdb_list()` 读取 PDB 列表。
7. 打印关键运行配置，便于追踪。

### 3.2 核心可配置项

- `model_roots`：方法名与源目录映射，决定后续统计与绘图方法顺序。
- `pdb_list_path`：要处理的父 PDB 列表文件。
- `required_samples_per_group`：每个 `(method, parent_pdb)` 期望样本数（当前 15）。
- 绘图参数：
  - `axis_title_fontsize`
  - `plot_title_fontsize`
  - `tick_label_fontsize`
  - `method_label_wrap_width`（目前变量定义了，但后续绘图并未直接使用该宽度做自动换行）
  - `x_tick_rotation`
- 测试模式：
  - `test_only_single_pdb`
  - `test_parent_pdb`

### 3.3 输入与输出

- 输入：`PDB.list` 文件。
- 输出：创建目录 + 控制台打印配置摘要。

### 3.4 使用方式

- 第一次运行必须先执行此单元。
- 改方法配置或路径后，重新运行 Cell 1。
- 若 `PDB.list` 不存在，会抛出 `FileNotFoundError`。

---

## 4. Cell 2：复制并重命名 metrics_summary.csv

### 4.1 功能

该单元将各方法目录下每个 PDB 的 `metrics_summary.csv` 复制到统一目录：

- 源：`<method_root>/<pdb>/metrics_summary.csv`
- 目标：`csv_summary/<YYYYMMDD>/<method>/<pdb>.metrics_summary.csv`

并同时记录复制成功与缺失信息。

### 4.2 关键逻辑

1. 遍历 `model_roots` 的每个方法。
2. 若方法根目录不存在：该方法下所有 PDB 都记为缺失（`method_root_not_found`）。
3. 若方法根目录存在：逐个 PDB 检查 `metrics_summary.csv` 是否存在。
4. 成功则 `shutil.copy2` 复制，失败记日志（`metrics_summary_missing`）。
5. 汇总每个方法的 `copied / missing / requested`。

### 4.3 输出文件

- `exports/<YYYYMMDD>/copy_detail_<run_tag>.csv`：逐文件复制明细。
- `logs/copy_missing_<run_tag>.csv`：缺失记录。
- `exports/<YYYYMMDD>/copy_summary_<run_tag>.csv`：方法级汇总。

### 4.4 使用方式

- 确认 Cell 1 参数正确后执行。
- 执行完成后先看 `copy_summary`，确认各方法是否覆盖完整。

---

## 5. Cell 3：读取复制结果并执行 15 样本 QC

### 5.1 功能

统一读取 Cell 2 复制后的 CSV，并执行数据质量控制：

1. 校验必需列是否齐全。
2. 检测 `(complex, seed, id)` 重复并去重。
3. 将 `scRMSD` 转数值并去除无效值。
4. 按 `(method, parent_pdb)` 统计样本数。
5. 仅保留样本数等于 `required_samples_per_group` 的完整组。

### 5.2 关键数据对象

- `all_df`：读取并基础清洗后的全量样本。
- `group_counts`：每个 `(method, parent_pdb)` 的样本计数与是否完整。
- `valid_df`：仅完整组数据（后续绘图主输入）。
- `bad_schema_df`：读失败或缺列记录。
- `duplicate_df`：重复样本记录。

### 5.3 输出文件

- `exports/<YYYYMMDD>/group_qc_summary_<run_tag>.csv`
- `logs/incomplete_pdb_<run_tag>.csv`
- `logs/bad_schema_<run_tag>.csv`
- `logs/duplicates_<run_tag>.csv`
- `exports/<YYYYMMDD>/all_loaded_samples_<run_tag>.csv`
- `exports/<YYYYMMDD>/scRMSD_valid_samples_<run_tag>.csv`

### 5.4 使用方式

- 必须在 Cell 2 后运行。
- 若无任何可读数据，会抛出：
  - `RuntimeError("No valid metrics_summary.csv loaded...")`
- 推荐检查：
  1. `group_qc_summary` 的 `is_complete_15` 比例。
  2. `bad_schema` 是否有方法列缺失问题。

---

## 6. Cell 4：绘制分 PDB + 全局 Top1/Oracle 箱线图

### 6.1 功能

该单元将 `valid_df` 可视化为多层次图：

1. 每个父 PDB 一张箱线图（所有方法对比）。
2. 全局 Top1 图（每个 `(method, parent_pdb)` 取 `ranking_score` 最大样本）。
3. 全局 Oracle 图（每个 `(method, parent_pdb)` 取 `scRMSD` 最小样本）。
4. Top1/Oracle 的 `scRMSD<=2.5Å` 过滤版图，并标注每个方法 `n` 与百分比。

### 6.2 关键辅助函数

- `method_label_from_underscores()`：方法名按 `-` 切分换行。
- `prepare_plot_df()`：增加 `method_label` 列供绘图。
- `format_axis_ticks()`：统一刻度字体、旋转、行间距。
- `annotate_counts_with_pct_on_boxes()`：过滤图顶部标注 `n=xx (yy.y%)`。
- `draw_global_box()`：统一绘制全局箱线图+散点图。

### 6.3 方法顺序策略

- 固定顺序：`method_order_fixed = list(model_roots.keys())`
- 保证图上横坐标顺序与输入字典顺序一致。

### 6.4 测试模式

当 `test_only_single_pdb=True` 时：

- 只绘制 `test_parent_pdb` 的分图。
- 跳过全局图生成。

### 6.5 输出文件

- 分 PDB 图目录：`figures/per_pdb_<run_tag>/`
- 全局图：
  - `figures/top1_ranking_score_scRMSD_distribution_<run_tag>.png`
  - `figures/oracle_scRMSD_distribution_<run_tag>.png`
  - `figures/top1_ranking_score_scRMSD_le2.5A_distribution_<run_tag>.png`
  - `figures/oracle_scRMSD_le2.5A_distribution_<run_tag>.png`
- 统计汇总：
  - `exports/<YYYYMMDD>/method_scRMSD_stats_<run_tag>.csv`

### 6.6 运行依赖与常见报错

- 依赖 `valid_df`（来自 Cell 3）。
- 若 `valid_df` 为空：抛 `RuntimeError`。
- 若缺少 `ranking_score`：Top1 全局图会抛 `ValueError`。

---

## 7. Cell 5：按模板导出全局 CSV（Oracle + Rank1）

### 7.1 功能

该单元输出模板风格的全局 CSV：

- 行：方法（按 `model_roots` 顺序）。
- 列：首列为方法名，然后是 `oracle` 列块，再是 `rank1` 列块。
- 列数：按各方法最大样本长度统一补齐（不足填空）。
- 额外输出 `scRMSD<=2.5Å` 的过滤版模板 CSV。

### 7.2 数据来源模式

通过 `export_source_mode` 控制：

1. `from_df`（默认）：直接使用 Cell 4 的 `oracle_df` / `top1_df`。
2. `from_csv_summary_dict`：通过 `custom_source_dict` 从指定 CSV 重建原始数据，再选 Oracle/Top1。

### 7.3 关键函数说明

#### `_ensure_complex_seed_id(df)`

- 若已有 `complex_seed_id` 直接使用。
- 否则尝试由 `complex + seed + id` 拼接。
- 缺字段时报错。

#### `_build_selected_from_raw(raw_df)`

- 从原始样本中构建：
  - Oracle（最小 scRMSD）
  - Top1（最大 ranking_score）
- 自动把 `scRMSD`、`ranking_score` 转数值。

#### `_load_raw_from_custom_dict(mapping)`

- 根据方法名 -> CSV 路径字典读取数据。
- 相对路径默认挂到 `csv_summary_dir` 下。
- 若 CSV 无 `parent_pdb`，会由文件名推断。

#### `export_template_oracle_rank1(oracle_df_in, top1_df_in, out_csv)`

- 按方法顺序整理 `oracle` 和 `rank1` 的 `scRMSD` 序列。
- 统一补齐到同一长度。
- 输出列名结构：`"" + [oracle...]+[rank1...]`。

### 7.4 输出文件

- 目录：`csv_summary/<YYYYMMDD>/global_plot_data_<run_tag>/`
- 全量模板：
  - `template_style_oracle_rank1_<run_tag>.csv`
- 过滤模板：
  - `template_style_oracle_rank1_le2.5A_<run_tag>.csv`

### 7.5 运行依赖与注意点

- `from_df` 模式依赖 Cell 4 先运行，且存在全局变量 `top1_df`、`oracle_df`。
- 若改用 `from_csv_summary_dict`，必须填写有效 `custom_source_dict`。
- 过滤版输出是基于 `scRMSD<=2.5`。

---

## 8. 推荐标准运行流程（实操）

1. 在 Cell 1 修改 `model_roots`、`pdb_list_path`、测试模式参数。
2. 依次运行 Cell 1~Cell 5（不建议跳步）。
3. 先看 `exports/<YYYYMMDD>/copy_summary_*.csv` 与 `group_qc_summary_*.csv`。
4. 再看 `figures/` 下全局图和分图。
5. 最后检查 `csv_summary/<YYYYMMDD>/global_plot_data_<run_tag>/` 两份模板 CSV。

---

## 9. 结果文件总索引（按用途）

### 9.1 数据搬运与QC

- 复制明细：`copy_detail_*.csv`
- 复制汇总：`copy_summary_*.csv`
- 缺失日志：`logs/copy_missing_*.csv`
- 质量汇总：`group_qc_summary_*.csv`
- 不完整组：`logs/incomplete_pdb_*.csv`
- schema错误：`logs/bad_schema_*.csv`
- 重复记录：`logs/duplicates_*.csv`

### 9.2 绘图

- 分PDB图：`figures/per_pdb_<run_tag>/*.png`
- 全局Top1/Oracle图及<=2.5图：`figures/*.png`
- 方法级统计：`method_scRMSD_stats_*.csv`

### 9.3 模板导出

- 全量模板：`template_style_oracle_rank1_*.csv`
- <=2.5模板：`template_style_oracle_rank1_le2.5A_*.csv`

---

## 10. 常见问题与排查

### Q1：Cell 2 复制几乎全缺失

- 检查 `model_roots` 路径是否正确。
- 检查源目录是否按 `<root>/<pdb>/metrics_summary.csv` 组织。
- 检查 `pdb_list_path` 是否与目录中的 PDB 名匹配。

### Q2：Cell 3 提示无有效数据

- 先查看 `logs/bad_schema_*.csv` 是否缺必需列。
- 检查 `scRMSD` 是否可转换为数值。
- 检查重复键 `(complex, seed, id)` 是否异常大量导致有效行减少。

### Q3：Cell 4 Top1 图报缺 `ranking_score`

- 确认 `metrics_summary.csv` 含 `ranking_score` 列。
- 若无该列，可只使用 Oracle 分析，或补充该列后重跑。

### Q4：Cell 5 `from_df` 模式报变量缺失

- 需要先运行 Cell 4，保证 `top1_df` 和 `oracle_df` 已生成。

### Q5：想只处理一个 PDB 快速调图

- 在 Cell 1 设置：
  - `test_only_single_pdb = True`
  - `test_parent_pdb = "目标PDB"`
- 然后重跑 Cell 1~Cell 4（全局图会跳过）。

---

## 11. 维护建议

- 每次修改 `model_roots` 后建议新开一次运行（新的 `run_tag`），避免不同批次结果混在一起。
- 若希望长期追踪方法变化，建议把当前 `model_roots` 另存为版本化配置文件。
- 若后续 seeds/id 数量变化，务必同步更新 `required_samples_per_group`。

---

如需，我可以继续补一版“面向新同学的一键运行清单”（包含检查命令 + 典型目录示意），放在同一个 `readme.md` 末尾。

---

## 12. 最小可复现实验清单（MRE）

下面给出“最短闭环”版本，目标是在最少改动下，完整跑通一次：复制→QC→绘图→模板导出。

### Step A：最小参数确认（Cell 1）

只检查 4 件事：

1. `model_roots` 中每个方法路径可访问。
2. `pdb_list_path` 指向正确的 `PDB.list`。
3. `required_samples_per_group = 15`（与你当前实验设定一致）。
4. `test_only_single_pdb = False`（如果要完整全局输出）。

执行 Cell 1 后，验收点：

- 控制台打印了 `Loaded PDB count`（大于 0）。
- 控制台打印了 `csv_summary_dir` 和 `exports_date_dir`。
- 对应目录已创建成功。

### Step B：数据归集（Cell 2）

执行 Cell 2，不改代码。

验收点：

- 控制台出现 `Copy summary` 表。
- `copy_summary` 中核心方法的 `copied` 接近 `requested`。
- 若 `missing` 偏高，优先查看 `logs/copy_missing_*.csv` 排查路径问题。

### Step C：质量控制（Cell 3）

执行 Cell 3，不改代码。

验收点：

- 控制台打印 `Valid rows (complete groups only)` 且大于 0。
- `Complete groups` 显著大于 0。
- `exports/<YYYYMMDD>/scRMSD_valid_samples_*.csv` 已生成。

若失败：

- 先看 `logs/bad_schema_*.csv`（缺列/读失败）。
- 再看 `logs/incomplete_pdb_*.csv`（样本数不是 15）。

### Step D：图形产物（Cell 4）

执行 Cell 4，不改代码。

验收点：

- 生成分 PDB 图目录：`figures/per_pdb_<run_tag>/`。
- 生成 4 张全局图（Top1、Oracle、Top1<=2.5、Oracle<=2.5）。
- 生成方法统计文件：`method_scRMSD_stats_*.csv`。

若失败：

- `ranking_score` 缺失会导致 Top1 报错。
- `valid_df` 为空说明上一步 QC 未通过。

### Step E：模板导出（Cell 5）

保持 `export_source_mode = "from_df"`，执行 Cell 5。

验收点：

- 目录 `csv_summary/<YYYYMMDD>/global_plot_data_<run_tag>/` 存在。
- 同时产出两份文件：
  - `template_style_oracle_rank1_<run_tag>.csv`
  - `template_style_oracle_rank1_le2.5A_<run_tag>.csv`
- 控制台打印两份 CSV 的 shape。

### Step F：最小交付核对（建议 1 分钟完成）

只核对以下 5 项即视为“复现成功”：

1. `copy_summary_*.csv` 已生成。
2. `group_qc_summary_*.csv` 已生成。
3. 全局图 4 张已生成。
4. 全量模板 CSV 已生成。
5. `<=2.5A` 模板 CSV 已生成。

### Step G：最小重跑策略（参数改动后）

若你只改了以下内容，建议最小重跑如下：

- 只改 `model_roots` / `pdb_list_path`：重跑 Cell 1→2→3→4→5。
- 只改绘图参数（字号、旋转、测试模式）：重跑 Cell 1→4→5。
- 只改模板导出格式：重跑 Cell 5。

这样可以减少不必要的重复计算，并保持结果可追踪。