#!/usr/bin/env python3
# v9 acceptance: compare a schema-5 frameserver decision log against the whole-tape parity truth set (line21_truth.py).
# For every unit where the truth has a reading, the engine's applied d must equal it:
#   field 1: exactly one parity-valid line other than 21 => d1 = line-21
#   field 2: exactly one parity-valid line other than 284 => d2 = line-284
#   (non-null bytes on the regenerated 21/284 with nothing elsewhere are the device's own slicing decision — reported,
#    never used as truth: measured 2026-09-05, rigid +1 picture shifts coexist with re-encoded data at 21)
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
    if insert!='none' and insert!='8080': return None, 'insert-data'   # the device's own slicing decision: corroboration, never truth
    return None, 'none'
T={}
for c,r in zip(ctr,truth):
    e1=expect(r['f1_lines'],r['f1_bytes'],r['insert21'],21); e2=expect(r['f2_lines'],r['f2_bytes'],r['insert284'],284)
    T[c]=(e1,e2)
log=[r for r in csv.DictReader(open(log_path)) if r.get('transport')=='Complete']   # exact units only (kind is the video kind, not exactness)
# the frameserver extends the device counter from its raw value and the truth set unwraps the same raw counter,
# so the two agree directly; verify on the first rows rather than searching for an offset
lc=[int(r['counter_extended']) for r in log]
offset=0
common=sum(1 for c in lc[:2000] if c in T)
if common < min(2000,len(lc))*0.9:
    raise SystemExit(f"counter join failed: only {common} of the first {min(2000,len(lc))} sidecar units have a truth row")
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
