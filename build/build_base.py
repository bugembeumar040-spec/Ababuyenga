"""Cut, conform and grade the 11 Higgsfield clips into one 1080x1920 base."""
import subprocess, os, sys
from edl import scenes, UPSCALE, FPS, W, H

os.makedirs("cut", exist_ok=True)

# Unified finish. Kept deliberately light -- the renders already carry the
# house grade. Grain is the important one: it masks the fact that six clips
# were generated at 720p and five at 1080p.
GRADE = (
    "eq=contrast=1.055:saturation=1.05:gamma=0.99,"
    "vignette=PI/5.2,"
    "noise=alls=5:allf=t+u"
)

for s in scenes():
    n, src = s["name"], f"clips/{s['name']}.mp4"

    chain = []
    if n in UPSCALE:
        # lanczos up + a touch of sharpening so the 720p sources don't read
        # softer than the natives once they sit next to each other
        chain.append("scale=1080:1920:flags=lanczos")
        chain.append("unsharp=5:5:0.42:5:5:0.0")
    else:
        chain.append("scale=1080:1920:flags=lanczos")
    chain.append(f"fps={FPS}")
    chain.append(GRADE)
    if s["freeze"] > 0:
        # hold the final settled frame; the scale has stopped moving by then
        # and the typography animating over it covers the hold
        chain.append(f"tpad=stop_mode=clone:stop={s['freeze']}")
    chain.append("setsar=1,format=yuv420p")

    cmd = [
        "ffmpeg", "-v", "error", "-y",
        "-ss", f"{s['src_in']:.4f}", "-i", src,
        "-vf", ",".join(chain),
        "-frames:v", str(s["frames"]),          # frame-exact, no drift
        "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "15",
        f"cut/{n}.mp4",
    ]
    subprocess.run(cmd, check=True)
    got = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                          "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0",
                          f"cut/{n}.mp4"], capture_output=True, text=True).stdout.strip()
    ok = "ok" if int(got) == s["frames"] else "*** MISMATCH ***"
    print(f"{n}  {s['frames']:4d} frames  got {got:>4}  {ok}"
          f"{'   (freeze ' + str(s['freeze']) + 'f)' if s['freeze'] else ''}")

with open("concat.txt", "w") as f:
    for s in scenes():
        f.write(f"file 'cut/{s['name']}.mp4'\n")

subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                "-i", "concat.txt", "-c", "copy", "base.mp4"], check=True)
d = subprocess.run(["ffprobe","-v","error","-count_frames","-select_streams","v:0","-show_entries","stream=nb_read_frames",
                    "-of","csv=p=0","base.mp4"], capture_output=True, text=True).stdout.strip()
print(f"\nbase.mp4  {d} frames = {int(d)/FPS:.3f}s")
