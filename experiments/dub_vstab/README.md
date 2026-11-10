# Vertical position of a noisy dub's fields (preliminary)

Investigation scripts for a 30 s capture of a damaged dub taken through the frame synchroniser. They read a cache made by
`extract.py` (every exact unit as a full 525-line UYVY raster, one read of the capture).

What the capture showed:

- The synchroniser never holds vertical lock. Every new field is a pass over 290 tape lines of which it keeps 262.5, and it
  repeats a field every 10-11 output fields. A repeat is the previous field again within the output chain's noise (row
  difference 1.2 codes against 30 for a new field), so repeats are found exactly (`look2.py`).
- Hence dead reckoning: new field j holds tape lines 290 j + row. Placed that way, features keep their vertical place from
  pass to pass (`fold1.py`, `place1.py`). No measurement of the picture is needed for this layer.
- The row profile of a single pair of fields is too weak to measure the shift (best lag within 3 rows of 27.5 in 16% of
  pairs, `shift1.py`); averaged over all pairs it peaks at 27.8 rows per pass (`shift2.py`).
- The signal is a floor at codes 6-7 (40% of samples) with pulses above it; whatever lies below the floor is not in the
  capture.
- In the dead-reckoned frame a thin line recurs every 525 tape lines and wanders by tens of rows over tens of fields. It
  is the candidate landmark for the tape's own vertical wander, not yet identified or tracked.

## Placing rows by the synchroniser's own behaviour (`passes.py`)

Inside a free run a row's tape line follows from counting passes (290 tape lines each). The read side is used only to
notice when the synchroniser restarted its write: every field's new/repeated pattern bounds when its pass started, the
bounds are carried forward, and an empty intersection is a break. The output field period is fitted per stretch in
units of a pass / 290 (262.12-262.20 on the capture). That number is the pass's length, not the tape's speed: a pass is
290.33-290.42 lines long, not 290 (see the timebase section), which is also why the roll measures 27.9 rows per pass.

- `test_passes.py`: a synchroniser simulated from its mechanism. Free runs (equal, longer, shorter and drifting line
  lengths) and a single restart come back exact. A stretch written in step with the read, or several restarts in a
  row, cannot be told from a free run by repeats alone until an expected repeat fails to come: the passes just before
  such a break can sit up to the size of the break off.
- On the capture: 1,644 passes, free for fields 0-796 and 1012-1811; 29 passes between fields 797 and 1011 placed by
  assumption (13 at a cut, 16 in step with the read).
- `render_placed.py`: one progressive frame per captured field, the tape's whole vertical cycle (525 frame lines), rows
  not delivered black, assumed placements marked by a white strip at the right edge.

```
python3 test_passes.py && python3 render_placed.py --selftest
python3 render_placed.py CACHE_DIR --log placed.csv | ffmpeg -f rawvideo -pix_fmt uyvy422 -video_size 720x526 \
    -framerate 60000/1001 -i - -c:v prores_videotoolbox -profile:v standard -aspect 640:525 OUT.mov
```

## The lean of the dark strokes and the vertical wander are one timebase error

The synchroniser never sees the tape's sync, so it writes on its own steady clock while the tape's line rate swings.
With rho = how much longer a written line is than a tape line, the tape's sync slides -858 rho samples per written row
(the lean of the dark strokes) and the tape's vertical landmark slides -290 rho rows per pass against pass counting.

- The dark slanted strokes (about 60 samples wide, pieces of 20-80 rows) lean as anything recorded on the tape must.
  `hband2.py` finds single strokes (known answer: 99% found, 1% false); a clean one is rare on the capture (6% of
  windows). They were first taken for the tape's sync pulses; they are not a line of sync running down the field
  (see "The sideways place" below).
- `fold525.py` + `vtrack.py`: the thin landmark that recurs every 525 lines, followed through the pass-counted fold
  (known answer: within 0.4 rows). Locked to it, the capture's rows show the tape's vertical structure: a dark band of
  about 20 lines after the landmark and again 262.5 lines later, the same in both free-running stretches.
- `timebase.py`: D(t), the landmark's fold position as a function of write time (local straight-line fits, 3 passes
  wide), and rho = -D'. A sample written at t sits at tape position t - D(t). `test_timebase.py` (known paths drawn
  into the capture's own scattered fold): D within 0.2 rows (95th pct 1.0), lean 858 rho within 0.2 samples per row
  (95th pct 0.7-1.2) against 1.2-2.4 uncorrected.
- `hband4.py`: the strokes' lean spectrum per field. Two artefacts of the first version are gone: the capture's own
  blanked edge columns (a false upright stroke) and tall noise where few rows are known. `hband4.py compare`: grouped
  by the landmark's prediction from -5.4 to +3.8 samples per row, the strokes' lean follows it throughout, offset by a
  constant +1.0 (+1.25 and +1.0 in the two free stretches).
- That constant is the pass's length. Write times count 290 lines per pass; a pass of 290 + d lines makes the landmark
  fall d rows per pass with no tape error at all, and the slope of D then overstates rho by d / 290 inside a pass.
  Three readings of d agree: the landmark's mean fall (0.36-0.38 rows per pass), the field period fitted from repeats
  alone (0.33-0.42) and the strokes (858 d / 290 = +1.0 to +1.25, d = 0.34-0.42). So the synchroniser's clocks and the
  tape agree on average (mean rho 0.00%), a pass is about 290.4 lines, and the earlier reading of the same numbers as
  a tape running 0.13% slow was wrong.
- What swings is the tape: rho between -0.50% and +0.53% (5th-95th pct), period 1.00 s (autocorrelation 0.84), steady
  over the clip.

## Drawing on the tape's raster (`render_locked.py`)

Each sample goes to tape position t - D(t) (+ the pass-length term, `--kappa` = d / 290 = b / 858): whole part = the
tape line, fraction x 858 = the column. Frame 858 x 526: the tape's whole line by its whole two-field cycle, the
landmark on line 4, the 138 samples per written line the capture does not carry left black (a slanted band, since
the written row runs across the tape's lines). Columns are resampled linearly; nothing is averaged across rows or
fields. `--no-skew` places whole rows only (720 wide).

- `test_locked.py`: a synthetic tape (a stroke at the start of every line, each line's brightness naming it, one bright
  line per 525) sampled on a swinging write clock in passes. With the true timebase every stroke and every line lands
  exactly (asserted; fails with the sign reversed or the skew left out). With the timebase estimated through the
  capture's own noise: lean left 0.16 samples per line (95th pct 0.7), landmark within 1 line in 95% of fields. With
  passes of 290.38 lines: +1.11 left without kappa, none with it (asserted).
- `lean_after.py`: on the capture drawn with kappa 0.001166 the strokes' lean sits at 0 in every group (centroids
  -0.8 to +0.5).
- Not pinned: the sideways place of a field. It needs D to a thousandth of a line and the landmark gives half a line,
  so fields stand upright but each at its own sideways offset (known answer: 50 samples median jump field to field,
  over 200 in 5%). Nothing in the capture pins it: next section.
- Not known: what the landmark is; the 215 fields where the synchroniser kept restarting (797-1011) are locked only as
  well as their assumed placement.

```
python3 test_timebase.py CACHE_DIR && python3 test_locked.py CACHE_DIR
python3 fold525.py CACHE_DIR && python3 vtrack.py CACHE_DIR            # after render_placed.py --log CACHE_DIR/placed.csv
python3 hband4.py CACHE_DIR run && python3 hband4.py CACHE_DIR compare
python3 render_locked.py CACHE_DIR --mono --kappa 0.001166 | ffmpeg -f rawvideo -pix_fmt uyvy422 -video_size 858x526 \
    -framerate 60000/1001 -i - -c:v prores_videotoolbox -profile:v standard -aspect 763:526 OUT.mov
```

## The sideways place of a field: not in this capture

Pinning a field sideways needs something at a fixed place on every tape line (sync tip, blanking, burst) or at least
structure shared between fields. Measured, each against a known answer made from the capture's own noise:

- `stroke_height.py`: darkness piled up along slanted lines over windows of 40 to 236 rows. A band the height of the
  field gains with the window (cut in at depth 0.2, i.e. one sample in five of it forced dark: z 2.8, 3.3, 3.7, 4.9
  against 2.7, 2.9, 3.0, 3.2 with none; depth 0.1 is not found). The capture as drawn: 3.1, 3.3, 3.4, 3.5, the same
  +0.4 over no band at every height: pieces a few tens of lines tall, nothing the height of a field. On the raw rows
  (no timebase involved, leans -10 to +10) the capture does gain with height, but the lean of each field's tallest
  full-height pile-up matches the timebase's prediction within 1 sample per row in 16-24% of fields against 14-16% for
  unrelated fields: not the tape's line.
- Parts of the same drawn field 80 or more lines apart share nothing at the same place on the line, in darkness,
  brightness or colour strength (correlation under 0.1% of the variance, either sign; 0.6% at 40 lines).
- Locked to the landmark, the tape's vertical blanking is only a little darker than its picture: 45-51% of samples
  at the floor against 40.5%. Horizontal blanking and sync can be expected to be as faint, which is at or below what
  one field can show.
- `pair_closure.py`: sideways offset of a field against the next from everything they share (rows that are vertical
  neighbours, cross-correlated over shift), checked without any truth by closure over three passes. Known picture at
  3% / 1% / 0.3% of the variance: offsets right within 30 samples in 94% / 74% / 35% (shapes of about 60 samples by
  30 frame rows, fields averaged over 16 lines first; 85% / 29% / 11% for shapes of 20 by 10 without averaging). The
  capture: triples close within 30 samples in 20% (9% without averaging; 7% by chance), the offsets are
  spread evenly over the line, and of the closing ones 35% sit at the difference of the two capture windows' places
  (23% by chance): partly the capture's own columns, not the tape. So what two consecutive fields share of the tape is
  about 0.3% of the variance or less.
- The capture has a pattern of its own across its columns (an arch of about +-1 code, the same in both halves of the
  clip); taking it out changes none of the above.

### Followed through all passes at once (`blank_track.py`): still not there

The tape's place along the line is continuous in write time, so a blanking band's place and lean in one pass fix where
it is in the next. Per pass, a score for every place and lean of a dark band 147 samples wide (63 for the sync tip
alone) the height of the field; the best path through all 711 + 713 free-running passes under the continuity rule is
found exactly (dynamic programming; the rule's one uncertain constant, the pass length, is scanned). Depth in points =
how many more of the band's samples sit at the floor than elsewhere; the capture's vertical blanking is 5 to 10 points
darker than its picture. "Followed" = path within 40 samples of the band (9% by chance).

| | followed | score per pass | even passes' path meets odd passes' |
|---|---|---|---|
| known answer, no band (rows slid at random) | | 1.42-1.44 | 8-10% |
| known answer, band 1.8 / 3 / 5 / 10 points | 33-38% / 69-76% / 88-91% / 92-95% | 1.5 / 1.7-1.8 / 2.3-2.4 / 3.0 | 11-13 / 19-29 / 48-58 / 64-70% |
| 10 points, sideways jump of 80 / 200 samples at every head switch | 81-85% / 51-56% | 2.7-2.8 / 2.2-2.3 | |
| 5 points, pass length constant off by 11% | 86-93% (scan peaks where it must, -36) | 2.3-2.4 | 50-54% |
| band cut into the capture's own rows, 3 / 5 / 10 points | 26% / 67% / 98% | 1.39 / 1.56 / 2.31 | 11 / 19 / 82% |
| the same, score limited per block of rows (`BLOCKS` 8) | 33% / 79% / 98% | 1.42 / 1.67 / 2.43 | 12 / 33 / 86% |
| **the capture** (and with blocks) | | **1.38** (1.38) | **8.6%** (9.3%) |
| the capture, every field's samples on another field's timebase | | 1.35 | 10.5% |

The known answers are a tape with the band in the first 147 samples of every line, sampled on a write clock swinging
+-0.5% at 1 Hz, the timebase estimated from a landmark drawn into the capture's own scattered fold; two seeds. With the
sync tip's width the picture is the same (capture 1.65 against 1.68 with rows slid; 5 points followed in 82-90%).
The capture's paths from even rows and from odd rows do agree in 25-35% of passes, but as often (21-30%) when every
field's samples are drawn on another field's timebase: that is the short dark pieces inside one field, not something
running on along the tape.

So a band 5 or more points darker than the picture, running the height of the field on a path that smooth, is not in
the capture; the clip's own dark pieces hide a 3-point band from this search, and a band that jumped sideways by much
more than 200 samples at every head switch (or jittered that much from line to line) would escape it too.

```
python3 stroke_height.py CACHE_DIR raw && python3 stroke_height.py CACHE_DIR drawn
python3 pair_closure.py CACHE_DIR 16 40 60 30
python3 blank_track.py CACHE_DIR ka && python3 blank_track.py CACHE_DIR inject 147 0 8 && python3 blank_track.py CACHE_DIR capture 147 0 8
```

## First look

```
python3 extract.py CAPTURE.tpc CACHE_DIR ../          # ../ = this repository's experiments directory
python3 look1.py CACHE_DIR && python3 look2.py CACHE_DIR
python3 shift2.py CACHE_DIR
python3 fold1.py CACHE_DIR 290 262.5 low OUT.png
python3 place1.py CACHE_DIR 200 12 OUT.png
```
