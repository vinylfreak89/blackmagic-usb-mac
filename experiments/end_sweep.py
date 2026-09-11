"""Does the end-censoring result rest on the typed +3.0, or survive a sweep of it?

`end_observability.py` uses `cut = ref["level"] + 3.0`. That constant is NOT neutral for this
question -- a generous cut counts more samples as blank and biases TOWARD the run reaching 719 -- and
100.0% with zero exceptions is the too-clean shape this project checks the population for first.

The refuting observation is specific: a row whose last blank sample lies INSIDE the row. If that
count stays at zero across the sweep, the constant is not doing the work.
"""
import sys
import numpy as np
sys.path.insert(0, "experiments")
from packet_capture_reader import walk_tagged
from source_reference import ORIGIN_ROW, source_reference

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
KS=(0.5,1.0,2.0,3.0,4.0,5.0)
st={"buf":bytearray()}; acc={k:[0,0,0] for k in KS}; seen=[0]

def emit(u):
    c=int.from_bytes(u[4:6],"little")
    if c<6667 or seen[0]>=60: return
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)[:,1::2].astype(np.float64)
    for f in (1,2):
        b=ORIGIN_ROW[f]
        ref=source_reference([Y[b+o] for o in range(20,210)])
        if ref is None: continue
        seen[0]+=1
        for k in KS:
            cut=ref["level"]+k
            for o in range(20,210):
                m=Y[b+o]<=cut
                if not m.any(): acc[k][2]+=1
                elif m[-1]:    acc[k][0]+=1
                else:          acc[k][1]+=1

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
print("cut = source level + k, over %d field-readings\n"%(seen[0]//len(KS)))
print("  %6s %12s %12s %12s   %s"%("k","reaches 719","ENDS INSIDE","no blank","reaches, of rows with any blank"))
for k in KS:
    r,i,n=acc[k]; tot=r+i
    print("  %6.1f %12d %12d %12d   %s"%(k,r,i,n,"%.1f%%"%(100*r/tot) if tot else "n/a"))
print("\n  the refuting observation is a row ENDING INSIDE; a tight cut instead removes rows entirely,")
print("  which is absence of evidence rather than evidence the end is visible.")
