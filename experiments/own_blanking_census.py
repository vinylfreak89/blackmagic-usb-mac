#!/usr/bin/env python3
"""The owner's absence test, made measurable: is this row's OWN horizontal blanking where it belongs?

His ruling of 2026-09-11 (relayed verbatim; the contract amendment has NOT landed and this instrument
does not assume it has): "the lines own horizontal blanking is the thing that compares it to. thats
the answer to your absensce part. if all the blanking and all the picture belong where they belong,
it aint a head switch like area. if its somewhere other than the fucking bottom before the deck,
device or [other] blanking, its not a head switch. its normal horizontal tearing."

So the question per row is not "does this row carry the OTHER head's blanking" but "is this row's own
blanking still where this source puts it". Those are opposite directions, and the distinction matters
because the first one is ALREADY A RULED-OUT ROUTE: CLAUDE.md records that gating the partial-row test
on relocated blanking fixes 62 readings and breaks 248, net -186, because a low blank-run is a property
BOTH populations share. This measures the other direction and shares no threshold with it.

The reference is LEARNED PER UNIT PER FIELD from that field's own ordinary picture rows -- lines 200-250
field-relative, picture and far from the switch band -- so no position or extent is typed in, and a
source whose window sits elsewhere is measured on its own terms rather than against capture 1's.

Reported per row: the row's own blank-level run nearest the row's end, its start and extent, and how
that compares with the field's learned reference. **It classifies nothing and adjudicates nothing.**
The six T disagreements are an open two-agent adjudication; this is evidence for it.

LINE NUMBERS are frame-continuous (`row + 4`, both fields) to join against RUN_TIMING.md and the
engine's schema-20 export without a conversion in the middle.

⚠️ MEASURED LIMITATION, found by the instrument on its own control rows: the reference's 5-95%
start window is learned from 51 rows and can be tight enough to exclude an ORDINARY picture row.
On counter 6785 field 1 the learned bands are start 702-707 and extent 13-18, and picture row 254
sits at 709 with extent 11 -- outside BOTH, by two samples each -- so a known picture row reports
absent. That is a false positive.

**So the LABEL is directional and the NUMBERS are the evidence.** What separates that control row
from the disputed rows is magnitude, not category: row 254 misses each band by two samples, while
the run reader's T on counters 6700/6704/6749/6785 carries a longest run of 1, 3, 3 and 2 samples
against a reference extent of 14-16 -- an order of magnitude, not a boundary case. A categorical
"absent/present" hides exactly that, so both quantities are printed for every row and no threshold
was widened to make the answer come out: widening one against these six units is fitting to the
fixture, which is the defect this project keeps paying for.

  own_blanking_census.py [capture.tpc] [--keys] [--from N] [--to N]
"""
from __future__ import annotations
import argparse, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
BLANK_ROWS = {1: list(range(7,16)), 2: list(range(270,279))}
ORIGIN = {1: 23, 2: 286}                     # field-relative line 23 lives at this storage row + 0
REF_LO, REF_HI = 177, 228                    # offsets: field-relative lines 200-250, picture, off the band
KEYS = [(6681,1,260),(6700,1,261),(6704,2,524),(6722,1,260),(6749,1,261),(6785,1,261)]


def runs_at(row, blank):
    """Every maximal run at or below the field's blank level, as (start, length)."""
    m = row <= blank + 1.0
    out = []; cur = 0; s0 = 0
    for i, v in enumerate(m):
        if v:
            if cur == 0: s0 = i
            cur += 1
        elif cur:
            out.append((s0, cur)); cur = 0
    if cur: out.append((s0, cur))
    return out


def tail_run(row, blank, ref=None):
    """The row's own end-of-row blanking.

    ⚠️ The first version of this returned simply the LAST run, and that was the proxy defect this
    file's docstring is about -- in this file. On a row carrying a large relocated interval plus a
    one-sample blip at 719, the last run IS the blip, so counter 6681's S row reported `719 extent 1`
    and the 161-sample interval at sample 35 never appeared. The proxy ("last run" for "the row's own
    end-of-row blanking") came apart exactly on the rows the instrument exists to look at.

    With a reference, a run qualifies only if BOTH its start and its extent fall inside that
    reference's own 5-95% range -- learned from the field's picture rows, nothing typed in -- so a
    one-sample blip cannot pass as this source's 11-18 sample blanking. Without one (while the
    reference is being built) the last run is returned, which is what building it needs.
    """
    r = runs_at(row, blank)
    if not r: return (-1, 0)
    if ref is None: return r[-1]
    (s_lo, s_hi), (n_lo, n_hi) = ref
    ok = [(s, n) for s, n in r if s_lo <= s <= s_hi and n_lo <= n <= n_hi]
    return ok[-1] if ok else (-1, 0)


def longest_run(row, blank):
    """The row's longest run at blank level, wherever it sits -- so a RELOCATED interval is visible
    rather than hidden behind whatever happens to sit at the row's end."""
    r = runs_at(row, blank)
    if not r: return (-1, 0)
    return max(r, key=lambda t: t[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture", nargs="?", default="captures/composite_program_30s.tpc")
    ap.add_argument("--keys", action="store_true", help="only the six disputed keys of RUN_TIMING.md")
    ap.add_argument("--from", dest="frm", type=int, default=6667)
    ap.add_argument("--to", dest="to", type=int, default=10**9)
    a = ap.parse_args()
    want = {k[0] for k in KEYS} if a.keys else None
    st = {"buf": bytearray()}; seen = {}

    def emit(u):
        ctr = int.from_bytes(u[4:6], "little")
        if not (a.frm <= ctr <= a.to): return
        if want is not None and ctr not in want: return
        seen[ctr] = np.frombuffer(u, np.uint8)[HDR:].reshape(LINES, ROW)[:, 1::2].copy()

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
    print("capture %s   units held %d" % (a.capture, len(seen)))
    print("Reference learned per unit per field from that field's own picture rows (field-relative")
    print("lines 200-250). No position or extent is typed in. NO VERDICT: the six are an open")
    print("two-agent adjudication.\n")

    for ctr, field, S in (KEYS if a.keys else []):
        Y = seen.get(ctr)
        if Y is None:
            print("counter %d field %d: NOT IN CAPTURE\n" % (ctr, field)); continue
        blank = float(np.median(Y[BLANK_ROWS[field]]))
        base = ORIGIN[field] - 4 if field == 1 else 260 - 1 + 23 - 4   # storage row of field-rel line 23
        base = 19 if field == 1 else 282
        starts, lens = [], []
        for off in range(REF_LO, REF_HI):
            s, n = tail_run(Y[base + off].astype(np.float64), blank)
            if n > 0: starts.append(s); lens.append(n)
        rs, rl = int(np.median(starts)), int(np.median(lens))
        lo, hi = int(np.percentile(starts, 5)), int(np.percentile(starts, 95))
        nlo, nhi = int(np.percentile(lens, 5)), int(np.percentile(lens, 95))
        ref = ((lo, hi), (nlo, nhi))
        srow = S - 4
        print("counter %d field %d  S=line %d (row %d)   phase T=%d, run T=%d" % (ctr, field, S, srow, S, S-1))
        print("   this field's OWN end-of-row blanking, from %d picture rows: start %d (5-95%%: %d-%d), "
              "extent %d (5-95%%: %d-%d)" % (len(starts), rs, lo, hi, rl, nlo, nhi))
        print("   %-4s %-6s %-9s %-28s %s" % ("row","line","tag","its own blanking","longest run anywhere"))
        for r in range(srow - 3, srow + 2):
            row = Y[r].astype(np.float64)
            s, n = tail_run(row, blank, ref)
            ls, ln = longest_run(row, blank)
            tag = "S" if r == srow else ("run's T" if r == srow - 1 else "")
            if n > 0:
                own = "at %d, extent %d" % (s, n)
            elif ln <= 0:
                own = "ABSENT: no blank-level sample at all"
            elif not (lo <= ls <= hi) and not (nlo <= ln <= nhi):
                own = "ABSENT: start AND extent both out"
            elif not (lo <= ls <= hi):
                own = "absent: extent ordinary, start %+d out" % (ls - (lo if ls < lo else hi))
            else:
                own = "ABSENT: at the right place, extent %d" % ln
            print("   %-4d %-6d %-9s %-28s %d at sample %d" % (r, r + 4, tag, own, ln, ls))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
