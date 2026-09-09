# v10 — what is pending

**This file is temporary and holds no findings.** It exists only because more is in flight than can be held in one
head. A row is DELETED when its item closes, not marked done, and when the last row goes the file goes with it.
Nothing confirmed lives here: every measurement, decision and ruling belongs in `docs/geometry_first_engine.md`
(the contract), `CLAUDE.md` or `LEARNINGS.md`, and this file only points at them (owner, 2026-09-09: "anything
that is confirmed should end up in permanent files. that tracker file must absolutely not host anything that
survives analysis, implementation, etc").

**One source at a time (owner, 2026-09-09).** "the contract is sequential. I should approve a render before you
move to the next of the 4 samples." Capture 1 remains the only capture whose ENGINE ACCEPTANCE is worked on. The
owner amended this the same day for analysis specifically — "run that analysis yourself across all 4 capture" —
so the comb and box censuses cover all four; that is measurement of the source, not engine acceptance, and it
does not advance capture 2.

## Triage

**Tier 1 — make a lock reachable at all on capture 1.** Nothing else about this capture can succeed first, and
three of these four are one small change to one function.

1. **Widen the confirmation route and fix its ordering.** Accept comb *or* VBI *or* caption, and compute the comb
   before the acquisition decision instead of after it. Right now the only route is captions and this tape has
   none, so the lock is unreachable by construction — and the comb, which should be the alternative, runs 59 lines
   too late to be consulted.
2. **Drop the unconditional switch-line precondition.** A lock is geometry plus one other observation; §2 has said
   the head switch is optional since it was written.
3. **The band hold.** Absent switch is a hold of the band, invalidated only when the line count below it changes —
   then the lock is truly lost.
4. **The box's validity bounds.** A box is not invariant: if the mask changes the geometry must open up to the
   full picture, so a box needs defined bounds where it is valid and where it is invalidated. It lives through the
   fade, and the fade is measured rather than treated as noise (owner, 2026-09-09).
5. **My box mask extent** — it still covers the WARNING label, so the box can't fix geometry on the units where it
   is the only route. Mine to fix before any of it goes to Codex as concept.

**Tier 2 — make the geometry readable once it can lock.** The `count − extent` reading doesn't exist;
`top − origin` is the only one implemented and it's degenerate on this source, reading 23/286 in every stable unit.

**Tier 3 — switch detector coverage on the non-boxed units.** Including the RF peak's polarity — white in some
units, black in others.

**Tier 4 — the comb's own quality.** The recalibrated tolerance and the pairwise dominance. This *drops* below the
wiring: a perfect comb connected to nothing is worth nothing, and that's what three turns bought.

**Tier 5 — classifier defects, before any render you review**, since they invalidate every render made before them
and none exists yet.

**Tier 6 — the render**, which is the actual gate for captures 2–4.

**Tier 7 —** robustness, performance, instrument qualifications, the §2 dispute.

The biggest change from the previous version: comb quality fell from tier 1 to tier 4, and the lock wiring — which
wasn't on the list at all an hour ago — took its place. We spent the day tuning an instrument that isn't connected
to the thing it was meant to inform.

Parallelism, per the rule that Codex gets concepts and never implementations: Claude takes the mask extent, Codex
takes tier 1 items 1–3 as concepts.

## A. Engine (Codex writes, Claude reviews)

| # | item | where it is written down | state |
|---|---|---|---|
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
| B6 | Horizontal-timing instrument for the owner's line-TBC mechanism | measurements belong in CLAUDE.md and are NOT yet written there | ran. **Within-capture: NULL** — field-1 jitter does not predict which units misregister (Cohen d −0.14 and +0.23, both opposite to the prediction). **Switch band: TBC-off is 27% rougher** (2.765 against 2.180), where the field body showed no difference at all (2.013/2.006) — the setting acting where it is documented to act. ⚠️ The null is not a refutation: the instrument measures the TBC's OUTPUT, downstream of the correction. **Capture 1 is unmeasurable by it and loosening the gate does not fix it** — the edge-peak gate trades validity for coverage: at 6.0, 453 of 920 units and the located edge sits at 9.45 samples where NTSC geometry predicts ~9; at 3.0, 752 units but the edge drifts to 7.44; at 1.5, 917 units at 7.02 with 583 outside a plausible 8–12. Lower gates are finding noise peaks, not line starts. Low-contrast material needs a different edge estimator, NOT a looser threshold |
| A21 | `comb_confirm` runs at `field_registration.c:892`, AFTER `v10_decide_field` has already made the lock decision at :833 — so the comb can never license a lock, and the comment above the lock claiming it does is wrong. The comb must be computed before the acquisition decision | contract §2 ("confirmed by secondary signals… ideally more than one") | not fixed; **tier 1**, and it makes all comb quality work moot until it lands |
| A22 | The lock's only accepted confirmation is `caption_confirmation == AGREES`. **The commercial tape carries no captions** (owner, 2026-09-09), so on that source the lock is unreachable by construction whatever the geometry does. Confirmation must accept comb or VBI or caption | contract §2 and rule 4 | not fixed; **tier 1** |
| A23 | The contract's second reading of `d`, count minus extent, is not implemented — `geometry_d = top - origin` (`:792`) is the only one. On capture 1 the top reads 23/286 in every stable unit, so the implemented reading is degenerate there and the informative one is absent | contract rule 3 | not implemented; **tier 2** |
| A18 | The engine's only lock-acquisition site requires `measurement->switch_measurable` unconditionally (`field_registration.c:833`). This contradicts contract §2's standing "the head switch is optional… the band count alone never moves anything": no source lacking a measurable switch can ever lock — boxed pictures, where rule 8 forbids measuring it, and line-TBC-corrected passes, where there is no switch to find. A lock is geometry plus at least one other observation | contract §2 and rule 4 | not fixed; **tier 1**, blocks every other capture-1 item. Reviewed repeatedly and never caught |
| A19 | The band is not held when the switch is undetectable: absent detection must hold the band, invalidated only when the line count below the head switch changes | contract rule 4 | not implemented; **tier 1** |
| A20 | The RF peak detector assumes one polarity; the peak reads pure white in some units and pure black in others | contract §2 | not fixed; part of the switch-detector coverage on the non-boxed units |
| A24 | A box is not invariant — when the mask changes the geometry must open up to the full picture. The box needs defined bounds for where it is valid and where it is invalidated, and it lives through the fade, which is measured rather than treated as noise | contract rule 8 (wording owed) | not specified, not built; **tier 1** |
| B9 | **The current box mask overlays the warning text, which is why geometry cannot go in.** The owner's rule is that the card's top line IS the picture top; the detected top band stops exactly above WARNING on a well-exposed unit (31 rows) and swallows it on the card's dim pass and at its fades (36–41). A box fixes geometry through its extent, so the extent is wrong on the units that matter | CLAUDE.md (the box measurements); owner, 2026-09-09 | not fixed; blocks box geometry in the engine |
| B7 | Box detection across the four captures | agent report; `experiments/box_census.py`, `experiments/box_panel.py` committed at `83abd99` | census done and the title-graphic false positive rejected on the panel; two further qualifications not acted on — per-row `h` overlaps far more than the region statistic suggested (28.1% of the commercial tape's post-card picture rows fall below threshold), and the denominator is an integer, making the ratio a step function of source noise |
| B3 | The render changes | contract §8 | not implemented |
| B8 | Audio in the review renders (`--dump-pcm`) | owner, 2026-09-09: "you rendered with no audio which is not cool" | not implemented |
| B4 | The acceptance runs | HANDBACK §7 steps 3 and 4 | blocked on B1 and the engine |

## E. To put to the owner

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
