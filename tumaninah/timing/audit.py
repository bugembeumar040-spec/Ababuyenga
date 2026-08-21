"""Check the script against the audio that actually exists, and time it."""
import json, re, unicodedata

def norm(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return [t for t in re.split(r"[^a-z0-9']+", s.lower().replace('’', "'")) if t]

asr = json.load(open('tumaninah/timing/asr.json'))
A = [norm(w['w'])[0] if norm(w['w']) else '' for w in asr['words']]
T = [w['t'] for w in asr['words']]
TK = [w['take'] for w in asr['words']]
beats = [b for b in json.load(open('tumaninah/timing/beats.json')) if b['kind'] == 'vo']

STOP = set("the a an and of to in it is are was that this be by for on as not you your".split())

def best(want, lo):
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

cur, rows = 0, []
for b in beats:
    sc, p = best(norm(b['text']), max(0, cur - 30))
    if p is not None and sc >= 0.5:
        cur = max(cur, p)
    rows.append({'sec': b['sec'], 'text': b['text'], 'score': sc,
                 'pos': p, 't': T[p] if p is not None else None,
                 'take': TK[p] if p is not None else None, 'words': b['words']})
json.dump(rows, open('tumaninah/timing/audit.json', 'w'), ensure_ascii=False, indent=1)

print('%-32s %5s %8s %8s %-9s %s' % ('SECTION', 'beats', 'start', 'end', 'takes', 'weak'))
secs = []
for r in rows:
    if not secs or secs[-1]['sec'] != r['sec']:
        secs.append({'sec': r['sec'], 'rows': []})
    secs[-1]['rows'].append(r)
for s in secs:
    ok = [r for r in s['rows'] if r['score'] >= 0.5]
    weak = len(s['rows']) - len(ok)
    tks = sorted({r['take'] for r in ok})
    st = min((r['t'] for r in ok), default=None)
    en = max((r['t'] for r in ok), default=None)
    f = lambda x: '%d:%05.2f' % (x // 60, x % 60) if x is not None else '—'
    print('%-32s %5d %8s %8s %-9s %s' % (s['sec'][:32], len(s['rows']), f(st), f(en),
          ','.join(map(str, tks)), ('%d MISSING' % weak) if weak else ''))
miss = [r for r in rows if r['score'] < 0.5]
print('\nnot found in audio: %d of %d beats' % (len(miss), len(rows)))
for r in miss[:14]:
    print('   %.2f  [%s]  %s' % (r['score'], (r['sec'] or '')[:22], r['text'][:70]))
