cat pred_v0.5.0_msa_notemplate.list | parallel -j 10 > out/pred_v0.5.0_msa_notemplate.out
wait
cat pred_v1_msa_notemplate.list | parallel -j 10 > out/pred_v1_msa_notemplate.out
wait
cat pred_v1_msa_pep-notemplate.list | parallel -j 10 > out/pred_v1_msa_pep-notemplate.out
wait
cat pred_v1_msa_template.list | parallel -j 10 > out/pred_v1_msa_template.out
wait
cat pred_v1_nomsa_template.list | parallel -j 10 > out/pred_v1_nomsa_template.out
