CUDA_VISIBLE_DEVICES=2 python3 /home/junjiechen/1_work/original_soft/alphafold3/run_alphafold.py \
  --input_dir=/home/junjiechen/1_work/250401-Dpepalign/Benchmark/Rosetta/interface/AF3/predict/inputs-rest \
  --model_dir=/CHU/model_weights/alphafold3 \
  --db_dir=/JIN/databases/alphafold3 \
  --output_dir=/home/junjiechen/1_work/250401-Dpepalign/Benchmark/Rosetta/interface/AF3/predict/outputs > /home/junjiechen/1_work/250401-Dpepalign/Benchmark/Rosetta/interface/AF3/predict/pro_msa_template-pep_nomsa_notemplate-rest.log 2>&1
# cp run.sh /home/junjiechen/1_work/250401-Dpepalign/Benchmark/Rosetta/interface/AF3/predict