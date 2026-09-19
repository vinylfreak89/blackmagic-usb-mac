# v11 geometry engine

`geometry_engine.c` ports the recorded experiment rule set (ledger entries
2/5/7/10/11, amendments 1–5, reading B). It does not replace v9's API.
The census thresholds, run-in period, bottom-profile tests, search range and
1.5 inclusive comb margin are reference parameters, not new fitted thresholds.

All decisions use NTSC lines; zero in an internal census means unavailable.
Applied offsets are always numeric. Unknown placement takes the last published
placement in the section, or zero at section start. Confidence is LOW when a
comb re-run is required, HIGH otherwise; it is not a probability of correctness.

The caller owns bounded storage (`ge_size`), initializes once, and submits
720×525 luma rasters. Nothing allocates during measurement or state updates.
Aligned pairing emits immediately. Reversed pairing buffers one unit and emits
unit-keyed placements: field 1 belongs to the preceding frame, field 2 to the
current frame. Unused boundary fields use their own census placement, or zero.
EOF/gaps flush them explicitly; they are not measured woven frames.

`reset` on a unit clears both fields' previous-unit comparisons and the held,
provisional and published-placement state before the first frame containing it.
In reversed pairing this is the preceding frame, not a second reset at the next
frame. Counter gaps break adjacency. Call `ge_break` on epoch changes, missing
rasters or transport loss; it completes any pending boundary unit and clears all
history. Live classifier action dispatch belongs to the frameserver caller.

Comb arithmetic uses exact integer product accumulation and a float32 mean,
then double precision for the ratio. NumPy's float32 reduction can round the
sum differently. Acceptance requires identical shift/decided, relative margin
error ≤1e-4, and explicit reporting of values within 1e-4 of the decision boundary.
No fast-math option is used. A separate audit flag runs comb on every frame for
validation; ordinary operation runs it only on the recorded triggers.

## Validation

`make geometry-test` runs synthetic shift, missing-evidence, pairing and gap
controls and builds `tests/geometry_probe`. The probe reads external luma and
metadata without importing reference code. From the repository root:

```
python3 scripts/check_geometry_goldens.py CACHE GOLDENS SCRATCH
```

The comparator independently derives reset flags from the saved classifier
stream and compares every eligible unit, frame, comb verdict and intermediate
feature in the external goldens. It prints every mismatch and exits nonzero on
any difference. Timing uses the calling thread's CPU clock. The audit-mode
engine cost includes an all-frame comb; production-only timing is separate.
Neither captured data nor generated results belong in this directory.
