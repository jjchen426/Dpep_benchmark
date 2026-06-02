declare -A model_params

model_params["ligandmpnn_v_32_020_25"]="./model_params/ligandmpnn_v_32_020_25.pt"
# model_params["ligandmpnn_v_32_030_25"]="./model_params/ligandmpnn_v_32_030_25.pt"

model_type="ligand_mpnn"
score_base=/home/junjiechen/1_work/250401-Dpepalign/Benchmark-Filter/Output

for pdb in $(cat /home/junjiechen/1_work/250401-Dpepalign/Benchmark-Filter/datasets/PepSet_3per_length/PDB.list); do

    pdb_path_multi1=$score_base/2000-0.3T/$pdb/ligandmpnn_v_32_020_25/score.json
    for model in "${!model_params[@]}"; do
        param="${model_params[$model]}"
        echo "Running LigandMPNN with model: $model"
        python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/score.py \
            --model_type $model_type \
            --checkpoint_ligand_mpnn $param \
            --seed 111 \
            --autoregressive_score 1 \
            --use_sequence 1 \
            --pdb_path_multi $pdb_path_multi1 \
            --parse_atoms_with_zero_occupancy 1 \
            --chains_to_design "L" \
            --out_folder "$score_base/2000-0.3T/$pdb/$model/score-autoregressive" \
            --batch_size 1 \
            --number_of_batches 10
    done
#     pdb_path_multi2=$score_base/$pdb-merged-0.2-1_2/ligandmpnn_v_32_020_25/score2.json
#     for model in "${!model_params[@]}"; do
#         param="${model_params[$model]}"
#         echo "Running LigandMPNN with model: $model"
#         python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/score.py \
#             --model_type $model_type \
#             --checkpoint_ligand_mpnn $param \
#             --seed 42 \
#             --autoregressive_score 1 \
#             --use_sequence 1 \
#             --pdb_path_multi $pdb_path_multi2 \
#             --parse_atoms_with_zero_occupancy 1 \
#             --chains_to_design "L" \
#             --out_folder "./Output/$pdb-merged-0.2-1_2/$model/score-autoregressive_2" \
#             --batch_size 1 \
#             --number_of_batches 10
#     done
done