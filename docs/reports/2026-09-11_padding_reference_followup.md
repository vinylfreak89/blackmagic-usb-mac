# Padding-reference follow-up and refusal-guard review

Merged through `df74254` as `746d5dcaf7ed2ae82bdcd200eb81c27aadcec031`.
No capture content opened or remeasured. All new reproductions below are synthetic;
the latest real-row measurements and any sole-cause attribution are not validated
by this review. No detector or contract repair is made.

## The previous findings stand within their stated scope

Finding 1 at `docs/reports/2026-09-11_blanking_extent_review.md:18` explicitly names
device hard padding, "not even the device's regenerated blanking intervals". The
committed probe changes only the synthetic padding from 16 to 2; its target dark
picture is 18. The matching CLAUDE.md note and final response also say padding.
Thus "neither review had it" is factually wrong: the new row measurement corroborates
the recorded distinction rather than correcting it. For precision, `Y[0:6]` selects
rows 0 through 5, inside the padding run 0 through 6. Padding, regenerated device
blanking and source blanking remain different objects; "decoded blanking" should not
silently replace the contract's device-written/regenerated provenance.

Finding 5 at that report's line 85 explicitly says **synthetic row**. Its test at
`experiments/blanking_extent_review_controls.py:102` uses level 1.4, dark content 4.2
and tolerance 2.5 versus 3.0, hence bounds 3.9 and 4.4. No production real-row
sensitivity was claimed. The conclusion is that the chosen level cut determines
both timing features and can change the verdict; a FITTED label does not qualify
it. It does not estimate how many real rows flip near either 4.4 or 19.

The follow-up reproduces the same sensitivity at padding-reference parameters:
level 16, synthetic dark content 19, tolerance 2.5 versus 3.0. Bounds 18.5 versus
19 change normal to extended. This is another helper-level synthetic counterexample,
not a new production capture result. The earlier actual-main synthetic reproduction
remains separately valid with the explicit acknowledgement supplied to the new CLI.

The independent duration, interval-identity, censoring, branch-order, calibration,
dependency and denominator findings are not invalidated. Correctly supplying a
reference does not make summed duration detect a translation or make a low-level
run an identified blanking interval. The report never certified the real-row counts
as switch detection or attributed their full distribution to one demonstrated cause.

## What the new account overstates

Withdrawing the counts **as validated source/switch measurements** is warranted.
The recorded outputs still describe the defective configured program and remain
useful for forensic reproduction, not as truth labels or a target error rate.

The bad reference does not exonerate the statistic or establish the unique cause of
both distributions. Nor does the cutoff mathematically guarantee a low false-positive
rate. On thirteen known synthetic no-switch rows, adding dark content while keeping
their true blanking unchanged yields thirteen false assertions at level 16 plus 3.
The error rate depends on the calibration and test masks, not on the padding cutoff
alone. Establishing a causal contribution in real rows would require a keyed,
controlled reference substitution and reporting changed masks, extents, positions,
tolerances, verdicts and unavailable cases on the same population. That was not done
here, and cannot be replaced by comparisons of unmatched aggregate summaries.

"Source blanking never exceeds 3" is also not an established source-wide upper bound
from the supplied observations. The immediately preceding review demonstrates that
selection can truncate genuine blanking values. Report the observed samples, their
selection and scope; do not put a universal ceiling into the refusal message.

## Refuse by default: retain it, but label the acknowledged output

`experiments/blanking_extent.py:255-263` does refuse before any capture read, with
exit 2 and empty stdout. Verified by replacing the walker with an assertion that
must not run. Keep the instrument and its historical outputs/known-answer controls;
deletion loses reproducibility and is unnecessary. It is a known-broken baseline,
not a reference answer the repair must match. Selftests must remain accessible.

However `--acknowledge-void` bypasses the only runtime warning. In an in-memory
synthetic main run, stderr is empty and stdout still begins "BLANKING EXTENT, both
directions, local window, D16's two conditions", followed by "identified" and
"FALSE identification" labels (`:315-322`). Thus the warning does not travel with
the very results that can still be copied. Keep a persistent invalidity banner in
acknowledged output, name the padding-derived cutoff and build/configuration, and
call counts configured assertions rather than qualified identities. An opt-in flag
authorizes diagnostic execution, not promotion of the output's meaning. This review
identifies the gap; it does not edit the owner's guard.

The older `blanking_extent_review_controls.py` runner is scoped to `d21f373` and
expects its six-control selftest to pass. The intentionally added failures and new
CLI guard change its execution prerequisites, not its prior synthetic results.
The new follow-up probe reuses its fixture but explicitly acknowledges the guard.
The merged `calibration_qualification.py` changes are not a full reviewed repair or
an endorsement of that diagnostic's remaining causal/qualification claims.

## Reproduction

Run `python3 experiments/blanking_extent_guard_review.py`. Selected output verbatim:

```text
SYNTHETIC level 1.4 tol 2.5 bound 3.9 classification ('normal', 0.0, None)
SYNTHETIC level 1.4 tol 3.0 bound 4.4 classification ('extended', 50.0, -300.0)
SYNTHETIC level 16.0 tol 2.5 bound 18.5 classification ('normal', 0.0, None)
SYNTHETIC level 16.0 tol 3.0 bound 19.0 classification ('extended', 50.0, -300.0)
padding-reference false assertions on known synthetic negatives: 13 of 13
DEFAULT EXIT 2 stdout ''
```

The acknowledgement-path guard defect is printed as:

```text
ACKNOWLEDGED STDERR ''
INVALIDITY WARNING PRESENT False
```
