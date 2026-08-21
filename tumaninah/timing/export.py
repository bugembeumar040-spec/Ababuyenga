import csv, json

rows = json.load(open('tumaninah/timing/placed.json'))
tl = json.load(open('tumaninah/timing/timeline.json'))
ts = lambda s: '%d:%05.2f' % (s // 60, s % 60)

with open('tumaninah/timing/shotlist.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['cut', 'scene', 'in', 'out', 'dur_s', 'timed_from', 'pack_chapter', 'file', 'vo'])
    for r in rows:
        w.writerow([r['cut_order'], r['scene'], ts(r['in_s']), ts(r['out_s']), r['dur_s'],
                    'spoken word' if r['has_audio'] else 'GAP - no audio',
                    '%s · %s' % (r['chapter'], r['chapter_title']), r['file'], r['vo']])

with open('tumaninah/timing/SHOTLIST.md', 'w') as f:
    T = tl['total']
    f.write('# Ṭumaʾnīnah — image timing\n\n')
    f.write('116 frames against the recorded voiceover. Runtime **%d:%02d** from 14 takes.\n\n'
            % (T // 60, T % 60))
    f.write('`in` is a measured word timestamp for the %d frames whose line is in the audio.\n'
            'The %d marked **GAP** sit in stretches of script that were never recorded — they\n'
            'are spaced between their neighbours and will re-time once that audio exists.\n\n'
            % (sum(1 for r in rows if r['has_audio']), sum(1 for r in rows if not r['has_audio'])))
    f.write('| # | in | out | dur | scene | timed from | frame | line |\n|--:|--|--|--:|--|--|--|--|\n')
    for r in rows:
        f.write('| %d | `%s` | `%s` | %.1fs | %s | %s | `%s` | %s |\n' % (
            r['cut_order'], ts(r['in_s']), ts(r['out_s']), r['dur_s'], r['scene'],
            'word' if r['has_audio'] else '**gap**', r['file'], r['vo'].replace('|', '\\|')[:80]))
print('exported', len(rows), 'shots')
