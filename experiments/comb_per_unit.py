#!/usr/bin/env python3
"""Per-unit comb verdict (counter, best shift, margin) - same metric as comb_census.py."""
import sys, os
import numpy as np
sys.path.insert(0, "/Users/vinylfreak89/Documents/blackmagic-usb-mac/experiments")
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
F1,F2,NF=23,286,240; S=2
cap=sys.argv[1]; repair="--repair" in sys.argv
st={"buf":bytearray(),"prev":None,"res":[]}
def emit(u):
    ctr=int.from_bytes(u[4:6],"little")
    r=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)
    if repair:
        p=st["prev"]; st["prev"]=(ctr,r)
        if p is None: return
        pctr,pr=p
        Y1=pr[:,1::2].astype(np.int32); Y2=r[:,1::2].astype(np.int32)
        f1=Y2[(F1-4):(F1-4)+NF]; f2=Y1[(F2-4)-S:(F2-4)+NF+S]; ctr=pctr
    else:
        Y=r[:,1::2].astype(np.int32)
        f1=Y[(F1-4):(F1-4)+NF]; f2=Y[(F2-4)-S:(F2-4)+NF+S]
    e={}
    n=NF-2
    for d in range(-S,S+1):
        bb=f2[S+d:S+d+n]
        if bb.shape[0]!=n: continue
        aa=f1[0:n]; cc=f1[1:n+1]
        e[d]=float(np.maximum((aa-bb)*(cc-bb),0)[:,24:696].mean())
    if len(e)<2*S+1: return
    best=min(e,key=e.get); others=[e[d] for d in e if d!=best]
    st["res"].append((ctr,best,min(others)/max(e[best],1e-9),e[best]))
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
walk_tagged(cap,on_video=on_video,progress=False)
for ctr,best,marg,ener in st["res"]:
    print(f"{ctr}\t{best:+d}\t{marg:.2f}\t{ener:.1f}")
