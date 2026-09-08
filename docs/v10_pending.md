# v10 — what is pending, and where it stands

Reconstructed 2026-09-09 03:58 JST at the owner's instruction ("either things are recorded in the contract or they
are still pending in the transcript... do not assume from memory") from: the 45 owner messages since the v10
restart (2026-09-07 20:29), `docs/geometry_first_engine.md`, `HANDBACK.md`, `CLAUDE.md`, the Codex turn logs
`/private/tmp/hw-session/codex_v10_turn*.log`, and the engine's own test output. Every line below names its source.
This file is a state record, not a contract: it is rewritten as items close and it never overrides the contract.

## A. With Codex (the engine). All raised, none implemented.

| # | item | source | state |
|---|---|---|---|
| A1 | **Rule 5 gate — registration off on anything but normal picture.** The caller must not measure on an ineligible raster, must publish the previously applied crop rather than `(0,0)`, must record a signal-gate hold rather than a placement, and must use current-unit eligibility, never a hysteretic prior `Present`. | owner 2026-09-09 00:44; contract rule 5; Codex turn 16 §4 | contract written; `frameserver.c:363` still calls `fieldreg_process` for every retained raster |
| A2 | **The signal-state snow / lost-lock correction at 27:18.** Acceptance, Codex's words: units 49105–49112 never `Present`; 49118–49125 snow-like lost lock (rule 5b), not mute; 49105–49166 zero registration placements; the sub-black appearances preserved. | owner 2026-09-09 03:01 and 03:12; CLAUDE.md §6; Codex turn 16 | measured and recorded; not implemented |
| A3 | **The registration → classifier feedback loop.** Codex's decision (turn 17, 2026-09-09 03:5x): remove BOTH halves, retire `signal_state_note_registration` and the unused `signal_state_commit_registration`, move chatter / applied phase / settlement to `field_registration`, and drop `settled_phase_known` and `settled_d1/d2` from `signal_result`. Its failing-first test: `registration_output_cannot_mutate_signal_state`. Its one correction to the finding as raised: the loop cannot cause `source == Present`, it can only falsely settle a misclassified interval, so it masks the 27:18 failure rather than causing it. | owner 2026-09-09 03:23 ("these are measured AFTER running registration... thats very backwards") | decision in hand, not implemented, and not yet reviewed by the harness owner |
| A4 | **Per-source references that die with the lock.** Horizontal timing and levels derived per recording, never fixed; a vertical tear or signal loss invalidates them and the lock is rebuilt. | owner 2026-09-09 00:13 | contract carries it; engine does not |
| A5 | **Three clusters of undeclared constants** — the damaged-caption classifier, the damaged-timing classifier, and the `zero_difference` gate in the other-head row test. Each names its measurement or is derived. | owner 2026-09-08 23:15 | open |
| A6 | **Absolute versus relative horizontal timing.** Codex costed both (turn 14): the absolute scan is roughly 2–10× cheaper on ordinary units and over 20× on a tear-heavy one, but it said only an implemented C benchmark gives median/p95. | Codex turns 12 and 14 | not decided |
| A7 | **The band detector split by regime** — repeated flat replacement rows for a corrected source, repeated whole-line displacement for an uncorrected one, accumulated per source and never decided from one field; the RF peak used only to confirm a switch line already found, never as the regime test (3% sensitivity). | Codex turn 15; owner 2026-09-09 02:50 | decided, not built |
| A8 | **Contract rules 2, 5, 5b, 6, 7, 8, 9, 10 in the engine.** Rules 1, 3 and 4 exist and are green: 5/5, 2/2, 5/5, at 2.53 / 0.45 / 0.48 ms per unit against the 10 ms budget. | contract §4; `make test` | seven rules to go |
| A9 | **Five unbounded `while (!done)` waits in the frameserver suite** — they hang instead of failing, which is what left five zombie processes running for up to five days. | measured 2026-09-08 | open |

## B. Mine (the harness). Step 1 of the agreed plan; not started.

| # | item | source | state |
|---|---|---|---|
| B1 | **The four references, one commit each, in the acceptance order.** All four captures exist and all eight named tools are present. | HANDBACK §7 step 1 | nothing built |
| B2 | **The bottom instrument.** `experiments/edge_variance.py` measured where content begins and ends horizontally, which moves with brightness. Over the commercial capture's stable interval it put the bottom at 259 in 460 units and 260 in 66, where it must be constant, and 578 of 1,840 field readings came back unmeasurable. Superseded by contract rule 3: the bottom is the row above the switch line, a geometry rule. | owner 2026-09-08 23:15; contract rule 3 | correction committed with its negative result; the replacement is the phase measurement, not a luma rule |
| B3 | **The render changes.** Both fields' applied shifts plotted, not `d1` alone; the head-switch band's top and bottom edges traced per field; the per-source horizontal-phase and level statistics in the band; the alignment guard changed from two frames per row to one; bwdif `send_frame` at 29.97p. | owner 2026-09-09 00:05, 00:11, 00:13; contract §8 | specified in the contract, not implemented |
| B4 | **The acceptance runs** (plan steps 3 and 4). | HANDBACK §7 | blocked on B1 and on the engine |

## C. Owner questions not answered

- **"How do you trace the head-switch band's top and bottom without covering the line?"** (2026-09-09 00:18, asked
  out of curiosity). Answered 2026-09-09 03:58: nothing is drawn on the raster. The two edges are plotted in the
  metrics band below the picture, on the same graph as the applied shifts, so the rows being measured are never
  painted over. The contract already required the band to sit below the picture and never over it.
- **"Do whites peak out too high?"** (2026-09-09 03:27). Partly. Not clipping at white IS measured: no samples at
  254 or 255 in three of the four captures and two in the fourth. Whether 100 IRE lands above BT.601's 235 was
  never measured — the figure of code 239 given that night was an estimate from the device's own line-21 insert,
  and the agent measuring it was stopped when the owner closed the topic. It does not matter under his ruling that
  the project does not match studio levels, and his acceptance was "as long as its not clipping", which is met.

## D. Running

- **The whole-tape signal-state audit** (owner, 2026-09-09 03:10: audit where the live engine unlocks, whether it is
  too reactive, and anything caught as snow-like that is not snow). Part A measures all 86,293 units directly,
  part B replays the whole tape through the live path, part C audits, with the known 27:18 miss as a check on its
  own method.

Nothing is blocked on it. What it changes is scope: a signal-state change invalidates every decision-log sidecar
and every render made before it (HANDBACK §7 step 3), so the cheapest order is to know the full set of classifier
corrections before the acceptance renders are generated, not after.

## E. Recorded elsewhere, still open, outside the v10 acceptance path

- The raster-damage state: no observable separated the owner's torn units from their neighbours, so no threshold
  was tuned; an owner decision is owed (CLAUDE.md §11, round 11/12).
- The EP recording's split/skewed caption class: whether `CaptionRelock` fires from the run-in row or never fires
  (CLAUDE.md §11, owner ruling owed).
- A `.tpc` tee from inside the OBS plugin (needs a runtime-attachable tagged sink in the capture core).
- Filling horizontally damaged rows from the other field — backlogged by the owner behind the real-time headroom
  gate, with the design settled (CLAUDE.md §9).
