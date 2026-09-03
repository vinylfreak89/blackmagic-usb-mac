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

The fixture includes a real one-unit displacement, an edge-only secondary
artifact, a coherent provisional inversion, chatter, a non-settling horizon,
an epoch reset, upward `-1`/`-2` offsets, common-mode `(-2,-2)`, a multi-phase
raster whose two outer evidence bands disagree with its designated main
picture, a fade while a candidate is active, and flat/dark content with intact
hard padding. It also contains a synthetic version of the timeline-frame-8169
stale latch: one positive `(0,1)` observation followed by 103 flat units while
the committed phase is `(1,0)`.

The current caller rewrites only abstaining rows, so this target is expected to
print `CURRENT-LIMITATION-REPRODUCED: YES`. The current top-edge search is also
expected to fail sustained upward `-2` cases: this is a required falsifying
characterization, not a test expectation to weaken. Per-scenario output reports
raster/oracle matches, common-gauge and transport/content abstentions, and
trajectory resets. A future trajectory implementation must improve the
trajectory-oracle score without silently relabeling physical-raster
disagreements as successes.
