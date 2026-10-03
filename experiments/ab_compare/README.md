# A/B review render

A 2x2 review render of chosen windows from two passes of the same tape: top row with H-timing and registration on, bottom row
with both off; left the first pass (A), right the second (B). A is the master (its timeline and audio). Each panel is the
frameserver's own published frame (`frameserver_replay --dump-uyvy`), keyed by unit counter from its `--dump-log`.

Everything about a particular pair of passes lives in a local JSON config outside git, passed as `AB_CONFIG`:
raw file and sidecar paths, output folder, byte and unit counts, first-unit counters, the B counter shift, the lost
stretches in B's raw file, and the windows (`[index, start, end]` in A recording time).

Steps:

1. `extract.py <A sidecar> A_live.npz` and `extract.py <B sidecar> B_live.npz` (per-unit series from each live sidecar).
2. `make_offset.py` in the same folder writes `ab_offset.npy`: the A-to-B row offset along the tape, from hard cuts matched in
   both sidecars.
3. `AB_CONFIG=<config> AB_OFFSET=ab_offset.npy REPLAY=<frameserver_replay> WORK=<scratch> python3 render_ab.py [1,5,12]`
   renders every window in the config, or only the listed indices. Each window replays about 20 s of each pass four times;
   its scratch panels are deleted after encoding. Output is ProRes 422 via VideoToolbox in the config's output folder.

The replay binary needs `--start-offset`, `--limit-units`, `--dump-uyvy`, `--dump-log` and `--dump-pcm`
(`make -C src/frameserver frameserver_replay` on a branch that has them).
