"""Map each Tumaninah take onto the script, and report what is and is not recorded."""
import bisect, json, re, unicodedata

def norm(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return [t for t in re.split(r"[^a-z0-9']+", s.lower().replace('’', "'")) if t]

beats = [b for b in json.load(open('tumaninah/timing/beats.json')) if b['kind'] == 'vo']
S, owner = [], []
for i, b in enumerate(beats):
    for t in norm(b['text']):
        S.append(t); owner.append(i)
N = len(S)
idx = {}
for i in range(N - 3):
    idx.setdefault(' '.join(S[i:i + 4]), []).append(i)

allasr = json.load(open('tumaninah/timing/asr_all.json'))
cls = {r['file']: r for r in json.load(open('tumaninah/timing/classify.json'))}
mine = [f for f, r in cls.items() if r['cov'] >= 0.5]

spans = []
for f in mine:
    toks = norm(allasr[f]['text'])
    hits = []
    for i in range(len(toks) - 3):
        for p in idx.get(' '.join(toks[i:i + 4]), []):
            hits.append(p)
    hits.sort()
    if not hits:
        continue
    # Stray 4-grams land all over the script, so percentiles smear the span.
    # Take the window the length of this take that actually contains the hits.
    L = len(toks)
    best, lo = -1, hits[0]
    for c in hits:
        k = bisect.bisect_right(hits, c + L) - bisect.bisect_left(hits, c)
        if k > best:
            best, lo = k, c
    hi = min(lo + L, N - 1)
    spans.append({'file': f, 'dur': allasr[f]['dur'], 'lo': lo, 'hi': hi,
                  'n': best, 'stray': len(hits) - best})
spans.sort(key=lambda s: s['lo'])

cov = [False] * N
print('%-26s %7s %6s %6s %5s  %s' % ('file', 'dur', 'from', 'to', 'hits', 'section at start'))
tot = 0.0
for s in spans:
    for p in range(s['lo'], s['hi'] + 1):
        cov[p] = True
    tot += s['dur']
    print('%-26s %7.1f %6d %6d %5d  %s' % (s['file'][:26], s['dur'], s['lo'], s['hi'],
          s['n'], (beats[owner[s['lo']]]['sec'] or '')[:38]))
print('\n%d takes, %.1fs = %d:%02d of audio' % (len(spans), tot, tot // 60, tot % 60))

# gaps in script coverage
gaps, i = [], 0
while i < N:
    if not cov[i]:
        j = i
        while j < N and not cov[j]:
            j += 1
        if j - i >= 25:
            gaps.append((i, j))
        i = j
    else:
        i += 1
print('\nscript words covered: %d of %d (%.0f%%)' % (sum(cov), N, 100 * sum(cov) / N))
print('gaps of 25+ words with no recorded audio:')
for a, b in gaps:
    print('  words %5d-%-5d (%3d)  [%s]  "%s..."' % (a, b, b - a,
          (beats[owner[a]]['sec'] or '')[:26], ' '.join(S[a:a + 11])))
json.dump({'spans': spans, 'gaps': gaps}, open('tumaninah/timing/coverage.json', 'w'))
