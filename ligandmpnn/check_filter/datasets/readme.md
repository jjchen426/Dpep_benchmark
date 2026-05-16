# 2026.3.24
## junjiechen

### 对PepSet-dimer进行结构预测，通过测试的scRMSD最小的pdb数据集
- 采用的筛选条件为bb—scRMSD<=2.5，ipTM>=0.7,pep_pLDDT>=0.7(在AF3中则为>=70)

- PepSet_AF3_pass_processed: AF3 v3.0.1
- PepSet-passed-dimer_processed: Protenix v1.0.0(msa+template)
    - 由于多肽的template对结构预测几乎没有影响，这里不考虑无template的结果。
    - 详细的Protenix对PepSet-dimer结构预测参考/home/junjiechen/1_work/250401-Dpepalign/Benchmark/protenix/PepSet