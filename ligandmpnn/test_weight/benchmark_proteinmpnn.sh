declare -A model_params

model_params["proteinmpnn_v_48_002"]="./model_params/proteinmpnn_v_48_002.pt"
model_params["proteinmpnn_v_48_010"]="./model_params/proteinmpnn_v_48_010.pt"
model_params["proteinmpnn_v_48_020"]="./model_params/proteinmpnn_v_48_020.pt"
model_params["proteinmpnn_v_48_030"]="./model_params/proteinmpnn_v_48_030.pt"

model_type="protein_mpnn"
pdb_path_multi=$1

for model in "${!model_params[@]}"; do
    param="${model_params[$model]}"
    echo "Running ProteinMPNN with model: $model"
    noise="${noise#"${noise%%[!0]*}"}"
    noise=${noise:-0}
    python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/run.py \
        --model_type $model_type \
        --checkpoint_protein_mpnn $param \
        --seed 111 \
        --pdb_path_multi $pdb_path_multi \
        --parse_atoms_with_zero_occupancy 1 \
        --chains_to_design "L" \
        --out_folder "./$2/$noise" \
        --batch_size 10 \
        --number_of_batches 1
done

