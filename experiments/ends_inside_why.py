"""For a row that ENDS INSIDE at a tight cut: is what follows blanking, or picture?

Two opposite hypotheses fit the k=0.5 collapse and no sweep separates them:
  (a) the interval's end is genuinely visible inside the row, and a generous cut HID it
  (b) the cut sits inside blanking's own spread and BREAKS a run that really reaches the edge

The peer session's discriminator, run here independently because the claim is mine. Take every row
that ends inside at k=0.5 and measure what lies AFTER its last blank sample. Under (b) those samples
are still blanking -- a code or two above the level. Under (a) they are picture, tens of codes up.
No threshold of its own is needed: the two predictions are orders of magnitude apart.
"""
import sys
import numpy as np
sys.path.insert(0, "experiments")
from packet_capture_reader import walk_tagged
from source_reference import ORIGIN_ROW, source_reference

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
st={"buf":bytearray()}; tails=[]; ctx=[]; seen=[0]

def emit(u):
    c=int.from_bytes(u[4:6],"little")
    if c<6667 or seen[0]>=60: return
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)[:,1::2].astype(np.float64)
    for f in (1,2):
        b=ORIGIN_ROW[f]
        ref=source_reference([Y[b+o] for o in range(20,210)])
        if ref is None: continue
        seen[0]+=1; lvl=ref["level"]; cut=lvl+0.5
        for o in range(20,210):
            r=Y[b+o]; m=r<=cut
            if not m.any() or m[-1]: continue         # only rows that END INSIDE at this cut
            last=int(np.flatnonzero(m)[-1])
            after=r[last+1:]                           # what follows the last "blank" sample
            if after.size:
                tails.append((float(after.mean()), float(after.max()), after.size, lvl))
            ctx.append(float(r[200:600].mean()))       # that row's own picture level, for scale

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
a=np.array([t[0] for t in tails]); mx=np.array([t[1] for t in tails])
n=np.array([t[2] for t in tails]); lv=np.array([t[3] for t in tails]); pic=np.array(ctx)
print("rows ending inside at k=0.5 : %d\n"%len(tails))
print("  the source's own blanking level      : %.3f"%np.median(lv))
print("  those rows' own PICTURE level        : %.1f   <- what (a) predicts the tail to resemble"%np.median(pic))
print()
print("  MEAN of the samples after the last blank sample : %.3f  (p10 %.3f, p90 %.3f)"
      %(np.median(a),np.percentile(a,10),np.percentile(a,90)))
print("  MAX  of those samples                           : %.3f  (p90 %.3f)"%(np.median(mx),np.percentile(mx,90)))
print("  how many samples follow                         : median %d"%np.median(n))
print()
d_blank=abs(np.median(a)-np.median(lv)); d_pic=abs(np.median(a)-np.median(pic))
print("  distance from blanking : %.2f codes"%d_blank)
print("  distance from picture  : %.2f codes"%d_pic)
print("\n  VERDICT: %s"%("(b) the cut broke a run that is still blanking"
      if d_blank < d_pic else "(a) the end is genuinely visible -- the tail is picture"))
