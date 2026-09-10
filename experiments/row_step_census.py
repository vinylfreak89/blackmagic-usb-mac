#!/usr/bin/env python3
"""Where the head boundary falls, measured on the picture rather than on the blanking.

LINE NUMBERS ARE FIELD-RELATIVE (owner's ruling, 2026-09-10: "Field 2's picture should be the same
as field 1. I want fucking field line numbers. That's the way every one in the industry does it").
Each field carries its own count, so BOTH fields' pictures are lines 23-262 and both switch bands
are 260-262. The frame-continuous numbering this file used before - field 2 at 286-525 - is
withdrawn. Row arithmetic is unchanged; only the printed label is.

The owner, 2026-09-10: testing line 260 against 261 is "the no shit duh case" - both are already
inside the band. The boundary that carries information is the LAST ORDINARY PICTURE LINE against
the FIRST LINE OF THE BAND, 259->260 in field 1 and 522->523 in field 2.

The head switch displaces line timing, so two rows carried by the same head sit at the same
horizontal position and two rows either side of the handover do not. This measures that directly:
the horizontal displacement of each row against the row above it, by cross-correlating their
picture content over samples 260-460 - a window clear of the relocated blanking in every row of
this band, so the reading never depends on the blanking being visible. A row pair whose peak is
not distinct is reported unmeasurable rather than given a number.

  row_step_census.py <capture.tpc> [--repair] [--from N] [--to N]
  -> counter, field, upper_line, lower_line, step_samples ('' if unmeasurable)
"""
import argparse, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
F1,F2 = 23,286
LO,HI,MAXLAG = 260,460,250      # window and search, both inside the delivered 720
PAIRS1=((256,257),(257,258),(258,259),(259,260),(260,261),(261,262))
PAIRS2=tuple((a+263,b+263) for a,b in PAIRS1)
MARGIN=1.15                     # the peak must beat everything outside +-8 samples by this much

def step(lower,upper):
    x=lower[LO:HI]; x=x-x.mean()
    if x.std()<3.0: return None
    sc=np.empty(2*MAXLAG+1)
    for i,L in enumerate(range(-MAXLAG,MAXLAG+1)):
        w=upper[LO+L:HI+L]; w=w-w.mean()
        d=np.sqrt(np.dot(x,x)*np.dot(w,w))
        sc[i]=np.dot(x,w)/d if d>0 else 0.0
    k=int(np.argmax(sc))
    other=np.concatenate([sc[:max(0,k-8)],sc[min(len(sc),k+9):]])
    if other.size and sc[k] < MARGIN*other.max(): return None
    return k-MAXLAG

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("capture")
    ap.add_argument("--repair",action="store_true")
    ap.add_argument("--from",dest="frm",type=int,default=0)
    ap.add_argument("--to",dest="to",type=int,default=10**9)
    a=ap.parse_args(); st={"buf":bytearray(),"prev":None}
    def do(ctr,Y,fld,pairs,base):
        for u,l in pairs:
            s=step(Y[u+base+1-4].astype(np.float64), Y[u+base-4].astype(np.float64))
            print(f"{ctr}\t{fld}\t{u}\t{l}\t{'' if s is None else s}")   # FIELD-RELATIVE labels
    def emit(u):
        ctr=int.from_bytes(u[4:6],"little")
        r=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)
        if a.repair:
            p=st["prev"]; st["prev"]=(ctr,r)
            if p is None: return
            pctr,pr=p
            if not (a.frm<=pctr<=a.to): return
            do(pctr,r[:,1::2],1,PAIRS1,0); do(pctr,pr[:,1::2],2,PAIRS1,F2-F1)
        else:
            if not (a.frm<=ctr<=a.to): return
            Y=r[:,1::2]; do(ctr,Y,1,PAIRS1,0); do(ctr,Y,2,PAIRS1,F2-F1)
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
    walk_tagged(a.capture,on_video=on_video,progress=False)

if __name__=="__main__": main()
