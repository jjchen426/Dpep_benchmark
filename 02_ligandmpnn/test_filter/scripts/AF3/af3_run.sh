# pro_msa_notemplate-pep_nomsa_notemplate

# 编写bash脚本，遍历/home/junjiechen/1_work/250401-Dpepalign/Benchmark/ligandmpnn/test_filter/AF3下的所有目录，传入input_dir
for dir in /home/junjiechen/1_work/250401-Dpepalign/Benchmark/ligandmpnn/test_filter/AF3/*; do
    if [ -d "$dir" ]; then
        filter_name=$(basename "$dir")
        input_dir="$dir/inputs"
        output_dir="$dir/outputs"
        python3 /home/junjiechen/1_work/original_soft/alphafold3/run_alphafold.py \
            --input_dir="$input_dir" \
            --model_dir=/CHU/model_weights/alphafold3 \
            --db_dir=/JIN/databases/alphafold3 \
            --output_dir="$output_dir" >"$dir/${filter_name}.txt" 2>&1
    fi
done

# python3 /home/junjiechen/1_work/original_soft/alphafold3/run_alphafold.py \
#   --input_dir=/home/junjiechen/1_work/250401-Dpepalign/Benchmark/ligandmpnn/test_filter/AF3/ \
#   --model_dir=/CHU/model_weights/alphafold3 \
#   --db_dir=/JIN/databases/alphafold3 \
#   --output_dir=/home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/pro_msa_notemplate-pep_nomsa_notemplate/output >/home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/pro_msa_notemplate-pep_nomsa_notemplate/pro_msa_notemplate-pep_nomsa_notemplate-2.txt 2>&1
# cp run.sh /home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/pro_msa_notemplate-pep_nomsa_notemplate
