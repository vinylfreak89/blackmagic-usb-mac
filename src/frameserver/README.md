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

## Optional horizontal retiming (two-test experiment)

`fs_config.hretime` remains OFF by default; tools map `FS_HRETIME`.
OBS's existing setting is unchanged. OFF retains schema28 and does no repair
analysis. Actual woven source ownership and published placements are used;
nothing feeds geometry, classifier, comb or vote.

This replaces E62 windows, uniqueness, temporal alignment and seed branches.
Full ordered 720-sample luma Pearson is maximised over shifts -2..2 (one chroma
period), with endpoint extension and identical support. A line's better match
to either woven neighbour is compared with those neighbours' mutual unshifted
correlation. At the first/last row the two available same-field neighbours
supply the mutual reference. Undefined Pearson provides no waveform evidence.

Only picture-carrying rows are eligible: at least one luma sample must exceed
that field's VI blank by the existing five-noise-sigma contrast margin.
Device inserts NTSC20/21 and283/284 are always excluded. A blank row is not
garbage edge blanking. Line22/285 is tested, not categorically excluded, since
its deck-generated content varies. Ineligible rows cannot enter a bridged band
or supply learned clean-edge statistics/expected-width references.
The shape test measures half-height edges. Picture occupying the learned
exterior blanking span detects spill and requests I. A failed crossing alone
is unknown measurement, not proof that blanking is missing.
Otherwise BOTH a departure outside normal edge variation AND the learned
correlation deficit are required. Either side may depart independently:
stretch/compression need not move both edges or move them equally.
A side does not supply displacement evidence when every available opposite-field
woven neighbour shows the same dark/flat content in the displaced interval.
That interval contains integer samples between the measured and normal crossing.
Dark means mean at/below the neighbour's local step midpoint; flat means standard
deviation within five VI-noise sigmas. There is no requirement that neighbouring
levels agree with this line: field-to-field content motion must not defeat
the dark/flat explanation. This reuses the locator's noise allowance;
it is not a guarantee of distinguishing dark content from blanking. With no
available neighbour, no content explanation is established. Correlation alone
never detects. Interior
blanking uses five VI-noise sigmas and a
minimum length equal to the larger learned exterior blanking width. It remains
an observation only unless edge blanking is missing/garbage: floor-crushed black
inside an otherwise ordinary picture must not trigger repair by itself.

Each field retains30 clean-frame summaries (roughly one NTSC second), including
actual edge samples. Body rows40..219 supply these. Cold start uses current body rows with
finite edges/correlations; subsequent updates admit only rows passing both
tests. Correlation deficit limit is unchanged: median plus five robust sigmas.
Normal edges are pooled clean-edge medians; each side's allowance is the99th
percentile absolute departure from that median, with no multiplier or sample
floor. This gives up small departures in the real content-dependent tail,
instead of extrapolating a Gaussian from MAD. Resets, epoch changes and counter gaps clear history.
A broadly damaged initial body can contaminate bootstrap; no label-specific
fallback or concealed clean-reference assumption repairs that limitation.

Bands are contiguous own-field flags, including singletons. Between successive
direct detections, every eligible picture row joins when their inclusive
own-field span fits the past90th-percentile directly detected run length.
The existing30-run tape-level ring supplies this upper-typical extent, shared
across fields. Only pre-fill runs train it, and the current frame cannot change
its own allowance. Cold start/reset has no history: no gap filling yet.
Missing/non-picture rows and excluded switch rows are barriers. Edge sign,
profile and measurability do not gate filling; the existing width rule decides
each joined row's action. There is no extrapolation beyond either bound.
Nearby detections can chain into a longer band; every final band is logged.
Switch rows f1>=255/f2>=518 remain excluded.

Repair uses the existing half-height instrument: left local picture median
26..35, right maximum696..705, crossing search147 samples from either border.
Contrast exceeds five noise sigmas. Exterior support is floor(left normal)
or floor(719-right normal), clipped0..147, from the same clean-edge history.
Cold start first measures with VI alone to bootstrap the existing body normal.
Only contiguous outer samples within five VI-noise sigmas, up to that learned
support, supply the local plateau median/MAD. A rolloff outside this envelope
cannot inflate plateau noise. With none, retain VI. Noise is1.4826*MAD with
quantisation floor1/sqrt(12). All samples of a nonempty learned exterior span
above half-height establish spill; zero support supplies no such witness.
A side supplies displacement evidence only when its exterior sample count
exceeds its crossing uncertainty max(1,sigma/slope). One exterior sample can
establish blanking presence/spill, but not independently resolve displacement.
Finite narrow-side crossings remain usable for the width rule. Unknown width
still selects I, not R, when another measurement detects the line.

Expected width is interpolated between nearest undetected measurable
same-field rows outside the entire final band (including its zero-action
rows). Search starts above its first row and below its last, never inside it.
One available side supplies both endpoints; with neither, use the learned
same-field normal edges, not the opposite field. If no finite normal exists,
width remains unavailable and the existing interpolation fallback applies.
Undetected bent rows outside a band's extent can still contaminate a reference;
being outside the band does not itself prove clean timing. Both width error and mean
edge displacement may be as large as the larger expected exterior blanking
width. Within that allowance, round displacement to an integer and retime.
An integer shift within the mean of the two crossing uncertainties
(`max(1,sigma/slope)` per edge) is suppressed as measurement noise.
Zero leaves pixels unchanged (C). Spill, missing width, or larger error uses
whole-line ELA. R needs no donor; it extends its own vacated source samples and
resamples U/V independently for odd shifts. I uses immutable unflagged woven
neighbours, directions0,+/-1..3 and a three-sample stencil; one donor copies.
If both adjacent rows are detected/unavailable, search outward for the nearest
unflagged opposite-field row; equidistant donors may use the same ELA. The
published aperture, not a fixed distance, bounds that search. If none exists,
preserve pixels and report U (no usable opposite-field row), never silently
substitute a flagged donor. No repaired-raster temporal detector remains.

ON schema35 keeps geometry cells unchanged except schema_version. R/I/U/C
tokens, counts and edge directions remain. Old window-offset columns are
replaced by hretime_evidence_f1/f2: NTSC:reason/rLine/rNeighbours/shift.
Reason bits are observations, not necessarily detections:1 correlation,
2 missing/spill,4 blanking size not explained by neighbouring content,
8 interior blank,16 learned-band fill. A row is
detected for2/16 or the conjunction1+4. hretime_normal_f1/f2 carry deficit limit, left/right
normal and their allowances; hretime_typical_band is the past direct-run P90
actually used for filling (zero at cold start).
Field1 belongs to frame_top_unit, field2 to the row counter.

`make tests/hretime_repair_probe` builds a diagnostic real worker with the
geometry_worker_bench CLI. HRT_REPAIR_PREFIX and HRT_REPAIR_CAPTURE select
exclusive scratch outputs. HRT_REPAIR_EXTRA accepts up to two comma-separated
source-counter:field pairs for additional actual source/output pixel dumps;
this observer-only selector does not change repair or registration decisions.
It buffers per-line reasons, widths, correlations,
bands and selected actual source/output pixels until worker join. Capacity is
1024 woven frames; not a full-tape logger. No path allocation or lookahead is
added. This remains a falsifiable experiment, not a validated/default repair.

## Deterministic audio evidence

The former video-worker lookup could exhaust all eight seqlock retries during
an unrelated correlation write even when its target entry already existed.
A condition-handshaked overlap reproduced the empty log cells; this was not
necessarily audio arriving late. The regression test preserves that distinction.

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
