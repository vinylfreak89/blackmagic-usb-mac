# Cohort adjudication: the criteria do not decide

Five independent adjudications of the same 64 frozen panels — Codex over all of them, and four
adjudicators of this side over disjoint quarters. Every one audited for what it actually read
(`audit_adjudicator.py`): **zero tool calls touching the other agent's verdicts, its branch, its
worktree, `git show`/`cat-file`/`log`, or a repository-wide search, in all four.**

| adjudicator | n | identifiable | L1 | L2 | L3 | strata seen |
|---|---:|---:|---:|---:|---:|---|
| Codex | 768 | **0** | 0 | **768** | 0 | all four |
| group 1 | 192 | 0 | 2 | 162 | 28 | card |
| group 2 | 192 | **86** | 81 | 0 | 25 | off-card lower quartile |
| group 3 | 192 | **186** | 0 | 6 | 0 | off-card inter/upper |
| group 4 | 192 | 0 | **192** | 0 | 0 | off-card inter/upper |
| this side, all | 768 | **272** | 275 | 168 | 53 | |

Against Codex, key by key — its result is unanimous so its verdict on every key is known from its
aggregate and its per-key file was never read here:

* both say NOT identifiable: **496 of 768 (64.6%)**
* verdicts disagree: **272 of 768 (35.4%)**
* and where the verdict agrees, the same failing test is named in only **168 of 496 (33.9%)**

## The sharpest fact, with the qualifications Codex added

**Groups 3 and 4 drew from overlapping strata and returned 186 of 192 and 0 of 192**, with L1 at 0
and 192 respectively.

⚠️ Two qualifications, both Codex's and both accepted. They reviewed **different keys** within
those overlapping strata, so this is NOT a same-row repeatability experiment and must not be
described as one. And the criteria never prescribed which failure to report when several applied,
so the "same failing test named" figure below cannot measure agreement on each individual test.
Neither rescues the cohort, but "all adjudication is impossible" would overstate what was shown.
Codex adds the same discipline to its own side: its universal L2 is a panel-limited judgement, not
proof of fundamental unmeasurability.

They describe the *same observation* and read it oppositely:

* group 3: "whether the trace genuinely returns to the blue line in the one or two samples before
  the picture starts — a 1–2 pixel distinction at panel scale" → the level is established, L1 passes
* group 4: "the trace only ever *crosses* the field's written blanking level rather than sitting on
  it … descends to touch the blue line at a single sample immediately before the picture step" →
  the level is never established, L1 fails

The criteria never say whether touching the level for one or two samples establishes it. That one
unspecified word decides every verdict in this cohort.

## What follows

The contract anticipated "no edges qualify" and required that be reported rather than the criteria
relaxed. What happened is different and more useful: **the criteria do not decide.** So the cohort
cannot be built by adjudication — not with a larger pilot, not with better strata, not with more
adjudicators. The blocker is the one both agents already named and neither could fill: there is no
identification METHOD, and these criteria were an attempt to substitute judgement for one.
Judgement does not converge, and that is now measured rather than suspected.

The classifier gate therefore stands untouched, and the critical path is the contract's measurement
(4) — whether any observable separates a dark region's endpoint from blanking's — which has to be a
measurement rather than an adjudication.

## The lead is probably dead, on timing — Codex's prior objection, computed

Before measuring anything, Codex asked whether a burst residual can be in the tested samples at
all. Worked from the standards figures:

    burst starts        5.300 µs after 0H          (ITU-R BT.470)
    burst length        2.514 µs                   (9 cycles at 3.579545 MHz)
    burst ends          7.814 µs
    window starts       9.037 µs                   (BT.601, 122 samples after 0H)
    gap                 1.223 µs = 16.5 samples

**Under nominal timing the burst is over 16.5 samples before the delivered window begins**, so
nothing at a normally-timed row's porch can be burst — and the humps the adjudicators described sit
on exactly those porches. The lead as originally stated is therefore probably dead: whatever that
2–10 code hump is, it is not the colour burst. Ringing, filter response and content all remain open
as explanations and none is measured.

⚠️ This is arithmetic from the standard, not a measurement of this decoder, and it is not a proof
of absence.

**But the same arithmetic reframes it, and the reframing is better than the original.** A DISPLACED
row is shifted by far more than 16.5 samples — the relocated blanking runs measured on capture 1
sit at columns 20–70 with lengths of 147–164 — so a displaced row's burst would be carried INTO the
window along with its blanking, at a predictable offset inside that run. Dark picture has no reason
to carry it. That makes burst a candidate positive signature of RELOCATED BLANKING rather than of
normal blanking, which is the opposite of the original idea and is closer to what the
identification method actually needs.
Codex's conditions on any such test stand and are not weakened by the reframing: energy at the
subcarrier frequency is NOT something dark picture cannot have — picture structure and chroma
leakage can supply it — so frequency would be supporting evidence, with timing position,
oscillatory structure and specificity against controls all still to be established. A positive
result would not by itself close the identification-method gate.

## The original lead, kept for the record

Group 3, unprompted: "nearly every porch carries a 2–10 code hump (burst-like) superimposed on the
blanking interval". Group 2 saw the same shape from the other side: some left edges "carry a 2-code
hump that returns to the line, leaving two candidate boundaries several samples apart".

If that hump is periodic at the colour burst's frequency, it is a POSITIVE signature of blanking
that dark picture cannot have — which is exactly the discriminator the identification method needs.
⚠️ Recorded as a lead, not a finding. It is not measured, the burst is a chroma signal and whether a
residual survives into this luma window is unknown, and two adjudicators calling something
"burst-like" by eye is not evidence that it is.

## A note on the verdict files' key column

The four verdict files name their key column `row_label` rather than `storage_row`. Codex's first
join failed on that. The values ARE the frozen storage-row indices - verified 768 of 768 exact
match against COHORT_KEYS.json, zero missing and zero extra - so the join is sound once the column
is mapped. The files are not renamed, because Codex has already joined against them as they stand.

## A defect in this instrument, found by group 3

The panel axis is mislabelled. `range(0,len(seg)+1,8)` produces a tick labelled 48 and
`px(min(48,47))` places it on sample 47, so the axis reads 0–48 across 48 samples and a reader
interpolating near the right end is off by up to a sample. Boundary VALUES read from this panel set
carry that error; the identifiable/not judgements do not depend on the tick labels. Not fixed
retroactively - the panels are frozen and the cohort is keyed to them - but any reuse must fix it
first.
