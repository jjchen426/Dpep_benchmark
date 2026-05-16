declare -A model_params

model_params["ligandmpnn_v_32_020_25"]="./model_params/ligandmpnn_v_32_020_25.pt"
# model_params["ligandmpnn_v_32_030_25"]="./model_params/ligandmpnn_v_32_030_25.pt"

model_type="ligand_mpnn"
# 读取pdb.list文件，每一行为一个pdb，保存为一个变量pdb_path，然后在循环中使用该变量
for pdb in $(cat /home/junjiechen/1_work/250401-Dpepalign/Benchmark/Rosetta/interface/AF3/data/PepSet_AF3_pass/PDB.list); do
    echo "Processing PDB: $pdb"
    for model in "${!model_params[@]}"; do
        param="${model_params[$model]}"
        echo "Running LigandMPNN with model: $model"
        python /home/junjiechen/1_work/250401-Dpepalign/soft/LigandMPNN/run_test.py \
            --model_type $model_type \
            --checkpoint_ligand_mpnn $param \
            --seed 42 \
            --pdb_path /home/junjiechen/1_work/250401-Dpepalign/Benchmark/Rosetta/interface/AF3/data/PepSet_AF3_pass/$pdb.pdb \
            --parse_atoms_with_zero_occupancy 1 \
            --chains_to_design "B" \
            --temperature 0.1 \
            --out_folder "/home/junjiechen/1_work/250401-Dpepalign/Benchmark/Rosetta/interface/AF3/ligandmpnn/$pdb" \
            --batch_size 50 \
            --omit_AA "C" \
            --number_of_batches 40 \
            --save_pdb 0
    done
done

