# Proposed set-observable review

Merged `origin/v10-harness` through `e5b4468` as
`a123dbc6c7d2b62f2cb1b0acaa8248b48f81a180` before review. The requested retractions
and controls were read. Other incoming changes are not implicitly approved by the
merge. No capture content was opened or remeasured. The proposed set detector is
not implemented; `experiments/extent_set_review_controls.py` tests its algebra and
dependencies on synthetic inputs only, not an operational switch classifier.

## Decision: a third reading

Keep the owner's OR for the excursion, and require a measurable horizontal-timing
component with interval identity established. Neither two positive set counts nor
adjacency to a thresholded boundary is itself that qualification. This does not
require two independent detectors: one qualified timing observation may support
both conditions. The existing bottom/location qualification also remains; a row
observable by itself does not distinguish a head switch from horizontal tearing
elsewhere. See contract `docs/geometry_first_engine.md:43-62`, `:420-446`, `:536-548`
and the relayed D16 quote in CLAUDE.md.

A converts the owner's OR into an AND. A positively identified boundary can move
with only one of b/p positive, so both are not necessary. They are not sufficient
either: a moving dark patch makes both positive with true blanking unchanged.

B's adjacency criterion is not sufficient. Expected blanking at [700,716), with
an observed low-level interval [690,716), admits both a moved blanking boundary and
unchanged blanking plus an adjacent dark-picture patch. The synthetic sample arrays
can be identical. An unqualified level-mask boundary does not distinguish those
constructions just because it lies next to an expected interval.

For the three examples: (i) is a measurable translation **if the displaced interval
has been identified**, not merely because b and p exceed tolerance. (ii) can carry
a measurable start shift on the same condition; it must not be categorically denied
because p=0. (iii) has a right-censored end, not an unchanged end. The unchanged
start is not proof of zero skew. If samples through 719 are positively identified
as the same blanking interval whose expected end is 716, the observation constrains
that end beyond the expected position; its exact endpoint is unavailable, not
necessarily every timing bound. If identity cannot be established, the right answer
from this route is Unknown, just as for the ambiguous dark-patch construction in
(ii). Do not give starts privileged status over ends.

Control 4 at `experiments/blanking_extent.py:173-179` can stay Unknown as an
insufficient-evidence control, but its explanation "expected position has no skew"
is not established by an unchanged run start. Uniform blank/picture controls lack
a within-row boundary for this method, so it must abstain on that evidence; this is
not a prohibition on other independently qualified evidence routes.

## What is proposed by the agent, not dictated by the owner

The owner supplies source-relative expected extents, departures in either direction,
local timing variation, measurable skew and separately qualified source blanking.
The following are implementation proposals rather than quotations or uniquely
implied consequences:

1. Sample-wise binary level masks; naming all their complements "picture". A sample
   outside a blanking-level cut can be noise, ramp, corruption or unknown, not
   positively identified picture. Blank-level membership likewise is not identity.
2. Intersection/union as the expected sets. These are observed consensus envelopes,
   not guaranteed blanking/picture regions. Stable dark content can occupy the
   intersection, and one mask error can remove a genuine blanking sample from it.
3. Calling the remaining set "the rows' own jitter". Variation can instead be level
   noise, changing content, misidentified intervals or contaminated calibration.
   A larger calibration population can enlarge this indeterminate set. The rule
   for unavailable or empty support must be explicit; do not call it normal.
4. Reducing the directional departure sets to the counts b/p. Retain their endpoints,
   topology, identity and censoring for timing qualification; counts alone still
   discard the information the proposed skew test needs.
5. Leave-one-out calibration, its aggregation into a tolerance (not yet specified),
   strict exceedance, and any requirement on both versus either count. These are
   chosen estimators/decision rules, not parameter-free consequences of the ruling.
6. Adjacency, start-only qualification, and a categorical interpretation of a
   censored end as no skew. None is supplied by D16.
7. The current `source_reference` implementation and an upper mask bound equal to
   the selected pool maximum. The source-reference requirement is settled; this
   code and this statistic are not thereby qualified.

The set formulation does repair a specific information loss of summed duration:
on a clean exact reference the translated and split synthetic intervals both
produce (b,p)=(16,16). It does not guarantee nonzero departures for every translation
once union/intersection ambiguity and tolerances are introduced. In a synthetic
calibration, one extra low-level region changes the same translated test from
(16,16) to (0,16); if maximum LOO scores are chosen as tolerances, they become
(50,0). That variation was not jitter and no switch was in calibration.

Leave-one-out is not a held-out validation population. If a held-out row contributed
to the source pool maximum or to row qualification, leaving it out only from the
set envelope does not withhold it from the pipeline. Either use an independently
qualified external reference for that fold or cross-fit all learned dependencies.
Keep separate validation keys and account for every unavailable field/row.

## Source pool maximum: candidate, not settled

Use the mean of qualified source-blanking samples for the reference level, with
variability separate, as the contract states. Replacing device padding is required;
calling `source_reference` is not itself proof of correct sample provenance or mean.
The merged `settled_samples` still selects low samples using `floor + 1.0`
(`experiments/source_reference.py:154-178`). On a synthetic sequence consisting
entirely of known settled blanking, [3,1,3,1,1,1], it retains [1,1,1,1]: the selected
mean and maximum are both 1, against an input mean 1.6667 and maximum 3. This repeats
the previously recorded selection issue rather than newly diagnosing a capture.

A maximum describes the largest **selected observed** value, not the source's
future support or a guaranteed blanking/picture separator. It depends on pool size,
dependence between samples, rare noise and contamination. Deriving a cutoff from
observations does not eliminate choosing the statistic, sample qualification or
the tolerated error. Its stability and held-out consequences have not been
measured here. No substitute percentile or magic constant is prescribed.

## What would decide the operational qualification

Use known-answer temporal waveforms with interval identity supplied independently:
translations of either sign, start-only and end-only changes, partial-line changes,
edge entry/exit and censoring; pair each with unchanged-timing dark-content controls,
including identical level-mask observations. Require timing estimates with their
uncertainty where distinguishable and explicit Unknown where the supplied evidence
does not separate the constructions. An independent timing landmark or a qualified
within-row phase observation can decide cases the level mask cannot; it need not be
a second detector merely for the sake of independence.

For the reference, inspect keyed selected and rejected sample provenance, measure
maximum stability across pool sizes and independent local units, and evaluate on
fixed held-out populations. Run known noisy-blanking and contamination controls.
Report false assertions, misses and abstentions separately. These measurements can
choose an implementation; nothing in the owner's words selects the maximum or
the proposed A/B Boolean rules for us.

## Checks

`python3 experiments/blanking_extent.py --selftest` exits 1, as committed. Failing
lines verbatim:

```text
  TRANSLATED 300 samples             -> normal     FAIL: a timing displacement reads normal
  SPLIT, same total duration         -> normal     FAIL: duration is blind to it
  uniformly blank, no boundary       -> extended   FAIL: identified with nothing to displace
SELFTEST FAILED
```

Controls 7/8 only require not-normal, so they permit Unknown; their passing would
not by itself demonstrate successful identification. The six earlier controls pass.
`python3 experiments/extent_set_review_controls.py` exits 0 with:

```text
ALGEBRA/DEPENDENCY CONTROLS PASS; no switch identity was certified
```

No detector, engine or contract repair is made by this review.
