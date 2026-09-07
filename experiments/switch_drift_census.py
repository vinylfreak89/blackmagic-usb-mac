#!/usr/bin/env python3
"""The head switch's travel along the line vs the one-row changes of S (owner, 2026-09-07: "did you correlate the horizontal
skew with the line vanishing?"). From an engine record with the disc_x column ('row:blank_x/lead_end/transient_x' for
S-1|S|S+1): per field, at every unit-to-unit change of S - top (the observed band height), whether the top moved, and the
horizontal position of the timing discontinuity at the switch row in both units (its drift, and whether it fell off the
row's edge: no position in one unit). Counts only. Usage: switch_drift_census.py <sg.csv> [--from-counter N]"""
import sys, csv, argparse, collections
ap=argparse.ArgumentParser(); ap.add_argument('sg'); ap.add_argument('--from-counter',type=int,default=0); A=ap.parse_args()
rows=[r for r in csv.DictReader(open(A.sg)) if int(r['counter'])>=A.from_counter and int(r['top'])>=0 and int(r['S_first_shifted'])>=0]
def pos(r):
    """the discontinuity's x at the switch row S: the blanking start if any, else the leading-run end, else the transient"""
    for part in (r.get('disc_x') or '').split('|'):
        if not part or ':' not in part: continue
        row,vals=part.split(':'); 
        if int(row)!=int(r['S_first_shifted']): continue
        bx,le,tx=[int(v) for v in vals.split('/')]
        return bx if bx>=0 else (le if le>=0 else (tx if tx>=0 else None))
    return None
for f in ('1','2'):
    R=sorted([r for r in rows if r['field']==f],key=lambda r:int(r['counter']))
    h=lambda r:int(r['S_first_shifted'])-int(r['top'])
    ch=[(a,b) for a,b in zip(R,R[1:]) if h(a)!=h(b)]
    cls=collections.Counter(); drift=[]
    for a,b in ch:
        dt=int(b['top'])-int(a['top']); pa,pb=pos(a),pos(b)
        k=('top moved' if dt else 'top still', 'position in both' if (pa is not None and pb is not None) else ('position in one' if (pa is not None or pb is not None) else 'position in neither'))
        cls[k]+=1
        if pa is not None and pb is not None: drift.append(pb-pa)
    # the drift of the position between consecutive units where S did NOT change (the travel along the line)
    same=[(pos(b)-pos(a)) for a,b in zip(R,R[1:]) if h(a)==h(b) and pos(a) is not None and pos(b) is not None]
    withpos=sum(1 for r in R if pos(r) is not None)
    print(f'field {f}: units {len(R)}, switch row with a measured discontinuity position {withpos}; height changes {len(ch)}')
    for k,v in sorted(cls.items(),key=lambda x:-x[1]): print('   ',v,k)
    if same: 
        import statistics; print(f'   position drift per unit, S unchanged: n={len(same)} median {statistics.median(same):.0f} |drift|>24 in {sum(1 for d in same if abs(d)>24)}')
    if drift: print(f'   position drift at height changes (both measured): n={len(drift)} values {sorted(drift)[:20]}')
