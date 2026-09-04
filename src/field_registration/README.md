# Registration v9: line 21 plus a geometry lock

`field_registration` corrects independent whole-line vertical displacement of
the two NTSC fields in one exact 756,048-byte Shuttle unit. It never
deinterlaces, allocates on the unit path, retains input, duplicates a line, or
manufactures pixels. Positive `d` selects a later whole UYVY source line.

The 720x480 clean-aperture output starts at unit rows 19/282 (NTSC lines
23/286). The engine scans the complete captured fields, unit rows 8..262 and
268..524 (NTSC lines 12..266 and 272..528), for CEA-608. A parity-valid line
away from the Shuttle's insert at rows 17/280 is the primary displacement
gauge and applies immediately, except for the line-22 ambiguity below.
Non-null re-encoded data on the insert corroborates `d=0`; it does not override
a live geometry lock that measures a nonzero displacement. Field 2 additionally uses the frozen
smeared-XDS discriminator documented in `CLAUDE.md` when parity cannot decode
that field.

A parity-valid row exactly one line below an insert carrying non-null data is
classified as station line-22/285 data and leaves the field aligned. Without
that discriminator, a one-line disagreement between an off-insert parity row
and a live geometry lock is `GaugeConflict` and holds. The sidecar records both
the parity row/bytes and `geometry_d`; a non-null insert opposed by a live
nonzero geometry lock is `InsertGeometryConflict`. Which gauge should win a
real conflict is pending owner ruling, so v9 never silently chooses either.

When the insert contains null data and there is no primary gauge, v9 measures
the picture top and bottom by row-mean luma (`mean(Y[x=40..679]) > 12`). A
geometry-only lock requires two identical source-top/height observations at
the current applied offset. A parity/fallback-gauged lock instead treats
`measured_top - d` as authoritative and may lock while its height is only a
censored lower bound. The first credible uncensored observation fixes `H`;
until then the sidecar reports `lock_height_known=0`.

```
uncensored_bottom = T + H - 1 + d
expected_bottom   = min(uncensored_bottom, C)  # when C is known
residual          = measured_bottom - expected_bottom
```

Only residual zero permits an ungauged `GeometryLockDecides`, except that an
ADC-boundary bottom is provisionally accepted while the clip ceiling remains
unknown. A contradiction holds the last applied offset, names `LockBroken`,
and starts a two-observation reacquisition at the unchanged presentation.
Dark/unmeasurable content holds without destroying a valid lock. A clip
ceiling is learned only when two parity/fallback-gauged observations at
different offsets saturate at the same bottom line; its candidate/count are separate
from the `UNLOCKED / ACQUIRE_ONE / LOCKED` state, so fitting never makes a
locked field appear unlocked.

`fieldreg_begin_segment()` forgets both locks and starts the new segment at
`d=0`. `fieldreg_discontinuity()` forgets the locks but preserves each last
applied offset. Neither buffers, backdates, drops, or repeats a unit. Until
both field locks are valid, `comb_safe` is false; callers still emit the
uncorrected/held frame and leave any presentation policy downstream.

## Sidecar schema 5

The frameserver retains its transport/signal columns and writes the following
v9 provenance for each field. Values named `*_line` are NTSC line numbers
(engine internals use unit row = line - 4).

- reason and gauge;
- insert presence and decoded bytes;
- parity/fallback candidate counts;
- selected gauge line, decoded bytes, correlation amplitude, and the live
  lock's independent `geometry_d` reading;
- blank-row mean, raw picture top/bottom/height, measurability and censoring;
- lock state/id, frozen top/height, whether that height is uncensored,
  `ClipUnknown`/`ClipFitting`/`ClipFitted`, and the optional clip ceiling; and
- expected bottom, lost-line count, and invariant residual.

The row also records the applied pair, whether both locks make the vertical
registration claim (`comb_safe`), publication/drop accounting, and schema
version. The offline renderer emits the same per-field engine provenance.

## Deliberately absent

No comb search, spatial bands, temporal correlation/veto, multi-candidate
trajectory, dwell, chatter suppression, common-mode arbitration, learned
position mode, FIFO, or backtracking remains in the live path. The old tools
remain offline diagnostics only; `docs/registration_archaeology*.md` records
why those models were retired.

Build and run the deciding tests with:

```sh
make -C src/field_registration test
```

The synthetic v9 golden landed first and scored 8/29 on v7. The replacement
must score 29/29, the decoder unit test 3/3, and the fixture agreement harness
must match `experiments/cc608_decode.py` line verdicts and bytes exactly.
