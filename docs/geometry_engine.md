# Approved geometry engine

The frameserver and OBS use the geometry engine by default. Its policy is the
engine approved as `v11-approved-2026-09-26` (`a7a4316`), with waveform tops,
same-frame bottom references, a paired-top anchor vote, and still/rigid-motion
comb authority. Legacy v9 code remains compiled but unselected pending its
separate post-merge removal. Captions are not a placement source.

## Configuration and ownership

`ge_default_config()` returns the approved numeric settings. `ge_init` copies
them into caller-owned, bounded engine storage (`ge_size()`); NULL selects
defaults. `fs_config.geometry_config` is likewise copied at `fs_open`.
A caller may discard or modify its original config after opening without
affecting that engine or any other instance. The OBS plugin passes NULL.
The library never reads the environment. No hot-path allocation is needed.

| Config member | Default | Replay/probe environment variable |
|---|---:|---|
| wave_bar | 0.45 | GE_WAVE_BAR |
| wave_clamp | 5 | GE_WAVE_CLAMP |
| comb_reject | 2 | GE_COMB_REJECT |
| comb_basin_factor | 1.5 | GE_COMB_BASIN_FACTOR |
| vote_window | 30 | GE_VOTE_WINDOW |
| vote_pair_min | 0.6 | GE_VOTE_PAIR_MIN |
| bottom_flat_margin | 3 | GE_BOTTOM_FLAT_MARGIN |
| blankspot_tolerance | 2 | GE_VOTE_BLANKSPOT_TOLERANCE |
| rigid_min | 2 | GE_COMB_RIGID_MIN |
| rigid_clarity | 1.3 | GE_COMB_RIGID_CLARITY |

Tools use one shared startup parser, not a library-global setting. Floating
values must be finite. Clamp is a nonnegative int; rigid minimum a positive
int; vote window is 1..256 (a fixed storage bound, not an evidence threshold).
Refusal and bottom margins are positive, basin factor and rigid clarity at
least 1, blank-spot tolerance nonnegative, pairing correlation in [-1,1].
Wave bar may be any finite value. Invalid configuration is rejected before
worker startup. Raster dimensions, search extents and sample coordinates
remain compile-time constants.

The former on/off experiment switches, flat-fill branch, plain-magnitude
comb withholding and top-refusal stubs are removed. They are not alternatives
to this engine. Numeric overrides are measurement tools, not approved defaults.

## Measurements

NTSC line = storage row + 4. Luma rasters are 720 by 525; body samples are
columns 40..679. A zero census edge means unavailable, never an inferred zero
displacement. Quantiles interpolate histogram order statistics consistently.

**Top:** correlate each row with the row above over the body, starting with
row 18 against 17 in each field. Scan rows 19..36 (+263 in field 2);
the first consecutive-correlation difference strictly greater than the bar
places the top one line before that step. Either standard deviation below
1e-9 gives correlation zero. No step means ABSTAIN. An observed displacement
outside the symmetric clamp around lines 23/286 means DISCARDED; the raw
observation remains logged. No amplitude, spread, chunk, plain-23 or run-in
patch is part of this top search.

The 0.45 bar separated eleven hand-checked frames; it was not derived from a
population distribution. The C raw-top census matched 172,586/172,586 field
edges. That validates implementation, not universal placement correctness.
Dark, low-contrast picture remains a known limitation of correlation steps.

**Bottom:** F is body row 258/521. If F's p95-p5 is at most 4, scan above it
through row 237/500. A row qualifies if its p50 or p95 exceeds F's matching
quantile by the margin, or its p5 is below F's by that margin. Comparisons use
margin minus 1e-9 to preserve inclusive ties. No qualifying row means unknown,
without fallback. If F is not flat, the original p95-minus-VI >5 and spread >4
test scans from row 259 in field 1 (the deck's half-line) and 521 in field 2.
The owner selected margin 3 after seven learned-reference forms failed.
The independent 12-row bottom profile, full-width VI median and horizontal
blanking quantile remain measured and logged; they are not interchangeable.

**Supplemental level top:** only on waveform ABSTAIN, never DISCARDED. Use
the median of blank rows 7..15 (+263), restricted to body samples. The first
row in 18..36 whose body mean strictly exceeds reference+10 is the sole
candidate. It must pass the same top clamp and correlate with the next row
above 0.30. There is no flat-row alternative. A fill is an input to the vote
only: it never replaces the census or enters relative-shift triggers.

## Relative placement and comb authority

The comb measures eleven shifts -5..5 on every frame, from fixed raw rows;
placement does not enter its energy computation. Product sums are exact
integers, with float32-rounded means and double-precision ratios. No fast math
or architecture-dependent reduction is used.

A triggered comb selects its best when runner-up/best reaches the basin
factor (1.5). Independently, proposed-energy/best strictly above the refusal
bar (2) rejects a placement. Build a contiguous floor extending through
neighbors at most factor times the minimum. Substitution requires an interior
floor with both exterior rises at least the same factor. Otherwise discard
the proposed geometry and retain the unvoted previous pair, or zero at a
section start. Never discard image data. A held relative correction belongs
to the two census tops that derived it; a changed or missing top invalidates
the correction and requests fresh evidence.

Per-field motion compares adjacent same-epoch units, never across a reset.
Vertical SAD searches -5..5 over aperture-relative rows 40..219 and body
columns 40..679 (aperture starts at storage row 19/282). Exact ties prefer
smallest absolute shift, then negative. Both known zero shifts make a still
frame. A still frame adds a trigger when the proposed comb ratio is at least
the refusal bar and the floor is enclosed, then uses the ordinary decision
path. Unknown motion leaves ordinary authority intact.

A field with absolute vertical shift at least rigid_min also gets a 2-D
search: dy -5..5, dx -8..8, the same rows, alternate body columns 40..678.
Exact ties take first dy/dx in scan order. Clarity is the minimum SAD at
least two away in either axis divided by best SAD. Zero best gives infinity
when far is positive, otherwise 1. Withhold comb verdicts only if both
frame-owned fields have dx=0, absolute dy at least rigid_min, and sufficient
clarity. Do not adopt, reject, substitute or update held correction from a
withheld comb. Other top-basis invalidation remains active.

Provenance: rejection/basin work passed the four-capture 21-substitution /
5-discard gate. Still/rigid motion was then checked against the whole-tape
vertical and 2-D censuses; 11,152 2-D fields had identical best shifts.
Reference SAD rounding, not the implementation, caused the original clarity
tolerance failures. The owner approved clarity 1.3 with captures 1–4 unchanged.
These checks do not turn relative alignment into evidence for an absolute
picture origin.

## Absolute anchor vote

A frame votes only when both vote tops exist, their implied shift is in the
enclosed comb floor widened by one on its high side, their cross-field
Pearson correlation reaches the pairing threshold, and every skipped field-2
line from 286 to its vote top contains a body sample no higher than that
field's full-width VI median plus blankspot_tolerance. Blank spots can remove
confidence only. Pairing threshold 0.6 and tolerance +2 are the approved
entry-37/39 instruments, not caption-derived placement.

Append the confident field-2 offset to the last vote_window confident frames.
The mode wins. Ties retain the current anchor if tied, otherwise the newest
tied value, otherwise the first tied value in chronological window order.
Non-confident frames neither vote nor change the anchor. Resets clear votes
but retain the last published anchor; only session start uses the engine's
own anchor while the window is empty.

Publish (anchor-d, anchor), preserving the relative path's d. Keep unvoted
fallback state separate from the vote: a prior voted anchor must not feed
back into held-correction or basin-discard decisions.

## Pairing, resets and sidecar compatibility

Aligned pairing completes immediately. Reversed pairing delays one unit:
frame field 1 comes from frame_top_unit, field 2 from the current row's unit.
Applied offsets describe each row's own fields, not necessarily one woven
frame. Unused boundaries are explicitly flushed with their own census
placement (or zero). Gaps and epoch changes break adjacency. After flushing,
ge_set_pairing clears decision evidence and votes but retains the published
anchor; ge_init starts an entirely new session.

The publisher's aperture is 240 lines per field: 23+d1..262+d1 and
286+d2..525+d2. Review renders use 243 per field starting three lines earlier.
Schema 28 is retained byte-for-byte, with the same ordering, formatting,
empty-value conventions and historical configuration columns. Frozen switch
columns read approved values; ge_comb_motion_min stays the historical value
1 for compatibility and is NOT the rigid minimum (default 2). No removed
switch is consulted to produce those values. Newly exposed numeric parameters
without schema-28 columns are echoed to stderr when overridden; retain that
startup output with non-default experiments.

comb_ran means triggered, not merely measured or adopted. confidence HIGH/LOW
reflects that trigger state, not probability and not vote_confident. Compare
frame_d2-frame_d1 against comb_d; never substitute applied_d2-applied_d1 on
reversed-pair rows. Measurement ownership is explicit: raw waveform and
horizontal-reference provenance are unit-owned, while census, bottom evidence,
vote, rejection and motion in a completed frame are frame-owned.

The legacy --geometry-v11 and --audit-comb tool arguments are compatibility
no-ops. Default fs_open and OBS use this policy without them or any engine
environment variables. Pair-next and pairing schedules still describe input
field ownership, not selection of a different engine.

## Validation and CPU

The cleanup gate is byte identity against the five registered approved
sidecars, including audio evidence and configuration echoes. Do not normalize
columns or regenerate references to obtain a pass. Capture losses, unknown
measurements and failed comparisons remain visible.

Run make geometry-test in src/field_registration and test, test-geometry,
test-pairing and sanitizer targets in src/frameserver. Synthetic tests cover
instance isolation, configuration copying/validation, numerical boundaries,
motion authority, source ownership, holds, reset/EOF handling and transport
accounting. Retained v9 tests cover the still-compiled legacy implementation.

For CPU use frameserver's bench-geometry with CAPTURE, fresh scratch SIDECAR
and TIMINGS paths, and optional BENCH_ARGS for input pairing. It executes the
actual default worker, including conditional 2-D searches, with production
compiler flags. Thread CPU covers classification through item completion,
including sidecar formatting, excluding queue waits and input I/O. Report
whole-worker median/p95 and zero/one/two-search populations; engine-only and
legacy-v9 timings are not substitutes for this measurement. Run final replay
at 4x with no competing project jobs, checking holes/drops and all sidecar bytes.

The phase-A full-tape default worker measured 1.748500/2.736334 ms median/p95
over 86,293 units, including 6,695 units with a 2-D search (11,152 fields).
Two-search units measured 3.144542/5.043500 ms; maximum worker CPU was
8.533708 ms, with no sample over the 10 ms budget. This is above the preceding
approved-worker record of 1.404041/2.531042 ms; unchanged classifier CPU also
increased between runs, so the measurements do not isolate a cleanup cost.
