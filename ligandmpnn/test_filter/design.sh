declare -A model_params

model_params["ligandmpnn_v_32_020_25"]="./model_params/ligandmpnn_v_32_020_25.pt"
# model_params["ligandmpnn_v_32_030_25"]="./model_params/ligandmpnn_v_32_030_25.pt"

model_type="ligand_mpnn"
pdb_path_multi=/home/junjiechen/1_work/250401-Dpepalign/Benchmark-Filter/datasets/PepSet_3per_length/Processed.json

for model in "${!model_params[@]}"; do
    param="${model_params[$model]}"
    echo "Running LigandMPNN with model: $model"
    python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/run.py \
        --model_type $model_type \
        --checkpoint_ligand_mpnn $param \
        --seed 111 \
        --pdb_path_multi $pdb_path_multi \
        --parse_atoms_with_zero_occupancy 1 \
        --chains_to_design "L" \
        --temperature 0.2 \
        --out_folder "./Output/PepSet_3per_length-0.2T/$model" \
        --batch_size 1000 \
        --number_of_batches 1
done
