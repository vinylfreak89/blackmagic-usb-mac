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
`log_header` in frameserver.c defines the CSV column set (schema 28 by default).

## Optional horizontal-timing repair

`fs_config.tear_repair` defaults to **0**. The replay tool maps
`FS_TEAR_REPAIR=0|1` to it; the library reads no environment. OBS's default open
leaves it off. This is downstream concealment, not a registration instrument:
the raw raster, classifier, geometry observations, placements and archival input
are unchanged. No MP4 or default promotion is implied by enabling this option.

Per published 240-row field aperture, the detector uses the full-width median
of nine VI rows (storage 7..15 / 270..278). A picture-carrying row contains eight
consecutive luma samples strictly above blank+20 in columns 8..715. Starting at
the last such row, it flags the contiguous backwards run of picture rows having
at least 60 samples within blank +/-3 in columns 8..199. Trailing blanking is
untouched; a field with no picture row abstains. These are entry 46's measured
detector constants, not general guarantees: dark pillars at blank level can
also satisfy the rule. Classifier ProgramLike gating is **not** applied.

Replacement sources are unflagged picture-carrying rows of the actual woven
pair. X averages the adjacent other-field rows (or uses the sole available
one). W interpolates the nearest own-field rows by vertical distance, or
duplicates the sole available side. No available source leaves the row
unchanged. All UYVY components use nearest-integer weighted averages; replacement
pixels are never used as sources for another replacement.

X requires local comb agreement: at most twelve row intervals above the run,
columns 40..679, using the engine's `max((a-b)*(c-b),0)` arithmetic at offsets
-5..+5. Only intervals clean and available at **all eleven** offsets contribute.
The nominal energy must be at most twice the minimum; this reuses the approved
comb's refusal factor 2. No clean support means W. This is an estimate of local
field agreement, not proof that replacement pixels reconstruct the original.

Reversed pairing uses next-unit field 1 and current-unit field 2. Repaired field
1 is cached for its own unit's subsequent publication; registration retained
the untouched luma first. No additional unit of lookahead is introduced. Unpaired
boundary fields are not repaired from a fictitious partner.

Off emits schema **28**, unchanged. On emits schema **29**, preserving existing
decision cells except `schema_version`, then adding `fs_tear_repair` and, for
each suffix `_f1` / `_f2`: `tear_flagged`, `tear_repaired`, `tear_fill` (X),
`tear_interpolate` (W), `tear_first_flagged`, `tear_last_flagged`, `tear_first`
and `tear_last`. Extents are NTSC lines, zero when none. Empty cells indicate no
complete woven frame. Like `frame_d1/frame_d2`, repair evidence is frame-owned:
field 1 belongs to `frame_top_unit`, not necessarily this row's transport unit.
`published=0` still means nothing reached the consumer. Counts describe the
attempted frame repair, not permission to treat a dropped frame as published.

This option transforms the frameserver's output pixels. A separate renderer
reading the original capture and only its placement log does not automatically
reproduce those pixels; it must also apply the repair or consume the repaired
frameserver output. The option's synthetic pipeline test checks emitted UYVY,
including reversed ownership, rather than relying only on log counts.

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
