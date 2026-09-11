# Guard-enforcement follow-up

Reviewed `2b31f01303eca701519a23985e4c99dfaa3711f5`,
`5c22e768139db0d27e709a71c8c7bdf56cf8392e`, and
`289d279ab9729d2d7454ce1c65618f8f8511ce07`, after merging the harness head
at the last commit. Citations below use that snapshot's lines, including the
runner before removal of the now-stale audit annotations. Commit messages were
read as well as code. No capture content opened, no full capture-capable suite
launched, and no engine, contract, supplied-fixture, verifier or texture repair.

## Repairs confirmed and owned probe updates

The restored overall result and separation of hidden geometric visibility from
establishable evidence are the intended directions. The existing matched pair's
expected availability now agrees while its hidden visibility may differ.
Value-identical calibration copies no longer bypass answer consistency.
The supplied verifier reproduces **16/16 mutations and 9/9 disabled-guard runs**.
Guards 1 and 4 now satisfy the older checks that previously failed. The texture
selftest reproduces **5/5**, including the finite margin sweep. The audit's
missing-guard failure and runner's negative-returncode failure also reproduce.

I updated ALL THREE owned probes, not just the two mentioned in the dispatch.
`establishable` replaces expected observable availability; `hidden_visible`
and `overall` are supplied when constructing synthetic cases. This is a semantic
mapping of the old mixed field, not an indiscriminate name substitution.

The older repair audit additionally raised `OSError: could not get source code`:
the new verifier introspects a selftest that the review probe had compiled without
retaining introspectable source. The shared `fixture_review_support.py` now
registers the ACTUAL mutant source in `linecache`, preserves the `selftest` name
and real module globals, and restores function/cache state afterward. It does
not fake the verifier's result or treat an introspection error as rejection.

After adaptation:

```text
AUDIT PASS (0 unmet checks)
CENSORING AUDIT: 15/15 checks passed
SCHEMA REVIEW: 9/9 checks passed
```

All exit 0. Their three expected-fail entries are removed. Historical versions
and reports remain in git. These passing probes establish their specified checks,
not completion of every broader claim. Five new positive checks below fail.

## Remaining findings

1. **The fixture's own listing command still reads the removed key.**
   `experiments/switch_fixtures.py:541`. **Reproduced.**

   Bare `python3 experiments/switch_fixtures.py` prints the table heading then
   raises `KeyError: 'observable'`. The claim that nothing reads this key is false.
   Update the command's columns deliberately: overall and endpoint decisions,
   establishable evidence, and hidden visibility are different facts. Add a
   synthetic smoke check of this entry point, not just `--selftest`.

2. **Guard 13's enforcement test lacks the enabled-guard rejection arm.**
   `experiments/switch_fixtures_review_controls.py:204`, `:227`.
   **Reproduced.**

   Its isolated mutation appears ONLY in `enforced`, which disables the guard
   and requires success. Unlike the other eight named mutations, it is never
   first required to fail with guard 13 enabled. Clear `contra` immediately
   before `ok &= not contra`, leaving that exact statement available to the
   mutator: the verifier still reports 9/9 although detection is permanently
   empty. The existing adapted schema probe DOES reject this regression; the
   verifier's standalone nine-guard claim is what fails.

   For each isolated case require enabled `(failure, intended cause)` followed
   by disabled success. The old adapted probes now genuinely close guards 1/4.
   Keeping the non-isolated matched-pair test as a separate compound test is fine.
   Scope coverage to the nine listed guards, not all fourteen numbered guards.
   Redundant rejection does not itself make a guard decorative; the test's
   isolation determines whether necessity can be attributed to it.

3. **Python exceptions still disappear behind expected-fail annotations.**
   `experiments/run_all_checks.py:169`. **Reproduced with mocked subprocesses.**

   Negative signal codes are now errors, which closes the precise -11 probe.
   But an unexpected Python `KeyError` produces positive exit 1. Inject a child
   with that code and a traceback under an annotation for a known semantic
   assertion failure: the runner exits 0. This is also the class of failure the
   unadapted owned probes actually produced, so signal-only handling does not
   implement the stated assertion-versus-crash distinction.

   Match a defined expected failure result/cause; exceptions, execution errors
   and unrecognized failures are not that result. If a temporarily unsupported
   probe is deliberately quarantined, report that as non-executed validation,
   not successful exercise of its expected assertions. A distinct structured
   result or explicit failure protocol is more reliable than generic exit 1.
   The headline still prints the size of the annotation dictionary rather than
   the number of expected failures actually observed.

4. **Overall absence can still be required with an unresolved hidden end.**
   `experiments/switch_fixtures.py:149`, `:519`. **Reproduced.**

   Default construction now yields the intended overall Unknown for A5/B2.
   Set BOTH cases' overall result to `none`, leaving their end `undecidable`:
   every control passes. Making both wrong avoids the equality check; guard 13
   only checks overall `none` over an explicit endpoint `departure`.

   Validate the declared overall-result relation, not just its enum and equality
   between examples. Under these fixtures' endpoint-only evidence, unavailable
   end evidence cannot establish whole-interval absence. If a future case has
   an independent whole-interval witness, represent that witness explicitly
   rather than letting an arbitrary override assert certainty.

5. **Control 0 still omits a field its consumers require.**
   `experiments/switch_fixtures.py:301`, `:477`. **Reproduced.**

   Deleting `censored` passes schema validation and reaches `KeyError: 'censored'`
   in control 9. Missing `row` is fixed; validating every accessed field is not.
   Check the complete shape, including allowed censoring values, span element
   shapes/types, array shapes and truth-value types before later indexing or
   arithmetic. The current key/container checks alone do not establish this.

6. **The margin result is finite; the remaining wording still claims impossibility
   at the exact cut already falsified by the review.**
   `experiments/matched_control_texture.py:211`, `:322`.
   **Sweep, printed wording and counterexample reproduced.**

   The synthetic 2-sigma spread and sampled 6-sigma agreement are real outputs.
   But “texture cannot reach the verdict” at six sigma is still too strong:
   the existing same-histogram counterexample uses the unchanged `CUT`, mean
   and sd and still changes extent 37 to 38. It did not require a tighter cut.
   Finite zero observed changes is not determinism for Gaussian noise with
   unbounded support. Say no changes were observed in the specified trials;
   any stronger probability claim needs its own bound and scope.

   The authored-parameter correction is correct at the constants, but control 4
   still prints `i.i.d. asserts rho~0, not the measured -0.29`. The docstring also
   retains the false choice that a conditional control is blocked unless it is
   texture-insensitive. Authored noise models were already permissible without
   claims of empirical representativeness. Amend these remaining assertions,
   not just the constants and final attribution of the maximum.

## The two structural changes

Separating sample-versus-declaration from truth-versus-declaration is sensible,
but it changes the effective precision: the remaining sample check permits +/-2.
An A3 row shifted two samples away from its unchanged declared span/truth now
passes, reproduced. Thus composition checks consistency within that tolerance,
not the exact equality previously imposed by control 3. Keep the intended
tolerance explicit rather than claiming the invariant is unchanged.

The exact-input and distribution checks are legitimately distinct. Under the
current shared authored generator, comparing merged geometry and value-equal
references is a useful distribution-level consistency check. Its justification
is that declared generator, not geometry alone. If noise laws, cross-sample
dependence or reference-generation relationships vary, include those model facts
in the distribution claim. Exact input equality must still use all allowed
inputs and their representation; shape/type validation is part of that boundary.

## New deciding checks (verbatim, exit 1)

`experiments/switch_fixture_guard_review.py --selftest` runs all five checks:

```text
FAIL fixture listing uses the current schema: KeyError: 'observable'
FAIL schema guard rejects missing censored field: KeyError: 'censored'
FAIL unresolved hidden end cannot imply overall absence: exit 0, guards []
FAIL verifier detects guard 13 with a permanently empty failure list: verifier still passes
FAIL expected failure does not conceal an unexpected Python exception: child exit 1 with KeyError traceback, runner exit 0
GUARD REVIEW: 0/5 checks passed
```

The original schema probe crashed before executing any of its nine checks;
that was not a 0/9 result. Its traceback ended in `KeyError: 'observable'`.
The older repair audit's traceback ended in `OSError: could not get source code`.
Both are repaired in the owned probes here, not counted as expected assertions.
