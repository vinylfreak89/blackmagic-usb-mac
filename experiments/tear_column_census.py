#!/usr/bin/env python3
"""Where, horizontally, the head switch's blanking sits inside the delivered window.

⚠️ CORRECTED 2026-09-10, and the sentence that stood here was wrong. It read "a row whose line
timing is normal carries no horizontal blanking at all: the blanking interval lies outside the
window". A correctly timed row DOES carry blanking inside the window, at BOTH ends, and the
standard requires it: the 525 line is 858 samples at 13.5 MHz, horizontal blanking is 10.9 us =
147.15 samples, so the ANALOG active line is 52.6556 us = 710.85 samples - and BT.601's digital
active line is 720, WIDER than the picture by 9.15 samples, positioned 122 samples after 0H while
the picture starts at 126.9. So about 4.9 samples of back porch sit inside the left edge and 4.25
of front porch inside the right. Measured on 33,150 picture rows of capture 1 per field
(experiments/porch_census.py): leading run median 4-5 samples, absent in 0.0-0.9% of rows;
trailing run never zero.

What a normally timed row does NOT carry is the blanking interval's ~147-sample BLOCK inside the
window. A row carried by the other head is timed differently and that block slides in. WHERE it
lands is a direct readout of that row's horizontal timing displacement, in samples of the 13.5 MHz
clock (74 ns each). So this instrument never asks "is blanking present" - it asks for an interior
run at the blanking interval's scale, or a leading run far larger than the porch.

Per row this reports the leading blank run, the trailing blank run, and the longest interior run
with the column it starts at, measured against THAT FIELD's own regenerated blanking level - the
rows above the picture, which carry no signal - never a typed constant.

A run that touches the left edge is TRUNCATED: its true start is outside the window, so its
column is a lower bound and its length is not the blanking interval. That is a distinct state
from "no blanking here", and conflating the two is how a displaced row reads as an ordinary one.

⚠️ NOT EVERY ROW OF THE UNIT IS A LINE OF THE SIGNAL, and an earlier version of this reported
device fill as if it were (owner, 2026-09-10: "how is it getting readings off line 263 and 264 at
all"). Measured on capture 1, identical in all 38 units checked: rows 0-6, 261-269 and 523-524 are
exactly Y16 with zero variance - the device's own digital padding, 18 rows, leaving 507 digitised.
Rows 259-260 and 522 are the device's WRITTEN blanking, not sampled signal: mean 1.375-1.382 with
lag-1 autocorrelation -0.30 to -0.34, the dither signature CLAUDE.md uses to tell written from
digitised (a picture row's own front porch reads 1.716 at -0.089). Field 1's last row carrying
signal is 258 and field 2's is 521, which are exactly NTSC lines 262 and 525 - the last active
line of each field in SMPTE RP-202. So the row-to-line map holds inside each field's active
picture and means nothing past it; those rows are labelled by REGION here rather than given a
line number that does not exist.
The written-blanking rows carry NOTHING from the tape, measured rather than assumed: over 38 units
whose own picture brightness ranges 17.4 to 119.1, their per-unit mean is 1.3818 and 1.3750 with a
standard deviation of 0.0103 and 0.0080, and its correlation with that brightness is -0.031 and
+0.097 (an ordinary picture row: +0.989). Their bytes do differ unit to unit - 38 distinct patterns
of 38 - but only as dither; the padding rows are byte-identical in all 38. So neither is readable
evidence, and the difference between them is only which filler the device chose.

THE OFFSET IS +4 AND IT IS NOW MEASURED, not carried from the record (2026-09-10). CEA-608 puts
captions on line 21 of field 1 and line 284 of field 2, by standard. Decoding every candidate row
at the top of each field as CEA-608 with odd parity over 38 units: exactly one row passes in each
field, in 38 of 38 units, and no other row passes in any unit. Those two rows are 4 below their
standard line numbers - the same 4 in BOTH fields, so it is one whole-frame shift and not something
that accumulates between them. Before this the offset rested on the assumption that the device's
synthetic insert sits where the standard says; it now rests on the waveform decoding there.
⚠️ What still cannot be measured from this side is the raster's absolute position against vertical
sync: the device delivers decoded YCbCr, so no sync waveform survives to align against.

THE WHOLE 525, in NTSC lines. The two fields' inserts correlate at +1.000 across a separation of
263 - the standard's inter-field spacing - so the unit is ONE continuous frame raster, not two
field blocks, and NTSC's line numbering runs continuously 1-525 without resetting per field.
Classification stable in all 38 units checked except line 526:

    4 - 10    7 rows   flat 16, the device's padding
   11 - 19    9 rows   written blanking
   20 - 21    2 rows   digitised: the Shuttle's own inserted timing line and line 21
   22         1 row    written blanking
   23 - 262 240 rows   digitised: FIELD 1's active picture, exactly the standard's 240
  263 - 264   2 rows   written blanking          <- the interval between the fields
  265 - 273   9 rows   flat 16, the device's padding
  274 - 282   9 rows   written blanking
  283 - 284   2 rows   digitised: field 2's inserts
  285         1 row    written blanking
  286 - 525 240 rows   digitised: FIELD 2's active picture, exactly the standard's 240
  526         1 row    written blanking
  527 - 528   2 rows   flat 16, the device's padding

  484 digitised, 23 written blanking, 18 padding = 525.

Lines 1-3 are not delivered at all. Of the rows that ARE delivered above field 1's picture, not one
carries a sample from the tape: per-pixel standard deviation ACROSS the 38 units is 0.48 on the
written-blanking rows and 0.53/0.60 on the two inserted lines - the device draws the same waveform
every unit - against 63-68 on a picture row. The first delivered row containing anything from the
tape is line 23.

  tear_column_census.py <capture.tpc> [--repair] [--from N] [--rows LO HI]
  -> counter, field, line, mean, lead, trail, run_len, run_col, state, region
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
LEAD_MIN = 20                  # every line delivers its own back porch inside the window - median 4-5 samples,
                               # p90 6, max 8 at this threshold over 33,150 picture rows of capture 1 - so a
                               # LEADING run only means displacement once it clearly exceeds that

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

def region(row):
    """what the device put in this row: its own padding, its own written blanking, or a sampled line"""
    if row.min()==16 and row.max()==16: return "device_padding"      # Y16 exact, zero variance
    if row.max()<=5 and row.std()<1.0:  return "device_blanking"     # the written dithered 1.375
    return "line"

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
            r = Y[line-4].astype(np.float64)
            reg = region(r)
            if reg != "line":
                # device fill: report it as what it is, never as a blank-run measurement
                print(f"{ctr}\t{fld}\t{line}\t{r.mean():.2f}\t-1\t-1\t-1\t-1\tnot_a_line\t{reg}")
                continue
            lead,trail,rl,rc = runs(r, thr)
            state, L, C = classify(lead,trail,rl,rc)
            print(f"{ctr}\t{fld}\t{line}\t{r.mean():.2f}\t{lead}\t{trail}\t{L}\t{C}\t{state}\tline")
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
