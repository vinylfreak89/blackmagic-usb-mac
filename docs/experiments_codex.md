# Experiment ledger — Codex

Commitments precede deciding tests, per CLAUDE.md §14. Append entries, amendments
and verdicts; keep code, labels, panels and detailed results in scratch.

## E-codex-2026-09-19-1 — surviving fragments in torn top rows

**Question (owner, relayed 2026-09-19):** "What is the census in the 4 caps
where the first line of real picture is" — every valid unit. This experiment
addresses the unresolved capture-4 field-2 census, not a replacement engine.

**Premise.** A torn first picture row retains a fragment of the scene that
continues into a lower picture row, although whole-row correlation is poor.
That fragment can distinguish it from source-carried data waveforms. This is
a testable local-continuation hypothesis, not a fact about all picture/data.

**Method, fixed before the test.** For each candidate NTSC line 285–303,
divide its 720 delivered samples into four non-overlapping 180-sample pieces.
Compare each piece by Pearson correlation with every 180-sample contiguous
window in the row four field lines below it, within the same raw field/unit.
The maximum correlation is the sole score. A score >=0.90 accepts the row as
picture; zero-variance comparisons supply no evidence. The first accepted row
is the candidate top; if none qualifies, abstain. No amplitude gate, temporal
carry, comb, caption decoder, or additional veto. The 180-sample window,
four-line comparison distance, 0.90 cutoff and bounded top search are authored
experiment settings, not owner rules or measured signal constants. They will
not be tuned after observing the result.

**Independent observation.** Before computing candidate scores, inspect raw
line strips including preceding and following lines for all 650 capture-4
units. Record a first-visible-picture label or an explicit uncertainty/bound;
a partial picture line counts. Inspect each label bin and candidate bin on raw
rows, including rare cases. Labels describe visible evidence, not an assumed
nominal source top. Claude's census and the candidate scores are not labels.

**Falsifier.** A raw-confirmed picture row rejected, a raw-confirmed data row
accepted, or a candidate top contradicted by preceding raw rows refutes this
method as a complete separator. Report both error directions and abstentions;
failure does not establish that no simple separator exists. Do not repair the
failure with another clause in this entry. A complete raw census is not claimed
if any units remain unlabelled or ambiguous.

**Material.** Supplied luma caches and counters under the session's
`scratchpad/geometry_exp1/cache/`, all 650 capture-4 units 171–820, field 2
in its original slot (no pairing or geometric repair). Previously identified
hard examples: 204, 259, 331, 335, 809, 810; the other 644 units are not used
to choose settings. Source-data controls, raw-labelled before scores: capture
2 counters 67446, 67608, 67654, 67770, 67932, 68094, NTSC 23/24/286/287;
capture 3 counters 13501, 13502, 13601, 13701, 13801, 13901, 14001, 14101,
14149, NTSC 23. These coordinates name inspection sites, not unconditional
data labels: picture at a named site must be labelled picture. Capture-2
stored counters are extended by 65536. Captures 1 (>=6667) and 2–3 remain
reference material; no new full census of those captures is claimed here.

**Provenance.** Preconditions checked: all four caches/counter arrays and
census CSVs, `census.py`, `explore/bins_cap4.png`, and Claude's entry/report
are present. Prior census is E-claude-2026-09-19-2 (entry fdb89c2, report
f71fedd), read from the Documents checkout. This experiment's code, labels,
checks and detailed report go in `/private/tmp/codex-torn-top.rSVrxF/`.

### Report (2026-09-19) — separator refuted; raw census has abstentions

The unchanged rule rejects definite torn picture (capture 4, 204/286) and
accepts definite data (capture 2, 67446/23 and /286, 67932/286). No numerical
amendments or additional clauses. A lower cutoff cannot separate these rows
on this score; this does not rule out a different simple observable.

Raw census, every unit inspected: 559 first at 286, 64 at 287, 27 unresolved
between them. The earlier frozen 586/64 visual labels were overconfident:
enlarged error review exposed faint rows missed in overview strips. All 650
were re-audited at larger scale; the 27 remain unknown, not relabelled from the
candidate. Against 623 definite labels: 184 exact tops, 439 misses; 27 unscored.
Data controls: 27/30 rejected, three false acceptances. Five instrument controls
and six independent real-row Pearson checks pass. This is not a fully blind
validation or a completed 650-unit census. Detailed report, individual labels,
bin checks and the retained original artifacts: the scratch path above,
`REPORT.md`. No engine change; unresolved faint-row identity needs review.

## E-codex-2026-09-19-2 — what the data-line entropy counts

**Question (owner, 2026-09-19).** "Why do the data lines come out as high
entropy. They are only 2 codes plus a sinusoidal ramp all within a noise band.
Why would that be high entropy?" Reasoning audit, not a detector proposal.

**Premise.** A two-level underlying signal does not imply two delivered luma
codes: plateau variation and sampled transitions populate additional codes.
The histogram entropy measures this marginal distribution, not temporal
waveform complexity. Ordered transitions can contribute substantial histogram
entropy without being unpredictable. This does not imply every data row is
less temporally unpredictable than every picture row.

**Method, committed before the deciding run.** Recompute Shannon entropy on
the exact 640 samples `[40:680]`, check agreement with `exp4_rows.csv`, and
inspect numerical traces/histograms without programme content. For explicit
histogram accounting, find the modal code on each side of the midpoint of
the 5th and 95th percentiles; partition codes into bands around those two
modes and the remainder. Use authored half-widths 1, 3 and 5 codes, reporting
all three, not selecting one for separation. Decompose entropy by the chain
rule into low/high occupancy, within-band variation, remainder occupancy and
within-remainder variation. These are exact code-bin contributions, NOT an
identified physical noise/ramp separation. Inspect a fixed row (capture 2,
67446/286) and the data row closest to the population median; where a temporal
trace supports plateau/ramp annotations, record those intervals explicitly
before their entropy accounting, and include conditional-label ambiguity.
Do not force an ambiguous physical decomposition.

As reasoning controls, shuffle each examined row (seed 20260919): histogram
entropy must be unchanged. Compute first-order empirical conditional entropy
of adjacent samples at code bin widths 1, 4 and 8, alongside shuffled values;
these authored diagnostic resolutions are not thresholds or a classifier.
Report finite-sample/sparse-context limitations and counterexamples, not a
claimed entropy-rate estimate or noise model. No fitting a waveform decoder.

**Falsifier.** Histogram disagreement falsifies reproduction; shuffle changing
histogram entropy falsifies the instrument. A substantial residual in entropy
accounting falsifies the decomposition. Traces lacking distinguishable
plateaus/ramps defeat physical attribution. A picture row with lower temporal
conditional entropy than data defeats a universal low-data/high-picture
reading of that statistic. No detector amendment follows such a result.

**Material and labels.** All supplied caches and the original `exp4.py`, CSV
and E-claude-2026-09-19-4 report are present. Audit capture-2 top rows marked
non-picture in that CSV, NTSC 23/24/286/287, counters 67446–68094; labels are
Claude's census labels, not independent truth for the whole population.
Fixed raw checks: capture 2 counters 67446, 67654 and 68094 at those four
lines; capture 3 counters 13501 and 14101 at 23/24; capture 1 counters 6700,
6731 and 6760 at 23/24; capture 4 counters 204 and 335 at 286/287. Inspect
these and retain uncertainty instead of calling every named site data.
Results and scripts stay in a new `/private/tmp/codex-entropy-*` directory;
only this entry and its verdict are committed locally.
