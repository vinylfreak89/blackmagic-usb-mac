# Synthetic registration truth golden

`make test` in this directory runs two tests: the unit test, and this capture-free golden.

`gen_registration_units.py` emits a raw unit stream — exact 756,048-byte `0xe801` units
concatenated without packet tags — plus a truth CSV. USB provenance is a separate contract and
would only obscure what this test measures. The generated raster contains byte-exact transport
padding at lines 0–6, 261–269 and 523–524; fixed two-line VBI-like fiducials beginning at
lines 16 and 279; coherent interlaced UYVY program content with strong top and bottom edges in
all three horizontal evidence bands; deterministic optional luma noise; and known independent
field translations, cuts, fades and a segment reset. It is deterministic for a given seed and
noise setting; the default fixture is 347 units (262 MB, generated in a few seconds, never
committed).

`field_registration_truth.c` loads the engine from the library path it is given, checks the header and
library ABI sizes, streams the raw units, and calls `begin_segment` where the truth CSV marks a
new acquisition epoch. Source, include and library paths are caller-controlled.

## Assertions

- On `expect=match` rows the applied `d1`/`d2` must equal the known physical translation,
  including one-unit events — the immediate measurement may be correct while the longer
  trajectory state is still in its confirmation dwell.
- On `expect=abstain` rows (a hard cut and every fade step) both trajectory decisions must be
  Unknown. Holding the already-known applied phase is allowed; inventing a new decision is not.
- Zero opposite-direction corrections.
- p95 processing cost below 33.37 ms per 29.97-frame unit (16.68 ms per field) — a real-time
  correctness guard, not a benchmark.

Expected summary (semantic counts are exact; timing is machine-dependent):

```
synthetic truth: rows=347 unambiguous=338 ambiguous=9
applied truth agreement: 100.000% (338/338)
ambiguous abstention: 100.000% (9/9)
opposite-direction corrections: 0
RESULT: PASS
```

## What this does and does not say

The engine gets every synthetic physical offset right — field-1 +1, field-1 +2, a single-unit
field-1 event, and the symmetry check of field-2 +1 — abstains on all cut/fade rows, and never
corrects in the opposite direction. Many unambiguous units report an Unknown trajectory decision
during the configured confirmation window; that is expected, and the golden does not count that
dwell as a failure.

This is a controlled integer-translation test, not proof against every analog waveform: it does
not synthesize heterogeneous within-field phase, sub-line phase, missing USB bytes, or a real
decoder's noise distribution. Measurements on real captures remain extended validation; they are
not needed to run this golden.

## Gated trajectory-redesign fixture

`make trajectory-test` runs a second, deliberately falsifying golden. It emits
two independent labels per unit: the physical location of the designated main
picture and the endpoint-constrained trajectory-policy oracle described in
`../TRAJECTORY.md`. A smaller right-hand asset may carry a conflicting phase;
it is evidence, never the main-picture label.

The fixture includes a real one-unit displacement; coherent physical field-1
and common-mode displacements alternating every unit (which must be followed);
an edge-only secondary artifact; a false-edge chatter negative control; a
coherent provisional inversion; weak/localized estimator chatter; a non-settling horizon;
an epoch reset, upward `-1`/`-2` offsets, common-mode `(-2,-2)`, a multi-phase
raster whose two outer evidence bands disagree with its designated main
picture, a fade while a candidate is active, and flat/dark content with intact
hard padding. It also contains a synthetic version of the timeline-frame-8169
stale latch: one positive `(0,1)` observation followed by 103 flat units while
the committed phase is `(1,0)`.

It additionally freezes two source classes measured after v6. Relative-only
static registration deliberately removes a trustworthy absolute envelope while
leaving a broad, temporally static picture body. The decisive release sequence
first locks `(1,0)`, then returns to `(0,0)` for 12 units: same-parity temporal
registration identifies field 1 on the first return and a persistent static
comb minimum establishes `d2-d1 == 0` thereafter. Mirror cases cover a sustained
`(1,0)` phase, a relative-only onset, and an epoch whose absolute gauge is never
known. Negative controls are an alternating-line card, a sub-16-column local
overlay, a scene cut, inter-field motion without a static-region consensus, and
a nominal raster. A no-evidence unit immediately after the release asserts that
the relative presentation did not replace the committed absolute lock.

The boundary class moves field 1 down five lines, clips source content at the
Shuttle's hard-padding row 261, and requires the visible body motion plus the
censored lower boundary to establish `+5`. Its negative control presents the
same top/boundary landmarks over a stationary body. Repeated leading lines and
their chroma are diagnostic only and are not synthesized as authority.

Frozen v6 scores before the relative-only implementation are:

```
relative-only-return-temporal-gauge  0/12
relative-only-sustained-plus1-guard 12/12
relative-only-onset-temporal-gauge   0/12
relative-only-gauge-unknown           0/15
bottom-censored-field1-plus5          0/12
all five relative false-positive guards 12/12 (scene-cut 1/1)
```

The complete pre-change fixture scores 1,168/1,220 against raster truth and
1,283/1,344 against the trajectory oracle. Ten of the 61 oracle differences
remain the deliberately archival-only provisional inversion; the other 51 are
the new deciding relative/boundary failures. The gauge-unknown warmup is an
additional intentional difference between physical raster truth and the
zero-lookahead presentation oracle, but it is not an oracle failure.

The live authority golden requires exact agreement for physical unit-rate
jitter, localized false-edge chatter, upward `-2` cases, the stale-hold class,
flat content with intact transport padding, and the multi-phase main-picture
class. Per-scenario output reports raster/oracle matches, common-gauge and
transport/content abstentions, and trajectory resets. The deliberately
provisional inversion remains an explicitly reported archival-only oracle
disagreement: no zero-latency estimator may claim to know that coherent raster
geometry will later prove provisional.

Algorithm v7's expanded fixture has 1,398 units and 1,273 raster-known rows.
The forward live engine matches 1,272/1,273 raster rows and 1,388/1,398
trajectory-oracle rows. The sole raster mismatch is the intentionally
gauge-unknown acquisition warmup; all ten oracle mismatches are the explicitly
archival-only provisional inversion. The deciding relative-only release,
sustained-phase mirror, temporal-gauge onset, unknown-gauge sequence,
bottom-censored `+5`, and every false-positive guard pass. The harness also
asserts provenance: relative authority is present on the release and onset
classes, the unknown-gauge class is labelled on every row, and a minimum that
confirms an already committed phase remains a guard rather than being labelled
as new relative-only authority.
