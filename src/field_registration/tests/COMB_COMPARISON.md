# Capture 1: why the two comb instruments disagree

Diagnostic at production engine b555868, synchronized through harness 7adcd96.
No production algorithm, signal-state rule or contract text changed here.
Only capture 1 was processed. The cited capture-3/4 examples remain outside
this turn's one-source scope; commercial counters 6667, 6687, 6690 and 6700
are the named raw-row controls from the previous reviews.

## Reproduction

`comb_compare_probe.c` includes the actual engine translation unit, drives its
normal classifier/registration gate through the production unit parser, and
preserves the pre-call state for diagnostics after timing the real call.
CAP1 loss/error records and parser provenance flags fail closed. It writes
scalars only. The local five-shift diagnostic is explicitly the harness's
comparison window, not a derived production search limit.

    cc -O3 -std=c11 -Wall -Wextra -Werror \
      src/field_registration/tests/comb_compare_probe.c \
      src/field_registration/cea608.c src/signal_state/signal_state.c \
      src/unit_parser/unit_parser.c -lm -o /tmp/comb_compare_probe
    /tmp/comb_compare_probe --self-test
    /tmp/comb_compare_probe CAPTURE > /tmp/comb_comparison.csv

Actual input: the original `captures/composite_program_30s.tpc`, not a slice.
Actual output: `/private/tmp/v10-comb-compare/measurements.csv`, SHA-256
`ebf961b895aebbbf72bb0a3068d2eb2e25e64a1da0d7be8b215d5768a204e4b6`.
919 exact units, 452 registration calls. Instrument's final changes add only
the synthetic self-test and rejection of an empty capture; measurement code
and the saved output are unchanged.

Native and ASan/UBSan `pixel_product_bracket_and_overshoot` pass: a middle
sample between its neighbors contributes zero; 140 between 100 and 120
contributes 800. The raw diagnostic is not a passing production comb golden.

## Same metric, same census

Independently calculated in C: field 1 starts at NTSC 23, field 2 at 286+d;
238 adjacent-row pairs, horizontal samples [24,696), positive part of
`(a-b)*(c-b)` averaged on each current raster, d=-2..+2. These exact apertures
reproduce `experiments/comb_per_unit.py`; they are not adopted engine constants.

Over 508 units from counter 6667: **506 minima at 0, two at +1 (6929, 6930)**,
median next-best/best **3.390436**. This reproduces the harness figure. The
two +1 units are not adjudicated by this diagnostic. A minimum and a margin
are measurements, not by themselves a calibrated confidence probability.

Raw woven panels, rendered with `weave_panel.py` and inspected:
`/private/tmp/v10-comb-compare/panels.png` (four counters, five shifts).
All four zero-shift crops have continuous detail; adjacent candidates show
one-line teeth. No program image is committed.

| Counter | product E(-1) | E(0) | E(+1) | Production comb |
|---|---:|---:|---:|---|
| 6667 | 77.136 | 39.258 | 87.101 | no previous witness |
| 6687 | 440.760 | 129.096 | 584.897 | ambiguous, candidate +232, 191 unresolved |
| 6690 | 440.640 | 129.908 | 588.151 | ambiguous, candidate +232, 83 unresolved |
| 6700 | 442.889 | 134.505 | 589.148 | ambiguous, candidate +232, 172 unresolved |

Counter 6667 is a legitimate difference in available evidence: the one-frame
instrument can measure weave energy; the engine has just acquired program and
cannot yet establish temporal stillness. It is not the same failure as the
later 449 ambiguous readings.

## Ablations: energy, support, then search

The engine first sums disjoint eight-sample boxes and measures
`abs(b - (a+c)/2)`, in luma codes. This differs from the positive-product
metric (squared-code units): it also penalizes a b lying between a and c
unless it equals their midpoint. Numeric energies across metrics are not
directly comparable.

To isolate the static mask, keep that engine energy and measured row bounds,
but compare all five LOCAL candidates on ONE shared set of pixels at both
times. The following are current-unit energies; previous-unit energies are
also in the scalar output. With no static rejection, zero is the minimum
on all three controls. With the engine's static mask, it is not.

| Counter / mask | Retained 8-pixel blocks | E(-1) | E(0) | E(+1) | Minimum over -2..+2 | Mean f1 luma on support |
|---|---:|---:|---:|---:|---:|---:|
| 6687 / none | 20,700 | 8.809 | 6.801 | 10.372 | 0 | 50.54 |
| 6687 / static | 305 | 0.188 | 0.184 | 0.176 | +1 | 1.85 |
| 6690 / none | 20,700 | 8.756 | 6.758 | 10.349 | 0 | 50.24 |
| 6690 / static | 332 | 0.329 | 0.568 | 0.633 | -1 | 2.19 |
| 6700 / none | 20,790 | 8.888 | 6.900 | 10.434 | 0 | 50.49 |
| 6700 / static | 168 | 0.172 | 0.169 | 0.163 | -2 | 1.48 |

The static tolerance is maximum temporal fluctuation on the device's generated
blanking rows: **5, 5, 4 summed codes**, respectively (0.625, 0.625, 0.5 codes
per pixel after averaging). It leaves **1.47%, 1.60%, 0.81%** of the common
support, predominantly blanking-level samples. This is the measured reason
that treating regenerated dither as the noise model for recorded picture
destroys the useful confirmation. A local-search-only change would retain
this failure.

The separate remote-overlap failure is reproduced using **production
`comb_pair`**, not a rewritten ranking rule. At 6687, nominal candidate 0
against +213 has only **five blocks**: current energies **1.5375 vs 1.1375**,
previous energies **1.2625 vs 1.1875**. The remote candidate wins those pixels
even though the raw weave at zero is clean. Against nominal zero, **65**
full-range comparisons remain unresolved at 6687, **38** at 6690, **206** at
6700. These counts differ from the production output because production
verifies its tournament's +232, not nominal zero.

Pairwise masks also differ from the five-way intersection used in the table.
For 6687 the exact production pairwise test of zero versus each local neighbor
passes its two-time envelope criterion; the remote alternatives defeat it.
For 6690 even the pairwise local -2 and -1 tests fail that criterion. Thus
both the full-range requirement AND the support selection are separately
falsified on the same source.

## Conclusion and limits

The disagreement is explained, not fixed: the engine demands temporal agreement
at a generated-blanking noise floor, then global dominance against tiny remote
overlaps. The harness measures current-raster weave energy on fixed common
support over five local placements, with neither of those demands. It does
evaluate candidate shifts; unlike the engine it does not require full-range
uniqueness. The product energy itself contains no agreement threshold.

The next implementation must test the geometry's relative placement on useful
detail and state its ambiguity limits. It must not call a local minimum a
proof of arbitrary-displacement uniqueness, nor use a generated-dither cutoff
as an unmeasured picture-noise model. These observations do not license a
new threshold or establish a static criterion for moving program.

Neither a clean relative weave nor a common-mode (+2,+2) displacement determines
absolute placement. Also, common-mode blindness alone does **not** imply low
relative margin: absolute ambiguity and relative-comb measurability are distinct
questions. No capture-2 conclusion is derived from capture 1 here.

Unchanged production engine timed in this O3 diagnostic: **9.856 ms median,
16.749 ms p95**, 452 registration calls. Diagnostics, classifier and output I/O
are excluded. The earlier run before the extra support-mean report measured
8.5435/15.380 ms; host/runtime variability is visible. Neither is a whole-worker
budget pass or a speedup. No production path was changed.
