#!/usr/bin/env python3
# v9 acceptance: compare a schema-5 frameserver decision log against the whole-tape parity truth set (line21_truth.py).
# For every unit where the truth has a reading, the engine's applied d must equal it:
#   field 1: exactly one parity-valid line other than 21 => d1 = line-21; only line 21 with NON-null bytes => d1 = 0
#   field 2: exactly one parity-valid line other than 284 => d2 = line-284; only 284 with non-null bytes => d2 = 0
# Units are joined on the device counter (truth: raw 16-bit, unwrapped here; sidecar: counter_extended).
# Usage: v9_acceptance.py <decision_log.csv> <line21_truth.csv>
import sys, csv, collections
log_path, truth_path = sys.argv[1], sys.argv[2]
def unwrap(seq):
    out=[]; base=0; prev=None
    for c in seq:
        if prev is not None and c < prev - 32768: base += 65536
        out.append(base + c); prev = c
    return out
truth=list(csv.DictReader(open(truth_path)))
ctr=unwrap([int(r['counter']) for r in truth])
def expect(lines, bytes_, insert, ins_line):
    L=[int(x) for x in lines.split()] if lines else []
    B=bytes_.split() if bytes_ else []
    off=[(l,b) for l,b in zip(L,B) if l!=ins_line]
    if len(off)==1:
        d=off[0][0]-ins_line
        if d < -6 or d > 9: return None, 'implausible'   # a picture line that passed parity by chance
        return d, 'parity@%d'%off[0][0]
    if len(off)>1: return None, 'ambiguous'
    if insert!='none' and insert!='8080': return 0, 'insert-data'
    return None, 'none'
T={}
for c,r in zip(ctr,truth):
    e1=expect(r['f1_lines'],r['f1_bytes'],r['insert21'],21); e2=expect(r['f2_lines'],r['f2_bytes'],r['insert284'],284)
    T[c]=(e1,e2)
log=[r for r in csv.DictReader(open(log_path)) if r.get('transport')!='Hole' and r.get('kind')=='0']
# align the sidecar's extended counter with the truth's unwrapped counter: pick the offset that lands the most
# sidecar rows on truth rows (both count from different bases)
lc=[int(r['counter_extended']) for r in log]; tkeys=sorted(T); best=(0,0)
for k in set(lc[i]-tkeys[j] for i in range(min(50,len(lc))) for j in range(min(50,len(tkeys)))):
    hits=sum(1 for c in lc[:5000] if (c-k) in T)
    if hits>best[0]: best=(hits,k)
offset=best[1]
stats={1:collections.Counter(),2:collections.Counter()}; mism=[]
for r in log:
    c=int(r['counter_extended'])-offset
    if c not in T: stats[1]['no-truth-row']+=1; continue
    for f,(e,why) in zip((1,2),T[c]):
        if e is None: stats[f]['truth:'+why]+=1; continue
        a=int(r['applied_d%d'%f])
        if a==e: stats[f]['agree:'+why.split('@')[0]]+=1
        else:
            stats[f]['DISAGREE:'+why.split('@')[0]]+=1
            if len(mism)<40: mism.append((r['ordinal'],c,f,e,a,r['f%d_reason'%f],why))
print(f"sidecar rows {len(log)}, truth rows {len(truth)}, counter offset {offset}")
for f in (1,2): print(f"field {f}: {dict(stats[f].most_common())}")
for m in mism: print("  mismatch ordinal %s counter %d field %d expected %+d applied %+d reason %s (%s)"%m)
