import json, csv, re, unicodedata

def norm(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return [t for t in re.split(r"[^a-z0-9']+", s.lower()) if t]

rows = json.load(open('tumaninah/timing/placed.json'))
beats = json.load(open('tumaninah/timing/beats.json'))
owner = []
for bi, b in enumerate(beats):
    if b['kind'] == 'arabic':
        continue
    owner += [bi] * len(norm(b['text']))
N = len(owner)

def sec_at(w):
    i = min(int(w), N - 1)
    return beats[owner[i]]['sec'] or '—'

def ts(s):
    return '%d:%05.2f' % (s // 60, s % 60)

for r in rows:
    r['section'] = sec_at(r['word'])

with open('tumaninah/timing/shotlist.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['cut', 'scene', 'in', 'out', 'dur_s', 'section', 'pack_chapter', 'file', 'in_cut', 'vo'])
    for r in rows:
        w.writerow([r['cut_order'], r['scene'], ts(r['in_s']), ts(r['out_s']), r['dur_s'],
                    r['section'], '%s · %s' % (r['chapter'], r['chapter_title']),
                    r['file'], 'yes' if r['in_cut'] else 'B-ROLL', r['vo']])

with open('tumaninah/timing/SHOTLIST.md', 'w') as f:
    f.write('# Ṭumaʾnīnah — image timing\n\n')
    f.write('116 frames cut to the assembled voiceover. Runtime **21:04** (1264 s).\n\n')
    f.write('Order follows the transcript, not the prompt pack — the script was resequenced\n'
            '(the ḥadīth beat now runs before "what we are walking toward"), so 13 frames sit\n'
            'more than three slots away from their pack position.\n\n')
    f.write('Rows marked **B-ROLL** have no matching line in this cut; they are parked beside\n'
            'their neighbour and can be dropped or used as cutaways.\n\n')
    cur = None
    for r in rows:
        if r['section'] != cur:
            cur = r['section']
            f.write('\n## %s\n\n| # | in | out | dur | scene | frame | line |\n|--:|--|--|--:|--|--|--|\n' % cur)
        f.write('| %d | `%s` | `%s` | %.1fs | %s%s | `%s` | %s |\n' % (
            r['cut_order'], ts(r['in_s']), ts(r['out_s']), r['dur_s'], r['scene'],
            ' ⟨B-roll⟩' if not r['in_cut'] else '', r['file'], r['vo'].replace('|', '\\|')[:88]))

print('wrote shotlist.csv + SHOTLIST.md')
longest = sorted(rows, key=lambda r: -r['dur_s'])[:6]
print('\nlongest holds (candidates for a slow push-in):')
for r in longest:
    print('   %-4s %6.1fs  @%s  %s' % (r['scene'], r['dur_s'], ts(r['in_s']), r['vo'][:56]))

# The overlay grid, and which frame each card lands on top of.
cards = json.load(open('tumaninah/cards-src/cards.json'))
def secs(t):
    m, s = t.split(':'); return int(m) * 60 + int(s)
with open('tumaninah/timing/cards.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['card', 'in', 'in_s', 'section', 'frame_under', 'scene', 'head', 'arabic', 'sub'])
    for c in cards:
        t = secs(c['t'])
        u = [r for r in rows if r['in_s'] <= t < r['out_s']]
        w.writerow([c['n'], c['t'], t, c['ch'], u[0]['file'] if u else '', c['scene'],
                    c['head'], c['ar'], c['sub']])
print('wrote cards.csv (%d marks)' % len(cards))
