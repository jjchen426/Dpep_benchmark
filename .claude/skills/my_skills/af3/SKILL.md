---
name: af3
description: Generate AlphaFold3 JSON input files from a CSV of chain sequences
---

# AlphaFold3 JSON Generator

Generate AlphaFold3 JSON input files for protein-peptide complex prediction from a CSV of chain sequences. Each row in the CSV becomes one JSON file (one AF3 prediction job).

## When to Use

Trigger when the user asks to generate AlphaFold3 input JSONs, prepare AF3 prediction inputs from a CSV, or create AF3 job files from sequence tables.

## Workflow

### Step 1: Gather requirements

Ask the user for the following:

1. **CSV file path** — CSV with chain ID headers (A, B, C...) as columns and sequences in cells. The first non-letter column (e.g., "name") provides job names.
2. **Output prefix** — Filename prefix for the generated JSON files (e.g., "job", "design")
3. **Output directory** — Where to save the generated JSON files
4. **Use MSA?** — Yes or No
   - If Yes: ask for the **MSA base directory**. The script expects `{msa_dir}/{job_name}/pairing.a3m` and `{msa_dir}/{job_name}/non_pairing.a3m` structure.
5. **Use templates?** — Yes or No
   - If Yes: `"templates": null` (AF3 will search for templates)
   - If No: `"templates": []` (no templates)
6. **Model seeds** — Comma-separated integers (default: `42,43,44`)

### Step 2: Run the generator

```bash
python .claude/skills/my_skills/af3/scripts/generate_af3_inputs.py \
    --csv <csv_path> \
    --prefix <prefix> \
    --output-dir <output_dir> \
    [--msa-dir <msa_dir>] \
    [--templates] \
    [--seeds <seeds>]
```

### Step 3: Verify output

- Confirm the JSON files exist in the output directory
- Spot-check one JSON file:
  - `dialect` is `"alphafold3"`, `version` is `2`
  - Each chain has correct `id` and `sequence`
  - MSA keys match the chosen mode:
    - With `--msa-dir`: `pairedMsaPath` / `unpairedMsaPath` (path values)
    - Without `--msa-dir`: `pairedMsa` / `unpairedMsa` (empty string values)
  - `templates` matches the chosen mode: `null` (with `--templates`) or `[]` (without)
  - `modelSeeds` contains the expected integers

## Input CSV Format

Column headers that are a single letter (A-Z, a-z) are treated as chain IDs. The first non-letter column header (e.g., "name") is used as the job name.

```csv
name,A,B
1a0n,VTLFVALYDYEART...,PPRPLPVAPGSSKT
1cqg,MVKQIESKTAFQE...,PATLKICSWNVDG
```

Each subsequent row is one job. Generated files: `{prefix}_0001.json`, `{prefix}_0002.json`, etc.

## Output JSON Structure (no MSA mode)

```json
{
    "name": "1a0n",
    "modelSeeds": [42, 43, 44],
    "dialect": "alphafold3",
    "version": 2,
    "sequences": [
        {
            "protein": {
                "sequence": "VTLFVALYDY...",
                "id": "A",
                "pairedMsa": "",
                "unpairedMsa": "",
                "templates": []
            }
        },
        {
            "protein": {
                "sequence": "PPRPLPVAPGSSKT",
                "id": "B",
                "pairedMsa": "",
                "unpairedMsa": "",
                "templates": []
            }
        }
    ]
}
```

## Notes

- The script does not validate MSA file existence — AlphaFold3 will report errors if paths are invalid
- Empty sequences in the CSV are allowed but will cause AF3 errors
- Chain IDs are automatically uppercased
- For per-chain MSA paths, symlink or run the script with different `--msa-dir` values per chain set
