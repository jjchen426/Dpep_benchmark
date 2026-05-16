for p in $(cat /home/junjiechen/1_work/250401-Dpepalign/Benchmark/protenix/PepSet/dimer/PDB.list)
do
    mkdir $p
    cd $p
    touch hmmsearch.a3m
    cd ..
done
