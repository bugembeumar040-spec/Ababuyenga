"""Check every card against the line it was snapped to and the frame under it.

The useful question is not whether the card's editorial copy echoes the speech —
it paraphrases by design — but whether the card is on screen while the line it
glosses is being spoken, and whether it sits on the frame that line belongs to.
"""
import json

CARD_LEN = 6.0
EDGE = 0.5          # a card landing this close to a cut reads as being on the wrong frame

cards = json.load(open('tumaninah/cards-src/cards.json'))
rows = json.load(open('tumaninah/timing/placed.json'))
plates = json.load(open('tumaninah/cards-src/plates.json'))
by = {r['scene']: r for r in rows}
plate_ends = {round(by[p['scene']]['out_s'], 2) for p in plates if p['scene'] in by}

def shot_at(t):
    for r in rows:
        if r['in_s'] <= t < r['out_s']:
            return r
    return None

issues = []
print('%-4s %8s %8s %7s  %-30s %s' % ('card', 'in', 'line at', 'lead', 'frame', 'head'))
for c in cards:
    t = c['t_s']; la = c.get('line_at')
    sh = shot_at(t)
    covered = la is not None and t <= la <= t + CARD_LEN
    near_cut = sh is not None and (t - sh['in_s'] < EDGE or sh['out_s'] - t < EDGE)
    same_shot = sh is not None and la is not None and shot_at(la) is sh
    # A card held back for a plate starts as the plate clears, so its line is
    # spoken a moment before it appears. That is the trade, not a fault.
    after_plate = round(t, 2) in plate_ends
    flag = []
    if after_plate:
        print('%-4s %8.2f %8.2f %+7.2f  %-30s %s   (follows a plate)' % (
            c['n'], t, la or -1, (la - t) if la else 0,
            ('sc%s %.1f-%.1f' % (sh['scene'], sh['in_s'], sh['out_s'])) if sh else '—',
            c['head'][:30]))
        continue
    if not covered:
        flag.append('LINE OUTSIDE CARD')
    if not same_shot:
        flag.append('CARD AND LINE ON DIFFERENT FRAMES')
    if near_cut and t - sh['in_s'] >= EDGE:
        flag.append('LANDS ON A CUT')
    if flag:
        issues.append((c['n'], flag))
    print('%-4s %8.2f %8.2f %+7.2f  %-30s %s%s' % (
        c['n'], t, la or -1, (la - t) if la else 0,
        ('sc%s %.1f-%.1f' % (sh['scene'], sh['in_s'], sh['out_s'])) if sh else '—',
        c['head'][:30], ('   << ' + ', '.join(flag)) if flag else ''))
print('\n%d of %d cards clean' % (len(cards) - len(issues), len(cards)))
for n, f in issues:
    print('  card %-3s %s' % (n, '; '.join(f)))
