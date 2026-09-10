# Historical masked comb: failed commercial confirmation

This report describes the pre-plain-comb engine. It and its private-API probes
are historical; [PLAIN_COMB.md](PLAIN_COMB.md) describes the current reader,
schema 21 and first capture-1 locks. The failures below are preserved, not
claims about the current executable.

This implementation runs a comb measurement; it has **not fixed the commercial
acceptance failure**. Its synthetic goldens pass, but it confirms **zero** real
units. The shared-support/search premise needs review before another change.
This is an engine measurement failure, not an open owner-output preference.
No contract or signal-state rule was changed.

Queueing follow-up: `../../frameserver/QUEUES.md` supersedes the publication
coupling described below. The previous witness now belongs to analysis at its
own decided crop; downstream delivery failure no longer clears that witness.
The comb algorithm and the failed measurement below are otherwise unchanged.

## What is implemented

`comb_lowpass`, `comb_pair`, `comb_search` and `comb_confirm` in
`field_registration.c` replace the unconditional comb stub. Geometry still
places the crop; the comb records confirmation/disagreement and does not install
a crop correction. A decisive reading can settle precedence once per lock and
confirm the measured switch counts; existing counts are not relearned. A later
disagreement reports Drift without changing that precedence. Discontinuity
invalidates the temporal witness; source reset also invalidates precedence.

Each row is represented by disjoint eight-sample luma sums covering all 720
samples. The eight-pixel low-pass aperture comes from the earlier static-comb
measurement recorded in CLAUDE.md section 11. Disjoint boxes are this
implementation's sampling choice, **not a claim of equivalence to the old audit**.
Energy is the mean absolute difference of field 2 from the mean of its two
adjacent field-1 rows, expressed in luma-code units.

Temporal differences compare the current crop with the previous unit at its
OWN published crop. Both fields, including field 2's adjacent rows, must pass
the static test. The tolerance is the largest observed change of a low-pass
sum over the pair's regenerated blanking rows (raw rows 7–15 / 270–278), not
the old fixed luma cutoff. This is an observed regenerated-row fluctuation,
**not a demonstrated model of analog picture noise**. Picture support excludes
rows outside the current and previous measured picture bounds and the raster;
when the switch is unmeasured the last recorded row supplies the lower limit.
Publication failure invalidates the pending witness, so an unpublished crop
cannot seed the next temporal comparison.

The current search considers every signed relative shift with visible overlap,
bounded by the 240-line aperture and the adjacent-row stencil. Every PAIR of
candidate alignments uses identical static pixels at both times. It does **not**
use one mask shared by the entire full-range search: there is no useful common
intersection across all those displacements. A tournament proposes a candidate;
a verification pass requires it to beat every supported alternative on their
shared pixels. The candidate's larger energy across the two units must be below
the alternative's smaller energy. Missing static support, ties or overlapping
two-unit energy envelopes abstain. These envelopes are not statistical
confidence intervals.

Full-range pairwise dominance is **our attempted algorithm, not an owner rule**.
It fails in the commercial run: distant candidates with tiny overlaps veto the
local reading, and there is no decisive global pairwise winner. Median support
in the limiting comparison is ONE eight-pixel block, fraction 0.000046 of the
240×90 grid. That is not enough evidence to interpret its proposed displacement.
At counter 6687 the unconfirmed candidate is +232 with 191 unresolved
alternatives; at 6690 it is +232 with 83. Neither is a measured picture shift.

Sidecar schema 17 appends `comb_candidate_shift` and
`comb_unresolved_alternatives`. The first is explicitly diagnostic, not a
placement or confirmation. `comb_best_shift` remains Unknown unless decisive;
its type is now signed 16-bit and Unknown is -32768, since -128 is an actual
member of this search range. Best/second energies and static fraction describe
the limiting comparison on the SAME pixels; a losing provisional candidate
can therefore have a larger reported energy than the alternative. `flat` means
no decisive reading, not necessarily a physically flat picture.

## Failing-first evidence and falsifications

- `be3c7a7` committed the first public-API comb golden against the stub:
  **4/17 passed**, 13 failures.
- A local-search prototype passed those tests and produced commercial
  confirmations, but a wider synthetic check falsified it: relative shifts
  -7, -4, +4 and +7 were incorrectly reported as agreement. It was rejected.
  Its commercial agreement counts are not an accepted result.
- The original positive pattern was itself periodic over 60 rows. That cannot
  establish full-range uniqueness. `fbfc7ee` changed the positive fixture to
  aperiodic detail, retained the periodic case as a required abstention, and
  added a four-line mismatch. The committed stub then passed **4/19** (exit 1).
- An initial full-range version ranked means taken on different supports.
  That ranking was invalid and was replaced by the pairwise comparisons above.
- The current implementation passes **19/19**, also **19/19 under ASan/UBSan**.
  Assertions cover running measurement, calibrated agreement, one- and four-line
  disagreement without crop mutation, unchanged settled precedence, return to
  agreement, previous unit at its own crops, discontinuity/reset, flat and
  periodic abstention. Passing those tests does not validate the failed search
  on real noisy picture.

The field-registration suite also reports unit 18/18, caption 3/3, rule 1 5/5,
rule 3 2/2, rule 4 5/5 and synthetic switch 32/32. Frameserver
`test-registration-gate` passes `non_program_never_measured` and
`signal_gate_preserves_published_crop`. No classifier changes were made.

## Commercial paced replay

Input: `captures/composite_program_30s.tpc` from the main checkout. Reproduction:

    src/frameserver/frameserver_replay CAPTURE FRESH_OUTPUT.csv --pace-us 16000 --ring-mb 512 --pool 32

Actual scratch record:
`/private/tmp/v10-comb-final/registration.csv`

SHA-256:
`7cf020a146587032846ec8504e9ff89a6c730bae21a6b312788a5e7186e99323`

| Result | Units |
|---|---:|
| Exact units published | 919 |
| Registration gated; comb not invoked | 467 |
| Registration invoked | 452 |
| No previous witness | 3 |
| Comb computed but ambiguous (`flat`) | 449 |
| Decisive agreement | 0 |
| Decisive disagreement | 0 |
| Calibrated precedence / comb-safe | 0 |

Replay: 930 observations, 919 exact, six short, zero holes, three unframed,
two device no-signal units; zero pool/ring/surface drops. All 919 published
rows use schema 17. Relative to the prior saved commercial record
`/private/tmp/v10-switch-review-fixed/registration.csv`, applied crops,
appearance labels and registration eligibility changed in **zero** units.
The existing eleven nonzero-crop units remain eleven; that is not proof they
are correct. Nothing was scored on another capture.

## Cost: over budget, not hidden

Final native O3 probe, all 452 registration calls, scalar timings in
`/private/tmp/v10-comb-profile.4jGFg7/units.csv`:

| Path | Median ms/unit | p95 ms/unit |
|---|---:|---:|
| Engine | 9.261 | 16.247 |
| Classifier plus engine | 9.617 | 16.603 |

p95 is the sorted sample at floor(0.95×(N−1)). This is not a whole-worker
benchmark: it excludes publication, queueing and sidecar I/O. It already exceeds
the whole-worker 10-ms budget.

The rule goldens' more expensive synthetic paths measured median/p95
19.604/20.731, 89.396/92.566 and 92.151/97.443 ms respectively. Before separating
the deferred performance gate, `make test` failed verbatim:

    Assertion failed: (p95 <= 10000.0), function main, file field_registration_v10_rule1.c, line 77.
    make: *** [test] Abort trap: 6

Per the owner's explicit correctness-before-optimization instruction, these
three tests now always report timing and print `PERFORMANCE BUDGET EXCEEDED`
when applicable; `FIELDREG_ENFORCE_BUDGET=1` restores the fatal budget assertion.
Their passing correctness counts are not a performance pass. Engine state is
189,108 bytes, within the existing 256-KiB state-capacity test; no engine heap
allocation was added.

## Remaining work

The next design review must resolve meaningful comparison support and the
temporal-noise model. Requiring a whole-raster candidate to win against every
remote one-block overlap is not a useful confirmation test. Conversely, the
falsified local search cannot be reinstated as a proven global reading. A
geometry-constrained comparison must state exactly what it confirms and which
ambiguities it cannot resolve, and must be checked on the commercial picture
as well as the alias controls. This turn did not resolve that measurement.
The comb is running, but capture 1 has **not passed**.
