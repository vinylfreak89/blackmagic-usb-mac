# Edge-censored switch-fixture review

Reviewed fixture repair `5e8797b0b7da59559a41ba40d2c80f592a44fee2`, including
its commit message, after fast-forwarding `v10-engine` to the pushed harness
head `095ee3ac8fd0f53c9e1f4b1ba0fb4122c946f997`. File/line citations below
refer to that snapshot. Other incoming work, including the dither withdrawal's
new instruments, is not implicitly reviewed. No capture content was opened,
rendered or remeasured. This review makes no engine, supplied-fixture or contract
change. The withdrawn texture result supplies no premise here.

Both supplied suites pass: eleven fixture checks; seven mutations report their
intended guard, six with no other guard reporting failure. Those observations
reproduce. They do not establish that all prior findings are repaired. The
synthetic-only `experiments/switch_fixture_censoring_audit.py` has twelve unmet
positive checks and exits 1 (3/15 pass); its output is reproduced below.

## Findings

1. **B2 requires `undecidable`, not positive absence; A5 shares the ambiguity.**
   `experiments/switch_fixtures.py:101`, `:115`.
   **Reasoned semantics; equal-input construction reproduced.**

   If `none` means no timing departure, B2 explicitly has a counterexample to that
   answer in its own hidden truth. An unchanged visible prefix boundary plus an
   unavailable end does not establish that the entire interval was unchanged.
   Under the allowed A5/B2 worlds, presence must be `undecidable` for both unless
   additional evidence excludes hidden end motion. The visible-start result can
   independently report no established shift; the end and full extent remain
   unavailable. No fourth presence value is needed.

   The current arrays are separate random draws, not literally byte-identical.
   Their input distributions coincide under the authored noise law, and the audit
   couples the same permitted realization to give identical full row and reference
   inputs with different hidden end truth. It does not expose the fixture name,
   `spans`, truth or required verdict to the hypothetical detector.

   Alternatively, explicitly change the question to `no_visible_departure` and
   name it that way. That is not the previously requested three-state presence
   result, and cannot be used downstream as proof of normal timing. A5 and the
   similarly censored C controls need consistent scoping, not just a B2 relabel.

2. **Keep `(702,720)` as one edge-censored observation case, not as a measured
   complete interval.** `experiments/switch_fixtures.py:39`, `:45`, `:70`.
   **Recommendation reasoned; calibration contradiction reproduced.**

   An empirically motivated placement is a legitimate authored fixture choice;
   it does not become a fitted runtime threshold. Keep it and A2's shortening,
   alongside interior-phase cases. But sample 720 is the delivery boundary, not
   an observed physical blanking endpoint. A low run reaching sample 719 supports
   censoring, not an exact latent interval end or full duration of eighteen samples.
   A median start is also not the start of every source row.

   The actual synthetic calibration independently jitters the end around 720:
   **9/24 reference rows end strictly inside delivery** at the default seed.
   Thus the generator does not implement its comment's all-censored reference.
   This is not a remeasurement of the empirical placement. The cited measurement
   itself uses `ref["level"] + 3.0` (`experiments/end_observability.py:30`), so
   its result should retain that selection rather than become a universal fact.

   Separate the visible intersection from a declared hidden interval. For an
   all-censored calibration, construct hidden ends beyond delivery throughout
   the injected jitter, then crop. For a physical full-waveform fixture use a
   declared full period and sampling phase. An abstract interval-algebra fixture
   is still useful, but do not translate the eighteen-sample visible fragment and
   call it a measured complete blanking waveform. When a formerly hidden endpoint
   appears, its current position can be measurable while its displacement from
   the reference end is only bounded.

3. **Numeric censoring and hidden truth bypass the new checks.**
   `experiments/switch_fixtures.py:112`, `:198`, `:241`.
   **Reproduced.**

   Declaring B2's end and extent observable still passes all eleven controls.
   So do declaring A5's window-edge end observable and all of absent B3 observable.
   Control 8 tests only the literal string `off-window`; numeric off-window ends
   and `absent` evade it. This is especially consequential because the new truth
   schema intends to keep hidden coordinates numeric.

   Changing B2's hidden end shift from +60 to +1000 also passes, despite its
   declared span still ending at 780: control 3 clips both to 720. Check full
   synthesis truth against the unclipped construction, then check visibility
   against the cropped observation. Do not try to recover hidden truth from the
   samples. B1 still stores `off-window` for a start the generator knows is -60;
   its numeric delta would be -762 relative to the current nominal start.

4. **Calibration validation checks one start, not each complete reference.**
   `experiments/switch_fixtures.py:232`.
   **Reproduced.**

   All eleven controls pass with an empty calibration, with every reference
   interval shortened to `[702,703)`, or with only A3's reference replaced by
   uniform picture. The guard examines only `C[0]["cal"]`, only looks for a
   matching start, and accepts an empty population vacuously. Validate each
   distinct reference, non-emptiness, full construction, permitted jitter and
   censoring. Preserve calibration truth separately from detector inputs.

5. **The small-shift rule still couples one endpoint's uncertainty to overall
   presence.** `experiments/switch_fixtures.py:104`, `:217`.
   **Reproduced; schema consequence reasoned.**

   Give A4 a -30 start shift and -1 end shift, regenerate its row consistently,
   and retain `departure`. Control 5 alone rejects it. The large start shift
   establishes departure within the fixture's qualified-interval model; inability
   to resolve the other shift must not invalidate that evidence. Separate endpoint
   position availability, displacement bounds/uncertainty and overall presence.
   Three availability booleans are progress, not the full requested separation.

   A6 is useful but changes only the start, -1/0; its name calls it a translation.
   A4's comment says it shortens although its interval grows from 18 to 37 samples.
   These are truth-description errors, not reasons to discard the stimuli.

6. **Guard identity is now reported, but rejection enforcement can still disappear
   undetected. Mask equality also remains weaker than input equality.**
   `experiments/switch_fixtures_review_controls.py:52`;
   `experiments/switch_fixtures.py:208`.
   **Disabled-enforcement bypass reproduced; interface distinction reasoned.**

   The positive suite retrieves `rc` but ignores it for mutated cases. Disable
   the rejection effect of control 3, 5, 7 or 8 individually, leaving its diagnostic
   `FAIL` text intact: the positive suite still passes. Its new 7/7 statement
   accurately counts messages; it does not prove seven enforced guards. Require
   both the correct structured failure cause and nonzero rejection, and verify
   disabling the intended guard breaks its positive control. Report collateral
   failures separately as the revised suite already does.

   Control 4 was not repaired: it groups thresholded low spans, ignoring the
   reference and remaining samples. That equivalence is valid only for an explicitly
   mask-only interface. Different references or timing-bearing textures can
   legitimately distinguish cases with equal low masks. Specify the allowed
   detector inputs before asserting that their required answers must coincide.

7. **The conditional matched control is buildable now; the unsupported source
   assertion still needs removal.** `experiments/switch_fixtures.py:128`.
   **Conditional construction reproduced; empirical scope reasoned.**

   Build A as a visible leading-boundary extension, and B as unchanged blanking
   plus immediately adjacent dark picture. Retain delivered normal blanking in
   both worlds. Declare equal low-level/noise behavior as a synthetic model
   assumption and use identical allowed inputs, with attribution only in hidden
   truth. The audit constructs that pair. No qualified texture measurement is
   needed to test insufficiency under this explicitly conditional model.

   My earlier request for qualified measurements applies to assertions that
   distinguishable or overlapping noise models describe this source, not to the
   existence of an authored conditional control. Do not block that half, and do
   not promote it into an analog-chain impossibility theorem. A separately
   distinguishable synthetic noise case can likewise test an estimator under a
   stated model; empirical representativeness remains unestablished.

   Line 128 still asserts this material has identical dither. The withdrawal
   elsewhere did not amend this consumer. Replace that assertion with the
   authored-model scope; neither the withdrawn experiment nor its opposite is
   required to construct the conditional pair.

## Audit output (verbatim)

```text
PASS unmodified fixture suite: exit 0, guards []
FAIL numeric censored B2 cannot expose its end/extent: exit 0, guards []
FAIL edge-censored A5 cannot expose its end/extent: exit 0, guards []
FAIL absent B3 cannot expose endpoints/extent: exit 0, guards []
FAIL B2 hidden truth must match its unclipped span: exit 0, guards []
FAIL empty reference rejected: exit 0, guards []
FAIL reference with correct start but wrong end rejected: exit 0, guards []
FAIL each case's own reference checked: exit 0, guards []
FAIL large start departure survives uncertain end shift: exit 1, guards [5]
FAIL positive suite detects disabled rejection effect 3: positive suite still passes
FAIL positive suite detects disabled rejection effect 5: positive suite still passes
FAIL positive suite detects disabled rejection effect 7: positive suite still passes
FAIL positive suite detects disabled rejection effect 8: positive suite still passes
PASS A5/B2 full row and reference can coincide with different hidden truth: conditional synthetic ambiguity; no physical occurrence claim
CALIBRATION: 9/24 ends strictly inside delivery; not all censored
PASS conditional extension/adjacent-dark luma pair is constructible: identical allowed inputs; hidden attribution differs; no analog bound
CENSORING AUDIT: 3/15 checks passed
```

`py_compile` and `git diff --check` pass. The contract diff against the merged
harness head is empty; `AGENTS.md` remains the symlink to `CLAUDE.md`. A sandboxed
lock-holder process check returned `zsh:4: operation not permitted: ps`; the
approved read-only retry succeeded and confirmed the dispatching process alive.
