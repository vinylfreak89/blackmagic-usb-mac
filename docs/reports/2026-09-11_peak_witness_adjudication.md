# RF-peak witness review of the six T disagreements

Reviewed harness commit `7c9d6de48d3db07a317f7b0f6e27b6ad5f13cefb`, merged into
`v10-engine` before this review. This is a measurement/adjudication report, not
an engine change or a change to the contract.

## Disposition

The peak association is reproduced, but it does not yet close the six-key
disagreement. The two visible spikes support T=S-1 strongly. The missing
qualification is whether the detected excursions are the identified RF
landmark, not whether the contract permits that landmark to identify T.

An identified head-switch RF peak has the narrower role already recorded in
CLAUDE.md: locating the partial switch line and its horizontal position. There
is no basis here for replacing that role with a new rule saying the switch is
merely somewhere at or after the peak. Conversely, an arbitrary positive
luma outlier does not inherit that role, or establish such a directional bound.

The contract's section-2 measured RF signature included a spike relative to
the **row-to-row difference**, on an otherwise aligned row, with the next row
torn from that sample onward. `peak_vs_s.py` instead selects the largest
absolute **within-row departure from the median**, normalized by that row's
spatial MAD. This is the statistic from `rf_peak_census.py`, but it does not
perform the earlier timing/identity qualification. The contract's current
Head switch definition also explicitly says its possible landmarks are not
automatically sufficient identification.

The raw six-key panel was inspected before new row measurements. Its two
bright features are real, narrow excursions. This inspection and their large
scores are useful evidence, not an independent measurement of the timing
relationship on either side of the landmark. The old SP-pass qualification
has not been reproduced on these commercial-tape keys in this review.

The appropriate next comparison is the candidate row against its preceding
normal-timing reference and following other-head row, at the candidate's
measured horizontal position, with readable versus ambiguous timing explicit.
Corresponding field-ordered neighbouring observations can corroborate landmark
identity, but persistence or an unchanged crop cannot establish it by itself.
This does not authorize a new cutoff or an automatic peak-based T override.

## Reproduced join and the 31 agreed readings

Executed unchanged:

```sh
python3 experiments/peak_vs_s.py /Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/composite_program_30s.tpc --from 6667 --geometry /private/tmp/run-timing.DdLgYt/plain/geometry.csv
```

Result: 1,016 field readings scanned; at the default score cutoff 30, 200
positive winners join to measurable engine S. Of these, 199 are on S-1 and
one on S. On the subset with engine T also known:

| Peak minus T | Peak minus S | Readings |
|---:|---:|---:|
| -1 | -1 | 31 |
| 0 | -1 | 166 |
| 0 | 0 | 1 |

The full threshold sweep and 1,680-reading spatial control are supplied
harness results; only the default-30 join above was rerun here.

This `geometry.csv` is the probe's independent measurement of every exact
raster, including signal-gated units (`switch_probe.c` calls `measure_field`
outside its live-registration conditional). The join does not filter its
`registration_measured` column. These are engine-reader diagnostic results,
not automatically observations made or applied by the live engine on all
those units; any live-path consequence requires that separate qualification.

The 31 are a real **peak-versus-engine discrepancy set**, not 31 newly proved
engine errors. If their excursions qualify as the RF landmark identifying T,
then their engine T=S results are wrong too. Agreement between the two readers
is not independent ground truth with which to disprove the peak witness.
Equally, a positive winner at S-1 is not sufficient to overturn that agreement.
Those 31 were not individually visually adjudicated in this review.

The phase reader's T=S branch deserves particular caution: it assigns S when
`previous_partial` is false, subject to its full-row and overlap tests. Failure
of that sufficient partial-prefix predicate is not a general positive proof
that the preceding row had no partial switch. Consensus can share that gap.

Two transcription claims in the new CLAUDE.md entry need correction:
"never on S" is contradicted by its own table, and the 197 are the agreed-T
readings whose **peak is on S-1**: 166 have engine T=S-1 and 31 have engine T=S.
They are not 197 readings where the engine reports T=S-1.

## Six-key raw checks

Field-relative line labels below; horizontal sample indices are zero-based.
The source is the original CAP1 above, not a rendered or repaired copy.
`rf_peak_census.peak` supplies the candidate-row score and half-extreme width.
The positive maximum was additionally measured separately in each of the
eight searched rows, before any negative-winner rejection.

| Key | Candidate S-1 | Candidate positive maximum / MAD | Column | Half-extreme width for the two spikes | Largest positive / MAD anywhere in eight rows |
|---|---:|---:|---:|---:|---:|
| 6681/f1 | 259 | 6.0 | 179 | — | 6.0 |
| 6700/f1 | 260 | 8.0 | 561 | — | 8.0 |
| 6704/f2 | 260 | 77.333 | 131 | 3 | 77.333 |
| 6722/f1 | 259 | 3.333 | 117 | — | 5.5 |
| 6749/f1 | 260 | 5.5 | 113 | — | 5.5 |
| 6785/f1 | 260 | 67.667 | 201 | 4 | 67.667 |

The two spike rows have median/MAD 23/3 and 26/3 respectively. Their large
scores do not involve the zero-MAD fallback. The four other keys have no
positive excursion reaching 30 in this window under the separately measured
positive statistic either. That is narrower than "no positive peak at all"
and remains absence of a qualified witness, not evidence for T=S.

The run reader does have evidence on those four, independent of using a peak:
retention of a locally observed leading porch plus shortening of its terminal
blank-code run, with a following qualified relocated full interval. A local
reconstruction of its positional predicate gives:

| Key | Local minimum leading/trailing runs | Candidate leading/trailing runs |
|---|---:|---:|
| 6681/f1 | 2 / 11 | 3 / 4 |
| 6700/f1 | 1 / 8 | 1 / 1 |
| 6704/f2 | 1 / 8 | 3 / 0 |
| 6722/f1 | 1 / 12 | 4 / 1 |
| 6749/f1 | 1 / 13 | 3 / 1 |
| 6785/f1 | 1 / 6 | 2 / 0 |

This reconstruction uses the field's observed regenerated-blanking code
alphabet, exact contiguous end runs, and the preceding 16 reference rows
excluding S-1, with `normal_porch`'s existing conditions. It is a diagnostic
reconstruction, not a new live C trace or independent ground truth for T.
All six satisfy the existing partial positional predicate in this calculation.

Exact-code terminal runs can shorten without establishing an identified
timing boundary. For example, 6722/f1 candidate line 259 ends at samples
705..719 with `[2,1,1,2,1,2,1,1,1,1,2,2,3,3,1]`: the two code-3 samples at
717..718 leave a terminal run of one, despite the preceding mostly blank-level
tail. This explains why a run length alone cannot settle the edge's timing
identity. At 6700/f1 and 6749/f1, most of the last 20 samples instead carry
levels near 20 before the final blank-level sample; these cases should not be
conflated with 6722's interrupted tail.

Keep the four current disputed T values Unknown while retaining S and both
readers' observations. That does not mean the run reader supplied no evidence,
or that an unmeasurable current T erases qualified retained bounds. The two
spike-bearing keys remain strong T=S-1 candidates, not promoted observations
by this review. No displacement or lock-count update follows from these scores.

## Selection assumptions and control limits

- The score is in spatial row-MAD units, **not calibrated sigma**. No standard
  deviation or false-positive probability is estimated. The zero-MAD fallback
  is the inherited fixed value 0.5, not measured source noise.
- The script selects one absolute winner across all samples of all eight
  rows, **then** rejects it if negative. It is not a strongest-positive search.
  A direct control using repeated `[49,50,51]`, one sample set to 0 and another
  to 85 returns the negative winner of 50 MAD while hiding a positive excursion
  of 35 MAD. Thus a negative winner cannot establish positive-peak absence.
- A positive-only subset is permitted as an explicitly limited measurement,
  but it excludes the real negative RF landmarks the owner also described.
  Neither the source's RF population nor its sensitivity is thereby measured.
- Restriction to the last eight positions, selection of one maximum, known-S
  join eligibility, and post-inspection choice of 30 all condition the result.
  Nested threshold sweeps show robustness of this association, not independent
  RF identity tests or an unfitted detector. The supplied fallback-S result is
  separate and does not contaminate the explicit engine-S join.
- Concentration in three of sixteen spatial cells is useful evidence of
  localization. It does **not** prove the peaks cannot be picture content:
  picture features need not be uniformly spread across those rows. Source
  content and edge artifacts can also be spatially localized. The control has
  no independently established content-versus-RF labels.
- `rf_peak_census.py` reports excursion width; `peak_vs_s.py` discards it.
  Neither amplitude alone nor this unqualified location control tests whether
  each selected feature is the previously characterized timing landmark.

There is also a separate coordinate defect in `t_adjudication.py`: its six-key
list passes the legacy field-2 S=524 to a field-relative mapper. Direct check:
`row_for_line(2,524)` returns `None`, whereas `row_for_line(2,261)` returns 520.
That script cannot inspect its field-2 key as written. The viewed panel uses
legacy row arithmetic consistently, so this does not invalidate that panel or
the reproduced `peak_vs_s.py` join.

The initial relative capture-path check failed with
`ls: captures/composite_program_30s.tpc: No such file or directory`.
The checks above used the original capture at its absolute path. No detector,
reference CSV, crop, contract rule, or harness implementation was changed.
