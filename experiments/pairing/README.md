# Pairing schedules

`--pairing-schedule` inputs for `frameserver_replay` (format: `first_counter,pairing,note`, starting at counter 0).

- `fixture_a.csv`: fixture A (`trip_tape.mov.raw.tpc`), reversed from play start, aligned from counter 48189, as in
  the approved 2026-09-26 decision log. Replaying with it reproduced that log exactly (0 changed placements of 86,289,
  2026-10-02), so the log can be regenerated from the capture with this schedule and the engine. Committed at the
  owner's request (2026-10-02) when the log itself was replaced by the 2026-10-02 review's.
