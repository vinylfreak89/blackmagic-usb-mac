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

### Amendment — interpreted feedback authorized; disabled confidence instrument

The owner has now authorized interpreted history and explicitly withdrawn the
class-count/comb-scheduling invariants for enabled arms: those changes must be
reported, not hidden or forced to zero. The narrowed physical premise is that
a top-only move barely above horizontal blanking is weak evidence of movement.
Whether rejecting such moves improves source registration remains unmeasured;
no nearness threshold has been selected or fitted.

Implement `GE_TOP_NEAR_BLANK`, default -1 (explicitly disabled), with finite
nonnegative values enabling an inclusive cutoff on measured final-top body p95
minus that field's derived horizontal level. Only GE_TOP_ONLY can be ignored;
an unavailable top is never filled. Preserve measured tops and record separate
interpreted tops, measured distances and ignore flags. Interpreted tops feed
the next comparison and the existing placement logic. No coherence condition.

Deciding method: synthetic C-engine transitions exercise the conjunction,
threshold boundary, repeated-run feedback, genuine bottom/tandem moves, no-top
abstention, reset/gaps and reversed ownership. Whole-tape and capture-1 runs
compare the disabled default with d5c9f08, including classifications, scheduling,
placements and all protected measurement columns; measure thread CPU cost.
Falsifier: any disabled-default difference, protected-feature change, mistaken
predicate/ownership, or suppression across missing history. Enabled tape-arm
edge-gate outcomes are deliberately deferred to the requested threshold sweep;
synthetic thresholds establish mechanism only. Report all default bands and
class/scheduling deltas, and never call the disabled result an improved edge gate.

### Report — disabled instrument implemented; source-quality premise still unknown

The mechanism and disabled-default compatibility hold. A single whole-tape read
fed the actual d5c9f08 and new C engines the same units, live resets and pairing
schedule. Every existing non-timing census column and class matches on all
86,293 units; every existing frame column matches on 86,289 woven frames.
Protected bottom/profile/blanking/level/column measurements are unchanged.
All four labelled counters retain their measured and interpreted tops. Capture 1
also has no changed census or placements; its real replay matches every existing
sidecar cell except schema version. This is not a claim that capture 1 is fixed.

The default cutoff remains -1; no enabled tape threshold was selected. Therefore
default class counts, comb scheduling and all agreement bands have zero changes,
and no independent edge-gate improvement is claimed. Full counts, abstentions,
bands and timing live in /private/tmp/near-blank-engine.El72pK/. Measured thread
CPU remains below the engine budget. The owner's physical premise is **unknown**
pending his threshold sweep and independent late-top gate, not held by identity.

Enabled synthetic tests establish an inclusive p95-level cutoff, immutable
measurements, repeated-run suppression, bright/missing-top handling, resets,
gaps and both pairings; enabled real-replay fixtures verify frame-owned provenance
and unchanged audit semantics. The formerly forbidden unit-102 bottom-only to
valid-move transition (comb 1 to 0) is now a passing mechanism control. Mutations
removing nearness, restoring measured history or overwriting observations each
fail the deciding assertions. Unit and sanitizer results are recorded in scratch.
No shadow classifier, coherence condition, comb override, push or render added.

## E-codex-2026-09-22-3 — aperture-overrun refusal: coordinate preflight

**Owner's question (entry 32, relayed).** "If the picture shifts up, you lose
nothing at the bottom but you do lose picture at the top and you create an
artificial jump." Refuse a top move gaining no picture and increasing bottom
overrun; verify the aperture assumption before building, without a fitted number.

**Premise to check first.** The proposed `max(0, first + H - 1 - last)`
describes the actual crop overrun. This requires both the correct height and the
correct start coordinate: measured first, interpreted first and comb-adjusted
published start need not be interchangeable. Near-blank suppression stays off.

**Method/material.** Inspect the current C publisher and review renderer, and
cross-check complete engine rows already obtained from the 9ed3923-compatible
whole-tape run. Use frame_d1/d2 and the proper frame-top unit under reversed
pairing. Exercise the actual C publisher on a synthetic row ruler at an observed
placement, verifying first/last sampled rows without programme content. The
renderer adds three lines above the 480i crop, so compare its endpoint too.

**Falsifier.** A reported first-line-based overrun differs from the actual
published aperture for a deciding frame, or replacing an interpreted top does
not ensure the stated crop action. If found, report the coordinate mismatch
before implementing a rule based on the stronger physical claim. Do not silently
move the guard after the comb or redefine previous applied top. If coordinates
hold, proceed with the specified disabled control and enabled acceptance runs;
independent edge-gate scoring remains with the other agent.

### Report — stopped at census-versus-published coordinate mismatch

**Verdict: the first-line formula is not generally the published-aperture
overrun.** The publisher height is indeed 240, starting at NTSC 23+d1 / 286+d2.
The review renderer is 243 lines per field, starting three lines earlier at
20+d1 / 283+d2. Both end at 262+d1 / 525+d2. The review-height difference
therefore does not change the bottom-overrun arithmetic when offsets are used.

The deciding mismatch is the start, not the height. Existing 9ed3923-compatible
engine output, correctly keyed by frame_top_unit under reversed pairing:
frame 4758 uses field 1 of unit 4759, measured/interpreted top 28, last 261,
frame_d1=1, so actual 480i start 24 and end 263. First-based overrun is 6;
actual overrun is 2. Frame 4757 also publishes start 24: the measured jump
23 to 28 produces no crop jump. Conversely frames 4747 to 4748 retain measured
top 23 and last 261, but published start moves 23 to 24 and overrun 1 to 2.
The literal first-based rule sees no increasing overrun there.

A synthetic row ruler through the actual C publisher and current review
renderer independently confirms the endpoints. Both checks exit 0 with no
runtime errors; the geometric identity being tested is false. This does not
refute usefulness of an interpreted-census guard, but it refutes treating it
as a guarantee on the final crop. The comb can subsequently move field 1.

No production change, new control, fitted threshold, acceptance sweep, push or
render. GE_TOP_NEAR_BLANK remains -1 by default. Ask whether the rule is an
interpreted-census veto before comb (without the final-aperture guarantee), or
a published-crop veto after comb (which changes the specified interaction with
comb). Detailed probes: /private/tmp/overrun-preflight.Xguwut/check.py and
row_ruler.c. Whole-tape enabled changes, cascade, bands, cost and independent
gate remain unmeasured because the requested preflight stop condition fired.

### Amendment — census veto explicitly authorized, without final-crop guarantee

The owner selected the pre-comb census policy after accepting the coordinate
finding. Use H=240 (publisher geometry), not the renderer's 243. The signal
premise to test is now narrower: rejecting these census moves may preserve more
picture without overriding comb. It does not guarantee the final crop.

Implement `GE_TOP_OVERRUN_VETO`, a strict 0/1 tool setting / corresponding C
global, default 0. Compare this measured top to the previous interpreted top;
compare `max(0, current_first+239-current_last)` with
`max(0, previous_interpreted_first+239-previous_last)`. Each overrun uses its
own unit's measured last line, so a tandem translation need not increase it.
Both tops and last lines must exist, on adjacent non-reset units. The two
conditions are nondecreasing top and strictly increased overrun. Substitute
only the interpreted top; keep all observations and comb authority unchanged.
Record the veto predicate separately from actual substitutions: equal tops
can satisfy the predicate when the bottom moves, but substitute nothing.
Near-blank suppression stays disabled in all source runs.

Deciding tests cover predicate boundaries, tandem movement, missing evidence,
reset/gaps, interpreted history and downstream comb authority. Stream actual
9ed3923, disabled and enabled C engines in one whole-tape read with live resets
and pairing. Report all changed census and published field edges, class and comb
scheduling deltas, protected measurements and CPU cost. Define both census and
published-edge cascade ratios per actual substitution; also count no-op matches.
Check the four labelled units and all comb bands including separate gains/losses.
Repeat capture 1. Disabled identity or protected-evidence failures invalidate the
implementation; label or agreement regressions falsify the source acceptance,
and are reported without tuning. The independent late-top gate remains external.

### Report — census mechanism implemented; independent edge verdict pending

Disabled identity holds against 9ed3923 on all 86,293 units and 86,289 woven
frames. Enabled processing preserves every protected measurement and the four
labelled units, and has no comb-agreement losses in any requested band, with
or without the counter-90300 cutoff. The independent gate has not yet judged
these changes: the physical premise of preserving more true picture remains
**unknown**, not proved by comb agreement.

Interpreted feedback has substantial downstream effects. Whole tape: 30,214
actual census refusals, 21,231 changed published field placements; capture 1:
371 refusals, 714 changed published field placements. The direct census ratio
is 1 in both; published-placement ratios are about 0.703 and 1.925 respectively.
Thus capture 1 is not a one-for-one downstream change, and is not called fixed.
Equal-top predicate matches are counted separately. Full before/after class
transitions, comb scheduling, unchanged observations, costs, band gains/losses
and changed-unit tables are in /private/tmp/census-overrun.Z7dxX8/.
The durable numerical report is [census_overrun_acceptance.md](census_overrun_acceptance.md).

The default remains off; no threshold was added. Synthetic tests decide both
predicate terms, zero-clipped overrun, tandem translation, missing measurements,
no-op accounting, interpreted history, resets/gaps, both pairings and preserved
downstream comb authority. Removing either conjunct or restoring measured history
fails the controls. Unit, ASan/UBSan and TSan checks pass. Capture-1 real replay
matches the disabled baseline and enabled probe placements. No push or render.

## E-codex-2026-09-22-4 — applied common-mode precondition: causality preflight

**Owner's instruction (relayed).** "Have codex fix the engine so that it only
considers moves when there is a common mode shift." The dispatch defines this
as both frame-applied offsets stepping by the same nonzero amount from the
previous frame, while retaining a census veto before the comb. It explicitly
asks for a stop if the applied reading cannot be evaluated there, rather than
silently substituting measured-top movement.

**Premise to check.** The current applied pair is available, or determined
without downstream choices, at the existing pre-comb census interpretation.
That computational premise is separate from the untested physical claim that
restricting to common-mode proposals preserves more useful picture. A late-top
gate that abstains on early tops cannot establish the latter claim.

**Method/material.** Inspect b1ce11a's actual C call order, then exercise its
frame decision with synthetic feature pairs and known-answer synthetic comb
rasters. Compare the census candidate, comb-resolved candidate, and any
census-vetoed result from identical entering state. Trace actual reversed
ge_push calls to establish when each field's frame decision exists. Existing
whole-tape disabled frame/unit CSVs may supply additional deciding counters;
they are engine evidence, not raw-row labels. No full-tape reread or source
quality claim is needed for this preflight.

**Falsifier / stop.** A pre-comb candidate and the actual applied pair differ in
common-mode status, or a field's decision requires a later unit. Report the
dependency and ask which candidate is meant before adding a speculative frame
pass or relocating the veto. Do not silently gate on a measured pair, stale
previous movement, or a new post-comb veto. Keep all production code and defaults
unchanged unless this preflight establishes the requested condition directly.

### Report — current applied pair is downstream; preview policy needed

**Verdict: the direct-availability premise is refuted.** The previous applied
pair is available, but the current one is assigned only after frame policy and
any triggered comb. A deciding actual-C probe starts at (0,0), proposes census
(1,1), and a decided -1 comb publishes (2,1): only the census proposal is common
mode. With decided comb 0 the no-veto result is (1,1), but a census refusal makes
the final result (0,0): proposed and final common-mode predicates differ too.
Reversed ge_push confirms a unit's field 2 decision awaits the next unit, while
its field 1 participates in the current completed frame. Existing real engine
rows also exhibit both directions of measured/applied disagreement.

Production code and defaults remain unchanged; no acceptance sweep, push or
render. The common-mode restriction's physical premise remains unknown, and the
late-top gate's early-top abstentions are not evidence of quality. A no-veto
frame preview followed by census rejection and finalization from original state
is a possible implementation, but needs an explicit policy decision. Do not
silently substitute measured tops, previous movement, or a final-crop veto.
Detailed evidence and probes: /private/tmp/common-mode-preflight.TXzoHq/.
Ordinary C, ASan/UBSan, TSan and the existing-row cross-check exit 0 without
runtime errors; the failed premise is a policy-data dependency, not a test crash.

### Superseding instruction — unchanged audit-comb shift, not applied movement

The owner now specifies equal current/previous frame comb_d together with a top
move and stationary bottom, plus the existing census-overrun predicate. The
applied-pair condition is withdrawn; no preview-and-rewind implementation is
authorized. Inspection finds that the current audit result is still computed
after census interpretation, and only for triggered or audit frames. Therefore
the dispatch's explicit availability stop condition applies. No new experiment
or engine change was performed.

This is an ordering issue, not the earlier applied-placement dependency:
ge_comb reads only rasters and can be computed before census interpretation
once both frame fields exist. Reversed pairing requires frame-owned timing;
the current unit's field 2 still awaits the next unit. An enabled rule needs
every-frame computation independently of the optional audit flag to preserve
audit/production equivalence. Ask authorization for that early computation and
timing change, not for a no-veto placement preview. Equal comb winners measure
unchanged relative alignment; they do not by themselves establish absolute
common-mode movement or correct picture edges. Source acceptance remains unknown.

### Amendment — early raster-only comb and frame-owned gating authorized

Build the enabled path only: compute ge_comb once per completed frame before
census interpretation, independently of audit logging. Retain the old disabled
path and scheduling exactly. No preview/rewind, no confidence cutoff, no new
threshold. Equal successive comb winners mean unchanged estimated relative
alignment, not established absolute common-mode movement.

For each frame field with adjacent non-reset source history, require all of:
current comb shift equals previous frame's; measured top differs from previous
interpreted top; measured bottom[k] equals previous bottom[k]; and the existing
non-gaining/increasing-overrun census predicate using last[k] and H=240. Missing
top/last/bottom or preceding comb history cannot fire. Frame-owned history uses
field 1 of c+1 and field 2 of c under reversed pairing; no field-2 decision before
that partner exists. Reuse early comb evidence for the final decision, without
changing what comb_ran means (triggered adoption eligibility).

Log the independent term bits and preceding comb evidence, so removals can be
counted separately and with all other terms retained, on the same interpreted
trajectory. Also report reach if both successive margins meet 1.5/3/5/8; these
are descriptive cuts, not additional policies. Compare against b1ce11a's enabled
outputs, separating overlap from trajectory-created firings.

Before source acceptance, decide synthetic conjunct failures, no-comb-history,
low-confidence equal winners, reset/gap, reversed pending/boundary ownership,
and audit invariance. Stream the whole tape once to actual baseline, disabled,
and enabled C engines. Compare every old unit/frame column, including non-audit
comb scheduling/evidence, against 9ed3923; protected measurements must not change.
Measure all four captures, labelled units, placement changes, cascade, class and
scheduling deltas, band gains/losses, and separate enabled/disabled CPU cost.
Failures are reported without tuning. A lower late-top wrong count cannot prove
quality because that independent gate abstains on too-early tops. No push/render.

### Report — early-comb-gated census veto

Implementation premise held on the committed population: the disabled engine
matches 9ed3923, including non-audit scheduling/evidence and placements. Enabled
frame-owned interpretation preserves raw measurements and audit invariance;
reversed field 2 waits for its real partner. The one existing early search is
reused for the final policy, with no duplicate pass or disabled-path search.
The four labelled units remain unchanged. Synthetic conjunct mutations fail,
and unit, ASan/UBSan and TSan checks pass. An initial fixture assertion failed
because its claimed unchanged-comb rasters were not identical inside the search
aperture; the corrected fixture, not a relaxed production rule, passes.

Source-quality premise remains **unknown**. Aggregate decided-comb agreement
improves or ties in every requested band, but individual new disagreements
remain, including at margin >=3. No tuning or confidence threshold was added.
The restriction removes most old unconditional refusals; the recorded class,
scheduling and placement changes are consequences, not evidence of quality.
Equal raster-only winners establish unchanged estimated relative alignment,
not absolute motion or correct edges. The independent gate has not been
rescored; its blindness to early tops prevents a lower wrong count from proving
preserved picture. Raw-row/owner review is still required before acceptance.

The whole tape was streamed through three actual C engines with the existing
live reset/pair schedule, not re-replayed through the full frameserver. The four
captures additionally passed enabled and disabled real frameserver replays.
Detailed populations, abstentions, separate gains/losses, firing identities,
per-term and descriptive confidence cuts, cost and the verbatim fixture failure
are in /private/tmp/comb-gated-overrun.6bHuEz/REPORT.md, with scripts and changed
unit/frame CSVs beside it. Rule remains disabled by default. No push or render.

## E-codex-2026-09-22 — delete superseded veto instruments

Owner: "scrap whatever veto work is going on because its not right... actually
delete it out of the engine". Remove both near-blank and overrun substitution,
their controls, early comb path, interpreted history and schema columns. Keep
the d5c9f08 top rule and its four comparison controls. No replacement policy.

Premise: removing default-disabled instruments changes no retained measurement,
placement or comb scheduling/evidence. This is a code-identity claim, not a new
claim about source geometry. Delete rather than retain dormant implementations;
use a new schema version to identify the smaller sidecar explicitly.

Deciding method: stream the whole tape and all four captures into actual C
engines built from pristine d5c9f08/c620966 and the new source. Compare all
retained measurements and audit/production decisions, including exact comb
energies and margins, triggers and source-owned offsets. Compare new defaults
with d5c9f08 and the retained (0,0,1,1) arm with c620966. Reuse the recorded live
reset/pair schedule and separately check frameserver integration. Falsifier:
any differing retained value on any eligible unit/frame, or a removed policy
still reachable. Run unit, ASan/UBSan and TSan checks; report errors verbatim.
Material: all 86,293 exact whole-tape units and all eligible units of captures
1–4, including reversed pairing in capture 3. Results remain in scratch.

### Report — veto deletion

Identity premise **held** on the complete committed population: all retained
measurements and production/audit decisions match d5c9f08 at defaults and
c620966 under the explicit old arm. Exact profile bytes and all comb energy/
margin bits were checked, not merely rounded CSV values. The removed policies
are absent from engine code, tool parsing, sidecar schema and active tests;
their history is recoverable from prior commits. No replacement is introduced.
The schema advances to 20 while returning to the retained schema-16 columns.
This is identity evidence only, not a new claim about picture quality.
Unit, ASan/UBSan and TSan checks pass. Full counts, methodology, CPU costs and
test logs are in
/private/tmp/remove-veto.LwcnlH/REPORT.md. No push or render.
