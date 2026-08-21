"""Check when each card's HEADLINE subject is actually spoken.

The line-level audit asks whether the card is up while its sentence is read. This
asks a sharper question: the headline names a thing, so when is that thing said?
A title card that leaves before the title is spoken is wrong even if its sentence
was on screen.
"""
import bisect, json, re, unicodedata

def norm(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return [t for t in re.split(r"[^a-z0-9']+", s.lower().replace('’', "'")) if t]

STOP = set("the a an and of to in it is are was that this be by for on as not you your no non a".split())
W = json.load(open('tumaninah/timing/timeline.json'))['words']
A = [norm(w['w'])[0] if norm(w['w']) else '' for w in W]
T = [w['t'] for w in W]
cards = json.load(open('tumaninah/cards-src/cards.json'))

print('%-4s %8s %8s %8s  %s' % ('card', 'start', 'end', 'head at', 'headline'))
bad = []
for c in cards:
    a, b = c['t_s'], c['t_s'] + c['dur_s']
    want = [t for t in norm(c['head']) if t not in STOP]
    if not want:
        continue
    lo = bisect.bisect_left(T, a - 60); hi = bisect.bisect_left(T, b + 60)
    best, bp = 0.0, None
    for p in range(lo, max(lo + 1, hi)):
        win = set(A[p:p + 20])
        sc = sum(1 for t in want if t in win) / len(want)
        if sc > best:
            best, bp = sc, p
    at = T[bp] if bp is not None and best >= 0.5 else None
    off = ''
    if at is not None and not (a <= at <= b):
        off = '   << headline spoken %+.1fs outside the card' % (at - a if at < a else at - b)
        bad.append((c['n'], c['head'], at, a, b))
    print('%-4s %8.2f %8.2f %8s  %s%s' % (c['n'], a, b, ('%.2f' % at) if at else '—', c['head'][:34], off))
print('\n%d of %d cards hold their headline' % (len(cards) - len(bad), len(cards)))
