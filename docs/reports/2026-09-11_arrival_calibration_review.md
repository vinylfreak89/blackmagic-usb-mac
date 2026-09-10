# Arrival finder, settlement and per-unit calibration review

Reviewed `8be9d89`, `04767be`, `b03265d`, `0c72441`, and `e847da74345883ea7a3989b48b51c746e699496b`.
Merged through `e847da7` as `3232b74c15fc544ce7d25fb4a7c1ad2d01c7a579`. Other incoming render changes are
not part of this review. No engine or contract change is made; the additional executable is a review probe,
not a replacement implementation. Source capture: the original capture-1 CAP1, counters >=6667.

## Findings and disposition

The finder removes the fixed sample-540 origin and repairs the specific steepest-fall failure. The rejected
variant control genuinely detects an injected defect. Neither result establishes the broader claims of
source-blanking identity, exact arrival, or no fabrication. The position/level separation is a sound interface
distinction, but the settlement implementation still admits ramp samples and its pool can bias the mean.

The operating-point sweep is exploratory, not independent validation of a chosen operating point. Its executable
and keyed populations are not committed with the cited change, so the reported 30-unit sweep cannot be audited
as fully as the per-unit experiment. Per-unit calibration avoids the simple fit-and-test-on-the-same-values
tautology, but has a wrong-field indexing defect and does not yet measure switch detection coverage.

## 1. A real variant control, with much narrower scope than the claims

Both supplied selftests pass. The abrupt fixture constructs a real step at sample 700 before the finder runs.
The retained implementation reports 700; `_ref_at_crossing=True` reports 717. Forcing that branch through the
production entry point makes the ordinary recovery check fail and selftest return 1. This is not merely checking
that a flag has a preferred value: it is a known-position counterexample to the rejected implementation.

However, requiring the old variant to remain wrong is a regression sentinel for that particular defect, not a
general scientific requirement that future alternative algorithms must fail. The authoritative requirement is
recovering the injected event and abstaining where identity cannot be established.

The four recovery checks use tolerance **±10 samples**, not exact equality. The current gradual fixture returns
701 against `want=700`; its explicit linear ramp actually reaches its injected floor at 704, and the returned
sample is still 5.3857 rather than 1.4. Thus "4/4 exact" does not describe the committed test. The tolerance
also cannot establish the one-sample precision needed by the bright comparison. In the production code, the
returned position is a second fractional-amplitude crossing, not a general detector of where the descent ends.
Calling it a position feature is possible; calling it the identified end of blanking arrival is not established.

The negative controls contain one deterministic realization of each noisy family. Repeating their same
picture-only and blanking-only Gaussian families over seeds 0..999 yields **61 non-Unknown transitions out of
1,000 in each family**. This is a synthetic control rate, not a measured capture false-positive rate. A terminal
dark-content rectangle, with no source blanking in the delivered samples, also returns a transition and trains
its content level as blanking. The finder requires an ending below its own midpoint; it has not identified the
physical provenance of that ending. Its no-fixed-search-origin improvement does not remove this confound.

The older diagnosis supports rejecting the largest single-sample fall when the true edge is weaker; it does not
rule out all methods using amplitude. Nor does a first-below-4.4-after-600 comparison become an independent
physical identity merely because it shares no code with the finder. The consistency/validation distinction in
the function's own docstring should govern the stronger surrounding claims as well.

## 2. Position and level need separate semantics; first local minimum is not settled blanking

`settled_index()` stops at the first non-descending pair. A quantized ramp can contain an equal-valued plateau
before it finishes. On a 720-sample row ending `84,55,26,26,1.6`, with picture before it, the finder returns 717
and settlement stays at 717, still at 26. The remaining three samples bypass the long-tail selection and their
mean becomes **17.8667**, although the only true floor sample is 1.6. The original contamination mechanism is
therefore not fully excluded by the split or its monotone-ramp control.

Even after a correct abrupt arrival, the selected pool is not necessarily the mean of all identified blanking
samples. The existing `minimum two-sample block mean + 1.0` filter selects by value. A known settled tail
`[1,1,5,5]` repeated five times has mean 3.0, but `source_reference()` reports 1.0. This demonstrates selection
bias; it is not a claim that this waveform describes capture 1. The fixed +1 cut also survives the "nothing
typed in" description. A first local minimum, low-tail selection and a source's mean blanking level are three
different quantities. Separating the position API from the level API is useful but does not prove either.

## 3. Per-unit calibration: indexing failure hidden by this capture

`per_unit_floor.py:53-59` uses field-relative `SWITCH_LINES=(260,261,262)` with the legacy origin 286 for field 2:

```text
field 1: base 19  + (260..262 - 23)  = storage rows 256..258
field 2: base 282 + (260..262 - 286) = storage rows 256..258
```

Both target reads come from field 1. Field 2's corresponding target rows are 519..521. The calibration rows
are correctly from field 2, so its result compares one field's candidate against the other field's reference.
The selftest constructs parity lists without invoking `unit_reading()` and cannot detect this defect.

The review probe traces the actual calls. A late transition only in field 1 makes field 2 assert; one only in
field 2 does not. Changing only field 2's target-coordinate list in an isolated call reverses both outcomes.
No production file is patched by this ablation.

Importantly, correcting those coordinates changes **zero of 508 keyed field-2 results on capture 1**. This is
not evidence the indexing is safe: it shows why a capture-only aggregate comparison misses it. Both target
triplets have maximum returned position **719 on every unit**. The diagnostic records the reference center,
absolute target maximum and paired margin rather than inferring this from equal aggregate counts.

The unmodified census reproduces the reported 680/1016 assertions and 354/81280 held-out row fires exactly.
Its breakdown is:

| population | field | assertions / readings | held-out row fires / rows | target maximum |
|---|---|---:|---:|---|
| all | 1 | 314/508 | 119/40640 | 719 throughout |
| all | 2 | 366/508 | 235/40640 | 719 throughout |
| card, 6667–6810 | 1 | 143/144 | 71/11520 | 719 throughout |
| card, 6667–6810 | 2 | 144/144 | 77/11520 | 719 throughout |
| bright, >=6900 | 1 | 82/275 | 3/22000 | 719 throughout |
| bright, >=6900 | 2 | 134/275 | 122/22000 | 719 throughout |

The coordinate-only field-2 ablation preserves every entry, not only the rounded percentages. Report the
287/288 card figure as 99.65% or its fraction, not as perfect coverage hidden by integer rounding.

## 4. What the parity split does and does not establish

The 80 calibration rows and 80 validation rows used to count exceedances are disjoint. The common reference
median is calculated from the first 200 rows, including validation rows, so preprocessing is not completely
held out. **But that shared scalar cancels from this particular comparison.** For common center m:

```text
floor = max(t_cal - m) = max(t_cal) - m
asserts iff max(t_target) - m > max(t_cal) - m
        iff max(t_target) > max(t_cal)
validation fire iff t_val > max(t_cal)
paired margin = max(t_target) - max(t_cal)
```

Consequently it would be wrong to attribute the assertion or row-fire rate to numerical leakage through m.
The probe changes only validation rows, moving m enough that floor/switch change from 0/30 to -40/-10; the
assertion and paired margin stay unchanged. Validation fires change, as they should when validation inputs do.
This cancellation holds for the available readings and current max-comparison code, not arbitrary later
qualification or a scale learned from validation rows.

The remaining limitations are different:

- The declared no-switch and switch populations come from fixed row selections. Positive targets are only
  three presumed switch rows, not independently identified timing events. The experiment never locates T/S.
- Interleaving index sets does not prove exchangeability, equal effects of picture content, or independence
  of adjacent raster samples. The selftest's claim that vertical variation therefore hits both equally is
  stronger than the property it checks. The alternating-content control produces 80/80 validation fires.
- A per-row exceedance rate is not the false-assertion rate of the maximum over three target rows. Matching
  the decision statistic and negative population matters, as does uncertainty across units rather than treating
  all spatial samples as independent trials.
- The operating-point sweep has already been used to choose a strategy. It is calibration/development evidence,
  not an untouched final validation set. Its code and keyed selections are absent from `0c72441`, which changes
  CLAUDE.md only; I do not assume that earlier sweep shares or avoids the later indexing bug.
- Unreadable row transitions are skipped. Fields returning None are omitted by `main()` rather than counted
  as Unknown. All 1016 fields were available in this run, so this does not change these figures, but the
  denominator cannot be called fixed or universally immune to qualification changes.

The calibration maximum is a legitimate empirical order statistic, not automatically circular. It is neither
an independently measured physical noise bound nor a specified error guarantee on new material. The partition
fixes the direct resubstitution problem; it does not establish the identities being compared.

## 5. Bright 39%: assertion rate, not demonstrated switch coverage or demonstrated impossibility

The supplied 216/550 is reproduced, including with corrected field-2 coordinates. Every target maximum is
719. On this bright cohort, the rule is therefore simply `max(calibration transitions) < 719`. The paired
margins are **216 at +1 and 334 at 0**. There is no fractional-sample decision margin: each transition is an
integer index and m cancels. Subtracting separately reported medians 1.2 and 1.0 is not a measurement of paired
margins. The displayed 1.2 is itself rounded from an aggregate statistic, not sub-sample timing resolution.

This is coverage of the instrument's *assertion*, if labeled that way. It is not yet coverage of correctly
identified head switches or valid T readings. The remaining 61% are non-exceedances of this statistic, not
proven physical absence of measurable evidence. Conversely these results do not prove that all bright timing
information is unusable. A useful next test has to distinguish actual identified timing departures from the
same endpoint/censoring and ordinary-variation behavior, with same-field inputs and matched negative decisions.
No new threshold, acquisition policy or owner question is proposed by this review.

## Reproduction and falsifying output

`experiments/arrival_review_controls.py` imports the actual functions, runs the mutation and synthetic probes,
and can reproduce the census with keyed availability and absolute centers:

```sh
python3 experiments/source_reference.py --selftest
python3 experiments/per_unit_floor.py --selftest
python3 experiments/arrival_review_controls.py
python3 experiments/per_unit_floor.py --capture /Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/composite_program_30s.tpc
python3 experiments/arrival_review_controls.py --census-only --capture /Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/composite_program_30s.tpc --csv /private/tmp/arrival-review.Z7a46w/census_with_centers.csv
```

The keyed census CSV from this run has SHA-256
`5c6b606a0ceafc37e65d808d9f014da0955c5d04f0a1ae3494043f7386105df2`.
The scratch CSV is not a permanent input dependency; the committed probe reproduces it from the capture.

The unmodified selftests pass. Selected falsifying probe output, verbatim:

```text
f1_late=True f2_late=False: field2 target storage rows=[256, 257, 258], asserts=True, own-field-coordinate ablation=False
f1_late=False f2_late=True: field2 target storage rows=[256, 257, 258], asserts=False, own-field-coordinate ablation=True
  card-like ABRUPT -> blanking at 700        -> 717   want ~700  FAIL
SELFTEST FAILED
mutated selftest status: 1
picture-only noise non-Unknown transitions: 61 /1000
blanking-only noise non-Unknown transitions: 61 /1000
transition= 600 learned_level= 17.7
transition= 717 settled= 717 level_at_settled= 26.0 true_floor_index=719 pooled_level= 17.866666666666667
known settled-tail mean= 3.0 selected pooled_level= 1.0
field2 coordinate-only ablation: differing keyed readings 0 of 508
```

The mutant failure is expected and demonstrates the control working; the other outputs falsify broader
implementation/qualification claims. They are not failed capture runs. No rendered output or engine correction
is evaluated here. `git diff --check` passes; the contract and engine remain unchanged, and AGENTS.md remains
a symlink to CLAUDE.md. All original untracked test binaries are preserved.
