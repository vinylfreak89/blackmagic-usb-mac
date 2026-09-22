# Codex experiment commitments

## E-codex-2026-09-22-1 — promote the measured top-search arm

**Owner's question/instruction (relayed):** "codex should be building the new
engine... not producing the renders based on half python, half C". The requested
top rule is a five-code margin over the derived horizontal level, next-row
11-of-16 chunk agreement on every candidate, and evidence-only plain23/run-in.
Bottom measurements and registration state transitions are not being changed.

**Premise.** On this tape, the new top rule improves high-confidence comb
agreement without relying on a Python copy of the engine or a different
pairing/reset history. This is a self-consistency check, not independent truth
about all source edges. The old rule must remain exactly reachable.

**Method.** Feed the same exact rasters, counters and the live sidecar's pairing
and reset flags to C probes built from c620966 and from the current engine with
explicit old (0,0,1,1) and proposed (5,3,0,0) controls. One streaming capture
pass, bounded per-unit memory; separate audit engines supply comb evidence while
non-audit engines supply CPU costs. Compare unit features bit-for-bit and frame
decisions by bottom-unit counter and top-unit identity. Score published
frame_d2-frame_d1 at margins 1.5/3/5/8, with and without counters >=90300;
enumerate gains/losses. Check the four requested labelled counters and inspect
the fade's missing-top placement fallback and the six requested edge cases.

**Preflight context.** The supplied arm feeder defaults to aligned throughout
and resets only on counter gaps. The live sidecar uses a pairing switch at
48189 and classifier resets. Those populations must be named separately;
the supplied figures must not be silently represented as live-path figures.

**Falsifier.** Any old-arm mismatch to c620966, change to bottom edges/profiles
or device blanking, failure of the four labelled counters, or decrease in the
live-path >=3/5/8 bands below counter 90300 prevents promotion pending review.
Report the unfiltered bands and every regression too. Missing-top fallback
must not be described as a general fade freeze if a decided comb or another
measured field can still move placement. No retuning after a failed gate.

**Material.** All 86,293 exact units of captures/fulltape.cap6; live pairing and
reset history from captures/fulltape_render_registration.csv. Supplied C arm
CSVs in scratchpad/ctr9040/arms are comparison evidence, not the oracle for
live framing/state. Synthetic tests cover default controls and protected paths;
unit/ASan/TSan checks follow any promoted implementation. Results stay in scratch.

**Pre-run addition (owner criterion 7).** The built default must reproduce every
non-timing column of ctr9040/arms/m5_g3_p0_r0.units.csv on all 86,293 units,
including rule_first/auto_first and evidence columns. Per-unit census is
independent of pairing/reset history. Any difference is reported, not reconciled;
the first ten differing counters carry both values. This is a separate gate
from scoring stateful placement with the live pairing/reset stream.

### Report

**Verdict: held for the specified numeric gate, not a general edge-truth or
fade-freeze claim.** The built default (5,3,0,0) exactly reproduces the chosen
C census on 86,293/86,293 units, every non-timing column included. The explicit
old arm (0,0,1,1) exactly matches c620966 on all 86,293 measured units and
86,289 frame decisions. Bottom edges, profiles, device blanking and derived
level provenance are unchanged on every unit. The four labelled counters pass.

With live pairing/resets and counters below 90300, agreement improves at all
four bands; >=5 gains 27 and loses 25, rather than the aligned-only gain of 29.
The supplied aligned-only percentages independently recount correctly, but are
not live-path figures. No thresholds were retuned. Field-1/field-2 unavailable
tops rise from 471/422 to 739/641. Noisy-level inflation remains uncured.

Raw checks on the six named units support removal of the accidental run-in
save: line 24 has 0..3/16 agreeing chunks and line 25 passes; the old rule scanned
24 then incremented to 25. All six new results are 25 directly. The unexplained
regression spans remain; comb self-consistency does not identify their physical
cause, nor prove every new top is correct.

The fade gap is real: in 48055..48195 the new rule has 35 frames with a missing
top, and seven of those change absolute placement. At frame 48063, tops (0,293)
publish (8,7), versus (1,0) at 48062, with an abstaining comb. Relative-shift
fallback survives; a still-measured field-2 top can move both fields. Thus the
rule does not implement a general fade freeze. Its decided-comb agreement in
that span does improve 6/86 -> 86/86. No additional fade/state rule was authorized
or added; this limitation is explicit in the engine documentation.

Normal, ASan/UBSan and TSan checks pass, including default-vs-explicit controls,
both pairings, and missing-top fallback assertions. Default non-audit engine
thread CPU is 0.114250 ms/unit median, 0.802917 p95 (old 0.232917/0.853225).
Detailed populations, gains/losses, raw-row numbers, instrument errors and all
outputs are in /private/tmp/top-rule-promotion.28Tfev/REPORT.md and summary.json.
No push or render. Mutual review remains required before treating this build
as accepted for publication.

## E-codex-2026-09-22-2 — ignore top-only moves: state-series preflight

**Owner's instruction (relayed, entry 31).** "if the chunk disagreement says
the line should be shifted, but the bottom did not shift, ignore the override
from the chunk disagreement. don't hold... ignore. does that rescue our class
of problems while saving the legitamate fixes."

**Premise.** Replacing only a GE_TOP_ONLY top with its predecessor's interpreted
top can suppress a spurious run while preserving true tandem/bottom-only moves,
the specified labelled counters, comb timing and abstentions. Measured features
must remain independently recoverable. This is not a whole-geometry freeze.

**Method.** Before production changes, use the existing C classify/frame/comb
code in a scratch instrument. Compare unmodified d5c9f08 with exactly the
proposed substitution after classification, storing that interpreted top for
the next comparison. Preserve the triggering class on the current unit, all
bottom features and reset/pairing behaviour. Test synthetic sequences showing
a top-only onset followed by a genuine tandem or bottom-only step. If needed,
stream real units through both states, emitting measured/interpreted tops,
classes, frame placements, comb evidence and timing. No Python rule mirror.

**Falsifier.** A baseline valid-move or bottom-only class changes, the comb's
run/decided semantics changes, a named labelled top fails, or agreement drops
in any required band. These are the entry's constraints, not permissions to
alter the classifier or add shadow decision state to force their invariance.
A conflict between interpreted-series feedback and these invariants must be
reported for an owner decision before production implementation. A measured-
series alternative is identified separately, not called equivalent run suppression.

**Material.** Synthetic features and rasters passed to the current C engine;
whole-tape exact units and capture 1 if preflight can proceed without a semantic
conflict. Use the same live pairing/reset stream as the preceding acceptance.
The owner will run the independent edge gate; do not substitute comb agreement
for that gate or call capture 1 fixed. Keep scratch code/results under /private/tmp.

### Report — stopped at the series/invariance conflict

**Verdict: the proposed feedback and the stated invariants are incompatible in
general; usefulness on source material remains unknown.** A deterministic
three-unit probe calls d5c9f08's actual classify/frame/comb helpers unchanged.
Measured field-1 (top,bottom) starts (23,260), then (24,260). Both paths classify
the onset TOP_ONLY; feedback substitutes top 23, retaining all other features.
Three independently reset continuations at synthetic unit 102 decide the issue:

- (25,261): baseline VALID_MOVE becomes NOT_IN_TANDEM under feedback.
- (24,261): baseline BOTTOM_ONLY becomes VALID_MOVE; comb_ran changes 1 -> 0.
- (24,260): baseline NOTHING becomes TOP_ONLY; comb_ran changes 0 -> 1.

The bottom profile has an actual qualifying newly-lit row on the bottom-step
cases; this does not bypass the classifier's blanking-change check. Flat rasters
make the comb abstain (margin 1), so none of this is a changed comb estimator or
an audit-only adoption. Normal, ASan/UBSan and TSan versions all reproduce the
three named failures with exit 1, no sanitizer warnings. Keeping the measured
comparison series instead restores top 24 on the very next repeated unit; it
does not provide the predicted run suppression.

Changing no classifier or trigger code does not guarantee unchanged results:
the input history is different. Raw and interpreted classes could both be logged,
but reporting unchanged raw counts would not establish unchanged interpreted
classes or comb timing. No shadow baseline trigger engine was invented.

Production code, defaults and schema remain at d5c9f08. No new control or sidecar
columns installed. If feedback is authorized despite these effects, preserve
measured f1_first/f2_first and add separately named interpreted tops; do not
overwrite observation columns. Feedback is the natural choice for suppressing
the full run, but requires relaxing the unchanged-class/comb-timing conditions.
Owner direction is required before choosing that over measured-series onset-only
suppression. Whole-tape/capture-1 changes, costs, edge gate and agreement bands
were not run after this preflight falsifier; none are claimed.

Probe and verbatim results: /private/tmp/top-only-preflight.PID5U7/probe.c and
REPORT.md. Documentation-only preflight, no push or render.

### Authoritative narrowing received after the preflight

The owner replaced the broad rule with GE_TOP_ONLY **and** a newly selected
top near the derived horizontal-blanking level. A briefly proposed coherence
condition and its worked example were explicitly withdrawn; neither is part
of the task. The stated level instrument is body p95 minus the same field's
derived horizontal level. That is consistent with the existing amplitude test;
no alternative metric or fitted threshold is proposed. The requested new
threshold control must default to an explicit disabled state, preserving
d5c9f08 until a sweep selects an enabled arm.

The synthetic results above concern the original broad-rule preflight, not a
measured reach or rejection rate for the narrowed rule. No threshold or census
test for the narrowed predicate has been run. Conditional eligibility reduces
where a substitution happens; whenever one does happen, feedback can still
change later classifications and comb triggers. The latest rule retains the
old invariance requirements without explicitly resolving that series question.
Requested direction: may enabled-arm interpreted-history effects be measured
and reported rather than required to be zero? Disabled-default identity is
separate and remains required. No production edits made while this is unresolved.
