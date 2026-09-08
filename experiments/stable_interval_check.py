#!/usr/bin/env python3
"""The owner's invariant as a TEST (never in the builder): on the commercial tape every unit from counter-based ordinal 551
onward (counter >= 6593) is a perfectly stable picture, so a geometry record must be constant there wherever it is measurable.
Reads an engine record (switch_geometry.py CSV) and prints, per field, over the stable interval: the histogram of top,
S, crop_last (top+239 clipped -- the CROP's last line, NOT the measured picture bottom, which is the row
above the switch line by contract rule 3), the unit-to-unit changes of each, and the unmeasurable units. Exit 1 if any measurable
top or S differs from the interval's modal value by more than the stated tolerance (S: 1 row, the partial-line ambiguity;
top: 0). Usage: stable_interval_check.py <sg.csv> [--from-counter 6593] [--clip 262,525]"""
import sys, csv, argparse, collections
ap=argparse.ArgumentParser(); ap.add_argument('sg'); ap.add_argument('--from-counter',type=int,default=6593); ap.add_argument('--clip',default='262,525'); A=ap.parse_args()
clip={ '1':int(A.clip.split(',')[0]), '2':int(A.clip.split(',')[1]) }
rows=[r for r in csv.DictReader(open(A.sg)) if int(r['counter'])>=A.from_counter]
for r in rows:   # the current record names the top switch line T; the earlier records named S
    if 'S_first_shifted' not in r: r['S_first_shifted']=r.get('T','-1') or '-1'
print(f'stable interval: counter >= {A.from_counter}: {len({r["unit"] for r in rows})} units')
bad=0
for f in ('1','2'):
    R=sorted([r for r in rows if r['field']==f],key=lambda r:int(r['counter']))
    tops=[int(r['top']) for r in R]; Ss=[int(r['S_first_shifted']) for r in R]
    meas=[(t,s) for t,s in zip(tops,Ss) if t>=0]
    unm=[r['counter'] for r,t in zip(R,tops) if t<0]
    mt=collections.Counter(t for t,_ in meas).most_common(1)[0][0] if meas else None
    ms=collections.Counter(s for _,s in meas if s>=0).most_common(1)[0][0] if meas else None
    bots=[min(t+239,clip[f]) if t>=0 else -1 for t in tops]
    print(f'field {f}: measurable {len(meas)}/{len(R)}; unmeasurable units (counters): {len(unm)} {unm[:20]}{"..." if len(unm)>20 else ""}')
    print(f'  top  {dict(collections.Counter(tops).most_common())}   mode {mt}')
    print(f'  S    {dict(collections.Counter(Ss).most_common())}   mode {ms}')
    print(f'  crop_last {dict(collections.Counter(bots).most_common())}   (top+239, the crop window, not the measured picture bottom)')
    print(f'  how  {dict(collections.Counter(r["how"] for r in R).most_common())}')
    ch=lambda seq:[(R[i]['counter'],a,b) for i,(a,b) in enumerate(zip(seq,seq[1:])) if a!=b and a>=0 and b>=0]
    ct,cs,cb=ch(tops),ch(Ss),ch(bots)
    print(f'  measurable-to-measurable changes: top {len(ct)} {ct[:10]} | S {len(cs)} {cs[:10]} | crop_last {len(cb)} {cb[:10]}')
    offt=[(R[i]['counter'],t) for i,t in enumerate(tops) if t>=0 and t!=mt]; offs=[(R[i]['counter'],s) for i,s in enumerate(Ss) if s>=0 and abs(s-ms)>1]
    noS=[R[i]['counter'] for i,(t,s) in enumerate(zip(tops,Ss)) if t>=0 and s<0]
    print(f'  top != mode: {len(offt)} {offt[:20]} | |S - mode| > 1: {len(offs)} {offs[:20]} | measurable top but no S: {len(noS)} {noS[:10]}')
    bad+=len(offt)+len(offs)
print('STABLE_INTERVAL_VIOLATIONS',bad); sys.exit(1 if bad else 0)
