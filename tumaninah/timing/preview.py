"""Build a silent picture-lock preview: frames cut to the shot list, cards composited.

Not a deliverable — a way to watch the timing before the audio is assembled.
"""
import json, os, subprocess, sys, csv

W, H, FPS = 1280, 720, 30
OUT = 'tumaninah/preview'
FFMPEG = subprocess.run(['python3', '-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],
                        capture_output=True, text=True).stdout.strip()

rows = json.load(open('tumaninah/timing/placed.json'))
os.makedirs(OUT, exist_ok=True)

# Picture track: one still per shot, held for its measured duration.
lst = os.path.join(OUT, 'frames.txt')
with open(lst, 'w') as f:
    for r in rows:
        p = os.path.abspath(os.path.join('tumaninah/images', r['file']))
        f.write("file '%s'\nduration %.3f\n" % (p, r['dur_s']))
    f.write("file '%s'\n" % p)   # concat demuxer drops the last entry without a repeat

base = os.path.join(OUT, 'picture.mp4')
subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                '-vf', 'scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=%d'
                % (W, H, W, H, FPS),
                '-c:v', 'libx264', '-crf', '23', '-preset', 'veryfast', '-pix_fmt', 'yuv420p',
                base], check=True)
print('picture track ->', base)

if '--picture-only' in sys.argv:
    sys.exit()

# Cards on top. They never overlap, so one chained overlay per card is enough;
# itsoffset puts each on the timeline without keying its enable window by hand.
marks = list(csv.DictReader(open('tumaninah/timing/cards.csv')))
# cards.csv carries the fitted in-point; the webm carries its own trimmed length.
webm = {f.split('_')[0].split('-')[1]: f for f in os.listdir('tumaninah/overlays/webm')}
args = [FFMPEG, '-y', '-loglevel', 'error', '-i', base]
fc, prev = [], '0:v'
n = 0
for m in marks:
    f = webm.get(m['card'])
    if not f:
        continue
    n += 1
    args += ['-itsoffset', m['in_s'], '-c:v', 'libvpx-vp9', '-i',
             os.path.join('tumaninah/overlays/webm', f)]
    fc.append('[%d:v]scale=%d:%d[c%d]' % (n, W, H, n))
    fc.append('[%s][c%d]overlay=0:0:eof_action=pass:repeatlast=0[v%d]' % (prev, n, n))
    prev = 'v%d' % n

# Ayah plates sit on the empty cartouche frames for the length of that shot.
plates = json.load(open('tumaninah/cards-src/plates.json'))
by_scene = {r['scene']: r for r in rows}
for pl in plates:
    f = 'tumaninah/overlays/plates/plate-scene-%s.webm' % pl['scene']
    if not os.path.exists(f):
        continue
    n += 1
    args += ['-itsoffset', str(by_scene[pl['scene']]['in_s']), '-c:v', 'libvpx-vp9', '-i', f]
    fc.append('[%d:v]scale=%d:%d[c%d]' % (n, W, H, n))
    fc.append('[%s][c%d]overlay=0:0:eof_action=pass:repeatlast=0[v%d]' % (prev, n, n))
    prev = 'v%d' % n

final = os.path.join(OUT, 'picture-lock.mp4')
args += ['-filter_complex', ';'.join(fc), '-map', '[%s]' % prev,
         '-c:v', 'libx264', '-crf', '23', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', final]
subprocess.run(args, check=True)
print('picture lock (%d overlays) ->' % n, final)
