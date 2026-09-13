"""Does the cached statistic match a fresh recomputation from the raw raster?

Written because the owner said "you have to have a math error somewhere" (2026-09-11) and
that is a claim to test, not to argue with.  It recomputes p90 straight from the unit's
luma and compares against experiments/field_line_count.py's cache, and prints COVERAGE --
the fraction of the row's 720 samples above the blanking codes -- beside it.

Result on counters 6810/6811: fresh == cache everywhere in the raster, so no arithmetic
error.  What the coverage column showed instead is that the statistic is the wrong SHAPE:
field 1 line 23 is 42-48% covered with codes running to 12, field 2 line 286 is 6-11%
covered with codes capped at 4-5, and p90 collapses that five-fold difference onto either
side of a cut with no margin.  Line 22 / 285 reads exactly 0.0% in both fields, so the
coverage measure has a true zero reference.
"""
import numpy as np, sys
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; RB=1440; ROWS=525; MARK=b"\x00\x00\xff\xff"
WANT=[6810,6811]
S="/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac/8ad5adc7-a74c-4853-97ac-571007154e12/scratchpad"
z=np.load(S+"/cap1_stats.npz"); C=z["counters"]; ST=z["stats"]; NM=list(z["stat_names"])
i90=NM.index("p90")
got={}; state={"buf":bytearray()}
class Done(Exception): pass
def emit(u):
    c=int.from_bytes(u[4:6],"little")
    if c in WANT and c not in got:
        got[c]=np.frombuffer(u,np.uint8)[HDR:].reshape(ROWS,RB)[:,1::2].astype(int)
        if len(got)==len(WANT): raise Done
def on_video(p):
    b=state["buf"]; b.extend(p)
    while True:
        i=b.find(MARK)
        if i<0: return
        if i>0: del b[:i]
        j=b.find(MARK,4)
        if j<0: return
        if j==UNIT: emit(bytes(b[:UNIT]))
        del b[:j]
try: walk_tagged("../captures/composite_program_30s.tpc", on_video=on_video, progress=False)
except Done: pass

for ctr in WANT:
    Y=got[ctr]; u=int(np.where(C==ctr)[0][0])
    print("="*78)
    print(f"counter {ctr}")
    print(f"{'frame':>6} {'f1row':>6} {'p90 fresh':>10} {'p90 cache':>10} {'cov>2':>7} "
          f"{'n=3+':>6} | {'f2row':>6} {'p90 fresh':>10} {'p90 cache':>10} {'cov>2':>7} {'n=3+':>6}")
    for L in range(22,29):
        r1, r2 = L-4, L+259
        a, b = Y[r1], Y[r2]
        pa, pb = np.percentile(a,90), np.percentile(b,90)
        ca, cb = ST[u,r1,i90], ST[u,r2,i90]
        print(f"{L:>6} {r1:>6} {pa:10.4f} {ca:10.4f} {100*(a>2).mean():6.1f}% {(a>=3).sum():6d}"
              f" | {r2:>6} {pb:10.4f} {cb:10.4f} {100*(b>2).mean():6.1f}% {(b>=3).sum():6d}")
    print(f"\n  fresh == cache everywhere in the raster: "
          f"{np.allclose(np.percentile(Y,90,axis=1), ST[u,:,i90], atol=1e-4)}")
    print(f"  f1 line 23  distinct codes: {sorted(set(Y[19].tolist()))[:12]}")
    print(f"  f2 line 286 distinct codes: {sorted(set(Y[282].tolist()))[:12]}")
