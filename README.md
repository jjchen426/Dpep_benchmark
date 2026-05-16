# 2026.02.02
## junjiechen

### ligandmpnn
- test_design_numbers: 测试不同采样次数对序列新颖性的影响，按照max confidence排序
- test_filter: 测试当蛋白视作分子时，不同筛选方式对设计成功率的影响
- test_score_times: 测试不同打分次数对序列分数分布的影响
- test_weight: 测试不同的权重在不同数据集以及加噪数据集上的序列恢复率（PepSet，PeptiDB-Tsaban，Colabfold）

### protenix
- PepSet:对PepSet中的二元复合物（170个）进行结构预测
    - dimer：二元复合物晶体结构
    - dimer：filtered：经过结构预测和指标筛选后的复合物结构，包含cif和对应转换后的pdb
    - MSA_pep：编写的多肽MSA，包含dimer中所有pdb的pairing.a3m和non_pairing.a3m
    - MSA_pro_per3length：从ligandmpnn/test_filter中的3perlength数据集中复制的蛋白MSA，属于dimer的子集
    - pred：结构预测结果，每一个pdb包含三个随机数种子的预测结果


### predict_summary
- 对Protenix和Alphafold3在PepSet数据集上进行结构预测的benchmark，多肽均不添加MSA和template，蛋白考虑msa和template添加与否的四种情况
    - csv_summary: 总结了不同的数据集预测后的输出csv
    - exports: 输出结果，包含数据加载，质量控制
    - figures: 绘制每个pdb以及每个方法的预测结果

### Rosetta
- Interface: 利用不同的方法对PepSet界面进行打分，获得合适的打分指标
- MDM2:包含天然MDM2、L-binder、D-binder
    - 在L-L的体系上test不同的界面指标情况，评价指标的值大小与binder的优劣之间的联系。至少需要找到一个合适的指标大小能够评价这个相互作用的强弱