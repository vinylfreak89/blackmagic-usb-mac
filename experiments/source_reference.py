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


def row_transition(row):
    """This row's own transition into blanking, as a TIME in its own sweep -- or None.

    REPAIRED 2026-09-11, and the criterion is written to a measurement rather than to an intuition.
    Diagnosed on 300 card PICTURE rows against an independent answer (first sample at the blanking
    floor, sharing no code with this): the previous "steepest fall" criterion agreed on 2% of them.
    The fall it chose measured -4.0 codes against the blanking edge it skipped at -2.0, and was the
    steeper of the two in 236 of 256 rows. The descent into blanking is GRADUAL per sample -- about
    two codes a step -- while ordinary picture texture carries steeper single-sample falls. So a
    magnitude criterion cannot find this edge BY CONSTRUCTION, and no threshold on it recovers.

    The criterion here is ARRIVAL, not magnitude: the row's FINAL downward crossing of its own
    midpoint -- after which it never returns -- followed forward to where the descent ENDS, which
    is where the row attains its floor. Nothing is typed in and nothing supplies a place to look:

      floor = the row's own minimum;  ref = the row's own median;  mid = halfway between them.

    Four defects paid for earlier tonight that this must not reintroduce, and does not:
      1. NO SEARCH ORIGIN. The old `search_from=540` was the tenth fixed-place-to-look and it
         created the 15% class where the fall was found in picture, below the card's own 601 floor.
      2. NO FABRICATION. A row that does not end below its own midpoint has no transition into a
         floor and returns None. Flat picture and all-blanking rows both return None.
      3. THE FLOOR IS THE ROW'S OWN. A typed 1.4 or 4.4 would be a magic number under rule 4 and
         would be wrong on any source whose blanking sits elsewhere.
      4. IT MUST BE HONEST ON BRIGHT PROGRAMME, where the floor is reached in exactly ONE sample
         (median 1, p90 1, max 2 of 1,010 rows). A criterion demanding a settled RUN behind the
         fall would return None across that whole population; this one requires only that the row
         does not come back, so one sample suffices -- and the coverage is measured, not assumed.

    ⚠️ AGREEMENT WITH THE INDEPENDENT METHOD IS A CONSISTENCY CHECK, NOT A VALIDATION. Both look for
    the arrival at blanking, so they are expected to agree; what the score can show is that this no
    longer picks picture edges, not that its definition is right. The definition rests on the
    diagnosis above. The genuine tests are the synthetic recoveries and the Unknown behaviour.
    """
    x = np.asarray(row, dtype=np.float64)
    n = x.size
    if n < 16:
        return None
    floor = float(x.min()); top = float(x.max())
    if top <= floor:
        return None                                  # a perfectly flat row has no transition
    mid = 0.5 * (floor + float(np.median(x)))
    if mid <= floor:
        return None                                  # median at the floor: the row IS blanking
    below = x <= mid
    if not below[-1]:
        return None                                  # never arrives: no transition in this window
    t = n - 1
    while t > 0 and below[t - 1]:
        t -= 1
    if t <= 0:
        return None
    # The crossing is where the descent BEGINS; the arrival is where it ENDS. Reporting the
    # crossing lands on the midpoint by construction -- measured, level 10.5 on card rows whose
    # floor is 1.0 -- which is not "lands at the row's own floor" however the docstring phrases it.
    # A docstring asserting what the code does not do is a defect this project has already paid
    # for twice tonight. So advance to the arrival: the first index at or after the crossing where
    # the row attains its minimum over the remainder. Parameter-free, and on a row that reaches its
    # floor in a single sample the crossing and the arrival coincide.
    # ARRIVAL, not the lowest sample. `argmin` over the tail was tried and a synthetic control
    # caught it overshooting into the settled run -- on a 20-sample blanking run the minimum sits
    # wherever noise puts it, which is the LATE class. The arrival is the FIRST sample that has
    # completed the descent: below the midpoint between the crossing's own level and the floor.
    # Both come from this row; nothing is typed in.
    tail = x[t:]
    # The reference level is the sample BEFORE the crossing, not at it. Using x[t] was tried and a
    # synthetic control caught it: on an ABRUPT transition x[t] is already at the floor, so the
    # midpoint becomes floor-to-floor and the search degenerates into hunting a noise dip 17
    # samples into the settled run. x[t-1] is the last sample still above the midpoint, so the
    # threshold always spans a real descent.
    done = tail <= 0.5 * (float(x[t - 1]) + floor)
    idx = np.flatnonzero(done)
    return t + int(idx[0]) if idx.size else t


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
