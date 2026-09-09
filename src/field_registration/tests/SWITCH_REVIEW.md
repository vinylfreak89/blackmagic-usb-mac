# Commercial counter 6687: the current switch detector is wrong

This is the historical adjudication at `5a62423`, not an acceptance pass.
The subsequent replacement and its remaining failures are in
`SWITCH_TIMING.md`. At the time, the scalar probe used the private engine predicate and
the real CAP1/unit-parser path; it does not import the harness instrument.

## What the current C predicate actually does

`full_other_head_row` first requires whole-row, zero-lag mean absolute
difference >=35. It then searches every admissible lag separately for eight
90-sample apertures. It fits neither gain nor offset, takes absolute lags,
and accepts their median >=10 without requiring a common signed displacement
or an identifiable timing landmark. `measure_field` scans upward from the
recorded clip and accepts the first such row. This does not establish that
the region below that row belongs to the other head.

On commercial counter 6687, the engine reports NTSC switch lines 236/498
and extents 27/28. These are the last strong within-picture brightness edges,
not horizontal timing departures. The top remains 23/286 and the last
recorded row remains 262/525; neither makes the switch measurement valid.

Full-width luma measurements for field 1:

| NTSC line | Mean | Sigma | MAD against row above | C predicate |
|---|---:|---:|---:|---|
| 235 | 65.636 | 60.351 | 17.381 | false |
| 236 | 19.419 | 18.442 | 47.433 | true |
| 237 | 18.340 | 5.701 | 7.915 | false |
| 238 | 19.606 | 4.797 | 2.226 | false |
| 259 | 21.422 | 5.120 | 1.792 | false |
| 260 | 19.614 | 7.739 | 6.656 | false |
| 261 | 17.600 | 9.291 | 4.408 | false |
| 262 | 17.617 | 9.577 | 1.922 | false |

At line 236 the eight winning signed lags are
`0, +40, -46, +360, +252, +180, +51, -2`; the median absolute lag is 48.5.
The best/zero SAD ratios are
`1.000, .739, .390, .098, .205, .161, .148, .874`.
These are independent matches to dark stretches elsewhere in the row above,
not a coherent translation. They are not the harness's gain/offset-fitted
ratios and must not be called the same measurement. Field 2 has the analogous
false hit at line 498: mean 20.622, sigma 25.275, MAD 62.033.

The physical bottom rows fail the 35-code gate before their lags are even
examined. Thus the algorithm simultaneously accepts a large content step
and suppresses the low-contrast timing change. Limiting the inferred band to
three rows, or tuning the SAD threshold, would conceal this defect.

## What the raw edges say

The exported raw field pair was inspected. Its dark recorded margin is
picture, not a 27-line head-switch band. At line 236 the ordinary left
blanking-to-picture ramp and right blanking survive; the interior picture
level changes. The end geometry also survives in the following dark rows.

As a directly reproducible scalar reading, both fields' regenerated blanking
rows have min/max codes 1/2. Runs at or below that measured maximum remain at
the ends through field-1 line 259: line 236 has runs [0,4) and [706,720),
line 259 [0,3) and [705,720). On line 260 the left edge still resembles the
preceding line but long blanking runs appear inside, [106,139) and [163,197),
and the right end carries active-level samples. Lines 261/262 carry the
fully displaced blank interval, e.g. [39,153) and [156,198) on line 261.

Field 2 likewise retains end geometry through line 521. Line 522 retains
the ordinary left ramp but has an interior blank run at [570,576) and
active-level right-end samples. Line 523 has a full interior blank run
[37,190), continuing in later rows.

My reading is partial switch at **260/522**, first full other-head row
**261/523**, hence picture bottom **259/521** on this unit. This is not a
constant for the whole capture. The harness's saved counter-6687 row reports
T=S=261/523: it finds S but misses the partial row here. Its 2/3 counts are
therefore not a replacement truth for the C engine's wrong 27/28. The claim
that no timing is readable in the entire dark margin is too broad: the
terminal rows have a blanking-position departure even though their content
does not support whole-row brightness matching.

No contract edit is needed: its partial-row definition already decides which
row to report when that partial row is observable. Do not resolve this by
choosing either instrument's count. Confirm these same raw rows independently.

## Cost: what the 24.293 ms number measured

The old benchmark's first loop runs 10,000 direct `fieldreg_process` calls,
cycling through 193 synthetic units from the 194-unit retired-v9 fixture
(the final invalid-header unit is excluded). It bypasses signal-state gating
and excludes classifier, publisher and record I/O. Its 24.293 ms p95 is an
engine-only synthetic workload measurement, NOT a measured whole-worker
capture percentile and NOT a proven worst-case bound. The second loop is a
different workload because it includes the current signal gate.

The rule-1 golden's 4.035/7.548 ms and the later active worker's 2.738/3.093
ms were also different workloads; they do not establish a before/after
speed-up. Invocation counts are now printed by the worker benchmark.

This diagnostic processed 919 eligible commercial units; 452 invoked the
engine, including 440 of the 582 units at counter >=6593. Existing mute
classification accounts for the rest; nothing was forced through the gate
to manufacture measurements. Over the 452 calls: engine median .434 ms,
p95 .486, max .918; classifier plus engine median .778, p95 .843, max 1.324.
Counter 6687 alone: engine .474 ms, classifier plus engine .818 ms.
These exclude publication and I/O, and are not the full worker budget check.

The source of potentially large work is visible in the current search: up to
8 * 631 * 90 = 454,320 sample differences per candidate row, after the cheap
brightness gate. Finding a switch late, or not finding one, repeats this
search. The plan is to correct the phase-identifiability defect first with
tests for an internal level step and a low-contrast terminal timing departure;
then profile the corrected current-program path on all four captures and
report the whole worker, including gated and measured populations separately.
Until that measurement exists, the broad synthetic tail remains open; it is
not dismissed as impossible on a real raster.

## Reproduction

Build `tests/switch_probe.c` with `cea608.c`, `../unit_parser/unit_parser.c`
and `../signal_state/signal_state.c`, using `-O3 -std=c11 -lm`. Invoke it as
`switch_probe CAPTURE 6686 6688 EXISTING_SCRATCH_DIRECTORY`, redirecting
stdout to a scratch CSV. It emits per-unit scalar timings and decisions,
`rows.csv` with per-aperture SAD traces, and PGM field pairs for the selected
counters. Program bytes remain in scratch, never in the repository.
Per-unit timing is stopped before the diagnostic row searches and exports.
The probe aborts on packet-provenance errors, excludes ineligible rasters,
and allows the capture's documented device-counter discontinuities.
