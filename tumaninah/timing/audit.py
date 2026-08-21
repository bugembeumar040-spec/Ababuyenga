"""One audit over the finished cut, on measured values only.

This replaces card_audit.py and head_audit.py, which scored cards against fields
snap.py used to write and against the bag-of-words match align_cards.py exists to
replace — so both had started reporting on data nothing produces any more.
"""
import json, os, re, subprocess, unicodedata

FF = subprocess.run(['python3', '-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],
                    capture_output=True, text=True).stdout.strip()

def slug(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'^-|-$', '', re.sub(r'[^a-zA-Z0-9]+', '-', s).lower())

mmss = lambda t: '%02d%s' % (int(t.split(':')[0]), t.split(':')[1])
cards = json.load(open('tumaninah/cards-src/cards.json'))
plates = json.load(open('tumaninah/cards-src/plates.json'))
rows = json.load(open('tumaninah/timing/placed.json'))
TOTAL = json.load(open('tumaninah/timing/timeline.json'))['total']
by = {r['scene']: r for r in rows}
fail = []

def check(name, bad, detail=lambda x: str(x)):
    if bad:
        fail.append(name)
        print('  FAIL %-34s %d' % (name, len(bad)))
        for b in bad[:6]:
            print('        %s' % detail(b))
    else:
        print('  ok   %s' % name)

print('CARDS (%d) over %d:%02d' % (len(cards), TOTAL // 60, TOTAL % 60))

check('card contains its phrase',
      [c for c in cards if c.get('phrase_s') is not None
       and not (c['t_s'] <= c['phrase_s'] and c['phrase_e'] <= c['t_s'] + c['dur_s'])],
      lambda c: 'card %s %.2f-%.2f vs phrase %.2f-%.2f  %s'
                % (c['n'], c['t_s'], c['t_s'] + c['dur_s'], c['phrase_s'], c['phrase_e'], c['head'][:26]))

check('phrase matched confidently',
      [c for c in cards if c.get('match', 1.0) < 0.75],
      lambda c: 'card %s match %.2f  %s' % (c['n'], c['match'], c['head'][:34]))

check('ends inside the cut',
      [c for c in cards if c['t_s'] + c['dur_s'] > TOTAL + 0.01],
      lambda c: 'card %s ends %.2f, cut ends %.2f' % (c['n'], c['t_s'] + c['dur_s'], TOTAL))

check('readable length',
      [c for c in cards if c['dur_s'] < 3.5],
      lambda c: 'card %s %.1fs' % (c['n'], c['dur_s']))

check('no card over a plate',
      [(c, p) for p in plates if p['scene'] in by for c in cards
       if c['t_s'] < by[p['scene']]['out_s'] and c['t_s'] + c['dur_s'] > by[p['scene']]['in_s']],
      lambda x: 'card %s over plate sc%s' % (x[0]['n'], x[1]['scene']))

check('numbered in time order',
      [i for i in range(len(cards) - 1) if cards[i]['n'] >= cards[i + 1]['n']],
      lambda i: 'card %s before %s' % (cards[i]['n'], cards[i + 1]['n']))

missing, wrong = [], []
for c in cards:
    f = 'tumaninah/overlays/webm/card-%s_%s_%s.webm' % (c['n'], mmss(c['t']), slug(c['head']))
    if not os.path.exists(f):
        missing.append((c, f)); continue
    r = subprocess.run([FF, '-i', f], capture_output=True, text=True).stderr
    m = re.search(r'Duration: (\d+):(\d+):([\d.]+)', r)
    a = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    if abs(a - c['dur_s']) > 0.2:
        wrong.append((c, a))
check('every card rendered', missing, lambda x: 'card %s -> %s' % (x[0]['n'], os.path.basename(x[1])))
check('render length matches spec', wrong, lambda x: 'card %s file %.2f vs spec %.2f' % (x[0]['n'], x[1], x[0]['dur_s']))

stale = [f for f in os.listdir('tumaninah/overlays/webm') if f.startswith('card-')
         and f not in {'card-%s_%s_%s.webm' % (c['n'], mmss(c['t']), slug(c['head'])) for c in cards}]
check('no stale renders', stale, lambda f: f)

ev = sorted([(c['t_s'], c['t_s'] + c['dur_s']) for c in cards] +
            [(by[p['scene']]['in_s'], by[p['scene']]['out_s']) for p in plates if p['scene'] in by])
prev, gaps = 0.0, []
for a, b in ev:
    if a > prev:
        gaps.append((a - prev, prev))
    prev = max(prev, b)
gaps.sort(reverse=True)
print('\n  overlays %d  |  avg one per %.0fs  |  longest bare %.0fs at %d:%02d  |  tail %.2fs'
      % (len(ev), TOTAL / len(ev), gaps[0][0], gaps[0][1] // 60, gaps[0][1] % 60, TOTAL - prev))
print('\n%s' % ('ALL CHECKS PASS' if not fail else 'FAILED: ' + ', '.join(fail)))
