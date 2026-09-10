#!/usr/bin/env python3
"""Is the horizontal blanking inside the delivered window on an ORDINARY picture row?

LINE NUMBERS ARE FIELD-RELATIVE (owner's ruling, 2026-09-10: "Field 2's picture should be the same
as field 1. I want fucking field line numbers. That's the way every one in the industry does it").
Each field carries its own count, so BOTH fields' pictures are lines 23-262. ⚠️ It does NOT follow
that both switch bands land on the same lines: renaming cannot move an observation. Measured on
capture 1, field 1's first FULLY switched line is 261 and field 2's is 260, so field 2's band is
one line longer - the asymmetry survives the renaming and is a measurement, not a consequence of it. The frame-continuous numbering this file used before - field 2 at 286-525 - is
withdrawn. Row arithmetic is unchanged; only the printed label is.

Arithmetic from SMPTE 170M / BT.601 first, because it decides the question before any pixel is
read. The 525 line is 63.5556 us = 858 samples at 13.5 MHz; horizontal blanking is 10.9 us =
147.15 samples; so the ANALOG active line is 52.6556 us = 710.85 samples. BT.601's digital
active line is 720 samples - WIDER than the picture by 9.15 samples - and it is positioned 122
samples after 0H while the picture starts at 126.9. So a correctly timed source puts about 4.9
samples of back porch inside the LEFT edge of the window and about 4.25 of front porch inside
the RIGHT edge. Blanking at both edges is what a valid line looks like, not a fault.

This measures what is actually there, on picture rows well away from the head-switch band, at
several thresholds, so a short reading can be told from a threshold artefact. It also prints the
mean luma of the first and last samples so the porch can be seen rather than inferred.

  porch_census.py <capture.tpc> [--repair] [--from N] [--to N]
"""
import argparse, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
F1,F2 = 23,286
BODY_LO, BODY_HI = 7, 228      # rows below the origin: NTSC 30-250 / 293-513, clear of the band
BLANK_REF = (12,18)            # NTSC lines above the picture that carry no signal: the field's zero
EDGE = 32                      # samples of each end whose profile is reported
THR = (2.0,3.0,4.0,6.0,10.0)   # codes above the field's own zero

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("capture")
    ap.add_argument("--repair",action="store_true")
    ap.add_argument("--from",dest="frm",type=int,default=0)
    ap.add_argument("--to",dest="to",type=int,default=10**9)
    a=ap.parse_args(); st={"buf":bytearray(),"prev":None}
    acc={f:{"lead":{t:[] for t in THR},"trail":{t:[] for t in THR},
            "head":np.zeros(EDGE),"tail":np.zeros(EDGE),"n":0,"z":[]} for f in (1,2)}
    def do_field(Y, origin, fld):
        d=acc[fld]
        z=float(np.median(Y[(BLANK_REF[0]-4)+(origin-F1):(BLANK_REF[1]-4)+(origin-F1)]))
        d["z"].append(z)
        blk=Y[(origin-4)+BODY_LO:(origin-4)+BODY_HI].astype(np.float64)
        d["head"]+=blk[:,:EDGE].sum(axis=0); d["tail"]+=blk[:,-EDGE:].sum(axis=0)
        d["n"]+=blk.shape[0]
        for t in THR:
            b = blk <= z+t
            lead = np.argmin(b,axis=1); lead[b.all(axis=1)]=blk.shape[1]
            rb = b[:,::-1]
            trail= np.argmin(rb,axis=1); trail[rb.all(axis=1)]=blk.shape[1]
            d["lead"][t].append(lead); d["trail"][t].append(trail)
    def emit(u):
        ctr=int.from_bytes(u[4:6],"little")
        r=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)
        if a.repair:
            p=st["prev"]; st["prev"]=(ctr,r)
            if p is None: return
            pctr,pr=p
            if not (a.frm<=pctr<=a.to): return
            do_field(r[:,1::2],F1,1); do_field(pr[:,1::2],F2,2)
        else:
            if not (a.frm<=ctr<=a.to): return
            Y=r[:,1::2]; do_field(Y,F1,1); do_field(Y,F2,2)
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
    print(f"picture rows only: lines {F1+BODY_LO}-{F1+BODY_HI-1} in BOTH fields (field-relative "
          f"numbering), clear of the head-switch band\n")
    for f in (1,2):
        d=acc[f]
        if not d["n"]: continue
        print(f"--- FIELD {f}: {d['n']} picture rows, field's own blanking level "
              f"{np.median(d['z']):.2f} ---")
        print("  threshold   leading blank-level run            trailing blank-level run")
        print("  (codes)     min p10 median p90 max  zero%      min p10 median p90 max  zero%")
        for t in THR:
            L=np.concatenate(d["lead"][t]); T=np.concatenate(d["trail"][t])
            print(f"   +{t:<5.1f}     {L.min():3d} {np.percentile(L,10):3.0f} {np.median(L):6.1f}"
                  f" {np.percentile(L,90):3.0f} {L.max():3d}  {100*(L==0).mean():5.1f}      "
                  f"{T.min():3d} {np.percentile(T,10):3.0f} {np.median(T):6.1f}"
                  f" {np.percentile(T,90):3.0f} {T.max():3d}  {100*(T==0).mean():5.1f}")
        h=d["head"]/d["n"]; tl=d["tail"]/d["n"]
        print("  mean luma, first 16 samples of the window:  "+" ".join(f"{v:5.1f}" for v in h[:16]))
        print("  mean luma, last  16 samples of the window:  "+" ".join(f"{v:5.1f}" for v in tl[-16:]))
        print()

if __name__=="__main__": main()
