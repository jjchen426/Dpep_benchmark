# Agent Plan (v6)

## Context
- Goal: Fix alignment logic so peptide-chain RMSD is computed after aligning on the non-peptide chain.
- Dataset: Dimer-only. The non-peptide chain is the only chain besides the peptide chain.
- Constraint: `peptide-chain-ref` and `peptide-chain-pred` specify peptide chains in ref and pred, respectively.
- Do NOT assume ref/pred chain IDs match for the non-peptide chain.

## Proposed Method (No Implementation Yet)
1. Ref chain selection:
   - Identify peptide chain by `peptide-chain-ref`.
   - Identify the single non-peptide chain (only chain besides peptide in dimers).
   - Validate non-peptide chain exists; otherwise skip with a clear reason.
2. Pred chain selection:
   - Identify peptide chain by `peptide-chain-pred`.
   - Identify the single non-peptide chain (only chain besides peptide).
   - Validate non-peptide chain exists; otherwise skip with a clear reason.
3. Alignment:
   - Align pred non-peptide chain to ref non-peptide chain.
   - Apply the same transform to pred peptide chain.
   - Compute peptide backbone RMSD.
4. Diagnostics:
   - Add explicit skip reasons for: missing peptide chain, missing non-peptide chain.
   - Length mismatch triggers an error and stops the run (not a skip reason).
   - Ensure summary logs show counts of each skip reason.
5. Missing residue handling (decision):
   - Decision: if lengths mismatch, raise an error and stop the run.
   - Missing residues are not expected; no intersection logic needed.

## File-Level Change Plan (v1)
- pipeline_metrics_v2.py
  - Update non-peptide chain selection logic to choose the only non-peptide chain in ref and pred separately.
  - Remove dependence on ref align chain ID when extracting pred chain coordinates.
   - Add validation for non-peptide chain existence in ref and pred.
   - Add validation for missing peptide chain in ref/pred with explicit skip reason.
  - Add clearer skip/print reasons for alignment failures and length mismatches.
   - On length mismatch, raise an error and stop the run (per decision).

## Risks / Open Questions
- Missing residues are not expected; no intersection logic required.

## Review Checklist
- Confirm chain selection rule for dimers.
- Confirm desired logging detail (stdout vs file).

## Iteration Notes
- This is round 6/6. Plan is finalized; ready for implementation on approval.

## Implementation Status
- pipeline_metrics_v2.py: updated non-peptide chain selection and alignment logic (completed).
