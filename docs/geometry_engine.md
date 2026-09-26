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
schema 28, including applied offsets, trigger bits (T1=1, unmeasurable=2,
field-1 change=4, field-2 change=8, confirmation=16, correction-basis change=32,
still-picture rejection=64),
comb evidence and HIGH/LOW.
Untriggered comb evidence is empty unless `--audit-comb`, the anchor vote, or
the still-picture comb control is enabled; audit does not change decisions.
Frame diagnostic columns refer to the bottom-field unit,
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

## Optional same-unit bottom reference (entry 38)

`GE_BOTTOM_FLAT=1` enables the bottom detector; default is off.
`GE_BOTTOM_FLAT_MARGIN` is finite and positive, default 3. The library reads no
environment variables. F is the body (columns 40..679) of storage row 258/521.
Its p5/p50/p95 use the engine's interpolated histogram quantile. If F's spread
is at most 4, scan upward from 257/520 through 237/500: a row qualifies when
its median or p95 exceeds F's corresponding value by at least M, or its p5
falls below F's p5 by at least M. Comparisons use M minus 1e-9 for inclusive
ties. No qualifying row means unknown, without fallback. A non-flat F uses
the original amplitude/spread test, starting at 259 for field 1 (the input
half-line) and 521 for field 2. Disabled scans retain the original 258/521
start. The 12-row bottom profile and every top measurement are unchanged.

Schema 25 appends `ge_bottom_flat`, `ge_bottom_flat_margin` and, for each N=1,2,
`bottom_rule_fN`, `bottom_F_p5_fN`, `bottom_F_p50_fN`, `bottom_F_p95_fN`.
Rules are `flat_reference`, `fallback`, or `unknown`. Like `fN_last`, these
are frame-owned: field 1 comes from `frame_top_unit`, field 2 from this row's
unit. Non-frame rows leave all evidence empty; with the control off, F is
unmeasured and its quantiles are empty. A found old-rule bottom is `fallback`.

## Experimental blank spots and still-picture comb (entry 39)

`GE_VOTE_BLANKSPOT` and `GE_COMB_STILL` are independent strict 0/1 startup
controls, both off by default. Blank spots can only remove vote confidence:
every skipped field-2 line 286..vote_top_f2-1 must contain a body sample at
or below that unit's full-width VI median plus 2. The empty range passes.
No caption information is read by the engine.

With the motion control enabled, same-field integer SAD over 180x640 samples
selects a vertical shift -5..5 against the previous adjacent non-reset unit.
Exact ties prefer the smallest absolute shift, then the negative shift.
Frame evidence joins field 1 from frame_top_unit and field 2 from its own unit.
Either unknown makes the frame unknown; otherwise any nonzero shift means
moving. `GE_COMB_MOTION_MIN` is a positive integer, default 1. Moving frames
whose largest absolute field shift is at least this value retain the ordinary
triggers and raw comb measurements but cannot adopt, reject, substitute or
update held evidence from that comb. Smaller nonzero shifts keep the existing
comb authority and do not gain a still trigger. The default reproduces entry
39's original moving-frame rule; 99 withholds nothing in the -5..5 search.
Other basis invalidation and top/fallback decisions remain active. A still
frame adds trigger bit 64 when the proposed relative shift's energy ratio is
at least GE_COMB_REJECT and the floor is enclosed. It then uses the unchanged
adoption/rejection path (the latter's own threshold remains strict). The
enabled control guarantees all-frame comb evidence even if the anchor vote
is off, so toggling audit cannot change its decisions. It reuses the one
existing search, never performs a second pass, and leaves disabled scheduling
unchanged. The requested base configuration already has all-frame evidence
through the anchor vote.

Schema 26 appends `ge_vote_blankspot`, `ge_comb_still`, `vote_blankspot_pass`,
`vote_blankspot_line` (first failed line, zero when none), `motion_shift_f1`,
`motion_error_f1`, `motion_error2_f1`, the corresponding f2 columns,
`picture_motion` (unknown/still/moving), `still_trigger`, and `comb_suppressed`.
Suppression counts threshold-qualified moving frames with an existing comb
trigger, including an undecided comb. Schema 27 appends `ge_comb_motion_min`
on every row. Motion errors are best and runner-up mean absolute differences.
Unknown/disabled shifts and errors are empty; all frame evidence is empty on
non-frame rows. These controls are experiments, not enabled production defaults.

`GE_COMB_RIGID` (default 0) replaces the motion-minimum suppression predicate
when `GE_COMB_STILL` is enabled. A field whose vertical |shift| is at least
2 also gets a 2-D SAD search (dy -5..5, dx -8..8), aperture rows 40..219,
body columns 40..678 at step 2. Exact ties take the first dy/dx in scan order.
Clarity is the minimum SAD at least two away in either axis divided by the
best SAD; a zero best with positive far SAD is infinite, two zero SADs give
1 (no distinction). Both frame-owned fields must have dx=0, |dy|>=2 and
clarity >= `GE_COMB_RIGID_CLARITY` (default 1.3, configurable finite >=1).
Still triggering and every other moving frame's comb authority are unchanged.
The rigid control is inert with STILL off; its disabled path adds no search.

Schema 28 appends `ge_comb_rigid`, `ge_comb_rigid_clarity` and each field's
`rigid_dx_f1`, `rigid_dy_f1`, `rigid_sad_f1`, `rigid_sad_far_f1`,
`rigid_clarity_f1` (and f2 equivalents). Measurements are frame-owned, empty
when not run, full-precision doubles. `comb_suppressed` remains the per-frame
withheld verdict; `comb_ran` still means an existing trigger, not adoption.

## Optional anchor vote (entry 36)

For current-worker CPU, use `make -C src/frameserver bench-geometry` with
`CAPTURE`, fresh scratch `SIDECAR` and `TIMINGS` paths, and optional replay
`BENCH_ARGS` (including a pairing schedule). It enables s12c, pairing .6,
flat-bottom, A1, still triggering and rigid withholding at 1.3. Unlike the
legacy v9 `bench` target, it runs the actual configured v11 replay worker,
including conditional 2-D searches. Thread-CPU samples cover classification
through item completion (including logged-row formatting, excluding queue
waits/input I/O). Reports split units by zero, one or two 2-D searches and
time classifier, engine and publisher separately. Timing output is buffered
until the worker joins; source measurements and publication are unchanged.

Three startup controls default to zero: `GE_ANCHOR_VOTE`, `GE_LEVEL_FILL`,
`GE_LEVEL_FLAT`. Replay and the probe share the strict 0/1 parser; the library
never reads the environment. Fill and flat have no effect with vote off; flat
has no effect with fill off. The existing waveform and comb controls are unchanged.

Vote-enabled frames compute comb evidence even without a trigger. `comb_ran`
continues to mean a triggered decision, and neither comb selection nor rejection
acts on an otherwise untriggered search. A frame votes only if both candidate
tops exist and their relative shift lies inside an enclosed comb floor. Its
field-2 offset enters the last-30-confident-frame window. The modal value wins;
ties retain the current anchor, then prefer the newest tied value, then the
first tied value in chronological window order. Non-confident frames add no vote.
All engine resets, gaps, breaks and pairing reinitializations empty this window.
An empty window holds the last published vote anchor, including across resets
and pairing changes. Only before the first frame of a new session does it use
the unchanged engine's final anchor (including its basin-discard fallback).
This display-anchor hold does not retain old votes or relative-decision state.
Use `ge_init` for a new session; after flushing the old pairing with `ge_break`,
use `ge_set_pairing` for a pairing change within the session.

Level fills apply to raw waveform ABSTAIN only, never DISCARDED. The reference
is the median of blank rows 7..15 (+263 in field 2), body columns 40..679.
The first row in 18..36 (+263) whose body mean is strictly above reference+10
is the sole candidate. It must satisfy the existing symmetric `GE_WAVE_CLAMP`
and correlate with the next row above 0.30; optional flat acceptance also permits
population sd below 10. Statistics are unrounded at the thresholds. The Pearson
zero-variance guard is the waveform's existing 1e-9 standard-deviation floor.
Fill candidates belong to the actual source fields under reversed pairing.

Fills never replace the census or enter relative-shift triggers/corrections.
The engine first advances its unchanged, unvoted relative/anchor state, then
publishes `(vote_anchor - d, vote_anchor)`. Keeping the baseline fallback state
separate prevents a voted anchor from feeding later baseline decisions. The
relative shift is therefore unchanged, including on missing-evidence/discard
frames. This is an absolute-anchor vote, not a new relative registration rule.

Schema 23 preserves existing columns and adds three configuration columns
`ge_anchor_vote`, `ge_level_fill`, `ge_level_flat`; frame-owned `vote_confident`,
`vote_anchor`, `vote_engine_anchor`, `vote_count`, `vote_winner_count`,
`vote_top_f1`, `vote_top_f2`; and, per field, `level_top_fN`, `level_ref_fN`,
`level_mean_fN`, `level_sd_fN`, `level_corr_fN`, `level_accepted_fN`. Level columns
are empty when not measured. All frame-owned additions are empty on boundary
or unpublished rows without a frame. Existing `f1_first/f2_first` stay immutable.
`anchor_source=anchor_vote` identifies a voted or empty-window held anchor; the original
engine's final anchor remains explicit in `vote_engine_anchor`.

Entry 37 adds `GE_VOTE_PAIR` (default 0) and `GE_VOTE_PAIR_MIN` (default .6,
finite [-1,1]). With vote and pairing enabled, confidence instead permits
the inclusive floor range `[lo, hi+1]` and also requires rB >= the threshold.
rB is Pearson over body samples 40..679 of the two vote-top rows, each from
its frame-owned source raster. Either population sd below 1e-9 gives zero.
No other vote, fill, census or relative-decision rule changes. Pairing has no
effect with vote off; disabling pairing retains the entry-36 confidence test.
Schema 24 appends `ge_vote_pair`, `ge_vote_pair_min`, `vote_rB`,
`vote_pair_pass`. The latter is only the correlation verdict, not full frame
confidence. Both evidence cells are empty without an enabled two-top
measurement; the configuration appears on every row. rB is logged unrounded
to 17 significant digits; comparisons never use display-rounded numbers.

`geometry_vote` checks threshold boundaries, clamp, first-candidate semantics,
tie handling, window eviction, resets and field ownership. `test_anchor_vote.py`
checks the enabled live paths under both pairings, including audit invariance,
relative-shift identity and inert subordinate controls. Acceptance results and
remaining falsifiers belong in the experiment ledger, not in this API contract.

## Comb rejection (entry 34, two-sided-floor amendment)

Selection is unchanged: the second/best energy ratio must reach 1.5. A separate
strict proposed/best ratio > `GE_COMB_REJECT` (default 2) refuses the proposed
placement on a triggered comb search. Extend the best's floor contiguously
through energies <=1.5 times its minimum. Substitute the best only if that floor
is interior and its two outside neighbours are each >=1.5 times the minimum.
The constant is shared with selection; this is not a second fitted shape bar.
A tied best pair can be an enclosed basin. Touching a search wall establishes
insufficient support, not proof that true alignment lies outside the search.

A refusal clears held correction, provisional confirmation and its census
basis. An unsupported floor discards the proposed geometry and publishes the
previous full pair (both offsets); at a section start it publishes (0,0).
It never drops/repeats the image or changes a measured top. Census fallback was
rejected because it would enact another unsupported placement from the frame
whose proposal was just discarded. The policy is explicit in both source
columns: `discard_previous` / `discard_section_start`; a supported substitution
has relative source `comb_rejection`. Existing future fallback can propagate a
substitution without a new rejection event; those rows must not be relabelled
as fresh refusals. The normal selection path may still choose a boundary best;
the basin test narrows rejection substitution only, not `comb_decided`.

Schema 22 preserves every schema-21 column and appends:
`ge_comb_reject`, `comb_reject_ratio`, `comb_rejected`, `comb_refused_d`,
`comb_substituted_d`, `comb_discarded`, `comb_floor_lo`, `comb_floor_hi`,
`comb_rise_left`, `comb_rise_right`, `comb_basin`.
The ratio concerns the proposal BEFORE rejection; the published pair is still
`frame_d1/frame_d2`. Refused/substituted cells exist only for actual events, and
substituted is empty on a discard. Floor endpoints are shifts, not array indices;
each rise is measured against the minimum, with a missing outside neighbour
logged empty. Floor/rise/ratio evidence can be logged under audit, but audit
alone never acts on it. Unknown search means empty evidence, never guessed zeros.
A proposed shift outside -5..5 has no measured energy and is not rejected by
this instrument (empty ratio). With zero minimum, 0/0 is 1 and positive/0 is
infinity, matching the existing comb ratio convention.

The replay/probe startup parser accepts a positive finite `GE_COMB_REJECT` and
echoes it; the library still never reads the environment. No new search, raster
copy, allocation or trigger is introduced. The review panel distinguishes the
current box/min ratio from the rejected proposal's ratio, and displays the
engine's logged floor and rises. DIFFERS occupies a fixed leading text slot.

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

A pairing change completes any old reversed boundary unit, then clears decision
and vote evidence before the switch unit. With voting enabled, only its last
published anchor survives for the empty-window hold. A note-only change does not reset.
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
