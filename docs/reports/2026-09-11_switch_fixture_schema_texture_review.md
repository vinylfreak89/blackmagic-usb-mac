# Endpoint-schema and texture-sweep review

Reviewed `fa281a7ea10b6684252809bf1d33f309092da899` and
`848f87e466a1ea811dea9ed54bdb65f99ea2ced8`, including their commit messages,
after fast-forwarding the engine branch to the former. References below name
files and lines at that snapshot. No capture content opened or measured, and
no engine, contract, supplied fixture or texture-instrument repair is made here.
The withdrawn dither measurements are not premises for this review.

The incoming censoring audit reproduces **15/15**, and the texture selftest
reproduces **4/4**. These close the specific rejection checks they exercise,
not every semantic obligation of the new schema. The old audit also exposes
two surviving enforcement failures before reaching its obsolete text lookup.

## Findings and decisions

1. **Endpoint results are useful additional facts, not a replacement for presence.**
   `experiments/switch_fixtures.py:16`, `:139`, `:159`, `:355`.
   **Schema judgment reasoned; false endpoint answer accepted, reproduced.**

   My recommendation was an overall tri-state presence result PLUS separate
   endpoint/extent availability and uncertainty. A5 and B2 can both have overall
   `undecidable`, with visible-start agreement and unavailable end/extent.
   The scalar never had to carry those other facts alone. No overall `none` in
   this particular all-right-censored cohort is legitimate: control 6's diversity
   requirement must not dictate the result semantics. Add a qualified, fully
   observable normal case if positive overall absence needs exercising.

   Keep the new endpoint results, but also state the overall presence obligation
   or an explicitly scoped aggregation of the qualified observations. A1 has
   positive departure despite an unavailable end; A5/B2 do not establish either
   whole-interval departure or whole-interval normality. Matching these facts is
   not accomplished by changing the result type alone.

   The current validator also accepts A4 with its end result changed to `none`:
   the injected end is eleven samples inside a reference that always reaches
   delivery's edge. All controls pass. Control 5 examines whether ANY true shift
   is large, not whether each required endpoint answer is justified. This is
   distinct from the now-fixed rejection of a large start shift with an uncertain
   end. Per-endpoint uncertainty still needs its own expectations.

2. **The matched pair has contradictory expected availability unless that field
   is explicitly hidden truth.** `experiments/switch_fixtures.py:97`, `:138`, `:222`.
   **Reproduced; interpretation follows the current docstring.**

   C3a/C3b have identical full row and calibration inputs and identical required
   dispositions, but `observable.start` is True for A and False for B. The helper
   knows which generative interval is blanking; the detector does not. An edge
   existing at the true boundary in one hidden world is not the same as being
   able to identify that boundary from the common observation.

   If these flags are expected detector outputs, both worlds must have compatible
   identifiable-availability expectations. If they describe latent geometric
   visibility, retain them with that name under truth and add the expected
   observation separately. Control 12 currently checks neither this distinction
   nor calibration equality when validating the matched pair.

3. **Object identity is not calibration equality, and geometry alone is not a
   complete distribution specification.** `experiments/switch_fixtures.py:340`.
   **Consistency bypass reproduced; distribution scope reasoned.**

   Give B2 A5's exact row bytes and a value-identical COPY of its calibration;
   change B2's required end answer to `none`, leaving A5 `undecidable`. Every
   control passes. `id(cal)` separates identical allowed evidence into different
   groups, so even the strongest concrete equal-input case escapes the check.

   A stronger, readily available test compares the complete declared detector
   input by value: arrays, dimensions, reference observations and any explicitly
   supplied qualification metadata. Hidden names, truth and expected answers are
   excluded. Hashing such a serialized interface is an implementation option.
   A separate distribution-equivalence check is useful only under an explicit
   complete joint noise/generation model, including dependence on calibration;
   merged intervals plus Python object identity do not encode it. Equal noise
   distributions also do not mean independent realized samples are identical.

4. **Naming non-isolation is honest but does not prove the named guard enforces
   rejection. The older audit must stay live.**
   `experiments/switch_fixtures_review_controls.py:64`, `:81`, `:114`.
   **Reproduced.**

   Removing guard 1's rejection effect still leaves its message plus guard 4's
   rejection. Removing guard 4's effect leaves guard 12 enforcing rejection.
   The positive suite still passes in both cases. Cause AND a nonzero exit
   establish that a cause was reported and SOME guard enforced rejection, not
   necessarily the intended one. The four newly detected disabled guards are
   genuine improvements; they do not close these two older obligations.

   Not every compound mutation needs isolation. To claim enforcement of each
   guard, use an isolated probe or test that guard's structured result directly,
   and verify disabling it breaks its own positive test. Isolated cases already
   work here: make invalid A2's remaining truth, absence, and endpoint answers
   consistent (only guard 1 fires), and alter B2's end answer against A5 rather
   than using the separately guarded C3 pair (only guard 4 fires).

   I adapted `switch_fixture_repair_audit.py`, rather than retiring it: its U1
   input now uses the live schema and checks acceptance without matching an old
   printed sentence. It exits 1 with **two actual unmet enforcement checks**,
   no exception. The original artifact remains in git and its frozen report.
   Accepting the input shape in this adapter does not approve the schema's
   completeness. The runner annotation is updated to name these live defects.

5. **The texture sweep is reproducible; general insensitivity “by construction”
   is false, and the empirical parameter labels are withdrawn premises.**
   `experiments/matched_control_texture.py:25`, `:44`, `:81`, `:139`, `:224`;
   `experiments/switch_fixtures.py:36`.
   **Sweep and counterexample reproduced; scope reasoned.**

   A threshold mask does not accept a lag coefficient as a separate argument,
   but it DOES accept ordered amplitudes. Temporal dependence can change which
   samples cross its cut, their adjacency, and the resulting run. Fixed marginal
   distribution does not fix a mask or its joint distribution. The Gaussian
   generator also has unbounded support; a cut six standard deviations above
   its mean does not make crossings impossible.

   A deciding synthetic example uses exactly the stated low-run mean 1.42 and
   population sd 0.50 over 38 samples. Reorder the SAME histogram, moving one
   above-cut sample from the start to the interior: `level_verdict` changes its
   mask and its reported extent from **37 to 38**. This does not claim those
   particular sample values occurred in the source, nor that the sampled sweeps
   failed. It falsifies the claimed general implication, even with the cut and
   first two moments unchanged. Identical masks guarantee equal results for this
   function; identical marginals do not guarantee identical masks.

   The null sweep remains a finite synthetic result at a generous authored
   operating point. Its texture-sensitive control confirms changes in that
   chosen summary, not power to detect rare mask changes. Conditional matched
   controls were already buildable without empirical texture qualification.
   Authored i.i.d. noise is no more prohibited than authored AR noise; neither
   should be called texture-neutral or an established source model.

   The -0.29/+0.27 constants are still called measured source signatures despite
   the withdrawal acknowledged at the top of this same file. Keep them as
   authored scenarios, not validated empirical anchors. Also, the reported
   maximum gap **+0.53 occurs at authored rho +0.90**; the +0.27 scenario gives
   about +0.27. The maximum is not a result at the two alleged measured textures,
   and a median feature difference is not a validated per-run classifier.

6. **The texture mutation audit exits successfully when no intended guard fires.**
   `experiments/matched_control_texture.py:185`, `:204`.
   **Reproduced.**

   Replace `run_controls` with an all-passing result so neither deliberate break
   fires. `--audit` prints `THE INTENDED GUARD DID NOT FIRE` and exits 0.
   It also computes but never verifies the baseline. Validate a clean baseline,
   require each intended mutated failure, and return nonzero for either missing
   obligation. This is a separate CLI from the successful `--selftest` path.

7. **Control 0 does not yet validate the schema consumed by later controls.**
   `experiments/switch_fixtures.py:271`, `:299`.
   **Reproduced.**

   Delete a case's `row`: control 0 passes and later validation raises
   `KeyError: 'row'`. It checks the shapes of three dictionaries but not the other
   required fields, their array/span types, or truth value types. Validate the
   complete input shape before semantic guards. A malformed fixture should have
   a structured schema failure; an internal checker exception must remain an
   error, not be converted to an expected semantic rejection.

8. **Explicit discovery is an improvement; expected failure currently hides
   crashes as well as known assertions.** `experiments/run_all_checks.py:50`,
   `:146`, `:157`.
   **Crash classification reproduced with a mocked subprocess; discovery checked.**

   For the annotated older audit, a synthetic child return of **-11** leaves the
   runner at exit **0**. Any nonzero result is accepted under the annotation,
   irrespective of failure cause. That is the distinction the new schema guard
   was meant to preserve. Expected failures need a defined assertion-result
   protocol; unexpected exceptions/signals remain errors. The headline counts
   `len(EXPECTED_FAIL)`, not the number of such results actually observed.

   I added a real `--selftest` entry point to both existing review audits; bare
   invocation remains supported. The new schema review uses it too. Discovery
   now finds all three automatically without renaming. Naming the seven
   unclassified audits is useful and they remain explicitly outside validated
   coverage. Do not use a global `_audit` execution rule or run possible capture
   instruments merely to classify them. The full runner was NOT executed here;
   its subprocesses were mocked for the classification probe, so no capture
   readers were launched and the reported whole-suite totals are not reverified.

## Verification

Before adapting the older audit it reproduced these failures before its crash:

```text
FAIL positive suite detects disabled guard: ok &= not bad
FAIL positive suite detects disabled guard: ok &= not clash
WITHIN-JITTER UNKNOWN CASE: fixture selftest exit 1
```

The traceback ended verbatim at:

```text
    print(next(line for line in output.splitlines() if "every nonzero shift" in line))
StopIteration
```

After adaptation it reports `WITHIN-JITTER UNKNOWN CASE: fixture selftest exit 0`
and `AUDIT FAILED (2 unmet checks)` (exit 1), with no crash. The censoring audit
reports `CENSORING AUDIT: 15/15 checks passed` (exit 0). I also corrected my own
stale output suffix: zero interior ends now says all reach delivery's edge,
rather than printing “not all censored” unconditionally. Its mixed-uncertainty
case now explicitly requests an undecidable end when using the endpoint schema.

New synthetic review output, verbatim (exit 1):

```text
FAIL matched inputs have consistent expected availability: start True / False (rename as hidden visibility if not an output obligation)
FAIL value-identical copied reference cannot evade answer consistency: exit 0, guards []
FAIL decisive delivered end departure cannot require no departure: exit 0, guards []
FAIL schema guard rejects a missing row before later controls: KeyError: 'row'
PASS an isolated guard-1 mutation is available: exit 1, guards [1]
PASS an isolated guard-4 mutation is available: exit 1, guards [4]
PASS fixed marginal does not force texture-independent level verdict: same histogram, mean 1.42, sd 0.50; extents 37 / 38
FAIL texture mutation audit fails when its guards never fire: missing-guard warning True, exit 0
FAIL expected-fail annotation cannot conceal a crashing check: child -11, runner exit 0
SCHEMA REVIEW: 3/9 checks passed
```
