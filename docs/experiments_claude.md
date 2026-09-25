# Experiment ledger — Claude

Commitments written and committed before each deciding test, per CLAUDE.md §14 (experiment
commitments). Append-only: entries and amendments are added, never edited. Each report answers its
entry. Results, panels and data stay in scratch; an entry points to them.

**Compaction (owner, 2026-09-21):** "lets compact it and remove experiments which have been refuted. its
not meant to be a graveyard. simple compaction to a 1 line item that failed for anything early that has
been superceded and now has a working version. for the things that we are still investgiating we should
keep them in the ledger and fold the part 2 back in." A one-line item below is a compacted entry: its
verdict is kept so the attempt is not repeated, its working and its reasoning are not.

- **E-claude-2026-09-19-1** — a weave from each field's first picture line is comb free: **refuted**. On captures 2 and 3 the clean weave puts field B's first picture line above field A's, and puts a data line inside the picture; the tops were also unreadable on capture 1's near-blank card and on capture 4's displaced top lines.

## E-claude-2026-09-19-2 — census of the first and last line of real picture

**Question (owner, 2026-09-19):** "Right now, what algorithm is it using to separate pictures from not
picture? What is the census in the 4 caps where the first line of real picture is" — after "I know for
a fact looking at the captures myself the bottom line in every capture being at 262/525 is wrong. I have
seen jumps for sure." Every valid unit, no sampling.

**What fell first.** Entry 1's bottom test (level only) called the deck's flat filler row picture, so it
returned 262 / 525 everywhere; raw rows show the picture ending on a partial line near 261 / 524. Its top
test rejected capture 1's faint partial line 23 and torn capture-4 lines, and passed some data lines.

**Premise.** Rows the Shuttle or the deck generates (blanking, the filler row) are flat, varying by 3
codes or less across the line; real picture, even faint or partial, varies by more and rises above
blanking. Tape data lines at the top are strong rows that do not continue into the picture below, while
a picture line does continue, allowing a horizontal shift for torn lines.

**Method.** Per field, per row, over samples 40-680: bright = 95th percentile minus the device blanking
level; spread = 95th minus 5th percentile. A row is picture if bright > 5 and spread > 4. A row with
spread 40 or more is additionally a data line, and not picture, unless its best correlation with the next
row over horizontal shifts of -24..+24 samples is 0.5 or more. First line: the first picture row from 22
(285) down. Last line: the first picture row from 262 (525) up. Settings of this census, not constants.

**Falsifier.** Raw rows of a census bin showing its line is not the first (or last) real picture line:
a flat or blank row counted, a data line counted, or a picture row above it missed. Every bin (capture,
field, end, line) is checked on raw rows, rare bins included; the census reports how many units sit in
bins the raw rows contradict.

**Material.** Every exact unit: capture 1 from 6667 (fade 6610-6666 apart), captures 2, 3 and 4 whole.

### Report (2026-09-19) — census premise partly held; stopped to ask the owner

Every bin checked on raw rows (up to 3 units each, all bins).
- **Held:** capture 1 field 1 first 23 (493 units), field 2 first 286 (322); capture 2 field 1 first
  24 / 25 (264 / 385), field 2 first 288 (642), bottoms 260 / 261 and 522; capture 3 field 2 first 286
  (649), bottoms 259-262 and 522-524; capture 4 field 1 first 23 (650), field 2 first 286 (516),
  bottoms 262 / 525 (switch debris, counted as the head-switch area).
- **Jumps are real.** Capture 2's field 1 moves as a whole: (first, last) = (25, 261) in 385 units and
  (24, 260) in 264, no other combination; field 2 stays at (288, 522). Capture 3's bottoms move 259-262
  and 522-524.
- **Contradicted:** capture 3 field 1 first 23 (554 units): a faint pulse row, not picture; capture 4
  field 2 first 288 / 289 (134): torn picture at 286-287 rejected as data; capture 2 field 2 first 286
  (3): a data line. Uncertain: capture 2 field 2 287 (4), capture 3 field 1 24 (91).
- **Not observable:** capture 1's card, where 23 / 286 sit at blanking level: field 1 in 15 units,
  field 2 in 186 (the owner's answer is 23 / 286; the raster cannot show it).
- **Amendments measured, none built** (none moved forward): spatial coherence along the line (capture
  3's faint 23 is as coherent as capture 1's card 23: 0.86-0.90 vs 0.96); a wider shift for torn lines
  (topmost torn lines continue at no shift within 120 samples, 0.16-0.39, while capture 2's data line
  286 would pass, 0.76); a scale-free pulse test (misses the faint row, flags 180 capture-1 picture
  rows); the caption run-in (present in only 8-17% of capture 3's line-23 rows).
- **Question for the owner:** capture 3's faint line 23 against capture 1's card line 23, raw rows in
  `explore/line23_question.png`.
- **Capture 3 line 23, labelled from raw rows (2026-09-19):** a faint pulse row (displaced caption
  line: data) in most units, but plainly picture in 120 (runs 13549-13608, 13730-13779, 13877-13894,
  13940-13973; checked on 9 units across 4 runs). With 23 counted only there, field 1 (first, last) =
  (24, 261) in 477 units and (23, 260) in 112: the whole field moves by one line, as in capture 2. No
  detector yet separates the faint row; the label is from raw rows and the owner's displaced-caption
  ruling. Capture 4's torn tops handed to Codex.
- **Capture 4 field 2, from Codex's raw audit** (E-codex-2026-09-19-1, entry e76052f, report 713d2a4
  on v11-codex): first picture line 286 in 559 units, 287 in 64 (286 a pulse row), 27 unresolved. Its
  fragment-matching separator failed (184 of 623; 3 of 30 data controls accepted). Reviewed against its
  entry: it answers every item and discloses that labels were revised after scoring. Checked on raw rows
  at 204 (286), 259, 331, 810 (287): agree. Unresolved 236 and 239 show a faint pulse row at 286 like
  capture 3's line 23; by the displaced-caption reading they would be 287 — a reading, not a measurement.

## E-claude-2026-09-19-3 — comb test redone on the confident census

**Question (owner, 2026-09-19):** "Before I review the census, with the ones it's confident in now, can
it redo the combing test".

**Premise** (entry 1's, retested with better tops): in every valid frame the two fields' first picture
lines are the same source line, so weaving them with slot 1 as the top field and the census tops
aligned is comb-free. Also reported, not the premise: whether the census last lines give the same shift.

**Method.** Tops and last lines from the census as labelled from raw rows: capture 1 23 / 286; capture 2
field 1 24 or 25, field 2 288; capture 3 field 1 23 where plainly picture (bright and continuing into
24), otherwise the first picture row from 24 down, field 2 286; capture 4 field 1 23, field 2 Codex's raw
labels (286 / 287). Slot 1 is the top field; capture 3 pairs slot 1 of u+1 over slot 2 of u, the others
slot 1 over slot 2 of the same unit. Shift = bottom field's top minus top field's top, in field lines.
Judge unchanged from entry 1, with its committed lines 30-240: comb minimum over -5..+5, decided at a
1.5x margin.

**Left out, as unresolved:** capture 1 frames whose field 1 top is not 23 or field 2 top not 286 (the
card where they cannot be seen); capture 2 frames with a field-2 top of 286 or 287 (3 data, 4 uncertain);
capture 3 frames whose census first line was 24 beneath a strong caption (the 91 uncertain); capture 4
frames with no Codex label (27). Counts reported.

**Falsifier.** Decided frames where the census shift is not the comb minimum.

**Material.** Every exact unit of captures 1 (from 6667), 2, 3 and 4 outside those exclusions.

### Report (2026-09-19) — held on captures 1, 3, 4; capture 2 off by a constant line

Decided frames where the census shift equals the comb minimum (frames judged; left out as unresolved):
capture 1 229 / 230 (316 judged; 192 card frames left out; 86 abstain); capture 3 487 / 500 (557; 91
beneath a strong caption and 1 with no partner left out; 57 abstain); capture 4 562 / 567 (623; 27
unlabelled left out; 56 abstain); capture 2 2 / 545 (642; 7 left out; 97 abstain).
- **Capture 2 is off by exactly one line, every time:** census shift 0 with comb -1 in 314 frames (field
  1 top 25), census shift +1 with comb 0 in 229 (field 1 top 24). The census tracks the field-1 jump
  exactly; field 2's first visible picture line (288) sits one source line lower than field 1's. The
  premise (same source line) fails on capture 2 by a constant, not at random.
- **Last lines** give the comb shift in 229 / 230, 0 / 545, 36 / 500 and 505 / 567: weaker than the tops
  on captures 2 and 3, where the last line depends on where the head switch falls.
- Frame-level results: scratch `geometry_exp1/exp3_frames.csv`.

- **E-claude-2026-09-19-4** — line entropy as a picture / no-picture measure: **partly refuted**. Blanking and filler sit apart from picture, but capture 2's data lines (4.85 bits at level 127) fall inside picture's range, and on faint rows the axis points the wrong way — capture 1's faint picture line reads lower on both axes than capture 3's faint row that is not picture.

- **E-claude-2026-09-19-5** — the census against the comb, whole tape, held out: **below the 95% bar at 80.7%** (62,017 of 76,886 decided frames; the comb abstains on 9,060). It also established the pairing schedule still in use — reversed through 47,995, aligned 48,188–81,361, mixed to 85,123, aligned after.

## E-claude-2026-09-19-6 — does capture 3's line 23 carry luma at 13784-13791?

**Question (owner, 2026-09-19), on the sparkle row above the picture:** "its color noise because thats
how bwdiff interpolates it, but it absolutely has a real luma component I'm pretty sure."

**Premise (the owner's).** Field 1's line 23 in capture 3 units 13784-13791 carries a luma signal of
its own, not blanking. Two readings fit a line with little luma and strong colour noise: (a) a picture
line whose luma follows the picture below it; (b) the tape's own blank line, carried down one line with
the picture, at blanking level with tape noise, its colour the chroma noise of a line with no colour
content.

**Method.** Raw slot-1 rows of those eight units (session scratch
`render_findings/cap3_13782_13791_uyvy.npz`, cut from capture 3's file), samples 24-695. Per unit:
luma mean and SD of line 23, of line 22 (deck-blanked) and of field 2's line 285 (blank). Following the
picture: correlation of line 23 with line 24 after an 8-sample moving average, in luma and in each
colour difference, against two controls: line 22 with line 24 (a blank line), and line 23 with line 24
of the unit five away (the same kind of line, other content).

**Falsifier.** Line 23's luma mean is within 1 code of the blank lines' and its luma correlation with
line 24 is no higher than both controls'. If its level or noise differs from the blank lines while it
does not follow line 24, that is reported as luma that is not picture: reading (b).

**Material.** Capture 3 units 13784-13791, slot 1; controls from the same units.

## E-claude-2026-09-19-7 — a blank line between picture lines means the placement is wrong

**Question (owner, 2026-09-19):** "the important thing is there is a blanked line between the two. that
is structurally impossible and deifnitely prove the registration is wrong. so the question I have, if
field order, stays constant, how is it possible that a line of real picture ended up ABOVE a line of
blanking. is that part of what we are missing in the tracking? does it need to be something more along
the lines of, if field 2's first picture line is above field 1, that forces field 1 down a line...
which that recalculates its own geometry because by forcing it down a line one of its bottom lines is
going to shift down"

**Premise (the owner's).** In a correct weave the picture fills one unbroken block of output rows. The
two fields' first picture lines sit on adjacent rows with no row of the other field between them, and
so do their last picture lines. Moving a field to fix one edge moves its other edge too, and that edge
has to fit as well.

**What it means for a placement.** Let d be the bottom field's shift against the top field, as the comb
judge measures it (field lines; the weave puts bottom-field line k+d directly under top-field line k).
Let st be the bottom field's first picture line minus the top field's, and sl the same for the last
lines (field-2 lines less 263). The top edge is unbroken only for d = st (the top field's line comes
first) or d = st+1 (the bottom field's line comes first). The bottom edge is unbroken only for d = sl
or sl+1. Any other d leaves a row of one field that is not picture between picture rows of the other.

**Three claims, tested separately:**
- A, necessary: the comb-free weave leaves both edges unbroken.
- B, what the tracking misses: every frame whose render placement differs from the comb's breaks an
  edge, so a one-frame check would have caught it.
- C, the rule's second half: at the upward moves from the render review (capture 3 13575,
  13601-13603 and 13779; capture 4 597), the moved field's last picture line rises by one while its
  first line stays. The placement that moves that field down one line, putting its last line back
  where it was against the other field's, is the comb's.

**Method.** Frames and lines as in entry 3 (scratch `geometry_exp1/exp3_frames.csv`: confident census
tops, census last lines by entry 2's rule, comb verdicts at 1.5x). Count decided frames where the comb's
d is in the top pair, in the bottom pair and in both, and how often the two pairs together leave
exactly one d and it is the comb's. Capture 2 is reported with its raw census tops and with field 1's
top taken one line lower, as the renders do. For B, use each render frame's applied placement (scratch
`geometry_renders/cap*_offsets.csv`) and the comb verdict for the same frame, recomputed where entry 3
left the frame out. For C, use the census lines of the units either side of each move and the comb.

**Falsifiers.** A: more than 5% of a capture's decided frames break an edge under the comb's d. B: any
decided frame whose applied placement differs from the comb's with both edges unbroken. C: at a listed
upward move, the last line does not rise by one, or the comb's d is not the one that moves the field down.

**Material.** Captures 1 (from 6667), 2, 3 and 4, as in entry 3. The flagged frames are raw-row
checked, with panels, before anything is reported about them. The whole tape (held out) is not in this
entry; its per-unit files hold no last lines.

### Report on entry 6 (2026-09-19) — no picture luma; the colour is the picture's

Verdict: the premise is refuted for picture luma. There is some luma above blanking, but it does not
follow the picture. The finding the premise did not ask about: the line carries the picture's colour.
- **Luma.** Line 23's mean is 1.75-2.64 against 1.36-1.39 on the blank lines 22 and 285: within 1 code in
  7 of 8 units, 1.27 above in 13791. Its SD is 1.3-2.5 against 0.48, from short bursts of 7-18 codes on
  2-5% of samples. Correlation with line 24 is -0.24 to 0.13. That is above both controls in 2 units by
  less than the controls' own spread (-0.25 to 0.12). The bursts sit at line 24's 38th brightness
  percentile against 65th for shifted positions, so they are not the picture's brightest parts
  showing through.
- **Colour.** U and V on line 23 correlate 0.66-0.83 and 0.64-0.86 with line 24. That matches line 24
  against line 25 (0.54-0.90), against about 0 for the blank line 22 and -0.15 to 0.45 for other
  content. The amplitude also matches: U SD 13-20 against 11-23, with a regression slope of 0.6-1.2.
  In colour, line 23 is a picture line; in luma, it is blank. Calling it "colour noise" in the sparkle
  answer was wrong. bwdif's bright speckle is that colour on a luma-black row between the Shuttle's
  bright insert rows.
- Not understood: whether the tape, the deck or the Shuttle removed the luma and kept the colour.
- Raw rows and panel: session scratch `render_findings/e6_line23*.py`, `e7/cap3_13785_line23_colour.png`.

### Report on entry 7 (2026-09-19) — A held; B refuted; C held on raw rows

- **A held.** The comb-free weave leaves both edges unbroken in 230 / 230 decided frames on capture 1,
  499 / 500 on capture 3, 565 / 567 on capture 4, and 542 / 545 on capture 2. For capture 2 that needs
  the owner's reading that field 1's visible first line is leaky line 22, not picture; with the raw
  census tops only 2 / 545 pass. The six exceptions are capture 3 13575, capture 4 395-396 (comb +2 and
  -1 on nominal lines; not examined) and capture 2 67451 / 68025-68026 (bottom).
  13575 is real. Field 2 moved up one line in unit 13575 (last line 260 -> 259, top 286 kept, content
  +1 at a 1.47 ratio), and its first picture line slid under the deck's fixed blank line 285. The
  comb-free weave then has that blank line inside the picture. The block rule must allow the deck's
  fixed blank lines (22 / 285) where a moved line was lost.
- **Structure alone often fixes the placement.** Where the two fields' picture heights differ by one
  line, the top pair and bottom pair share exactly one d. That happened in 459 / 500 frames on capture
  3, 544 / 545 on capture 2 (offset), 57 / 567 on capture 4 and 0 / 230 on capture 1; the shared d is
  the comb's in 1,058 of 1,060. Where the heights are equal, two placements a line apart both leave the
  block unbroken, and something else has to choose.
- **B refuted.** Of 79 decided frames whose render placement differs from the comb's, an edge check
  flags 53: all 52 on capture 3, including all seven the owner flagged (13783-13789, top broken), and
  capture 2 1969. Ten have an edge the census could not measure. 16 misplacements leave both edges
  unbroken, every one with equal heights: capture 1 6929; capture 2 2489-2490; capture 3 13587, 13601,
  13779, 13939, 13950, 13957, 13961, 13972; capture 4 391-392, 395-396, 597.
- **C held on raw rows, for either field.** Capture 3 unit 13602, field 1 (frames 13601-13603): first
  line 23 kept, last 260 -> 259, content +1 (1.57); comb +1, field 1 one line down. Capture 3 unit
  13575, field 2 (frame 13575): as above; comb -1, field 2 one line down. Capture 4 unit 597, field 1:
  first line 23 kept, raw line 262 91.5 -> 8.5 (last 262 -> 261), content +1 (1.70); comb +1. Entry 2's
  bottom rule still read 262 there, so that census misses this move. Capture 3 unit 13779, field 1
  (frame 13778): first line kept, last 260 -> 259, comb +1 but abstaining (1.38).
  The listed frame 13779 was not an upward move: field 1 of unit 13780 went down, its first line from
  23 to 25 (24 blank, 23 caption-like) while its content moved about two lines down from 13779's. The
  census top put d at -2, the comb at -1, and both leave the block unbroken. Not understood.
- **Amendments:** none. Frame-level results: session scratch `e7/e7_frames.csv`, `e7/e7.out`; panels
  `e7/cap3_13785_weave_top.png`, `e7/moves_top.png`, `e7/moves_bottom.png`.

### Corrections to the reports on entries 6 and 7 (2026-09-19, from an independent recount)

A blind recount from the raw data, with its own code, matched every number except these:
- Entry 6: the luma bursts on line 23 are 7-24 codes on 1.6-7.0% of samples, not 7-18 on 2-5%.
  13791's mean is 1.26 above its own line 22.
- Entry 7, B: 14 of the 16 misplacements with both edges unbroken have equal heights, not all 16.
  Capture 2 2489-2490 (whole-tape 68025-68026) have unequal heights. There the edges alone leave the
  applied d = -1, and the comb, decided at 1.53 and 1.63, gives 0. These are the two capture-2 frames
  where the shared d is not the comb's, and two of A's six exceptions. Not examined on raw rows.

### Review by Codex (2026-09-19) — six findings, all accepted

Codex agreed with the pair algebra (the rows between the fields' first lines are 2(st-d)+1). It also
agreed that frame 13575 is field 2 moving up under the deck's blank line 285 (occlusion; the erased
line cannot be inspected), and that "13779" was a frame-versus-unit slip. Its findings, now part of
the verdicts:
1. Entry 6's verdict was stronger than its committed falsifier allows. The falsifier holds in 5 of 8
   units. It fails in 13784 and 13788, where the luma correlation with line 24 (0.128, 0.106) is above
   both controls, and in 13791, 1.26 above blanking. Excusing those by the controls' spread was a
   tolerance not in the entry. Amended verdict: unknown for luma, with no consistent picture-following
   luma shown. The colour result stands.
2. Burst range (already corrected above).
3. Entry 7 A, capture 2 with its raw tops: both edges unbroken in 0 / 545, not 2 (2 is the top edge
   alone). A holds on capture 2 only when field 1's top visible line is read as leaky line 22.
4. The unequal heights at capture 2 2489-2490 (already corrected above).
5. C held at the three decided upward moves (capture 3 unit 13602 field 1, unit 13575 field 2, capture
   4 unit 597 field 1). The fourth, unit 13779 field 1 (frame 13778), abstains at 1.378. The listed frame
   13779 was not an upward move. Unit 13780's content moved down, but `moves.py` searched only +-2
   lines; searched wider, it weakly prefers three (MAD 10.50 against 11.15). The size is unresolved.
6. B's population included 412 capture-1 frames before 6667, outside the entry: 2 decided, 410
   abstaining, no disagreements. The 79 disagreements are unchanged.
Codex's evidence: its scratch `/private/tmp/codex-e6-e7-review-Je7000/REVIEW.md`.
Codex's check of this section (2026-09-19): two wording corrections, otherwise accurate.
- Entry 6's falsifier requires line 23's correlation to be "no higher than both controls". Read
  literally (no higher than either), it holds in 1 of 8 units (13786), not 5. The 5 counts units not
  above both. The verdict, unknown for luma, is unchanged.
- 2(st-d)+1 is the signed separation of the two first lines' output rows (1 means adjacent), not the
  number of rows between them.

- **E-claude-2026-09-19-8** — the unbroken-block rules on the whole tape: **refuted, and a regression** — 56.9% against entry 5's 80.7%, with capture 3 at 26.9% against 91.3%.

## E-claude-2026-09-19-9 — does the whole-tape census reproduce captures 2 and 3?

**Question (owner, 2026-09-19):** "does the "whole tape consensus" reproduce the cap2,3 results for
those same units. if it doesn't, then the algorithm is probably not implemented properly"

**Premise.** Captures 2 and 3 are byte slices of the whole tape. Where the whole-tape pass (entries
5 and 8) and the capture runs (entries 2, 3 and 7) apply the same rule, they give the same answer on the
same units. That covers first and last lines by entry 2's rule, the comb's verdict, and the placement
and edge pairs computed from the same inputs.

**Method.** On every overlapping unit (capture 2: whole-tape counters 67,446-68,094; capture 3:
13,501-14,149), compare per field:
1. entry 2's first and last lines, capture census against the whole-tape pass;
2. the comb verdict and margin per frame (capture 3 reversed, capture 2 aligned), entry 3 / 7 against
   entry 5;
3. the first lines used for placement: entry 3's confident tops and the renders' tops against entry 5's
   automatic tops, with every mismatch classed by the rule difference that produces it;
4. entry 7's edge-pair classes, recomputed with the whole-tape pass's code from entry 7's inputs, and
   the reverse.
Where entries 7 and 8 differ, separate the inputs that differ (tops, rule 2's count carried in from
units before the capture) from the code.

**Falsifier.** Any mismatch in items 1, 2 or 4, or any item-3 mismatch not produced by a stated rule
difference. Either is an implementation error to be found.

**Material.** The 649 units of capture 2 and 649 of capture 3 and their frames.

### Report on entry 9 (2026-09-19) — reproduced; no implementation error found

Verdict: the premise held. A blind recount from the data files, with its own code, matched every number.
1. Entry 2's lines, capture census against the whole-tape pass: identical on all 649 units of each
   capture, first and last line, both fields.
2. Comb verdicts: identical in shift and margin on every frame (entry 3: capture 2 642, capture 3 557;
   the renders: 649 and 648).
3. Placement first lines: identical on every frame entry 3 judged (capture 2 642, with its one-line-
   lower reading; capture 3 557). The only differences are frames entry 3 left out by rule. Capture 2:
   7 with field 2 at 286 / 287. Capture 3: 91 with field 1's first line 24 by rule, and 1 with no
   partner. Entry 5 places those automatically.
4. Rule 1's pair classes: identical frame by frame whether entry 7's inputs or the whole-tape inputs
   go through entry 8's code (capture 2 543 / 545 agree with the comb, capture 3 491 / 500).
- **The only difference between entries 7 and 8 on these units is rule 2's count.** Entry 7 checked
  upward moves one by one and never ran the count. With the count, capture 3 falls to 150 / 500 as
  carried in from the tape (field 1 at 1, field 2 at 2 when capture 3 begins). Restarted at capture 3's
  first unit, it still falls to 174 / 500. The count is nonzero on 378 of capture 3's 649 units for
  field 1 and 550 for field 2. Capture 2 stays at 541 / 545. Entry 8's regression is rule 2 as
  committed, on the capture as on the whole tape, not the whole-tape code.
- Scratch: `geometry_exp1/e9_repro.py` / `.out`.

### Review by Codex of entry 9's report (2026-09-19) — one finding, accepted; the missing comparison run

Codex: the entry promised to compare the renders' tops as well, but the script compared only entry 3's.
So "the only difference ... is rule 2's count" holds for entry 3's 545 / 500 judged frames, not all
render inputs. Codex reproduced 543 -> 541 / 545, 491 -> 150 / 500 and 174 / 500 within that scope.
The promised comparison, now run over every render frame (`e9_repro.py` item 3b):
- Capture 3: the renders' first lines equal the whole-tape pass's on all 648 frames, both fields.
  That includes the 91 frames entry 3 left out, where the renders took the raw census's 24.
- Capture 2: 642 of 649 frames equal. The 7 that differ are exactly those entry 3 left out:
  - At all 7, the renders have no field-2 top, while the whole-tape pass has 286 / 287.
  - At 3 of them (67467, 67557, 68065, field 2 at 286), field 1's top differs as well: 26 in the
    renders, 25 in the whole-tape pass. The renders applied capture 2's one-line-lower reading to every
    frame. The whole-tape rule applies it only when the line above field 2's first line is not blank,
    and line 285 is blank there.
  These are differences between rule versions, not code errors; neither involves rule 2's count.

### Correction to entries 7 and 8: rule 2 was not the owner's rule (2026-09-19)

Entry 8's premise called both rules "the owner's". Rule 2 was mine. His sentence (05:59) puts the cause
at the top: "if field 2's first picture line is above field 1, that forces field 1 down a line...
which that recalculates its own geometry because by forcing it down a line one of its bottom lines is
going to shift down". The bottom shifting is the consequence of the move, and the geometry is recomputed
after it. Entry 7's claim C made the bottom the evidence, because an upward move cannot be seen at the
top when the field's first line slides under 22 / 285. Entry 8 made that the trigger, through a
running count.

His later message (10:17) defines the bottom line rising as blanking: "partial blanking along a line
or the entire line being blanked as the bottom line rising". Entry 8 measured something else: entry
2's threshold line (5 codes, spread 4) moving by one.

So entry 8 tested my inference, not his rule, and its regression says nothing for or against his rule.
Entry 8's rule 1 results and its measurements stand as reported.

### Owner's rulings on the bottom rule and the blank line (2026-09-19, relayed verbatim by the watchdog)

- 10:31, the bottom: "if 523 was blank and then it becomes partially blank, then the bottom should shift
  DOWN to 523, which basically means both the top and bottom moved right. ... what I meant was a line
  that had normal luma/chroma and BECAME blank, but the inverse (what i discussed above) is absolutely
  evidence that the shift went in the OPPOSITE direction. but yes, my intent originally was if a line
  suddenly increased blanking and the rest of the geometry didn't shift, then yes, re-run the comb
  search". "Above" means the woven frame.
- 10:38, the light line: "the light line should be field 1. the important property is a blank line
  can't sit between the light line and the next real picture line." He hedged the geometry: "don't
  quote me on that".
- 10:44, after the comb put the black line (field 2's deck-blanked 285) between the light line and
  the picture at 13783-13790, one line from his fix: "I guess if the deck blanked it... I guess it
  doesn't really matter if you shift field 1 or field 2 against its each. mathematically its the same
  thing. yeah in that case the existing blank line was a red herring... my bad. it can't be used to
  proxy anything, except its existence should absolutely mean rerun the comb because that is extremely
  nonstandard".

**The rule as it now stands.** "Placement" means a rule that sets d; "re-run" means a reason to run the
comb search again, where the comb sets d.
- A blank line between picture lines in the woven frame (10:44): **re-run**. It is not a placement
  gauge, since a deck-blanked line can sit inside a correct weave (13575, 13783-13790).
- Rule 1, the unbroken block: the same observation, so by the 10:44 ruling it is **re-run**, not
  placement. On the whole tape, where it decided it matched entry 5's placement (96.8% against
  96.7%), so as a placement rule it added nothing measured.
- A line on the bottom gaining blanking while the rest holds (10:31): **re-run**. It is evidence the
  picture moved up. A blank line gaining picture is evidence it moved down; the comb decides.
- The top relation (05:59): **describes the result, not placement or re-run.** It describes the placement the
  comb finds after an upward move: the other field's line first, and the moved field one line down with
  its bottom recomputed. The first lines cannot show it (they do not change at an upward move), so it
  is neither a trigger nor a placement rule by itself. For him to confirm.

## E-claude-2026-09-19-10 — does the restated rule set reproduce the comb results without regression?

**Question (owner, 2026-09-19):** "lets make sure if we lock down on what the rule set is, we are able to
get the same combing result since we subtly changed thing so I don't want another regression."

**Premise.** The restated rule set keeps every frame the existing census placement got right and does
not lose one. The rule set: the census placement between comb searches, the comb's placement where the
search re-runs, and a re-run at a blank line inside the picture or at a blanking change on the bottom
line. The comb is also the judge, so wherever the rule set consults it, it agrees by construction. The
informative results are: frames lost against the census placement; the census placement's
disagreements the triggers catch and the ones they miss; how often each trigger fires.

**Two readings of "between comb searches", both run.**
- A: a triggered frame where the comb decides takes the comb's d; every other frame takes the census d.
- B: at such a frame the correction c = comb d - census d is kept, and every frame takes census d + c
  until the next decided re-run. c returns to 0 after a gap.

**Triggers, per frame.**
- T1, a blank line inside the picture: under the placement the frame would otherwise take, an edge
  pair is broken (entry 7's algebra), d not in {st, st+1} or not in {sl, sl+1}.
- T2, a blanking change on the bottom line, the owner's 10:31 definition, in either field of the frame
  against the same field of the previous unit. For each of the field's last 12 lines (NTSC 251-262 /
  514-525), a line's picture extent is its count of samples 24-695 whose 8-sample luma average is more
  than 20 codes above the device blanking. The bottom line is the last line with 8 or more.
  - T2 fires when the bottom line changes: a picture line has gone wholly blank, or a blank line has
    gained picture.
  - It also fires when the same bottom line's extent changes by more than 64 samples (partial blanking
    grows or shrinks).
  These numbers are this experiment's settings.

**Material and comparison.**
- Captures 1 (from 6667), 2, 3 and 4 on entry 3's judged frames and inputs: confident tops, capture 2
  read one line lower, census last lines, entry 3's comb. Entry 3's figures are 229/230, 543/545,
  487/500 and 562/567.
- The whole tape on entry 8's judged frames and inputs: entry 5's tops and comb, entry 2's last lines.
  The census placement's figure is 62,017 / 76,886 (80.7%).
- The bottom extents are a new pass over every unit (the whole tape) and the capture caches.
- Frame by frame: every frame whose verdict changes, and why.

**Falsifier.** Any judged frame the census placement got right and the rule set gets wrong.

### Report on entry 10 (2026-09-19) — A held (no frame lost); B refuted (25 lost)

A blind reimplementation from this entry's text reproduced every number below. It resolved three
readings the same way I did:
- A missing last line leaves only the top edge for T1.
- A change between "no picture line" and a picture line is a T2 change.
- The judge's 1.5 is inclusive; seven stored margins are exactly 1.5.
The census placement reproduces entry 3's per-capture figures and entry 8's whole-tape 62,017 / 76,886.
- **Captures (entry 3's judged frames), A and B identical, no frame lost:**
  - capture 1: 229 / 230 (census 229);
  - capture 2: 543 / 545 (543);
  - capture 3: 498 / 500 (487; caught 13575, 13587, 13601-13603, 13758, 13779, 13939, 13950, 13967,
    13972);
  - capture 4: 567 / 567 (562; caught 391, 392, 395, 396, 597).
  T2 caught capture 4 597, which entry 2's bottom line had missed. Triggers fired on 14 of 316 frames
  (capture 1), 234 of 642 (capture 2), 72-73 of 557 (capture 3) and 37 of 623 (capture 4).
- **Whole tape, A:** 67,909 / 76,886 (88.3%, from 80.7%), 0 lost. It caught 5,892 of the census's
  14,869 disagreements: 3,720 by T1 alone, 993 by T2 alone, 1,179 by both. It missed 8,977, frames
  where the census is wrong and no trigger fired. By segment: 89.4%, 80.5%, 88.2%. Triggers fired
  on 14,224 of 85,946 frames (16.5%): T1 6,551, T2 9,200, both 1,527.
- **Whole tape, B:** 72,348 / 76,886 (94.1%), with 25 lost. It caught 10,356, 3,461 of them by a
  held correction on untriggered frames, and missed 4,513. Triggers fired on 16,489 frames (19.2%):
  T1 10,177, T2 9,200. Every lost frame is untriggered, with a held +1 gone stale while the census was
  right: 16 runs of 1-3 frames, 24 in the first recording (4817-35666) and 1 at 60882.
- **Verdict.** A: premise held. No judged frame the census got right is lost. That is guaranteed
  wherever the comb is consulted, and the census is reproduced exactly elsewhere. B: premise refuted,
  25 frames lost. Neither reaches the 95% bar.
- **Not understood:** the 8,977 frames A misses, where the census is wrong without either trigger
  firing. Also why capture 2's bottom changes so often (T2 on 36% of its frames).
- Scratch: `geometry_exp1/fulltape_exp10.py`, `exp10_w{1..4}.csv`, `exp10_analysis.py` / `.out`,
  `exp10_changes.csv` (every changed frame).

### Review by Codex of entry 10's report (2026-09-19) — two findings, accepted

Codex reproduced the totals and all 29,805 changed-frame records, B's 25 losses included. It agreed that
T1 and readings A and B follow the entry, and that A's no-loss guarantee is stated with its circularity.
Genuine T2 catches check out on raw rows: capture 4 597, line 262, extent 576 -> 48. Findings:
1. **T2 measures brightness coverage, not blanking specifically.** Some firings are brightness crossing
   the 20-code cutoff on a line whose profile barely changes. Capture 2 67662 -> 67663, line 522: 533 ->
   602 counted samples, from a median rise of 1.9 codes, profile correlation 0.9997; the line below
   stays near 11. 67633 -> 67634 reports 581 -> 515 on nearly identical profiles. The 36% on capture 2
   is the proxy's firing rate, not measured bottom movement.
2. **T2 lacks the owner's condition that "the rest of the geometry didn't shift".** On 224 of capture 2's
   234 firings, field 1's first and last lines both move by one line (112 up, 112 down; for example
   67633 -> 67634, 24 -> 25 and 260 -> 261). These are whole-field moves, which his trigger would
   exclude. That explains the "not understood" frequency. The implementation follows the committed
   method, which is broader than his conditional event.
Neither finding changes any number or A's verdict. They limit what T2's firing counts mean: T2 as run is
a brightness-coverage proxy without his "rest held" condition, not his blanking trigger as he stated it.

## E-claude-2026-09-19-11 — the either/or rule: a valid move is top and bottom in tandem

**Question (owner, 2026-09-19, 10:57):** "yeah it should be either/or. ... In order for it to be a valid
move, both top and bottom half of the field have to move in tandem. otherwise, rerun comb check to
realign. assuming that answer and also have it reproduce cap1-4 in the same folder assuming the
experiment and comb check holds. for the full tape it has to be 80% or better. reproducing the same
result full tape isn't necessary. if we get to like 95 % or better full tape, then the next step will to
be to build this to an engine." And (11:00): "that tiny variance, losing under 100 frames across the whole
tape is NOT an invalidation. there are obviously going to be weird one offs we need to figure out."

**Premise.** Re-running the comb whenever a field's top and bottom do not move together, and whenever a
blank line sits inside the picture, keeps the frames the census gets right and catches enough of the
rest for 80% or better on the whole tape.

**Method.** Readings A and B, the placement and T1 all as in entry 10. The field-level trigger replaces
entry 10's T2. It follows the owner's 10:31 and 10:57 words and Codex's two findings on entry 10:
blanking is judged by a real change on the line, and a move of top and bottom together fires nothing.
- **Bottom lines, per field and unit.** The field's last 12 lines (NTSC 251-262 / 514-525), samples
  24-695. A sample is blank when its 8-sample luma average is within 12 codes of the device blanking.
  The bottom line is the last line with 8 or more non-blank samples.
- **Changes against the previous unit of the same field:**
  - A sample gains blanking when it turns blank and its average falls by more than 20 codes. It gains
    picture when it turns non-blank and its average rises by more than 20. Brightness drifting across
    the level is not a change.
  - Bottom move Δb: the change of the bottom line, in lines (+ = down). It counts only if the lines
    between the old and new bottom lines gained blanking (up) or picture (down) in 8 or more samples;
    otherwise Δb = 0.
  - Partial change: Δb = 0, but the old bottom line and the line below it gained blanking or picture
    in 64 or more samples.
  - Top move Δt: the change of the first line used for placement.
- **Classes per field:**
  - nothing (no top move, no bottom move, no partial change);
  - valid move (Δt = Δb, not 0, no partial change): no re-run;
  - bottom only (Δt = 0 with a bottom move or a partial change);
  - top only (Δt not 0, Δb = 0, no partial change), the owner's either/or;
  - both but not in tandem (anything else).
  The last three re-run the comb. With no previous unit, or no first line, nothing fires.
- **A frame re-runs** on T1 or on a re-run class in either of its fields.
- **Material and inputs:** as entry 10. Capture 2's field 1 is read one line lower on both the
  placement and its top moves.

**Report.** For A and B, per capture and for the whole tape:
- agreement with the comb, against the census's figures and the owner's 80% and 95% marks;
- every frame lost against the census, listed;
- what the re-runs catch and miss;
- how often each class fires, and how the bottom-only firings compare with entry 10's T2.

**Falsifier.** For a reading: the whole tape below 80%, or 100 or more lost frames on the whole tape.
Fewer than 100 are the owner's one-offs, listed, not a failure.

**Renders if a reading holds.** Captures 1-4 at the same paths, replacing the earlier renders, with the
reading Codex and I judge better, named. Same renderer (`experiments/geometry_render.py`) and command.
Each is written under a new name and moved onto the old path in one rename. The placement for every
render frame comes from the rule set, run on the renders' own per-frame inputs (entry 7's), with the
comb's correction applied to field 1. The owner: "it doesn't really matter if you shift field 1 or field
2 against its each. mathematically its the same thing".

### Amendment 1 to entry 11 (2026-09-19, before the report): an unmeasurable field re-runs the comb

**Owner (11:18):** "if one field can't be measured, absolutely the comb checks should be re-run. I noticed
that looking through its own output."
- **The trigger, U.** A frame re-runs the comb when either of its fields lacks a first picture line, a
  last picture line or entry 11's bottom line in that unit.
- **Physical reason.** Without a field's edges, neither rule 1 nor the either/or classes can say
  whether the placement still holds, so the comb has to.
- **What it should improve.** Frames with a missing edge:
  - capture 4's 9 render frames with no field-2 label;
  - the whole tape's frames with no field-2 last line, and its 22 frames with no first line. Those
    had no census placement at all; they are now placed by the comb where it decides, and reported
    apart from the census comparison.
- **What it must not break.** Any frame the census gets right. It cannot lose one: where the comb
  decides, it agrees by construction.

**The owner's two-valued confidence, reported with it** (his 05:42 words: "high confidence decisions
(where both top and bottom shift at the same time of one field) which results in a standard adjustment
vs where one shifts or when a line gets partially blanked, resulting in having to run the combing
detection algorithm"):
- HIGH: no trigger fired (nothing moved, or a valid move), so the census placement stands.
- LOW: any trigger fired, so the comb's answer is applied where it decides. Where it abstains, the
  placement stays unconfirmed.
For A and B, reported: HIGH frames and their agreement with the comb, and LOW frames split into decided
and abstaining. My four-level proposal (11:12) stays on file, unbuilt, as the fallback if his fails
(owner: "if my proposal fails, we can build its more complex confidence one").

### Amendment 2 to entry 11 (2026-09-19, before the report): an unmeasurable move also re-runs the comb

**What amendment 1 broke.** In reading B, on capture 4's render frames, amendment 1 lost 44 frames
(546 / 590 against the comb, from 581 / 590). At 236 field 2 has no label, so U re-ran the comb, which
correctly gave +1 for that frame. From 237 on, field 2's move against the unlabelled 236 cannot be
classed ("unknown"), so nothing fired, and B held the stale +1 until the next trigger. Reading A lost
nothing (590 / 590).
- **The trigger.** A field whose move against the previous unit cannot be classed re-runs the comb.
  That covers a missing first line, last line or bottom line in either unit, and no previous unit.
- **Physical reason.** This is the owner's "if one field can't be measured, absolutely the comb checks
  should be re-run", applied to the move as well as to the unit. Without a measured move, the either/or
  rule cannot vouch for a held placement.
- **What it should improve.** B's stale holds after an unmeasured frame, such as capture 4 237-809.
- **What it must not break.** Reading A anywhere; B's whole-tape 99.0% and its 28 lost frames.

### Report on entry 11 (2026-09-19) — held for both readings; B passes the 95% mark

Checks: a blind reimplementation reproduced the run before the amendments, every number. Codex reviewed
the run and both amendments, reproduced all totals and all eight render offset files, and chose reading
B. Its two findings, accepted:
- Flat rows at Y 10-14 below the picture can be picked as the bottom line, costing extra comb checks,
  not losses. Example: capture 2 67481, a one-line move of top and bottom classed "not in tandem".
- Amendment 2's code missed the previous unit's census last line. Now fixed: frame 84310 goes from
  HIGH to LOW (the comb abstains), and no total changes.
Numbers below are with both amendments and the fix.
- **Verdict:** premise held for both readings. A: 89.7% on the whole tape, 0 lost. B: 99.0%, 28 lost,
  under the owner's 100. Both clear his 80%; only B reaches his 95%.
- **Captures (entry 3's judged frames), A and B identical, 0 lost:** 229 / 230, 543 / 545, 500 / 500 (from
  487), 567 / 567 (from 562).
- **Whole tape by segment:** A 90.2%, 85.5%, 89.8%; B 98.8%, 98.7%, 99.4%. A caught 6,977 of the census's
  14,869 disagreements and missed 7,892; B caught 14,156 and missed 713.
- **B's lost frames:** 8600, 11127-11129, 12800, 14371, 14373-14377, 19898-19901, 19903-19905, 32911,
  33848, 35666, 60882, 60896, 60897, 60910, 60911, 60913, 60914. Every one is untriggered, with a held
  correction gone stale.
- **Firing, whole tape (85,946 frames):**
  - T1: 6,551 (A), 11,255 (B).
  - Field classes: bottom only 2,690, top only 6,989, not in tandem 1,173, move unclassable 95.
  - U: 58, always together with an unclassable move.
  - Any trigger: 14,333 frames (16.7%, A), 15,663 (18.2%, B).
  - The new bottom-only class fires on 2,690 frames against entry 10's T2 on 9,200; 2,643 are shared.
  - Captures: 14, 120, 72 and 75 frames. Capture 1's are all unclassable moves.
- **Amendments:**
  - Amendment 1 (U) caught no judged disagreement. It placed 5 of the 22 frames with no first line. It
    regressed B on capture 4's render frames (44 lost).
  - Amendment 2 moved that forward to 1 lost (794: the re-run at 793 abstained, and B kept the +1 from
    792). Neither changes the whole tape or the capture totals.
- **The owner's two-valued confidence:**
  - Whole tape, A: HIGH 71,613 frames; 64,693 judged, 87.8% agree with the comb. LOW 14,333 frames: the
    comb decided in 12,193 and abstained in 2,140.
  - Whole tape, B: HIGH 70,283 frames; 63,708 judged, 98.8% agree. LOW 15,663: decided 13,178, abstained
    2,485.
  - Captures: HIGH agrees in 99.5-100%.
- **Renders (reading B)** replaced captures 1-4 at the same paths, each moved over the old file in one
  rename.
  - Frame counts are unchanged: 922, 649, 648 and 650.
  - The machine strip read back from every frame of every file matches the offsets used: 0 mismatches.
  - On the render inputs, placement agrees with the comb in 372 / 373, 549 / 551, 586 / 586 and 589 / 590
    (capture 4's 794).
  - Each frame's band says whether it is the census, a comb re-run or a held comb correction.
- **Circularity:** where the comb is consulted, it agrees by construction. B's lead over A comes from
  corrections held between re-runs, which the comb confirms on 98.8% of HIGH frames.
- **Not understood:** B's 713 missed frames, and capture 2's two misses.
- Scratch:
  - geometry_exp1/: `fulltape_exp11.py`, `exp11_w{1..4}.csv`, `exp11d_analysis.py` / `.out`,
    `exp11d_changes.csv`, `exp11d_render_offsets.py`;
  - geometry_renders/: `cap*_offsets_e11dB.csv`, `e11_readback.py`.

- **E-claude-2026-09-19-12** — one comb check per section instead of per frame: **refuted**. The misalignment is not constant within a section (segment C: −1 on 25,083 frames, 0 on 4,413, +1 on 1,915), so a fixed per-section offset agrees on 0.2% and 2.6% against 78.2% and 80.3%.

## E-claude-2026-09-19-13 — the engine on the whole tape: its real figure, with live resets

**Question (owner, 2026-09-19, 10:57):** "Then produce `fulltape_render.mp4` and
`fulltape_render_registration.csv` in the captures folder, replacing the existing (and doing an atomic
swap. do not render directly into that folder)". The watchdog asked for the engine's real whole-tape
figure, with the live classifier's resets, against the experiment's 99.2%.

**Pairing (the watchdog's derivation, applied as given; pairing is still a given setting, CLAUDE.md §9).**
- The schedule is `S/fulltape/pairing_schedule.csv`: reversed up to 48,188, aligned from the recording
  boundary at 48,189. That is one pairing change, and it resets the engine.
- The mixed stretch is aligned by majority (153 aligned scene cuts against 134 reversed). Taking each
  unit's pairing from its nearest scene cut, 1,282 of the 3,768 units in 81,362-85,129 (34%, in 57
  spans) read reversed. Those are the likely mis-paired frames, marked by note rows.
- Two ambiguous edges are noted: 47,996-48,188, and the first cut after the relock at 48,242.

**Premise.** The engine, run live on the whole tape with the classifier's resets and this schedule, agrees
with the comb about as the experiment did. Any difference from 99.2% traces to what the experiment did
not model: the live resets and the pairing inside non-programme events.

**Method.**
- One paced replay of `captures/fulltape.cap6`: `--geometry-v11 --pairing-schedule ... --audit-comb
  --pace-us 8000`, with PCM and A/V log dumps. The audit comb does not change decisions.
- Agreement is the published shift against the comb's on every comb-decided frame, overall, per segment,
  and on the experiment's population (entry 8's judged frames).
- Frames that differ are listed by cause: reset-adjacent, inside the mixed stretch, other.

**Falsifier.** Agreement on the experiment's population more than 0.5 points below 99.2%, or differences
that do not trace to resets or pairing.

**Material.** The whole tape.

### Report on entry 13 (2026-09-19) — held: the engine gets 99.24% on the whole tape, above the experiment

- **Replay.** v11-engine e3868e7, `--geometry-v11 --pairing-schedule --audit-comb --pace-us 8000`.
  - 86,305 observations: 86,293 exact, 7 short, 4 unframed, 1 0x0800.
  - Published 86,293, with no pool, ring or surface drops.
  - The registration log has 86,305 rows, schema 12, with pairing and pairing_note on every row.
  - 20 live resets: begin-segment 15, discontinuity 12, and the pairing switch.
- **Agreement with the comb**, published placement against every comb-decided frame:
  - all: 76,546 / 77,129 (99.24%);
  - first recording 38,174 / 38,567 (98.98%); after the boundary 4,854 / 4,872 (99.63%); after 27:18
    33,278 / 33,450 (99.49%); tape start and events 240 / 240.
  - The comb abstains on 9,160 frames.
- **On the experiment's population:** 76,300 / 76,883 (99.24%), against the experiment's 76,254 /
  76,886 (99.18%). Three of the experiment's judged frames are not woven frames in the engine: the
  unit flushed at the pairing switch and reset boundaries.
- **Engine against experiment, frame by frame.** They differ on 49 frames, and on every one the engine
  agrees with the comb and the experiment did not. All 49 lie in two runs that start exactly at a live
  reset the experiment did not model: 53,410-53,462 and 69,517-69,520. At each, the reset's forced
  re-run found the census one line off, held the correction, confirmed it on the next frame, and held
  it through the run. The experiment stayed on the census placement there.
- **Mixed stretch.** The 1,282 units noted as likely mis-paired agree with the comb on 628 of 655 decided
  frames (95.9%). That checks the vertical shift under the aligned weave, not the pairing itself; the
  comb cannot see temporal mis-pairing.
- **Verdict.** Premise held. Differences from 99.2% trace to live resets, all of them improvements.
- Scratch: `fulltape/fulltape_registration.csv`, `exp13_analysis.py` / `.out`, `experiment_frames_B.csv`.

### Review by Codex of entry 13's report (2026-09-19) — two findings, accepted

1. **The three frames between the populations are not boundary flushes.** Frames 60,874, 71,445 and
   90,127 are published woven frames. Their full-precision comb margins (1.49998849, 1.49964987,
   1.49987114) are just under 1.5, while entry 5 stored margins rounded to three decimals (1.500), so the
   experiment counted them as decided. On the identical 76,883-frame population the comparison is engine
   76,300 against experiment 76,251. The rounding also bears on entries 5-12's whole-tape figures: the
   seven stored margins of exactly 1.500 moved at most a few frames between decided and abstaining. The
   engine uses full precision.
2. **"49 differences, all improvements" holds for the judged frames only.** Across all shared frames, engine
   and experiment placements differ on 89:
   - 49 are comb-decided: all improvements, all in the two runs from the live resets at 53,410 and
     69,517;
   - 38 are frames where the comb abstains, which cannot be judged;
   - 2 are the rounding cases 60,874 (experiment 0, engine -1) and 71,445 (-1, engine -2).
   Neither "all differences trace to resets" nor "all are improvements" holds unqualified. The engine's
   headline count stands.
Codex's recount: its scratch `/private/tmp/codex-e13-review-5p0udR/recount.py`.

### The full-tape render through the engine, swapped into captures/ (2026-09-19)

- **Pipeline.** v11-engine e3868e7 (registration log) and `experiments/geometry_render.py` 330bd51
  (`--engine-log --pairing-schedule`). The renderer's schedule support was reviewed by Codex over three
  rounds to "No findings": the switch frame matches the engine's flush, and the loader is a one-to-one
  port of the engine's.
- **Validated before the swap:**
  - 86,296 encoded frames, as planned: 86,289 woven plus 7 fills.
  - Every frame's machine strip decoded in order; all 86,289 woven frames carry the engine's placement.
  - Field order bff for output frames 0-43,677 (reversed), tff from 43,678.
  - Audio 2,879.40 s against video 2,879.41 s.
  - Registration log: 86,305 rows, 86,293 units, every unit with applied d1/d2, schema 12. Pairing and
    note on every row; 1,282 units carry the likely-mis-paired note.
- **Swap.** Scratch and captures/ are on one filesystem (device 16777232). Each file moved in one
  rename: the inode was unchanged across the move (render 127830637, log 127823701) and SHA-256 matched
  (render 4ff10b59..., log 4283fb64...). They replaced the 2026-09-05 files `captures/fulltape_render.mp4`
  (3,524,569,727 bytes) and `captures/fulltape_render_registration.csv` (18,554,296 bytes).
- **Known limitation, measured.** The renderer places audio by sample ordinal, so it does not advance
  audio past the device's audio-only deficits:
  - 23 samples at 1,021 s (0.016 frame);
  - 1,183 samples at 2,066 s. After it, audio leads the picture by 0.755 frame (25 ms) to the end.
  Placing audio blocks by their audio-clock time would remove it; not done.

## E-claude-2026-09-19-14 — the full-tape render's audio, stepped at the device's audio-only deficits

**Question.** The watchdog relayed this as a derivation from a recorded rule, not a new owner ruling.
CLAUDE.md §6 (whole-tape audio timing): an A/V adapter must apply the audio publisher's correlation
residual "only where it steps (a discontinuity event: advance audio time by the lost samples once,
flagged) and never resample continuously". The full-tape render places audio by sample ordinal, so after
the device's 1,183-sample deficit at 2,066 s the audio leads the picture by 0.755 frame (25 ms).

**Premise.** Where the residual steps, the capture lost exactly that much audio and nothing else. Advancing
audio time once by the lost samples, at those units, puts every frame's audio back within the residual's
quantization of its picture, without touching the video.

**Method.**
- The frameserver's v11 log gains, per unit, the audio-clock residual and the step at that unit, in lost
  samples (Codex; from the audio publisher's own residual). A step is flagged where the residual moves by
  more than its quantization.
- The renderer inserts that many silent samples at the unit's audio resync and marks the frame in its
  band. There is no resampling.
- The whole tape is replayed and re-rendered, validated as before, and swapped into captures/ atomically.

**Falsifier.** After the change, either of these fails:
- the A/V offset (each frame's audio-resync output time against its picture output time) stays within
  0.002 frame across the whole tape;
- the placement strip is identical frame for frame to the current render.
If Codex and I conclude the §6 rule does not apply to a review render, the reason is recorded and nothing
is changed.

**Material.** The whole tape. Expected steps: 1,021 s (about 23 samples) and 2,066 s (about 1,183 samples).

### Review by Codex of the renderer change (f1c7d0e), and amendment 1 to entry 14 (2026-09-19, before the whole-tape render)

**Review.** Codex confirmed two things: the section 6 rule applies to a review render, and the two
whole-tape steps map to sample ordinals 49,028,611 and 99,176,727. It found three P2 defects with
synthetic probes:
- a step after an audio re-anchor was located against the first run's origin, and refused;
- the fill timeline used audio times without the inserted silence, so a deficit next to a short unit
  dropped a fill and left the audio 1.000125 frames late;
- the start trim was computed before an insertion at the first rendered frame, leaving the audio
  23 samples late.

All three are accepted. None of them occurs on the whole tape, which is one audio run whose first frame
carries no step. They are defects in the rule's implementation, not in its premise.

**Amendment (built in c36f7dc before this entry; written before the whole-tape render).** The physical
reason: the frameserver places each audio run on the video timebase, so a sample's physical time is its
pts, not its ordinal in the dump. Every sample now has one position: its pts on the 48 kHz grid. The PCM,
the steps, the timeline and the anchor all use that position.
- A re-anchored run plays where the frameserver placed it, rounded to the nearest sample.
- A block with no anchor yet takes its position from its run's first resync.
- A run that never anchors follows the previous block and is reported.
- An overlap is refused.
- The start trim is applied while the PCM is written, exact to a sample, instead of through ffmpeg's
  `-ss`, or an `adelay` truncated to whole milliseconds.

It should close the three findings. It must not change the whole tape's placement. There, pts minus
5 × ordinal is constant over all 86,303 dump-log blocks, so position equals ordinal. With no steps, the
rebuilt PCM must be the dump PCM from the anchor on. Deciding tests are synthetic and in scratch. They
pass on c36f7dc; on f1c7d0e the three findings' tests, plus re-anchor placement and the overlap
refusal, fail.

**Added to the method.** The offset measure reads the renderer's anchor from its log. On its own, that
reads back the renderer's claim. So the encoded file is checked directly as well. The mp4's AAC audio is
decoded and cross-correlated, at points across the tape, against the dump PCM at the sample the rule
predicts: before, between and after both steps. The expected lag is 0, within the codec's precision.
Any other lag fails this entry the same way the offset falsifier does.

### Review rounds 2–4 by Codex, and Codex's 95c916a (2026-09-20)

- **Round 2 (on c36f7dc): three findings, accepted.**
  - A step's silence was carried into a freshly anchored run.
  - A downstream queue drop was read as a new audio run. The frameserver marked both with
    DISCONTINUITY_BEFORE.
  - A step on a unit rendered as a fill was not marked.
  - Fixed in a19570b: a run is identified by its placement (pts − 5 × ordinal), which is exactly what
    its residual is measured against.
- **Round 3 (on a19570b): one finding, accepted.** A resync inside a gap where a new run began was given
  the previous run's step. Fixed in a556b19: such a unit's time is used only when both candidate runs
  would place it identically. Otherwise it is left out of the audio clock and reported, and a step on it
  is refused.
- **Round 4 (on a556b19): no findings.**
- **95c916a (Codex, pushed on v11-engine): reviewed and approved.** It separates the two meanings with
  `AP_FLAG_DROPPED_BEFORE`. The OBS plugin had been resetting its applied correction on every downstream
  drop, and it now keeps it. The mutation that restores the old flag fails its test. One P3 was left
  optional: a dropped block's COUNTER_GAP is not carried forward.
- None of these cases occurs on the whole tape. On the a14 dump, `place_audio()` gives identical output
  at a19570b and a556b19.

### Report on entry 14 (2026-09-20) — held: the audio stepped once at each device deficit, picture unchanged

**Verdict: the premise held.** Advancing audio once by the lost samples, at the two units where the
residual steps, puts every frame's audio within 0.002 frame of its picture. The video is not changed.

**Material and producers.**
- Replay: frameserver f268f26, whole tape, 2× realtime. 0 holes, 0 dropped audio blocks, 0 unanchored
  blocks. 86,293 exact units.
- The PCM is byte-identical to the first replay. The dump log has the same rows, with audio and video
  interleaved differently.
- The sidecar matches the published one on all 86,305 rows and 31 shared columns. It adds
  `audio_residual_ticks` and `audio_step_samples`. Only two steps are flagged: counter 35,120 (+23
  samples) and 66,432 (+1,183).
- The five startup deficits fall before the first rendered frame (4,511) and are absorbed by the anchor.
- Render: geometry_render a19570b, whose audio placement equals a556b19's on this tape.
  - 86,289 frames and 7 fills, as before.
  - The anchor trim is 5,262 samples, a whole number recomputed from the dump log.
  - The 1,206 samples of silence are inside delivered blocks. 0 undelivered stretches.

**Falsifier 1, A/V offset: held.** The offset is each frame's audio-resync output time against its
picture output time, computed exactly in ticks of 1/240,000 s (8,008 per frame) over the same 86,292
frames that have an audio-clock time. Min / max / median, in frames; negative means the audio is early:

| stretch | before (published render) | after |
|---|---|---|
| start – 1,021 s | −0.0020 / +0.0002 / −0.0017 | −0.0020 / +0.0002 / −0.0017 |
| 1,021 s – 2,066 s | −0.0164 / −0.0159 / −0.0161 | −0.0020 / −0.0015 / −0.0017 |
| 2,066 s – end | −0.7550 / −0.7545 / −0.7547 | −0.0020 / −0.0015 / −0.0017 |
| whole tape, max \|offset\| | 0.754995 (6,046 ticks) | 0.001998 (16 ticks) |

No frame is at 17 ticks or more, where 0.002 frame would be exceeded.

The figures measured last night with `av_offset.py` differ by +0.00075 frame. That is a defect in the
measure, not the render: it took the render's trim from a log line printed to four decimals (0.1096 s),
while ffmpeg received 0.109625 s. The cross-correlation below confirms the published render's effective
trim was 5,262 samples. The new render's log carries the trim exactly. `av_offset.py` on the new render
reads −0.0020 / +0.0002 / −0.0017 in every stretch and a maximum of 0.0020.

**Encoded audio checked directly.** The mp4's AAC track was decoded and cross-correlated in 1-second
windows against the dump PCM, at the sample the rule predicts. There were 60 checkpoints: every 60 s,
plus 1.5, 5 and 20 s either side of each step. Correlation peaks were 0.998–1.000, and one window was
quiet.
- The same instrument on the published render found 1 sample early before the first step, 24 early
  after it, and 1,207 early after the second. The differences are exactly 23 and 1,183.
- On the new render, the lag is 0 samples at all 59 decided checkpoints, including 1 s after each step.

**Falsifier 2, picture unchanged: held.** The machine strips of all 86,296 frames (unit, placement)
are identical to the published render's, with the same SHA-256. Validation passes: 86,296 frames
encoded as planned, all 86,289 engine frames at engine placement, schema 13, no applied value missing.

**Amendment 1: moved forward.** It closed Codex's findings with deciding tests, and it did not change
the whole tape's placement.

**Not understood, or open.**
- The 0.002 margin is 0.02 tick. The render has a constant 14 ± 2-tick lead (0.0017 frame, 58 µs), and
  it was already in the published render. It comes from anchoring on the first frame, 4,511, whose
  residual (21,738 ticks) is still in the device's startup ramp. The residual reaches about 21,750
  within about ten units and then holds.
- The ± 2 is the 48 kHz grid against 1,601.6 samples per unit.
- Anchoring on the steady residual would centre the offset. That is a change to the anchor rule, not
  made here.
- A capture where a run break coincides with a downstream drop, in a frameserver older than 95c916a,
  cannot be placed from its dump log. The renderer refuses it by name.

**Published.** Both files went into `captures/` by one same-filesystem rename each; the inodes were
preserved and the SHA-256 checked:
- `captures/fulltape_render.mp4`: 3,524,574,146 B, sha256 dd590315…
- `captures/fulltape_render_registration.csv`: 19,244,702 B, sha256 0b6e199b…

They replace 4ff10b59… and 4283fb64….

**Raw rows** (scratch, `fulltape/`): `a14/replay.out`, `a14/render.log`, `a14/validate.out`,
`a14/av_after.out`, `a14/xcorr_after.out`, `xcorr_before.out`, `strips_before.txt`,
`a14/strips_after.txt`, and the synthetic tests in `a14_tests/check_fix.py`.

## E-claude-2026-09-20-15 — the frames the owner found combed in the full-tape render

**Question (owner, 2026-09-20, watching the render).** "First combed frame I see is on ctr 9040",
then "string of badly combed frames at 10989-11001", "more combed frames 11127-11129", "13284",
"13449", and "48064-48187 ... that is definitely misregisterd". Also: "I think in some of those
frames, it needs to go back and re-examine if top and bottom are found properly. I definitely saw
jumps in at least some of those"; "is it running the comb against luma only or chroma"; "after a
fade, comb check should run on every frame until it is confirmed. the engine knows about fades
right?"

**Note on this entry.** These are diagnostic measurements on frames the owner identified, written
with their report. They are not a premise test of a new rule, and nothing in the rule set was
changed. What they decide is where the existing rule set fails and why.

**Method.** Each named unit was read from the capture. For every frame: the comb's eleven energies
at both pairings, computed here, against the engine's logged decision; each field's first and last
picture line measured from the raw rows (fraction of samples more than 20 codes above that field's
own blanking) against the engine's logged edges; and for the fade span, the picture level per unit.

**What the data did.**

1. **Every frame he named is misplaced by the comb's own measure.** The published placement measures
   3.5× to 81× the comb's minimum: 9040 5.9×, 10989–11001 3.5×, 11127–11129 3.9×, 13284 6.1×,
   13449 81×, and 78 frames of 48,110–48,187 above 2×. 10282 is the exception: every shift there
   measures above 4,000, so its two fields are different pictures — a scene cut, not a placement.

2. **Two failure classes, both measurable from the published sidecar** (the replay logs the comb for
   every frame, whether or not the engine used it):
   - the comb ran and abstained on a near-tie, and the census placement stood: **1,885 frames,
     2.18%**, in 604 clusters;
   - nothing fired, so the comb never ran and a held correction went stale: **583 frames, 0.68%**,
     404 of them in runs of five or more, the longest 48,108–48,187.

3. **The census misses one-line jumps, in two ways.** Its edge test is "95th percentile more than 5
   codes above blanking, spread more than 4", and a blank line in this material carries 10–14 codes
   of noise, so a blank line passes as picture. In the units around his frames, 10 of 110 reported
   first lines are a blank line with the picture on the next line; 26 of 110 are reported one line
   late, including every frame of 10,988–11,001, where the engine reads field 1 as starting at 24
   while line 23 is 100% picture. That one comes from the +1 run-in correction.

4. **The signature he described is real and invisible to the triggers.** At 10,990, 10,995 and
   11,000 the woven frame reads, in output order, f1 23 picture, f2 285 blank, f1 24 picture,
   f2 286 picture — his field/blank/field. T1 stayed silent because it compares the published shift
   only with the census's own tops and bottoms, and the census was wrong in exactly the way that
   makes them agree. With the true edges, T1 fires on every frame of that run.

5. **The comb reads luma only**, in the engine and in the reference. At 13,449 the two fields differ
   by 0.80 in luma, against 10.9 and 11.3 either side and 14.5 line-to-line inside one field: a held
   frame, as the owner read it. Its only real difference is chroma, which nothing in the rule set
   measures — not the comb, not the census, not the bottom test.

6. **The sparkle is at both ends.** At 11,127–11,129 the fraction of samples more than 20 codes off
   neutral chroma is 57–93% at the top lines and 82–95% at the bottom lines.

7. **The fade span.** 48,064–48,187 fades to black (level 39 → 12), holds ~35 frames, then returns
   to 63. In the black part the comb has no information (energies 29–34 at every shift, margins
   1.01–1.04) and the held +1 costs nothing. As the picture returns, the published +1 goes to 1.8×
   the minimum at 48,108 and 3.1–3.3× thereafter, and the comb decides d1=0 from 48,108 on — but
   confidence is HIGH and no trigger fires for the whole span. The pairing label is not implicated:
   averaged over the span the best energy is 53.8 reversed against 353.3 aligned.

8. **Nothing in the engine's inputs identifies a fade.**

**What is not understood, or not decided here.**
- Whether the decide rule should reject a placement the comb excludes (rather than requiring a
  winner), and what "confirmed" should mean after a fade, are the owner's calls. Both are reported,
  neither is changed.
- A whole-tape rate for the census defects is not measured; 110 edges around his frames is the
  sample.
- Why the +1 run-in correction fires on a picture that already starts at 23 is not established.

**Raw rows** (scratch, `ctr9040/`): `combset.out`, `census_recheck.out`, `chroma_and_trigger.py`
output, `fade_span.out`, and the panels `ctr9040_panel.png`, `ctr10282_chroma.png`.

### Correction to entry 15, and the noise and chroma measurements (2026-09-20)

**Correction.** Entry 15 said the late-reported field-1 top at 10,988–11,001 "comes from the +1
run-in correction". That is wrong. Measured over 195 cached units, the +1 correction fires on
**none** of them. The mechanism is the plain-23 test: line 23 counts as picture only if it lifts
more than 30 codes above blanking **and** correlates at least 0.5 with line 24; otherwise the scan
restarts at line 24. Through that run line 23 lifts 150–155 codes — unmistakably picture — while its
correlation with line 24 measures **0.40 to 0.48**, just under the bar, so the detector steps over
it. In the same sample line 23 passes the test on 16% of units, and 103 of 195 units have a bright
line 23 (lift above 30) rejected by the correlation term alone.

**Noise (owner: "is there a way to measure noise that will lower confidence and force the comb to
re-run?").** Measured per field on 389 edges:
- The field's own blanking rows are not the place to look: their spread is **1.0 code in every unit**,
  so it separates nothing. The noise that fools the detector is the source's blank line, 10–14 codes.
- What does separate is the detector's own headroom, the accepted line's 95th percentile above
  blanking: **wrong edges sit at 9–12 codes (median 5.0 above the 5-code bar, 10th percentile 4.0),
  right edges at 25–180 (median 55)**. A single threshold at 9 catches 12 of 12 wrong edges and fires
  on 0 of 377 right ones in this sample.
- It would have caught 9040 (margins 3.1 and 6.0), 13284 (7.0 and 9.0) and 13449's field 2 (5.0). It
  would NOT catch 10,989–11,001 or 11,127–11,129, whose edges lift 175–180 codes: that class is the
  correlation term above, not noise.

**Chroma in the comb (owner: "should the comb be matching on chroma as well?").** His instinct is
right. On the same frames and a control set where the luma comb decided cleanly:
- chroma margins are flat — **median 1.02 against luma's 3.00** — because NTSC chroma is
  band-limited and barely changes when a field moves one line;
- on the control frames chroma agrees with the luma verdict on **1 of 8**, so as a comb input it
  would add noise, not information;
- the one exception is the held frame 13,449, where luma is tied (margin 1.00) and chroma is sharp
  (**margin 37.6 on U, 30.6 on V**) — but its answer disagrees with luma's, and one frame is not
  enough to say which is right.

**A sudden chroma change as its own signal: yes, and it is clean.** Over 48 units the field-to-field
difference is luma median 12.18, U 13.14, V 8.61. Only **3 of 48** units have a luma difference below
2.0 — 9041, 13285 and 13449 — and all three are held frames, with chroma differences of 2.1–3.7,
i.e. **3.2 to 3.8 times their luma difference** against about 0.9 for ordinary units. "The two fields
carry the same luma but different chroma" is therefore detectable on this material, and it marks
exactly the frames where the comb has no luma information to work with.

**Open, for the engine's author.** At 13,449 the engine logs field 1's top as 24, while the same rule
in the reference gives 23 and the raw row shows line 23 is picture (lift 122, correlation 0.93, 100%
of samples above blanking+20). The C and the reference implement the same tests, so this is a
borderline numeric divergence worth checking.

## E-claude-2026-09-20-16 — the owner's three rulings: the woven frame, comb confidence, and after a fade

**Question (owner, 2026-09-20, verbatim).** "one thing we need to add is after a fade, comb check should
run on every frame until it is confirmed. the engine knows about fades right? it should reconfirm things
after fades." And: "ABSOLUTELY we should be considering how things look in the final raster. I thought
this is what the comb test does? or are you saying on frames where we don't run the comb as well?" And:
"I think if both comb decisions are at a wildly high threshold, the answer should be to abstain. the
whole engine as it exists today is working better because it has confidence scoring. why shouldn't combs
have their own confidence scoring".

**Premise.** The engine publishes a placement the comb can already judge, on every frame, because the
comb is computed on every frame. Judging the published placement against the comb's own confidence —
accepting it only where the comb does not exclude it, and holding where the comb knows nothing —
corrects the frames the owner found without disturbing the frames that are right today.

**The design being tested.**
- **The comb runs on every frame** (it is already computed for the log; this makes the engine act on it).
- **The comb carries a confidence** built from its eleven energies: the minimum's level, the ratio of
  second-best to best, and the spread, max over min. Three verdicts: *decided* (ratio at least 1.5),
  *no information* (spread under 1.5 — every shift within half of the best), *narrowed* (neither: no
  winner, but most shifts excluded).
- **The published placement is accepted only if the comb does not exclude it** — its energy within 1.5×
  the minimum. Otherwise the placement moves to the comb's best. On *no information* the placement is
  held and nothing moves.
- **After a fade**: no separate fade detector is proposed. A fade to black reads as *no information*
  while it is dark, so the placement holds; the first frames with information test the held placement
  and correct it if the comb excludes it. If the owner wants an explicit fade state, that is a separate
  decision; this entry tests the simpler rule.

**Falsifier.** Any of these fails it:
- on the control set — frames where the comb decided and the published placement already equals its best
  — the rule moves any frame;
- on the passages with no information (the black part of the fade span, the scene cut at 10,282, the
  held frames 9041 and 13,285) the rule moves any frame;
- on a sample of the frames it does move, the raw rows do not show the moved placement to be the better
  weave.

**Material.** The whole tape's schema-14 sidecar (all eleven energies per frame), the owner's combed set
(9040, 10,989–11,001, 11,127–11,129, 13,284, 13,449), the fade span 48,064–48,187, and the two failure
classes as counted in entry 15.

**Open choices, to the owner before building.** What "confirmed" means (the comb deciding and agreeing,
against the weaker test used here: the comb merely not excluding the published shift), what the comb's
confidence is made of, and whether he wants an explicit fade state at all given the above.

### Report on entry 16 (2026-09-20) — held: the comb's own confidence corrects the reported frames and moves nothing that is right

**Verdict: the premise held on all three arms of the falsifier.** Measured over the whole tape's
schema-14 sidecar, 86,289 frames.

**What the rule changes: 1,338 frames, 1.55%.**
- 583 are the class-B frames from entry 15 — nothing fired, the comb had decided otherwise. All move.
- 755 are *narrowed* frames: the comb cannot pick a winner but excludes the published shift.
- 430 of entry 15's 1,885 class-A frames move; the other 1,455 keep their placement, because the comb
  does not exclude it.
- **908 of the moved frames are HIGH confidence today** — the silent class.
- The move is one line on 767 frames, two on 329, three or more on 242. The published shift was 3 to 10
  times the comb's minimum on 489 of them, and more than 10 times on 26.

**What it does not touch.**
- **Control, 76,546 frames** where the comb decided and the placement is already its best: **0 moved.**
- **No information, 1,621 frames** (every shift within half of the best): **0 moved.** This covers the
  black part of the fade span (36 frames, none moved), the scene cut at 10,282, and the held frames
  9041 and 13,285, whose placement is already the comb's best.

**The owner's frames.** 9040 moves to d1 −2 (published 5.9× the minimum), 13,284 to −1 (6.1×), 13,449 to
0 (80.7×), and 10,990 / 10,995 / 11,000 / 11,128 to 0 (3.3–3.9×). The fade span moves on
**48,106–48,187, 82 frames**, and not one frame of its dark part.

**Raw rows.** Six moved frames were woven at the published and the proposed placement and looked at:
9040, 13,284, 13,449, 10,995, 11,128 and 48,150. In all six the published placement is visibly combed
and the proposed one is clean (`ctr9040/rulings_panel.png`).

**Cost.** The comb is already computed on every frame for the log. Acting on it adds nothing; making the
search unconditional costs 0.24 ms per frame against a 33.37 ms period, about 21 seconds of CPU across
the tape.

**The two readings of "confirmed", measured.** Moving only where the comb DECIDED and disagrees changes
583 frames and leaves 9040, 13,284 and 13,449 — the frames the owner reported — wrong. The weaker test
used here, moving wherever the comb EXCLUDES the published shift, changes 1,338 and corrects them. The
raw rows above support the weaker test.

**Not decided here.** Whether an explicit fade state is wanted anyway; the exact factor (1.5 was reused
from the decide rule, not fitted); and whether the engine should also record the verdict per frame.

### Amendment 1 to entry 16 (2026-09-20, after the capture-1 regression fired): a minimum at the window edge is not an answer

**Physical reason.** The comb searches shifts −5 to +5. When its minimum sits at ±5 the true minimum may
lie outside the window, so the value is a boundary artefact, not a measurement. The engine's own search
range is the source of this, not a fitted number.

**What it should improve.** The owner's capture-1 regression: with the minimum trusted at the edge, the
rule moved 102 of capture 1's 919 frames and **81 of them away from zero, 77 landing on +5**. With an
edge minimum treated as no information, capture 1 moves 25 and the whole tape 1,284 instead of 1,338 —
so the guard removes the damage and costs 54 frames on the tape.

**What it must not break.** The control and no-information arms stay at zero moved, and the frames
measured on raw rows still move: 9040, 13,284, 13,449, the 10,989–11,001 run, 11,127–11,129 and the
fade span are unaffected by the guard.

**Result: the falsifier fired and was answered.** Reported as such, not as an improvement.

### Capture 1 against entry 16 (2026-09-20)

**Capture 1 does not come out at zero today, before any change.** Published relative shift over its 919
frames: 0 on 492 (54%), −1 on 332 (36%), and the rest spread from −14 to +10. Applied field-1 shifts run
0 to 15. So "the engine produces 0 shifts on capture 1" is not the current state, and this measurement
is the baseline, not a regression caused by the rule.

**With the edge guard, the rule moves 25 of 919 frames.** 23 are in the opening, counters 6253–6390 —
the acquisition and dark fade-in the owner ruled should stay unregistered ("It's the tape coming in…
That should stay unregistered"). Their comb minima are 0.3–0.8 against 60–110 on programme. The other
two, 6929 and 6930, sit on a flat grey card with no vertical structure; woven at either placement they
look identical (`ctr9040/cap1_moves.png`).

**A source-derived "not enough detail" guard was tried and did not work**: holding back frames whose own
comb maximum falls below a fraction of a running median of that capture's maxima. At 5%, 10% and 20% it
left capture 1's 25 moves untouched (its whole opening is dark, so the running median is low there) while
holding back 168, 632 and 1,674 frames on the tape. Not proposed; a threshold that separated them would
have to be fitted, which is what the owner asked us not to do.

### The hard-coded numbers, audited against the code (2026-09-20)

| number | where | constant or derived | can it be derived from the source |
|---|---|---|---|
| 5 codes above blanking, spread over 4 | picture test, `geometry_engine.c` | constant | **yes** — from the source's own blank-line spread, 10–14 codes here against the device's blanking at 1.0. This is the threshold the wrong-blank class clears; a derived bar separated 12 of 12 wrong edges from 377 right ones |
| 30 codes | plain-23 lift | constant | **yes**, same derivation |
| 0.5 correlation | plain-23 | constant | **no help**. The body's own adjacent-line correlation is 0.74–0.76 median with 2–4% of lines below 0.5; line 23 in the 10,989–11,001 run measures 0.43–0.46, in that bottom few percent. Deriving the bar from the body would reject line 23 harder. The question is the rule, not the number |
| 0.5 run-in power, 5 codes | run-in correction | constant | **yes** — the detector reads 0.005 median and 0.027 maximum on this material, so a floor plus a margin is measurable per source |
| 12 codes blank margin, 20-code change | bottom test | constant | **yes**, same noise derivation |
| 8 samples of 12, 64 samples | bottom test extents | constant | **no** — these are extents, not levels. They say how much of a line must change; expressing them as fractions of the line is a rewrite, not a derivation |
| ±5 | comb search window | constant | **no** — it is the search itself. Amendment 1 makes its limit explicit instead of hiding it |
| 1.5 | comb decide, and the exclusion test | constant, accepted by the owner | **not needed** — a dimensionless ratio that does not scale with level or noise |

**What derivation would mean in practice.** Measure the source's blank-line spread and the run-in floor
at registration start and again after every reset the engine already takes (classifier discontinuity,
begin-segment, counter gap). Where the source is black or flat there is nothing to measure: hold the
last derived set, and if none has been established yet, do not register rather than invent one.

## E-claude-2026-09-20-17 — deriving the engine's thresholds from the source at startup

**Question (owner, 2026-09-20, verbatim).** "When we say these are derived from source does the engine
auto derive these on static startup. It should." And: "My guess is there will be a run in period for
several dozen units where the engine finds its values and locks in. Functionally this should change 0
decisions in the current engine." And: "Obviously, if noise is detected, it will wait until there is a
stable signal or non mute picture."

**Premise.** The picture test's bar is a property of the source, not of the engine. The rows in each
field's top search window fall into two groups — lines with no picture, a few codes above blanking, and
lines with picture, tens to hundreds above — and the bar belongs between them. Measuring it from the
source at startup reproduces the decisions the fixed constant produces on this tape.

**Falsifier (his prediction).** A derived bar that changes any decision on this tape. A difference is
the falsifier firing, not an improvement.

**Method.** For each unit, the 95th percentile above blanking of every row in the field-1 search window
(NTSC 22–40). Pool the rows over the first N units, place the bar in the widest empty stretch between
the two groups, and re-run the engine's own top rule — `first()`, then plain-23, then the run-in step —
against the logged tops, keyed to each frame's `frame_top_unit`.

**Report: the premise held, and his prediction with it.**
- The rows do separate: 7% sit under 20 codes (median 1.0, maximum 18.0) and the rest above (median 57,
  2nd percentile 22).
- The bar settles almost at once: 5.53 after one unit, **4.53 from the fifth unit onward**, unchanged at
  10, 20, 50, 100 and 199 units. His "several dozen" is an over-estimate; about five units suffice on
  this material.
- It lands at **4.53 against the fixed 5**, and reproduces the engine's logged field-1 top on
  **189 of 189 units — zero decisions changed.**
- A different placement of the same derivation, between the two clusters at 20.0, changes 4 of 189, and
  those four are wrong-blank edges. **So the two conditions pull apart**: derive to reproduce today's
  decisions (4.5, nothing changes, the wrong-blank class stays), or derive to separate the clusters
  (20, the class is fixed, decisions change). That is the owner's choice, not ours.
- Waiting on noise: the derivation needs rows with picture in them. Where the source is black, muted or
  flat the two groups do not separate and no bar can be placed; the engine holds the last derived set,
  and registers nothing if none has been established.

**Correction to entries 15 and the census figures I reported.** For a reversed-pairing frame the row's
`f1_first` belongs to the frame's **top unit**, not to the row's own counter. My sample figures compared
it against the wrong unit's rows. Corrected, over 383 edges: a first line on a blank row occurs on
**7 (1.8%)**, not the 9% I reported, and a first line reported late on **107 (27.9%)**, against 24%.
Codex's whole-tape census keyed this correctly from the start, so its figures — 5.54% of frames with a
blank first line, 44.95% late — stand unchanged. The headroom finding also survives the correction and
is stronger: wrong edges clear the 5-code bar by at most 9, right edges by 20 to 175, and a threshold at
9 catches 7 of 7 while firing on none of 376.

**Correction on capture 1's 6929 and 6930.** The owner: "6929 and 6930 are not flat grey cards. They are
the actual video footage." He is right; my crop had auto-selected a flat sky band. On the detailed part
of the frame the comb energy falls from 10.2 to 5.2 at 6929 and from 22.4 to 15.2 at 6930 when the move
is applied, and at 6930 the line-pitch striping on a fence post and branches visibly clears. The move is
sound on both.

### For the stabilisation entry, when it is written (2026-09-20): the owner's crop ruling, and his premise checked

**His ruling, verbatim.** "For vacated lines, just crop. Obviously this should only be a problem at the
bottom because a picture should never shift up from line 23. In other words, at top you can only add
blank lines if too much picture gets lost."

**His premise, checked on raw rows.** Over 219 units spanning both recordings on the tape and capture 1,
the picture never reaches above line 23 in field 1 or 286 in field 2: line 22 is over half occupied on
**0 of 219** units (median occupancy 0.0%), and line 285 on **0 of 219**. Lines 23 and 286 are occupied
on 152 and 160 of them, the rest being dark, fade or mute units. The Shuttle's own inserts behave as
expected — line 20 never over half occupied, line 21 (the caption waveform) on 21 units.

So the tape agrees with him, on this sample. Two qualifications: the engine cannot test this itself,
because its scan starts at NTSC 22 and 285 and so can never report a top above them — only raw rows can;
and 219 units is a sample, not the whole tape. A whole-tape check costs one capture pass.

**What "too much picture gets lost" would have to mean.** The stabiliser moves the pair of fields by a
common shift. Moving the picture down pushes its bottom past the end of the delivered raster, and those
lines are gone; moving it up costs nothing at the top, because above line 23 there is no picture to lose.
So the only real choice is at the bottom, and it is: how many picture lines may fall outside the output
window before the stabiliser pads at the top instead of cropping at the bottom. Three ways he could say
it, and the choice is his:
- never lose a line: pad the top as soon as one picture line would fall off;
- lose up to a stated number of lines before padding;
- judge by proportion of the picture's height rather than a count.
Two things complicate the count and he should know them: the measured last picture line itself moves
(259 to 262 in field 1 on this tape), so "how many lines would be lost" is a per-unit measurement, not a
constant; and the lowest lines are the head-switch region, which is not picture in the ordinary sense,
so losing them may not be a loss at all. No number is proposed here.

- **E-claude-2026-09-20-18** — the first picture line from temporal change between units: **refuted**, superseded by entry 20. It fixes the late-top class but fails the blank-line class outright: at 9040 the blank line 286 has the largest inter-unit change of any row in the field, so change does not separate picture from blanking.

- **E-claude-2026-09-20-19** — the vacated line as the trigger the rule set lacks: **refuted on every arm**, superseded by entry 20. The signature is not rare — a bar low enough to catch the four known moves flags 20.6% of the tape, and a bar rare enough to be a trigger catches none of them.

## E-claude-2026-09-21-20 — the tape's own horizontal blanking as the reference (the owner's proposal)

**Question (owner, 2026-09-20).** "Why wouldn't we just use the horizontal blanking as a swap in…" and,
on the population, "How is it thin against 720… there's 240 lines of it", and on the threshold, "that
will not be constant because it's a noisy edge so that should not be a fixed but a derived threshold",
and on how to derive it: "It shouldn't be a distribution. It should decide per unit what to include and
what to exclude. If it includes samples that are conceivably picture or will throw the whole thing off."

**Why this and not the dark-end rule.** Mine measured the candidate line's own dark end against the
device's synthetic blanking, and it changed 21.5% of field-1 tops whole-tape. His uses a different
quantity entirely: the tail of the source's own horizontal blanking that begins every delivered line.
CLAUDE.md §6 already establishes it as measurable here — the NTSC setup measurement used "each line's
OWN blanking as its 0 IRE reference (the classical black-minus-porch measurement, needing no device
constant)". It carries the source's own noise by construction, which is the quantity the census lacks.

**Measured before writing this entry, to know the experiment is worth running:** on this raster the
delivered line begins with about six samples of blanking, rising to picture level by sample 12 to 14 —
not the 25 the nominal timing implies. Pooled over a field that is roughly 1,400 samples of the source's
own blanking per unit.

**Premise.** Pooled over one field, those leading samples measure what the source's blanking actually
reaches on that unit, dropout speckle included. A line carries picture only if its body rises above that
level. No device constant enters, and the reference is re-measured every unit.

**Method.** Per unit and field:
- **Selection**, per his instruction, deciding what to include rather than fitting: column 0 is blanking
  by construction; include each further leading column while its across-line median stays within column
  0's own across-line spread, and stop at the first that does not. Anything conceivably picture is
  excluded by that test rather than by a sample count.
- **Reference**: pool the included columns over all the field's lines; take a high quantile as the level
  blanking reaches. Reported at the 99th, 99.5th and 99.9th so its sensitivity is visible.
- **Decision**: the first picture line is the first row of the search window whose body 95th percentile
  exceeds that level. The existing continuity test is retained; nothing else changes.

**Falsifier.**
- The selection finds fewer than two safe columns on more than a few per cent of units: the reference
  cannot be measured and the premise fails.
- The known cases are not fixed: 9040, 13,284 and 13,449 must move field 2 from 286 to 287, and the
  late-top run at 10,988–11,001 must return 23 for field 1.
- The whole-tape disagreement with the engine's current tops is far larger than the measured size of the
  class, about 5.5% of frames: anything in the tens of per cent means it is moving frames that are not
  in the class, as my dark-end rule did.
- A sample of the disagreements is not supported by raw rows.

**Material.** The whole tape, all 86,293 exact units. The known cases above. Capture 1 as the external
check.

**Pre-registered before the deciding run**, unlike the two dark-end passes, which ran before the note
covering them was written. That was a departure from §14 and is recorded here as one.

### Report on entry 20 (2026-09-21) — held: the tape's own horizontal blanking is the reference the census was missing

**Verdict: the owner's premise held.** Every arm of the pre-registered falsifier passes, and the one arm
I withdrew is recorded below with its reason.

**The selection works.** Column 0 is blanking by construction; each further column is included while its
across-line median stays inside column 0's own spread. Over the whole tape it keeps a **median of 5
columns**, and **fewer than two columns survive on 77 units, 0.09%** — so the reference can be measured
essentially everywhere. The level it derives is **18 codes median (10th percentile 8, 90th 24)**, which
is where the tape's speckle actually reaches, against the fixed 5 the census used with a synthetic
reference whose own spread is 1.0.

**Size: 5,900 units, 6.84%** at the 99th percentile — field 1 4.51%, field 2 3.47%. That is the region
of the measured defect, 5.54% of frames, not the tens of per cent my own dark-end rule produced. The
choice of quantile matters little: 6.84% at the 99th, 7.38% at the 99.5th, 12.27% at the 99.9th.

**The changes are right, judged by a measure independent of the rule** — the fraction of a line's samples
more than 20 codes above blanking, which is the test Codex's census used. Of 6,621 changed edges:
- **6,354 move the top later**, and for those the abandoned line has a **median occupancy of 0.0%** while
  the newly chosen line has **100.0%**;
- **5,995, or 94.4%, are supported outright** — the old line blank, the new line picture;
- **78, 1.2%, are contradicted**: the old line was more than half picture and the rule skipped past it;
- 281, 4.4%, are neither, on dim material where both lines are partial;
- the three commonest moves are 24→25 (2,542), 287→288 (1,614) and 286→288 (972), all with the old line
  at about 0% occupancy and the new at about 100%.

**Where it is wrong, measured rather than hidden.** 267 units move the top **earlier**, and for those the
newly accepted line has a median occupancy of 0.0% — the rule takes a blank line as the top on about 174
of them, where the derived level falls low enough for speckle to pass. With the 78 contradicted moves
that is roughly **250 units, 0.3% of the tape**, against 5,995 corrected.

**The defect is larger than the earlier census measured.** Codex's figure of 5.54% required the line
immediately below the reported one to be picture, so cases where the census sat two lines high — 286→288,
972 units — were outside it.

**The withdrawn falsifier arm.** I pre-registered that the late-top run at 10,988–11,001 must return 23.
That was mis-specified: the late-top class is governed by the plain-23 **correlation** term, not by the
picture test this entry replaces, so his reference cannot address it and should not have been asked to.
Withdrawn with its reason, not dropped.

**What this does not settle.** The owner's "must not change anything" bar cannot be met by any fix to
this class, as recorded yesterday: correcting 5,995 edges is a change of that size by definition. This
entry shows the change is overwhelmingly a correction, which is the evidence that decision needs.

### Amendment 1 to entry 20 (2026-09-21) — the margin that the reference swap deleted

**Registered before it is built, as §14 requires.**

**The defect, and its physical reason.** The task I wrote for the engine said: "the brightness bar
becomes `hi > level` in place of `hi - blank > 5`." That replaced the reference and deleted the noise
margin in the same sentence, and the deletion was not deliberate — I treated the `> 5` as belonging to
the device constant it sat next to. It does not. The derived level is a **99th percentile of the leading
blanking columns**; the quantity compared against it is the **body's 95th percentile**. Two statistics
over two different populations, so a dim row's body clears a blanking-column percentile by a code or
two without carrying any picture. Measured on the whole tape from `margins.csv`: **2,100 of 171,693
field edges have their chosen line clearing the level by 5 codes or less**, and **1,383 of the 1,695
blank tops — 81.6% of that error class — are inside that band.** Field 2 has 1,052 edges at a margin of
3 or less against field 1's 525, which is the two-line field-2 error appearing in the statistic.

Worked instance, counter 69566 field 2: the derived level is 12.0; line 286 has body p95 **13**, line
287 has **15**, and the first real picture line, 288, has **93**. The rule as shipped takes 286.

**What the amendment changes.** One term: the top test becomes `p95 - level > margin`. The bottom, the
spread test, the high-contrast correlation guard, `plain23`, the run-in step and the logged level and
column count are all untouched.

**What it should improve.** The blank-top class, and field 2's placement specifically.

**What it must not break, and the reason this is not free.** **717 currently-lit tops also sit inside
that band** and a margin pushes every one of them later. A genuinely dim picture line clearing the level
by 3 would be skipped. That is the cost to measure, not to assume, and it is why the margin is swept
(0, 3, 5, 8) rather than chosen.

**Falsifier.** Judged by the owner's own gate — "the real test is our comb agreement statistic …
especially if we filter to only when the comb confidence is high … its a specific but not sensitive
instrument which is the right thing for a pass/fail check":
- Comb self-consistency does not improve at high comb confidence, or regresses in any confidence band.
  The engine's published shift cannot be re-derived outside the engine, so the quantity measured is
  engine-free and stricter: a rule's own two field tops imply `rel = (t1 + 263) - t2`, and the comb,
  computed directly from the rasters, says which shift is right.
- Or the lit tops it pushes later outnumber the blank tops it fixes.
- Or the independent gate (line above the top full-amplitude coherent ⇒ the top is late) does not improve.
- Or no single margin works for both fields, which would mean the level is not the common reference the
  entry claims.

**Material.** All 86,293 exact units, `scratchpad/ctr9040/combcensus.py`.


### Report on amendment 1 to entry 20 (2026-09-22) — the margin is not carried by the gate that judged it

**Verdict: unresolved, and weaker than the amendment claimed.** The margin was registered to fix the
blank-top class and field 2's placement. Measured on the whole tape through the engine itself, it does
neither on its own.

- **Comb is indifferent.** Margins 3, 5 and 8 sit on today's agreement to three decimal places in every
  confidence band. That was predicted — comb sees only relative alignment — so it is not evidence
  against the margin, but it is not evidence for it either.
- **The independent gate is mildly against it.** Late tops: today 5,498, margin 3 → 5,553, margin 5 →
  5,564, margin 8 → 5,560, of 172,586 edges judged per arm. The margin alone makes placement slightly
  worse by the one instrument that never chose a top.
- **It does not fix field 2 alone.** On the owner's four labelled units the margin alone gives field 2 =
  290, overshooting his 288 by two lines. Only the margin together with the per-chunk test lands on 288.
- **Its remaining support is a different instrument.** 1,383 of entry 20's 1,695 blank tops sit inside
  the deleted margin, measured by occupancy — which CLAUDE.md already records as blind to dark picture.

**What was not tested, and should have been:** every arm supporting the margin also carried the
per-chunk test. The chunk rule at margin 0 was never measured, so the margin's contribution to the
candidate is not isolated. That is a defect in my experimental design, not a result.

**Population:** all 86,293 exact units; 172,586 field edges per arm; engine abstentions 893 → 1,380
between today and the candidate.

**Raw rows:** `scratchpad/ctr9040/arms/*.units.csv`, each naming its arm on its first line;
`gate_arms.csv` for the verdicts.

## E-claude-2026-09-21-21 — does the comb rescue the horizontal-blanking rule's mistakes? — **REFUTED.** Comb agreement does not recover either error class of the derived-level rule; the owner's separate prediction about the class was confirmed. Compacted 2026-09-21.

## E-claude-2026-09-21-22 — coherence with the line below as a second stage for marginal cases — **REFUTED as a rescue.** Banding the derived level and deciding the margin by whole-line correlation does not fix the classes it was aimed at. The same correlation used differently is live work (see entry 30). Compacted 2026-09-21.

## E-claude-2026-09-21-23 — the same derived reference at the bottom of the field — **REFUTED.** The derived level is a top-of-picture instrument: at the bottom it is the stricter test and excludes a partly-lit last line, which the owner then ruled is picture ("31 % lit row absolutely counts as last picture line"). The bottom keeps the device constant. Compacted 2026-09-21.

## E-claude-2026-09-21-24 — excluding the samples that are conceivably picture, as he specified — **diagnosis confirmed, cure REFUTED.** The derived level really does inflate on noisy material (median 134 codes on the affected edges against 18 tape-wide, maximum 247); collapsing the selection further does not cure it without changing edges outside the class, which was his acceptance bar. Shipped knowingly in entry 20. Compacted 2026-09-21.

## E-claude-2026-09-21-25 — freezing the geometry through a fade — **superseded.** The freeze was measured and did not reach the defect: fewer than all 80 comb-decided units at 48063-48188 come from the held correction. Entry 33's frame-level confidence covers the same ground from the signal rather than from a fade label. Compacted 2026-09-22.

## E-claude-2026-09-21-26 — the amplitude check on the line above the top — **not needed as a rule.** Measured; the case it was aimed at is covered by the top search itself. Compacted 2026-09-22.

## E-claude-2026-09-21-27 — the held correction, and letting a confident comb override

**Ruling (owner, 2026-09-21):** "the whole thing should be built on confidence scores. any instrument
detecting a change should recalculate confidence based on its own previous decisions and only enact that
change if it is of high enough confidence. thats how you can get the weak 11126 decision overridden at
11127". Build and test authorised the same day.

**Two changes, both from one worked case.** At 11118–11125 the engine publishes a top of 24 with a held
correction of +1, and the comb agrees. At 11126 the top corrects to 23 — and it is a correction, the raw
rows show line 23 at 99–100% lit, p95 181–188, coherence +0.89 to +1.00 with the line below, against line
22 at 0% lit and p95 2.0. But the held +1 was compensating for a top of 24, and it rides on for six
units, pushing the published shift to +1 while the comb sits decided at margin 3.71–4.01 saying 0 and is
never consulted. At 11132 it drops to 0 on its own and agreement returns.

- **Invalidate the held correction when its basis changes.** A correction derived against one top is not
  evidence about another; when the top moves, it is stale and must be re-derived rather than carried.
- **Let a decided comb override an untriggered placement.** The comb is computed on every frame under
  audit; today it is acted on only when a trigger fired. Scope measured: **1,595 frames** tape-wide where
  the comb is decided, no trigger fired, and the published shift disagrees — including 80 in the fade span
  and 6 at 11127–11131.

**Premise.** Both defects are one thing: a decision held past the evidence that justified it. Dropping a
correction when its basis moves, and letting confident contradicting evidence act without waiting for a
trigger, place the picture correctly where the engine currently does not.

**Falsifier.**
- The worked case does not come right: 11126–11131 must agree with the comb after the change.
- Or the owner's gate fails: published shift against the comb, filtered to high confidence — margins 3, 5
  and 8 must not degrade. The 1.5 band is reported but is not the criterion, being the region where entry
  21 measured the comb naming the right placement about one time in seven.
- Or it changes frames outside the measured scope: more than the 1,595 plus the held cases, counted and
  reported rather than netted.
- Or raw rows on a sample of the changed frames show the new placement worse.

**Material.** All 86,293 exact units, on top of the entry-20 draft `91a5b64`.

#### Amendment 1 to entry 27 — two figures of mine were wrong, and the owner has dropped the override

**The scope figure was measured with the wrong columns, for the third time today.** I wrote 1,595 frames
where the comb is decided, no trigger fired, and the published shift disagrees. That came from
`applied_d2 - applied_d1`. The published shift is `frame_d2 - frame_d1`; Codex's preflight recomputed it
as **583** on the published baseline and **743** on entry 20. I had already corrected this column choice
for the agreement baseline this morning and failed to carry it into the scope measurement.

**The worked-case falsifier was wrong.** I required 11126–11131 to agree with the comb after the change.
At **11126 the comb abstains** — margin 1.00049, winner +3 — so it cannot be forced to agree with a
winner it does not have; and **11130–11131 already agree** with its winner of +1. The correction the
entry should require is **11127–11129** and nothing else.

**A conflict the entry did not anticipate, raised by Codex before writing any code.** Dropping the
`comb_ran &&` guard makes `--audit-comb` change placements, which breaks the standing rule that the
audit comb does not change decisions. Always computing and adopting avoids that, but then agreement with
a decided comb is **100% by construction**, which destroys the owner's own acceptance gate as independent
validation. The gate and the override cannot both be measured on the same quantity.

**Owner's ruling (2026-09-21):** "lets leave 27b out for now. and see where the render puts us once those
changes are in place". So the comb override is withdrawn from this build and the entry is carried by its
first change alone — invalidating the held correction when the top moves. The override, and the
circularity above, are open and unresolved rather than refuted.

## E-claude-2026-09-21-28 — letting the plain-23 guard abstain — **moot.** plain-23 is removed from the engine entirely as of d5c9f08; there is no guard left to abstain. Compacted 2026-09-22.

## E-claude-2026-09-21-29 — one measurement, scanned: the settle point as the top — **refuted.** The whole-tape census failed the 69566-69576 span, placing field 2 two lines from the owner's reading. Compacted 2026-09-22.

## E-claude-2026-09-21-30 — one line below, per chunk: does any chunk disagree?

**Question (owner, 2026-09-21).** "I think the instrument for coherence is wrong. its not do all of the
chunks agree when averaged together. its... does any chunk disagree". On symmetry: "it can be brighter.
thats too overfit. the whole point is does it disagree. no chunk may be substantially brighter OR darker
than its corresponding shunk". On how many lines to read: "read one line. as I asked. 5 lines is exactly
the kind of thing that fucks up an instrument that has moving picture. one line should always be near
coherent on real picture". And on the structure ratio: "why drop the structure ratio? it didn't measure
the right thing so make it measure the right thing".

**Premise.** Real picture resembles the line immediately below it *at every horizontal position*, not
only in its line average. A caption, a data line or blanking does not: it disagrees with the line below
somewhere along the sweep, whatever its average. One line below is the whole instrument — averaging
several brings moving picture into a test about the current line.

**Why a second instrument at all, given amendment 1 to entry 20.** They reject different things and
neither is sufficient. Amplitude rejects blanking and dim pedestal rows, which is 82% of the blank-top
class. Captions and data lines are *bright*, clear any amplitude bar comfortably, and are the remaining
312. This is the owner's own division: "you are trying to run one instrument when you need multiple".

**Method — two forms of the same one-line idea, measured against each other.**
- **Per-chunk agreement.** Split the line and the line below into 16 chunks of equal width, take each
  chunk's mean, and count the chunks agreeing within a relative tolerance. A line is picture only if at
  least 11 of 16 agree. Symmetric by construction: the test is on |a-b|, so brighter and darker fail alike.
- **The repaired structure ratio**, `std(line) / std(the next line)`, read over one line rather than the
  median of five it previously used. Scale-free, so it measures structure rather than level: a caption
  over blanking explodes, blanking over picture collapses, picture over picture sits near one.

**What each is expected to do, stated before the run.** On four hand-checked units (69566, 69568, 69570,
69573) the separation is clean and identical for both: caption 1-4 of 16 chunks agreeing and a ratio of
20-24; blanking 0 of 16 and a ratio of 0.01-0.08; the first picture line 11 of 16 and a ratio of
1.44-1.54; deep picture 16 of 16 and a ratio near one. Four units is not a result, and both forms tie
there, which is precisely why the whole tape has to separate them.

**Falsifier.**
- Neither form improves comb self-consistency at high comb confidence over amplitude alone, in which
  case the second instrument is not earning its place.
- Or either form rejects real picture: its top lands later than the amplitude-only top on frames whose
  amplitude-only top is already correct by the independent gate.
- Or the two forms disagree with each other on a large population without the raw rows supporting one of
  them, which would mean neither is measuring what the entry claims.
- Or the 11-of-16 threshold and the ratio band cannot be justified from the tape's own distributions and
  remain fitted to the four units.

**Material.** All 86,293 exact units, scored jointly with amendment 1 in `scratchpad/ctr9040/combcensus.py`.
The four units above are the build material and are therefore not the judge.

### Report on entry 30 (2026-09-22) — refuted for a characterized class, held elsewhere

**Verdict: the premise is refuted, and the class where it fails is identified.**

The premise was the owner's: real picture resembles the line immediately below it *at every horizontal
position*, so "one line should always be near coherent on real picture". The falsifier registered was
"either form rejects real picture: its top lands later than the amplitude-only top on frames whose
amplitude-only top is already correct by the independent gate". **It fired.**

**What the data did.** Judged by the independent gate over 172,586 field edges per arm, the per-chunk
rule with plain-23 and run-in removed takes late tops from **5,498 to 2,261**. But the error set is
**replaced, not reduced**: 5,326 fixed, **2,089 newly wrong**, 172 wrong in both. The new failures fall
in 319 runs, the largest being 11537–11798, 484 edges.

**Why it fails there, from the raw rows and confirmed by render.** At counter 11540 field 1 the picture
begins at line 24 — visible, and today's engine gets it right. The new rule takes 29. Lines 24–28 clear
amplitude comfortably and fail on chunk count, and they fail honestly: their chunk means span 2.4 to
182.4 across the width, and the maximum absolute difference to the line below reaches **170 codes**. The
material is a bright curved edge against black, so the boundary moves further than one 40-sample chunk
per line. Real picture genuinely disagrees with the line below. The premise is false on steep
high-contrast boundaries.

The gate disagrees with the instrument for a reason that is not a contradiction: it correlates chunk
means, which is scale- and offset-invariant, so a boundary that merely shifts horizontally still
correlates at 0.996. Both instruments are right by their own definitions.

**The two forms did not tie, and the structure ratio lost.** By comb it looked best at margin ≥1.5
(99.177%) and worst at ≥8 (98.655% against the per-chunk rule's 99.978%), moving 39,412 field-1
placements. The gate then showed why: 312 "wrong" but **62,598 abstentions**, 36% of its tops landing
where the gate cannot judge either way against ~9% for every other arm. A rule whose placements are
mostly unjudgeable is not conservative.

**What the entry did establish, and it is not nothing.** Removing plain-23 and run-in is required for
the per-chunk test to help at all, and those two guards are independently and **exactly additively**
harmful: of 5,760 late tops they cause together, plain-23 accounts for 3,474 and run-in for 2,286
(3,474 + 2,286 = 5,760 exactly). Their combined effect on field 1 is a **+1 on 15,621 of 15,743 moved
units** — plain-23's re-search window begins at line 24 and structurally cannot return 23, and run-in is
literally `first[0]++`. On the fade at 48055–48195 comb agreement at confidence goes from 6 of 86 to
86 of 86, because the misregistration is never introduced rather than corrected.

**What is not understood.** The remaining 318 new runs are not characterized; only 11537–11798 was
rendered. Whether the amplitude margin contributes to these failures is unknown, because the chunk rule
at margin 0 was never measured (see amendment 1's report).

**A premise that would survive this counterexample**, for a future entry rather than a patch here: a
chunk straddling a blanking-to-bright boundary is a *detected edge*, not a disagreement, and should be
excluded from the count rather than failing it. That is a different claim about the signal and needs its
own entry, falsifier and material.

**Material.** All 86,293 exact units, twelve whole-tape arms. The four build units (69566, 69568, 69570,
69573) were not the judge. Raw rows: `scratchpad/ctr9040/arms/*.units.csv`, `gate_arms.csv`, and the
rendered rows at counter 11540.

**Built into the engine as the default** at `d5c9f08` on `v11-engine`, local, not pushed, carrying this
regression knowingly and reported to the owner with the render.

## E-claude-2026-09-22-31 — a top that moves without its bottom is not a picture displacement

**Question (owner, 2026-09-22, verbatim).** "if the chunk disagreement says the line should be shifted,
but the bottom did not shift, ignore the override from the chunk disagreement. don't hold... ignore.
does that rescue our class of problems while saving the legitamate fixes. it should absolutely fix the
problems on this capture (cap 1)."

**Premise.** A real picture displacement moves the top and the bottom together — §7's tandem principle,
the owner's own: extra blank space below for an upward shift, above for a downward shift. A top that
moves while its bottom stays put is therefore not the picture moving; it is the top measurement
changing its mind. Where the new coherence rule produces such a move it should be **ignored** — the
previous top stands — not held, which would freeze the whole geometry.

**Why this and not another threshold.** Five approaches were measured and refuted first: excluding
boundary-straddling chunks, finer sub-chunking, discarding wholly-disagreeing chunks, a
contrast-restricted comb override (23 frames, 0.027%) and abstaining on high contrast (33:1 against).
This is the first with a favourable ratio, and unlike the others it rests on a physical claim about
the signal rather than on a statistic that separated one population from a differently-defined one.

**Measured before building, so the entry is not written to a known answer.** Classified by the
engine's own `classify()` over the whole tape: **TOP ONLY is 34.5% of the regression (717 of 2,079
classifiable) against 6.2% of the fixes (329 of 5,310) and 4.1% of all edges** — a 5.6-fold
enrichment. Ignoring those moves avoids 717 bad edges and costs 329 good ones, **2.2:1**.

That 717 is a **lower bound**. The regression arrives in 319 runs; only a run's onset is a top-only
move, and the 61.4% classified `nothing` are units mid-run inheriting a top that is already wrong.
Suppressing an onset means the run never starts, which a static classification cannot show and only
the engine can measure.

**The method.** When `f->motion[k]` is `GE_TOP_ONLY` on an adjacent, non-reset unit, the previous
unit's top stands for that field. The measured value is still logged: observations are immutable and
interpretations revisable, so the sidecar must show what was measured as well as what was applied.
Nothing else changes — not the bottom, not the comb, not abstention.

**Falsifier.**
- The independent gate's late-top count does not fall, or the fixes lost exceed the regression avoided.
- Or the owner's four labelled units (69566, 69568, 69570, 69573 → f1 26/26/25/26, f2 288) stop landing.
- Or comb agreement regresses in any confidence band.
- Or it suppresses real movement: `GE_VALID_MOVE` and `GE_BOTTOM_ONLY` counts change, which they must
  not, since the rule touches neither.

**What it is already known NOT to fix, recorded so the report cannot claim it.** On capture 1 the rule
reaches 48 of 806 changed field-edges. Half of that capture's change is the new rule declining to place
a top at all during a paused passage — the owner: "half of cap 1 is garbage during a pause" — and a
tandem test says nothing about an abstention, because there is no move to ignore. The owner's
expectation that this fixes capture 1 is not supported by the static measurement; what it does reach
there is the relative-alignment change, 89 of ~215 classifiable edges among the 415 frames the comb
cannot judge.

**Material.** All 86,293 exact units and capture 1. Judged by the independent gate and by the owner's
labelled units, not by the comb alone, since the comb is blind to the common-mode part of this change.

### Amendment 1 to entry 31 (2026-09-22) — the rule narrowed, and a falsifier of mine withdrawn

**Registered before the build proceeds.**

**The rule is narrower than the entry states.** The owner, after seeing the spec: "just having it
abstain whenever there is high coherence and the top moves only is wrong", and then twice: "it should
only abstain IF there is high coherence AND the level is near blanking", finally "it needs to be top
moves, bottom doesn't, level of top is near blanking" — "in other words, a low confidence decision".
The coherence term is not in the final statement. The conjunction is **top moved, bottom did not, and
the newly chosen top's level is near blanking**, where nearness is the top line's body 95th percentile
against the derived horizontal-blanking level the engine already computes. Its physical reason is his:
that combination is weak evidence, and weak evidence should not be enacted.

**A falsifier of mine is withdrawn because it was unsatisfiable.** The entry required
`GE_VALID_MOVE` and `GE_BOTTOM_ONLY` counts to be unchanged, "since the rule touches neither". That is
wrong. The class is computed by comparing a unit's top against the previous unit's, so substituting a
top necessarily reclassifies the NEXT unit. Codex's preflight produced the counterexample before any
production code changed: unit 102, measured top/bottom 24/261, `bottom only` becoming `valid move`
with `comb_ran` 1 → 0. My criterion forbade the mechanism the entry predicts. The class and
comb-scheduling deltas are still reported in full — they are evidence about what the rule did — but
they are not a gate.

**Interpreted history is the design, deliberately.** The substituted top feeds the next unit's
comparison. The owner said "ignore", not "hold", and the entry's predicted effect depends on it: 61.4%
of the regression classifies as `nothing` because it sits mid-run inheriting an already-wrong top, so
only onset suppression reaches it. Keeping the measured series would let a rejected top reassert on
the next unit and recover none of that. The measured tops remain in the log beside the applied ones,
so the record stays immutable even though the engine's working history is interpreted.

**What this costs the entry's prediction.** The 34.5%-against-6.2% enrichment was measured for the
top-only condition ALONE. The third condition can only reduce it, so 717 avoided against 329 lost is
an upper bound on reach, not an expectation. The sweep of the nearness threshold decides the real
figure, and the threshold is exposed as a control defaulting to a no-op rather than fitted.

**Unchanged falsifiers:** the gate's late-top count, the owner's four labelled units, per-band comb
agreement with gains and losses reported separately, and the bottom/profile/blanking/level columns at
0 differing units of 86,293.

## E-claude-2026-09-22-32 — refuse a move that discards picture and gains only blanking

**Question (owner, 2026-09-22, verbatim).** "What I'm trying to differentiate is if freezing the top
when there is a common mode shift rescues a class of failures. It might cause more jumps but it
wouldn't cause picture to be lost... That's a jump that has no tangible benefit, and at the most you
lose some stabilization at hopefully no cost to combing but also losing no real picture." Then, on the
geometry: "If the picture shifts up, you lose nothing at the bottom but you do lose picture at the top
and you create an artificial jump." And the conclusion the entry rests on: "mathematically You can't
differentiate these classes, so a compromise that retains the most information along with the correct
picture is the right one."

**Premise.** The two classes cannot be told apart by what the lines look like — six measured attempts
say so: chunk coherence at any scale, within-line contrast, line-to-line difference, sub-chunk
structure, near-blankness, and a comb override all failed, most with heavily overlapping populations.
They can be told apart by **what a move does to the information**. A top that moves later discards real
picture lines at the top while the fixed-height window runs further past the last picture line and
fills with blanking. That move cannot be worth taking under any reading, so it can be refused without
knowing which line is truly picture.

**Why this is not another threshold.** The test is `gain <= 0 AND overrun increases`, where gain is the
picture lines kept at the top and overrun is how far the window runs past the measured last picture
line. Both come from `f*_first` and `f*_last`, which the engine already produces. There is no number
to fit, which is what every previous candidate foundered on.

**Measured before building, on the 7,403 edges the independent gate has already judged:**

| | discards picture at the top AND increases bottom overrun |
|---|---|
| the regression (2,089 edges) | **2,031 — 97.2%** |
| the fixes (5,314 edges) | **101 — 1.9%** |

Means: the regression loses 2.19 picture lines at the top and runs 2.2 lines further into blanking,
net +4.39 lines of blanking for nothing. The fixes gain 0.99 lines at the top and sit 1.0 line closer
to the last picture line. 98.1% of fixes move the opposite way to 97.2% of the regression. This is the
cleanest separation any instrument has produced on this problem, and it is geometric rather than
statistical.

**What it costs.** Some stabilisation on the 1.9% of legitimate fixes that also increase overrun, and
more frame-to-frame movement generally, since refusing a move leaves the previous placement standing.
The owner has accepted that trade explicitly: jumps are acceptable, lost picture is not.

**Falsifier.**
- The independent gate's late-top count does not fall, or the fixes lost exceed the regression avoided.
- Or the owner's four labelled units (69566, 69568, 69570, 69573 → f1 26/26/25/26, f2 288) stop landing.
- Or comb agreement regresses in any confidence band.
- Or the cascade changes the separation materially: this is a static classification of decisions already
  made, and with interpreted history both counts can move. The near-blank instrument measured a cascade
  factor of exactly 1.00, so the expectation is that it does not, and a departure is a real result.
- Or the window is not `top .. top+239`: the aperture is my assumption, and if the render window differs
  the overrun arithmetic changes, though not the sign of the effect.

**Material.** All 86,293 exact units and capture 1, judged by the independent gate and the owner's
labelled units. The comb cannot judge this class at all: 92.4% of the regression is a common-mode
shift, which leaves the field relationship unchanged and is invisible to it by construction.

**Supersedes in practice, not by refutation:** entry 31's near-blank instrument, which reaches 25 of
2,089 regression edges (1.2%) at a 12:1 ratio. It is left in the engine disabled at the owner's
instruction, pending a cleanup pass that removes the pieces not being kept.

### Amendment 1 to entry 32 (2026-09-22) — the figures were measured on the wrong quantity

**Registered before the build proceeds.** Codex's preflight caught it before any engine edit.

**The error.** I computed overrun from the measured first picture line. The publisher's crop does not
start there: it starts at `23 + d1` (field 1) and `286 + d2` (field 2), and the comb and the hold can
move `d1`/`d2` after the measurement. Codex's counterexample from a real run: frame 4758, measured top
28, published crop top 24 — my formula reports 6 lines of overrun where the truth is 2. The correct
quantities are `max(0, 262 + frame_d1 - f1_last)` and `max(0, 525 + frame_d2 - f2_last)`, with field 1
joined to its source unit under the frame's pairing, not to the unit that owns the row.

**Re-measured on the published crop.** The separation survives, weaker than stated:

| | discards picture at the top AND increases overrun |
|---|---|
| the regression, 2,089 edges | **1,884 — 90.2%** (was claimed 97.2%) |
| the fixes, 5,326 edges | **128 — 2.4%** (was claimed 1.9%) |

Means: the regression loses 1.96 lines at the crop start and runs 1.96 further into blanking; the
fixes gain 0.32 and sit 0.32 closer. The entry's claim holds; its numbers were wrong and are replaced
by these.

**Aperture, now measured rather than assumed.** The publisher is H=240, field 1 `23+d1 .. 262+d1`,
field 2 `286+d2 .. 525+d2`. The review renderer is H=243, starting three rows higher at `20+d1` and
`283+d2`; the bottom endpoints agree. The rule uses the publisher's geometry. My "240 lines beginning
at 23/286" was right for the publisher and wrong about which start the crop uses.

**Policy chosen, with its cost stated.** Codex asked whether to veto census tops before the comb or
published crop starts after it. **Before**, on three grounds: the owner accepts the trade "at hopefully
no cost to combing", and a post-comb veto overrides comb-driven placement, which is exactly that cost;
92.4% of the regression is a common-mode shift the comb is blind to and did not cause, so the move
originates at the census; and the published crop already equals the measured top on 67,575 of 85,554
field-1 frames (79.0%), so a census veto reaches most final crops in practice.

**What this policy does NOT do, recorded so no report can claim it:** it does not guarantee the final
crop. On the 21% where the hold or the comb moves the crop away from the measured top, a vetoed top can
still be published with an increased overrun. The rule refuses the census move that would discard
picture; what happens downstream is a separate policy the owner may decide differently once he sees a
render.

## E-claude-2026-09-22-33 — the first line that looks like the line above it

**Question (owner, 2026-09-22, verbatim).** "here's my conceptual understanding. a line will have
nearly identical luma to the line above and below it in the normal case, true?" … "the whole thing we
are trying to detect is when blanking or data suddenly goes to picture. and we need something that can
detect that in a real time setting so it can't be too mathematically complex" … "I think this is the
engine we want codex to build."

**Premise, stated apart from the method.** Two picture lines carry nearly the same waveform; blanking,
a caption and a data line do not resemble the picture line beneath them. So the top of picture is
visible as a **step in the line-to-line waveform correlation**, and it is a single-line event. The
first line whose waveform correlates with the line above it is one *below* the first picture line.
Everything the current engine's top search does — a level test, its guards, the chunk rule — is an
attempt to recognise this same transition through a proxy.

**Why instantaneous, and why this kills the previous version.** Any statistic that spans lines — a
largest-rise over a window, a smoothed baseline, a rate of change measured against an accumulated
reference — lets a scene feature deeper in the picture out-score the real transition, because the
transition is one line wide and a scene edge can be larger. The owner named this before it was
measured: "you aren't looking for the largest rate of change. you are looking for a rate of change
that increases from a baseline… it should be an instantaneous rate of change. anything that smooths is
going to introduce the problem." The largest-rise version placed tops 10 and 20 lines into the picture;
the first-step version does not. Chunking was only ever a cheap way to measure the same object — "okay
but chunking is just a proxy" — and is dropped.

**The method.** Per field, walk down from the top of the search window. For each line, correlate its
luma against the line above it over the delivered body (samples 40–680), raw — no chunking, no
smoothing, no baseline window. The first line whose correlation **rises by ≥0.45 across a single
line** marks the transition; the top is that line minus one. Three rules around it:

1. **Abstain.** No single-line step clears the bar anywhere in the window → that field edge produces no
   answer. The abstention is the confidence statement; it is not a fallback to a guess.
2. **One clamp, default ±5, configurable, applied identically to both edges** (field 1 against 23,
   field 2 against 286) — the same range `ge_comb` itself searches. Outside it the placement is
   **discarded**, not clamped and published. The owner: "discard it. it doesn't [a]ct as a decision."
3. **A confident comb may override**, where the tops abstained or were discarded.

**Measured before building.** Whole tape, 86,293 units, bar 0.45:

| | |
|---|---|
| firm hand-checked labels | 11/11 |
| edges placed | 155,364 (90.0%) |
| edges abstained | 17,222 (10.0%) |
| units with both edges placed | 74,202 (86.0%) |
| discarded by the ±5 clamp | 1,369 units (1.6% of the tape) |
| field-1 tops ≥26 surviving the clamp | 5,654, against ~15,600 on both current engines |
| field-1 tops ≥30 surviving the clamp | **0** |

**Falsifier.**
- The C engine does not reproduce the Python census unit-for-unit — same top or same abstain on each
  of the 172,586 field edges. A disagreement indicts the build, and if the build is right it indicts
  the premise; either way it is reported, never absorbed.
- Or the owner's labelled units stop landing (69566, 69568, 69570, 69573 → f1 26/26/25/26, f2 288).
- Or field-1 tops at 30 and beyond come back, which is the defect this is aimed at.
- Or it costs more real placements than it saves bad ones on the render.

**Two things this rests on that are weaker than the table looks, recorded so no report can hide them.**
The bar 0.45 is not derived from a distribution: it is the value that separated **eleven** hand-checked
frames, and it may want to move once the renders are seen. And the independent gate that produced every
comparative score in entries 30–32 detects **late** tops only — a top placed too early scores
`abstain`, never `wrong` — so every "wrong" count across this work is one-directional and understates.

**Material.** The whole tape for the census; captures 1–4 for the renders the owner validates first.

## E-claude-2026-09-22-34 — a comb that cannot choose can still refuse

**Question (owner, 2026-09-22, verbatim).** "but the actual used comb is trash? from what I can see
in the render, the red box selected one is much higher than the one noted as the minimum" — then,
on the proposed guard: "yes thats the change I want".

**Premise, stated apart from the method.** The comb's power to *select* and its power to *reject* are
different quantities, and the engine only tests the first. `decided = energy[second]/energy[best] >=
1.5` asks whether the best candidate beats the runner-up. When the two best are adjacent and nearly
tied it answers no — but that tie says both are good, and says nothing about a third placement far
away. A comb that cannot choose between +0 and +1 is still perfectly able to say −1 is wrong. The
engine already computes the whole 11-entry energy array every frame and never compares the shift it
is about to publish against the best one in it.

**The measurement that found it.** At cap3 counter 13576 the array is

| shift | −5 | −4 | −3 | −2 | −1 | +0 | +1 | +2 | +3 | +4 | +5 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| energy | 711.7 | 628.8 | 531.3 | 423.6 | **282.2** | **4.3** | 4.3 | 284.8 | 425.4 | 529.3 | 619.5 |

The engine published **−1**, at **66× the minimum**, because the margin test saw 4.3 against 4.3,
returned undecided, and let a held correction speak unchallenged.

**Population, all four captures, published frames where the published shift's own energy is ≥2× the
best available:**

| | frames | of | comb undecided | comb decided |
|---|---|---|---|---|
| cap1 | 15 | 919 | 15 | 0 |
| cap2 | 5 | 649 | 5 | 0 |
| cap3 | 2 | 648 | 2 | 0 |
| cap4 | 4 | 650 | 4 | 0 |

**26 of 26 had `decided = 0`.** Across 2,100 frames where the comb did decide the ratio never
exceeds **1.9**, and its median over all 2,866 published frames is **1.000** — normally the published
shift *is* the best. That separation is why the bar is 2.0 and not a guess.

**Two populations, recorded because the remedy differs and a report must not merge them.**
- **A held correction is the bad shift** — 2 frames (cap3 13576, 13577). Dropping the correction
  falls back to the measured tops, which are right there.
- **The measured tops are themselves the bad shift** — 20 frames, mostly cap1's run at 6257–6267,
  where the waveform accepted f1 28 / f2 289 giving st −2 at energy 130.4 while the comb's minimum is
  +2 at 10.3. Falling back changes nothing; the comb's best is the only other answer available.

Both were checked against an instrument the engine does not use — mean |line − average of its two
neighbours| over the woven frame:

| | published | comb's best | |
|---|---|---|---|
| cap3 13576 | 10.608 | 5.348 | comb's best |
| cap1 6257 | 6.330 | 2.795 | comb's best |
| cap1 6264 | 6.521 | 2.939 | comb's best |
| cap1 6266 | 6.482 | 2.805 | comb's best |
| cap1 6267 | 6.481 | 2.872 | comb's best |

**The method.** Whenever the comb has run, compute `reject = energy[published_shift]/energy[best]`.
If it exceeds a configurable bar (`GE_COMB_REJECT`, default **2.0**) the published shift is refused:
any held correction is dropped, and the comb's best shift is substituted. The refusal, the ratio, the
refused shift and the substituted one are all logged — the observation stays immutable and the
interpretation is visible.

**Falsifier.**
- Any of the 26 does not change, or changes to something the roughness instrument scores worse.
- Or any frame outside the 26 changes: 0 of 2,100 comb-decided frames exceed 2.0, so the guard must
  be inert wherever the comb decided.
- Or the whole-tape census disagrees on any of the 172,586 field edges — the guard must not touch the
  top measurement, only what is published from it.
- Or the owner's labelled counters stop landing.

**What this does not claim.** It does not make the waveform's absolute tops right on cap1's run —
they were accepted at 28/289 and the frame still weaves four lines away. It fixes what is published,
not what was measured, and the gap between those two is entry 33's unfinished business.

**Material.** Captures 1–4 for the renders; the whole tape for the census identity.

### Amendment to E-claude-2026-09-22-34 (2026-09-22) — a minimum is a minimum only if it rises on both sides

**The falsifier fired.** Codex built the guard, changed exactly the 26 frames and nothing else, then
stopped: three of them — cap1 6271, 6272 and cap2 2309 — score *worse* on the independent roughness
instrument. It left the engine, sidecars and renders unchanged and reported the failure rather than
narrowing the rule on its own. `FRAMES_CHANGED=26 EXTRA_CHANGED=0 DECIDED_FRAMES_CHANGED=0`.

**The physical reason, the owner's, verbatim.** "isn't the best shift supposed to be a minimum on
both sides? otherwise it shouldn't have any confidence. thats what a real comb does."

The three failures share one shape: the energy runs **monotone into the wall of the ±5 search range**.

```
6271     14.3  13.8  13.1  12.6  11.9  11.3   6.5  6.0  5.3  4.6 [4.4]   strictly decreasing to +5
6272     11.2  10.4   9.3   8.6   7.9   6.9   5.9  5.1  4.4 [4.2] 4.7    decreasing to +4
2309    954.1 843.6 734.3 624.7 507.4 391.4 292.2 198.7 103.6 [46.0] 61.6 decreasing to +4
```

Such a comb has not located an alignment; it is reporting that the alignment lies outside its range.
Reading the edge value as a minimum reads the end of a slope as a basin. Two more in the set, 2311
and 2312, are the same shape (monotone to −5) and were scored too generously as successes: they
improved only 9.37→8.02 and 10.10→9.23, terrible to slightly-less-terrible.

**The amendment, and it introduces no new constant.** Take the **floor** — the minimum plus any
adjacent shift within the engine's existing 1.5 factor, i.e. the shifts the engine already considers
indistinguishable from it. Substitute the comb's best only when the floor lies wholly inside the
search range *and* the energy rises by that same 1.5 on both sides of it. Otherwise the published
shift is still refused, but nothing is substituted: the frame is **discarded**, per the owner's
standing ruling that an unsupported placement "doesn't act as a decision".

**A rejected first attempt, recorded because it was nearly shipped.** An earlier form required the
minimum to rise against its immediate neighbours. That rejects 13576 — the flagship case — because
its two best shifts are *tied* at 4.3, so each reads as a flat neighbour of the other. Treating the
tie as the floor, 13576 rises 66.1× on the left and 66.7× on the right: the sharpest basin in the
set. A separate attempt used `|best shift| <= 3`, which separates the same 26 but is a bar read off
the failures it explains; the owner's two-sided condition supersedes it and is preferred because it
is a statement about the signal, not about the outcome.

**Separation, all 26, zero disagreements:** every frame the roughness instrument scored worse falls
out as *no minimum found*; every frame it scored better is a basin with both arms present. Floors:
13576 at +0..+1 (66×), 6257–6267 at +2..+3 (~5×), cap4's four at +0..+1 (1.5–2.7×); against
6271/6272 at +1..+5, 2309 at +4..+5, 2311/2312 at −5..−4, all touching the wall.

**What this must not break.** The 21 substitutions stand and must still score better on roughness;
the five discards must publish no substituted shift; nothing outside the 26 may change; the 172,586
census edges stay identical. **What is still open:** whether a discarded frame holds the previous
placement or publishes the measured tops — not decided here, and the report must say which it did.

**Forward or not.** Forward: it removes a whole failure mode rather than excusing three cases, it
adds no number, and the condition is about the energy profile's shape rather than about the frames
it was found on. It has been checked only on the 26; the whole tape is material it was not built on.

## E-claude-2026-09-22-35 — if you cannot measure all four edges, do not shift

**Question (owner, 2026-09-22, verbatim).** "the card gets shifted up by +2/+2 and then by +5/+5 when
it appears on the screen. problem starts at 6641 for the first shift, then 6667 for the second… in all
of those there is no top in at least 1 of the fields. no top in 1 field within a frame should be
disqualifying to create a shift" — then, when the first form of the rule proved too narrow: "c'mon
now. if you can't measure all 4 tops and bottoms, don't shift shit... period"

**Premise.** A picture displacement is a statement about where the whole picture sits, and the only
evidence for it is the four edges — both fields' tops and both fields' bottoms. A frame that cannot
produce all four has not measured a displacement; it has measured a fragment, and a fragment must not
move the published crop. This is the owner's tandem principle applied to the *absolute* placement
rather than to the relative alignment.

**What the engine does instead.** The relative shift is correctly guarded on both tops
(`known = t->first[0] && b->first[1]`), but the absolute anchor is taken from field 2 alone,
unconditionally:

```c
int d2 = b->first[1] ? b->first[1]-286 : (g->have_placement ? g->last_d2 : 0);
o.frame_d1 = d2 - d;  o.frame_d2 = d2;
```

Field 1's own top enters only through `st`, and `st` is discarded whenever the comb decides. So one
field's top can move the entire frame, and at capture 1's boxed card it does — twice.

**Why no existing guard could have caught it, measured.** A common-mode shift moves both fields
together, leaving the relative alignment unchanged, so every relative instrument is blind to it *by
construction*. Vertical roughness across (0,0) through (5,5) on the card frames spans 0.061, 0.103 and
0.148 — nothing is distinguishable from anything. The comb measures relative alignment and cannot
validate an absolute anchor; there is no second witness for the anchor anywhere in the engine.

**The method, in the engine's own vocabulary.** A published placement may move only when all four
edges are measured and neither field's motion class is `unknown` — `unknown` being exactly the state
where an edge was unmeasurable so motion could not be determined. The classification already exists
(`class_f1`/`class_f2`); the anchor is gated on it. No new classifier.

**Population, all four captures, every frame where the published placement moved:**

| motion class | moves | | motion class | moves |
|---|---|---|---|---|
| valid move / nothing | 144 | | unknown / nothing | 8 |
| nothing / top only | 118 | | nothing / nothing | 8 |
| top only / nothing | 76 | | nothing / unknown | 7 |
| not in tandem / nothing | 46 | | **unknown / unknown** | **5** |
| bottom only / nothing | 10 | | 17 smaller classes | — |

456 moves in total; **20 carry `unknown` in at least one field**, and both of the owner's card shifts
are among them — 6641 `(0,0)→(2,2)` and 6667 `(2,2)→(5,5)`, each classed `('unknown','unknown')`.

**The first form of the rule, recorded because it was dispatched and was wrong.** "Both tops measured"
reaches 6641 but not 6667, where all four edges *are* present (f1 25/262, f2 291/525). What is wrong at
6667 is that the tops moved while the bottoms did not — f1 bottom 262 and f2 bottom 525 hold constant
across 6663–6673 — which the engine already classes `unknown` because field 2 had no top in the
preceding frames. The bottoms were necessary; the tops alone could never have caught it.

**Falsifier.**
- The 20 moves are not refused, or frames outside them change other than by propagation.
- Or the card still shifts at 6641 or 6667.
- Or the census disagrees on any of the 172,586 field edges — this gates publication, never measurement.
- Or a refused move strands the picture: the change is stateful, so refusing 6641 means 6667 is reached
  from (0,0) and 6878's return to (0,0) becomes a no-op. Direct refusals and propagated changes are
  reported separately.

**Deliberately excluded, so no report can claim it.** `top only` (194 moves), `bottom only` (19) and
`not in tandem` (55) are frames where all four edges *were* measured and contradict each other. That is
entry 31's territory and a far larger behavioural change. It is measured here and left alone.

**What is not understood.** Why the waveform accepts a top at 291 on the card at all. The likely
mechanism is that a flat dark picture region has near-zero variance, so its correlation is forced to
zero exactly as blanking is, and the first step lands on the card's textured edge rather than on the
top of picture. That is a limitation of entry 33's instrument and is not addressed by this entry.

**Material.** Captures 1–4; the whole tape for census identity.

### Amendment to E-claude-2026-09-22-35 (2026-09-22) — the gate was the wrong layer; the defect is in the measurement

**The falsifier fired, on the entry's own terms: "the card still shifts at 6641 or 6667".** Codex built
the four-edge gate and reported that it delays the shift rather than removing it — counters 6641–6669
hold (0,0), then **6670 publishes (5,5) with both motion classes `nothing`**. It also changed 56 frames
against an expected 20 (32 direct holds, 24 propagated). It was not promoted.

**Why it could never have worked, and this supersedes the entry's method.** A motion class describes
*change between frames*; the anchor is *absolute*. Once the card's top has been measured on two
consecutive frames, "nothing moved" is true and the anchor still reads +5. **Motion cannot witness a
position.** The entry's premise — that the four edges are the evidence for a displacement — stands;
gating on the engine's motion classification was the wrong instrument for it.

**The real cause, measured line by line at counter 6667, field 2** (mean / sd / correlation with the
line above):

| NTSC | mean | sd | corr | |
|---|---|---|---|---|
| 285 | 1.4 | 0.49 | +0.004 | blanking |
| 286 | 2.0 | 1.15 | −0.032 | blanking |
| **287** | **19.8** | 2.04 | −0.048 | **picture starts — an 18-code jump** |
| 288–290 | 20.9–22.2 | ~2.2 | −0.17…+0.11 | dark picture, no correlation |
| 291 | 25.6 | 2.46 | −0.229 | **the engine's top, four lines late** |
| 292 | 26.4 | 2.37 | +0.310 | step +0.538 clears the 0.45 bar |

The picture begins at 287. Rows 287–291 are dark and low-contrast, so row-to-row correlation is
dominated by their own noise and never rises. Field 1 on the same frame is sharp (23: 4.2, 24: 9.6,
25: 23.5, step +0.833 at 26) and its top of 25 is right. Measured against each field's own blanking the
card frame sits at about **d1 +2, d2 +1** — a coherent near-common-mode displacement. The published
(5,5) is entirely field 2's four-line miss.

**A hypothesis of mine, refuted and recorded so it is not re-tested.** I proposed that a flat dark
region has near-zero variance and is forced to correlation 0 by `waveform.py`'s guard, exactly as
blanking is. It is not that: those rows measure sd 2.0–2.9, far above the 1e-9 floor. Correlation
requires *structure*, and dark low-contrast picture has none above its own noise.

**Verdict on the entry: premise held, method refuted.** The four edges are the right evidence; the
engine's motion classification is not a way to read them, and no publication gate can repair a top that
was measured four lines late. **This is a defect in entry 33's instrument**, and the two instruments
look complementary — correlation for structured picture, level for dark picture, which is the amplitude
test entry 20 was built on. That is a new entry, not an amendment to this one.

**Not fixed in the render the owner will see next**, and he was told so rather than finding out.
