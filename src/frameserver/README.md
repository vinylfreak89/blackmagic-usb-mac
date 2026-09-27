# Frameserver and decision sidecar

The default frameserver and OBS registration path is the approved geometry
engine. The v9 engine and its schema-9 writer have been removed. See
[geometry_engine.md](../../docs/geometry_engine.md) for the measurement,
publication, parameter and schema-28 contract.

Decision rows are transport-unit keyed, with an independent published-frame
pair in `frame_d1/frame_d2`. Under reversed pairing, `frame_top_unit` names
the next unit supplying field 1; `applied_d1/applied_d2` describe the fields
owned by the row's own unit. Reversed pairing delays unit completion by one
unit; consumers pair fields according to the logged ownership. Measurements
and explicit unavailable values are retained separately from placement.
`log_header` in frameserver.c defines the complete CSV column set.

## Optional scene-cut pairing detection

`fs_config.field_order_detect` is zero by default. The replay tool maps
`FS_FIELD_ORDER_DETECT=0|1`; the library never reads the environment. OBS exposes
the English checkbox **Detect field pairing from scene cuts (experimental)**,
also off by default. It changes transport pairing, not spatial parity or the
OBS TFF/deinterlacer setting. It is independent of horizontal retiming.
It selects the geometry engine's pairing interpretation through the existing
`pair_next` path; publication retains the existing unit-owned field contract
described above, rather than rewriting capture slots or deinterlacing pixels.

The observer measures raw storage luma rows 20..79 and 283..342, all 720 samples,
against the same slot in the previous adjacent complete unit. This top-picture
strip is the cut-measurement region, not a shifted or repaired aperture. The
rolling baseline is the preceding 30 mean absolute differences per slot; eight
differences are required before detection. A spike must strictly exceed
`max(8, 3*median, median + 6*1.4826*MAD)`. The one-second history and robust
six-sigma/threefold separation distinguish abrupt changes from ordinary noise
and motion; the eight-code floor is half the measured black/blank separation
in CLAUDE.md §6. These are experimental fixed policy values, not label-tuned
thresholds or proof that a spike is an edit.

An isolated both-slot spike followed by a quiet unit votes aligned. Slot 2
spiking, then slot 1 on the next unit, then quiet votes reversed. Every other
spike episode is ambiguous. Two successive matching unambiguous episodes are
needed to confirm pairing; an ambiguous episode clears that streak. Between
cuts the last pairing is held, not re-estimated. The quiet closing unit adds
one unit of **decision** delay, not video buffering. Cold start uses
`geometry_pair_next` (normally aligned); it cannot repair earlier output or
establish the pairing at play start before sufficient cuts. An explicit
`pairing_schedule` and automatic detection are mutually exclusive.

On a change, the worker finishes the old pending boundary with `ge_break`,
then calls `ge_set_pairing` and starts the new pairing with a geometry reset.
`pairing_note` and `field_order_discontinuity` name `FieldOrderCutAligned` or
`FieldOrderCutReversed` on that unit. The existing `pairing` column always
describes the applied setting, including orphaned/late pending units. Event
evidence travels with the unit, not mutable next-unit state. Counter gaps,
counter aliases, epoch changes, incomplete units and host loss reset the
observer and consistency; the applied pairing is held until reconfirmed.
Classifier appearance changes do not erase cut evidence. No source pixel,
H-retiming detector or capture timestamp is changed by this observer.

When enabled the log is schema 36, or 37 when H-retiming is also enabled.
It appends `field_order_change_f1/f2`, `field_order_threshold_f1/f2`,
`field_order_spikes` (bit 0 slot 1, bit 1 slot 2), `field_order_cut_first`
(first spike's extended counter), `field_order_event` (aligned/reversed/ambiguous),
`field_order_votes` (0..2), `field_order_confirmed`, and
`field_order_discontinuity`. Empty cells mean no corresponding measurement or
event, not zero evidence. OFF preserves schemas 28/30 and their bytes.

The small per-unit change sentinel runs whenever enabled, but pairing verdicts
are event-driven only. The ~87 KB reference/history is allocated at open and
owned by the video worker: no per-unit allocation, cross-thread wait, optical
flow or extra retained full raster. Repeated source edits on alternating
field phases, telecine, flashes, motion, fades and sparse/no cuts remain
limitations; two matching cuts cannot distinguish source editing cadence
from a hardware-induced pairing offset. Do not treat this as a header/status
flag or universal automatic field-order detection.

Validation found the expected reversed verdict on capture 3 and aligned on
capture 4, but **not exact agreement with the approved whole-tape pairing
history**: the two-cut rule sometimes switches within a registered constant
interval and necessarily reacts late at startup/boundaries. It also abstains
on a weaker listed cut. The option remains an OFF-by-default experiment,
not a replacement for that reviewed schedule or approval for automatic use.

`make test-field-order` checks synthetic cuts through the actual worker against
explicit pairing schedules, including both switch directions and pending-unit
boundary cells. The pure observer is also in unit and sanitizer suites.

## Optional horizontal retiming

`fs_config.hretime` defaults to zero. Tools accept `FS_HRETIME=0|1`; the library
does not read the environment. Off retains schema 28 and performs no repair
analysis. This is a per-tape presentation option, not a new registration input.
Raw capture, classifier, geometry, offsets, vote and comb decisions are unchanged.

The detector runs on the actual published 720x480 pair. Each luma row is compared
with its woven neighbours' mean over columns [60,660), searching shifts -24..24
(first minimum wins). A nonzero winner with SAD ratio <0.8 marks a discontinuity.
The ratio retains the reference's 1e-6 denominator floor at zero SAD; ties in
owner strength abstain, including uniformly blank frames.
Contiguous discontinuities form a band; the strongest qualifying same-field
boundary break assigns its owner. Equal strength or no qualifying break abstains.
These are the owner-reviewed entry-57 detector settings, not width tolerances.
Each field-1 line >=255 and field-2 line >=518 is excluded from repair, including
the end of a band crossing the cutoff. Detected damage there is not a donor.

For a flagged line, picture edges cross the midpoint between its VI median
(full-width storage rows 7..15 or 270..278) and its own [60,660) median.
Unflagged, uncensored own-field aperture rows 40..219 provide median width and
the 90th percentile absolute width deviation. Missing picture or usable width
support means interpolation, not a guessed shift. Width is right minus left;
no extra amplitude bar or minimum tolerance is imposed. Shift-induced picture
loss must fit that tolerance; censored edges (0 or >=718) additionally count
inferred missing width against the same allowance.

An admissible line is shifted by the detected amount. Vacated luma uses its
blank-side median (VI median if none is visible), chroma neutral 128. Odd shifts
interpolate chroma at half phase, rather than corrupting UYVY phase or rounding
the luma shift. Otherwise a small ELA interpolator averages opposite-field
neighbours along the best of seven directions (0, +/-1, +/-2, +/-3), comparing
three luma samples and preferring vertical on ties. This bounded local stencil
is not NNEDI3 and makes no claim to recover missing detail. One available donor
is duplicated; no unflagged donor leaves the line unchanged and explicitly
unavailable. All donors are immutable raw rows, never earlier repairs.

The workspace and two unit copies are allocated at open. Reversed pairing
repairs current-unit f1 with pending-unit f2; repaired f1 is retained until its
own transport unit publishes. No additional lookahead or frame allocation is
introduced. Orphan boundaries have no fictitious repair partner.

On uses schema 30 (29 belonged to the reverted head-switch experiment). Only
`schema_version` changes among old cells. New columns are `fs_hretime` and,
for each `f1`/`f2`, `hretime_bands_*`, `hretime_retimed_*`,
`hretime_interpolated_*`, `hretime_unavailable_*`, `hretime_first_*`,
`hretime_last_*`, `hretime_lines_*`. Line lists contain space-separated
`NTSC:R`, `NTSC:I` or `NTSC:U` tokens. First/last cover actual repairs only;
zero means none. Empty cells mean no complete frame to assess. These are
frame-owned observations: f1 belongs to `frame_top_unit`, f2 to the row's own
counter. A publisher failure remains unpublished even if repair was computed.

The reference script's displayed coordinates already include +4 (NTSC), and
its printed list shows only the first three bands per field. Detection is
checked against its complete list; switch-crossing repair truncation is
reported separately. Synthetic tests cover width change, censoring, mirrored
field ownership, blank input, UYVY phase and actual reversed-pair publication.

## Deterministic audio evidence

The parser/delivery thread writes audio correlations and snapshots the matching
correlation when it emits a video-unit observation. That input-order boundary,
not the video worker's scheduling, is the decision log's evidence cutoff.
`audio_residual_ticks` and `audio_step_samples` use that immutable snapshot,
which travels with the unit through its existing bounded queue and reversed
pairing. No extra queue, per-unit allocation, wait or video buffering is added.

If the resync is absent at this cutoff, or has already left the 256-entry
correlation history, both cells stay empty. A later resync cannot retroactively
fill them. This is a deterministic placeholder rule for the same ordered input,
not a zero residual or evidence that audio itself is absent. Ineligible transport
and dropped-pool observations retain their existing empty-cell policy. Residual steps
still compare published units within one epoch and audio anchor generation;
missing evidence does not invent a step or a new anchor.

Live `fp_frame.audio_pts_known/audio_pts_num` are separate: they retain the
publication-time best-effort lookup, so available later evidence may timestamp
the frame even when its log cells are empty. That bounded seqlock lookup may
also abstain during concurrent writes. The OBS timestamp policy, PCM, media
publication order and registration decisions are unchanged.

`make tests/audio_lookup_probe` builds a diagnostic replay which timestamps
failed lookups and compares ingress with publication evidence.
`tests/audio_lookup_stress` additionally yields the writer inside its update;
report those scheduler-perturbed counts separately from natural replay rates.
Neither probe nor scheduler hook is enabled in production. `audio_evidence_test`
uses a condition-handshaked writer overlap and covers eviction, late/missing
audio, epochs and pending-item ownership; it is included in native and sanitizer
targets.

## Loss accounting

- A pool-full observation retains its own ordinary row, is unpublished, and says `PoolFull`.
- Ring-full observations cannot reach the worker individually. Their count is attached to the
  next retained row as `preceding_ring_drops`, locating the omitted ordinal range immediately
  before that row.
- If no later observation exists, one synthetic `RingFullTail` row is emitted. Its `ordinal` is
  the first omitted ordinal and `preceding_ring_drops` is the number of omitted observations.
  It is a range marker, not a captured video unit.
- `PublisherFull` means analysis completed but no output surface was available.
- Short, unframed and other ineligible observations keep their provenance and
  explicit drop reason; they do not receive fabricated raster measurements.

These rules preserve the conservation relation between ingress observations,
sidecar rows/ranges, and published or explicitly dropped units.

## Checks and worker budget

`make test test-geometry test-pairing` exercises transport, publication,
configuration, measurement and pairing. ASan/UBSan and TSan variants are
`test-asan test-geometry-asan` and `test-tsan test-geometry-tsan`.

`make bench CAPTURE=/path/input.tpc SIDECAR=/non-synced/new.csv
TIMINGS=/non-synced/new.timings.csv` runs the real geometry worker at 4x.
Use `BENCH_ARGS="--pair-next"` or `--pairing-schedule FILE` for the input's
field ownership. No engine environment settings are required. `bench-geometry`
is an alias. Timing begins at classifier entry and ends at item completion,
including geometry's conditional 2-D search, assembly/publication and sidecar
formatting, excluding queue waits and input I/O. The report separates units
with zero, one and two 2-D searches. Run isolated; count holes and drops and
compare every sidecar byte with the registered reference.
