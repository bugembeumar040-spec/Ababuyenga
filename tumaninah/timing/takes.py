"""Pick the 13 final takes out of the 34 uploads, and build the voiceover.

The uploads total 49:18 — roughly double the runtime — so they include alternates.
The transcript's duration table is the only statement of which takes are final,
so the set is recovered by fitting it: the increasing subsequence of 13 files
(chronological, since the recording stamp is script order) whose durations best
match the table.

Rows 6-9 do not match any upload cleanly and are the ones to check by ear.
"""
import importlib.util, json, os, subprocess, sys

UPLOADS = sys.argv[1] if len(sys.argv) > 1 else \
    '/root/.claude/uploads/b6b8a957-a047-5e7c-b664-115ea9a25bf7'
TABLE = [144, 108, 147, 34, 135, 93, 89, 114, 73, 23, 117, 108, 79]

spec = importlib.util.spec_from_file_location('mp3dur', 'tumaninah/timing/mp3dur.py')
mp3dur = importlib.util.module_from_spec(spec); spec.loader.exec_module(mp3dur)

files = sorted((f for f in os.listdir(UPLOADS) if f.endswith('.mp3')),
               key=lambda f: f.split('Benjamin')[1][:15])
durs = [(f, mp3dur.duration(os.path.join(UPLOADS, f))[0]) for f in files]

N, K, INF = len(durs), len(TABLE), float('inf')
dp = [[INF] * (K + 1) for _ in range(N + 1)]
ch = [[None] * (K + 1) for _ in range(N + 1)]
for i in range(N + 1):
    dp[i][0] = 0
for i in range(1, N + 1):
    for k in range(1, K + 1):
        take = dp[i - 1][k - 1] + abs(durs[i - 1][1] - TABLE[k - 1])
        if take <= dp[i - 1][k]:
            dp[i][k], ch[i][k] = take, 'T'
        else:
            dp[i][k], ch[i][k] = dp[i - 1][k], 'S'
i, k, sel = N, K, []
while k > 0:
    if ch[i][k] == 'T':
        sel.append(i - 1); k -= 1
    i -= 1
sel.reverse()

total = 0.0
for r, idx in enumerate(sel):
    f, du = durs[idx]; total += du
    flag = '  <- check by ear' if abs(du - TABLE[r]) > 2 else ''
    print('%2d  want %3ds  got %6.2fs  %+5.1f  %s%s' % (r + 1, TABLE[r], du, du - TABLE[r], f[:46], flag))
print('\nconcat %.1fs = %d:%02d   table %ds' % (total, total // 60, total % 60, sum(TABLE)))

json.dump([durs[i][0] for i in sel], open('tumaninah/timing/takes.json', 'w'), indent=1)

if '--build' in sys.argv:
    FF = subprocess.run(['python3', '-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],
                        capture_output=True, text=True).stdout.strip()
    os.makedirs('tumaninah/preview', exist_ok=True)
    lst = 'tumaninah/preview/audio.txt'
    open(lst, 'w').write('\n'.join("file '%s'" % os.path.join(UPLOADS, durs[i][0]) for i in sel))
    subprocess.run([FF, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-c:a', 'aac', '-b:a', '160k', 'tumaninah/preview/voiceover.m4a'], check=True)
    print('built tumaninah/preview/voiceover.m4a')
