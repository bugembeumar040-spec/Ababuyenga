"""Sort the uploads by which script they belong to, and put them in script order."""
import json, re, unicodedata

def norm(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return [t for t in re.split(r"[^a-z0-9']+", s.lower().replace('’', "'")) if t]

beats = [b for b in json.load(open('tumaninah/timing/beats.json')) if b['kind'] == 'vo']
S, owner = [], []
for i, b in enumerate(beats):
    for t in norm(b['text']):
        S.append(t); owner.append(i)

def grams(toks, n=4):
    return {' '.join(toks[i:i + n]) for i in range(len(toks) - n + 1)}

SG = grams(S)
pos_of = {}
for i in range(len(S) - 3):
    pos_of.setdefault(' '.join(S[i:i + 4]), i)

allasr = json.load(open('tumaninah/timing/asr_all.json'))
rows = []
for f, d in allasr.items():
    toks = norm(d['text'])
    g = grams(toks)
    hit = g & SG
    cov = len(hit) / max(len(g), 1)
    ps = sorted(pos_of[x] for x in hit)
    rows.append({'file': f, 'dur': d['dur'], 'cov': cov, 'hits': len(hit),
                 'start': ps[len(ps) // 20] if ps else None,
                 'median': ps[len(ps) // 2] if ps else None,
                 'sec': beats[owner[ps[len(ps) // 2]]]['sec'] if ps else None})

rows.sort(key=lambda r: -r['cov'])
print('%-26s %7s %6s %6s %8s  %s' % ('file', 'dur', 'cov', 'hits', 'wordpos', 'section'))
for r in rows:
    print('%-26s %7.1f %5.0f%% %6d %8s  %s' % (r['file'][:26], r['dur'], r['cov'] * 100,
          r['hits'], r['start'], (r['sec'] or '—')[:34]))
json.dump(rows, open('tumaninah/timing/classify.json', 'w'), ensure_ascii=False, indent=1)
