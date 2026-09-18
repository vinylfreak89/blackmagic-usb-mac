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
