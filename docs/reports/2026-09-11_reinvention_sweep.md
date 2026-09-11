# Reinvented instruments removed, 2026-09-11

Owner: "make sure it deletes any garbage scratch of things I already fucking asked for that it
"rewrote" rather than editing. I all its little "experiments" it didn't fucking find and
re-invented (wrongly) before gone"

Scope applied: a file is in scope only where a PRE-EXISTING file measures the same object and I
did not find it. Established from each file's own docstring, not from memory. Recoverable from
git; nothing here is lost.

| removed | sha256 | bytes | the predecessor I failed to find |
|---|---|---|---|
| peak_line.py | ba02d0bf53e05f67 | 4385 | rf_peak_census.py - the head switch's RF peak, where along the row |
| peak_vs_s.py | 1d95eaf9db4e7de6 | 8204 | rf_peak_census.py + displaced_row_census.py - peak vs the harness's S |
| recovery_ramp.py | 93ce280a2ad03e4b | 4693 | rf_peak_census.py |
| t_adjudication.py | d42885813d42bbd1 | 4482 | switch_geometry.py + displaced_row_census.py |
| t_adjudication_panel.py | cb9f583864c6acb0 | 4278 | switch_panel.py - raw rows across the band so a reader can look |
| blanking_boundary.py | 48454c9e3f10c954 | 4985 | tear_column_census.py - where the switch's blanking sits in the window |
| picture_in_blanking.py | dd9563aee974f2d9 | 5072 | porch_census.py - is the blanking inside the window on an ordinary row |
| own_blanking_census.py | 6ba5393e70e09b65 | 9110 | porch_census.py |
| switch_instant.py | dc5a47cce68c0346 | 8900 | switch_geometry.py - per-unit per-field geometry under the contract |

## KEPT, with the reason, because the instruction is not 'delete everything new'

- `blanking_extent.py` - VOID as a result, but 11 references including Codex's committed
  `blanking_extent_review_controls.py` and `blanking_extent_guard_review.py`, which test it BY
  NAME. Removing it would break another agent's review artifacts.
- `timing_disturbance.py` - imported by `no_jump_reference.py`.
- `top_skew_row.py`, `switch_without_shift.py` - Codex required these as keyed executables
  rather than prose summaries.
- every `*_review*.py` / `*_audit.py` / `fixture_review_support.py` - Codex's review probes,
  not mine to delete.
- `band_render.py` - the owner's explicit call, and a separate one-off.
- instruments with no predecessor: `source_reference.py`, `per_unit_floor.py`,
  `end_observability.py`, `end_sweep.py`, `ends_inside_why.py`, `dither_compare.py`,
  `dither_displaced.py`, `settled_bias.py`, `matched_control_texture.py`,
  `calibration_qualification.py`, `switch_fixtures.py`, `no_jump_reference.py`,
  `run_all_checks.py`, `owner_queue_check.py`, `superseded_check.py`,
  `withdrawn_figure_check.py`, `cited_commit_check.py`.

Already removed in 36586d3: review_frame.py, locked_render.py, locked_render_check.py -
predecessor review_render.py, which already built frames and already rendered.

## Loose scratch probes removed from /private/tmp

One-off probes written outside the repo instead of finding or extending an existing
instrument. CLAUDE.md already records the hazard they create: a figure resting on an
uncommitted instrument cannot be re-run, so it is unfalsifiable. Anything that produced a
standing result was rebuilt into `experiments/` before this sweep.

```
167        /private/tmp/badprobe.py
2599       /private/tmp/basis.py
2782       /private/tmp/bm_extract.py
3389       /private/tmp/bm_measure.py
3661       /private/tmp/boundary.py
3865       /private/tmp/boundary2.py
917        /private/tmp/check_regen.py
2909       /private/tmp/combgate.py
714        /private/tmp/composite_bottom_panel.py
2816       /private/tmp/decide.py
3568       /private/tmp/decide2.py
2138       /private/tmp/drift.py
1235       /private/tmp/extract_target_cap1.py
3094       /private/tmp/gap_test.py
2325       /private/tmp/halfline.py
1481       /private/tmp/inspect_v3_top.py
2584       /private/tmp/joint.py
3548       /private/tmp/joint2.py
4126       /private/tmp/joint3.py
2088       /private/tmp/l22.py
1512       /private/tmp/l23raw.py
2408       /private/tmp/lock_audit.py
2854       /private/tmp/motion.py
3446       /private/tmp/motion2.py
2258       /private/tmp/ownts.py
2332       /private/tmp/peakline.py
2685       /private/tmp/peakline2.py
3575       /private/tmp/picinblank.py
2954       /private/tmp/prefix_census.py
604        /private/tmp/probe_b.py
933        /private/tmp/probe_c.py
519        /private/tmp/probe_class.py
764        /private/tmp/probe_d.py
697        /private/tmp/probe_e.py
476        /private/tmp/probe_f.py
801        /private/tmp/probe_g.py
564        /private/tmp/probe_h.py
462        /private/tmp/probe_i.py
266        /private/tmp/probe_j.py
3227       /private/tmp/qualified.py
3693       /private/tmp/ramp.py
3626       /private/tmp/ramp2.py
2047       /private/tmp/refcmp.py
2278       /private/tmp/refcmp2.py
3677       /private/tmp/reli.py
4341       /private/tmp/reli2.py
813        /private/tmp/row_samples.py
2921       /private/tmp/shape.py
3190       /private/tmp/shape2.py
1943       /private/tmp/thr.py
3275       /private/tmp/topskew.py
11932      /private/tmp/turn10_probe.py
466        /private/tmp/v10-gate-bench-generate.py
1364       /private/tmp/v10-loss-record.py
998        /private/tmp/v10-record-ownership.py
4739       /private/tmp/v10-remove-feedback.py
779        /private/tmp/v10_adjacent_circular.py
1069       /private/tmp/v10_center_phase.py
1167       /private/tmp/v10_consensus_adjacent.py
1092       /private/tmp/v10_crop_panel.py
6396       /private/tmp/v10_phase_probe.py
3611       /private/tmp/v10_regime_counts.py
4531       /private/tmp/v10_regime_stream.py
4714       /private/tmp/v10_signal_probe.py
2674       /private/tmp/v10_splice_panel.py
2099       /private/tmp/v10_temporal_phase.py
27433      /private/tmp/wc_full.py
```
