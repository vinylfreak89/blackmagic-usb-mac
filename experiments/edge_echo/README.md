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

### Reworked: the echo's shapes read from the picture's own edges (`harness.py`)

After the reviews the model was reworked and scored in the picture. The two amounts per field still come from the
test bar; what they do to an edge is now read from the picture.

- **The fast part is echo, and the bar's reading of it is good** (`shape2.py`). The two test lines of a frame agree
  on it (correlation 0.90), it lasts about a second (0.61 after 30 frames), it does not follow the test line's own
  position (0.01), and the place of the picture's dip follows it (-0.83). What failed was the taps.
- **What the bar's taps did on picture edges.** On left picture edges that stay put for 12+ frames (2,188 tracks,
  77,143 edges; the slope of the profile on each amount inside a track, so content cancels): per unit of the first
  amount the picture shows 0.19 / 0.38 / 0.30 / 0.15 at +4 / +6 / +8 / +10 and the removal took 0.25 / 0.48 / 0.45 /
  0.21, then added 0.05-0.08 from +16 to +24. The second amount in the picture is a short early feature (-0.33,
  -0.51 at +2, +4, nothing later); the bar's taps for it took half of that and added a level of 0.18 from +24 on.
- **Method.** Those two slopes are the echo's shapes as the picture shows them. Taps for lags 1..85 are fitted to
  make them out of the edge itself (each track run back to no echo; rms 0.016 and 0.023 of shapes of 0.083 and
  0.091). No lag near blanking. A sample at the capture's floor is taken as cut off when the estimate plus its
  predicted echo lies below the floor, and is then filled from the estimate; otherwise it is blanking and stays.
- **Known answer** (`harness.py ka`): the weak passage's frames as the clean picture, a made-up system with content
  at lag 0, the strong passage's amounts with a field's reading noise, cut at the floor. Error against the clean
  frames, whole picture: 6.8 / 7.8 / 11.0 / 15.4 codes captured, 3.1 / 3.7 / 6.2 / 7.7 after, 2.4 / 2.8 / 5.6 / 7.4
  with the true system. Left-edge bands 4-13 codes captured, 1.0-3.4 after.

Shapes read from the odd-numbered tracks, scored on the even ones (second clip's removal -> reworked):

| | captured | second clip | reworked |
|---|---|---|---|
| what follows the reading, dip (+2..+24) | 0.468 | 0.148 | 0.062 |
| what follows the reading, bands (+26..+90) | 0.021 | 0.136 | 0.025 |
| what follows amount 1 / amount 2, dip | 0.166 / 0.180 | 0.082 / 0.136 | 0.022 / 0.021 |
| bands in codes at readings 0.30-0.45 / 0.45-0.55 / 0.55-0.65 / 0.65-0.75 / 0.75-0.90 | | 3.3 / 4.1 / 9.1 / 20.3 / 31.6 | 1.5 / 1.8 / 2.3 / 4.3 / 6.9 |

Not used in the calibration:
- Steady edges inside the picture: rises 0.106, falls 0.073 (second clip 0.116, 0.113; captured 0.41, 0.43).
- The weak passage: what the removal adds is centred on the dip and the edge comes out without a hump at every reading.
- The test line: bar-top swing 0.045 / 0.038 / 0.050 / 0.059 / 0.069 by reading (second clip 0.036 / 0.037 / 0.050 /
  0.087 / 0.145; captured about 0.04). The narrow pulse is 0.045-0.141 (captured 0.061-0.171), still poor at strong echo.

What it leaves: after removal the left edge sits 0.15-0.27 of its step below its far level at +6..+8 and is back by
about +22. That is the edge with the echo run back to nothing (0.81 at +6, 0.85 at +12, 0.95 at +22), and the weak
passage's edge has the same form. Whether it is the tape's own edge or echo that is never absent is not known.

The owner watched the third clip (this removal over the same 30 s) on 2026-11-25: the repeating bands and the echo
added at weak strength are fixed. That verdict covers this passage in motion, not the items under Open.

### A second passage, 36 minutes later: the shapes do not carry over

30 s from 62 minutes into the capture (900 frames, one read, colour kept as well: `stretch.py ... all`). Readings
0.46-0.98, median 0.69; the second amount is 0.55-0.85 here (first passage -0.01 to 0.59, median 0.16). Nothing was
refitted: amounts from the bar as before, shapes from the first passage (`harness.py score/tl/remove ... lum= vbi=
tracks=`).

| removal, scored on the 62-minute passage's left edges | bands by reading 0.45-0.55 / 0.55-0.65 / 0.65-0.75 / 0.75-0.90, codes |
|---|---|
| first passage's shapes (the removal the owner judged fixed there) | 13 / 9 / 24 / 29 |
| the second clip's model | 10 / 10 / 19 / 26 |
| shapes read from this passage alone (odd tracks, scored on even) | 12 / 10 / 21 / 34 |
| shapes read from both passages together | 10 / 6 / 17 / 20 (and the first passage worsens to 3 / 4 / 7 / 12 / 17) |

With the first passage's shapes what follows the reading goes 0.377 -> 0.111 at the dip but 0.065 -> 0.142 in the bands
(more than captured); the bar-top swing on the test line is 0.064 / 0.101 / 0.149 / 0.216. Shapes read inside this
passage remove the slopes inside it (0.040 / 0.068 per amount) but the edge "run back to no echo" is not believable
(1.50 at +2): the amounts here span a narrow range far from zero.

Why: at the same reading the echo is a different shape here. Left edge, reading 0.65-0.75, t = 2..20 step 2:

    first passage  1.15 0.75 0.25 0.41 0.65 0.73 0.78 0.83 0.88 0.93
    62 minutes     0.91 0.44 0.23 0.47 0.75 0.83 0.86 0.91 0.95 0.99

The dip starts about a sample earlier, is narrower, has no overshoot before it and almost none of the slow recovery
over +10..+22. The test bar shows the same thing: on its rise at 62 minutes the two shapes leave -0.07 to -0.11 at
+2..+4 and +0.02 to +0.06 from +6 to +40 at every reading (rms 0.032 against 0.018-0.021 in the other passages). So
the echo has at least a third thing that moves (where it sits and how wide it is), the bar sees it, and two amounts
times two fixed shapes cannot follow it. The owner's "fixed" holds for the first passage only.

Colour: in the capture the test line has no colour at all (U and V at neutral on both fields' lines), so colour has
no per-field reference like the bar. Steady saturated left edges were too few here (3 tracks) to say whether colour
follows the luma echo.

### After the second passage: what the bar can and cannot say, and a reading from the picture itself

Three ways of carrying a description across passages were tried and each failed with a passage held out
(`wide.py`; bands on the held-out passage's left edges, codes, by reading):

| description | scored on | bands |
|---|---|---|
| the first passage's two shapes, calibrated on both strong passages | 62 min / first | 10-20 / 3-17 |
| capture-wide bar shapes (below), picture calibration on all three passages | 62 min / first | 10 / 6 / 17 / 19 and 2.6 / 3.4 / 5.4 / 9.8 / 13.8 |
| the same, calibrated without the scored passage | 62 min / first | 12-26 / 4-40 |

What was learned on the way:
- **Two bar shapes do describe the bar everywhere, but not the two from one passage.** Over 1,533 bar rises 5 s apart
  across the capture (`wide.py build`, from the survey's test lines) two shapes leave the bar at its field-to-field
  noise (0.020 against 0.020) in every passage, 62 minutes included. The first passage's pair pointed elsewhere.
  Across the capture the second amount runs -0.85 to +0.52 (5-95%: -0.33 to +0.23); the 62-minute passage sits in
  the lowest twentieth.
- **The bar and a picture edge do not show the same echo.** Passing the bar's shapes through the kernel that turns
  the bar's no-echo edge into the picture's misses the picture's measured shapes by 40% (first) and 100% (second).
  On the bar the second amount moves +8..+12 by 0.3 per unit, inside every passage; on picture edges by 0.03-0.10.
  It is not the bar's size: picture steps of 170-260 codes behave like smaller ones. Cause not found.
- **What a picture edge does per unit of a bar amount changes with the echo's state** (the dip per unit of the
  first amount peaks at +4 in the weak passage, +6 in the first, +2..+4 at 62 minutes), so one calibration cannot
  serve the capture, and a calibration made inside a narrow, far-off range cannot be run back to no echo.
- **Bounding the division does not remove the bands** at 62 minutes; it only leaves echo in (limits 0.03-0.3:
  bands 15-21 codes at the strongest readings, dip left 0.22-0.47 of the step).

**Reading from the picture (`direct.py`).** Each frame's echo is read from that frame's own left picture edges
(lines that step out of blanking into a flat stretch, pooled by median) against one fixed reference edge (the
first passage's edge run back to no echo), and taps are solved for it. No bar and no shapes in the reading.
- Known answer on frames with no echo of their own (210 frames of another tape; this capture's weakest passage
  cannot serve, its own moving echo is rightly removed and then counted as error): a made-up echo moving in
  strength (0.03-0.46 of a step), place (4.2-7.8 samples) and width. Error against the clean frames, codes rms by
  strength: captured 3.9 / 6.6 / 6.7 / 4.7, removed 3.1 / 5.1 / 4.6 / 2.1, removed with the true system 2.7 / 4.5 /
  4.4 / 1.7. With no echo added the reading changes the frames by 0.65 codes.
- Read from even rows, scored on odd rows: first passage bands 3.0 / 2.3 / 2.6 / 4.4 / 6.1 codes and 0.073 of the
  dip still following the reading (the calibrated removal judged fixed there: 1.5 / 1.8 / 2.3 / 4.3 / 6.9, 0.062).
  62 minutes: 10 / 7 / 12 / 15 codes, 0.082; the edge comes out the same at every reading (0.73-0.74 at +8, 0.81-0.83
  at +14, 0.94-0.95 at +20).
- What the band figure at 62 minutes is made of: after removal +14..+44 sits 3-7% lower than captured, mostly the
  reference edge's slow settle being imposed on a scene whose own left edge is flat by +20 (the bar shows no echo
  out there in this passage), plus a ripple of 2-3.5% at readings above 0.75.
- Taking the part beyond +16 from the bar instead (`mix`) scored worse on both passages (62 min 17 / 12 / 21 / 22,
  first 1.9 / 3.0 / 4.2 / 7.0 / 8.7).
- Frames with too few such lines (364 of 900 at 62 minutes, 139 of 900 in the first passage) take a straight-line
  fit on the bar's amounts made on the frames that could be read; it reproduces their readings to 0.030 of 0.140.
  Too few steady edges fall in those frames to score them, and the known answer did not exercise that path.

A clip of the 62-minute passage with this reading was sent on 2026-11-25. The owner: the bands are still there, and
in motion there are rolling diagonal bands the removal introduces or enhances. Their question: the echo was added at
RF and then demodulated, so why invert it as if it were added to the demodulated picture; should the inversion not
depend on level?

- **The diagonal bands are the capture's own content, about doubled** (`diag.py`, 62 minutes): line-to-line
  content after / before removal is 1.3 / 1.9 / 2.1-2.2 / 1.6-1.8 / 1.2-1.3 at 0.25-0.35 / 0.35-0.45 / 0.45-0.55 /
  0.55-0.70 / 0.70-1.0 MHz and 1.0 elsewhere; the exact undoing asks for a gain of 4-10 at 0.45-0.55 MHz.
- **The echo is not the same at every level, so it is not a linear operation on the picture** (`stair.py`: the
  staircase's four risers, each about 0.17 of the bar, at four levels, strong-echo fields against weak ones).
  Each plateau sinks under strong echo, more the higher it sits (3-25% of a riser at +24, up to 0.03-0.04 of the
  bar); the plateaus carry colour subcarrier and the bar, which does not sink, has none. A level that moves with
  the echo where subcarrier is present cannot come from a linear operation. The dip as a share of its riser, net
  of that sinking, readings above 0.75: first passage 0.52 / 0.58 / 0.62 / 0.64 from the lowest riser to the
  highest and 0.69 on the bar (relatively stronger toward white); 62 minutes 0.79 / 0.86 / 0.85 / 0.82 and 0.76 on
  the bar (no trend with level; small steps hit harder than the full step).
- This is why the bar and picture edges disagree and why one calibration cannot serve. "Linear in level" under
  "What it is" compared steps that all start at blanking and did not test this.

**Steady tones in the capture itself** (`tones.py`: line-to-line spectrum of the captured luma, each peak's phase
step per line and per frame). The owner sees diagonal bands in every capture made with this VCR.
- A comb at 291.85, 792.36, 1293.2, about 1790 and 2292 kHz (spacing 500.5 kHz), 2-4 times the background, steady
  from line to line (coherence 0.7-0.8) and frame to frame. The 292 kHz member is 46 samples per cycle and steps
  -162.5 degrees per line: a slanted band about every 21 lines of a field, which rolls. Strongest at 62 minutes,
  weaker in the first passage, not found in the weak passage three minutes before 62, and not found in a September
  capture of a commercial tape through the other chain. Cause not identified; not the capture device.
- Checked on 10 s of another capture made three days earlier (a different tape, same week): no comb, and no steady
  tone above 1.6 times the background anywhere from 0.08 to 5.5 MHz. On this evidence the comb belongs to this
  recording, not to the VCR, and whatever the owner sees in every capture has not been found by this measurement.
  Band-passing a field around 292 kHz to picture the tone shows mostly picture edges ringing in the filter; no
  usable picture of it was made.
- **The bands the owner sees in every capture from this VCR are a different tone, near 393 kHz** (`tones2d.py`: a
  two-dimensional spectrum of flat patches; `tones.py` works on line-to-line differences and is nearly blind to a
  tone that barely changes phase from line to line). The owner pointed at another capture made three days earlier,
  a commercial tape. 36 frames spread across it: in 14 of 18 frames with a flat patch a tone at 392.0-393.0 kHz
  stands about 100 times above its column's median (neighbouring frequencies 12), stepping -3 to -23 degrees per
  line: about 21 slanted bands across the picture. The echo capture has it in all three passages at about 395 kHz,
  +20 to +25 degrees per line. Size 0.84-0.96 codes peak to peak in both captures, the same at patch levels of 15,
  19, 27, 124 and 208 codes: it is added to the finished picture, not carried on tape. A September capture through
  the other chain does not have it (0 of 6 flat frames). A free-running source somewhere in the playback chain
  (its frequency differs by 0.6% between the two captures); which box is not established.
  The echo removal about doubles it (gain 1.9-2.2 at 0.35-0.55 MHz).
  It is not in every capture from that week (`tonesmall.py`: many small flat patches; `tonediff.py`: differences
  between consecutive frames, which cancel still picture and keep a free-running tone; both find it where the
  large-patch measurement does). Present: the capture the owner pointed at (24 x against 5-7 beside it) and the
  echo capture (9-20 x against 2-4 in all three passages). Absent: another commercial tape captured the same day
  as the first (3.0 x against 3.4-3.8, 585 patches) and a home-edited tape captured four days later (1.7 x against
  1.4-1.6). Undetermined: a camcorder tape from October (one quiet patch in 10 s). So it goes with the tape while
  being the same size at every picture level. Candidate, not tested: the two Hi-Fi sound carriers of VHS sit 400
  kHz apart, and a beat between them leaking into the picture would be there only on tapes with a Hi-Fi track, at
  a frequency set by the recorder that made the tape.
- 1266.6 kHz = 80.5 x line rate, flipping every line: twice the VHS colour-under carrier, colour leaking into luma
  on tape. 9 times the background in the weak passage, 3 in the first.
- 920.6 kHz = 58.5 x line rate in the first passage: the sound/colour beat of the off-air reception.
- The removal multiplies content by 1.2-1.3 at 0.25-0.35 MHz and by about 2 at 0.35-0.55 MHz (above).

Not yet done: a model of the echo at RF (picture as carrier amplitude, a delayed copy with strength, phase and
delay, then the detector), fitted to the whole test line.

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
| `wide.py` | bar shapes learned across the capture; picture calibration over several passages with one held out (failed, see above) |
| `direct.py` | each frame's echo read from its own left picture edges; known answer, scores, removal |
| `stair.py` | the echo after each staircase riser, by level: is it the same at every level |
| `diag.py` | what the removal does to line-to-line content by frequency (the diagonal bands) |
| `tones.py` | steady interfering tones in a captured stretch: frequency, step per line, step per frame |
| `tones2d.py` | slanted bands in flat patches: two-dimensional spectrum, also sees tones that hardly change from line to line |
| `tonesmall.py`, `tonediff.py` | the 393 kHz question in busy picture: many small flat patches; differences of consecutive frames |
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
| `harness.py` | scoring in the picture (steady left edges, bands, fill) and on the test line by part; the echo's shapes read from the picture and their taps; known answer; removal of a stretch |
| `shape2.py` | is the fast-moving second amount echo or the test line's own? |
| `panel4.py` | stills: captured, second clip's removal, reworked, and both differences |
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

- Every removal here treats the echo as a linear operation on the demodulated picture; `stair.py` shows it is not.
  A model at RF is the next thing to try.
- The reading from the picture (`direct.py`) is the only one that holds in both passages; the owner still sees bands.
  Its open points: frames without usable left edges (filled from the bar, unscored); the reference edge is one
  scene type's and is imposed on others beyond about +12; two passages only.
- Why the bar and picture edges show different echoes is not known.
- Colour: no measurement yet of whether it carries the echo beyond the 8 frames under "What it is".
- What is left after the left edge (above): tape's own edge or echo that is never absent.
- Narrow strokes: the 2T pulse is not improved at strong echo; fine lettering above a reading of 0.8 is not clean.
- Bands of 4-7 codes remain above a reading of 0.65.
- The zero of the second amount rests on the fast part averaging to nothing when the slow part is weak.
- The five-line cleaning threshold was chosen by hand; luma only.
