#!/usr/bin/env python3
"""
"You Sink to Your Room" — assembles the 16 Seedance 2.5 clips + the emotion-tagged
voiceover into one 1080x1920 master, per companyyoukeeppromptpack.txt.

Order of operations follows the pack's house rule: the VO is the clock, the
picture is cut to it.
"""
import json, os, subprocess, sys

BUILD = os.path.dirname(os.path.abspath(__file__))
RAW   = os.path.join(BUILD, "raw")
VO    = os.path.join(BUILD, "vo")
SEG   = os.path.join(BUILD, "seg")
CAP   = os.path.join(BUILD, "cap")
OUT   = os.path.join(BUILD, "out")
for d in (SEG, CAP, OUT):
    os.makedirs(d, exist_ok=True)

W, H, FPS = 1080, 1920, 24
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# palette (pack: PALETTE — hex, for the edit and for any burn-in)
CREAM     = (245, 239, 226)   # #F5EFE2 caption fill
NAVY      = (20,  36,  51)    # #142433 caption outline / lower-third bed
TERRACOTTA= (232, 98,  47)    # #E8622F accent word

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAILED:", cmd, file=sys.stderr)
        print(r.stderr[-3000:], file=sys.stderr)
        sys.exit(1)
    return r.stdout

def dur(path):
    return float(sh(f'ffprobe -v error -show_entries format=duration -of csv=p=0 "{path}"').strip())

# ---------------------------------------------------------------- timeline ---
# line audio file, and the gap of silence that follows it inside its own scene
LINES = [
    ("ht_01.wav",         0.10),
    ("ht_02.wav",         0.12),
    ("ht_03.wav",         0.35),   # open loop — let it hang
    ("ht_04_tight.wav",   0.28),   # beat before the payoff
    ("ht_05.wav",         0.65),   # THE beat: "So he stops making them."
    ("ht_06.wav",         0.18),
    ("ht_07.wav",         0.15),
    ("ht_08.wav",         0.32),   # the turn
    ("ht_09.wav",         0.28),   # title line
    ("ht_10.wav",         0.14),
    ("ht_11.wav",         0.32),
    ("ht_12_tightA.wav",  0.18),
    ("ht_13.wav",         0.25),
    ("ht_14.wav",         0.16),
    ("ht_15.wav",         0.45),   # "Who do I become in that room?"
    ("ht_16.wav",         0.25),   # tail after "Follow."
]
LEAD = 0.10   # silence before the first word

# per-clip picture strategy.
#   trim  -> take a `start`-second window at natural speed (shot reads the same anywhere)
#   speed -> retime to fit, preserving the shot's full arc (a reveal that must be seen)
#   slow  -> stretch to fill, only ever on a near-static shot where it is invisible
PICTURE = {
    1:  ("slow",  0.0),
    2:  ("trim",  0.0),
    3:  ("trim",  1.00),
    4:  ("trim",  0.0),
    5:  ("trim",  0.90),   # window holds the ball rolling out AND coming to rest
    6:  ("trim",  1.20),
    7:  ("trim",  0.0),
    8:  ("speed", 0.0),    # match-cut pitch->street must complete
    9:  ("trim",  0.0),
    10: ("trim",  0.0),
    11: ("speed", 0.0),    # cushion sinks AND phone dims to black
    12: ("slow",  0.0),    # "absolute stillness" — stretch is undetectable
    13: ("slow",  0.0),    # already extreme slow motion
    14: ("trim",  0.0),
    15: ("trim",  0.90),
    16: ("slow",  0.0),
}

scenes = []
t = 0.0
for i, (fn, gap) in enumerate(LINES, start=1):
    d = dur(os.path.join(VO, fn))
    lead = LEAD if i == 1 else 0.0
    sd = lead + d + gap
    scenes.append(dict(n=i, line=fn, line_dur=d, gap=gap, lead=lead,
                       start=t, dur=sd, line_start=t + lead))
    t += sd
TOTAL = t

print(f"{'#':>3} {'start':>7} {'len':>6} {'line':>6} {'gap':>5}  picture")
for s in scenes:
    src = dur(os.path.join(RAW, f"{s['n']:02d}.mp4"))
    mode, st = PICTURE[s["n"]]
    ratio = s["dur"] / (src - st)
    note = {"trim": f"trim @{st:.2f}s", "speed": f"speed {ratio:.3f}x",
            "slow": f"slow {ratio:.3f}x"}[mode]
    print(f"{s['n']:>3} {s['start']:>7.3f} {s['dur']:>6.3f} "
          f"{s['line_dur']:>6.3f} {s['gap']:>5.2f}  {note}")
print(f"TOTAL {TOTAL:.3f}s\n")

# ------------------------------------------------------------------- audio ---
# lay each line at its own start time on one continuous bed, then master
parts, filt = [], []
for k, s in enumerate(scenes):
    parts.append(f'-i "{os.path.join(VO, s["line"])}"')
    delay = int(round(s["line_start"] * 1000))
    filt.append(f"[{k}:a]aresample=48000,adelay={delay}|{delay}[a{k}]")
mix = "".join(f"[a{k}]" for k in range(len(scenes)))
filt.append(f"{mix}amix=inputs={len(scenes)}:normalize=0:dropout_transition=0[mixed]")
# gentle master: tame peaks, then bring to broadcast-ish loudness for social
filt.append("[mixed]acompressor=threshold=-18dB:ratio=2.5:attack=8:release=180:makeup=2,"
            "loudnorm=I=-14:TP=-1.5:LRA=11,"
            f"apad,atrim=0:{TOTAL:.4f},asetpts=N/SR/TB[outa]")
sh(f'ffmpeg -y -v error {" ".join(parts)} '
   f'-filter_complex "{";".join(filt)}" -map "[outa]" '
   f'-c:a pcm_s16le "{os.path.join(OUT, "vo_master.wav")}"')
print(f"voiceover master: {dur(os.path.join(OUT,'vo_master.wav')):.3f}s")

# ----------------------------------------------------------------- picture ---
for s in scenes:
    n, target = s["n"], s["dur"]
    src_path = os.path.join(RAW, f"{n:02d}.mp4")
    src = dur(src_path)
    mode, st = PICTURE[n]
    dst = os.path.join(SEG, f"{n:02d}.mp4")
    scale = (f"scale={W}:{H}:flags=lanczos:force_original_aspect_ratio=increase,"
             f"crop={W}:{H},setsar=1")
    if mode == "trim":
        vf = f"{scale},fps={FPS}"
        cmd = (f'ffmpeg -y -v error -ss {st:.4f} -i "{src_path}" -an '
               f'-vf "{vf}" -t {target:.4f} ')
    else:
        ratio = target / (src - st)
        vf = f"setpts={ratio:.6f}*PTS,{scale},fps={FPS}"
        cmd = (f'ffmpeg -y -v error -ss {st:.4f} -i "{src_path}" -an '
               f'-vf "{vf}" -t {target:.4f} ')
    cmd += ('-c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p '
            f'-r {FPS} -video_track_timescale 24000 "{dst}"')
    sh(cmd)
    got = dur(dst)
    if abs(got - target) > 0.08:
        print(f"  ! scene {n}: wanted {target:.3f}s got {got:.3f}s")

with open(os.path.join(SEG, "list.txt"), "w") as f:
    for s in scenes:
        seg_path = os.path.join(SEG, "%02d.mp4" % s["n"])
        f.write("file '%s'\n" % seg_path)
sh(f'ffmpeg -y -v error -f concat -safe 0 -i "{os.path.join(SEG,"list.txt")}" '
   f'-c copy "{os.path.join(OUT,"picture.mp4")}"')
print(f"picture: {dur(os.path.join(OUT,'picture.mp4')):.3f}s")

json.dump(dict(total=TOTAL, scenes=scenes), open(os.path.join(BUILD, "timeline.json"), "w"), indent=2)
print("wrote timeline.json")
