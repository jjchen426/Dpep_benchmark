CUDA_VISIBLE_DEVICES=1 protenix pred \
    -i job2.json \
    -o ./test \
    -s 42,43,44 \
    --model_name protenix_base_default_v1.0.0 \
    --use_msa false \
    --use_template false > test.log 2>&1
