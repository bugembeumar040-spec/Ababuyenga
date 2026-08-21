"""Transcribe every upload so takes can be selected by content, not duration.

The uploads turned out to hold two different scripts — this study and an earlier
"honour your parents" one. Duration-fitting cannot tell them apart; the words can.
"""
import json, os
from faster_whisper import WhisperModel

UPLOADS = '/root/.claude/uploads/b6b8a957-a047-5e7c-b664-115ea9a25bf7'
OUT = 'tumaninah/timing/asr_all.json'
files = sorted((f for f in os.listdir(UPLOADS) if f.endswith('.mp3')),
               key=lambda f: f.split('Benjamin')[1][:15])
have = json.load(open(OUT)) if os.path.exists(OUT) else {}
model = WhisperModel('base.en', device='cpu', compute_type='int8', cpu_threads=4)

for i, f in enumerate(files, 1):
    if f in have:
        continue
    segs, info = model.transcribe(os.path.join(UPLOADS, f), word_timestamps=True,
                                  vad_filter=False, beam_size=1)
    words = [{'t': round(w.start, 2), 'w': w.word.strip()}
             for s in segs for w in (s.words or [])]
    have[f] = {'dur': round(info.duration, 2), 'words': words,
               'text': ' '.join(w['w'] for w in words)}
    json.dump(have, open(OUT, 'w'), ensure_ascii=False)
    print('%2d/%d  %6.1fs  %4d words  %s' % (i, len(files), info.duration, len(words), f[:26]), flush=True)
print('done ->', OUT)
