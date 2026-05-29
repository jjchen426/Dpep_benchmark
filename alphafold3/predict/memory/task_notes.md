Task: diagnose missing complexes in metrics_summary.csv vs mapping JSON
- Mapping JSON: msa_template_mapping.json
- Metrics summary: original_result/msa_template/output/metrics_summary.csv
- Pipeline skips due to missing files, JSON errors, missing chain IDs, or length mismatches
- Next: compute missing complexes and per-complex skip reasons
- Results: 170 complexes in mapping, 150 in metrics_summary, 20 missing
- Reasons: length_mismatch_align=240, missing_align_chain=60 (total missing entries=300)
- Alignment rule confirmed: dimer dataset, non-peptide chain is the only chain besides peptide; do not assume ref/pred chain IDs match.
