#!/usr/bin/env python3
"""Falsification probe, NOT the production box observer.

Try a scale-relative, two-class partition of row spread, then require edge
anchoring and a majority of structured rows between the anchors. No extent
is used for placement. The synthetic negative has texture on EVERY row.
Raw acquisition uses only the existing strict CAP1 walker, not oracle measures.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'experiments' / 'geometry_oracle'))
from oracle import walk_exact_units


def partition(field):
    # SMPTE blanking duration, rounded to 147 BT.601 samples: omit that much
    # at EACH end as a conservative diagnostic aperture, not a measured edge.
    # Does not promise immunity to an interval displaced into the interior.
    v = field[:, 147:720-147].astype(float).var(axis=1)
    if np.any(v <= 0) or np.all(v == v[0]):
        return dict(box=False, reason='no two positive spread classes')
    s = np.sort(np.log(v))
    p = np.cumsum(s)
    n = np.arange(1, len(s))
    # Least within-class squared error in log variance. A multiplicative
    # gain adds a constant in log space, preserving the partition before
    # quantization. Two classes means proposed band versus content, not a
    # fitted brightness cut. The partition's existence is NOT its validation.
    score = p[:-1]**2/n + (p[-1]-p[:-1])**2/(len(s)-n)
    k = int(np.argmax(score))
    cut = float(np.exp((s[k]+s[k+1])/2))
    hi = v > cut
    rows = np.flatnonzero(hi)
    if not len(rows):
        return dict(box=False, reason='no structured candidate')
    first, last = int(rows[0]), int(rows[-1])
    sustained = int(hi[first:last+1].sum()) > (last-first+1)/2
    return dict(box=bool(first > 0 and last < len(v)-1 and sustained),
                first=first, last=last, threshold_variance=cut,
                structured=int(hi.sum()), sustained=bool(sustained),
                first_variance=float(v[0]), last_variance=float(v[-1]))


def controls():
    # Constructed controls; these values describe signals, NOT decision knobs.
    x = np.arange(720)
    texture = ((x*13) % 23 - 11).astype(float)
    small_noise = (x % 2)*2-1
    boxed = np.tile(64+small_noise, (240, 1)).astype(float)
    boxed[30:210] += 4*texture
    unboxed = boxed.copy()
    unboxed[:30] += texture
    unboxed[210:] += texture
    one_end = boxed.copy()
    one_end[210:] += 4*texture
    results = {
        'constructed_box': partition(boxed),
        'same_box_gain_quarter': partition(boxed/4),
        'one_end_only': partition(one_end),
        'full_picture_textured_on_every_row': partition(unboxed),
    }
    results['negative_rejected'] = not results['full_picture_textured_on_every_row']['box']
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--capture', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    result = dict(method='diagnostic log-variance partition, not production',
                  controls=controls(), units=[])
    if args.capture:
        def consume(unit, ordinal):
            a = np.frombuffer(unit, np.uint8)[48:].reshape(525,1440)[:,1::2]
            result['units'].append(dict(counter=int.from_bytes(unit[4:6], 'little'),
                ordinal=ordinal, fields=[partition(a[19:259]), partition(a[282:522])]))
        walk_exact_units(args.capture, consume)
    with args.output.open('x') as out:
        json.dump(result, out, indent=2)
    print(json.dumps(result['controls'], indent=2))
    if result['units']:
        eligible = [r for r in result['units'] if r['counter'] >= 6667]
        print(json.dumps(dict(exact=len(result['units']), registerable=len(eligible),
            candidate_box_fields=[sum(r['fields'][f]['box'] for r in eligible) for f in (0,1)],
            candidate_both=sum(all(f['box'] for f in r['fields']) for r in eligible))))
    # Nonzero status is the deciding falsification, not a passing box test.
    return 0 if result['controls']['negative_rejected'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
