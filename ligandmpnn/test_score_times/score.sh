declare -A model_params

model_params["ligandmpnn_v_32_020_25"]="./model_params/ligandmpnn_v_32_020_25.pt"
# model_params["ligandmpnn_v_32_030_25"]="./model_params/ligandmpnn_v_32_030_25.pt"

model_type="ligand_mpnn"
# for model in "${!model_params[@]}"; do
#     param="${model_params[$model]}"
#     echo "Running LigandMPNN with model: $model"
#     CUDA_VISIBLE_DEVICES=1 python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/score.py \
#         --model_type $model_type \
#         --checkpoint_ligand_mpnn $param \
#         --seed 111 \
#         --autoregressive_score 1 \
#         --use_sequence 1 \
#         --pdb_path "/home/junjiechen/1_work/250401-Dpepalign/LigandMPNN/test_design_numbers/100-0.1T/ligandmpnn_v_32_020_25/backbones/1a0n_1.pdb" \
#         --parse_atoms_with_zero_occupancy 1 \
#         --chains_to_design "L" \
#         --out_folder "./test_score_times/10_times" \
#         --batch_size 1 \
#         --number_of_batches 10
# done

# for model in "${!model_params[@]}"; do
#     param="${model_params[$model]}"
#     echo "Running LigandMPNN with model: $model"
#     CUDA_VISIBLE_DEVICES=1 python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/score.py \
#         --model_type $model_type \
#         --checkpoint_ligand_mpnn $param \
#         --seed 111 \
#         --autoregressive_score 1 \
#         --use_sequence 1 \
#         --pdb_path "/home/junjiechen/1_work/250401-Dpepalign/LigandMPNN/test_design_numbers/100-0.1T/ligandmpnn_v_32_020_25/backbones/1a0n_1.pdb" \
#         --parse_atoms_with_zero_occupancy 1 \
#         --chains_to_design "L" \
#         --out_folder "./test_score_times/50_times" \
#         --batch_size 1 \
#         --number_of_batches 50
# done

# for model in "${!model_params[@]}"; do
#     param="${model_params[$model]}"
#     echo "Running LigandMPNN with model: $model"
#     CUDA_VISIBLE_DEVICES=1 python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/score.py \
#         --model_type $model_type \
#         --checkpoint_ligand_mpnn $param \
#         --seed 111 \
#         --autoregressive_score 1 \
#         --use_sequence 1 \
#         --pdb_path "/home/junjiechen/1_work/250401-Dpepalign/LigandMPNN/test_design_numbers/100-0.1T/ligandmpnn_v_32_020_25/backbones/1a0n_1.pdb" \
#         --parse_atoms_with_zero_occupancy 1 \
#         --chains_to_design "L" \
#         --out_folder "./test_score_times/100_times" \
#         --batch_size 1 \
#         --number_of_batches 100
# done

for model in "${!model_params[@]}"; do
    param="${model_params[$model]}"
    echo "Running LigandMPNN with model: $model"
    CUDA_VISIBLE_DEVICES=1 python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/score.py \
        --model_type $model_type \
        --checkpoint_ligand_mpnn $param \
        --seed 111 \
        --autoregressive_score 1 \
        --use_sequence 1 \
        --pdb_path "/home/junjiechen/1_work/250401-Dpepalign/LigandMPNN/test_design_numbers/100-0.1T/ligandmpnn_v_32_020_25/backbones/1a0n_1.pdb" \
        --parse_atoms_with_zero_occupancy 1 \
        --chains_to_design "L" \
        --out_folder "./test_score_times/250_times" \
        --batch_size 1 \
        --number_of_batches 250
done

# for model in "${!model_params[@]}"; do
#     param="${model_params[$model]}"
#     echo "Running LigandMPNN with model: $model"
#     CUDA_VISIBLE_DEVICES=1 python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/score.py \
#         --model_type $model_type \
#         --checkpoint_ligand_mpnn $param \
#         --seed 111 \
#         --autoregressive_score 1 \
#         --use_sequence 1 \
#         --pdb_path "/home/junjiechen/1_work/250401-Dpepalign/LigandMPNN/test_design_numbers/100-0.1T/ligandmpnn_v_32_020_25/backbones/1a0n_1.pdb" \
#         --parse_atoms_with_zero_occupancy 1 \
#         --chains_to_design "L" \
#         --out_folder "./test_score_times/500_times" \
#         --batch_size 1 \
#         --number_of_batches 500
# done

# for model in "${!model_params[@]}"; do
#     param="${model_params[$model]}"
#     echo "Running LigandMPNN with model: $model"
#     CUDA_VISIBLE_DEVICES=1 python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/score.py \
#         --model_type $model_type \
#         --checkpoint_ligand_mpnn $param \
#         --seed 111 \
#         --autoregressive_score 1 \
#         --use_sequence 1 \
#         --pdb_path "/home/junjiechen/1_work/250401-Dpepalign/LigandMPNN/test_design_numbers/100-0.1T/ligandmpnn_v_32_020_25/backbones/1a0n_1.pdb" \
#         --parse_atoms_with_zero_occupancy 1 \
#         --chains_to_design "L" \
#         --out_folder "./test_score_times/1000_times" \
#         --batch_size 1 \
#         --number_of_batches 1000
# done