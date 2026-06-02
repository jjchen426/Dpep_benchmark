# Processed Data Description

共 **12** 个文件，每个文件包含统一列：
`complex, seed, id, pep_plddt, iptm, scRMSD, dockq_score, lrmsd, irmsd, fnat, model, method`

## Processing Details

| Model | Method | Source & Merge | Complexes |
|-------|--------|----------------|-----------|
| AF3 | msa_template | metrics_summary.csv + docking_results.csv → 以 (complex,seed,id) 合并 | 170 |
| AF3 | msa_notemplate | metrics_summary.csv + docking_results.csv → 以 (complex,seed,id) 合并 | 170 |
| AF3 | nomsa_template | metrics_summary.csv + docking_results.csv → 以 (complex,seed,id) 合并 | 170 |
| AF3 | nomsa_notemplate | metrics_summary.csv + docking_results.csv → 以 (complex,seed,id) 合并 | 170 |
| ESMFold2 | nomsa_loop10_samples200 | 单文件 merged_esmfold2_nomsa_loop10_samples200.csv，含预测指标 + DockQ 结果 | 165 |
| ESMFold2 | fast_loop10_samples200 | 单文件 merged_esmfold2_fast_loop10_samples200.csv，含预测指标 + DockQ 结果 | 167 |
| ESMFold2 | fast_loop10_samplingsteps68 | 单文件 merged_esmfold2_fast_loop10_samplingsteps68.csv，含预测指标 + DockQ 结果 | 167 |
| ESMFold2 | msa_nonpairing_loop10_samples200 | 单文件 merged_esmfold2_msa_nonpairing_loop10_samples200.csv，含预测指标 + DockQ 结果 | 166 |
| PTX | msa_template | per-complex metrics_summary CSVs + msa_template_docking_results.csv → 以 (complex,seed,id) 合并 | 170 |
| PTX | msa_notemplate | per-complex metrics_summary CSVs + msa_notemplate_docking_results.csv → 以 (complex,seed,id) 合并 | 170 |
| PTX | nomsa_template | per-complex metrics_summary CSVs + nomsa_template_docking_results.csv → 以 (complex,seed,id) 合并 | 170 |
| PTX | nomsa_notemplate | per-complex metrics_summary CSVs + nomsa_notemplate_docking_results.csv → 以 (complex,seed,id) 合并 | 170 |

## Overall Statistics

- Total files: 12
- Complexes common to all 12 files: **165**
- Excluded from comparison (not in all files): **5**
- Excluded complexes: `3pe4`, `4hom`, `5e33`, `6ej7`, `6g5g`

## Per-File Summary

| File | Rows | Complexes |
|------|------|-----------|
| af3_msa_notemplate.csv | 2550 | 170 |
| af3_msa_template.csv | 2550 | 170 |
| af3_nomsa_notemplate.csv | 2550 | 170 |
| af3_nomsa_template.csv | 2550 | 170 |
| esmfold2_fast_loop10_samples200.csv | 2505 | 167 |
| esmfold2_fast_loop10_samplingsteps68.csv | 2505 | 167 |
| esmfold2_msa_nonpairing_loop10_samples200.csv | 2490 | 166 |
| esmfold2_nomsa_loop10_samples200.csv | 2475 | 165 |
| ptx_msa_notemplate.csv | 2550 | 170 |
| ptx_msa_template.csv | 2550 | 170 |
| ptx_nomsa_notemplate.csv | 2550 | 170 |
| ptx_nomsa_template.csv | 2550 | 170 |
