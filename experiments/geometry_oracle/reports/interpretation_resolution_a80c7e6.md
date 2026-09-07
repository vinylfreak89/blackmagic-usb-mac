# Interpretation resolution against contract a80c7e6

Scope: the nine questions in the turn-16 brief, read against the complete contract at engine revision `a80c7e6`, the owner's 03:09–03:35 transcript, the owner-message transcript for the current session, the chronological 72-hour owner-message extract, and `CLAUDE.md` sections 7 and 11. Later owner statements control where they correct earlier ones. “Extreme” below means that the quoted words select the interpretation without needing a new measurement or policy choice.

## Chronological corrections that control this read

1. The 2026-09-07 03:39 statement that the head-switch band “should not move” was corrected at 06:11: “what I meant by should not moved I meant its height should be fixed ... not the band itself which absolutely can move if the whole picture does.” The invariant is the learned geometry/band count, not an absolute raster row.
2. The 03:39 proposal that bottom blanking showed a shifted-up field, including the proposed continuous field-2 `-1`, was expressly withdrawn at 06:11: “my previous estimation that a shift down must have been lines added because of the VBI blanking remains wrong” and “new lines of luma appearing alone can't mean for sure the actual picture shifted.” The 06:22 replacement is: “could be indicative. needs to be confirmed against the comb.”
3. The 2026-09-06 16:54 statement that the band was not constant per field was superseded first by the peak/partial-line analysis and then by the 06:11/06:22 account: the band may change raster position with the field, while its source count is the learned invariant and the partial top row is its travel/ambiguity.
4. The older v9 rule that a failed geometric invariant killed the lock, and the 2026-09-05 suggestion that comb needed remeasurement, are narrowed by the latest rules: the settled comb stands for the lock, while only snow-like signal, a vertical tear, or another explicit lock-like event resets it. Ordinary damage preserves geometry and leaves the unit's position Unknown when it cannot be measured.

## 1. Comb after an applied displacement

**Interpretation.** The comb registration and field precedence are settled once for a source lock. A per-unit geometry measurement may move a crop; that moved crop must agree with the already-settled comb. The engine does not settle a new comb or use comb to originate another correction. A measurable failure to agree is a true-disagreement candidate for the harness to report to the owner with the required frame.

**Deciding words.** The owner described “the comb checking” as “set only once at the beginning of a picture lock” (2026-09-04 16:57), and his latest correction still refers to “a comb disagreement on the settled comb” (2026-09-07 06:11). The current contract makes the consequence explicit: “Comb ... settled once per lock; thereafter a disagreement is the arbiter” and “no comb correction of the crop.”

**Confidence:** extreme. **Claude:** agree. **Two-agent status:** resolved, provided Claude's own confidence is extreme.

## 2. One field falls out of the raster

**Interpretation.** Loss of one field's previously visible edge cues is not itself a reset. If the line account measures a displacement and the settled comb confirms it, that field receives the measured displacement. If the edge is no longer measurable, its position is Unknown and the crop is left where it was; that is not a claim that the position held. A reset of both fields requires the signal-state layer to report snow-like signal, a vertical tear, or another explicit lock-like loss.

**Deciding words.** On the original case the owner said, “those signals not being there when they were one frame before means they shifted away. confirm that with a shift of the top geometry and its near certain, the field shifted and it needs adjustment” (03:34 transcript). He later bounded resets: “anything thats not ‘snow like’ or a vertical tear ... should be indicative of continuing program and therefore previous geometry (not position) holds through the damage,” followed by “snow units mean the lock is gone. everything resets” and “why would there be snow in one field but not the other” (2026-09-07 06:11).

**Confidence:** extreme. **Claude:** agree, with the stated measurable/Unknown distinction. **Two-agent status:** resolved, provided Claude's own confidence is extreme.

## 3. A caption may place the first unit but never acts alone

**Interpretation.** These statements are consistent. Geometry supplies the placement candidate and the regenerated rows establish a usable raster; a valid caption can be the one required independent confirmation, including on the first unit. Thus caption can complete acquisition without another secondary signal, but it never overrides or invents geometry by itself. A caption/geometry disagreement is recorded and geometry wins.

**Deciding words.** The owner said, “Lock only happens after you get a at least one confirmation that the geometry is correct. Either combing, captions or both” (2026-09-07 04:29). The current contract says both “a caption may place the very first unit of a segment” and “a caption that disagrees with measured geometry is logged, geometry wins.”

**Confidence:** extreme. **Claude:** agree. **Two-agent status:** resolved, provided Claude's own confidence is extreme.

## 4. Source-loss detection ownership

**Interpretation.** Snow-like signal, vertical tears, splice, loss, and relock are classified outside the geometry engine. The signal-state layer delivers the resulting event as an explicit input; the geometry engine consumes it and resets or holds as directed. Row-level candidate features may be computed upstream, but the geometry engine must not infer the event from a body-half heuristic.

**Deciding words.** The current contract is direct: “Segment events (splice, signal loss, relock) come from the signal-state layer as explicit inputs; never inferred from a body-half heuristic.” `CLAUDE.md` section 8 likewise keeps source-lock state distinct from USB/session state, and section 11 records the parser → classifier → engine ordering.

**Confidence:** extreme. **Claude:** agree. **Two-agent status:** resolved, provided Claude's own confidence is extreme.

## 5. Confirmed height change with the peak present

**Interpretation.** Report the height disagreement loudly, but do not reset merely because that measurement disagrees. Preserve the locked geometry; if the unit cannot yield a coherent position, mark its position Unknown and leave the crop. Reset only if the signal-state layer independently classifies the unit as snow-like, vertically torn, relocking, spliced, or otherwise lock-like. If that independent event is present, the event—not the height discrepancy alone—is the reset cause.

**Deciding words.** The owner required only that an unexplained height change be exposed: “if that height changes other than for the reason I said, I should know about it.” His later reset boundary is narrower and chronological: “anything thats not ‘snow like’ or a vertical tear ... [means] previous geometry (not position) holds through the damage,” while “snow units mean the lock is gone. everything resets” (2026-09-07 06:11). The current contract reinforces that tracking breaks “only on a vertically torn raster or a lost lock” and separately leaves the height anomaly as something “reported.”

The older 2026-09-04 formulation—“if the math doesn't math, then your OLD LOCK IS DEAD”—is therefore superseded by the later damage/reset distinction. No audited raw-row unit can decide a state-machine policy by itself; this conclusion comes from the owner's latest policy boundary.

**Confidence:** extreme. **Claude:** disagree; Claude says report and reset. **Two-agent status:** unresolved because the agents disagree, despite my extreme confidence.

## 6. Per-unit applied offset and the first confirmed unit

**Interpretation.** On every measurable locked unit, the offset is read anew as the count of recorded bands above the picture, checked by the complementary below-picture account, and confirmed against the settled comb. It is not changed merely by integrating a temporal `X`. On an unmeasurable damage unit the position is Unknown and the crop is left; no number is substituted. Before acquisition the crop is standard, and the first unit whose geometry receives the required confirmation adopts that unit's measured offset.

**Deciding words.** The owner said the task is “where does the picture start, and did it move since the last unit” and later, “number of picture lines should indicate position ... most important is agreement” (2026-09-07 06:22). The current definition is explicit: “Bands above the picture ... [are] the offset, read every unit and confirmed by the comb,” while “before a lock, standard placement.”

**Confidence:** extreme. **Claude:** agree, with the Unknown-unit qualification. **Two-agent status:** resolved, provided Claude's own confidence is extreme.

## 7. An upward move from offset zero whose top is hidden

**Interpretation.** The proposed observation is sound only as a candidate: with visible top clamped at line 23, a one-row reduction in the in-raster pre-switch account and the corresponding below-picture evidence can indicate `d = -1`; new luma or bottom blanking alone cannot. The settled comb must confirm it. The record can then state `d = -1`, and the missing source row is unrecoverable.

The output action is not fully defined. Claude's “never read above line 23; leave the lost top line lost” is compatible with the latest direct rules “line 23 remains the top line always” and “VBI should never be rendered.” But the contract also says the raster crop origin is `23 + d`, which is line 22 for `d = -1`; it does not specify whether the output inserts legal black at its top, clamps the read origin at 23, or expresses the unavailable row some other way. “One line short at the top” does not select one of those byte-level outputs.

**Deciding words.** The latest owner statement is: bottom blanking “could be indicative. needs to be confirmed against the comb,” followed by “line 23 remains the top line always. VBI should never be rendered” (2026-09-07 06:22). This explicitly corrects the 03:39 proposal to pull blanking/VBI into the picture. The contract itself lists “the hidden-top confirmation” as a measurement still to be built and shown.

No existing audited unit establishes the exact hidden-top output treatment; that absence is the deciding evidence for retaining the ambiguity.

**Confidence:** not extreme. **Claude:** agree on detection, the `-1` record, and irrecoverability; disagree that the crop behavior is fully resolved. **Two-agent status:** unresolved.

## 8. Switch rows that fall past the clip

**Interpretation.** The source's total switch-band count is the running comparator learned within the current lock, not a typed per-source constant. Per unit, visible switch rows are observed and any remainder past the clip is explicitly censored and supplied only by the locked line account. Thus a nominal account such as 237 picture rows plus three switch rows closes to 240 even when one or more switch rows cannot be observed beyond the clip; the hidden rows must never be presented as direct observations.

**Deciding words.** The owner said, “number of picture lines should indicate position assuming the number of head switch lines stay fixed. in other words, 237 real picture line + 3 head switch lines = 0 offset” (2026-09-07 06:22). The current contract adds: “rows past the clip are lost,” while its comparator rules require the band count to be derived online rather than configured.

**Confidence:** extreme. **Claude:** agree, with “fixed per source” understood as the learned lock comparator rather than metadata or a magic number. **Two-agent status:** resolved, provided Claude's own confidence is extreme.

## 9. Bottom black from the TBC versus a high field

**Interpretation.** They are not distinguishable from those black rows alone. The running source-lock comparator absorbs the stable number of switch rows, including rows the TBC renders black. A change in below-picture blank rows is only a displacement candidate against that learned account; the settled comb must confirm a high field. Without decisive comb/geometry agreement, no movement is applied.

**Deciding words.** The owner's latest formulation is exact: blank rows “could be indicative. needs to be confirmed against the comb” and the picture-line count works only “assuming the number of head switch lines stay fixed” (2026-09-07 06:22). This replaces his 03:39 inference that bottom blanking itself implied a shifted-up field and his proposed continuous field-2 `-1`.

**Confidence:** extreme. **Claude:** agree. **Two-agent status:** resolved, provided Claude's own confidence is extreme.

## Items for the owner

Only items that fail the required two-agent extreme-confidence agreement belong here:

1. **Item 5 — height disagreement with the peak present:** I read the latest reset boundary as report/hold, not reset; Claude reads it as report/reset.
2. **Item 7 — hidden upward displacement:** the detection and `d = -1` record are agreed, but the contract does not reconcile `origin = 23 + d` with “line 23 remains the top line always” and “VBI should never be rendered,” so the exact output fill/clamp behavior is unresolved.

All other items are resolved on my side at extreme confidence and agree with Claude's stated interpretation, subject only to Claude recording the same confidence level.
