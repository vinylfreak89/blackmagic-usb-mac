# Source-dither comparison review

Reviewed `experiments/dither_compare.py` from `f49ce91`, the interpretation at
`968d2b5`, and its live `source_reference.py` dependency. Merged the harness by
fast-forward to `968d2b561fa78d49964340f40f0eab64777ed45b`. Other incoming changes,
including the latest fixture repairs, are not implicitly reviewed here.

During this review the harness advanced through `464a5df`, including follow-up
selection/descent work (`22e808d`, `9a9fd82`, `590c198`). Those changes are not
merged or evaluated here; findings and reproductions refer to the snapshot above.

No capture content was opened or remeasured. The module reads a capture at import
time, so the review replaces `walk_tagged` BEFORE loading it. All executed rows
and transport units are generated synthetically. The supplied population counts
remain reported observations of this configured program, not independently
reproduced source measurements. No engine, detector, supplied instrument, fixture
or contract repair is made.

**The candidate-witness interpretation is overstated.** Lag texture is a sensible
candidate feature to investigate, but this comparison establishes neither the
blanking-identity half nor the displacement half of the one-ended witness. The
same raw process acquires opposite signs under the two selection paths. This
demonstrates a confound, not that it caused all of the reported real-data split.
The earlier same-dither assertion remains unsupported; this test does not yet
establish its opposite as a physical property.

## Findings

1. **The blanking arm does not measure lag one in original sample time.**
   `experiments/dither_compare.py:45`, `:75`; `experiments/source_reference.py:172`.
   **Reproduced with the actual selection and emit functions.**

   `settled_samples` computes a floor from the minimum two-sample block mean,
   then retains `tail[tail <= floor + 1.0]`. It removes values and their indices.
   `lag1` subsequently treats adjacent survivors as adjacent samples. A reference
   pool intended for a level estimate is not thereby a contiguous time sequence.
   The dark arm retains contiguous slices and does not perform this same removal.

   A repeating `[1,2,3,4,3,2]` process has lag +0.447727. The selected subsequence
   has lag -0.483333, and its codes 3/4 disappear. Putting identical copies in
   the interior and tail of each synthetic row, then running the REAL `emit` and
   source-reference implementation, produces median lags -0.483333 and +0.437679.
   Opposite signs and differing histograms therefore can arise with identical
   raw processes and no physical class separation.

   Retain original indices and compute lag from actual adjacent-time pairs on
   contiguous qualified intervals. Do not bridge rejected samples. Compare the
   unfiltered qualified runs, and record which samples each selection removed.
   Even an index-preserving low-tail selection can bias the conditional statistic;
   the qualification and comparison need to expose that selection explicitly.
   The transition/settling routines also select where a run starts; removing the
   value mask alone would not prove that start selection is unbiased.
   Whether the particular measured runs lost samples is unmeasured here. A keyed
   raw-versus-selected rerun, not this synthetic counterexample alone, decides how
   much of the reported split the mechanism explains.

2. **The labels and sampling rules do not establish two physical populations.**
   `experiments/dither_compare.py:39`, `:41`, `:47`, `:54`.
   **False labeling reproduced; selection implications reasoned.**

   The blanking arm is whatever the current transition finder and selected-tail
   routine return. The dark arm is every run in samples 0..639 below
   `ref.level + 3.0`, of length at least eight. It includes the LEFT EDGE and can
   include relocated blanking or a tail beginning before 640. In a synthetic
   input with one known shifted blanking prefix per field, the other reference
   rows unchanged, and no low-picture patch, the real emitter labels BOTH known
   prefixes as dark; the dark median is -0.991667. Each target row has only the
   prefix, not an invented second blanking interval. Position is not identity.

   Neither the +3 cutoff, the 640 boundary nor the >=8 rule follows from the
   autocorrelation formula. Eight is an authored cohort filter, not a standard
   or demonstrated qualification threshold under rule 4. An explicitly labeled
   exploratory filter is reportable as such; it cannot become the engine's
   threshold without qualification. Contiguous low-run selection conditions on
   both values and persistence, excludes interruptions/high excursions and splits
   longer regions. It can change the population's correlation; the direction and
   magnitude need measurement rather than assumption. The dark population is not
   actually defined simply as "at or below the blanking level": it uses level +3.

   Compare independently identified source blanking and picture, use equivalent
   unfiltered treatment, report length distributions and unavailable cases, and
   sweep the authored cutoff/length choices. Match or stratify by run length,
   level and source context, with held-out validation. The same source rows used
   to construct the reference also supply the reported comparison, so this is
   not a held-out discriminator evaluation. Shared rows do not by themselves make
   the two arms unbiased or pair each classified run with its counterpart.

3. **Neither lag sign nor a nominally long run certifies identity.**
   `experiments/dither_compare.py:26`, `:46`, `:75`.
   **Estimator counterexamples reproduced; qualification implications reasoned.**

   This is a mean-subtracted, finite-sequence autocorrelation estimate, not a
   unique dither identifier. Conditional on a fixed nonconstant value bag with
   random ordering, this estimator's mean at lag one is -1/n: the sum of all
   off-diagonal centered products is minus the sum of squares. Enumerating all
   permutations of `[1,2,3]` reproduces -1/3 with no filtering/dither mechanism.
   Blanking accepts sequences down to length three; dark accepts length eight.
   Run lengths, selection, and finite-sample effects need accounting before
   comparing their quantiles.

   The supplied overlapping quantiles do not specify a classification operating
   point, error rates or an uncertainty bound for any particular run. Roughly
   147 samples may be more informative than two; it is not automatically enough.
   Effective adjacent pairs, nonzero variance, dependence and decision margin
   matter. A constant 120-sample sequence yields NaN; the program drops NaN lags
   before summarizing them. Report those abstentions as well as the remaining n.

   A stationary rectangle concerns persistence across fields, not the lag of
   successive samples along a scan. An interior can be flat plus white,
   positively correlated, or negatively correlated acquisition noise. The
   synthetic stationary alternating-noise rectangle yields lag -0.991667; a
   perfectly constant interior is undecidable for this statistic. If a rectangle
   does have positive lag, that would HELP the proposed negative-lag classifier
   reject it, not defeat it. What must be excluded is a non-blanking region whose
   observed noise is classified as blanking. Test both stationary and changing,
   interior and edge-connected rectangles, including ambiguous noise laws.

4. **The comparison does not join to or validate the declined one-ended cohort.**
   `experiments/dither_compare.py:35`, `:42`, `:46`, `:54`;
   `CLAUDE.md` one-ended decision at incoming `:3570-3589` and
   `src/field_registration/tests/RUN_TOLERANCE.md`, final disposition.
   **Reasoned from data flow; no target-key measurement performed.**

   The script samples offsets 20..209 from each field's picture origin, not the
   disputed bottom candidates. It saves arrays only, not counter/field/row/run
   coordinates or original sample indices. There is no keyed test of the 255,
   black-rectangle rejection, source-local boundary displacement or departure/
   return behavior. Its label separation, even after repaired estimation, would
   be a candidate identity feature, not completed timing qualification.

   Once a feature positively identifies the interval, its exposed boundary may
   be compared against qualified local timing references. That chain could support
   a one-ended reading while the missing endpoint/extent remains unavailable.
   Reusing the same samples is not automatically disqualifying: no mandatory
   second detector is invented. The feature must add independently qualified
   discriminating evidence, not merely rename the original ambiguous mask.
   The normal reference, its validity after loss, uncertainty and the terminal-band
   versus ordinary tearing distinction still matter. The current 255-reading
   disposition therefore stands; no engine change follows from these medians.

5. **The histogram formatter cannot support "never reaches code 3" from a 0% label.**
   `experiments/dither_compare.py:73`, `:78`.
   **Reproduced; application to the supplied wording conditional.**

   `np.unique` returns only present codes, then `%.0f%%` rounds their frequencies.
   A synthetic bag with ONE code-3 sample out of 1,000 prints `3:0%`. If that
   token came from this formatter, it establishes presence, not absence. Exact
   code counts are needed for the categorical statement. Selection in finding 1
   is a separate reason the selected histogram is not the raw blanking histogram.
   No claim is made here about the actual unreported count of code 3.

6. **Do not replace all matched dark-content controls with a different-noise law
   on this evidence.** `experiments/switch_fixtures.py:128`;
   `experiments/dither_compare.py:8`.
   **Design recommendation reasoned.**

   Replace the unsupported source-wide same-dither assertion with a stated
   synthetic assumption. Preserve the conditional equal-observation/adjacent-dark
   ambiguity control as a test of what its restricted evidence cannot establish;
   do not claim it demonstrates this source's physical noise. Add distinguishable
   noise cases as separate positive controls after estimating the noise from
   contiguous, independently qualified runs. Include overlapping/ambiguous cases
   requiring abstention. Drawing every dark rectangle from a conveniently positive
   process while every blank run is negative would build the desired discriminator
   into the fixture labels, not validate it. Actual source-derived fixtures need
   separate held-out tests and explicit limits on generalization.

## Reproduction

`python3 experiments/dither_compare_review.py` exits 0, reproducing the confounds
without reading a capture. Its output is:

```text
SAME PROCESS raw: n=120 mean=2.500000 lag=+0.447727 codes=[1.0, 2.0, 3.0, 4.0]
AFTER settled_samples: n=60 mean=1.666667 lag=-0.483333 codes=[1.0, 2.0]
REAL emit, identical raw processes: blank median=-0.483333 dark median=+0.437679
KNOWN BLANKING PREFIX labeled dark: 2 runs; dark median=-0.991667
STATIONARY RECTANGLE model: alternating noise lag=-0.991667; constant interior lag=NaN
RANDOM ORDER n=3: exact mean estimated lag=-0.333333
NONZERO CODE 3 COUNT=1, current formatting: 1:60%, 2:40%, 3:0%
REVIEW REPRODUCTIONS PASS; no capture read and no witness validated
```

Pass means the review reproduced these mechanisms, not that the instrument or a
physical identity witness passed validation. Whether the reported empirical split
survives corrected sampling remains an open measurement, not an owner question.
