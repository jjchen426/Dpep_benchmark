import sys

def check_pdb_defects(pdb_file):
    print(f"正在检查文件: {pdb_file}")
    
    with open(pdb_file, 'r') as f:
        lines = f.readlines()
        
    atom_lines = [l for l in lines if l.startswith('ATOM') or l.startswith('HETATM')]
    
    # 统计变量
    alt_loc_count = 0
    ca_alt_locs = []
    oxt_count = 0
    residues = {} # key: (chain, resseq, inscode), value: count of CA atoms
    
    for line in atom_lines:
        atom_name = line[12:16].strip()
        alt_loc = line[16] # 第17列是替代构象标识符
        res_name = line[17:20].strip()
        chain = line[21]
        res_seq = line[22:26].strip()
        i_code = line[26]
        
        res_id = f"{chain}_{res_seq}{i_code}".strip()
        
        # 1. 检查替代构象 (AltLoc)
        if alt_loc != ' ':
            alt_loc_count += 1
            if atom_name == 'CA':
                # 记录具体的残基，方便定位
                ca_alt_locs.append(f"{res_name} {res_id} (AltLoc: {alt_loc})")
                
        # 2. 检查 OXT 原子 (有时会干扰骨架定义)
        if atom_name == 'OXT':
            oxt_count += 1
            
        # 3. 统计 CA 原子数量以发现重复
        if atom_name == 'CA':
            residues[res_id] = residues.get(res_id, 0) + 1

    # 输出分析结果
    print("-" * 30)
    print(f"【检查报告】")
    
    # 分析 AltLocs
    unique_residues = len(residues)
    total_ca = sum(residues.values())
    
    print(f"1. 序列长度 (唯一残基数): {unique_residues}")
    print(f"2. CA原子总数: {total_ca}")
    
    diff = total_ca - unique_residues
    if diff > 0:
        print(f"   ⚠️ 发现 {diff} 个额外的 CA 原子！")
        print(f"   具体有问题的残基: {[loc.split()[0:2] for loc in ca_alt_locs if 'A' in loc or 'B' in loc][:5]} ...") # 只显示前几个
    else:
        print("   ✅ 没有发现骨架(CA)冗余。")

    if alt_loc_count > 0:
        print(f"3. 包含替代构象的总原子数: {alt_loc_count}")
    else:
        print("3. 没有发现任何替代构象。")

    if oxt_count > 0:
        print(f"4. 发现 OXT 原子 (C端氧): {oxt_count} 个 (建议移除)")
    
    print("-" * 30)
    print("建议处理：")
    if diff > 0 or alt_loc_count > 0:
        print("运行: pdb_selaltloc 2ivz.pdb | pdb_delhetatm | pdb_tidy > 2ivz_clean.pdb")
    else:
        print("文件看起来很干净，如果报错请检查是否存在非标准残基。")

# 使用方法：将脚本保存为 check_pdb.py，然后运行：
# python check_pdb.py 2ivz.pdb
if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_pdb_defects(sys.argv[1])
    else:
        print("请提供 PDB 文件路径，例如: python check_pdb.py 2ivz.pdb")