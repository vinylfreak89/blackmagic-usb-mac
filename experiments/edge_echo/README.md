# Luma edge echo on one off-air recording (experiments, not a canceller)

One 64-minute off-air recording shows a "ghost" on every line: each luma edge is followed a few
samples later by an opposite-going copy of that edge which fades back. These scripts measure it and
try removing it. Nothing here is wired into the frameserver.

All scripts run from a scratch directory that holds the arrays they name (`units.npy`, `run_*.npy`,
`vbi_*.npy`, `lo_*.npy`, `sv_*.npy`); results stay out of the repository.

**Target (owner, 2026-11-24):** remove the echo only; the tape's own edge shape stays in the result.

## What it is (measured)

- **Shape.** Step response read from the left blanking edge (a known step, blanking to picture):
  full level by +2 samples, a dip of the step centred +6 to +7 samples after the edge's half-way
  point, back to full level by about +22. Net level is unchanged, so it is not a plain displaced copy.
- **Linear in level.** Within a frame the dip takes the same share of the step for steps of 46 to
  200 codes.
- **Luma only.** The colour step at the left edge rises smoothly with no dip and is the same in
  frames with a weak or strong luma echo (8 frames had enough saturated lines).
- **A reference in every field.** The broadcaster's test line (line 18 / 281: staircase, pulses,
  white bar) passes through the same path. Its bar's rising edge gives the same strength as the left
  picture edge (correlation 0.96 over 1,006 fields), and it is there in dark scenes. Reading = 1 minus
  the lowest point of the bar's rise +5..+9 samples after its half-way point.
- **Never gone, across the whole capture** (`survey_tl.py`: 768 points 5 s apart, one 1.5 MiB read
  each, both test lines read at every point). Reading: median 0.45, 5% 0.31, 95% 0.62, highest 0.88,
  lowest 0.12; below 0.2 in 0.7% of points. Within the weakest passages single fields read 0.06-0.10.
- **The edge with almost no echo** (`family.py`, bar's rise where the reading is below 0.1; 18
  field-lines from two passages a minute apart that agree): 0.78 of the bar at +1, 1.02 at +2, 1.13 at
  +3, 1.02 at +5, 0.91 at +7..+8, 0.93 at +9, 0.98 by +22. Whether that last shallow dip is the tape's
  own or a remnant of echo is not known; nothing weaker was met.
- **By strength**, the bar's rise keeps its overshoot (1.13-1.15 at +3..+4) up to a reading of 0.3,
  then loses it (0.95 at 0.85); the dip sits at +7..+8 at every strength and deepens from 0.91 to 0.17.
- **Two shapes, not one.** The bar's departure from the almost-no-echo edge, over 4,199 field-lines
  with readings 0.06-0.89: one shape carries 91%, a second 6%, a third 1%. The first follows the
  reading (correlation 0.99) and drifts over minutes; the second moves within seconds and shifts the
  dip earlier or later.
- **Falls.** At weak echo the staircase-end fall lands on blanking by +4 with no undershoot visible
  (the capture cuts off below blanking, so a small one cannot be ruled out). At a reading of 0.5-0.65
  the bump after that fall is +0.29 of the step at +8, about half the rise's dip at the same strength,
  and a sample later.
- **Picture edges have no single shape of their own.** Pooled by content, mid-level rises overshoot
  anywhere from 1.04 to 1.8 at the same echo strength (`picture_own.py`).

### Withdrawn

- "The tape's own edge overshoots to 1.36-1.38 at +4..+5" and "the tape's own fall undershoots to
  -0.18": both came from a straight line fitted over readings 0.28-0.86 and run down to zero. The
  response is not a straight line in the reading below 0.3 (the overshoot does not change there). The
  measured overshoot is 1.13 at +3; no fall undershoot is visible.
- "The over-subtraction after falls is the tape's own undershoot": not supported, for the same reason.
- The cross-kind comparison of `compare.py` / `left_level.py` ("the echo sits one sample after each
  edge's own overshoot peak", "taps from one kind miss another's by 0.2-0.5") used own edges from the
  same straight line and is not evidence either way.
- The bar finder started its search at column 400 and took the 12.5T pulse for the bar where that
  pulse stood above half the bar: a third of fields were dropped, the weaker-echo ones more often
  (median reading 0.38 against 0.47). It now starts at 440 and reads every field.

## Echo read from the test bar, two numbers per field (`refit3.py`)

Echo of a field = amount 1 x shape 1 + amount 2 x shape 2; both amounts are that field's bar rise
minus the almost-no-echo edge, projected on the two shapes; taps for each shape are read against the
almost-no-echo edge (lags 2-27, kept smooth; they reproduce the shapes to 0.017 and 0.088 rms).
Removal as in `model.py`: divide once for an estimate, then predict the echo from the estimate and
subtract it, three times, with the predicted echo lagged and scaled near blanking (0.4, 0.8; not
refitted for these taps).

Bar check with a known answer: amounts read from line 18, removal scored on line 281 of the same
frame against the almost-no-echo edge (rms, 0..+24; the shapes themselves were read from all fields):

| reading | captured | one shape (`refit2.py`) | two shapes |
|---|---|---|---|
| 0.05-0.15 | 0.015 | 0.019 | 0.008 |
| 0.25-0.35 | 0.082 | 0.037 | 0.026 |
| 0.50-0.65 | 0.203 | 0.025 | 0.024 |
| 0.65-0.90 | 0.273 | 0.040 | 0.018 |
| part that follows the reading | 0.45 | 0.11 | 0.04 |

Field by field (median) the two-shape distance is 0.023-0.041 at every strength. The straight-line
model (`model.py`) leaves 0.05-0.11 and an overshoot of 1.40.

Picture check, nothing fitted on the picture (`same_edge.py`'s steady edges, first passage, 32 rises
and 40 falls of about 120 codes, readings 0.28-0.86): part of the response that still follows the
reading (rms, +2..+24, uncertainty 0.04):

| | captured | straight-line model | one shape | two shapes |
|---|---|---|---|---|
| picture rises | 0.41 | 0.15 | 0.24 | 0.10 |
| picture falls | 0.43 | 0.10 | 0.24 | 0.11 |

What is left after rises is a shortfall of about 0.3 per unit of reading at +3 samples: picture rises
are hit about a sample earlier than the bar predicts. Pooled, the rises come out with no dip and no
added overshoot (0.97 at +3, 0.86-0.88 from +6 to +15, 0.97 by +24).

In motion (`clip.py`: the first passage's 900 frames, the same removal with the five-line cleaning,
both fields, captured over removed): picture rises 0.11, falls 0.10 by the same check. 1.05% of
output samples land below code 0, nearly all in the last 40 columns, after the picture's fall into
the right blanking (19% of samples there, 2.5% captured); inside the picture 0.003%. Line-to-line
change at 0.2-0.6 MHz goes 4.96 -> 6.05 codes on these picture frames; restored picture and added
noise are not separated by that number. At readings above 0.8 fine white lettering comes out dimmer
and still doubled.

Falls on the test line (`falls3.py`), staircase-end fall against its weak-echo shape: reading
0.50-0.65: 0.126 captured, 0.136 after removal without the lag near blanking, 0.073 with it;
0.65-0.90: 0.183, 0.186, 0.076. With the lag the fall still ends about 0.07 of the step low.

## Steady picture edges as a check (`same_edge.py`)

An edge that stays put for 12 or more frames is the same content while the echo strength drifts.
Regressing its response on the reading within each edge cancels the content. Known answer
(`same_edge.py ka`, made-up edges whose own overshoot grows with strength): true echo recovered to
0.011 rms, where one regression over everything is off by 0.44. `stretch_check.py`'s block-to-block
check is confounded by content and is superseded by this. The split's "own edge" is a straight line
run to zero and is not to be read as the edge without echo (see Withdrawn).

## Removal tried earlier

- `deghost.py`: echo taps from the pooled left-edge step (lags 3-36), removed by running each line
  left to right. Unstable on about half the frames (the echo is strong).
- `aware.py`: the echo is divided out per line only to get a picture estimate; that estimate is
  cleaned across five lines of the same field; the echo predicted from the cleaned copy is
  subtracted from the captured line. Tape noise is left as captured.
  - Plain division boosts 0.2-0.6 MHz by 1.5-2x and with it the tape noise (line-to-line change in
    that band 2.2 -> 3.1-3.4 codes on flat frames); the noise-aware version leaves it at 2.2.
  - Known answer (`aware.py ka`): made-up picture, echo of this strength, noise added after the
    echo: error 23.8 codes captured, 9.7 division, 7.6 noise-aware; the noise alone is 2.9.
- `model.py`: straight-line split of the bar's rise, taps from it, lag near blanking fitted on the
  staircase-end fall. Superseded by the two-shape reading; its lag near blanking is still used.

## Scripts

| script | does |
|---|---|
| `sample_units.py` | N single frames spread through a capture |
| `stretch.py` | N consecutive frames from a byte offset: picture rows, the test-signal rows (`vbi`), or both in one read (`both`) |
| `survey_tl.py`, `survey_read.py` | the two test lines at N points across a capture, one short read each; strength over the capture |
| `family.py` | the bar's rise at every strength met; the almost-no-echo edge; shapes of the departure from it |
| `refit2.py`, `refit3.py` | one-shape and two-shape echo against the almost-no-echo edge, scored on the bar and on steady picture edges |
| `falls3.py` | test-line falls against their weak-echo shape, with and without the lag near blanking |
| `picture_own.py` | picture edges pooled by strength beside the bar; steady edges of the weak-echo passage |
| `same_edge.py` | steady picture edges across frames; within-edge split; `ka` |
| `same_refit.py` | taps read from the bar, the picture or both, each scored on the other edges |
| `panel3.py` | stills: captured, straight-line model, two-shape echo |
| `clip.py` | a stretch in motion: two-shape removal over consecutive frames, its checks, woven frames for an encoder |
| `deghost.py` | left-edge step response, echo taps, left-to-right removal, `ka` |
| `aware.py` | spectral division, five-line cleaning, noise-aware removal, `ka`, panels |
| `band.py` | gain of the division by frequency and where line-to-line junk grows |
| `chroma.py` | colour step at the left edge against the luma echo depth |
| `lin.py` | dip against step height and against position in the field; right-edge bump |
| `inpic.py` | isolated steps inside the picture, before and after removal |
| `shift.py` | the "left edge is a gate" idea, scored on right edge and in-picture steps (refuted) |
| `track.py`, `bar.py` | depth and place per field from the left edge and from the test bar |
| `falls.py`, `falls2.py` | rise and fall times and pooled responses of in-picture steps by size |
| `testline.py`, `split.py`, `checks.py`, `tl_remove.py`, `model.py`, `stretch_check.py`, `panel2.py`, `left_level.py`, `compare.py` | the straight-line split and what was built on it (see Withdrawn) |

## Open

- Picture rises are hit about a sample earlier than the bar predicts; a quarter of what follows the
  reading is left on picture edges.
- The lag near blanking is not refitted for the two-shape taps; falls into blanking end about 0.07 low.
- Whether the almost-no-echo edge's shallow dip is the tape's own.
- The five-line cleaning threshold was chosen by hand; luma only; one 30 s passage in motion.
- A reading near 0.9 leaves some frequencies almost cancelled; fine lettering above 0.8 is not clean.
- The removal undershoots into the right blanking.
