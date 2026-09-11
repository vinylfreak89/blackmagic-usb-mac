# Post-calibration harness review

Reviewed `0a8fabe`, `b9d1f7e`, `0b38bf5`, `584867f`, `d425259`, `0d1a00e`,
`47fa1b7`, `ed20348`, `2f81837`, and `91e2372`; merged through the last as
`879dc70da03a0bbda28cdd508660ccbe469c0517`. Source changes are limited to
`source_reference.py`, `per_unit_floor.py`, `review_frame.py` and CLAUDE.md.
The P3 repeats, R12 experiments, O-B6 summary and new skew-row figures were
recorded in prose, not accompanied by new measurement executables in these commits.

The additional `experiments/post_calibration_review_controls.py` is a review
instrument, not a repair. Both supplied selftests pass. The review reran a capture-1
row census and synthetic/mutation controls; it did not rerun the render, P3 timings
or R12 capture comparison. Engine and contract are unchanged.

## 1. The repair and the fabrication ceiling

The field-2 target indexing repair is correct for the current legacy-coordinate
implementation. The selftest now exercises the consumer. Mutating only that
consumer back to the old target coordinates, leaving fixture construction correct,
produces:

```text
FAIL: field 2's own switch rows did not assert
SELFTEST FAILED
```

The equality-plateau repair also works on the reported fixture:

```text
equal plateau arrival 717 settled 719 pooled 1.6 known floor 1.6
local rise arrival 717 settled 717 pooled 18.2 known floor 1.6
known settled-tail mean 3.0 reported 1.0
```

The second control changes one plateau sample from 26 to 27 before the final
descent to 1.6. It demonstrates that first-local-minimum settlement still does not
establish completed descent. The third is the previous known-mean control; the
value-selective `minimum block mean + 1.0` filter remains and still biases the
answer. These are synthetic counterexamples, not assertions about their frequency
on capture 1. The repaired equality case is not full settlement qualification.

Tightening recovery tolerance from ±10 to ±2 is real, but ±2 still cannot validate
a one-sample distinction. The gradual fixture still returns 701, while its injected
ramp floor is at 704. Its target 700 and the returned fractional-amplitude feature
do not establish exact physical arrival. The source still contains "NO FABRICATION",
"Flat picture and all-blanking rows both return None", and exact-arrival claims.
The new limit paragraph does not retract those assertions. Nor was "coverage"
replaced throughout: it remains in per_unit_floor's final output and source_reference.

The 12/12/36 ceilings reproduce over the fixed 200-seed families. They are useful
**regression ceilings on those exact controls**, not statistical upper bounds on
new seeds, new noise distributions or real signal. An unchanged count can also hide
which cases changed; preserving keyed failures would distinguish that from a stable
failure set. A zero count on a finite test would not itself prove universal identity
either. Nonzero candidate-feature errors need not block retaining an exploratory
instrument. They do block promoting its output to qualified blanking or switch
evidence without a demonstrated downstream discriminator/error treatment.

Rejecting a flatness variant for failing a known valid ramp is a legitimate reason
not to adopt that variant as a complete repair. It does not prove false negatives
are universally worse than false positives, or that no other qualification works.
The quieter-after predicate is not executable in the reviewed diff, so its failure
is a peer-reported experiment here. The prior review `698c11a` did not prescribe
that specific predicate; it identified the provenance/settlement gaps.

## 2. The skew-row rates reproduce, but they are not detection rates

The review calls the actual `unit_reading` function and traces its source reference
and target transitions. No target selection is changed. Capture 1 counters >=6667:

| field | fields available | target assertions / attempted | targets returning 719 | held-out fires / readable rows |
|---|---:|---:|---:|---:|
| 1 | 508/508 | 939/1524 | 1503/1524 | 119/40640 |
| 2 | 508/508 | 1097/1524 | 1522/1524 | 235/40640 |

All 3048 target rows were readable. **Every one of the 2036 asserted targets
returned sample 719**, not merely the maximum per field. The 62%/72% figures may
be quoted as positive-departure assertion fractions over these preselected rows.
They are not recall/sensitivity or detection coverage of independently identified
switch rows. The denominator problem can create both apparent misses and apparent
hits: an ordinary row in the assumed band is not automatically a true positive.
The asserted endpoint alone does not identify the temporal transition claimed.

The comparison is also one-sided. Using the same synthetic source with normal
blanking onset 600, the actual function gives:

```text
earlier blanking onset 500 normal onset 600 asserts False target departure -100.0
later blanking onset 700 normal onset 600 asserts True target departure 100.0
```

The contract's disturbance definition is departure in either direction. This
later-arrival test is not that general per-row primitive, and is not made one by
assembling a run. Missing/censored relocated intervals and interval identity remain
separate issues from magnitude exceeding a calibration maximum.

354/81280 = 0.4355% is reproduced as a held-out **positive-exceedance rate on the
selected nominally ordinary rows**. Calling it a false-positive rate requires that
negative-population designation; it does not validate the identities of positives.
The three historical methods have different statistics/selection/operating points;
these figures alone do not establish "20x better" detector accuracy.

The population happened not to shrink here. It can shrink in this code: unreadable
row transitions are skipped, and a field returning None is omitted by main().
"Its population cannot shrink" remains false. Parity disjointness does not establish
equal content effects, independence or exchangeability; the unchanged selftest still
prints that stronger implication. The common median cancels, so the previous review's
non-circularity conclusion for this max comparison is unchanged.

## 3. The structural-floor rule is mathematically false

A fixed 5th-to-95th empirical percentile interval leaves roughly 10% outside on a
continuous, untied population. That is a chosen interval mass, not an irreducible
9.6% error floor for percentile methods. Changing interval mass changes the tail;
ties and boundary conventions also affect it. Executable arithmetic counterexamples:

```text
(5, 95) outside 100 of 1000
(0.2, 99.8) outside 4 of 1000
(0, 100) outside 0 of 1000
tied population (5,95) outside 0 of 1000
```

These are not proposed detector thresholds. They falsify "no value of the cut" and
"a rate the percentile form cannot reach at any setting". Max is itself the endpoint
order statistic. Separating calibration from evaluation makes evaluation meaningful;
it does not by itself lower the true error rate. Indeed a training-set min/max gives
zero training exceedances without disjointness, which demonstrates the tautology,
not a working detector. General advice that all same-data estimators have an untunable
positive floor, or that disjointness usually repairs the estimator, should not land.

## 4. R12: the sign survives as a qualified association, not an adjudication

Fewer measured disturbances with the corrector on is relevant evidence against the
narrow hypothesis that this same observable is created by enabling that corrector.
Unpaired observations do not become useless merely because they are unpaired.
But the size of a raw count ratio does not neutralize selection or observability
differences. 1957 versus 11 are counts with unequal opportunities; report their own
row denominators and eligibility rules. The peak comparison has another population
(36/1174 versus 1–2/606). Do not attach the 396/1216 field counts to every statistic
as though they were one cohort. They do not measure joint per-event disappearance.

"Both vanish" is false as an absolute: both reported on-populations have residual
detections. The observations are consistent with the owner's account; they neither
establish it uniquely nor exclude a smaller TBC-introduced component alongside a
larger incoming disturbance that correction removes or makes unobservable. The
line-TBC-on pass is already documented to replace much affected content with flat
rows, so measurement opportunity itself changes. Writing a prediction before a new
test does not make already-known historical counts held-out evidence.

The four co-location cases are insufficient for the strong conclusion. Even a
large same-row coincidence count would not by itself establish one instant: that
requires within-row timing with uncertainty and identified landmarks. The rejected
device-row result is properly withdrawn, but its executable and keyed populations
are absent from these commits, so this review cannot independently verify the new
four-case result. Also keep the question straight: the older pending R12 discussion
cites field misregistration and a comb offset; the new comparison concerns horizontal
sample displacement. Those are not interchangeable outcomes.

## 5. P3, O-B6, the render and the device-fill rule

The P3 three-run series establishes a 2.7% range of medians in those three later
executions, not exclusion of run-to-run variance generally. First-run-fastest does
not rule out cold-cache effects in a different earlier execution; these medians each
summarize 10,000 calls. Host-side attribution remains an inference, not isolated by
elapsed time. Retain 20.992/47.851 as measured elapsed overruns on their workload/load,
without treating them as baseline CPU cost. The low direct-engine runs still do not
close the whole-path budget. These are the same scope limits as `eb1cb5d`, not a
request to stop the owner's applications or repeat uncontrolled timing indefinitely.

O-B6 correctly distinguishes an instrument definition from an engine or contract
definition. But `none` means neither bar reaches minband after sufficient content
is found, not literally no bars or picture reaching both edges. The actual functions
on five-row bars at both ends return:

```text
top 5 bottom 5 verdict none
```

The recorded summary also omits the leading/trailing short-run exclusions (`tail=8`,
`switch=6`), and the source's old FIELDS ranges include device/cross-field boundary
rows. h has an actual denominator floor of 0.5; a measured denominator of 1.0 is not
its definition. The run/threshold verdict is operational, not a completed physical
definition of structurelessness, boxing or unbounded geometry.

`b9d1f7e` adds T/clip marks and suppresses invalid/Unknown values. Its row arithmetic
matches the existing exporter (row+4); it is not a field-relative-label migration.
This review inspected the change, not the rendered video or claimed pixel census.
The builder still slices fixed 486 windows and takes applied d only as display text.
An all-(0,0) run therefore does not validate displaced rendering. A fixed crop also
does not establish stability of identified source lines inside it; source content
can move despite a stationary output window. Do not broaden the marking change into
proof of all render requirements or the first-six-lines criterion.

"Check the consumed population when an answer is suspiciously clean" is useful.
"Device fill is constant, any statistic is perfect, nothing real is perfect" is
not: hard padding is constant, generated blanking is dithered, and regenerated
inserts can carry changing decoded data. Real finite populations can separate
exactly. Check row ownership/provenance before interpreting every result, not only
perfect ones; imperfection does not exonerate a device-row measurement either.

## Reproduction

```sh
python3 experiments/source_reference.py --selftest
python3 experiments/per_unit_floor.py --selftest
python3 experiments/post_calibration_review_controls.py
python3 experiments/post_calibration_review_controls.py --capture /Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/composite_program_30s.tpc --csv /private/tmp/post-calibration-review.VmgsGx/row_assertions.csv
```

The keyed scratch census SHA-256 is
`ac67c05ea292aaedfc010f02a9aef638f0bf7feff1fcc3731a127c339528d3b2`.
The committed probe regenerates it; scratch is not a durable input dependency.
Mutation failure above is expected and confirms the guard. Other controls document
remaining limitations; the probe deliberately reports their values without repairing
the measured functions. No new engine or contract edits are proposed here.
