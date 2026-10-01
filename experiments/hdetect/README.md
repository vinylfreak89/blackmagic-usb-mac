# H-timing detector, physics version (Python playback experiment)

Detection only. Each field is judged in playback order from statistics of the preceding
fields (30-frame sliding window, detected bands cut out of it). This is an experiment that
feeds and scores; it is not the engine and is not on the live path.

- `phys.py` - the detector (v11 as of 2026-10-01); `NOT_MEASURED` lists every choice that is
  not yet a measurement. Version history and verdicts: the agent's experiment ledger.
- `edges_full.py` - generated from `phys.edges` with the rise/fall search limits removed;
  used only by the head-switch measurement.
- `phys_run.py` - drivers: `local` (captures 1-4 and the pan) or a comma list of tape 1 windows.
- `phys_score.py`, `phys_local_score.py` - score against the owner's scored fields.
- `switch_probe*.py` - the head-switch line measurement.
- `playback.py` - reads exact 756,048-byte units from a .tpc.

Paths to captures, scored-event files and decision logs are the ones used on the development
machine; adjust before running elsewhere.
