"""Parse transcript.md into ordered spoken beats with word counts."""
import re, json

SRC = 'tumaninah/transcript.md'
STAGE = re.compile(r'\[(calm|serious|thoughtful|emphatic|quiet|warmly)\]')
ARABIC = re.compile(r'^\[ARABIC — DROP IN:\s*(.+?)\]$')

def beats():
    sec = None
    audio = None
    out = []
    body = open(SRC, encoding='utf-8').read().split('## Audio-boundary reference')[0]
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r'^\[(\d\d):(\d\d)\] — AUDIO (\d+)$', line)
        if m:
            audio = int(m.group(3))
            continue
        if line.startswith('## '):
            t = line[3:].strip()
            if re.match(r'^\d+ · ', t):
                sec = t
            continue
        if line.startswith('★') or line.startswith('---') or line.startswith('|'):
            continue
        # Everything before the first section header is front matter, and audio 13
        # carries no dialogue, so neither contributes words to the timeline.
        if sec is None or audio == 13:
            continue
        m = ARABIC.match(line)
        if m:
            out.append({'audio': audio, 'sec': sec, 'kind': 'arabic',
                        'text': m.group(1), 'words': 6})
            continue
        text = STAGE.sub('', line).strip()
        if not text:
            continue
        out.append({'audio': audio, 'sec': sec, 'kind': 'vo',
                    'text': text, 'words': len(text.split())})
    return out

if __name__ == '__main__':
    b = beats()
    json.dump(b, open('tumaninah/timing/beats.json', 'w'), ensure_ascii=False, indent=1)
    print('beats:', len(b), ' words:', sum(x['words'] for x in b))
    # per-audio word counts vs the durations the user supplied
    tbl = [144,108,147,34,135,93,89,114,73,23,117,108,79]
    print('\n aud  words   wpm@given   given(s)  fair-share(s)')
    tot_w = sum(x['words'] for x in b)
    tot_s = sum(tbl)
    for i in range(1, 14):
        w = sum(x['words'] for x in b if x['audio'] == i)
        g = tbl[i-1]
        fair = tot_s * w / tot_w
        print('%4d %6d %10.0f %10d %13.0f' % (i, w, w/g*60 if g else 0, g, fair))
    print('total words %d over %ds = %.0f wpm' % (tot_w, tot_s, tot_w/tot_s*60))
