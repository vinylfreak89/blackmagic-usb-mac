#!/usr/bin/env python3
"""Where, horizontally, the head switch's blanking sits inside the delivered window.

The device delivers 720 of the line's 858 samples, so a row whose line timing is normal carries
no horizontal blanking at all: the blanking interval (about 147 samples) lies outside the window.
A row carried by the other head is timed differently, and its blanking slides into the window.
WHERE it lands is a direct readout of that row's horizontal timing displacement, in samples of the
13.5 MHz clock (74 ns each).

Per row this reports the leading blank run, the trailing blank run, and the longest interior run
with the column it starts at, measured against THAT FIELD's own regenerated blanking level - the
rows above the picture, which carry no signal - never a typed constant.

A run that touches the left edge is TRUNCATED: its true start is outside the window, so its
column is a lower bound and its length is not the blanking interval. That is a distinct state
from "no blanking here", and conflating the two is how a displaced row reads as an ordinary one.

  tear_column_census.py <capture.tpc> [--repair] [--from N] [--rows LO HI]
  -> counter, field, line, mean, lead, trail, run_len, run_col, state
"""
import argparse, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
F1,F2 = 23,286                 # picture origins, NTSC lines
BLANK_F1 = (12,18)             # NTSC lines above the picture that carry no signal: the field's own zero
MARGIN   = 4.0                 # codes above that zero still counted as blanking
FULL_MIN = 100                 # a run this long is the whole blanking interval, so the row is fully switched
PART_MIN = 10                  # an interior run shorter than this is not blanking, it is content
LEAD_MIN = 20                  # every line delivers a few samples of its own front porch (4-10 measured on
                               # capture 1), so a LEADING run only means displacement once it clearly exceeds that

def runs(row, thr):
    b = row <= thr; n=len(b)
    lead=0
    while lead<n and b[lead]: lead+=1
    trail=0
    while trail<n and b[n-1-trail]: trail+=1
    best_len, best_col = 0, -1
    i=lead
    while i < n-trail:
        if b[i]:
            j=i
            while j<n-trail and b[j]: j+=1
            if j-i>best_len: best_len, best_col = j-i, i
            i=j
        else: i+=1
    return lead, trail, best_len, best_col

def classify(lead, trail, rl, rc):
    if lead >= LEAD_MIN:                       # the run reaches the left edge: start unobservable
        return ("truncated_full" if lead >= FULL_MIN else "truncated_part"), lead, 0
    if rl >= FULL_MIN:  return "full", rl, rc
    if rl >= PART_MIN:  return "partial", rl, rc
    return "none", rl, rc

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("capture")
    ap.add_argument("--repair",action="store_true")
    ap.add_argument("--from",dest="frm",type=int,default=0)
    ap.add_argument("--rows",nargs=2,type=int,default=[230,242],
                    help="rows below the picture origin to walk (default 230 242 = NTSC 253-264 / 516-527)")
    a=ap.parse_args(); st={"buf":bytearray(),"prev":None}
    LO,HI=a.rows
    def do_field(ctr, Y, origin, fld):
        z = float(np.median(Y[(BLANK_F1[0]-4)+(origin-F1):(BLANK_F1[1]-4)+(origin-F1)]))
        thr = z + MARGIN
        for off in range(LO,HI):
            line = origin + off
            r = Y[line-4]
            lead,trail,rl,rc = runs(r.astype(np.float64), thr)
            state, L, C = classify(lead,trail,rl,rc)
            print(f"{ctr}\t{fld}\t{line}\t{r.mean():.2f}\t{lead}\t{trail}\t{L}\t{C}\t{state}")
    def emit(u):
        ctr=int.from_bytes(u[4:6],"little")
        r=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)
        if a.repair:
            p=st["prev"]; st["prev"]=(ctr,r)
            if p is None: return
            pctr,pr=p
            if pctr < a.frm: return
            do_field(pctr, r[:,1::2], F1, 1); do_field(pctr, pr[:,1::2], F2, 2)
        else:
            if ctr < a.frm: return
            Y=r[:,1::2]; do_field(ctr,Y,F1,1); do_field(ctr,Y,F2,2)
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
