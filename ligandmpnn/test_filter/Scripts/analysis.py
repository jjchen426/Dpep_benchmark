import pandas as pd
from pathlib import Path



def dedup_fasta(
        src_path: str,
        dst_path: str
        ) -> None:
    """
    Deduplicate a FASTA file based on sequence content, skipping the first two lines.
    The output FASTA file will have headers reformatted to include name, index, and temperature."""
    src = Path(src_path)
    dst = Path(dst_path)

    with src.open('r', encoding='utf-8') as f:
        lines = f.readlines()

    # Skip the first two lines (start reading from the 3rd line)
    lines = lines[2:]

    unique = []
    seen = set()
    header = None
    seq_lines = []

    def commit(hdr, seq_str):
        if not hdr:
            return
        if seq_str not in seen:
            seen.add(seq_str)
            unique.append((hdr, seq_str))

    for line in lines:
        line = line.rstrip('\n')
        if line.startswith('>'):
            # commit previous record
            commit(header, ''.join(seq_lines).strip())
            header = line
            seq_lines = []
        else:
            if line.strip():
                seq_lines.append(line.strip())
    # commit last record
    commit(header, ''.join(seq_lines).strip())

    with dst.open('w', encoding='utf-8') as out:
        for (hdr, seq) in unique:
            raw = hdr[1:].strip()
            parts = raw.split(',')
            parts = [p.strip() for p in parts]
            idx = parts[1].split('=')[1]
            temperature = parts[2].split('=')[1]
            name = parts[0] if parts else ''
            new_hdr = f">{name}_{idx}_{temperature}"
            out.write(new_hdr + '\n')
            for i in range(0, len(seq), 60):
                out.write(seq[i:i + 60] + '\n')


