# 2026.03.23
## junjiechen

### 测试LigandMPNN在HETATM方法下的相关参数


- test_design_numbers: 在PepSet-3per_length数据集中，检验不同采样次数，最终获得的top10中重复序列的个数，以测试采样饱和时的采样次数

- test_filter: 在不同的数据集中，利用LigandMPNN-HETATM方法进行序列设计，尝试不同的filter方式，最终利用Protenix进行结构预测，检验不同filter方法的成功率

- check_filter: 在PepSet数据集预测的结构的基础上，利用LigandMPNN-HETATM进行三次重复设计，并利用不同的结构预测模型进行进一步的结构预测，检验filter方法的稳定性

- test_weight: 在不同的数据集中，检测不同的LigandMPNN权重设计的序列恢复率。重点比较LigandMPNN、LigandMPNN-HETATM、ProteinMPNN以及Rosetta的差异

- test_hyperparam: 构建pipeline，与test_weight相似，增加了温度变量

- test_score_times: 评估打分次数的影响，但仅测试了1个case，暂时不考虑。在test_filter中测试了打分次数的影响


