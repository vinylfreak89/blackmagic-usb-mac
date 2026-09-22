#!/usr/bin/env python3
"""Compare raw engine observations to an external first-step census, never refit.

Usage: check_waveform_census.py reference.csv engine.csv disagreements.csv
Engine input can be hblank_probe output or a schema-21 unit sidecar. Raw tops
are compared BEFORE policy discard; an empty cell is an explicit abstention.
Every disagreement is written, including missing/extra/duplicate unit keys.
"""
import csv
import json
import sys
from collections import Counter

def read(path):
    rows={};duplicates=[]
    with open(path) as f:
        for r in csv.DictReader(line for line in f if not line.startswith('#')):
            key=r.get('counter',r.get('counter_extended',''))
            if key in ('',None):continue
            key=int(key)
            if key in rows:duplicates.append(key)
            rows[key]=r
    return rows,duplicates

def main():
    reference,engine,output=sys.argv[1:]
    a,ad=read(reference);b,bd=read(engine);diff=[];counts=Counter()
    for c in sorted(set(a)|set(b)):
        for k,nom in ((1,23),(2,286)):
            expected=a.get(c,{}).get(f'f{k}_top','MISSING')
            actual=b.get(c,{}).get(f'wave_top_f{k}',b.get(c,{}).get(f'f{k}_top','MISSING'))
            if expected!=actual:
                diff.append((c,k,expected,actual))
            if c in b and actual not in ('MISSING','',None):
                counts['raw_placed']+=1
                counts['discarded_edges']+=abs(int(actual)-nom)>5
            elif c in b:counts['raw_abstained']+=1
    for c in ad:diff.append((c,'reference','duplicate',''))
    for c in bd:diff.append((c,'engine','','duplicate'))
    with open(output,'w') as f:
        w=csv.writer(f);w.writerow(('counter','field','reference_top','engine_top'));w.writerows(diff)
    n=2*len(a);count=len(diff)
    print(f'EDGES_TOTAL={n} EDGES_MATCH={n-count} EDGES_DIFFER={count}')
    print(json.dumps(dict(counts),sort_keys=True))
    return bool(diff)

if __name__=='__main__':sys.exit(main())
