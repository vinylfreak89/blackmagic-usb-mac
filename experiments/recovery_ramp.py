#!/usr/bin/env python3
"""The peak's recovery ramp, measured UNTIL IT STOPS -- duration is the observable.

Owner, 2026-09-11: "dark peaks (and any peaks) always have a luma ramp... because duh... its
temporal signal... so to the right of the peak the luma will either ramp up or down depending on if
its a dark or light peak", and then, on the first attempt: **"you only want to measure the excursion
coming off the identified peak until the ramp stops"**.

⚠️ The first attempt took the slope over a FIXED 48 samples. That is a spatial window -- an arbitrary
distance -- and it is why the control "recovered" 63% of the time: over any fixed span a selected
extremum drifts back toward the median. The ramp is settling behaviour and it lasts as long as it
lasts, so its LENGTH is the measurement. Follow the signal from the excursion's end while it keeps
getting closer to baseline; stop when it stops.

Measured on capture 1 this separates light peaks cleanly and says something unexpected about dark
ones -- see the table in CLAUDE.md.

  recovery_ramp.py
"""
import sys, csv, collections
import numpy as np
sys.path.insert(0,'/Users/vinylfreak89/Documents/blackmagic-usb-mac/experiments')
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
BASE={1:19,2:282}
eng={}
for r in csv.DictReader(open('/private/tmp/run-timing.DdLgYt/plain/geometry.csv')):
    eng[(int(r['counter']),int(r['field']))]=(int(r['T']),int(r['S']))
PATIENCE=6   # samples allowed to not improve before the ramp is called over

def recovery(d, b, sg):
    """From the excursion's end, follow the signal WHILE IT KEEPS RECOVERING toward baseline, and
    stop when it stops. Returns (duration in samples, amplitude recovered).
    No fixed window: the ramp's own length is the measurement."""
    best = sg*d[b]          # how far from baseline, in the excursion's direction (positive = far)
    i = b+1; last_i = b; miss = 0
    while i < len(d):
        v = sg*d[i]
        if v < best - 0.5:            # closer to baseline than anything so far == still recovering
            best = v; last_i = i; miss = 0
        else:
            miss += 1
            if miss > PATIENCE: break
        i += 1
    return last_i-b, float(sg*d[b] - best)

def candidates(row):
    med=float(np.median(row)); d=row-med; out=[]
    order=np.argsort(-np.abs(d)); seen=set()
    for k in order[:600]:
        if k in seen: continue
        amp=float(d[k]); sg=1 if amp>0 else -1; thr=abs(amp)/2
        a=k
        while a>0 and abs(d[a-1])>=thr and np.sign(d[a-1])==sg: a-=1
        b=k
        while b<len(d)-1 and abs(d[b+1])>=thr and np.sign(d[b+1])==sg: b+=1
        seen.update(range(a,b+1))
        if b-a+1>=100 or b>=len(d)-20: continue
        dur,rec = recovery(d,b,sg)
        out.append((abs(amp),sg,b-a+1,dur,rec))
        if len(out)>=4: break
    return out
st={"buf":bytearray()}; rows=[]
def emit(u):
    c=int.from_bytes(u[4:6],"little")
    if c<6667: return
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)[:,1::2].astype(np.float64)
    for fld in (1,2):
        T,S=eng.get((c,fld),(-1,-1))
        if T<0 or S<0: continue
        for off in range(232,240):
            for r in candidates(Y[BASE[fld]+off]): rows.append(r+("band",))
        for off in (120,150,180):
            for r in candidates(Y[BASE[fld]+off]): rows.append(r+("control",))
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
print("THE RAMP MEASURED UNTIL IT STOPS -- duration is the observable, not a fixed window.\n")
def rep(name,sel):
    v=[r for r in rows if sel(r)]
    if not v: print("  %-42s none"%name); return
    dur=np.array([x[3] for x in v]); rec=np.array([x[4] for x in v])
    print("  %-42s n=%5d   ramp median %3.0f samples  p90 %3.0f   recovered median %5.1f codes"
          %(name,len(v),np.median(dur),np.percentile(dur,90),np.median(rec)))
rep("BAND  light, amp>=89",lambda r:r[5]=="band" and r[1]>0 and r[0]>=89)
rep("CONTROL light, amp>=89",lambda r:r[5]=="control" and r[1]>0 and r[0]>=89)
rep("BAND  dark,  amp>=89",lambda r:r[5]=="band" and r[1]<0 and r[0]>=89)
rep("CONTROL dark,  amp>=89",lambda r:r[5]=="control" and r[1]<0 and r[0]>=89)
print()
rep("BAND  dark,  amp 20-88",lambda r:r[5]=="band" and r[1]<0 and 20<=r[0]<89)
rep("CONTROL dark,  amp 20-88",lambda r:r[5]=="control" and r[1]<0 and 20<=r[0]<89)
