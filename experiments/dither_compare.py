"""Does clipped dark picture share the SOURCE BLANKING's dither, or is it distinguishable?

CLAUDE.md :2743 asserts "black content in this material can be clipped to exactly the blanking level
with the same dither", citing "CLAUDE.md §2" -- which records no such thing. The contract at :461
already says the claim "needs its own supporting measurement and does not follow from the means and
standard deviations". Codex flagged the same assumption in switch_fixtures.py. So it is measured.

It matters twice. If the two are distinguishable, a matched control that draws its dark content from
blanking's distribution is assuming away the very thing that would separate them -- and the recorded
limitation that a blank-level run "cannot establish relocated blanking rather than clipped black
content" is weaker than stated.

Two statistics, neither needing a threshold:
  the VALUE distribution over codes, and the LAG-1 AUTOCORRELATION -- negative is the high-pass
  signature of dither, which is how this project established the device's fill was written.
"""
import sys
import numpy as np
sys.path.insert(0, "experiments")
from packet_capture_reader import walk_tagged
from source_reference import ORIGIN_ROW, source_reference, row_transition, settled_samples

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
st={"buf":bytearray()}; blank=[]; dark=[]; seen=[0]

def lag1(x):
    x=np.asarray(x,float)
    if x.size<3: return float("nan")
    x=x-x.mean()
    d=(x*x).sum()
    return float((x[:-1]*x[1:]).sum()/d) if d else float("nan")

def emit(u):
    c=int.from_bytes(u[4:6],"little")
    if c<6667 or seen[0]>=40: return
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)[:,1::2].astype(np.float64)
    for f in (1,2):
        b=ORIGIN_ROW[f]
        ref=source_reference([Y[b+o] for o in range(20,210)])
        if ref is None: continue
        seen[0]+=1; hi=ref["level"]+3.0
        for o in range(20,210):
            r=Y[b+o]; t=row_transition(r)
            if t is not None:
                sm=settled_samples(r,t)
                if sm is not None and sm.size>=3: blank.append(np.asarray(sm,float))
            # DARK PICTURE: a low run in the row's INTERIOR, well away from the terminal blanking
            m=r[:640]<=hi
            i=0
            while i<640:
                if m[i]:
                    j=i
                    while j+1<640 and m[j+1]: j+=1
                    if j-i+1>=8: dark.append(r[i:j+1].astype(float))
                    i=j+1
                else: i+=1

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
for nm,runs in (("SOURCE BLANKING",blank),("CLIPPED DARK PICTURE",dark)):
    if not runs: print("%-22s : no runs found"%nm); continue
    allv=np.concatenate(runs)
    codes,counts=np.unique(np.round(allv).astype(int),return_counts=True)
    top=sorted(zip(counts,codes),reverse=True)[:4]
    lags=[lag1(r) for r in runs if r.size>=3]
    lags=[l for l in lags if l==l]
    print("%-22s : %7d samples in %5d runs   mean %.3f"%(nm,allv.size,len(runs),allv.mean()))
    print("%-22s   codes: %s"%("",", ".join("%d:%.0f%%"%(c,100*n/allv.size) for n,c in top)))
    print("%-22s   lag-1 autocorrelation: median %+.3f  (p10 %+.3f, p90 %+.3f, n=%d)"
          %("",np.median(lags),np.percentile(lags,10),np.percentile(lags,90),len(lags)))
