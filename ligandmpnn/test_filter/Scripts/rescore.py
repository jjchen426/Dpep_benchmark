import torch
import os
import pandas as pd
from Bio.PDB import PDBParser
from Bio.SeqUtils import seq1
import os


def overall_confidence_from_score_pt(
        pt_path: str
        )-> float:
    """Compute overall confidence from a LigandMPNN score.pt file."""
    d = torch.load(pt_path, map_location="cpu")
    # inputs from score.py
    log_probs = torch.tensor(d["log_probs"], dtype=torch.float32)  # [N, L, 21]
    native_seq = torch.tensor(d["native_sequence"], dtype=torch.long)  # [L]
    mask = torch.tensor(d["mask"], dtype=torch.float32)  # [L]
    chain_mask = torch.tensor(d["chain_mask"], dtype=torch.float32)  # [L]
    m = mask * chain_mask  # [L]

    # broadcast native sequence across all samples N
    N, L, _ = log_probs.shape
    S_one_hot = torch.nn.functional.one_hot(native_seq, num_classes=21).float()  # [L, 21]
    S_one_hot = S_one_hot.unsqueeze(0).repeat(N, 1, 1)  # [N, L, 21]

    loss_per_pos = -(S_one_hot * log_probs).sum(-1)  # [N, L]
    loss = (loss_per_pos * m).sum(-1) / (m.sum() + 1e-8)  # [N]
    overall_confidence = torch.exp(-loss)  # [N]
    return overall_confidence.mean().item()