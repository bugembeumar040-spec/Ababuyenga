#!/usr/bin/env python3
"""Re-derive scene cue times from the assembled master.

The image pack's cue times were written against the script's ~150wpm estimate
(43:18). The recorded master runs shorter, so every cue drifts. This locates
each scene's VO anchor line in the real audio and reports the true cue.
"""
import json, re, sys, os, difflib
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit import norm

PACK = "clarity/script/clarity-image-prompts.txt"
EDL  = "clarity/master/edl.json"

def master_words():
    """[(abs_time, token)] across the whole assembled master."""
    edl = json.load(open(EDL))
    out = []
    for b in edl["batches"]:
        tr = json.load(open(f"clarity/transcripts/batch-{b['batch']:02d}.json"))
        trim0 = b["src_trim"][0]
        for seg in tr["segs"]:
            for st, en, w in seg["w"]:
                toks = norm(w)
                if toks:
                    out.append((b["start"] + (st - trim0), toks[0]))
    return out

def scenes():
    src = open(PACK).read()
    pat = (r"\[ (\d+)/180 \]\s+(\S+)\n\s+scene (\S+)\s+·\s+(\S+) pass\s+·\s+seed group (\S+)"
           r"\n\s+cue (\d+):(\d+)\s+·\s+VO: (.*?)\n\s+aspect (\S+)\s+·\s+SAVE AS (\S+)")
    sc = {}
    for idx, name, s, ps, sg, mm, ss, vo, asp, save in re.findall(pat, src):
        e = sc.setdefault(s, dict(scene=s, cue=int(mm) * 60 + int(ss), vo=vo.strip(),
                                  aspect=asp, plates={}))
        e["plates"][ps] = save
    return [sc[k] for k in sorted(sc, key=lambda x: (sc[x]["cue"], x))]

def locate(anchor_toks, words, toks, index, floor=0):
    """Best (score, abs_time, pos) at or after `floor`.

    Scenes run in order, so the search is forward-only. Several anchor lines
    recur verbatim -- "Read, in the name of your Lord who created" opens the
    film and closes it -- and without the floor the closing scene matches the
    opening occurrence 31 minutes early.
    """
    n = len(anchor_toks)
    if not n: return 0.0, None, floor
    cands = set()
    for t in anchor_toks:                       # every token is a candidate anchor,
        for p in index.get(t, ()):              # so transliteration misses don't sink it
            if p >= floor:
                cands.add(max(floor, p - n))
    best = (0.0, None, floor)
    for c in sorted(cands):
        for off in (0, n // 2):
            st = c + off
            win = toks[st:st + n + 2]
            if not win: continue
            r = difflib.SequenceMatcher(None, anchor_toks, win).ratio()
            if r > best[0]:
                best = (r, words[st][0], st)
    return best

def main():
    words = master_words()
    index = defaultdict(list)
    for i, (_, w) in enumerate(words):
        index[w].append(i)
    toks = [w for _, w in words]
    rows, floor = [], 0
    for s in scenes():
        a = norm(s["vo"])
        # Allow a short backward reach: a few scenes are cued in the opposite
        # order to the sentence they anchor to (S019/S020 -- the VO says
        # "collected into one written volume ... after a battle at Yamama",
        # the pack cues Yamama first). Slack lets those be found and flagged
        # instead of failing, while staying far too small to reach a repeat of
        # a line minutes away.
        SLACK = 60
        score, t, pos = locate(a, words, toks, index, max(0, floor - SLACK))
        if score >= 0.60:                # only a confident match advances the floor
            floor = max(floor, pos)
        rows.append(dict(scene=s["scene"], pack_cue=s["cue"], real_cue=t,
                         score=round(score, 3), vo=s["vo"], plates=s["plates"],
                         drift=None if t is None else round(t - s["cue"], 2)))
    # Placement confidence: what share of an anchor's distinctive words actually
    # appear around the matched time. Sequence ratio alone punishes short anchors
    # ("Open a mushaf") that are correctly placed, so recall is what decides
    # whether a scene is placeable at all.
    STOP = set("a an the and or of to in is was be it that this for on at as with "
               "by not no".split())
    for r in rows:
        t = r["real_cue"]
        if t is None:
            r["recall"] = 0.0
            continue
        ctx = {w for tt, w in words if t - 4 <= tt <= t + 10}
        a = [x for x in norm(r["vo"]) if x not in STOP]
        r["recall"] = round(sum(1 for x in a if x in ctx) / len(a), 3) if a else 0.0

    # A scene whose anchor line is absent from the recording has no measurable
    # cue. Interpolate one from its neighbours so the plate still has somewhere
    # to sit, and mark it so it is never mistaken for a measurement.
    UNPLACEABLE = 0.20
    for i, r in enumerate(rows):
        if r["recall"] >= UNPLACEABLE: continue
        prev = next((x for x in reversed(rows[:i]) if x["recall"] >= UNPLACEABLE), None)
        nxt = next((x for x in rows[i + 1:] if x["recall"] >= UNPLACEABLE), None)
        if prev and nxt and nxt["pack_cue"] != prev["pack_cue"]:
            f = (r["pack_cue"] - prev["pack_cue"]) / (nxt["pack_cue"] - prev["pack_cue"])
            r["real_cue"] = round(prev["real_cue"] + f * (nxt["real_cue"] - prev["real_cue"]), 2)
            r["drift"] = round(r["real_cue"] - r["pack_cue"], 2)
            r["interpolated"] = True

    # A scene cued before another it actually follows in the audio is an
    # ordering fault in the pack, not a matching failure -- flag it from the
    # final sequence rather than mid-search.
    prev = None
    for r in rows:
        r["out_of_order"] = bool(prev is not None and r["real_cue"] is not None
                                 and r["real_cue"] < prev)
        if r["real_cue"] is not None:
            prev = r["real_cue"]
    json.dump(rows, open("clarity/master/cuesheet.json", "w"), indent=1)
    return rows

if __name__ == "__main__":
    rows = main()
    bad = [r for r in rows if r["score"] < 0.75]
    print(f"{len(rows)} scenes located; {len(bad)} below 0.75 confidence")
    for r in rows[:6] + rows[-4:]:
        rc = "—" if r["real_cue"] is None else f"{int(r['real_cue']//60)}:{r['real_cue']%60:05.2f}"
        print(f"  {r['scene']}  pack {r['pack_cue']//60}:{r['pack_cue']%60:02d} -> real {rc}  "
              f"drift {r['drift']:+.1f}s  conf {r['score']:.2f}")
    if bad: print("low confidence:", [b["scene"] for b in bad])
