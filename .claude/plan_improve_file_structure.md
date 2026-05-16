# Plan: 完善 Benchmark 目录的文件结构与软连接

> 状态: **待执行** · 创建: 2026-05-14
> 目标: 清理 5,392 个软连接（99.9%为绝对路径），优化 .gitignore，使仓库可推送到远程且他人可用

---

## 1. 现状分析

### 1.1 仓库规模

| 项目 | 当前值 |
|------|--------|
| 总大小 | **116 GB** |
| 软连接数 | **5,392** (绝对路径 5,388 / 相对路径 4) |
| 文件数 | ~60 万+ (大量 pdb/cif/json/a3m) |

### 1.2 软连接问题分类

| 类别 | 数量 | 示例 | 问题 |
|------|------|------|------|
| 指向 dataset/ 的软连接 | ~数十 | `clash_metrics/PepSet_dimer -> /home/.../dataset/PepSet_dimer` | 绝对路径，clone后broken |
| ligandmpnn 内软连接 | 大量 | `ligandmpnn/test_weight/datasets/*` | 指向外部数据目录 |
| ligandmpnn model_params | 多个 | `ligandmpnn/test_weight/model_params` | 指向外部权重文件 |
| alphafold3 MSA 软连接 | 数个 | `alphafold3/MSA_pep -> /home/.../protenix/PepSet/MSA_pep` | 跨模块绝对路径引用 |
| Rosetta 软连接 | 数个 | `RFdiffusion2/minimized -> /home/.../Rosetta/interface/...` | 绝对路径 |

### 1.3 绝对路径 vs 相对路径

**5,388 个绝对路径软连接**在他人 clone 后全部失效。应该：
- 如引用仓库内路径 → 改为**相对路径**
- 如引用仓库外路径 → 列出外部依赖，统一用脚本配置

---

## 2. 修改清单

### Phase 1: 更新 .gitignore

**文件**: `/.gitignore`

- 新增排除: `*.a3m` `*.fasta` `*.fa` `*.out` `*.sc` `*.trb` `*.mutfile` `*.ddg` `*.m8` `*.pml` `*.params`
- 新增排除: `__pycache__/` `*.pyc` `.ipynb_checkpoints/`
- 新增目录排除: `/alphafold3/PepSet_dimer_noC/output/` `predict_summary/csv_summary/`
- 修复 CSV 跟踪规则: 用 `!/predict_summary/template.csv` 替代 `!/predict_summary/**/*.csv`
- 修复 Rosetta 排除: `/Rosetta/` 整体排除
- 新增软连接排除: 所有 ligandmpnn 下 `model_params`、`datasets/`、`outputs`、`predict`、`LigandMPNN-Output`
- 新增 dataset 子目录排除: `PDBs/` `Processed_PDBs/` `Merged_PDBs/`

### Phase 2: 绝对路径软连接 → 相对路径

**原则**：
- 引用同一仓库内的路径 → 改为相对路径
- 引用仓库外路径 → 保留但添加到 `.gitignore`，并在文档中注明外部依赖

需要检查并修改的软连接包括（但不限于）：

| 软连接路径 | 当前目标 | 建议动作 |
|-----------|---------|---------|
| `clash_metrics/PepSet_dimer` | `/home/.../Benchmark/dataset/PepSet_dimer` | 改为 `../dataset/PepSet_dimer` |
| `RFdiffusion2/minimized` | `/home/.../Rosetta/interface/InterfaceAnalyzer/minimized` | 改为相对路径 |
| `alphafold3/MSA_pep` | `/home/.../protenix/PepSet/MSA_pep` | 改为 `../protenix/PepSet/MSA_pep` |
| `alphafold3/dimer` | `../dataset/PepSet_dimer/` | ✅ 已为相对路径，保留 |
| `protenix/PepSet/PepSet_dimer` | `/home/.../dataset/PepSet_dimer` | 改为 `../../dataset/PepSet_dimer` |
| `ligandmpnn/test_weight/datasets/*` | 外部绝对路径 | 核查是否指向仓库内路径 |
| `ligandmpnn/**/model_params` | 外部权重文件 | 保留绝对路径，在 doc 中注明下载来源 |

### Phase 3: 删除不需要的软连接

部分软连接指向的目录**已经被 `.gitignore` 排除**（如 dataset/ 下大量 PDB 目录）。这些软连接提交到 git 只会产生 broken link，建议删除。

需要逐条判断：
- 该软连接的指向目标是否在仓库内且会被 track？
- 上游脚本是否依赖该软连接存在？
- 如依赖 → 用相对路径重建；如不依赖 → 删除

### Phase 4: 验证

- 检查 `.gitignore` 覆盖是否完整：`git status --short` 不应出现预期排除的文件
- 检查软连接可访问性：`find . -type l -xtype l` 找出 broken links
- 模拟 clone 测试：在临时目录 `git clone`，验证软连接均有效

---

## 3. 执行顺序

```
Phase 1: 更新 .gitignore
    ↓
Phase 2: 绝对路径软连接 → 相对路径重建
    ↓
Phase 3: 删除不需要的软连接
    ↓
Phase 4: 验证 + git add / commit / push
```

每个 Phase 完成后通知用户确认，再进入下一 Phase。

---

## 4. 注意事项

- 修改软连接前确认上游脚本（.py/.sh/.ipynb）是否写死了绝对路径引用
- 部分 `model_params` 软连接指向外部权重文件（~1GB+），不应纳入仓库
- Rosetta 目录 76GB，直接整体 `.gitignore` 排除，内部软连接一并无视
- 执行前先 `git stash` 或备份当前工作区
