# Frameserver sidecar

The frameserver publishes corrected interlaced UYVY units immediately and writes an optional CSV
decision sidecar. Schema `13` keeps the transport, signal-state, applied-pair,
publication, and loss-accounting columns from schema 3. Between them it replaces
the retired v7 evidence graph with two identical per-field groups:

```text
fN_reason,fN_gauge,fN_insert_present,fN_insert_bytes,fN_insert_relation,fN_caption_confirmation,fN_parity_candidates,fN_fallback_candidates,fN_gauge_line,fN_gauge_bytes,fN_gauge_amplitude,fN_geometry_d,fN_blank_mean,fN_blank_chroma_noise,fN_body_witness_valid,fN_body_shift,fN_body_mad,fN_body_geometry_agrees,fN_body_reference_top,fN_body_implied_top,fN_body_differential,fN_body_common_mode,fN_picture_position_valid,fN_measured_picture_top,fN_picture_from_body,fN_recorded_first,fN_recorded_last,fN_raw_top,fN_raw_bottom,fN_switch_line,fN_first_full_other_head_line,fN_rf_peak_line,fN_rf_peak_position,fN_raw_span,fN_picture_rows,fN_band_extent,fN_observed_switch_line_count,fN_switch_count_agrees,fN_switch_count_conflict,fN_switch_signature,fN_switch_measurable,fN_geometry_measurable,fN_lock_state,fN_zero_source,fN_lock_id,fN_lock_top,fN_lock_switch_line_count,fN_lock_switch_line_count_known,fN_clip_state,fN_clip_ceiling,fN_expected_bottom,fN_lines_lost,fN_invariant_residual
```

`drop_reason` is `None`, `PoolFull`, `PublisherFull`, or `RingFullTail`.
`fN_*_line`, recorded bounds, top, bottom, lock-top, clip, and expected-bottom
values use NTSC line numbers; `rf_peak_position` is a horizontal sample index.
The schema also records `comb_correction` and the ordinal where
the current nonzero correction was installed; `-1` means none. `comb_safe`
requires valid locks, calibrated parity, and an honored correction. Exact
semantics are in `../field_registration/README.md`.

- A pool-full observation retains its own ordinary row, is unpublished, and says `PoolFull`.
- Ring-full observations cannot reach the worker individually. Their count is attached to the
  next retained row as `preceding_ring_drops`, locating the omitted ordinal range immediately
  before that row.
- If no later observation exists, one synthetic `RingFullTail` row is emitted. Its `ordinal` is
  the first omitted ordinal and `preceding_ring_drops` is the number of omitted observations.
  It is a range marker, not a captured video unit.
- `PublisherFull` means analysis completed but no output surface was available.

These rules preserve the conservation relation between ingress observations, sidecar rows/ranges,
and published or explicitly dropped units. Registration has no live trajectory or FIFO in v10;
the per-field lock and hold semantics are defined in
[`../field_registration/README.md`](../field_registration/README.md).
