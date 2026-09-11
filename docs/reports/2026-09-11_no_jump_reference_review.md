# No-jump reference and the six T disagreements

Reviewed `dc339f0bd3422f3c2c37f99270be2c147f5e362c` and its instrument ancestry, including
`b954914`, `4ca99f7`, and `3265f8f`, through harness merge `f668f0b`. Local merge:
`7ea60aae70c0401b759ac5a821fab5182b71c327`. The contract is unchanged and byte-identical to that merge.
This is a measurement/code review, not an engine change or an adjudication by majority vote.

## Answer: it bears on the six, but does not settle them

I reran the unmodified instrument on the original capture-1 CAP1 and joined its CSV one-to-one to
`unknown_causes.csv`. I also regenerated and inspected the existing six-key raw-row panel before interpreting
the join. The panel's contrast mapping clips bright detail and its red bars use its own different low-level
threshold; it is a visual aid, not an independent timing identification.

Five of the six keys pass this instrument's adjacency test. Four match the run reader, one matches the phase
reader, and one remains unqualified. Field-relative line labels below are converted from the legacy
frame-continuous CSV convention; the join itself preserves that convention on both sides.

| counter / field | candidate line | adjacency-qualified | low-run start / length | relation to the two engine observations |
|---|---:|---|---:|---|
| 6681 / 1 | 255 | no | 708 / 7 | neither: phase T260, run T259 |
| 6700 / 1 | 260 | yes | 0 / 1 | run T=S−1; phase T261 |
| 6704 / 2 | 260 | yes | 0 / 3 | run T=S−1; phase T261 |
| 6722 / 1 | 260 | yes | 35 / 157 | phase T=S; run T259 |
| 6749 / 1 | 260 | yes | 0 / 3 | run T=S−1; phase T261 |
| 6785 / 1 | 260 | yes | 0 / 2 | run T=S−1; phase T261 |

These matches are useful characterization, not new positive identification of T. In particular, the four
run-reader matches carry low runs of only 1–3 samples at the delivered start; the qualifier ignores the run
position, length and identity. For 6700/f1, the equal-line predecessor's longest low run starts at 515 rather
than 0. The 6722/f1 candidate matches the opposite reader. None of this repairs the engine's existing
failed-prefix-predicate versus positively absent partial distinction. The six combined T readings remain
unresolved by this evidence; their agreed S is not erased.

## The +1 class reproduces, but its proposed mechanism has the wrong direction

The strongest reported association reproduces exactly: all 42 adjacency-qualified candidates one line below
the engine T have low-run starts at samples 1–59. The agreeing class also reproduces: 204, split 86/32/86 over
start 0 / start 1–59 / start ≥60.

The additional deciding join is **candidate line minus engine S = 0 on all 42**. Thus these are candidate=S,
engine T=S−1. An explanation in which the ENGINE defaults late to T=S on a failed partial-prefix test predicts
the opposite sign if the reference supplies the earlier partial. The aggregate does not establish which reader
is right. It characterizes this reference locating the engine's full row, not 42 demonstrated late engine T
readings. Cohorts defined by candidate minus engine T also use the engine to define cohort membership; only
candidate construction and adjacency selection are engine-independent.

The negative class in the dispatch does not reproduce as stated from the committed CSV: there are 48 at −1/−2,
with 21 start-at-0, 2 starts 1–59, 24 starts ≥60, and one with no low run at all (start −1, length 0).
The three published rows sum to 292, while the qualified known-T cohort is 294. If the reported 46 uses an
additional selection, that selection and its keyed output must travel with the table. The no-run reading must
not be counted as an interior or censored interval. This discrepancy does not undo the reproduced 42/42 result.

## A column is the right coordinate only for an identified event

`run_start` is the start of the longest contiguous set satisfying `luma <= reference level + 3*sd` on the
candidate row. It is NOT the timing-departure transition used to select the row, and neither has been identified
as the instant the heads change. The +1 class's measured low-run lengths range from 73 to 160 samples, not
660–719. Inferring that the remainder of the row belongs to the other head requires the missing identification
of the switching instant; it does not follow by subtracting this low-run start from 720.

The conversion from a delivered-sample coordinate to time is conditional arithmetic. It dates the measured
low-run opening under the supplied origin/rate; it cannot turn that opening into a head-switch instant. The
horizontal phase of an interval in an already other-head row is a different event from the switch into that
head's timing. Here all 42 rows are exactly the engine's S, which makes that distinction immediately relevant.

A rule using the time of an IDENTIFIED transition between timing regimes, its observed continuation and
censoring is the appropriate shape. A rule assigning T/S from a cutoff such as run_start<60 is not supported.
Moving the decision from a line number to a column number does not cure a missing landmark identity. No new
cutoff or engine rule is proposed by this review.

## The claimed owner qualification is not what the cited rule says

Contract §1's head-catch paragraph explicitly permits motion by one or two lines when temporally sound, and
defines that condition on the boundary's travel ALONG the row. `qualified()` instead accepts equality of the
candidate LINE at counter c−1 OR c+1 in the same field. It discards run position/length, permits future evidence,
and has no landmark identity, continuation range or opposite-field predecessor check.

That is an offline adjacent-line persistence filter, not an implementation of the cited owner's temporal
qualification. It can be studied as a heuristic without attributing it to him. The control below accepts equal
lines while run_start changes 5→650, and rejects changed lines even when their diagnostics move from the
delivered end to the next start. These demonstrate its inputs, not independent proof of a valid or invalid
physical trajectory. Future-neighbor qualification also needs to be labeled retrospective before any reuse
in an online engine.

The observed narrowing around the mode is real. The unqualified control shows that far candidates are
reachable; it does not exclude persistent wrong candidates. The mode is learned from the same candidate
instrument and population, not an independently established lock/landmark. Therefore the 83 cannot be promoted
from assertions on engine-Unknowns to 83 qualified physical switch measurements.

## Deciding synthetic controls and unreported selection

`experiments/no_jump_review_controls.py` exercises the actual imported builder, not a reimplementation.
Its no-switch control keeps every source porch at samples 700–719, with all preceding picture samples ≥20.
Only an internal picture edge changes between ordinary and bottom rows. The larger picture fall wins the
steepest-fall search; the true blanking remains fixed. The resulting false candidates qualify in two identical
adjacent units. This is a stationary picture-content confound, not a simulated switch.

Output verbatim (candidate labels in this diagnostic are the legacy CSV labels):

```text
SYNTHETIC DIAGNOSTICS (observed behaviour, not expected detector success)
picture_edge f1: candidate=(259, 700, 20), adjacency_qualified=True
picture_edge f2: candidate=(522, 700, 20), adjacency_qualified=True
picture_edge: all 240 source porches fixed at 700..719; all earlier samples are picture >=20
later f1: candidate=(260, 680, 40), adjacency_qualified=True
later f2: candidate=(523, 680, 40), adjacency_qualified=True
earlier f1: candidate=None, adjacency_qualified=False
earlier f2: candidate=None, adjacency_qualified=False
same line, run-start 5->650: True
different line, delivered-end/start: False
flat picture, no falling edge: transition= 541 reference= {'level': 40.0, 'level_sd': 0.0, 'n': 35800, 'rows': 200, 'silent': 0, 'transition_median': 541.0, 'transition_p10': 541.0, 'transition_p90': 541.0, 'transition_sd': 0.0}
```

The earlier/later cases expose another scope limit: `candidate_line()` takes only positive departures ≥0.5 sd.
It is not symmetric, although its imported timing-departure instrument describes both directions. The flat
control exposes missing-is-not-a-value one layer earlier: `argmin(diff)` returns a location even without a
fall, and a flat picture becomes a non-Unknown blanking reference. More rows do not identify that reference.

The detector is not parameter-free. Its dependency starts its transition search at sample 540, takes the
steepest fall, selects a low tail within minimum-two-sample-block mean +1 code, and requires 20 contributing
rows. The caller assumes the first 200 positions supply the reference, applies +0.5 sd, admits a terminal run
ending at either of the last two window rows, and uses 3 sd for the low-run annotation. The optional reliability
ablation adds a 10% picture-support fraction. A source-derived scale does not derive the chosen multiplier or
search window. No new claim that all these choices are wrong is needed: they must be disclosed and tested,
and the controls already show two material consequences. The search is against the fixed delivery-window end,
not a qualified per-source clip.

The peer's five selftest groups pass as published. They exercise coordinate arithmetic/builder output on a
clean late-shift synthetic and adjacency/gap behavior. They do not test stationary picture confounds, early
departure, absence of a transition, temporal identity, reset boundaries or uncertainty. A passing implementation
test of adjacency does not prove that adjacency is the owner's qualification.

## The exact cause join, and the concealed disagreement class

The known-T population is 478; all 538 engine-Unknowns (532 with neither T/S plus six T disagreements) are
excluded from its score. The 83 assertions and 37 unqualified candidates on the Unknown population reproduce.
Joining the actual `cause` column gives:

| cause | total | adjacency-qualified | unqualified with candidate |
|---|---:|---:|---:|
| accepted_then_returned | 146 | 39 | 17 |
| no_accepted | 44 | 5 | 8 |
| no_basis | 75 | 22 | 6 |
| no_complete | 1 | 0 | 0 |
| no_disjoint | 264 | 12 | 5 |
| no_prefix_free | 2 | 0 | 0 |
| observation_disagreement | 6 | 5 | 1 |

The dispatch's figures reproduce only with `box` taking precedence over `cause`. All six disputed keys have
that flag, so the five qualified disagreements disappear inside its six qualified "box" readings. That is
a different partition, not a bad key join; call it box-first grouping and retain the actual cause alongside it.
Three Unknowns in no_complete/no_prefix_free were also omitted from that category table's displayed totals.

Likewise, start-at-0 is not proof of left censoring without interval identity. The current script still prints
"run start 0 = off-window" and contains the proxy claim the dispatch correctly retracts. A finer claim about
255 censored no_disjoint readings requires their individual annotations; the broad cause join alone does not
prove that none of the 12 asserting no_disjoint cases belong to that finer subset.

## Reproduction and scope

```sh
python3 experiments/no_jump_reference.py --selftest
python3 experiments/no_jump_reference.py --capture /Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/composite_program_30s.tpc --csv /private/tmp/no-jump-review.HoOVex/readings.csv
python3 experiments/no_jump_review_controls.py --csv /private/tmp/no-jump-review.HoOVex/readings.csv --causes /private/tmp/run-timing.DdLgYt/unknown_causes.csv
```

The existing `t_adjudication_panel.py` produced `/private/tmp/no-jump-review.HoOVex/six_rows.png`; no new render
feature or delivery artifact was developed. SHA-256 for the reproduced CSV:
`55bc94b61c94271f7efcfe76edd30a4b196052259e698083172228bcadce5fb1`.
Inputs: plain geometry CSV `23dffe5157ca322e457da2772caf7cf02133f78fb9e5d7055a6a0f6b2ade5841`;
cause CSV `a5b6ea4490295d61faf1984de2e0b0cd59b0923451da6bfc80c7d8d933ade147`.
These score the historical schema-20 switch observations named in the brief, not a new live-engine run.

`git diff --check` passes. Both repaired document selftests (`owner_queue_check.py` and
`superseded_check.py`, each with `--selftest`) now report SELFTEST OK; no harness fix was made here.
Their passing output does not validate the switch detector. The review adds this report, a bounded diagnostic
probe and CLAUDE.md findings only. No engine or contract changes are made. The AGENTS symlink is preserved.

Initial convenience lookups failed; the actual capture path and implementation file were then used:

```text
rg: src/field_registration/switch_timing.c: No such file or directory (os error 2)
rg: src/field_registration/run_timing.c: No such file or directory (os error 2)
ls: captures/composite_program_30s.tpc: No such file or directory
zsh:1: operation not permitted: ps
```
