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
Each instance owns a copy of `signal_state_config`. Pass `NULL` to
`signal_state_init()` for defaults, or start with `signal_state_default_config()`
and override named members. `fs_config.signal_config` passes the same copied
configuration at frameserver open; a default OBS/tool open supplies `NULL`.
The library reads no environment. There are no new tool environment overrides.
Epoch resets preserve configuration, not temporal evidence.

## Parameters and provenance

Defaults below reproduce the pre-configuration classifier, including its known
limitations. These are inherited heuristic constants, **not newly fitted or
distribution-derived thresholds**. The provenance keys name the commits that
introduced the current value: A = `4fc8e9e` (initial classifier),
B = `7928b67` (neutral raster with localized overlays), C = `edcabf0`
(robust extent/sub-black rules). CLAUDE.md §6 records the September 9 audit,
including failure cases; it does not validate every constant independently.

Initialize a complete configuration from the defaults, not a zero-filled or
partial aggregate. Floating members must be finite; score denominators must be
positive; fractions/confidences conventionally lie in [0,1]. The existing six
hysteresis members retain zero-means-default handling; the phase window is
capped at 64 and its threshold at the window length. The new tuning members
are used literally (zero can intentionally be a cutoff), with no fallback or
new parameter-validation policy. Clamps to [0,1], absent-evidence zeros,
format-level certainty 1, counting arithmetic and histogram medians are
mathematical definitions, not tuning controls.

| Member | Default | Decision | Origin |
|---|---:|---|---|
| `appearance_confirm_units` | 2 | Minimum appearance/source confirmation. | A |
| `acquisition_confirm_units` | 5 | Program/reacquiring confirmation. | C |
| `mute_confirm_units` | 3 | Mute/no-input confirmation, except immediate sub-black. | A |
| `phase_chatter_window_units` | 30 | Optional feedback window length. | A |
| `phase_chatter_threshold` | 4 | Changes that open an unsettled interval. | A |
| `settle_confirm_units` | 30 | Stable applied phases needed to settle. | A |
| `tile_activity_min` | 12 | Tile luma range >= value counts as active. | C |
| `flat_luma_distance_max` | 2.0 | Sample absolute Y-minus-mean <= value counts as flat. | A |
| `neutral_chroma_distance_max` | 4 | Sample absolute C-minus-128 <= value counts as neutral. | C |
| `subblack_luma_cutoff` | 16 | Sample Y < value counts as sub-black (not the padding code). | C |
| `overlay_static_mad_max` | 3.0 | Static score clamp((value - temporal MAD) / value). | C |
| `overlay_extent_rise` | 0.02 | Rising extent-score denominator. | C |
| `overlay_extent_fall_start` | 0.35 | Falling extent-score zero crossing. | C |
| `overlay_extent_fall_width` | 0.25 | Falling extent-score denominator. | C |
| `padding_fraction_min` | 0.98 | Padding fraction below value makes appearance unknown. | A |
| `padding_confidence_gain` | 10.0 | Unknown confidence multiplier for padding deficit. | A |
| `neutral_chroma_median_max` | 4.0 | Median chroma distance <= value permits neutral rules. | C |
| `neutral_chroma_fraction_min` | 0.75 | Neutral sample fraction >= value permits neutral rules. | C |
| `subblack_median_max` | 12.0 | Neutral luma median <= value selects sub-black. | C |
| `subblack_confidence_luma_reference` | 16.0 | Sub-black confidence luma zero reference. | C |
| `subblack_confidence_luma_span` | 8.0 | Sub-black confidence luma denominator. | C |
| `subblack_confidence_fraction_offset` | 0.70 | Sub-black confidence fraction subtrahend. | C |
| `snow_sigma_min` | 35.0 | Sigma > value required for snow. | C |
| `snow_gradient_min` | 30.0 | Gradient > value required for snow. | C |
| `snow_extent_min` | 0.50 | Active extent > value required for snow. | C |
| `snow_confidence_sigma_offset` | 30.0 | Snow confidence sigma subtrahend. | C |
| `snow_confidence_sigma_span` | 25.0 | Snow confidence sigma denominator. | C |
| `snow_confidence_gradient_offset` | 25.0 | Snow confidence gradient subtrahend. | C |
| `snow_confidence_gradient_span` | 30.0 | Snow confidence gradient denominator. | C |
| `gray_sigma_max` | 3.0 | Uniform sigma < value; also uniform confidence denominator. | B |
| `gray_gradient_max` | 2.0 | Uniform gradient < value. | B |
| `gray_flat_fraction_min` | 0.55 | Overlay branch requires flat fraction > value. | B |
| `gray_extent_max` | 0.30 | Overlay branch requires extent < value. | C |
| `gray_temporal_mad_max` | 3.0 | Overlay branch permits zero MAD or MAD < value. | C |
| `gray_mean_min` | 8.0 | Neutral-gray rule requires mean >= value. | A |
| `gray_mean_max` | 240.0 | Neutral-gray rule requires mean <= value. | A |
| `gray_confidence_flat_offset` | 0.50 | Overlay confidence flat-fraction subtrahend. | C |
| `gray_confidence_flat_gain` | 2.0 | Overlay confidence flat-fraction multiplier. | C |
| `ambiguous_extent_max` | 0.12 | Extent < value selects flat ambiguity; also confidence denominator. | C |
| `program_confidence_sigma_span` | 24.0 | Program confidence sigma denominator. | A |
| `program_confidence_gradient_span` | 18.0 | Program confidence gradient denominator. | A |
| `held_source_confidence` | 0.5 | Confidence when retaining source across contrary or absent evidence. | C |
| `phase_change_confidence_min` | 0.25 | Optional phase feedback accepts confidence >= value. | C |

The snow confidence is the smaller of its two offset/denominator ramps. The
sub-black confidence adds its luma ramp and fraction-minus-offset. The overlay
confidence is the larger of its flat-fraction ramp and localized-overlay score.
The program confidence is the larger of sigma/span and gradient/span. Every
confidence is finally clamped to [0,1]; operator order is unchanged.

Raster geometry remains compile-time: 525 rows × 720 pixels, 48-byte header,
UYVY, sampling every fourth pixel on storage rows 20..256 and 282..518;
15×15 tiles per field; fixed padding rows 0..6, 261..269 and 523..524;
VBI rows 16..17 and 279..280. C128/Y16 is the device-written padding
signature, not an adjustable picture-black threshold. It stays distinct from
the configurable sub-black pixel cutoff, even though that cutoff also defaults
to 16.

## Registration connection and known limitations

The current frameserver consumes `actions`, not appearance/source labels or
their confidence, to request geometry resets. `BEGIN_SEGMENT` clears the vote
window/relative history; the last published anchor is retained by the geometry
engine's empty-window policy. `unsettled` contributes only to statistics. No
classifier label supplies a vote top or a vote confidence.

The September 9 audit in CLAUDE.md §6 names three unresolved limitations:

- SnowLike lacks temporal/vertical-coherence terms. A missed acquisition may
  omit a reset; no replacement rule is defined by this parameterization.
- SubBlackMuteLike installs immediately while leaving it requires confirmation.
  Appearance and source inference are separate: a stale appearance alone does
  not establish a geometry reset, but source transitions can do so.
- NeutralGrayMuteLike tests uniformity, not greyness. The historical 253
  near-black units are an audit result, not a fresh score; falsely inferring
  mute can produce a new segment when source inference returns to Present.

The worker benchmark's optional `CLASSIFIER_TRACE=/scratch/new.csv` buffers
all per-unit results (hexadecimal doubles), action bits and geometry reset
inputs until join. Its test-only `--suppress-begin-segment` option masks that
action downstream of the recorded result, retaining all transport resets.
This measures the action connection, not a proposed classifier repair or a
claim that every inferred reset is erroneous. Tracing is excluded from CPU
timings and does not change the production sidecar schema.

## Optional registration feedback

The optional `signal_state_note_registration()` API can feed the same unit's
phase observation back into the trajectory gate, allowing positive-but-provisional
chatter to open an `unsettled` interval. The geometry frameserver does not use
that feedback API. It maps the returned registration action bits to geometry
resets; the classifier does not call an engine directly.

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

With defaults, a neutral raster with luma median `Y <= 12` is immediately
`SubBlackMuteLike`, regardless of sparse
white streaks, bottom noise, or OSD edges. This is a safety veto: such a unit
can never be reported as `ProgramLike`. A flat neutral raster may carry a
localized static high-contrast overlay and remain
`NeutralGrayMuteLike`; broad spatial extent is required before the fallback
program rule can fire. These are signal properties, not knowledge of any deck.
The sub-black constants retain the original nominal-code hypothesis; they do
not use the geometry engine's measured blanking reference. CLAUDE.md §6 records
the measured source-level distinction and the classifier's known limitations.

Appearance and source labels otherwise use asymmetric hysteresis. Defaults are
five consecutive units to enter program/reacquiring, three to enter mute or
no-input, and two for ambiguous/unknown. The last confirmed label is held
during a shorter contradictory run instead of flapping through `Unknown`.
The format-level `0x0800` observation and the robust sub-black veto are applied
immediately; source-state confirmation remains separate except that a robust
sub-black raster is itself sufficient for the property label `Muted`.

## `unsettled` on the live path

An interval opens at startup, on a structural discontinuity, on a confirmed
acquisition/source transition, or when positive registration observations
chatter. Repeated units in an already-confirmed mute/no-input state do not
reopen it. A confirmed mute/no-input state is a settled non-picture endpoint
with no settled raster phase.

For present video, the forward-only caller supplies both the estimator's
instantaneous observation and the phase actually applied to the published
unit. The interval settles after the source is confirmed, the applied phase is
unchanged for `settle_confirm_units` (default 30), and the registration-change
window is clear. Thus a valid applied fallback can settle the live stream when
absolute visual evidence abstains; `settled_phase_known` describes the phase
being presented, not a claim that a physical landmark was observed in every
unit. The optional archival trajectory layer may revisit provisional history,
but it is not part of this zero-latency state machine.

Host-side shedding is explicitly separate from source state. A caller sets
`host_raster_unobserved` when an otherwise valid current raster was shed by a
bounded downstream pool; the result reports `Unknown` appearance for that row
while retaining the confirmed source, interval, and settled phase. It cannot
fire a registration action. `host_observations_missing_before` clears only the
same-parity temporal image reference before classifying the next retained
raster. Parser-originated hole, short, and unframed observations remain real
structural discontinuities and still reset source/phase inference.
