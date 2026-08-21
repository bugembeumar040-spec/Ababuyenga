"""Anchor every card to the phrase it names, measured in the audio.

The old anchor was a bag-of-words overlap scored over a sliding window, which
returns where the *window* starts — often many words before the phrase itself.
And every card ran a fixed six seconds whether its phrase took one second to say
or five. Between them that is why cards read early or late all through the cut.

Here each card's headline is matched as an ordered sequence against the
transcript, tolerant of how the recogniser mangles transliteration ("Arad" for
Ar-Raʿd, "Tumanina" for ṭumaʾnīnah). The card then rises just before the first
word of that phrase and holds until after its last.
"""
import bisect, difflib, json, re, sys, unicodedata

LEAD, HOLD = 0.7, 2.2          # up just before the phrase, held just past it
# A card carrying Arabic, a headline and a reference needs time to be read; the
# floor is set by reading, not by the phrase being short.
MIN_DUR, MAX_DUR = 4.5, 8.0
FUZZ = 0.78                    # token similarity that counts as a match

def toks(s):
    """Whitespace tokens with the punctuation stripped inside each token, so
    AR-RAʿD becomes one token 'arrad' rather than three fragments."""
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    out = []
    for w in s.lower().replace('’', "'").split():
        w = re.sub(r"[^a-z0-9]", '', w)
        if w:
            out.append(w)
    return out

STOP = set("the a an and of to in it is are was that this be by for on as not you your no non "
           "its his her their with what when where which who".split())

W = json.load(open('tumaninah/timing/timeline.json'))['words']
A = [toks(w['w'])[0] if toks(w['w']) else '' for w in W]
T = [w['t'] for w in W]

def eq(a, b):
    if a == b:
        return True
    if len(a) < 4 or len(b) < 4:
        return False
    return difflib.SequenceMatcher(None, a, b).ratio() >= FUZZ

def find(phrase, near=None, radius=90):
    """Best ordered match of `phrase` in the stream; returns (score, i0, i1)."""
    p = [t for t in toks(phrase) if t not in STOP]
    if not p:
        return 0.0, None, None
    lo, hi = 0, len(A)
    if near is not None:
        lo = max(0, bisect.bisect_left(T, near - radius))
        hi = min(len(A), bisect.bisect_left(T, near + radius))
    best = (0.0, None, None)
    slack = len(p) + 6
    for s in range(lo, hi):
        j, hits, first, last = s, 0, None, None
        for t in p:
            k = j
            while k < min(len(A), s + slack + len(p)):
                if eq(t, A[k]):
                    hits += 1
                    first = s if first is None else first
                    first = k if first is None else first
                    last = k
                    j = k + 1
                    break
                k += 1
            else:
                continue
        if hits:
            sc = hits / len(p)
            if sc > best[0]:
                first = next((k for k in range(s, min(len(A), s + slack + len(p)))
                              if eq(p[0], A[k])), s)
                best = (sc, first, last)
    return best

cards = json.load(open('tumaninah/cards-src/cards.json'))
rows = json.load(open('tumaninah/timing/placed.json'))
TOTAL = json.load(open('tumaninah/timing/timeline.json'))['total']

print('%-4s %8s %8s %6s %5s  %s' % ('card', 'phrase@', 'card in', 'dur', 'score', 'headline'))
for c in cards:
    if 'anchor_s' in c:
        t0 = t1 = c['anchor_s']; sc = 1.0; src = 'anchor'
    else:
        sc, i0, i1 = find(c['head'], near=c.get('t_s'))
        if sc < 0.6:                     # headline mangled; fall back to the sub line
            sc2, j0, j1 = find(c['sub'], near=c.get('t_s'))
            if sc2 > sc:
                sc, i0, i1 = sc2, j0, j1
                src = 'sub'
            else:
                src = 'head'
        else:
            src = 'head'
        if i0 is None:
            print('%-4s %8s %8s %6s %5.2f  %s   << NO MATCH, left where it was'
                  % (c['n'], '—', '%.2f' % c['t_s'], '%.1f' % c.get('dur_s', 6.0), sc, c['head'][:30]))
            continue
        t0, t1 = T[i0], T[min(i1, len(T) - 1)]
    c['phrase_s'] = round(t0, 2)
    c['phrase_e'] = round(t1, 2)
    c['match'] = round(sc, 2)
    t = max(0.0, t0 - LEAD)
    dur = min(MAX_DUR, max(MIN_DUR, (t1 - t) + HOLD))
    dur = min(dur, TOTAL - t)      # never run past the end of the cut
    c['t_s'] = round(t, 2)
    c['t'] = '%d:%02d' % (int(t) // 60, int(t) % 60)
    c['dur_s'] = round(dur, 2)
    print('%-4s %8.2f %8.2f %6.1f %5.2f  %s%s' % (c['n'], t0, t, dur, sc, c['head'][:30],
          '' if sc >= 0.75 else '   << weak (%s)' % src))

cards.sort(key=lambda c: c['t_s'])
if '--write' in sys.argv:
    json.dump(cards, open('tumaninah/cards-src/cards.json', 'w'), ensure_ascii=False, indent=0)
    print('\nwritten')
