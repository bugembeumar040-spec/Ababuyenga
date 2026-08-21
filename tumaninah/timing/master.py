"""Render the upload master: 1920x1080, high bitrate, cards and plates native.

preview.py builds at 1280x720 with a preview bitrate — fine for checking timing,
not for upload. Here the overlays composite at their native 1920x1080 so the type
and the Arabic stay crisp; the watercolour is upscaled from 1376x768, which it
takes well.
"""
import csv, json, os, subprocess

W, H, FPS = 1920, 1080, 30
OUT = 'tumaninah/master'
FF = subprocess.run(['python3', '-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],
                    capture_output=True, text=True).stdout.strip()
os.makedirs(OUT, exist_ok=True)
rows = json.load(open('tumaninah/timing/placed.json'))

lst = os.path.join(OUT, 'frames.txt')
with open(lst, 'w') as f:
    for r in rows:
        p = os.path.abspath(os.path.join('tumaninah/images', r['file']))
        f.write("file '%s'\nduration %.3f\n" % (p, r['dur_s']))
    f.write("file '%s'\n" % p)

base = os.path.join(OUT, 'picture.mp4')
subprocess.run([FF, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                '-vf', 'scale=%d:%d:flags=lanczos:force_original_aspect_ratio=decrease,'
                       'pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=%d' % (W, H, W, H, FPS),
                '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                base], check=True)
print('picture ->', base, flush=True)

marks = list(csv.DictReader(open('tumaninah/timing/cards.csv')))
webm = {f.split('_')[0].split('-')[1]: f for f in os.listdir('tumaninah/overlays/webm')
        if f.startswith('card-')}
args = [FF, '-y', '-loglevel', 'error', '-i', base]
fc, prev, n = [], '0:v', 0
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

by = {r['scene']: r for r in rows}
for p in json.load(open('tumaninah/cards-src/plates.json')):
    f = 'tumaninah/overlays/plates/plate-scene-%s.webm' % p['scene']
    if not os.path.exists(f) or p['scene'] not in by:
        continue
    n += 1
    args += ['-itsoffset', str(by[p['scene']]['in_s']), '-c:v', 'libvpx-vp9', '-i', f]
    fc.append('[%d:v]scale=%d:%d[c%d]' % (n, W, H, n))
    fc.append('[%s][c%d]overlay=0:0:eof_action=pass:repeatlast=0[v%d]' % (prev, n, n))
    prev = 'v%d' % n

final = os.path.join(OUT, 'tumaninah-master.mp4')
args += ['-i', 'tumaninah/preview/mix.m4a',
         '-filter_complex', ';'.join(fc), '-map', '[%s]' % prev, '-map', '%d:a' % (n + 1),
         '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p',
         # the encoder defaulted to 96 kHz, which YouTube only resamples; 48 is standard
         '-c:a', 'aac', '-ar', '48000', '-b:a', '256k', '-shortest', '-movflags', '+faststart', final]
subprocess.run(args, check=True)
print('master (%d overlays) ->' % n, final, flush=True)
