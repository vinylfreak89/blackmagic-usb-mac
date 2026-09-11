# Expected-failure follow-up and arrival probe repair

Reviewed `5edab6b8f81642eb5e3db999c885de9e3050cb3c` and timeout change
`144e611c0efa3f22b9cc0a7f75cdbc9d875bd94c`, including their commit messages.
The harness was merged before review. References below use the reviewed snapshot;
the runner's subsequent removal of the arrival annotation shifts its line numbers.
No captures opened, no full capture-capable suite run. The incoming
`69e2f96` withdrawal scanner is not given a separate validation verdict here.

## Confirmed repairs

The supplied mutation verifier reproduces **16/16 mutations and 9/9 enforcement
brackets**. Guard 13 now has the enabled rejection as well as disabled acceptance;
permanently emptying its failure list is detected. The five previous guard-review
checks pass. So do the repair audit (zero unmet checks), censoring audit (15/15),
schema review (9/9), and texture selftest (5/5).

The bare fixture listing no longer raises, overall absence with an unresolved end
is rejected, deleting `censored` is caught at control 0, and the originally probed
unexpected `KeyError` is not excused. Those concrete repairs are confirmed. The
broader crash/expected-failure distinction and schema-validation claims remain
incomplete, as detailed below.

Keep control 2's +/-2 tolerance. The previous review requested an accurate
description of that composition, not removal of synthesis noise. It verifies
sample/declaration agreement within that tolerance and truth/declaration
agreement separately; it does not prove exact sample agreement.

The extended timeout now fails the runner, reproduced by injecting
`TimeoutExpired`, not by waiting thirty minutes. The default timeout is reported
as pending and not counted as ran. A timeout establishes failure to finish within
the budget; it does not establish whether the process was hung or merely slow.
The returned status and explicit timeout limit are the useful facts.

## Remaining findings

1. **An exception type is still not an expected-failure identity.**
   `experiments/run_all_checks.py:170-179`. **Reproduced with mocked child runs.**

   Under an annotation for a particular calibration assertion, all of these
   unrelated failures still produce runner exit 0:

   - `AssertionError: unrelated baseline setup is broken` (child exit 1);
   - Python's missing-script diagnostic (child exit 2, no traceback);
   - a real `KeyError` traceback followed by the exception note `AssertionError`.

   The last unindented line of a traceback need not be its exception class.
   More importantly, even correctly identifying `AssertionError` says nothing
   about which assertion failed. Asserts enforce setup and schema invariants too;
   `SystemExit` is equally available to failures outside the annotated condition.
   Absence of a traceback is not proof of an expected assertion.

   The new probe includes the named assertion as a positive counterpart so a
   blanket rejection of every assertion is not a repair. The runner needs an
   explicit recognizable expected outcome/cause, not a broad exception allowlist.
   An unsupported historical probe may instead be separately quarantined as
   unavailable validation, never represented as an exercised expected assertion.
   The headline still counts annotation entries, not observed expected failures.

2. **Control 0 checks field presence but still does not validate consumed shape.**
   `experiments/switch_fixtures.py:307`, `:332`. **Reproduced.**

   Set a case's `spans` to `[None]`: control 0 passes, then unpacking raises
   `TypeError: cannot unpack non-iterable NoneType object`.
   Set its truth start to `[]`: a later set operation raises
   `TypeError: cannot use 'list' as a set element (unhashable type: 'list')`.
   The missing-`censored` repair closes that example, not the previously requested
   element/type validation. Validate the nested types, array shapes and allowed
   truth values before downstream arithmetic, hashing or unpacking.

3. **The texture claim is still false even when restricted to draws from this
   noise model.** `experiments/matched_control_texture.py:70`, `:332-344`.
   **Printed contradiction reproduced; six-sigma conclusion reasoned from code.**

   The output says `>=4 sigma deterministic FOR DRAWS FROM THIS NOISE MODEL`,
   while the same default run's four-sigma row contains a 99% agreement entry
   and a 0.8-point spread. That is an actual sampled counterexample to the
   statement's four-sigma part.

   Six sigma makes an excursion rare, not impossible. `ar1()` draws unbounded
   Gaussian innovations; its stationary one-sample upper tail at six sigma is
   `0.5 * erfc(6 / sqrt(2)) = 9.865876450377014e-10`. That is a per-sample
   probability, not a guarantee about a run or a sweep. Restricting the claim to
   draws does not turn a nonzero probability into zero. Open neighborhoods of
   finite counterexample sequences remain possible under this generator.

   The existing same-cut 37-to-38 counterexample still runs, but non-Gaussian
   sources are not needed to reject determinism. State the finite result instead:
   **no six-sigma differences were observed in these specified trials**. A
   probabilistic bound must name its event, population and dependence assumptions.
   Remove the remaining deterministic-draw assertions in place, including the
   commit message's interpretation in the durable correction record. Control 4's
   authored-rho label is now corrected.

   The docstring's texture-insensitive-or-blocked fork also remains incorrect
   (`:16-19`): explicitly authored conditional fixtures need no empirical texture
   justification, whether sensitive or not. Empirical representativeness is a
   different claim. The printed 24% / 31.5-point narrative is stale against this
   run's 25% / 39.2-point two-sigma row; derive the narrative from the run or scope
   it to its original settings.

## Owned arrival probe: repaired, not retired or re-annotated

The reported crash reproduced before edits:

```text
  File "/private/tmp/blackmagic-v10/experiments/per_unit_floor.py", line 59, in unit_reading
    for ln in SWITCH_LINES[field]:
              ~~~~~~~~~~~~^^^^^^^
TypeError: 'int' object is not iterable
```

The old probe's tuple patch was mine and incompatible with the field-keyed
interface. Its runner annotation wrongly treated a crash as a designed failure.
The fix patches a dictionary, checks both fields through actual `unit_reading`
calls, and requires the original wrong-field mutant to fail those same checks.
The reference selftest must pass before the rejected arrival variant is forced.
Settlement, +/-2 position agreement and common-center cancellation now have
explicit positive obligations. `--selftest` is synthetic-only and rejects
capture/census arguments; the optional capture path was not run.

The result is:

```text
PASS wrong-field mutation rejected by the same ownership checks
PASS unmutated source selftest before forcing the rejected variant
ARRIVAL REVIEW PASS: ownership, mutation, position tolerance, settlement and center cancellation
Diagnostics above are not acceptance of source identity, fabrication or selected-pool bias.
```

The failed inner variant selftest is required evidence, not failure of the outer
probe. The printed diagnostics still reproduce 61/1000 synthetic fabricated
transitions in each noise family and a selected level of 1.0 for a known tail
whose mean is 3.0. Their retention is not a claim those limitations are repaired.
The stale arrival expected-fail annotation is removed.

## New deciding checks

`experiments/runner_disposition_review.py --selftest` executes only synthetic
fixtures and mocked child processes; timeouts are instantaneous injections.

```text
PASS the named expected assertion remains distinguishable: runner exit 0
FAIL an unrelated assertion is not the annotated failure: runner exit 0
FAIL a launch error is not an expected assertion: child exit 2, runner exit 0
FAIL exception notes cannot relabel a KeyError: runner exit 0
FAIL schema validates span elements before unpacking: TypeError: cannot unpack non-iterable NoneType object
PASS extended timeout fails with its limit reported: runner exit 1
PASS ordinary timeout is reported as incomplete, not ran: runner exit 0; pending validation, not a completed pass
DISPOSITION REVIEW: 3/7 checks passed
```

Exit 1. These checks are discoverable and not annotated away. The arrival repair
therefore does not imply a green suite: four reproduced obligations still fail.
No engine, contract, fixture implementation, enforcement implementation or
texture implementation changed. The only runner edit removes the stale owned
probe annotation. Existing unrelated untracked binaries are preserved.
