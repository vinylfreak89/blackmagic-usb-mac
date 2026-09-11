# Revised switch-fixture review

Reviewed `b8cedaf204345d957ca00f9f30ef304e46910e5e` (fixtures) and
`2517b62f965e69f4688dd4c9658c4fee11c98e0e` (positive controls), after fast-forwarding
`v10-engine` to `origin/v10-harness` at
`6c7c8e3caa7ba278c3752d2e254db1627fdc78d3`. Other incoming changes are not
implicitly approved. No capture content opened or measured. No supplied fixture,
detector, engine or contract is changed by this review.

During final checks the remote-tracking harness branch advanced to `c454164`
(after `dcaeba0` and `b074849`). Those later changes are outside this review;
the file/line citations and design recommendation concern the snapshot above.
The contract was not changed in this worktree and is not asserted byte-identical
to that newer harness head.

Both supplied commands exit 0: the fixture's nine controls and converted positive
suite pass. A2 now contains its declared interval and C3 is removed. The repairs
are real, but validation remains incomplete. The new synthetic-only
`experiments/switch_fixture_repair_audit.py` expresses positive rejection checks;
it currently exits 1 with six unmet checks, reproduced below.

## Findings and recommendations

1. **Restore the edge-placed reference and shorten A2; retain interior phases as
   additional cases, not as the replacement.** `experiments/switch_fixtures.py:39`,
   `:81`, `:85`, `:96`. **Recommendation reasoned; A2 construction reproduced.**

   Use `(700,717)` for the existing abstract visible-interval reference and make
   A2 end at 709: an authored -8 stimulus, leaving a valid nine-sample interval
   and exceeding the declared +/-2 jitter. This reproduces exactly in the row
   generator. There was room to shorten the old interval, just not by 40.
   Keep 660 and other placements as additional phase cases. Reference-relative
   measurement must not depend on any one fixed interval location.

   This is not a constant-only substitution: A4 and B2 depend on it too. A4
   start -30/end -8 is an unequal, uncensored two-end test; B2 start -5 with its
   end beyond delivery retains a visible leading boundary. These are examples
   of test stimuli, not operational thresholds. Recompute truth and censoring
   for all cases. Neither 660..677 nor 700..717 alone represents a complete
   nominal blanking waveform. Label these interval-algebra cases as abstract,
   with interval identity supplied/qualified. For physical placement, generate a
   full line period and crop at a declared sampling phase. Normal blanking can
   contribute at BOTH delivered edges, as contract `:66` and `:416` already state.

2. **JITTER is legitimate; a blanket prohibition on small shifts is not.**
   `experiments/switch_fixtures.py:42`, `:66`, `:185`.
   **Reasoned; uncertainty-case rejection reproduced.**

   Declaring injected endpoint jitter +/-2 is not a fitted runtime threshold
   under rule 4. Selecting larger stimuli is sensible for a separately identified
   endpoint-recovery subset. But small shifts also belong in a test suite, with
   Unknown or interval-valued expectations where uncertainty requires them.
   A consistent +1 translation labeled `undecidable` is rejected by control 5
   alone. The guard ignores the requested disposition.

   A4 with a large start shift and small end shift can establish departure without
   resolving the second shift. Banning it globally defeats the separation between
   presence and magnitude certainty. Scope recovery demands to the quantities
   they ask to resolve. The generator's jitter is also not necessarily the whole
   measurement uncertainty: sample noise and estimator uncertainty remain, and
   the finite calibration does not automatically reveal its declared bound.

3. **Truth checks still skip censored and dark-content cases; expected evidence
   needs its own schema.** `experiments/switch_fixtures.py:60`, `:72`, `:93`,
   `:162`. **Bypass reproduced; schema recommendation reasoned.**

   Setting B1's visible end shift to +1000, or C1's start shift to +1000, leaves
   all nine controls passing. Control 3 skips the entire case if either endpoint
   is a string or `dark_at` is truthy. Validate each delivered endpoint separately;
   dark content must not disable checking of the true interval. Hidden synthesis
   truth should identify that interval rather than assuming first/last low run.

   Keep the three-value PRESENCE result. Add separate machine-readable expected
   endpoint/extent availability, bounds, uncertainty and reasons before a detector
   consumes the fixtures. B1 can require `presence=departure` AND `extent=unavailable`,
   possibly with an available lower bound. `censored` is a useful beginning, but
   prose in `why` does not test that obligation. No fourth presence value is needed.

   Full hidden truth remains separate: synthesis knows B1 starts at -60 and B2
   ends at 780 from their spans. Store numeric true endpoints/deltas there even
   when the detector's corresponding measurement is censored. Unobserved does
   not mean unknown to the generator.

4. **Calibration is unverified; mask equality is still called observation
   equality.** `experiments/switch_fixtures.py:66`, `:133`, `:177`.
   **Reference omission reproduced; equivalence consequence reasoned.**

   Replacing every calibration row with uniform picture leaves all nine controls
   passing. None verifies the reference defining the shifts or its declared
   jitter. Give calibration hidden construction truth and corresponding checks.

   Control 4 groups only thresholded blank spans, ignoring calibration and all
   other sample information. The same row with different qualified references
   can imply different displacement; the same mask with different timing-bearing
   texture can contain different evidence. Define the allowed detector interface,
   then compare that COMPLETE interface for answer consistency. A mask-only
   equivalence check applies only to an explicitly mask-only interface, not to all
   possible row-local methods.

5. **The positive suite does not prove its intended guards fire.**
   `experiments/switch_fixtures_review_controls.py:60`, `:70`, `:89`, `:107`.
   **Reproduced by disabling guards individually.**

   Removing the rejection effect of control 1, 4 or 5, one at a time, leaves the
   whole positive suite passing. The invalid-span mutation leaves the old row
   behind, so containment can reject it. The identical-row mutation leaves A5's
   old span/truth behind. The jitter mutation changes spans/truth without
   regenerating the row. Other checks reject these bundles; exit 1 alone cannot
   attribute rejection to the intended guard.

   Keep mutations coherent with unrelated invariants, check the rejection cause,
   and verify disabling the intended guard makes its positive control fail.
   Structured validation results would make that attribution easier. The present
   mutations demonstrate rejection of the bundles, not regression protection for
   each named guard.

   Review-probe correction: my first guard mutator copied module globals, bypassing
   the positive suite's patch of `fixtures.cases`. It reported
   `FAIL a declared span with b <= a must FAIL, not be normalised out` for all
   three disabled guards. That meta-test was invalid. The committed version keeps
   the actual module globals and reproduces all three undetected guard removals.

6. **Remove old C3, not every possible matched ambiguity case. B3 and the dither
   claim still need scoping.** `experiments/switch_fixtures.py:16`, `:99`, `:105`;
   `experiments/switch_fixtures_review_controls.py:46`.
   **Removal and conditional example reproduced; physical scope reasoned.**

   C3's hidden-whole-interval story stays rejected. B3, however, still declares
   both endpoints `off-window` and `censored=both` while delivering no interval.
   Renaming it did not remove that same causal premise. A uniform/no-identifiable-
   boundary row can be a robustness input with unknown cause/identity; it is not
   evidence that a nominal interval lies wholly outside delivery.

   Use a visible-boundary-extension/adjacent-dark-content pair instead. A advances
   a blanking boundary. B retains normal blanking and adds dark picture immediately
   adjacent to it. Neither world hides the whole interval. This was already the
   algebra example in `experiments/extent_set_review_controls.py`.

   The new audit gives a cyclic sampled-level example: period 858, window 720,
   normal full interval 147.15 samples. Advancing its leading edge by ten samples
   gives the same delivered level signal as normal timing plus ten samples of
   adjacent dark content. Nine samples of normal blanking remain delivered.
   Period/sampling parameters follow [BT.601-7](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.601-7-201103-I%21%21PDF-E.pdf);
   nominal blanking duration follows [BT.470-6](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.470-6-199811-S%21%21PDF-E.pdf).
   Phase, extension and equal levels are authored test choices.

   This is admissible within the DECLARED SAMPLED-LEVEL MODEL, without the gap
   contradiction. It tests insufficiency of level evidence, not equality of the
   analog chain's full noise, filtering, sync and chroma observations. Those
   assumptions need qualification before a universal raw-row bound follows. A
   useful negative control for a level-only method does not need that universal
   claim. The source-wide same-dither assertion at line 105 still exceeds contract
   `:433-440`; it should name a synthetic assumption, not an established source
   property. Preserve rejection of the inadmissible construction, not a permanent
   prohibition on any function named `matched_pair`.

## Audit output (verbatim)

```text
FAIL B1 false visible truth rejected (selftest exit 0)
FAIL C1 false visible truth rejected (selftest exit 0)
FAIL missing calibration intervals rejected (selftest exit 0)
FAIL positive suite detects disabled guard: ok &= not bad
FAIL positive suite detects disabled guard: ok &= not clash
FAIL positive suite detects disabled guard: ok &= not tight
WITHIN-JITTER UNKNOWN CASE: fixture selftest exit 1
  5 every nonzero shift exceeds the calibration jitter -> FAIL: U1 within-jitter translation, U1 within-jitter translation
PASS edge-placed A2 shortening is valid and observable in synthetic samples
PASS extension/dark-addition matched in declared luma model, no hidden interval
PAIRED MODEL: normal interval still delivered on 9 samples; no physical bound claimed
AUDIT FAILED (6 unmet checks)
```

`python3 experiments/switch_fixture_repair_audit.py` exits 1. The first six checks
express desired positive rejection behavior, committed failing because the reviewed
implementation does not satisfy them. The uncertainty case demonstrates the scope
problem separately. Neither passing synthetic construction certifies a detector.
