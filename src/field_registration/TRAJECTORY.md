# Registration trajectory contract (implementation gated)

This document specifies the trajectory layer that sits between per-unit
`field_registration` observations and a consumer. It does not change the C
estimator. Implementation is gated on owner approval because it changes
presented offsets, including the measured 104-unit stale-latch interval.

## Why a second layer exists

The estimator answers, for one exact transport unit, which crop offsets are
supported by that unit and what stable fallback is currently learned. Those
are observations, not a finalized temporal path. A positive observation can
be provisional: during acquisition or decoder vertical-phase hysteresis the
observable raster can briefly support one pair and settle at another, including
the legal inversion `(0,1) -> (1,0)`.

The current caller backdates a newly locked fallback only over abstaining rows.
It cannot revise a positive provisional row. Worse, `previous_phase` can hold
that row through later abstentions after the locked fallback contradicts it.
The whole-tape sidecar contains one such event: a lone `(0,1)` observation at
timeline frame 8169 is held for 104 units against a locked `(1,0)` fallback.

## State and terminology

- **Observation:** immutable per-unit estimator output and evidence.
- **Provisional phase:** the best phase assigned before an interval resolves.
- **Committed phase:** the last phase accepted by a resolved trajectory.
- **Unsettled interval:** contiguous units whose final path is not yet known.
- **Settlement:** sufficient endpoint and in-interval evidence to finalize a
  path, not merely the last observed pair winning a counter.
- **Horizon:** maximum retained duration. It is a physical parameter and must
  cover measured source reacquisition (at least 69 NTSC units); 36 is too short.

Committed and provisional phase are separate variables. A provisional phase
must never silently overwrite the committed phase.

## Interval boundaries

Buffer from the first unit that departs from the committed path, including the
initial `UnknownSpatialPhase` unit that commonly precedes
`UnknownPhaseDwell`. Other start signals are:

- source acquisition/relock or classifier `Unsettled` transition;
- abnormal phase-change rate/chatter;
- a positive phase that contradicts the locked trajectory;
- a transport discontinuity that invalidates temporal evidence.

Scene cuts and global luma changes gate visual evidence but do not alone start
a source-relock epoch. `fieldreg_begin_segment()` is reserved for acquisition
or relock. Plain byte discontinuities call `fieldreg_discontinuity()`.

## Endpoint-constrained path

Resolution is a bounded path problem over candidate `(d1,d2)` states, not
"paint the interval with the final phase." The cost includes:

1. per-unit absolute/relative evidence and its confidence;
2. a transition penalty, relaxed by classifier `Unsettled` evidence;
3. a strong pre-interval endpoint constraint from the committed phase;
4. a post-interval endpoint constraint from the newly settled phase;
5. explicit abstention cost rather than fabricated evidence.

Strong, coherent one-unit physical displacement therefore remains representable.
A misleading positive observation can be revised when the endpoint-constrained
path rejects it. Both raw raster geometry truth and trajectory-policy truth are
reported by tests; agreement with one must never be mislabeled agreement with
the other.

## Resolution and horizon

On settlement, finalize and emit every buffered unit in order, including units
that had positive provisional observations. The path may contain real internal
transitions; settlement does not require a flat result.

On horizon expiry:

1. emit the best unresolved path currently available; never drop, repeat, or
   synthesize a unit;
2. log `UnresolvedHorizon` with interval id, evidence, and retained length;
3. enter cooldown so the same unresolved episode is not repeatedly buffered;
4. reacquire a fresh committed lock when the classifier and estimator settle.

The horizon is configurable in media units and time. Default NTSC sizing must
be at least 69 units plus a small scheduling margin; PAL uses equivalent time.

## Stale-latch invariant

A one-unit positive observation may be provisional, but it may not remain the
presented phase indefinitely once a locked trajectory supplies contradictory
evidence. Every provisional hold has exactly one terminal outcome: path
resolution, horizon emission, explicit discontinuity, or epoch reset.

## Live and recording policies

- **Delayed/corrected:** retain the bounded interval and publish only finalized
  units. This is the recorder/default corrected-stream policy.
- **Low-latency live:** publish provisional units immediately, marked
  `Unsettled`. The sidecar retains enough evidence for an archival re-render.

Both policies preserve unit order and timestamps. The USB/event thread never
waits for trajectory resolution; a fixed pool is handed to a processing worker
through SPSC pointer rings. No per-unit allocation is permitted.

## Decision-log fields

Every unit records at minimum:

```
interval_id, unsettled, provisional_d1, provisional_d2,
applied_d1, applied_d2, committed_d1, committed_d2,
settled_known, settled_d1, settled_d2,
resolution {Immediate, SettledPath, UnresolvedHorizon, Discontinuity, EpochReset},
evidence_mode, confidence
```

The log must distinguish live provisional presentation from a later finalized
recording decision without rewriting the original observation.

## Required golden classes

The public golden is capture-free and labels two independent truths:

- `raster_d1/raster_d2`: where the designated main picture is in that unit;
- `trajectory_d1/trajectory_d2`: the endpoint-constrained policy oracle.

It includes steady paths, real one-unit displacements, edge-only secondary
artifacts, coherent provisional transients that return, `(0,1)->(1,0)`
inversion, chatter, cuts/fades, non-settling horizon expiry, and segment reset.
Secondary horizontal assets may carry a different phase, but the generator
marks which asset is the main-picture truth. Tests report both scores and must
never collapse them into one "accuracy" number.

The current engine/caller is expected to fail the provisional-policy cases;
that is the frozen pre-redesign baseline, not a reason to weaken the golden.
