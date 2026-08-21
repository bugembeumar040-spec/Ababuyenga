"""Transcribe the selected takes to get real timings for the assembled cut.

The transcript's own AUDIO boundaries proved unusable and the take selection was
fitted, not stated, so both were guesses. This replaces them with measurement:
each take is transcribed with word timestamps and stacked at its true offset,
giving one timed transcript of the audio that actually exists.
"""
import json, os, sys
from faster_whisper import WhisperModel

UPLOADS = '/root/.claude/uploads/b6b8a957-a047-5e7c-b664-115ea9a25bf7'
takes = json.load(open('tumaninah/timing/takes.json'))
model = WhisperModel('base.en', device='cpu', compute_type='int8', cpu_threads=4)

words, offset, per_take = [], 0.0, []
for i, t in enumerate(takes, 1):
    segs, info = model.transcribe(os.path.join(UPLOADS, t), word_timestamps=True,
                                  vad_filter=False, beam_size=1)
    n0 = len(words)
    end = 0.0
    for s in segs:
        for w in (s.words or []):
            words.append({'t': round(offset + w.start, 2), 'w': w.word.strip(), 'take': i})
            end = max(end, w.end)
    per_take.append({'take': i, 'file': t, 'offset': round(offset, 2),
                     'dur': round(info.duration, 2), 'words': len(words) - n0,
                     'last_word_at': round(end, 2)})
    print('take %2d  %6.1fs  %4d words  offset %7.1f  %s'
          % (i, info.duration, len(words) - n0, offset, t[:22]), flush=True)
    offset += info.duration

json.dump({'takes': per_take, 'words': words},
          open('tumaninah/timing/asr.json', 'w'), ensure_ascii=False)
print('total %.1fs  %d words -> tumaninah/timing/asr.json' % (offset, len(words)))
