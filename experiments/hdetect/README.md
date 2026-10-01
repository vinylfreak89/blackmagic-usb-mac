# H-timing detector, physics version (Python playback experiment)

Detection only. Each field is judged in playback order from statistics of the preceding fields
(30-frame sliding window, detected bands cut out of it). It feeds and scores; it is not the engine
and not on the live path.

- `premise/phys.py` - the detector (v11). `NOT_MEASURED` lists every choice that is not yet a
  measurement.
- `premise/phys_run.py` - drivers: `local` (captures 1-4 and the pan) or a comma list of tape 1 windows.
- `premise/phys_score.py`, `phys_local_score.py` - score against the owner's scored fields.
- `premise/*_probe.py`, `*_analyse.py`, `*_census.py` - the measurements behind each change.
- `premise/edges_full.py` - generated from `phys.edges` with the search limits removed (switch measurement only).
- `edgestats/` - the earlier whole-tape statistics and window-rule experiments.

How this history was made (2026-10-01): the work was done in a session scratchpad and rebuilt here
as dated commits. Detector versions are exact: v3-v12 from the copies saved before each change or at
each revert, v1 and v2 recovered from the session transcript and verified by replaying the recorded
v3 edit onto them, which reproduces the saved v3 byte for byte. Each detector commit is dated by the
transcript's timestamp for the edit. Tools and probes are committed in their final state, dated by
their last write; their earlier iterations are only in the transcript. Results are not committed
(repository rule); each commit message carries the result and verdict.

Paths to captures, scored-event files and decision logs are the development machine's.

## Backlog (low priority)

- **Heavy noise bands repaired line by line** (owner, 2026-10-02: "Yes but pretty low priority. On playback that is
  very much a 'who cares' and I would actually argue a few things (like the jacket outline) did come out cleaner").
  Fixture A frame 66096 (34:14): field-1 lines ~118-176 and field-2 ~380-442 carry mixed retime/resize/interpolate/
  unavailable actions, and the top of the band renders as stacked bars from retimed, resized and far-donor rows
  rather than smeared noise. Open question for later correction work: whether a band this damaged is noise (his rule:
  timing errors only, not dropouts) and should be left alone or interpolated only from a clean field, while keeping
  edges that came out cleaner.
