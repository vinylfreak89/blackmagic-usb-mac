# Switch observations and the capture-1 Unknown census

## Settled change, not a bounds policy

Rule 8: "So on a boxed picture the switch is measured like any other" and
"The unit's own current observations are reported either way." The reader now
runs `measure_switch` before the categorical box return. T/S, current bottom,
span and visible band extent are observations, not held bounds. The boxed
path still returns before deriving displacement, picture-row count, or a
switch-line count. Boxed geometry remains Unknown; the existing caption and
comb eligibility paths cannot acquire from these observations alone.

No assertion is made about which bounds must be held, how to initialise them,
or a lift-off classifier. Those questions remain open. This is not full rule-8
conformance. No detector predicate, top reader, box classifier, signal gate,
comb algorithm or acquisition site changes. The old blanket exclusion test
and its replay checker describe a superseded requirement.

## Deciding test

`box_exclusion_test` retains its filename, now prints BOX-SWITCH-OBSERVATION.
An explicitly boxed synthetic raster exposes a partial row and a following
relocated full blanking interval. Both T/S and the visible extent must be
reported; no geometry/count or fresh lock/crop may be inferred from them.
Existing weak-texture, one-ended, gain-halved and held-crop controls remain.

The first draft's synthetic full rows had zero median adjacent noise but
nonzero spread; the box observer correctly refused that constructed input.
Adding alternating one-code noise to those synthetic rows (not changing the
detector) corrected the fixture. That draft failed as follows:

    FAIL: box with timing is observed
    FAIL: switch observation does not seed boxed geometry
    FAIL: box with timing is observed
    FAIL: switch observation does not seed boxed geometry
    FAIL: observations alone establish no lock or crop
    FAIL: 6668 box reports directly measurable switch
    FAIL: 6668 box reports directly measurable switch
    BOX-SWITCH-OBSERVATION: 24/31 passed

Failing-first commit e27dbe9: 22/31. The initial optional cached luma-only
control incorrectly required a readable switch; the direct reader abstains
on that input too. Its post-change failure was retained:

    FAIL: 6668 box reports directly measurable switch
    FAIL: 6668 box reports directly measurable switch
    BOX-SWITCH-OBSERVATION: 29/31 passed

The optional control now checks equality with a direct invocation, including
abstention. It does not assert detection on that luma-only reconstruction.
The final test was rerun against the old engine: 24/31, seven synthetic/public
observation assertions fail. On the changed engine: 31/31, also ASan/UBSan.
Full original-CAP1 counter 6668 is separately readable in both fields; it is
not the cached luma-only test input.

## Census definition and reproducibility

`switch_unknown_census.py` generates a scratch C translation unit from the
current engine, adding counters beside the actual predicates without changing
them. Exact replacement assertions fail if the source structure changes.
It builds the existing strict CAP1 `switch_probe` with these counters. The
optional raw export is disabled by a counter outside the 16-bit alphabet.
No raw recording content is written to the repository or diagnostic output.

    python3 src/field_registration/tests/switch_unknown_census.py \
      /Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/composite_program_30s.tpc \
      /private/tmp/switch-causes.eig8nr \
      --previous /private/tmp/switch-agreement.sVDxfc/engine_switch.csv

The separate uninstrumented `switch_probe` run has byte-identical geometry.csv
and identical non-timing live output. This checks that instrumentation does
not change the readings. Engine source SHA-256:
`3de0b0687e6b010e67343843b0767f11cc9c1421f94f6b248352d95a702deca3`.

The two join files each carry counter,field,T,S for 6667..7174, both fields:
1,016 unique keys. T is the top switch row; S is the first entirely other-head
row. NTSC lines, -1 Unknown. `engine_switch.csv` measures every exact raster
diagnostically, including source-gated units; `engine_switch_live_gated.csv`
additionally marks those gated observations Unknown. Neither is a held bound.
`unknown_causes.csv` retains all predicate counts, box/eligibility flags,
last accepted/returned lines, cause and membership in the prior non-box cohort.

The prior artifact has **814 Unknown T values, 287 box exclusions and 527
non-box Unknowns**, not the brief's 811/285/526. The original file SHA-256 is
`b54e7e83e31aaef5ced22644ca9d989e0d43b0df4296e413d7012ae811fd7333`.
Every non-box T/S pair is identical before and after this observation change.

## The 527 prior non-box Unknowns, mutually exclusive execution causes

| First unsatisfied stage / terminal clearing | f1 | f2 | Total |
|---|---:|---:|---:|
| No complete 147-sample blanking interval | 1 | 0 | 1 |
| No complete-interval candidate has a readable local basis | 68 | 7 | 75 |
| All complete-interval candidates with a basis overlap its phase envelope | 122 | 143 | 265 |
| All remaining candidates retain a normal prefix | 0 | 2 | 2 |
| All full candidates vetoed by the preceding same displaced phase | 31 | 8 | 39 |
| Departure accepted, then cleared by return to its pre-departure phase | 1 | 144 | 145 |
| Total | 223 | 304 | 527 |

The scan considers the entire current measured top..recorded-last region.
For fields with no accepted candidate, the classification is the first zero
in the nested candidate funnel **over that whole scan**, not an assertion
about which particular row is the true band. A complete interval elsewhere
in picture can enter that funnel: these counts do not establish that the
physical switch satisfied the complete-interval test. No harness T/S was used
to choose candidates, assign causes or tune a predicate.

If a candidate was accepted but the result is Unknown, a subsequent phase
return cleared it. Of those 145 last returns, 141 are at NTSC 525 (f2), three
at 524 (f2), one at 262 (f1). That locates the dominant clearing event but is
not an adjudication that the terminal row genuinely resumed normal timing.
494 of this 527-reading diagnostic cohort are live registration calls;
33 are gated. No missing-top or wholly unreadable-profile case occurs here.

## Result and limits

280 boxed observations are restored. Current raw export: 284 known f1 T,
198 known f2 T, 534 Unknown total. Live-gated export: 226/153 known. Boxed
Unknowns remaining: seven; non-box Unknowns remain 527. Counter 6687 now
reports T/S 260/261 and 522/523. No detector agreement claim is made.

The classifier/engine probe processed all 919 exact units; geometry_lock_known
and nonzero applied d1/d2 counts are all zero. This is an analysis-path replay,
not a new paced publication/queue benchmark. Plain, uninstrumented timing:
452 actual registration calls, median 9.7475 ms / p95 16.772 ms engine only;
classifier + engine 10.1395 / 17.165 ms. Nearest-rank p95, concurrent `make test`.
This excludes publication and logging and is not a whole-worker budget pass.
Performance is recorded, not gating; capture 1 is not accepted and capture 2
was not run.

`make test` exits zero: unit 18/18, CEA 3/3, rule1 5/5, rule3 2/2,
rule4 5/5, switch 32/32, comb 19/19, unlocked 24/24, box 25/25 without
the optional cached input. Its synthetic budget warnings are not passes:

    PERFORMANCE BUDGET EXCEEDED: 20417.000 us/unit p95
    PERFORMANCE BUDGET EXCEEDED: 94777.000 us/unit p95
    PERFORMANCE BUDGET EXCEEDED: 100686.000 us/unit p95
