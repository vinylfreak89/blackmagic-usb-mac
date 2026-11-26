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
- Above about 2 MHz the test line's echo does not carry over at all (the ringing); consistent with small and large
  edges being sharpened differently (above).
- **So:** the test line gives the echo's form and a quiet per-frame state (three numbers), not the kernel. The
  picture-read kernel stays; what it lacks is still a reference that is not one scene's.

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
| `rfmodel.py`, `rf_sim.py` | the echo modelled at RF through the off-air simulator; arithmetic checks, the chain's own answer on level and colour (`level`), known-answer recovery, fit to the test line, residual panel, picture-edge test |
| `barread.py` | the echo read from the test line's plain-luma parts with free taps on both sides of the edge; references, known answer, picture scores (same edge at two strengths, what moves together across rows) |
| `reflect.py`, `reflect_score.py` | one reflection at RF relative to the weakest state: fit to the pooled test lines; three numbers per frame and the picture scores |
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
| `lin.py` | dip against step height and against position in the field; right-edge bump |
| `inpic.py` | isolated steps inside the picture, before and after removal |
| `shift.py` | the "left edge is a gate" idea, scored on right edge and in-picture steps (refuted) |
| `track.py`, `bar.py` | depth and place per field from the left edge and from the test bar |
| `falls.py`, `falls2.py` | rise and fall times and pooled responses of in-picture steps by size |
| `testline.py`, `split.py`, `checks.py`, `tl_remove.py`, `model.py`, `stretch_check.py`, `panel2.py`, `left_level.py`, `compare.py` | the straight-line split and what was built on it (see Withdrawn) |

## Open

- The residuals of the picture-read removal (`direct.py`), per the two reviews above: one reference edge imposed on
  every scene; the division limit and the reading's error where the echo nearly cancels 0.5 MHz (62 minutes, readings
  above 0.65); the 393 kHz region multiplied by about 2; frames filled from the bar. None needs the recording VCR.
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
- Colour: no measurement yet of whether it carries the echo beyond the 8 frames under "What it is".
- What is left after the left edge (above): tape's own edge or echo that is never absent.
- Narrow strokes: the 2T pulse is not improved at strong echo; fine lettering above a reading of 0.8 is not clean.
- Bands of 4-7 codes remain above a reading of 0.65.
- The zero of the second amount rests on the fast part averaging to nothing when the slow part is weak.
- The five-line cleaning threshold was chosen by hand; luma only.
