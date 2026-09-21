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

### Report on entry 23 (2026-09-21) — refuted: the reference is a top-of-picture instrument

**Verdict: the premise is refuted.** Every arm of the falsifier fires. The derived level does not behave
at the bottom the way it behaves at the top, and the reason is not a threshold that needs tuning — the
bottom of this raster is a different object from the top.

**Size and direction.** 762 changed edges, 636 units, **0.74% of units** against the top's 6.84%.
**All 762 move the bottom up**, as registered.

**The clip band arm fires decisively.** On **741 of the 762** changes the census's bottom was already
inside the clip band, where the bottom is known unmeasurable. The change is almost entirely a decision
about the two or three lines the engine already marks `bottom_censored`.

**The support arm fires, and my own test was the wrong instrument for it.** I pre-registered a
blank-versus-picture classification carried over from the top. At the bottom it does not adjudicate:

| abandoned → chosen | count | share |
|---|---|---|
| blank → partly lit | 282 | 37.0% |
| partly lit → fully lit | 253 | 33.2% |
| partly lit → partly lit | 151 | 19.8% |
| blank → fully lit | 32 | 4.2% |
| blank → blank | 23 | 3.0% |
| fully lit → fully lit | 18 | 2.4% |
| fully lit → partly lit | 3 | 0.4% |

Only 4.2% is the clean blank→picture correction the top achieved on the large majority, so the arm fires
as written. But **456 of 762 have dim lines at both ends**: the bottom of this picture *fades* rather
than ending, so a brightness level lands inside a gradient instead of on an edge. That is the finding,
and it is not a result my classification was built to express — recorded as a limitation of the entry,
not repaired after the fact.

**The cutting arm fires, and it exposes a defect in the reference itself.** Of the 362 changes that span
a line, **127 step over a line more than half lit**, and 21 abandon a line more than 90% lit. These are
not spread evenly: the derived level's median is **18 codes** across the tape, but on the cases that cut
picture its median is **101, with a 90th percentile of 164 and a maximum of 247**. On noisy material the
blanking columns are full of noise, so the pool's 99th percentile is inflated and the bottom scan skips
every real picture line to stop at the noisiest one. Counter 4704 is the panel case: level 229.4, the
scan passes a flat grey block at lines 250–254 and stops at 246 inside relock noise.

**This is a defect in entry 20's reference, not only in its use here.** The inflated level exists at the
top of those same units. Entry 20 measured 94.4% of its changes supported, so it is a minority effect
there, but it was never isolated and it has not been looked for. That is a new entry, not a claim.

**What it does get right.** 285 changes replace a blank or partly lit last line with a fully lit one, and
32 of those are the census over-extending one line into speckle at the bottom — the same over-extension
defect entry 20 found at the top, in the other direction.

**A question for the owner, not for me to settle.** The commonest single change is trimming a partly
filled final row (261→260, 188 times; 522→521, 109). Counter 4919 in the panel is one: line 261 is 31%
lit — content across the left of the sweep and black after it, the half line. His rule says the geometry
includes the head-switch area. So whether that row is the last picture line or is excluded is his call,
and the derived level currently excludes it.

**Raw rows.** `panel_bottom.png`: counter 4704 field 1 (the inflated level cutting into noise), 4919
field 1 (the half line, both answers inside the clip band), 7344 field 2 (the census taking a blank line
as the bottom and the derived level stopping one line higher, correctly). Each line is labelled with the
fraction of it that is lit.

**Files.** `bottom.py`, `bot_panel.py`, `bottom.csv`, `panel_bottom.png` in scratch.

## E-claude-2026-09-21-24 — excluding the samples that are conceivably picture, as he specified

**Question.** Entry 23 measured a defect in entry 20's reference: its level has a median of 18 codes
across the tape but 101 on the cases where it cuts picture, reaching 247. On noisy material the leading
columns carry noise, and a quantile over the pool absorbs it.

**His instruction, which entry 20 did not fully implement (owner, 2026-09-21, on the horizontal-blanking
experiment):** "that will not be constant because it's a noisy edge so that should not be a fixed but a
derived threshold" and "It shouldn't be a distribution. It should decide per unit what to include and
what to exclude. If it includes samples that are conceivably picture or will throw the whole thing off."

Entry 20 decides per unit which **columns** to include, then pools every sample from those columns over
the whole field and takes the 99th percentile — a distribution, and the exact thing he said not to do.
The inflation entry 23 found is that decision failing in the way he predicted, so this is not a new idea
of mine; it is the unimplemented half of his.

**Premise.** The inflation is caused by including samples that are conceivably picture, and the blanking
samples separate from them: on a unit whose leading columns carry noise, the sorted samples show a gap
between the blanking floor and the excursions above it. Excluding everything above that gap — a decision
per unit, taken from the source, with no threshold written in — removes the inflation **without changing
the level on units that never had it**.

**Method.** One pass, all 86,293 exact units. Entry 20's column selection unchanged. Then, in place of
the 99th percentile, the level is taken at the **widest empty stretch in the sorted samples**: the
largest value below the widest gap. Two variants are measured, because "exclude the samples" and
"exclude the lines they came from" are different readings of his sentence — (B) the sample-level
exclusion just described, and (C) the same gap used to drop whole lines whose leading columns contain an
excluded sample. Reported against entry 20's level and its tops for the same units.

**Falsifier.** His acceptance bar governs the first arm, in his words: it "must not change anything
across the tape (there might be small variance as it's not a hard coded full source derived number but
it should be extremely close)".
- **It disturbs what entry 20 got right.** On units whose current level is inside the tape's ordinary
  range — at or below the 99th percentile of 27 codes, a description of entry 20's own measurement and
  not a threshold in the rule — the first-picture-line placements must be essentially unchanged. More
  than a small variance there and the premise fails, whatever it does for the noisy units.
- **Or the inflation survives.** On the units entry 23 identified, the level must fall into the ordinary
  range. If it does not, the cause was not the inclusion of conceivably-picture samples and the premise
  is refuted rather than the method adjusted.
- **Or the repair does not reach the damage.** The bottom cases entry 23 measured — 127 changes stepping
  over a lit line, 21 abandoning one more than 90% lit — must fall. If the level comes down and those do
  not, the inflation was not what caused them.
- **Or the level becomes unmeasurable.** If a gap cannot be found on more than a small fraction of units,
  the rule has traded one failure for another and that is the result.

**Material.** All 86,293 exact units; entry 20's levels and tops and entry 23's `bottom.csv` as the
baselines to compare against, both already measured.

#### Amendment 1 to entry 24, written before the run — what the gap is taken over, and why

**Physical reason.** The gap must separate lines whose horizontal blanking is clean from lines whose
blanking carries noise. Taken over every sample it cannot do that: the samples are integers and a field
carries thousands of them, so nearly every adjacent pair differs by 0 or 1, "the widest gap" is a tie
broken arbitrarily, and on a clean unit it lands near the bottom and returns a level of about zero,
which accepts every row. The gap is therefore taken over the **per-line maxima** — the highest blanking
sample on each line, a few hundred values — which is the granularity at which the separation exists.

**What this should improve and what it must not break.** It should leave the level where it is on clean
units and pull it down where noise has inflated it; it must not start excluding large numbers of lines,
since a level measured from a handful of lines is not the field's blanking.

**Consequence for the registered variants.** Once the gap is taken over per-line maxima, "exclude the
samples" and "exclude the lines they came from" are the same operation and return the same number. The
two variants collapse into one rule and are reported as one; the entry above asked for both, and this
records that the distinction does not exist rather than reporting a duplicate as a second result.

**Tie-break, stated because it is a choice.** Where several gaps are equally wide the highest is taken:
the separation being sought lies above the blanking bulk, and a higher level is the stricter picture
test, so it is the conservative direction.
