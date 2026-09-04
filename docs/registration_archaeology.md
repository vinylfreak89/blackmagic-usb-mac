# Registration engine archaeology — nine versions, one missed signal

Reconstructed 2026-09-04 from the git history (hashes and dates below are from `git log --all`),
the CLAUDE.md narrative as it was written at each stage (section line numbers refer to the file
at commit `9b5226f`), and the dated session transcripts of both agents. Times are JST. Anything not
traceable to one of those is marked UNSOURCED. Codex's independent account from its own rollouts
is reconciled in the last section.

## The phenomenon everyone was chasing

The deck's output shows the picture "jumping" vertically by a line or two, and a motion-adaptive
deinterlacer (yadif, NNEDI) combs wherever that happens. Nine versions of a registration engine
tried to remove the jump. The question that was never asked until the ninth was: *where, in the
signal, is the reference the picture is jumping relative to?*

## v1 — "field 2's origin drifts" (offline, 2026-08-29)

- **Premise.** The unit's second field starts at a varying line; comb/weave scoring over a
  window of candidate field-2 origins (274–285) finds the best interleave.
- **Mechanism.** `capture_render.py` searched field-2 origin candidates by weave energy.
- **Record.** `e811226` "Answer the core question: field flipping is a spatial field-origin slip"
  (22:15); `4f8b65b` "crop field 1 at 17+d1" (22:29). CLAUDE.md §7 header "ANSWERED — it is a
  spatial field-ORIGIN slip" (line 685) still reads as written that evening.
- **Falsified the same night.** A field-origin census over 6,160 intact units of the untagged
  capture: transport raster rigid (`f1_origin=17` 99.35 %, `f2_origin=280` 99.25 %); field 2's
  picture translated 0 lines in 4,042/4,042 rigidly measurable units; **field 1's picture moves**
  by 1–2 whole lines. "The 274–285 wander was estimator noise": comb can only constrain
  `d2 − d1`, never an absolute origin (§7, the CORRECTED block at line 690; commit `564c0b9`
  22:50; `11c3703` LEARNINGS "an estimator's best guess is not a measurement"). Transcript
  13:51 UTC (22:51 JST): "the census killed its own premise — including the answer I gave you".
- **What it got right.** The error is spatial and integer-line, not temporal/cadence.
- **What it got wrong.** It measured an inter-field *relation* and reported it as an absolute
  position. Correction direction was also backwards for a while (`e153b82`, Codex review, 23:33).

## v2 — the per-field (d1, d2) model (offline, 2026-08-30)

- **Premise.** Each field's picture has its own signed integer offset inside a rigid raster;
  neither field is a permanent anchor; comb constrains only `d2 − d1`; absolutes need temporal
  same-parity registration, landmarks, or a learned stable segment; say `Unknown` otherwise.
- **Mechanism.** `f936339` "per-field (d1,d2) model replaces the field-2-origin model" (15:49);
  `ac1e59c` "apply offsets only when weave and landmark evidence agree" (16:12). CLAUDE.md
  "General registration model" (line 773).
- **Measurements.** Untagged capture resolves as `d1 ∈ {0,+1,+2}, d2 = 0` — "test data, not
  policy" (line 783).
- **Why it was still a proxy.** Position was inferred from the picture's own edges, comb and
  temporal correlation; the deck's regenerated VBI lines (rows 16/17) were treated as a "transport
  ruler" to skip by row number, never as a reference the content could be compared against.

## v3 — the C engine and the 120-unit rolling mode (2026-08-30 → 09-01)

- **Premise.** Port v2 to allocation-free C with the same anchors (padding ruler, VBI rows,
  temporal registration), hysteresis and `Unknown`. The 120-unit rolling majority that "settles
  the plateau" was NOT in the first C port: `phase_history` first appears in `14fe5d5` (09-01),
  together with ±6-line motion search in three bands and cut/fade abstention. Codex's account
  splits these into two stages (first C engine, then motion/rolling); the git objects support
  that split and this section originally conflated them.
- **Record.** `f5b261b` "Add allocation-free C field registration engine" (21:00), `bf3f3bc`
  "independent edge evidence" (21:43), `0f29e37` "dual-edge veto and segment-gauge reset"
  (08-31 03:01), `0d807af` "Render tagged captures through the C registration engine",
  `14fe5d5` "motion-phase evidence; abstain on cuts and fades" (09-01 20:39).
- **Measurements.** Full-tape golden 86,293/86,293 units and 56,441/56,441 confident decisions
  matching the offline model; untagged census 4,042/4,042 applied offsets correct; 1.29 ms
  median per unit (CLAUDE.md line 1068).
- **Falsified.** "The rolling majority was proven to manufacture delayed plateaus" (line 1082):
  a plateau that starts is followed only after the window's majority flips, tens of units late.

## v4 — bounded FIFO, backdating, horizon (2026-09-02)

- **Premise.** Keep a caller-owned FIFO (30-unit confirmation, 36-unit hard horizon); a coherent
  top+bottom candidate may correct a buffered unit; a settled fallback is backdated onto buffered
  abstentions; hysteresis changes only the fallback.
- **Record.** `56892df` "bounded FIFO replaces the 120-unit rolling mode; synthetic-truth golden"
  (00:45); `2a4b23f` "Preserve registration phase across resets" (02:37) = the "Algorithm v4
  horizon fix" (line 1117): two `RawAwaitingLock` transitions had snapped to (0,0) after reset
  with no observation.
- **Measurements.** Six-minute production proof: 54 finalized transitions, five 1–3-unit runs;
  untagged golden 3,784/4,042 overall, 3,499/3,499 confident, 258 conservative under-corrections;
  full v4 golden 86,293 units at 2.532 ms median, 464 hard resets with zero reset-induced phase
  changes (lines 1100–1128).
- **Why it was wrong anyway.** It answered "is a move real?" by waiting, which is illegal for a
  live path: a published frame cannot be revised, so every unit spent waiting was a unit
  presented with the wrong crop. The owner's overnight brief of 09-02 17:23 UTC asked exactly
  this ("I think we might have overengineered"); the lookback investigation (`dd60843`,
  `2cdf4f2`, 09-03 03:09–03:14) concluded the FIFO/backtracking belongs to an offline pass only.

## v5 — the lookback investigation (2026-09-02/03; numbered here for continuity)

- Two independent arms (an external analyst, Codex) audited the v3/v4 sidecars: 936/948 applied
  transitions began on a matching current-unit observation, six were deliberate backdated locks,
  two were reset snaps. Verdict (CLAUDE.md line 1147–1155): the dominant whole-tape failure was
  *evidence authority*, not missing lookahead — a local two-of-three band majority overruled an
  agreeing coherent full-width envelope. Transcript 09-02 19:21 UTC "Morning report … the
  lookback verdict". No engine of its own; it decided v6.

## v6 — authority-first, forward-only (2026-09-03)

- **Premise.** Zero presentation FIFO. A coherent full-width envelope plus relative consensus is
  authoritative; coherent top+bottom motion in two broad bands plus same-parity temporal
  corroboration follows per-unit jitter immediately; delta authority bounded to one line around
  an absolute gauge.
- **Record.** `1daad46` "make field registration authority-first" (13:10), `17bf744`, `890fa25`
  "anchor unit-rate registration motion", `79ba2bc` "bound motion authority to an absolute
  gauge"; merged and rendered as the watch copy the owner signed off (transcript 09-03 06:17 and
  08:37 UTC; CLAUDE.md line 1205).
- **Measurements.** Two-truth golden raster 1,017/1,017 (v4: 858), oracle 1,130/1,140;
  full-tape strict coherent-envelope disagreement 10,547 → 1,021 of 55,329; 35–40 min
  follow/hold 0/1,066 → 594/438; 1.466 ms median (line 1146).
- **Owner sign-off, with the caveat that mattered.** "A large improvement"; the remaining jumps
  bring *new* lines into the picture, i.e. recorded-signal instability, not raster position
  (line 1205). Everyone read that as "done except the deck"; it was.
- **Falsified on re-review.** A yadif test of the frameserver's output combed wherever the two
  fields were misregistered; the "bottom landmark falls off the raster" hypothesis was refuted
  (edge moves into rows 257/258); the residual was a *relative-only* class: raw need 0 while the
  engine kept a held (1,0) through 3–19 units of abstention — 132 of 143 classifiable residuals
  were over-corrections (line 1156–1180). Instrument: `static_comb_metric.py` (`71f2227`).

## v7 — relative-only authority (2026-09-03 → 09-04 01:xx, merged `abfa648`)

- **Premise.** A static-region comb search (8-px low-pass, static mask, ≥16-column persistence,
  reweave −3..+3) may *release* a held phase at unit rate when the raster returns; current-unit
  authority only; gauge by differential field identity, minimum-crop when unknown.
- **Record.** `66962f3`, `e7cb33c`, `220765c` "keep relative authority current-unit only"; two
  threshold changes tuned against tape results were reverted before merge (Codex, transcript
  09-03 15:29 UTC "BLOCKED … 1,025 vs 1,021").
- **Measurements.** Misregistered static frames 88 → 29 (first 100 s), 17 → 13 (620 s),
  803 → 268 (2,400 s credits); blip audit 87/97 correct follows, 5 noise (line 1181).
- **Why it was still wrong.** Comb is content: it sees the *relation* between the fields and
  nothing about where either field sits in the raster. The owner's frame-by-frame review with
  the overlay (09-04 morning, line 1214): "severely under-selecting — almost all of its Unknown
  decisions happen during real instability".

## v8 — bottom-edge placement plus comb refinement (2026-09-04, branch `bottom-edge-v8`)

- **Premise.** The owner's placement rule as an instrument: per field the crop's final line
  should be the first mostly-black line under the picture; measure the bottom edge directly,
  learn a per-segment target, apply `edge − target` at unit rate.
- **Record.** `f9a8a1d`, `fb05f9e`, `5aea42e` "place fields from their lower picture boundary",
  `20711c0`, `91e44b3`, `0fc4ade` (all 09-04). Instrument first: `bottom_edge_census.py`
  (`13320a9`) — first minute: raw moved & crop followed 80, moved & held 198, changed & still 69.
- **Measurements.** Pure bottom-only was falsified by the comb metric at 937/2,069 bad frames
  (Codex's own trace); the accepted fusion (bottom = absolute gauge, comb refines `d2 − d1`) gave
  29 → 5 (SP) and 268 → 138 (credits) and census 214/64/34 — but registered the field-1 bottom
  at 256 in 1,038 units and 255 in 546, i.e. the comb overrode the owner's rule in a third of
  the units. Cost 2.75 ms median. Twelve review findings across three rounds; the branch was
  never merged.
- **Why it was wrong.** Still a proxy: one edge of one field, then a content-derived relative
  term to patch what the edge could not see. The owner: "you've settled on this bottom-edge
  thing like it's gold … you have not measured the number of actual picture lines, where the
  top line is and where the bottom line is".

## Two false alarms on the same day (2026-09-04)

- **The counter-wrap preview.** A full-raster preview keyed decisions by the 16-bit device
  counter; the tape's second half overwrote the first half's rows, the first minute rendered
  with decisions from 37 minutes later, and the visible jitter was reported as engine chatter
  (`f80b1f9` fix; LEARNINGS "validate a new instrument against a known reference"). Cost: a
  wrong defect brief to Codex and an hour.
- **Crop origin versus picture origin.** Sequence from both transcripts (UTC, 09-04): 08:29 the
  owner tells Codex "we've been rendering from line 17 instead of line 19 this entire time" and
  Codex calls it a foundational mistake; 08:33 the owner tells Claude the crop should come from
  the standard, and Claude commits 19/282 (`bdac68b`, 08:35) answering with the clean aperture
  alone; 08:36 the owner asks Codex whether analog renders normally show line 21 first, Codex
  agrees ("17/280 is the VBI-preserving window; my 'foundational mistake' conclusion was wrong");
  08:36:50 the owner: "but that's not the problem. OUR render is starting at line 19" (the effect
  of `bdac68b`), and Codex withdraws the 19/282 change and proposes auditing the renderer for a
  bug; 08:38 the owner to Claude: "you are confusing both me and yourselves"; 08:39 Claude reverts
  `bdac68b` (`2930095`) to match Codex's VBI-preserving answer and tells Codex the line-19 render
  was its own commit; 08:41–08:51 the owner asks about the 486-line raster and decides 720×480 =
  clean aperture, 720×486 = alternate mode; `7285d89` restores 19/282 (08:51). The fault was
  Claude's: three coordinate systems (unit rows 17/19, the standard's lines 21/23, the deck's
  regenerated lines versus the tape's) all called "line N" without saying which, which is what
  confused the owner. LEARNINGS "two coordinates, one name".

## The direct signal (2026-09-04 afternoon)

Dumping the luma of rows 12–26 of two units (transcript 09-04 ~09:00 UTC) showed what every
render had displayed on its first row for six days: row 16 is the deck's fixed timing line; row
17 is the deck's regenerated **line 21**, a null closed-caption waveform (seven-cycle run-in,
start bit, two null bytes); the **tape's own line 21** rides exactly on it when the field is
correctly placed and moves *with the picture* when it is displaced (first minute: caption 17 /
picture top 19 in 50/50 units; 19 / 21 in 38/38; EP slice 17 / 19 in 500/500), always two rows
above the picture with the black line 22 between. The picture origin 19/282 is the standard's
first visible line (SMPTE RP-202: 23/286). Field 2 sits there in 1,573/1,800 first-minute units
and 1,800/1,800 in the EP slice. The parity test on raw units (per-field model 202–0 over a
whole-picture display-line shift) settled that field 1 alone moves, as a rigid whole-field
shift (envelope census: 199 rigid moves, top and bottom together).

## v9 — the agreed plan (`docs/registration_v9_plan.md`)

Golden rule: assume the picture is locked at the deck's line 21 unless the tape's line 21 is
found anywhere else in the field; only that changes the lock; one or two jumps near the start of
a recording are acceptable and recorded. Line 21 (blank waveform, no caption data required) is
the primary gauge; the picture envelope (top, bottom, height, black relative to the field's own
blanking, VBI-type lines excluded by signature) is the secondary; black line 22, the next field's
leaky line 21 in the head-switch band, and video above the insert are confirmations. One unit
of memory (no lookahead, FIFO or backtracking), field parity as an atomic invariant, whole
UYVY lines moved, holds always named. Deleted: bands, phase voting, comb authority, temporal
vetoes, candidate searches, dwell, chatter suppression, common-mode arbitration, provisional
trajectories, learned position references. Still to be built and tested.

## The through-line

Every unit carries three layered signals: the Shuttle's digital fill, the deck's regenerated
raster (sync, its timing line, its line-21 insert), and the tape's content (its line 21, the
black line 22, the picture). Registration error is the difference between the last two. Eight
versions reconstructed that difference from the picture alone, through proxies that respond to
content as much as to position, each patched with the next proxy; the direct comparison was
never made because the deck's lines were "VBI" to skip by row number, and because the crop put
line 21 *inside* the picture window where it read as content. The instruments were wrong in the
same way: the census skipped rows 17 and 19 by number and so censored a picture top at 19; the
first VBI probe demanded caption *data* and found line 21 in a tenth of the units it was on.

## Reconciliation with Codex's account

Codex wrote its own excavation from its rollout records and the git objects without reading this
file (`docs/registration_archaeology_codex.md`, committed verbatim as `724a9cb`). The two accounts
agree on every deciding measurement they both cite (the 274–285 wander as estimator noise, the
147 forward-only rows, 10,547 → 1,021, 88 → 29 / 803 → 268, 80/198/69, 29 → 937 for pure
bottom-only, 256 × 1,038 / 255 × 546, 202–0 in the parity test, 19/282). Where they differ:

1. **Partition of the nine.** This file counts v1 (field-2 origin) · v2 (d1,d2) · v3 (C engine
   + rolling) · v4 (FIFO) · v5 (lookback investigation, no engine) · v6 · v7 · v8 · v9. Codex
   counts Python estimator · first C engine · motion/rolling v2 · FIFO v3/v4 · authority-first v6
   · relative-only v7 · the `unknown-hold` experiment · bottom-edge v8 · v9 plan, and states that
   no `v5` exists in repository naming. Both partitions reach nine; the git objects favour
   Codex's split of the C engine from the rolling mode (`phase_history` is absent from `f5b261b`
   and `0f29e37`, present in `14fe5d5`), and this file's v3 section has been corrected above.
   "v5" here is a label for the investigation that decided v6, not a claim that an engine existed.
2. **Where v1 starts.** Codex begins at `4f8b65b` (22:29, the first corrective crop, already
   moving field 1); this file begins at `e811226` (22:15, the field-2-origin premise it
   corrected 35 minutes later). Both are in git; no conflict, different choice of first commit.
3. **The v6 sign-off.** This file said the owner's reading ("the remaining jumps bring new lines
   in — recorded-signal instability, not raster position") was taken as final and "it was".
   Codex calls that interpretation *overturned* by the 09-04 frame-by-frame review and the raw
   parity/envelope measurements (rigid whole-field shifts of field 1, 202–0). Codex is right and
   the sentence here was wrong: at least the rigid-shift class the engine abstained on is
   registration-correctable. Some jumps may still be recorded signal; that is now a per-unit
   question for v9's envelope, not a global verdict.
4. **The `unknown-hold` detour (09-04 12:08–12:12, `7991fa9`, `f605bcd`, not merged).** Omitted
   here; sourced by Codex. It was the direct cost of the counter-wrap false alarm: the sidecar's
   2,475 phase changes on `Unknown*` rows were a real policy inconsistency, but freezing every
   Unknown row worsened both presentation windows because Unknown usually meant "the proxy failed
   while the raster moved". Accepted as an addition.
5. **Why `bdac68b` was reverted — settled from both transcripts.** The revert commit `2930095`
   carries no rationale; the rollouts do. Codex's account (the revert followed recognizing that
   line 21 belongs in a VBI-preserving window) is right: Codex gave the owner that answer at
   08:36:48 UTC and Claude reverted at 08:39 to match it. Claude's first recollection ("Codex
   found the render starting at line 19") was wrong: the OWNER reported the line-19 render to
   Codex at 08:36:50, having seen the effect of Claude's own commit; Codex withdrew the change and
   proposed a renderer audit. The full sequence is in the false-alarm section above.
6. **The 20/283 picture top.** Codex attributes the earlier 20/283 statement in `8f58f37` to a
   line-number interpretation error; this file attributes it to the census skipping rows 17 and
   19 by number. Both are true and sequential: the instrument (`0e349c5`) produced 20 by
   censoring 19, and the research note then justified 20 as "the standard first active line".
7. **v7 denominators.** Codex distinguishes 803/2,871 → 268/2,870 (first run) from
   803/2,869 → 268/2,865 (record-aligned filtering) and warns not to merge them; this file quoted
   only the numerators. Codex's precision is adopted.
8. **Codex's UNSOURCED flags, checked.** The v9 labels `Line21Placement` /
   `Line21OnlyPlacement` / `Line21EnvelopeConflict` and the priority order ARE sourced: they are in
   `docs/registration_v9_plan.md` (`d61ee8e` on main), which Codex's worktree at `0fc4ade` did not
   contain. The SP line-21 row-set counts `(17,) = 1,663`, `(17,19) = 85` and the EP `(17,) =
   1,762` are, as Codex says, transcript-only: they come from `line21_probe.py` in Claude's
   09-04 session over the first 1,800 units and the 1,300 s EP slice, and are recorded here with
   that provenance. The whole-tape envelope census was still running when both accounts were
   written; its result is reported separately when it lands.
9. **Coverage.** Codex's §9 (what each instrument could and could not prove) has no counterpart
   here and is the better reference for that question; the twelve v8 review findings across
   three rounds and the owner's quoted directions are here only, from Claude's transcript.
