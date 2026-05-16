declare -A model_params

model_params["ligandmpnn_v_32_020_25"]="./model_params/ligandmpnn_v_32_020_25.pt"
# model_params["ligandmpnn_v_32_030_25"]="./model_params/ligandmpnn_v_32_030_25.pt"

model_type="ligand_mpnn"
pdb_path_multi="/home/junjiechen/1_work/250401-Dpepalign/Benchmark-Filter/Output/2000-0.1T/ligandmpnn_v_32_020_25/score_0.1.json"
for model in "${!model_params[@]}"; do
    param="${model_params[$model]}"
    echo "Running LigandMPNN with model: $model"
    CUDA_VISIBLE_DEVICES=1 python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/score.py \
        --model_type $model_type \
        --checkpoint_ligand_mpnn $param \
        --seed 111 \
        --autoregressive_score 1 \
        --use_sequence 1 \
        --pdb_path_multi $pdb_path_multi \
        --parse_atoms_with_zero_occupancy 1 \
        --chains_to_design "L" \
        --out_folder "./Output/2000-0.1T/$model/score-500_0.1" \
        --batch_size 1 \
        --number_of_batches 500
done

