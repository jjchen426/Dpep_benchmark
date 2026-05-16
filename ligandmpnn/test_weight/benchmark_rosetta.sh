# rosetta

input_list=$1
xml=pack_design.xml
nproc=20
rosetta_app=rosetta_scripts.mpi.linuxgccrelease
base_out=$2
# IFS=$' \t\n'

# while IFS= read -r line; do
#     # 跳过空行
#     [ -z "$line" ] && continue

#     pdb_name=$(basename "$line" .pdb)

#     # 输出目录（结构清晰）
#     out_dir="$base_out/$pdb_name"
#     mkdir -p "$out_dir"
#     echo "----------------------------------------"
#     echo "Processing: $line"
#     echo "PDB name: $pdb_name"
#     echo "Output -> $out_dir"

    # 执行 rosetta_scripts
        # mpirun -np $nproc $rosetta_app \
        # -s $line \
        # -parser:protocol $xml \
        # -parser:script_vars wts=ref2015 \
        # -nstruct 10 \
        # -out:path:all $out_dir \
        # -ignore_unrecognized_res true \
        # -beta \
        # -overwrite \
        # > $out_dir/run.log 2>&1 < /dev/null
    # mpirun -np $nproc $rosetta_app \
    #     -s $line \
    #     -parser:protocol $xml \
    #     -parser:script_vars wts=/home/junjiechen/1_work/250401-Dpepalign/Benchmark/Rosetta/Rosetta-interface/weights_and_flags_files/beta_jan25_cart.wts \
    #     @/home/junjiechen/1_work/250401-Dpepalign/Benchmark/Rosetta/Rosetta-interface/weights_and_flags_files/beta_jan25_flags \
    #     -nstruct 10 \
    #     -out:path:all $out_dir \
    #     -ignore_unrecognized_res true \
    #     -beta \
    #     -overwrite \
    #     > $out_dir/run.log 2>&1 < /dev/null
# done < $input_list
# mkdir -p $base_out/6h7b
mpirun -np $nproc $rosetta_app \
        -s $1 \
        -parser:protocol $xml \
        -parser:script_vars wts=ref2015 \
        -nstruct 10 \
        -out:path:all $base_out/4x2h \
        -ignore_unrecognized_res true \
        -beta \
        -overwrite \
        > $base_out/4x2h/run.log 2>&1 < /dev/null