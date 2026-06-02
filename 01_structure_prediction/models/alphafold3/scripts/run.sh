# msa_template
python3 /home/junjiechen/1_work/original_soft/alphafold3/run_alphafold.py \
  --input_dir=/home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict/original_result/msa_template/input \
  --model_dir=/CHU/model_weights/alphafold3 \
  --db_dir=/JIN/databases/alphafold3 \
  --output_dir=/home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict/original_result/msa_template/output > /home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict/original_result/msa_template/msa_template.log 2>&1
# cp run.sh /home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict/original_result/msa_template

# nomsa_notemplate
python3 /home/junjiechen/1_work/original_soft/alphafold3/run_alphafold.py \
  --input_dir=/home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict/original_result/nomsa_notemplate/input \
  --model_dir=/CHU/model_weights/alphafold3 \
  --db_dir=/JIN/databases/alphafold3 \
  --output_dir=/home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict/original_result/nomsa_notemplate/output > /home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict/original_result/nomsa_notemplate/nomsa_notemplate.log 2>&1
# cp run.sh /home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict/original_result/nomsa_notemplate

# nomsa_template
python3 /home/junjiechen/1_work/original_soft/alphafold3/run_alphafold.py \
  --input_dir=/home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict/original_result/nomsa_template/input \
  --model_dir=/CHU/model_weights/alphafold3 \
  --db_dir=/JIN/databases/alphafold3 \
  --output_dir=/home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict/original_result/nomsa_template/output > /home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict/original_result/nomsa_template/nomsa_template.log 2>&1
# cp run.sh /home/junjiechen/1_work/250401-Dpepalign/Benchmark/alphafold3/predict/original_result/nomsa_template

