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

## Optional horizontal retiming (other-field blanking)

`fs_config.hretime` remains OFF by default; tools map `FS_HRETIME`.
OBS's existing setting is unchanged. OFF retains schema28 and does no repair
analysis. Actual woven source ownership and published placements are used;
nothing feeds geometry, classifier, comb or vote. No history is kept and
nothing is allocated per frame.

The timing reference is the sharp blanking falloff at each side of the
picture, compared with the OTHER field at that moment, like a line TBC.
Both fields of a frame share one blanking position (measured within 0.3
samples on pan, tape1 and capture 4), so each frame has one standard per side:
the median half-height falloff of its lines that have picture there; a first
pass uses the first rise 20 codes above blanking, and with fewer than 20
measured lines there is no standard and no detection that frame.
Eligible rows carry picture (five VI-noise sigmas), exclude the device
inserts NTSC20/21 and283/284, and exclude switch rows f1>=255/f2>=518.

Per side, a line's picture level is the 10-sample median 4..13 samples
inside the standard. At or above 40 codes over blanking (black with setup is
~16) the line's own half-height crossing is its falloff. Below that the side
is near blanking: it gives evidence only when both woven other-field
neighbours have picture there, measured at their half-height. Picture already
at the window edge is spill; sample 719 is the window's attenuated last
sample and never picture, and right spill is window-limited (1-3 samples of
blanking on some tapes), so only an inward right falloff is evidence.

A side is evidence when its falloff is sharp (20-80% rise within 8 samples),
departs from the standard by more than a few (4) samples, and disagrees by
more than 4 with every measured other-field neighbour. A timing error moves
the whole line, so the other side must agree: a measured other side departs
the same way by more than 4 and within 4 of the same shift, or the picture
spilled past the right window on a move right. A measured side within 4 of
the standard vetoes (content or one-sided jitter). No left blanking where the
other field has it is garbage and needs no confirmation. With the other side near blanking, the whole
waveform shifted by the edge's departure must match the neighbours better than
unshifted and pass the agreement bar below. A lone detected line is a dropout
or little one-line shift: a detection needs a detected own-field neighbour.

Per field, every eligible line from the first to the last detection is
repaired. The reference is the two nearest undetected other-field lines (up
to seven rows away), preferring lines outside that field's own range. The
shift is the left falloff's offset from the reference's (the right's if the
left is spilled or unmeasured; a two-sided width disagreement beyond 4
interpolates; no blanking on either side interpolates; no left blanking with
the right too dark to measure searches leftward shifts of 5..147 for the best
waveform match to the reference, subject to the agreement bar).
A line with no usable falloff is near blanking here and in the other field
and is left alone (C), as is a shift within 4. Otherwise the shifted waveform must agree with the
reference: 1-r at most 4x the reference lines' own 1-r (correct retimes of
bends measured 1.0-3.2x; a 3-sample misalignment ~15x) and better than
unshifted; a line agreeing as well unshifted is C. With only one reference
line there is no bar, and the line interpolates. Agreement retimes (R);
failure interpolates (I, ELA from undetected eligible other-field rows within
seven rows; none leaves the line unchanged, U). A retime's
vacated columns and the window's first/last samples come from that
interpolation, so up to half the line may run out of the window before the
agreement measure itself is undefined.

ON schema36 keeps geometry cells unchanged except schema_version. R/I/U/C
tokens and counts remain. hretime_edges_f1/f2 give each range line's
departure directions against the standard ('=' known and within limits, '?' unmeasured).
hretime_evidence_f1/f2: NTSC:reason/agreement/bar/shift. Reason bits: 1
agreement failed, 2 no blanking (spill) on a side, 4 detected, 8 width
break, 16 in range but not itself detected. hretime_normal_f1/f2 carry
nan, the frame standard left/right and the few-sample limit twice;
hretime_typical_band is 0. Field1 belongs to frame_top_unit, field2 to the
row counter.

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
