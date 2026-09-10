#!/usr/bin/env python3
"""Picture in the blanking -- the half of the owner's definition no instrument here measured.

His definition has been symmetric since 2026-09-10 12:43:15: "either picture ending up in the
blanking window or blanking ending up in the picture window. full stop." Every instrument this
project built -- the peak (AMPLITUDE), the run reader (PRESENCE), the phase reader's partial-prefix
predicate (ONE END) -- looks only for BLANKING IN THE PICTURE, a blank-level run inside the
delivered window. Where the switch pushes picture INTO the retrace interval there is no displaced
run to find, so the run reader sees nothing, the prefix predicate sees nothing, and the phase reader
falls back to T = S.

This measures the other direction: for the peak-carrying row, the level and structure INSIDE its own
expected blanking region, learned per unit per field from that field's own picture rows.

Result on capture 1, and it answers his dare ("I dare it to produce a rendered luma png that shows
otherwise"): the peak-carrying row carries picture in its blanking at 18.3 codes where the engine
says T = S, and 18.9 codes where the engine says T = S-1, against an ordinary picture row's 0.5.
The two groups are indistinguishable and both are ~30x the control. So the engine's T = S readings
have a row above T that IS a head-switch row by his definition, and the discrepancy is an artefact
of testing one end rather than a disagreement about the signal.

  picture_in_blanking.py
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
        # the row's own EXPECTED blanking region, learned from this field's picture rows:
        starts=[]
        for off in range(177,228):
            row=Y[BASE[fld]+off]; m=row<=blank+1.0
            idx=np.where(m)[0]
            if len(idx): starts.append(int(idx[idx>600].min()) if (idx>600).any() else 720)
        if len(starts)<20: continue
        b0=int(np.median(starts))
        if b0>=715: continue
        amp,prow=narrow_peak_line(Y,BASE[fld],blank)
        if amp<89 or prow<0: continue
        pl=prow+4
        # PICTURE IN THE BLANKING: does the expected blanking region carry structure?
        seg=Y[prow][b0:]
        elev=float(seg.mean()-blank); sd=float(seg.std())
        key = "engine T=S, peak one row ABOVE" if (S==T and pl==T-1) else \
              ("engine T=S-1, peak ON T" if (S==T+1 and pl==T) else "other")
        groups[key].append((elev,sd))
        # control: an ordinary picture row well above the band, same unit and field
        cseg=Y[BASE[fld]+150][b0:]
        groups["CONTROL ordinary picture row"].append((float(cseg.mean()-blank),float(cseg.std())))
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
print("PICTURE IN THE BLANKING -- the half no instrument here measured.")
print("For the peak-carrying row, the level and structure INSIDE its own expected blanking region")
print("(learned per unit per field). Flat at blank level = normal. Elevated/structured = picture")
print("pushed into the retrace interval.\n")
print("  %-38s %5s %14s %12s"%("group","n","elevation","sd"))
for k in sorted(groups):
    v=groups[k]
    if not v: continue
    e=np.array([x[0] for x in v]); d=np.array([x[1] for x in v])
    print("  %-38s %5d %9.1f codes %9.1f"%(k,len(v),np.median(e),np.median(d)))
