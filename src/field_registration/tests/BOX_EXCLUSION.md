# Qualified box observation, exclusion only (rule 8)

**Historical implementation below; blanket switch exclusion is superseded.**
The owner's corrected rule 8 requires the current switch observation on boxed
rasters too. See `SWITCH_UNKNOWNS.md`: only the exclusion of switch measurement
is removed; boxed displacement still lacks measured geometry and stays Unknown.
The old full-card exclusion checker is a historical acceptance test for the
withdrawn requirement, not the current acceptance criterion.

The categorical observation cannot provide a displacement. A positive reading
skips the switch reader, leaves all switch/band quantities Unknown, and leaves
geometry unmeasurable. The raw top reader still runs unchanged and its tentative
row stays in the diagnostic record; it is not a valid position on this path.
Neither acquisition site can use the excluded evidence. A prior non-boxed lock
is invalidated in both fields, while analysis's last applied crop is held.
No standard-origin substitution, extent measurement, centring, fade-extent
hold, or comb promotion is implemented here. The comb remains quarantined.

## Instrument, not a source definition

The owner-facing brief explicitly qualified the harness's length guards as
FITTED instrument limits, not minimum dimensions for legitimate sources.
This reader adopts that limited class. It is not a universal box classifier.
False means **not detected by this instrument**, not proof of unboxed geometry.

- Row statistic: median absolute deviation from the row's mean, divided by
  median absolute adjacent-sample difference, over samples 24..695. This is
  the reported harness/comb measurement aperture, not a measured porch edge.
- Both medians are calculated exactly from 256-bin 8-bit histograms; there is
  no substituted noise floor. A zero denominator abstains unless the row is
  exactly flat. Histograms and row arrays are fixed memory capacities.
- Structured-level reference: median of the field aperture's middle third.
  Threshold is 0.28 of that reference, from the harness's reported separation:
  band 0.19..0.20 versus WARNING 0.39..0.41. The middle-third aperture and 0.28
  are this instrument's empirical choices, not standards or owner definitions.
  Neither every middle third nor every low-statistic row is assured to be
  content/band on other sources. No transfer claim is made.
- An initial low row and no sustained structure until at least six rows have
  passed establish the top candidate. Three consecutive high rows establish
  structured content (the card's backdrop step was measured at two rows).
  At least 40 high-statistic rows are required before a lower candidate.
  These 6/40/3 gates are qualified limits, not expected source band counts.
- A lower low run of at least six rows must lie in a suffix whose median is
  also low. The suffix reaches the measured last recorded row (capped by the
  ordinary 240-row aperture); it deliberately tolerates terminal switch rows.
  No switch endpoint is measured to establish the verdict. The suffix median
  is a robust regional check, not a reported extent or claimed boundary.

This rejects the existing weak-textured-edge negative that defeated variance
partitioning. That control's high-frequency texture is not mistaken for a
low row statistic merely because its amplitude is lower. It does not prove
rejection of every possible weak texture. All seven prior raw comb controls
are unrelated to this observer's qualification and are not claimed here.

## Tests and live-path result

Failing-first `522f58e`: 4/6; both boxed-geometry assertions failed before
implementation. Extended `box_exclusion_test`: 18/18 with raw counter 6668,
12/12 without it; the 18/18 raw run also passes ASan/UBSan. Includes explicit positive box flags, weak textured edges,
one-ended picture, a gain-halved box, and a public-path prior-lock control:
Unknown observation with the previously applied (2,2) crop held, not (0,0).
Counter 6668 is now positively boxed in BOTH fields; switch and geometry are
both unmeasurable, geometry d is -128, and it cannot acquire a lock.

Schema 19 adds `f1_box_detected` and `f2_box_detected`. A gated unit has no
registration observation; its false flag is not a negative box measurement.
Every positive box row in the replay was checked for suppressed switch and
geometry evidence and Unknown geometry d. Header/row alignment was checked.

Original commercial capture, paced full live path: 930 observations, 919 exact
and published, zero input, publication or log drops. No first lock;
`geometry_lock_known`, `applied_d1`, `applied_d2` are zero on every observation.
149 positive box readings per field across the capture. Outside-card positives
are counters 6263..6268 in f1 and 6263..6267 in f2. They are not independently
adjudicated, so this is not a false-positive rate or a capture pass.

Card counters 6665..6810: 146 observations, of which 6665 and 6666 are already
signal-gated. Of the 144 measured card units, f1 excludes 143 and f2 excludes
144. **Residual: field 1 at counter 6810 is not detected; switch evidence is
still present there. Full-card exclusion acceptance therefore FAILS.** No
threshold is adjusted to remove this residual. Geometry stays unplaced because
no lock is acquired. Detecting/holding the class through the remaining card
transition is still open; this reader does not implement a fade lifecycle.

`box_exclusion_replay_check.py` returns 1 with:

    FAIL: card switch evidence remains at field 1 counter 6810

Final schema-19 replay: `/private/tmp/box-exclusion.7JSEyR/registration-schema19.csv`.
Worker median/p95: 0.703/11.872 ms over 919 exact units; 8.9325/13.672 ms over
452 registration calls. The budget is not passed; concurrent synthetic tests
ran during this measurement. No optimization/speedup claim is made.

`make test` functional results: unit 18/18, CEA 3/3, rule1 5/5, rule3 2/2,
rule4 5/5, switch 32/32, comb 19/19, unlocked placement 24/24, box controls pass.
Synthetic benchmark warnings are retained verbatim:

    PERFORMANCE BUDGET EXCEEDED: 21091.000 us/unit p95
    PERFORMANCE BUDGET EXCEEDED: 95209.000 us/unit p95
    PERFORMANCE BUDGET EXCEEDED: 92449.000 us/unit p95

The first ad-hoc scoring attempt used `counter` and failed `KeyError: 'counter'`;
the actual join key is `counter_extended`, used by the committed replay check.

## Reproduction

    make -C src/field_registration test
    src/field_registration/tests/box_exclusion_test /private/tmp/box-6668.luma
    python3 src/field_registration/tests/box_exclusion_replay_check.py /private/tmp/box-exclusion.7JSEyR/registration-schema19.csv

The raw control is 525x720 luma bytes for counter 6668, extracted by the strict
CAP1 walker from the original commercial capture; it remains scratch only.
The classifier runs in C; no Python or harness observation feeds production.
