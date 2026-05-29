# Research Notes

## Scope
- Workspace path: /home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict
- Mapping JSON: /home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict/msa_template_mapping.json
- Output base: /home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict/original_result/msa_template/output
- Metrics summary: /home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict/original_result/msa_template/output/metrics_summary.csv

## Key Observations
- Output base contains per-complex directories plus CSV outputs (metrics_summary.csv, filtered CSV, success rates).
- metrics_summary.csv columns: complex, seed, id, pep_plDDT, plDDT, ipTM, pTM, pep_pTM, pAE_min, ipAE, ranking_score, scRMSD.

## Pipeline Behavior (Skip Conditions)
From pipeline_metrics_v2.py:
- A sample is skipped if any of these files are missing:
  - {design_name}_{sample_name}_model.cif
  - {design_name}_{sample_name}_confidences.json
  - {design_name}_{sample_name}_summary_confidences.json
- JSON parsing errors (confidences or summary) cause a skip.
- CIF parsing yields missing chain coordinates for:
  - peptide_chain_pred (default B)
  - align_chain_id (first non-target chain in ref PDB)
- Coordinate length mismatches lead to skip:
  - pred_pep_coords vs ref_pep_coords
  - pred_align_coords vs ref_align_coords
- Non-existent design directories are skipped.

## Hypotheses for Missing Complexes
- Some complexes have zero valid samples due to missing files.
- Chain ID mismatch between CIF and ref PDB (align_chain_id not found in CIF).
- Missing residues/atoms leading to length mismatch and full rejection of samples.
- JSON format issues or partial output generation.

## Next Diagnostics (Pending)
- Compare mapping JSON keys vs metrics_summary.csv complexes to list missing complexes.
- For each missing complex, scan its sample directories to tally missing files, JSON errors, chain-id absence, and length mismatch counts.
- Summarize missing reasons per complex and globally.

## Diagnostics Results
- Complexes in mapping: 170
- Complexes in metrics_summary: 150
- Missing complexes: 20
- Missing report: /home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict/original_result/msa_template/output/missing_samples_report.csv
- Total missing entries: 300
- Reason counts:
  - length_mismatch_align: 240
  - missing_align_chain: 60

Missing complexes:
- 1a0n, 1f47, 1mv0, 1v1t, 2aij, 2c3i, 2cch, 2p1o, 2qos, 2vzg,
  4dg3, 5bs2, 5fml, 5fv6, 5huw, 5lyn, 5wyi, 5xxq, 6dei, 6g5g

Per-missing-complex top reasons (all 15 samples each):
- missing_align_chain: 2aij, 2qos, 4dg3, 5huw
- length_mismatch_align: all other missing complexes

## Alignment Rule Update
- Dataset is dimer-only; the non-peptide chain is the only chain besides the peptide chain.
- Alignment should use the non-peptide chain in both ref and pred, without assuming chain IDs match across ref/pred.
