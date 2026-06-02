"""Compress all PDBs to .pdb.gz and archive by dataset source group.

Step 1: For each .pdb file, create a .pdb.gz in 00_compressed/ mirroring the
original directory structure (keeps original files untouched).

Step 2: For each dataset source group, bundle all .pdb.gz files into one tar.gz
stored in 00_compressed/.
"""
import gzip
import shutil
import tarfile
from pathlib import Path

DATASET = Path(__file__).resolve().parent
COMPRESSED = DATASET / "00_compressed"

# Dataset source groups: group_name -> list of subdirectory names
GROUPS = {
    "Colabfold": [
        "Colabfold",
        *(f"Colabfold-noise-{i/10:.1f}" for i in range(1, 6)),
    ],
    "PepSet": [
        "PepSet",
        *(f"PepSet-noise-{i/10:.1f}" for i in range(1, 6)),
    ],
    "PepSet_AF3_noC_pass": [
        "PepSet_AF3_noC_pass",
        *(f"PepSet_AF3_noC_pass-{i/10:.1f}" for i in range(1, 6)),
    ],
    "PepSet_AF3_noC_pass-HETATM": [
        "PepSet_AF3_noC_pass-HETATM",
        *(f"PepSet_AF3_noC_pass-HETATM-{i/10:.1f}" for i in range(1, 6)),
    ],
    "PepSet_dimer": ["PepSet_dimer"],
    "PeptiDB-Tsaban": ["PeptiDB-Tsaban"],
}


def compress_pdbs():
    """Step 1: gzip all PDBs into 00_compressed/ mirroring original paths."""
    # Collect all PDBs across all dataset directories (excluding 00_compressed)
    all_pdbs = []
    for subdir in sorted(d for d in DATASET.iterdir() if d.is_dir() and d.name != "00_compressed"):
        all_pdbs.extend(sorted(subdir.rglob("*.pdb")))

    count = 0
    for pdb_path in all_pdbs:
        # Relative path under dataset/
        rel_path = pdb_path.relative_to(DATASET)
        # Output: 00_compressed/<rel_path>.gz
        gz_path = COMPRESSED / f"{rel_path}.gz"
        gz_path.parent.mkdir(parents=True, exist_ok=True)

        with open(pdb_path, "rb") as f_in:
            with gzip.open(gz_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        count += 1
        if count % 500 == 0:
            print(f"  Compressed {count} PDBs...")

    print(f"  Total PDBs compressed: {count}")
    return count


def archive_groups():
    """Step 2: create one tar.gz per dataset group in 00_compressed/."""
    total = 0
    for group_name, subdirs in GROUPS.items():
        tar_path = COMPRESSED / f"{group_name}.tar.gz"
        files_added = 0
        skipped = 0

        with tarfile.open(tar_path, "w:gz") as tar:
            for subdir in subdirs:
                src_dir = COMPRESSED / subdir
                if not src_dir.is_dir():
                    continue
                for gz_file in sorted(src_dir.rglob("*.pdb.gz")):
                    arcname = gz_file.relative_to(COMPRESSED)
                    if "processed" in str(arcname).lower():
                        skipped += 1
                        continue
                    tar.add(gz_file, arcname=arcname)
                    files_added += 1

        print(f"  {group_name}.tar.gz: {files_added} files (skipped {skipped} processed)")
        total += files_added
    print(f"  Total files archived: {total}")


if __name__ == "__main__":
    COMPRESSED.mkdir(parents=True, exist_ok=True)

    print("Step 1: Compressing PDBs to .pdb.gz ...")
    n = compress_pdbs()
    print(f"  Done — {n} .pdb.gz files created in {COMPRESSED}/\n")

    print("Step 2: Creating group tar.gz archives ...")
    archive_groups()
    print("  All done!")
