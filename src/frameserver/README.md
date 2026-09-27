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

## Optional horizontal retiming

`fs_config.hretime` defaults to zero. Tools accept `FS_HRETIME=0|1`; the library
does not read the environment. Off retains schema 28 and performs no repair
analysis. This is a per-tape presentation option, not a new registration input.
Raw capture, classifier, geometry, offsets, vote and comb decisions are unchanged.

The detector runs on the actual published 720x480 pair. Each luma row is compared
with its woven neighbours' mean at every integer shift -147..147. The bound is
the owner-specified NTSC horizontal blanking interval (10.9 us at 13.5 MHz).
Every candidate uses the **same** reference samples [147,573), 426 samples;
shifted reads remain within [0,720). No candidate gets a shorter/easier support.
This is an estimate within the search range, not proof that larger damage is
absent or recoverable. The edge/width/loss tests below decide whether to shift.
An exact integral-sum lower bound prunes impossible winners; every survivor gets
a full-resolution SAD using prepared doubled luma and fused NEON accumulation.
Comparisons use exact integer SAD sums, and ties choose the
lowest shift even though near-zero candidates are visited first. There is no
decimated finalist heuristic. A nonzero winner with SAD ratio <0.8 marks a discontinuity.
The ratio retains the reference's 1e-6 denominator floor at zero SAD; ties in
owner strength abstain, including uniformly blank frames.
Contiguous discontinuities form a band; the strongest qualifying same-field
boundary break assigns its owner. Equal qualifying strengths abstain.

If neither field passes a boundary test, a band touching either field's first
published row (woven start 0 or 1) can use the owner's symmetric edge test.
Each field's unflagged body rows 40..219 supply median left/right midpoint edges
and separate p90 absolute edge deviations. Boundary-owned flags are resolved
first; the unresolved top band is also excluded from its own reference. Missing
edge support abstains. Censored observed coordinates participate in this edge
test, unlike the uncensored widths required for retiming. A band line counts
once when either edge moves in **either direction** beyond its own spread.
The field with more displaced lines owns the band; equal counts abstain.
No minimum spread or single-line-band filter is added. This fallback never
overrides a qualifying boundary owner or equal qualifying boundary strengths.
The ratio/band rules are entry 57; fixed support and symmetric top ownership
are the owner's task31 amendment, not newly fitted detection thresholds.
Each field-1 line >=255 and field-2 line >=518 is excluded from repair, including
the end of a band crossing the cutoff. Detected damage there is not a donor.

An owned picture band grows upward/downward through adjacent same-field rows
whose edges pass that same symmetric displacement test, even if their shift
ratio does not pass 0.8. Growth stops at the first non-displaced or unmeasurable
row, aperture boundary or switch cutoff. The edge reference is frozen before
growth; it is not refitted repeatedly. Switch-only seeds cannot grow into the
picture. Overlapping grown intervals of the same field merge. A shared donor
that becomes flagged is unavailable, never used to repair another line.

For a flagged line, picture edges cross the midpoint between its VI median
(full-width storage rows 7..15 or 270..278) and its own [60,660) median.
Unflagged, uncensored own-field aperture rows 40..219 provide median width and
the 90th percentile absolute width deviation. Missing picture or usable width
support means interpolation, not a guessed shift. Width is right minus left;
no extra amplitude bar or minimum tolerance is imposed. A retime also needs
both measured edges, shifted back by the detected amount, to lie within their
normal median edges' respective p90 spreads. Censored line or median edges
(0 or >=718) cannot certify a retime: unknown width means interpolation. The
existing shift-induced picture-loss allowance remains an additional check,
not a replacement for measuring both edges.

Before either available repair is applied, neighbour/shape confirmation
checks that line against the immutable woven rows immediately above and below,
using each row's own field VI median. **Only for this confirmation**, the body
median must be strictly above VI blank +20; otherwise the midpoint edge is
treated as noise-dominated and unavailable. This reuses the flagging work's
picture-level definition, not a replacement threshold for the edge/width
references or retime certification. Left edges at 0 and right edges >=718 are
unmeasurable, independently for each side of the candidate and its neighbours.
On either side, the line must be beyond every measurable neighbour in the SAME
direction, by strictly more than its field's existing p90 edge spread. A line
between its neighbours is not an excursion. One measurable neighbour decides
alone; none provides no evidence.

Ordered shape must also confirm the displacement: double-precision Pearson
correlation over [147,573) must be lower than the neighbours' mutual correlation
before shifting, and at least as high after the detected shift (bounded +/-147).
The reference is the mean of the two raw woven neighbours. At row 0 it is row 1,
with mutual correlation of rows 1/3; at row 479 it is row 478, with rows 478/476.
Zero variance gives correlation zero. No added correlation threshold is used.
If either the edge excursion or ordered-shape comparisons fail, the
candidate is left untouched as content/agree. Detection, ownership, frozen
references and the original flagged donor mask do not change: a withheld
candidate never becomes a new donor. Original unavailable repairs stay
unavailable. This intentionally misses some small displacements inside the
frame's edge spread; no special-case recovery is applied.

An admissible line is shifted by the detected amount. Vacated luma and chroma
retain opposite-field interpolation, never blanking fill. Odd shifts interpolate
chroma at half phase, rather than corrupting UYVY phase or rounding the luma
shift. Otherwise the whole line uses a small ELA interpolator, averaging
opposite-field neighbours along the best of seven directions (0, +/-1, +/-2, +/-3), comparing
three luma samples and preferring vertical on ties. This bounded local stencil
is not NNEDI3 and makes no claim to recover missing detail. One available donor
is duplicated; no unflagged donor leaves the line unchanged and explicitly
unavailable. All donors are immutable raw rows, never earlier repairs.

The workspace and two unit copies are allocated at open. Reversed pairing
repairs current-unit f1 with pending-unit f2; repaired f1 is retained until its
own transport unit publishes. No additional lookahead or frame allocation is
introduced. Orphan boundaries have no fictitious repair partner.

On uses schema 32 (31 added symmetric edge evidence; 29 belonged to the reverted
head-switch experiment, 30 to the earlier H-retiming search). Only
`schema_version` changes among old cells. New columns are `fs_hretime` and,
for each `f1`/`f2`, `hretime_bands_*`, `hretime_retimed_*`,
`hretime_interpolated_*`, `hretime_unavailable_*`, `hretime_first_*`,
`hretime_last_*`, `hretime_lines_*`, followed by `hretime_edges_f1/f2` and
`hretime_content_f1/f2`.
Line lists contain space-separated
`NTSC:R`, `NTSC:I`, `NTSC:U` or `NTSC:C` tokens. C means an available candidate
withheld by neighbour/shape confirmation (agreement or insufficient evidence),
not a repaired row. Band counts still describe detection, not confirmed repairs.
First/last cover actual R/I repairs only;
zero means none. Empty cells mean no complete frame to assess. These are
frame-owned observations: f1 belongs to `frame_top_unit`, f2 to the row's own
counter. A publisher failure remains unpublished even if repair was computed.
Edge lists have one token for each action, `NTSC:directions`: `L-`/`L+` and
`R-`/`R+` mean an earlier/later left or right edge beyond that edge's own spread.
Both sides may be present, e.g. `291:L-R-`; `=` means within spread and `?`
means edges/reference unavailable. Thus inward and outward bends remain
separately auditable. These columns are absent with the option off.

The old narrow-search reference's displayed coordinates already include +4
(NTSC), and its printed list shows only the first three bands per field. Its
bands are a comparison baseline, not a reference for the fixed-support search.
Tests compare the new search to an exhaustive scalar oracle, including ties,
range endpoints and captured row triples. Synthetic tests also cover width
change, edge certification, interpolated vacated samples, band extension/merging,
switch-only seeds, censoring, symmetric edge directions/strict spread/ties/missing
support, confirmation-only eligibility/strict comparisons/one-neighbour cases,
mirrored field ownership, blank input, UYVY phase and actual
reversed-pair publication. Wider searches also admit more unlabelled bands;
passing named labels is not a quality guarantee for those repairs.

Measured limits remain. Fixed support and symmetric top ownership restored
cap4 232's f2 lines 291..294 after the overlap-search ownership failure. Task32
edge growth repairs cap4 204's f2 line 288 by interpolation without changing its
shift ratio 0.837803 or the 0.8 cutoff. Edge certification changes cap1 6805's f1
line 228 from retiming to interpolation: full-row neighbour MAD 6.910->2.908.
Labels remain 26/26 on cap3 and 42/42 on the corrected cap4 set; the two named
known-clean mirrors remain unflagged. Neither label hits nor more repairs
establish that every repaired row is damaged.

Across captures 1..4, strict worse-MAD rows decrease from 213 in task31 to 49,
all retimes; no interpolated row worsens against the same raw-neighbour mean.
This instrument is not a visual quality verdict. Growing both fields' repair
masks also leaves 83 flagged rows without a clean donor; they remain unchanged
and are explicitly unavailable. Cap1 programme bands are 448 single-line and 115
multi-line (task31: 498/76); multi-line flags increased. Whole-tape bands expand
from 10,879 in the +/-24 build to 78,496, with 17,712 unavailable rows. These
unreviewed flags are not all established damage. No single-line filter,
MAD gate, default change or promotion is implied. Owner/counterpart panel review
remains necessary. Detailed experiment row lists stay in the ignored working
ledger and scratch, not the committed source tree.

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
