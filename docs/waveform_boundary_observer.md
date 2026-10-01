# Standalone blanking-step observer (Task41)

`make tests/waveform_boundary_observer` builds a diagnostic replay worker,
not a library or OBS feature. Set `HRT_BOUNDARY_PREFIX` to a new scratch
prefix and `FS_HRETIME=1` to observe the raw, actually paired aperture after
the unchanged E-62 call. CSV output is deferred until worker join. This
bounded tool supports 1,024 frames per invocation; overflow aborts. It is
not a whole-tape recorder. OFF invokes no locator. No observation changes
pixels, decisions, previous-reference validity, configuration or schemas.

Each side is read inward over 147 samples (the previously specified NTSC
horizontal-blanking duration in sample units). Four-on-four differences
find candidate rises. The strongest qualified rise wins, outside-first on
ties. An eight-sample inner plateau starts four samples past the centre.
The exterior is all samples before centre minus four; fewer than four
exterior samples uses the field's full-width nine VI rows instead.

Levels are medians. Noise is Gaussian-scaled MAD (1.4826), floored at VI
noise and quantisation RMS `1/sqrt(12)`. Contrast must exceed five exterior
sigmas; exterior and VI levels must agree within five combined sigmas.
Two four-sample halves of the inner plateau must agree within three
combined sigmas; a reversal across the rise exceeding three combined
plateau sigmas rejects it. These are registered operational hypotheses,
not guarantees of distinguishing arbitrary content from blanking.

The reported position linearly interpolates the raw samples bracketing
half the measured step height. Uncertainty is combined plateau sigma
divided by local slope, floored at half a sample. With no resolved step,
two initial eight-sample plateaus may support a censored-picture hypothesis
only if their levels agree within three combined sigmas, their contrast
exceeds five VI sigmas, and all first-eight samples exceed half height.
A censored result is only `left <= 0` or `right >= 719`, not a recovered
coordinate. Unknown is explicit. A bright content edge can still imitate
this model; results must be judged against raw evidence, not promoted as
a repair decision.

`locator_ms` measures thread CPU for both VI references and all 960 side
measurements, excluding E-62 and CSV writing. Offline analysis computes
per-field body medians/p90 spreads (indices 40..219), neighbouring-edge
departures, and an edge-only retime candidate where both measured edge
displacement uncertainty intervals intersect. That does not certify
interior waveform recovery. Numeric choices were recorded before replay
in the ignored experiment ledger; no label selects these parameters.

Synthetic smoke check (also suitable for ASan/UBSan):
`cc -std=c11 -Wall -Wextra tests/waveform_boundary_test.c -lm -o /tmp/wb-test`
