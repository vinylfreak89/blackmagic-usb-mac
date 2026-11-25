# Luma edge echo on one off-air recording (experiments, not a canceller)

One 64-minute off-air recording shows a "ghost" on every line: each luma edge is followed a few
samples later by an opposite-going copy of that edge which fades back. These scripts measure it and
try removing it. Nothing here is wired into the frameserver.

All scripts run from a scratch directory that holds the arrays they name (`units.npy`, `run_*.npy`,
`vbi_*.npy`); results stay out of the repository.

## What it is (measured)

- **Shape.** Step response read from the left blanking edge (a known step, blanking to picture):
  full level by +2 samples, a dip of 26-90% of the step centred +6 to +7 samples after the edge's
  half-way point, back to full level by about +22. Net level is unchanged, so it is not a plain
  displaced copy.
- **Linear in level.** Within a frame the dip takes the same share of the step for steps of 46 to
  200 codes.
- **Same inside the picture.** Isolated moderate steps inside the picture, rising and falling, show
  the same response, and come out flat (within about 0.1 of the step) when the left-edge echo is
  removed.
- **Luma only.** The colour step at the left edge rises smoothly with no dip and is the same in
  frames with a weak or strong luma echo (8 frames had enough saturated lines).
- **Moves over seconds.** Over 30 s (1,800 fields) the depth ran 0.35-0.9 and the dip's place
  5.7-7.2 samples, deeper meaning earlier. Field to field the depth changes 0.014 (median), and top
  and bottom of one field agree within 0.04 (median).
- **A reference in every field.** The broadcaster's test line (line 18 / 281: staircase, pulses,
  white bar) passes through the same path. Its bar's rising edge gives the same depth as the left
  picture edge (correlation 0.96 over 1,006 fields, median difference -0.02), and it is there in
  dark scenes where the picture edge gives nothing. The bar settles at full level from +22 on, which
  confirms the echo's length and that its net is zero.
- **Each big edge has its own over/undershoot, echo or not.** Regressing the test line's edges on echo
  depth over 783 fields splits them into a part that is always there and a part that follows the echo.
  Always there: the bar's rise overshoots to 1.36-1.38 at +4..+5 samples; the staircase-end fall
  undershoots to -0.18 at +5..+7. The first estimate (`deghost.py`) counted the rise's overshoot as echo.
- **The echo after a fall is the rise's echo, mirrored and softened.** Blurred by about 1.75 samples,
  1.25 samples later and 0.79 as large (rms mismatch 0.043 against 0.232 for a plain mirror). Edges in
  the picture show the same thing: the half of an edge near dark takes 3.0-3.7 samples, the half near
  bright 1.4-2.0. The level scale itself is straight (staircase treads evenly spaced).
- **The "over-subtraction" after falls was mostly not an error.** With the echo removed, a fall into
  blanking sits 30-38 codes below blanking for about 12 samples at every echo depth: that is the tape's
  own undershoot, which the capture otherwise clips at blanking.
- **Strength mostly, place a little.** One fixed echo shape carries 75% of the field-to-field change of
  the bar's rise; a second, shift-like shape carries 16%.

**Target (owner, 2026-11-24):** remove the echo only; the tape's own edge over/undershoot stays in the result.

## Fall model (`model.py`)

Edge response = the tape's own edge (always there) + depth x echo. Echo taps come from the rise part
only (kept smooth); near blanking the predicted echo is lagged (one-pole coefficient 0.4) and scaled
(0.8), fading to no change at white. Those two numbers were fitted on the middle third of fields by
depth and checked on the other two thirds:

| check (test line) | without the lag | with it |
|---|---|---|
| staircase-end fall after removal vs the tape's own fall, shallow third (rms) | 0.085 | 0.033 |
| same, deep third | 0.205 | 0.065 |
| middle third (fitted) | 0.148 | 0.050 |

The bar's fall (not used) comes out as the tape's own fall. The bar's rise keeps its overshoot, within
0.05-0.1.

## On picture edges (`same_edge.py`, `same_refit.py`, `left_level.py`, `compare.py`)

An edge that stays put for 12 or more frames is the same content while the echo strength drifts (0.14-0.15 within
an edge, median). Regressing its response on strength within each edge cancels the content. Known answer
(`same_edge.py ka`, made-up edges whose own overshoot grows with strength): true echo recovered to 0.011 rms, where
one regression over everything is off by 0.44. On 30 s, mid-level edges of about 120 codes (32 rises, 40 falls):

| part of the response that follows the strength (rms, +2..+24) | captured | after `model.py` removal |
|---|---|---|
| picture rises | 0.35 | 0.15 |
| picture falls | 0.36 | 0.09 |

(uncertainty 0.04-0.05, from resampling whole edges)

- **The overshoot left on picture rises is the picture's own**: 1.21-1.25 at +3 samples in the part that does not
  follow the strength, the same before and after removal.
- `stretch_check.py`'s "no gain" was the content confound; its block-to-block check is superseded by this one.
- **The echo is not one fixed filter for every edge.** With a strength reading that leaves each field's own reading
  out (mean of its four neighbouring fields; `compare.py`), the echo per unit of strength is deepest at: test bar
  -1.22 at +6 (own overshoot peaks 1.40 at +5); picture rises -0.89 at +4 (1.25 at +3); picture falls -0.96 at +5
  (1.27 at +4); left blanking edge by the level it lands on -1.11 at +4, -0.84 at +4, -0.92 at +5, -1.44 at +5 (own
  peaks at +3, +3, +3, +4). In all seven the echo is deepest one sample after the edge's own overshoot peak, not at
  a fixed delay after the edge's half-way point. Taps read from one kind predict another kind's echo with an error
  of 0.2-0.5 of that echo (0.07-0.36 on the kind they were read from). No simple rule by landing level.
- Taps read from the bar's rise and the picture's rises together: picture rises 0.07, picture falls 0.10, bar rise
  0.20 (0.14 with the bar's own taps). On the picture that is within the uncertainty of the bar's taps.
- The edge with the echo regressed out keeps a shallow dip (0.83-0.95 of the step) from +7 to +18 in every kind,
  the bar included: either the tape's own, or echo that does not scale with the reading. The stretch has no field
  below a strength of 0.29, so it cannot tell which. A stretch where the echo is gone would give the tape's own
  edge directly.

The 2T pulse keeps a shoulder (0.2-0.5 of the pulse) after removal because the capture clipped what went below
blanking.

## Removal tried

- `deghost.py`: echo taps from the pooled left-edge step (lags 3-36), removed by running each line
  left to right. Unstable on about half the frames (the echo is strong).
- `aware.py`: the echo is divided out per line only to get a picture estimate; that estimate is
  cleaned across five lines of the same field; the echo predicted from the cleaned copy is
  subtracted from the captured line. Tape noise is left as captured.
  - Plain division boosts 0.2-0.6 MHz by 1.5-2x and with it the tape noise (line-to-line change in
    that band 2.2 -> 3.1-3.4 codes on flat frames); the noise-aware version leaves it at 2.2.
  - Known answer (`aware.py ka`): made-up picture, echo of this strength, noise added after the
    echo: error 23.8 codes captured, 9.7 division, 7.6 noise-aware; the noise alone is 2.9. Most of
    what remains is the echo estimate.

## Scripts

| script | does |
|---|---|
| `sample_units.py` | N single frames spread through a capture |
| `stretch.py` | N consecutive frames from a byte offset, picture rows or (`vbi`) the test-signal rows |
| `deghost.py` | left-edge step response, echo taps, left-to-right removal, `ka` |
| `aware.py` | spectral division, five-line cleaning, noise-aware removal, `ka`, panels |
| `band.py` | gain of the division by frequency and where line-to-line junk grows |
| `chroma.py` | colour step at the left edge against the luma echo depth |
| `lin.py` | dip against step height and against position in the field; right-edge bump |
| `inpic.py` | isolated steps inside the picture, before and after removal |
| `shift.py` | the "left edge is a gate" idea, scored on right edge and in-picture steps (refuted) |
| `track.py` | depth and place per field quarter over a stretch, from the left edge |
| `bar.py` | depth and place per field from the test line's bar, beside `track.py`'s reading |
| `falls.py`, `falls2.py` | rise and fall times and pooled responses of in-picture steps by size |
| `testline.py`, `split.py`, `checks.py` | the test line's known edges pooled by depth; always-there part vs echo part; staircase, fixed-shape and mirror checks |
| `tl_remove.py` | first-version removal run on the pooled test line |
| `model.py` | the fall model, fitted on one third of fields and checked on the rest |
| `stretch_check.py`, `panel2.py` | the model on 30 s of picture; stills panel |
| `same_edge.py` | steady picture edges across frames; response split within each edge into its own shape and the part that follows the strength, before and after removal; `ka` |
| `same_refit.py` | taps read from the bar, the picture or both, each scored on the other edges |
| `left_level.py`, `compare.py` | left blanking edge by landing level; every kind against one strength reading; taps from one kind tried on the others |

## Open

- An echo description that holds across edge kinds (it follows each edge's own overshoot peak, not a fixed delay);
  a quarter to almost half of the picture's echo is left by the present taps.
- The tape's own edge with no echo present (needs a stretch where the echo is gone).
- The bar finder misses field 1 in about two thirds of fields.
- The five-line cleaning threshold was chosen by hand and tried on stills only.
- Echo depth near 0.9 leaves some frequencies almost cancelled.
