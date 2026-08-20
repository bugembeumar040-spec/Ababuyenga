#!/usr/bin/env python3
"""Print the next N pending scenes, so a batch is never generated twice."""
import json, sys

n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
done = {l.strip() for l in open('tumaninah/done.txt') if l.strip()}
reqs = json.load(open('tumaninah/manifest.json'))['requests']
pending = [r for r in reqs if r['scene'] not in done]

print("pending: %d  |  est $%.2f at 0.0375/image\n" % (len(pending), 0.0375 * len(pending)))
for r in pending[:n]:
    print("### %s | %s" % (r['scene'], r['file'].replace('.png', '.jpg')))
    print(r['params']['el_prompt'])
    print()
