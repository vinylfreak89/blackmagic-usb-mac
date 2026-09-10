# The burst lead is dead, on displaced rows as well as normal ones

## The null

`burst_probe.py` over capture 1 from counter 6667. Quadrature amplitude at the nominal subcarrier,
3.579545 MHz, local linear baseline removed, in luma codes:

| window | n | amplitude, median | p90 | amp/rms, median |
|---|---:|---:|---:|---:|
| relocated run, **predicted** burst window, offset 92–126 | 1478 | **0.147** | 0.264 | 0.281 |
| relocated run, same width at offset 10 — positional control | 1478 | **0.151** | 0.270 | 0.291 |
| dark picture, same width — matched control | 9144 | 0.256 | 3.723 | 0.127 |

**The positional prediction fails flatly.** The window where burst must be if it is anywhere reads
0.147 and the same-width window 82 samples away in the same run reads 0.151 — indistinguishable,
and the predicted window is if anything the lower of the two. There is no subcarrier signature
inside relocated blanking, at the predicted offset or elsewhere.

## The instrument is not blind, and that is measured rather than asserted

A null is worthless without it. Taking a real relocated-blanking window as the substrate and
injecting a synthetic burst of known amplitude at six phases:

| injected, codes | recovered | ratio |
|---:|---:|---:|
| 0.25 | 0.266 | 1.065 |
| 0.50 | 0.506 | 1.013 |
| 1.00 | 1.000 | 1.000 |
| 2.00 | 1.993 | 0.996 |
| 5.00 | 4.977 | 0.995 |
| 20.00 | 19.906 | 0.995 |

The probe recovers an injected burst to within half a percent from one code upward, and a burst of
**a quarter of one code** already reads 0.266 against a substrate floor of 0.131. The measured
relocated windows sit at that floor. **A burst is not there, and one would have been seen.**

## Why, probably — labelled as explanation, not measurement

Burst is a chroma signal and this is decoded luma. Any competent NTSC decoder notches or combs the
subcarrier out before the luma is delivered, so nothing carrying burst should survive into these
samples whatever the row's timing. That is consistent with the null and was not tested.

## What this closes and what it leaves

Two candidate routes to the identification method are now eliminated by measurement rather than by
argument:

1. **Adjudication against level-based criteria** — five independent readings of the same panels
   returned 0, 0, 86, 186 and 0 identifiable; the criteria do not decide (RESULT.md).
2. **Colour burst as a positive signature of blanking** — absent on normally timed rows by timing
   arithmetic, and absent inside relocated runs by this measurement, with the instrument
   demonstrated sensitive to a quarter of a code.

So the agreed route to the decision margin has failed with no replacement, and the classifier gate
stands. What happens next is a decision for the owner, not one to be made between the agents: the
evidence-gathering the contract authorised has been done and has not produced a cohort.
