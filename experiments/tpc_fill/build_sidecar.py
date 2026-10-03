# The sidecar for the filled capture: the live rows, with each gap's rows replaced by rows measured from a replay of the filled stretch,
# every unit present with its counter, no missing-audio steps, ordinals consecutive, and the audio/video offset column without the gaps' steps.
import sys, csv, json, pickle, glob
csv.field_size_limit(1 << 30)
def load(fn):
    rows = []; hdr = None; pre = []
    for line in open(fn):
        if line.startswith('#'): pre.append(line); continue
        if hdr is None: hdr = line.rstrip('\n').split(','); continue
        rows.append(line.rstrip('\n').split(','))
    return pre, hdr, rows
EV = json.load(open('ev/events.json'))
pre, hdr, live = load('live_sidecar.csv'); ix = {h: i for i, h in enumerate(hdr)}
CE, OC, DR, RES, STEP, ORD, FTU, EP = (ix[k] for k in ('counter_extended', 'observed_counter', 'drop_reason', 'audio_residual_ticks', 'audio_step_samples', 'ordinal', 'frame_top_unit', 'epoch'))
row_of = {int(r[CE]): i for i, r in enumerate(live) if r[CE]}
spans = []      # (first live row to replace, last live row to replace, replacement rows)
report = []
for f in sorted(glob.glob('ev/m[0-9][0-9].pkl')):
    g = int(f[4:6]); mods = pickle.load(open(f, 'rb'))
    if not mods: continue
    _, h2, rep = load('ev/n%02d.csv' % g); assert h2 == hdr
    rp = [r for r in rep if r[CE]]
    # offset between the replay's extended counters and the live ones: a whole number of 16-bit wraps, picked by where the stretch sits in the recording
    meta = EV[g]; near = None
    for k in range(meta['rows'][0], 0, -1):
        if live[k][CE]: near = int(live[k][CE]); break
    c_first = int(rp[0][CE]); D = round((near - c_first) / 65536) * 65536
    assert c_first + D in row_of and abs(c_first + D - near) < 3000, ('stretch does not line up with the live sidecar', g, c_first, D, near)
    rpd = {int(r[CE]) + D: r for r in rp}
    for m in mods:
        rp_ = m['rep']; cs = []
        gaps16 = [(a, b) for a, b, *_ in rp_.get('video_gaps_final', [])] + [(a, b) for a, b, n in rp_.get('audio_gaps', [])]
        # extended counters of the span: from the unit after the earliest "last good" to three units after the latest "next good"
        def ext(c16):
            near = [c for c in rpd if c % 65536 == c16 % 65536]; assert near, ('unit not in the replay', c16); return near[0]
        lo = min(ext(a) for a, b in gaps16) + 1; hi = max(ext(b) for a, b in gaps16) + 3
        new = []
        for c in range(lo, hi + 1):
            assert c in rpd, ('the filled stretch has no row for unit', c)
            assert rpd[c][DR] == 'None' and rpd[c][STEP] in ('', '0'), ('replay row is not a clean unit', c, rpd[c][DR], rpd[c][STEP])
            new.append((c, list(rpd[c])))
        # live rows covered: from the row after unit lo-1 to the row of unit hi
        r0 = row_of[lo - 1] + 1; r1 = row_of[hi]
        # the unit before the span must exist in both, to carry the audio/video offset level across
        spans.append(dict(r0=r0, r1=r1, new=new, D=D, anchor=lo - 1, anchor_replay_res=rpd[lo - 1][RES], name=rp_['name']))
        report.append(dict(cluster=rp_['name'], units=[lo, hi], live_rows_replaced=r1 - r0 + 1, rows_written=len(new), live_kinds=sorted(set(live[k][DR] for k in range(r0, r1 + 1)))))
spans.sort(key=lambda s: s['r0'])
for a, b in zip(spans, spans[1:]): assert a['r1'] < b['r0'], ('spans overlap', a['name'], b['name'])
out = []; pos = 0; removed = 0      # removed: ticks taken out of the offset column so far (the gaps' steps and the live session's re-anchors)
last_flat = None
def keep(k):
    # a live row, with the offset column continued on the level it was on (the usual jitter is a few ticks; a larger move is a step to remove)
    global removed, last_flat
    r = list(live[k])
    if r[RES]:
        v = int(r[RES]) - removed
        if last_flat is not None and abs(v - last_flat) > 40: removed += v - last_flat; v = last_flat
        r[RES] = str(v); last_flat = v
    if r[STEP] not in ('', '0') and k > 5: r[STEP] = '0'
    out.append(r)
for s in spans:
    for k in range(pos, s['r0']): keep(k)
    assert s['anchor_replay_res'] != '' and last_flat is not None
    anchor_flat = int(out[-1][RES]) if out[-1][CE] == str(s['anchor']) and out[-1][RES] else last_flat
    K = anchor_flat - int(s['anchor_replay_res'])      # replay offset level -> the level the live column is on
    for c, r in s['new']:
        r[CE] = str(c)
        if r[FTU]: r[FTU] = str(int(r[FTU]) + s['D'])
        r[EP] = live[s['r0'] - 1][EP]
        if r[RES]: r[RES] = str(int(r[RES]) + K); last_flat = int(r[RES])
        r[STEP] = '0'; out.append(r)
    pos = s['r1'] + 1
for k in range(pos, len(live)): keep(k)
# ordinals: consecutive from the first row's
o0 = int(out[0][ORD])
for i, r in enumerate(out): r[ORD] = str(o0 + i)
# checks
cs = [int(r[CE]) for r in out[3:] if r[CE]]; steps = [(a, b) for a, b in zip(cs, cs[1:]) if b - a != 1]
kinds = {}
for r in out[3:]: kinds[r[DR]] = kinds.get(r[DR], 0) + 1
resv = [int(r[RES]) for r in out[3:] if r[RES]]
print('rows %d -> %d | counter steps after the start rows: %s | row kinds after the start rows: %s | audio steps left: %d | offset column range %d..%d | rows without an offset: %d'
      % (len(live), len(out), steps[:5], kinds, sum(1 for r in out[3:] if r[STEP] not in ('', '0')), min(resv), max(resv), sum(1 for r in out[3:] if not r[RES])))
with open('filled_sidecar.csv', 'w') as f:
    for l in pre: f.write(l)
    f.write(','.join(hdr) + '\n')
    for r in out: f.write(','.join(r) + '\n')
json.dump(report, open('ev/sidecar_report.json', 'w'), indent=1)
for x in report: print(x)
