# Plain comb: first capture-1 locks, no nonzero applied pair

Implements the owner's 2026-09-11 plain-energy instruction and the subsequent
two corrections: switch measurability is not a prerequisite for either lock
confirmation route, and the comb is not evaluated under a maintained lock.
No contract, switch detector, box detector, signal classifier, render or
profiling change. This is an engine handoff, not a capture acceptance.

## Reader and acquisition

The energy is the mean absolute vertical second difference of the current
woven picture. Both parities center the three-sample stencil; all 720 raw
luma samples contribute within the overlapping picture aperture. The existing
geometry supplies its top and bottom (or recorded last row if the switch is
unknown). No horizontal low-pass, temporal mask, dominance test, support cutoff,
or margin threshold remains. No preceding unit is required.

All relative shifts with a complete stencil inside both 240-position field
windows are searched, not just -2..+2. Mean energies are compared by integer
cross-products; an exact tied minimum does not confirm. This simple ranking
uses each candidate's overlap. It does not assert full-range alias rejection
or static scene identity. The harness's small-range product census and its
margin ratios are not this statistic and are not acquisition thresholds.

The existing candidate-versus-standard order check remains. The comb does not
install its minimizing shift as a correction. Both fields must have placeable
measured geometry before comb acquisition; unknown boxed geometry remains
unknown. Caption confirmation remains the other route. Neither route requires
a measurable switch. At acquisition a measured switch supplies its count;
otherwise that count stays Unknown (-1 with known=false), not zero or a seed.
Later observations do not silently establish a previously unknown count.

Once both fields are locked, geometry tracking continues but `comb_confirm`
is not called. Acquisition/reacquisition can evaluate again after the existing
lock-reset paths. This guard is in the same change as the new reader: the new
reader must not introduce a new continuous evaluation obligation.

## Schema 21 handoff

Column layout is unchanged. `comb_check=not_evaluated` means a maintained lock,
distinct from `flat` (evaluated but no unique result) and from signal-gated
`n.a.`. Its best/candidate shifts are Unknown, energies are placeholders, and
`comb_safe` is false because there is no current agreement reading. Do not
interpret that flag as a bad locked frame. Lock state is recorded separately.
`comb_static_fraction` is deprecated and always zero, not a measured fraction.
`comb_unresolved_alternatives` now counts exact ties, not failed dominance tests.
Legacy luma-cache storage is reserved but unused; it supplies no evidence.
Coordinates retain the pre-existing schema-20 convention in this change.

## Capture 1, actual parser/classifier/engine/publisher path

Final log: `/private/tmp/plain-comb.ZNrk82/handoff.csv`.
SHA-256: `0847c8fa14ddd0f73ef44221e4baacbb5d85e8dd0cbc34434dce420cd4a1924f`.

930 observations: 919 exact published units, six short, three unframed, two
device-no-signal. Zero holes, pool/ring/surface/output/log drops, or log errors.
Registration ran on 452 units. Comb: 4 agreements, 148 disagreements, 300
maintained-lock units not evaluated. The other 478 observation rows had no
engine evaluation. There are **302 locked exact units**, versus zero previously.
All **919 published applied pairs are (0,0)**, including all 302 locked ones.

The first fresh comb lock is at counter **6269**, in the pre-program interval
that the unchanged classifier calls ProgramLike. That is not used as evidence
of a clean program lock. From counter 6667 onward there are 508 exact units,
296 locked: the fresh acquisition is **6811**. The visible locked intervals
are 6811-6813 and 6882-7174; the latter is retained state returning after the
signal gate, **not another fresh acquisition**. Overall, 6269 acquires with
both counts Unknown; 6811 acquires with both measured counts known.

The result is a first lock, not demonstrated corrective movement. Four comb
agreements are not four locks: two have one field's geometry unresolved and
do not acquire. Categorical boxing still supplies no measured geometry; this
change does not manufacture bounds to make the card acquire.

Reproduce without rendering or profiling:

```sh
make -C src/frameserver frameserver_replay CFLAGS='-O3 -std=c11 -Wall -Wextra -Werror'
src/frameserver/frameserver_replay CAPTURE1 FRESH.csv --pace-us 16000 --ring-mb 512 --pool 32
python3 src/field_registration/tests/plain_comb_replay_check.py FRESH.csv
```

The check records denominators, lock counts, applied pairs and optional keyed
baseline differences. Use observation ordinals, not a join that drops Unknowns.
The older `run-timing.DdLgYt/worker-final.csv` differs on six S-only readings;
its asserted-identical-observations comparison failed, so it is not used as an
exact pre-change baseline. No change to `measure_field` is in this patch.
An exact pre-change replay was therefore built from the engine at `3bc8fe1`
with the otherwise unchanged current frameserver. Its log is
`/private/tmp/plain-comb.ZNrk82/before.csv`, SHA-256
`b711d90d6a4718203990c7ad374b5458a4867b6abf80af4f517e304f539e3c25`.
The ordinal join now passes: zero changed counters, appearance/source labels,
registration eligibility, raw tops, T/S observations, geometry/switch
measurability flags, or applied pairs. This baseline has zero locks. Both
replays use schema-21 serialization; only the baseline engine is old.

## Tests and limitations, including failures

The initial new public test failed **2/7 passed** against the old engine:
`plain_comb_reads_first_unit_without_temporal_witness`,
`plain_comb_confirms_measured_geometry`,
`current_unit_energy_needs_no_static_mask`,
`remote_relative_error_remains_visible`, and `equal_energies_do_not_confirm`.
The final expanded public test passes 23/23, including optional counts in
neither/either field, maintained-lock non-evaluation and unplaceable geometry.
The direct energy test passes 23/23, including independent explicit-weave
arithmetic, relative shifts -4..+4, ties, no aperture, and the caption OR route.
Both pass ASan/UBSan.

The old comb test reported **14/19**, and unlocked-placement **23/24**, before
their temporal-witness expectations were amended. The old periodic-abstention
assertion also failed: ordinary mean ranking over different overlaps does not
provide the removed pairwise alias guarantee. That guarantee is withdrawn,
not claimed preserved. The final comb and placement tests pass 18/18 and 24/24.
The rule-1 suite initially aborted verbatim:

```text
Assertion failed: (decision.field[0].lock_state == FIELDREG_LOCK_UNLOCKED), function main, file field_registration_v10_rule1.c, line 62.
make: *** [test] Abort trap: 6
```

That assertion required a qualified caption to fail without a switch. It now
requires the confirmed geometry to lock and its absent count to remain Unknown.
The full field-registration suite passes. The synthetic frameserver signal-gate
test also passes, including nonzero (2,0) placement before the gate and a held
published crop through mute. Rule tests run correctness only by default;
their existing benchmark loops require `FIELDREG_BENCHMARK=1` explicitly.

**Known open pan:** the historical product-energy failure in `STATIC_MASK.md`
remains. The new plain reader is also directly falsified by a constructed
fixed-geometry coherent pan: true displacement 0, minimizing shift +2,
energy 22.124053563 versus next 58.302142185. The test asserts reproduction
of the failure, not correct registration. The maintained-lock guard removes
fresh evaluation there; the acquisition ambiguity remains open. No new mask,
threshold, or motion classifier is added to defend against it.

The first sandboxed replay returned `open failed`; the authorized local replay
outside that sandbox completed. No hardware capture or raw-image dump occurred.
Historical `static_comb_test.c` and `comb_compare_probe.c` target the removed
private masked-reader API; replay them with the pre-change engine, not this
one. Current reader tests are `plain_comb_test` and `plain_energy_test`.

The harness owns the locked render next, including the owner's overlays and
line-placement requirements. Profiling remains after that render.
