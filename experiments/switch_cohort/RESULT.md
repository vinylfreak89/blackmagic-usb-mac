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

## The sharpest fact

**Groups 3 and 4 drew from the same strata and returned 186 of 192 and 0 of 192.** Not a shading of
emphasis — 97% against 0%, with L1 at 0 and 192 respectively.

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

## A lead for that measurement, from the adjudication rather than from theory

Group 3, unprompted: "nearly every porch carries a 2–10 code hump (burst-like) superimposed on the
blanking interval". Group 2 saw the same shape from the other side: some left edges "carry a 2-code
hump that returns to the line, leaving two candidate boundaries several samples apart".

If that hump is periodic at the colour burst's frequency, it is a POSITIVE signature of blanking
that dark picture cannot have — which is exactly the discriminator the identification method needs.
⚠️ Recorded as a lead, not a finding. It is not measured, the burst is a chroma signal and whether a
residual survives into this luma window is unknown, and two adjudicators calling something
"burst-like" by eye is not evidence that it is.

## A defect in this instrument, found by group 3

The panel axis is mislabelled. `range(0,len(seg)+1,8)` produces a tick labelled 48 and
`px(min(48,47))` places it on sample 47, so the axis reads 0–48 across 48 samples and a reader
interpolating near the right end is off by up to a sample. Boundary VALUES read from this panel set
carry that error; the identifiable/not judgements do not depend on the tick labels. Not fixed
retroactively - the panels are frozen and the cohort is keyed to them - but any reuse must fix it
first.
