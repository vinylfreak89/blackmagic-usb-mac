#!/usr/bin/env python3
"""WHERE the blanking interval begins in the sweep -- a phase, not a level.

Owner, 2026-09-11, on the previous attempt: "again its dare is measuring wrong. the whole point is
it should be measuring the blanking region. it is trying to smooth a temporal band spatially...
again". That attempt reported MEAN ELEVATION across the expected blanking region -- a scalar summary
of an interval, which collapses a temporal event into an amplitude. Two rows where picture intrudes
20 samples and 140 samples return the same mean, so "18.3 versus 18.9, indistinguishable" was two
different phases reading the same.

This reports the BOUNDARY: the sample position at which the row's level settles into blanking,
against where this source's own good picture lines put it. Displacement is the difference.

⚠️ The first version of THIS searched forward from b0-60 and reported "absent" for every disputed
row -- bounding a temporal quantity spatially, the same error a third time. An interval that arrives
660 samples early is not absent. The search now covers the whole sweep.

  blanking_boundary.py
"""
import sys, csv, collections
import numpy as np
sys.path.insert(0,'/Users/vinylfreak89/Documents/blackmagic-usb-mac/experiments')
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
BASE={1:19,2:282}; BLANK={1:list(range(7,16)),2:list(range(270,279))}
eng={}
for r in csv.DictReader(open('/private/tmp/run-timing.DdLgYt/plain/geometry.csv')):
    eng[(int(r['counter']),int(r['field']))]=(int(r['T']),int(r['S']))

def blank_onset(row, blank, lo=0):
    """Where in the sweep this row's blanking interval BEGINS. Searched over the WHOLE row -- the
    previous version searched forward from b0-60, which bounds a temporal quantity spatially and
    reports 'absent' for an interval that merely arrived early. The relocated interval on a switched
    row starts near sample 20-40, roughly 660 samples before its expected phase."""
    W=8
    for i in range(0, len(row)-W):
        if np.all(row[i:i+W] <= blank+1.5): return i
    return None

def narrow_peak_line(Y,base,blank):
    best=(0.0,-1)
    for off in range(232,240):
        row=Y[base+off]; med=float(np.median(row)); d=row-med
        order=np.argsort(-np.abs(d)); seen=set()
        for k in order[:400]:
            if k in seen: continue
            amp=float(d[k]); sg=1 if amp>0 else -1; thr=abs(amp)/2
            a=k
            while a>0 and abs(d[a-1])>=thr and np.sign(d[a-1])==sg: a-=1
            b=k
            while b<len(d)-1 and abs(d[b+1])>=thr and np.sign(d[b+1])==sg: b+=1
            seen.update(range(a,b+1))
            if b-a+1<100:
                if abs(amp)>best[0]: best=(abs(amp),base+off)
                break
    return best

st={"buf":bytearray()}; groups=collections.defaultdict(list)
def emit(u):
    c=int.from_bytes(u[4:6],"little")
    if c<6667: return
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)[:,1::2].astype(np.float64)
    for fld in (1,2):
        T,S=eng.get((c,fld),(-1,-1))
        if T<0 or S<0: continue
        blank=float(np.median(Y[BLANK[fld]]))
        # where THIS SOURCE says the blanking interval begins: from its own good picture lines
        exp=[]
        for off in range(177,228):
            b=blank_onset(Y[BASE[fld]+off],blank,0)
            if b is not None and b<600: b=None
            if b is not None: exp.append(b)
        if len(exp)<20: continue
        b0=int(np.median(exp))
        amp,prow=narrow_peak_line(Y,BASE[fld],blank)
        if amp<89 or prow<0: continue
        got=blank_onset(Y[prow],blank)
        key=("engine T=S, peak one row ABOVE" if (S==T and prow+4==T-1) else
             "engine T=S-1, peak ON T" if (S==T+1 and prow+4==T) else "other")
        groups[key].append(None if got is None else got-b0)
        cg=blank_onset(Y[BASE[fld]+150],blank)
        groups["CONTROL ordinary picture row"].append(None if cg is None else cg-b0)
def on_video(p):
    b=st["buf"]; b.extend(p)
    while True:
        i=b.find(MARK)
        if i<0: return
        if i>0: del b[:i]
        j=b.find(MARK,4)
        if j<0: return
        if j==UNIT: emit(bytes(b[:UNIT]))
        del b[:j]
walk_tagged('/Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/composite_program_30s.tpc',on_video=on_video,progress=False)
print("BOUNDARY POSITION over the WHOLE sweep -- no spatial bound on the search.")
print("against where this source's own good picture lines say it should. A phase, in samples.\n")
print("  %-38s %5s %10s %10s %10s %8s"%("group","n","median","p10","p90","no bound"))
for k in sorted(groups):
    v=groups[k]; ok=[x for x in v if x is not None]
    if not v: continue
    print("  %-38s %5d %10s %10s %10s %8d"%(k,len(v),
        "%+d"%int(np.median(ok)) if ok else "-",
        "%+d"%int(np.percentile(ok,10)) if ok else "-",
        "%+d"%int(np.percentile(ok,90)) if ok else "-",
        sum(1 for x in v if x is None)))
