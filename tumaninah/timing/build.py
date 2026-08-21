"""Build the real cut: audio from the takes that belong to this script, and
image timing taken from where the words are actually spoken.

Supersedes the earlier estimate-based path. That one assumed the uploads were all
one script and that the transcript's AUDIO table described them; both were wrong.
Here the takes are the ones ASR says belong to this study, ordered by where they
sit in the script, and every in-point is a measured word timestamp.
"""
import bisect, json, os, re, subprocess, sys, unicodedata

UPLOADS = '/root/.claude/uploads/b6b8a957-a047-5e7c-b664-115ea9a25bf7'
MIN_SHOT = 1.5

def norm(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return [t for t in re.split(r"[^a-z0-9']+", s.lower().replace('’', "'")) if t]

allasr = json.load(open('tumaninah/timing/asr_all.json'))
spans = json.load(open('tumaninah/timing/coverage.json'))['spans']
spans.sort(key=lambda s: s['lo'])

# One word stream for the assembled audio, each take at its true offset.
stream, offset, order = [], 0.0, []
for s in spans:
    for w in allasr[s['file']]['words']:
        stream.append({'t': round(offset + w['t'], 2), 'w': w['w']})
    order.append({'file': s['file'], 'offset': round(offset, 2), 'dur': s['dur'],
                  'script_from': s['lo']})
    offset += s['dur']
TOTAL = offset
A = [norm(w['w'])[0] if norm(w['w']) else '' for w in stream]
T = [w['t'] for w in stream]
json.dump({'total': TOTAL, 'order': order, 'words': stream},
          open('tumaninah/timing/timeline.json', 'w'), ensure_ascii=False)

STOP = set("the a an and of to in it is are was that this be by for on as not you your".split())

def find(want, lo):
    w = [t for t in want if t not in STOP] or want
    bs, bp = 0.0, None
    for p in range(lo, len(A)):
        win = set(A[p:p + max(len(want) + 8, 14)])
        sc = sum(1 for t in w if t in win) / len(w)
        if sc > bs:
            bs, bp = sc, p
            if bs == 1.0:
                break
    return bs, bp

scenes = json.load(open('tumaninah/manifest.json'))['requests']
on_disk = {int(f.split('_')[0]): f for f in os.listdir('tumaninah/images')}

# Matched freely, not monotonically: the script was resequenced after the pack
# was written, so forcing the pack's order pins later frames behind earlier text.
rows = []
for order_i, s in enumerate(scenes):
    sc, p = find(norm(s['vo']), 0)
    ok = p is not None and sc >= 0.55
    rows.append({'pack_order': order_i, 'scene': s['scene'], 'index': s['index'],
                 'file': on_disk.get(s['index'], s['file']),
                 'chapter': s['chapter'], 'chapter_title': s['chapter_title'],
                 'vo': s['vo'], 'score': round(sc, 2),
                 'in_s': T[p] if ok else None, 'has_audio': ok})

# B-splits share their parent's line, so they match the same word; hold the split
# just after its parent instead of tying.
by = {r['scene']: r for r in rows}
for r in rows:
    if r['scene'].endswith('B'):
        par = by.get(r['scene'][:-1])
        if par and par['in_s'] is not None and r['in_s'] == par['in_s']:
            r['in_s'] = par['in_s'] + 0.01
rows.sort(key=lambda r: (r['in_s'] if r['in_s'] is not None else 1e9, r['pack_order']))

# A line with no audio sits in one of the unrecorded gaps. Hold it between its
# neighbours rather than dropping it, so the frame stays in the bin.
known = [i for i, r in enumerate(rows) if r['in_s'] is not None]
for i, r in enumerate(rows):
    if r['in_s'] is not None:
        continue
    prev = max([k for k in known if k < i], default=None)
    nxt = min([k for k in known if k > i], default=None)
    a = rows[prev]['in_s'] if prev is not None else 0.0
    b = rows[nxt]['in_s'] if nxt is not None else TOTAL
    lo = prev if prev is not None else -1
    hi = nxt if nxt is not None else len(rows)
    r['in_s'] = a + (b - a) * (i - lo) / (hi - lo)

run = 0.0
for r in rows:
    run = max(run, r['in_s']); r['in_s'] = run
for i in range(len(rows) - 1):
    if rows[i + 1]['in_s'] - rows[i]['in_s'] < MIN_SHOT:
        rows[i + 1]['in_s'] = rows[i]['in_s'] + MIN_SHOT
for i, r in enumerate(rows):
    r['cut_order'] = i + 1
for i, r in enumerate(rows):
    r['out_s'] = rows[i + 1]['in_s'] if i + 1 < len(rows) else max(TOTAL, r['in_s'] + MIN_SHOT)
    r['in_s'], r['out_s'] = round(r['in_s'], 2), round(r['out_s'], 2)
    r['dur_s'] = round(r['out_s'] - r['in_s'], 2)
json.dump(rows, open('tumaninah/timing/placed.json', 'w'), ensure_ascii=False, indent=1)

nog = [r for r in rows if not r['has_audio']]
d = [r['dur_s'] for r in rows]
print('audio %.1fs = %d:%02d from %d takes' % (TOTAL, TOTAL // 60, TOTAL % 60, len(order)))
print('frames %d | timed to spoken words %d | in unrecorded gaps %d'
      % (len(rows), len(rows) - len(nog), len(nog)))
print('shot len min %.1f median %.1f max %.1f' % (min(d), sorted(d)[len(d)//2], max(d)))
print('30s marks needed: %d (0:00 .. %d:%02d)' % (int(TOTAL // 30) + 1,
      (int(TOTAL // 30) * 30) // 60, (int(TOTAL // 30) * 30) % 60))

if '--audio' in sys.argv:
    FF = subprocess.run(['python3', '-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],
                        capture_output=True, text=True).stdout.strip()
    os.makedirs('tumaninah/preview', exist_ok=True)
    lst = 'tumaninah/preview/audio.txt'
    open(lst, 'w').write('\n'.join("file '%s'" % os.path.join(UPLOADS, o['file']) for o in order))
    subprocess.run([FF, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-c:a', 'aac', '-b:a', '160k', 'tumaninah/preview/voiceover.m4a'], check=True)
    print('built tumaninah/preview/voiceover.m4a')
