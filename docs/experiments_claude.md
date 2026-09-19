# Experiment ledger — Claude

Commitments written and committed before each deciding test, per CLAUDE.md §14 (experiment
commitments). Append-only: entries and amendments are added, never edited. Each report answers its
entry. Results, panels and data stay in scratch; an entry points to them.

## E-claude-2026-09-19-1 — comb-free weave from each field's first picture line

**Question (owner, 2026-09-19):** "if we can determine the number of picture lines, we can also
determine the geometry." "if we can align the picture and get the field order correct, there should be
no combing ... all we want to do is designate which is the first and last line of picture (including
the head switch area, and [track] that." Goal: all four captures comb free; then, without changing the
mechanism, the whole tape 95% or more comb free; every valid unit, no sampling; 720x486 renders of the
four captures. Capture 1's top is known: line 23.

**Premise.** In every valid unit the two fields' first picture lines are the same source line, so a
weave that puts the top field's first picture line directly above the bottom field's is free of
combing. Second part: that first line can be told from the lines above it (the Shuttle's lines 20/21
and 283/284, blank lines, raw tape caption and data lines) from the raster alone, or carried from the
last unit where it could.

**Pairing, measured, not assumed** (scene cuts: the two fields of one frame agree at a cut, a pair
straddling it does not): capture 3 reversed (5 of 5 cuts), captures 2 and 4 aligned (3 of 3, 5 of 5),
capture 1 aligned (owner; no programme cut). The owner's note had capture 2 reversed; the data does not.
Whole-tape segments between deck relocks are measured the same way in the same pass.

**Method.**
- Judge, independent of the tops (owner-specified): textbook comb, (a-b)(c-b) positive part, mean over
  samples 24-695 and top-field lines 30-240, bottom field shifted -5..+5 lines; the minimum is the
  comb-free shift; decided when the next-lowest is at least 1.5x the lowest, otherwise the judge abstains.
- Top, per field: walking down from line 22 (285), the first line whose mean over samples 20-700 is
  more than 6 codes above the device blanking rows and that continues into the line below (correlation
  0.5 or more over samples 20-700, or both lines flat within 3 codes). None found by line 40: carry the
  field's last top.
- Bottom, per field: walking up from 262 (525), the last line more than 6 codes above blanking. Tracked
  and reported, not used for the weave.
- The weave's shift is the bottom field's top minus the top field's top, in field lines.
The numbers are this experiment's settings, not instrument constants.

**Falsifier.** Decided units where the comb's shift differs from the tops' shift while the raw rows show
both tops were found correctly: the tops are right and the weave still combs. For the second part:
capture-1 units where the top is not 23 / 286, and units elsewhere where the raw rows show the found top
is not the first picture line.

**Material.** Every exact unit of capture 1 from counter 6667 (6610-6666, the fade-in the owner left
unregistered, reported apart), capture 2 (whole-tape counters 67,446-68,094), capture 3 (13,501-14,149),
capture 4 (171-820). Held out, not used to build anything: the whole tape, every exact unit outside the
three non-programme events (counters up to 4725, 48,189-48,240, 53,616-53,674).

Results, panels and renders: session scratch `geometry_exp1/`.

### Report 1 (2026-09-19) — premise refuted; stopped, no amendments

- **Judge** checked on raw rows at 6 frames across all four captures (woven crops at both shifts): its
  minimum is the clean weave every time.
- **Part 1 (same source line): refuted** on captures 2 and 3 where the tops are clear. Capture 3 frame
  13501: tops 286 / 24, both confirmed picture on raw rows, 285 blank; the clean weave (+2) puts field B's
  first picture line above field A's, the reverse of the committed order. Capture 2 frame 67654: tops 25 /
  288 confirmed, 287 a data line; the clean weave (-1) puts that data line inside the picture, between
  25 and 26.
- **Part 2 (tops readable from the raster): refuted as built** on capture 1 (154 of 508 frames not 23 /
  286; the near-blank card) and capture 4 (field-2 tops misread on displaced top lines, about 160 frames).
- **Population**, decided frames and tops' shift = comb shift: capture 1 371, 226 (137 abstained);
  capture 2 551, 159 (98); capture 3 586, 27 (62); capture 4 590, 466 (60).
- **Bottoms:** 262 / 525 in every frame of all four; the deck blanks 263 / 526, so the last visible line
  is the deck's raster edge, not the tape's picture.
- **Amendments:** none. Detector fixes for captures 1 and 4 cannot reach the goal while part 1 fails on 2
  and 3. No renders (goal not reached); whole-tape check not run.
- **Not understood:** why field B's first line leads in capture 3 and lags in capture 2; whether the blank
  line 22 / 285 hides a first picture line.

### Review by Codex and correction (2026-09-19)

Codex reproduced the reported counts and both counterexample frames independently. Accepted:
- **Capture 3 is not a refutation.** For its reversed pairing the experiment put the temporally first
  field (slot 2) on top. Keeping the same two fields with slot 1 on top, the tops' shift equals the comb
  minimum in 555 of 586 decided frames (was 27). Pairing says which fields belong together, not which is
  spatially on top; slot 1 is the top in every capture. Its "lead" is explained by that choice.
- **Part 1 is refuted on capture 2 only.** Frame 67654 survives the parity check. With slot 1 on top the
  four captures agree in 226 / 371, 159 / 551, 555 / 586 and 466 / 590 decided frames. Captures 1 and 4
  miss mainly on tops the detector misread.
- **Part 2 is "this detector fails", not "the raster cannot give the top."** Capture 4 frame 235:
  line 286 already holds partial picture and the detector returned 292. Capture 1's 154 are departures
  from the owner's 23 / 286, not independently labelled misreads.
- **Judge:** checked on six raw crops chosen where the shifts disagree most; the counts are agreement
  with this judge, not independently measured comb-freedom. It used top-field lines 30-239, not the
  committed 30-240; including 240 changes only capture 1 frame 6845, which abstains either way.
- **Bottoms:** the fixed 262 / 525 and blank 263 / 526 are observations here; that the deck blanks
  263 / 526 in playback comes from the separate half-line measurement, not from this experiment.
- **Accounting added:** capture 1 fade interval 6610-6666: 57 frames, 2 decided, 0 matching, 55
  abstentions. Capture 3 counter 14149 has no following field to pair and was not evaluated. One carried
  top in capture 1 (main) and one in the fade.
The stop stands: capture 2 prevents "all four comb-free" under this premise.

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

## E-claude-2026-09-19-4 — a level x entropy matrix for picture lines

**Question (owner, 2026-09-19):** "is line entropy a better measure of picture vs no picture. Anything
that is blanking, near blanking or data will have low entropy so I don't think this test can live in
isolation, but might allow us to tighten the number of codes above blanking required along with a
certain entropy value ... come up with a matrix between those 2 values that can hopefully more
correctly identify picture lines ... the matrix decides which to give more weight".

**Premise (his).** Blanking, near-blanking (filler) and data rows have low line entropy; picture rows,
including faint and torn ones, sit apart from them in the plane of (level above blanking, entropy), so a
cell map over that plane classifies rows more correctly than entry 2's level-and-variation rule.

**Method.** Per row, over samples 40-680: level = 95th percentile minus the device blanking rows;
entropy = Shannon entropy (bits) of the row's 8-bit code histogram. Labelled rows come from the confident
census (raw-row verified bins; capture 4 field 2 from Codex's raw labels; capture 3's line 23 as
labelled in the report above; exclusions as in entry 3): at the top, rows from 22 (285) above the first
picture line are not picture and the first line and the two below are picture; at the bottom, the last
line and the two above are picture and the rows below it through 263 (526) are not. Matrix: level bins
0,1,2,3,4,6,8,12,20,40+ codes x entropy in half-bit steps; each cell takes its majority label, or is
mixed. Each capture is classified by a matrix built from the other three only. The matrix census (first
picture row from 22 / 285 down, last from 262 / 525 up) is then judged by raw rows and by the comb,
exactly as entry 3, and compared with entry 2's rule on the same rows.

**Falsifier.** Picture and non-picture rows overlap in the plane (mixed cells hold a material share of
either class), or on held-out captures the matrix classifies rows no better than entry 2's rule, or it
still gets the hard rows wrong: capture 3's faint pulse row 23, capture 1's faint card line 23,
capture 4's torn tops, capture 2's data lines.

**Material.** Every confident unit of the four captures (capture 1 from 6667). Labels depend on
bin-level raw checks (up to 3 units per bin), not a per-unit relabel; stated as a limit.

### Report (2026-09-19) — premise partly refuted; no amendment

- **Held:** blanking (median entropy 0.96 bits, level 1) and the filler / near-blank rows (1.9 bits,
  level 11) are low-entropy and sit apart from picture (median 6.1 bits, 10th percentile 4.0).
- **Refuted for data:** capture 2's data lines are 4.85 bits (4.3-5.4) at level 127, inside picture's
  range. **And for faint rows the axis points the wrong way:** capture 1's faint card picture line 23 is
  2.85 bits at level 8; capture 3's faint pulse row 23, not picture, is higher on both (3.6 bits, 12).
  Torn capture-4 tops are 6.2 bits, so entropy does help there.
- **Mixed cells** (minority 20% or more) hold 1,699 non-picture and 1,142 picture rows of 44,889.
- **Held out by capture**, rows classified correctly, matrix vs entry 2's rule: capture 1 0.890 / 0.992,
  capture 2 0.840 / 1.000, capture 3 0.956 / 0.966, capture 4 0.994 / 0.974. The rule's figures are
  inflated: most labels come from its own verified bins; capture 4's (Codex's raw labels) are the fair
  comparison, and the matrix wins there.
- **Matrix census through the comb** (decided frames where its shift is the comb minimum): capture 1 248 /
  370, capture 2 232 / 551, capture 3 201 / 586, capture 4 533 / 590, against entry 3's 229 / 230, 2 /
  545 (a constant line), 487 / 500, 562 / 567 on confident frames. It calls capture 2's data lines and
  capture 3's faint pulse row picture in nearly every unit, and loses capture 1's faint card top.
- **Structural limit:** each hard row type occurs in one capture only, so a matrix built from the other
  three never sees it; a held-out test cannot learn it, and fitting it in-sample would be memorising.
- **Amendments:** none. Matrix, rows and frame results in scratch `geometry_exp1/exp4_*`.

### Capture 2's one-line offset, explained (2026-09-19; measured without a prior entry)

The owner asked whether field 1's first picture line in capture 2 is really picture or "that field's
line 22 being leaky". The tape's caption (source line 21, found by its clock run-in) sits directly above
field 1's first picture line in every unit: raster 24 when the top is 25 (384 of 385), raster 23 when
the top is 24 (262 of 264). So field 1's first visible picture line is source line 22 in both states.
Field 2 has no run-in; by the comb its first picture line 288 is source 286, and 287 (source 285, its
line-22 counterpart) carries data. Neither a misread nor a displacement: the source carries picture on
field 1's line 22 and data on field 2's. Taking field 1's top one line lower (source 23), capture 2's
census shift equals the comb minimum in 543 of 545 decided frames (was 2); the two exceptions, 68025 and
68026, have margins 1.53 and 1.63. Panel: `geometry_exp1/explore/cap2_woven_top.png`.
