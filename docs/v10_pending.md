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
| A21 | ~~The comb cannot license a lock~~ **WITHDRAWN, Claude was wrong** (Codex, 2026-09-09). There are TWO acquisition sites, not one: `field_registration.c:608` locks from the comb with no caption, and `:839` locks from a caption. The comb is wired to a lock. The claim that three turns of comb work were aimed at a disconnected path was false | — | closed, kept only so the error is not repeated |
| A22 | ~~Confirmation is caption-only, so a caption-less tape cannot lock~~ **WITHDRAWN, Claude was wrong.** The comb path at `:608` needs no caption. Also wrong in the same brief: confirmation must accept "comb or VBI or caption" — the contract's Source lock definition carries the owner's own words, "combing, captions, or both, and nothing else", so VBI was Claude's invention | contract §3 Source lock | closed |
| A23 | The contract's second reading of `d`, count minus extent, is not implemented — `geometry_d = top - origin` (`:792`) is the only one. On capture 1 the top reads 23/286 in every stable unit, so the implemented reading is degenerate there and the informative one is absent | contract rule 3 | not implemented; **tier 2** |
| A18 | **BOTH acquisition sites require a measurable switch on both fields** (`field_registration.c:601–602` for the comb path, `:834` for the caption path), so no source lacking one can lock — boxed pictures, where rule 8 forbids measuring it, and line-TBC-corrected passes, where the owner says there is none. **This is not an engine defect: the contract's Source lock definition requires it in the owner's own words** ("at a unit whose switch line and band are measurable"). The contract contradicts itself and neither agent may resolve it | contract §3 Source lock against §2 and rule 8 | **blocked on the owner**; nothing in tier 1 can proceed until he settles it |
| A19 | The band is not held when the switch is undetectable: absent detection must hold the band, invalidated only when the line count below the head switch changes | contract rule 4 | not implemented; **tier 1** |
| A20 | **RF-peak confirmation is unimplemented** — there is no detector at all (`field_registration.c:344` initialises both peak fields to −1 and nothing assigns them; `measure_switch:186` uses displaced blanking intervals, not the peak). Claude's "the detector assumes one polarity" was wrong: it tests neither polarity. The record's `f*_rf_peak_line/position` columns are therefore always −1. Building one needs local-departure evidence that separates a genuine peak from an ordinary picture edge, with goldens for BOTH polarities — the owner's black-polarity observation stands and has not been searched for | contract §2 | not built; switch-detector coverage on the non-boxed units |
| A24 | A box is not invariant — when the mask changes the geometry must open up to the full picture. The box needs defined bounds for where it is valid and where it is invalidated, and it lives through the fade, which is measured rather than treated as noise | contract rule 8 (wording owed) | not specified, not built; **tier 1** |

## B. Harness (Claude writes, Codex reviews)

| # | item | where it is written down | state |
|---|---|---|---|
| B1 | The four references, one commit each, in the acceptance order — **1 of 4 done** | contract §8; `experiments/geometry_oracle/REFERENCE_SPEC.md` states every column's raw-row derivation | PARTLY — capture 1 only. Its reference is built and its invariant CHECKED: 0 violations (`stable_interval_check.py`, 508 units from counter 6667, both fields measurable in all 508). Captures 2, 3 and 4 not started — they follow capture 1's acceptance |
| B6 | Horizontal-timing instrument for the owner's line-TBC mechanism | measurements belong in CLAUDE.md and are NOT yet written there | ran. **Within-capture: NULL** — field-1 jitter does not predict which units misregister (Cohen d −0.14 and +0.23, both opposite to the prediction). **Switch band: TBC-off is 27% rougher** (2.765 against 2.180), where the field body showed no difference at all (2.013/2.006) — the setting acting where it is documented to act. ⚠️ The null is not a refutation: the instrument measures the TBC's OUTPUT, downstream of the correction. **Capture 1 is unmeasurable by it and loosening the gate does not fix it** — the edge-peak gate trades validity for coverage: at 6.0, 453 of 920 units and the located edge sits at 9.45 samples where NTSC geometry predicts ~9; at 3.0, 752 units but the edge drifts to 7.44; at 1.5, 917 units at 7.02 with 583 outside a plausible 8–12. Lower gates are finding noise peaks, not line starts. Low-contrast material needs a different edge estimator, NOT a looser threshold |
| B7 | Box detection across the four captures | `experiments/box_census.py`, `experiments/box_panel.py` | census done, title-graphic false positive rejected, and the integer-denominator qualification is now understood and worked around (the threshold is a fraction of the field's own structured level, so the fade no longer moves the band). Remaining: per-row `h` overlaps far more than the region statistic suggested, so it is the band STRUCTURE — a run anchored at the field edge, in both fields, with sustained content between — carrying the census, not the per-row threshold |
| B3 | The render changes | contract §8 | PARTLY: capture 1 renders end to end at `1d66719` — 919 units, 720×486, colour, band below the picture, band edges as margin ticks, running line, audio in sync to 8 ms. Remaining against §8: the 525-line raster panel beside the picture; the graph traces d1/d2 but not the band's two edges per field; the machine read-back is not run over it; the identity-strip label overlaps the strip. The band also lacks gauge line and decoded bytes, geometry `d`, clip line, the conservation equation and `comb_safe` — all present in the record — and pedestal, the line-22 level with its comparator count and the horizontal phase, which the engine does not emit at all |
| B4 | The acceptance runs | contract §8 | blocked on B1 and the engine |

## Blocked on the owner

Neither agent may resolve these; the process sends contract conflicts to him.

1–3 **ANSWERED 2026-09-09 and written into the contract**: the switch requirement is conditional (required only
   where the geometry is not boxed and not all lines are picture); confirmation stays comb-or-caption and a source
   that never locks is an accepted outcome, fail closed; the hold keeps the head switch's position line and is lost
   only when the total number of bands changes, ordinary clipping excluded. A change of geometry — box to full
   picture or back — resets the lock.

~~4. The contract's 486 crop is off by one~~ — CONFIRMED and corrected 2026-09-09.
~~4. Rule 8's box-validity wording is owed~~ — the bounds where a box is valid and where it is invalidated. Neither
   agent should write it. Asked and explained; answer pending.
~~5. Is VBI a confirmation signal alongside captions?~~ The owner raised it himself: "isn't VBI another confirmation
   signal? ... caption and VBI are kind of part of the same class I think". It would give a caption-less source a
   second confirmation. Answered back to him with the asymmetry that decides it; his ruling pending.

## C. Recorded elsewhere, still open, outside the v10 acceptance path

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
