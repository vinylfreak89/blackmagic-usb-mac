#!/usr/bin/env python3
"""The owner's bottom definition, measured directly and dumbly (contract §1: "if a horizontal signal falls outside of
the variance of the normal left or right edge (and variance is important because horizontal timing aint perfect)
thats your headswitch band. sometimes on the right. sometimes the left.").

Per field of a unit, per row of the pass-through region, the row's ACTIVE EDGES: the first and last sample whose luma
rises above the row's own horizontal-blanking level. The blanking level is read from the row itself, from the samples
before the picture starts, so no level is assumed and nothing is fitted to a tape:
  base   = the median of the row's first 6 samples (the source's horizontal-blanking dip; measured luma 1-3 at 05:00
           and 2-8 at 35:00, and the pedestal ~11 on a recorded-black row)
  noise  = the field's regenerated blanking rows' luma std (their own noise, ~0.5), never a constant
  left   = the first sample >= base + 6*noise that begins a run of 8 such samples (8 = 0.6 us at 13.5 MHz, shorter
           than any picture feature and longer than a single-sample spike)
  right  = the last such sample of the last such run
A row with no run has no edges (flat/blank) and is reported as such.

Then the FIELD'S OWN VARIANCE of those edges over its body (the rows from top+20 to top+200, which are picture by
construction) as [min, max] of left and of right. A row whose left is below min(left) or above max(left), or whose
right is outside the same interval for right, falls OUTSIDE the field's horizontal-timing variance: the head-switch
band. The last row inside the variance is the picture bottom.

No threshold here is fitted to a capture: 6*noise and the 8-sample run are the row's own noise and the sampling
clock; the variance is the field's own.
Usage: edge_variance.py <capture> <out.csv> [--units 3,4,5] [--only] [--first N] [--panel DIR]"""
import sys, os, csv, argparse, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
# unit rows: field 1 pass-through 19..260 (NTSC 23..264), field 2 282..522 (286..526); blanking 7..15 / 270..278
FIELD={1:(19,261,7,16), 2:(282,523,270,279)}
RUN=8

def edges(y, base, thr):
    """first and last sample of the row's active span: runs of >=RUN samples above base+thr."""
    a = y > (base + thr)
    if not a.any(): return None, None, 0
    # runs of consecutive True
    d = np.diff(np.concatenate(([0], a.view(np.int8), [0])))
    starts = np.flatnonzero(d == 1); ends = np.flatnonzero(d == -1)
    keep = (ends - starts) >= RUN
    if not keep.any(): return None, None, 0
    return int(starts[keep][0]), int(ends[keep][-1] - 1), int(keep.sum())

def field_rows(R, f):
    a, b, ba, bb = FIELD[f]
    Y = R[a:b, 1::2].astype(np.float32)            # luma, 720 samples per row
    B = R[ba:bb, 1::2].astype(np.float32)          # the Shuttle's regenerated blanking rows
    return Y, a, float(B.mean()), float(max(B.std(), 0.3))

def measure(R, f):
    Y, row0, blank_mu, blank_sd = field_rows(R, f)
    thr = 6.0 * blank_sd
    rows = []
    for i in range(Y.shape[0]):
        y = Y[i]
        base = float(np.median(y[:6]))
        l, r, n = edges(y, base, thr)
        rows.append(dict(row=row0+i, line=row0+i+4, base=round(base,2), left=l, right=r, runs=n,
                         mean=round(float(y.mean()),2), std=round(float(y.std()),2)))
    return rows, blank_mu, blank_sd

def body_variance(rows, top_idx):
    """the field's own edge variance over rows that are picture by construction (top+20 .. top+200)"""
    body = [x for x in rows[top_idx+20:top_idx+201] if x['left'] is not None]
    if len(body) < 40: return None
    L = [x['left'] for x in body]; Rt = [x['right'] for x in body]
    return dict(lmin=min(L), lmax=max(L), rmin=min(Rt), rmax=max(Rt), n=len(body))

def summarise(rows, var):
    """the field's reading: picture bottom = the last row inside the field's own edge variance; the band = the rows
    after it that have edges and lie outside it; the clip = the last row with any edges at all."""
    if not var: return None
    idx = {r['row']: k for k, r in enumerate(rows)}
    inside = [r for r in rows if r['left'] is not None and
              var['lmin'] <= r['left'] <= var['lmax'] and var['rmin'] <= r['right'] <= var['rmax']]
    if not inside: return None
    top = inside[0]['row']; bottom = inside[-1]['row']
    withedges = [r for r in rows if r['left'] is not None]
    clip = withedges[-1]['row']
    band = [r for r in rows if r['row'] > bottom and r['left'] is not None]
    # how far outside the variance each band row sits, in samples: the separation the rule rests on
    def outby(r):
        dl = max(var['lmin'] - r['left'], r['left'] - var['lmax'], 0)
        dr = max(var['rmin'] - r['right'], r['right'] - var['rmax'], 0)
        return max(dl, dr)
    # the same figure for the rows inside the picture, to expose false positives
    inside_out = [outby(r) for r in rows[idx[top]:idx[bottom]+1] if r['left'] is not None]
    stray = [r['row'] for r in rows[idx[top]:idx[bottom]+1]
             if r['left'] is not None and outby(r) > 0]
    return dict(top=top, bottom=bottom, clip=clip, band=len(band),
                band_out_min=min((outby(r) for r in band), default=''),
                band_out_max=max((outby(r) for r in band), default=''),
                stray=len(stray), stray_max=max(inside_out, default=0),
                lmin=var['lmin'], lmax=var['lmax'], rmin=var['rmin'], rmax=var['rmax'], nbody=var['n'])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('cap'); ap.add_argument('out')
    ap.add_argument('--units', default=''); ap.add_argument('--only', action='store_true')
    ap.add_argument('--first', type=int, default=0); ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--summary', action='store_true', help='one row per field per unit: the reference')
    A = ap.parse_args()
    want = {int(x) for x in A.units.split(',') if x}
    N = [0]; buf = bytearray()
    out = open(A.out, 'w', newline=''); W = csv.writer(out)
    if A.summary:
        W.writerow(['unit','counter','field','class','top_line','bottom_line','clip_line','band_rows',
                    'band_out_min','band_out_max','stray_rows','stray_max','lmin','lmax','rmin','rmax','body_rows'])
    else:
        W.writerow(['unit','counter','field','row','line','base','left','right','runs','mean','std',
                    'lmin','lmax','rmin','rmax','inside'])
    def emit(u):
        i = N[0]; N[0] += 1
        if i < A.start: return
        if A.only and i not in want: return
        if A.first and i >= A.start + A.first: return
        c = int.from_bytes(u[4:6], 'little')
        R = np.frombuffer(u, np.uint8)[HDR:].reshape(LINES, LINE)
        for f in (1, 2):
            rows, bmu, bsd = measure(R, f)
            first = next((k for k, x in enumerate(rows) if x['left'] is not None), None)
            var = body_variance(rows, first) if first is not None else None
            if A.summary:
                sm = summarise(rows, var)
                if sm is None:
                    W.writerow([i, c, f, 'unmeasurable'] + ['']*13)
                else:
                    W.writerow([i, c, f, 'observed', sm['top']+4, sm['bottom']+4, sm['clip']+4, sm['band'],
                                sm['band_out_min'], sm['band_out_max'], sm['stray'], sm['stray_max'],
                                sm['lmin'], sm['lmax'], sm['rmin'], sm['rmax'], sm['nbody']])
                continue
            for x in rows:
                ins = ''
                if var and x['left'] is not None:
                    ins = int(var['lmin'] <= x['left'] <= var['lmax'] and var['rmin'] <= x['right'] <= var['rmax'])
                W.writerow([i, c, f, x['row'], x['line'], x['base'], x['left'], x['right'], x['runs'],
                            x['mean'], x['std'],
                            var['lmin'] if var else '', var['lmax'] if var else '',
                            var['rmin'] if var else '', var['rmax'] if var else '', ins])
        out.flush()
    # units are marker-delimited in the video endpoint's byte stream; hold at most one unit in memory
    def on_video(p):
        buf.extend(p)
        while True:
            i = buf.find(MARK)
            if i < 0: return
            if i > 0: del buf[:i]
            j = buf.find(MARK, 4)
            if j < 0: return
            if j == UNIT: emit(bytes(buf[:UNIT]))
            del buf[:j]
    walk_tagged(A.cap, on_video=on_video, progress=False)
    out.close(); print(f'units seen {N[0]}, rows written to {A.out}')

main()
