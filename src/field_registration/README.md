# Registration v10: geometry first

`field_registration` corrects independent whole-line vertical displacement of
the two NTSC fields in one exact 756,048-byte Shuttle unit. It never
deinterlaces, allocates on the unit path, retains input, duplicates a line, or
manufactures pixels. Positive `d` selects a later whole UYVY source line.

The normative design is [`../../docs/geometry_first_engine.md`](../../docs/geometry_first_engine.md).
The implementation is landing one rule at a time with a failing golden before
each rule.

## Implemented: rules 1, 3 and 4

Measurable current-unit geometry is the sole placement authority. The field's
measured top and provisional lower edge are recorded; its top against the standard
23/286 origin supplies the provisional crop until the conserved line account
lands in rules 3–4. A caption cannot place, veto, hold, re-anchor, or otherwise
mutate a crop. A picture row is a non-waveform recorded row: its luma exceeds
this unit's own blanking-row ceiling, or its chroma noise crosses the measured
1.48×/2.02× blanking-to-recorded gap at 2×. The first such row is the top;
there is no multi-row brightness gate. A caption's decoded row and bytes are retained as an explicit
`agrees`/`disagrees`/`ambiguous` confirmation. Geometry is measured without
using a decoded caption row to choose where its top scan begins.

The round-10 body veto, caption placement, zero re-anchoring, comb calibration,
and comb crop-correction paths have been removed from the compiled engine.
Body and comb confirmation will return only as the contract defines them; they
currently report no observation. Acquisition/reset/damage behavior still has
the inherited placeholder state and is implemented by rules 5–6, after the
fixed switch-line count.

Rule 3 measures the lower geometry horizontally, never from luma level. The
last recorded row is found from the same per-unit decoder-noise boundary as
the top. Working upward from it, the engine finds `S`, the first full
other-head row, by the capture's measured separation: ordinary adjacent
picture rows have full-row MAD 8–17 and median segment lag 0–1; `S` has MAD
35–80 and median lag at least 10. Eight equal apertures are a fixed memory
capacity over the standard 720 luma samples, not a fitted corridor. When no RF
peak exposes the partial row above `S`, `switch_line` is `S`; the record keeps
both columns so the contract's one-row partial ambiguity stays visible.

`raw_bottom` is the row above `switch_line`. `raw_span` is the number of rows
from the standard 23/286 origin through that bottom; `band_extent` is the
visible switch band through the measured last recorded row. For a visible
top, `observed_switch_line_count = band_extent + d` and `picture_rows = 240 -
observed_switch_line_count`. The two Rule 3 golden units hold that observed
count at three while a one-line downward move increases the span and decreases
the visible band.

Rule 4 freezes the switch-line count only at a source-lock confirmation on a
unit whose switch line and band are measurable. The implemented confirmation
path is a unique pass-through caption agreeing with the current geometry;
acquisition comb confirmation lands with rules 5–6. Once frozen, every later
measurable count is compared with the lock. A mismatch is recorded as
`SwitchCountConflict`; it neither relearns the count nor overrides the
current-unit top placement. `picture_rows` is then the source constant 240
minus the locked switch-line count.

There is no bottom censor, luma-derived bottom, or typed fixture-A clip start.

The frameserver decision log is schema 13. Each per-field group records the
recorded bounds, top and picture bottom, `switch_line`, `S`, RF-peak line and
horizontal position, span, picture rows, visible band, observed switch-line
count, its agreement/conflict with the locked count, the locked count itself,
and switch signature. Line-valued fields remain NTSC line numbers.

Build and run the current suite with:

```sh
make -C src/field_registration test
```

The retired v9 fixture remains available only as a contradiction inventory:
`make -C src/field_registration retired-v9-test`. It is deliberately not part of the
v10 pass suite because it encodes the authority hierarchy prohibited by the
current contract.
