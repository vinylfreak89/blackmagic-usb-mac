# v11 geometry engine

`geometry_engine.c` ports the recorded experiment rule set (ledger entries
2/5/7/10/11, amendments 1–5, reading B). It does not replace v9's API.
The census thresholds, run-in period, bottom-profile tests, search range and
1.5 inclusive comb margin are reference parameters, not new fitted thresholds.

All decisions use NTSC lines; zero in an internal census means unavailable.
Applied offsets are always numeric. Unknown placement takes the last published
placement in the section, or zero at section start. Confidence is LOW when a
comb re-run is required, HIGH otherwise; it is not a probability of correctness.

The caller owns bounded storage (`ge_size`), initializes once, and submits
720×525 luma rasters. Nothing allocates during measurement or state updates.
Aligned pairing emits immediately. Reversed pairing buffers one unit and emits
unit-keyed placements: field 1 belongs to the preceding frame, field 2 to the
current frame. Unused boundary fields use their own census placement, or zero.
EOF/gaps flush them explicitly; they are not measured woven frames.

`reset` on a unit clears both fields' previous-unit comparisons and the held,
provisional and published-placement state before the first frame containing it.
In reversed pairing this is the preceding frame, not a second reset at the next
frame. Counter gaps break adjacency. Call `ge_break` on epoch changes, missing
rasters or transport loss; it completes any pending boundary unit and clears all
history. Live classifier action dispatch belongs to the frameserver caller.

The entry-27a prototype binds a held correction to the two census tops of the woven frame that
derived it. If either changes (including becoming unavailable), discard the held
correction and its provisional confirmation before forming a new placement, and
request a fresh comb search. An abstention leaves the correction cleared. A
decided search with known tops records a new basis, including a zero correction.
This basis is frame-owned under both pairings and is cleared by every existing
reset. Missing-placement fallback is unchanged. Entry 27b's untriggered comb
override is **not** implemented: audit still never changes decisions.
This prototype is not acceptance-approved: its whole-tape comparison fixes the
worked case but fails the owner's non-degradation gate in the high-margin bands.
Do not treat recovery of the worked case as approval of the changed trajectory.

Comb arithmetic uses exact integer product accumulation and a float32 mean,
then double precision for the ratio. NumPy's float32 reduction can round the
sum differently. Acceptance requires identical shift/decided, relative margin
error ≤1e-4, and explicit reporting of values within 1e-4 of the decision boundary.
No fast-math option is used. A separate audit flag runs comb on every frame for
validation; ordinary operation runs it only on the recorded triggers.

## Validation

`make geometry-test` runs synthetic shift, missing-evidence, pairing and gap
controls and builds `tests/geometry_probe`. The probe reads external luma and
metadata without importing reference code. From the repository root:

```
python3 scripts/check_geometry_goldens.py CACHE GOLDENS SCRATCH
```

The comparator independently derives reset flags from the saved classifier
stream and compares every eligible unit, frame, comb verdict and intermediate
feature in the external goldens. It prints every mismatch and exits nonzero on
any difference. Timing uses the calling thread's CPU clock. The audit-mode
engine cost includes an all-frame comb; production-only timing is separate.
Neither captured data nor generated results belong in this directory.

## Frameserver integration

Select `frameserver_replay --geometry-v11`; add `--pair-next` for reversed pairing.
Without this selection the existing v9 path and schema are unchanged. v11 writes
schema 15, including applied offsets, trigger bits (T1=1, unmeasurable=2,
field-1 change=4, field-2 change=8, confirmation=16, correction-basis change=32),
comb evidence and HIGH/LOW.
Untriggered comb evidence is empty unless `--audit-comb` is set; that switch does
not change decisions. Frame diagnostic columns refer to the bottom-field unit,
whereas `applied_d1/d2` always refer to the row's own unit. Ineligible observations
have empty placement keys, with their original counter in `observed_counter`.
`comb_energies` appends eleven space-separated values in shift order -5..+5,
formatted with nine significant digits (the energies are float32-rounded).
It is present exactly when the comb was computed, including audit-only searches;
otherwise it is empty. Zero minima give margin infinity if the second minimum
is positive, or margin 1 if both are zero. `comb_ran` still denotes a trigger,
not an audit-only computation. Existing columns retain their meanings.
Within the same row, the published relative shift is `frame_d2 - frame_d1`;
compare it to `comb_d`, with `comb_decided` indicating whether the minimum was
decisive. This requires no cross-unit join even under reversed pairing.

The top search uses the per-field horizontal-blanking level of experiment 20:
over storage rows 18..261 (+263 for field 2), keep column 0 and then columns
1..23 while each median is at most `median(col0) + max(p90(col0)-median(col0),1)`.
The level is p99 of the pooled kept samples, using the existing interpolated
quantile. Only the top brightness bar changes to `p95(row) > level`; spread,
correlation, plain23/run-in logic, device blanking, bottom search and bottom
profiles retain their existing rules. Noisy leading columns can inflate the
level; this known limitation is deliberately retained for review, not repaired.
The required `spread > 4` guard remains. Acceptance uses the corrected
`expected_tops.csv`, which retains that guard; the original experiment-20
`hblank.py` omitted it and rounded levels to one decimal. Compare levels with
floating-point tolerance, not equality of differently formatted decimal strings.

`tests/hblank_probe` accepts a streaming luma record (uint64 counter, uint32
reset, uint32 reversed-pairing flag, then 525×720 luma bytes) and reports census
features and thread-CPU costs. An optional output path enables a separate
all-frame-audit engine's frame CSV. The measured engine stays non-audit; frame
agreement uses `frame_d2 - frame_d1`, never the two unit-owned placements.
Feed old and new builds the same rasters, pairing schedule and live reset flags,
and verify the old frame output against the published log before comparing rates.
Exact census agreement does not establish preserved placement quality: separately
compare published frame shifts with decided comb minima at margins 1.5, 3, 5 and 8.
A regression in that gate needs owner review; do not alter the specified census
rule to make the acceptance numbers fit.

Beside the existing bottom-line coordinates `bl1`/`bl2`, schema 15 adds
`hblank_level_f1`, `hblank_cols_f1`, `hblank_level_f2`, `hblank_cols_f2`.
These describe the row's **own unit**, including unused boundary fields; they
are empty for ineligible observations. Under reversed pairing, the frame's
field-1 provenance is found on `frame_top_unit`, like its applied placement.

For mixed recordings use `--pairing-schedule FILE` instead of `--pair-next`
(`fs_config.pairing_schedule` for callers). The CSV header is
`first_counter,pairing,note`; pairing is `aligned` or `reversed`. Counters are
unsigned extended counters in strictly increasing order. The first row must
start at zero, making the setting defined before any delivered unit. At each
unit the last row whose counter is no greater than that unit's counter applies.
The file is validated and copied at `fs_open`; later file edits cannot affect a
running session. Malformed CSV, duplicate/unsorted counters, unknown pairings,
more than 65,536 rows or fields longer than 4,096 bytes are errors, not truncation.

A pairing change completes any old reversed boundary unit, then clears the
whole geometry state before the switch unit. A note-only change does not reset.
Every v11 log row includes `pairing` and an always-quoted `pairing_note` (CSV
escaping preserves commas, quotes and newlines). Delayed rows use their own
unit's note; counterless hole/tail rows use the active setting. Without a schedule
the note is empty. The applied-offset columns keep their renderer contract.
Pairing remains supplied configuration, not a live detector.

Unit-keyed rows also carry `audio_residual_ticks` (video minus audio time at that
unit's own resync, in 1/240000 s) and `audio_step_samples`. Both cells are empty
if correlation is unavailable; observation-only rows without a placement key
also leave them empty. Correlations are bounded, race-free publisher snapshots;
a resync not yet delivered or no longer in history is unknown, not estimated.
Known residuals are compared to the previous known unit in the same audio run.
Only an absolute difference **greater than 6 ticks** exceeds the two ±3-tick
quantization envelopes. Convert that difference to the nearest signed sample
(5 ticks/sample); positive means audio time needs advancing. Other known rows
carry step zero. Missing resyncs do not reset the comparison. Audio re-anchors
(hole/unframed/epoch changes) seed a new baseline; geometry resets, pairing
changes and sidecar attachment do not reset it. Initial residual is a baseline,
not an instruction to insert startup silence. A run crossing unavailable units
can locate a step only at the next known unit, not within the unobserved span.

These are metadata only: neither PCM, publisher timestamps nor geometry changes.
The audio sink distinguishes `AP_FLAG_DROPPED_BEFORE` (downstream queue loss)
from `AP_FLAG_DISCONTINUITY_BEFORE` (publisher run break). Both may be set if a
run break occurred in dropped blocks. The next delivered block preserves that
break; queue loss alone does not reset an adapter's residual correction.
An A/V review adapter may insert explicitly flagged silence for device deficits,
as §6 specifies, without resampling or modifying the archival PCM. Negative steps
are reported too; their downstream handling is not decided by this logger.
`make -C src/frameserver test-audio-steps` checks quantization, missing resyncs,
signed steps, own-unit identity under both pairings, and unchanged PCM/timestamps.

The classifier's DISCONTINUITY and BEGIN_SEGMENT actions are accumulated until
the next eligible raster. The engine additionally breaks on counter gaps; the
caller breaks on epoch changes, parser counter-discontinuity flags, ineligible
rasters and explicit pool/ring loss. Counter flags matter because the parser may
extend a repeated/backward raw counter by +1; numeric adjacency is insufficient.
Analysis and log writes run on the processing worker, never the transport callback.
v11 does not feed its two-valued confidence into v9's phase-settlement heuristic;
classifier reset actions therefore follow the same independent stream as the oracle.

The frameserver remains a transport-unit publisher, including for reversed pairing.
It buffers one extra complete unit so each published unit has both of its final
own-field placements; a consumer weaving reversed material still needs the same
pairing parameter. EOF/gaps complete the unused boundary fields explicitly.
The reviewed renderer consumes these unit-keyed rows through `--engine-log`.

v11 publication preserves the requested offset. Each field reads only its own
storage rows (field 1: 0–261; field 2: 262–524). A crop beyond those bounds
fills only unavailable rows with Y16/C128, matching the renderer, and exposes their
count as `fp_frame.unavailable_rows`. The legacy publisher's whole-crop clamp remains
for v9. Clamping a v11 crop would make the pixels disagree with the recorded offset.

For live validation pass `--live-dir SCRATCH` to the golden comparator, with
`cap1_live.csv` … `cap4_live.csv` produced by the real replay. Use paced replay;
any downstream loss is a real discontinuity, not an excuse to omit mismatches.

`make -C src/frameserver test-geometry` checks the real path on both synthetic
fixtures, for both pairings. `test-geometry-asan` and `test-geometry-tsan` exercise
the same new path with instrumentation. The test reserves the whole fixture's
possible raster population; a correctness assertion must not race sanitizer
throughput. Existing frameserver tests separately force pressure and verify loss.
`scripts/check_geometry_render.py GOLDEN_FRAMES.csv RENDER.mp4` decodes every
machine strip from the actual review encode and checks its counter and offsets.

`make -C src/frameserver test-pairing` checks both switch directions against fresh
runs, old/new boundary handling, note-only invariance, CSV round trips and input
rejection. The geometry sanitizer targets also run these schedule tests. For
capture acceptance, produce the usual `capN_live.csv` with a one-row schedule
and use the unchanged golden comparator above.
