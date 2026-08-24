#!/usr/bin/env python3
"""Speech bounds measured from the waveform.

ASR word timestamps are not reliable for this -- whisper reports the first word
at 0.00s on files that demonstrably open with silence -- and parsing ffmpeg's
silencedetect output proved no better. Decoding to PCM and finding the first and
last frame above a threshold is exact and has no edge cases.
"""
import subprocess, numpy as np

SR = 44100

def pcm(path):
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path,
                          "-f", "s16le", "-acodec", "pcm_s16le", "-ar", str(SR),
                          "-ac", "1", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0

def bounds(path, thresh_db=-45.0, win=0.02):
    """(speech_start, speech_end, duration) in seconds."""
    x = pcm(path)
    dur = len(x) / SR
    n = max(1, int(win * SR))
    trim = len(x) - (len(x) % n)
    if trim == 0: return 0.0, dur, dur
    rms = np.sqrt((x[:trim].reshape(-1, n) ** 2).mean(axis=1))
    loud = rms > (10 ** (thresh_db / 20.0))
    if not loud.any(): return 0.0, dur, dur
    idx = np.flatnonzero(loud)
    return idx[0] * n / SR, min(dur, (idx[-1] + 1) * n / SR), dur

if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        s, e, d = bounds(p)
        print(f"{p}  dur {d:.2f}s  speech {s:.2f}-{e:.2f}s  head {s:.2f}s  tail {d-e:.2f}s")
