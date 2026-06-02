# 2026.03.23
## junjiechen

- 采用的数据集来源为PepSet-dimer数据集，包含170个蛋白-多肽复合物的晶体结构
- MSA_pep：多肽序列的MSA文件，每个多肽仅有自身序列作为MSA信息
- MSA_pro_all_PepSet_dimer: 蛋白序列的MSA文件，由Protenix的MSA计算获得


# 2026.03.26
## junjiechen

修改了AF3输出的文件名，统一为蛋白和多肽是否使用msa和template，存放在predict目录下
- pro_msa_notemplate-pep_nomsa_notemplate
- pro_msa_template-pep_nomsa_notemplate（即包含了noC和withC的最初的所有结果）
- pro_nomsa_notemplate-pep_nomsa_notemplate
- pro_nomsa_template-pep_nomsa_notemplate


<p> 
注意!在前两个蛋白采用了msa的预测任务中，使用的是已经预先计算了msa的路径，在json文件中写入的键为pairedMsaPath和unpairedMsaPath，而多肽也是使用的path
但是多肽的path中写入的msa仅包含其自身序列，也意味着没有使用msa。
<p> 这么写的原因在于先前不知道可以通过设置msa为空字符串来限制不使用msa
<p> 后续在pro_nomsa_notemplate-pep_nomsa_notemplate和pro_nomsa_template-pep_nomsa_notemplate中直接在json里传入"pairedMsa": "", "unpairedMsa": ""来避免使用msa
