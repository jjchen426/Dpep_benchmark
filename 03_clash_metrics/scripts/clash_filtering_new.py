# junjiechen
## 26.04.25
"""clash detection and filtering."""


from __future__ import annotations

import os
import shutil

import numpy as np
from Bio.PDB import PDBParser

VDW_RADII = {"O": 1.6, "N": 1.6, "C": 2.1, "S": 1.8, "H": 1.2}
DEFAULT_VDW = 2.1


def get_element_from_atom(atom_name: str, atom_element: str) -> str:
    """Infer a usable atom element when BioPython returns X."""
    if atom_element != "X":
        return atom_element

    if atom_name.startswith(("O", "OG", "OD", "OE", "OH", "OXT")):
        return "O"
    if atom_name.startswith(("N", "ND", "NE", "NH", "NZ")):
        return "N"
    if atom_name.startswith(("S", "SG")):
        return "S"
    if atom_name.startswith("C"):
        return "C"
    if atom_name.startswith("H"):
        return "H"
    return atom_element


def calculate_distance(
    pdb_file: str,
    chain_id_1: str,
    chain_id_2: str,
    all_atoms: bool = False,
):
    """Calculate all atom-pair distances between two chains. \n
    chain_id_1: binder链, 只考虑骨架和CB原子 \n
    chain_id_2: target or small molecule
    """
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("sample", pdb_file)
    model = structure[0]

    chain1_atoms = []
    chain1_idxs = []
    chain2_atoms = []
    chain2_idxs = []

    if all_atoms:
        for chain in model:
            if chain.get_id() == chain_id_1:
                for residue in chain:
                    for atom in residue:
                        if atom.get_name() in ["N", "CA", "C", "O", "CB"]:
                            chain1_atoms.append(atom.get_coord())
                            chain1_idxs.append((residue.get_id()[1], atom.get_name(), atom.element))
            elif chain.get_id() == chain_id_2:
                for residue in chain:
                    for atom in residue:
                        if not atom.get_name() in ["H", "HA", "HB", "HG", "HD", "HE", "HH"]:
                            chain2_atoms.append(atom.get_coord())
                            chain2_idxs.append((residue.get_id()[1], atom.get_name(), atom.element))
    else:
        for chain in model:
            if chain.get_id() == chain_id_1:
                for residue in chain:
                    for atom in residue:
                        if atom.get_name() in ["N", "CA", "C", "O", "CB"]:
                            chain1_atoms.append(atom.get_coord())
                            chain1_idxs.append((residue.get_id()[1], atom.get_name(), atom.element))
            elif chain.get_id() == chain_id_2:
                for residue in chain:
                    for atom in residue:
                        if atom.get_name() in ["N", "CA", "C", "O", "CB"]:
                            chain2_atoms.append(atom.get_coord())
                            chain2_idxs.append((residue.get_id()[1], atom.get_name(), atom.element))

    if not chain1_atoms or not chain2_atoms:
        return None, None

    coords1 = np.array(chain1_atoms)
    coords2 = np.array(chain2_atoms)
    diff = coords1[:, np.newaxis, :] - coords2[np.newaxis, :, :]
    distance_matrix = np.sqrt(np.sum(diff**2, axis=2))

    index_matrix = []
    for idx1 in chain1_idxs:
        row = []
        for idx2 in chain2_idxs:
            row.append((idx1, idx2))
        index_matrix.append(row)

    return distance_matrix, index_matrix


def count_close_contacts(distance_matrix, index_matrix, vdw_scale: float = 0.7) -> int:
    """Count atom clashes under scaled VDW cutoff."""
    count = 0
    for i in range(distance_matrix.shape[0]):
        for j in range(distance_matrix.shape[1]):
            atom1_info = index_matrix[i][j][0]
            atom2_info = index_matrix[i][j][1]

            elem1 = get_element_from_atom(atom1_info[1], atom1_info[2])
            elem2 = get_element_from_atom(atom2_info[1], atom2_info[2])
            r1 = VDW_RADII.get(elem1, DEFAULT_VDW)
            r2 = VDW_RADII.get(elem2, DEFAULT_VDW)

            if distance_matrix[i, j] < vdw_scale * (r1 + r2):
                count += 1
    return count


def filter_by_clash(
    input_dir: str,
    output_dir: str,
    chain1_id: str,
    chain2_id: str,
    vdw_scale: float = 0.7,
) -> list[str]:
    """Filter PDBs by clash count == 0."""
    os.makedirs(output_dir, exist_ok=True)

    passed_pdbs: list[str] = []
    pdb_files = [x for x in os.listdir(input_dir) if x.endswith(".pdb")]

    for pdb_file in pdb_files:
        pdb_path = os.path.join(input_dir, pdb_file)
        try:
            distance_matrix, index_matrix = calculate_distance(pdb_path, chain1_id, chain2_id)
            if distance_matrix is None:
                continue

            min_distance = np.min(distance_matrix)
            clash_count = count_close_contacts(distance_matrix, index_matrix, vdw_scale)
            print(f"{pdb_file}: min_dist={min_distance:.2f}, clashes={clash_count}")

            if clash_count == 0:
                passed_pdbs.append(pdb_path)
                shutil.copy(pdb_path, os.path.join(output_dir, pdb_file))
                print("  -> 通过clash筛选")
        except Exception as exc:
            print(f"跳过 {pdb_file}: {exc}")

    print(f"\n通过clash筛选: {len(passed_pdbs)}/{len(pdb_files)} 个PDB")
    return passed_pdbs
