# v10 — what is pending

**This file is temporary and holds no findings.** It exists only because more is in flight than can be held in one
head. A row is DELETED when its item closes, not marked done, and when the last row goes the file goes with it.
Nothing confirmed lives here: every measurement, decision and ruling belongs in `docs/geometry_first_engine.md`
(the contract), `CLAUDE.md` or `LEARNINGS.md`, and this file only points at them (owner, 2026-09-09: "anything
that is confirmed should end up in permanent files. that tracker file must absolutely not host anything that
survives analysis, implementation, etc").

Last reconciled 2026-09-09 04:23 JST against an independent re-derivation of this list and the completed
whole-tape signal-state audit.

## Next, in order

1. Codex's current turn (A3, A1, A2 together, plus the §2 amendment) lands and I review it.
2. Capture 1's reference finishes and is checked against its own invariant (`stable_interval_check.py`).
3. The classifier defects the audit found (A10–A12) go to Codex as one dispatch, after its current turn.
4. Captures 2, 3, 4 references.

## A. Engine (Codex writes, Claude reviews)

| # | item | where it is written down | state |
|---|---|---|---|
| A1 | Rule 5 gate: registration off on anything but normal picture | contract rule 5; CLAUDE.md §11; the +101/+118-line crops from a contentless raster are in CLAUDE.md §6 | dispatched 2026-09-09 04:3x |
| A2 | Signal-state snow / lost-lock correction at 27:18 | CLAUDE.md §6; contract rule 5b | dispatched with A1 |
| A3 | Retire the registration → classifier feedback path | CLAUDE.md §11 (the one-way ownership rule and its deciding test) | dispatched with A1; its decision came back in the task output, not a turn log, so there is no `codex_v10_turn17.log` to cite |
| A4 | Per-source timing and level references that die with the lock | contract §3, rule 5b | not implemented, and wider than first written: `grep` finds **no line-22 level comparator in the engine at all**, though contract rule 4 requires the owner's eight-slot running comparator; the level references are recomputed per `field_measurement` and never retained under the lock |
| A5 | Undeclared constants named or derived | contract rule 4 ("no magic numbers") | **four**, not three: `caption_like_damage`, `timing_like_damage`, the `zero_difference` gate, and `field_registration.c:91`'s `>= 2 * 10` median-lag boundary. The owner's own three from 2026-09-08 (the bare `+4`, the three-consecutive-row rule, the five-line clip band) were already removed in Codex turn 10 and are NOT these |
| A6 | Absolute versus relative horizontal timing | contract §2; Codex turn 14 costed both | undecided; needs a C benchmark |
| A7 | Band detector split by regime | contract §2; CLAUDE.md §11 (the RF peak's role) | not built |
| A8 | Contract rules 5, 5b, 6, 7, 8, 9, 10 (rule 2's conflict report is built) | contract §4 | rules 1, 3, 4 green; rule 1's p95 reached 6.9 ms under load, 69% of the §11b budget, and must be re-measured on a quiet machine |
| A9 | Deadlines on nine unbounded waits in `frameserver_test.c`, and the `--limit`-only bound in `frameserver_replay.c:59` | LEARNINGS.md method lesson 2, which now also carries the shell form of the same defect | not fixed |
| A10 | The `SnowLike` rule has no temporal and no vertical-coherence term, so a torn raster reads as programme | CLAUDE.md §6 (the audit's mechanism and the measured correlations) | not dispatched; queued behind A1–A3 |
| A11 | The appearance latch is asymmetric: `SubBlackMuteLike` installs with no confirmation and needs three to leave | CLAUDE.md §6 | not dispatched |
| A12 | `NeutralGrayMuteLike` tests uniformity, not greyness, and asserts a `Muted` source on near-black programme | CLAUDE.md §6 | not dispatched |
| A13 | `frameserver_replay --pace-us 0` destroys a whole-tape run and exits 0, printing no capture-level loss | CLAUDE.md §6 | not fixed; use `--pace-us 8000`, or a ring larger than the file for a slice |

## B. Harness (Claude writes, Codex reviews)

| # | item | where it is written down | state |
|---|---|---|---|
| B1 | The four references, one commit each, in the acceptance order | HANDBACK §7 step 1; `experiments/geometry_oracle/REFERENCE_SPEC.md` states every column's raw-row derivation | `switch_geometry.py` already implements most of the spec; capture 1 building, its invariant not yet checked |
| B2 | The bottom instrument on the phase measurement | contract rule 3 | done inside `switch_geometry.py`: the bottom is the row above the switch line, from the phase profile, not from luma |
| B3 | The render changes | contract §8 | not implemented |
| B4 | The acceptance runs | HANDBACK §7 steps 3 and 4 | blocked on B1 and the engine |

## C. Contract

- **§2's displaced-row figure is disputed and unamended.** It states "0 displaced rows against 1,957" and calls the
  separation categorical; Codex measured 11 against 1,957, "strong, not categorical" (turn 15), proposed replacement
  wording that was never applied, and §9 still reads "Nothing is open". I agree with its measurement, so it is with
  Codex for assent in the current turn; it reaches the owner only if we cannot settle it.

## D. To put to the owner

- **His vertical-tear definition was measured insufficient and amended without a word to him.** Applied literally it
  fires 1,038 times, so the contract now carries three added qualifiers (contract §3). He asked us to confirm the
  definition "makes sense"; what we found is that it needs three conditions he did not state. He has not been told
  that in those terms.
- He said on 2026-09-09 00:11 "I haven't responded to all your questions so give me a minute". Nothing tracks which
  of my questions are still with him.

## E. Recorded elsewhere, still open, outside the v10 acceptance path

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
