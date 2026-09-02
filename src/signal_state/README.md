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
`signal_state_note_registration()` then feeds the same unit's phase observation
back into the trajectory gate, allowing positive-but-provisional chatter to
open an `unsettled` interval. The caller, not this library, invokes
`fieldreg_begin_segment()` or `fieldreg_discontinuity()` according to the
returned action bits.

`SIGNAL_ACTION_REGISTRATION_DISCONTINUITY` is transport truth. Acquisition and
relock transitions produce `SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT`; ordinary
scene cuts or global luma changes do not. Optional audio-mute/OSD inputs are
generic corroborating context, never defining evidence.
