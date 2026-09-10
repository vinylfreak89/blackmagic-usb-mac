# Terminal off-reference run: review, not a replacement detector

Input `f4f24ca`, merged before review. The previously approved `98a3307` was
pushed to `origin/v10-engine` first. No engine or contract change is made.

## Decision

Keep the terminal-run proposal as a candidate to test, not an adopted switch
measurement. The reported experiment rejects the particular **first
off-reference hit** rule on this selected cohort. It does not reject downward
traversal, establish that every row in the terminal run is positively identified
skew, or establish that the run's upper boundary is T.

The head-switch region's terminal location is relevant under the owner's rule.
An exact contiguous suffix of failures of a reference test is an additional
measurement criterion that still needs qualification. The change from first
hit to terminal run changes the decision rule, not merely traversal direction.

The same terminal suffix can be found upward or downward. An exhaustive
non-raster check over all 1,024 ten-element Boolean sequences gave identical
starts: scan back from the end while flags are true, or scan forward retaining
the latest run start and clearing it whenever a false flag arrives. This does
not validate either row predicate; it isolates the direction claim.

The engine already scans downward with return-to-normal cancellation:
`measure_switch` clears a departure on return to its previous phase, and
`measure_run_switch` clears one on return to its held porch profile. It is not
the naive first-off-reference comparator in the new table. This does not
excuse its separate unsupported T=S fallback.

## What the rates do and do not establish

The supplied 71.5% exact and 94.0% within-one figures are **agreement with the
engine on 284 selected readings**, not accuracy against independently identified
T. The six original disputes have engine T Unknown in the referenced export,
so a T-known cohort excludes them. It cannot adjudicate them indirectly through
its aggregate agreement rate. Engine-abstention and reference-unaskable cohorts
also remain outside this figure.

The supplied 9.6% is an observed off-reference rate in the chosen control rows.
A 5th–95th percentile band does not guarantee a 10% held-out false-positive rate.
Discrete ties, sample size, integer rounding, conditioning and distribution
changes matter. This predicate requires both start and length to match, and
allows any matching run; two marginal quantile bands do not define a calibrated
joint error rate. A simple counterexample is 51 tied values: both quantiles
equal the value and zero of the 51 observations are outside the band.

If flags were independent with constant probability p=0.096, their expected
first-hit position would be 10.42, not a guarantee of a hit within ten rows.
The probability of a hit within ten would be 63.55%, and within 240 almost one.
Those are conditional-model calculations, not properties measured here.
They explain why a noisy first-hit rule is dangerous under that model; they
cannot establish that every learned-band detector or downward scan is unusable.

The 22.5% exact-one-row extension is not comparable to 9.6% as a chance baseline
without further work. It is conditioned on the terminal-run selection, known
engine T and usable references, and concerns a different location in the field.
Adjacent errors share references and can be correlated. Even an idealized iid
null with a guaranteed true run beginning at T gives p(1-p)=8.6784% for an
**exactly one-row** false extension, as distinct from p for at least one.
Neither idealized number is an established null for these captures.

Therefore "something real sits there" is not established by the ratio alone.
The residual is a useful disagreement population; it does not choose between
detector overreach and a late engine boundary.

## Measurement that separates the alternatives

Freeze the keyed residual population and matched controls before adjusting
the reference or detector. Include exact agreements, other discrepancies,
the original six T-Unknown keys, and appropriate unaskable/abstention cases.
Preserve unit, physical field, displayed/storage mapping, engine component
readings, clip provenance, reference samples and exclusions. The engine T may
select a diagnostic neighbourhood, but must not label the independent answer.

For each candidate T-1, reconstruct the signal chronology through that scan
and into the following one, including the unsampled time interval explicitly.
Measure the identified own-blanking timing and any transition between the
before/after timing states, with uncertainty and censoring. Do not use a
content-correlation lag or an out-of-percentile label as timing identity.
Keep the candidate out of the reference used to judge it. Use independently
qualified normal timing references, not location alone as their qualification.

The deciding observations are:

- Positive head-switch timing disturbance already on T-1: the current engine
  T is late, subject to the established meaning of current observed T.
- Positive normal timing on T-1 while only the proxy leaves its reference
  envelope: the terminal-run detector overreaches.
- Timing identity not resolvable: the boundary remains Unknown. A failed test
  does not choose either answer.

Estimate a boundary-appropriate control distribution with the same predicate
and selection rules, retaining adjacent-row and within-unit dependence. Report
run-length errors and their dependence, not just a pooled marginal flag rate.
Do not treat every pixel or adjacent row as an independent replicate.

Before adoption, test a single affected partial line, a normal-looking or
unreadable row inside an otherwise affected region, source blanking/remainder
after the band, an uncertain/censored clip, and held bounds after a partial
disappears. A numeric clip in an export is not by itself evidence that a
positively identified switch region reaches it. Current observed boundaries
and qualified retained bounds remain separate.

## Reproduction gap

`f4f24ca` records the result in CLAUDE.md. The supplied
`experiments/switch_without_shift.py` tests for any off-reference row within
an engine-selected T/S-to-clip interval. It does not implement the new
top-down/terminal-run comparison or emit its 284-key table. No keyed artifact
or executable reproducing that comparison was located in the supplied changes.
The percentages above are therefore attributed results, not rerun measurements.

Please provide that executable and keyed output, including the exact control
range: 28,400/284 is 100 rows per reading, whereas lines 100–200 inclusive
would contain 101. The reference code uses 51 rows at lines 200–250; the
precise endpoint convention also determines reference/control overlap.

The existing script also retains explicit selections: reference lines
200–250, a blank+1 code comparison, 5/95 percentiles, minimum 20 reference
observations, and a greater-than-40 start-range exclusion. The last was
reported inert on the tested sample, not removed or generally proved inert.
Learning reference values does not make these choices threshold-free.

## Two scope corrections

The unsampled 16.08% is a fraction of **line time**, not "roughly one line in
six" observations. No phase-frequency estimate follows from it. T remains
unresolved when its required history cannot be established; no S-1 default
is licensed by the temporal framing.

Being a symptom of skew prevents treating peak-present and peak-absent as
distinct underlying signal regimes. It does not make all comparisons of
measurement coverage meaningless: different observables of the same event
can have different availability. Such comparisons require explicitly defined
populations, qualified event labels where needed, and separate Unknowns.
The supplied three-word fragment does not by itself define T universally.

The relayed column 191 result, if independently qualified, falsifies the
specific late-column prediction for 6722. It does not reject the temporal
model itself or identify the remaining peak-free switch times. This review
did not inspect or rerun that column detector.

## R3 queue instruction

Yes: put the following in the owner queue, attributed to Codex, as a narrow
recovery clarification rather than reopening the invalid-signal predicate:

> When good video returns, does "starts from scratch" still apply—must it find
> a new lock before correcting the picture again?

The status should distinguish "invalid-signal gate ruled" from "recovery
clarification pending". The old blanket CLOSED label must not be used as
evidence that this clarification has already been answered. This report
authorizes that queue wording; it does not claim the question has been sent.
