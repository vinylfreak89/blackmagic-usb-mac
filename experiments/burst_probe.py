#!/usr/bin/env python3
"""Is there colour burst inside a relocated blanking run, and not inside dark picture?

WHY THIS AND NOT THE POROUS VERSION. Two adjudicators independently described a 2-10 code hump on
the porches of ordinary rows and one called it burst-like. It cannot be burst: from the standards
figures burst runs 5.300-7.814 us after 0H while the delivered window starts at 122 samples =
9.037 us, so burst is over 16.5 samples before the window begins on a normally timed row.
A DISPLACED row is a different matter. Its whole line is time-shifted by far more than that - the
relocated runs on capture 1 sit at columns 20-70 with lengths 147-164 - so a displaced row carries
its burst INTO the window along with its blanking. That makes burst a candidate positive signature
of RELOCATED blanking, which is what the identification method needs, rather than of normal
blanking.

THE PREDICTION IS POSITIONAL AS WELL AS SPECTRAL, and both parts are prespecified here before any
data is read. The blanking interval is 10.9 us = 147.2 samples measured from the front porch's
start; burst occupies 6.800 to 9.314 us into it, which is samples 92 to 126 from the run's start,
holding 9.0 cycles at 13.5/3.579545 = 3.7714 samples per cycle. So burst should appear at THAT
offset inside a relocated run and not elsewhere in it.

WHAT THIS CANNOT SHOW, carried from Codex's conditions and not softened: energy at the subcarrier
frequency is NOT something dark picture cannot have - picture structure and chroma leakage supply
it - so frequency is supporting evidence only. Timing position, oscillatory structure and
specificity against controls all have to be established separately, and a positive result does not
by itself close the identification-method gap.

Method per candidate window: remove a local linear baseline (so a step or a single hump cannot
masquerade as oscillation), then take the quadrature amplitude at the nominal subcarrier - sine and
cosine components, so unknown phase cannot cancel it - normalised by the window's residual RMS.
A scan across frequency is reported alongside as EXPLORATORY ONLY; its largest peak does not
retrospectively become the target.

  burst_probe.py <capture.tpc> [--from N] [--to N]
"""
import argparse, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
F1,F2 = 19,282                 # storage rows of each field's first picture row
FS=13.5e6; FSC=3.579545e6
BURST_OFF_LO, BURST_OFF_HI = 92, 126      # derived above, not fitted
RUN_MIN = 100                  # a run this long is a relocated blanking interval
BLANK_MARGIN = 4.0

def quad_amp(x, f=FSC):
    """quadrature amplitude at f, after a local linear baseline is removed, normalised by residual RMS"""
    n=len(x)
    if n < 8: return float('nan'), float('nan')
    t=np.arange(n)
    a,b=np.polyfit(t,x,1)
    r=x-(a*t+b)
    rms=float(np.sqrt(np.mean(r*r)))
    w=2*np.pi*f/FS
    c=float(np.dot(r,np.cos(w*t))*2/n); s=float(np.dot(r,np.sin(w*t))*2/n)
    return float(np.hypot(c,s)), rms

def runs(row, thr):
    b=row<=thr; n=len(b)
    lead=0
    while lead<n and b[lead]: lead+=1
    trail=0
    while trail<n and b[n-1-trail]: trail+=1
    out=[]
    i=lead
    while i<n-trail:
        if b[i]:
            j=i
            while j<n-trail and b[j]: j+=1
            out.append((i,j-i)); i=j
        else: i+=1
    if lead>=20: out.append((0,lead))          # a run clipped at the left edge
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("capture")
    ap.add_argument("--from",dest="frm",type=int,default=6667)
    ap.add_argument("--to",dest="to",type=int,default=10**9)
    a=ap.parse_args(); st={"buf":bytearray()}
    print("counter\tfield\trow\tclass\trun_start\trun_len\tamp_burstwin\trms_burstwin\tamp_elsewhere\trms_elsewhere")
    def do(ctr,Y,orig,fld):
        z=float(np.median(Y[(12-4)+(orig-F1):(18-4)+(orig-F1)])); thr=z+BLANK_MARGIN
        for off in range(232,243):                              # the band and the rows below it
            r=Y[orig+off-4].astype(np.float64) if orig+off-4 < LINES else None
            if r is None: continue
            for s,L in runs(r,thr):
                if L < RUN_MIN: continue
                lo,hi = s+BURST_OFF_LO, s+BURST_OFF_HI
                if hi > s+L or hi > 720: continue               # the predicted window must be inside the run
                amp,rms = quad_amp(r[lo:hi])
                # the same width elsewhere in the same run, as the positional control
                elo = s+10
                ehi = elo+(BURST_OFF_HI-BURST_OFF_LO)
                if ehi > s+L: elo,ehi = s+L-(BURST_OFF_HI-BURST_OFF_LO), s+L
                amp2,rms2 = quad_amp(r[elo:ehi])
                print(f"{ctr}\t{fld}\t{orig+off}\trelocated\t{s}\t{L}\t{amp:.4f}\t{rms:.4f}\t{amp2:.4f}\t{rms2:.4f}")
        for off in (40,120,200):                                # dark-picture controls, same widths
            r=Y[orig+off-4].astype(np.float64)
            for s in (120, 300, 500):
                amp,rms = quad_amp(r[s:s+(BURST_OFF_HI-BURST_OFF_LO)])
                print(f"{ctr}\t{fld}\t{orig+off}\tpicture\t{s}\t-1\t{amp:.4f}\t{rms:.4f}\t\t")
    def emit(u):
        ctr=int.from_bytes(u[4:6],"little")
        if not (a.frm<=ctr<=a.to): return
        Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)[:,1::2]
        do(ctr,Y,F1,1); do(ctr,Y,F2,2)
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
