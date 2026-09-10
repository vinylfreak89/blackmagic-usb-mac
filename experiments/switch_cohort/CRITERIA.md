# Frozen cohort: adjudication criteria

Stated **before** any panel is adjudicated, per the contract entry of 2026-09-10 ("What is
authorised while the margin is open"). Recorded with the cohort and never edited after adjudication
begins; if they must change, the cohort is rebuilt and the old one kept with its criteria.

## What is being asked

**Per edge, not per row.** Each panel shows a row's left edge and its right edge. They are labelled
independently: a contaminated right edge does not disqualify a usable left edge, and a usable left
edge does not vouch for the right.

For each edge the adjudicator answers two things:

1. **Is the timing at this edge positively identifiable?** yes / no
2. If yes, **where is the boundary?** — the sample index at which blanking gives way to picture
   (left edge) or picture gives way to blanking (right edge), to the nearest sample.

That is all. The adjudicator does **not** say whether the row is switched, does not say whether the
reading is normal, and does not compare the number against any expectation.

## What makes timing positively identifiable

All three must hold, and the adjudicator records which one failed when it does not:

- **L1 The samples at the edge reach the field's own written-blanking level**, not merely "dark".
  The panel prints that field's own written-blanking level beside the row for comparison.
- **L2 There is a distinguishable transition** between that level and picture — a rise or fall that
  is not itself ambiguous with ordinary dark content.
- **L3 The boundary can be placed** to within a sample or two. If the adjudicator cannot say where
  it is, the edge is not identifiable however clear the levels are.

## What is explicitly NOT a criterion

- **The run's length.** The adjudicator must not judge identifiability by whether the run is "about
  five samples" or any other value. That quantity is the thing this cohort exists to calibrate and
  using it here would train the envelope on itself.
- **Agreement with neighbouring rows.** It may corroborate — the panel shows the rows above and
  below for that purpose — but it cannot establish identifiable timing on its own.
- **Interior picture transitions.** Ordinary picture has structure; it is not evidence either way.
- **The presence or absence of an RF peak.** The peak is optional and carries no information when
  absent; this project measured it at about 3% sensitivity on a line-TBC-off capture.
- **Position within the field.** Position is used only to keep candidate switch rows out of the
  cohort as a guard against leakage. It is never a label.

## Exclusions

An edge that fails L1, L2 or L3 is **excluded** and the failing test is recorded. Exclusions are
never replaced to keep the cohort's size up. If no edges qualify, that is the result and it is
reported rather than the criteria being relaxed.

## Independence

Both agents adjudicate the same panels **without seeing each other's verdicts**. Each freezes its
own verdicts before any comparison. Edges where the two disagree are excluded from calibration with
the disagreement recorded. Validation material is kept out of any later calibration or tuning.

## ⚠️ A limitation this scheme does not solve

"Positively identifiable timing" is judged by eye from raw samples, and the judgement of whether a
transition is "ambiguous with ordinary dark content" (L2) is exactly the distinction the
identification method has not yet settled — a stationary dark side margin can present a clean
transition that identifies the dark region's endpoint rather than blanking's. So this cohort can be
contaminated by the same ambiguity it is meant to sit outside of. Two partial defences are in
place: L1 requires the field's own written-blanking level rather than darkness, and the two agents
adjudicate independently so a shared mistake has to be made twice. Neither is a proof. This is
recorded as a known weakness of the cohort rather than argued away, and it is why measurement (4)
of the contract entry - whether a side-margin transition is separable from a real extension's
endpoint - is on the list.
