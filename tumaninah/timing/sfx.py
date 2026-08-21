"""Ambience beds for the cut, synthesised rather than sourced.

No instruments: this is a Qurʾānic study, and music is contested for a good part
of the audience. Everything here is weather, stone and water — the sūrah is named
after thunder, so the sound design is the sūrah's own imagery.

Beds are written as a separate stem as well as a mix, so the level stays the
editor's decision.
"""
import json, os, subprocess
import numpy as np

SR = 44100
OUT = 'tumaninah/preview'
rng = np.random.default_rng(7)

def shaped(n, tilt, lo=None, hi=None):
    """Noise with a spectral tilt (-1 pink, -2 brown) and optional band limits."""
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    X *= f ** (tilt / 2.0)
    if lo:
        X *= 1 / (1 + (lo / f) ** 4)
    if hi:
        X *= 1 / (1 + (f / hi) ** 4)
    y = np.fft.irfft(X, n)
    m = np.max(np.abs(y))
    return y / m if m else y

def env_loop(y, fade=0.5):
    """Make a seamless loop by crossfading the tail over the head."""
    k = int(fade * SR)
    y = y.copy()
    head, tail = y[:k], y[-k:]
    w = np.linspace(0, 1, k)
    y[:k] = head * w + tail * (1 - w)
    return y[:-k]

def tile(loop, n):
    reps = int(np.ceil(n / len(loop)))
    return np.tile(loop, reps)[:n]

def rain(n):
    base = env_loop(shaped(SR * 12, -1.0, lo=400, hi=7000))
    y = tile(base, n)
    # slow gusting so it does not sit flat under the voice
    t = np.arange(n) / SR
    return y * (0.75 + 0.25 * np.sin(2 * np.pi * t / 17 + 1.2))

def rumble(n):
    base = env_loop(shaped(SR * 15, -2.0, hi=110))
    t = np.arange(n) / SR
    return tile(base, n) * (0.6 + 0.4 * np.sin(2 * np.pi * t / 23))

def cave(n):
    base = env_loop(shaped(SR * 14, -2.0, lo=60, hi=320))
    y = tile(base, n) * 0.9
    # sparse drips, each with one soft reflection
    for at in np.arange(3.0, n / SR, 9.7):
        i = int(at * SR)
        d = int(0.35 * SR)
        if i + d * 2 > n:
            break
        t = np.arange(d) / SR
        ping = np.sin(2 * np.pi * 780 * t) * np.exp(-t * 26)
        y[i:i + d] += ping * 0.22
        y[i + int(0.19 * SR):i + int(0.19 * SR) + d] += ping * 0.09
    return y

def thunder(dur=7.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    crack = shaped(n, -1.5, hi=2600) * np.exp(-t * 5.5)
    body = shaped(n, -2.0, hi=160) * (1 - np.exp(-t * 9)) * np.exp(-t * 0.75)
    y = crack * 0.5 + body * 1.0
    return y / np.max(np.abs(y))

def db(x, level):
    m = np.max(np.abs(x))
    return x * (10 ** (level / 20.0) / m) if m else x

rows = json.load(open('tumaninah/timing/placed.json'))
TOTAL = json.load(open('tumaninah/timing/timeline.json'))['total']
N = int(TOTAL * SR)
bed = np.zeros(N)

def place(sig, at, level, fin=1.5, fout=3.0):
    i = int(at * SR)
    sig = db(sig, level)
    k = min(len(sig), N - i)
    if k <= 0:
        return
    s = sig[:k].copy()
    a, b = int(fin * SR), int(fout * SR)
    if a and k > a:
        s[:a] *= np.linspace(0, 1, a)
    if b and k > b:
        s[-b:] *= np.linspace(1, 0, b)
    bed[i:i + k] += s

# --- cue sheet -------------------------------------------------------------
# storm under the opening: the sūrah is named after it and the narration is
# describing the weather directly
place(rain(int(63.9 * SR)), 0.0, -33)
place(rumble(int(63.9 * SR)), 0.0, -30)
place(thunder(), 4.0, -23, fin=0.0, fout=1.5)
place(thunder(), 19.5, -29, fin=0.0, fout=1.5)
# the glass on the table — a quiet room, nothing more
place(shaped(int(91.4 * SR), -2.0, hi=220), 701.3, -40)
# Mount Thawr
place(cave(int(77.0 * SR)), 792.7, -32)
# the close returns to the thunder it opened on
place(rumble(int(79.3 * SR)), 1008.0, -34, fin=4.0, fout=6.0)
place(rain(int(79.3 * SR)), 1008.0, -37, fin=4.0, fout=6.0)

peak = np.max(np.abs(bed))
bed = bed / max(peak, 1.0)
pcm = (np.clip(bed, -1, 1) * 32767).astype('<i2')

import wave
os.makedirs(OUT, exist_ok=True)
with wave.open(os.path.join(OUT, 'ambience.wav'), 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('ambience stem %.1fs, peak %.1f dBFS' % (TOTAL, 20 * np.log10(peak)))

FF = subprocess.run(['python3', '-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],
                    capture_output=True, text=True).stdout.strip()
# Voice first: high-pass off the rumble, level to broadcast, then the bed under it.
subprocess.run([FF, '-y', '-loglevel', 'error',
                '-i', os.path.join(OUT, 'voiceover.m4a'),
                '-i', os.path.join(OUT, 'ambience.wav'),
                '-filter_complex',
                '[0:a]highpass=f=70,loudnorm=I=-16:TP=-1.5:LRA=11[v];'
                '[1:a]highpass=f=35[a];'
                '[v][a]amix=inputs=2:duration=first:weights=1 0.85:normalize=0[m]',
                '-map', '[m]', '-c:a', 'aac', '-b:a', '176k',
                os.path.join(OUT, 'mix.m4a')], check=True)
print('mixed ->', os.path.join(OUT, 'mix.m4a'))
