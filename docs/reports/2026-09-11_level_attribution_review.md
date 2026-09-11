# Level-attribution review

Reviewed `386d202`, merged as `3d3aa03e16690267f845570f3693dab6112d21ff`.
References below are to that merged snapshot. No capture content was opened or
remeasured, and the reported real-data counts were not reproduced here. The new
controls execute the instrument on synthetic units, with the capture walker mocked
before loading its import-time code. The real source-reference and classifier are
used except in explicitly named unavailable-state/equal-level injection controls.

The no-leak argument is unsound, and "both accuracy rates improved" overstates this
experiment. Changing the level and consequently recomputing masks and tolerances
is a legitimate reference-input ablation. That fact does not make the validation
rows held out, supply target truth, or enforce matching evaluation populations.

## Findings

1. **Five validation rows contribute to the fitted source level.**
   `experiments/level_attribution.py:20`, `:32`, `:38-41`.
   **Code trace and synthetic reproduction using the real reference builder.**
   Reference offsets are 20 through 219; validation offsets include
   211,213,215,217,219. Thus five of thirteen nominally held-out rows are reference
   inputs. The reference also overlaps five calibration rows; training overlap is
   not itself wrong, but validation overlap defeats the stated holdout separation.
   Changing only those five validation rows in a synthetic field, leaving every
   calibration and candidate row byte-identical, moves that field's source level
   1.5 to 2.05 and changes three unchanged candidates from normal to extended.
   The device-arm candidate verdicts stay unchanged. This is active fitting-input
   reuse, not just a possible address collision. It is not proof that the reported
   rate change was caused by leakage, and no label leakage is alleged. Current-unit
   adaptation may be legitimate production behavior; its fitting rows cannot also
   be advertised as independently held-out validation. Use separate reference and
   validation keys or cross-fit the entire learned path when measuring that claim.

2. **Matching row lists do not enforce matching evaluated populations.**
   `experiments/level_attribution.py:35-46`, `:67-69`.
   **Reproduced by explicit unavailable-expectation injection into one arm.**
   Each arm independently continues when its expectation is None. The synthetic
   control reports two seen fields, but validation denominators device=26 and
   source=0; candidate tallies likewise disappear from the unavailable arm. With
   an empty mocked walk the formatter prints 0/0 as 0.00%. This mechanism is not
   asserted to have occurred in the supplied 400-field run: the reported candidate
   totals sum to 1,200 in each arm, consistent with all 400 fields being evaluated.
   Nonetheless the comparison does not enforce the property on which its claim
   relies. Record per-(counter,field,row,arm) results and unavailable reasons, and
   assert matching attempted keys rather than trusting aggregate counts. A paired
   available subset, if reported, must be named alongside full-cohort availability.

3. **Recomputed tolerances are a legitimate mediator, not themselves leakage.**
   `experiments/level_attribution.py:35-39`.
   **Reasoning from dependencies, plus an equal-level control.**
   The level determines masks, which determine the fitted expectation and tolerances
   and then the verdict. Recomputing them measures the total effect of changing
   the level input to this pipeline; holding them fixed would answer a different
   ablation question. The same raw rows can remain selected while their derived
   features legitimately move. With equal levels injected into the two arms, the
   synthetic wrapper produces identical candidate tallies and validation counts.
   That supports the intended branch symmetry, not the absence of evaluation
   reuse in finding 1. Nor does calling the other value source-derived qualify
   the `source_reference` sample selection or the still-fitted +3.0 cutoff.

4. **Joint movement of these metrics is not demonstrated joint accuracy improvement.**
   `experiments/level_attribution.py:9-10`, `:42-46`, `:62-69`;
   `CLAUDE.md:5467-5482`.
   **Reasoned from the metric definitions; no capture figures reproduced.**
   Higher positive-label frequency on fixed expected-band rows is not improved
   sensitivity without independently established positives. The classifier's
   duration and identity defects remain, as the author correctly acknowledges.
   The negative-side fraction is also not an independently held-out error estimate
   with the current reference overlap. Validation Unknowns are included in its
   denominator but not separately reported, so a lower assertion fraction does
   not by itself mean more correctly identified normal rows.
   The methodological objection to a rule forbidding joint error improvement
   remains correct, but this experiment is not an empirical proof that both true
   error rates improved. The 88.8% has a limited, interpretable meaning: configured
   assertion frequency on the selected candidate-row population. Its paired
   contrast can show program sensitivity to the reference input, not switch
   coverage, correctness or a whole-capture dominant-cause conclusion. Preserve
   the counts with configuration, denominator, selection and availability limits.

5. **The cohort is selected by source-reference availability, and the cap can overrun.**
   `experiments/level_attribution.py:28-34`.
   **Code trace and synthetic reproduction.**
   A missing source reference omits both arms before `seen` increments, even though
   the padding arm might otherwise run. An injected missing reference yields seen=0
   and two empty arm tallies. This is a common selection, not demonstrated unequal
   arm selection, but "400 field-readings from 6667" means a selected prefix of
   source-reference-available fields, not all fields or a whole-capture census.
   Attempted keys and rejected-reference counts are absent. Separately, the limit
   is checked once before processing both fields: starting seen at 399 with two
   available fields ends at 401. That is a wrapper defect the classifier's tests
   cannot catch; no claim is made that it happened in the supplied run.

6. **The comparison does not carry its invalidity qualification into runtime output.**
   `experiments/level_attribution.py:9-10`, `:59-70`.
   **Reproduced with a mocked empty walk; no file was read.**
   The docstring correctly says these are not switch counts, but stdout names
   switch-band verdicts and false-identification without any diagnostic/invalidity
   banner. Importing helpers bypasses `blanking_extent.main()`'s acknowledgement
   warning. That warning was verified as newly present in the detector's own
   acknowledged execution; it does not protect this separate output path. The
   non-switch-count qualification needs to travel with this table too. The code
   also invokes the real capture walker at import time; tests must mock it before
   load until a callable entry point and explicit main guard exist.

## Controls the comparison itself needs

The argument that unchanged classifier inputs already have six controls fails:
reference construction, cohort selection, arm pairing and formatting belong to
this wrapper, not to `classify`. At minimum:

- Equal-level arms must produce identical per-key results, including unavailable
  cases; use asymmetric fields so an ownership/indexing mix-up cannot pass.
- Holdout isolation: mutating only validation rows must not alter the fitted
  reference/expectation for an independently held-out evaluation. The current
  implementation fails that property, demonstrated without changing any target.
- Inject a missing source reference and an expectation available in only one arm;
  assert attempted denominators and explicit abstentions, not disappearing keys.
- Enforce the field cap when one field was unavailable earlier, and test fragmented
  transport input so input chunking cannot change paired keys or verdicts.
- Empty input and acknowledged diagnostic output must not present 0/0 as a measured
  rate or omit the instrument's limitations. Importing the module must not read a
  capture as a side effect.

These are tests of the comparison's claims, not a proposal to repair the underlying
switch detector. The synthetic probe records passing controls for branch equality
and reproductions of the failed properties; its exit 0 is not a detector sign-off.

## Reproduction

`python3 experiments/level_attribution_review_controls.py` produces:

```text
REFERENCE / VALIDATION OVERLAP [211, 213, 215, 217, 219]
VALIDATION-ONLY MUTATION: source levels [1.5, 1.5] -> [2.05, 1.5]
UNCHANGED CANDIDATES: source verdicts {'normal': 6} -> {'extended': 3, 'normal': 3}
EQUAL-LEVEL ARMS: identical tallies and denominators PASS
INJECTED SOURCE-EXPECTATION FAILURE: seen 2 validation denominators {'device': 26, 'source': 0}
INJECTED SOURCE-REFERENCE FAILURE: seen 0 both arms omitted {'device': {}, 'source': {}}
CAP CONTROL: initial 399, final 401
MOCKED EMPTY WALK: reports 0 of 0 as 0.00% True
MOCKED EMPTY WALK: invalidity banner present False
REVIEW CONTROLS PASS: dependencies/omission paths reproduced, no capture evaluated
```

No engine, detector, attribution implementation or contract change is made by this
review. Shared-note interpretations are corrected in place; original measurements
remain attributed, not newly certified.
