# Run-route rejection census — measurement only

Production measured: `33e102c` (harness merge; engine identical to `856ec13`).
No detector, acquisition, bounds, box, top-reader, comb or classifier change.
Capture 1 remains unaccepted. Capture 2 was not read.

## Cohort and method

The cohort is the **264** `cause=no_disjoint` keys in the immutable
`/private/tmp/run-timing.DdLgYt/unknown_causes.csv`, not a new selection from
the harness. The diagnostic traces the actual C run observer in a generated
scratch header. Each field's cause is the first empty stage over its whole
top..recorded-last scan. This does not identify the true switch row.

The funnel is ordered candidate-first for diagnosis; production tests basis
first in the same conjunction. Independent candidate facts are also retained,
so overlapping blockers are not mistaken for exclusive causes. All 1,016
field outcomes, component observations and causes match the prior export;
geometry and both raw/live-gated T/S CSVs are byte-identical. No thresholds
or harness candidate rows enter the measurement.

## Result: the candidate test, not the two-ended basis, dominates

| First empty stage | Field 1 | Field 2 | Total |
|---|---:|---:|---:|
| No exposed interior alphabet run >=147 samples | 119 | 136 | **255** |
| No unique run (multiple candidates) | 0 | 0 | 0 |
| No qualifying local two-ended porch basis | 1 | 3 | **4** |
| Leading porch not completely lost | 1 | 1 | **2** |
| Trailing minimum extent not lost | 0 | 0 | 0 |
| Predecessor neither normal nor qualifying partial | 1 | 1 | **2** |
| Run code absent from local porch alphabet | 0 | 0 | 0 |
| Run CDF outside local distribution envelope | 0 | 1 | **1** |
| Accepted then cleared by a return | 0 | 0 | 0 |
| Total | 122 | 142 | **264** |

255/264 (96.59%) fail before reference-porch eligibility matters. Only nine
fields offer a candidate, five have a qualifying local basis, three lose the
required porches, one passes the predecessor check, and none passes the CDF
test. Across 63,360 scanned rows there are only 12 qualifying candidate rows;
all have one run. Six of those rows lack a basis. Independent blockers overlap:
four candidate rows retain a leading porch; four with a basis fail predecessor
qualification. None with a basis retains the trailing minimum.

The nine fields and remaining failures:

- No basis: 7010/f2, 7019/f1, 7044/f2, 7056/f2.
- Leading remnant: 7025/f1, 7045/f2 (one sample survives on each candidate).
- Predecessor: 7020/f1 (both preceding ends absent), 7151/f2 (preceding left
  extent 2 versus local minimum 10).
- Distribution: 7033/f2, line 524, CDF distance **0.173986486** versus
  measured envelope **0.105113636**. Code support agrees; the CDF does not.

**The proposed both-ends explanation is not the dominant constraint in this
implementation.** It applies to local *reference* porches; the candidate must
lose them. Relaxing that predicate alone cannot recover the 255 readings with
no candidate. This census does not claim that relaxing it recovers the other
four, since subsequent checks can still fail.

"No candidate" means no fully interior, uninterrupted >=147-sample run whose
every code occurs in generated blanking. It does NOT mean no physical blanking
or no switch. The census does not yet separate insufficient run length,
alphabet interruptions and edge-connected runs within those 255. The nominal
147-sample physical interval and this strict observed-code-run predicate are
not interchangeable measurements. No floor or alphabet was changed here.

## Six observation disagreements: T only, same S

| Counter / field | Phase T/S | Run T/S | Local minimum left/right | Preceding left/right |
|---|---|---|---|---|
| 6681 / 1 | 260/260 | 259/260 | 2/11 | 3/4 |
| 6700 / 1 | 261/261 | 260/261 | 1/8 | 1/1 |
| 6704 / 2 | 524/524 | 523/524 | 1/8 | 3/0 |
| 6722 / 1 | 260/260 | 259/260 | 1/12 | 4/1 |
| 6749 / 1 | 261/261 | 260/261 | 1/13 | 3/1 |
| 6785 / 1 | 261/261 | 260/261 | 1/6 | 2/0 |

T/S are NTSC lines; porch extents are samples. All six preceding rows retain
the required leading extent, lose the trailing minimum, and fail the normal
porch predicate (their total porch extent is below nine). Hence the run reader
calls them partial, T=S-1. The phase reader does not identify that partial and
falls back to T=S. All six run distributions pass; their distances/envelopes
and candidate positions/extents are in `run_stage_summary.json`.

These are not disagreements about S or the identity of the full row. Combined
T remains Unknown, common S remains recorded. Neither this execution trace nor
the harness's S validation adjudicates T; no winning T is asserted here.

## Artifacts and checks

Directory: `/private/tmp/run-stage.VlR6Rk/`.

- `no_disjoint_run_stages.csv`: the 264 per-field stage-count rows.
- `run_candidates.csv`: scalar candidate predicates, keyed by counter/field/line.
- `run_stage_summary.json`: exclusive counts, overlapping blockers, six conflicts.
- `engine_switch.csv`, `engine_switch_live_gated.csv`: unchanged join exports.

Reproduce into a new scratch directory:

    python3 src/field_registration/tests/switch_unknown_census.py \
      /Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/composite_program_30s.tpc \
      OUTPUT --previous /private/tmp/switch-causes.eig8nr/engine_switch.csv
    python3 src/field_registration/tests/run_stage_report.py \
      /private/tmp/run-timing.DdLgYt OUTPUT

The report asserts unchanged observations and monotone funnels, and checks
that diagnostic CDF pass counts equal actual acceptance counts. CAP1 provenance
checks pass. Fresh production `run_timing_test`: **34/34**, including the
stationary-black-rectangle, partial, relocated-run and departure/return controls.
There is no production timing change; traced-call timings include scalar I/O
and are not production benchmarks. No new acceptance or budget pass is claimed.
