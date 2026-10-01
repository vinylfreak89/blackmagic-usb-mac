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

The [configuration table](../../docs/geometry_engine.md#configuration-and-ownership)
is the single reference for numeric defaults, validation and `GE_*` tool mappings.
There are no alternate-policy switches or library environment reads. All streaming
state is bounded; measurement and publication do not allocate.

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

From this directory, `make test` runs synthetic waveform, quantile,
comb/basin, vote, pairing/reset, motion and per-instance configuration tests.
The default-policy regression gate is byte identity with the five registered
approved sidecars, not a comparison to retired experiment arms.

For integration tests, sanitizers and whole-worker CPU (including conditional
2-D searches), use the [frameserver checks](../frameserver/README.md#checks-and-worker-budget).
No captures, reference sidecars or results belong in this source tree.
The worker benchmark reports rigid-search CPU separately from the rest of
geometry. Those timers exist only in the benchmark build; production has no
timing hooks. `tests/geometry_worker_verify` takes the same arguments and
checks each captured rigid result against the scalar unit-test oracle. Its
timings include reference work and must not be used as performance results.

## Independent caption instrument

`cea608.c/.h`, `libcea608.dylib`, `tests/cea608_unit.c` and
`tests/compare_cea608.py` remain a standalone C/Python decoder cross-check.
They are not linked into the frameserver or OBS and do not supply placement.
`make test` includes the decoder's synthetic unit tests; `make geometry-test`
runs just the geometry tests. The v9 engine, its ABI, fixtures and targets
have been removed. Policy history remains in git and `TRAJECTORY.md`.
