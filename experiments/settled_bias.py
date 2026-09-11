"""Did `settled_samples` invalidate my dither numbers? Same rows, selection versus raw run.

`dither_compare.py` took its blanking population from `settled_samples(row, t)`, which returns
`tail[tail <= floor + 1.0]` -- a BOOLEAN-MASK SELECTION, not a contiguous slice. Adjacent elements of
what it returns were not adjacent in time, so a lag-1 autocorrelation computed on it is not the
row's autocorrelation. The peer session's independent measurement on the same rows got -0.014 where
mine got -0.292, and its blanking reached code 3 where mine never did.
"""
import sys
import numpy as np
sys.path.insert(0, "experiments")
from packet_capture_reader import walk_tagged
from source_reference import ORIGIN_ROW, source_reference, row_transition, settled_samples, settled_index

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
st={"buf":bytearray()}; sel=[]; raw=[]; drop=[]; seen=[0]

def lag1(x):
    x=np.asarray(x,float)
    if x.size<3: return None
    x=x-x.mean(); d=(x*x).sum()
    return float((x[:-1]*x[1:]).sum()/d) if d else None

def emit(u):
    c=int.from_bytes(u[4:6],"little")
    if c<6667 or seen[0]>=30: return
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)[:,1::2].astype(np.float64)
    for f in (1,2):
        b=ORIGIN_ROW[f]
        ref=source_reference([Y[b+o] for o in range(20,210)])
        if ref is None: continue
        seen[0]+=1
        for o in range(20,210):
            r=Y[b+o]; t=row_transition(r)
            if t is None: continue
            s=settled_samples(r,t)
            if s is None or s.size<3: continue
            i=settled_index(r,t)
            contiguous=r[i:]                      # the SAME span, unfiltered
            if contiguous.size<3: continue
            sel.append(s); raw.append(contiguous)
            drop.append(1.0-s.size/contiguous.size)

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
for nm,pop in (("SELECTED (what I measured)",sel),("RAW contiguous (same span)",raw)):
    allv=np.concatenate(pop)
    codes,counts=np.unique(np.round(allv).astype(int),return_counts=True)
    lags=[l for l in (lag1(x) for x in pop) if l is not None]
    print("%-28s %7d samples / %5d runs  median len %.0f"%(nm,allv.size,len(pop),np.median([len(x) for x in pop])))
    print("%-28s codes: %s"%("",", ".join("%d:%.1f%%"%(c,100*n/allv.size) for n,c in sorted(zip(counts,codes),reverse=True)[:4])))
    print("%-28s lag-1 median %+.3f  (p10 %+.3f, p90 %+.3f)"%("",np.median(lags),np.percentile(lags,10),np.percentile(lags,90)))
print("\n  the selection discards a median %.1f%% of the span's samples"%(100*np.median(drop)))
