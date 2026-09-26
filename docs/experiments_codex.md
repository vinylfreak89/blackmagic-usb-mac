# Codex experiment commitments

Commitments precede deciding tests, per CLAUDE.md §14. Append entries, amendments
and verdicts; keep code, labels, panels and detailed results in scratch.

## E-codex-2026-09-19-1 — surviving fragments in torn top rows

**Question (owner, relayed 2026-09-19):** "What is the census in the 4 caps
where the first line of real picture is" — every valid unit. This experiment
addresses the unresolved capture-4 field-2 census, not a replacement engine.

**Premise.** A torn first picture row retains a fragment of the scene that
continues into a lower picture row, although whole-row correlation is poor.
That fragment can distinguish it from source-carried data waveforms. This is
a testable local-continuation hypothesis, not a fact about all picture/data.

**Method, fixed before the test.** For each candidate NTSC line 285–303,
divide its 720 delivered samples into four non-overlapping 180-sample pieces.
Compare each piece by Pearson correlation with every 180-sample contiguous
window in the row four field lines below it, within the same raw field/unit.
The maximum correlation is the sole score. A score >=0.90 accepts the row as
picture; zero-variance comparisons supply no evidence. The first accepted row
is the candidate top; if none qualifies, abstain. No amplitude gate, temporal
carry, comb, caption decoder, or additional veto. The 180-sample window,
four-line comparison distance, 0.90 cutoff and bounded top search are authored
experiment settings, not owner rules or measured signal constants. They will
not be tuned after observing the result.

**Independent observation.** Before computing candidate scores, inspect raw
line strips including preceding and following lines for all 650 capture-4
units. Record a first-visible-picture label or an explicit uncertainty/bound;
a partial picture line counts. Inspect each label bin and candidate bin on raw
rows, including rare cases. Labels describe visible evidence, not an assumed
nominal source top. Claude's census and the candidate scores are not labels.

**Falsifier.** A raw-confirmed picture row rejected, a raw-confirmed data row
accepted, or a candidate top contradicted by preceding raw rows refutes this
method as a complete separator. Report both error directions and abstentions;
failure does not establish that no simple separator exists. Do not repair the
failure with another clause in this entry. A complete raw census is not claimed
if any units remain unlabelled or ambiguous.

**Material.** Supplied luma caches and counters under the session's
`scratchpad/geometry_exp1/cache/`, all 650 capture-4 units 171–820, field 2
in its original slot (no pairing or geometric repair). Previously identified
hard examples: 204, 259, 331, 335, 809, 810; the other 644 units are not used
to choose settings. Source-data controls, raw-labelled before scores: capture
2 counters 67446, 67608, 67654, 67770, 67932, 68094, NTSC 23/24/286/287;
capture 3 counters 13501, 13502, 13601, 13701, 13801, 13901, 14001, 14101,
14149, NTSC 23. These coordinates name inspection sites, not unconditional
data labels: picture at a named site must be labelled picture. Capture-2
stored counters are extended by 65536. Captures 1 (>=6667) and 2–3 remain
reference material; no new full census of those captures is claimed here.

**Provenance.** Preconditions checked: all four caches/counter arrays and
census CSVs, `census.py`, `explore/bins_cap4.png`, and Claude's entry/report
are present. Prior census is E-claude-2026-09-19-2 (entry fdb89c2, report
f71fedd), read from the Documents checkout. This experiment's code, labels,
checks and detailed report go in `/private/tmp/codex-torn-top.rSVrxF/`.

### Report (2026-09-19) — separator refuted; raw census has abstentions

The unchanged rule rejects definite torn picture (capture 4, 204/286) and
accepts definite data (capture 2, 67446/23 and /286, 67932/286). No numerical
amendments or additional clauses. A lower cutoff cannot separate these rows
on this score; this does not rule out a different simple observable.

Raw census, every unit inspected: 559 first at 286, 64 at 287, 27 unresolved
between them. The earlier frozen 586/64 visual labels were overconfident:
enlarged error review exposed faint rows missed in overview strips. All 650
were re-audited at larger scale; the 27 remain unknown, not relabelled from the
candidate. Against 623 definite labels: 184 exact tops, 439 misses; 27 unscored.
Data controls: 27/30 rejected, three false acceptances. Five instrument controls
and six independent real-row Pearson checks pass. This is not a fully blind
validation or a completed 650-unit census. Detailed report, individual labels,
bin checks and the retained original artifacts: the scratch path above,
`REPORT.md`. No engine change; unresolved faint-row identity needs review.

## E-codex-2026-09-19-2 — what the data-line entropy counts

**Question (owner, 2026-09-19).** "Why do the data lines come out as high
entropy. They are only 2 codes plus a sinusoidal ramp all within a noise band.
Why would that be high entropy?" Reasoning audit, not a detector proposal.

**Premise.** A two-level underlying signal does not imply two delivered luma
codes: plateau variation and sampled transitions populate additional codes.
The histogram entropy measures this marginal distribution, not temporal
waveform complexity. Ordered transitions can contribute substantial histogram
entropy without being unpredictable. This does not imply every data row is
less temporally unpredictable than every picture row.

**Method, committed before the deciding run.** Recompute Shannon entropy on
the exact 640 samples `[40:680]`, check agreement with `exp4_rows.csv`, and
inspect numerical traces/histograms without programme content. For explicit
histogram accounting, find the modal code on each side of the midpoint of
the 5th and 95th percentiles; partition codes into bands around those two
modes and the remainder. Use authored half-widths 1, 3 and 5 codes, reporting
all three, not selecting one for separation. Decompose entropy by the chain
rule into low/high occupancy, within-band variation, remainder occupancy and
within-remainder variation. These are exact code-bin contributions, NOT an
identified physical noise/ramp separation. Inspect a fixed row (capture 2,
67446/286) and the data row closest to the population median; where a temporal
trace supports plateau/ramp annotations, record those intervals explicitly
before their entropy accounting, and include conditional-label ambiguity.
Do not force an ambiguous physical decomposition.

As reasoning controls, shuffle each examined row (seed 20260919): histogram
entropy must be unchanged. Compute first-order empirical conditional entropy
of adjacent samples at code bin widths 1, 4 and 8, alongside shuffled values;
these authored diagnostic resolutions are not thresholds or a classifier.
Report finite-sample/sparse-context limitations and counterexamples, not a
claimed entropy-rate estimate or noise model. No fitting a waveform decoder.

**Falsifier.** Histogram disagreement falsifies reproduction; shuffle changing
histogram entropy falsifies the instrument. A substantial residual in entropy
accounting falsifies the decomposition. Traces lacking distinguishable
plateaus/ramps defeat physical attribution. A picture row with lower temporal
conditional entropy than data defeats a universal low-data/high-picture
reading of that statistic. No detector amendment follows such a result.

**Material and labels.** All supplied caches and the original `exp4.py`, CSV
and E-claude-2026-09-19-4 report are present. Audit capture-2 top rows marked
non-picture in that CSV, NTSC 23/24/286/287, counters 67446–68094; labels are
Claude's census labels, not independent truth for the whole population.
Fixed raw checks: capture 2 counters 67446, 67654 and 68094 at those four
lines; capture 3 counters 13501 and 14101 at 23/24; capture 1 counters 6700,
6731 and 6760 at 23/24; capture 4 counters 204 and 335 at 286/287. Inspect
these and retain uncertainty instead of calling every named site data.
Results and scripts stay in a new `/private/tmp/codex-entropy-*` directory;
only this entry and its verdict are committed locally.

### Report (2026-09-19) — histogram explanation holds; class ordering does not

Reproduced all 44,889 CSV entropies exactly. The 2,318 selected data rows have
median 4.845668 bits; quoted 4.3–5.4 is p10–p90, not the full range. The
median example (cap2 67654/24) contains 87 codes. Explicit temporal accounting
attributes 2.532 bits to variation within low/high regions and 1.444 to rounded
pulses/transitions; occupancy and overlap complete 4.845566. This is descriptive,
not physical noise attribution: baseline drift, waveform distortion and noise
are not separately identified. A second row (67446/286) gets most of its
entropy from within-region variation, not sharp edges. All three precommitted
code-band widths reconstruct total entropy but change its attribution.

Shuffling all 26 fixed raw rows preserves histogram entropy exactly. Keeping
sample order lowers empirical conditional entropy, but picture does too:
cap1 6700/23 and cap4 204/286 are below the median data example at all three
resolutions. Universal low-data/high-picture conditional ordering is refuted;
no claim about a validated waveform-conditioned model follows. Five synthetic
controls pass; temporal accounting includes overlapping phase/code values.
No amendments or detector. Population labels remain inherited; raw checks are
the fixed sites, not independent whole-population truth. Detailed accounting,
traces, limitations and every authored choice: `/private/tmp/codex-entropy-LY1FcP/REPORT.md`.

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

## E-codex-2026-09-22 — waveform top search, entry 33 build

Owner: "I think this is the engine we want codex to build. and see it against a
real render. cap 1-4 first, then once I validate those, the full tape."
This implements E-claude-2026-09-22-33, not a new signal hypothesis: the first
single-line rise in adjacent-row waveform correlation identifies the top line.
The physical premise remains subject to raw-row/render judgement; eleven labels
do not establish a distribution-derived bar or general accuracy.

Stage one introduces a C scan alongside the unchanged old search. Pearson uses
body samples 40..679, each row against its predecessor, storage rows 18..36 plus
263 per field. First consecutive-correlation difference strictly greater than
the bar (default 0.45) chooses the preceding line. Zero-variance correlations
are zero. The dispatch and authoritative step_tape.py scan() use strict >,
which takes precedence over the ledger's >= wording. No smoothing, chunking,
largest-step selection, level or spread gate participates in this scan.

Compare every raw top/abstention against /private/tmp/wave-engine/step_tape.csv
on all 86,293 exact whole-tape units; report every counter/field disagreement.
Also compare recorded selected/max steps at their supplied precision, without
using rounded steps to decide a top. Synthetic tests distinguish first from
largest, strict comparison, constant rows and both field coordinates.
Falsifier: any unexplained census disagreement. No removal or render before the
measurement gate passes. Read scan(), not waveform.py's superseded first_top().

Only after that gate, remove the obsolete top guards and promote the C scan.
Expose the step bar and symmetric nominal-line clamp (default 5) as tool startup
controls. Preserve raw results separately from accepted census edges: no step
means abstain; out-of-range means discard, never clamp-to-boundary. Missing
census evidence continues to request the existing decided-comb check (>=1.5).
Relative comb evidence cannot supply an absolute field-2 anchor: any existing
section-start/previous-placement fallback must be explicitly identified in the
sidecar, not relabelled as a measured top. No new comb/adoption rule is proposed.

Recheck the integrated census and exact bottom edges, bottom coordinates,
profiles and device blanking against a05ad82, and cost CPU median/p95 under
§11b. Confirm the four labelled units and report the clamp's unexercised negative
side honestly. Run unit and sanitizer tests. Then generate only captures 1–4
with their own engine sidecars and engine-derived overlays, validate in scratch
before publication. The full-tape render awaits owner validation; it is not
authorized by passing the numeric census gate alone.

Stage-one result (before removal of the old search): 86,293 units, 172,586
edges, 172,586 exact top/abstention matches, zero disagreements. Selected/max
steps match the census's four-decimal precision (maximum difference
0.00005019797050032082). Geometry unit suite and standalone waveform ASan/UBSan
and TSan pass. Evidence: /private/tmp/waveform-engine.5I96wG/scan_summary.json
and disagreements.csv (header only).

Population correction, independently recounted from the reference itself:
1,369 clamp-discard units counts only the 74,202 units with BOTH raw tops.
Across all 86,293 units, 2,223 have at least one out-of-range edge (2,658 edges).
The stated 5,654 field-1 tops >=26 counts only units where BOTH tops survive;
the per-field survivor count is 5,963. Apply the specified clamp independently
to each field; do not discard the valid partner of an absent/discarded edge.
Raw placed/abstained counts remain 155,364/17,222. Negative offsets are not
exercised by this tape (observed raw offsets 0..16 in both fields).

Promotion result: integrated scan again matches 172,586/172,586 raw edges;
post-clamp policy differences zero. The four labelled units retain the required
26/26/25/26 and 288 tops. Old top guards are removed only after the standalone
gate. Schema 21 carries unit-owned raw top/step/max/status and frame-owned
accepted census, relative/anchor source and held correction. Defaults are
GE_WAVE_BAR=.45 and GE_WAVE_CLAMP=5; retired commands are rejected.
Exact protected-feature comparison against a05ad82 (its geometry C/header are
identical to the compiled d5c9f08 baseline) found zero bottom-edge, profile,
device-blanking, bottom-coordinate or horizontal-reference differences across
86,293 units and captures 1–4 (919/649/649/650). Thread-CPU whole-engine median/
p95 is 0.309083/0.8916418 ms per unit, production scheduling with the same live
reset/pairing stream; measurement alone 0.065667/0.159917 ms. Native unit,
frameserver, ASan/UBSan and TSan checks pass. Numeric success authorizes the
four review renders, not a full-tape render or an assertion of picture quality.

Review-render integration uses the already reviewed renderer at 948a06e plus
schema-21 evidence labels. Corrected its reversed-pair census lookup: accepted
first/last columns are frame-owned on the bottom unit, whereas raw waveform
columns are unit-owned. It now prints the engine's held correction rather than
inferring one by subtraction. Missing answers do not borrow manual edges.
Synthetic ownership/status tests and all retained audio-placement probes pass.
Real replays have zero drops and zero per-unit raw/accepted census differences;
MP4 readback matches all 919/649/648/650 frame placements (three extra fill
slots in capture 1), with zero missing frames or strip differences. The four
review files and their own sidecars replace only the owner's geometry_renders
scratch copies after validation; prior copies are recoverable in the run's
backup directory. Full-tape rendering awaits owner validation.

Count reconciliation: capture 3's 649 published units include tail boundary
14149 (f2_unused=1, no frame_top_unit). Encoded frames are exactly 13501..14148,
648 consecutive frame keys, and the last uses field 1 of 14149. Fresh strip
readback found zero missing interior frames, sequence errors or source-placement
differences; no re-encode or sidecar edit is needed. The prior report should
have stated this denominator distinction. Added producer-named, hash-backed
renders.status validation so stale status cannot stand for the replacement run.

## E-codex-2026-09-22 — entry 34 rejection-power implementation gate

Owner-authorized premise (E-claude-2026-09-22-34): a near-tied best and runner-up
can still exclude a much higher-energy proposed placement. Test the proposed
shift's energy against the minimum, separately from the existing >=1.5 selection
margin. Strict ratio >GE_COMB_REJECT (default 2) substitutes the best and clears
held correction, provisional confirmation and correction basis. Do not change
the census, comb energies, or decided definition. No new comb scheduling:
comb_ran denotes a triggered search; audit alone remains observational. All 26
reported candidates are triggered searches, as independently recounted.

Before publication/render, run the actual C state path against the same rasters,
pairing and live reset stream. The static 26-row count does not establish that
later placements are invariant after dropping state and publishing a new shift.
Falsifiers: any extra/missing changed frame, worse independently measured woven
roughness on a target, census differences or label failure. Preserve and report
a failed gate rather than tune around it. Explicitly settle zero-energy ratios
and proposed shifts outside the eleven measured candidates; do not index outside
the array or silently claim an energy the comb never measured.
If gates pass, add separate refusal evidence/provenance, test strict thresholds,
audit invariance and state reset, measure cost and census identity, fix clipped
DIFFERS/ratio labels, then stage/validate/publish only captures 1–4 with producer
status. No full-tape render is authorized.

Entry-34 preflight result: the bounded C prototype changes exactly the 26 target
frames (15/5/2/4), with no extras, no missed targets, and no changed placements
among the 2,100 decided-comb frames. Audit and non-audit placements agree.
There are 23 direct refusals; three other changes propagate through the existing
placement/correction state. Capture 1 counter 6272 consequently publishes +5,
not its current minimum +4: the inherited +5 is only 1.049 times that minimum
and is not itself refused. Do not call all 26 fresh refusals.

The no-worse-roughness gate fails under an independent implementation of the
stated operator, mean abs(line - average(two vertical neighbours)), on the
publisher's 720x480 aperture: cap1 6271 rises 2.103753 to 2.460633, cap1 6272
rises 1.987461 to 2.254934, and cap2 2309 rises 6.296182 to 6.486143.
Both cap1 failures persist on the interior 210-line-per-field / columns 24:696
check; cap2 2309 instead improves there, so aperture matters. The original
entry's precise roughness aperture/code was not supplied and has been requested;
its five example numbers have not been independently reproduced. These are
instrument scores, not a verdict on appearance. All target-source cached rasters
match the original captures byte-for-byte; a separate literal-loop scorer
reproduces the three full-aperture regressions. Evidence and the complete 26-row
table: /private/tmp/comb-reject.HLom5S/roughness.csv, verify_raw.out and
preflight.out. Production engine/renderer changes and new renders are stopped
at this falsifier. Whole-tape identity, CPU and promotion tests were not run;
existing engine, sidecars and review renders remain unchanged.

### Entry 34 amendment — require an enclosed indistinguishable floor

Owner: "isn't the best shift supposed to be a minimum on both sides? otherwise
it shouldn't have any confidence. thats what a real comb does." The committed
Claude amendment at 784d6f2 narrows rejection substitution to an interior floor:
extend contiguously from the best through energies within 1.5 times the minimum,
and require an outward rise of at least the same existing 1.5 factor on both
sides. A floor reaching a search endpoint is unsupported. This is evidence of
a bounded basin, not proof that the true alignment is outside the search range.
No new confidence threshold and no changes to census or selection margin.

Before promotion, run both authorized discard interpretations through the C
state path, not a static table. Prefer holding the last published pair: discarding
a candidate should not adopt a different unsupported candidate from the same
frame. This holds placement, not pixels, and must be labelled as a geometry
discard; at a section start the existing zero placement is the only fallback.
Clearing held correction/provisional/basis remains mandatory on rejection.
Compare the alternate census fallback to expose any policy-dependent propagation.
Do not add an audit-dependent decision path or a new comb search.

Falsifiers: any extra changed frame or decided-frame placement; any of the 21
supported target placements scoring worse on the independently specified full
720x480 roughness; any of the five unsupported targets gaining a substituted
comb shift; census or label differences. Distinguish direct substitutions from
propagated placements. If passed, preserve the four-capture/render gates from
the parent entry, record floor/rises and refusal disposition, cost the built
engine, and render only those captures. A new failure is reported, not tuned.

Amendment result: held on the specified material. Both discard policies were
run forward; they differ only at cap2 2312. Chosen policy holds the prior full
published pair, clears correction state and labels geometry discarded (image
data is still published). The five discards are cap1 6271/6272 and cap2
2309/2311/2312. Exactly the 21 supported target placements improve the 720x480
full-width neighbour-residual mean; zero worsen. Nineteen are direct
substitutions and two (6254/13577) propagate from previous events. Two discards
also change placement by holding the new prior pair: 23 placement changes
total, zero outside the 26 targets, zero among 2,100 decided-comb frames.
No claim is made that all 21 improvement rows contain a fresh refusal event.

The production C engine through real four-capture replays matches the scratch
state prototype exactly, with zero drops. Raw/accepted census, bottoms and
blanking/reference evidence are unchanged on all four captures. Whole-tape
comparison against 47423f3 finds all 86,293 complete ge_features structures
byte-identical, hence 172,586/172,586 raw top/abstention matches; the four labelled
counters still match. Production-scheduled whole-engine thread-CPU median/p95:
0.307667/0.333541 ms per unit; measurement alone 0.0635/0.079875.
Native, ASan/UBSan and TSan checks pass. The initial audit test failed because
its evidence exclusion lacked the new audit-only floor/ratio columns; only
those measured columns were excluded, with all actions/state still exact.
The mutation that ignores basin support fails the discard-state assertion.
Schema 22 appends rejection provenance; no selection threshold, census, search
schedule or audit-adoption change. Evidence: /private/tmp/comb-basin.KlFmop.
This gate authorizes only the four review renders, not full-tape publication.

### Additional owner rule — one accepted field top cannot move the pair

Owner: "no top in 1 field within a frame should be disqualifying to create a
shift". When exactly one frame-owned accepted top exists, retain both offsets
from the previous published frame (or section-start zero). Do not alter either
measurement, comb evidence/scheduling or the both-top case at cap1 6667.
This is additional to the basin amendment. Test with the actual C forward
state: holding 6641 can also change later fallback placements, so the requested
exactly-five changed-frame gate is not established by five moving onsets.
Report any propagation separately and stop on an extra changed frame rather
than silently restoring the rejected anchor. Commit/test this scope before
changing the engine or restarting renders. The first two basin-only encodes
had finished in scratch when the steer arrived; remaining encode processes
were stopped and no MP4/sidecar replacements were published.

One-field scope falsifier: the C prototype changes 31 placements, not five:
cap1 6641..6666 (26), cap2 2338 (1), cap3 13894/13895/13962/13965 (4), cap4
none. The 26 extras are cap1 6642..6666 and cap3 13895. Five old moving onsets
are not five changed output frames after a stateful hold. Cap1 6644 has no top
in either field and inherits the held pair; subsequent one-top frames cannot
legitimately restore the rejected two-line anchor. The rule performs eight
direct hold interventions; the remaining 23 changed placements inherit state.
At cap1 6667 both tops exist (25/291) and the result stays (5,5), relative shift
zero, unchanged from the basin-only engine. No second anchor rule was added.
Production-baseline and audit-invariance checks have zero differences; inputs
and outputs are in /private/tmp/comb-basin.KlFmop/one-field. The one-field rule
remains a scratch prototype pending resolution of the exactly-five gate.
Basin implementation 3a87891 is committed, but no new review files are published.

### Replacement owner rule — all four edges and known motion

Owner: "if you can't measure all 4 tops and bottoms, don't shift shit... period".
This replaces, not extends, the one-field prototype. Retain the previous full
published pair if either current field lacks a first/last edge or either
existing frame-owned motion classification is GE_UNKNOWN. Other measured
classes remain eligible, including top-only, bottom-only and not-in-tandem.
Do not invent a classifier, substitute history, or change census/comb evidence.
At a reset/section start the existing unregistered placement is zero.

Test forward from the basin-only engine, recording actual candidate-to-held
pair interventions and propagated output changes separately. Compare the
reported 20 moving onsets against the current published baseline as well as
the basin-only build: adding rejection can change the set before this gate.
Falsifiers: direct refusals outside the specified 20, a missing specified
refusal, any change not due to the allowed hold/state propagation, or changed
census. Stop at a conflicting gate; do not fit the condition to its counter list.
Renders remain stopped until the replacement rule's acceptance is resolved.

Four-edge replacement result: the C forward prototype performs 32 direct
candidate-to-held interventions (12/3/12/5), not the reported 20. It changes
56 frame placements against the basin-only build (36/3/12/5): 32 direct and
24 inherited changes. Of the listed 20, 18 intervene directly; cap2 2312 is
already held by the basin discard and 2339 becomes a no-op on the changed
trajectory. Fourteen other interventions are startup placements, reattempts
after earlier holds, or the basin rule's newly changed candidates. They are
not a fitted counter exception. Baseline reproduction and audit invariance
remain exact. The implemented predicate reads current first/last and the
existing frame-owned GE_UNKNOWN classes only; other classes are not vetoed.

The predicted persistent freeze does not follow: cap1 6641..6669 stays (0,0),
including 6667, but 6670 has all four measured edges and nothing/nothing
classes and publishes (5,5). No authorized term rejects it. At 6878 the return
is held at (5,5); 6879 returns to (0,0). Thus the instruction delays that shift
three frames rather than eliminating it. Adding a rule against nothing/nothing
or changing classification history would be an unauthorized second rule.
The exactly-20 gate is unresolved; this replacement remains only in scratch
at /private/tmp/comb-basin.KlFmop/four-edge. Neither superseded hold prototype
has been promoted. The basin-only commit remains 3a87891. All eight published
review artifacts still match their previous hashes; no replacement occurred.

### Owner withdrawal of the hold rules — resume basin-only review renders

The owner rejected the four-edge prototype after its scope and persistent-hold
falsifiers. Keep ffa5cce and both scratch prototypes; neither enters production.
Motion classification cannot establish an absolute anchor merely because a
previously measured late top becomes stable. The relayed raw-row explanation
attributes cap1 6667 to a late waveform transition on low-contrast rows, not
the zero-variance guard. That instrument change is explicitly out of scope;
the basin-only placement there remains (5,5).

Authorized work is now the already accepted schema-22 engine and overlay code
at 3a87891, followed by captures 1–4 only. No new rule, scope exception or
full-tape render. Rebuild from the accepted real-replay sidecars, verify every
encoded frame key and both source-unit placements, retain recoverable copies
of the prior eight review artifacts, then publish with a fresh producer-named
renders.status. The earlier hold-rule gates no longer block this publication;
their negative results remain recorded above rather than reverted.

Basin-only publication result: all four encodes completed, with 922/649/648/650
encoded frames and zero frame-sequence or source-unit placement differences.
Capture 1 includes three explicit fills; capture 3 has 649 published units but
648 paired frames, with terminal unit 14149's unused field 2 accounted as a
tail boundary, not an interior loss. All eight files were closed, validated,
backed up by hard link, then replaced by same-filesystem rename; final hashes
and a second strip readback pass agree. geometry_renders/renders.status is
READY, schema 22, naming engine and renderer 3a87891 with visual acceptance
pending. The fixed DIFFERS slot and logged ratio/floor/rise overlay tests pass.
No production code changed during this resumed publication; no hold prototype
was promoted, no push occurred and no full-tape render was made. Backup and
publication manifests remain in /private/tmp/comb-basin.KlFmop.

### Entry 34 whole-tape scale gate before review encoding

Owner authorization relayed with watchdog provenance (line 77096, UUID
d97db69d-1fb8-40f4-a065-d758fff7a3aa, 2026-09-22T11:58:14Z): finish the four
review renders and, if time allows, the full tape. The four are complete.
The four-capture rejection/basin validation does not establish whole-tape
publication behavior; prior whole-tape census identity measures a different
property. Run the unchanged 3a87891 engine with the existing pairing schedule,
audit evidence and 8000-us replay pacing, keeping all growing files in scratch.

Precommitted scale falsifier: render only if actual comb_rejected frame rows
are strictly below 5% of published paired frames and actual geometry discards
are strictly below 2%. Count direct events separately from state propagation;
report substituted/discarded counts, rejected-ratio median/p90/p99/max, and
the no-basin fraction across all frame rows. Verify complete replay accounting,
not only exit status. If either bound fails, report and render nothing. Do not
tune the engine or use the rejected four-edge prototype to pass this gate.

If passed, require adequate free space and same-filesystem publication, render
from the new sidecar, read every encoded placement back against both source-unit
decisions, and publish closed MP4/CSV plus producer-named hashed status. The
known cap1 anchor defect is not part of this task. Evidence for this run lives
in /private/tmp/basin-fulltape.f19Ygq; no new registration rule is authorized.

Scale-gate result: passed on the complete real replay. All 86,293 exact units
were published with zero pool/ring/surface/audio drops; 86,289 are paired frame
rows and four are boundary units. Actual rejection events number 329 (0.3813%):
315 substitute and 14 discard (0.0162%). The no-basin population is 2,457
(2.8474%), not all of which triggers a rejection. An independent streaming
recount and energy-ratio reconstruction find zero differences. Both strict
rate limits hold; this authorizes the whole-tape review encode, not a claim
of visual quality or a correction to the known absolute-anchor defect.

The initial sandboxed replay failed before reading units with "open failed";
the elevated local retry completed normally at the required 8000-us pacing.
Free space after replay is 29.96 GiB. Full statistics, quantile convention,
event identities and accounting remain in the scratch directory above.

Whole-tape review publication completed from engine/renderer 3a87891. The
closed encode contains 86,296 frames (86,289 paired plus seven fills), duration
2879.409867 s. Every encoded counter/placement and both source-unit joins match
the sidecar; zero sequence or placement differences. The independent audio-clock
check bounds the offset by 0.001998002 frame, with only the two expected sample
steps. MP4 and schema-22 sidecar hashes match before and after same-filesystem
rename into captures/. captures/renders.status is READY, names both producer
commits and hashes, and leaves owner visual acceptance pending. The previous
two files are recoverable under /private/tmp/basin-fulltape.f19Ygq/replaced-review.
No engine rule changed and neither rejected hold prototype was promoted.

## E-codex-2026-09-25-36 — validate the vote's reference before promotion

Owner's gates, relayed in entry 36: "First, the comb agreement should IMPROVE
with the geometry agreement. Secondly, I expect less excursions on both the
[top] and bottom and less common mode jumps." The proposed method is a causal
30-confident-frame anchor vote with optional, vote-only level fills; it must
not change the baseline relative decision or waveform census.

Premise to test before implementing: the supplied frame reference expresses
those rules using the correct source field, accepted-versus-abstained status
and reset policy. Independently reconstruct its inputs from the approved tag's
sidecar and the unit-keyed level census. Check reversed-pair source ownership,
discarded waveform results, threshold serialization and section boundaries.
Then, if the definitions agree, port the bounded vote and level measurement to
C, verify all-off identity and the three reference variants, and measure the
owner's gates and CPU cost before any review encoding. Preserve the relative
engine path and keep additional measurements out of its triggers and census.

Falsifier: any reference column depends on a different field's samples or an
unstated policy, any all-off/census/relative invariant differs, or a required
reference variant disagrees. Report deciding counters rather than tuning the
engine to a faulty join. An unresolved interpretation is returned for review;
the specified s1/s12c render stop conditions still apply. Material: the tagged
whole-tape sidecar, reference_anchor.csv and its two level censuses, with raw
source rows used to adjudicate discrepancies; captures 1–4 only after gates.
Scratch evidence: /private/tmp/vote-entry36.aBbP7d. No whole-tape encode.

Preflight verdict: the reference-input premise is refuted; no engine or renderer
change was made. Reconstructing its literal policies matches all seven columns
on all paired frames, but its stage-2 field-1 fill uses the bottom unit instead
of frame_top_unit under reversed pairing. Raw C checks confirm the first
contradiction at frame 4761 (source 4762). It also fills DISCARDED waveform
results although the dispatch says ABSTAIN only (first counter 4766). The
reference carries the vote through resets and the pairing-switch ge_init;
retaining the existing clear-history contract instead changes stage-1 anchors,
first at 48240. That reset policy needs an explicit ruling, so the stage-1-only
render fallback is not yet validated. No quality gate or CPU result is claimed.
Detailed counts, all differences and raw numeric checks are in the scratch
REPORT.md above. No review artifacts were altered; return these definitions
for review rather than tuning the engine to the inconsistent reference.

### Resume under entry 36 amendment 2

The corrected reference resolves ownership, permits ABSTAIN fills only, applies
the shared waveform clamp to level candidates, and explicitly clears the vote
on engine resets. Build those rules with three off-by-default controls and an
independent bounded anchor window. Preserve the original relative decision and
its fallback state; vote-only measurements must never feed that path. Additional
comb evidence is enabled only for the vote and must not adopt untriggered comb
decisions. Test all three variants against reference_anchor2.csv, all-off against
the approved tag, and census/relative invariants before rendering. Unrounded
body statistics use the specified strict thresholds, not the reference CSV's
serialization precision; any discrepancy is reported, not fitted away. The
previous render stop conditions remain. Evidence: /private/tmp/vote-build.zxHiET.

Build verdict: the bounded C vote reproduces every stage-1 reference column;
all-off tag identity, waveform census and relative-shift invariants pass. Each
fill variant has one confidence discrepancy from rounded reference statistics:
32714 has sd 9.997575878 (serialized 10.00); frame 29281's field-1 source 29282
has correlation .300012175 (serialized .3000). Raw checks confirm both. Every
variant's anchor sequence matches; the strict thresholds were not altered.

The named-case falsifier nevertheless fires in capture 1 under both s1 and
s12c: reset 6667 clears the window and the specified cold start republishes
anchor +5 through 6877. Only 27 of the requested 238 frames remain at (0,0).
Real live replays confirm the result; neither the requested render nor its s1
fallback is produced. The 82421..83342 prose claim also overstates the corrected
reference: reset 83330 leaves 13 frames at anchor 0, not +2. The aggregate
movement gates match the reference; they do not erase either named failure.
Controls remain off by default. Unit, ASan and TSan checks pass; complete
counts, timings, discrepancy lists and probes are in the scratch report above.
Existing review artifacts remain untouched. No reset policy or threshold was
tuned to convert these findings into a passing render.

### Amendment 3 — empty-window hold

Owner's premise: "the most often candidate becomes the correction"; no new
candidate does not license the original engine's uncorroborated anchor. Preserve
the last published vote anchor through an empty window, including resets and
pairing changes; only session initialization has no previous publication and
uses the original engine anchor. Reset still removes all old votes. Nothing
changes in the relative engine, census, fill measurements or strict thresholds.
Test against reference_anchor3, allowing only the two documented confidence
serialization discrepancies; require all-off tag identity and relative/census
identity, the named counter intervals and complete capture-1 hold. A remaining
stage-1/reference or named-case failure stops rendering; a fill-only reference
failure permits the specified s1 fallback. Measure CPU, run unit/sanitizer checks,
then validate every encoded placement before publishing captures 1–4. No whole
tape encode. Detailed evidence: /private/tmp/vote-hold.zlY5U0.

Amendment-3 verdict: the empty-window premise holds on the specified gates.
All three anchor sequences match reference 3 exactly; the only confidence
differences are its two acknowledged rounded cells. Tag identity, census and
relative invariants pass. Capture 1 holds (0,0) on all 238 specified frames;
the other named intervals match the corrected reference, including +2 at 48352
and +0 at 81508. The requested s12c reduces common-mode moves/excursions to
29/6 with no one-frame jumps; its geometry-agreement measure is 54.3059%.
These operational gates do not establish independent absolute-picture truth.

Normal, ASan and TSan tests pass, including empty holds through both live
pairing-switch directions and matching streaming-probe behavior. Captures 1–4
were rendered from engine e08b19c and renderer a76eef5, s12c, and published only
after every encoded placement and source-unit join passed. Their frame counts
are 922/649/648/650 with zero differences; capture 3's unit 14149 is the unused
tail boundary, not a lost frame. Status is READY with configuration, producer
commits and hashes; owner visual acceptance remains pending. Previous review
files are recoverable in the run's replaced-reviews directory. No whole-tape
encode was made and the three controls remain off by default.

## E-codex-2026-09-26-37 — paired vote tops

Owner's question: improve comb/geometry agreement while reducing excursions
and common-mode jumps. Entry 37's revised premise is that a field-1 extra top
line can legitimately put the top-implied shift one above the comb floor, but
the two chosen top rows must themselves correlate. Add an off-by-default
vote-only pairing control: extend only the floor's high end by one and require
raw body Pearson rB >= a configurable .6. The threshold is fitted evidence,
not a general signal law. Do not change census, level fills, relative decisions,
window history, resets or empty holds. Keep exact unrounded measurements.

Test whole-tape frame ownership, correlation, confidence and anchor against
reference 4; report the six named rounding cases and any other discrepancy.
Require control-off identity with e08b19c, invariant relative shifts/census,
named intervals, and zero-loss real replay at the requested 16x pace. Report
movement gates as operational measures, not absolute-picture ground truth.
A discrepancy outside the allowed reference rounding stops renders. Otherwise
render only captures 1–4 with s12c plus pairing, from engine-owned overlays,
and validate every encoded placement before replacing their review files.

Entry-37 verdict: the specified paired-top confidence and anchor sequences
match reference 4 on every whole-tape frame. Every supplied reference rB also
matches at its stated precision, including all six near-threshold cases. The
previously recorded fill-rounding case at 29281 supplies additional C evidence
but stays non-confident. Additional correlations on ineligible frames are
observations, not extra votes. The prose interval 82421..83330 includes two
anchor-zero endpoints in the reference itself; the build reproduces them.
The operational movement gates and all four capture cases pass; these fitted
gates do not establish independent absolute-picture truth. Control-off,
census, relative-shift and comb-decision identity hold. Normal, ASan/UBSan and
TSan checks pass. Detailed counts and probes: /private/tmp/vote-pair.FuKNZz.

The first two 16x whole-tape live runs overlapped sanitizer validation and
failed transport completeness (3,164 holes; then 896 holes and three pool
drops). They remain findings, not successful runs. After confirming every
other validation worker had exited, the identical isolated run published all
86,293 units with zero holes/drops and matched the deterministic engine on
every decision. This does not establish no-loss 16x operation under competing
load; replay exit status alone would have concealed both failures.

Captures 1–4 were then rendered from engine 299e878 and renderer de3b92b with
s12c plus pairing at .6. Their complete encoded-placement readbacks pass;
922/649/648/650 frames are published with matching sidecars and fresh READY
status/configuration/hashes. The previous review files remain recoverable in
the run's replaced-reviews directory. No full-tape encode; owner visual
acceptance remains pending. The pairing control remains off by default.

## E-codex-2026-09-26-38 — same-unit flat-band bottom

Owner's question: replace the bottom detector's fixed spread test; margin
choice is explicitly "Fixed 3, recorded". The amended premise is local, not
temporal: the qualified lowest scanned line measures this field's current
flat band, and picture differs from that band in level, even when uniform.
Use p5/p50/p95 over the existing body, a qualified spread <=4, and the three
specified inclusive margin comparisons with 1e-9 tolerance. If the reference
does not qualify, retain the old test, starting field 1's enabled fallback at
line 263; keep the disabled scan exact. No new learner, top/vote/comb policy,
or bottom-profile changes. Expose the requested off-by-default controls and
record which bottom rule supplied each frame-owned census edge and its F.

Before renders, compare every old bottom with 299e878 and every available
reference_bottom answer by source unit; retain exact quantiles for mismatches
and report missing-reference rows rather than inventing their answer. Require
unchanged tops/profiles/blanking and labelled cases. Measure downstream
relative/placement/trigger effects instead of assuming a changed census is
inert; report bottom-only comb decisions and all changed frames. A reference
mismatch stops rendering. Run the 16x live replay with no competing jobs,
slowing only if an idle run loses data and retaining every failure. Render
captures 1–4 after validation, then full tape only if their placements are
identical to the existing reviews. Encoded-strip validation and explicit
producer/configuration/hash status precede atomic publication.

Entry-38 deciding result: the amended C bottom scan matches every available
reference answer, including the inclusive-margin ties. The reference's old
bottom column matches the compiled 299e878 baseline everywhere. Missing census
rows remain separately reported, not counted as matches. The disabled build
is byte-identical to 299e878 for measurements and decisions on the whole tape
and all four captures. Enabled tops, profiles, blanking and level evidence
are unchanged, and the named bottom cases pass.

The dispatch's relative-shift invariant does not hold: corrected bottoms
remove T1 triggers and hence some previously adopted comb results. At 60843,
tops remain 25/288 (st=0), field-1 bottom remains 260, and field-2 bottom goes
521 to 522. The bottom shift therefore goes -2 to -1; incoming d=0 now fits
the bottom's {-1,0} range, so T1 clears. The same raw comb still measures +1,
margin 1.586329837037961, but the unchanged policy does not adopt an untriggered
audit result. The published relative shift changes +1 to 0. Sixteen frames
change relative placement, through this trigger/held-state mechanism; no
confidence or anchor changes. All four captures retain their placements.
This cannot be reconciled by altering the bottom measurements or silently
changing the comb's authority. Renders are withheld pending the owner's
disposition of that invariant, despite the bottom-reference gate passing.

Normal unit/worker, ASan/UBSan and TSan checks pass, including enabled-rule
provenance under reversed pairing. The overlay reads the logged frame-owned
F quantiles and deciding rule; it performs no bottom measurement. A worst-case
text-width check initially failed (`assert dr.textlength(g.bottom_label(row),font=font)<452`,
`AssertionError`); compact separators retain two-decimal quantiles and the
rerun passes. Schema 25 records the new evidence; the control remains off by default.

Whole-tape pacing failures are retained: at 16x, zero holes and five pool
drops; at 8x, zero holes and one pool drop. Both had zero ring, surface and
audio drops. Neither run overlapped project tests, sanitizers or renders,
but unrelated desktop applications were consuming CPU, so these are not
proof of failure on a fully idle machine. The 4x retry published all 86,293
units with zero holes and zero pool/ring/surface/audio drops; it matches the
deterministic C decisions exactly. All four capture replays are also clean.
Detailed counts and every changed frame/edge are recorded under
/private/tmp/bottom-flat.bsfr5V.

Counts: control-off differences 0/86,293 whole-tape units and 0/919, 0/649,
0/649, 0/650 capture units. Old reference bottoms 172,586/172,586 exact;
new reference answers 171,998/171,998 exact, 588 unavailable-reference rows,
and all 9,473 exact-margin rows matched. The unavailable rows yield 531
unknowns and 57 measured bottoms, each listed separately. Tops match on all
172,586 edges; bottom profiles, device blanking, hblank and level evidence
match on all 86,293 units. New bottoms differ on 32 field-1 and 892 field-2
edges. Frame-owned sidecar rule/F provenance matches all 172,578 frame edges.
The only non-metadata sidecar columns changing are logged in full: bottom
edges, motion classes, triggers/comb_ran/confidence, relative source,
held correction, reject ratio and 16 field-1 placements. All raw comb
energies, winners, margins and decided flags remain identical.

Whole-tape gates before/after: confident 58,940/86,289 (68.3053%), common-mode
moves 16, excursions 6, one-frame 0, all unchanged. Bottom-only comb runs /
decided / changed-relative fall from 582/203/144 to 531/155/136. Capture
placements differ on 0/919, 0/649, 0/648, 0/650 frames; every capture still
has zero common-mode moves. The card holds 238/238 with unchanged bottoms;
cap 2 has zero anchor-one frames in the 173-frame interval. Named bottoms
all pass, including cap 4's 262/525 on every unit. Enabled CPU median/p95 is
0.317916/0.340167 ms per unit; disabled is 0.318750/0.336208 (thread CPU,
O3 engine, s12c with pairing and all-frame comb). No media or review status
was replaced. Engine 6778e76 and renderer 5045652 are committed for review;
render authorization remains blocked by the relative-shift invariant.

Entry-38 authorization amendment (2026-09-26): the owner accepts all sixteen
relative-shift changes and withdraws the dispatch's over-specified invariant.
The reviewer's independent same-field vertical-motion probe supports this:
minimum mean absolute difference at offsets -3..+3 follows the comb winner's
sign on fifteen of the sixteen changed frames; 60848's winner is zero. With
steady measured tops and corrected bottoms, this supports content motion
across the field interval, rather than registration, as the old T1-driven
comb correction's cause. Evidence supplied by the reviewer is
/private/tmp/wave-engine/vote/vmotion.py and vm.txt; this attribution is their
measurement, not a new independent replay by this agent. The evidence log
also ends with `edge tpc provenance validation failed: 0x83 packet-index errors=3`;
that diagnostic is retained, not represented as clean transport validation.

Proceed with the already-tested engine 6778e76 and renderer 5045652, s12c plus
pairing .6 and flat-bottom margin 3. Rebuild the four reviews, require zero
placement changes against their existing sidecars and read back every encoded
placement. Then replay the whole tape at 4x with PCM, with no concurrent
project workload; require zero holes and every video/audio drop counter zero,
retrying slower if needed. Full encoded-strip and audio-clock checks, closed
file hashes, explicit producer/configuration status and same-filesystem
publication precede replacement. Previous published files remain recoverable
by hard links. No measurement or publication policy is changed in this step.

Entry-38 publication verdict: captures 1–4 have zero placement differences
against the prior reviews, and their complete encoded-strip readbacks pass
on 922/649/648/650 frames. Capture 3's 649th published unit remains the known
unpaired tail, not an interior omission. All four fresh 4x replays have zero
holes and video/audio drops. Their schema-25 sidecars and updated bottom
overlays are published with READY status naming engine 6778e76, renderer
5045652, s12c, pairing .6, and flat-bottom margin 3.

The fresh full-tape replay also succeeds at 4x on its first attempt: 86,293
published units, zero holes, zero pool/ring/surface/audio drops, and no
sidecar-cell differences against the accepted clean entry-38 replay. No
concurrent project test, replay or encode ran alongside either full-tape
phase. The encode contains 86,289 paired frames plus seven fills, 86,296
frames total, duration 2879.409867 seconds. Full-strip readback finds zero
sequence/placement differences. Audio-clock offsets are below .002 frame
throughout (maximum .001998001998); the two logged audio steps are applied.

Closed, validated MP4 and sidecar were published by same-filesystem renames
to captures/fulltape_render.mp4 and fulltape_render_registration.csv. Fresh
READY status records producer revisions, configuration, accounting and
SHA-256 hashes; publication readback hashes match. Replaced full-tape and
capture artifacts are recoverable by hard links under
/private/tmp/bottom-review.FXkjDh. The owner's visual acceptance is pending.
No additional engine or renderer change was needed for this authorization.

## E-codex-2026-09-26-39 — blank spots and same-field motion

Owner's question: combine A1 and the vertical comb rule without other
regressions or a massive shift. The two premises are separate: skipped
field-2 lines must contain blanking, and same-field vertical motion makes
the cross-field comb an unreliable registration witness. Caption decoding
is an independent score only, never an input to placement.

Implement two off-by-default controls. A1 removes existing vote confidence
using the field-2 unit's own full-width VI median and body samples. Motion
compares adjacent, non-reset units over the specified aperture, with the
entry's smallest-absolute-shift tie rule. Join field motion to its frame
under reversed pairing. Still-frame energy rejection adds a trigger to the
existing comb path; moving frames cannot apply comb verdicts. Do not change
the census, voting policy, bottom detector, or default path.

Before rendering, require control-off identity against 6778e76 and exact A1
and motion reference comparisons; identify exact ties and reference rows
whose previous unit crosses an engine reset. The supplied motion generator
sorts equal errors by signed shift rather than absolute shift and does not
filter resets; neither difference authorizes changing the engine definition.
Measure every placement run and named case, caption scores, capture gates,
CPU and loss accounting. A reference mismatch beyond accounted ties/reset
availability, a named-case falsifier, a caption regression below A1, an
unexplained long placement run, or excess CPU stops publication. Preserve
the current renders until these gates and complete encoded readbacks pass.

Entry-39 result: the combined policy is refuted by its precommitted gates.
Do not render it or tune around the counterexamples. The independently built
A1 instrument reproduces all five reference columns on 86,289 frames, with
zero differences; the full-width VI medians match on 172,586 field observations.
Same-field motion matches all 172,546 observable reference rows, including
best/runner-up errors within the reference's three-decimal formatting. There
are no shift or tie disagreements. Thirty-two additional reference rows
(both fields on sixteen units) cross engine resets and correctly have unknown
motion; the reference generator did not filter those resets. Counters:
4707, 4735, 48189, 48204, 48244, 53410, 53678, 68613, 69517, 70451, 71361,
72291, 81505, 83330, 84339, 85268.

Control-off identity against compiled 6778e76: zero differing decisions or
measurements on 86,293 whole-tape units and 919/649/649/650 capture units.
The census is identical in every arm: 172,586/172,586 field edges, including
the four labelled units. The final real capture-worker replays also match
the deterministic harness; every old sidecar cell in the off arm is identical
except the schema number and new appended evidence columns.

On 86,289 paired frames, baseline / A1 / both give confident counts
58,940 / 57,681 / 57,681 (68.3053% / 66.8463% / 66.8463%). Common-mode
moves / excursions / one-frame jumps are 16/6/0, 6/0/0, 6/0/0. The caption
score on 48,611 frame-owned field-1 labels is:

| Arm | Correct | Off by 1 | Off by 2+ | Correct % |
|---|---:|---:|---:|---:|
| Baseline | 45,441 | 1,371 | 1,799 | 93.4788 |
| A1 | 45,665 | 1,179 | 1,767 | 93.9396 |
| Both | 41,301 | 5,765 | 1,545 | 84.9623 |

A1 changes 575 anchors and zero relative shifts. Both changes 575 anchors,
7,030 relative shifts, and 7,570 placement pairs. There are 4,210 still
triggers and 12,615 moving frames with existing comb triggers suppressed;
motion states are 67,313 still, 18,954 moving, 22 unknown. The largest failure
population is moving-frame suppression publishing census-relative placement:
4,281 newly incorrect caption scores against the baseline. Motion reproduction
therefore does not validate the proposed blanket withdrawal of comb authority.

All five named false anchor changes disappear, and all six required +2 starts
occur on their original counters (zero delay). The protected 60843–60931 span
nevertheless changes on sixteen frames: 60850–60851, 60854–60858, 60883,
60892–60894, 60897–60899, 60924–60925. At 60850, measured tops 24/288 and
bottoms 260/522 imply relative +1, while same-field shifts are -1/-2. The
baseline's triggered decided comb -1 (margin 1.91257) publishes (3,2);
the new policy suppresses that verdict and publishes census (1,2). This is
the requested policy, not a changed measurement, and falsifies the invariant.

Of the still frames in 82073–82159, 73/75 publish the comb minimum. The two
exceptions, 82119 and 82154, have no enclosed basin (floor -5..+5), so the
specified still trigger cannot act. In 84496–84570, 71/71 still frames publish
the minimum. No moving frame in 89492–90721 applies a comb verdict. Captures
1–4 change 1/919, 232/649, 10/648, 29/650 placement pairs, respectively,
while retaining zero common-mode moves, the card's 238/238 (0,0) hold, and
cap 2's zero anchor-one frames out of 173. This is not placement identity.

Engine CPU median/p95, thread CPU with the O3 whole-tape harness, ms/unit:
baseline .319834/.346583; A1 .320208/.348458; both .401333/.440750. Unit,
worker integration, ASan/UBSan and TSan suites pass, including reversed
field ownership, reset/adjacency, exact motion ties, inclusive blank spots,
still triggering, moving suppression, and audit invariance with vote off.
Initial integration failures were stale schema-25 expectations and an editing
indentation error in a test; their original logs remain in scratch alongside
the corrected passing runs. No engine measurement was adjusted to match a
reference. The two controls remain off by default; schema 26 appends their
configuration, blank-spot evidence, frame-owned motion/errors and authority
flags. Engine implementation: 3413040. No renderer change is authorized by
these failed gates, and the existing published media and status are untouched.

Detailed evidence: /private/tmp/entry39.5N6B32. comparison.json contains the
complete metrics and named checks; changed_placements.csv lists every changed
pair in the tape and captures; runs_over30.csv lists every long change run;
motion_reference_unknown.csv identifies every reset-unavailable reference row.
No corpus-dependent caption label enters the engine.

Final pipeline accounting: each of the eight 4x capture replays (off and both
on captures 1–4) reports zero holes and zero video pool/ring/surface or audio
drops, with zero harness differences. The isolated 4x whole-tape both-on
replay (`--pace-us 4000`, pool 32) also completes on its first attempt:
86,305 observations, 86,293 exact/published units, 86,289 paired frames,
seven device-short units, zero holes, and all video/audio drop counters zero.
Every compared decision agrees with the harness. No concurrent project test,
sanitizer, replay or encode ran alongside it. No render was started. The stop
file reports, verbatim:

```
caption below A1
60843 bounce changed
```

Entry-39 amendment commitment: test the narrower claim that only motion of
at least two whole lines per unit invalidates the comb's relative placement.
Add GE_COMB_MOTION_MIN, positive integer, default 1 to reproduce 3413040.
With A1 fixed on, compare still-trigger-only (99) and suppression at 2 against
the published 6778e76 configuration and A1 alone. The still predicate and
all measurements stay unchanged. Caption scoring, including each named span,
is independent evidence only; the former unchanged-bounce requirement is
withdrawn. Require overall score at least 93.94%, named anchor/still results,
explained long change runs and the capture gates before any encode. Prefer
threshold 2 only if it passes and scores no worse than 99. No threshold tuning
or further exception is authorized; if neither passes, preserve all media.

Entry-39 amendment verdict: neither variant meets the caption gate; render
nothing. Default threshold 1 reproduces compiled 3413040 byte-for-byte on
86,293 whole-tape decisions and 919/649/649/650 capture units. Measurement
differences are zero in all arms. Published-baseline, A1 and prior-min1 CSV
comparisons also have zero differing rows. Schema 27 adds ge_comb_motion_min;
the two experimental enabling controls remain off. Implementation edb551c.

On the same 48,611 caption-scored frames, baseline / A1 / min99 / min2 give
45,441 / 45,665 / 45,653 / 45,018 correct (93.478842% / 93.939643% /
93.914958% / 92.608669%). The no-suppression arm gains one and loses thirteen
against A1: gain 49290; losses 89476–89486 and 89490–89491, immediately before
the specified credits interval. Min2 gains 493 and loses 1,140. In 60843–60931
it improves 73/89 to 82/89; in 89492–90721 it improves 148/1,227 to 570/1,227.
Those local gains do not rescue its overall falsifier. In 82073–82159 the
correct count stays zero while 85 labels move from off-one to off-two-plus;
84496–84570 has no caption labels and is explicitly unscored. Caption scoring
remains an independent instrument, not an engine input or visual truth.

Both arms retain all five false-move removals, zero delay on the six +2 starts,
73/75 and 71/71 still-frame minimum placements, 6/0/0 common-mode/excursion/
one-frame counts, 66.8463% confidence, and every capture gate. Min99 changes
334 relative shifts and min2 changes 2,718; each changes the same 575 A1
anchors. Capture placement differences are 0/0/0/0 for min99 and 0/58/3/2
for min2. The still-trigger/withheld counts are 2,745/0 and 2,834/4,298.
Whole-tape engine thread-CPU median/p95 ms are .390250/.430042 and
.389958/.429333. Neither threshold nor any other policy was fitted further.

All four configurations' six requested measures, per-span caption categories,
per-capture CPU and every long change run with its state-path attribution are
in /private/tmp/entry39-motion.4OnXJz/REPORT.md and comparison.json. Per-frame
changes and caption gains/losses are preserved there as CSV/JSON. Long-run
attribution describes the policy path, not independent evidence of quality.
No media replay/encode, publication or status replacement was started after
the failed gate; the current approved renders remain intact. The stop output:

```
VARIANT_A CAPTION_GATE_FAILED: 93.914957520% < 93.940000000%
VARIANT_B CAPTION_GATE_FAILED: 92.608668820% < 93.940000000%
```

Unit, worker integration, ASan/UBSan and TSan checks pass, including each
field independently crossing the inclusive threshold and all three settings
under aligned/reversed pairing. The default identity, not a retuned reference,
establishes that the threshold control did not change the previous arm.

Entry-39 A1-only publication authorization: render the already-validated A1
arm with engine edb551c, s12c, pairing .6, flat-bottom margin 3 and
GE_VOTE_BLANKSPOT=1; GE_COMB_STILL remains 0. The comb-variant failures stand.
Compare each fresh replay to the exact A1 harness decisions, require clean
4x-or-slower replay accounting, and validate every encoded placement before
same-filesystem publication. Captures must retain their prior placements.
Record the A1/control settings in status and show its logged blank-spot result
in the review overlay. No new engine policy or measurement is authorized.

Entry-39 A1-only publication result: engine edb551c, renderer e5e6a90,
schema 27. The logged A1 pass/failure now precedes the wave settings in the
overlay; status records (blankspot, still, motion_min) = (1,0,1). No engine
source changed. Waveform, vote, bottom-overlay and status tests pass.

All five completed replays used pace_us=4000 (4x), pool 32 and audit comb,
with zero holes, pool/ring/surface drops and audio-sink drops. The first cap1
launch in the sandbox failed before input with exactly `open failed`; its
log is retained, and the authorized local shared-memory retry was clean.
Capture harness decision differences: 0/919, 0/649, 0/649, 0/650 units.
Whole-tape differences: 0/86,293 units and 0/86,289 frame decisions. Comparisons
cover placements, triggers, comb decision/margin, held correction, census,
classes, vote state and A1 evidence, accounting for the log's numeric format.

Capture 1–4 prior-placement differences are 0/0/0/0; encoded frames are
922/649/648/650, with complete strip sequence/placement differences 0/0/0/0.
Capture 1 includes three visible fill slots. Capture 3's counter 14149 is
the explicitly unpaired tail, not a missing interior frame. All four MP4s
and sidecars were replaced only after validation and have fresh READY status.

The isolated full replay took 721.652 seconds and delivered 138,217,498 PCM
samples without sink loss. The full encode contains 86,296 frames (86,289
paired frames plus seven visible fills), duration 2879.409867 seconds.
Every encoded strip matches both its frame placement and its source-unit
placements; sequence/placement differences are zero. Audio-clock readback
on 86,292 units has maximum error 0.001998002 frame, retaining the two logged
sample steps. MP4 and sidecar were published by same-filesystem rename to
captures/fulltape_render.mp4 and captures/fulltape_render_registration.csv;
post-publication hash differences are zero, and renders.status is READY.

Full-tape SHA-256: MP4
`baf3090cc14be390c54159c9f937ed0f74bbcbbea7ce8a47412b4cd9edbf1f3e`;
sidecar `f2ac7c06addcdeaef539462cc7fc8c84e98f783ef3cc66df903afc9a38f28393`.
Scratch verification, scripts and recoverable hard-linked prior artifacts:
/private/tmp/a1-review.76PJkK (capture validation/publication JSON) and its
full-4000 directory (whole-tape identity, statistics, strips, validation and
publication JSON). The two failed comb variants remain off; publication is
not owner visual acceptance.

Entry-39 amendment-2 commitment: test the owner's "only withold comb if
there is high vettical motion but horizontal motion is stable" premise.
Add an off-by-default rigid-translation modifier to the existing still-comb
control, retaining exact old behavior when the modifier is off. On adjacent
field units with measured vertical |shift| >= 2, measure unsmoothed 2-D SAD
over the specified 180 x 320 body samples, dy -5..5, dx -8..8. Withhold only
when both frame-owned fields have dx=0, |dy|>=2 and far/best >=1.3. Preserve
the still trigger and the field-ownership join. The 1.3 threshold is fitted
on this tape, not a derived universal confidence boundary.

Falsifiers: off-path identity, 2-D reference mismatch, caption regression
against A1 outside 81508–82402, unsupported long change runs, named-span or
held-out capture failures, or the real-time CPU budget. Measure whole tape
and captures 1–4 before any rendering. motion2d.csv rounds SAD to .3f;
report clarity discrepancies and precision limits rather than tuning or
silently changing the reference. Captions remain scoring evidence only.

Entry-39 amendment-2 verdict: implementation a7a4316, schema 28, remains
off by default (GE_COMB_RIGID=0; clarity 1.3). The premise is not refuted by
the measured outcomes, but acceptance is unresolved: reference B lacks the
precision needed by its own clarity gate. No render or publication follows.

Direct compiled-baseline comparisons reproduce edb551c with the new modifier
off, and 6778e76 with entry-39 controls off: zero decision/measurement
differences over 86,293 tape units and 919/649/649/650 capture units. All
tested configurations preserve the 172,586 tape census edges. Unit, worker
integration, ASan/UBSan and TSan pass.

All 11,152 searched fields match reference dx/dy. However, 10,816 clarity
ratios exceed the requested 1e-6 relative tolerance: motion2d.csv writes
the two SAD means to .3f. Every C SAD and far SAD is within that rounding
interval (zero outside). Counter 4683 field 1 is decisive: exact means
0.4639756944444444 and 0.46427083333333335 yield 1.0006361085126285;
the printed .464/.464 yields 1. No reference or tolerance was changed.
Full-precision reference values are needed to clear B.

Compared with A1, the rigid arm changes 1,187 relative shifts and zero
anchors. Caption score excluding 81508–82402 is 96.422734% against A1's
95.697640%; overall 94.651416% against 93.939643%. These are instrument
scores, not visual truth. Withheld: 668 frames, eight outside the credits,
zero in 60843–60931. The existing still-trigger span results are retained.
Capture placement differences are zero; all four have zero common-mode
moves, the card holds 238/238, and cap 2 has zero +1 anchors on 173 frames.
Long change runs and their policy traces are listed in the scratch report;
the 1.3 cutoff remains tape-fitted and has not been visually accepted.

M3 engine CPU: rigid median/p95 0.404041/1.597516 ms/unit; disabled base
0.320875/0.418225. The 2-D search ran on 6,695/86,293 units (7.758451%).
No full media replay was launched; holes/drops and encoded readback are
unmeasured this turn, not zero. Published A1 files/status remain untouched.
Full results, run lists, every changed placement, exact clarity mismatches,
test output and reproducible harnesses: /private/tmp/entry39-rigid.R1ZMaT.

The existing 10,000-unit v9 worker benchmark passes on a local shared-memory
retry: worker median/p95 4.263/5.212 ms. The initial sandbox attempt failed
verbatim `BENCH: fp_open failed` / `make: *** [bench] Error 2`; it did not
reach the publisher loop. This legacy benchmark is not the new engine's CPU
measurement above.

Entry-39 amendment-2 gate-B acceptance: the reviewer accepts zero shift
differences on 11,152 fields and all SAD values inside the reference's .3f
rounding intervals. The 1e-6 clarity mismatch was a reference-precision
defect, not an implementation disagreement. The three rounding-sensitive
fields are reported with exact engine arithmetic; 33107 field 2 is not
searched on the production path (vertical shift zero), so its requested
clarity is a separate diagnostic measurement, not logged production evidence.

Authorized publication: engine a7a4316, s12c, pairing .6, flat-bottom margin
3, A1, still trigger and rigid withholding at clarity 1.3. Update overlays
from logged motion only. Require clean isolated paced replays, complete
harness identity and encoded-strip readback before replacing any artifacts;
capture placements must remain identical to the published A1 run. Record the
idle-worker benchmark separately from the legacy benchmark's stage timings.

Owner publication-retention amendment: no backups of replaced media, sidecars
or status, and no retained derived staging media after validated publication.
Existing backup cleanup belongs to Claude; this turn must not touch it.

Entry-39 amendment-2 publication result: engine a7a4316 is unchanged;
renderer c533392 adds logged still/withheld and per-field 2-D evidence.
Schema 28; s12c, pairing .6, bottom-flat margin 3, A1, still and rigid
withholding at clarity 1.3. Gate B is accepted for the reference-precision
reason recorded above, not by adjusting the engine or its threshold.

Exact requested clarities and frame withholding:

| Unit / field | Clarity | Production 2-D search | Withheld |
|---|---:|---|---|
| 33107 / 2 | 1.3001202681622788 | no; separate C diagnostic, dx=0/dy=0 | no |
| 79624 / 2 | 1.2998686706551874 | yes; dx=-1/dy=-3 | no |
| 82197 / 1 | 1.3001577662116106 | yes; dx=-1/dy=-2 | no |

The 33107 diagnostic initially failed on the unframed leading fragment:
`TypeError: '>=' not supported between instances of 'NoneType' and 'int'`.
The scratch reader was corrected to skip absent counters and the diagnostic
rerun. It uses the compiled engine's measurement, not a Python reimplementation;
it does not insert a search into production evidence.

Captures 1–4 and the whole tape all passed their first 4x replay
(pace_us=4000), with zero holes, pool/ring/surface/audio drops, and zero
harness-versus-replay decision or logged motion-evidence differences.

| Input | Exact units | Paired frames | Encoded frames | Placement differences vs A1 | Encoded readback differences |
|---|---:|---:|---:|---:|---:|
| capture 1 | 919 | 919 | 922 | 0 | 0 |
| capture 2 | 649 | 649 | 649 | 0 | 0 |
| capture 3 | 649 | 648 | 648 | 0 | 0 |
| capture 4 | 650 | 650 | 650 | 0 | 0 |
| whole tape | 86,293 | 86,289 | 86,296 | 1,187 relative shifts; 0 anchors | 0 |

Capture 1 has three fill frames; capture 3 retains its explicit unpaired
tail at 14149, not an interior drop. The whole-tape replay took 722.894428 s;
the encode has seven fill frames and duration 2879.409867 s. Audio-clock
readback over 86,292 units has maximum error 0.001998002 frame, preserving
the two logged source sample steps. The full sidecar's 318 rejections are
304 substitutions and 14 discards; all decisions match the accepted harness.

The owner required the worker benchmark to include the expensive 2-D search.
Commit 621d8e4 adds bench-geometry: it times the actual configured v11
frameserver processing path using thread CPU time, including classification,
geometry (with both motion searches), assembly and publication. It excludes
input I/O and queue waits; sidecar-formatting CPU is included. Its replay
decisions are identical to the accepted harness; sample/search-count
differences are zero on all 86,293 units.

| 2-D searches in unit | Units | Worker median ms | Worker p95 ms | Worker maximum ms |
|---|---:|---:|---:|---:|
| all | 86,293 | 1.404041 | 2.531042 | 8.229542 |
| zero | 79,598 | 1.365958 | 1.924917 | 3.995667 |
| one | 2,238 | 2.421375 | 3.448542 | 5.162542 |
| two | 4,457 | 2.929667 | 4.309583 | 8.229542 |

The 2-D search ran on 6,695 units (7.758451%), covering 11,152 fields;
zero worker samples exceeded the 10 ms CPU budget. For two-search units,
geometry is the dominant cost: median/p95 2.474083/3.560417 ms. All-unit
geometry is .701416/2.055583, classifier .397750/.551667, publication
.039125/.090500. Stage medians are not additive.

The previous 4.263/5.212 ms whole-worker figure measured legacy v9, not
this configured v11 path: this is a scope correction, not a like-for-like
speedup claim. A diagnostic repeat of the legacy benchmark spent about
4.047/4.863 ms in registration. No competing project jobs ran alongside
the full replay or encode, but unrelated desktop/system CPU activity was
present and recorded. These are thread-CPU measurements under that load,
not a claim of the requested fully idle host.

All five MP4s and their sidecars were validated and published, with fresh
READY status naming engine, renderer and configuration. Full-tape hashes:
MP4 `71bd8b51215586f16a3856f704d5dadeaf676144eadd124c04635e7107587ec1`;
sidecar `82609a5956963d91d65b978de685826518302c5db3d53a18aef944f489f2509b`.
Post-rename hash differences: zero. Same-filesystem replacement, no backups;
derived staging MP4/sidecar/PCM/AV files and the redundant benchmark sidecar
were removed. No existing replaced-review folder was touched. Verification
records, timings, scripts and logs remain in /private/tmp/rigid-review.YcoRt6;
the published status files carry the durable artifact hashes. Publication
is not owner visual acceptance.

Phase-A cleanup commitment: freeze the owner's approved a7a4316 behavior,
then replace mutable process-wide settings with per-instance configuration.
No signal or publication policy changes. The registered schema-28 sidecars
are the acceptance reference, byte for byte, including configuration echoes.
Check all five captures after each code-changing stage and with the final
isolated 4x replay; report any differing rows rather than normalizing them.
Retain v9 and explicit v11 selection. Review Claude-trailered code changes
against the whole system; substantive findings are reported, not fixed here.
Keep no media backups and perform no scratch sweep. CPU includes conditional
2-D search; unit and sanitizer gates remain required. Mutual review is pending
until Claude reviews the completed cleanup diff.

Owner scope amendment: default frameserver and OBS opens now select the approved
v11 engine, without an environment switch. Keep v9 compiled but unselected;
its deletion is deferred until after the full-history merge. The byte-identity
gate is unchanged and now also exercises default selection.

Phase-A verdict: the approved default freeze (957425a), per-instance numeric
configuration (2fc87b0), and mechanical cleanup (195b611) each reproduce all five
registered schema-28 sidecars byte for byte: zero differing rows across
86,305 / 930 / 651 / 651 / 652 rows. Final isolated 4x replay has zero holes
and drops. No reference normalization, schema consolidation, classifier change,
new rule, render, backup or v9 deletion. Default OBS builds against the same
engine; unit, ASan/UBSan and TSan checks pass. Documentation is e454098.

The full worker, including 11,152 conditional 2-D field searches on 6,695 of
86,293 units, measures 1.748500/2.736334 ms median/p95, maximum 8.533708;
zero samples exceed 10 ms. The previous approved record is 1.404041/2.531042.
The unchanged classifier also costs more in this run; this is not an isolated
causal performance comparison. Search-population differences are zero.

One earlier instrumented cap-1 run differed at 6253 only: audio_residual_ticks
11763 and audio_step_samples 0 were empty. Ordinary rerun and both later stages
match. This intermittent audio-evidence result remains unexplained and unfixed;
it was neither filtered nor treated as an engine-placement difference.

Counterpart review: 14 surviving net-changed code files have non-merge Claude
trailers; three more touched legacy tools are unchanged from main. Reported,
not fixed: tpc_slice source-alias truncation and unchecked short payloads
(both reproduced on synthetic input), and the renderer's pair-next/TFF-default
CLI hazard (approved cap 3 explicitly used BFF). Also noted the existing OBS
Makefile install/uninstall removal-path mismatch; no installation was performed.
Detailed inventory, per-stage hashes, timing populations and verbatim diagnostics
are in /private/tmp/cleanup-phase-a.hkGJkE/REPORT.md. Claude's review of this diff
and convergence are pending; this verdict does not authorize merging.
