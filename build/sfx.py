#!/usr/bin/env python3
"""
Sound design bed for "You Sink to Your Room".

Brief: engaging, quiet, not disturbing — peaceful to sit inside. So this is
ambience and spot effects only. No music, no melody, nothing with a pitch centre
that would turn into a tune under the voiceover.

Everything is synthesised here rather than sampled, which keeps it licence-clean
and, more usefully, means every sound in the mix is one we chose deliberately.

Three ambience movements, tracking the picture:
    0.00 - 27.19  open air over the pitch
   27.19 - 29.63  the match cut, and the street on the other side of it
   29.63 - 58.68  interior — rooms, close and quiet
   58.68 - 67.35  night: rain on glass, then the street outside

Spot effects sit only on beats the picture already plays. Nothing is added to a
scene just because it was quiet.
"""
import math, os, struct, subprocess, sys, wave
import numpy as np

BUILD = os.path.dirname(os.path.abspath(__file__))
OUT   = os.path.join(BUILD, "out")
SR    = 48000
TOTAL = 67.345
N     = int(TOTAL * SR)

rng = np.random.default_rng(20260809)

# ------------------------------------------------------------------ helpers --
def t_arr(n=None):
    return np.arange(n if n else N) / SR

def sl(t0, t1):
    """sample slice for a time window"""
    return slice(int(t0 * SR), min(int(t1 * SR), N))

def white(n):
    return rng.standard_normal(n)

def lp_fast(x, fc, order=2):
    """
    Frequency-domain low-pass. Far quicker than sample recursion for the long
    ambience buffers, and the phase behaviour does not matter for noise.
    """
    n = x.size
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    H = 1.0 / (1.0 + (f / max(fc, 1e-6)) ** 2) ** (order / 2.0)
    return np.fft.irfft(X * H, n)

def hp_fast(x, fc, order=2):
    n = x.size
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    with np.errstate(divide="ignore", invalid="ignore"):
        H = 1.0 / (1.0 + (fc / np.maximum(f, 1e-6)) ** 2) ** (order / 2.0)
    H[0] = 0.0
    return np.fft.irfft(X * H, n)

def bp_fast(x, lo, hi, order=2):
    return lp_fast(hp_fast(x, lo, order), hi, order)

def pink(n):
    x = white(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1] if f.size > 1 else 1.0
    return np.fft.irfft(X / np.sqrt(f), n)

def env_ar(n, attack, release, hold=0.0):
    """raised-cosine attack / hold / release — no clicks anywhere"""
    a = max(1, int(attack * SR))
    h = max(0, int(hold * SR))
    r = max(1, int(release * SR))
    body = a + h + r
    if body < n:
        r += n - body
    a, h, r = min(a, n), min(h, max(0, n - a)), max(1, n - a - h)
    up = 0.5 - 0.5 * np.cos(np.linspace(0, math.pi, a))
    dn = 0.5 + 0.5 * np.cos(np.linspace(0, math.pi, r))
    e = np.concatenate([up, np.ones(h), dn])
    return e[:n] if e.size >= n else np.pad(e, (0, n - e.size))

def fade(x, fin=0.0, fout=0.0):
    """in-place fades; works on mono (n,) and stereo (n,2) alike"""
    n = x.shape[0]
    shape = (-1,) + (1,) * (x.ndim - 1)
    if fin > 0:
        k = min(n, int(fin * SR))
        x[:k] *= (np.linspace(0, 1, k) ** 1.5).reshape(shape)
    if fout > 0:
        k = min(n, int(fout * SR))
        x[n - k:] *= (np.linspace(1, 0, k) ** 1.5).reshape(shape)
    return x

def widen(mono, spread=0.25, seed_shift=137):
    """decorrelate slightly into stereo so ambience sits around the voice"""
    n = mono.size
    d = int(spread * SR / 1000 * 8)
    r = np.roll(mono, d)
    l = mono
    return np.stack([l, 0.85 * r + 0.15 * l], axis=1)

def add(buf, x, t0, gain=1.0):
    """mix x into the stereo buf at t0"""
    i = int(t0 * SR)
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    k = min(x.shape[0], buf.shape[0] - i)
    if k > 0:
        buf[i:i + k] += gain * x[:k]

def rms_db(x):
    r = np.sqrt(np.mean(x ** 2))
    return 20 * math.log10(max(r, 1e-12))

MIX = np.zeros((N, 2))

# =========================================================== AMBIENCE BEDS ===
def moving_air(dur, fc, depth=0.18, rate=0.07, seed_lp=2):
    """broadband air with a slow breathing motion — the peaceful backbone"""
    n = int(dur * SR)
    base = pink(n)
    base = lp_fast(base, fc, seed_lp)
    base /= max(np.abs(base).max(), 1e-9)
    t = np.arange(n) / SR
    lfo = 1.0 + depth * np.sin(2 * math.pi * rate * t + rng.random() * 6.28)
    lfo *= 1.0 + 0.5 * depth * np.sin(2 * math.pi * rate * 2.7 * t)
    return base * lfo

# --- 0.00-27.19  open air over the pitch -------------------------------------
seg = 27.19
air = moving_air(seg, 900, depth=0.22, rate=0.055)
add(MIX, widen(fade(air, 0.9, 0.6)), 0.0, 0.040)
# a little more top so it reads as outdoors rather than a room
top = hp_fast(lp_fast(pink(int(seg * SR)), 4200, 2), 1400, 2)
top /= max(np.abs(top).max(), 1e-9)
add(MIX, widen(fade(top, 1.2, 0.6)), 0.0, 0.015)

# distant birdsong — sparse, soft, well back in the field.
def bird(f0=2350, n_notes=2, spacing=0.16, glide=-140, dur=0.085):
    parts = []
    for k in range(n_notes):
        n = int(dur * SR)
        t = np.arange(n) / SR
        f = f0 + glide * (t / max(dur, 1e-6)) + 60 * np.sin(2 * math.pi * 22 * t)
        ph = 2 * math.pi * np.cumsum(f) / SR
        s = np.sin(ph) * env_ar(n, 0.012, dur * 0.75)
        s += 0.18 * np.sin(2 * ph) * env_ar(n, 0.012, dur * 0.5)
        parts.append(s)
        parts.append(np.zeros(int(spacing * SR)))
    y = np.concatenate(parts)
    y = lp_fast(y, 5200, 1)
    tail = np.zeros(int(0.55 * SR))
    y = np.concatenate([y, tail])
    # cheap air-distance reverb: a couple of soft, filtered reflections
    for d, g in ((0.055, 0.30), (0.105, 0.20), (0.180, 0.12)):
        y[int(d * SR):] += g * lp_fast(y[: y.size - int(d * SR)], 2600, 1)
    return y / max(np.abs(y).max(), 1e-9)

for t0, f0, nn in ((2.9, 2450, 2), (8.1, 2180, 3), (14.6, 2600, 2), (23.9, 2300, 2)):
    b = bird(f0=f0, n_notes=nn)
    add(MIX, widen(b, spread=0.5), t0, 0.021)

# --- 27.19-29.63  the match cut, and the street ------------------------------
street = moving_air(2.62, 520, depth=0.10, rate=0.5)
add(MIX, widen(fade(street, 0.5, 0.5)), 27.19, 0.048)

# --- 29.63-58.68  interiors --------------------------------------------------
seg_i = 58.68 - 29.00
room = moving_air(seg_i, 520, depth=0.12, rate=0.04)
add(MIX, widen(fade(room, 0.9, 1.0), spread=0.16), 29.00, 0.058)

# scene 10, the friends' flat: warmth, no intelligible voices — just the low
# body of a room with people in it, well under the voiceover.
n10 = int(4.702 * SR)
murm = bp_fast(pink(n10), 190, 700, 2)
murm /= max(np.abs(murm).max(), 1e-9)
tm = np.arange(n10) / SR
murm *= 1.0 + 0.55 * np.sin(2 * math.pi * 0.9 * tm) * np.sin(2 * math.pi * 0.31 * tm)
add(MIX, widen(fade(murm, 0.8, 0.9), spread=0.3), 33.644, 0.028)

# --- 58.68-67.35  night ------------------------------------------------------
night = moving_air(67.345 - 58.68, 300, depth=0.10, rate=0.05)
add(MIX, widen(fade(night, 1.0, 0.0), spread=0.2), 58.68, 0.040)

# =============================================================== SPOT WORK ===

# scene 05 — the ball rolls out, slows, and stops on the dirt.
# picture window is 0.90-3.48s of the clip; it comes to rest ~1.6-2.2s in.
n = int(2.45 * SR)
t = np.arange(n) / SR
slowdown = np.clip(1.0 - t / 2.15, 0.0, 1.0) ** 1.35
roll = bp_fast(pink(n), 70, 900, 2)
roll /= max(np.abs(roll).max(), 1e-9)
grain = 1.0 + 0.35 * np.sin(2 * math.pi * (26 * slowdown + 3) * t)
roll *= slowdown * grain
settle = np.zeros(n)
si = int(2.02 * SR)
if si < n:
    ln = min(int(0.16 * SR), n - si)
    thud = lp_fast(white(ln), 260, 2) * env_ar(ln, 0.004, 0.13)
    settle[si:si + ln] = thud / max(np.abs(thud).max(), 1e-9)
add(MIX, widen(fade(roll, 0.10, 0.35) * 0.9 + settle * 0.55, spread=0.2), 17.15, 0.055)

# scene 04 — the sprint. one soft pass-by, no more.
n = int(1.05 * SR)
sw = bp_fast(white(n), 300, 3000, 2)
sw /= max(np.abs(sw).max(), 1e-9)
sw *= env_ar(n, 0.34, 0.68)
add(MIX, widen(sw, spread=0.6), 12.45, 0.030)

# scene 08 — the match cut. the one moment allowed to lift.
n = int(1.30 * SR)
t = np.arange(n) / SR
rise = white(n)
X = np.fft.rfft(rise); f = np.fft.rfftfreq(n, 1 / SR)
rise = np.fft.irfft(X * (1.0 / (1.0 + (f / 2400.0) ** 2)), n)
sweep = np.interp(t, [0, 0.62, 1.30], [0.0, 1.0, 0.18]) ** 1.6
rise = rise / max(np.abs(rise).max(), 1e-9) * sweep
add(MIX, widen(rise, spread=0.7), 26.95, 0.042)

# scene 11 — the cushion giving way under an unseen weight.
n = int(1.75 * SR)
t = np.arange(n) / SR
cush = lp_fast(pink(n), 520, 2)
cush /= max(np.abs(cush).max(), 1e-9)
cush *= np.clip(1.0 - t / 1.75, 0, 1) ** 0.9 * env_ar(n, 0.28, 1.1)
add(MIX, widen(cush, spread=0.15), 38.45, 0.034)

# scene 13 — the vase. delicate ceramic, on the three caption beats.
# these are the sharpest sounds in the piece and they are still tiny.
def ceramic(dur=0.30, bright=2600, ring=(1850, 3100, 4700)):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    tick = bp_fast(white(n), 900, bright * 2.2, 2) * env_ar(n, 0.0012, 0.045)
    body = np.zeros(n)
    for k, fq in enumerate(ring):
        body += (0.6 ** k) * np.sin(2 * math.pi * fq * tt) * np.exp(-tt * (16 + 7 * k))
    y = 0.85 * tick / max(np.abs(tick).max(), 1e-9) + 0.5 * body / max(np.abs(body).max(), 1e-9)
    for d, g in ((0.031, 0.22), (0.062, 0.13)):
        y[int(d * SR):] += g * lp_fast(y[: n - int(d * SR)], 3000, 1)
    return y / max(np.abs(y).max(), 1e-9)

for t0, g, br in ((49.33, 0.052, 2400), (50.68, 0.050, 2750), (51.88, 0.058, 3000)):
    add(MIX, widen(ceramic(bright=br), spread=0.3), t0, g)
# a few micro-shards drifting after the third
for t0, g in ((52.20, 0.022), (52.46, 0.017), (52.85, 0.014), (53.20, 0.011)):
    add(MIX, widen(ceramic(dur=0.18, bright=3400, ring=(2600, 4200, 6100)), spread=0.5), t0, g)

# scene 14 — leaving the warm room for the cold hallway. two soft steps.
def footstep(soft=1.0, bright=1500):
    n = int(0.19 * SR)
    y = lp_fast(white(n), bright, 2) * env_ar(n, 0.005, 0.15)
    low = lp_fast(white(n), 190, 2) * env_ar(n, 0.008, 0.11)
    y = y / max(np.abs(y).max(), 1e-9) + 0.7 * low / max(np.abs(low).max(), 1e-9)
    return soft * y / max(np.abs(y).max(), 1e-9)

for t0, g in ((54.35, 0.030), (55.02, 0.026), (55.71, 0.021)):
    add(MIX, widen(footstep(), spread=0.25), t0, g)

# scene 15 — rain beading on the glass. gentle, never a downpour.
n = int(3.30 * SR)
rain = hp_fast(white(n), 2600, 2)
rain /= max(np.abs(rain).max(), 1e-9)
tr = np.arange(n) / SR
rain *= 1.0 + 0.30 * np.sin(2 * math.pi * 0.32 * tr) * np.sin(2 * math.pi * 0.11 * tr)
add(MIX, widen(fade(rain, 0.9, 0.9), spread=0.4), 58.70, 0.015)
# individual beads running down the pane
for t0 in (59.35, 60.10, 60.62, 61.24):
    nb = int(0.10 * SR)
    tb = np.arange(nb) / SR
    bead = np.sin(2 * math.pi * (3400 - 900 * tb / 0.10) * tb) * env_ar(nb, 0.002, 0.085)
    add(MIX, widen(lp_fast(bead, 5200, 1), spread=0.6), t0, 0.010)

# scene 16 — two of them walking, in step, going away from us.
for k in range(9):
    t0 = 62.05 + k * 0.52
    if t0 > 66.9:
        break
    dist = 1.0 - 0.62 * (k / 8.0)           # they get further away
    add(MIX, widen(footstep(bright=1150), spread=0.3), t0, 0.024 * dist)
    add(MIX, widen(footstep(bright=980), spread=0.35), t0 + 0.075, 0.017 * dist)

# ================================================================== POLISH ===
MIX = fade(MIX, 0.6, 0.45)

peak = np.abs(MIX).max()
print(f"sfx bus  peak {20*math.log10(max(peak,1e-12)):6.2f} dBFS   "
      f"rms {rms_db(MIX):6.2f} dBFS")
if peak > 0.95:
    MIX *= 0.95 / peak
    print("  (peak-limited)")

path = os.path.join(OUT, "sfx_bed.wav")
data = (np.clip(MIX, -1, 1) * 32767).astype("<i2")
with wave.open(path, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(data.tobytes())
print("wrote", path, f"{os.path.getsize(path)/1048576:.1f} MiB")
