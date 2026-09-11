# Switch-fixture review

Reviewed `experiments/switch_fixtures.py` at
`ed56ce75c5b4dd165258a76f2fa76bb8179e1bff`, after merging `origin/v10-harness`
through `3007c96552757d3e485a5a1d04168655b3b8518b` as
`ea5d2b60c86556559126af5e213e32f4e8c6b11c`.
Merge is not approval of other incoming changes. No capture content was opened or
remeasured. The probes below use only the supplied synthetic generators. Neither
the supplied fixtures nor an engine, detector or contract is repaired here.

**C3 is overstated.** Equal blank-level masks are not equal sample arrays, the
proposed normal-timing world is inconsistent with its shared reference, and the
undelivered-instant argument does not establish an undelivered full blanking
interval. A valid indistinguishability construction remains a useful kind of
control; this one has not established its physical premise.

## Findings

1. **A2 generates an empty row interval, not a moved trailing boundary.**
   `experiments/switch_fixtures.py:64`, `:39`, `:167`, `:203`. **Reproduced.**
   The nominal width is 17 samples; subtracting 40 from its end produces
   `[700,677)`. The builder silently skips it. Control 1 drops the same reversed
   span from its expected set, so it passes; control 5 checks varying truth labels,
   not whether either boundary actually moved in the delivered input.

   A2 and B3 therefore have the same all-picture generation law and shared
   calibration, but require `departure` and `undecidable`, respectively. Replacing
   A2's draw by B3's exact array makes their observable inputs identical without
   breaking any of the five controls. Likewise, changing A1's truth from -40 to
   -400 while leaving its samples untouched passes. Validate ordered nonempty
   *unclipped* spans first, then censor valid spans; independently check truth
   coordinates against injected coordinates and require consistency for identical
   allowed detector inputs. A bad span is not an off-window interval.

2. **C3 does not contain the identical observations its bound claims.**
   `experiments/switch_fixtures.py:108`, `:128`, `:130`, `:194`. **Reproduced.**
   A and B use successive independent random draws: all 720 samples differ.
   Control 4 checks only equal thresholded blank sets and unequal prose strings.
   Adding 100 to one of B's picture samples also leaves the selftest passing.
   A function of these two fixed arrays can separate them; that fact alone would
   not make it a meaningful physical classifier. Conversely, if the complete
   observable inputs really were identical, no noise statistic, autocorrelation
   or other deterministic function of those inputs could separate them.

   Under the stipulated Gaussian generator, A and B do have the same conditional
   row distribution. That supports a no-information result *inside that model*;
   it is an assumption of the generator, not a measured property of the analog
   chain. It does not repair the false claim of literal sample equality. Check
   arrays (and all allowed reference/context inputs), not just masks. Establish
   physical admissibility separately; copying the array alone cannot do that.

3. **The hidden-interval story is not physically justified by the 16% gap.**
   `experiments/switch_fixtures.py:116`, `:125`, `:130`, and the C3 interpretation
   in `CLAUDE.md` (incoming entry at line 4167). **Reasoned from the code and
   checked nominal standards arithmetic; not a capture measurement.**

   ITU-R BT.601-7 table 3 specifies 858 samples per 525-system line, 720 active
   samples and 13.5 MHz; BT.470-6 table 1-1 gives M/NTSC line blanking as
   10.9 +/- 0.2 microseconds. At the nominal value the full interval spans
   147.15 samples, exceeding the 138 undelivered samples by 9.15. Thus it cannot
   fit wholly in that gap under this intact-line model. An unobserved switch
   *instant* is a different object. See [BT.601-7](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.601-7-201103-I%21%21PDF-E.pdf)
   and [BT.470-6](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.470-6-199811-S%21%21PDF-E.pdf).

   The contract already states the overlap/visibility distinction at
   `docs/geometry_first_engine.md:416`. The fixture's 17-sample low-level run
   could instead represent only a visible fragment or an abstract pulse. Neither
   interpretation establishes that the *whole* nominal blanking interval vanished.
   This is not an instruction to force nominal extents onto damaged VHS or to use
   147 as a detector threshold. A shortened, overwritten or level-obscured interval
   needs that mechanism represented explicitly before it supports this story.

   There is a second, independent reference inconsistency even for an abstract
   17-sample pulse: B receives the same calibration showing normal blanking near
   `[700,717)`, yet declares the interval outside the window while timing stays
   normal. Changing its phase relative to that window is not unchanged timing
   relative to this reference. Giving B a different calibration would instead
   give a reference-aware detector different inputs. To decide the physical case,
   generate full line-period waveforms, crop with a specified sampling phase,
   distinguish visible fragments from full intervals, and carry the same
   reference and observation model through both worlds. Then verify complete
   observation equality, or justify equality of their observation distributions.
   Occurrence frequency is a separate question; possibility is a necessary premise
   of the claimed bound, not something the bound can dispense with.

4. **Hidden generator truth is being promoted to compulsory observable certainty.**
   `experiments/switch_fixtures.py:14`, `:67`, `:96`, `:98`, `:129`.
   **Reproduced inconsistency; physical implications reasoned.**
   A3 demands `departure` for the same translated-interval generator family that
   C3-A calls necessarily `undecidable`. Replacing A3's row and calibration with
   C3-A's exact inputs leaves all five controls passing with opposite required
   answers. No single interface restricted to row and calibration can honor both.

   The fixture must state whether interval identity is supplied to the detector,
   independently established, or deliberately unavailable. A hidden label that
   says a dark patch is picture cannot itself justify a compulsory `none`, just
   as a hidden translation cannot compel a decision from ambiguous observations.
   If interval identity is provided, the clean endpoint tests can test timing
   algebra. If only raw rows/reference samples are provided, expected certainty
   must be justified under the same permitted physical hypotheses in every class.

   The claim at line 96 about identical source dither also exceeds the record:
   contract `:433-440` explicitly distinguishes approximately matching local
   means/standard deviations from demonstrated equal texture. `_row` stipulates
   identical independent Gaussian low-level noise for both kinds of run; it does
   not test actual dither, quantization, correlated noise or sub-blanking behavior.
   These fixtures do not rule out every legitimate row-local discriminator, and
   do not establish that the entire rebuild must use cross-row or cross-unit
   evidence. Those are possible additional evidence routes for genuinely
   ambiguous cases, not a demonstrated universal requirement.

5. **Injected magnitudes are legitimate test stimuli, but do not establish
   unambiguous recoverability by declaration.**
   `experiments/switch_fixtures.py:28`, `:49`, `:61`, `:70`.
   **Reasoned; A2's invalid magnitude reproduced in finding 1.**
   Choosing a known 40- or 160-sample shift for an abstract regression test is not
   a fitted operational threshold under rule 4. The calibration size, jitter,
   levels, noise model and shift sizes are nevertheless authored test-design
   choices, not owner-specified facts or a guarantee of physical realism.
   They must produce valid intervals and test different signs, sizes, uncertainty
   boundaries and censoring phases rather than only easy cases. In particular,
   A4's +2 end shift lies inside the independently injected +/-2 end jitter;
   its large start change may support a departure, but the +2 does not by itself
   establish that both end shifts are separately measurable. Ground truth and
   measurement uncertainty remain different even in a synthetic test.

6. **The three presence dispositions are sufficient on one axis, not for the
   whole measurement record.**
   `experiments/switch_fixtures.py:30`, `:81`, `:85`, `:89`.
   **Reasoned from the schema.**
   Keep `departure`, `none` (positively established normal timing), and
   `undecidable` for whether departure is established. A departure can be
   established while an endpoint or its exact magnitude remains unmeasurable:
   report `departure` plus unavailable/censored extent, not `undecidable` merely
   because a full count is missing. B1/B2 already gesture toward this distinction.
   A true-but-unobservable departure has different hidden truth but the same
   evidence disposition as an unresolved normal case; truth belongs separately.

   Give the observable interface explicit endpoint/delta units, uncertainty,
   censoring and reasons. Currently A's `truth.start/end` are deltas, B1/B2's
   numeric fields are absolute positions, and other entries are strings. A schema
   consumer cannot safely treat these as the same quantity. A horizontal timing
   departure in one row is also not automatically head-switch identity; the
   separate bottom/location qualification still needs its input/context.

## Reproduction

`python3 experiments/switch_fixtures_review_controls.py` invokes the supplied
selftest and performs named mutations without changing the supplied file. Output:

```text
CONTROLS -- the ways a known-answer fixture set fails to be one
  1 every fixture contains its injected geometry        -> PASS
  2 required answers are mixed                          -> ['departure', 'none', 'undecidable'] PASS
  3 censored fixtures are censored at the window edge   -> PASS
  4 matched pair: identical blank sets, opposite truth  -> [(540, 557)] PASS
  5 class A moves each end independently               -> PASS
SELFTEST PASS
C3: unequal samples 720 ; equal blank sets, not equal observations
C3 picture-sample mutation: fixture selftest exit 0
A2: declared span [(700, 677)] ; delivered spans []
A2/B3 identical row and calibration, required departure / undecidable ; fixture selftest exit 0
A3/C3-A identical row and calibration, required departure / undecidable ; fixture selftest exit 0
A1 truth-only mutation -40 to -400: fixture selftest exit 0
NOMINAL full blanking 147.15 samples > omitted 138 ; minimum overlap 9.15 samples
REVIEW PROBES PASS: historical defects reproduced; no fixture acceptance
```

Exit 0 means the review reproduced these defects. It is not fixture approval.
The review probes deliberately pin this version; repairing the fixtures should
invalidate these historical assertions and lead to positive replacement controls.
