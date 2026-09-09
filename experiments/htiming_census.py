#!/usr/bin/env python3
"""Per-field horizontal timing instability: the sub-sample position of each row's line-start edge.

The blanking-to-active transition at the start of the delivered window IS the line start. Its
position moves when line time drifts, and it is an edge, so it can be located to a fraction of a
sample - unlike a count of blank samples, which is an integer and pins to its quantization floor
(the first version of this file did that: every field reported an IQR of exactly 2.00 and the
measure could not resolve anything).

Per row: the gradient peak within the first 24 samples, refined by parabolic interpolation on the
three samples around it. Rows whose peak is too weak to locate are reported unmeasurable rather
than given a position. The spread of the located positions across the field's body is the
instability. The body excludes the head-switch band, whose timing is physically different.

  htiming_census.py <capture.tpc> [--repair]
  -> counter, f1 sd, f2 sd, f1 measurable frac, f2 measurable frac, f1 median pos, f2 median pos
"""
import argparse, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
F1,F2 = 23,286
BODY  = 200
EDGE  = 24          # the line-start edge lies within the first EDGE samples of the window
MINPK = 6.0         # a gradient peak below this is not an edge; the row is unmeasurable

def field_stats(Y):
    pos=[]
    for r in range(Y.shape[0]):
        row=Y[r,:EDGE+2].astype(np.float64)
        d=np.diff(row)
        if d.size<3: continue
        k=int(np.argmax(d))
        if d[k]<MINPK or k==0 or k>=d.size-1: continue
        a,b,c=d[k-1],d[k],d[k+1]                      # parabolic refinement of the peak
        den=a-2*b+c
        off=0.0 if den==0 else 0.5*(a-c)/den
        if abs(off)>1: off=0.0
        pos.append(k+off)
    n=Y.shape[0]
    if len(pos)<20: return float('nan'), len(pos)/n, float('nan')
    p=np.array(pos)
    return float(p.std()), len(pos)/n, float(np.median(p))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("capture"); ap.add_argument("--repair",action="store_true")
    a=ap.parse_args(); st={"buf":bytearray(),"prev":None}
    def emit(u):
        ctr=int.from_bytes(u[4:6],"little")
        r=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)
        if a.repair:
            p=st["prev"]; st["prev"]=(ctr,r)
            if p is None: return
            pctr,pr=p
            Y1=r[:,1::2][(F1-4):(F1-4)+BODY]; Y2=pr[:,1::2][(F2-4):(F2-4)+BODY]; ctr=pctr
        else:
            Y=r[:,1::2]; Y1=Y[(F1-4):(F1-4)+BODY]; Y2=Y[(F2-4):(F2-4)+BODY]
        s1,f1,m1=field_stats(Y1); s2,f2,m2=field_stats(Y2)
        print(f"{ctr}\t{s1:.4f}\t{s2:.4f}\t{f1:.3f}\t{f2:.3f}\t{m1:.3f}\t{m2:.3f}")
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
