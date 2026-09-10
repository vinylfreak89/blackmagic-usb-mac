# Static mask: real-picture calibration and a falsifying pan

Historical experiment. The 2026-09-11 owner instruction supersedes the later
recommendations in this report to retain a mask: production now uses plain
comb energy. The pan falsification remains a known open acquisition case;
see [PLAIN_COMB.md](PLAIN_COMB.md) for the current reader and maintained-lock
guard. The historical margins below are product-energy margins, not the new
mean-absolute-second-difference measurement.

Diagnostic only; no production comb, classifier, queue or contract change.
The current brief explicitly requests the four named SP/SP-off controls in
addition to capture 1. They are tested here, not advanced through acceptance.
Capture 2 is not processed or assigned an expected abstention.

## Calibration before the pan test

Load named exact units and their immediate same-field predecessors with the
existing `oracle.walk_exact_units` CAP1 walker, without slice-boundary exceptions
or early termination. Inspect the paired raw pictures, then annotate a stationary
picture patch. Measure absolute differences of eight-pixel horizontal luma SUMS
at the same field coordinates between the two units. No noise is measured on
the device's generated blanking. Tolerance for this experiment is the largest
observed patch difference, separately per field, frozen before the other units
and pan are tested. This is a finite observed envelope, NOT a statistical bound
on future noise or an automatic per-recording calibration algorithm.

| Source / pair | Field-relative patch y, x (half-open) | Samples per field | f1 median / p95 / max | f2 median / p95 / max |
|---|---|---:|---|---|
| Commercial 6686→6687 | [60,140), [240,640) | 4,000 | 9 / 40 / **107** | 9 / 39 / **100** |
| SP 13652→13653 | [40,80), [80,200) | 600 | 36 / 101 / **173** | 36 / 106 / **162** |
| SP-off 738→739 | [15,45), [400,496) | 360 | 34 / 101.05 / **154** | 29 / 98.15 / **146** |

Coordinates are fixture annotations from inspected picture, not detection
constants. Patches are printed detail on the commercial card and stationary
background on the other two sources. In averaged-luma units, the tolerances are
**13.375/12.500, 21.625/20.250, 19.250/18.250**, respectively. They include the
observed analog fluctuation at those coordinates; they do not separate every
horizontal timing fluctuation from level noise.

Rejected calibration: initially using the SP patch coordinates on SP-off 739
included moving foreground. Its f1 median/p95/max was 69/552.3/1008 summed codes.
That is not a static noise sample. It was discarded on the raw paired image,
not because of a comb verdict. The new stationary background patch was selected
before rerunning the comparison. No universal transfer of a patch or tolerance
between recordings is asserted.

## Golden comparison

Use the positive-product energy, fixed samples [24,696), and common field-row
indices [3,237) for all five shifts -2..+2. This is 157,248 raw pixels (19,656
eight-pixel blocks), not the earlier harness's 238-row census aperture. Compare
maskless aggregation against the calibrated temporal mask, keeping every other
part identical. The mask retains the production stencil: both f1 rows and all
f2 neighbors required by any of the five candidates must pass at both times.
No margin threshold enters the energy calculation.

| Counter | Expected and both measured shifts | Maskless margin | Masked margin | Support retained |
|---|---:|---:|---:|---:|
| 6687 | 0 | 3.412 | 3.411 | 99.705% |
| 6690 | 0 | 3.381 | 3.419 | 99.634% |
| 6700 | 0 | 3.295 | 3.336 | 99.227% |
| 13653 | -1 | 3.222 | 2.131 | 86.971% |
| 13972 | 0 | 3.060 | 2.978 | 96.963% |
| 739 | 0 | 3.340 | 3.158 | 81.950% |
| 333 | +1 | 3.566 | 3.602 | 90.715% |

Inspected the five raw weaves for each SP/SP-off control: the stated candidate
is clean and its adjacent candidates have teeth. Commercial controls were also
inspected in the preceding diagnostic. No program images are committed.
Calibration restores picture support without changing any named golden's
winner. It does **not** improve all margins; at 13653 it reduces the margin.

## Coherent vertical pan: high margin can be wrong

Construct an aperiodic, piecewise-linear vertical scene, sampled at successive
interlaced field times. The source picture/blanking geometry remains fixed at
zero displacement. Content moves down **four full-frame lines per field
interval**, eight between same-field units. The later field then matches the
earlier field's spatial phase at candidate **+2**, not zero. This is motion,
not a registration displacement. Seed 1729, eight-pixel horizontal patches,
30–220 luma knots and ±0.5 additive noise are explicit synthetic fixture
parameters, not claims about the recordings.

Measured energy vector for d=-2..+2:

    2311.011745, 2303.258089, 2341.859090, 831.434983, 0.000811363

Maskless winner **+2**, margin **1,024,738.784×**, true geometry shift **0**.
The same construction with independent noise drawn from each calibration
patch's signed eight-pixel-average temporal differences still selects +2:

| Empirical difference-noise distribution | Wrong winner's margin |
|---|---:|
| Commercial | 1,426.517× |
| SP | 83.476× |
| SP-off | 123.630× |

These sampled *differences* are injected as per-raster additive noise for a
stress control; they are not claimed to reconstruct the analog noise process.
The result is not dependent on the initial near-noiseless fixture.

Rule 9 protects placement: geometry still chooses zero. It cannot make this
motion-induced comb result a valid confirmation/veto, nor by itself enforce
the contract's "without static detail ... reads nothing" at acquisition.
Raising a margin requirement does not solve an ambiguity that can have this
much margin. Static eligibility must survive in some form.

The recalibrated pixel mask is **also not sufficient by itself**:

- Commercial tolerance retains **zero** pixels: correctly no reading.
- SP tolerance retains **16/157,248** pixels (two blocks); they spuriously
  prefer +2 with zero energy and nonzero alternatives.
- SP-off tolerance retains **8/157,248** pixels (one block), with tied minima
  at -2 and +2: no unique reading.

Thus the mask has a measured useful purpose against the pan, but the current
"any surviving support" approach still admits accidental temporal matches.
Do **not** delete static checking in favor of margin + rule 9. Do **not** ship
only this tolerance replacement either. Retain static-evidence checking for
the next prototype, with an explicitly tested static-*detail* measurability
condition; the required support cannot be inferred from these seven goldens.
This turn does not invent a minimum sample count or certify a new detector.
Maskless aggregation alone fails the pan; a recalibrated mask alone fails the
sparse-support control. Both falsifications are useful results.

## Reproduction, tests and cost

    python3 src/field_registration/tests/static_mask_probe.py /tmp/static-mask --case commercial
    python3 src/field_registration/tests/static_mask_probe.py /tmp/static-mask --case sp
    python3 src/field_registration/tests/static_mask_probe.py /tmp/static-mask --case off
    python3 src/field_registration/tests/static_mask_probe.py /tmp/static-mask

First loads run full provenance checks, then cache only the named luma rasters.
Subsequent runs use those scratch caches; remove/recreate the task cache to
verify the capture again. These are diagnostics, not a replacement reference.
Assertions passed: `seven_raw_goldens_preserved`,
`high_margin_pan_false_minimum_reproduced`, `sparse_mask_failure_reproduced`.
The last two mean the proposed defenses are falsified, not production passes.

The first diagnostic exposed a margin-reporting overflow for a zero-energy
minimum, verbatim: `RuntimeWarning: overflow encountered in scalar divide`.
Reporting now distinguishes `infinite` and `tie` explicitly without changing
energies or mask support. The corrected run emits no warning.

Scratch results `/private/tmp/v10-static-mask/results.json`, SHA-256:
`116a152e18ae5a081b71e3cb4d64d49a44136097eaef0b77515627ec46771b57`.
Paired images and five-shift weaves are in the same scratch directory.
Python diagnostic mask+five energies on seven cached units: median **2.535 ms**,
p95 **2.824 ms** (sorted floor(0.95*(N-1)), one sample per unit). This excludes
I/O and calibration and is NOT an engine/whole-worker benchmark. Production
unchanged; no new production speed or budget claim is made.
