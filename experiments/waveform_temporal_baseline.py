#!/usr/bin/env python3
"""One-allowance temporal-shape BASELINE, not a registration engine.

Hypothesis under test: after suppressing reversals no larger than epsilon,
every internal turning point visits one of the row's two extreme-level bands.
Require one full excursion (low-high-low or high-low-high); window endpoints
are not assumed to be turning points. Candidate levels are min/max, NOT a
qualified identification of blanking. There is deliberately no fitted level,
amplitude, duration, chroma, symmetry, pulse-count (>1) or location clause.

Disclosed experimental choices: epsilon is an absolute luma-code allowance;
sweep 2,4,8,16 rather than tune to positive extrema. Disjoint endpoint bands
require range > 2*epsilon. Extrema suppression, endpoint-band matching and
minimum complete excursion are model choices, not owner-supplied equations.
Intermediate holds and picture shaped like a pulse can pass: this is weaker
than a full identity test, and its false positives must remain visible.

Evaluation consumes manually labelled rows, never constructs truth. NPZ:
luma[N,W]; CSV in the same order: capture,counter,line,label,sha256 (optional
reason). Labels positive/negative/unresolved. Results belong OUTSIDE git.
No CEA-608 decoder is called. No comb or geometry calculation is performed.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np


def temporal_shape(row, epsilon):
    """Return bool plus explicit reason; all arithmetic is signed floating point."""
    y = np.asarray(row, dtype=float)
    if y.ndim != 1 or len(y) < 3 or not np.isfinite(y).all():
        raise ValueError('expected finite one-dimensional row with >=3 samples')
    if not np.isfinite(epsilon) or epsilon <= 0:
        raise ValueError('epsilon must be positive and finite')
    lo, hi = float(y.min()), float(y.max())
    if hi-lo <= 2*epsilon:
        return False, 'bands_not_separable'

    # Confirm a direction only after an excursion larger than epsilon. Record
    # its extreme when the reverse excursion becomes larger than epsilon.
    peak = trough = float(y[0])
    peak_i = trough_i = 0
    direction = 0
    vertices = []
    for i in range(1, len(y)):
        v = float(y[i])
        if direction == 0:
            if v > peak: peak, peak_i = v, i
            if v < trough: trough, trough_i = v, i
            if v-trough > epsilon:
                vertices.append((trough_i,trough)); direction=1
                peak,peak_i=v,i
            elif peak-v > epsilon:
                vertices.append((peak_i,peak)); direction=-1
                trough,trough_i=v,i
        elif direction == 1:
            if v > peak: peak,peak_i=v,i
            elif peak-v > epsilon:
                vertices.append((peak_i,peak)); direction=-1
                trough,trough_i=v,i
        else:
            if v < trough: trough,trough_i=v,i
            elif v-trough > epsilon:
                vertices.append((trough_i,trough)); direction=1
                peak,peak_i=v,i
    vertices.append((peak_i,peak) if direction == 1 else (trough_i,trough))
    bands=[]
    for i, v in vertices:
        band=0 if v <= lo+epsilon else 1 if v >= hi-epsilon else None
        # A cut transition at the window edge does not assert a turning point.
        if band is None and i in (0,len(y)-1): continue
        if band is None:
            return False,f'intermediate_reversal:x={i},y={v:g},lo={lo:g},hi={hi:g}'
        if not bands or bands[-1] != band: bands.append(band)
    if len(bands)<3: return False,'no_complete_excursion'
    return True,'two_band_excursions'


def selftest():
    def r(values): return np.asarray(values,dtype=np.uint8)
    checks=[
        ('flat',r([2]*30),False),
        ('small noise',r([1,2,3,2]*10),False),
        ('pulse',r([2]*8+[30,60,90]+[120]*8+[90,60,30]+[2]*8),True),
        ('start high',r([120]*8+[90,60,30]+[2]*8+[30,60,90]+[120]*8),True),
        ('single transition unavailable cycle',r([2]*8+[30,60,90]+[120]*8),False),
        ('middle turnback',r([2]*8+[30,60,40,60,90]+[120]*8+[90,60,30]+[2]*8),False),
        ('unequal peaks',r([2]*8+[120]*8+[2]*8+[60]*8+[2]*8),False),
        ('small reversal',r([2]*8+[30,60,58,90]+[120]*8+[90,60,30]+[2]*8),True),
        ('cut ramps',r([40,60,90]+[120]*8+[90,60,30]+[2]*8+[30,60,90]+[120]*8+[90,60,40]),True),
    ]
    for name,row,expected in checks:
        got=temporal_shape(row,4)[0]
        assert got==expected,(name,expected,got)
        # Time reversal is an invariant of this shape-only experiment.
        assert temporal_shape(row[::-1],4)[0]==expected,('reversal',name)
    assert temporal_shape(r([2]*8+[120]*8+[2]*8),4)==temporal_shape(r([12]*8+[130]*8+[12]*8),4)
    print(f'SELFTEST PASS {len(checks)} named cases + reversals + level-translation control')


def extract(path, counters, output):
    """Preserve selected raw units with the existing validated streaming reader.

    Counters select inspection material, never labels. This helper is limited
    to short e801 captures without counter wrap; duplicate selected counters
    are refused instead of silently joining different tape times.
    """
    from capture_render import TaggedVideoUnits
    from packet_capture_reader import walk_tagged
    selected = {}
    wanted = set(counters)

    def take(index, counter, unit, state, captured):
        if counter not in wanted or state != 'Exact':
            return
        if counter in selected:
            raise ValueError('selected counter repeated; use a shorter capture')
        uyvy = np.frombuffer(unit[48:], np.uint8).reshape(525, 1440).copy()
        selected[counter] = (index, uyvy)

    splitter = TaggedVideoUnits(take, copy_units=True)
    stats = walk_tagged(path, on_video=splitter.feed, progress=False)
    splitter.finish()
    stats.assert_lossless()
    missing = wanted - selected.keys()
    if missing:
        raise ValueError(f'selected exact counters absent: {sorted(missing)}')
    ordered = sorted(selected, key=lambda c: selected[c][0])
    np.savez_compressed(output, counter=ordered,
                        index=[selected[c][0] for c in ordered],
                        uyvy=[selected[c][1] for c in ordered])
    print(json.dumps(dict(path=str(path), exact=splitter.exact_units,
                          short=splitter.short_units, absent=splitter.absent_units,
                          selected=ordered)))


def score(rows_path, labels_path, output, allowances):
    rows=np.load(rows_path)['luma']
    with open(labels_path) as f: labels=list(csv.DictReader(f))
    if len(rows)!=len(labels): raise ValueError('row/label count mismatch')
    for row,lab in zip(rows,labels):
        if lab['label'] not in ('positive','negative','unresolved'):
            raise ValueError('invalid label')
        if hashlib.sha256(row.tobytes()).hexdigest()!=lab['sha256']:
            raise ValueError('row/label hash mismatch')
    results=[]
    for eps in allowances:
        for row,lab in zip(rows,labels):
            asserted,reason=temporal_shape(row,eps)
            results.append({**lab,'epsilon':eps,'asserted':int(asserted),'reason_code':reason})
    with open(output,'w') as f:
        w=csv.DictWriter(f,fieldnames=list(results[0])); w.writeheader(); w.writerows(results)
    for eps in allowances:
        for cap in sorted({r['capture'] for r in results}):
            cohort=[r for r in results if r['epsilon']==eps and r['capture']==cap]
            counts={}
            for lab,prefix in [('positive','TP'),('negative','FP'),('unresolved','unresolved_assert')]:
                a=[r for r in cohort if r['label']==lab]
                counts[prefix]=sum(r['asserted'] for r in a)
                counts[{'positive':'FN','negative':'TN','unresolved':'unresolved_reject'}[lab]]=len(a)-counts[prefix]
            p=counts['TP']+counts['FN']; n=counts['TN']+counts['FP']
            print(json.dumps(dict(capture=cap,epsilon=eps,**counts,
                sensitivity=counts['TP']/p if p else None,
                specificity=counts['TN']/n if n else None,
                accuracy=(counts['TP']+counts['TN'])/(p+n) if p+n else None)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--selftest',action='store_true')
    p.add_argument('--rows',type=Path); p.add_argument('--labels',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--extract',type=Path)
    p.add_argument('--counters',type=int,nargs='+')
    p.add_argument('--allowances',type=float,nargs='+',default=[2,4,8,16])
    args=p.parse_args()
    if args.selftest: selftest()
    elif args.extract:
        if not args.counters or not args.output: p.error('extract needs counters and output')
        extract(args.extract,args.counters,args.output)
    elif not all((args.rows,args.labels,args.output)): p.error('supply rows, labels and output')
    else: score(args.rows,args.labels,args.output,args.allowances)
