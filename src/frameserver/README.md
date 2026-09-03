# Frameserver sidecar

The frameserver publishes corrected interlaced UYVY units immediately and writes an optional CSV
decision sidecar. Schema `3` has this exact header:

```text
ordinal,counter_extended,transport,kind,appearance,appearance_confidence,source,source_confidence,interval_id,unsettled,provisional_d1,provisional_d2,applied_d1,applied_d2,baseline_d1,baseline_d2,settled_known,settled_d1,settled_d2,resolution,evidence_mode,confidence,relative_only,relative_only_gauge_unknown,relative_only_gauge_source,relative_only_phase,relative_only_best_energy,relative_only_runner_energy,relative_only_prior_energy,relative_only_margin,relative_only_ratio,relative_only_static_columns,relative_only_persistent_columns,relative_only_transport_gate,relative_only_cut_gate,bottom_f1_censored,bottom_f2_censored,published,drop_reason,schema_version,preceding_ring_drops
```

`drop_reason` is `None`, `PoolFull`, `PublisherFull`, or `RingFullTail`.
The `relative_only_*` columns preserve the static-region curvature decision,
absolute-gauge provenance, winner energies/margins, spatial support, and gates.
`bottom_f*_censored` distinguishes a measured boundary from a complete lower
picture edge. Their semantics are specified by the registration contract.

- A pool-full observation retains its own ordinary row, is unpublished, and says `PoolFull`.
- Ring-full observations cannot reach the worker individually. Their count is attached to the
  next retained row as `preceding_ring_drops`, locating the omitted ordinal range immediately
  before that row.
- If no later observation exists, one synthetic `RingFullTail` row is emitted. Its `ordinal` is
  the first omitted ordinal and `preceding_ring_drops` is the number of omitted observations.
  It is a range marker, not a captured video unit.
- `PublisherFull` means analysis completed but no output surface was available.

These rules preserve the conservation relation between ingress observations, sidecar rows/ranges,
and published or explicitly dropped units. The registration engine's semantic trajectory fields
are defined in [`../field_registration/TRAJECTORY.md`](../field_registration/TRAJECTORY.md).
Full raw evidence vectors and audio serving remain named P3 gaps.
