# Independent run timing observation — qualified, capture 1 not accepted

## Measurement and limits

The existing phase-envelope instrument is unchanged. The new reader scans
the same current-unit top..recorded-last rows and retains a second T/S pair.
Neither reader uses the harness's candidate row, counter or verdict.

The new observation requires all of the following:

- A unique interior contiguous run at least 147 samples long. Its endpoints
  must both be exposed, rather than connected to the delivered edges. 147
  comes from 10.9 us at 13.5 MHz; no 64 floor or 200 ceiling is imported.
- Run samples belong to the current field's generated-blanking code alphabet.
  This only locates candidate runs; it does not distinguish black content.
- Locally readable **source** porches at both delivered ends, in a 16-row
  history (the existing memory capacity). Their combined length must reach
  the nine-sample overlap but remain shorter than a full blanking interval.
  Requiring both ends is an explicit instrument limitation, NOT a claim that
  the standards guarantee blanking at both ends on every source.
- Complete loss of the leading porch and loss of the trailing porch's local
  minimum extent. A surviving leading remnant cannot identify a FULL row.
  A stationary black rectangle with unchanged porches is therefore rejected,
  even when its samples are exactly identical to blanking.
- Agreement with the local source-porch distribution: every run code has
  appeared in those porches, and the run's maximum CDF difference from their
  pooled histogram is no greater than the greatest per-row porch CDF
  difference from that pool. This is an empirical within-unit variability
  envelope, NOT a statistical confidence or a guarantee on another source.
  Distance and tolerance are both recorded. Histograms have 256 entries,
  the complete 8-bit alphabet; no fixed level/noise threshold is introduced.

The preceding row must positively retain normal timing or a leading porch
with lost trailing timing. The latter supplies partial T=S-1, otherwise T=S.
A later readable full row cannot be called FIRST if the preceding row had
already lost both porches. Return to the established two-ended porch profile
clears a mid-field event. References are stack-local and rebuilt every call;
no reference or bound is trained across a reset or a source-gated raster.

This is deliberately incomplete: one-ended timing, noisy/interrupted runs,
multiple long dark intervals, unreadable source porches, or incompatible
distributions can still abstain. The current run length is a measured low-run
extent, not proof that every sample in it belongs exclusively to blanking.
The additional positional witnesses are essential; level alone proves nothing.

## Integration, not a new lock policy

Both independent T/S pairs, the run's sample start/length, its distribution
distance/tolerance, and disagreement are in `fieldreg_field_decision` and
schema-20 sidecars. If one reader abstains, the other may supply the current
observation. If both agree, that observation is reported. If they disagree,
T/band is Unknown, while an agreed S is retained; both original pairs remain
explicit. There is no selected winner on a disagreement.

No acquisition site, held-bound rule, top reader, classifier, box placement
or comb changes. Boxed geometry is still Unknown. No source lock or count is
seeded from a categorical box verdict or an assumed standard origin.

## Tests

Failing-first commit `23d1ec4`: RUN-TIMING 6/10. The four failures were:

    relocated run survives envelope overlap: got -1 expected 257
    retained prefix identifies partial row: got -1 expected 256
    relocated run survives envelope overlap: got -1 expected 520
    retained prefix identifies partial row: got -1 expected 519

The original tests include the stationary black rectangle, relocated full
and partial rows, departure-and-return, and a sub-147 negative. Expanded
controls also cover a surviving leading remnant, exposed S without a partial,
the wrong blank distribution, and conflicting T with a common S. The latter
requires both observations retained, T Unknown and S still observable.
Final test: 34/34, including ASan/UBSan. No raw content is embedded in tests.

## Capture-1 census

`switch_unknown_census.py` instruments the unchanged phase predicates and
times the added routine separately. Its `phase_cause` continues to describe
the OLD phase-only result, while `cause` names recovery or disagreement in
the combined observation. `phase_T/S` are unchanged on all 1,016 comparison
keys. The previous non-box cohort remains the actual 527, not the brief's 526.

Of the 265 `no_disjoint` readings, **one is recovered** (7034/f2, T523 S524)
and **264 remain Unknown**. The new reader also recovers the boxed 6764/f2
T522 S523, previously cleared by a return. This does not close the coverage
gap; no threshold was changed to reproduce the harness census.

Six previously measurable T readings now disagree. All agree on S:

| counter / field | phase T/S | run T/S |
|---|---|---|
| 6681 / 1 | 260/260 | 259/260 |
| 6700 / 1 | 261/261 | 260/261 |
| 6704 / 2 | 524/524 | 523/524 |
| 6722 / 1 | 260/260 | 259/260 |
| 6749 / 1 | 261/261 | 260/261 |
| 6785 / 1 | 261/261 | 260/261 |

These are observations for adjudication, not six asserted engine corrections.
Current T coverage: 279 f1 / 199 f2, 478/1,016 combined versus the prior 482.
Live-gated T: 221/154. There are 538 Unknown T values, including six explicit
disagreements; common S stays in the join CSV. No acceptance pass is claimed.

Exports and execution-path census live in `/private/tmp/run-timing.DdLgYt/`:
`engine_switch.csv`, `engine_switch_live_gated.csv`, `unknown_causes.csv`.
Exactly counter,field,T,S in each join file; counter >= 6667, both fields;
NTSC lines, -1 Unknown independently for each coordinate. The raw-detector
variant evaluates all exact rasters diagnostically; live-gated additionally
marks both coordinates Unknown when registration did not run.

Reproduce from the original CAP1 (not a cut or harness reference):

    python3 src/field_registration/tests/switch_unknown_census.py \
      /Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/composite_program_30s.tpc \
      /private/tmp/run-timing.DdLgYt \
      --previous /private/tmp/switch-causes.eig8nr/engine_switch.csv

The CAP1 probe disables its optional raw export. The plain C probe and actual
paced worker provide separate checks of the instrumented outputs. The
worker sidecar has schema 20; all new fields must align with the header,
and non-program rows must not manufacture timing observations.

## Verification and timing

Final paced worker: 930 observations, 919 exact/published, zero input/output/
log drops or log errors. Zero locks and zero nonzero applied crops. All 176
sidecar columns align on every row; both component T/S pairs, combined T/S,
distribution distance/tolerance agree with the probe after applying the live
gate. Plain and instrumented geometry exports are byte-identical. An earlier
comparison read the file while its writer was still running and printed False;
the completed-file assertion passes, so that was not a detector discrepancy.

Added run routine, both fields summed per actual registration unit (452):
median **0.3115 ms**, nearest-rank p95 **0.372 ms**, measured around the routine
in the diagnostic build. This is added work, not an inferred speedup from two
wall-clock runs. Plain O3 classifier/engine probe on the same input:
engine-only **8.345/12.497 ms**, classifier plus engine **8.698/12.848 ms**.
The prior reported 9.7475/16.772 ms was a different run; comparing those alone
does not isolate this routine's cost.

Actual O2 paced analysis worker, including output copies/enqueues, excluding
independent sinks: all 919 exact units **0.888/12.744 ms** median/p95;
452 registration calls **9.169/13.923 ms**. Worker p95 uses the existing
queue_bench index floor(0.95*(n-1)); probes use nearest rank. Other synthetic
tests ran concurrently. The whole-worker 10-ms budget is **not passed**;
performance is recorded, not gating.

Functional suite: unit 18/18, CEA 3/3, rule1 5/5, rule3 2/2, rule4 5/5,
switch 32/32, comb 19/19, unlocked placement 24/24, box 25/25, run 34/34.
Run controls also pass 34/34 under ASan/UBSan. The synthetic timing failures
remain verbatim (make returns zero for functional checks):

    PERFORMANCE BUDGET EXCEEDED: 21100.000 us/unit p95
    PERFORMANCE BUDGET EXCEEDED: 91584.000 us/unit p95
    PERFORMANCE BUDGET EXCEEDED: 92557.000 us/unit p95
