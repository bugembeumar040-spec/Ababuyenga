#!/usr/bin/env python3
"""Index every plate in the image pack: id, scene, pass, cue, prompt."""
import re

PACK = "clarity/script/clarity-image-prompts.txt"

def index():
    src = open(PACK).read()
    blocks = re.split(r"\n\[ (\d+)/180 \]\s+(\S+)\n", src)
    out = []
    for i in range(1, len(blocks), 3):
        idx, name, body = blocks[i], blocks[i + 1], blocks[i + 2]
        m = re.search(r"scene (\S+)\s+·\s+(\S+) pass\s+·\s+seed group (\S+)", body)
        c = re.search(r"cue (\d+):(\d+)\s+·\s+VO: (.*)", body)
        s = re.search(r"SAVE AS (\S+)", body)
        p = re.search(r"\nPROMPT\n(.*?)\n", body, re.S)
        if not (m and c and s): continue
        out.append(dict(n=int(idx), name=name, scene=m.group(1), pas=m.group(2),
                        seed=m.group(3), cue=int(c.group(1)) * 60 + int(c.group(2)),
                        vo=c.group(3).strip(), save=s.group(1),
                        prompt=p.group(1).strip() if p else ""))
    return out

if __name__ == "__main__":
    import sys
    ix = index()
    print(f"{len(ix)} plates, {len({p['scene'] for p in ix})} scenes")
    if len(sys.argv) > 1:
        q = " ".join(sys.argv[1:]).lower()
        for p in ix:
            if q in p["prompt"].lower():
                print(f"  {p['n']:3d}/180 {p['save']:16s} scene {p['scene']} {p['pas']:5s} "
                      f"cue {p['cue']//60}:{p['cue']%60:02d}  {p['prompt'][:66]}")
