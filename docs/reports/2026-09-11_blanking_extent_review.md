# Symmetric blanking-extent review

Requested commits: `c8faa10`, `9f8dd3f`, `d21f373`. Merged `origin/v10-harness`
through `d21f373` as `12aa8cdafc79695774311d4e63f1666586bcbfa6` before inspection.
The incoming superseded-check edits are outside these three requested changes.
References below are to that merged snapshot. No capture file was opened, displayed,
or remeasured; the supplied residue counts are not independently reproduced here.
All reproductions use `experiments/blanking_extent_review_controls.py` with synthetic
arrays, including an in-memory transport unit passed through the real main function.

Neither proposed residue interpretation is accepted as stated: (a) zero difference
between selected run starts is not absence of horizontal skew; (b) calibration
contamination is possible but not causally established by a position-range statistic,
which does not even control the branch called normal.

## Findings

1. **Device padding is the operative level reference, not merely a scale.**
   `experiments/blanking_extent.py:217-222`, `:54-56`. **Reproduced through main.**
   `median(Y[0:6])` is passed directly to calibration and classification as `level`;
   `blank_spans` thresholds each sample with `row <= level + tol`. There is no
   separate qualified source-level input or conversion that would make this
   "scale only". The selected storage rows are device hard padding, not even the
   device's regenerated blanking intervals. This violates the reference distinction
   the implementation claims to follow. Keeping synthetic source rows identical
   and changing only those six device rows from 16 to 2 changes target assertions
   from 6/6 to 0/6; held-out false assertions remain 0/26 in both. The targets have
   unchanged true blanking plus dark picture, so this is also a counterexample to
   treating a clean negative rate as positive identification. The supplied selftest
   always calls helpers with level 1.4 and never exercises this wiring.

2. **The two returned features do not establish D16's two physical conditions.**
   `experiments/blanking_extent.py:72-84`, `:123-126`. **Reproduced synthetically.**
   Total low-valued sample count and the start of the longest low-valued run both
   derive from the same unqualified level mask. Sharing a waveform is not itself
   prohibited; the failure is missing interval identity and timing evidence. With
   true blanking unchanged, adding a longer dark-picture run changes both features
   and returns `('extended', 50.0, -300.0)`. Conversely a known 20-sample horizontal
   texture phase shift plus a changed right-hand interval returns
   `('Unknown', 20.0, 0.0)` because an unchanged left run remains the first longest
   run. Thus zero in this variable can coexist with a known temporal shift.
   Ties select the earliest run; runs touching the delivered edge are not marked
   censored. Reading (a), especially "those rows are not switches", is rejected.
   Unknown remains unresolved, not demonstrated absence. To decide which mechanism
   affects the supplied 93%, retain all interval endpoints, selected-run identity,
   censoring and an identified timing witness per key; a histogram of p-minus-median
   alone cannot decide it. That per-key investigation is not performed here.

3. **Total duration loses interval placement and opposing edge changes; normal is
   not positively established.** `experiments/blanking_extent.py:82`, `:117-122`.
   **Reproduced.** A 16-sample interval translated from 700 to 500 returns normal
   because total duration is unchanged. Replacing it with two separated eight-sample
   intervals also returns normal. The expected temporal interval is occupied
   differently in both cases, even though its total measure is unchanged. Both
   direction labels being reachable is therefore not sufficient symmetry. The
   general controls use nonzero calibration tolerances (extent 2, position 4), so
   these findings do not depend on exact/zero-variance calibration.
   A uniform blank-level row returns `('extended', 704.0, -700.0)` despite having no
   observable boundary or picture timing component. A row with no blank samples
   returns normal under a sufficiently broad extent tolerance because the normal
   branch precedes the missing-position branch. The selftest's no-blanking result
   is confined to its narrow calibration; it does not defend the general rule.

4. **The 292 position tolerance cannot cause the normal branch, and the calibration
   address description is wrong.** `experiments/blanking_extent.py:104-105`,
   `:118-125`, `:220-221`; `CLAUDE.md:5188-5196`. **Code trace and synthetic
   reproduction; the actual residue's cause is unmeasured in this review.**
   Only extent tolerance is tested before returning normal. Position tolerance is
   consulted afterwards and can produce Unknown, not normal. The None returned
   with normal means skew was not evaluated/reported, not proven unmeasurable.
   The table supplies position spread where an attribution to this branch requires
   extent spread. I reproduced a position range of exactly 292 with identical true
   blanking on all calibration rows and just one added dark-picture run. No switch
   contaminated that calibration. Setting only position tolerance to zero leaves
   the target normal, because the extent range is still broad.
   `210..236` denotes offsets, not storage rows. Actual calibration addresses are
   229,231,...,253 in field 1 and 492,494,...,516 in field 2; validation is interleaved
   at 230..254 and 493..517. A fixed sampling window can be unqualified without
   having been shown to contain switch rows or to form a circular dependency.
   To decide reading (b), inspect independently identified calibration intervals and
   their row ownership, source-vs-content identities, extent range and position range
   separately, then perform a controlled qualification ablation. Moving the window
   or improving the final count alone would not isolate its cause.

5. **The fitted level cut is a timing decision input. Labeling it does not qualify
   it.** `experiments/blanking_extent.py:32-38`, `:56`, `:217-218`. **Reproduced.**
   On an unchanged synthetic row, changing tol from 2.5 to 3.0 changes extent/position
   from (16,700) to (66,400) and classification from normal to extended. Being in
   level units rather than sample units does not make this cut independent of the
   timing verdict: it creates the sample mask from which both quantities are computed.
   Experimental outputs remain reportable as conditional results of the explicitly
   fitted, device-referenced configuration. They are not qualified switch counts or
   evidence of contract conformance. For that promotion the interval provenance and
   level/variability reference must be qualified from the source; deriving a number
   from variance alone does not exclude dark picture at the same level. The source
   level must not be replaced by another fitted device-level shortcut.

6. **Qualifying by level is not automatically independent of timing, nor automatically
   circular.** `CLAUDE.md:5205-5208`; `experiments/blanking_extent.py:56`, `:96-105`.
   **Reasoning from dependencies; no proposed qualifier implementation was supplied.**
   Level determines mask membership, which determines duration, position and both
   tolerances. The distinct names of the outputs do not isolate their information.
   An independently qualified source-level reference can be computationally
   non-circular, but normal-timed and skewed blanking can have identical levels;
   level qualification alone does not establish that a calibration row is normally
   timed. If its level reference is itself extracted using the timing expectation
   currently being fitted, the claimed independence has to be proved rather than
   assumed. Likewise timing-based qualification is not inherently circular when its
   normal-timing evidence is independently established. The circular case is declaring
   rows normal because they agree with the very estimate they train. What decides
   the proposed repair is an explicit reference/selection dependency trace, held-out
   row keys and same-level normal/skewed negative controls, not the level/timing names.

7. **The fixed 0.23% acceptance condition is invalid.** `CLAUDE.md:5202-5204`.
   **Mathematical/methodological reasoning, not a new capture experiment.**
   A better discriminator or a corrected reference can reduce false positives and
   false negatives simultaneously. A tradeoff for varying a threshold on one fixed
   score does not prohibit a better score/reference. Joint improvement is neither
   sufficient proof of leakage nor a reason to reject a repair. Freeze evaluation
   populations and report keyed before/after errors, abstentions and denominators;
   investigate leakage by dependencies and controls rather than requiring an old
   empirical error count to remain unchanged. No new policy error budget is proposed.
   The repeated rationale at blanking_extent.py:91-93 is also still wrong: a fixed
   percentile interval has a chosen tail mass, not an immutable error floor for all
   percentile choices. That was already corrected in the preceding review.

8. **The reported denominator can shrink silently.**
   `experiments/blanking_extent.py:101-102`, `:223-224`, `:256-263`;
   `CLAUDE.md:5211-5212`. **Reproduced through main using a synthetic unit.**
   When calibration has fewer than six positions, main skips the entire field.
   It records neither its three target rows nor its thirteen validation rows as
   unavailable. Removing usable calibration in the synthetic unit prints
   `identified on the switch band : 0 of 0 = 0%` and
   `FALSE identification on held-out no-switch rows : 0 of 0 = 0.00%`, with zero
   Unknown reported. A qualification repair can therefore improve apparent rates
   through attrition. This is a real mechanism to guard against, unlike the claim
   that any joint improvement implies leakage. Fixed expected-band targets also
   remain presumed positives, not independently identified switch rows. The six
   controls cover neither reference wiring, unavailable-field accounting nor an
   asymmetric field-ownership/reference test; control 6 repeats reachability already
   exercised by controls 2 and 3. Passing all six is not coverage of these requirements.

## Reproduction and scope

```sh
python3 experiments/blanking_extent.py --selftest
python3 experiments/blanking_extent_review_controls.py
```

The supplied selftest prints SELFTEST PASS. Selected review output, verbatim:

```text
same duration, translated blanking features (16, 500) classification ('normal', 0.0, None)
dark content adds longer run; true blanking unchanged features (66, 400) classification ('extended', 50.0, -300.0)
uniform blank-level row; both edges censored features (720, 0) classification ('extended', 704.0, -700.0)
known texture phase shift 20 reported ('Unknown', 20.0, 0.0)
contaminated expectation (16.0, 50.0, 700.0, 292.0)
same target, position tolerance 292 ('normal', 16.0, None)
same target, position tolerance 0 ('normal', 16.0, None)
no blanking, broad extent tolerance ('normal', -16.0, None)
```

The probe reports falsifying outputs without repairing the detector or redefining
its statuses. Known synthetic interval/texture construction supplies the independent
answer; none of these outputs describes capture content. No new implementation or
contract edit is proposed by this review.
