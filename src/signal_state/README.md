# Signal-state classifier

This library reports three deliberately separate layers:

1. transport state copied from `unit_parser` (never inferred from pixels);
2. observable raster appearance, named only by measurable properties;
3. temporally hysteretic source-state inference, allowed to answer `Unknown`.

No label names a deck or assumes a deck-specific mute policy. A neutral gray,
blue, black, or OSD-bearing mute from a different source remains a measured
appearance plus an explicitly uncertain inference.

The hot path is allocation-free and retains only subsampled luma history and a
small state machine. `signal_state_classify()` runs before registration.
Registration never feeds back into this library. The caller, not this library, invokes
`fieldreg_begin_segment()` or `fieldreg_discontinuity()` according to the
returned action bits.

`normal_picture` requires the current appearance observation to be ProgramLike
and the source to have acquired Present. A previous hysteretic ProgramLike/Present
label cannot authorize a current gray, sub-black, snow or unknown raster. The
frameserver publishes its last successful crop through this gate and emits
`SignalGateHold`, `registration_measured=0`, and the current gate cause.

`SIGNAL_ACTION_REGISTRATION_DISCONTINUITY` is transport truth. Acquisition and
relock transitions produce `SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT`; ordinary
scene cuts or global luma changes do not. Optional audio-mute/OSD inputs are
generic corroborating context, never defining evidence.

## Observable appearance rules

The active raster is sampled into 15 by 15 broad tiles per field. In addition
to mean/sigma and gradient energy, the public measurements expose robust luma
and chroma-distance medians, neutral-chroma and sub-black pixel fractions, the
fraction of tiles with meaningful luma range (`program_extent_fraction`), and
a temporal/locality score for a small static overlay. Edge energy alone is
never program evidence.

A neutral raster with luma median at least three code values below nominal
blanking (`Y <= 12`) is immediately `SubBlackMuteLike`, regardless of sparse
white streaks, bottom noise, or OSD edges. This is a safety veto: such a unit
can never be reported as `ProgramLike`. A flat neutral raster may carry a
localized static high-contrast overlay and remain
`NeutralGrayMuteLike`; broad spatial extent is required before the fallback
program rule can fire. These are signal properties, not knowledge of any deck.

Appearance and source labels otherwise use asymmetric hysteresis. Defaults are
five consecutive units to enter program/reacquiring, three to enter mute or
no-input, and two for ambiguous/unknown. The last confirmed label is held
during a shorter contradictory run instead of flapping through `Unknown`.
The format-level `0x0800` observation and the robust sub-black veto are applied
immediately; source-state confirmation remains separate except that a robust
sub-black raster is itself sufficient for the property label `Muted`.

## `unsettled` on the live path

An interval opens at startup, on a structural discontinuity, or on a confirmed
acquisition/source transition. Repeated units in an already-confirmed mute/no-input state do not
reopen it. A confirmed mute/no-input state is a settled non-picture endpoint
with no settled raster phase.

Present settles when source evidence confirms Present. This says nothing about
the geometry lock or the correctness of the published crop. The engine owns
its lock, applied phase, and per-field observation changes; the record carries
those separately. No phase dwell or chatter threshold controls source inference.

Host-side shedding is explicitly separate from source state. A caller sets
`host_raster_unobserved` when an otherwise valid current raster was shed by a
bounded downstream pool; the result reports `Unknown` appearance for that row
while retaining the confirmed source and interval. It cannot
fire a registration action. `host_observations_missing_before` clears only the
same-parity temporal image reference before classifying the next retained
raster. Parser-originated hole, short, and unframed observations remain real
structural discontinuities and still invalidate temporal source evidence.
