#编写bash脚本，进入./*-0.1T/ligandmpnn_v_32_020_25目录，运行protenix predict命令，输入文件为protenix_pred-filter1.json，输出目录为./predict_output-filter1，使用MSA，随机种子为42,43,44
# !/bin/bash
for pdb in $(cat /home/junjiechen/1_work/250401-Dpepalign/Benchmark-Filter/datasets/PepSet_3per_length/PDB.list); do
    cd 10000-0.1T
    cd $pdb
    echo "Running protenix predict in directory: $pdb"
    CUDA_VISIBLE_DEVICES=2 protenix predict --input pred_filter12.json --out_dir ./predict_output-filter12 --use_msa true --seeds 42,43,44 > protenix_predict-filter12.log 2>&1
    echo "Finished protenix predict in directory: $pdb -filter12"
    echo "----------------------------------------"
    cd ..
    cd ..
done

# 10k, ranked by mean overall confidence