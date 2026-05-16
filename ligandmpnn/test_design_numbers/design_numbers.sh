declare -A model_params

model_params["ligandmpnn_v_32_020_25"]="./model_params/ligandmpnn_v_32_020_25.pt"
# model_params["ligandmpnn_v_32_030_25"]="./model_params/ligandmpnn_v_32_030_25.pt"

model_type="ligand_mpnn"
pdb_path_multi=/home/junjiechen/1_work/250401-Dpepalign/Benchmark-Filter/datasets/PepSet_3per_length/Processed.json

for model in "${!model_params[@]}"; do
    param="${model_params[$model]}"
    echo "Running LigandMPNN with model: $model"
    CUDA_VISIBLE_DEVICES=1 python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/run.py \
        --model_type $model_type \
        --checkpoint_ligand_mpnn $param \
        --seed 111 \
        --pdb_path_multi $pdb_path_multi \
        --parse_atoms_with_zero_occupancy 1 \
        --chains_to_design "L" \
        --temperature 0.1 \
        --out_folder "./ligandmpnn/100-0.1T/$model" \
        --batch_size 100 \
        --number_of_batches 1
done

for model in "${!model_params[@]}"; do
    param="${model_params[$model]}"
    echo "Running LigandMPNN with model: $model"
    CUDA_VISIBLE_DEVICES=1 python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/run.py \
        --model_type $model_type \
        --checkpoint_ligand_mpnn $param \
        --seed 111 \
        --pdb_path_multi $pdb_path_multi \
        --parse_atoms_with_zero_occupancy 1 \
        --chains_to_design "L" \
        --temperature 0.1 \
        --out_folder "./ligandmpnn/500-0.1T/$model" \
        --batch_size 500 \
        --number_of_batches 1
done

for model in "${!model_params[@]}"; do
    param="${model_params[$model]}"
    echo "Running LigandMPNN with model: $model"
    CUDA_VISIBLE_DEVICES=1 python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/run.py \
        --model_type $model_type \
        --checkpoint_ligand_mpnn $param \
        --seed 111 \
        --pdb_path_multi $pdb_path_multi \
        --parse_atoms_with_zero_occupancy 1 \
        --chains_to_design "L" \
        --temperature 0.1 \
        --out_folder "./ligandmpnn/1000-0.1T/$model" \
        --batch_size 1000 \
        --number_of_batches 1
done

for model in "${!model_params[@]}"; do
    param="${model_params[$model]}"
    echo "Running LigandMPNN with model: $model"
    CUDA_VISIBLE_DEVICES=1 python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/run.py \
        --model_type $model_type \
        --checkpoint_ligand_mpnn $param \
        --seed 111 \
        --pdb_path_multi $pdb_path_multi \
        --parse_atoms_with_zero_occupancy 1 \
        --chains_to_design "L" \
        --temperature 0.1 \
        --out_folder "./ligandmpnn/2000-0.1T/$model" \
        --batch_size 2000 \
        --number_of_batches 1
done

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
        --temperature 0.1 \
        --out_folder "./test_design_numbers/5000-0.1T/$model" \
        --batch_size 500 \
        --number_of_batches 10
done