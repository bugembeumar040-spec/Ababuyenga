"""Snap each card to the line it names instead of a rigid 30-second clock.

A card every 30s by the clock lands wherever the narration happens to be — the
audit found drift up to 18s. The cadence is still roughly 30s, but each card is
now anchored to the words it glosses and pre-rolled so its animation finishes as
those words are spoken.
"""
import bisect, json, os, re, sys, unicodedata

PREROLL = 1.0      # card starts this early so the text is up as the line lands
MIN_GAP = 8.0      # cards run 6s; keep them from stacking
WINDOW = 45        # only look this far from the card's nominal mark

def norm(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return [t for t in re.split(r"[^a-z0-9']+", s.lower().replace('’', "'")) if t]

tl = json.load(open('tumaninah/timing/timeline.json'))
W = tl['words']
A = [norm(w['w'])[0] if norm(w['w']) else '' for w in W]
T = [w['t'] for w in W]
STOP = set("the a an and of to in it is are was that this be by for on as not you your no non".split())

cards = json.load(open('tumaninah/cards-src/cards.json'))
for c in cards:
    m = (int(c['n']) - 1) * 30      # the nominal 30s grid, independent of any previous snap
    c['mark'] = m
    want = [t for t in norm(c['head'] + ' ' + c['sub']) if t not in STOP]
    lo, hi = bisect.bisect_left(T, m - WINDOW), bisect.bisect_left(T, m + WINDOW)
    best, bp = 0.0, None
    for p in range(lo, max(lo + 1, hi)):
        win = set(A[p:p + 22])
        sc = sum(1 for t in want if t in win) / max(len(want), 1)
        if sc > best:
            best, bp = sc, p
    c['line_at'] = T[bp] if bp is not None and best >= 0.3 else None
    c['score'] = round(best, 2)

# Cards whose line could not be located keep their spacing between neighbours.
known = [i for i, c in enumerate(cards) if c['line_at'] is not None]
for i, c in enumerate(cards):
    if c['line_at'] is None:
        prev = max([k for k in known if k < i], default=None)
        nxt = min([k for k in known if k > i], default=None)
        a = cards[prev]['line_at'] if prev is not None else 0.0
        b = cards[nxt]['line_at'] if nxt is not None else tl['total']
        lo_i = prev if prev is not None else -1
        hi_i = nxt if nxt is not None else len(cards)
        c['line_at'] = a + (b - a) * (i - lo_i) / (hi_i - lo_i)

# Pre-roll must not push a card back onto the previous frame: a card that names
# the cave should not fade up while the silt glass is still on screen.
shots = json.load(open('tumaninah/timing/placed.json'))
def shot_in(t):
    for r in shots:
        if r['in_s'] <= t < r['out_s']:
            return r['in_s']
    return 0.0

t = 0.0
for i, c in enumerate(cards):
    want = max(0.0, c['line_at'] - PREROLL, shot_in(c['line_at']))
    t = want if i == 0 else max(want, t + MIN_GAP)
    c['t_s'] = round(t, 2)
    c['t'] = '%d:%02d' % (int(t) // 60, int(t) % 60)

moved = [c for c in cards if abs(c['t_s'] - c['mark']) > 3]
print('%-4s %6s %8s %8s  %s' % ('card', 'was', 'now', 'moved', 'head'))
for c in cards:
    print('%-4s %6d %8.2f %+8.1f  %s' % (c['n'], c['mark'], c['t_s'], c['t_s'] - c['mark'], c['head'][:40]))
gaps = [cards[i + 1]['t_s'] - cards[i]['t_s'] for i in range(len(cards) - 1)]
print('\nmoved >3s: %d of %d | cadence min %.0fs median %.0fs max %.0fs'
      % (len(moved), len(cards), min(gaps), sorted(gaps)[len(gaps) // 2], max(gaps)))

if '--write' in sys.argv:
    for c in cards:
        for k in ('mark', 'line_at', 'score'):
            c.pop(k, None)
    json.dump(cards, open('tumaninah/cards-src/cards.json', 'w'), ensure_ascii=False, indent=0)
    print('written')
