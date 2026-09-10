#!/usr/bin/env python3
"""The switch line qualified by the owner's own no-jump rule (contract :164).

:164 says the partial line's location must not jump - a per-unit continuity condition.
Used here as a QUALIFIER rather than as a property to check afterwards: a reading is
qualified when it equals an adjacent unit's reading for the same field. Parameter-free.
The engine's T is used ONLY to score, never to qualify - that circularity is what
killed the earlier confirmation instruments.

Unqualified readings are the control, and readings that qualify nowhere are Unknown.
A reference that says Unknown where the rows do not decide is worth more than one
that answers everywhere.

DEFECT THIS FILE EXISTS TO NOT REPEAT (2026-09-11): the first version of this
measurement returned `23 + offset` as the candidate LINE for both fields, so every
field-2 reading was scored 263 lines below its own coordinates - the field spacing.
That produced a clean-looking cluster at -262..-265 which was read as a second
population in the data ("47% exact, 41% beyond +-4, two populations"). It was one
population and one bug. --selftest exercises that route.
"""
import sys, csv, collections, argparse
import numpy as np
sys.path.insert(0, __file__.rsplit('/',1)[0])
from packet_capture_reader import walk_tagged
from source_reference import row_transition, source_reference, ORIGIN_ROW, UNIT, HDR, ROW, LINES, MARK

# Each field's picture origin as a LINE. ORIGIN_ROW is the storage row of the same
# thing; the two differ by field and must never be interchanged (see the defect note).
ORIGIN_LINE = {1: 23, 2: 286}
PIC = 240
K = 0.5          # departures at or beyond +0.5 sd are the positive region (timing_disturbance.py)


def candidate_line(Y, fld, gate=False, gatestat=None):
    """This field's switch line, from its own rows: the first row of the last run of
    positive timing departures reaching the field's bottom. Returns a LINE, or None."""
    base = ORIGIN_ROW[fld]
    rows = [Y[base + o] for o in range(PIC) if base + o < LINES]
    ref = source_reference(rows[:200])
    if ref is None:
        return None
    exp = ref["transition_median"]; sd = max(ref["transition_sd"], 1e-6)
    lvl = ref["level"]; lsd = max(ref["level_sd"], 1e-6)
    pos = []
    for row in rows:
        if gate:
            # Reliability propagated one level down: a row with almost no content above
            # the SOURCE's own blanking cannot supply a picture-to-blanking transition,
            # so its steepest fall is noise. Threshold from the reference's own spread.
            if float((row > lvl + 3 * lsd).mean()) < 0.10:
                if gatestat is not None: gatestat['gated'] += 1
                pos.append(None); continue
            if gatestat is not None: gatestat['kept'] += 1
        t = row_transition(row)
        pos.append(None if t is None else (((t - exp) / sd) >= K))
    runs = []; i = 0
    while i < len(pos):
        if pos[i] is True:
            j = i
            while j + 1 < len(pos) and pos[j + 1] is True: j += 1
            runs.append((i, j)); i = j + 1
        else:
            i += 1
    last = [r for r in runs if r[1] >= len(pos) - 2]
    if not last:
        return None
    off = last[-1][0]
    line = ORIGIN_LINE[fld] + off
    # Where this candidate row's own blank-level run BEGINS. The engine's largest
    # blind class is recorded as left-censored: the displaced interval runs off the
    # delivered window, so its run starts at sample 0. This lets a reading be placed
    # in or out of that class instead of assumed either way.
    r = rows[off]
    m = r <= lvl + 3 * lsd
    best = (0, -1); cur = 0
    for i, v in enumerate(m):
        if v:
            cur += 1
            if cur > best[0]: best = (cur, i - cur + 1)
        else:
            cur = 0
    return (line, best[1], best[0])


def qualified(series, i, idx):
    """The owner's rule: this reading is qualified when an ADJACENT unit of the same
    field read the same line. Nothing from the engine enters this decision."""
    c, v = series[i][0], series[i][idx]
    if v is None: return False
    v = v[0] if isinstance(v, tuple) else v          # his rule is about the LINE, and only
    for j in (i - 1, i + 1):                          # the line: the run's start and extent
        if not (0 <= j < len(series)): continue       # are diagnostics carried alongside it
        w = series[j][idx]                            # and must not tighten the qualifier.
        if w is None or abs(series[j][0] - c) != 1: continue
        if (w[0] if isinstance(w, tuple) else w) == v:
            return True
    return False


def score(cand, eng, idx, want_qualified):
    err = collections.Counter(); byf = {1: collections.Counter(), 2: collections.Counter()}
    unknown = 0
    for fld in (1, 2):
        s = cand[fld]
        for i, rec in enumerate(s):
            T = eng.get((rec[0], fld), -1)
            if T < 0: continue                      # engine has no T: outside this comparison
            if qualified(s, i, idx) != want_qualified:
                unknown += 1; continue
            if rec[idx] is None:
                unknown += 1; continue
            d = rec[idx][0] - T
            err[d] += 1; byf[fld][d] += 1
    return err, byf, unknown


def report(label, err, byf, unknown, per_field=True):
    n = sum(err.values())
    if not n:
        print("  %-24s no readings" % label); return
    ex = err.get(0, 0)
    w1 = sum(v for k, v in err.items() if abs(k) <= 1)
    far = sum(v for k, v in err.items() if abs(k) > 4)
    print("  %-24s asserts %4d  Unknown %4d   exact %3.0f%%  within1 %3.0f%%  beyond+-4 %3.0f%%"
          % (label, n, unknown, 100*ex/n, 100*w1/n, 100*far/n))
    if per_field:
        for fld in (1, 2):
            t = sum(byf[fld].values())
            if t:
                print("        field %d  n=%3d  exact %3.0f%%   offsets %s"
                      % (fld, t, 100*byf[fld].get(0, 0)/t,
                         dict(sorted(byf[fld].items()))))


def selftest():
    """Controls derived from the ROUTES by which this measurement can be wrong."""
    ok = True
    # 1. the defect that happened: a field-2 candidate scored in field 1's coordinates.
    if ORIGIN_LINE[2] - ORIGIN_LINE[1] != 263:
        print("FAIL 1: field spacing is not 263; the coordinate defect's signature moves"); ok = False
    else:
        print("PASS 1: field spacing 263 - a field-2 reading scored as field 1 shows as -263")
    # 2. RUN the builder on a synthetic raster whose switch line is known, once per
    #    field. Restating `ORIGIN_LINE[fld] + offset` here would be the same two-stores
    #    defect this file is about, so the real function is exercised instead.
    for fld, want in ((1, 260), (2, 523)):
        Y = np.zeros((LINES, ROW // 2), dtype=np.float64)
        base = ORIGIN_ROW[fld]
        for o in range(PIC):
            r = base + o
            if r >= LINES: break
            row = np.zeros(ROW // 2)
            # picture to column 600, then this row's own blanking; displaced rows
            # carry their transition 60 samples later, which is the departure.
            edge = 600 + (60 if ORIGIN_LINE[fld] + o >= want else 0)
            row[:edge] = 80.0
            row[edge:] = 1.4
            Y[r] = row
        got = candidate_line(Y, fld)
        got = got[0] if got else got
        if got != want:
            print("FAIL 2: synthetic field %d switch at line %d read as %s" % (fld, want, got))
            ok = False
        else:
            print("PASS 2: synthetic field %d switch at line %d read back exactly" % (fld, want))
    # 3. ORIGIN_LINE and ORIGIN_ROW must not be interchangeable - the defect's cause.
    if ORIGIN_LINE[1] == ORIGIN_ROW[1] or ORIGIN_LINE[2] == ORIGIN_ROW[2]:
        print("FAIL 3: a line equals its own row; substituting one for the other is silent"); ok = False
    else:
        print("PASS 3: line != row in both fields (23/19, 286/282) - substitution is detectable")
    # 4. the qualifier must not consult the engine. Give it a series and a poisoned scorer.
    series = [(10, 260, 260), (11, 260, 260), (12, 999, 999)]
    if not qualified(series, 0, 1) or not qualified(series, 1, 1) or qualified(series, 2, 1):
        print("FAIL 4: no-jump qualification does not match adjacency"); ok = False
    else:
        print("PASS 4: qualification is adjacency only - 10/11 qualify, the lone 12 does not")
    # 5. non-adjacent counters must not qualify each other (a gap is not continuity).
    if qualified([(10, 260, 260), (14, 260, 260)], 0, 1):
        print("FAIL 5: counters 4 apart qualified as adjacent"); ok = False
    else:
        print("PASS 5: a counter gap does not qualify - continuity means adjacent units")
    print("SELFTEST", "5/5 PASS" if ok else "FAILED")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--capture', default='captures/composite_program_30s.tpc')
    ap.add_argument('--geometry', default='/private/tmp/run-timing.DdLgYt/plain/geometry.csv')
    ap.add_argument('--from-counter', type=int, default=6667)
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--csv', help='write per-reading results here, for joining against the '
                                  "engine's own Unknown-cause export")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())

    eng = {}
    for r in csv.DictReader(open(a.geometry)):
        eng[(int(r['counter']), int(r['field']))] = int(r['T'])
    cand = collections.defaultdict(list); gatestat = collections.Counter()
    st = {"buf": bytearray()}

    def emit(u):
        c = int.from_bytes(u[4:6], "little")
        if c < a.from_counter: return
        Y = np.frombuffer(u, np.uint8)[HDR:].reshape(LINES, ROW)[:, 1::2].astype(np.float64)
        for fld in (1, 2):
            cand[fld].append((c,
                              candidate_line(Y, fld, False),
                              candidate_line(Y, fld, True, gatestat)))

    def on_video(p):
        b = st["buf"]; b.extend(p)
        while True:
            i = b.find(MARK)
            if i < 0: return
            if i > 0: del b[:i]
            j = b.find(MARK, 4)
            if j < 0: return
            if j == UNIT: emit(bytes(b[:UNIT]))
            del b[:j]

    walk_tagged(a.capture, on_video=on_video, progress=False)
    if a.csv:
        with open(a.csv, 'w', newline='') as fh:
            w = csv.writer(fh)
            w.writerow(['counter','field','line','run_start','run_length','qualified','engine_T'])
            for fld in (1, 2):
                for i, rec in enumerate(cand[fld]):
                    v = rec[1]
                    w.writerow([rec[0], fld,
                                v[0] if v else -1, v[1] if v else -1, v[2] if v else -1,
                                int(qualified(cand[fld], i, 1)),
                                eng.get((rec[0], fld), -1)])
        print("wrote %s" % a.csv)
    print("capture %s   from counter %d\n" % (a.capture, a.from_counter))
    print("Candidate lines are in EACH FIELD'S OWN numbering (23.. / 286..).\n")
    report("QUALIFIED (no jump)",  *score(cand, eng, 1, True))
    report("CONTROL: unqualified", *score(cand, eng, 1, False))
    # Where the ENGINE is blind. These cannot be scored - there is nothing to score
    # against - so coverage is the result, checked against the contract's OWN invariant
    # (section 8: the switch line stays within one row of the field's mode) rather than
    # against the engine. An instrument that only speaks where the engine already has an
    # answer adds nothing; this is the measurement of whether that is the case.
    print()
    print("  WHERE THE ENGINE REPORTS NO T (it cannot be scored here - coverage IS the result):")
    for fld in (1, 2):
        s_ = cand[fld]
        vals = [r[1][0] for r in s_ if r[1] is not None]
        mode = collections.Counter(vals).most_common(1)[0][0] if vals else None
        tot = q = qfar = u = ufar = 0
        for i, rec in enumerate(s_):
            if eng.get((rec[0], fld), -1) >= 0: continue
            tot += 1
            if rec[1] is None: continue
            far = mode is not None and abs(rec[1][0] - mode) > 1
            if qualified(s_, i, 1):
                q += 1; qfar += far
            else:
                u += 1; ufar += far
        if tot:
            print("        field %d  engine-Unknown %3d | QUALIFIED %3d (%2.0f%%), %d outside mode+-1"
                  "  | CONTROL unqualified %3d, %d outside (%2.0f%%)"
                  % (fld, tot, q, 100*q/tot, qfar, u, ufar, 100*ufar/max(1,u)))
    print()
    print("  DO THOSE READINGS SIT IN THE ENGINE'S LEFT-CENSORED CLASS? (run start 0 = off-window)")
    for fld in (1, 2):
        s_ = cand[fld]
        for label, blind in (("engine-blind", True), ("CONTROL: engine has a T", False)):
            b = collections.Counter(); n = 0
            for i, rec in enumerate(s_):
                has = eng.get((rec[0], fld), -1) >= 0
                if has == blind: continue
                if rec[1] is None or not qualified(s_, i, 1): continue
                st_ = rec[1][1]; n += 1
                b['start 0' if st_ == 0 else ('start 1-2' if st_ <= 2 else 'interior')] += 1
            if n:
                print("        field %d %-24s n=%3d   %s" % (fld, label, n, dict(b)))
    print("        mode = this field's own modal candidate line. The control answers whether the")
    print("        invariant check has any power: if unqualified readings there ALSO never leave")
    print("        mode+-1, the instrument cannot emit a far value and the check proves nothing.")

    print()
    report("ablation: reliability-gated", *score(cand, eng, 2, True), per_field=False)
    g, k = gatestat['gated'], gatestat['kept']
    print("        gate removed %d rows of %d (%.3f%%) - report count WITH exactness, because"
          % (g, g + k, 100 * g / max(1, g + k)))
    print("        an improvement from discarding half the population is a smaller reference.")


if __name__ == '__main__':
    main()
