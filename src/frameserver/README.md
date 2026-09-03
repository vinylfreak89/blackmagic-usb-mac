# Frameserver sidecar

The frameserver publishes corrected interlaced UYVY units immediately and writes an optional CSV
decision sidecar. Schema `2` has this exact header:

```text
ordinal,counter_extended,transport,kind,appearance,appearance_confidence,source,source_confidence,interval_id,unsettled,provisional_d1,provisional_d2,applied_d1,applied_d2,baseline_d1,baseline_d2,settled_known,settled_d1,settled_d2,resolution,evidence_mode,confidence,published,drop_reason,schema_version,preceding_ring_drops
```

`drop_reason` is `None`, `PoolFull`, `PublisherFull`, or `RingFullTail`.

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
