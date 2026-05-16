declare -A model_params

model_params["ligandmpnn_v_32_005_25"]="./model_params/ligandmpnn_v_32_005_25.pt"
model_params["ligandmpnn_v_32_010_25"]="./model_params/ligandmpnn_v_32_010_25.pt"
model_params["ligandmpnn_v_32_020_25"]="./model_params/ligandmpnn_v_32_020_25.pt"
model_params["ligandmpnn_v_32_030_25"]="./model_params/ligandmpnn_v_32_030_25.pt"

model_type="ligand_mpnn"

for model in "${!model_params[@]}"; do
    param="${model_params[$model]}"
    echo "Running LigandMPNN with model: $model"
    python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/run.py \
        --model_type $model_type \
        --checkpoint_ligand_mpnn $param \
        --seed 111 \
        --pdb_path '5njx.pdb' \
        --chains_to_design "L" \
        --out_folder "./test/$model" \
        --batch_size 10 \
        --number_of_batches 1
done

