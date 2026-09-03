# Registration trajectory contract

The live contract is implemented by the allocation-free C estimator: coherent
physical evidence is followed forward at unit rate with no presentation FIFO.
The optional retroactive layer described below is recording-side only and
remains gated until a real tape proves that a positive, coherent provisional
observation was wrong. It is not part of the CMIO latency path.

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

There is a second, independent lock mechanism in the current estimator. A
measured relative phase may contradict the selected phase while absolute
picture edges abstain. `UnknownCommonModeGauge` then clears the pending
candidate and charges the presentation-horizon counter until a trajectory
reset invalidates the baseline, but the selected phase remains the presented
fallback. Reacquisition consequently requires stronger evidence while the
phase contradicted by the relative measurement stays on screen. The trajectory
layer must treat sustained relative contradiction as an unsettled interval,
not as a reason to retain the old phase indefinitely.

## State and terminology

- **Observation:** immutable per-unit estimator output and evidence.
- **Provisional phase:** the best phase assigned before an interval resolves.
- **Committed phase:** the last phase accepted by a resolved trajectory.
- **Unsettled interval:** contiguous units whose final path is not yet known.
- **Settlement:** sufficient endpoint and in-interval evidence to finalize a
  path, not merely the last observed pair winning a counter.
- **Horizon:** maximum retained duration. It is a physical parameter and must
  cover measured source reacquisition (at least 69 NTSC units); 36 is too short.
- **Ring depth:** caller-owned storage capacity for delayed units. It limits
  how far a later decision can be applied retroactively, not how long evidence
  remains valid.
- **Trajectory staleness limit:** independent physical bound after which an
  unresolved candidate must produce an explicit outcome and fresh acquisition.

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

Transport truth and content availability are separate inputs. Broken hard
padding or an explicit byte discontinuity invalidates raster geometry and
terminates temporal evidence. Missing VBI, a dark/flat field, or an absent
picture landmark is only missing content evidence: it abstains and holds an
existing candidate rather than destroying it.

## Absolute gauge and censored landmarks

Relative evidence constrains only `d2-d1`. A sustained relative contradiction
may open an unsettled interval and constrain its candidate paths, but it may
never manufacture an absolute `(d1,d2)` gauge on its own. The committed
endpoint, an uncensored absolute landmark, or another explicit gauge source is
required to place that relative constraint in the transport raster.

A picture-top result at the first searchable line (`start+1` in the current
estimator) is censored: the real edge may lie there or anywhere above it. It is
not a measured `-1` offset. A bottom edge that remains inside the transport slot
may provide a bottom-only absolute candidate when relative phase corroborates
it; confidence is stronger when independent horizontal bands and same-parity
temporal evidence also agree. Top and bottom censoring must be reported in the
decision log rather than converted into contradictory exact measurements.

## Endpoint-constrained path

This section specifies that optional archival-side pass. It consumes the live
decision sidecar; it is not permission for the live device to delay frames.

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

The live authority rule is stricter and immediate: **coherent per-field
top+bottom displacement across independent broad bands, corroborated by
same-parity temporal displacement and not gated by a cut, applies at unit
rate. Transition penalties arbitrate weaker evidence only; they may not smooth
this case.** A coherent full-width envelope plus relative-phase consensus also
outvotes a conflicting local band majority. Field 2 remains pinned unless its
own evidence moves it.

The displacement form is deliberately a delta rule as well as an absolute
envelope rule. A heterogeneous raster can expose a top landmark from one layer
and a bottom landmark from another, so neither yields a trustworthy absolute
gauge. If both landmarks move by the same signed integer between consecutive
units, at least two broad bands independently show the same top+bottom delta,
and both same-parity temporal searches corroborate it, apply that delta to the
committed phase immediately. A localized overlay cannot satisfy the broad-band
and full-width requirements. The `physical-multiphase-envelope-jitter` golden
freezes this distinction.

## Resolution and horizon

On settlement, finalize and emit every buffered unit in order, including units
that had positive provisional observations. The path may contain real internal
transitions; settlement does not require a flat result.

The current `phase_unsettled_units` counter is retired. Candidate/interval age,
trajectory staleness, and retained ring occupancy are distinct quantities. A
settled decision may request at most
`min(interval_age, retained_ring_units)` of backdating. Units already emitted
outside the ring remain honestly provisional in the live output and are
recoverable only from the sidecar/raw recording; no counter may pretend they
were rewritten. Candidate age is not unbounded: the independent physical
staleness limit still forces the horizon outcome below.

On horizon expiry:

1. emit the best unresolved path currently available; never drop, repeat, or
   synthesize a unit;
2. log `UnresolvedHorizon` with interval id, evidence, and retained length;
3. enter cooldown so the same unresolved episode is not repeatedly buffered;
4. reacquire a fresh committed lock when the classifier and estimator settle.

The trajectory-staleness horizon is configurable in media units and time.
Default NTSC sizing must be at least 69 units plus a small scheduling margin;
PAL uses equivalent time. Ring depth is independently configurable according
to the selected live-latency/memory policy and may be shorter than the physical
horizon.

## Stale-latch invariant

A one-unit positive observation may be provisional, but it may not remain the
presented phase indefinitely once a locked trajectory supplies contradictory
evidence. Every provisional hold has exactly one terminal outcome: path
resolution, horizon emission, explicit discontinuity, or epoch reset.

## Live and recording policies

- **Live/default:** publish the forward authority-first result immediately,
  marked provisional/settled in the sidecar. There is no registration FIFO.
- **Optional recording-side refinement:** a downstream recorder may retain a
  bounded interval and publish a finalized endpoint-constrained path, but only
  when explicitly enabled and justified by source evidence.

Both policies preserve unit order and timestamps. The USB/event thread never
waits for trajectory resolution; a fixed pool is handed to a processing worker
through SPSC pointer rings. No per-unit allocation is permitted.

This engine corrects integer vertical field registration only. Sub-line phase,
horizontal/line-time instability, flagging, skew, and heterogeneous source
layers that genuinely occupy different phases are out of scope. It does not
"stabilize the tape completely."

## Decision-log fields

Every unit records at minimum:

```
interval_id, unsettled, provisional_d1, provisional_d2,
applied_d1, applied_d2, committed_d1, committed_d2,
settled_known, settled_d1, settled_d2,
structural_transport_ok, content_evidence_available,
top_f1_censored, top_f2_censored, retained_ring_units, interval_age,
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

Required boundary/content classes include field-1 and field-2 upward
displacements at `-1` and `-2`, common-mode `(-2,-2)`, a multi-phase raster in
which a band majority and the global envelope disagree, a fade while a
candidate is active, and blank/dark units whose hard-padding transport ruler
remains intact. The frozen current implementation is expected to fail some of
these; those failures are required characterization until the redesign lands.

The current engine/caller is expected to fail the provisional-policy cases;
that is the frozen pre-redesign baseline, not a reason to weaken the golden.
