# Registration archaeology: how the engine changed, and why

Date of excavation: 2026-09-04 (JST). This is a reconstruction from repository objects,
surviving experiment outputs, decision sidecars, and Codex rollout records. It is not a
retelling from memory. The engine names `v3` through `v8` are the names used by the project;
the earlier Python and C implementations did not always carry a version number at the time.

## Source ledger and confidence rules

The principal durable sources are:

- Git history on `main`, `p2-trajectory-engine`, `relative-only`, `unknown-hold`, and
  `bottom-edge-v8`, inspected with `git log --all`. Commit dates below are author dates in JST.
- Historical files addressed as `<commit>:<path>`, especially `CLAUDE.md`,
  `experiments/capture_render.py`, `src/field_registration/field_registration.{c,h}`,
  `src/field_registration/README.md`, `src/field_registration/TRAJECTORY.md`, and
  `src/field_registration/tests/TRUTH.md`.
- The published v7 decision sidecar, `captures/fulltape_render_registration.csv`, and the
  preserved branch measurements under `/private/tmp/unknown-hold/` and
  `/private/tmp/bottom-v8/`. Large regenerable UYVY dumps were deliberately deleted on
  2026-09-04; the CSVs, JSON summaries, and test logs remain.
- Codex rollouts, abbreviated here as:
  - `R1`: `~/.codex/sessions/2026/09/01/rollout-2026-09-01T20-22-53-01a05cb5-3217-7900-875f-3f0e194794a4.jsonl`
  - `R2`: `~/.codex/sessions/2026/09/02/rollout-2026-09-02T00-40-00-01a05da0-9601-7170-afbe-d15b2bb44f47.jsonl`
  - `R3`: `~/.codex/sessions/2026/09/02/rollout-2026-09-02T15-23-17-01a060c9-4313-7653-be00-6ebc65c24184.jsonl`
  - `R4`: `~/.codex/sessions/2026/09/03/rollout-2026-09-03T19-15-00-01a066c3-c3e8-7253-b5c1-9e9c6496d76f.jsonl`
  - `R5`: `~/.codex/sessions/2026/09/03/rollout-2026-09-03T22-13-14-01a06766-f002-7680-88b1-e19f200b8f5e.jsonl`
  - `R6`: `~/.codex/sessions/2026/09/04/rollout-2026-09-04T00-29-43-01a067e3-e25b-73d3-9437-2bae2f3859de.jsonl`
  - `R7`: `~/.codex/sessions/2026/09/04/rollout-2026-09-04T14-54-59-01a06afc-1185-7d61-8008-facafabed46e.jsonl`

The rollouts are JSONL session records, not edited design prose. They preserve requests,
measurements, false starts, and reported outcomes. A claim marked **UNSOURCED** could not be
located in those rollouts, a Git object, or a surviving measurement file. “Golden truth” means
the policy encoded by a synthetic fixture; it does not by itself establish physical truth.

## Chronology at a glance

| Stage | Dates | Principal commits / branch | Dominant premise |
|---|---|---|---|
| Offline Python estimator | 2026-08-29–30 | `4f8b65b`, `f936339`, `ac1e59c`; main | A field's program layer moves by integer lines inside a fixed transport raster. |
| First C engine | 2026-08-30–31 | `f5b261b`, `bf3f3bc`, `0f29e37`; main | The Python evidence hierarchy can become an allocation-free live estimator. |
| Motion/rolling v2 | 2026-09-01 | `14fe5d5`; main | Motion compensation plus a long rolling phase mode will reject content edges and stabilize ambiguity. |
| FIFO trajectory v3/v4 | 2026-09-02 | `56892df`, `2a4b23f`; main | A bounded trajectory and lookback distinguish observations from fallback presentation. |
| Authority-first v6 | 2026-09-03 | `a97ae06`–`3b30718`; `p2-trajectory-engine` | Most residual error is wrong evidence authority, not insufficient lookahead. |
| Relative-only v7 | 2026-09-03–04 | `10ee0ec`, `66962f3`, `d1512f4`, `220765c`; `relative-only`, merged as `abfa648` | Static-body inter-field evidence must release held phases even without an absolute gauge. |
| Unknown-hold experiment | 2026-09-04 | `7991fa9`, `f605bcd`; `unknown-hold`, not merged | An abstention must never change presentation. This proved too broad on the real tape. |
| Bottom-edge v8 | 2026-09-04 | `f9a8a1d`–`0fc4ade`; `bottom-edge-v8`, not merged | Direct lower-picture placement is the absolute authority; older evidence only refines relative phase. |
| Clean-sheet v9 plan | 2026-09-04 | no engine commit; discovery `0e349c5`, `8f58f37`, `1756fba`; main docs `7f5e93e`–`6c504dd` | The tape's own line-21 waveform is the primary direct registration signal; the envelope is secondary. |

There is no registration `v5` in the surviving repository naming. The trajectory contract was
written between v4 and v6 (`dd60843`, `2cdf4f2`, `47a7cf6`, `2133d6b`, 2026-09-03), and the
implemented successor was called v6. Treating an inferred missing v5 as real would be invention.

## 1. Offline `capture_render.py` estimator

### Dates and commits

The first corrective crop landed on 2026-08-29 at 22:29 (`4f8b65b`). The generalized per-field
model followed on 2026-08-30 at 15:49 (`f936339`), then a conservative weave/landmark gate at
16:12 (`ac1e59c`). Sources: those commit objects; `4f8b65b:CLAUDE.md` through
`ac1e59c:CLAUDE.md`; `ac1e59c:experiments/capture_render.py`.

### Premise

The initial visual “field flip” was reclassified as a spatial whole-line displacement, not field
order or cadence. The first correction assumed field 1 moved and field 2 was stable: crop field 1
at `17+d1`, field 2 at 280. The next-day generalization correctly stopped baking fixture A into
the API and represented `(d1,d2)` independently. Source: `e811226`, `564c0b9`, `dd9f4c1`, and
`b13c86d` in `CLAUDE.md` history, 2026-08-29–30.

### Mechanism

The Python `RegistrationEstimator` searched small integer field-origin pairs. Weave energy
constrained the relative term `d2-d1`; top/active landmarks and same-parity temporal evidence
attempted to supply an absolute gauge. Candidate support, pending state, and hysteresis held a
selected pair when evidence was ambiguous. `ac1e59c` required weave and landmark evidence to
agree; otherwise it emitted Unknown and rendered nominal crops. Source:
`ac1e59c:experiments/capture_render.py` and its commit message.

### Deciding measurements then

- A confirmed region, counters 24533–25025, lasted about 16 seconds; the inferred field-1
  plateau had median run length 4 frames and maximum 44. Source: historical `CLAUDE.md` at
  `f936339`/`bde8781`.
- The earlier field-2-origin search wandered over 274–285. Independent analysis showed that was
  estimator noise: 42% of off-263 weave picks had median margin 0.027, versus 0.587 for reliable
  picks. Source: `f936339:CLAUDE.md`.
- The full-tape Python decision trace later summarized `(0,0)=63,476`, `(1,0)=19,265`,
  `(2,0)=2,315`, `(3,0)=1,244`; 2,165 nonzero constant runs, 1,282 only 1–3 units. Bridging zero
  gaps shorter than 10 seconds produced nine diagnostic clusters, headed by 15.215–975.641 s and
  2837.201 s–end. Source: `56892df:CLAUDE.md` and current `CLAUDE.md` §6.

### What it got right

It established the durable spatial model: chronological fields remain in order; correction is a
whole-line crop translation; `(d1,d2)` is an observation separate from the transport field starts;
weave alone is common-mode blind; Unknown is preferable to an invented absolute phase. Those
contracts survived into the C API. Source: `b13c86d:CLAUDE.md`,
`src/field_registration/field_registration.h` history.

### How it was falsified

The trace itself was not physical ground truth. Its 1,282 short runs and the 274–285 wander showed
that content-dependent weave and landmark minima could manufacture motion. Later direct raw-field
checks also showed spatially incompatible layers, so one pair cannot align every edge. Source:
`56892df:CLAUDE.md`; `src/field_registration/README.md` at `56892df`.

### What changed next

The estimator moved into an allocation-free C library so its behavior could be replayed exactly,
benchmarked, and integrated off the USB callback. Independent top and bottom evidence and a
differential veto were added instead of trusting the Python candidate score. Source: commits
`f5b261b`, `bf3f3bc`, `0f29e37`.

## 2. First C engine

### Dates and commits

The first library landed 2026-08-30 at 21:00 (`f5b261b`), independent edge evidence at 21:43
(`bf3f3bc`), and the dual-edge/differential-veto form on 2026-08-31 at 03:01 (`0f29e37`). Source:
commit messages and `f5b261b:src/field_registration/field_registration.c`.

### Premise and mechanism

The premise was that transport/VBI landmarks, inter-field weave, same-parity temporal matching,
and hysteresis jointly described the physical translation. The first C port preserved Python
compatibility. The hardened path required coherent top and bottom landmarks, allowed a strong
one-unit correction, exposed edge disagreement as Unknown, reset the segment gauge explicitly,
and vetoed a rigid-envelope candidate when opposite same-parity differential motion said the
dominant picture moved differently. It was allocation-free on `process()`. Source: `f5b261b`,
`bf3f3bc`, `0f29e37` commit bodies and `0f29e37:field_registration.c`.

### Deciding measurements then

- Compatibility mode matched all 86,293 exact tagged-tape decisions, all 56,441 explicit Python
  decisions, and every logged diagnostic field. Source: `56892df:src/field_registration/README.md`
  (which records the earlier compatibility run).
- The untagged-capture independent census initially matched 4,042/4,042 and preserved all 320
  `+1` and 66 `+2` decisions; median cost was about 1.29 ms/unit and state about 185 KiB. Source:
  historical `CLAUDE.md` immediately after `f5b261b` (also preserved in R1). The exact state byte
  count for this first revision is **UNSOURCED**; only the rounded 185 KiB survives.
- After the dual-edge/differential veto, agreement was 3,784/4,042 overall and 3,499/3,499 on
  confident census rows. All 258 differences were conservative under-corrections: 192 raw
  census `(1,0)` held at zero, 52 `(2,0)` held at one, and 14 held at zero; there were no opposite
  corrections. Median cost was 2.58 ms/unit. Source: `0f29e37` commit body and
  `56892df:src/field_registration/README.md`.

### What it got right

It made edge disagreement explicit, proved the hot path could be deterministic and real-time,
and caught that a source-carried edge or overlay can disagree with the dominant picture. It also
established the conservative “no opposite correction” property. Source: `0f29e37` and the ordinary
truth fixture later documented in `src/field_registration/tests/TRUTH.md`.

### Falsification and successor

Conservatism became under-selection, while its hysteretic rolling state could still retain a bad
phase. The next revision tried to make content motion explicit and stabilize the phase over a
longer history. Source: `14fe5d5` and R1.

## 3. Motion-phase / rolling-mode v2

### Date and commit

2026-09-01, `14fe5d5` (“motion-phase evidence; abstain on cuts and fades”). Source: commit and
`14fe5d5:src/field_registration/field_registration.c`.

### Premise and mechanism

The premise was that content edges become safe if motion is compensated and a 120-unit rolling
mode supplies the stable trajectory. The code kept a 120-unit `phase_history`, searched motion
over ±6 lines in three bands, censored out-of-range differential estimates, and made cuts/global
luma steps abstain. Candidate/pending confirmation sat on top. Source: `14fe5d5` code and commit
body.

### Deciding measurements then

The full-tape v2 audit recorded 48 baseline transitions, applied `(0,0)` to 42,767 units,
`(1,0)` to 43,030, and `(2,0)` to 496, while 5,353 fast edge candidates were not applied. Source:
`56892df:src/field_registration/README.md` and R2.

### What it got right

It correctly separated scene cuts/fades from registration evidence and recognized that local
edges need motion context. That abstention machinery, though later simplified, was an important
guard against scene content. Source: `14fe5d5`.

### Falsification

The 120-unit rolling majority manufactured delayed plateaus and retained old phases after the
raster returned. It converted a weak estimator preference into long presentation state. This is
stated explicitly in the successor commit. Source: `56892df` commit body and R2.

### What changed next

The rolling mode was removed. A caller-owned bounded FIFO separated current observations from a
fallback trajectory and put a hard limit on lookback. Source: `56892df`.

## 4. Bounded-FIFO trajectory v3 and reset-safe v4

### Dates and commits

V3: 2026-09-02 00:45, `56892df`. V4: 2026-09-02 02:37, `2a4b23f`. The design was later written
down in `src/field_registration/TRAJECTORY.md` by `dd60843` and tested by `2cdf4f2` on
2026-09-03. Branch history: main, later used as the base of `p2-trajectory-engine`.

### Premise and mechanism

Strong current-unit absolute geometry was allowed to apply immediately. A separate trajectory
needed 30 units of confirmation, with a 36-unit hard horizon; buffered abstentions could be
backdated to a settled phase, but known observations could not. The FIFO lived in the caller,
not the engine hot path. V4 fixed resets so they invalidated confidence but preserved the last
actually presented phase instead of snapping to a stale baseline. Source: `56892df`, `2a4b23f`,
`09a1b96:CLAUDE.md`, and `TRAJECTORY.md`.

### Deciding measurements then

- The first ordinary synthetic golden contained 347 units: 338/338 unambiguous applied matches,
  9/9 cut/fade abstentions, and zero opposite corrections. Source:
  `56892df:src/field_registration/tests/TRUTH.md`.
- V3 deliberately differed from v2: applied-pair parity was 50,686/86,293 (58.74%); explicit
  decision parity 48,088/72,547 (66.29%). In the 713 rows where both made different explicit
  decisions, 650 were old `(1,0)` → v3 `(0,0)`, 62 old `(0,0)` → v3 `(1,0)`, and one old
  `(2,0)` → v3 `(1,0)`. Source: `56892df:src/field_registration/README.md`.
- Raw full-tape v3 output was `(0,0)=75,729`, `(1,0)=10,271`, `(2,0)=180`, `(0,1)=113`.
  Source: same README.
- A six-minute production path initially produced 144 transitions and 70 short runs because the
  caller reset buffered abstentions to raw at each horizon. Preserving the held trajectory reduced
  that to 54 transitions, five 1–3-unit runs, zero known-observation/application mismatches, and
  zero backdates over known observations. Source: `09a1b96:CLAUDE.md` and R3.
- Targeted windows: 7,300 late-tape units had three transitions and no 1–3-unit runs; 4,500 units
  around 36:40 had one directly observed `(1,0)` unit and 4,499 `(0,0)` units. Source:
  `09a1b96:CLAUDE.md`.
- Full v4: 86,293 exact units, 2.532 ms median, all 50,042 confident v3 evidence decisions
  preserved, 464 hard resets with zero reset-induced phase changes. Five transitions without a
  same-unit observation were explicit 30–32-unit convergence/backdate events. Source:
  `09a1b96:CLAUDE.md`.
- Forward-only versus accepted FIFO presentation differed in exactly 147 rows, at five onset
  windows: frames 490–518, 5281–5309, 8633–8663, 80154–80182, and 86060–86088. Source: R3 and
  `09a1b96:CLAUDE.md`. The exact visual magnitude of each window is **UNSOURCED**.

### What it got right

It killed unbounded history, made fallback state explicit, bounded latency, kept current evidence
separate from presentation policy, and fixed reset snaps. The 147-row comparison later proved
that backtracking was a small part of the rendered result. Source: `56892df`, `2a4b23f`,
`09a1b96`.

### Falsification

Two distinct failures survived. First, the FIFO could only rewrite abstentions; a coherent but
wrong positive observation could not be revised. The synthetic frame-8169 case put one `(0,1)`
observation before 103 flat units while the correct locked trajectory was `(1,0)`; it remained
presented for 104 units. Second, whole-tape analysis found 10,547/55,329 coherent rows where the
selected phase contradicted both the global envelope and relative consensus. Backtracking repaired
only about 1.0% of that class. Source: `2cdf4f2:tests/TRUTH.md`, `2133d6b:TRAJECTORY.md`, R3/R4,
and `3b30718:README.md`.

### What changed next

Live backtracking was demoted. V6 became forward-only and changed who had authority on the current
unit. Optional endpoint-constrained re-registration remained only as an archival-side concept.
Source: `ba8b4e8`, `21492aa`, and `TRAJECTORY.md`.

## 5. Authority-first v6

### Dates and commits

Goldens and engine work on `p2-trajectory-engine`, 2026-09-03: `a97ae06` (12:48), `1daad46`
(13:10), `17bf744` (13:10), `bad7835` (13:38), `890fa25` (13:46), `79ba2bc` (13:57),
`3b30718` (14:14), documentation merge `ba8b4e8` (14:15). Owner visual sign-off was recorded in
`089ea5b` at 17:33. Source: Git history.

### Premise

The dominant error was evidence authority: a two-of-three local band majority was beating an
agreeing full-width envelope and relative consensus. Physical one-field and common-mode raster
jitter must be followed at unit rate; transition penalties should arbitrate weak evidence, not
smooth coherent motion. Backtracking was the wrong dominant tool. Source: `1daad46`,
`src/field_registration/TRAJECTORY.md`, and R4.

### Mechanism

V6 was zero-latency and forward-only. Coherent full-width absolute envelope plus relative
consensus overruled the band-pair majority. Coherent top+bottom motion across broad bands with
same-parity temporal corroboration applied immediately. A stable raw edge anchor prevented
integrated drift, and delta authority was bounded to one line around an absolute gauge. It also
split transport validity from content availability, allowed a corroborated bottom-only candidate
when the top search hit its censored floor, fixed common-mode dimensional comparison to
`absolute-prior`, and added the stale-positive no-latch invariant. Source:
`1daad46`–`79ba2bc` and `3b30718:src/field_registration/README.md`.

### Deciding measurements then

- Public two-truth fixture: v4 scored 858/1,017 raster-known and 962/1,140 trajectory-oracle;
  v6 scored 1,017/1,017 and 1,130/1,140. The ten oracle differences were explicitly archival
  hindsight against a physically observed provisional `(0,1)`. Source:
  `3b30718:src/field_registration/README.md` and `tests/TRUTH.md`.
- All unit-rate field/common-mode/multiphase FOLLOW cases, false-edge HOLD cases, upward `-2`,
  blank-with-padding, and the 124-unit stale-latch case passed. Source: same files.
- Strict coherent-envelope mismatch fell 10,547/55,329 → 1,021/55,329. Coherent one-field
  transitions followed rose 850/4,128 → 2,939/4,128; holds fell 3,277 → 1,093. At 35:00–40:00,
  v4 followed 0/1,066; v6 followed 594 and held 438 (the remaining rows were not in those two
  reported subcategories). Source: `3b30718:README.md`.
- V6 changed 19,238/86,296 presented pairs versus v4 in the later emitted-row audit. An earlier
  doc said 19,237; `60cfee7` corrected the emitted-row count. Source:
  `60cfee7:src/field_registration/README.md`.
- Runtime was 1.466 ms median / 1.569 ms p95 per unit; state 188,320 bytes; no hot-path
  allocation. Source: `3b30718:README.md`.

### What it got right

It fixed the egregious tears, followed real one-field unit-rate movement, eliminated the stale
positive latch forward, and showed that live FIFO latency was unnecessary. The owner called the
NNEDI watch copy a large improvement and “what a digitally captured VHS tape should look like.”
Source: `089ea5b:CLAUDE.md`.

### Falsification

V6 still required an absolute gauge before relative evidence could release a held phase. In the
first 100 seconds, raw nominal crops were misregistered in 1,659/2,975 measurable frames (55.8%;
`+1` ×1,328, `+2` ×320); v6 reduced this to 153/2,974. Of 143 classifiable residuals, however,
132 were over-corrections and only 11 under-corrections: the raster returned to nominal for
3–19 units while v6 held `(1,0)` in `UnknownPhaseDwell`. Source: `44f1ee3:CLAUDE.md`, R5, and
`src/field_registration/tests/TRUTH.md`.

An initial visual conclusion that nearly every remaining jump introduced genuinely new lines and
was outside integer correction was recorded in `089ea5b` but was overturned by the 2026-09-04
frame-by-frame overlay/census review: Unknown rows clustered on real movement. This is a genuine
falsification of our interpretation, not merely a later preference change. Source:
`089ea5b:CLAUDE.md` versus `0340ca2:CLAUDE.md`.

### What changed next

V7 allowed strong relative static-body evidence to act on the current unit without becoming a
new absolute lock. Source: `66962f3`, `d1512f4`, `220765c`.

## 6. Relative-only v7

### Dates and commits

Tool and diagnosis: `71f2227`, 2026-09-03 22:13. Goldens first: `10ee0ec` at 22:19. Engine:
`66962f3` at 22:42; provenance `e7cb33c` at 22:45. No-latch golden and fix:
`d1512f4`, `220765c`, 2026-09-04 01:15. Merged to main as `abfa648`; results recorded by
`aa5d595` at 01:19. Full render tooling was `b2d0f70`. Source: Git history.

### Premise and mechanism

The residual was not missing bottom raster; it was relative misregistration when absolute edges
were nominal or unavailable. V7 horizontally low-passed by 8 pixels, constructed a same-parity
static mask, required persistence across at least 16 columns, searched reweaves from −3 to +3,
and required an absolute margin plus winner/runner-up ratio. Same-parity temporal evidence chose
which field moved; without that gauge it chose a deterministic minimum-crop/prior representation
and marked `gauge_unknown`. Crucially, relative authority was current-unit-only and could not
replace the committed absolute phase. Source: `71f2227`, `220765c`, and
`220765c:src/field_registration/README.md`.

### Goldens before and after

Before the engine change, v6 scored 0/12 on relative return, 12/12 on sustained-`+1` guard,
0/12 on relative onset, 0/15 on gauge-unknown, and 0/12 on bottom-censored `+5`; all five
false-positive guards passed. Complete score: 1,168/1,220 raster and 1,283/1,344 oracle; 51 new
required failures plus ten archival-only differences. Source: `10ee0ec` commit body and
`10ee0ec:tests/TRUTH.md`.

Final v7 fixture: 1,272/1,273 raster-known, 1,388/1,398 oracle, with the single gauge-unknown
warmup and ten archival inversions explicitly named. Ordinary golden remained 338/338,
9/9 abstentions, zero opposite corrections. A successor no-evidence unit proved that a relative
release did not latch. Source: `220765c` commit body and current `tests/TRUTH.md`.

### Real-tape measurements

- Paced, zero-drop static-comb: first 100 s 88/1,808 → 29/1,817; 620 s window 17 → 13;
  2,400 s credits window 803/2,871 → 268/2,870 (the final design-doc denominators are
  803/2,869 → 268/2,865 after record-aligned filtering). Both denominator pairs survive in R6;
  they are different filtering snapshots and must not be merged into one ratio.
- In the credits window, branch one-unit flips: 87 correct physical follows, 5 unmeasurable,
  5 engine-noise; v6 had 3 noise among 6 audited flips. Source: `aa5d595:CLAUDE.md` and R6.
- The strict proxy worsened 1,021 → 1,128, while every measured presentation window improved.
  This killed strict coherent-envelope mismatch as an acceptance oracle. Source:
  `aa5d595:CLAUDE.md`.
- Cost rose to 3.6 ms median / 5.5 ms p95 (from about 1.5/1.6), still inside 10 ms/unit.
  Source: same commit.
- Published v7 sidecar: 86,296 rows; `(0,0)=48,366`, `(1,0)=30,017`, `(-1,0)=4,068`,
  `(2,0)=3,360`, `(0,-1)=313`; 7,461 changes and 2,570 one-unit flips versus v6 3,957/1,281.
  Source: `b6e9b3f:CLAUDE.md` and `captures/fulltape_render_registration.csv`.

### What it got right

It repaired the measured return-to-nominal class, preserved physical credits jitter rather than
smoothing it, proved relative authority need not become state, and supplied explicit sidecar
provenance. Source: `220765c`, `aa5d595`.

### Falsification

The algorithm still inferred registration through content proxies. The owner’s overlay review
found raw edge movement held 198 times in the first 1,800 units, against only 80 follows, while
the crop changed on a still raw edge 69 times. V7 was under-selecting exactly where it abstained.
Source: `0340ca2:CLAUDE.md` and `experiments/bottom_edge_census.py` at `13320a9`.

The published render also contained a caller defect independent of the estimator: the partial
remap held source rows 17–18 and shifted only below them, duplicating row 18 for negative offsets
and dropping row 19 for positive offsets. The full-raster preview had a mirror duplication below
its window. `3b94b51` replaced both with pure whole-window shifts. Therefore visual review of the
old published MP4 mixed engine errors with renderer artifacts. Source: `3b94b51` and
`0340ca2:CLAUDE.md`.

### The `unknown-hold` detour

The sidecar showed 2,475/7,461 phase changes on `Unknown*` rows: UnknownSpatialPhase 883,
UnknownEdgeTransient 711, UnknownPhaseDwell 392, UnknownCommonModeGauge 323, and
UnknownSceneCutHold 166. `7991fa9` added a golden in which v7 changed 160 synthetic Unknown rows;
`f605bcd` isolated a support-1 continuation. This was a real policy inconsistency, but the broad
fix—freeze every Unknown row—was wrong for the tape because Unknown commonly meant “our proxy
failed while the raster moved.” The experiment yielded zero Unknown-row changes but worsened both
presentation windows. It was not merged. Sources: `unknown-hold` commit bodies,
`/private/tmp/unknown-hold/{trajectory-new-golden-current.txt,fixed_fulltape_metrics.json,
v8_fulltape_metrics.json,main_fs3000_metric.txt}`, and R6.

The precise worsened window counts for the final freeze-every-Unknown variant are **UNSOURCED** in
the surviving summary files; several intermediate `v8*` files exist, but their naming does not
unambiguously identify the final variant. The conceptual result is sourced in `0340ca2:CLAUDE.md`.

## 7. Bottom-edge v8

### Dates and commits

Instrument `13320a9` and pure-shift renderer `3b94b51`, 2026-09-04 13:03–13:08. Goldens
`f9a8a1d` (13:16), `fb05f9e` (14:18). Engine `5aea42e` and frameserver provenance `20711c0`
(14:47). Dark-hold reacquisition `91e44b3` and executable oracle policy `0fc4ade` (15:13–15:14).
Branch: `bottom-edge-v8`; never merged.

### Premise

The owner’s direct placement rule was: per field and unit, find the last picture line before the
first mostly-black line, and shift the whole crop so that lower boundary lands at a fixed target.
Near-blank ADC rows were content-bearing and had to be measured relative to the field’s own
blanking level; hard padding could be read safely. Source: `0340ca2:CLAUDE.md`, `13320a9`, and
`f9a8a1d:tests/TRUTH.md`.

### Mechanism

V8 learned a per-segment lower target from four program-qualified units, scanned each field’s
lower boundary, followed accepted motion per unit, and named dark/noisy/cut/out-of-range holds.
After a dark interval, a large apparent return was provisional once and accepted on the second
consistent measurement. A pure bottom-only prototype failed, so the implementation retained the
v7 static-body estimator to refine `d2-d1` when strong; it could not add common-mode motion.
Source: `5aea42e`, `91e44b3`, `src/field_registration/field_registration.c` on this branch.

### Goldens and measurements

- Pre-change v7 failed new v8 dark hold 0/6, fade hold 0/6, fade reacquisition 0/8. It also
  scored 0/12 on a body-`+2`/bottom-`+1` relative residual. Source: `f9a8a1d` and `fb05f9e`.
- Final ordinary golden remained 338/338, 9/9 abstentions, zero opposite. Post-dark reacquisition
  improved 0/11 → 11/11. Source: `91e44b3`.
- Truth-policy harness: `live-v8` 1,415/1,415; ten archival disagreements and 167 retired-v7
  disagreements were named diagnostics, not hidden green failures. Source: `0fc4ade` and
  current `tests/TRUTH.md`.
- First-1,800-unit v7 census: raw field-1 lower edge 256 ×1,299, 257 ×245, 255 ×42, 258 ×5,
  259 ×169 (grey mute), plus dark outliers. Follow/under/over was 80/198/69. Source:
  `0340ca2:CLAUDE.md` and `/private/tmp/bottom-v8/first1800-current.csv`.
- V8 changed follow/under/over to 214/64/34. Registered lower edge was 256 in 1,038 units and
  255 in 546, exposing that retained relative refinement often overrode literal lower placement.
  Source: current `CLAUDE.md` and `/private/tmp/bottom-v8/census1800_frameserver_v8.csv`.
- Pure bottom-only made first-window static comb catastrophically worse, 29 → 937. The hybrid
  improved v7 29/1,822 → 5/2,011 in the SP window and 268/2,869 → 138/2,865 at 2,400 s.
  Source: current `CLAUDE.md`; `/private/tmp/bottom-v8/*comb.csv`.
- Whole-tape engine cost: 2.752 ms median / 2.816 ms p95. Final mode counts were
  BottomEdgePlacement 46,162; BottomEdgeRelativePlacement 36,533; UnknownBottomEdgeHold 1,029;
  UnknownSceneCutHold 2,569; ShortDeviceUnit 3. Source:
  `/private/tmp/bottom-v8/fulltape_v8_reacquire_metrics.json`.

### What it got right

It replaced “abstain because evidence conflicts” with a direct measured placement for many units,
made hold reasons explicit, followed far more lower-edge motion, never duplicated/dropped source
rows, and formalized which old synthetic policies were retired rather than silently rewriting
truth. Source: `5aea42e`, `0fc4ade`, `3b94b51`.

### Falsification

Bottom position was only half the geometry. The new envelope census found, in the first minute,
field 1 clustered at top/bottom/height 20/256/237 with 199 rigid one-line moves (100 up, 99 down)
and 94 single-edge events; field 2 clustered 283/518/236 with zero rigid moves and 86 bottom-only
flickers; grey mute had distinct 18/259 and 281/521 envelopes. Source: `0e349c5`, R7, and the
measurement recorded later in main `CLAUDE.md`. Subsequent signature-aware coordinates corrected
the aligned picture top to 19/282; the earlier 20/283 statement in
`8f58f37:docs/registration_vsync_research.md` was an indexing/line-number interpretation error.

The literal target was not constant after relative refinement (256 ×1,038 versus 255 ×546), and
the bottom-only version’s 937 bad frames proved that a single content boundary cannot define the
raster. V8 had also accumulated the v7 comb path, lower-edge authority, body-relative override,
cut gates, reacquisition, learned target, and multiple policy labels—the complexity the owner
explicitly rejected. Coding stopped; v8 was not merged and no v8 watch copy was accepted. Source:
`0fc4ade` branch, current `tests/TRUTH.md`, and R7. A completed whole-tape envelope census is
**UNSOURCED**; it was still running when clean-sheet planning began.

## 8. Agreed clean-sheet v9 plan (not implemented)

### Date and source state

Agreed concept work occurred 2026-09-04 after v8 stopped. There is no v9 engine commit. Durable
discovery/instrument commits are `0e349c5` (picture envelope), `8f58f37` (V-sync research),
`1756fba` (caption/timing recognition), and main documentation `7f5e93e`, `17aabca`,
`b3b144f`, `ddfcbed`, `e32f85e`, `6c504dd` between 17:32 and 18:04. Source: Git history and
`main:CLAUDE.md`.

### Physical premise

The Shuttle/deck supplies a rigid line raster, but the tape-carried field content can be placed
one or more whole field lines away from its proper standard location. Field 1 genuinely moves
alone: among 241 field-1-only moves in the first minute, same-parity per-field matching beat a
whole-picture one-display-line model 202–0, with 39 mixed; common-mode moves were only 10/1,800.
Field-2-only moves were mostly ambiguous (3/3/29). Source: raw-unit parity measurement recorded in
`main:CLAUDE.md` after `8f58f37` and R7.

The direct reference is the tape’s own blank line-21 waveform: seven-cycle clock run-in, start
bit, and two null bytes/parity structure. The deck inserts its fixed line 21 at unit row 17
(field-2 equivalent 280). When aligned, tape and insert waveforms coincide; when displaced, a
second line-21-like row appears at `17+d`. The black line 22 and picture begin at 18 and 19
(field 1), with picture origin 282 for field 2. Source: `1756fba`, `7f5e93e`, `b3b144f`,
`e32f85e`, `6c504dd`, and `main:CLAUDE.md`.

Measured SP first-minute line-21 row sets were `(17,)` in 1,663 units and `(17,19)` in 85; all
85 second-row cases agreed with picture displacement `+2`. An EP slice had `(17,)` in 1,762.
The first-minute signature spot-checks were caption/picture 17/19 in 50/50 and 19/21 in 38/38;
the EP spot-check was 17/19 in 500/500. Source: `main:CLAUDE.md` records the 85 and spot-check
counts. The `(17,)=1,663` and EP `(17,)=1,762` counts survive only in the owner’s plan addendum
inside the current dispatched transcript, not an on-disk Git file or listed rollout: **UNSOURCED
outside the current request**.

### Planned mechanism

No v9 code exists. The latest recorded plan is:

1. Search the whole field, top first and including the bottom, for a tolerant but structurally
   valid line-21 waveform. Reject duplicates, split/skewed candidates, and broad leaking-VBI
   bands as ambiguous.
2. A unique second line-21 row at `17+d` is primary displacement evidence. If a valid envelope
   agrees, label `Line21Placement`; if the envelope is unmeasurable, line 21 may act alone as
   `Line21OnlyPlacement`; if the two disagree, hold as `Line21EnvelopeConflict`.
3. With no second line-21 row, use the picture envelope per field against fixed picture origins
   19/282. Learn only envelope height per signal lock, never a positional baseline. Rigid
   top+bottom movement with unchanged height is corrected every unit; height/content change is
   preserved or held as measured, not called registration.
4. A consistently displaced line-21 waveform while the picture envelope remains at its origin
   can re-lock the caption reference once without moving the picture (`CaptionRelock`). Ambiguous
   captions never alter lock or crop. No gauge means hold last applied, initially zero.
5. Apply only whole-window UYVY shifts, fields independently, preserving chroma with luma and
   preserving field parity. There is one unit of memory (last valid envelope and applied offset),
   no FIFO/lookahead, no long dwell, no comb estimator, no band hierarchy, no multi-candidate
   trajectory search, and no magnitude-based “cut” rule.

Steps 1, 3, 4, and the measured line-21 model are durable in `main:CLAUDE.md` at `6c504dd`.
The priority ordering and labels `Line21Placement`, `Line21OnlyPlacement`, and
`Line21EnvelopeConflict` were stated after that commit in the current request and are
**UNSOURCED outside the current dispatched transcript**. They require owner review before code.

### Output geometry, kept separate from registration

The final owner decision is 720×480 clean aperture from unit rows 19/282 (standard lines 23/286),
with captions omitted; 720×486 is a future alternate mode retaining line 21. Picture origin is
19/282 in both registration models. Main briefly applied 19/282 (`bdac68b`, 17:35), reverted it
(`2930095`, 17:39), then reapplied it with the clean-aperture/alternate-mode distinction
(`7285d89`, 17:51). Sources: those commits and `b3b144f:CLAUDE.md`.

### Planned acceptance

- Every unique second line-21 row must yield the corresponding applied field-1 displacement;
  aligned tape line 21 must land on the deck insert. Conflicts and EP split/skew cases must be
  named, not used. Leaking bands must not classify as line 21 or picture.
- The signature-aware census measured an EP slice with 458/1,800 units carrying at least two
  bright leaking-band rows and 138 carrying one; those become negative controls. Source:
  `6c504dd:CLAUDE.md`.
- Registered top/bottom should be constant per signal segment whenever height is valid; zero crop
  changes when the raster is still; every rigid move followed; content-height changes preserved.
- The after-the-fact confirmation is primary line-21 landing and envelope constancy. Static-comb
  must be no worse than the best v8 observations, 5/2,011 and 138/2,865, but it is not the truth
  source. Source: v8 results above and the v9 plan in R7/current request.
- Estimated clean-sheet size was roughly a few hundred C lines, state under 1 KiB, and one or two
  line scans per field. Exact line count and runtime are **UNSOURCED estimates** because v9 has
  not been implemented.

### What survives from v7/v8

Only the stable API (`fieldreg_open/process/begin_segment/discontinuity/close`), allocation-free
hot-path requirement, whole-window crop semantics, explicit Unknown/hold provenance, sidecar
auditability, and offline diagnostic tools are intended to survive. Static comb, temporal vetoes,
band voting, multi-candidate search, rolling history, live FIFO/backtracking, and bottom-only
authority are diagnostic history, not live v9 inputs. Source: owner clean-sheet direction in R7
and the current dispatched transcript. Because no v9 branch exists, this remains plan, not code.

## 9. Instruments: what each could and could not prove

### Decision sidecars

Sidecars are exact records of what the engine/caller presented, not ground truth. They exposed
the 2,475 Unknown-row changes, the 7,461 transitions, and the v4/v6/v7 differences. They cannot
say whether a crop was physically correct without joining raw pixels. Source:
`captures/fulltape_render_registration.csv`, schema history in `README.md` and `TRAJECTORY.md`.

The 2026-09-04 full-raster preview violated even that limitation: it keyed rows by the 16-bit
counter, so values after wrap at 65,536 overwrote first-half decisions. The published render and
sidecar were consistent; the preview was not. Source: R6/current owner correction.

### Ordinary and two-truth goldens

Goldens decided implementation contracts reproducibly and caught the 8169 latch, relative-only
state leak, dark-hold reacquisition, and silent green “FAIL” reporting. They also encoded policy
by fiat. V8’s 177 disagreements forced the harness to label 1,415 `live-v8`, ten `archival`, and
167 `retired-v7` rows rather than pretending every historical oracle remained truth. Source:
`tests/TRUTH.md`, `0fc4ade`.

### Independent field-origin / edge census

The early census was valuable because its 3,499 confident rows were independent of engine state,
but it ignored ambiguous rows—the very rows later found to contain much real movement. “Perfect
3,499/3,499” therefore meant agreement on easy cases, not full selection. Source:
`0f29e37`, `56892df:README.md`.

### Strict coherent-envelope oracle

This joined coherent top and bottom edges and compared raw versus applied relative phase. It made
the v6 authority failure visible (10,547 → 1,021), but became wrong as an acceptance proxy when
v7 improved actual frames while the score worsened to 1,128. It also left 1,887 late-tape flips
unknown because edges were censored. Source: `3b30718`, `aa5d595`, and R6.

### `experiments/static_comb_metric.py`

This uses an 8-pixel horizontal low-pass and persistent static regions, then tests reweaves over
integer relative shifts. It directly measures field-to-field registration on static detail and
showed ~40% energy drops in the first identified failures. It cannot establish absolute/common-mode
placement, cannot judge moving scenes, and can confuse local content motion with raster motion.
The initial “153/2,974” and later paced “88/1,808” are not contradictory engine counts: they used
different frame sets/filters and must not be compared as identical denominators. Source:
`71f2227`, `aa5d595`, `experiments/static_comb_metric.py`.

The blip audit used the strict oracle and reported zero branch noise flips, but 1,887 were
unclassifiable. A direct per-frame comb audit of the credits window found five v7 noise flips among
97. Thus “zero” meant zero among strict-classifiable rows, not zero on tape. Source:
`aa5d595:CLAUDE.md`, `/private/tmp/blackmagic-relative-only/blip_audit.csv` if retained, and R6.

### `experiments/bottom_edge_census.py`

This made under-selection measurable: 80 follows, 198 holds, 69 crop-on-still in the first 1,800
units. But a lower content boundary is not a raster reference on dark pictures, grey mute, fades,
letterbox/envelope changes, or when picture reaches digitized near-blank rows. The bottom-only
prototype’s 29 → 937 presentation collapse killed it as a sole authority. Source: `13320a9`,
`0340ca2`, v8 CSVs.

### `experiments/picture_envelope_census.py`

This added top, bottom, and height and separated rigid shifts from single-edge/content changes.
Its first interpretation still treated VBI/picture rows too much by coordinate and reported the
nominal tops as 20/283. `1756fba` changed it to recognize caption and timing signatures; raw data
then established the aligned picture origin 19/282 and exposed line 21 itself. The instrument
improved because its ontology changed from “bright edge at row N” to “which standard waveform is
this?” Source: `0e349c5`, `1756fba`, `8f58f37:registration_vsync_research.md`, and
`main:CLAUDE.md`.

### Visual NNEDI/Yadif watch copies

Human review caught large-scale improvement and later under-selection, but it was confounded at
different times by deinterlacer behavior, partial-row renderer duplication, and the counter-wrap
preview. The useful rule was to freeze exact raw/corrected units and join them to an extended
counter sidecar; appearance alone could not assign cause. Source: `089ea5b`, `3b94b51`, R4–R7.

## 10. Two false alarms on 2026-09-04

### Counter-wrap-keyed preview

The owner-visible jitter in Claude’s full-raster preview was initially attributed to v7 changing
phase on Unknown rows. The preview keyed decisions by the 16-bit device counter; after wrap at
65,536, second-half decisions overwrote the first half. The published MP4 and sidecar were
consistent. Source: owner correction preserved in R6/current transcript.

Cost: it triggered the `unknown-hold` branch, two commits (`7991fa9`, `f605bcd`), a whole-tape
decision pass, paced presentation checks, and approximately 12 GB of regenerable scratch later
deleted. The 12 GB figure is from the housekeeping request in the current transcript; no retained
filesystem census proves its exact byte count, so that size is **UNSOURCED outside the request**.
The sidecar’s 2,475 Unknown-row changes remained a legitimate policy measurement, but not the
cause of that preview.

### Crop origin 17/280 versus 19/282

The second alarm conflated two questions: whether line 21 is normally carried in a VBI-preserving
analog raster, and whether this project’s 720×480 output is clean aperture. The sequence was:
signature discovery (`1756fba`, 17:31), switch to 19/282 (`bdac68b`, 17:35), revert to 17/280
after recognizing that line 21 is expected in a VBI-preserving window (`2930095`, 17:39), then
the final owner decision to use 19/282 for 720×480 clean aperture while reserving 720×486 as the
caption-preserving mode (`7285d89`, 17:51). Source: those Git objects and `main:CLAUDE.md`.

Cost: three geometry commits in 16 minutes, two reversals, repeated plan revisions, and rebuilds
of publisher/census tests. No surviving source shows that a full-tape media render was performed
during this 16-minute interval, so any claimed re-render cost would be **UNSOURCED**. The final
19/282 decision is not itself the false alarm; the false alarm was treating crop origin and
picture/registration origin as the same question before output mode was specified.

## 11. Through-line

Every implemented engine through v8 tried to infer a fixed standard raster from proxies carried
by program content:

- weave measured only `d2-d1`;
- band votes measured whichever local edge dominated;
- same-parity temporal search measured content motion as well as raster motion;
- rolling mode and FIFO converted uncertain measurements into trajectory policy;
- coherent-envelope strictness assumed top and bottom content edges represented one rigid body;
- static comb measured relative registration only on static detail;
- the bottom census treated one content boundary as absolute raster position;
- the full envelope improved that to top+bottom+height, but still required identifying which
  lines were picture and which were standard vertical-interval structures.

Those proxies were useful: they established integer, per-field, whole-line motion and fixed most
visible errors. They failed wherever content was flat, dark, moving, layered, clipped, or carried
multiple edges—the exact cases in which the engine emitted Unknown or chose the wrong authority.

The direct signal was present all along but misclassified as generic visible VBI: the tape’s own
blank line-21 waveform. The deck supplies a fixed line-21 insert at row 17; aligned tape line 21
coincides with it, while a displaced field exposes another structurally identical waveform at
`17+d`. That is a standard-timed, content-independent observation of field-1 displacement. The
black line 22 and picture envelope then corroborate it; the envelope remains the fallback for
units/fields without a unique line-21 waveform. Source: `1756fba`, `7f5e93e`, `b3b144f`,
`e32f85e`, `6c504dd`, and `main:CLAUDE.md`.

That discovery does not retroactively make the earlier work useless. The older engines proved the
transport is rigid, motion is per field rather than cadence, shifts must move complete UYVY lines,
and a live solution fits comfortably within budget. But the excavation’s central conclusion is
blunt: we spent v1–v8 estimating a standard timing relationship indirectly after assuming its
direct timing waveform was merely nuisance VBI. V9’s reason to exist is not another refinement of
that hierarchy. It is to start from the standard signal, use content only as corroboration or
fallback, and leave every ambiguous case explicitly named.
