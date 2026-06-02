# 2026.02.02：目录说明
## junjiechen


dataset：包含PepSet的不同子集，其中
- 3per_length：5-20个多肽长度，每个随机取3个pdb组成的48个pdb集合
- 5d94：pdb为5d94，仅作test
- PepSet-passed-dimer_processed：对PepSet的所有二聚体进行3随机数种子的结构预测，每个结构复合物5个sample，对结果计算scRMSD，按照scRMSD<2.5，ipTM>70，pLDDT>85进行筛选，通过筛选且scRMSD最小的pdb组成的集合，包含93个pdb，其中有33个在3per_length中

LigandMPNN—Output：对3per_length的pdb中binder序列进行设计，不同温度、采样总数、打分方式以及筛选方式的目录

LigandMPNN-Output-pred_dimer：对PepSet-passed-dimer_processed中的binder骨架进行的三次重复设计，采用42、43、44三个随机数，在T=0.1的条件下设计2000条序列，按照Max confidence排序去重

Protenix：对设计结果进行自洽性验证


