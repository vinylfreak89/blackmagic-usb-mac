#!/usr/bin/env python3
"""Unit-by-unit agreement between the engine's record (switch_geometry.py CSV) and the harness reference (contract v3):
per field: top vs picture_top_line; S vs switch_first_line (S is the first row entirely the other head; the switch
lands in S or S-1, so |S - switch_first_line| <= 1 is agreement within the partial ambiguity, 0 exact); band vs band.
Prints histograms of the differences and lists the units outside them. Usage: compare_records.py <sg.csv> <reference.csv> [--repair-slots]
(--repair-slots: the engine ran with --repair (fields re-paired one later); the reference's slot 1 = engine field 2 of the previous unit, slot 2 = engine field 1)"""
import sys, csv, collections, argparse
ap=argparse.ArgumentParser(); ap.add_argument('sg'); ap.add_argument('ref'); ap.add_argument('--repair-slots',action='store_true'); A=ap.parse_args()
R={int(r['ordinal']):r for r in csv.DictReader(open(A.ref))}
# join on the device counter, never on the engine's exact-unit index: on a capture with device-short or skipped units
# the engine's index and the reference's counter-based ordinal diverge (commercial: 213 units apart)
ORD={int(r['counter']):o for o,r in R.items()}
E={}; unjoined=0
for r in csv.DictReader(open(A.sg)):
    o=ORD.get(int(r['counter']))
    if o is None: unjoined+=1; continue
    E[(o,r['field'])]=r
print(f'joined {len(E)//2} engine units by counter; engine units with no reference counter: {unjoined}')
def refcols(r,f):
    return dict(top=int(r.get(f'f{f}_picture_top_line',-1) or -1), sw=int(r.get(f'f{f}_switch_first_line', r.get(f'f{f}_switch_line',-1)) or -1), bot=int(r.get(f'f{f}_bottom_line',-1) or -1))
for f in ('1','2'):
    dtop=collections.Counter(); dsw=collections.Counter(); out=[]
    for (u,ef),e in sorted(E.items()):
        if ef!=f: continue
        if A.repair_slots:
            # engine field 1 (this unit's slot 2) <-> reference slot 2 of unit u; engine field 2 (next unit's slot 1) <-> reference slot 1 of unit u+1
            ru,rf=(u,'2') if f=='1' else (u+1,'1')
        else: ru,rf=u,f
        if ru not in R: continue
        rc=refcols(R[ru],rf); et=int(e['top']); es=int(e['S_first_shifted'])
        if et<0 or rc['top']<0: dtop['unmeasurable']+=1
        else: dtop[et-rc['top']]+=1
        if es<0 or rc['sw']<0: dsw['noS' if es<0 else 'ref-none']+=1
        else:
            d=es-rc['sw']; dsw[d]+=1
            if abs(d)>1: out.append((u,es,rc['sw']))
    print(f'field {f}: top(engine - ref):',dict(sorted(dtop.items(),key=lambda x:str(x[0]))),'| S - switch_first:',dict(sorted(dsw.items(),key=lambda x:str(x[0]))),'| |diff|>1 units:',out[:20])
