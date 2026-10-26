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
the scripts imported; `final_hretime.py` is `recovery/hretime.py` as it stood at 21:37:58 JST on 2026-10-24.

## Provenance

These lived in a session scratchpad under `/private/tmp` and were lost when the Mac restarted on 2026-10-26. They
were rebuilt by replaying, in order and once each, the file-writing steps of the session transcript up to the
crash (no analysis was re-run, nothing outside the scratchpad was written, and no data file was copied).

Checks against the 13:16 APFS local snapshot, which macOS later deleted:

- all 225 files match the snapshot listing's sizes exactly;
- 7 are byte-identical to copies read back from that snapshot before it went;
- two files whose size matched but whose content an earlier replay got wrong (`luma_echo.py`'s sync window,
  `vbi_grab.py`'s marker separator) were checked against the session's own later tool output, which shows the
  values these copies carry.

`final_hretime.py` is the 20:47 commit `9b0cff1` of `recovery/hretime.py` plus the session's edits to it up to the
moment it was copied, rebuilt on a scratch copy; the one patch in that window that failed in the session fails the
same way in the rebuild.

Programme-content words were replaced with neutral labels. The scripts still point at the scratchpad paths they ran
from. Data (captures, caches, results) is not in git.
