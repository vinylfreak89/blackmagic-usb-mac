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
