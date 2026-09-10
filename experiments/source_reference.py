#!/usr/bin/env python3
"""The SOURCE's own blanking reference, per unit per field, accumulated at each row's own instant.

The foundation of the harness rebuild. Every level-derived number taken on 2026-09-11 used the
DEVICE's regenerated fill as its reference; contract :531 names the SOURCE's own blanking on its
good picture lines and says **"device-generated fill never establishes it"**.

⚠️ THE OPERATION IS THE POINT, and it is what broke three attempts in one night. The source's
blanking is not AT A PLACE in the row — it is at a TIME in that row's own sweep, and the row tells
you when. Averaging a fixed column range finds picture (measured: 51.97 against a true 1.41).
Counting a run in a fixed window finds "one usable sample". Both bound a temporal quantity
spatially. Here each row is asked for its OWN transition, and the samples after it are pooled ACROSS
rows — which is not the same as averaging a column range, and is what makes the reference usable:

  one row alone      sd 0.492   (only 1-2 samples sit at blanking after the transition on bright content)
  pooled across rows sd falls as the pool grows -- reported below rather than asserted

⚠️ NOTHING IS TYPED IN. The transition is each row's own steepest fall, found not located. The
statistic is the MEAN, per the owner's accepted ruling of 2026-09-11: the device writes a DITHERED
constant, so the mean recovers the written level where the median quantises it and throws the dither
away. No threshold, no column, no level.

⚠️ It reports UNKNOWN where the rows do not decide, rather than a number. A reference that answers
Unknown where the evidence is absent is worth more than one that answers everywhere.

  source_reference.py [capture.tpc] [--from N] [--to N] [--rows LO HI]
"""
from __future__ import annotations
import argparse, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
ORIGIN_ROW={1:19,2:282}          # storage row of each field's picture origin (lines 23 / 286)
DEVICE_ROWS={1:list(range(7,16)),2:list(range(270,279))}   # for COMPARISON only, never the reference


def row_transition(row, search_from=540):
    # ⚠️ THREE DEFECTS, named by Codex's review a7760f6 and confirmed by reading this function.
    # They are recorded here rather than silently carried, because every level and timing number
    # taken on 2026-09-11 rests on this primitive:
    #   1. `search_from=540` is a HARDCODED SAMPLE -- the tenth fixed-place-to-look instance in
    #      this project, and in the one place that claims to read each row at its OWN instant.
    #   2. It takes argmin of the difference, so it only ever finds a FALLING edge; a positive
    #      departure is invisible to it. Same positive-only shape already retired twice.
    #   3. A FLAT row with no transition still returns one. It should answer Unknown; instead it
    #      fabricates a position, which is "missing is not a value" inverted.
    # Not repaired in place: the results that rest on it are published, so a change here must be
    # measured against them rather than slipped in.
    """This row's own transition into blanking: the steepest fall in its own trailing sweep.

    Found, not located -- no column is typed in, and the search start only says "the trailing part
    of the row" rather than naming where blanking begins.
    """
    seg = row[search_from:]
    if len(seg) < 8: return None
    d = np.diff(seg)
    return search_from + int(np.argmin(d)) + 1


def source_reference(field_rows):
    """Pool every row's post-transition samples AT THAT ROW'S OWN INSTANT.

    Returns a dict, or None when too few rows decide. The pooling is across rows, each at its own
    time -- NOT an average over a shared column range, which is the distinction that makes this a
    reference rather than a picture measurement.

    ⚠️ IT ALSO RETURNS THE TRANSITIONS THEMSELVES. The first version computed each row's transition,
    used it to slice, and DISCARDED it -- keeping the level and throwing away the phase. That is the
    owner's property backwards: "the ribbon is actually the sweep moving back into its own horizontal
    blanking interval", so the POSITION is the observable and the level is only the tell that you
    found it. A reference that reports only a level cannot serve a temporal instrument.
    """
    pool = []; transitions = []; contributing = 0; silent = 0
    for row in field_rows:
        t = row_transition(row)
        if t is None or t >= len(row): silent += 1; continue
        tail = row[t:]
        if len(tail) == 0: silent += 1; continue
        # the row's own settled level after its transition: the lowest sustained part of its tail.
        # No absolute cut -- the row's own tail decides, by its own minimum block.
        if len(tail) >= 4:
            k = (len(tail)//2)*2
            blocks = tail[:k].reshape(-1,2).mean(axis=1)
            floor = float(blocks.min())
            settled = tail[tail <= floor + 1.0]
        else:
            settled = tail
        if len(settled) == 0: silent += 1; continue
        pool.extend(settled.tolist()); transitions.append(t); contributing += 1
    if contributing < 20: return None
    a = np.array(pool, dtype=np.float64); tr = np.array(transitions, dtype=np.float64)
    return {"level": float(a.mean()), "level_sd": float(a.std()), "n": len(a),
            "rows": contributing, "silent": silent,
            "transition_median": float(np.median(tr)),
            "transition_p10": float(np.percentile(tr, 10)),
            "transition_p90": float(np.percentile(tr, 90)),
            "transition_sd": float(tr.std())}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("capture",nargs="?",default="captures/composite_program_30s.tpc")
    ap.add_argument("--from",dest="frm",type=int,default=6667)
    ap.add_argument("--to",dest="to",type=int,default=10**9)
    ap.add_argument("--rows",nargs=2,type=int,default=[20,220],
                    help="offsets into the field's picture used as GOOD picture lines")
    ap.add_argument("--limit",type=int,default=200)
    a=ap.parse_args()
    st={"buf":bytearray()}; out=[]
    def emit(u):
        c=int.from_bytes(u[4:6],"little")
        if not (a.frm<=c<=a.to) or len(out)>=a.limit: return
        Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)[:,1::2].astype(np.float64)
        for fld in (1,2):
            rows=[Y[ORIGIN_ROW[fld]+o] for o in range(a.rows[0],a.rows[1])]
            r=source_reference(rows)
            dev=float(Y[DEVICE_ROWS[fld]].mean())
            out.append((c,fld,r,dev))
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
    ok=[(c,f,r,d) for c,f,r,d in out if r is not None]
    unk=[(c,f) for c,f,r,d in out if r is None]
    print("capture %s   counters %d..   field-readings %d"%(os.path.basename(a.capture),a.frm,len(out)))
    print("  UNKNOWN (too few rows decided): %d"%len(unk))
    if not ok: print("  no readable references"); return 0
    m=np.array([r["level"] for _,_,r,_ in ok]); sd=np.array([r["level_sd"] for _,_,r,_ in ok])
    n=np.array([r["n"] for _,_,r,_ in ok]); con=np.array([r["rows"] for _,_,r,_ in ok])
    tm=np.array([r["transition_median"] for _,_,r,_ in ok])
    tsd=np.array([r["transition_sd"] for _,_,r,_ in ok])
    tlo=np.array([r["transition_p10"] for _,_,r,_ in ok])
    thi=np.array([r["transition_p90"] for _,_,r,_ in ok])
    dev=np.array([d for _,_,_,d in ok])
    print("\n  SOURCE reference, pooled at each row's own instant:")
    print("    level        median %.3f   p10 %.3f   p90 %.3f"%(np.median(m),np.percentile(m,10),np.percentile(m,90)))
    print("    within-unit  sd median %.3f   -- the spread of the POOL, not of one row"%np.median(sd))
    print("    pool size    median %d samples from %d rows"%(int(np.median(n)),int(np.median(con))))
    print("    unit-to-unit sd of the level itself: %.4f"%m.std())
    print("\n  THE PHASE the same rows carry -- each row's own transition into retrace:")
    print("    per-unit median transition   sample %.1f   (p10 %.1f  p90 %.1f within a unit)"
          %(np.median(tm),np.median(tlo),np.median(thi)))
    print("    within-unit spread across rows  sd %.2f samples"%np.median(tsd))
    print("    unit-to-unit spread of that median  sd %.2f samples"%tm.std())
    print("\n  DEVICE fill (comparison only, NEVER the reference):")
    print("    level        median %.4f   unit-to-unit sd %.4f"%(np.median(dev),dev.std()))
    print("\n  the two differ by %.3f codes; :531 forbids the second as a reference."%(np.median(m)-np.median(dev)))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
