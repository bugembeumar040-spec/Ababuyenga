"""Keep plates uncontested, and stop cards running into them.

A lower-third carrying across a cut is ordinary editing, so a card is left at its
full length over a picture change. A plate is different: it states an āyah full
frame, and a card competing with it is clutter — doubly so where the two say the
same thing, which is most of these collisions.
"""
import json, sys

MAX, MIN = 6.0, 3.5      # below this a card is a flash, not something you read
TAIL = 1.5      # a line this close to a plate's end belongs to what follows it

cards = json.load(open('tumaninah/cards-src/cards.json'))
rows = json.load(open('tumaninah/timing/placed.json'))
plates = json.load(open('tumaninah/cards-src/plates.json'))
by = {r['scene']: r for r in rows}
pw = sorted((by[p['scene']]['in_s'], by[p['scene']]['out_s'], p['scene'])
            for p in plates if p['scene'] in by)

def frame_out(t):
    for r in rows:
        if r['in_s'] <= t < r['out_s']:
            return r['out_s']
    return t + MAX

def plate_at(t):
    for a, b, sc in pw:
        if a <= t < b:
            return (a, b, sc)
    return None

def next_plate_in(t):
    for a, b, sc in pw:
        if a > t:
            return a
    return None

kept, dropped = [], []
for c in cards:
    t, la = c['t_s'], c.get('line_at', c['t_s'])
    p = plate_at(t)
    if p:
        # A line landing right at the end of a plate is not the plate's beat —
        # the card just needs to wait for it. Only drop when the line sits well
        # inside the plate, where the two really are saying the same thing.
        if la < p[1] - TAIL:
            c['drop'] = 'plate on scene %s states this beat full frame' % p[2]
            dropped.append(c)
            continue
        t = p[1]                      # wait for the plate to finish
    # Crossing a picture cut is fine; running into a plate is not. The length
    # comes from align_cards — it is how long the phrase takes to say — so this
    # only ever shortens it.
    np_ = next_plate_in(t)
    dur = c.get('dur_s', MAX)
    if np_ is not None:
        dur = min(dur, np_ - t)
    if dur < MIN:
        c['drop'] = 'only %.1fs before the next plate takes the frame' % dur
        dropped.append(c)
        continue
    c['t_s'] = round(t, 2)
    c['t'] = '%d:%02d' % (int(t) // 60, int(t) % 60)
    c['dur_s'] = round(dur, 2)
    kept.append(c)

print('kept %d, dropped %d' % (len(kept), len(dropped)))
for c in dropped:
    print('  drop card %-3s %-34s  %s' % (c['n'], c['head'][:34], c['drop']))
short = [c for c in kept if c['dur_s'] < MAX]
print('\nshortened so they end as a plate begins: %d' % len(short))
for c in kept:
    if c['dur_s'] < MAX:
        print('  card %-3s %.1fs  %s' % (c['n'], c['dur_s'], c['head'][:38]))
gaps = [kept[i+1]['t_s'] - kept[i]['t_s'] for i in range(len(kept)-1)]
print('\ncadence min %.0fs median %.0fs max %.0fs' % (min(gaps), sorted(gaps)[len(gaps)//2], max(gaps)))

if '--write' in sys.argv:
    kept.sort(key=lambda c: c['t_s'])
    shots = json.load(open('tumaninah/timing/placed.json'))
    for i, c in enumerate(kept, 1):
        c['n'] = '%02d' % i
        under = [r for r in shots if r['in_s'] <= c['t_s'] < r['out_s']]
        c['scene'] = under[0]['scene'] if under else ''
    json.dump(kept, open('tumaninah/cards-src/cards.json', 'w'), ensure_ascii=False, indent=0)
    json.dump(dropped, open('tumaninah/timing/cards_dropped.json', 'w'), ensure_ascii=False, indent=1)
    print('written')
