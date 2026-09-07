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

- **Top edges:** `active_top_line` is the first of three consecutive active rows in a field's
  pass-through region and remains as an auditable raw channel. `recorded_top_line` is the first
  such sustained row whose chroma offset/noise identifies it as decoder-originated rather than
  regenerated. A detected 608 waveform cannot become either top. `picture_top_line` is normally
  the recorded top. When the leading recorded row(s) are black—luma within 12 codes of the
  field's blanking and row standard deviation below 8—and are directly followed by sustained
  non-black picture, the CSV reports both `black_band_start_line` and
  `black_band_picture_start_line`; picture top is the latter. The compatibility `top_line` field
  is an alias of `picture_top_line`.
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
- **Last recorded row:** independently locates the decoder-originated/regenerated boundary from
  chroma deviation relative to the same field's regenerated blanking. `last_recorded_line` does
  not replace the content bottom and does not assume either fixture has a particular clip line.
- **Flat raster:** `flat_raster` is a conservative spatial classification: the 90th-percentile
  horizontal and vertical differences of the eight-pixel-low-passed body must both remain below
  gates derived from that field's regenerated blanking. The raw energies and gates are retained.
  No independent snow classifier is asserted: the measured snow onset overlaps noisy program in
  spatial and temporal statistics, while the owner-specified snow/mute event remains forbidden.
- **Picture:** a sustained set of rows distinguishable from the field's own blanking by luma
  level, spatial spread, or horizontal texture.  This includes dark and boxed program material;
  it does not assume studio black is any fixed code value.
- **CEA-608 waveform and parity:** `cc_waveform_lines` measures a seven-cycle 503.5 kHz run-in at
  the 13.5 MHz sample clock with tolerant phase/local skew and amplitude relative to the field's
  own blank-to-picture range. Start-bit and data-cell-grid strengths are reported separately, and
  the cell span must contain the low-level occupancy required by a 608 start/data/parity train.
  Every independent candidate is retained so ambiguity remains visible; a vertically smeared
  waveform is represented by its strongest row. `cc_parity_lines` separately reports rows whose
  two bytes decode with odd parity; parity is not required to classify a row as VBI. The legacy
  `line21_*` columns retain the parity-decoded tape landmark and implied RP-202 top.
- **Black line 22:** only a black band anchored at the measured recorded-region onset can be tape
  line 22. The older search across the first twelve pass-through rows was rejected because it
  could call a dim row inside real picture a gap. The band and picture edges are both retained;
  the row alone does not claim whether a source used that line as black or active picture. The
  coincident Shuttle line 22 is outside the pass-through scan and supplies no tape evidence.
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
python3 experiments/geometry_oracle/score_crops.py \
  experiments/geometry_oracle/reports/fulltape_geometry.csv \
  crops.csv /private/tmp/geometry_crop_verdict
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

Every exact unit processed must have exactly one crop row. Missing and duplicate ordinals abort
the scorer. A crop up to 12 lines from the standard 23/286 start is scored normally even when its
240-line read reaches the legal hard-padding ruler; it is counted as `out_of_raster`. Larger
displacements and non-integer starts abort as malformed. This keeps the independent measurement
fail-closed without confusing a reportable engine decision with malformed input.

For the full fixture capture, `--ordinal-from-counter` defines `ordinal` as the unwrapped device
unit counter minus the counter of the first exact unit. Device-short units consume ordinals;
leading endpoint fragments do not. Thus the shorts at counters 4515, 4520, and 4701 are ordinal
holes 4, 9, and 190 rather than shifts in the known relock/event annotations. `local_exact` remains
the dense index of exact units actually processed.

`activity_probe.py` exposes the level, within-row spread, and horizontal-gradient predicates
individually at the review sites. The combined `active` result is their logical OR; the probe
exists so a flat dim row cannot be described merely by that combined result.

## Bounded raw-reviewed references

`build_reference.py` produces the contract-v3 per-exact-unit records for the SP recording, EP
recording, the SP recording with V-stabilize off, and the commercial tape through one measurement
path. Capture specifications contain transport identity only: count, label, and ordinal origin.
No capture supplies a top, switch row, stable interval, or per-unit answer. A spatially flat field
is measurable when its recorded region has a clear level boundary from raster blanking. A hidden
top or switch retains the prior locked decision in `picture_top_under_lock_line` and
`switch_line_from_geometry`; the raw per-unit measurement remains independently visible
and its position is marked unknown.

Each field records the measured picture top and its blanking/VBI/caption evidence, expected bottom
(`top + 239`), raster clipping, first switch row, last reliable row (`switch - 1`), last visible
switch/pedestal row, first blanking-level row, raster limit, and the visible plus censored band count.
RF transient, discontinuous aperture-edge/skew, AGC, comb, VBI, and caption evidence have separate
columns and statuses. `bottom_line` aliases the last reliable row for the review renderer;
`hs_bottom_line` is the last visible switch/pedestal row, and `hs_partial_line` is its exact
compatibility alias. Chroma-only survival cannot extend either marker. `dp` and
`switch_displacement` compare the preceding unit's same raster slot only when both coordinates
exist.

The authoritative geometry lock is source-blind. Picture lines `H` (the account top through the
row before the partial switch line) and switch-line count `c` are fixed constants from the first
measurable segment unit. They are re-seeded only by the first raw caption after a relative/windowed
lock or by a comb-confirmed hidden-top seed. Repeated per-unit H/c readings are evidence and never
vote the geometry to a new value; a segment that persistently contradicts its seed is reported.
The measured clip line and identified tape-line-22 luma level are the two fixed eight-slot
running-count comparators per field. A hit increments only its own count and bubbles upward;
a challenger takes over only after its count passes the incumbent. A new value uses a free slot or
replaces the least-counted slot, and no count is decremented. Every row stores each comparator,
its count, its runner-up count, and every occupied slot. The first measurable segment unit seeds `H` and
`c` from its directly visible geometry, using its visible top displacement or caption placement.
The expected switch identity is the placed top plus `H`. `switch_first_line` and
`first_full_other_head_line` remain raw evidence. Missing edges are `hold`; counter discontinuity
or a signal-state lock-like loss resets both fields. Absent Shuttle-regenerated rows hold an
existing lock and feed no gauge. A caption/XDS lock requires regenerated rows and exposed geometry
in that field; an agreeing-comb lock requires both fields. The commercial rewind therefore remains
`no-lock`/`acquiring`, with no lock-derived
coordinates even where the raw detector emits a candidate.

For a visible top below the standard line, `d` is that signed line difference. With a clamped top,
`d` is the visible picture-line count minus `H`; the hidden-top reading is applied only when the
comb confirms it. The crop origin is the standard line plus signed `d` at every sign, including
the Shuttle-overwritten row for negative `d`.

One-row switch-only motion is `travel`; a larger switch-only motion or different top/switch
amounts are `reported-hold`. Clip and line-22 comparator replacements are reported settling
events and never move the crop. The running line-22-level comparator
resolves ambiguous sub-black rows without a source-specific magic value. VBI
exclusions are based only on their measured waveform/run-in signatures. A measured comb that
differs from the shift settled at acquisition is recorded as a true disagreement for owner review;
the reference does not adjudicate it or change the settled comb.

An RF transient candidate retains its row, sample, strength, ratio, and before/after segment lags.
The former before-x lag gate was withdrawn because a tear can begin before the transient's sample.
The transient plus after-x tear remains useful evidence, but its RF status is `inferred`: it is not
promoted to an observed head-switch identification by itself.

The top detector treats a consecutive chroma-confirmed recorded, non-VBI dark band as picture;
brightness only locates the later luma onset. An isolated recorded black row is not promoted to
a band. Same-slot body displacement plus the raw first-row transition identifies the four SP
field-2 units whose picture begins at L287. Source-field parity is part of the measured transport
mapping, so the same luma pattern in the half-field-phased capture is not confused with the same
VBI row.

The contract-v3 comb confirmation uses each unit's measured field tops, stops at each field's
last reliable row (`switch - 1`), and evaluates relative shifts -3 through +3. A single
same-parity static mask is formed against the preceding unit at the published geometry and shared
by all seven candidates, so candidates cannot win by selecting different pixels. The measured
shift says which second named parity row sits between two adjacent first named parity rows.
Ordinary field-1/field-2 ordering expects zero. The V-stabilize-off slice is source-paired as
slot 2 of the current unit then slot 1 of the following unit; that reverses raster parity and
expects +1. The partner, expected shift, all seven energies, best/second energy,
their ratio, static-pixel count/fraction, texture, the resulting line mapping, and the top/switch/
band evidence are retained. Flat, moving, indecisive, missing-predecessor, and unavailable-
geometry units are `unmeasurable` and carry the literal shift `unmeasurable`, never a number.
Because this is one relationship between the two fields, the identical reading is stored in both
field-prefixed comb column families.

`reports/turn8_raw_row_audit.md` records the deciding line measurements for the commercial dark
band, the two comb-ordering questions, the isolated SP registration departure, and the four-unit
SP field-2 top correction.

`reports/turn9_body_comb_audit.md` cross-checks the five nominated SP body shifts against
their neighbouring seven-shift comb vectors and raw top/switch rows. It also records the EP
top/switch/band/comb census and the fixed-top switch-transition result.

`reports/turn10_row_disagreements.md` adjudicates the EP top rows and the commercial-tape
head-switch boundary directly from the raster. It documents the caption-following first-picture-row
fix, the EP field-2 VBI signature, the mid-row blanking cue from the other head, and the resulting
commercial stable-interval falsification.

The commercial capture uses counter-based review ordinals: first exact unit 211, with device-short
ordinals 213, 214, and 216 absent. The owner-provided stable-picture boundary at 551 is deliberately
an external test assertion in `build_invariant_report.py`, never a builder input. Units with an
acquired field lock (`locked` or a reported `hold`) and measurable edges test that invariant;
everything else is listed rather than counted as agreement. `signature_top_line` preserves the
per-unit VBI classifier's candidate, while `picture_top_line` and
`picture_top_under_lock_line` carry the account's decided/rendered top. This distinction is
required where an isolated dark row resembles line 22 but the bottom geometry says the picture
did not move. Across all 582 stable units the placed tops are L23/L286; field 2's provisional L287
signature in 174 units is retained as disagreement evidence and never moves the crop.

```sh
python3 experiments/geometry_oracle/build_reference.py \
  /private/tmp/hw-session/w_300s.tpc \
  experiments/geometry_oracle/reports/reference_w_300s.csv --profile w_300s
python3 experiments/geometry_oracle/build_reference.py \
  /private/tmp/hw-session/w_2100s.tpc \
  experiments/geometry_oracle/reports/reference_w_2100s.csv --profile w_2100s
python3 experiments/geometry_oracle/build_reference.py \
  /private/tmp/hw-session/sp_vstab_off_slice.tpc \
  experiments/geometry_oracle/reports/reference_sp_vstab_off.csv --profile sp_vstab_off
python3 experiments/geometry_oracle/build_reference.py \
  captures/composite_program_30s.tpc \
  experiments/geometry_oracle/reports/reference_composite.csv --profile composite
python3 experiments/geometry_oracle/build_comb_report.py \
  experiments/geometry_oracle/reports/comb_summary.md \
  w_300s=experiments/geometry_oracle/reports/reference_w_300s.csv \
  w_2100s=experiments/geometry_oracle/reports/reference_w_2100s.csv \
  sp_vstab_off=experiments/geometry_oracle/reports/reference_sp_vstab_off.csv \
  composite=experiments/geometry_oracle/reports/reference_composite.csv
python3 experiments/geometry_oracle/build_switch_lock_report.py \
  experiments/geometry_oracle/reports/switch_lock_summary.md \
  /private/tmp/hw-session/w_300s.tpc \
  w_300s=experiments/geometry_oracle/reports/reference_w_300s.csv \
  w_2100s=experiments/geometry_oracle/reports/reference_w_2100s.csv \
  sp_vstab_off=experiments/geometry_oracle/reports/reference_sp_vstab_off.csv \
  composite=experiments/geometry_oracle/reports/reference_composite.csv
```

`motion_audit.py` expands the reference's independently measured `dp` and switch displacement into
one row per transition and field. A missing current or preceding coordinate is `unmeasurable`,
never numeric motion. `build_motion_report.py` writes the joint histograms, complete unit lists for
every cell other than `(0,0)`, and three raw-row witnesses per populated cell. `field_alignment.py`
records the V-stabilize-off half-frame pairing without comparing like-numbered raster slots;
`slice_membership.py` verifies selected slice units byte-for-byte against the longer capture.

The reproducible transition audit consumes the generated reference itself:

```sh
python3 experiments/geometry_oracle/motion_audit.py \
  experiments/geometry_oracle/reports/reference_w_300s.csv \
  experiments/geometry_oracle/reports/motion_w_300s.csv \
  --capture w_300s
```

## Crop verdict layer

`score_crops.py` joins the frozen oracle and the published-crop table by transport ordinal. It
rejects missing, extra, or duplicate ordinals, missing schema columns, non-integer starts, and
starts more than 12 lines from 23/286. Owner-annotated garbage/snow/mute/relock units are written
to `forbidden.csv` and excluded from scoring. Authority is selected independently per field in the
fixed order parity-decoded caption, off-insert waveform, measured geometry, then none. A unique
off-insert waveform implies picture on the following line; when the independently measured black
tape gap is immediately after that waveform, picture begins two lines after it instead. Outputs
are `summary.md`, a per-field `verdicts.csv`, and exhaustive
`disagreements.csv`/`forbidden.csv` files. Existing output directories are never overwritten.
Geometry verdicts use `picture_top_line`; every verdict row also carries the recorded top and
black-band edges so their distinction remains auditable.

## Mutual-review fixtures

`reports/review_fixtures.csv` freezes the raw-raster examples found during the first mutual
review of the geometry-first prototype. Each row names a transport ordinal, field, raw-confirmed
`picture_top_line`, expected crop event, review finding, and the luma mean/standard deviation of
the candidate row and its two neighbors. It is regenerated directly from the capture and frozen
oracle rather than transcribed from an engine sidecar:

```sh
python3 experiments/geometry_oracle/build_review_fixtures.py \
  captures/fulltape.cap6 \
  experiments/geometry_oracle/reports/fulltape_geometry.csv \
  experiments/geometry_oracle/reports/review_fixtures.csv
```

The fixture events have crop-level meanings. `place` requires the published start to equal the
raw picture top. `hold_previous` requires the preceding exact unit's published crop. `forbid` and
`relock` require the standard 23/286 crop because the contract invalidates registration during
signal loss and on the relock unit. The three-column crop adapter cannot prove an engine's
internal reason name; a separate sidecar review must do that.

Score just these fixtures while still using the full crop CSV for predecessor lookups:

```sh
python3 experiments/geometry_oracle/score_crops.py \
  experiments/geometry_oracle/reports/fulltape_geometry.csv \
  crops.csv /private/tmp/review_fixture_verdict \
  --fixtures experiments/geometry_oracle/reports/review_fixtures.csv
```

Every fixture ordinal must occur in both the reference and crop table; missing rows, duplicate
fixture identities, changed frozen tops, invalid event names, and fixture/reference event
conflicts abort. A nonzero command exit means at least one fixture failed. The per-row output is
`fixture_verdicts.csv`; `fixture_summary.md` groups pass/fail counts by review finding.
