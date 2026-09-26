# Field registration

The default frameserver/OBS registration path is the approved geometry engine
(`geometry_engine.c`, tag `v11-approved-2026-09-26`). Its complete measurement,
publication and parameter contract is in [geometry_engine.md](../../docs/geometry_engine.md).

## API and defaults

Allocate `ge_size()` bytes and initialize with `ge_init`. Each engine owns a
copy of `ge_config`; NULL uses `ge_default_config()`. Configuration is validated
before initialization and is immutable through the public streaming API.
`fs_open` copies `fs_config.geometry_config` in the same way. A default OBS
open needs no engine selection or environment settings.

The approved path always uses waveform tops, continuation-only level fills
on waveform abstention, same-frame flat-band bottoms, the paired-top anchor
vote, blank-spot confidence, still-picture comb triggering and rigid-vertical
comb withholding. Numeric defaults:

- Wave step bar 0.45; symmetric top clamp 5.
- Comb refusal ratio 2; selection/enclosed-floor factor 1.5.
- Vote window 30 confident frames; top-pair correlation 0.6.
- Flat-bottom margin 3; blank-spot tolerance +2.
- Rigid-motion minimum 2 lines; clarity 1.3.

There are no alternate-policy switches. Replay/probe tools share the numeric
`GE_*` parser in `geometry_tool_controls.h`; the library reads no environment.
The fixed vote storage capacity is 256, with a configurable window 1..256.
All streaming state is bounded; measurement and publication do not allocate.

`ge_push` consumes contiguous 720x525 luma and emits 0..2 completed unit
decisions. Coordinates are NTSC lines (storage row+4); zero edges explicitly
mean unavailable. Aligned pairing emits immediately. Reversed pairing pairs
next-unit field 1 with current-unit field 2 and delays completion one unit.
Call `ge_break` at broken adjacency/epoch/EOF. After flushing, `ge_set_pairing`
changes pairing inside a session without dropping the published vote anchor.
Resets clear votes and relative-decision evidence; only a new `ge_init` starts
a new anchor session.

Raw waveform observations, accepted census edges, supplemental vote inputs,
unvoted placement and published placement are distinct. A fill never changes
the census or relative correction. Schema 28 retains its historical column
set and frozen configuration echoes for byte identity with the approved logs;
a historical switch column is not evidence that its removed branch still exists.

## Validation

From this directory, `make geometry-test` runs synthetic waveform, quantile,
comb/basin, vote, pairing/reset, motion and per-instance configuration tests.
The default-policy regression gate is byte identity with the five registered
approved sidecars, not a comparison to retired experiment arms.

From `src/frameserver`, run `make test test-geometry test-pairing` and the
ASan/UBSan and TSan targets. `bench-geometry` measures the real default worker
with conditional 2-D motion searches, reports whole-worker thread CPU and
separates zero/one/two-search populations. It requires fresh scratch output
paths; no captures, reference sidecars or results belong in this source tree.

## Retained legacy code

`field_registration.c/.h` and `cea608.c/.h` retain the v9 implementation and
API. They remain compiled but are not selected by a frameserver or OBS open.
Their deletion is a separate post-merge task. `make test`, `make v9-test`
and the synthetic v9 fixture/decoder tests continue to cover that code.
The legacy frameserver `bench` target measures v9, not the approved engine.
Policy history and superseded experiments remain in git; captions are not
inputs to the current geometry engine.
