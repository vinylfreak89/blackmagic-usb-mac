#!/usr/bin/env python3
"""The owner's challenge, run over every registerable field-reading of a capture.

His words, relayed 2026-09-11: "I have yet to see a place where S sits above T and there is no
horizontal timing shift. if it finds such a field I'd love to see it."

So: wherever the engine identifies a switch, is a horizontal timing shift actually present? A field
with an identified switch and NO shift anywhere in its band is the counterexample he is asking for,
and this prints those fields rather than only counting them.

"Horizontal timing shift" is HIS test, not a fitted one (ruling of the same day): "the lines own
horizontal blanking is the thing that compares it to... if all the blanking and all the picture
belong where they belong, it aint a head switch like area." So a row shows a shift when its OWN
end-of-row blanking is not where this field puts it -- reference learned per unit per field from
that field's own picture rows (field-relative lines 200-250), 5-95% bands on both start and extent.
Nothing is typed in and no threshold is swept.

⚠️ This is the OPPOSITE direction from the route CLAUDE.md rules out. That one gated the partial-row
test on the OTHER head's relocated blanking arriving (net -186). This asks whether the row's own
blanking has LEFT. They share no threshold.

⚠️ It reports a NEGATIVE the way a negative must be reported: the denominator is field-readings where
the engine identifies a switch, because the question cannot be asked where it does not.

  switch_without_shift.py [capture.tpc] [--from N] [--geometry geometry.csv]
"""
from __future__ import annotations
import argparse, sys, os, csv
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
BLANK={1:list(range(7,16)),2:list(range(270,279))}
BASE={1:19,2:282}                    # storage row of each field's field-relative line 23
REF_LO,REF_HI=177,228                # offsets: field-relative lines 200-250


def runs_at(row, blank):
    m=row<=blank+1.0; out=[]; cur=0; s0=0
    for i,v in enumerate(m):
        if v:
            if cur==0: s0=i
            cur+=1
        elif cur: out.append((s0,cur)); cur=0
    if cur: out.append((s0,cur))
    return out


def at_reference(row, blank, ref):
    """Does this row's own end-of-row blanking sit where this field puts it?"""
    (slo,shi),(nlo,nhi)=ref
    return any(slo<=s<=shi and nlo<=n<=nhi for s,n in runs_at(row,blank))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("capture",nargs="?",default="captures/composite_program_30s.tpc")
    ap.add_argument("--from",dest="frm",type=int,default=6667)
    ap.add_argument("--geometry",default="/private/tmp/run-timing.DdLgYt/plain/geometry.csv")
    a=ap.parse_args()
    eng={}
    for r in csv.DictReader(open(a.geometry)):
        eng[(int(r["counter"]),int(r["field"]))]=(int(r["T"]),int(r["S"]),int(r["clip"]))
    st={"buf":bytearray()}; asked=0; shift=0; counter_ex=[]; unaskable=[]

    def emit(u):
        nonlocal asked, shift
        c=int.from_bytes(u[4:6],"little")
        if c<a.frm: return
        Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)[:,1::2]
        for fld in (1,2):
            T,S,clip=eng.get((c,fld),(-1,-1,-1))
            if S<0 and T<0: continue                      # the switch is not identified: cannot ask
            asked+=1
            blank=float(np.median(Y[BLANK[fld]]))
            starts,lens=[],[]
            for off in range(REF_LO,REF_HI):
                rr=runs_at(Y[BASE[fld]+off].astype(np.float64),blank)
                if rr: starts.append(rr[-1][0]); lens.append(rr[-1][1])
            if len(starts)<20: continue
            ref=((int(np.percentile(starts,5)),int(np.percentile(starts,95))),
                 (int(np.percentile(lens,5)),int(np.percentile(lens,95))))
            # ⚠️ A reference that admits a ONE-SAMPLE run cannot separate "blanking present" from
            # "blanking gone", so the question is UNASKABLE on that field-reading rather than
            # answered by it. This is not a fitted threshold: it is the criterion being unable to
            # distinguish its own two outcomes. The first version of this script lacked the check
            # and produced 62 spurious counterexamples with bands like extent (1,3) and start
            # (0,719) -- every one of them a degenerate reference reporting "no shift" vacuously.
            if ref[1][0] <= 1 or (ref[0][1] - ref[0][0]) > 40:
                unaskable.append((c,fld,ref)); asked-=1; continue
            top=(T if T>0 else S)-4                       # storage row of the band's first line
            bot=(clip-4) if clip>0 else min(top+4,524)
            off_ref=[r for r in range(max(top,0),min(bot,524)+1)
                     if not at_reference(Y[r].astype(np.float64),blank,ref)]
            if off_ref: shift+=1
            else: counter_ex.append((c,fld,T,S,clip,ref))

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
    print("capture %s, counters >= %d" % (a.capture,a.frm))
    print("field-readings where the engine identifies a switch: %d" % (asked+len(unaskable)))
    print("  EXCLUDED as unaskable -- the field's own reference admits a 1-sample run, or its start")
    print("  band spans >40 samples, so it cannot separate blanking-present from blanking-gone: %d"
          % len(unaskable))
    print("  askable: %d" % asked)
    print("  of those, at least one band row's own blanking is OFF its field's reference: %d (%.1f%%)"
          % (shift, 100*shift/asked if asked else 0))
    print("  of those, NO band row shows a shift -- the fields he is asking for:      %d" % len(counter_ex))
    for c,fld,T,S,clip,ref in counter_ex[:25]:
        print("     counter %d field %d  T=%d S=%d clip=%d   reference start %s extent %s"
              % (c,fld,T,S,clip,ref[0],ref[1]))
    if len(counter_ex)>25: print("     ... and %d more" % (len(counter_ex)-25))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
