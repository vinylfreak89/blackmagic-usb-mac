"""Is the blanking interval's END observable at all on real rows, or clipped by the window?

The peer session inferred that "an end-shift at the window edge is largely unobservable" from two
recorded positions. That is an INFERENCE, not a measurement, and it bears on whether the fixture's
nominal interval belongs at (700,717) or (660,677) -- so it gets measured rather than adopted.

The question is precise: on real picture rows, does the row's terminal blank run REACH the last
delivered sample (719)? If it does, the interval's end is censored by the window on every row, an
end-LENGTHENING is unobservable by construction, and a fixture that moves the nominal inward to make
such a case constructible is testing something the source cannot show.
"""
import sys
import numpy as np
sys.path.insert(0, "experiments")
from packet_capture_reader import walk_tagged
from source_reference import ORIGIN_ROW, source_reference

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
st={"buf":bytearray()}; rows=[]; seen=[0]

def emit(u):
    c=int.from_bytes(u[4:6],"little")
    if c<6667 or seen[0]>=60: return
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)[:,1::2].astype(np.float64)
    for f in (1,2):
        b=ORIGIN_ROW[f]
        ref=source_reference([Y[b+o] for o in range(20,210)])
        if ref is None: continue
        seen[0]+=1
        cut=ref["level"]+3.0
        bright=float(Y[b+40:b+200].mean())
        for o in range(20,210):
            r=Y[b+o]; m=r<=cut
            if not m.any(): rows.append((bright,None,None)); continue
            # the row's TERMINAL run: walk back from the last sample while still at blank level
            if m[-1]:
                i=719
                while i>0 and m[i-1]: i-=1
                rows.append((bright,i,719))         # reaches the window edge
            else:
                idx=np.flatnonzero(m); rows.append((bright,int(idx[-1]),None))  # ends inside

def on_video(p):
    bb=st["buf"]; bb.extend(p)
    while True:
        i=bb.find(MARK)
        if i<0: return
        if i>0: del bb[:i]
        j=bb.find(MARK,4)
        if j<0: return
        if j==UNIT: emit(bytes(bb[:UNIT]))
        del bb[:j]

walk_tagged("captures/composite_program_30s.tpc",on_video=on_video,progress=False)
tot=len(rows)
reach=[r for r in rows if r[2]==719]
inside=[r for r in rows if r[2] is None and r[1] is not None]
none_=[r for r in rows if r[1] is None]
print("picture rows examined: %d over %d field-readings\n"%(tot,seen[0]))
print("  terminal blank run REACHES sample 719 : %6d  %5.1f%%"%(len(reach),100*len(reach)/max(tot,1)))
print("  last blank sample lies INSIDE the row : %6d  %5.1f%%"%(len(inside),100*len(inside)/max(tot,1)))
print("  no blank sample at all                : %6d  %5.1f%%"%(len(none_),100*len(none_)/max(tot,1)))
if reach:
    st_=np.array([r[1] for r in reach]);  print("\n  where the terminal run STARTS: median %d, p10 %d, p90 %d"%(np.median(st_),np.percentile(st_,10),np.percentile(st_,90)))
    print("  its length: median %d samples"%(720-np.median(st_)))
b=np.array([r[0] for r in rows]); cut=np.median(b)
for nm,msk in (("dim",b<cut),("bright",b>=cut)):
    sub=[r for r,k in zip(rows,msk) if k]; rr=[r for r in sub if r[2]==719]
    print("  %-7s half: %5.1f%% reach 719 (n=%d)"%(nm,100*len(rr)/max(len(sub),1),len(sub)))
