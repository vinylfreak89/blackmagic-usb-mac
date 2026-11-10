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
bounds are carried forward, and an empty intersection is a break. The output field period in tape lines is fitted per
stretch (262.12-262.20 on the capture: tape lines are 0.14% longer than output lines, which is also why the roll measures
27.9 rows per pass and not 27.5).

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

## First look

```
python3 extract.py CAPTURE.tpc CACHE_DIR ../          # ../ = this repository's experiments directory
python3 look1.py CACHE_DIR && python3 look2.py CACHE_DIR
python3 shift2.py CACHE_DIR
python3 fold1.py CACHE_DIR 290 262.5 low OUT.png
python3 place1.py CACHE_DIR 200 12 OUT.png
```
