#!/usr/bin/env python3
"""
Force-align the shot pack's VO lines against the recorded voiceover.

Why this exists. The first cut scaled the pack's planned timeline onto the real
VO duration by a single ratio and then snapped each boundary to the nearest
pause. That is only correct if the recording compressed evenly, and it did not:
group 1 came in at 107.00s against a planned 107s, a ratio of 1.0, while the
film overall came in 9% short. Every shot in that stretch was therefore pulled
early against audio that had not compressed at all, and the captions drifted off
their lines.

A pause is not evidence that a particular line ended. The words are. So this
transcribes the VO with word timestamps, aligns that transcript to the script
text we already have, and reports when each shot's line is actually spoken.

Writes media/vo-align.json. Run tools/build-beats.py afterwards.

Usage:  python3 tools/align-vo.py [--asr]      (--asr re-runs transcription)
"""
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT.parent / "jinn-shot-pack-final.txt"
WORDS = ROOT / "media" / "vo-words.json"
OUT = ROOT / "media" / "vo-align.json"
AUDIO = ROOT / "public" / "jinn-vo.mp3"

SHOT_RE = re.compile(r"^(S\d+[a-z]?) · \d+:\d+[–-]\d+:\d+\s*$")
VO_RE = re.compile(r"^VO(>|\s) ?(.*)$")


def transcribe() -> list[dict]:
    from faster_whisper import WhisperModel

    model = WhisperModel("base.en", device="cpu", compute_type="int8", cpu_threads=4)
    segments, _ = model.transcribe(str(AUDIO), word_timestamps=True, vad_filter=False)
    words = [
        {"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)}
        for seg in segments
        for w in (seg.words or [])
    ]
    WORDS.write_text(json.dumps(words))
    return words


def parse_pack() -> list[tuple[str, list[str]]]:
    """[(shot id, [spoken word, ...])] in cut order."""
    lines = PACK.read_text(encoding="utf-8").splitlines()
    shots, i = [], 0
    while i < len(lines):
        m = SHOT_RE.match(lines[i])
        if not m:
            i += 1
            continue
        text = []
        j = i + 1
        while j < len(lines) and not lines[j].startswith("PROMPT"):
            vm = VO_RE.match(lines[j])
            if vm:
                chunk = vm.group(2)
                k = j + 1
                while k < len(lines) and lines[k].startswith("      "):
                    chunk += " " + lines[k].strip()
                    k += 1
                # Drop stage directions and editing notes — never spoken.
                chunk = re.sub(r"\[[^\]]*\]", " ", chunk)
                chunk = re.sub(r"<-.*", " ", chunk)
                text.append(chunk)
            j += 1
        shots.append((m.group(1), tokens(" ".join(text))))
        i = j
    return shots


def tokens(text: str) -> list[str]:
    """Spoken-form tokens. Numbers in the script are read aloud as words, and
    the transcript writes them as digits, so both sides are normalised hard."""
    text = text.lower().replace("’", "'").replace("—", " ").replace("-", " ")
    return [t for t in re.findall(r"[a-z']+", text) if t]


def main() -> None:
    words = (
        transcribe()
        if "--asr" in sys.argv or not WORDS.exists()
        else json.loads(WORDS.read_text())
    )
    heard = [tokens(w["w"])[0] if tokens(w["w"]) else "" for w in words]

    shots = parse_pack()
    script, owner = [], []
    for sid, toks in shots:
        for t in toks:
            script.append(t)
            owner.append(sid)

    # Locate each shot's line independently, against the whole transcript.
    #
    # Walking the script in pack order and consuming the transcript as we go
    # assumes the recording follows the pack. It does not: S29 and S29b are
    # spoken in the opposite order, and eight other shots are not spoken at all
    # (the pack's own CUT 1 and CUT 2, applied at record time). Either
    # assumption alone puts every later caption under the wrong line.
    #
    # So each shot is matched on its own, and the cut order that comes out is
    # the order the recording actually says them in. The VO is the spine.
    def locate(toks: list[str]):
        sm = SequenceMatcher(a=toks, b=heard, autojunk=False)
        # Runs of 3+ consecutive words are specific enough to be this line and
        # not a stock phrase reused elsewhere in the script.
        blocks = [b for b in sm.get_matching_blocks() if b.size >= 3]
        if not blocks:
            return None
        hit = sum(b.size for b in blocks) / len(toks)
        s = words[blocks[0].b]["s"]
        e = words[blocks[-1].b + blocks[-1].size - 1]["e"]
        return {"start": round(s, 3), "end": round(e, 3), "hit": round(hit, 2)}

    wps = len(words) / words[-1]["e"]          # speaking rate of this recording
    spoken, dropped, matched = {}, [], 0
    for sid, toks in shots:
        needed = len(toks) / wps if toks else 0.0
        loc = locate(toks) if toks else None
        # A real match sits inside a span roughly the length of the line. A
        # scatter of common words across the whole film does not.
        if loc and loc["hit"] >= 0.4 and (loc["end"] - loc["start"]) <= needed * 2.5:
            spoken[sid] = loc
            matched += round(loc["hit"] * len(toks))
        else:
            dropped.append((sid, round(needed, 1), loc))

    # Cut order follows the recording, not the pack.
    spoken = dict(sorted(spoken.items(), key=lambda kv: kv[1]["start"]))

    # A shot's trailing match can reach into the next line when the two share
    # wording — S30 and S30b both close on "made from". Clamp each window at
    # the next one's start so no line claims words another shot is captioned
    # with; build-beats.py asserts on exactly this.
    ids = list(spoken)
    for a, b in zip(ids, ids[1:]):
        if spoken[a]["end"] > spoken[b]["start"]:
            spoken[a]["end"] = round(spoken[b]["start"] - 0.05, 3)
            spoken[a]["clamped"] = True
    drop_ids = [d[0] for d in dropped]
    pack_order = [s for s, _ in shots if s in spoken]
    moved = [s for s, v in zip(pack_order, spoken) if s != v]

    OUT.write_text(
        json.dumps(
            {
                "_note": "Where each shot's line is actually spoken in "
                "public/jinn-vo.mp3, in seconds, force-aligned from a "
                "word-timestamped transcript against the shot pack's VO lines. "
                "'dropped' are shots the recording does not contain at all — the "
                "VO was recorded from a shorter script than the pack (see the "
                "pack's CUT 1 / CUT 2). build-beats.py builds the cut from this "
                "file and never from the pack's planned timings.",
                "coverage": f"{len(spoken)}/{len(shots)} shots spoken",
                "order": "cut order is the order of this file — the recording's order, not the pack's",
                "reordered_vs_pack": sorted(set(moved)),
                "asr_words": len(words),
                "matched_words": matched,
                "dropped": drop_ids,
                "spoken": spoken,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"{matched}/{len(script)} script words matched in the transcript")
    if moved:
        print(f"spoken out of pack order: {', '.join(sorted(set(moved)))}")
    print(f"{len(spoken)}/{len(shots)} shots are spoken in the recording")
    if dropped:
        print(f"NOT IN THE VO ({len(dropped)}):")
        for sid, needed, loc in dropped:
            why = "no matching run of words" if not loc else (
                f"best match only {loc['hit']:.0%} and spread over "
                f"{loc['end'] - loc['start']:.0f}s for a ~{needed}s line")
            print(f"  {sid:5} {why}")
        print("  These have no line to sit under. build-beats.py drops them from")
        print("  the cut; their plates stay in public/plates/ for a fuller recut.")


if __name__ == "__main__":
    main()
