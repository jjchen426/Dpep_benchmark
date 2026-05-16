#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 8 ]]; then
    echo "Usage: $0 <pdb_json> <out_dir> <temperature> <checkpoint> <chains_to_design> <batch_size> <number_of_batches> <save_pdb>"
    exit 1
fi

pdb_path_multi="$1"
out_dir="$2"
temperature="$3"
checkpoint="$4"
chains_to_design="$5"
batch_size="$6"
number_of_batches="$7"
save_pdb="$8"

if [[ ! -f "$pdb_path_multi" ]]; then
    echo "[ERROR] pdb json not found: $pdb_path_multi"
    exit 1
fi

if [[ ! -f "$checkpoint" ]]; then
    echo "[ERROR] checkpoint not found: $checkpoint"
    exit 1
fi

mkdir -p "$out_dir"

echo "[INFO] Running LigandMPNN"
echo "[INFO] pdb_json=$pdb_path_multi"
echo "[INFO] out_dir=$out_dir"
echo "[INFO] temperature=$temperature"
echo "[INFO] checkpoint=$checkpoint"
echo "[INFO] chains_to_design=$chains_to_design"
echo "[INFO] batch_size=$batch_size"
echo "[INFO] number_of_batches=$number_of_batches"
echo "[INFO] save_pdb=$save_pdb"

python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/run_test.py \
    --model_type ligand_mpnn \
    --checkpoint_ligand_mpnn "$checkpoint" \
    --seed 111 \
    --pdb_path_multi "$pdb_path_multi" \
    --parse_atoms_with_zero_occupancy 1 \
    --chains_to_design "$chains_to_design" \
    --temperature "$temperature" \
    --out_folder "$out_dir" \
    --batch_size "$batch_size" \
    --number_of_batches "$number_of_batches" \
    --save_pdb "$save_pdb"

