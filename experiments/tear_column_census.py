#!/usr/bin/env python3
"""Where, horizontally, the head switch's blanking sits inside the delivered window.

LINE NUMBERS ARE FIELD-RELATIVE (owner's ruling, 2026-09-10: "Field 2's picture should be the same
as field 1. I want fucking field line numbers. That's the way every one in the industry does it").
Each field carries its own count, so BOTH fields' pictures are lines 23-262 and both switch bands
are 260-262. The frame-continuous numbering this file used before - field 2 at 286-525 - is
withdrawn. Row arithmetic is unchanged; only the printed label is.

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

⚠️ THE UNIT IS TWO STACKED FIELD BLOCKS, NOT AN INTERLEAVED FRAME RASTER (owner, 2026-09-10:
"it sends the two fields stacked one on top of the other"; measured the same day). An earlier
version of this file claimed one continuous frame raster because the two caption rows correlate at
+1.000 across 263 rows. That test cannot tell the two apart: BOTH predict 263, since the frame's
two caption lines are 263 apart and so are the 18th rows of two 263-row blocks. The discriminator
is what lies BETWEEN them - row against row+263 correlates +0.869 mean / +0.933 median, the
HIGHEST of any offset tested, above row against row+1 (+0.834/+0.908), with a row+131 control at
+0.436. Rows 263 apart are therefore ADJACENT DISPLAY LINES, which is stacking; under interleaving
they would be 131 display lines apart and look like the control. The structure agrees: each field's
240 picture rows are CONTIGUOUS, two blocks separated by 23 rows of fill, where interleaving would
put all 480 in one run. The +4 offset is therefore measured WITHIN each block and runs one-for-one
from that block's caption row to the end of its picture (row 17 to row 258 is 242 rows; line 21 to
line 262 is 242 lines). It does not continue past a field's last line into the next field's.

THE BLOCK BOUNDARY IS SETTLED (owner, 2026-09-10, measured the same day). Walking the 525 rows
CYCLICALLY - the unit repeats, so a run crossing its end is one run - the structure appears twice,
identically, and the boundary falls where the two copies align:

   field 1's block                          field 2's block
     1 written   row 522                      1 written   row 260
     9 PADDING   rows 523,524,0-6             9 PADDING   rows 261-269
     9 written   rows 7-15                    9 written   rows 270-278
     2 inserts   rows 16-17                   2 inserts   rows 279-280
     1 written   row 18                       1 written   row 281
   240 picture   rows 19-258                240 picture   rows 282-521
     1 written   row 259   <- the extra           (none)
   -----------                              -----------
   263 rows      lines 1-263                262 rows      lines 264-525

FIELD 1 GETS THE EXTRA ROW, and it is the half line, 263 - which is why: field 1 spans 263
line-times and field 2 spans 262, so the block sizes are the fields' own line counts rather than
a rounding. Lines 1, 2 and 3 ARE delivered, at rows 522, 523 and 524, at the END of the unit,
because a block's start wraps there; an earlier claim here that they are not delivered is
withdrawn. So is the retraction of row 260's label: 264 IS a field 2 line and row 260 is the
FIRST row of field 2's block, not a row past field 1's end. Every anchor lands - row 17 -> line 21
and row 280 -> line 284, both decoding CEA-608 in 38 of 38 units; row 19 -> 23 and row 258 -> 262;
row 282 -> 286 and row 521 -> 525.

NAMING (owner's ruling, 2026-09-10: "Properly label them 262.5 and 1"). Field 1's last row is the
HALF LINE and is written 262.5, never 263: a half line is the second half of 262 and the first half
of what follows, which is why a field counts 262.5 lines, and calling it 263 asserts a whole line
where the standard has half of one. The first row of field 2's block is that field's own line 1.
An earlier "no anchor below field 2's caption" paragraph here, and its arithmetic "lines 526-528"
for the last three delivered rows, are both superseded by the block structure above: those three
rows are field 1's lines 1, 2 and 3, at the start of its block.
⚠️ WHAT IS NOT SETTLED, and is not swept here: whether FIELD 2's lines are numbered per block too.
The ruling names the two rows; it does not say whether field 2's picture is 286-525 (the frame-
continuous numbering CLAUDE.md's coordinate convention states, and which the contract, the engine's
constants and every field-2 figure measured tonight use) or 23-262 (per block, the same numbers as
field 1). Those are the same rows under two conventions and renumbering would move every field-2
line number in the project. That is a decision for the owner and Codex together, not a harness
sweep, so field 2 is left on the existing convention below and the disagreement is named rather
than resolved.
Classification stable in all 38 units checked except the third-from-last row:

  FIELD 1's BLOCK, its own line numbers
  line    1        1 row    written blanking      (delivered at the END of the unit, rows 522-524
  lines   2 -  10  9 rows   flat 16, padding       carry lines 1, 2 and 3 - the block wraps there)
  lines  11 -  19  9 rows   written blanking
  lines  20 -  21  2 rows   digitised: the device's two inserted lines, the 2nd the CEA-608
                            caption row, which the standard puts on line 21 - THE ANCHOR
  line   22        1 row    written blanking
  lines  23 - 262 240 rows  digitised: FIELD 1's active picture, exactly the standard's 240
  line  262.5      1 row    written blanking - THE HALF LINE, the last row of field 1's block
  FIELD 2's BLOCK  (line numbers below on the frame-continuous convention - see the note above)
  line    1 of f2  1 row    written blanking - the FIRST row of field 2's block (frame-continuous
                            numbering calls this 264)
  lines 265-273    9 rows   flat 16, padding
  lines 274-282    9 rows   written blanking
  lines 283-284    2 rows   digitised: field 2's inserts, the 2nd its CEA-608 row (line 284)
  line  285        1 row    written blanking
  lines 286-525  240 rows   digitised: FIELD 2's active picture, exactly the standard's 240

  484 digitised, 23 written blanking, 18 padding = 525.

NOTHING WRAPS AND NOTHING CARRIES OVER, measured 2026-09-10 after the owner asked whether the
device is looping around the raster to make these rows. Over 38 units, 874 written-blanking rows
examined: ZERO exact byte repeats - every written row in every unit is a distinct pattern. The half
line 262.5 of one unit against the same row of the next correlates +0.054 (max 0.117 over 30
consecutive pairs), against field 2's line 1 of the next -0.009, against the next unit's first
written row -0.002, against the next unit's last delivered row +0.010; within one frame, 262.5
against every other written row peaks at |r| 0.086. The flat-16 padding is the opposite and shows what reuse looks like: ONE
identical byte pattern in all 38 units.
What the generator is doing is representable: each written row is about 62% at code 1 and 38% at
code 2, mean 1.38, because the level falls between two integers. The two codes are deliberately
SPREAD rather than scattered - two high samples land adjacent in 6.35% of positions against 14.31%
by chance, and lag-1 autocorrelation is -0.325 where the identical samples shuffled give -0.002.
Not periodic at any lag to 16, and the running error is smaller than a shuffle's (6.5-7.5 against
8-12 per row) but not bounded near one code, so it is not classic error diffusion either. Per-row
generator, algorithm not identified.
That also explains why there are two kinds of fill and not one: 16 is an integer the device can
write exactly, 1.375 is not. Which rows get which is still not known from this side.

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
            line = F1 + off                 # FIELD-RELATIVE: both fields count 23-262
            r = Y[origin + off - 4].astype(np.float64)
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
