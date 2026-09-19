#!/usr/bin/env python3
"""Read every machine strip back from a rendered MP4 and compare frame goldens.
Usage: check_geometry_render.py GOLDEN_FRAMES.csv RENDER.mp4
Extra strips may represent absent units, but may not reuse a golden's identity.
No programme pixels are inspected or printed by this check.
"""
import csv
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments'))
from live_overlay_strip import decode_gray, STRIP_X, STRIP_WIDTH, STRIP_HEIGHT

gold = {int(r['frame']):r for r in csv.DictReader(open(sys.argv[1]))}
meta = json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=height','-of','json',sys.argv[2]]))
y = int(meta['streams'][0]['height'])-14
data = subprocess.check_output(['ffmpeg','-v','error','-i',sys.argv[2],'-vf',f'crop={STRIP_WIDTH}:{STRIP_HEIGHT}:{STRIP_X}:{y}',
                                '-pix_fmt','gray','-f','rawvideo','pipe:1'])
size = STRIP_WIDTH*STRIP_HEIGHT
assert len(data)%size == 0
seen, fills, errors = set(), [], []
for i in range(len(data)//size):
    ordinal, counter, d1, d2 = decode_gray(data[i*size:(i+1)*size])
    if ordinal != i: errors.append((i,'ordinal',ordinal))
    if counter in gold:
        if counter in seen: errors.append((i,'duplicate',counter))
        seen.add(counter); r=gold[counter]
        want=(int(r['applied_d1']),int(r['applied_d2']))
        if (d1,d2)!=want: errors.append((i,counter,(d1,d2),want))
    else: fills.append((i,counter))
missing=sorted(gold.keys()-seen)
for error in errors: print('MISMATCH',error)
print('RENDER STRIPS:',len(seen),'golden frames;',len(fills),'extra fill slots;',len(errors),'mismatches; missing',missing)
raise SystemExit(bool(errors or missing))
