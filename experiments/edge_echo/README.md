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
- **Falls to blanking are different.** The bar's fall, and the picture's fall into blanking at the
  right, are about half as fast as the rises, and the bump after them is smeared (0.33 where the
  mirror of the rise predicts 0.61). So a removal read from rising edges over-subtracts there by
  about 0.2 of the step. Sliding the echo later to fix that makes steps inside the picture worse,
  so the cause is in how large falls reached the tape, not in the echo estimate. Not modelled.

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

## Open

- Falls into blanking (and probably large falls into dark picture) are not the mirror of rises.
- The bar finder misses field 1 in about two thirds of fields.
- The five-line cleaning threshold was chosen by hand and tried on stills only.
- Echo depth near 0.9 leaves some frequencies almost cancelled.
