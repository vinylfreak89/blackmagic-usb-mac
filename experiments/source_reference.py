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


def row_transition(row, _ref_at_crossing=False):
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
    # `_ref_at_crossing` exists ONLY so --selftest can run the rejected variant and require it to
    # fail. Production never passes it. Keeping it as a flag rather than a second function means
    # the control exercises this code, not a copy of it.
    ref_level = float(x[t]) if _ref_at_crossing else float(x[t - 1])
    done = tail <= 0.5 * (ref_level + floor)
    idx = np.flatnonzero(done)
    # A FLATNESS REQUIREMENT WAS TRIED HERE AND REVERTED, recorded so it is not re-tried: requiring
    # the region after the arrival to be quieter than the region before it does reduce fabrication,
    # but it REJECTS A LEGITIMATE MULTI-SAMPLE RAMP -- the ramp's own samples (84, 55, 26) make the
    # after-region's spread large, so a known-good fixture returned None. A false negative on a case
    # whose answer is known is worse than the false positive it was meant to fix. The fabrication
    # rate on same-noise synthetic rows therefore stands as a MEASURED, GATED BOUND (see selftest),
    # not as a defect claimed fixed.
    return t + int(idx[0]) if idx.size else t


def settled_index(row, t):
    """The first SETTLED index at or after the arrival `t` -- what the LEVEL consumer needs.

    ONE NAME, TWO QUANTITIES, which is this project's commonest defect class and was this one too.
    `row_transition` returns the ARRIVAL: where the descent reaches the floor. That is right for the
    POSITION consumer and its eight controls prove it. The LEVEL consumer needs something different
    -- samples strictly after the descent has FINISHED -- and was being handed the same index.

    Measured, that is exactly what went wrong: on bright programme the row at the arrival sits 27
    codes above its floor and the next sample sits 2 above, in 1,972 of 1,972 rows. So the arrival
    is the last RAMP sample. With a pool ~20 samples wide (the card) one ramp sample is absorbed and
    the level reads 1.437; with a pool ONE sample wide (bright) it IS the mean, and the level read
    13.13 instead of 1.41.

    Parameter-free: walk forward while the row is still strictly descending. On an abrupt fall this
    returns `t` unchanged, so the two quantities coincide exactly where they should.
    """
    x = np.asarray(row, dtype=np.float64)
    # NON-INCREASING, not strictly decreasing. Codex's control (a7760f6 follow-up) constructed a
    # quantized ramp `84, 55, 26, 26, 1.6` where a strict walk stops on the equal-valued plateau at
    # 26 and pools it as though it were blanking -- level 17.87 against a floor of 1.6. Blanking
    # noise is symmetric, so a non-increasing walk still stops within a sample or two of the floor
    # rather than running to the row's end.
    i = int(t)
    while i + 1 < x.size and x[i + 1] <= x[i]:
        i += 1
    return i


def settled_samples(row, t):
    """The samples this row contributes to the reference: those settled after its own descent ends.

    Extracted from `source_reference` so that the reference and anything QUALIFYING a row against
    it share one implementation instead of two that drift. One format, one loader: a qualification
    that recomputed "this row's settled level" its own way would be comparing a row against a
    reference built by a different rule, and the disagreement would read as a property of the row.

    Returns None where the row contributes nothing -- a row whose descent runs to the row's end,
    or whose tail holds no settled samples. None is "this row did not decide", never a level.

    ⚠️⚠️ ITS OUTPUT IS NOT CONTIGUOUS IN TIME. NEVER COMPUTE A TEMPORAL STATISTIC ON IT.
    The last line is a BOOLEAN MASK -- `tail[tail <= floor + 1.0]` -- so adjacent elements of what
    comes back were not adjacent in the row. It is correct for a LEVEL (the caller wants a pool, and
    order is irrelevant to a mean) and silently wrong for anything reading order: autocorrelation,
    run length, spacing, a transition position. Nothing in the name or the signature says so, which
    is why this warning is here rather than in a note elsewhere.
    Cost, 2026-09-11: a lag-1 autocorrelation computed on this output read -0.288 and was reported as
    the source blanking's dither signature. It is a selection artefact. The same filter also strips
    code 3 by construction (floor ~1.4 cuts at ~2.4), which produced a "blanking never reaches code
    3" column that is a property of this function and not of the source.
    ⚠️ AND THE OBVIOUS ALTERNATIVE IS ALSO WRONG, so a temporal caller must not simply take the raw
    span instead: `row[settled_index(row, t):]` over the same indices carries codes 22-23 at about
    10% -- picture, because the index can land before blanking is reached -- and its lag-1 reads
    +0.662, the descent's correlation rather than the blanking's. A temporal caller needs samples
    that are contiguous AND actually at blanking; neither this function nor that span provides both.
    """
    x = np.asarray(row, dtype=np.float64)
    t = settled_index(x, t)
    if t >= x.size: return None
    tail = x[t:]
    if tail.size == 0: return None
    # the row's own settled level after its transition: the lowest sustained part of its tail.
    # No absolute cut -- the row's own tail decides, by its own minimum block.
    if tail.size >= 4:
        k = (tail.size // 2) * 2
        floor = float(tail[:k].reshape(-1, 2).mean(axis=1).min())
        settled = tail[tail <= floor + 1.0]
    else:
        settled = tail
    return settled if settled.size else None


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
        # POSITION and LEVEL are different quantities. The transition is reported as the arrival;
        # the level must pool only what is SETTLED after the descent finishes. See settled_index.
        settled = settled_samples(row, t)
        if settled is None: silent += 1; continue
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
    ap.add_argument("--selftest",action="store_true",
                    help="run the controls that decided this function's criterion")
    a=ap.parse_args()
    if a.selftest:
        return selftest()
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


# ---------------------------------------------------------------------------------------------
# The controls that DECIDED this function, as runnable fixtures rather than comments about a run.
#
# They are here because they did the decisive work: the abrupt-transition case at 700 is what
# rejected the higher-scoring variant (84% on the card against this one's 56%). A decision recorded
# in prose and not enforced by a check is a second store -- and this project has already paid for
# that twice tonight, with an instrument left in /private/tmp and a conclusion filed in a tracker
# that gets deleted when empty. Both were fixed by moving the artefact, not by describing it better.

def _fixtures():
    rng = np.random.default_rng(7)
    return [
        ("picture 100 -> blanking at 600", 600,
         np.concatenate([rng.normal(100, 4, 600), rng.normal(1.4, 0.5, 120)])),
        ("card-like ABRUPT -> blanking at 700", 700,
         np.concatenate([rng.normal(20, 3, 700), rng.normal(1.4, 0.5, 20)])),
        ("bright: ONE settled sample, at 719", 719,
         np.concatenate([rng.normal(120, 5, 719), [2.0]])),
        ("gradual, two codes a sample, from 690", 700,
         np.concatenate([rng.normal(20, 3, 690), np.linspace(20, 1.4, 15), rng.normal(1.4, 0.4, 15)])),
    ], [
        ("flat picture, no edge", rng.normal(100, 4, 720)),
        ("all blanking", rng.normal(1.4, 0.5, 720)),
        ("steep interior edge, never reaches a floor",
         np.concatenate([rng.normal(120, 4, 300), rng.normal(60, 4, 420)])),
    ]


def selftest():
    pos, neg = _fixtures()
    ok = True
    print("RECOVERY -- known answers, injected:")
    for name, want, row in pos:
        got = row_transition(row)
        good = got is not None and abs(got - want) <= 2   # +-10 could not validate a one-sample claim
        ok &= good
        print("  %-42s -> %-5s want ~%d  %s" % (name, got, want, "PASS" if good else "FAIL"))
    print("NO FABRICATION -- rows with no transition must return None, over 200 SEEDS each.")
    print("  (one seed is not a control: Codex measured 61 of 1,000 seeds fabricating on these)")
    for name, row in neg:
        got = row_transition(row)
        ok &= got is None
        print("  %-42s seed 7 -> %-5s %s" % (name, got, "PASS" if got is None else "FAIL"))
    shapes = [("flat picture", lambda r: r.normal(100, 4, 720)),
              ("all blanking", lambda r: r.normal(1.4, 0.5, 720)),
              ("steep interior edge", lambda r: np.concatenate([r.normal(120, 4, 300), r.normal(60, 4, 420)]))]
    # ⚠️ THIS IS A REGRESSION GATE ON A MEASURED BOUND, NOT AN ASPIRATION TO ZERO -- and saying so
    # is the point. The rate is NOT zero: on synthetic rows engineered so the region after the
    # candidate carries the SAME noise as the region before it, this criterion cannot always tell a
    # step-and-stay from a transition into blanking. Claiming "3/3 negative controls pass" was true
    # of ONE SEED and was luck; Codex measured the same class independently at 61 of 1,000.
    # The gate fails on any INCREASE, so the bound cannot quietly grow, and it is printed every run
    # so the limit travels with the result instead of sitting in a docstring.
    BOUND = {"flat picture": 12, "all blanking": 12, "steep interior edge": 36}
    for nm, gen in shapes:
        fab = sum(1 for sd in range(200) if row_transition(gen(np.random.default_rng(sd))) is not None)
        within = fab <= BOUND[nm]
        ok &= within
        print("  %-42s 200 seeds -> fabricated on %2d of 200 (recorded bound %2d)  %s" % (
            nm, fab, BOUND[nm], "within bound" if within else "FAIL: REGRESSED"))
    print("  ^ a NON-ZERO fabrication rate on same-noise synthetic rows is a STATED LIMIT of this")
    print("    criterion. Real blanking is far quieter than picture, which is why it works on the")
    print("    capture; these fixtures remove that margin deliberately.")
    print("THE VARIANT CONTROL -- the rejected criterion must FAIL the abrupt case:")
    name, want, row = pos[1]
    bad = row_transition(row, _ref_at_crossing=True)
    fires = bad is None or abs(bad - want) > 10
    ok &= fires
    print("  reference AT the crossing on %-24s -> %-5s want ~%d  %s" % (
        name.split(' ->')[0], bad, want,
        "PASS (fails as it must)" if fires else "FAIL: the rejected variant now passes, so this "
        "control no longer defends the choice"))
    print("  reason: on an abrupt fall the crossing is already at the floor, so the midpoint")
    print("          becomes floor-to-floor and the search hunts a noise dip in the settled run.")
    print("POSITION vs LEVEL -- the two quantities must separate on a ramp and coincide on a step:")
    rng2 = np.random.default_rng(11)
    ramp = np.concatenate([rng2.normal(120, 4, 700), [84.0, 55.0, 26.0], rng2.normal(1.6, 0.3, 17)])
    step = np.concatenate([rng2.normal(120, 4, 700), rng2.normal(1.6, 0.3, 20)])
    # ⚠️ Assert the PROPERTY, not an index relationship. The first version of this control required
    # the two indices to COINCIDE on an abrupt step; they legitimately differ by a sample there,
    # because the settled walk advances while the row descends and blanking noise descends by a
    # fraction of a code. Both indices were at the floor, which is all the level consumer needs.
    # Requiring index equality tested a proxy for the requirement and failed a correct implementation.
    for nm, row, must_differ in (("multi-sample ramp", ramp, True), ("abrupt step", step, False)):
        t = row_transition(row)
        st_ = settled_index(row, t) if t is not None else None
        floor = float(np.min(row))
        settled_at_floor = st_ is not None and abs(float(row[st_]) - floor) <= 1.0
        arrival_above = t is not None and (float(row[t]) - floor) > 5.0
        good = settled_at_floor and (arrival_above == must_differ)
        print("  %-20s arrival %-4s settled %-4s  level at arrival %6.1f -> at settled %5.1f  %s" % (
            nm, t, st_, row[t] if t is not None else float("nan"),
            row[st_] if st_ is not None else float("nan"),
            "PASS" if good else ("FAIL: settled is NOT at the floor" if not settled_at_floor
                                 else "FAIL: arrival should%s be above the floor here"
                                      % ("" if must_differ else " NOT"))))
        ok &= good
    print("SELFTEST", "PASS" if ok else "FAILED")
    return 0 if ok else 1


if __name__=="__main__":
    raise SystemExit(main())
