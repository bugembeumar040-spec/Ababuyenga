"""Place the 116 scene images on the real 21:04 timeline.

Two things the naive approach gets wrong, both handled here:

1. The transcript's AUDIO boundaries are unusable as stated — taken literally they
   imply 452 wpm in audio 4 and 39 wpm in audio 3. Position therefore comes from
   the text: each scene's VO line is located in the transcript and its word offset
   is scaled across the measured runtime.

2. The script was reordered between the prompt pack and this cut — the ḥadīth
   beat (pack ch.4) now runs before "what we are walking toward" (pack ch.3). So
   scenes are matched independently and then sorted by where they actually land,
   rather than being forced to keep the pack's sequence.
"""
import json, os, re, unicodedata, sys

TOTAL = float(sys.argv[1]) if len(sys.argv) > 1 else 1264.0
# Audio 13 (79 s) has no scripted dialogue, so narration is laid out across the
# 1185 s that precede it and the closing frame simply holds through the tail.
CONTENT_END = float(sys.argv[2]) if len(sys.argv) > 2 else 1185.0
MIN_SHOT = 1.5
MATCH_FLOOR = 0.55          # below this, the line is not in this cut

def norm(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace('’', "'")
    return [t for t in re.split(r"[^a-z0-9']+", s) if t]

beats = json.load(open('tumaninah/timing/beats.json'))
toks, owner = [], []
for bi, b in enumerate(beats):
    if b['kind'] == 'arabic':
        continue
    for t in norm(b['text']):
        toks.append(t); owner.append(bi)
N = len(toks)

STOP = set("the a an and of to in it is are was that this be by for on as not you your".split())

def score(pos, want):
    w = [t for t in want if t not in STOP] or want
    win = set(toks[pos:pos + max(len(want) + 6, 12)])
    return sum(1 for t in w if t in win) / len(w)

scenes = json.load(open('tumaninah/manifest.json'))['requests']

# The manifest records the name each frame was requested under (.png); what
# actually landed on disk is .jpg, so resolve by the index prefix instead.
on_disk = {int(f.split('_')[0]): f for f in os.listdir('tumaninah/images')}

rows = []
for order, s in enumerate(scenes):
    want = norm(s['vo'])
    best, bp = 0.0, None
    for p in range(N):
        v = score(p, want)
        if v > best:
            best, bp = v, p
            if best == 1.0:
                break
    rows.append({'scene': s['scene'], 'index': s['index'], 'file': on_disk.get(s['index'], s['file']),
                 'chapter': s['chapter'], 'chapter_title': s['chapter_title'],
                 'vo': s['vo'], 'pack_order': order,
                 'word': bp, 'score': round(best, 2),
                 'beat': owner[bp] if bp is not None else None,
                 'in_cut': best >= MATCH_FLOOR})

# A B-split shares its parent's VO, so it matches the same word. Nudge it after
# the parent so the pair reads as two shots on one line rather than a tie.
by_scene = {r['scene']: r for r in rows}
for r in rows:
    if r['scene'].endswith('B'):
        p = by_scene.get(r['scene'][:-1])
        if p and p['word'] is not None and r['word'] == p['word']:
            r['word'] = p['word'] + 0.5

# Lines cut from the script have no anchor: hold them beside their neighbour so
# they stay available as B-roll rather than vanishing from the list.
last = 0.0
for r in rows:
    if r['word'] is None or not r['in_cut']:
        r['word'] = last + 0.25
    last = r['word']

rows.sort(key=lambda r: (r['word'], r['pack_order']))

for i, r in enumerate(rows):
    r['cut_order'] = i + 1
    r['in_s'] = r['word'] / N * CONTENT_END
for i, r in enumerate(rows):
    r['out_s'] = rows[i + 1]['in_s'] if i + 1 < len(rows) else TOTAL

# No shot shorter than MIN_SHOT; steal from the following shot, never the past.
for i in range(len(rows) - 1):
    if rows[i + 1]['in_s'] - rows[i]['in_s'] < MIN_SHOT:
        rows[i + 1]['in_s'] = rows[i]['in_s'] + MIN_SHOT
for i, r in enumerate(rows):
    r['out_s'] = rows[i + 1]['in_s'] if i + 1 < len(rows) else max(TOTAL, r['in_s'] + MIN_SHOT)
    for k in ('in_s', 'out_s', 'word'):
        r[k] = round(r[k], 2)
    r['dur_s'] = round(r['out_s'] - r['in_s'], 2)

json.dump(rows, open('tumaninah/timing/placed.json', 'w'), ensure_ascii=False, indent=1)

out = [r for r in rows if not r['in_cut']]
moved = [r for r in rows if abs(r['cut_order'] - 1 - r['pack_order']) > 3]
d = [r['dur_s'] for r in rows]
print('placed %d   runtime %.1fs (%d:%02d)' % (len(rows), rows[-1]['out_s'],
                                               rows[-1]['out_s'] // 60, rows[-1]['out_s'] % 60))
print('shot len  min %.1fs  median %.1fs  max %.1fs  mean %.1fs'
      % (min(d), sorted(d)[len(d)//2], max(d), sum(d)/len(d)))
print('\nno matching narration in this cut (%d):' % len(out))
for r in out:
    print('   %-4s %.2f  %s' % (r['scene'], r['score'], r['vo'][:62]))
print('\nmoved >3 slots from pack order: %d' % len(moved))
