#编写bash脚本，进入./*-0.1T/ligandmpnn_v_32_020_25目录，运行protenix predict命令，输入文件为protenix_pred-filter1.json，输出目录为./predict_output-filter1，使用MSA，随机种子为42,43,44
# !/bin/bash
# for dir in *-0.1T; do
#     cd $dir
#     cd ligandmpnn_v_32_020_25
#     echo "Running protenix predict in directory: $dir"
#     protenix predict --input protenix_pred-filter1.json --out_dir ./predict_output-filter1 --use_msa true --seeds 42,43,44 > protenix_predict-filter1.log 2>&1
#     echo "Finished protenix predict in directory: $dir"
#     cd ..
#     cd ..
# done

# for dir in 5v3r* 5xxq* 6b27* 6co4* 6dei* 6f0w* 6f6d* 6fbk* 6g5g*; do
#     cd $dir
#     cd ligandmpnn_v_32_020_25
#     echo "Running protenix predict in directory: $dir"
#     protenix predict --input protenix_pred-filter1.json --out_dir ./predict_output-filter1 --use_msa true --seeds 42,43,44 > protenix_predict-filter1.log 2>&1
#     echo "Finished protenix predict in directory: $dir"
#     echo "----------------------------------------"
#     cd ..
#     cd ..
# done

