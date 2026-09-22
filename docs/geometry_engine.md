# v11 geometry engine

`geometry_engine.c` implements entry 33's waveform top census with the retained
bottom, pairing and reading-B decision path (entries 2/5/7/10/11 and 27a).
It does not replace v9's API. The default bar 0.45 was selected from eleven
hand-checked frames, not derived from a distribution; census reproduction is
implementation validation, not proof of placement quality.

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
schema 21, including applied offsets, trigger bits (T1=1, unmeasurable=2,
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

Schema 21 replaces the old top-search controls with `ge_wave_bar` and
`ge_wave_clamp`. The waveform scan was introduced separately in 77a8eaa and
matched all 172,586 raw tops/abstentions before the old guards were deleted.
No amplitude, spread, lag correlation, chunk agreement, plain23 re-search or
run-in increment remains in the TOP path. The BOTTOM path retains exactly its
old p95-minus-device-blank >5 and spread >4 tests, and its profiles are unchanged.

## Waveform census (entry 33)

For each field, Pearson correlation compares consecutive rows over body samples
40..679. Search storage rows 18..36, plus 263 for field 2, each against the row
above. Starting with row 19, the FIRST rise in correlation strictly greater than
`ge_wave_bar` (default 0.45) selects the preceding row as top. Correlations
with either population standard deviation below 1e-9 are zero. No smoothing,
accumulation or largest-step selection. The maximum step is evidence only.

Raw results are immutable. No qualifying step is ABSTAIN. A result more than
`ge_wave_clamp` (default 5) lines from NTSC23/286 is DISCARDED, independently
for each field; it is never rounded to the clamp boundary. ACCEPTED raw results
become the census first lines. Both absent and discarded census trigger the
existing comb check; a decided comb (margin >=1.5) supplies relative alignment,
not an absolute top measurement.

Missing-placement policy remains explicit: `relative_source` is census,
held_correction, comb, previous, or section_start; `anchor_source` is census,
previous, or section_start. The comb cannot establish an absolute field-2
anchor if that census is missing. Existing previous-placement/zero fallback is
marked as such and does not manufacture a first-line observation. This is not
a general fade-freeze policy.

Schema 21 retains schema 20's first 39 columns, through `comb_energies`, with
their existing meanings; it removes the four `ge_top_*` arm columns and appends:

```text
ge_wave_bar,ge_wave_clamp,wave_top_f1,wave_step_f1,wave_max_step_f1,wave_status_f1,wave_top_f2,wave_step_f2,wave_max_step_f2,wave_status_f2,relative_source,anchor_source,held_correction
```

Exactly 52 columns. The eight `wave_*` columns describe the row's OWN unit,
including unused boundary fields. The raw top is empty with status ABSTAIN,
selected step 0 and the measured maximum. Discarded raw tops and their selected
steps remain numeric. Ineligible observations have no waveform evidence.
Under reversed pairing read field-1 waveform evidence on `frame_top_unit`.
By contrast, `f1_first/f2_first`, last lines, classes, comb, held correction,
publication sources and `frame_d1/d2` describe the FRAME whose bottom field is
this unit. `f*_first` is the accepted census, empty on abstention or discard.
Numeric published offsets are not a declaration of measured tops.

Horizontal-blanking level/column count remain measured and logged, but no longer
gate the top. `hblank_level_f1/hblank_cols_f1/hblank_level_f2/hblank_cols_f2`
are unit-owned, including boundaries. Device blanking and bottom profiles remain
unchanged. `bl1/bl2` are frame-owned bottom coordinates, not blanking levels.

Tools alone read `GE_WAVE_BAR` (finite double) and `GE_WAVE_CLAMP`
(nonnegative int), through the shared `geometry_tool_controls.h` parser.
The engine exposes the two process-wide variables, configured before worker
startup; it never reads the environment. Retired `GE_TOP_*` controls are refused
loudly so an old command cannot silently run a different experiment.
Replay echoes the settings on stderr and writes them on every sidecar row.
Both `hblank_probe` CSVs start with a
`# GE_WAVE_BAR=... GE_WAVE_CLAMP=...` comment before the header.
Its raw waveform columns include status before policy and its `f*_first`
columns are accepted after policy. Costs use thread CPU time; the audit engine
is separate from the timed production engine.

`scripts/check_waveform_census.py reference.csv engine.csv disagreements.csv`
compares every raw top or abstention, including missing/extra/duplicate keys.
It does not exclude clamp discards. The tape exercises only raw offsets 0..16;
the negative half of the symmetric clamp has synthetic coverage only.

The review renderer imports no census instrument. Its overlays read raw
waveform/status and accepted frame census from the engine sidecar with the
ownership above. Missing answers remain missing. It also displays the engine's
comb energies, selected shift, decision, trigger and publication sources.
Captures 1–4 are staged outside synced storage and validated before replacing
the owner's scratch review files; a full-tape render still requires his approval.

Review publication must also name its producer revisions. Before starting a run,
use `scripts/geometry_review_status.py DIRECTORY --engine-commit ENGINE_SHA
--renderer-commit RENDERER_SHA --begin`. After publishing all four MP4/sidecar
pairs, run the same command without `--begin`. It atomically writes
`renders.status`: IN_PROGRESS/VALIDATING is not a claim about the old files;
READY records decoded frame counts, boundary units, placement checks, settings
and hashes. A failed check leaves FAILED, not the previous run's READY status.
The supplied revisions identify the builds actually used, not the checker HEAD.
READY does not mean the owner has visually accepted the renders.

Published units and paired frames have different denominators. In capture 3,
649 units (13501..14149) yield 648 reversed-pair frames (13501..14148).
Unit 14149's field 1 appears in frame 14148; its field 2 has no next-unit partner
and is logged f2_unused=1, with no frame_top_unit. The renderer omits that tail
frame key, not an interior frame. Do not edit the unit sidecar to force equal
counts, and do not describe all 649 units as complete woven frames.

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
