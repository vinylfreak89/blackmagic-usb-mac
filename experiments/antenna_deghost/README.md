# Antenna-tape deghost research (scratch code, recovered)

Research scripts for removing antenna-multipath ghosts from the TBC-off capture of the off-air antenna tape:

- the owner's sequential removal (latest ghost first, re-echoes cancelled inline, re-measure), and the colour-only
  result he judged cleaner than the earlier baseline;
- an off-air tuner simulator: negative modulation, vestigial sideband, synchronous / PLL / quasi-synchronous /
  envelope detectors, sync-tip AGC and back-porch clamp;
- ghost fits through that simulator, on blank lines and on plain-start lines at several picture levels.

Main modules: `seq2.py` (the sequence, with exact cross-term bookkeeping), `tref.py`, `simple.py`, `ghostx.py`,
`ghosty.py` (reference and copy models), `rf_sim.py` (tuner simulator), `tuner_fit.py`, `plain_fit.py`,
`bright_seq.py`, `split.py`, `tape_cache.py`, `tape_show.py`. `er/hretime.py` is the copy of `recovery/hretime.py`
the scripts imported at the time.

## Provenance

These lived in a session scratchpad under `/private/tmp` and were lost when the Mac restarted on 2026-10-26. They
were rebuilt by replaying the session transcript's file-writing steps (no analysis was re-run) and checked against
the file sizes in the 13:16 APFS local-snapshot listing: 199 of 225 files match exactly in size, and 7 of those are
also byte-identical to copies read back from that snapshot. Programme-content words were replaced with neutral
labels.

Not exact in size: `cpedge.py`, `er/echo_render.py`, `gfit.py`, `gfit_M.py`, `gfit_all.py`, `gfit_c.py`,
`gx_test.py`, `look.py`, `seq.py`, `three_way.py`.

Missing (one-off diagnostics and early tests whose creation is not recoverable from the transcript): `diag_edge.py`,
`diag_gen.py`, `diag_pass.py`, `er/baseline_render.py`, `final_hretime.py`, `gpool2_test.py`, `kscale_view.py`,
`ripple_fit_const.py`, `sbs2.py`, `sbs_stream.py`, `seq2_test.py`, `seq_test.py`, `set2_view.py`, `toluma.py`,
`tref_test2.py`, `tref_test3.py`.

The scripts still point at the scratchpad paths they ran from. Data (captures, caches, results) is not in git.
