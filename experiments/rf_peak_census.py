#!/usr/bin/env python3
"""The head switch's RF peak: is there one on this row, and where along the row does it sit.

LINE NUMBERS ARE FIELD-RELATIVE (owner's ruling, 2026-09-10: "Field 2's picture should be the same
as field 1. I want fucking field line numbers. That's the way every one in the industry does it").
Each field carries its own count, so BOTH fields' pictures are lines 23-262. ⚠️ It does NOT follow
that both switch bands land on the same lines: renaming cannot move an observation. Measured on
capture 1, field 1's first FULLY switched line is 261 and field 2's is 260, so field 2's band is
one line longer - the asymmetry survives the renaming and is a measurement, not a consequence of it. The frame-continuous numbering this file used before - field 2 at 286-525 - is
withdrawn. Row arithmetic is unchanged; only the printed label is.

The contract describes the head switch as discontinuous horizontal skew, an RF peak in the luma,
or both. The peak's polarity is not fixed - it reads pure white in some units and pure black in
others (owner, 2026-09-09) - so the detector is signed-blind: it looks for the largest excursion
from the row's own median in EITHER direction, measured in units of that row's own MAD, and
reports its column and sign. No amplitude is typed in; the statistic is reported and the
population is read off the distribution.

Rows walked are the last few picture rows of each field, where the switch lives.

  rf_peak_census.py <capture.tpc> [--repair] [--from N] [--to N]
  -> counter, field, line, row_median, row_MAD, peak_sigma, peak_col, peak_sign, peak_len
"""
import argparse, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
F1,F2 = 23,286
LO,HI = 232, 240      # positions within the field's 240 picture rows: the last eight

def peak(row):
    med=float(np.median(row))
    mad=float(np.median(np.abs(row-med)))
    if mad<=0: mad=0.5
    d=(row-med)/mad
    k=int(np.argmax(np.abs(d)))
    sg=1 if d[k]>0 else -1
    # how many contiguous samples stay beyond half the extreme, i.e. how wide the excursion is
    thr=abs(d[k])/2.0
    a=k
    while a>0 and abs(d[a-1])>=thr and np.sign(d[a-1])==sg: a-=1
    b=k
    while b<len(d)-1 and abs(d[b+1])>=thr and np.sign(d[b+1])==sg: b+=1
    return med, mad, float(abs(d[k])), k, sg, b-a+1

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("capture")
    ap.add_argument("--repair",action="store_true")
    ap.add_argument("--from",dest="frm",type=int,default=0)
    ap.add_argument("--to",dest="to",type=int,default=10**9)
    a=ap.parse_args(); st={"buf":bytearray(),"prev":None}
    def do(ctr,Y,origin,fld):
        for off in range(LO,HI):
            line=F1+off                     # FIELD-RELATIVE: both fields count 23-262
            m,md,s,c,sg,ln = peak(Y[origin+off-4].astype(np.float64))
            print(f"{ctr}\t{fld}\t{line}\t{m:.2f}\t{md:.2f}\t{s:.1f}\t{c}\t{sg:+d}\t{ln}")
    def emit(u):
        ctr=int.from_bytes(u[4:6],"little")
        r=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)
        if a.repair:
            p=st["prev"]; st["prev"]=(ctr,r)
            if p is None: return
            pctr,pr=p
            if not (a.frm<=pctr<=a.to): return
            do(pctr,r[:,1::2],F1,1); do(pctr,pr[:,1::2],F2,2)
        else:
            if not (a.frm<=ctr<=a.to): return
            Y=r[:,1::2]; do(ctr,Y,F1,1); do(ctr,Y,F2,2)
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
