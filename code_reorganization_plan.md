# Benchmark 代码整理方案

## 目标

将 `/home/junjiechen/1_work/250401-Dpepalign/Benchmark/` 中所有的 `.py`、`.sh`、`.ipynb` 代码文件分类复制到 `/home/junjiechen/1_work/250401-Dpepalign/Scripts/benchmark/`，保持原有结构可运行，数据路径不变。

## 约束

1. **复制**（保留原位置），不删除 Benchmark/ 中原代码
2. **排除** `Rosetta/Rosetta-interface/`（独立 git 仓库）
3. **排除**自动生成的脚本（如 `ligandmpnn/test_filter/Protenix/*/msa.sh` 等由 pipeline 生成的执行脚本）
4. **数据路径不变**，脚本内部引用的 `/home/junjiechen/1_work/250401-Dpepalign/Benchmark/...` 路径不做修改
5. 配置/模板文件（`.json`、`.list`、`model_params/` 中的 `.pt` 软链接等）随脚本一起复制

## 分类结构

```
Scripts/benchmark/
├── Predict/                              # 结构预测（已存在，扩展）
│   ├── pipeline_metrics_v2.py            # 并行 scRMSD/成功率 计算
│   ├── predict.ipynb                     # 主预测流程（AF3 + Protenix）
│   ├── AlphaFold3/                       # AlphaFold3 相关
│   │   ├── process.ipynb                 # AF3 结果后处理
│   │   ├── compress.ipynb
│   │   ├── run.sh                        # AF3 运行脚本
│   │   ├── template.json
│   │   └── template_nomsa.json
│   │   └── predict_metrics/             # 指标汇总
│   │       ├── aggregate_metrics.ipynb
│   │       ├── search_metrics.ipynb
│   │       ├── pareto.ipynb
│   │       ├── check.ipynb
│   │       ├── ipSAE/ipsae.ipynb
│   │       └── DockQ/dockq_compute.ipynb
│   ├── Protenix/                         # Protenix 相关
│   │   ├── template.json
│   │   ├── template_without_msa.json
│   │   ├── demo.sh                       # Protenix 综合 demo
│   │   ├── run.sh                        # PepSet 批量预测
│   │   ├── 1_gen_json.ipynb
│   │   ├── 2_protenix.ipynb
│   │   ├── 3_gen_msa_all.ipynb
│   │   ├── check_pdb.ipynb
│   │   └── DockQ/docking.ipynb
│   └── ESMFold2/                         # ESMFold2 相关（新目录）
│       ├── run_esmfold2.py               # 带 MSA 的 ESMFold2
│       ├── run.py                        # ESMFold2-Fast（无 MSA）
│       ├── run_esmfold2fast_lowerloop_sample.py
│       ├── esmfold.ipynb
│       ├── dockq_compute.ipynb
│       ├── esmfold_test.ipynb
│       └── DockQ/run.sh
│
├── Design/                               # 序列设计（新目录）
│   ├── pipeline.py                       # 主 benchmark pipeline
│   ├── LigandMPNN_process.ipynb          # 设计后处理
│   ├── test_weight/                      # 权重比较
│   │   ├── pipeline.py                   # 编排脚本
│   │   ├── benchmark_rosetta-pipeline.py
│   │   ├── benchmark_ligandmpnn.sh
│   │   ├── benchmark_proteinmpnn.sh
│   │   ├── benchmark_rosetta.sh
│   │   ├── test.sh
│   │   ├── 1_addnoise.ipynb
│   │   ├── 1_merge-Lig-Protein.ipynb
│   │   ├── 2_gen-modpdb_for_MPNN.ipynb
│   │   ├── 3_calculate_seqrec.ipynb
│   │   ├── 3_seqrec-forPepset.ipynb
│   │   └── pipeline.ipynb
│   ├── test_filter/                      # 过滤策略
│   │   ├── design.sh
│   │   ├── design_3per_length.sh
│   │   ├── design_pred_dimer.sh
│   │   ├── score.sh
│   │   ├── score_batch.sh
│   │   ├── af3_run.sh
│   │   ├── mpnn_pipeline.ipynb
│   │   ├── mpnn_pipeline_batch.ipynb
│   │   ├── af3_pipeline_batch.ipynb
│   │   ├── protenix_pipeline.ipynb
│   │   ├── protenix_pipeline_batch.ipynb
│   │   ├── Scripts/rescore.py
│   │   ├── Scripts/analysis.py
│   │   ├── datasets/PepSet_3per_length/MSA/gen_msa.ipynb
│   │   └── DockQ/docking.ipynb
│   ├── check_filter/                     # 稳定性检查
│   │   ├── design_pred_dimer.sh
│   │   └── mpnn_post.ipynb
│   ├── test_hyperparam/                  # 超参数搜索
│   │   ├── pipeline.py
│   │   ├── pipeline_peptidempnn.py
│   │   └── pipeline.ipynb
│   ├── test_design_numbers/              # 采样数量测试
│   │   ├── design_numbers.sh
│   │   ├── move.sh
│   │   ├── benchmark_design_number.ipynb
│   │   ├── analysis.ipynb
│   │   └── test.ipynb
│   └── test_score_times/                 # 评分时间测试
│       ├── score.sh
│       ├── test_score_method.ipynb
│       └── analysis.ipynb
│
├── Metrics/                              # 评价指标（新目录）
│   ├── Clash/                            # 空间冲突检测
│   │   ├── clash_filtering_new.py
│   │   ├── clash_analysis.ipynb
│   │   └── test.ipynb
│   ├── ipSAE/                            # ipSAE 评分
│   │   └── ipsae.ipynb
│   └── DockQ/                            # DockQ 汇总
│       ├── run.sh
│       └── dockq_compute.ipynb           # 来自 alphafold3/predict_metrics/
│
├── Structure_Prediction/                 # 跨方法评估（新目录）
│   ├── eval_af3_ptx.ipynb
│   ├── dockq_comparison.ipynb
│   └── eval_by_scrmsd.ipynb
│
├── RFdiffusion/                          # RFdiffusion2（新目录）
│   ├── resources/pipeline.py
│   ├── run/generate_run_sh.py
│   ├── gen_rfd2_file.ipynb
│   └── alanine-scan/
│       ├── analysis_ddg.ipynb
│       └── gen_mutfile.ipynb
│
├── Rosetta/                              # Rosetta 分析（已存在，扩展）
│   ├── py_contact_ms.py                  # CMS 计算库
│   ├── cm_surface.ipynb                  # CMS 分析
│   ├── interface-classifier/
│   │   ├── 3_AF3/scripts/
│   │   │   ├── pipeline_metrics_v2.py
│   │   │   ├── docking.ipynb
│   │   │   ├── check_af3_out.ipynb
│   │   │   ├── mpnn_post.ipynb
│   │   │   └── process.ipynb
│   │   ├── scale/
│   │   │   ├── py_contact_ms.py
│   │   │   ├── cm_surface.ipynb
│   │   │   └── get_scale.ipynb
│   │   └── InterfaceAnalyzer/
│   │       └── analysis.ipynb
│   └── interface/
│       └── AF3/relax/
│           └── gen_job.ipynb
│
├── Dataset/                              # 数据集处理（新目录）
│   ├── 1_addnoise.ipynb
│   ├── check.ipynb
│   └── Colabfold/
│       └── copy_mmcif.ipynb
│
├── MSA/                                  # MSA 生成（新目录）
│   └── gen_msa.ipynb                     # 来自 dataset_for_predict/
│
└── .claude/                              # Claude Code 配置脚本
    └── skills/my_skills/af3/scripts/
        └── generate_af3_inputs.py
```

## 各来源文件详细清单

### 来自 alphafold3/ → Predict/AlphaFold3/
- `Benchmark/alphafold3/predict/pipeline_metrics_v2.py`
- `Benchmark/alphafold3/predict/process.ipynb`
- `Benchmark/alphafold3/predict/compress.ipynb`
- `Benchmark/alphafold3/template.json`
- `Benchmark/alphafold3/template_nomsa.json`
- `Benchmark/alphafold3/predict_metrics/aggregate_metrics.ipynb`
- `Benchmark/alphafold3/predict_metrics/search_metrics.ipynb`
- `Benchmark/alphafold3/predict_metrics/pareto.ipynb`
- `Benchmark/alphafold3/predict_metrics/check.ipynb`
- `Benchmark/alphafold3/predict_metrics/ipSAE/ipsae.ipynb`
- `Benchmark/alphafold3/predict_metrics/DockQ/dockq_compute.ipynb`

### 来自 esmfold2/ → Predict/ESMFold2/
- `Benchmark/esmfold2/run_esmfold2.py`
- `Benchmark/esmfold2/run.py`
- `Benchmark/esmfold2/run_esmfold2fast_lowerloop_sample.py`
- `Benchmark/esmfold2/esmfold.ipynb`
- `Benchmark/esmfold2/dockq_compute.ipynb`
- `Benchmark/esmfold2/esmfold_test.ipynb`
- `Benchmark/esmfold2/DockQ/run.sh`

### 来自 protenix/ → Predict/Protenix/
- `Benchmark/protenix/demo.sh`
- `Benchmark/protenix/template.json`
- `Benchmark/protenix/template_without_msa.json`
- `Benchmark/protenix/PepSet/run.sh`
- `Benchmark/protenix/PepSet/1_gen_json.ipynb`
- `Benchmark/protenix/PepSet/2_protenix.ipynb`
- `Benchmark/protenix/PepSet/3_gen_msa_all.ipynb`
- `Benchmark/protenix/PepSet/check_pdb.ipynb`
- `Benchmark/protenix/PepSet/DockQ/docking.ipynb`

### 来自 ligandmpnn/ → Design/
已在上面 Design/ 部分逐一列出

### 来自 clash_metrics/ → Metrics/Clash/
- `Benchmark/clash_metrics/clash_filtering_new.py`
- `Benchmark/clash_metrics/clash_analysis.ipynb`
- `Benchmark/clash_metrics/test.ipynb`

### 来自 RFdiffusion2/ → RFdiffusion/
- `Benchmark/RFdiffusion2/resources/pipeline.py`
- `Benchmark/RFdiffusion2/run/generate_run_sh.py`
- `Benchmark/RFdiffusion2/gen_rfd2_file.ipynb`
- `Benchmark/RFdiffusion2/alanine-scan/analysis_ddg.ipynb`
- `Benchmark/RFdiffusion2/alanine-scan/gen_mutfile.ipynb`

### 来自 Rosetta/（排除 Rosetta-interface） → Rosetta/
已在上面 Rosetta/ 部分列出

### 来自 dataset/ → Dataset/
- `Benchmark/dataset/1_addnoise.ipynb`
- `Benchmark/dataset/check.ipynb`
- `Benchmark/dataset/Colabfold/copy_mmcif.ipynb`

### 来自 structure_prediction/ → Structure_Prediction/
- `Benchmark/structure_prediction/predict_summary/eval_af3_ptx.ipynb`
- `Benchmark/structure_prediction/new_summary/dockq_comparison.ipynb`
- `Benchmark/structure_prediction/new_summary/eval_by_scrmsd.ipynb`

### 来自 dataset_for_predict/ → MSA/
- `Benchmark/dataset_for_predict/MSA_pro_per3length/gen_msa.ipynb`

### 来自 .claude/
- `Benchmark/.claude/skills/my_skills/af3/scripts/generate_af3_inputs.py`

## 排除的文件

- `Rosetta/Rosetta-interface/` 下的所有内容（独立 git 仓库）
- 自动生成的 `msa.sh` 脚本
- 数据文件（`.pdb`, `.cif`, `.csv`, `.tsv`, `.fa`, `.a3m`, `.pt` 等输出数据）
- `ligandmpnn/test_filter/Scripts/__init__.py`（空文件）

## 验证方式

1. 复制完成后，检查 Scripts/benchmark/ 下的文件结构和数量是否与清单匹配
2. 对比原目录和复制目录的代码文件，确认无遗漏
3. 检查复制的 `.sh` 脚本是否具有可执行权限
