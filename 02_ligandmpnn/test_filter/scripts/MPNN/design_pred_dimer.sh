declare -A model_params

model_params["ligandmpnn_v_32_020_25"]="./model_params/ligandmpnn_v_32_020_25.pt"
# model_params["ligandmpnn_v_32_030_25"]="./model_params/ligandmpnn_v_32_030_25.pt"

model_type="ligand_mpnn"
# 读取pdb.list文件，每一行为一个pdb，保存为一个变量pdb_path，然后在循环中使用该变量
for pdb in $(cat /home/junjiechen/1_work/250401-Dpepalign/Benchmark/ligandmpnn/test_filter/datasets/PepSet-passed-dimer_processed/PDB_pep_plddt.list); do
    echo "Processing PDB: $pdb"
    for model in "${!model_params[@]}"; do
        param="${model_params[$model]}"
        echo "Running LigandMPNN with model: $model"
        python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/run.py \
            --model_type $model_type \
            --checkpoint_ligand_mpnn $param \
            --seed 42 \
            --pdb_path /home/junjiechen/1_work/250401-Dpepalign/Benchmark/ligandmpnn/test_filter/datasets/PepSet-passed-dimer_processed/$pdb.pdb \
            --parse_atoms_with_zero_occupancy 1 \
            --chains_to_design "B" \
            --temperature 0.1 \
            --out_folder "./LigandMPNN-Output-pred_dimer/2000-0.1T/$pdb/seed42" \
            --batch_size 200 \
            --omit_AA "C" \
            --number_of_batches 10
    done

    for model in "${!model_params[@]}"; do
        param="${model_params[$model]}"
        echo "Running LigandMPNN with model: $model"
        python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/run.py \
            --model_type $model_type \
            --checkpoint_ligand_mpnn $param \
            --seed 43 \
            --pdb_path /home/junjiechen/1_work/250401-Dpepalign/Benchmark/ligandmpnn/test_filter/datasets/PepSet-passed-dimer_processed/$pdb.pdb \
            --parse_atoms_with_zero_occupancy 1 \
            --chains_to_design "B" \
            --temperature 0.1 \
            --out_folder "./LigandMPNN-Output-pred_dimer/2000-0.1T/$pdb/seed43" \
            --batch_size 200 \
            --omit_AA "C" \
            --number_of_batches 10
    done

    for model in "${!model_params[@]}"; do
        param="${model_params[$model]}"
        echo "Running LigandMPNN with model: $model"
        python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/run.py \
            --model_type $model_type \
            --checkpoint_ligand_mpnn $param \
            --seed 44 \
            --pdb_path /home/junjiechen/1_work/250401-Dpepalign/Benchmark/ligandmpnn/test_filter/datasets/PepSet-passed-dimer_processed/$pdb.pdb \
            --parse_atoms_with_zero_occupancy 1 \
            --chains_to_design "B" \
            --temperature 0.1 \
            --out_folder "./LigandMPNN-Output-pred_dimer/2000-0.1T/$pdb/seed44" \
            --batch_size 200 \
            --omit_AA "C" \
            --number_of_batches 10
    done
done

