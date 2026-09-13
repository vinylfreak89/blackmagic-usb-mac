"""Both ends of both fields, raw, as block means -- the panel behind the half-line and
head-switch findings of 2026-09-11.  Device-generated rows (the Shuttle's timing line and
caption inserts at NTSC 20/21/283/284, and the padding ruler) are labelled so they are never
read as tape content.  Reproduces the finding rather than describing it."""

import numpy as np
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; RB=1440; ROWS=525; MARK=b"\x00\x00\xff\xff"
WANT=list(range(6700,6704))
# every line at both ends of both fields, plus the device's own inserts for reference
GROUPS=[("field 1 TOP",     list(range(18,29))),
        ("field 1 BOTTOM",  list(range(257,266))),
        ("field 2 TOP",     list(range(281,292))),
        ("field 2 BOTTOM",  list(range(520,528)))]
DEVICE={20:"Shuttle timing line",21:"Shuttle caption insert",284:"Shuttle caption insert",
        265:"PADDING (device fill)",266:"PADDING",267:"PADDING",268:"PADDING",269:"PADDING",
        270:"PADDING",271:"PADDING",272:"PADDING",273:"PADDING",527:"PADDING",528:"PADDING"}
got={}; state={"buf":bytearray()}
class Done(Exception): pass
def emit(u):
    c=int.from_bytes(u[4:6],"little")
    if c in WANT and c not in got:
        R=np.frombuffer(u,np.uint8)[HDR:].reshape(ROWS,RB)
        got[c]=R[:,1::2].astype(int)
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
c0=sorted(got)[0]
print(f"counter {c0}  (means of 40 luma samples across the 720-sample delivered window)")
print("blanking reads 1.4; the device's padding ruler reads exactly 16.0\n")
for title,lines in GROUPS:
    print(f"--- {title} ---")
    for n in lines:
        if not (0 <= n-4 < ROWS): continue
        v=got[c0][n-4]
        bm=" ".join(f"{v[i:i+40].mean():5.1f}" for i in range(0,720,40))
        tag=DEVICE.get(n,"")
        # is the row split?  compare its left third against its right third
        L=v[:240].mean(); Rr=v[480:].mean()
        split=" SPLIT" if (max(L,Rr)>4 and min(L,Rr)<2.5) else ""
        print(f"{n:>4} {bm}  {tag}{split}")
    print()
