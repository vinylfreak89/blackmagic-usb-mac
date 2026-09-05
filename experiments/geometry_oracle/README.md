# Geometry-first raw oracle

This directory is the independent validation side of the geometry-first registration work.  It
does not import or inspect the registration engine.  `oracle.py` reads exact NTSC UYVY transport
units and writes measurements only; it does not decide whether an engine placement passes.

## Coordinate convention

All reported edge and landmark coordinates are NTSC line numbers (`unit row + 4`).  Field 1's
pass-through region is lines 23–264 and field 2's is lines 286–526.  The standard crop origins are
23 and 286.  A bottom in the final five pass-through lines is reported as censored because the
head-switch/padding transition makes its exact position unknowable.

## Independent measurements

- **Top edge:** `active_top_line` is the first of three consecutive active rows in a field's
  pass-through region; it is retained so the raw activity decision is auditable.  `top_line`
  excludes a uniquely measured flat black gap immediately before the picture.
  Activity is measured relative to that field's own blanking rows using row mean, spatial spread,
  and horizontal gradient.  A unique flat dark transition immediately before two active rows is
  identified separately as tape line 22 and excluded from the picture.  If a decoded tape line 21
  overlaps the proposed start, geometry reports `vbi_ambiguous` rather than silently using the
  caption to move the edge.
- **Bottom edge:** the last of three consecutive active rows.  A result in the five-line
  head-switch corridor is a visible lower bound (`bottom_censored=1`), not an exact edge.
- **Height:** inclusive top-to-bottom height, valid only when both edges are exact.  A censored
  bottom still reports `visible_height`, but never a valid height.
- **Picture:** a sustained set of rows distinguishable from the field's own blanking by luma
  level, spatial spread, or horizontal texture.  This includes dark and boxed program material;
  it does not assume studio black is any fixed code value.
- **Tape line 21:** every whole-field row that independently decodes as two odd-parity CEA-608
  bytes after a 503.5 kHz run-in and start bits.  A sole decoded row away from the Shuttle insert
  reports an independent implied RP-202 top two lines below it.
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
- **Static comb:** at standard crops, field 2 is tested at relative shifts −3…+3 against the mean
  of its neighboring field-1 lines, on pixels static against the preceding unit.  Best energy,
  second energy, ratio, static fraction, and uniqueness are reported; no threshold converts this
  into a placement decision.
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
```

The first deliverable is the oracle and its owner-site measurement tables.  Engine verdict logic,
never-bounce scoring, hold scoring, and nonzero exit policy intentionally come later, after both
sides agree that these raw definitions match the reference raster.

Cut `.tpc` slices begin/end inside USB transfers and therefore carry exactly three packet-index
boundary errors.  The explicit slice option accepts only that exact diagnostic.  Full captures
remain fail-closed on every provenance error.
