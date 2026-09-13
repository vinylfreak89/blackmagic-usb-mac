#!/usr/bin/env python3
"""Waveform detection by walking the line in time.  The owner's algorithm, verbatim:

    "walk the line sample by sample. starts with near blanking codes. should monotonically rise
     to a far away from blanking code, stop there, and then again gradually fall toward blanking"
    "if you read the whole line, and thats the ONLY signal you see, its a waveform"
    "if you see any other type of signal, its not a waveform. plain and simple"
    "the far left isn't always blanking. sometimes if the timing is really bad it will be the
     'top' of the waveform so either works"

Not a histogram, not an average -- the order of the samples IS the test.  An excursion is a run
of samples above near-blanking.  It is a PULSE when, walked in time:
  - it rises monotonically (a dip of more than TOL below the running maximum breaks the rise),
  - it reaches a code far from blanking (peak >= FAR),
  - it stops there (the plateau stays within 2*TOL of its own level),
  - it falls monotonically back (a bump of more than TOL above the running minimum breaks it).
At the row's LEFT edge an excursion may begin at the top code instead of at blanking (his rule):
it must then already be on its plateau at sample 0 and fall from there.  At the RIGHT edge the
default is strict (an excursion cut off by the row's end is other signal); `right_edge_top`
measures the symmetric allowance he did NOT state, so its effect is reported, never assumed.
WHOLE-LINE VERDICT: a waveform iff the line carries at least one pulse and NOTHING ELSE.

FAR, NEAR and TOL are FITTED on 26 labelled rows (near<=20, far>=40, tol 8 was the only setting
that found 4 of 6), not derived.  The census sweeps them.
"""
import numpy as np


def _shape(seg, far, tol, left, right, right_edge_top):
    pk = float(seg.max())
    if pk < far:
        return "low"                                    # rose, never far from blanking
    top = np.flatnonzero(seg >= pk - tol)
    a, b = int(top[0]), int(top[-1])
    if left and a != 0:
        return "left-edge-mid-ramp"                     # row starts neither at blanking nor top
    if right and not (right_edge_top and b == len(seg) - 1):
        return "right-edge"                             # cut off by the row's end
    rise, plat, fall = seg[:a + 1], seg[a:b + 1], seg[b:]
    if np.any(np.maximum.accumulate(rise) - rise > tol):
        return "rise-not-monotonic"
    if plat.max() - plat.min() > 2 * tol:
        return "no-plateau"
    if np.any(fall - np.minimum.accumulate(fall) > tol):
        return "fall-not-monotonic"
    return "pulse"


def excursions(y, near, far, tol, right_edge_top=False, stop_at_other=False):
    """Every excursion on the line, in time order: (start, end_exclusive, peak, verdict)."""
    y = np.asarray(y, dtype=np.float32); n = len(y)
    p = np.concatenate(([1], (y <= near).astype(np.int8), [1]))
    d = np.diff(p)
    out = []
    for i, j in zip(np.flatnonzero(d == -1), np.flatnonzero(d == 1)):
        seg = y[i:j]
        v = _shape(seg, far, tol, i == 0, j == n, right_edge_top)
        out.append((int(i), int(j), float(seg.max()), v))
        if stop_at_other and v != "pulse":
            break
    return out


def verdict(y, near, far, tol, right_edge_top=False, stop_at_other=False):
    ex = excursions(y, near, far, tol, right_edge_top, stop_at_other)
    pulses = sum(1 for e in ex if e[3] == "pulse")
    other = len(ex) - pulses
    return (pulses >= 1 and other == 0), pulses, other, ex


def selftest():
    """Synthetic rows with known answers.  Returns failures."""
    fails = []
    base = np.full(720, 1.0)
    def pulse(y, at, width, hi=118.0, ramp=4):
        for k in range(ramp):
            y[at + k] = 1 + (hi - 1) * (k + 1) / (ramp + 1)
            y[at + ramp + width + k] = hi - (hi - 1) * (k + 1) / (ramp + 1)
        y[at + ramp:at + ramp + width] = hi
        return y
    cases = []
    y = base.copy()
    for k in range(7): pulse(y, 30 + 27 * k, 6)
    cases.append(("seven clean pulses", y, True))
    y = base.copy(); y[:12] = 118; y[12:16] = [95, 70, 45, 20]; pulse(y, 200, 10)
    cases.append(("left edge starts at the top (his rule)", y, True))
    y = base.copy(); y[:6] = [60, 80, 100, 118, 118, 118]; y[6:10] = [90, 60, 30, 5]; pulse(y, 200, 10)
    cases.append(("left edge starts mid-ramp", y, False))
    y = base.copy(); pulse(y, 100, 10); y[400:500] = 30.0
    cases.append(("pulse plus a pedestal at a third level", y, False))
    y = base.copy(); pulse(y, 100, 10); pulse(y, 300, 10); y[312:318] = 118 - np.array([0, 20, 40, 40, 20, 0])
    cases.append(("plateau with a deep sag", y, False))
    y = base.copy(); pulse(y, 100, 10); y[700:] = 118
    cases.append(("cut off at the right edge, strict", y, False))
    y = np.clip(60 + 40 * np.sin(np.arange(720) / 9.0), 0, 255)
    cases.append(("picture-like texture never at blanking", y, False))
    y = base.copy()
    cases.append(("blank line", y, False))
    for name, y, want in cases:
        got = verdict(y, 20, 40, 8)[0]
        print(f"   {'PASS' if got == want else 'FAIL'}  {name}: want {want} got {got}")
        if got != want:
            fails.append(name)
    got = verdict(cases[5][1], 20, 40, 8, right_edge_top=True)[0]
    print(f"   {'PASS' if got else 'FAIL'}  cut off at the right edge, right_edge_top allowance: want True got {got}")
    if not got:
        fails.append("right_edge_top")
    return fails


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--selftest"]:
        f = selftest()
        print("SELFTEST", "PASS" if not f else f"FAIL {f}")
        sys.exit(1 if f else 0)
    z = np.load(sys.argv[1])
    for near in (10, 20):
        for far in (40, 80):
            for tol in (4, 8):
                tp = fn = fp = tn = 0
                for key in z.files:
                    cls = key.split("_")[2]
                    w = verdict(z[key], near, far, tol)[0]
                    if cls == "WAVE":
                        tp += w; fn += (not w)
                    else:
                        fp += w; tn += (not w)
                print(f"near<={near:>2} far>={far:>2} tol {tol}:  waveforms found {tp}/{tp+fn}   "
                      f"non-waveform rows called waveform {fp}/{fp+tn}")
