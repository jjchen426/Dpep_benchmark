# 将Output目录下所有.fa文件软连接到10000目录下
tar_dir='/home/junjiechen/1_work/250401-Dpepalign/Benchmark-Filter/ligandmpnn/seq_num/10000'
base_dir='/home/junjiechen/1_work/250401-Dpepalign/Benchmark-Filter/Output'
for file in $(find $base_dir -name "*.fa"); do
    ln -s $file $tar_dir
done