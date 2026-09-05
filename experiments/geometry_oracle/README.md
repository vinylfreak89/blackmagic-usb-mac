# Geometry-first raw oracle

This directory is the independent validation side of the geometry-first registration work.  It
does not import or inspect the registration engine.  `oracle.py` reads exact NTSC UYVY transport
units and writes measurements only; it does not decide whether an engine placement passes.

## Coordinate convention

All reported edge and landmark coordinates are NTSC line numbers (`unit row + 4`).  Field 1's
pass-through region is lines 23–264 and field 2's is lines 286–526.  The standard crop origins are
23 and 286.  No fixed top or bottom corridor is presumed: both picture edges are measured in every
unit from that unit's raster.

## Independent measurements

- **Top edge:** `active_top_line` is the first of three consecutive active rows in a field's
  pass-through region; it is retained so the raw activity decision is auditable.  `top_line`
  excludes a uniquely measured flat black gap immediately before the picture.
  Activity is measured relative to that field's own blanking rows using row mean, spatial spread,
  and horizontal gradient.  A unique flat dark transition immediately before two active rows is
  identified separately as tape line 22 and excluded from the picture.  If a decoded tape line 21
  overlaps the proposed start, geometry reports `vbi_ambiguous` rather than silently using the
  caption to move the edge. A top-interval row carrying the 503.5 kHz CEA-608 waveform is excluded
  even when tape damage prevents its bytes from satisfying odd parity.
- **Bottom edge:** the last row satisfying the same field-relative picture-activity test. An active
  row remains picture when it is horizontally disturbed by head switching; no row-number corridor
  excludes it. Fixture A commonly ends at lines 260/522, while the commercial composite capture
  reaches lines 262/525. Those are source measurements, not constants. `bottom_h_shift_px` reports
  the best horizontal shift of the bottom row against the median of the preceding three picture
  rows after an eight-pixel low-pass; its MAD, runner-up MAD, and ratio expose whether that phase
  reading is discriminating without invalidating the bottom.
- **Height:** inclusive measured top-to-bottom height, valid whenever both edges are measurable.
- **Picture:** a sustained set of rows distinguishable from the field's own blanking by luma
  level, spatial spread, or horizontal texture.  This includes dark and boxed program material;
  it does not assume studio black is any fixed code value.
- **CEA-608 waveform and parity:** `cc_waveform_lines` measures a seven-cycle 503.5 kHz run-in at
  the 13.5 MHz sample clock with tolerant phase/local skew and amplitude relative to the field's
  own blank-to-picture range. Start-bit and data-cell-grid strengths are reported separately. A
  vertically smeared waveform is represented by its strongest row. `cc_parity_lines` separately
  reports rows whose two bytes decode with odd parity; parity is not required to classify a row as
  VBI. The legacy `line21_*` columns retain the parity-decoded tape landmark and implied RP-202 top.
- **Black line 22:** the unique flat row in the first twelve pass-through rows followed by two
  active rows and separated from them by more than the measured blanking noise.  Its absolute
  luma is not fixed.  The coincident Shuttle line 22 is outside the scan and supplies no tape
  evidence.
- **Same-field temporal witness:** integer vertical shift −3…+3 minimizing MAD over a safe
  160-line body after an eight-pixel horizontal box filter.  The CSV reports the best and
  second-best MAD, their ratio, uniqueness, and an adaptively measured static-pixel fraction;
  no confidence cutoff is fused into geometry.  Three independent top/middle/bottom band shifts
  and MADs expose a vertically mixed field without converting horizontal tearing into a vertical
  placement.
- **Static comb:** field 2 is tested at relative shifts −3…+3 against the mean of its neighboring
  field-1 lines, on pixels static against the preceding unit.  Without a crop table this uses the
  standard 23/286 starts for raw validation.  With `--published-crops`, both the current unit and
  preceding unit use their own published starts.  Best energy, second energy, ratio, static
  fraction, and uniqueness are reported; no threshold converts this into a placement decision.
- **Field repeat:** byte identity of a field with the same field in the immediately preceding
  exact unit.  It is independent of low-MAD or visual similarity.

The `event` column carries fixture-A validation truth only: relocks at ordinals 300 and 43,737;
garbage/snow/mute from 43,686 through 43,736; and ordinary program elsewhere.  Those annotations
do not modify any measurement.

## Usage

```sh
python3 experiments/geometry_oracle/oracle.py INPUT.tpc OUTPUT.csv \
  --base-ordinal 0 --select 295-305 --allow-slice-boundary-provenance
python3 experiments/geometry_oracle/test_oracle.py
python3 experiments/geometry_oracle/validate_sites.py
python3 experiments/geometry_oracle/summarize_sites.py \
  experiments/geometry_oracle/reports/sites \
  experiments/geometry_oracle/reports/owner_sites.md
python3 experiments/geometry_oracle/activity_probe.py
python3 experiments/geometry_oracle/run_fulltape.py \
  captures/fulltape.cap6 \
  experiments/geometry_oracle/reports/fulltape_geometry.csv \
  experiments/geometry_oracle/reports/fulltape_census.md
```

The first deliverable is the oracle and its owner-site measurement tables.  Engine verdict logic,
never-bounce scoring, hold scoring, and nonzero exit policy intentionally come later, after both
sides agree that these raw definitions match the reference raster.

Cut `.tpc` slices begin/end inside USB transfers and therefore carry exactly three packet-index
boundary errors.  The explicit slice option accepts only that exact diagnostic.  Full captures
remain fail-closed on every provenance error.

The optional published-crop file is a harness-owned adapter boundary, not an engine schema:

```csv
ordinal,published_f1_start,published_f2_start
300,23,286
301,23,286
```

Every exact unit processed must have exactly one crop row. Missing, duplicate, or out-of-raster
starts abort the oracle. This keeps the independent comb measurement fail-closed while allowing
either new engine to export decisions without coupling this code to engine internals.

For the full fixture capture, `--ordinal-from-counter` keeps the dense `local_exact` index while
deriving `ordinal` from the unwrapped transport counter. Device-short periods therefore appear as
ordinal holes instead of shifting the known relock/event annotations.

`activity_probe.py` exposes the level, within-row spread, and horizontal-gradient predicates
individually at the review sites. The combined `active` result is their logical OR; the probe
exists so a flat dim row cannot be described merely by that combined result.
