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

- The dark slanted strokes are the tape's sync pulses (about 60 samples wide, in segments of 30-60 rows). `hband2.py`
  finds single strokes (known answer: 99% found, 1% false); a clean one is rare on the capture (6% of windows).
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
  over 200 in 5%). The strokes themselves would have to pin it.
- Not known: what the landmark is; the 215 fields where the synchroniser kept restarting (797-1011) are locked only as
  well as their assumed placement.

```
python3 test_timebase.py CACHE_DIR && python3 test_locked.py CACHE_DIR
python3 fold525.py CACHE_DIR && python3 vtrack.py CACHE_DIR            # after render_placed.py --log CACHE_DIR/placed.csv
python3 hband4.py CACHE_DIR run && python3 hband4.py CACHE_DIR compare
python3 render_locked.py CACHE_DIR --mono --kappa 0.001166 | ffmpeg -f rawvideo -pix_fmt uyvy422 -video_size 858x526 \
    -framerate 60000/1001 -i - -c:v prores_videotoolbox -profile:v standard -aspect 763:526 OUT.mov
```

## First look

```
python3 extract.py CAPTURE.tpc CACHE_DIR ../          # ../ = this repository's experiments directory
python3 look1.py CACHE_DIR && python3 look2.py CACHE_DIR
python3 shift2.py CACHE_DIR
python3 fold1.py CACHE_DIR 290 262.5 low OUT.png
python3 place1.py CACHE_DIR 200 12 OUT.png
```
