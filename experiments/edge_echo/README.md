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
  The owner (2026-11-25): the commercial tape that shows it is Hi-Fi and the commercial tape that does not is not
  Hi-Fi; the off-air tape of the echo capture (has it) is Hi-Fi and the home-edited tape (does not) is not. Four
  for four. Intermodulation between the two Hi-Fi carriers giving slanted stripes over the whole picture
  is described in the patent literature for the third-order product near 0.9 MHz (US 5,347,405); the plain
  difference near 0.4 MHz, which is what is measured here in luma, was not found described. A companion tone near
  0.94 MHz shows in one flat frame of the Hi-Fi tape only, not in the others: no support from that.
  Last check, at the owner's request: a Hi-Fi tape captured through the OTHER chain (36 spread frames, 199 quiet
  small patches): no tone, 1.3 x against 1.7-1.9 beside it and nothing anywhere from 300 to 500 kHz; fitted size
  0.16-0.27 codes in its quietest frames against 0.84-0.96 where the tone is present. So it takes both: a Hi-Fi
  tape and this VCR" was the reading at that point; the next check withdrew it.
  Then the first tape of the same series (same production house, Hi-Fi, captured on THIS VCR): no tone either (4.0 x
  against 3.5-4.3 beside it, nothing from 300 to 500 kHz, 0.25 codes fitted in its quietest frame). So a Hi-Fi
  tape on this VCR is not enough; it depends on the tape. Every tape with the tone is Hi-Fi (two), no tape without
  Hi-Fi has it (two), and two Hi-Fi tapes from one production house lack it on either chain. Whether the tone is
  recorded on those two tapes by the machines that made them, or made in playback by this VCR from something those
  tapes have more of, is not separated: playing a tape that has it on the other deck would.
  In the flattest frame the tone's frequency moves between 386 and 399 kHz from line to line and its phase moves
  by 40-50 degrees along one line while its size stays 0.9-1.0 codes: frequency modulation, as sound carriers
  have and a power supply does not.
- **Taking the tone out (`tonecut.py`), an experiment, luma only.** A band-stop wide enough for the tone's wander
  would ring by about 5 codes around a 200-code edge, to remove 0.9 codes. So: one slanted wave fitted in small
  half-overlapping patches (16 lines x 480 samples), subtracted only as far as it stands above what the same patch
  shows at the frequencies beside the tone, never above 1.3 times the tone's size.
  - On 10 s of the tape that shows it best (dark title card, then picture): small flat patches 32 x -> 2.9 x the
    column median; differences of consecutive frames 27 x -> 7 x; large flat patches standing out in 38 of 58
    frames -> 4 of 58, fitted size 0.78-0.91 -> 0.16-0.23 codes.
  - Frames of two tapes without the tone: changed by 0.04 codes rms, never more than 0.53 codes at a sample.
  - Known answer with a made-up tone matched to the real one's wander (three statistics, in the script): 62% of
    it removed on a flat card with 1.5 codes of noise, 47% with 3 codes; on ordinary busy picture 4-16%. It acts
    where the picture is flat, which is where the tone can be seen, and leaves it elsewhere.
  - The tone is under half a code. Subtracted and rounded back to whole 8-bit codes, the capture's values simply
    return (measured: no change at all). The result has to stay finer than 8 bits, or be rounded with dither
    (0.29 codes rms of added noise), which the clip sent to the owner uses.
  - Three earlier estimators failed the known answer or the tone-free control and are described in the script's
    head: a four-cycle sliding fit, one sine per line, and patches judged against white noise.
  - Not done: colour; the echo capture (its tone sits near 395 kHz); any wiring into a render; the patch size and
    the two factors were chosen on five frames of one tape.
  - The owner watched the clip (2026-11-25): the bands are still there. Measured afterwards by part of the clip
    (tone over the boxes 90 kHz either side, in quiet patches of consecutive-frame differences; 1 = nothing): dark
    title card 28 -> 1.9, and a decoded frame of the clip itself shows no bands there; the bright picture after it
    12 -> 5.6, so the tone is still in the not-flat parts of ordinary picture. Which part the owner means is not
    yet known.
  - Tried against that residue: a running median for the slow part (keeps step edges out of the fit): no gain
    (5.7); smaller patches: worse on both parts; the factor at 1.2: 1.0 and 4.0, with tone-free frames changed by
    0.075 codes; an estimator that turns the tone's band down to zero frequency and smooths it in two dimensions
    everywhere: far worse (14 on the dark card), dropped. In noisy or textured picture the tone (0.45 codes) is
    below what the picture and tape noise put at the same frequency, and a blind estimate from luma cannot tell
    them apart.
  - The owner: the bands that remain are in the picture after the card. Tried then, and not kept: fitting the tone
    in the difference between a frame and the median of its neighbours (still picture cancels, the rolling tone
    does not), all frames solved in passes. Known answer on 30 consecutive frames of a tone-free tape with a
    made-up tone: 93% of the tone left (96% one frame at a time); only 4% of that footage holds still, and even
    there 93% is left. The limit is not the picture but the noise: the tone is 0.45 codes against 4-5 codes rms of
    tape noise in ordinary picture, and a patch small enough for the tone to stay in step does not hold enough
    samples to find it. A blind estimate needs far more samples in step than the tone's wander allows; removing it
    in ordinary picture needs the tone's phase from somewhere else. Untried: if it is the two Hi-Fi carriers
    beating, its phase follows the difference of the two sound channels, which the capture also holds.
  - That was then tested and found nothing (`tonesound.py`; the same 10 s read again with its sound, `stretch.py
    ... audio`). On 51,718 flat lines of the title card the tone's frequency (median 392.9 kHz, spread +-4.4 kHz)
    was set against the captured sound averaged over each line: right minus left, left, right, and their sum, at
    every offset within +-50 ms. Strongest correlation 0.014; the same with the frequencies shuffled gives 0.012.
    Limits of the test: the sound under the title card is near silence (about -58 dB, mostly hiss), the only
    place where lines are flat enough to read the tone's frequency. The captured sound was the Hi-Fi sound (owner).
    So no predictor from the captured sound, and the carrier-beat explanation is not confirmed by this; the tally
    of tapes still stands. Not yet tried: a flat passage with loud sound, where a relation, if any, would be
    plain.
    Then the deciding case: the end credits of the same tape, a flat dark card for 10 s with loud sound throughout
    (left about -16 dBFS, right minus left -26 to -42 dBFS; 40 dB above the sound under the title card). 97,511
    flat lines: the tone's frequency spread is +-5.1 kHz (+-4.4 kHz under near silence), its size 0.87 codes and
    frequency 393.0 kHz as before, and the strongest correlation with any of the four sound signals at any offset
    is 0.014 (shuffled 0.008-0.011; chance over 4,801 offsets gives about 0.013). The tone does not move with the
    sound at all. A beat between the two Hi-Fi carriers would have to: each carrier's frequency follows its
    channel. **The carrier-beat explanation is refuted**, and with it "frequency modulation, as sound carriers
    have" above: about half of the measured wander is the reading's own noise (a steady sine in the same noise
    reads +-2.2 kHz), and the rest is fast phase jitter of unknown origin. What stands: which tapes have the tone
    (two Hi-Fi tapes; not two other Hi-Fi tapes from one production house; not the two tapes without Hi-Fi), its
    constant size at every picture level, and a slightly different frequency on each tape. Cause unknown.
    The sound itself reads as Hi-Fi, as the owner suggested checking: content up to 18-20 kHz in the loud part
    (10-15 dB above the quiet part's floor there), a noise floor near -71 dBFS over 1-20 kHz against loud passages
    at -14 dBFS, and hiss that differs between left and right. A linear track would stop near 10 kHz with a floor
    some 25 dB higher. (Lines at multiples of 60 Hz stand 15-27 times above their surroundings in the quiet part:
    head switching or mains hum, not separable in 4 s.)
- 1266.6 kHz = 80.5 x line rate, flipping every line: twice the VHS colour-under carrier, colour leaking into luma
  on tape. 9 times the background in the weak passage, 3 in the first.
- 920.6 kHz = 58.5 x line rate in the first passage: the sound/colour beat of the off-air reception.
- The removal multiplies content by 1.2-1.3 at 0.25-0.35 MHz and by about 2 at 0.35-0.55 MHz (above).

### The echo modelled at RF (`rfmodel.py`): fitting repaired, model not established

The owner's point: the echo was added at RF and then demodulated, so model it there. `rfmodel.py` runs the test
line as broadcast (FCC composite: staircase with subcarrier, 2T and 12.5T pulses, bar, with sync and porches)
through the off-air simulator written for the antenna tape (`rf_sim.py`, copied unchanged from the
`antenna-deghost` branch: negative modulation, vestigial sideband, one delayed copy with complex RF gain and
delay, tuner filter, detector, sync-tip AGC, back-porch clamp), then a fitted stage for recorder, tape and
playback, then the capture's limits. Per group of fields (passage x reading, 8 groups, 168-1,181 test lines each):
the reflection (strength, carrier phase, delay). Shared by all groups: the line's pulse positions and levels, the
tuner's sideband slope (width and centring), the tape stage. With rf_sim's own tuner filter this file returns
rf_sim's output exactly, for all four detectors (`check`).

**First fits (withdrawn as numbers).** With the tuner slope fitted and shared and per-group numbers solved by
turns, the reflection came out as "0.6 microseconds late, a quarter turn off the carrier, strength 0.23-0.90
following the reading". That fit failed its known answer (2.0-2.6 IRE against 0.4 of noise). What survives in
every later fit, from every start and with either detector: strength rises with the reading in both passages; the
phase is negative, between an eighth and a third of a turn; the 62-minute passage sits 10 to 45 degrees from the
first. The delay (5.6-11 samples) and the phase are not settled.

**Three faults in the fitting, repaired.** (1) A captured line is scaled to its own bar top and placed on its own
half-height crossing; the model line was not, so anything the echo did to the top or the crossing was a misfit.
The model line now goes through the same two rules. (2) The shared numbers and the per-group numbers were solved
by turns, which stalls where they trade against each other; they are now solved together, from four starting
tuners. (3) The reflection is solved as a complex gain, not strength and phase. Known answer (`recover`: made-up
lines with their own tuner slope, tape filter and unknown placement, put through the capture's scaling and
placing, 0.3 IRE of noise): either detector fitted to its own lines ends at 0.36-0.38 IRE, recovers every
reflection (strength within 0.01, phase within 3 degrees, delay within 0.2 samples) and the tuner slope, and
predicts made-up picture edges to 4-11% of the echo. Fitted with the other detector the same lines end at 1.2-2.6
IRE with picture edges 20-57% off: on lines of this kind the detectors can be told apart.

**The captured lines do not fit (2.4-2.5 IRE with either detector), for two measured reasons.**

- *The recorder/player sharpens small edges more than large ones.* On the weak-echo line each staircase riser
  (15-18 IRE) overshoots by 36-40% of its height; the bar (100 IRE) overshoots by 14%. One tape filter cannot do
  both: the weak line alone, with its own filter and reflection, stays at 1.7 IRE. A tape stage with size-limited
  detail (the line's detail, limited at 3, 10 and 30 IRE, each with its own taps) brings the weak line alone to
  0.9 IRE (bar rise 2.8 -> 0.9); what is left there is a ripple on the staircase tops (the tape's colour, not
  modelled).
- *The echo is deeper, in proportion, on the full-height edge than on small steps.* Strongest group of the first
  passage: the bar falls to 22 IRE after its rise (78% of the step); the staircase risers fall 9.5-10.4 IRE below
  their plateaus (about 55-60% of a step). Neither detector with one reflection gives that: fitted, the bar's
  lowest point is 40 against 22, while the risers come out about right (envelope) or too deep (synchronous).

**With the size-dependent tape stage the test line no longer settles the reflection.** All groups together end at
2.1-2.4 IRE from every start and with either detector; the same group's strength ends anywhere from 0.10 to 0.43
depending on the start. A strong-echo line alone fits to 0.9-1.5 IRE, with reflections that mean nothing
(strength 0.06 at delay 15.6 in one): a tape stage free enough for the measured sharpening can imitate the echo.
The known answer with this stage fails (1.24 IRE against 0.3, phases 60 degrees off, picture edges 34-45% off).

**Picture edges (`edges`), which the fit never saw: failed.** Left picture edges (30-110 IRE steps out of
blanking), the change between the weakest- and strongest-echo groups of a passage, in units of the step. Captured
change at its deepest: -0.39 to -0.54 (first passage). The model's: -0.26 to -0.30, missing 35-49% of the captured
change with either detector. Taking the change to be the same at every step size (a linear echo at its best)
misses 23-26%. No passage has picture edges without echo (the weak passages' edges sit at readings 0.3-0.5), so
only changes can be compared.

Not known: whether the size dependence of the echo is made at RF (a detector unlike either here, more than one
reflection) or by the recorder's size-dependent stage acting on a linear echo. The test line alone does not
separate them.

### Two reviews of the RF turn (2026-11-26): the request for another tape withdrawn

The owner's objection to the conclusion above ("why do you need it? ... initial tests looked very good but there are
just a few residual issues to fix") was put to two reviewers working apart, each with the code, the arrays and the
owner's words: Codex and an adversarial reviewer. Both: a tape from the recording VCR is not needed, and identifying
the whole chain was the wrong response to "should the inversion depend on level". Their measurements, with what was
rerun here:

- **The owner's question has a short answer from the chain alone** (`rfmodel.py level`, no tape stage, no fit, no
  data; rerun here). Plain luma steps of 20-100 IRE out of blanking, reflection a quarter turn off the carrier: with a
  synchronous detector the echo is the same share of the step at every height (0%); with an envelope detector its
  depth differs by under 5% and its shape by 7-19% of the echo for 20-80 IRE (18-32% at 100 IRE). So for plain luma a
  linear removal is the right frame, and a fixed recorder/player stage after a near-linear echo never has to be known.
- **Why the staircase disagreed with the bar: its colour, not its size.** In the same chain the bar's dip is 1.18-1.30
  times the risers' with the staircase's subcarrier on (envelope detector) and 1.01-1.08 with it off; a synchronous
  detector gives 1.02-1.04 either way. Captured: about 1.2-1.3 (Codex: riser dips 60-66% of the current step against
  78% for the bar, and the README's "55-60%" depends on the denominator). "The echo is not a linear operation"
  (`stair.py`) holds for a line carrying 40 IRE of subcarrier, not for plain luma. Its "small steps hit harder at 62
  minutes" is a second definition (strong minus weak, mostly the riser losing its overshoot), not a second behaviour.
- **Small risers overshoot 36-40%, the bar 14%: measured, cause not attributed.** Reproduced by both, in both fields,
  not the capture's ceiling, not residual subcarrier ripple (0.05-0.11 IRE), not rise-time difference alone. Nothing
  assigns it to the recording machine rather than the player or the line as broadcast. "The recorder sharpens small
  edges more" above is withdrawn as a cause.
- **The fitted lines pool two different waveforms.** Field 1's test line minus field 2's is 1.7-2.1 IRE rms in every
  passage (split-half noise 0.2-0.7; rerun here), about the size of the fit's misfit. Field 2 alone still does not fit
  (1.79 IRE, envelope). Also: fitted values of the line as broadcast sit at their bounds; the model scales and shifts
  before its size-dependent stage where the captured lines were scaled and placed after it (0.3-1.5 IRE); the bar top
  is 182 codes in the weak passage and 219-237 at strong echo, unexplained.
- **The bands left by `direct.py` are made by the method.** Adversarial bench: echo-free frames of another tape given
  each 62-minute frame's fitted kernel (exactly linear), cut and rounded, then `direct.py`'s own reading and removal:
  leftover ripple 0.030 / 0.048 / 0.072 of the step by reading (real capture after removal 0.039 / 0.067 / 0.086).
  With the true kernel the ripple is the division limit (0.057 -> 0.034 -> 0.021 above a reading of 0.75 as the limit
  goes 0.01 -> 0.003 -> 0.001, for 3.9 -> 4.3 codes of whole-picture error); the reading gets the near-null's depth
  wrong (0.060 read against 0.028 true). Caveat noted here: those kernels put 0.063-0.087 of ripple at +22..+92 on the
  clean frames where the capture itself shows 0.035, so the kernels' tails overstate the real echo; the bench matches
  the size, not necessarily the route.
- **The reference edge is imposed.** Codex: `direct.py` with its production reference, on a tape with no echo and none
  added, changes the picture by 4.5 codes rms (2.3 with a reference learned from that tape; the README's 0.65 used a
  reference from the same frames). Adversarial: at 62 minutes every left edge comes out at 1.22-1.25 at +2 (captured
  0.92) and the reading asks for -0.075 at +20 because the first passage's reference is still settling there.
- **Other residuals measured:** the removal multiplies the 393 kHz region by 1.7-2.1; frames filled from the bar barely
  remove what follows the reading (0.471 -> 0.368; read frames 0.366 -> 0.087; a hidden readable frame is predicted to
  0.055-0.072 of the step at the dip); every "per unit of amount" slope is diluted by the reading's noise (to about
  0.88 of the truth in the first passage, 0.40 at 62 minutes), which is most of "the bar and picture edges show
  different echoes" (a one-sample shape difference survives).
- **Not decided by either:** whether the echo's share depends on level in the picture (the estimator is the diluted
  one); the detector type; what a never-absent part of the echo looks like (a common fixed distortion cannot be told
  from the tape's own edge without an anchor).

Next, in this order: (1) on the known-answer bench (echo-free frames, kernels with a near-null), how the frame's
kernel is read and the division limit, scored against the clean frames: success is ripple at or below 0.03 of the
step above a reading of 0.75 with whole-picture error no higher than 3.9 codes; failed if no reading from the frame's
own left edges gets below 0.05. (2) Each steady edge keeping its own baseline, changes fitted with and without a
level term on held-out tracks and time blocks, with the reading's noise handled: the level term is kept only if it
cuts the held-out error at the dip by 20% in each passage.

### Reading the echo from the test line (`barread.py`, `reflect.py`): right in the dip, not usable as the picture's kernel

Tried as the cure for the imposed reference edge: the test line is the same waveform in every field, so its reference
is truly fixed, and every field has one. Only its plain-luma parts are read (2T pulse, the bar's rise and top).

- **No stretch of this capture is free of echo.** As a running median over 11 frames the reading is never below
  0.12 in any array here; single lines reading below 0.1 (the "almost-no-echo edge" of `family.py`) are noise picks.
  The reference is therefore the weakest state (running median below 0.15, 74 lines per field), every kernel here is
  relative to it, and a removal takes the picture to how it looks there. In that state the picture's own left edge
  overshoots to 1.12, dips to 0.79 at +7 and is back by about +24 (the bar: 1.17, 0.88, back by +20).
- **The echo starts before the edge.** At strong echo the foot of the bar's rise comes up as well as its top coming
  down; free taps need two lags before the edge (misfit 2.6% -> 1.6% of the bar; more lags add nothing). An echo that
  only follows the edge cannot do that; a reflection a quarter turn off the carrier does (its quadrature part is an
  odd function of frequency below the receiver's slope).
- **Free taps (89 per field, `barread.py`).** Known answer (`ka`: the reference lines through made-up echoes, three
  that only follow the edge and three as a reflection at RF makes them, with gain, shift, noise 3.5 codes, rounding
  and the capture's limits): an echo of 0.06-0.41 of a picture-like edge comes back to 0.003-0.023, the depth of the
  near-cancellation within 5%. Three faults the known answer caught on the way: gain, sideways shift and the first
  tap trade freely on a rise (level now pinned, no shift fitted); samples the capture cut off at blanking were read
  as echo (now left out); straight-line interpolation blurred the rise (now band-limited). On the captured lines the
  fit leaves 1.5-1.7% of the bar; the two fields' taps agree to 0.02 rms.
- **One reflection (`reflect.py`): three numbers per group, fitted to the change from the weak line, so the line as
  broadcast and the recorder never enter.** 22 pooled lines, 38 numbers: 2.2% of the bar from four of five starts
  (free taps: 1.4%; the line set beforehand was 1.5 times the free taps, missed at 1.56). Delay 6.3-6.9 samples
  (0.47-0.51 microseconds) in every group; phase -129 to -138 degrees in the first passage and the weak one, -111 to
  -123 at 62 minutes; strength 0.48 -> 0.88 and 0.64 -> 0.96 with the reading; weak state 0.40 at -144 degrees;
  receiver slope 0.72 MHz wide (straight) or 1.03 (raised cosine), the same fit either way. Per frame the three
  numbers move by 0.005 and 0.03 samples from one frame to the next.
- **On the picture's steady left edges** (`barread.py score`, `reflect_score.py`; odd rows; division limit 0.01):

  | | same edge, stronger minus weaker echo, +2..+24 / +26..+90 | ripple +22..+92 of the removed edge by reading, first passage | 62 minutes |
  |---|---|---|---|
  | captured | 0.055 / 0.002 | 0.037-0.044 | 0.032-0.035 |
  | free taps from the bar | 0.021 / 0.015; rings at about 2.4 MHz | | |
  | one reflection, all frequencies | 0.025 / 0.019; rings at about 2.2 MHz | | |
  | one reflection, below 1.6 MHz only | 0.012 / 0.014; no ringing | 0.042 / 0.062 / 0.095 / 0.135 / 0.172 | 0.081 / 0.089 / 0.134 / 0.159 |
  | `direct.py` (passes "same edge" by construction on left edges) | 0.007 / 0.003 | 0.040 / 0.036 / 0.036 / 0.032 / 0.027 | 0.039 / 0.039 / 0.067 / 0.086 |

  With the one-reflection reading the edge comes out the same at every reading within 0.02 (first passage +6..+18:
  0.80-0.87; 62 minutes 0.77-0.94) and looks like the weak passage's own edges, so the dip is the same echo on the bar
  and in the picture. But far after the edge it adds 2-5 times the ripple `direct.py` does, at every reading in
  both passages. It is not the padding of the profile (same with 1,500 samples of hold) and not the reflection's
  own tail (its step response is back to 1.00 by +26): it is the division by a near-cancellation near 0.45 MHz acting
  on the scene's own slow settle after an edge. The bar's near-cancellation is not the picture's closely enough to
  be divided out.
- **Calibrating the test line's state to the picture (`reflect_cal.py`)**: each steady edge keeps its own shape, the
  per-frame state comes from the test lines, a few shared numbers are fitted on half of the first passage's long
  tracks. With the weak state left free it wandered (an edge's own shape absorbs anything common to all frames) and
  wrecked the edges; pinned, the fit asks for almost nothing (strength x 0.99, phase +4 to +6 degrees, delay +1.0 to
  +1.3 samples). Held out: the same edge at stronger against weaker echo 0.055 -> 0.016 near and 0.006-0.007 far;
  ripple of the removed edge 0.061-0.110 on the first passage's other tracks and 0.058-0.123 at 62 minutes. Better
  than uncalibrated, still 2-3 times `direct.py`. Dropped as a kernel.
- **A reference edge made for the passage (`scene_ref.py`)**: `direct.py`'s reading, its one fixed reference replaced
  by the passage's pooled edge with the one-reflection echo divided out (first 18 samples) joined to the captured
  pooled edge (from +26, which the echo does not reach). Judged on the frame's own test bar after removal with the
  picture-read taps (independent of the picture's left edges), rms of the bar by reading:

  | 62 minutes | bar rise, captured -> fixed reference / passage reference | picture ripple +22..+92, fixed / passage |
  |---|---|---|
  | 0.45-0.55 | 0.144 -> 0.059 / 0.040 | 0.034 / 0.057 |
  | 0.55-0.65 | 0.159 -> 0.068 / 0.053 | 0.033 / 0.059 |
  | 0.65-0.75 | 0.186 -> 0.069 / 0.055 | 0.058 / 0.082 |
  | 0.75-0.90 | 0.209 -> 0.081 / 0.072 | 0.068 / 0.092 |

  The bar comes out 10-30% closer with the passage's reference and the picture's far ripple 25-70% larger; in the
  first passage the two references score the same (the fixed one was made there). The join at +18..+26 carries the
  first swing of the one-reflection removal's own ripple, which may be the cause; not pursued. Either way the
  picture-read taps leave 0.04-0.08 of the bar on the bar's rise, make the 2T pulse worse in the first passage
  (0.050 -> 0.068 ... 0.130 -> 0.161) and add to the bar's top (0.018 -> 0.03).
- Above about 2 MHz the test line's echo does not carry over at all (the ringing); consistent with small and large
  edges being sharpened differently (above).
- **So:** the test line gives the echo's form and a quiet per-frame state (three numbers), not the kernel. The
  picture-read kernel stays; what it lacks is still a reference that is not one scene's.

### Removal that adds nothing where no ghost is predicted (`gate.py`, 2026-11-26)

Owner's target: "good cancellation with no extra artifacts", not complete cancellation; and the question why tapering
the cancellation toward the carrier does not prevent the artifacts.

- **Where the removal boosts.** `direct.py`'s per-frame taps, picture left by the echo and the removal's boost (division
  limit 0.01), median by reading. All the boost sits between 0.2 and 0.85 MHz; above 0.85 MHz the removal attenuates
  (0.65-1.1). First passage: picture left at 0.39-0.45 MHz 0.77 (reading 0.30-0.45) down to 0.24 (0.75-0.90), boost 1.3
  to 3.6. At 62 minutes the hole is deeper and sits at 0.5 MHz: 0.27 down to 0.09 left, boost 3.3 to 5.0 (the limit)
  there and 2.0-2.8 at 393 kHz.
- **A taper toward the carrier keeps the boost out and the ghost in.** Taps weakened by w(f) = 1 - exp(-(f/f0)^2/2),
  the smallest f0 per frame that keeps the boost under 1.5 or 2.5. The ghost is that band: the dip after an edge is the
  0.3-0.7 MHz part of the edge gone missing, so not boosting it leaves it. Known answer (below), where the true echo is
  over 8 codes: error captured 22.3, taper 21.3 / 19.8, full removal 3.2. Real edges at 62 minutes, reading 0.75-0.90,
  level at +6: captured 0.19, taper 0.35 / 0.46, full 0.85; the 2.5 taper leaves ripple 0.138 against 0.035 captured.
- **Gate.** The full removal's correction (removed minus captured) is applied only where its local size (rms over 17
  samples twice along the line and 3 lines of the field) stands clear of the frame's own floor (10th percentile of that
  size): share applied = 1 - 9 floor^2 / size^2, never below 0. Flat picture stays as captured. A lower division limit
  (0.003, "more boost") was tried on top of it and withdrawn (below).
- **Known answer** (`gate.py ka`: 100 echo-free frames of another tape, taps of 352 strong-echo frames of the 62-minute
  passage, noise 0.7 codes, a 393 kHz tone of 0.45 codes, cut off and rounded; removal with the true taps). Error against
  the echo-free frames, codes rms, by the true echo's local size:

  | | 0.5-1 | 1-2 | 2-4 | 4-8 | over 8 | tone left (0.45 put in) |
  |---|---|---|---|---|---|---|
  | captured | 1.13 | 1.67 | 2.76 | 5.12 | 22.3 | 0.45 |
  | full removal | 1.42 | 1.75 | 2.11 | 2.46 | 3.24 | 1.02 |
  | gated | 1.14 | 1.67 | 2.59 | 3.06 | 3.36 | 0.45 |
  | gated, more boost | 1.14 | 1.68 | 2.61 | 3.10 | 3.03 | 0.45 |

  Pass lines set beforehand (tone within 10%; over 4 codes within 15% of the full removal and under half of captured;
  between, no worse than captured): met. Not tested: picture with a true echo under 0.5 codes (under 1% of these frames).
  With the factor at 4 instead of 9: 4-8 codes 2.60, tone 0.46.
- **Real passages** (`gate.py score`, steady left edges on odd rows, taps from even rows). The pooled removed edge is
  the full removal's to 0.01. Ripple +22..+92 at 62 minutes by reading (0.45-0.55, 0.55-0.65, 0.65-0.75, 0.75-0.90):
  captured 0.035 / 0.034 / 0.033 / 0.035; full 0.039 / 0.037 / 0.066 / 0.086; gated with more boost 0.044 / 0.028 /
  0.034 / 0.038. First passage (five bins from 0.30): captured 0.036-0.044, full 0.027-0.040, gated 0.039-0.052: there
  the gate gives back what the full removal gained far after the edge and leaves a soft step of up to 0.016 of the edge
  where the correction fades out. About 36% of the correction is applied (62 minutes); 60% of the removed clip's samples
  are identical to captured.
- **Flat picture at 62 minutes** (373 stretches of 96 samples with a spread under 2 codes): 393 kHz amplitude captured
  0.99, full removal 2.13, gated 1.06 (factor 4: 1.23; factor 16: 1.02); change from captured 2.38 / 0.69 codes rms.
- **Not changed by this:** the reading itself (one reference edge, frames filled from the bar), so what is left at the
  strongest frames' edges and fine lettering is what the full removal left. Edges whose echo is 2-8 codes get part of
  the correction only. A frame with less than a tenth of quiet picture gets a floor that is too high and less removal.
  Colour untouched.
- **Owner on that clip (gated, division limit 0.003):** the earlier artifacts are gone and it still looks good, but
  "occasional vertical bands of bright and dark that move horizontally across the picture", there at some times and
  not at others. Found: with the limit at 0.003 a regular pattern of about 27 samples per cycle (the 0.5 MHz region)
  covers the whole width in the frames where under 0.06 of the picture is left there, and changes from frame to frame.
  At 0.01 it is not seen. Neither known answer predicted it: with the reading's own error in the taps (even-row
  reading against all-row reading, `gate.py ka2`), and with the echo also drifting down each frame to the next frame's,
  0.003 scores best on every count, the error near the cancelled frequency included. What the real picture has that
  these lack is not identified. The left-edge ripple could not see it either: the taps are fitted to those edges.
- **A score that does see it** (`gate.py moving`): a part of the picture that stands still (a caption card on black,
  320 frames), change from frame to frame of what is the same down 180 rows, median frame, codes rms. Captured 0.93;
  full removal as in the earlier clips 1.60; gated at limit 0.003 1.67, 0.01 1.41, 0.02 1.29, 0.04 1.23. Every removal
  makes still picture less still, because each frame's taps are read on their own. Taps averaged over 3 / 5 / 9 frames
  at limit 0.01: 1.15 / 1.10 / 1.10 (1.07 on the rendered clip).
- **Setting now: gated, limit 0.01, taps averaged over 5 frames.** Left edges as before (same edge at stronger against
  weaker echo, first passage: 0.0096 against 0.0547 captured; ripple at 62 minutes 0.044 / 0.030 / 0.043 / 0.048
  against 0.035 / 0.034 / 0.033 / 0.035 captured and 0.039 / 0.037 / 0.066 / 0.087 for the full removal). Flat
  stretches: 393 kHz amplitude 1.04 against 0.99 captured. Known answer at this limit, true echo over 8 codes: 3.4
  against 22.3 captured.
- **Owner on that clip:** the bands are still there, "especially around 14-16 seconds". Found there, frame by frame:
  after the picture's bright left border (a step of about 160 codes at reading 0.80) the removed frames carry a ripple
  of 28 samples per cycle on a wall that is flat in the capture, up to +-7 codes, 100+ samples long, 3.6 codes rms in
  one frame and 1.7 (the capture's own) half a second later. The same train follows every strong vertical edge.
- **What it is.** Where the echo cancels almost everything (0.02 of the picture left at 0.47 MHz in that frame) the
  division limit restores the band on both sides and not its centre. The capture's hole is wide (a compact dip next to
  the edge); the removal leaves a NARROW hole, and a narrow hole rings long: about 20 codes of a 160-code step sit
  within 0.1 MHz of 0.5 MHz. Its depth and place follow each frame's reading, so the train comes and goes. Cutting the
  division's response off in time instead (reach 8 to 64 samples) makes the wall worse (ripple 3.2 to 7.8 against 2.2).
- **Wide leftover hole (`HOLE`, `GMAX`).** The division is made so that division times echo is 1 - B(f), with B the
  shortfall a gain limit forces, widened by a Gaussian of HOLE MHz; one pass. On that wall, ripple over columns 32-112,
  median / largest of 14 frames: captured 1.74 / 1.94, limit 0.01 as sent 2.20 / 4.55, hole 0.15 MHz gain 3 2.06 /
  2.72, hole 0.25 MHz gain 3 1.77 / 1.95, hole 0.25 MHz gain 5 1.82 / 2.39.
- **Scores at hole 0.25 MHz, gain 3, taps over 5 frames, gated.** Still picture from frame to frame (`gate.py moving`):
  0.94 against 0.93 captured and 1.10 as sent (gain 5: 0.99; without the averaging: 1.15). Added where the captured
  picture is flat (`gate.py flat`, 48 samples within 3 codes, 150 frames): 0.35 codes rms, 5.1 exceeded by 1 sample in
  1000, against 0.46 and 6.8 as sent. Ripple +22..+92 at 62 minutes by reading: 0.039 / 0.028 / 0.034 / 0.052
  (captured 0.035 / 0.034 / 0.033 / 0.035).
- **The price: less removal where the echo is strongest.** Pooled edge at +4 / +6 / +8, 62 minutes, reading 0.75-0.90:
  captured 0.39 / 0.19 / 0.42, as sent 1.10 / 0.84 / 0.73, wide hole 0.87 / 0.59 / 0.54 (readings under 0.65: within
  0.06 of as sent). First passage, same edge at stronger against weaker echo +2..+24: 0.025 against 0.0096 as sent and
  0.055 captured. Known answer with the taps known exactly, true echo over 8 codes: 12.0 against 3.4 as sent and 22.3
  captured; 4-8 codes: 4.1 against 3.1 and 5.1. The known answer does not have the trouble the hole is there for.
- **Setting now: gated, hole 0.25 MHz, gain 3, taps over 5 frames.** Judged by the owner on the 62-minute stretch
  (2026-11-26): the moving vertical bands are gone. Not yet judged: whether what is left of the ghost at the strongest
  moments is acceptable.

### Two reviews before going further (2026-11-26): the cancelled band is not the place; thin strokes are

The owner asked for the assumptions behind "reduce it further" to be put to Codex and to an independent adversarial
agent before any work. Both read the code and the record and ran their own checks; the claims used below were
re-measured here.

- **Wrong: "the band is not lost to noise".** Assumed 0.11 codes rms per line near 0.5 MHz (0.7 codes spread evenly
  over 4.2 MHz). Measured in flat picture at 0.42-0.53 MHz: 0.55-0.75 (agent), 0.68-0.72 (Codex), 1.1 on the wall after
  the border from frame differences (here). The 0.7 was the deck's grey-mute floor, not this tape's noise. What the
  echo leaves of an ordinary edge in that band is at or under the noise.
- **The echo's zero sits on the unit circle** (agent; re-measured: |z| 1.0024, 1.0003, 0.9964, 0.9926 at frames 420,
  423, 430, 440, all at 0.474-0.479 MHz). The exact inverse rings for hundreds of samples and changes side (after the
  edge, before it) within twenty frames; the reading's own error there is as large as what is left of the picture.
- **So "a more accurate kernel would allow more gain there" falls.** Both: do not raise the gain or narrow the hole.
- **The response written above was inexact** (both): with the pass after the division, removal times echo is
  1 + (H - 1) B = (1 - B) + B H, i.e. inside the hole the captured echo is put back, and the noise gain reaches 3.9
  where the division's own limit is 3. The leftover dip at strong echo is that hole, by design.
- **The proposed measurement (exact division on the border and on held-out edges) would not have decided anything**:
  noise, a wrong fit, a kernel that differs by field or level, and the zero on the circle all predict ringing; on a
  720-sample line in a 1024-point transform exact division rings from the wrap alone (Codex: 61 codes rms with the true
  kernel and no noise). What would: a forward test with no division (fit on one group of edges, predict another: field
  1 against field 2, large steps against small, rises against falls). First numbers: the two fields of a frame differ
  at the dip by about 0.04 of the step after the odd/even-row control (agent), 0.019 rms in response near 0.5 MHz
  against 0.045 left there (Codex); cause not separated.
- **Found by Codex, re-measured here: features one or two field rows tall get NO removal, in any version.** The
  five-line cleaning drops them from the estimate the echo is predicted from. A 120-code stroke on 40, true taps, no
  noise, error over the stroke's rows in codes rms: captured 23.3; one and two rows tall 23.3 after every removal;
  three rows and taller 14.6 (wide hole) and 5.6 (limit 0.01, three passes). Without the cleaning: 14.6 at every
  height. This is outside the cancelled band and is a candidate for the doubles on fine lettering.
- **Scores do not cover** (both): the two fields against each other; noise texture beside edges (row-incoherent, and
  `flat` looks only where the gate is shut); ringing before edges; small steps against large; static doubles on sparse
  features.
- The reviews differ on one point: the agent would stop (three limits each larger than what is left in the band);
  Codex would pause the gain and not call the leftover unrecoverable before the remover itself (cleaning, pass, gate)
  is tested with known kernels.

### Thin features kept in the echo prediction (`THIN=1`, `gate.py clean_keep`, 2026-11-26)

The five-line cleaning replaces a sample that disagrees with its five-line median by the other rows' mean. With
`THIN=1` such a sample is averaged with the rows that agree with it instead, so a feature one or two field rows tall
stays in the estimate the echo is predicted from. Everything else as before (gated, hole 0.25 MHz, gain 3, taps over
5 frames).

- **Known answer** (50 echo-free frames of another tape, strong-echo taps, noise 0.7, 25 made-up dropout streaks a
  frame; error in codes rms, captured / median cleaning / thin kept). Where the median cleaning misses over 2 codes of
  true echo (7% of the picture): 14.5 / 8.0 / 7.9. Where that missed echo is over 4 codes and most of the true echo
  (0.1%; a one-off variant of the script): 7.6 / 7.2 / 5.3. Elsewhere, echo over 4 codes: 15.1 / 8.4 / 8.4; under 2 codes: 1.60 / 1.60 / 1.65. After a
  dropout streak (which has no echo; one is now predicted and subtracted): 8.0 / 4.9 / 10.7. The pass line set before
  the run (a quarter lower where the echo is missed) was not met on these frames: they hold little fine lettering.
- **Real lettering decides it the other way.** Caption text is four or five field rows tall, so most of a letter
  disagrees with its five-line median. Raw panel of the caption card at readings 0.96 and 0.74: captured doubled,
  median cleaning still doubled, thin kept readable. Output changed on the card by 7.2-7.7 codes rms. In the picture
  the change sits on diagonal edges and foliage (about 3 codes rms, over 10 codes on 2.4% of it); flat picture is
  unchanged.
- **Scores.** Still picture from frame to frame 0.92 (median cleaning 0.94, captured 0.93). Added where the capture is
  flat 0.356 rms and 5.2 at 1 in 1000 (0.346 and 5.1). The wall after the border as captured (1.6-2.0).
- **Dropout-like streaks** (one row, 12+ samples, 30+ codes off both field neighbours, there in that frame only):
  0.13 a frame at 62 minutes, 0.02 in the first passage.
- Judged by the owner: pending.

### The reading led by the test bar; each frame on its own echo (`direct.py readw`, 2026-11-26)

Owner on the clip with thin features kept: no difference seen at a glance; "there is still a ringing problem in both
this and the old version around 18 seconds"; "you can see a ghost shift position and then shift back". And: why a
five-frame mean of the readings, why is every frame not judged by its own echo?

- **What happens at 18 s.** The scene is dark, with 12-23 dim left edges a frame (step about 55 codes). The reading
  switched between the frame's own edges (20+ lines) and the bar's fit from one frame to the next, and the own reading
  from so few dim edges is sometimes wrong outright (frame 550: tap at lag 1 +0.66 where its neighbours have -0.08).
  The five-frame mean then carried that into four more frames. Measured on the black beside the picture's right
  border (a falling edge's echo is a bright bump there, on a known level; `gate.py border_ghost`): the ghost left
  after removal, share of the border's step, at frames 545 / 548 / 551 / 554: 0.51 / 0.59 / 0.61 / 0.56 with the old
  reading, 0.52 / 0.53 / 0.49 / 0.50 with the new one (captured 0.83-0.89).
- **Why there was a mean at all.** A frame's own picture reading alone made still picture change more from frame to
  frame after removal than in the capture (1.15 against 0.93); the mean hid that. It also smears any real change and
  spreads one bad frame over five.
- **The new reading (`readw`).** The test bar is in every frame and reads the echo the same way whatever the scene:
  its fit (a straight line in the bar's two amounts) carries the change from frame to frame. The picture's own edges
  only correct it, slowly: what the frames' own readings say beyond the bar, averaged over neighbouring frames (weight
  exp(-|frames apart| / 3)), each frame weighed by its inverse variance (spread among its edges; a frame with few
  edges leans on what its step height predicts). No line-count rule. Two simpler weighings were tried first and
  dropped: per-frame inverse-variance mixing of own reading and bar let frames with 2-8 edges move the taps (their
  spread understates their error).
- **Known answer** (`direct.py kaw`; frames with 150+ edges are the truth, a third of them read again from a few of
  their edges, with a third of those edges wrong, or with none). Error, rms +2..+40, median: 6 edges alone 0.0114,
  12 alone 0.0090, 22 alone 0.0064, 22 with a third wrong 0.0140, bar alone 0.0125; `readw` 0.0058-0.0059 in every
  case, with no edges of its own included. Taps from one frame to the next over the whole stretch (lags 1-29),
  median / 99th / largest: old reading 0.031 / 0.306 / 0.920, `readw` 0.023 / 0.088 / 0.128. Time constants 3 to 50
  frames all pass; 3 has the lowest error, on test frames whose neighbours are well read.
- **Each frame on its own echo.** With `readw` and no mean, still picture from frame to frame is 0.94 / 0.99 (deep
  frames / others) against 0.91 / 0.97 captured; the old reading without the mean gave 1.16 / 1.11. With a five-frame
  mean on top it is 0.88 / 0.91. The clip sent uses no mean (`STEADY=1`). Left edges unchanged; added where the
  capture is flat 0.340 rms, 5.1 at 1 in 1000.
- **More removal is not there** (`gate.py more`, the new reading, no mean). Ghost left on black beside the right
  border, median / largest over 16.7-18.9 s, then wall ripple median / largest and still-card change: captured 0.71 /
  0.93, 1.74 / 1.94, 1.03. Gain 3 hole 0.25: 0.44 / 0.56, 1.78 / 2.22, 1.05. Gain 5: 0.40 / 0.56, 1.86 / 3.01, 1.18.
  Gain 7: 0.39 / 0.56, 1.90 / 3.98, 1.28. Gain 3 hole 0.15: 0.38 / 0.46, 2.11 / 2.83, 1.09. So at this echo strength
  about 0.6 of a strong edge's ghost stays whatever is done; that is what "ringing" at 18 s still is.
- **Line timing there.** The picture's right border moves by about 2 samples and its line-to-line jitter doubles
  (0.7-0.96 samples against 0.3-0.5) at 16.7-17.6 s, while the echo strengthens (captured ghost 0.45 -> 0.9 by 18.6
  s). The removal works along each line and does not depend on where the line sits; the five-line cleaning does mix
  neighbouring lines.
- Judged by the owner: pending.

### Back to one reflection from the test bar, at full strength (`onerefl.py`, 2026-11-26)

Owner on the clip with the bar-led reading and the wide hole: "worse. with everything. it barely fixes any of the
ghosting on the clip and it still has artifacts"; why picture edges and the rest at all: "find the ghost, subtract out
its phase"; "I don't understand why we are weakening the fixes"; and, on hearing that the two paths are about equal in
strength at 14-20 s: "isn't it best to do nothing?"

- **The model:** one reflection per frame, three numbers (strength, phase, delay) from that frame's test bar (the fit
  of "Reading the echo from the test line", below 1.6 MHz), removed with the division limit 0.01, three passes, gated,
  thin features kept. No picture edges, no leftover hole.
- **On an edge nothing was fitted to** (the picture's right border, a falling edge onto black; `gate.py border_ghost`),
  ghost left as a share of the border's step, near (+1..+9) / far (+11..+44), median over frames, by the reflection's
  strength from the bar:

  | strength | captured | one reflection, full strength | bar-led picture reading, full strength | the same, wide hole (the clip judged worse) |
  |---|---|---|---|---|
  | under 0.8 (48 frames) | 0.18 / 0.06 | 0.09 / 0.08 | 0.18 / 0.15 | 0.18 / 0.12 |
  | 0.8-0.9 (53) | 0.66 / 0.24 | 0.19 / 0.17 | 0.22 / 0.25 | 0.37 / 0.22 |
  | 0.9 and over (36) | 0.74 / 0.26 | 0.22 / 0.15 | 0.29 / 0.21 | 0.49 / 0.24 |

  The one-reflection model is the best of the three at every strength, near and far. The picture-edge readings were
  fitted to the rising left edges and passed their own tests by construction; on this edge they leave the near ghost
  untouched at low strength and add far ripple. The earlier rejection of the one-reflection kernel ("far ripple 2-5
  times `direct.py`") was scored on those left edges.
- **By strength** (`onerefl.py bystrength`): added where the capture is flat, codes rms, 0.09 / 0.12 / 0.23 / 0.47 /
  0.80 at strength 0.6-0.7 / 0.7-0.8 / 0.8-0.9 / 0.9-1.0 / over 1.0 at 62 minutes (40% of the stretch is under 0.8,
  40% at 0.8-0.9, 20% above); 0.06-0.11 in the first passage (strength 0.5-0.9). At 0.96 the wall after the left
  border carries 7.2 codes rms of ripple (captured 1.7). The bar puts the reflection ABOVE the direct signal at
  18.7-19.4 s (1.03-1.12).
- **Fade** (`onerefl.py`, `FADE0`): full removal while the strength is under 0.8, none from 1.0 on, linear between.
  The 0.8 is read off the table above, not measured as an edge of anything.
- **Owner on four stills at full strength:** "except the edge ringing is back". Measured at strength 0.76 beside the
  right border: the main bump (0.41 at +5) is gone; left are 0.13 at +17 and 0.07 at +39. The capture has 0.12-0.08
  at +13..+17 and 0.05 at +39 already: the echo's longer part (noted after the first clip: the bar sits 0.02-0.04
  high from +20 to +50), which one reflection does not contain, and which reads as a separate ghost once the main one
  is gone. The fit leaves 2.2% of the bar where 89 free taps leave 1.4%.
- A three-row clip of the 62-minute stretch (captured / full strength / faded) was sent. Judged by the owner: pending.

### The line-19 sweep: a purpose-built reference, direct division, and a chain that is not linear (`gcr.py`, `bartest.py`, 2026-11-26)

Owner on the three-row clip: the full-strength row has the best cancellation and the ringing; the faded row "barely
cancels the ghost". "Why is there any fitting going on at all? ... a wave phase cancellation, right?"; the blanking
signal must match the picture; "think about this problem from a physics standpoint".

- **The bar test** (`bartest.py`): the removal applied to each frame's own test bar, whose shape is known. With the
  three numbers fitted to predict the captured bar, the removed bar still carries +-2.5% of the bar at +20..+34 and
  0.03-0.05 rms over the rise, at every strength. Fitted instead so that the REMOVED bar is clean: 0.0215 -> 0.0173
  (noise 0.009-0.011), with the numbers moving the same way in every frame (phase -12 degrees, delay -0.8 samples). A
  second, longer path sharing a ratio and a delay: 0.0186 -> 0.0173 on held-out frames; the pass line was 0.012. Not a
  second reflection.
- **Line 19 / 282 carry the broadcast's ghost-cancelling reference**: a sweep to about 4 MHz on a 30 IRE pedestal,
  inverted about the pedestal in fields 2, 4, 5 and 7 of eight (rows 5 and 13 of the VBI arrays; polarity seen
  flipping every two frames). Never used before today.
- **Direct division** (`gcr.py`): the frame's sweep over the weak-state sweep, no model. Three faults of my own on
  the way, each caught by a check: polarity set per passage (the reference upside-down), a tapering window across
  the sweep (weighs the delayed echo differently from the direct signal), a low band limit and a tight lag limit.
  Known answer after those: a made-up echo put on the reference sweep and bar, recovered from the sweep, removed from
  the bar: rise 0.0030 where the true echo leaves 0.0024.
- **On the real lines the sweep's echo does not clean the bar.** Frames pooled by strength (noise negligible), rise
  of the bar captured -> after: 0.139 -> 0.075, 0.160 -> 0.074, 0.191 -> 0.079 at 62 minutes; 0.099 -> 0.059,
  0.141 -> 0.062, 0.192 -> 0.092 in the first passage (the three-number fit to the bar: 0.03-0.06). The 2T pulse
  comes out somewhat better with the sweep's echo than with the fit (0.056-0.11 against 0.08-0.15).
- **Why: what arrives is not a linear function of what was sent.** For a linear chain the part of line 19 that does
  not flip with the sweep's polarity is zero. Measured: 20-28% of the flipping part in rms (peak +26 to +44 codes
  against +-100), already 25% in the weakest-echo passage. The capture's floor cuts off the sweep's swings below
  blanking, but that touches 5% of the samples and reading around it changes nothing. The reflection is linear at RF;
  the receiver's detector and the record and playback processing after it are not, and a small fast signal (the
  sweep) and a large edge (the bar, picture edges) come through differently. Which stage: not identified.
- So the bar stays the reference for large edges, and what the three numbers leave on it (3-4% of the bar) is what
  comes back as ringing, multiplied where the two paths cancel.

### The detector is linear; back to the picture-read removal with two targeted changes (2026-11-26)

Owner: "Yes, model at RF"; then, on stills of the three-number model beside the sweep's echo: "there is still ringing
in the middle and right pictures ... somehow you were able to remove the ringing almost entirely at one point in this
process. and if its linear, then I really feel like you are hunting around at the wrong thing."

- **The receiver's detector behaved linearly** (two tests with no free parameter). (1) Standard NTSC transmission
  through an envelope detector makes the sweep's non-flipping part DARKER (about 3 IRE rms); measured, it is brighter.
  About half of it is this capture cutting off the sweep's swings below blanking (predicted and measured peaks agree
  within a code: 36.3 against 36.3, 35.1 against 35.7); the rest, about 12% of the sweep, also has the wrong sign for
  a detector. (2) An envelope detector with negative modulation makes the ghost after a falling edge about 0.04 of the
  ghost after a rising edge; measured on the same frames, 0.89-0.91. The statement in the section above that the
  floor cut-off does not matter was wrong.
- **The sweep's echo on the picture** (`gcr.py remove`): stills sent; a clip was rendered and NOT sent: the wall at
  14-15 s rings at 3.6-6.7 codes rms (captured 1.7-1.9) and still picture changes 1.26 against 0.93.
- **Removing the weak state's own reflection as well** (the bar fit's 0.40 at -144 degrees, no new numbers): tested
  as the reason for what is left; false. Near the right border 0.09 -> 0.06 at low strength, far unchanged, and
  0.19 -> 0.44 at strength 0.8-0.9.
- **The right-border measure cannot rank kernels.** It sits on black, where the capture cuts off below blanking: a
  ripple shows only its bright half there, before and after removal. The claim above that the one-reflection model
  "is the best of the three" on an unfitted edge rests on it and is withdrawn.
- **The clean measure: after RISING picture edges** (steady left edges, odd rows; the picture stays above black).
  Ripple +22..+92 of the pooled edge, share of the step, by the reflection's strength (under 0.8 / 0.8-0.9 / 0.9 and
  over): captured 0.035 / 0.033 / 0.032; picture-read taps from even rows (the removal of clips 4-7) 0.038 / 0.040 /
  0.051; three numbers 0.089 / 0.150 / 0.153; line-19 sweep 0.035 / 0.126 / 0.166. On the wall at strength 0.96 and
  the still card (limit 0.01): picture-read 2.2 and 1.21; three numbers 7.2 and 1.23; sweep 4.9 and 2.03.
  The picture-read removal, the one the owner judged good, does not ring at any strength; it was read from rising
  left edges, so this is not an independent test of it, but it is what the picture shows.
- **Its two faults, fixed one each** (`gate.py`: `MEDIAN=1`, `remove ... PAR.npy FADE0`). The reading that jumped at
  18.4 s: the taps are the median of the frame's and its two neighbours' either side instead of their mean (tap at
  lag 1 at frames 548-552: -0.07 throughout; the mean gave +0.07). The moving bands where the two paths are nearly
  equal: full-strength removal adds to the still card's frame-to-frame change by nothing under strength 0.8, 6-13% at
  0.8-0.85, 15-24% from 0.85 to 1.0 (no sharp edge); the owner's bands sat at 0.92-0.97; the removal is faded from
  full at 0.9 to none at 1.0 (the owner: where they are equal, "isn't it best to do nothing?").
- **The stretch rendered that way** (picture-read taps, median of 5, limit 0.01, three passes, gated, thin features
  kept, no leftover hole, faded 0.9 -> 1.0): full strength in 80% of the frames, none in 4%. Wall at 14-15 s 1.7-2.5
  (captured 1.6-1.9; 4.5 in the fifth clip). Still card 1.03 against 0.93 (0.97 against 0.84 at 11.5-14.5 s, 0.83
  against 0.75 at 17.9-18.6 s). Rising edges: the dip at +6 / +8 from 0.35 / 0.59 to 0.82 / 0.74 under 0.8, from
  0.23 / 0.47 to 0.84 / 0.73 at 0.8-0.9, to 0.66 / 0.64 at 0.9-0.95 and 0.42 / 0.53 above; ripple 0.037-0.043.
  Judged by the owner: "nope. this has the same problems as the version you said I liked. those intermittent vertical
  bars in flat areas, the picture frame issue, and just general ringing".
- **Where that leaves it.** Four ways of knowing the echo (picture edges, three numbers from the bar, the line-19
  sweep, the bar leading with the picture correcting) and every full-strength removal shows bars or ringing to the
  owner; the one version without them (the wide leftover hole, the sixth clip: "Bands gone", "mostly fine, definitely
  more watchable") leaves much of the ghost where the echo is strong. The measures here passed renders the owner then
  rejected: pooled medians over edges and frames average out a ripple whose phase changes from frame to frame, which
  is exactly what the bars are. Only the still card's frame-to-frame change sees it, and it rises with the
  reflection's strength for every kernel. The picture-frame scene (17.9-18.6 s) has the strength swinging between
  0.92 and 1.03, so any removal whose amount depends on the strength changes visibly there while the capture's own
  ghost only grows steadily.

### The sixth clip's removal, with nothing done around the moment the two paths trade places (2026-11-26)

The owner, shown the sixth clip again: "mostly fine except that yes during the strongest moments you introduce those
weird artifacts. the shifting around the picture frame, and those horizontal lines ... in the 'unforgivable' lettering
as its zooming in"; the shifting "looks like the primary signal trading with the ghost"; get rid of those two "then I
think we are good".

- **One event.** The bar puts the reflection at or above the direct signal in exactly one run of this stretch, frames
  556-592 (18.6-19.8 s). The capture's own line-to-line jitter at the left border rises there (0.25-0.5 samples
  before, 0.56 at 19.4 s, 1.3 at 19.7 s). The picture-frame scene (17.9-18.6 s) is just before it, the title zoom
  (18.9-20.7 s) during and after.
- **In the sixth clip's frames there.** The removal moves the picture's right border by -0.5 samples before the cut
  into the picture-frame scene and +0.2 to +0.5 after it, changing by up to 0.25 from one frame to the next inside the
  scene, while what is left of the border's ghost goes 0.51 / 0.59 / 0.61 / 0.56. In the title zoom the captured rows
  sit several samples apart sideways and carry dashed lines; the five-line cleaning and the echo prediction act on
  that row by row.
- **The rule** (`gate.py trade_weight`, `remove ... PAR.npy trade`): no removal from 30 frames before to 30 frames
  after any frame where the bar's strength is 1.0 or more; ramped back to the usual removal over the next 24 frames.
  Everything else exactly the sixth clip's setting (picture-read taps, mean of 5 frames, leftover hole 0.25 MHz, gain
  3, gated; no thin-feature change, no median).
- **Verified on the rendered frames:** frames 526-622 (17.55-20.75 s) identical to the capture; frames outside the
  ramps identical to the sixth clip's removal (checked at 3.3, 10.0, 14.3, 16.0, 23.4, 28.4 s); ramps 502-525 and
  623-646.
- **Owner on that clip:** "pretty decent", but on the last title card "the ghost stairsteps ... there should be no non
  smooth gradients of change ... after you turn your filters back on, the ghost of the lettering moves all over the
  place and it does it in steps"; and: "nothing should be using anything other than a smooth weighting. real RF
  doesn't jump"; and check that none of the other defects came back.
- **Cause.** The sixth clip's reading is each frame's own left picture edges (the bar's fit where a frame has under 20
  such lines), then a flat mean of 5 frames. On the title card the reading follows the lettering's own edges as they
  move (tap at lag 1 from -0.22 to -0.04 and back to -0.17 within two seconds) while the bar's strength eases from
  0.79 to 0.73; the flat window and the switch between sources turn that into steps (largest change of the taps from
  one frame to the next 0.19).
- **Every step in time made smooth** (the rule: no flat window, no switch, no corner).
  `direct.py readw` (`combine`): the bar's fit carries the change from frame to frame, its amounts weighted along time
  with a Gaussian of 5 frames; the picture's edges correct it with a Gaussian of 45 frames, each frame by its inverse
  variance; no line-count switch. Known answer (`kaw`): error 0.0078-0.0080 against the frames with 150+ edges (bar
  alone 0.012, 22 edges alone 0.0064), taps from one frame to the next 0.003 median, 0.013 largest. `gate.py`: no
  mean of taps on top (`STEADY=1`); the gate's floor weighted along time (`GATESMOOTH=5`: its change from frame to
  frame 0.014 median and 0.40 largest as read, 0.003 and 0.075 weighted); the ramp around the trade eased at both
  ends (largest change of the amount applied in one frame 0.065). The decision that a trade is happening (bar
  strength 1.0 or more, from a fit that pools the bar's lines of 5 frames) is still a yes or no; what it switches
  is ramped.
- **Regression check** (`regress.py`: capture / the sixth clip's removal / this render; frames with the removal on).
  393 kHz in bright flat stretches 1.02 / 1.06 / 1.07 codes. Added where the capture is flat 0.335 -> 0.280 rms,
  4.8 -> 3.9 at 1 in 1000. Mean level of a frame moved by 0.15 -> 0.10 codes. Wall at 14-15 s 1.7 | 1.9 captured,
  1.8 | 2.0, 1.8 | 1.9. Still caption card from frame to frame 0.93 / 0.92 / 0.91, on the last title card 0.77 / 0.79
  / 0.77. Title lettering rows (what is the same down the rows) from frame to frame on the last card 1.04 / 1.36 /
  1.17. Rising edges, level at +6 / +8, at +40 / +60, ripple, by strength: under 0.7 0.77/0.70 1.00/1.01 0.038 ->
  0.77/0.71 1.00/1.01 0.039; 0.7-0.8 0.74/0.68 0.042 -> 0.76/0.69 0.039; 0.8-0.9 0.64/0.59 0.034 -> 0.64/0.58 0.034;
  0.9-1.0 0.59/0.54 0.050 -> 0.57/0.53 0.048 (captured 0.20-0.35/0.43-0.60, 0.032-0.038). Identical to the capture
  in frames 525-623. Echo taps from one frame to the next 0.0087 median, 0.191 largest -> 0.0026, 0.013.
  Nothing came out worse than the sixth clip's removal.
- **Owner on that clip:** "It's smooth. The only problem remaining is the ghost fades over time way too late on the
  card now. It's like it's being seen as correctable too late and that's not carrying back to prior frames."
- **Measured after the trade:** the bar's strength is 0.97 at 19.8 s, 0.91 at 20.0, 0.83 at 20.2, 0.79 at 20.4 and
  settles at 0.78; the capture's line-to-line jitter inside a field (each row against the row above, 0.3-0.5 samples
  normally) is 0.6-0.8 from 19.2 to 20.1 s and normal from 20.2 s; the title stops moving at about 20.4 s. The fixed
  second after the trade kept the removal off until 20.8 s and fully back only at 21.5 s.
- **The return follows the signal** (`gate.py trade_weight`): after a trade the removal comes back by how far the
  strength (weighted along time, Gaussian of 2 frames) has come down from 1.0 toward the level it settles at (the
  median over the second and a half that starts a second after the trade), eased at both ends; once back it stays
  back. Before a trade the strength gives no warning (a plateau at 0.92-0.93), so that side stays eased out by time,
  54 to 30 frames ahead. Amount applied: 0.03 at 19.8 s, 0.36 at 20.0, 0.84 at 20.2, 0.99 at 20.4; largest change in
  one frame 0.09. Title lettering during the return (frames 598-616, captured / removed / difference): the correction
  follows the letter stems; no row-wise lines in the difference.
- **Regression check on that render:** as above line for line (393 kHz 1.03 / 1.06 / 1.07; added on flat 0.330 ->
  0.274; wall 1.8 | 1.9; still card 0.91 and 0.77; title rows 1.04 / 1.36 / 1.17; rising edges unchanged; taps 0.0026
  median, 0.013 largest); identical to the capture in frames 525-592. Judged by the owner: "Yes, we're good."
  (This is the luma setting for this stretch; nothing is built into the pipeline. Next asked: chroma.)

### Colour on the 62-minute stretch: nothing to remove (`chroma_check.py`, 2026-11-26)

Asked by the owner once the luma setting was accepted. The stretch's colour (kept at the one read) against the echo's
strength from the bar, 0.6 to 1.1.

- **Steady colour does not follow the echo.** The blue glow of the layout keeps its hue: -34.5 / -36.3 / -35.1 / -34.1
  degrees at strength 0.7-0.8 / 0.8-0.9 / 0.9-1.0 / over 1.0. It sweeps, so its size is compared at the peaks of the
  sweep: 52.7 at strength 0.82, 52.2 at 1.00, 54.7 at 0.73. (The receiver sets colour against the burst, which the
  same reflection reaches.)
- **No ghost on colour edges.** The picture box's borders as colour edges, along the row's own colour direction: the
  rise and the fall are smooth at every strength, with no dip and no second step. At strength 0.95 and over there is
  an overshoot of 5-6% after the rising border and an undershoot of 3-7% after the falling one; the largest turn of
  hue at an edge is 0.13-0.19 of the colour's size at every strength.
- **Place against luma.** Within scenes (so a change of scene does not count), per 0.1 of strength the right border as
  a colour edge moves -1.9 +- 0.4 luma samples against the same border in luma (the luma edge itself -0.2 +- 0.1).
  The strength moves by about 0.1 inside a scene, the colour edge is 15-28 luma samples wide, and the picture also
  moves inside a scene, so this is small and not separated from content. The luma removal moves luma edges by under
  half a sample.
- **Not looked at here:** the first passage (its colour is not on disk; 8 frames earlier showed no dip); the stretch
  around the trade, where nothing is done to luma either; whether saturated colour lowers the luma level under strong
  echo in the picture as it does on the staircase (still open, a luma question); cross-colour on the caption lettering
  (in the capture at every strength, not from the echo).
- So: nothing is proposed for colour on this stretch.

### The accepted removal over a whole capture, as a one-off render (`full_*.py`, 2026-11-27)

The owner asked for one full encode of the capture with the accepted luma removal, made by the dashboard's renderer
with the removal as its picture filter, outside the tool, replacing the capture's existing render. Nothing was built
into the pipeline. It takes two reads of the capture:

1. **Measure** (`full_measure.py`): the capture is read once as a stream and, per whole picture unit, the test-signal
   rows, the picture's left-edge reading (`direct.gather`'s, same lines) and the CRC of one picture line are kept.
   The frameserver cannot do this pass: its first published line is 19 at the lowest and the test bar is line 18.
2. **Table** (`full_table.py`): one row per unit, made with the accepted setting's own functions (`wide.rises` and
   `amounts_of`, `reflect.fit_frames`, `direct.combine`, `gate.trade_weight`): the taps and the share of the removal
   to apply. Added for a whole capture: where no test bar is found for a while nothing is removed (a weight from the
   share of nearby frames with a bar, Gaussian in time; a lone frame without a bar changes nothing).
3. **Render** (`full_filter.py` as the plain render's `PLAIN_RENDER_FILTER`): each 720x480 frame's row is found by
   the CRC, searched forward; `gate.remove_hole` runs on the whole frame (240 lines a field), the gate floor is
   measured on the lines the accepted setting measured it on and weighted along time as `gate.py remove` does (the
   filter reads 21 frames ahead); colour is untouched; a frame whose weight is 0 leaves byte for byte. Frames not
   found in the table in numbers fail the render, and the render it would replace stays.

Checks before the capture was touched, on the approved stretch: the table built in pieces by four processes equals
the approved one (amounts and taps identical, the three numbers within 3e-8, weights within 4e-11); the filter's
output is byte-identical to the same steps run in one process on the same frames (0 of 311 million samples); a
full-height frame gives the crop's correction exactly once the five-line cleaner's noise figure is taken from the
same lines (with the test's repeated lines above and below the crop it is not, and 9% of samples differ: the test
input's doing). A dry run through the plain render script on a local test capture found all 915 units' rows; its 13
partly shown units took the row after the last one found.

The measuring pass: 107,670 whole units (59.9 min), every byte proven by the checked reader; on the approved stretch
(rows 104,801-105,700, 58:17 into the capture: the "62-minute" stretch is at 58 minutes of picture) the test-signal
rows and the left-edge readings are identical to the experiment's arrays. 63,518 frames have 30 or more left edges,
19,700 none.

The table over the whole capture:

| | |
|---|---|
| reflection's strength | 5% 0.51, median 0.61, 95% 0.77, largest 1.25; by four-minute stretches the median is 0.56-0.63 until the last three minutes (0.70, 95% 1.05): the approved stretch is the capture's worst part |
| at strength 1.0 or more | 629 frames in 18 runs (14:19, 16:42, 24:09, 52:23, and from 56:43 on); two runs are one frame long (57:39, inside a longer stretch; 58:56, alone: the removal is off for 1.0 s around one frame read as 1.00) |
| nothing removed | 12 stretches, 36.3 s (1.0% of the capture), the longest 14.1 s at 57:31; in part: 20.3 s |
| no test bar | 52 frames; nothing removed for that reason in 18 frames (0.6 s) |
| picture left at the deepest point of the cancelled band | median 0.63 (approved stretch: 0.11-0.12) |
| taps, change from one frame to the next | median 0.0013, largest 0.026 |

The whole capture has one bar-to-picture fit where the approved stretch had its own. On the approved stretch the
whole-capture taps differ from the approved ones by 0.0039 rms (taps 0.043 rms), the strength by at most 0.006, the
weights not at all; the removed picture differs in 19% of samples, 1.1% by 4 codes or more, 0.85 codes rms. The
regression check (`regress.py`) on that stretch with the whole-capture taps, against the approved result:

| | captured | approved | whole-capture taps |
|---|---|---|---|
| 393 kHz in flat stretches, codes | 1.03 | 1.07 | 1.08 |
| added where the capture is flat, codes rms | - | 0.274 | 0.278 |
| wall after the left border, ripple: median, worst | 1.7, 1.9 | 1.8, 1.9 | 1.8, 2.0 |
| still caption card, change frame to frame | 0.93 | 0.91 | 0.91 |
| last title card; title lettering rows | 0.77; 1.04 | 0.77; 1.17 | 0.77; 1.17 |
| dip at +6 / +8, strength 0.8-0.9; 0.9-1.0 | 0.23/0.47; 0.20/0.43 | 0.64/0.58; 0.57/0.53 | 0.64/0.59; 0.59/0.54 |
| ripple +22..+92, strength 0.8-0.9; 0.9-1.0 | 0.034; 0.032 | 0.034; 0.048 | 0.036; 0.044 |
| frames identical to the capture around the trade | - | 525-592 | 525-592 |

Not judged by anyone before the render: everything outside the approved 30 seconds; the first and last lines of
each field (the clips showed lines 34-253 / 297-516; the head-switch lines at the bottom get the removal too).

**The render (2026-11-27, 62 minutes, the filter at 29 frames a second with four processes).** The plain render's own
checks passed and the capture's render was replaced: 215,370 frames at 59.94 a second (3,593.09 s), audio unbroken,
every byte of the capture proven by the checked reader. The filter took 107,677 frames in and out, found all 107,670
table rows (7 frames were in no row: the repair put back 6 units the Shuttle sent at the wrong length), worked on
106,588, changed 106,559, and passed 1,089 byte for byte, which is the table's count of frames with nothing removed.
Read back from the encoded file: one second inside the approved stretch (30 units, both fields, the lines yadif
passes untouched) is within 0.70-0.73 codes rms of the removed picture, which is the encoder's loss, and 8-12 codes
rms from the captured picture; regressing (render - captured) on (removed - captured) gives 0.999-1.000 on every frame.
That read-back shows the removal reached the encoded picture; it says nothing about how it looks outside the approved
30 seconds.

### After the first watch: one wrong stretch, its cause, and two fixes (2026-11-27)

The owner on the first two minutes: "a lot better than the raw. much more crisp", no strange artifacts; then "between
3:23 and 3:28 it gets really bad and then it fades out by 3:30".

**Cause, from the table and the picture.** From 3:22 to 3:28 the taps are the largest of the capture (largest tap
0.73; median 0.15, bar alone 0.06 there). The frames have two or three left edges each, all on one object whose edge
is not a clean step (captured, its level 6 and 8 samples after the edge is 1.58 / 1.41 of the step, where a step with
the echo reads about 0.45 / 0.70). Their reading departs from the bar's by 0.85 rms (usual: 0.04 with 120 or more
edges, 0.15 with two), yet its claimed error was 0.09, and `direct.combine` counted each of the 150 frames as a fresh
reading, so the slow correction followed them. The removal then changed the picture by 7.5-9.8 codes rms there (1.8-4.8
in the scenes before and after) and forced those edges to the reference shape (0.91 / 0.94).

**What is wrong in the weighting, measured.** A frame's departure from the bar is still there in the next frame: as an
rms over lags 2..40, 0.21 with 2-3 edges, 0.12 with 4-9, 0.10 with 10-29, 0.074 with 30-59, 0.057 with 60-119, 0.052
with 120 or more; for 2-3 edges it is unchanged 90 frames on. What a frame of any class shares with a frame of 120 or
more edges some frames later is 0.03-0.06: that is the echo's own departure from the bar, about 0.05 for every class.
The rest is tied to the edges themselves and repeats while the scene holds; with 30-59 edges it is as large as the
correction being measured.

**The capture-wide accounting (`direct.combine(shared=True)`, `shared_error`; `full_table.py` with `FIX=shared`;
shown to the owner as clip 15, not rendered).** The repeating part is measured from the capture by edge count (product of successive frames' departures
minus the echo's own share; joined by straight lines in log(edges)) and kept out of the averaging over time: however
many frames repeat a reading, the correction is trusted no further than one such reading deserves. The time weighting
is unchanged (Gaussian, `WSLOW`), nothing is switched. Known answer (`shared_ka.py`): few-edge scenes ten seconds
long, each repeating one wrong shape: error of the reading against the truth inside the tested scene 0.413 before,
0.003 after (bar alone 0.020); honest few-edge scenes (noise only) 0.005 both; far from any few-edge scene 0.0017 both.

On the capture: largest tap at 3:22-3:28 0.73 -> 0.06-0.09; change made to the picture there 7.5-9.8 -> 1.1-1.2 codes
rms. Over the whole capture the picture's correction keeps a median weight of 0.66 (was 1.00); the largest tap changes
by more than 0.02 in 42% of frames, by more than 0.10 in 33 stretches (all with 16 or fewer edges a frame but 51:03; the longest
22:19-22:29, 38:35-38:44, 12:18-12:27, 16:33-16:41, 3:22-3:29, 49:59-50:07). **What it costs:** in scenes of 20-40 edges
the removal follows the picture's edges less: at 3:13-3:20 the level 6 samples after rising left edges is 0.45
captured, 0.83 as rendered, 0.72 with the fix (overshoot 1.15 / 1.25 / 1.21). That measure is taken on the edges the
reading came from, so the rendered 0.83 is partly the taps fitted to those edges' own shape. On the approved stretch
the taps change by 0.0020 rms (taps 0.043), the picture differs from the approved one by 1.14 codes rms (0.85 for the
table as rendered), and `regress.py` reads the approved numbers within a few hundredths (393 kHz 1.07, added on flat
0.225, wall ripple 1.8 / 1.9, cards 0.91 / 0.77, title rows 1.21 against 1.17, dip 0.77/0.71 ... 0.59/0.54, same 68
untouched frames at the trade, taps' largest step 0.012).

**The narrow fix, which is what the re-render uses (`direct.combine(outlier=True)`; `full_table.py`'s default,
`FIX=outlier`).** The owner, on being asked to re-render: "can you also do a regression check when you re-render... if
any other part of the capture changes more than a few codes, present it to me before replacing the render". The
capture-wide accounting fails that by its nature: on the ordinary scene at 3:13-3:21 it moves 1 sample in 1000 by 13
codes or more against the render the owner watched (rms 1.5, 3.9% of samples by more than 3), and the taps move by more
than 0.02 in 42% of frames. The narrow fix leaves every reading alone but the ones no reliable frame resembles: over the
whole capture a frame with 120 or more edges never departs from the bar by more than 0.33 (rms, lags 2..40; 99.9% under
0.26); a reading beyond that counts less (cosine), and not at all from twice it. 405 readings count in part, 114 not at
all, of 84,894. Known answer (`shared_ka.py`): 0.413 -> 0.010 inside the tested scene, honest few-edge scenes
unchanged, far from any few-edge scene the old numbers exactly. On the capture the taps change by more than 0.02 with
the removal on in four stretches: 3:21.9-3:30.4 (up to 0.76: largest tap 0.73 -> 0.18), 9:19-9:24 (0.06), 32:47-32:52
(0.08), 34:43-34:46 (0.06); on the approved stretch by at most 0.0010. On 3:13-3:38 the picture is the rendered one
outside 3:22-3:30 (rms 0.01-0.13 codes apart) and inside it the change made to the picture falls from 7.5-9.8 to 1.8-2.5
codes rms (1.1-1.2 with the capture-wide accounting: the narrow fix keeps the correction the scene before it supports).
`full_table.py` got `REUSE=TABLE` (the bar amounts and three numbers, which no fix changes, taken from an existing
table; `FIX=none REUSE=T` reproduces `T` exactly, every field).

**The re-render's regression check (`full_filter.py TABLE F1,F2 PROCS OLD_TABLE REPORT LIMIT SKIP_A:SKIP_B`).** The
filter works every frame out with both tables, exactly as the first render's filter did with the old one, writes what
the new luma differs from the old by per frame, and ends with status 7 after the last frame if any frame outside the
skipped rows (3:21.5-3:30.9 here) has 1 sample in 1000 changed by more than LIMIT (3 codes): the plain render then
fails before its last step, keeps the finished render under its working name and leaves the existing render in place;
`finish.py` publishes it later. Tested before the capture was touched: output byte-identical to the previous filter;
the report equal, frame by frame, to an independent comparison of two single-table outputs; status 7 with changed
tables, 0 with every row skipped, 0 with the same table twice; and through `plain_render.sh` on a 2.6 s slice with a
pass-through filter ending in status 7: existing output untouched, the finished render kept, then published by
`finish.py`.

**Colour (the owner: "the whole color profile looks oversaturated. could that happen from a misread of the burst
signal?").** The burst itself is outside the captured window. Measured instead (`colour_ref.py`):
- The render's colour samples are the capture's (one decoded second: slope 0.98-1.00, mean colour size 14.52 against
  14.53); the removal and the encode change no colour.
- Lines 14-20 and 277-282 arrive without colour. Line 283 carries the station's composite test signal with colour: a
  white bar, a staircase with a subcarrier of fixed size at burst phase, a 12.5T pulse. At 21 points through the hour
  (12 frames each; two more points carry no test signal) and frame by frame on two stretches, the staircase's colour
  is 32-36 codes in size at most points (41-45 at a few) and mostly within 0..+14 degrees of burst phase; it does not follow the echo's
  strength (correlation -0.05 over the points, -0.04 and -0.17 within the stretches). With the Rec.601 conversion and
  the bar as 100 IRE it is 14-15 IRE peak where the standard is 20: 40-88% of standard, median 69%. By that reference
  the colour is weaker than standard, not stronger. The Shuttle's colour scale has not been checked against a
  generator here, so the percentage may be off by one fixed factor; the steadiness does not depend on it.
- The white bar is not steady: 192 to 248 codes above blanking from point to point. Colour held, brightness moving:
  the colour-to-brightness ratio moves by about 13% either way through the hour.
- In the dark scenes at 3:25, 16-22% of samples decode to a colour channel below zero (luma median 47-54 codes).

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
| `direct.py` | each frame's echo read from its own left picture edges; `readw`: the reading led by the test bar with the picture's edges as a slow correction, and its known answer (`kaw`); scores, removal |
| `stair.py` | the echo after each staircase riser, by level: is it the same at every level |
| `diag.py` | what the removal does to line-to-line content by frequency (the diagonal bands) |
| `tones.py` | steady interfering tones in a captured stretch: frequency, step per line, step per frame |
| `tones2d.py` | slanted bands in flat patches: two-dimensional spectrum, also sees tones that hardly change from line to line |
| `tonesmall.py`, `tonediff.py` | the 393 kHz question in busy picture: many small flat patches; differences of consecutive frames |
| `rfmodel.py`, `rf_sim.py` | the echo modelled at RF through the off-air simulator; arithmetic checks, the chain's own answer on level and colour (`level`), known-answer recovery, fit to the test line, residual panel, picture-edge test |
| `barread.py` | the echo read from the test line's plain-luma parts with free taps on both sides of the edge; references, known answer, picture scores (same edge at two strengths, what moves together across rows) |
| `reflect.py`, `reflect_score.py` | one reflection at RF relative to the weakest state: fit to the pooled test lines; three numbers per frame and the picture scores |
| `reflect_cal.py`, `scene_ref.py` | the test line's per-frame state calibrated to the picture on held-out tracks; a reference edge made for the passage, judged on the test bar |
| `gate.py` | the removal applied only where its correction stands clear of the frame's own floor; the taper toward the carrier; the wide leftover hole; thin features kept in the echo prediction; known answers (also with the reading's error and a drifting echo), left-edge scores, still-picture change from frame to frame, what is added on flat picture, a gated stretch |
| `thin_ka.py` | known answer for keeping thin features in the echo prediction: error where the median cleaning cannot predict the echo, elsewhere, and after made-up dropout streaks |
| `onerefl.py` | the owner's model: one reflection per frame from the test bar, removed at full strength, with the fade near equal strength; three-row clip frames; results by strength |
| `bartest.py` | the removal applied to each frame's own test bar: what is left on a shape that is known |
| `gcr.py` | the line-19 ghost-cancelling sweep: per-frame echo by direct division, its known answer, and the bar test with it |
| `shared_ka.py` | known answer for the repeating-error accounting in `direct.combine(shared=True)` |
| `colour_ref.py` | the station's colour test signal (line 283) at points through a capture: colour size and phase against the standard, against the echo |
| `full_measure.py`, `full_table.py`, `full_filter.py`, `full_review.py` | the accepted removal over a whole capture as a one-off render: measuring pass, table, the plain render's picture filter, and the table's review |
| `regress.py` | regression check of a rendered 62-minute stretch against the capture and a reference render: every defect fixed on the way |
| `tonecut.py` | taking the 393 kHz tone out by patch-wise fit and subtract; known answers; measuring its size |
| `tonesound.py` | the tone's frequency line by line against the captured sound |
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
| `chroma_check.py` | the 62-minute stretch's colour against the echo's strength: steady colour, colour edges, place against luma |
| `lin.py` | dip against step height and against position in the field; right-edge bump |
| `inpic.py` | isolated steps inside the picture, before and after removal |
| `shift.py` | the "left edge is a gate" idea, scored on right edge and in-picture steps (refuted) |
| `track.py`, `bar.py` | depth and place per field from the left edge and from the test bar |
| `falls.py`, `falls2.py` | rise and fall times and pooled responses of in-picture steps by size |
| `testline.py`, `split.py`, `checks.py`, `tl_remove.py`, `model.py`, `stretch_check.py`, `panel2.py`, `left_level.py`, `compare.py` | the straight-line split and what was built on it (see Withdrawn) |

## Open

- The residuals of the picture-read removal (`direct.py`), per the two reviews above: one reference edge imposed on
  every scene. (Frames filled from the bar: replaced by `readw`, the bar leading in every frame; owner's verdict
  pending.) The 393 kHz region multiplied by about 2 and the ripple far after strong
  edges are taken out by applying the correction only where a ghost is predicted (`gate.py`); the ripple train after
  strong edges where the echo cancels nearly everything, by leaving a wide hole there instead of a narrow one, at the
  price of less removal in those frames; the owner confirmed the bands gone. None needs the recording VCR.
- A reference for the picture-read kernel that is not one scene's edge: reading the kernel from the test line instead
  was tried and fails far after the edge (above). Open.
- The full-chain fit at RF (`rfmodel.py fit`) is parked: not established, and not needed for plain luma
  (`rfmodel.py level`). Whether saturated colour changes the luma echo in the picture as it does on the staircase is
  not measured.
- The reading from the picture (`direct.py`) is the only one that holds in both passages; the owner still sees bands.
  Its open points: frames without usable left edges (filled from the bar, unscored); the reference edge is one
  scene type's and is imposed on others beyond about +12; two passages only.
- The bar and picture edges: the size difference is mostly the reading's noise diluting the slopes; a one-sample
  shape difference is not explained.
- Colour: measured on the 62-minute stretch (`chroma_check.py`): no ghost, hue and size do not follow the echo; nothing proposed. The first passage's colour is not on disk.
- What is left after the left edge (above): tape's own edge or echo that is never absent.
- Narrow strokes: the 2T pulse is not improved at strong echo; fine lettering above a reading of 0.8 is not clean.
- Bands of 4-7 codes remain above a reading of 0.65.
- The zero of the second amount rests on the fast part averaging to nothing when the slow part is weak.
- The five-line cleaning threshold was chosen by hand; luma only.
