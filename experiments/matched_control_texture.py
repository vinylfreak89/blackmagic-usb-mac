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

⚠️ AND THE ANSWER IS A MARGIN, NOT A CONSTRUCTION. The first version of this concluded "insensitive
BY CONSTRUCTION -- a level mask never takes texture as an input". That is FALSE and the peer session
caught it: the mask is texture-blind PER SAMPLE, but its output is the index set that fell below the
cut, and that set is a property of the REALIZED SEQUENCE, which texture orders. `--margin` measures
it: at 2 sigma the identical-mask rate swings 16% -> 55% across rho, a 39-point spread; at the
committed 6 sigma the spread is zero. So the conclusion holds AT THIS CUT and carries its own
precondition, where "by construction" would have licensed reusing it at a tight cut -- and this
project has already measured a tight cut failing (the k=0.5 collapse, 38% of real rows).

TWO SWEEPS, both at FIXED marginal distribution so only temporal structure changes:
  sweep 1  both objects share one texture -- the worst case for a detector, hence the right case for
           a control, but it also assumes away the discriminator, so on its own it cannot separate
           "insensitive" from "the construction removed the thing to be sensitive to"
  sweep 2  the blanking holds the authored -0.29 while the ADJACENT DARK CONTENT's texture is
           swept independently, out to the authored +0.27 for dark content

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
# ⚠️ THESE TWO ARE AUTHORED SCENARIO PARAMETERS, NOT MEASURED SIGNATURES (Codex's finding 5). They
# came from the dither comparison WITHDRAWN the same night: its lag-1 ran on a boolean-mask
# selection whose adjacent elements were not adjacent in time, and the population the claim was
# actually about reads -0.044 with 56.8% negative against 50% by chance. Citing them as measured
# would revive a retracted result through a fixture, which is how a withdrawn number comes back --
# not by anyone re-asserting it, but by a downstream artefact carrying it forward without the
# retraction. They are plausible textures to sweep THROUGH, and nothing here rests on their values.
BLANK_RHO = -0.29            # AUTHORED: a blanking-like texture, from a withdrawn figure
DARK_RHO = +0.27             # AUTHORED: a dark-content-like texture, from a withdrawn figure
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


def level_verdict(row, cut=None):
    """What a LEVEL-ONLY reading can say: which samples are at or below the cut, and the run's
    extent -- the quantity a boundary-extension detector actually reads.

    ⚠️ THE MASK IS TEXTURE-BLIND PER SAMPLE; ITS OUTPUT IS NOT. The returned index set is a property
    of the REALIZED SEQUENCE, and texture is what orders a realization -- permute one and the
    multiset is unchanged while every run changes. So this is insensitive to texture only where the
    cut is far enough from the level that the mask is effectively deterministic. `margin_sweep()`
    measures where that stops being true."""
    c = CUT if cut is None else cut
    if MUTATE == "cut-blind-mask":
        # a mask that ignores the cut: flat at EVERY margin, so control 5's second half is false
        c = BLANK + 3.0
    if MUTATE == "texture-aware-mask":
        # a mask that DOES read texture: keep samples whose local spread is small. Control 1 must
        # fail under this, or "the level verdict never moves" is unfalsifiable.
        loc = np.array([row[max(0, i - 1):i + 2].std() for i in range(row.size)])
        m = (row <= c) & (loc <= 0.45)
    else:
        m = row <= c
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


def sweep(shared, trials, seed, cut=None):
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
            mA, eA = level_verdict(A, cut)
            mB, eB = level_verdict(B, cut)
            same += (mA == mB)
            ext.append((eA, eB))
            tA, tB = texture_verdict(A), texture_verdict(B)
            if tA is not None and tB is not None:
                tex.append(tB - tA)
        out.append((rho, same, trials, ext[0], float(np.median(tex)) if tex else float("nan")))
    return out


def margin_sweep(trials=200, seed=5):
    """Where does the cut stop being far enough? Returns [(k, sigma, [rate per rho], spread)].

    This exists because "insensitive BY CONSTRUCTION" was written here first and is FALSE: it would
    licence reusing the reasoning at a tight cut, and this project has already been burned by one
    (the k=0.5 collapse, where 38% of real rows had their terminal run broken by which samples noise
    pushed over the line). Stated as a margin, the claim carries its own precondition."""
    out = []
    for k in (0.25, 0.5, 1.0, 1.5, 2.0, 3.0):
        cut = BLANK + k
        rates = []
        for rho in (-0.8, -0.4, 0.0, 0.4, 0.9):
            rng = np.random.default_rng(seed)
            same = 0
            for _ in range(trials):
                A = world_A(rng, rho)
                B = world_B(rng, rho, rho)
                same += (level_verdict(A, cut)[0] == level_verdict(B, cut)[0])
            rates.append(same / trials)
        out.append((k, k / BLANK_SD, rates, max(rates) - min(rates)))
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

    ms = margin_sweep(trials=120)
    far_spread = next(sp for k, _, _, sp in ms if abs(k - 3.0) < 1e-9)
    tight_spread = next(sp for k, _, _, sp in ms if abs(k - 1.0) < 1e-9)

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
        # 5 is the precondition, and it must fail in BOTH directions or it is not a claim: the
        # verdict must be flat at the committed cut AND must MOVE at a tight one. Without the
        # second half "insensitive" would be unfalsifiable and would licence any cut.
        ("insensitivity is a MARGIN: flat at %.1f sigma, MOVES at 2 sigma" % (3.0 / BLANK_SD),
         far_spread < 0.02 and tight_spread > 0.10,
         "spread %.1f pts at 6 sigma, %.1f pts at 2 sigma"
         % (100 * far_spread, 100 * tight_spread)),
    ], (s1, s2, tex_gap, ms)


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
    ap.add_argument("--mutate", choices=("texture-aware-mask", "blind-control", "cut-blind-mask"))
    a = ap.parse_args()

    if a.audit:
        print("MUTATION AUDIT -- which controls catch each deliberate break\n")
        # ⚠️ THE AUDIT MUST BE ABLE TO FAIL. It printed its warnings and exited 0, so a suite in
        # which NO mutation fired its guard reported exactly like a clean one -- an audit that
        # cannot fail is the rung-3 defect this project records, inside the instrument written to
        # verify other guards. It now validates its BASELINE first (an unmutated run that already
        # fails makes every mutation result meaningless) and exits non-zero on any unmet obligation.
        ok_all = True
        base, _ = run_controls(a.trials, a.seed)
        names = [n for n, _, _ in base]
        base_fired = [i for i, (_, ok, _) in enumerate(base) if not ok]
        if base_fired:
            print("  ⚠️ BASELINE ALREADY FAILING: controls %s fire with NO mutation applied."
                  % ", ".join(str(i + 1) for i in base_fired))
            print("     Every mutation below is uninterpretable until that is fixed.\n")
            ok_all = False
        else:
            print("  baseline: unmutated run passes, no control fires\n")
        for mut, intended in (("texture-aware-mask", 0), ("blind-control", 1),
                              ("cut-blind-mask", 4)):
            MUTATE = mut
            got, _ = run_controls(a.trials, a.seed)
            fired = [i for i, (_, ok, _) in enumerate(got) if not ok]
            MUTATE = None
            print("  %s" % mut)
            if intended >= len(names):
                print("    ⚠️ INTENDED GUARD %d DOES NOT EXIST (%d controls) -- the audit and the"
                      "\n       control set have drifted apart\n" % (intended + 1, len(names)))
                ok_all = False
                continue
            print("    intended guard : %d %s" % (intended + 1, names[intended]))
            print("    fired          : %s" % (", ".join(str(i + 1) for i in fired) or "NONE"))
            if fired == [intended]:
                print("    ISOLATED: the intended guard, and only it\n")
            elif intended in fired:
                # the guard list is DERIVED, never described: a hardcoded explanation naming two
                # controls went stale the moment a third started firing, which is the
                # stale-explanatory-text class this project records.
                print("    ⚠️ not isolated: %d guards (%s). Exit status would not say which caught"
                      "\n       it. This mutation changes the masked index set, so every control"
                      "\n       reading that set responds to it.\n"
                      % (len(fired), ", ".join(names[i] for i in fired)))
            else:
                print("    ⚠️ THE INTENDED GUARD DID NOT FIRE -- it does not defend what it claims\n")
                ok_all = False
        print("AUDIT %s" % ("PASSED" if ok_all else "FAILED"))
        raise SystemExit(0 if ok_all else 1)

    MUTATE = a.mutate
    controls, (s1, s2, tex_gap, ms) = run_controls(a.trials, a.seed)

    report("SWEEP 1 -- both objects share one texture (only temporal structure changes)", s1, "rho")
    report("SWEEP 2 -- blanking held at the authored %+0.2f; the DARK CONTENT's texture swept"
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
    print("MARGIN -- why the verdict is flat, and where it stops being flat")
    print("  the cut is BLANK+3.0, %.1f sigma above the blanking mean. Sweeping it:" % (3.0 / BLANK_SD))
    print("  %-14s %-6s %-28s %s" % ("cut", "sigma", "identical masks, rho -0.8..+0.9", "spread"))
    for k, sig, rates, spread in ms:
        print("  BLANK+%-8.2f %-6.1f %-28s %5.1f pts"
              % (k, sig, " ".join("%3.0f%%" % (100 * r) for r in rates), 100 * spread))
    print()
    print("  ⚠️ SCOPE, and it is the whole of what this establishes.")
    print("     The verdict is insensitive to texture AT THIS MARGIN -- NOT by construction. A level")
    print("     mask is texture-blind PER SAMPLE, but its output is the set of indices that fell")
    print("     below the cut, and that set is a property of the REALIZED SEQUENCE, which texture")
    print("     orders: permute a sequence and the multiset is unchanged while every run changes.")
    print("     The sweep above shows exactly that at 2 sigma. At 6 sigma the mask is effectively")
    print("     deterministic and texture cannot reach the verdict, so no texture measurement")
    print("     gates this control AT THIS CUT -- a claim that carries its own precondition.")
    print("     ⚠️ 'By construction' was written here first and would have licensed reusing the")
    print("     reasoning at a tight cut, where this project has already measured it failing.")
    print("     It does NOT follow that the two worlds are indistinguishable: the control column")
    print("     shows a texture-aware reading has a separable quantity available -- but its %+0.2f is"
          % tex_gap)
    print("     at rho +0.90, NOT at the authored %+0.2f, so it is the sweep's widest separation and"
          % DARK_RHO)
    print("     not a figure for any particular texture. This demonstrates LEVEL-ONLY ambiguity and")
    print("     nothing wider -- Codex's own")
    print("     caveat on the old C3, that it does not prove all analog observables")
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
