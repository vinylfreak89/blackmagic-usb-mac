# v10 — what is pending

**This file is temporary and holds no findings.** It exists only because more is in flight than can be held in one
head. A row is DELETED when its item closes, not marked done, and when the last row goes the file goes with it.
Nothing confirmed lives here: every measurement, decision and ruling belongs in `docs/geometry_first_engine.md`
(the contract), `CLAUDE.md` or `LEARNINGS.md`, and this file only points at them (owner, 2026-09-09: "don't let
that live as a permanent artifact ... anything that is confirmed should end up in permanent files. that tracker
file must absolutely not host anything that survives analysis, implementation, etc").

Reconstructed 2026-09-09 03:58 JST from the 45 owner messages since the v10 restart, the contract, `HANDBACK.md`,
`CLAUDE.md`, the Codex turn logs and the engine's test output.

## A. Engine (Codex writes, Claude reviews)

| # | item | where it is written down | state |
|---|---|---|---|
| A1 | Rule 5 gate: registration off on anything but normal picture | contract rule 5; CLAUDE.md §11 | not implemented |
| A2 | Signal-state snow / lost-lock correction at 27:18 | CLAUDE.md §6; contract rule 5b | not implemented |
| A3 | Retire the registration → classifier feedback path | CLAUDE.md §11 (the one-way ownership rule and its deciding test) | not implemented; not yet reviewed by me |
| A4 | Per-source timing and level references that die with the lock | contract §3, rule 5b | not implemented |
| A5 | Three clusters of undeclared constants named or derived | contract rule 4 ("no magic numbers") | open |
| A6 | Absolute versus relative horizontal timing | contract §2; Codex turn 14 costed both | undecided; needs a C benchmark |
| A7 | Band detector split by regime | contract §2; CLAUDE.md §11 (the RF peak's role) | not built |
| A8 | Contract rules 2, 5, 5b, 6, 7, 8, 9, 10 | contract §4 | rules 1, 3, 4 green; seven to go |
| A9 | Deadlines on the frameserver suite's five unbounded waits | LEARNINGS.md method lesson 2 | not fixed |

## B. Harness (Claude writes, Codex reviews)

| # | item | where it is written down | state |
|---|---|---|---|
| B1 | The four references, one commit each, in the acceptance order | HANDBACK §7 step 1 | not started |
| B2 | The bottom instrument rebuilt on the phase measurement | contract rule 3; the luma rule's falsification is in contract §3 | not started |
| B3 | The render changes | contract §8 | not implemented |
| B4 | The acceptance runs | HANDBACK §7 steps 3 and 4 | blocked on B1 and the engine |

## C. Running

- The whole-tape signal-state audit. Nothing is blocked on it; it sets the order, because a signal-state change
  invalidates every sidecar and render made before it (HANDBACK §7 step 3), so the full set of classifier
  corrections is cheaper to know before the acceptance renders than after.

## D. Waiting on the owner

- Codex's model and effort changed under the upgrade (reported 2026-09-09 04:11 JST): whether the v10 thread stays on
  the new default or goes back to xhigh, and whether the app-server is restarted onto the newer CLI on disk.
