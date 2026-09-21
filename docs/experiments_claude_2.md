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
