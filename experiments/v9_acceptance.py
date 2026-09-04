#!/usr/bin/env python3
# v9 acceptance: compare a schema-7 frameserver decision log against the whole-tape parity truth set (line21_truth.py).
# For every unit where the truth has a reading, the engine's applied d must
# equal it unless the sidecar explicitly records one of the owner-approved
# current-picture vetoes:
#   field 1: exactly one parity-valid line other than 21 => d1 = line-21
#   field 2: exactly one parity-valid line other than 284 => d2 = line-284
#   CaptionOnlyMotion / CaptionBodyDisagree: current top plus the one-unit body
#   witness reject a caption-only or differently moving VBI line;
#   Line21Ambiguous / GaugeConflict: caption evidence was discarded and current
#   geometry either placed or explicitly held the unit.
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
with open(truth_path, newline='') as f:
    truth=list(csv.DictReader(f))
if not truth:
    raise SystemExit("truth set is empty")
ctr=unwrap([int(r['counter']) for r in truth])
def expect(lines, bytes_, insert, ins_line, high):
    L=[int(x) for x in lines.split()] if lines else []
    B=bytes_.split() if bytes_ else []
    raw_off=[(l,b) for l,b in zip(L,B) if l!=ins_line]
    # A valid-parity picture line well outside the engine's physical crop range
    # is not a second line-21 candidate.  Discard it before deciding uniqueness;
    # otherwise one real +2/+3 reading plus one chance body hit is mislabeled
    # ambiguous (74 units in fixture A's whole-tape truth set).
    off=[(l,b) for l,b in raw_off if -6 <= l-ins_line <= high]
    if len(off)==1:
        d=off[0][0]-ins_line
        return d, 'parity@%d'%off[0][0]
    if len(off)>1: return None, 'ambiguous'
    if raw_off: return None, 'implausible'
    if insert!='none' and insert!='8080': return None, 'insert-data'   # the device's own slicing decision: corroboration, never truth
    return None, 'none'
T={}
for c,r in zip(ctr,truth):
    if c in T:
        raise SystemExit(f"truth counter is not unique after unwrapping: {c}")
    e1=expect(r['f1_lines'],r['f1_bytes'],r['insert21'],21,9)
    e2=expect(r['f2_lines'],r['f2_bytes'],r['insert284'],284,3)
    T[c]=(e1,e2)
with open(log_path, newline='') as f:
    # COMPLETE alone is insufficient: the parser also calls a complete 0x0800
    # device-no-signal unit Complete.  Only kind 0 is an exact e801 raster and
    # therefore has a row in line21_truth.py's fixed-raster truth set.
    all_log=list(csv.DictReader(f))
    log=[r for r in all_log
         if r.get('transport')=='Complete' and r.get('kind')=='0']
if not log:
    raise SystemExit("sidecar has no exact e801 rows")
bad_delivery=[r for r in log if r.get('published')!='1' or r.get('drop_reason')!='None']
if bad_delivery:
    r=bad_delivery[0]
    raise SystemExit(f"exact unit was not published cleanly: ordinal {r['ordinal']} "
                     f"published={r.get('published')} drop_reason={r.get('drop_reason')}")
# the frameserver extends the device counter from its raw value and the truth set unwraps the same raw counter,
# so the two agree directly; verify on the first rows rather than searching for an offset
lc=[int(r['counter_extended']) for r in log]
if len(lc) != len(set(lc)):
    raise SystemExit("sidecar exact-unit counters are not unique")
common=sum(1 for c in lc[:2000] if c in T)
if common < min(2000,len(lc))*0.9:
    raise SystemExit(f"counter join failed: only {common} of the first {min(2000,len(lc))} sidecar units have a truth row")
picture_veto_reasons={
    'CaptionOnlyMotion', 'CaptionBodyDisagree',
    'Line21Ambiguous', 'GaugeConflict',
}
stats={1:collections.Counter(),2:collections.Counter()}; mism=[]
for r in log:
    c=int(r['counter_extended'])
    if c not in T:
        raise SystemExit(f"exact sidecar counter {c} has no truth row (ordinal {r['ordinal']})")
    for f,(e,why) in zip((1,2),T[c]):
        if e is None: stats[f]['truth:'+why]+=1; continue
        a=int(r['applied_d%d'%f])
        if a==e: stats[f]['agree:'+why.split('@')[0]]+=1
        elif r['f%d_reason'%f] in picture_veto_reasons:
            # Preserve the exact rejection class in the acceptance output;
            # a generic "veto" total would hide a policy regression.
            stats[f]['picture-veto:'+r['f%d_reason'%f]]+=1
        else:
            stats[f]['DISAGREE:'+why.split('@')[0]]+=1
            if len(mism)<40: mism.append((r['ordinal'],c,f,e,a,r['f%d_reason'%f],why))
print(f"exact e801 sidecar rows {len(log)}, truth rows {len(truth)}, counter offset 0")
for f in (1,2): print(f"field {f}: {dict(stats[f].most_common())}")
for m in mism: print("  mismatch ordinal %s counter %d field %d expected %+d applied %+d reason %s (%s)"%m)
if mism:
    raise SystemExit(f"acceptance failed: {sum(v for s in stats.values() for k,v in s.items() if k.startswith('DISAGREE:'))} disagreements")
