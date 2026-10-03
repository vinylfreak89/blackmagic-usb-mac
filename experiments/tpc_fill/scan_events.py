# For every event the live sidecar shows (video events and audio-only steps), save the surrounding stretch of the target's raw file
# and describe it exactly: units present/missing, resync intervals, where in the file.
import sys, json, csv, os, numpy as np
sys.path.insert(0, '.')
from region import *
T = os.environ['TARGET']      # the target capture's raw file
csv.field_size_limit(1 << 30)
rows = []; hdr = None
with open('live_sidecar.csv', newline='') as f:
    for line in f:
        if line.startswith('#'): continue
        if hdr is None: hdr = next(csv.reader([line])); continue
        rows.append(line.rstrip('\n').split(',', 40)[:40])
ix = {h: i for i, h in enumerate(hdr[:40])}
# event rows: any row that is not a plain unit, or carries an audio step
marks = [i for i, r in enumerate(rows) if r[ix['drop_reason']] != 'None' or r[ix['audio_step_samples']] not in ('', '0')]
groups = []
for i in marks:
    if groups and i - groups[-1][-1] <= 400: groups[-1].append(i)      # events within ~13 s share one stretch
    else: groups.append([i])
print(len(marks), 'event rows in', len(groups), 'stretches', flush=True)
SIZE = os.path.getsize(T); PER = SIZE / len(rows); out = []
for g, grp in enumerate(groups):
    lo = max(0, int(grp[0] * PER) - 130_000_000); hi = min(SIZE, int(grp[-1] * PER) + 300_000_000)
    p0, b = read_region(T, lo, hi - lo); open('ev/t%02d.bin' % g, 'wb').write(b)
    R = Region(b, p0)
    # units
    whole = [(off, c) for off, c, fm, ok in R.marks if ok and fm == 0xe801]
    vgaps = []
    for (o1, c1), (o2, c2) in zip(whole, whole[1:]):
        if o2 - o1 != UNIT or (c2 - c1) % 65536 != 1:
            vgaps.append(dict(last_whole=c1, next_whole=c2, bytes_between=o2 - (o1 + UNIT), missing=(c2 - c1) % 65536 - 1, stream_from=o1 + UNIT, stream_to=o2,
                              marks_between=[(o, c, hex(fm)) for o, c, fm, ok in R.marks if o1 + UNIT <= o < o2]))
    # resyncs
    agaps = []
    for (i1, s1, c1), (i2, s2, c2) in zip(R.resyncs, R.resyncs[1:]):
        n = s2 - s1; k = (c2 - c1) % 65536
        if k != 1 or n not in (1601, 1602): agaps.append(dict(from_counter=c1, to_counter=c2, samples_between=n, counters=k, rec_from=i1, rec_to=i2, sample_from=s1, sample_to=s2))
    d = dict(group=g, rows=grp, first_time='%d:%02d' % (grp[0] / 29.97 // 60, grp[0] / 29.97 % 60), file_from=p0, file_bytes=len(b), units=[whole[0][1], whole[-1][1]],
             resyncs=[R.resyncs[0][2], R.resyncs[-1][2]], video_gaps=vgaps, audio_gaps=agaps, sizes_v=sorted(set(R.recs[k][7] for _, k in R.vpk)), sizes_a=sorted(set(R.recs[k][7] for _, k in R.apk)))
    out.append(d); json.dump(out, open('ev/events.json', 'w'), indent=1)
    print(g, d['first_time'], 'units', d['units'], 'video gaps', [(x['last_whole'], x['next_whole'], x['bytes_between'], x['missing']) for x in vgaps], 'audio gaps', [(x['from_counter'], x['to_counter'], x['samples_between']) for x in agaps], 'pkt sizes', d['sizes_v'], d['sizes_a'], flush=True)
print('done')
