# Experiment ledger — Claude, part 2

Continues `docs/experiments_claude.md`, which reached the 150 KB Markdown cap that
`scripts/git-hooks/artifact_guard.py` enforces. Nothing in part 1 was edited or removed; entries
continue here in the same series and under the same rule (CLAUDE.md §14): the commitment is written
and committed before the deciding test, amendments are appended, and each report answers its entry.
Results, panels and data stay in scratch.

**The cap is the owner's to rule on.** Part 1 grew because its entries carried result tables the rule
puts in scratch. Splitting the file keeps every rule intact without an `.artifact-allowlist`
exception or a `--no-verify`, both of which are his decision, not mine. If he would rather the ledger
moved out of the repo (§14 allows that in one commit), this split is easy to undo.

## E-claude-2026-09-21-22 — coherence with the line below, as a second stage for marginal cases

**Question (owner, 2026-09-21, two minutes after entry 21).** "does it help to not just compare to the
blanking reference but also to the line below and if they are a certain amount coherent, call that a
picture line? Does that rescue the bad class?" And, after the comb result: "I'm saying it should do both.
The brightness test as a first pass but anything that is on the margins gets this second level check"

**Same investigation as entry 21**, which asked whether the errors could be caught afterwards. They
cannot — the comb sees about half and names the right placement in a seventh of those — so the only
route left is getting the first pass right, which is what this tests.

**Is the coherence quantity new?** No, and saying so matters because conflating quantities is how the
last two rules went wrong. The engine already computes exactly this: `continues()` takes the maximum
correlation between a row and the row below it over lags of ±24 samples and asks for 0.5. Today it is
applied only to high-contrast lines, as a guard inside the picture test, and the plain-23 rule uses the
same correlation at lag 0 for one specific pair. His proposal points the existing measurement at a
different set of rows: those whose brightness leaves them **on the margin** of his derived level.

**Premise.** Real picture resembles the line beneath it; blanking with speckle does not. So among lines
whose brightness alone cannot decide, coherence with the line below separates the two, and applying it
only to those lines leaves the confident cases untouched.

**Method.** Per unit and field, in one pass: the horizontal-blanking level of entry 20, then for each row
of the search window its body 95th percentile. A row is decided by brightness when it sits clearly above
or clearly below that level; a row **within a band around it** falls through to the coherence test, which
is `continues()` unchanged — maximum correlation with the row below over lags of ±24, threshold 0.5.
Because the owner has not specified the band and it must not be invented, three widths are measured —
±25%, ±50% and ±100% of the level — and the result is reported for each.

**Falsifier.**
- It rescues neither error class: for both the 78 skips and the ~174 early cases, fewer than half are
  corrected at every band. Reported per class, never averaged.
- Or the whole-tape change rate moves materially beyond entry 20's 6.84% — more than about a point —
  which would mean the second stage is deciding confident cases too, the failure that made both dark-end
  rules change 21% of the tape.
- Or the rescues are not supported by raw-row occupancy.
- If no band satisfies these, that is the result: no band works.

**Material.** All 86,293 exact units; the error classes as defined in `hblank_check.csv`; entry 20's tops
as the baseline.

### Report on entry 22 (2026-09-21) — refuted as a rescue; the same test corrects a larger population

**Verdict: the premise is refuted for the question it was asked.** Coherence with the line below does
not rescue either error class at any band that survives the change-rate arm. It does something else,
measured here and not claimed beyond it: it corrects about a thousand tops the brightness rule and the
census both got wrong, which is a different population and belongs to a different entry.

**The rescue, per class and per band, never averaged.**

| band | skips (78) | early (170) |
|---|---|---|
| ±25% | 18, 23.1% | 24, 14.1% |
| ±50% | 24, 30.8% | 42, 24.7% |
| ±100% | 26, 33.3% | 87, 51.2% |

Only one cell clears half, and it is the band the next arm excludes.

**The change-rate arm fires on ±100%.** Against the current census, in entry 20's own convention:
entry 20 5,900 units 6.84%, ±25% 6,239 7.23%, ±50% 6,304 7.31%, **±100% 7,085 8.21%** — 1.37 points
beyond, past the "about a point" the entry allowed. The two narrow bands sit within half a point.
The instrument reproduces entry 20's 5,900 exactly, which is what makes the comparison meaningful.

**Why the class is not rescued — two mechanisms, both measured.**
- The blank lines the brightness rule accepts sit **far above** the derived level, not near it, so a band
  around that level never reaches them: at ±50%, **122 of the 170** early cases are left exactly where
  entry 20 put them, never having entered the second stage at all.
- The coherence test **cannot see flat picture**. A dim, nearly flat picture line has too little variance
  to correlate with anything, so the second stage rejects it. That is the skip class: 54 of 78 unrescued
  at ±50%, on lines whose occupancy is 1.000 — real picture, invisible to this test.

**What it does instead, and this is the substantial result.** At ±50% the second stage moves 1,484 edges
off entry 20's answer: **1,152 land on picture, 9 land off it, 323 neither.** Of those 1,152, the census
and entry 20 **agreed with each other on 1,062** — tops both rules left on a blank line, which neither
previous measurement counted, because the error classes were defined from the places those two rules
*differed*. The blank-line defect is therefore substantially larger than entry 20 measured.

**Control arm, every changed edge judged by occupancy** (independent of the rule): entry 20 6,621 edges,
90.6% supported, 4.7% contradicted; ±25% 89.8% / 4.1%; **±50% 7,712 edges, 92.1% supported, 4.4%
contradicted**; ±100% 85.1% / 11.4%. Entry 20's report quoted 94.4% for the same thing — that was
5,995 over the 6,354 later-moves alone; over all its edges it is 5,996 of 6,621, one edge from this
pass's count.

**The regressions, named rather than netted.** Nine edges at ±50% go the wrong way: all field 2, all
accepting line 286 where entry 20 had picture at 288. Blanking can correlate with blanking, so the
second stage admits a blank line on the strength of its resemblance to the blank line beneath it. Nine
against 1,152 is the ratio, and it is not zero.

**Raw rows.** `panel_coherence.png` shows four of them at the top of the picture: 69511 field 2, where
both existing rules stop on a blank line; 70274 field 2, one of the nine regressions; 4812 field 1, a
flat dim picture line the coherence test cannot see; 82404 field 1, a blank line it correctly rejects.

**What is not understood.** Why the band that helps most on the wider population (±50%) helps least on
the classes is explained by the two mechanisms above, but the size of the 1,062 was not predicted by
anything in entries 20 or 21 and has not been checked against material outside this tape.

**Files.** `coherence.py`, `coherence_report.py`, `coherence.csv`, `coherence_cases.csv`,
`panel_coherence.png` in scratch.

#### Amendment 1 to the entry-22 report (2026-09-21) — the raw rows found a new error class I had not measured

Looking at the panel before sending it caught two things the report above stated without checking. Both
are corrected here rather than in the text above, which stands as written.

**A new error class, and it fires the owner's "no new errors" condition.** A move is only clean if it did
not step over picture on the way. Measuring the highest occupancy of the lines **strictly between** the
census top and each rule's top, the same way for both rules and split by direction:

| | later moves | vault over a picture line | moves of 3+ lines later | of those, vaulting picture |
|---|---|---|---|---|
| entry 20 | 6,354 | 185, 2.9% | 138 | 60, 43% |
| two-stage ±50% | 7,491 | **387, 5.2%** | 321 | **221, 69%** |

The second stage more than doubles the count of tops that land late past real picture, and its long moves
are wrong about seven times in ten. This is one mechanism, not two: the coherence test's false negatives
on real picture are its dominant cost, and a band exists precisely to route more lines into it. The
±50% trade is therefore **+1,152 edges corrected onto picture against 202 new late tops and 9 blank-line
regressions** — net positive by count, and not something to adopt on that count alone.

**Entry 20's own figure was measured differently.** Its check included the abandoned line in that
maximum; excluding both endpoints, which is what makes the two rules comparable, gives the 185 above.

**The skip class is partly an artifact of the run-in step.** On **62 of the 78** skips the census's
finished top is not the line its picture test accepted, and on **46** the line it accepted is blank
(occupancy < 0.05) — the run-in +1 step moved it onto picture. The class still correctly identifies a
picture line that entry 20 passed, so entries 20 and 21 stand; but the census's agreement with that line
is accidental on 46 of 78, and reports should not read it as the census having found the top.

**What bounds the rescue.** On **29 of the 78** skips the skipped line is vetoed by the **existing**
high-contrast guard (spread ≥ 40 and correlation with the line below < 0.5), which runs after the second
stage. No band can rescue those: the veto is downstream of the whole question this entry asked.

**A correction to my own caption.** I described counter 4812's line 25 as flat dim picture. It is not:
p95 179, spread 90, occupancy 1.000 — bright, high-contrast picture. It is rejected by the guard above,
not by darkness. The panel is what caught it.

**An instrument defect, disclosed.** `coherence.py` opened its output files at import, so importing it
from the analysis script truncated the results it was about to read. Both files were regenerated and
every figure in the report above reproduced identically; the module no longer writes anything at import.

## E-claude-2026-09-21-23 — the same derived reference at the bottom of the field

**Question (owner, 2026-09-21):** "Are we using the same newly derived blanking levels for the bottom
too?"

**The factual half, answered from the source before any run.** No. In the C engine, `measure_field`
computes `picture_threshold = blank_mean + 4.0` where `blank_mean` is the mean of the rows above the
picture (NTSC 11–20 in field 1, 274–283 in field 2), and the bottom scan compares each row's mean to
that same threshold. The census instrument does the same with its own constant. So the bottom is judged
against blanking measured at the **top** of the field and has never had a reference of its own, and
nothing from entry 20 reached it — that entry was measured, judged and reported entirely on
first-picture-line placement.

**Two ways the bottom test is weaker than the top, which matter here.** The top requires three
consecutive qualifying rows and applies the high-contrast guard; the bottom accepts a single row. The
top uses a body percentile; the bottom uses the row mean. A reference change at the bottom therefore
lands on a coarser test, and the two cannot be compared line for line.

**The cost is nil, and that is a fact about the instrument, not an argument for the change.** Entry 20's
level is already pooled over the leading blanking columns of **every line of the field**, bottom lines
included, so the number the bottom would use is the one already computed. Nothing new is measured to
make it available.

**Premise.** The derived level describes the source's blanking on every line, not where picture begins,
so it is the correct reference at the bottom as well; substituting it for the top-derived constant
should move last-picture-line placements onto picture in the same direction and proportion it achieved
at the top.

**The direction is opposite, and that is the risk.** The derived level (median 18 codes) is well above
the census's effective bar, so at the bottom it is the **stricter** test and will pull bottoms **up**,
discarding dim lines. The rows just above the clip band are exactly where the tape carries dark content
(§6 records those rows averaging about 31 codes on the programme tape against 1.4 with no input), so
this rule can cut real dark picture off the bottom. That is what the falsifier is aimed at.

**Method.** One pass, all 86,293 exact units, the same instrument as entries 20 and 22: the bottom under
the current rule and under the derived level, per unit and field. Every change judged by the independent
occupancy measure — the fraction of a line's samples more than 20 codes above blanking — on the line
abandoned, the line chosen, and the lines **strictly between** them, which is how amendment 1 caught the
top rule vaulting over picture. Censored bottoms (landing in the clip band, NTSC 260/522 and below) are
counted and reported separately and never netted into the totals.

**Falsifier.**
- The changes are not supported: among changed bottoms, fewer than half abandon a line that is blank for
  one that is picture, by occupancy. The top achieved this on the large majority and the bottom is being
  claimed to behave the same way.
- Or it cuts picture off: more than a small minority of changes abandon a line whose occupancy is above
  half, or step over such a line, measured the same way as amendment 1 and reported by direction.
- Or the correction is concentrated in the clip band, where the bottom is known-unmeasurable — a change
  there is not evidence the reference works.
- Or the change rate is far from the top's 6.84% with no account of why.
- A refuted premise here is a complete result: it would mean the reference is a top-of-picture
  instrument, not a property of the field, which is itself worth knowing.

**Material.** All 86,293 exact units of `captures/fulltape.cap6`.
