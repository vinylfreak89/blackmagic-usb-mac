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

## Optional horizontal retiming (E-61 experiment)

`fs_config.hretime` defaults to zero; OBS's existing setting is unchanged.
Tools map `FS_HRETIME`; the library reads no environment. Off retains schema
28 and performs no repair analysis. This experimental presentation path is
not an approved replacement for registration or a default-on repair policy.
Transport, classifier, geometry, vote and comb see only immutable source pixels.

The detector uses the actual published field pair and placements. Six
120-sample luma windows cover each row. Each window searches full valid
reference windows at integer offsets within +/-64, independently against the
previous repaired same-field row and the current counterpart field row.
Detection never averages the two fields. SAD is exact integer arithmetic with
a NEON implementation; equal minima prefer zero, then smaller absolute offset,
then negative reference shift. Positive logged displacement means the current
line moved right; correction reads source[x+displacement].

Both compared windows must have population SD >=4. Nonzero evidence requires
SAD <0.8 of its zero-offset value; the best match also needs Pearson >=0.8.
These are explicit experimental qualifications, not universal VHS constants.
At least four qualified windows must fit a linear offset profile within two
samples. At least one qualified displacement must reach four samples; a stretch
can cross zero at the centre and still move its ends. Two adjacent
same-field seed lines must agree within eight samples at their jointly measured
windows. Shared coherent temporal motion does not establish ownership.

Boundary evidence is independent: a sustained four-sample run above VI+8,
a 40-sample inside median above VI+20, and an exterior median within three
codes of that field's VI blank. A window-censored edge supplies an inequality,
never retime certification. Each side has its own median/p90-deviation reference
from field rows 40..219. A departure must exceed both three samples and the
measured spread. Missing edges remain unknown. Current counterpart evidence can
seed repair after a missing temporal reference; temporal evidence alone needs
a quiet counterpart. An established band extends through adjacent displaced
boundaries, but not stable boundaries or counterpart displacement.
Field-1 lines >=255 and field-2 lines >=518 remain excluded.

Retiming conservatively requires all six qualified offsets to agree with one
offset within two samples and both uncensored edges to return to their normal
edges within their respective spreads. Otherwise repair interpolates the full
line. Immutable opposite-field neighbours supply ELA donors (directions
0,+/-1,+/-2,+/-3, three-luma-sample stencil, vertical wins ties). One trustworthy
donor duplicates; none leaves the row unchanged as unavailable. Both accepted
repair masks and recognised displaced boundaries exclude donors. Vacated
retime samples also come from donors, never blank fill. Odd shifts resample
U and V independently at half phase.

All buffers are allocated at open. Previous repaired luma is keyed by field
source counter, epoch and storage row, not a changing output crop. Nonadjacency,
resets and pairing changes invalidate it. Recognised displaced rows that were
not repaired are not retained as clean references. This cannot guarantee that
an entirely unrecognised defect never enters history; independent current
boundary/counterpart evidence is the recovery path. No added lookahead.
Reversed pairing uses current-unit f1 and pending-unit f2 without modifying
the geometry engine's retained raw raster.

On uses schema 33. Existing decision cells retain their meaning; only
`schema_version` changes among schema-28 cells. Repair counts, first/last NTSC
lines and per-line `R/I/U/C` tokens remain. C now means a recognised displaced
boundary without an accepted repair, not established content or harmlessness.
Added `hretime_offsets_f1/f2` record every aperture line as
`NTSC:t0|t1|t2|t3|t4|t5/x0|x1|x2|x3|x4|x5`: temporal and counterpart offsets.
`?` means no qualified comparison (flat, failed alignment, missing reference
or excluded row), not zero. Counts and offset lists are frame-owned: field 1
belongs to `frame_top_unit`; field 2 to the row counter. No-frame rows have
empty repair cells. On-mode schema changes do not affect off-mode byte identity.

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
