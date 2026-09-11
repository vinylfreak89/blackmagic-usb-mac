"""Does RELOCATED blanking keep the dither signature? The population the T/S question is about.

`dither_compare.py` measured UNDISPLACED blanking against clipped dark picture and I then wrote a
conclusion about "relocated blanking versus clipped black content". Relocated blanking was never in
that measurement -- the scope class, committed inside a finding about an unsupported claim. The peer
session caught it.

The inference is plausible (same source signal, displaced by the head switch rather than regenerated,
so nothing strips the high-pass character) and plausible is what the :2743 citation was. So it is
measured here on the rows that carry it: the switch band's interior runs at the field's own blank
level, long enough to estimate an autocorrelation.
"""
import sys
import numpy as np
sys.path.insert(0, "experiments")
from packet_capture_reader import walk_tagged
from source_reference import ORIGIN_ROW, source_reference

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
FIELD_ORIGIN={1:23,2:286}
BAND={1:(258,264), 2:(521,527)}          # around the switch band, in NTSC lines
st={"buf":bytearray()}; runs=[]; seen=[0]

def lag1(x):
    x=np.asarray(x,float)
    if x.size<3: return None
    x=x-x.mean(); d=(x*x).sum()
    return float((x[:-1]*x[1:]).sum()/d) if d else None

def emit(u):
    c=int.from_bytes(u[4:6],"little")
    if c<6667 or seen[0]>=120: return
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)[:,1::2].astype(np.float64)
    for f in (1,2):
        b=ORIGIN_ROW[f]; org=FIELD_ORIGIN[f]
        ref=source_reference([Y[b+o] for o in range(20,210)])
        if ref is None: continue
        seen[0]+=1; hi=ref["level"]+3.0
        lo,hg=BAND[f]
        for ln in range(lo,hg+1):
            r_i=b+(ln-org)
            if not (0<=r_i<LINES): continue
            r=Y[r_i]; m=r<=hi
            i=0
            while i<720:
                if m[i]:
                    j=i
                    while j+1<720 and m[j+1]: j+=1
                    L=j-i+1
                    # a RELOCATED interval: long, and INTERIOR (not the ordinary terminal run)
                    if L>=100 and j<715:
                        a=lag1(r[i:j+1])
                        if a is not None: runs.append((a,L,i,float(r[i:j+1].mean())))
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
if not runs:
    print("no relocated intervals found in the band window"); raise SystemExit(0)
a=np.array([r[0] for r in runs]); L=np.array([r[1] for r in runs])
s0=np.array([r[2] for r in runs]); mn=np.array([r[3] for r in runs])
print("RELOCATED blanking in the switch band: %d runs over %d field-readings\n"%(len(runs),seen[0]))
print("  run length      : median %d samples (p10 %d, p90 %d)"%(np.median(L),np.percentile(L,10),np.percentile(L,90)))
print("  run starts at   : median %d"%np.median(s0))
print("  run mean level  : %.3f"%np.median(mn))
print("  LAG-1 AUTOCORR  : median %+.3f   (p10 %+.3f, p90 %+.3f)"
      %(np.median(a),np.percentile(a,10),np.percentile(a,90)))
print("\n  for comparison, from dither_compare.py on the same capture:")
print("    undisplaced blanking  -0.292      clipped dark picture  +0.274")
print("\n  share of these runs with a NEGATIVE lag-1 (the dither signature): %.1f%%"%(100*(a<0).mean()))
