# v10 — what is pending

**This file is temporary and holds no findings.** It exists only because more is in flight than can be held in one
head. A row is DELETED when its item closes, not marked done, and when the last row goes the file goes with it.
Nothing confirmed lives here: every measurement, decision and ruling belongs in `docs/geometry_first_engine.md`
(the contract), `CLAUDE.md` or `LEARNINGS.md`, and this file only points at them (owner, 2026-09-09: "anything
that is confirmed should end up in permanent files. that tracker file must absolutely not host anything that
survives analysis, implementation, etc").

Last reconciled 2026-09-09 18:2x JST. Closed and deleted since the 04:23 reconciliation: **A3** (the
registration -> classifier feedback path; its vacuous test was replaced by one requiring the retired names to
fail compilation). Everything else on list A is unchanged, and the day added more than it closed.

**One source at a time (owner, 2026-09-09).** "the contract is sequential. I should approve a render before you
move to the next of the 4 samples." Capture 1 remains the only capture whose ENGINE ACCEPTANCE is worked on. The
owner amended this the same day for analysis specifically — "run that analysis yourself across all 4 capture" —
so the comb and box censuses cover all four; that is measurement of the source, not engine acceptance, and it
does not advance capture 2.

## Next, in order

0. **Codex's working tree is behind mine** — `3090b76` contains none of `c072b65`, `b40eb47`, `83abd99`, `2b619f9`. Its next dispatch must merge `origin/v10-harness` before anything else.
1. The comb's static mask (A15) — the identified cause of capture 1's only remaining engine blocker.
2. Capture 1's reference finishes and is checked against its own invariant (`stable_interval_check.py`).
3. The classifier defects the audit found (A10–A12) go to Codex as one dispatch.
4. Captures 2, 3 and 4 acceptance — ONLY after the owner approves capture 1's render.

## A. Engine (Codex writes, Claude reviews)

| # | item | where it is written down | state |
|---|---|---|---|
| A1 | Rule 5 gate: registration off on anything but normal picture | contract rule 5; the whole-tape score is in CLAUDE.md §6 | implemented, reviewed, whole-tape registration-on-non-picture 270 → **1**; that unit is 43,678, accepted by the owner, so the gate is closed as far as it will be closed |
| A2 | Signal-state snow / lost-lock correction at 27:18 | CLAUDE.md §6; contract rule 5b | implemented, reviewed, whole-tape misses 17 → **2**; the owner has ACCEPTED those two (units 43,678–43,679, a recording end with weird coherence, cleaned up a frame later) — not to be chased |
| A3 | Retire the registration → classifier feedback path | CLAUDE.md §11 (the one-way ownership rule) | implemented; its first deciding test was vacuous (a macro compiled the body out) and is replaced by one requiring the retired names to fail compilation |
| A4 | Per-source timing and level references that die with the lock | contract §3, rule 5b | not implemented, and wider than first written: `grep` finds **no line-22 level comparator in the engine at all**, though contract rule 4 requires the owner's eight-slot running comparator; the level references are recomputed per `field_measurement` and never retained under the lock |
| A5 | Undeclared constants named or derived | contract rule 4 ("no magic numbers") | **four**, not three: `caption_like_damage`, `timing_like_damage`, the `zero_difference` gate, and `field_registration.c:91`'s `>= 2 * 10` median-lag boundary. The owner's own three from 2026-09-08 (the bare `+4`, the three-consecutive-row rule, the five-line clip band) were already removed in Codex turn 10 and are NOT these |
| A6 | Absolute versus relative horizontal timing | contract §2; Codex turn 14 costed both | undecided; needs a C benchmark |
| A7 | Band detector split by regime | contract §2; CLAUDE.md §11 (the RF peak's role) | not built |
| A8 | Contract rules 5, 5b, 6, 7, 8, 9, 10 (rule 2's conflict report is built) | contract §4 | rules 1, 3, 4 green; rule 1's p95 reached 6.9 ms under load, 69% of the §11b budget, and must be re-measured on a quiet machine |
| A9 | Deadlines on nine unbounded waits in `frameserver_test.c`, and the `--limit`-only bound in `frameserver_replay.c:59` | LEARNINGS.md method lesson 2, which now also carries the shell form of the same defect | not fixed |
| A10 | The `SnowLike` rule has no temporal and no vertical-coherence term, so a torn raster reads as programme | CLAUDE.md §6 (the audit's mechanism and the measured correlations) | not dispatched; queued behind A1–A3 |
| A11 | The appearance latch is asymmetric: `SubBlackMuteLike` installs with no confirmation and needs three to leave | CLAUDE.md §6 | not dispatched |
| A12 | `NeutralGrayMuteLike` tests uniformity, not greyness, and asserts a `Muted` source on near-black programme | CLAUDE.md §6 | not dispatched |
| A14 | Audit the classifier's thresholds for magic numbers, using the commercial capture's opening as the case: the mute-to-programme boundary there is a rising level crossing a fixed threshold. The owner, 2026-09-09: once the warning card is legible it "shouldn't be showing up as mute but if it is, not the end of the world. Probably another thing to audit for magic numbers, but since it's the first real picture from this source I expect it to be a little slow to react." Not a defect; an audit. | CLAUDE.md §6 | not started |
| A15 | The comb's static mask: tolerance was calibrated on the device's generated blanking, so it retained 0.81–1.60% of support at blanking luma and flipped the verdict | CLAUDE.md §14; `COMB_COMPARISON.md`, `STATIC_MASK.md` | cause identified, tolerance re-measured from stationary picture patches (107/100, 173/162, 154/146 summed codes), **production still unchanged after three turns**. Claude's "the mask is redundant" argument is FALSIFIED: a coherent vertical pan makes the maskless product pick +2 at a 1,024,739× margin. The recalibrated mask is ALSO insufficient — the SP mask keeps two accidental blocks and still favours +2. Next step is an implementation, not another diagnosis |
| A16 | `complete_log` calls `abort()` on a completion mis-join — inside OBS that kills the host and the user's recording | `src/frameserver/QUEUES.md`; Codex accepted at `dec922f` | open before shipping; named fatal-session handling is the agreed policy, not implemented |
| A17 | A permanently blocked consumer cannot stall analysis but prevents shutdown drain (`fs_stop` hangs) | `src/frameserver/QUEUES.md`; Codex accepted at `dec922f` | open before shipping; caller-deadlined shutdown with quarantined live resources is the agreed policy, not implemented |
| A13 | `frameserver_replay --pace-us 0` destroys a whole-tape run and exits 0, printing no capture-level loss | CLAUDE.md §6 | not fixed; use `--pace-us 8000`, or a ring larger than the file for a slice |

## B. Harness (Claude writes, Codex reviews)

| # | item | where it is written down | state |
|---|---|---|---|
| B1 | The four references, one commit each, in the acceptance order | HANDBACK §7 step 1; `experiments/geometry_oracle/REFERENCE_SPEC.md` states every column's raw-row derivation | `switch_geometry.py` already implements most of the spec; capture 1 building, its invariant not yet checked |
| B5 | All four acceptance slices were cut mid-transfer and failed the reader's provenance check | `experiments/tpc_slice.py` header comment carries the measurement | CLOSED — both ends now align to a whole transfer; all four re-cut and provenance-clean. Delete this row |
| B6 | Horizontal-timing instrument for the owner's line-TBC mechanism | measurements belong in CLAUDE.md and are NOT yet written there | ran. **Within-capture: NULL** — field-1 jitter does not predict which units misregister (Cohen d −0.14 and +0.23, both opposite to the prediction). **Switch band: TBC-off is 27% rougher** (2.765 against 2.180), where the field body showed no difference at all (2.013/2.006) — the setting acting where it is documented to act. ⚠️ The null is not a refutation: the instrument measures the TBC's OUTPUT, downstream of the correction. **Capture 1 is unmeasurable by it and loosening the gate does not fix it** — the edge-peak gate trades validity for coverage: at 6.0, 453 of 920 units and the located edge sits at 9.45 samples where NTSC geometry predicts ~9; at 3.0, 752 units but the edge drifts to 7.44; at 1.5, 917 units at 7.02 with 583 outside a plausible 8–12. Lower gates are finding noise peaks, not line starts. Low-contrast material needs a different edge estimator, NOT a looser threshold |
| B7 | Box detection across the four captures | agent report; scripts `experiments/box_census.py`, `experiments/box_panel.py` UNCOMMITTED | census done and the title-graphic false positive rejected on the panel; three qualifications of the measure not yet acted on, chiefly that per-row `h` overlaps far more than the region statistic suggested (28.1% of the commercial tape's post-card picture rows fall below threshold) and that its denominator is an integer, making the ratio a step function of source noise |
| B2 | The bottom instrument on the phase measurement | contract rule 3 | done inside `switch_geometry.py`: the bottom is the row above the switch line, from the phase profile, not from luma |
| B3 | The render changes | contract §8 | not implemented |
| B8 | Audio in the review renders (`--dump-pcm`) | owner, 2026-09-09: "you rendered with no audio which is not cool" | not implemented |
| B4 | The acceptance runs | HANDBACK §7 steps 3 and 4 | blocked on B1 and the engine |

## C. The switch line on capture 1

Both instruments put the picture top at lines 23 and 286 in all 582 units of the stable interval: the owner's
invariant holds in two independent implementations. The switch line did not agree, and reading the raw samples of
unit 6687 settled what each was doing wrong.

- **The engine fired ~25 rows early** on a 35-code brightness gate; Codex diagnosed it and is rewriting.
- **My reference was one row late**, seeking the partial row as a lag improvement a flat dark row cannot supply.
  Fixed at `3244999` by measuring the row's own two ends.
- **Both agree on the raw rows**: picture bottom 259/521, partial switch row 260/522, first full other-head row
  261/523 — matching contract §2's already-adjudicated 259/521.
- **Codex objects to the ends test as a universal detector** and is right; the contract already makes the method
  per-instrument, with S as the stated fallback and Unknown only when neither is measurable.
- ⚠️ **My "the contract's count is one low" framing was itself wrong** (owner, 2026-09-09: the count "is source
  dependent"). There was no contract number to be right or wrong about; the count is learned per source at the
  lock and held. The per-source counts are removed from the contract's definition, and what an instrument is
  checked against is the other instrument on the same source, unit by unit, plus the lock's own constancy.

## D. Contract

- **§2's displaced-row figure is disputed and unamended.** It states "0 displaced rows against 1,957" and calls the
  separation categorical; Codex measured 11 against 1,957, "strong, not categorical" (turn 15), proposed replacement
  wording that was never applied, and §9 still reads "Nothing is open". I agree with its measurement, so it is with
  Codex for assent in the current turn; it reaches the owner only if we cannot settle it.

## E. To put to the owner

- **When a box fixes the geometry, is the fixed value taken once from a well-exposed unit and held under the lock,
  or re-measured per unit?** Rule 4 holds every other per-source quantity from a confirmed unit, which points at the
  first, but rule 8 does not say it. It matters because the verdict is stable and the EXTENT is not: the same card's
  top band reads 31 rows well-exposed and 36–41 on its dim pass and at its fades (CLAUDE.md). Asked 2026-09-09,
  not answered.

- **His vertical-tear definition was measured insufficient and amended without a word to him.** Applied literally it
  fires 1,038 times, so the contract now carries three added qualifiers (contract §3). He asked us to confirm the
  definition "makes sense"; what we found is that it needs three conditions he did not state. He has not been told
  that in those terms.
- He said on 2026-09-09 00:11 "I haven't responded to all your questions so give me a minute". Nothing tracks which
  of my questions are still with him.

## F. Recorded elsewhere, still open, outside the v10 acceptance path

- The render and the live path disagree in ~8,400 units, almost all field 2 of the first recording, by one line,
  because the renderer does not make the live path's `fieldreg_begin_segment` calls (CLAUDE.md §11). This bears on
  contract §8, which makes the owner's watch copy the live path's output.
- The raster-damage state: no observable separated the owner's torn units from their neighbours (CLAUDE.md §11).
- The EP recording's split/skewed caption class (CLAUDE.md §11, owner ruling owed).
- Genuinely unlocked baseband still needs a TBC-less deck or camcorder (CLAUDE.md §11).
- CLAUDE.md §6's deferred set: submission-order reconstruction, after-stop-authoritative live stats, the sidecar's
  full raw-evidence columns, audio serving.
- A `.tpc` tee from inside the OBS plugin.
- Filling horizontally damaged rows from the other field, backlogged behind the headroom gate (CLAUDE.md §9).
