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
- "Read as two amounts the echo comes off the bar to 0.008-0.032 of the no-echo edge": the no-echo edge is
  picked by lowest reading and is off along the second shape (see "After the first clip"); the figure is
  agreement with that pick, not with an echo-free edge.
- The first clip's removal: taps for lags 2..27 (a net level shift after bright edges) and the second shape's
  zero (a constant false echo). Corrected in `refit4.py`.
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

### After the first clip (`refit4.py`)

The owner watched the clip: the strength is off, and where the real echo weakens the removal adds echo.
Measured, then two defects of the model above found and corrected; the clip was remade with them.

- **Not timing.** The left picture edge's dip follows the same field's bar reading one for one in every
  quarter of the field (slope 0.93-1.09, no better with the neighbouring field's reading); the reading
  moves 0.025 (median) from one field to the next.
- **The echo is longer than the taps.** Past the dip the bar sits 0.02-0.04 high from +20 to +50 and is
  back by about +60. Shapes read over 0..+24 and taps for lags 2..27 had a net sum (-0.06, -0.10), so
  the removal moved the level of everything after a bright edge: the bar's flat top came out 4.6-7.0%
  of the bar low, at every strength. Shapes over 0..+80, taps 2..75: sum +0.005 / +0.011, bar top
  +0.1-0.4%.
- **The zero of the second shape was off.** The "almost no echo" edge is the fields with the lowest
  reading, and the reading itself moves with the second shape, so that pick sits to one side along it:
  the second amount is -0.14 to -0.20 at every reading from 0.1 to 0.6, in passages half an hour apart.
  That constant was being removed from every field as echo. In the weak passage (readings 0.13-0.30,
  `weak_after.py`) it took 0.03-0.07 off the left edge at +3..+6 and added 0.04-0.05 at +9..+11, a
  bright band beside the real dip. With the zero put where the second amount heads as the first goes
  to nothing (-0.198, a line through binned medians), what the removal adds is centred on the dip at +7
  and the edge comes out without a hump. This rests on the fast part averaging to nothing when the slow
  part is weak. The weak line used as reference in the bar checks is picked the same way and shares
  the bias.

Test line by part (`refit4.py tl`: amounts from line 18, removal scored on line 281 against the weak
line; rms, captured -> removed), taps 2..27 as in the first clip, then as corrected:

| reading | model | staircase | after its fall | 2T pulse | 12.5T pulse | bar rise | bar top |
|---|---|---|---|---|---|---|---|
| 0.30-0.45 | first clip | 0.040 -> 0.057 | 0.044 -> 0.052 | 0.045 -> 0.058 | 0.045 -> 0.019 | 0.076 -> 0.022 | 0.011 -> 0.044 |
| | corrected | 0.035 | 0.031 | 0.054 | 0.012 | 0.023 | 0.009 |
| 0.60-0.75 | first clip | 0.050 -> 0.065 | 0.094 -> 0.065 | 0.119 -> 0.128 | 0.084 -> 0.037 | 0.165 -> 0.014 | 0.009 -> 0.061 |
| | corrected | 0.035 | 0.039 | 0.124 | 0.032 | 0.029 | 0.011 |
| 0.75-0.90 | first clip | 0.054 -> 0.071 | 0.115 -> 0.072 | 0.139 -> 0.169 | 0.100 -> 0.077 | 0.208 -> 0.032 | 0.011 -> 0.071 |
| | corrected | 0.038 | 0.051 | 0.165 | 0.077 | 0.056 | 0.024 |

Steady picture edges are unchanged by the corrections (rises 0.11, falls 0.11). The narrow 2T pulse is
not improved by any version (fine lettering). The staircase steps sit 0.03-0.05 of the bar lower
under strong echo for their whole width while the bar's top does not move: the steps carry colour,
the bar does not; that is not an echo of a luma edge and nothing here removes it.

### After the second clip

The owner: echo is still added where the real one weakens, and the remade clip shows repeating weaker echoes,
dark vertical bands, late in the clip (the strong-echo part). Asked whether the tuner changes which copy it
treats as the main one.

- **No sign of a change of main copy** (`primary.py`; 1,533 test lines across the capture, 3,599 in two
  passages). If the later copy became the main one, the other would show before each edge. Before the bar's
  rise and on the bar's top before its fall nothing above 0.02 of the bar is there at any reading; the echo is
  after the edge everywhere. The test line does sit up to 19 samples early in about 15% of fields, spread out
  and not at one offset, and the picture's left edge in the same field does not move with it (correlation
  about 0, edge within half a sample): timing at the top of the field, not a change of reference.
- **The repeating bands are real and come from undoing a near-cancellation** (`repeats.py`, `ring.py`). At
  readings 0.75-0.90 the echo leaves 0.13 of the picture at 0.45 MHz (0.04 in the worst field), 0.29 at
  0.60-0.75, 0.67 at 0.30-0.45. After removal the bar's flat top carries a decaying ripple every 30 samples
  (-0.10, +0.08, -0.06, +0.04 of the bar at +12, +27, +42, +57), swing 0.12 against 0.04 captured; 0.05 at
  0.60-0.75; none at 0.30-0.45. Limiting the division trades the ripple for echo left in, with no setting that
  has neither (strongest fields: swing 0.11 / edge left 0.06 at the present setting; 0.06 / 0.16 limited and
  without the further passes, which bring the ripple back; captured 0.04 / 0.27). The longer taps made this
  worse than the first clip.
- **The lag near blanking delays the predicted echo wherever the picture is not bright** (by half a sample to
  a sample at mid levels). Without it, and with samples at the floor left as captured (`nolag.py`): steady
  picture rises 0.085 (0.11 with it), falls unchanged, and the weak passage's left edge comes out smooth at
  every reading. The left edge in the strong passage scores worse against the weak passage's edge (0.06-0.10
  against 0.04-0.07), a comparison across different scenes. Not adopted, not settled.

### Two independent reviews of the band explanation (2026-11-25)

The owner did not accept "the bands come from dividing a near-cancellation back out" and had it challenged by
two reviewers working separately on the same data (their scripts and logs stayed in scratch). Both measured
in the picture, which the notes above never did.

Agreed by both, and accepted:
- The removal creates bands in the picture, about 30 samples apart, growing steeply with the reading; the
  remade clip has about twice the first clip's. On the left picture edge the swing is 2.6-3.1 codes below a
  reading of 0.55, 7 at 0.55-0.65, 20 at 0.65-0.75, 30 at 0.75-0.90. Below 0.55 there is no alternation,
  only a small one-signed darkening 20-45 samples after edges (about 1-3% of the step).
- The near-cancellation is in the capture itself, read without the model: the strongest fields keep about
  0.18 of the weak line's content near 0.42 MHz (the model said 0.13 at 0.45).

Corrections to the notes above:
- **The division is not the cause; the model is.** Put through the model's own echo, the weak line comes back
  with a bar-top swing of 0.003-0.007 up to a reading of 0.75, whatever the division limit or number of passes;
  the real lines show 0.07 and do not care about the limit either. The bands are the difference between the
  modelled and the real echo near 0.45 MHz, magnified by the near-cancellation. "No setting has neither"
  described a limit that only helps by leaving echo in; it says nothing about a better model. At 0.75-0.90
  about half the ripple is reproduced by the capture's floor alone and cannot be undone.
- **Narrow detail is over-corrected.** Scaling the subtracted echo: the narrow (2T) pulse is best at 0.40-0.55
  of the applied amount at every reading and is worse after removal than before at strong echo (0.135
  captured, 0.16 removed, 0.10 at 0.55); the wide pulse is best at 0.85; the bar's rise at 1.0.
- **The bar's echo is not the picture's.** After removal the level at the dip on the left picture edge runs
  0.74-0.97 of the step from second to second, unrelated to the reading (-0.05) and tied to the second amount
  (-0.40): the second shape read from the bar does not carry over. At 8-13 s (readings 0.35-0.47) the dip is
  over-filled and 0.74-0.89 of the amount would have been right, while the test line asks for 1.03-1.07.
- **The reading is a share, not what is seen.** Against the left edge's dip as a share of its step it holds
  (correlation 0.96); against the dark line's depth in codes it does not (0.69): the weakest reading of the
  clip (0.34, at 14 s) has a 77-code dark line, readings of 0.61-0.66 at 0-1 s have 48-52 codes.

Where the reviews did not support the owner's reading: the bands are largest at strong echo, not weak, and
their polarity (dark first after a rise) is that of too little correction; less subtraction lowers them only by
leaving echo in. Where the two reviews differ: one finds broad picture edges want 1.15 or more of the amount,
the other 0.9-1.0 on the left edge; one finds removing the lag near blanking alone does not help.

### One system for the whole test line (`sysid.py`): tried, not used

Captured line = (weak line through one kernel, lags -14..+60, two amounts per field), cut at the
blanking floor; kernels fitted on the whole line with the staircase steps, a sideways slip and an
offset as extra terms.
- Known answer (`sysid.py ka`, made-up lines through a made-up system with a floor and noise 2.5 codes):
  error 9.0 / 12.5 / 24.8 / 28.2 codes captured, 3.4 / 3.8 / 6.2 / 8.6 after. Without the staircase in
  the fit the kernel's response was off by 0.13-0.3 (the echo is 0.37); with it 0.07-0.10.
- Without any inversion (`sysid_fwd.py`) the fitted system reproduces the bar and the 12.5T pulse
  (0.02-0.05) but leaves 0.04-0.06 after the staircase-end fall and 0.03-0.07 at the 2T pulse at every
  strength, with two shapes or six. Cutting the prediction at the floor explains part of the "fall echo
  is half the rise's" (a fit of that region alone: 0.049-0.100 uncut, 0.009-0.027 cut); the rest of
  what happens next to blanking is not one linear system.
- On the picture it is worse than the bar-rise model (steady edges 0.22 / 0.15) and rings at about
  2.5 MHz.

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
| `refit4.py` | the two-shape echo read over its whole length, the second shape's zero corrected; test line by part; removal over a stretch |
| `left_after.py`, `weak_after.py` | the left picture edge before and after a removal, by reading, in the strong and the weak passage |
| `primary.py` | line position by field and anything before the edges: a change of main copy? |
| `repeats.py`, `ring.py` | repeating bands on the bar's top after removal; how much of the picture the echo leaves by frequency; division limit against echo left |
| `nolag.py` | the removal without the lag near blanking |
| `sysid.py`, `sysid_fwd.py` | one system for the whole test line with the blanking floor: fit, known answer, forward check, removal (not used) |
| `clip.py` | a stretch in motion: checks of a removed stretch and woven frames for an encoder (its own `remove` is the first clip's model; `refit4.py remove` writes the same files) |
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

- At readings above about 0.55 the removal leaves repeating bands every 30 samples: a model error near 0.45 MHz,
  magnified. What the real echo does there that the model misses is not known.
- The second shape read from the bar does not carry over to the picture; narrow detail is over-corrected about
  two-fold. Any next model is to be scored in the picture and on every part of the test line, not the bar's rise.
- Echo is still seen added where the real one weakens (owner, second clip); the lag near blanking is one
  contributor, not shown to be all of it.
- Narrow strokes: the 2T pulse is no better after removal at any strength; fine lettering above a reading of
  0.8 is not clean.
- Next to blanking the echo does not follow the system read from the bar; the lag near blanking (0.4, 0.8) is
  still the first model's, and the removal undershoots into the right blanking.
- The zero of the second shape rests on an assumption (above), checked only on the left edge of one weak passage.
- Picture rises are hit about a sample earlier than the bar predicts; a quarter of what follows the reading is
  left on steady picture edges.
- Whether the almost-no-echo edge's shallow dip is the tape's own.
- The five-line cleaning threshold was chosen by hand; luma only; one 30 s passage in motion.
