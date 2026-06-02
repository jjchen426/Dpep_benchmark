# 采用loop=10，NUM_SAMPLING_STEPS=68


import os
os.environ["CUDA_VISIBLE_DEVICES"] = "1"

from itertools import groupby
from Bio.PDB import PDBParser
from Bio.SeqUtils import seq1
import json
import torch

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"


from esm.utils.msa import MSA
from esm.models.esmfold2 import (
    ProteinInput,
    ESMFold2InputBuilder,
    StructurePredictionInput,
)
from transformers.models.esmfold2.modeling_esmfold2 import ESMFold2Model


# MODEL_DEVICE = "cuda:2"
MODEL_ID = "biohub/ESMFold2-Fast"
NUM_LOOPS = 10
NUM_SAMPLING_STEPS = 68
SEEDS = [42, 43, 44]
SAMPLES_PER_SEED = 5
INPUT_ROOT = "./PepSet_dimer"
OUTPUT_ROOT = "./predict/PepSet_dimer_output_esmfold2_fast_loop10_samplingsteps68"
# MSA_PATH = "/home/junjiechen/1_work/250401-Dpepalign/Benchmark/dataset_for_predict/MSA_pro_all_PepSet_dimer"

if not os.path.exists(OUTPUT_ROOT):
    os.makedirs(OUTPUT_ROOT)


model = ESMFold2Model.from_pretrained(MODEL_ID).cuda().eval()


def compute_chain_plddt_mean(complex_obj) -> dict:
    chain_lookup = complex_obj.metadata.chain_lookup
    chain_labels = [
        str(chain_lookup.get(int(chain_id), int(chain_id)))
        for chain_id in complex_obj.chain_id.tolist()
    ]
    entries_sorted = sorted(
        zip(chain_labels, complex_obj.plddt.tolist()),
        key=lambda x: x[0],
    )
    return {
        label: (sum(values) / len(values) if values else None)
        for label, group in groupby(entries_sorted, key=lambda x: x[0])
        for values in ([v for _, v in group],)
    }


def get_pep_seq(
    pdb_code: str,
    complex_base_dir: str,
) -> tuple:
    """从complex的pdb文件中提取pro和pep的序列"""
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure(pdb_code, f"{complex_base_dir}/{pdb_code}.pdb")
    for model in structure:
        for chain in model:
            if chain.id == "L":
                pep_sequence = ""
                for residue in chain:
                    if residue.id[0] == " ":
                        one_letter_resname = seq1(residue.get_resname())
                        pep_sequence += one_letter_resname
            else:
                pro_sequence = ""
                for residue in chain:
                    if residue.id[0] == " ":
                        one_letter_resname = seq1(residue.get_resname())
                        pro_sequence += one_letter_resname
    return pro_sequence, pep_sequence






os.makedirs(OUTPUT_ROOT, exist_ok=True)
for pdb in sorted(os.listdir(INPUT_ROOT)):
    if pdb.endswith(".pdb"):
        complex_name = pdb[:-4]
        try:
            SEQ_PRO, SEQ_PEP = get_pep_seq(complex_name, INPUT_ROOT)
            # msa = MSA.from_a3m(path=f"{MSA_PATH}/{complex_name}/non_pairing.a3m", remove_insertions=True, max_sequences=1000)
            # print(f"MSA depth: {msa.depth} sequences, length: {msa.seqlen} residues")
            # # Sanity check — first MSA seq should match the query
            # print("First MSA seq matches query:", msa.sequences[0] == SEQ_PRO)
            # print("First MSA seq:", repr(msa.sequences[0][:80]))
            # print("Query:        ", repr(SEQ_PRO))

            inputs = StructurePredictionInput(
                sequences=[
                    ProteinInput(id="A", sequence=SEQ_PRO),     # 不添加msa
                    ProteinInput(id="B", sequence=SEQ_PEP),     # 多肽不添加msa
                ]
            )

            for base_seed in SEEDS:
                for i in range(SAMPLES_PER_SEED):
                    sample_seed = base_seed * 100 + i
                    result = ESMFold2InputBuilder().fold(
                        model,
                        inputs,
                        num_loops=NUM_LOOPS,
                        num_sampling_steps=NUM_SAMPLING_STEPS,
                        num_diffusion_samples=1,
                        seed=sample_seed,
                    )

                    sample_dir = os.path.join(
                        OUTPUT_ROOT,
                        complex_name,
                        f"seed-{base_seed}-sample-{i}",
                    )
                    os.makedirs(sample_dir, exist_ok=True)

                    result_json = {
                        "base_seed": base_seed,
                        "sample_seed": sample_seed,
                        "sample_index": i,
                        "complex": {
                            "id": result.complex.id,
                            "plddt": result.complex.plddt.tolist(),
                            "chain_plddt_mean": compute_chain_plddt_mean(result.complex),
                        },
                        "plddt_mean": float(result.complex.plddt.mean()),
                        "ptm": float(result.ptm),
                        "iptm": float(result.iptm),
                    }

                    json_path = os.path.join(sample_dir, "result.json")
                    with open(json_path, "w") as f:
                        json.dump(result_json, f, indent=2)

                    cif_path = os.path.join(sample_dir, "complex.cif")
                    with open(cif_path, "w") as f:
                        f.write(result.complex.to_mmcif())

                    torch.cuda.empty_cache()
        except torch.OutOfMemoryError:
            print(f"  CUDA OOM on {complex_name}, skipping.")
            torch.cuda.empty_cache()
