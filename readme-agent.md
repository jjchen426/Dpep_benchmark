# Benchmark 子目录深度调研说明（readme-agent）

> 目录：`/home/junjiechen/1_work/250401-Dpepalign/Benchmark`  
> 生成时间：2026-03-26  
> 调研方法：结合各子目录 README/readme + 关键脚本与模板文件静态分析（未实际运行计算）。  
> 参考技能库：`/home/junjiechen/1_work/.claude/protein-design-skills`（重点参考了 protein-design-workflow / ligandmpnn / alphafold 的流程术语与阶段划分）。

---

## 1. 全局定位与主流程

该 `Benchmark` 目录是一个围绕 **蛋白-多肽复合物** 的方法评估与横向比较工程，核心链路可概括为：

1. **数据集准备**（`dataset/`）
2. **序列设计**（`ligandmpnn/`）
3. **结构预测/自洽验证**（`alphafold3/` + `protenix/`）
4. **指标汇总与可视化**（`predict_summary/`）
5. **几何/界面质量评估**（`clash_metrics/` + `Rosetta/` + `AutoDockCP/`）

这与 skills 中“设计→预测→筛选→分析”的标准 workflow 一致，但本项目更偏重：
- HETATM 形式输入对 LigandMPNN 设计行为的影响；
- AF3 与 Protenix 两条预测路线对设计成功率的对比；
- 多种过滤策略（scRMSD/ipTM/pLDDT）和打分策略的稳定性验证。

---

## 2. 顶层子目录详解（含深入子目录）

## 2.1 `alphafold3/`

### 目录功能
用于存放 AlphaFold3 的批量预测任务输入/输出、不同 MSA/template 组合实验以及后处理筛选结果。

### README 显式信息（已核对）
- 包含 `PepSet-dimer`（170 个复合物）及其衍生筛选集；
- 有 `PepSet_AF3_noC_pass` / `PepSet_AF3_noC_pass-HETATM` / `PepSet_AF3_pass` 等过滤后的代表结构；
- 明确区分了蛋白端与多肽端是否使用 MSA/template 的实验组合；
- 记录了后续规范：通过在 JSON 中传空字符串（`"pairedMsa": ""`）禁用 MSA。

### 关键子目录与作用
- `PepSet_dimer_noC/`, `PepSet_dimer_withC/`：AF3 原始预测输出仓库（按是否含 Cys 分层）。
- `pro_msa_notemplate-pep_nomsa_notemplate/`
- `pro_msa_template-pep_nomsa_notemplate/`
- `pro_nomsa_notemplate-pep_nomsa_notemplate/`
- `pro_nomsa_template-pep_nomsa_notemplate/`  
  上述四个是“蛋白端 MSA/template 条件”控制实验，目录命名本身承载实验变量。
- `MSA_pep/`, `MSA_pro_all_PepSet_dimer/`：预计算 MSA 资产。
- `DockQ/`：对预测结构与天然结构进行 DockQ 评估（与 `protenix/PepSet/DockQ` 形成对照）。

### 关键脚本分析
- `run.sh`：直接调用本地 AF3 运行入口 `original_soft/alphafold3/run_alphafold.py`，指定 `input_dir/model_dir/db_dir/output_dir`，说明本仓库依赖外部权重与数据库路径（非自包含）。
- `template.json` / `template_nomsa.json`：任务模板骨架，区分是否引入 MSA 信息。
- `process.ipynb`：后处理与筛选工作台（结合目录命名与产物推断）。

### 输入/输出要点
- **输入**：按复合物组织的 JSON + 可选 MSA/template 文件。
- **输出**：每个复合物多 seed 多样本预测结果，后续提取最优/过滤通过样本进入 `PepSet_AF3_*` 集。

---

## 2.2 `ligandmpnn/`

### 目录功能
该目录是序列设计与方法学对比的中心，主要评估 LigandMPNN（含 HETATM 方案）的参数、过滤与稳定性。

### README 显式信息（已核对）
包含多个实验分支：
- `test_design_numbers`：采样数对新颖性/重复率影响；
- `test_filter`：不同过滤方式对成功率影响；
- `check_filter`：重复设计+多预测器验证过滤稳定性；
- `test_weight`：不同权重/不同方法（LigandMPNN、HETATM、ProteinMPNN、Rosetta）序列恢复率对比；
- `test_hyperparam`：扩展温度等超参；
- `test_score_times`：打分次数影响（在其他分支部分吸收）。

### 2.2.1 `test_filter/`（深入）
#### 核心作用
在不同数据集上执行“设计→筛选→预测验证”闭环。

#### 关键文件
- `README.md`：给出数据集定义与流程说明。
- `design.sh`：对 `Processed.json` 批量设计（链 `L`，可控温度/批大小）。
- `design_pred_dimer.sh`：对 `PepSet-passed-dimer_processed` 中每个 PDB 做三 seed（42/43/44）设计，链 `B`，`omit_AA "C"`，每 seed 2000 条（200×10）。
- `score.sh` / `score_batch.sh`：对设计序列执行 autoregressive score，评估打分策略对排序/筛选的影响。
- `template.json` / `template_without_msa.json`：后续 Protenix 预测模板。
- `DockQ/`、`Protenix/`：验证结果与外部预测对接产物。

#### 产物逻辑
- `LigandMPNN-Output/`：设计序列与分数；
- `LigandMPNN-Output-pred_dimer/`：面向通过筛选 dimer 子集的大规模重复设计结果。

### 2.2.2 `check_filter/`（深入）
#### 核心作用
验证过滤策略在 AF3/Protenix 成功样本上的可重复性。

#### 关键文件
- `datasets/readme.md`：定义 `PepSet_AF3_pass_processed` 与 `PepSet-passed-dimer_processed` 等输入来源及阈值。
- `predict/readme.md`：说明在不同预测器上复验设计结果。
- `design_pred_dimer.sh`：与 `test_filter` 类似的三 seed 设计，但使用 `run_test.py`、`--save_pdb 0`，更偏向大规模统计测试。
- `protenix_template.json`：后续预测接入模板。

### 2.2.3 `test_design_numbers/`（深入）
#### 核心作用
测“采样规模 vs 序列去重/饱和”的关系。

#### 关键文件
- `design_numbers.sh`：在同一数据集上做 100/500/1000/2000/5000 等采样级别；
- `unique_sequence_summary_transposed.csv`：关键统计产物；
- `benchmark_design_number.ipynb` / `analysis.ipynb`：可视化与统计分析。

### 2.2.4 `test_weight/`（深入）
#### 核心作用
多方法/多权重序列恢复率对比与 pipeline 实验。

#### 关键文件
- `benchmark_ligandmpnn.sh`, `benchmark_proteinmpnn.sh`, `benchmark_rosetta.sh`, `benchmark_rosetta-pipeline.py`：跨方法基准入口。
- `2_gen-modpdb_for_MPNN.ipynb`, `3_calculate_seqrec.ipynb`：数据准备与恢复率统计。
- `pack_design.xml`：Rosetta 设计配置文件，显示此子目录含 Rosetta 侧对照实验。

---

## 2.3 `protenix/`

### 目录功能
用于 Protenix 结构预测（尤其 PepSet 二元复合物），并与 AF3 形成平行验证通道。

### 顶层文件含义
- `demo.sh`：官方/示例型推理命令集合，包含不同模型、MSA/template 选项。
- `template.json`, `template_without_msa.json`：任务模板。
- `PepSet/`：主实验目录。

### 2.3.1 `protenix/PepSet/`（深入）
#### README 显式信息（已核对）
- `dimer`：原始集合；
- `dimer_filtered` / `dimer_filtered-Protenix_v1`：按 `scRMSD<=2.5, pep_plddt>0.7, iptm>0.7` 过滤后最优结构；
- `dimer_noCys_filtered`：去除多肽含 Cys 条目；
- `pred*`：不同版本/配置预测结果；
- `MSA_*`：蛋白与多肽 MSA 资产；
- `DockQ/`：打分任务清单与结果。

#### 关键脚本/配置分析
- `run.sh`：当前执行块展示了 `protenix_base_default_v1.0.0` + `use_msa false` + `use_template false` 的批量预测（seeds 42/43/44），并把配置快照复制到输出目录，具备可追溯性。
- `job2-final-updated.json`：显式为蛋白与多肽提供 `pairedMsaPath/unpairedMsaPath/templatesPath`，说明路径级控制 MSA/template。
- `job2-final-updated_pep-notemplate.json`：将多肽 template 指向专门目录（`template_pep/`），用于评估多肽 template 效应。

#### 子目录角色
- `pred_v1-*` / `pred-v05-*`：不同模型版本与 MSA/template 组合的结果矩阵；
- `1_gen_json.ipynb`, `2_protenix.ipynb`, `3_gen_msa_all.ipynb`：前处理、推理与 MSA 构建流水线 Notebook。

---

## 2.4 `predict_summary/`

### 目录功能
统一汇总 AF3/Protenix 多方法预测结果并输出统计图与 CSV。

### README 显式信息（已核对）
`eval_af3_ptx.ipynb` 被详细文档化，流程包括：
1. 收集各方法 `metrics_summary.csv`；
2. `(method,parent_pdb)` 组别 QC（默认每组 15 样本）；
3. 生成 per-PDB 与全局 Top1/Oracle 分布图；
4. 导出模板风格 CSV（含 `scRMSD<=2.5Å` 版本）。

### 目录结构解读
- `csv_summary/`：标准化复制后的中间 CSV 仓库；
- `exports/`：汇总表导出；
- `figures/`：图像输出；
- `logs/`：缺失文件、schema 错误、重复样本等 QC 日志；
- `template.csv`：标准输出表头模板。

### 功能价值
这是全 benchmark 的“评估中枢”，将上游实验目录结构异构问题统一到可比较统计框架。

---

## 2.5 `clash_metrics/`

### 目录功能
聚焦复合物几何冲突（clash）分析，是结构质量的补充维度。

### README 显式信息
- 目标是检验蛋白-多肽复合物 clash 指标；
- `PepSet_dimer` 为主要数据源。

### 文件与流程推断
- `test.ipynb`：clash 指标计算与可视化入口（Notebook 工作流）。
- `PepSet_dimer/`：待评估结构输入集。

### 与其他模块关系
可作为 `predict_summary` 后的二次质量过滤维度，帮助排除虽通过 scRMSD/ipTM/pLDDT 但局部几何不合理的样本。

---

## 2.6 `Rosetta/`

### 目录功能
围绕界面打分、柔性对接与基准参数对比开展 Rosetta 路线评估。

### 顶层分支
- `interface/`：本地实验主目录（InterfaceAnalyzer/FlexPepDock/MDM2 等）。
- `Rosetta-interface/`：外部/独立 Rosetta interface 基准工程（含自身 README 与代码结构）。

### 2.6.1 `Rosetta/interface/`（深入）
#### 子目录作用
- `InterfaceAnalyzer/`：界面能量/面积等传统指标评估。
- `FlexPepDock/`：多肽柔性对接与重打分，含 `README` 与 `test/readme.md`。
- `Dock/`：对接任务输入输出。
- `MDM2/`：天然/L-binder/D-binder 对比用例，用于建立“指标大小与结合优劣”的判别关系。
- `weight_and_flags/`：Rosetta 参数化配置文件。

### 2.6.2 `Rosetta/Rosetta-interface/`（深入）
含独立工程结构：`designs_and_xtals/`, `interface_ddg/`, `interface_prediction/`, `monomer_ddg/`, `weights_and_flags_files/`，显示该目录用于更系统的 interface benchmark 与 ddG 类分析。

---

## 2.7 `AutoDockCP/`

### 目录功能
用于 AutoDockCP 路线预处理/运行入口（当前脚本不完整，但用途可辨）。

### 关键文件
- `PDB.list`：任务列表。
- `run.sh`：按 `PDB.list` 循环处理，每个条目先 `echo`，随后调用 `reduce` 对 `PepSet-bound/$line/reb_b.pdb` 做预处理（脚本末尾截断，推测后续应接 docking 准备或执行命令）。
- `PepSet-bound/`：输入结构仓库。

### 状态判断
此目录更像“在建或局部脚本截断”的 docking 分支；建议后续补齐 `run.sh` 末段命令与 README。

---

## 2.8 `dataset/`

### 目录功能
提供 benchmark 的基准数据及其噪声扩增版本，是所有上游实验的输入基础层。

### 关键内容
- 基础集：`PepSet/`, `Colabfold/`, `PeptiDB-Tsaban/`, `PepSet_dimer/`；
- 噪声集：`*-noise-0.1` 到 `*-noise-0.5`（多组）；
- 通过筛选的结构集：`PepSet_AF3_noC_pass` 及其 HETATM 版本与噪声版本。
- 清单文件：`*-PDB.list`, `fix_pdb.list`。
- `1_addnoise.ipynb`：噪声注入与数据增强流程入口。

### 与设计模块关系
`ligandmpnn/test_weight`、`test_filter` 等直接消耗这些数据集做方法对比，保证同一输入条件下评估公平性。

---

## 3. 跨目录数据流（深入版）

### 3.1 主链路 A（AF3 先验筛选）
1. `protenix/PepSet/dimer` 或 `alphafold3/dimer` 起始结构；
2. AF3 / Protenix 预测并筛出通过阈值样本（如 `scRMSD<=2.5` 等）；
3. 过滤后集合进入 `ligandmpnn/test_filter` 或 `check_filter` 做序列再设计；
4. 设计序列再进入 AF3/Protenix 验证；
5. `predict_summary` 汇总统计，`clash_metrics`/`Rosetta` 做补充质量与界面分析。

### 3.2 主链路 B（参数敏感性）
1. `dataset/` 提供多数据集 + 噪声版本；
2. `ligandmpnn/test_design_numbers`、`test_weight`、`test_hyperparam` 改变采样数/温度/权重；
3. 输出序列恢复率、重复率、预测成功率等指标；
4. 在 `predict_summary` 形成跨方法可视化对比。

---

## 4. 关键指标与筛选标准（项目中反复出现）

常见阈值（不同子实验可能有细微差异）：
- `scRMSD <= 2.5 Å`（结构相似性）
- `ipTM >= 0.7` 或 `>0.70`（界面可信度）
- `pep_pLDDT >= 0.7`（或 AF3 百分制 `>=70`）

解释：
- `scRMSD` 偏低意味着设计后预测结构接近目标构象；
- `ipTM` 与 `pLDDT` 联合用于降低“几何看起来像但界面不可靠”的假阳性；
- `clash_metrics` 与 Rosetta 界面指标可作为二次筛选，补足深度学习指标盲区。

---

## 5. 目录成熟度与改进建议

### 成熟度较高（流程闭环完整）
- `ligandmpnn/test_filter`, `ligandmpnn/check_filter`
- `protenix/PepSet`
- `predict_summary`

### 成熟度中等（有数据和脚本但文档可加强）
- `alphafold3`（实验命名清晰，但可补统一输入模板规范文档）
- `Rosetta/interface`（建议补总览 readme 汇总各分支参数与输出字段）

### 待完善
- `AutoDockCP`：`run.sh` 当前可见内容不完整，建议补充完整命令链与 readme。

---

## 6. 可复现执行建议（最小实践）

1. 先在 `dataset/` 固定一个小子集（如 3per_length）验证端到端；
2. 在 `ligandmpnn/test_filter` 执行单模型单温度单 seed 小规模设计；
3. 使用 `protenix/PepSet` 或 `alphafold3` 模板跑预测；
4. 把 `metrics_summary.csv` 统一放入 `predict_summary` 流程；
5. 最后补充 `clash_metrics` 与 Rosetta 指标，形成多维评估结论。

---

## 7. 本次调研覆盖性说明

已覆盖的一级目录：
- `AutoDockCP/`
- `Rosetta/`
- `alphafold3/`
- `clash_metrics/`
- `dataset/`
- `ligandmpnn/`
- `predict_summary/`
- `protenix/`

并深入读取了关键二/三级目录的 README 与入口脚本（`design*.sh`、`score*.sh`、`run.sh`、`job*.json`、模板 JSON 等），形成上述功能分析。
