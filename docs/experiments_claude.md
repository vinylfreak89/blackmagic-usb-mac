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
