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
