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

## E-claude-2026-09-19-5 — the census against the comb on the whole tape (held out)

**Question (owner, 2026-09-19):** "I am willing to say the previous census we arrived at is the right
shape ... see the agree/disagree amount on the full tape."

**Premise.** The census, run automatically, finds each field's first picture line on the whole tape
well enough that weaving the tops together is the comb-free weave on most valid frames, as it was on
captures 2-4, which came from this tape.

**Method: only the automatic parts of the census** (capture 4's hand labels and capture 1's card do not
exist on this tape). Per unit and field, from the device blanking level: (1) entry 2's rule, first
picture row from 22 (285) down; (2) field 1: if that row is 23 and 23 is not plainly picture (more than
30 codes above blanking on average and correlating 0.5 or more with 24), rescan from 24 (capture 3's
faint pulse row); (3) line 22: if the tape caption's clock run-in (score 0.5 or more) sits directly
above field 1's first line AND the row directly above field 2's first line is not blank (brightest
content more than 5 codes above blanking), field 1's top is taken one line lower (capture 2). Slot 1 is
the top field. Pairing per segment between deck relocks, by the scene-cut test in the same pass.
Judge: entry 1's comb over lines 30-240, -5..+5, decided at 1.5x.

**Falsifier.** Fewer than 95% of decided frames agree (the owner's bar for the whole tape).

**Material.** Every exact unit outside the three non-programme events (counters up to 4725,
48,189-48,240, 53,616-53,674); frames with no top found are counted, not carried.

### Report (2026-09-19) — below the 95% bar: 80.7%

Every valid exact unit (86,028). Decided frames where the automatic census shift is the comb minimum:
62,017 of 76,886 (80.7%); the comb abstains on 9,060; no top found 22; one frame without a partner.
By segment: first recording 31,349 / 38,567 (81.3%, reversed pairing); after the boundary to 27:18
3,808 / 4,869 (78.2%); after 27:18 26,860 / 33,450 (80.3%). Falsifier met.
- **Pairing** by scene cuts is steady: reversed through 47,995, aligned from 48,188 to 81,361, mixed
  81,539-85,123 (alternating runs; likely source cadence, not a relock), aligned from 85,130.
- **Where it holds:** field 1 at 23 by the rule in the first recording, 98.7% of 14,953; field 1 at 25
  with the line-22 offset and field 2 at 288 after the boundary, 99.4% of 17,268.
- **Where it fails:** the faint-row rescan (23 not plainly picture, rescanned to 24) in the first
  recording, 79.2% of 18,351; field 1 at 24 by the rule there, 39.6% of 3,043; field 2's data line 287
  accepted as picture after the boundary, under 1% of about 2,500; field 2 at 286 after the boundary with
  a rescanned field 1, 0% of 1,087. The automatic census is weakest exactly where the confident census
  relied on hand labels.
- Per-unit results: scratch `geometry_exp1/exp5_w{1..4}.csv`, summary `exp5_summary.py`.

### Observation from the owner's render review (2026-09-19; analysis, no test run)

Raw rows at the frames he flagged: when a field's picture moves UP one line, its first visible line
does not move, because the line that would become first slides under the fixed blank line above it
(22 / 285). Capture 4 597, field 1: every line carries the next line down of 596, line 22 stays at
blanking (1.4), and the switch-debris row 262 goes to 3.1 (from 86.9) because the debris moved to 261.
Capture 3 13602 slot 1: the same, top still 23, last line 260 -> 259. Downward moves do move the top.
So the first picture line is one-sided; the census placement used it alone, and each upward move combs
(capture 3 13575, 13601-13603, 13779; capture 4 597). Separately, the carried placements at capture 2
1969 and capture 3 13604 / 13783-13789 were the confident-census rule's exclusions, not the signal: in
13784-13789 the top really is 24 (faint row at 23), a class the rule wrongly lumped with "under a strong
caption". Panels: session scratch `render_findings/`.

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

## E-claude-2026-09-19-8 — the whole-tape census with the unbroken-block rules

**Question (owner, 2026-09-19):** "With this new finding, let's run a whole tape census applying these
new rules."

**Premise.** The owner's two rules, applied to the census's first and last picture lines, give the
comb-free placement on the whole tape. Rule 1: the picture forms one unbroken block across both fields.
The deck's own blank line 22 / 285 may sit inside it only where a field's first line has slid under it.
Rule 2: a field whose last line rises one while its first line holds has moved up. Its real first line
is under that blank line, so it goes down a line.

**Method.**
- **Edges, per unit and field.** First lines: entry 5's automatic census exactly (its rules 1-3). They
  are recomputed in the new pass and must match entry 5's per-unit files unit for unit. Last lines:
  entry 2's rule, unchanged. Walking up from 262 / 525, take the last line whose 95th percentile is
  more than 5 codes above the device blanking and whose 5-95 spread is over 4.
- **Rule 2, per field in unit order.** A count u starts at 0 and returns to 0 after any gap. If the
  first line equals the previous unit's and the last line is exactly one line higher, u goes up by 1.
  If the first line holds and the last line is exactly one line lower, u goes down by 1, not below 0.
  If both hold, u carries; any other change resets u to 0. The field's effective first line is its
  first line minus u; its last line is unchanged.
- **Rule 1, per frame,** with pairing per segment as in entry 5. st is the bottom field's effective
  first line minus the top field's, in field lines, and sl the same for last lines. The top edge
  allows d in {st, st+1}; the bottom edge allows d in {sl, sl+1}.
  - One shared value: the rule decides d.
  - Two shared (equal heights): the rule cannot decide.
  - None shared: the edges contradict.
  - Where the rule does not decide, the placement falls back to d = st, the top field's line on top.
    That is entry 5's placement wherever u = 0 in both fields.
- **Judge:** entry 5's comb verdicts, from the same frames, decided at 1.5x.

**Report.** Agreement with the comb against entry 5's placement on the same decided frames (80.7%):
- by segment;
- by entry 5's top cases;
- by rule class (decides, equal heights, contradict, no last line), with frames that carry a
  moved-up count apart.
Units that are in captures 2 and 3, from which the rules were built, are reported apart from the
held-out rest.

**Falsifier.** Fewer than 95% of decided frames agree with the comb where the rule decides, or overall
(the rule where it decides, the fallback elsewhere) below the owner's 95% bar. The change against 80.7%
is reported either way.

**Material.** Every exact unit outside the three non-programme events, as in entry 5 (counters up to
4725, 48,189-48,240, 53,616-53,674).

### Report on entry 8 (2026-09-19) — premise refuted: 56.9% against 80.7%, a regression

Stopped for the owner: under the §14 rule, an amendment would be needed and the result is a regression.
A blind reimplementation from this entry's text reproduced every number below.
- **Population.** Entry 5's first lines were recomputed identically in all 86,028 units, and entry 5's
  agreement reproduces exactly: 62,017 of 76,886 judged frames. The comb abstains on 9,060, 22 have no
  top and 1 has no partner. The valid material is 85,969 units: entry 5's report called its 86,028
  rows "every valid exact unit", but those rows include the 59 units of the 27:18 event. Its results
  are unaffected.
- **Overall:** the new rules agree in 43,737 / 76,886 (56.9%), against 80.7%. By segment: A 35.9% (was
  81.3%), B 74.3% (78.2%), C 78.5% (80.3%). Units of capture 3: 26.9% (was 91.3%). Capture 2: 98.2%
  (98.5%). Held out: 56.8% (80.4%).
- **By rule class, frames with no moved-up count:**
  - decides: 40,687 frames, agreement 96.8% (entry 5's placement: 96.7%);
  - equal heights: 6,874 frames, 2.6% for both; the comb picks the bottom field's line first in
    6,607 of them;
  - contradict: 3,530 frames, 8.8% for both.
- **Frames with a count:**
  - decides: 10,090 frames, 37.5% (entry 5: 83.7%);
  - equal heights: 13,448 frames, 0.5% (entry 5: 86.5%);
  - contradict: 2,256 frames, 0.5% (entry 5: 93.6%).
  The whole regression is in frames where rule 2's count is nonzero. Where rule 1 decides without a
  count, it meets the 95% bar but changes almost nothing.
- **Why rule 2 misfires.**
  - In segment A the count is nonzero in 24,915 of 43,463 field-2 units, from only 228 rises; once
    raised, it carries while both lines hold (runs up to 2,671 units).
  - Field 2's last line flips 522 / 523 through a partial row at the head switch, whose visible length
    varies unit to unit while the picture holds (panel below).
  - In capture 3's range, 12 of field 2's 26 rises and falls have no content move on raw rows. Field
    1's bottom there does track the picture: rises move up one in 22 of 27, falls move down one in
    20 of 24.
  - Rises and falls come in similar numbers (segment A: field 1 959 / 903, field 2 228 / 173). A count
    floored at 0 turns a return from a downward excursion into a lasting "moved up".
- **Where entry 5's 14,869 disagreements sit:** 6,696 equal heights (no count), 3,218 contradict (no
  count), 1,355 where rule 1 decides the same d, 3,600 in frames with a count.
- **Amendments:** none. **Not understood:** why the comb picks the bottom field first in almost every
  equal-height frame, and the census edges in the contradicting frames.
- Per-unit edges: session scratch `geometry_exp1/exp8_w{1..4}.csv`; analysis `exp8_analysis.py` /
  `.out`, `exp8_diag.py`; panel `e7/e8_field2_bottom_flip.png`.

### Review by Codex of entry 8's report (2026-09-19) — three findings, all accepted

Codex reproduced 43,737 / 76,886 with the committed rules. It found the attribution of the regression to
rule 2's count supported as a net attribution: at unit 13594, line 523 is still partly visible but its
5-95 spread falls to 3.05, under the census's 4, while the content does not move. Corrections:
1. **The diagnostic counts.** Using its own 1.1 ambiguity criterion, field 2's 26 events in capture 3's
   range are 10 with no content move, 9 moving up one and 7 unclear, not 12 with no move. Field 1's
   rises move up one in 22 of 25 and its falls move down one in 20 of 23, not 22 of 27 and 20 of 24.
2. **One more valid unit.** The new pass read 85,970 valid units: unit 90806 is an exact 0xe801
   unit that entry 5 did not reach, so it has no comb verdict and is unjudged. The comparison
   population stays 85,969.
3. **The held-out set.** Reversed frame 13500 uses field 1 of unit 13501, inside capture 3. Without it,
   the held-out set is 75,747 frames: entry 5 60,937, new 43,038 (80.4% and 56.8%, unchanged).
Codex's evidence: its scratch `/private/tmp/codex-e8-review-P71eRj/REVIEW.md`.

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

## E-claude-2026-09-19-12 — capture 2's one-line offset: a per-frame rule, or one comb check per section?

**Question (owner, 2026-09-19, 11:05):** "how is it fixing cap2 (and that part of the tape's) misaligned
by 1 line? presumably with a single comb check? assuming thats the case, then the registration engine
should do a one time comb check "correction" that operates as a fixed offset within a section. as
always, when any signal loss like event occurs, the whole engine should re[set]."

**How it is fixed today (from entry 5's method, not a new measurement).** Not by a comb check. Entry 5's
census rule 3 fires per unit. If the tape caption's clock run-in sits directly above field 1's first
line, and the row directly above field 2's first line is not blank, field 1's top is taken one line
lower. Where it fires, the census placement is one line from the raw first lines, and the comb agrees.

**Premise (his).** On the EP recording, the misalignment between the raw first lines and the comb-free
placement is constant within a section. So a comb check at the section's start, applied as a fixed
offset, does what rule 3 does per frame.

**Method.**
- Raw first lines: entry 5's rules 1-2 without rule 3 (f1_auto). Comb: entry 5's, at 1.5.
- Sections: the whole tape's segments, split at every signal-loss-like event the data records: the
  three non-programme events and any break in exact units.
- Per section, the fixed offset o is the comb's d minus the raw st at the section's first decided
  frame. The placement is then raw st + o on every frame.
- Compared on capture 2's units and on the EP recording (segments B and C) against the comb, and
  against today's placement with rule 3:
  1. o alone;
  2. o inside entry 11's rule set (reading B, as last recorded), with rule 3 dropped and a comb check
     forced at each section start.
- Also reported: how constant the comb's d minus raw st is inside each section.

**Falsifier.** The section-fixed offset agrees with the comb on fewer judged frames than today's rule 3
placement, on capture 2 or on the EP recording, in either comparison.

**Material.** Capture 2's units (67,446-68,094) and whole-tape segments B and C. Segment A is reported
too, since rule 3 also fires there.

### Report on entry 12 (2026-09-19) — a single check per section: refuted; the held correction does it

- **Sections.** The valid material has no break in exact units inside a segment, so each segment is one
  section. The only signal-loss-like events are the three non-programme events.
- **The misalignment is not constant within a section.** Comb d minus raw st:
  - segment C: -1 on 25,083 frames, 0 on 4,413, +1 on 1,915, -2 on 858;
  - segment B: -1 on 3,777, 0 on 978, +1 on 82, -2 on 20;
  - segment A: 0 on 31,337, +1 on 4,428, -1 on 2,250, -2 on 430.
- **Comparison 1, the fixed offset alone: premise refuted.** The first decided check sets +2 in segment B
  and -2 in segment C. Agreement:
  - segment B 10 / 4,869 (0.2%) and segment C 858 / 33,450 (2.6%), against rule 3's 78.2% and 80.3%;
  - capture 2 0 / 551, against 543;
  - raw first lines with no offset: 20.1%, 13.2% and 0.9%.
  Even the section's most common offset (-1) would give about 77.6% and 75.0%, below rule 3.
- **Comparison 2, inside entry 11's rule set (reading B).** Rule 3 is dropped and a comb check is forced at
  each section start. Agreement:
  - segment B 4,868 / 4,869 (100.0%), against 4,806 (98.7%) with today's tops;
  - segment C 33,369 / 33,450 (99.8%), against 33,238 (99.4%);
  - capture 2 551 / 551, against 549;
  - segment A unchanged, 98.8%.
  It gets there by re-running the comb far more often. The raw first lines move by a line so often that
  the either/or classes fire on about 85% of the EP recording's frames: 4,568 of 5,364 in segment B,
  31,677 of 37,123 in segment C, 649 of 649 on capture 2. With today's tops that is 744 and 8,828.
- **Verdict.** His one-time section offset does not reproduce rule 3 on this tape. What does the job is
  reading B's held correction: set by a comb check, held until a trigger, reset at a gap. That is his
  idea with a re-check whenever the geometry changes. Keeping rule 3 costs fewer comb runs; dropping it
  gains 0.4-1.3 points on the EP recording for comb runs on most of its frames.
- Scratch: `geometry_exp1/exp12_analysis.py` / `.out`.
