"""Build the cut: audio from the takes that belong to this script, image timing
taken from where the words are actually spoken.

Three things this handles that an estimate cannot:

- The uploads hold two scripts. Only the takes classify.py scores as this one are
  used, ordered by where they sit in the script.
- Roughly 3:50 of script was never recorded. Frames whose line falls in those
  stretches are held OUT of the cut rather than squeezed in — squeezing gave 37
  frames a 1.5s flash each, piled past the end of the audio.
- Slated section headings read aloud are trimmed, and every downstream timestamp
  shifts with them.
"""
import json, os, re, subprocess, sys, unicodedata

UPLOADS = '/root/.claude/uploads/b6b8a957-a047-5e7c-b664-115ea9a25bf7'
MIN_SHOT = 1.5

def norm(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return [t for t in re.split(r"[^a-z0-9']+", s.lower().replace('’', "'")) if t]

allasr = json.load(open('tumaninah/timing/asr_all.json'))
spans = sorted(json.load(open('tumaninah/timing/coverage.json'))['spans'], key=lambda s: s['lo'])
cuts = json.load(open('tumaninah/timing/cuts.json'))

# One word stream for the assembled audio, each take at its true offset.
raw, offset, order = [], 0.0, []
for s in spans:
    for w in allasr[s['file']]['words']:
        raw.append({'t': round(offset + w['t'], 2), 'w': w['w']})
    order.append({'file': s['file'], 'offset': round(offset, 2), 'dur': s['dur']})
    offset += s['dur']

# Apply the trims: drop what falls inside a cut, pull everything after it back.
def shift(t):
    d = 0.0
    for c in cuts:
        if t >= c['to']:
            d += c['to'] - c['from']
    return round(t - d, 2)

inside = lambda t: any(c['from'] <= t < c['to'] for c in cuts)
stream = [{'t': shift(w['t']), 'w': w['w']} for w in raw if not inside(w['t'])]
TOTAL = offset - sum(c['to'] - c['from'] for c in cuts)

A = [norm(w['w'])[0] if norm(w['w']) else '' for w in stream]
T = [w['t'] for w in stream]
json.dump({'total': TOTAL, 'order': order, 'cuts': cuts, 'words': stream},
          open('tumaninah/timing/timeline.json', 'w'), ensure_ascii=False)

STOP = set("the a an and of to in it is are was that this be by for on as not you your".split())

def find(want):
    w = [t for t in want if t not in STOP] or want
    bs, bp = 0.0, None
    for p in range(len(A)):
        win = set(A[p:p + max(len(want) + 8, 14)])
        sc = sum(1 for t in w if t in win) / len(w)
        if sc > bs:
            bs, bp = sc, p
            if bs == 1.0:
                break
    return bs, bp

scenes = json.load(open('tumaninah/manifest.json'))['requests']
on_disk = {int(f.split('_')[0]): f for f in os.listdir('tumaninah/images')}

cut, held = [], []
for i, s in enumerate(scenes):
    sc, p = find(norm(s['vo']))
    rec = {'pack_order': i, 'scene': s['scene'], 'index': s['index'],
           'file': on_disk.get(s['index'], s['file']),
           'chapter': s['chapter'], 'chapter_title': s['chapter_title'],
           'vo': s['vo'], 'score': round(sc, 2), 'has_audio': sc >= 0.55}
    if rec['has_audio']:
        rec['in_s'] = T[p]
        cut.append(rec)
    else:
        held.append(rec)

# B-splits share their parent's line, so they match the same word.
by = {r['scene']: r for r in cut}
for r in cut:
    if r['scene'].endswith('B'):
        par = by.get(r['scene'][:-1])
        if par and r['in_s'] == par['in_s']:
            r['in_s'] = par['in_s'] + 0.01

# Sorted by where the words land, not by the pack: the script was resequenced.
cut.sort(key=lambda r: (r['in_s'], r['pack_order']))
for i in range(len(cut) - 1):
    if cut[i + 1]['in_s'] - cut[i]['in_s'] < MIN_SHOT:
        cut[i + 1]['in_s'] = cut[i]['in_s'] + MIN_SHOT
for i, r in enumerate(cut):
    r['cut_order'] = i + 1
    r['out_s'] = cut[i + 1]['in_s'] if i + 1 < len(cut) else TOTAL
    r['in_s'], r['out_s'] = round(r['in_s'], 2), round(r['out_s'], 2)
    r['dur_s'] = round(r['out_s'] - r['in_s'], 2)

json.dump(cut, open('tumaninah/timing/placed.json', 'w'), ensure_ascii=False, indent=1)
json.dump(held, open('tumaninah/timing/held.json', 'w'), ensure_ascii=False, indent=1)

d = [r['dur_s'] for r in cut]
print('audio %.1fs = %d:%02d from %d takes, %d trim(s) removing %.1fs'
      % (TOTAL, TOTAL // 60, TOTAL % 60, len(order), len(cuts),
         sum(c['to'] - c['from'] for c in cuts)))
print('in the cut %d frames | held out (no recorded line) %d' % (len(cut), len(held)))
print('shot len min %.1f median %.1f max %.1f' % (min(d), sorted(d)[len(d) // 2], max(d)))
print('30s marks: %d (0:00 .. %d:%02d)' % (int(TOTAL // 30) + 1,
      (int(TOTAL // 30) * 30) // 60, (int(TOTAL // 30) * 30) % 60))

if '--audio' in sys.argv:
    FF = subprocess.run(['python3', '-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],
                        capture_output=True, text=True).stdout.strip()
    os.makedirs('tumaninah/preview', exist_ok=True)
    lst = 'tumaninah/preview/audio.txt'
    open(lst, 'w').write('\n'.join("file '%s'" % os.path.join(UPLOADS, o['file']) for o in order))
    keep = 'aselect=' + '*'.join("'not(between(t,%.3f,%.3f))'" % (c['from'], c['to']) for c in cuts) \
        + ',asetpts=N/SR/TB' if cuts else 'anull'
    subprocess.run([FF, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-af', keep, '-c:a', 'aac', '-b:a', '160k',
                    'tumaninah/preview/voiceover.m4a'], check=True)
    print('built voiceover.m4a')
