#!/usr/bin/env python3
"""Is the matched control's verdict SENSITIVE to the noise texture it cannot justify?

BACKGROUND. Codex's replacement for the withdrawn C3 is a visible blanking-boundary EXTENSION
against unchanged blanking plus ADJACENT DARK PICTURE, normal blanking retained in both worlds. Its
recommendation says the distinguishable and overlapping cases must come from properly qualified
measurements -- and the only texture measurement attempted on this capture is WITHDRAWN (the dither
refutation; `settled_samples` selects a boolean mask, so its output is not contiguous in time).

⚠️ THE TEMPTING ESCAPE DOES NOT WORK. Drawing the dark content i.i.d. from the measured level and sd
ASSERTS ZERO AUTOCORRELATION, which is precisely the unmeasured quantity. An i.i.d. draw is not
texture-neutral; it is a specific texture claim, and it is the one the withdrawn measurement was
supposed to establish. A control built that way would embed the assumption it exists to avoid, which
is the shape C3 was withdrawn for.

SO THE FORK IS: either the control's verdict is INSENSITIVE to texture -- turning an unmeasured
assumption into a sensitivity result, the move that settled the +3.0 cut -- or it MOVES, and the
control genuinely needs the measurement and is blocked. The second is a result too: it says the
measurement is load-bearing rather than decorative.

TWO SWEEPS, both at FIXED marginal distribution so only temporal structure changes:
  sweep 1  both objects share one texture -- the worst case for a detector, hence the right case for
           a control, but it also assumes away the discriminator, so on its own it cannot separate
           "insensitive" from "the construction removed the thing to be sensitive to"
  sweep 2  the blanking holds this capture's measured -0.29 while the ADJACENT DARK PICTURE's
           texture is swept independently, out to the +0.27 measured for clipped dark picture

⚠️ THE CONTROL THAT MUST FIRE. "The verdict did not move" fits two causes: genuinely insensitive, OR
this sweep has no power. So a texture-SENSITIVE verdict runs over the same worlds and is REQUIRED to
move. Without it the null is vacuous -- the same reason the 0-of-83 invariant check needed a
population where far values were reachable.

⚠️ MUTATIONS REPORT THE FIRED SET, NOT EXIT STATUS. `--audit` runs each mutation and names which
controls catch it. Exit status only says SOMETHING caught it, which is not evidence the intended
guard fired -- Codex's finding 5 on the fixture repair, in this instrument's own controls.
"""
import argparse
import numpy as np

N = 720                      # delivered samples per row
BLANK = 1.42                 # this capture's measured source blanking level
BLANK_SD = 0.5
PICT = 90.0
CUT = BLANK + 3.0            # the settled +3.0 cut
NOM = (702, 720)             # the terminal blanking run: measured start 702, reaches 719
EXTEND = 20                  # samples by which the visible boundary moves earlier in world A
BLANK_RHO = -0.29            # measured, undisplaced blanking
DARK_RHO = +0.27             # measured, clipped dark picture
RHOS = (-0.8, -0.4, BLANK_RHO, 0.0, DARK_RHO, 0.6, 0.9)

MUTATE = None                # set by --mutate / --audit; the named control MUST then fail


def ar1(rng, n, rho, mean, sd):
    """A run with the given lag-1 correlation and (asymptotically) the given mean and sd."""
    e = rng.normal(0, sd * np.sqrt(max(1e-9, 1 - rho * rho)), n)
    x = np.empty(n)
    x[0] = rng.normal(0, sd)
    for i in range(1, n):
        x[i] = rho * x[i - 1] + e[i]
    return x + mean


def world_A(rng, rho):
    """EXTENSION: the visible boundary moves earlier, so the blank run is longer. ONE object."""
    r = rng.normal(PICT, 4.0, N)
    a, b = NOM
    r[a - EXTEND:b] = ar1(rng, b - (a - EXTEND), rho, BLANK, BLANK_SD)
    return r


def world_B(rng, blank_rho, dark_rho):
    """UNCHANGED blanking plus ADJACENT DARK PICTURE at the same level. TWO objects, one run."""
    r = rng.normal(PICT, 4.0, N)
    a, b = NOM
    r[a:b] = ar1(rng, b - a, blank_rho, BLANK, BLANK_SD)            # the real interval, untouched
    r[a - EXTEND:a] = ar1(rng, EXTEND, dark_rho, BLANK, BLANK_SD)   # dark content beside it
    return r


def level_verdict(row):
    """What a LEVEL-ONLY reading can say: which samples are at or below the cut, and the run's
    extent -- the quantity a boundary-extension detector actually reads."""
    if MUTATE == "texture-aware-mask":
        # a mask that DOES read texture: keep samples whose local spread is small. Control 1 must
        # fail under this, or "the level verdict never moves" is unfalsifiable.
        loc = np.array([row[max(0, i - 1):i + 2].std() for i in range(row.size)])
        m = (row <= CUT) & (loc <= 0.45)
    else:
        m = row <= CUT
    idx = np.flatnonzero(m)
    if idx.size == 0:
        return (), None
    return tuple(idx), int(idx[-1] - idx[0] + 1)


def texture_verdict(row):
    """A deliberately texture-SENSITIVE reading of the same samples, used ONLY as the control that
    this sweep has power. Lag-1 of the sub-cut run. NOT proposed as a detector."""
    if MUTATE == "blind-control":
        return 0.0   # control 2 must fail: a control that reads nothing separates nothing
    idx = np.flatnonzero(row <= CUT)
    if idx.size < 3:
        return None
    seg = row[idx[0]:idx[-1] + 1]
    s = seg - seg.mean()
    d = (s * s).sum()
    return float((s[:-1] * s[1:]).sum() / d) if d else 0.0


def sweep(shared, trials, seed):
    rng = np.random.default_rng(seed)
    out = []
    for rho in RHOS:
        same = 0
        ext = []
        tex = []
        for _ in range(trials):
            bl = rho if shared else BLANK_RHO
            A = world_A(rng, bl)
            B = world_B(rng, bl, rho)
            mA, eA = level_verdict(A)
            mB, eB = level_verdict(B)
            same += (mA == mB)
            ext.append((eA, eB))
            tA, tB = texture_verdict(A), texture_verdict(B)
            if tA is not None and tB is not None:
                tex.append(tB - tA)
        out.append((rho, same, trials, ext[0], float(np.median(tex)) if tex else float("nan")))
    return out


def run_controls(trials, seed):
    """Return [(name, passed, detail)] -- the SET, so a mutation names the guard that caught it."""
    s1 = sweep(True, trials, seed)
    s2 = sweep(False, trials, seed + 1)
    moved1 = sum(1 for _, same, t, _, _ in s1 if same != t)
    moved2 = sum(1 for _, same, t, _, _ in s2 if same != t)
    tex_gap = max(abs(d) for *_, d in s2)

    rng = np.random.default_rng(7)
    _, eA = level_verdict(world_A(rng, BLANK_RHO))
    _, eB = level_verdict(world_B(rng, BLANK_RHO, DARK_RHO))
    want = NOM[1] - (NOM[0] - EXTEND)

    rng = np.random.default_rng(11)
    iid = rng.normal(BLANK, BLANK_SD, 400)
    s = iid - iid.mean()
    r_iid = float((s[:-1] * s[1:]).sum() / (s * s).sum())

    return [
        ("level verdict never moves across either sweep",
         moved1 == 0 and moved2 == 0, "moved %d/%d and %d/%d" % (moved1, len(s1), moved2, len(s2))),
        ("texture control DOES separate the worlds (>=0.20)",
         tex_gap >= 0.20, "max %+0.2f" % tex_gap),
        ("both worlds present the SAME run extent to a detector",
         eA == eB == want, "%s / %s, want %s" % (eA, eB, want)),
        ("i.i.d. asserts rho~0, not the measured %+0.2f" % BLANK_RHO,
         abs(r_iid) < 0.10 and abs(BLANK_RHO) > 0.10, "i.i.d. %+0.2f" % r_iid),
    ], (s1, s2, tex_gap)


def report(title, rows, label):
    print(title)
    print("  %-10s %-24s %-22s %s" % (label, "LEVEL verdict: same?", "run extent A / B",
                                      "TEXTURE control: B-A"))
    for rho, same, trials, (eA, eB), dtex in rows:
        print("  %+ -10.2f %-24s %-22s %+0.2f"
              % (rho, "YES in %d of %d" % (same, trials), "%s / %s" % (eA, eB), dtex))
    print()


def main():
    global MUTATE
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trials", type=int, default=60)
    ap.add_argument("--seed", type=int, default=31)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--audit", action="store_true",
                    help="run each mutation and NAME the controls it fires (not exit status)")
    ap.add_argument("--mutate", choices=("texture-aware-mask", "blind-control"))
    a = ap.parse_args()

    if a.audit:
        print("MUTATION AUDIT -- which controls catch each deliberate break\n")
        base, _ = run_controls(a.trials, a.seed)
        names = [n for n, _, _ in base]
        for mut, intended in (("texture-aware-mask", 0), ("blind-control", 1)):
            MUTATE = mut
            got, _ = run_controls(a.trials, a.seed)
            fired = [i for i, (_, ok, _) in enumerate(got) if not ok]
            MUTATE = None
            print("  %s" % mut)
            print("    intended guard : %d %s" % (intended + 1, names[intended]))
            print("    fired          : %s" % (", ".join(str(i + 1) for i in fired) or "NONE"))
            if fired == [intended]:
                print("    ISOLATED: the intended guard, and only it\n")
            elif intended in fired:
                print("    ⚠️ not isolated: %d guards. Exit status would not say which caught it;"
                      "\n       this mutation necessarily changes the run extent too, so controls"
                      "\n       1 and 3 are not independent for it.\n" % len(fired))
            else:
                print("    ⚠️ THE INTENDED GUARD DID NOT FIRE -- it does not defend what it claims\n")
        raise SystemExit(0)

    MUTATE = a.mutate
    controls, (s1, s2, tex_gap) = run_controls(a.trials, a.seed)

    report("SWEEP 1 -- both objects share one texture (only temporal structure changes)", s1, "rho")
    report("SWEEP 2 -- blanking held at %+0.2f; the ADJACENT DARK PICTURE's texture swept"
           % BLANK_RHO, s2, "dark rho")

    moved1 = sum(1 for _, same, t, _, _ in s1 if same != t)
    moved2 = sum(1 for _, same, t, _, _ in s2 if same != t)
    print("RESULT")
    print("  the LEVEL-only verdict moved in %d of %d settings (sweep 1) and %d of %d (sweep 2)."
          % (moved1, len(s1), moved2, len(s2)))
    print("  the TEXTURE control separates the two worlds by up to %+0.2f in lag-1, so the sweep"
          % tex_gap)
    print("  demonstrably HAS power -- the level verdict's flatness is not this test failing to")
    print("  detect movement.")
    print()
    print("  ⚠️ SCOPE, and it is the whole of what this establishes: the level verdict is")
    print("     insensitive to texture BY CONSTRUCTION -- a level mask never takes texture as an")
    print("     input. So a texture measurement can never be a PREREQUISITE for this control's")
    print("     verdict. It does NOT follow that the two worlds are indistinguishable: the control")
    print("     column shows a texture-aware reading has a separable quantity available at the")
    print("     measured textures. This demonstrates LEVEL-ONLY ambiguity and nothing wider --")
    print("     Codex's own caveat on the old C3, that it does not prove all analog observables")
    print("     indistinguishable.")

    if a.selftest:
        print("\nCONTROLS")
        for i, (name, ok, detail) in enumerate(controls):
            print("  %d %-52s : %s (%s)" % (i + 1, name, "PASS" if ok else "FAIL", detail))
        allok = all(ok for _, ok, _ in controls)
        print("\nSELFTEST %s" % ("PASSED" if allok else "FAILED"))
        raise SystemExit(0 if allok else 1)


if __name__ == "__main__":
    main()
