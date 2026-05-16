# 2026.03.23
## junjiechen

- dimer: 使用的PepSet-dimer数据集，包含170个蛋白-多肽复合物的晶体结构
- MSA_pep：多肽序列的MSA文件，每个多肽仅有自身序列作为MSA信息
- MSA_pro_all_PepSet_dimer: 蛋白序列的MSA文件，由Protenix的MSA计算获得
- PepSet_AF3_noC_pass: 通过了AF3验证的、多肽scRMSD最小的pdb，其中多肽链不包含Cys
- PepSet_AF3_noC_pass-HETATM: 通过了AF3验证的、多肽scRMSD最小的pdb，其中多肽链不包含Cys，并将蛋白链的残基名称和属性修改为"UNK"与"HETATM"，以供LigandMPNN-HETATM设计使用
- PepSet_AF3_pass: 包含了所有通过AF3验证的、多肽scRMSD最小的pdb，蛋白添加msa和template，多肽无msa和template
- PepSet_dimer_noC: AF3对PepSet-dimer中多肽链无Cys的复合物所有预测结果
- PepSet_dimer_withC: AF3对PepSet-dimer中多肽链含有Cys的复合物所有预测结果


# 2026.03.26
## junjiechen

修改了AF3输出的文件名，统一为蛋白和多肽是否使用msa和template
- pro_msa_notemplate-pep_nomsa_notemplate
- pro_msa_template-pep_nomsa_notemplate（即包含了noC和withC的最初的所有结果）
- pro_nomsa_notemplate-pep_nomsa_notemplate
- pro_nomsa_template-pep_nomsa_notemplate


<p> 
注意!在前两个蛋白采用了msa的预测任务中，使用的是已经预先计算了msa的路径，在json文件中写入的键为pairedMsaPath和unpairedMsaPath，而多肽也是使用的path
但是多肽的path中写入的msa仅包含其自身序列，也意味着没有使用msa。
<p> 这么写的原因在于先前不知道可以通过设置msa为空字符串来限制不使用msa
<p> 后续在pro_nomsa_notemplate-pep_nomsa_notemplate和pro_nomsa_template-pep_nomsa_notemplate中直接在json里传入"pairedMsa": "", "unpairedMsa": ""来避免使用msa
