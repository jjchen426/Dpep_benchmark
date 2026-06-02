# junjiechen
# 2026.02.01 22.13

#编写bash脚本，进入采用42、43这两个随机数的ligandmpnn序列设计文件夹，运行protenix predict命令，输入文件为pred.json，输出目录为./，使用MSA，随机种子为42,43,44
cd 2000-0.1T-dimer
for pdb in $(cat /home/junjiechen/1_work/250401-Dpepalign/Benchmark/ligandmpnn/test_filter/datasets/PepSet-passed-dimer_processed/PDB_pep_plddt.list); do
    cd $pdb
    cd ligandmpnn_seed43
    echo "Running protenix predict in directory: ligandmpnn_seed43/$pdb"
    CUDA_VISIBLE_DEVICES=1 protenix predict --input pred.json --out_dir ./ --use_msa true --seeds 42,43,44 > protenix_predict.log 2>&1
    echo "Finished protenix predict in directory: ligandmpnn_seed43/$pdb"
    echo "----------------------------------------"
    cd ..
    cd ..
done

# 2k, max confidence