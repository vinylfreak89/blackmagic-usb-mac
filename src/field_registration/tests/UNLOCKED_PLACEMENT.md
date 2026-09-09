# Unlocked geometry is not applied placement

Contract rule 8: "The output picture never moves except at a segment's initial
lock and after a re-acquisition." Scope: application ownership only. The top,
switch, box classifier, acquisition requirements, signal classifier, comb metric
and static mask are not changed.

`v10_decide_field` still produces the geometry proposal and caption evidence.
The existing comb acquisition can inspect that proposal. Only after both
acquisition paths have run does `apply_locked_geometry` commit each locked
field's crop. An unlocked field holds its last applied value (standard after
init/reset), with `Acquiring` / `Hold` on measurable unconfirmed geometry.
Measured offsets and raw rows are retained, not replaced by the held crop.
This is a per-field gate, not a new requirement that both fields acquire together.

When application rejects a proposal, comb diagnostics are evaluated at the
actual held crop; the existing standard reading is reused where possible.
The saved temporal crop is also the actual applied crop. Publication remains
downstream and contributes no lock or crop state.

## Tests

Failing-first commit: `8ea7dbb`. Constructed flat picture with moving edges at
offsets 1, 3, 0, 1 has no confirmation. The committed golden returned:

```
FAIL: unlocked_geometry_cannot_move_output
FAIL: unlocked hold is labelled
FAIL: unlocked_geometry_cannot_move_output
FAIL: unlocked hold is labelled
FAIL: unlocked hold is labelled
FAIL: unlocked_geometry_cannot_move_output
FAIL: unlocked hold is labelled
FAIL: loss restores standard until re-acquisition
UNLOCKED-PLACEMENT: 12/20 passed
```

After the gate: 20/20; four additional checks protect the applied baseline and
saved temporal crop, giving 24/24, also under ASan/UBSan. The existing comb
test remains 19/19, including acquisition and tracking after acquisition.
The rule-4 fixture still acquires from a caption at +2 on its first unit.

The first full-suite run exposed an obsolete rule-1 application assertion:

```
Assertion failed: (decision.applied_d1 == expected_d[i]), function main, file field_registration_v10_rule1.c, line 59.
make: *** [test] Abort trap: 6
```

That fixture never has a measurable switch or a lock; its geometry and caption
agreement/disagreement expectations are preserved, but its applied crop now must
hold zero. The rule-3 fixture likewise retains every line-account measurement
while applying zero before confirmation. Neither fixture's raw input changed.

The initial draft also assumed a fresh common-mode +1 synthetic unit would
acquire from comb on its second call; that control failed before any fix
(`FAIL: comb acquisition still applies its confirmed geometry`). It was not
an established passing control. The committed test instead protects the existing
zero-offset comb acquisition and subsequent +1 tracking, while rule 4 protects
nonzero caption acquisition. No change to the comb was made to force that draft
expectation to pass.

Frameserver integration passes: publisher/logger isolation, failed-delivery
held-crop ownership, log-overflow reporting, deterministic wakeup race, audio
publisher, frame publisher and frameserver tests. These run with native IOSurface
access. A sandboxed process-inspection attempt returned
`zsh:1: operation not permitted: ps`; native inspection confirmed the remaining
synthetic benchmark was CPU-bound, not a shutdown hang.

Final `make -C src/field_registration test`: unit 18/18, CEA-608 3/3,
rule 1 5/5, rule 3 2/2, rule 4 5/5, switch timing 32/32, comb 19/19,
unlocked placement 24/24. Its repeated synthetic calls reported the following
wall-clock costs (not the commercial worker measurement below):

| fixture | median ms/unit | p95 ms/unit |
|---|---:|---:|
| rule 1 | 21.319 | 26.133 |
| rule 3 | 92.518 | 127.737 |
| rule 4 | 102.769 | 272.131 |

All three print `PERFORMANCE BUDGET EXCEEDED`; correctness passes do not close
the performance backlog.

## Commercial live-path replay

```
make -C src/frameserver tests/queue_bench
src/frameserver/tests/queue_bench CAPTURE FRESH_SIDECAR.csv
```

Whole original `composite_program_30s.tpc`, through the real parser, classifier,
analysis worker and asynchronous sinks; paced at 16000 us per transfer.
930 observations, 919 exact units, 919 published; input pool/ring drops,
publication drops, log queue drops and log errors all zero. Registration ran on
452 units; neither field acquired a lock. All 930 rows have:

| quantity | nonzero rows |
|---|---:|
| applied_d1 | 0 |
| applied_d2 | 0 |
| geometry_lock_known | 0 |

Before: field 2 applied +1 at counters 6692, 6710, 6713, 6744, 6768, 6791,
6807; +3 at 6705, 6783, 6792, 6801. After: those same measurements remain
visible, each labelled Acquiring with applied zero. Comparison against the
pre-gate queue replay found zero changes in ordinal/counter, source/appearance,
registration eligibility, either field's raw top, geometry offset or switch line.
Comb census stays 449 flat / 481 not applicable; no confirmations manufactured.

Actual analysis-worker time, including classifier and bounded copy/enqueue but
excluding asynchronous sinks: all exact units median **2.509 ms**, p95
**14.111 ms**; the 452 registration calls median **9.140 ms**, p95
**16.330 ms**. The p95 exceeds the 10-ms budget; optimization remains deferred,
not claimed passed. Engine state remains 189108 bytes; no new allocations.

Sidecar: `/private/tmp/v10-unlocked-commercial.G71zXe/registration.csv`.
SHA-256: `4f1cb497888bae04fe07663218b99f7f204faa90ca58eaf55887c43fea68d184`.
This closes unlocked application, not capture-1 acceptance or its zero-lock issue.
