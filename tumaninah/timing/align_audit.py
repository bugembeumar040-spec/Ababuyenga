"""Check every shot against the words spoken while it is on screen."""
import bisect, json, re, unicodedata

def norm(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return [t for t in re.split(r"[^a-z0-9']+", s.lower().replace('’', "'")) if t]

STOP = set("the a an and of to in it is are was that this be by for on as not you your".split())
tl = json.load(open('tumaninah/timing/timeline.json'))
W = tl['words']; T = [w['t'] for w in W]
rows = json.load(open('tumaninah/timing/placed.json'))

out = []
for r in rows:
    i, j = bisect.bisect_left(T, r['in_s']), bisect.bisect_left(T, r['out_s'])
    spoken = set(norm(' '.join(w['w'] for w in W[i:j])))
    want = [t for t in norm(r['vo']) if t not in STOP] or norm(r['vo'])
    hit = sum(1 for t in want if t in spoken) / len(want)
    # where the line really is, to measure lead/lag
    best, bp = 0.0, None
    A = [norm(w['w'])[0] if norm(w['w']) else '' for w in W]
    out.append({'scene': r['scene'], 'in': r['in_s'], 'out': r['out_s'], 'dur': r['dur_s'],
                'on_screen_hit': round(hit, 2), 'vo': r['vo'], 'file': r['file']})

good = [o for o in out if o['on_screen_hit'] >= 0.6]
mid = [o for o in out if 0.3 <= o['on_screen_hit'] < 0.6]
bad = [o for o in out if o['on_screen_hit'] < 0.3]
print('shots %d | line fully on screen %d | partial %d | line NOT in window %d'
      % (len(out), len(good), len(mid), len(bad)))
print('\nline not spoken while the frame is up:')
for o in sorted(bad, key=lambda x: x['in']):
    print('  %-5s %7.1f (%4.1fs) %.2f  %s' % (o['scene'], o['in'], o['dur'],
          o['on_screen_hit'], o['vo'][:62]))
json.dump(out, open('tumaninah/timing/align_audit.json', 'w'), ensure_ascii=False, indent=1)
