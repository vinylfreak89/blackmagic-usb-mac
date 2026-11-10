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

```
python3 extract.py CAPTURE.tpc CACHE_DIR ../          # ../ = this repository's experiments directory
python3 look1.py CACHE_DIR && python3 look2.py CACHE_DIR
python3 shift2.py CACHE_DIR
python3 fold1.py CACHE_DIR 290 262.5 low OUT.png
python3 place1.py CACHE_DIR 200 12 OUT.png
```
