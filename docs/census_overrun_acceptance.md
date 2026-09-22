# Census-overrun veto acceptance (2026-09-22)

Implementation acceptance passes; independent raw-edge quality scoring remains
pending. No source-quality verdict, push, or render is implied. Baseline: 9ed3923.
Registered before testing in experiments_codex.md, entry E-codex-2026-09-22-3,
amendment "census veto explicitly authorized, without final-crop guarantee".

## Rule and provenance

`GE_TOP_OVERRUN_VETO=1` enables the census veto; default is **0/off**.
`GE_TOP_NEAR_BLANK` remains **-1/off**, including every real-data test here.
The other four controls retain their defaults (5, 3, 0, 0).

H=240 is the publisher's field height: 23+d1..262+d1 and 286+d2..525+d2.
The review render adds three lines above each aperture, not below it. The census
condition deliberately uses the publisher's geometry, not that 243-line crop.
Each overrun uses its own unit's measured last line. Interpreted history feeds
the next unit. The veto is before the comb and **does not guarantee the final
crop or no picture loss**. A deciding synthetic test refuses census top 28 to
23, then a decided comb legitimately publishes top 24.

Measured `f1_first`/`f2_first` remain immutable. Existing
`interpreted_f1_first`/`interpreted_f2_first` record the census used downstream;
`top_ignored_f1`/`top_ignored_f2` record actual substitutions. Schema **18**
appends `ge_top_overrun_veto`, `top_overrun_veto_f1`, `top_overrun_veto_f2`.
The latter flags record predicate matches, including equal-top no-ops. Evidence
columns are frame-owned: under reversed pairing field 1 comes from frame_top_unit,
not the bottom-unit row key. The changed-unit tables join back to field ownership.

## Method and identity

Scratch: `/private/tmp/census-overrun.Z7dxX8/`.
`accept.py` streams each capture once into three C probes: an unmodified 9ed3923
build, the new disabled build, and the enabled build. Transport framing and the
existing live reset/pairing stream are shared; Python does not implement census,
classification, or placement. A separate audit engine supplies all-frame comb
evidence; timing is the non-audit engine's thread CPU time. No full-tape live
frameserver replay was performed in this acceptance; capture 1 additionally goes
through the real frameserver and checks its sidecar against these placements.

| Check | Whole tape | Capture 1 |
|---|---:|---:|
| Exact units | 86,293 | 919 |
| Woven frames | 86,289 | 919 |
| Disabled unit differences, all existing non-timing columns | 0 | 0 |
| Disabled frame differences, all existing columns | 0 | 0 |
| Enabled protected-evidence differing units | 0 | 0 |
| Comb measurement differing frames | 0 | 0 |

Protected evidence includes both measured first/last lines, bottom coordinates,
profile hashes, device blanking, horizontal level/column counts, rule_first,
auto_first, plain23, runin, and measured top distances. The comb comparison
includes shift, margin, decided, and top-unit identity.

Capture-1 real replay (off and on, --audit-comb, pool 32, pace 8000): each has
930 observation rows, 919 eligible units, zero drops. Off has zero existing-cell
differences against the 9ed3923 real replay (except schema). On has zero placement,
trigger, comb-run and interpretation differences against the probe.

All four labels hold in measured, interpreted, and published coordinates:

| Counter | Field 1 | Field 2 |
|---|---:|---:|
| 69566 | 26 | 288 |
| 69568 | 26 | 288 |
| 69570 | 25 | 288 |
| 69573 | 26 | 288 |

## Changed placements and cascade

| Count | Whole tape | Capture 1 |
|---|---:|---:|
| Predicate matches | 31,221 | 377 |
| Equal-top no-ops | 1,007 | 6 |
| Actual census refusals / changed census field edges | 30,214 | 371 |
| Changed census units | 24,921 | 225 |
| Changed published field placements | 21,231 | 714 |
| Changed published units | 11,539 | 518 |
| Changed woven-frame placements | 11,352 | 518 |
| Census edges per actual refusal | 1.000000 | 1.000000 |
| Published field placements per actual refusal | 0.702687 | 1.924528 |

The direct census ratio is one by the substitution accounting; it does not imply
absence of downstream effects. Capture 1's published-placement effect is not
one-for-one, and capture 1 is not called fixed. No threshold or tuning was used.

Changed-unit CSVs (union of changed census or published placement) contain every
before/after top, last, interpretation, own-unit d1/d2, class and refusal flag:

- `full.changed_units.csv`: 25,338 rows.
- `cap1.changed_units.csv`: 519 rows.

Both are in the scratch directory above. `*.placements.csv` contain all units;
`*.changed_frames.csv` retain all common-column changes, including class/schedule
changes even when published placement is unchanged. `*.summary.json` retain all
gain/loss counter identities and class transition matrices.

## Comb agreement

Agreement is `frame_d2 - frame_d1 == comb_d` on comb-decided frames with the stated
minimum margin. Before is the disabled baseline, after the enabled veto. Counters
are the frame's bottom-unit key in both pairings. Gains and losses are separate.

| Population | Margin | Before | After | Gains | Losses |
|---|---:|---:|---:|---:|---:|
| All | 1.5 | 76,331/77,129 (98.965370%) | 76,760/77,129 (99.521581%) | 429 | 0 |
| All | 3 | 47,305/47,707 (99.157356%) | 47,486/47,707 (99.536756%) | 181 | 0 |
| All | 5 | 28,659/28,903 (99.155797%) | 28,745/28,903 (99.453344%) | 86 | 0 |
| All | 8 | 18,840/18,884 (99.766999%) | 18,880/18,884 (99.978818%) | 40 | 0 |
| Counter <90300 | 1.5 | 75,942/76,685 (99.031101%) | 76,316/76,685 (99.518811%) | 374 | 0 |
| Counter <90300 | 3 | 46,923/47,271 (99.263819%) | 47,050/47,271 (99.532483%) | 127 | 0 |
| Counter <90300 | 5 | 28,280/28,474 (99.318677%) | 28,316/28,474 (99.445108%) | 36 | 0 |
| Counter <90300 | 8 | 18,468/18,472 (99.978346%) | 18,468/18,472 (99.978346%) | 0 | 0 |

Capture 1, both populations, before=after: 372/373 at 1.5, 332/332 at 3,
201/201 at 5, 183/183 at 8. All gains and losses zero.

## Classes and scheduling

Own-unit field counts; before -> after:

| Class | Whole field 1 | Whole field 2 | Capture 1 field 1 | Capture 1 field 2 |
|---|---:|---:|---:|---:|
| TOP_ONLY | 6,895 -> 20,240 | 1,483 -> 10,154 | 59 -> 174 | 75 -> 196 |
| VALID_MOVE | 4,412 -> 3,866 | 73 -> 63 | 0 -> 0 | 0 -> 0 |
| BOTTOM_ONLY | 430 -> 432 | 524 -> 506 | 0 -> 0 | 0 -> 0 |
| NOT_IN_TANDEM | 1,267 -> 1,811 | 80 -> 108 | 0 -> 0 | 0 -> 0 |
| NOTHING | 72,327 -> 58,982 | 83,313 -> 74,642 | 523 -> 408 | 479 -> 358 |
| UNKNOWN | 962 -> 962 | 820 -> 820 | 337 -> 337 | 365 -> 365 |

Full whole-tape class transition matrices, including unchanged classes:

| Before -> after | Field 1 | Field 2 |
|---|---:|---:|
| BOTTOM_ONLY -> BOTTOM_ONLY | 336 | 506 |
| BOTTOM_ONLY -> NOT_IN_TANDEM | 73 | 17 |
| BOTTOM_ONLY -> VALID_MOVE | 21 | 1 |
| NOT_IN_TANDEM -> BOTTOM_ONLY | 60 | 0 |
| NOT_IN_TANDEM -> NOT_IN_TANDEM | 1,152 | 79 |
| NOT_IN_TANDEM -> VALID_MOVE | 55 | 1 |
| NOTHING -> NOTHING | 57,060 | 74,155 |
| NOTHING -> TOP_ONLY | 15,267 | 9,158 |
| TOP_ONLY -> NOTHING | 1,922 | 487 |
| TOP_ONLY -> TOP_ONLY | 4,973 | 996 |
| UNKNOWN -> UNKNOWN | 962 | 820 |
| VALID_MOVE -> BOTTOM_ONLY | 36 | 0 |
| VALID_MOVE -> NOT_IN_TANDEM | 586 | 12 |
| VALID_MOVE -> VALID_MOVE | 3,790 | 61 |

Comb-run schedule:

| Transition | Whole tape | Capture 1 |
|---|---:|---:|
| 0 -> 0 | 49,477 | 301 |
| 0 -> 1 | 15,937 | 129 |
| 1 -> 0 | 325 | 21 |
| 1 -> 1 | 20,550 | 468 |
| Total runs before -> after | 20,875 -> 36,487 | 489 -> 597 |

These are consequences of interpreted history, not pass/fail invariants.

## Cost and tests

Thread CPU ms/unit, non-audit C engine including ge_measure:

| Population | Arm | Median | p95 |
|---|---|---:|---:|
| Whole | 9ed3923 baseline | 0.062292 | 0.307625 |
| Whole | New disabled | 0.062459 | 0.309833 |
| Whole | New enabled | 0.103500 | 0.552458 |
| Capture 1 | 9ed3923 baseline | 0.298125 | 0.758842 |
| Capture 1 | New disabled | 0.299875 | 0.762271 |
| Capture 1 | New enabled | 0.318250 | 0.758738 |

Every command below exits 0:

- `make -C src/field_registration test geometry-test`
- `make -C src/frameserver test`
- `make -C src/frameserver test-asan`
- `make -C src/frameserver test-tsan`
- `make -C src/frameserver test-geometry`
- `make -C src/frameserver test-geometry-asan`
- `make -C src/frameserver test-geometry-tsan`
- Standalone geometry_overrun with ASan/UBSan; with TSan.
- `accept.py full`, `accept.py cap1`, `cap1_replay.py`.

Deciding tests cover both conjuncts, clipping, tandem translation, missing
measurements, equal-top accounting, interpreted history, resets/gaps, both
pairings, audit invariance, and downstream comb authority. Three mutations
deliberately fail, with these verbatim diagnostics:

```
omit-overrun REJECTED -6 Assertion failed: (b.top_overrun_veto[k]==cases[i][4] && b.top_ignored[k]==cases[i][5]), function main, file geometry_overrun.c, line 38.
omit-no-gain REJECTED -6 Assertion failed: (b.top_overrun_veto[k]==cases[i][4] && b.top_ignored[k]==cases[i][5]), function main, file geometry_overrun.c, line 38.
measured-history REJECTED -6 Assertion failed: (f->first[0]==24 && f->interpreted_first[0]==23 && f->top_overrun_veto[0]), function main, file geometry_overrun.c, line 48.
```

No unexpected build/test/acceptance error. The pending independent gate must
separately report regression avoided and fixes lost; comb agreement cannot
measure common-mode picture loss.
