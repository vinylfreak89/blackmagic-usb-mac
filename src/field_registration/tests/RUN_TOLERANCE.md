# Scattered-code tolerance ablation — diagnostic only

Production base `71d7c74`; engine unchanged from `856ec13`. No production
detector, policy, lock, geometry or classifier change. Capture 1 not accepted;
capture 2 not started. Nothing from the recordings is embedded in these tests.

## Counterfactual and provenance

Test membership within the current field's generated-blanking mean +/- six
standard deviations, instead of requiring an observed code. Six is the
**harness instrument's experimental choice**, not a standard, recommended
production tolerance, or claim that generated and source blanking are the same
population. No gap length is invented and no run is extended by interpolation.
The 147 floor and exposed-endpoint requirement remain unchanged.

Two scratch variants isolate the question:

1. `interior`: tolerant membership for the candidate interval only; original
   exact-code porches, local basis and source histogram remain unchanged.
   Exposure is checked against the candidate's own tolerant alphabet.
2. `all`: the same tolerance also identifies the source porches. All later
   predicates are unchanged, but their measured basis and histogram can change.

The production strict build is the control. The engine never receives a
harness row. Separately, a trace uses the published reference S to reproduce
the reported membership comparison. Reference SHA-256:
`aa26fedd5582460eab15e079e04347f85fa82f78018ade474a67b1f82d8d033e`.
No empirical sigma floor is used by either variant. A separate diagnostic
column applies the harness census's 0.5 floor; it selects the same 42 keys.

## The missing cross-tab, independently reproduced

At the published S rows for the prior 255 candidate failures:

| Longest-run result | Starts 0 | Starts 1–2 | Starts >=3 | Total |
|---|---:|---:|---:|---:|
| Under 147 even with tolerance | 169 | 15 | 21 | 205 |
| Reaches 147 with tolerance, not exact membership | **33** | **4** | **5** | **42** |
| Reaches 147 with exact membership | 8 | 0 | 0 | 8 |
| Total | 210 | 19 | 26 | 255 |

Thus the reported 205/42/8 counts reproduce, but the groups are not separate
physical causes. **33 of the 42 are edge-connected even with tolerance.**
Only nine offer two exposed endpoints; likewise 36 of the 205 short runs
start inside the window. A start of zero records censoring/edge connection,
not proof that these samples are physically blanking rather than dark content.

## Survival of the 42

Counts below mean at least one candidate anywhere in the field's actual scan,
not forced selection of the reference S. Each row is cumulative.

| Stage | Strict | Interior only | Interval and porches |
|---|---:|---:|---:|
| Exposed candidate >=147 | 0 | **9** | **9** |
| Unique run | 0 | 9 | 9 |
| Local two-ended basis | 0 | 4 | 9 |
| Complete leading-porch loss | 0 | 4 | 9 |
| Trailing minimum loss | 0 | 4 | 9 |
| Normal/partial predecessor | 0 | **0** | **1** |
| Source-histogram code support | 0 | 0 | 1 |
| CDF agreement | 0 | 0 | **0** |
| Surviving run observation | **0** | **0** | **0** |

Exclusive losses: interior-only has 33 no candidate, five no basis, four no
qualifying predecessor. Applying tolerance to both populations has 33 no
candidate, eight no qualifying predecessor, one CDF rejection. The latter is
6982/f2, line 523: CDF distance **0.421687764**, local envelope **0.135021097**.
No observation is accepted and subsequently cleared in this 42-key cohort.

The nine exposed keys are 6898/f2, 6936/f2, 6982/f2, 6996/f2, 7005/f2,
7017/f2, 7058/f1, 7141/f2 and 7147/f2. The scalar 42-key CSV retains the full
stage counts, reference interval endpoints (start and length), and verdicts.

## Control cost and verdict

All three variants retain **34/34** existing run controls. Six new constructed
scenes, both fields each, explicitly put code 4 among blank codes 1/2:

- Stationary interior black rectangle: rejected in both fields.
- Newly appearing edge-connected black rectangle, real trailing porch intact:
  rejected in both fields.
- Departure followed by return: rejected in both fields.
- Truncated interval: still Unknown in both fields.
- Wrong distribution: rejected in both fields.
- Genuine relocated complete interval with a partial predecessor: strict and
  interior-only abstain; the interval-and-porches variant recovers both fields
  at the constructed T (raster rows 256/519).

The new suite passes **12/12 per variant**, with those explicitly different
positive expectations. Therefore tolerance is exercised, and there are **zero
new false positives in the ten negative field-controls**. This is not an
estimated false-positive rate on arbitrary real content.
The broader variant's new controls also pass **12/12 under ASan/UBSan**.

It still buys **0/42 readings**. Across all 1,016 field readings, strict has
478 known T and six disagreements; interior-only 482/zero (it also loses the
old run observations); interval-and-porches 469/19. These are coverage and
disagreement counts, not accuracy or acceptance results. All phase T/S, top,
box and eligibility observations remain identical. All three analysis probes
report 919 exact units, zero locks and zero nonzero crops.

**Do not promote either tolerance variant on this evidence.** The negative
controls survive, but the requested real cohort does not recover. This does
not prove the 42 are intrinsically unmeasurable, nor license weakening their
predecessor or CDF checks. A production source-distribution model remains a
separate design question; six sigma on generated rows is only this ablation.

## Diagnostic correction and reproduction

An initial interior-only ablation changed run membership without checking
exposure in that new alphabet: it falsely counted 23 candidate-bearing fields
instead of nine. Fourteen newly tolerant prefixes were not truly interior.
Correcting the diagnostic to retain the required exposed endpoints restores
nine. The initial trace is preserved as `interior_unchecked`; it is not used
for the reported survival counts. Production was never changed.

Artifacts: `/private/tmp/run-tolerance.MhCmkF/`, especially `split_42.csv`,
`tolerance_summary.json`, and the strict/interior/all per-field/per-row traces.
Strict geometry and both join CSVs are byte-identical to the prior production
export. The diagnostic prints scalar traces; its timings include instrumentation
and are not production benchmarks. No new performance claim is made.

Reproduce into fresh output directories for each MODE (strict, interior, all):

    python3 src/field_registration/tests/switch_unknown_census.py CAPTURE OUTPUT/MODE \
      --previous /private/tmp/switch-causes.eig8nr/engine_switch.csv \
      --diagnostic-tolerance MODE --diagnostic-reference REFERENCE
    python3 src/field_registration/tests/run_tolerance_report.py OUTPUT \
      --baseline /private/tmp/run-stage.VlR6Rk --reference REFERENCE
    python3 src/field_registration/tests/run_tolerance_diagnostic.py --controls OUTPUT

CAPTURE is the original `captures/composite_program_30s.tpc`, not a slice;
REFERENCE is `/private/tmp/hw-session/v10/ref_capture1.csv` with the hash above.
