# !/bin/bash
# #编写bash脚本，进入./*-0.1T/ligandmpnn_v_32_020_25目录，采用model=0.5.0运行protenix predict命令，输入文件为protenix_pred-filter1.json，输出目录为./predict_output-filter1，使用MSA，随机种子为42,43,44
# CUDA_VISIBLE_DEVICES=1 protenix pred \
#     --input job.json \
#     --out_dir ./test \
#     --use_msa true \
#     --model_name protenix_base_default_v0.5.0 \
#     --seeds 42,43,44 > pred.log 2>&1



# protenix_base_default_v1.0.0, using template
# CUDA_VISIBLE_DEVICES=0 protenix pred \
#     -i job2.json \
#     -o ./pred_v1_msa_template \
#     -s 42,43,44 \
#     --model_name protenix_base_default_v1.0.0 \
#     --use_msa true \
#     --use_template true > pred_base_v1.log 2>&1


cp job2.json ./pred_v1-pro_nomsa_notemplate-pep_nomsa_notemplate
cp run.sh ./pred_v1-pro_nomsa_notemplate-pep_nomsa_notemplate
CUDA_VISIBLE_DEVICES=1 protenix pred \
    -i job2.json \
    -o ./pred_v1-pro_nomsa_notemplate-pep_nomsa_notemplate \
    -s 42,43,44 \
    --model_name protenix_base_default_v1.0.0 \
    --use_msa false \
    --use_template false > ./pred_v1-pro_nomsa_notemplate-pep_nomsa_notemplate/pred_v1-pro_nomsa_notemplate-pep_nomsa_notemplate.log 2>&1
