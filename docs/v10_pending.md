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

**Tier 0 — the harness's own switch line must be trustworthy before anything is compared against it.** It jitters
by a row where the signal does not, and typed constants remain. **What jitters is the band's TOP (`T`), not the
switch line — `S` is stable across the blips, and `switch_lines` is derived from `T` so it inherits it.** Field 1
normally reads T=S=260 and blips to 259; field 2 normally reads T=522 with S=523 and blips to 523: the two fields
sit on opposite sides of the same binary "is the row above the switch part of the band" decision. The raw rows say
the blip row is ordinary picture, so it is instrument error; `SG_EXPLAIN` names which disjunct fires.
**The typed-constant ledger, every entry decided by measurement on capture 1 rather than by argument.** Six, not
the five first counted — the sixth was a duplicate nobody had noticed.

| constant | outcome | evidence |
|---|---|---|
| caption run-in gate | **derived**, from CEA-608's 50 IRE p-p run-in and BT.601's 219 codes/100 IRE | `98257b0`; 0 of 1,840 readings changed |
| insert-presence test | **derived**, from the field's own blanking noise | `113882a`; 0 of 1,840 |
| duplicate run-in gate (a second copy, typed 35, whose comment claimed it sat "at the decoder's own gate" while the decoder's had become 27.375) | **removed**, now imported | `910f345`; 0 of 1,840 |
| span floor (`len(span)>=60`) | **derived**, `2*MAXLAG` from the search it guards | `d964a73`; sweeping to 40 and 100 left the reference byte-identical, and the floor is monotone, so identical output at both ends PROVES no row has a span in [40,100) |
| `M_run+8` blanking slack | **KEPT, and it is load-bearing** | `7340fa5`; removing it changed 3 field-2 units, converted two documented holds into detections, and introduced a jitter blip at 6674 — a regression on tier 0's own criterion |
| field-2 envelope (mean < 95, bins 20–47 ≤ 40, run of ≥ 6 bins > 60) | **KEPT, and inert here** | `fef5a43`; 11,017 calls on capture 1, FIRED 0 (rejected by mean 3,390, by the right-hand bins 197, by no run of six 7,430). Cannot be derived — the bar is a smeared source artefact of fixture A's second recording, not a standard waveform |

**All six are settled.** Two things this ledger should not be read as saying. `M_run+8` staying is not a defeat:
the measurement found it carries a decision, and the principled replacement — the body's DISTRIBUTION instead of
its maximum plus a constant — is named at the site for the next attempt. And the field-2 envelope firing nowhere
on capture 1 makes it inert HERE, not derived; it decides real rows on capture 2, and removing a test because the
capture in front of us never triggers it would be fitting the instrument to the fixture, which is the fault this
exercise exists to remove.

**"Off-mode" is the WRONG stability metric, measured 2026-09-10, and it was counting legitimate travel as error.**

- **`|T − mode| > 1` is ZERO** in both fields across every registerable unit (508 field 1, 505 field 2). That is
  exactly what contract §8 permits: "the switch line moves only with the top and only within the partial line's
  one-row travel". On the contract's own stated invariant the harness already passes.
- The residual off-mode units are mostly RUNS, not scatter: field 2 has runs of 20, 17, 6, 4, 4 and 3 units;
  field 1 a run of 9 and four of 2.
- **The longest run was checked on the raw rows and it is real travel.** At the transition into field 2's 20-unit
  run, line 522's trailing blank run reads 0 at counter 6691 and 19 at 6692 — at 6691 the other head has taken
  that row's trailing blanking, so it IS the partial line and T=522; at 6692 its own blanking is back and the
  partial structure has moved down to 523, so T=523. The panel shows the transient at the far right of 522 in
  6691 and not in 6692. The harness is following the signal, not wobbling.

**What is actually left is the single-unit blip class: 17 in field 1 and 8 in field 2**, down from 27 and 14. A
one-unit excursion that returns is the shape that cannot be real travel, and that is the number the harness lock
should be judged on — not off-mode, which the contract already licenses.

⚠️ Settling the constants and reframing the metric still does NOT lock the harness — that is the owner's gate to
close, on his criterion, and "stable and agreeing" is his phrase to interpret.

⚠️⚠️ **AND THE STABILITY METRIC IS STRUCTURALLY BLIND TO A REAL ERROR — found 2026-09-10 by the engine comparison,
which is exactly why the gate has two halves.** At counters 6899 and 6817 and their neighbours, the raw sample
profiles put the partial row unambiguously at line 261: it carries 180–215 samples of blank-level prefix against
the ~9 the contract allows a correctly timed row, while line 260 carries none and is ordinary picture. **The
harness reads T=260 in all six units — wrong in all six.** Since 260 IS the mode, off-mode counts it correct and
`|T − mode| ≤ 1` passes: no stability measure taken tonight can see this class of error. Stable is not correct.

**SCOPED, and it is LOCAL — the systematic-error alarm above is withdrawn** (`experiments/displaced_row_census.py`,
which detects both morphologies of long blank-level run, with bounds carried over from `switch_geometry.py` — NOT
the contract's, see the correction below — and the blank level from each field's own regenerated rows, sharing no
code with the harness):

| harness's `S` vs the first long blank-level run | readings |
|---|---:|
| **exact, at HEAD** | **1013 of 1013 (100%)** |
| as first measured | 963 of 1013 |

**The harness's `S` is now exact in every registerable field-reading on capture 1.** Three things got it there,
each measured and none argued: `torn` no longer selects the switch line (963 → 1009), `step` no longer selects it
(→ 1012), and the census's own unjustified 200-sample ceiling came off (→ 1013).

⚠️ **The last one was MY instrument's fault, not the harness's**, and it matters because this census is what
scored every other change tonight. At 6907 f1 the harness reads `S=261`, the ENGINE AGREES, and line 261 carries
a 205-sample blank-level run — above the ceiling I had wrongly called the contract's — so the census skipped the
correct row. The harness had no residual off-by-one; the ruler did. The scoring of the other changes survives,
because each was judged on MOVEMENT in the same instrument and a fixed ceiling biases every arm identically.

⚠️ **What this does NOT establish**, unchanged and important: the census validates `S`, which is POSITION. It does
not validate `T`, which is where the real disagreement with the engine lives (71 of 97). And it does not
establish that the run is physically relocated blanking rather than clipped black content — Codex is building an
independent observation with a stationary-black-rectangle control for exactly that hole.

⚠️ Four instrument errors on the way to that number — three caught by the instrument's own output rather than by
review, the fourth by adjudicating its last reported discrepancy on raw rows. All recorded so the next census
does not repeat them. The first version tested only a LEADING blank
run and was blind to the interior-run morphology (6667 line 260 reads `lead_run 0`, `blank_run 158`), giving
itself away by flagging field 2's clip line as displaced. The second compared the relocated row against `T` and
reported `T+1` in 907 of 1013 — which is the DEFINITION of the T-to-S relationship, not an error, since `T` is
the partial row and need not carry a whole relocated interval. `S` is the quantity that means the same thing.
What survives from the alarm: 6899 is a real fault in `S`, and the mode-based stability metrics cannot see it.

Also unfixed and named at its site: `lead_blank` is a bool, so an unreadable lead is asserted as "not blank"
rather than unknown. Harmless on this capture; a real fault where the regenerated rows are absent.

**AGREEMENT, the gate's second half — measured 2026-09-10 against the rule-8-conformed engine (`800ed67`).**
The earlier 142 agree / 60 disagree was against pre-ruling behaviour and is superseded; it was never reported to
the owner as a result, which was the right call.

| | pre-ruling engine | rule-8 conformed |
|---|---:|---:|
| agree | 142 | **383** |
| disagree | 60 | **97** |
| engine Unknown, boxed | 285 | **7** |
| engine Unknown, NOT boxed | 526 | 526 |

Where both instruments measure — 480 readings — they agree on **383 (79.8%)**. ⚠️ Codex's own count corrects
figures quoted earlier here: **814 Unknowns = 287 boxed + 527 non-box**, not 811/285/526.

**71 of the 97 disagreements (73%) are ONE shape, and it is not the one the earlier join suggested.** 41 in
field 1 (engine 261/261 against harness 260/261) and 30 in field 2 (engine 523/523 against harness 522/523):
**the two instruments agree on `S` and differ only on `T`** — whether a partial row sits above the first full
other-head row. The engine reads no partial where the harness reads one. This is now one-directional, where the
pre-ruling split was 26 one way and 18 the other.

⚠️ **The displaced-row census CANNOT adjudicate this.** It validates `S`, which is exactly what the two
instruments already agree on. Deciding whether the partial exists needs raw-row adjudication on a sample of the
71, and that is the next measurement on this half.

**The 527 non-box Unknowns are the larger half and are NOT one cause** (Codex's per-reading census, keyed in the
CSV as `no_disjoint` 265, `accepted_then_returned` 147, `no_basis` 75, `no_accepted` 44, `no_prefix_free` 2,
`no_complete` 1, against 482 measured). **141 of the clearing events occur at field-2 line 525**, the clip line.
The 145-versus-147 difference is NOT an error (Codex, 2026-09-10): it is a cohort distinction. 145 belong to the
prior 527 non-box cohort; the full CSV adds two boxed readings, 6671/f2 and 6764/f2. Both numbers are correct for
their cohort.

**The largest bucket is a GAP, not a rule correctly applied — measured 2026-09-10.** For all 265 `no_disjoint`
readings, the row the HARNESS independently identifies carries a long run at the field's own blank level —
**265 of 265, 100%** — with the mass at 140–159 samples, against the ~147 the contract's 10.9 µs horizontal
blanking interval gives at 13.5 MHz:

| blank run at that row | 80–99 | 100–119 | 120–139 | 140–159 | 160–179 | 180–199 |
|---|---:|---:|---:|---:|---:|---:|
| readings | 8 | 2 | 89 | **146** | 9 | 11 |

So the engine declines rows carrying a long blank-level run because their phase departure is not separable from
local horizontal variation.
⚠️ **Two corrections, both Codex's, both accepted.** (1) The 64 and 200 bounds are the HARNESS's, from
`switch_geometry.py`, NOT the contract's — the contract carries only the 10.9 µs interval, and 200 is not derived
from it. Earlier text here called them the contract's, which was a falsely sourced constant. (2) A blank-level run
is not proof of relocated blanking: the test admits any qualifying low-level window, and CLAUDE.md records that
black content in this material can be clipped to exactly the blanking level with the same dither. So the gap
finding stands on POSITION — a long blank-level run sits where the harness reads S, in all 265 — and NOT on an
assertion of what that run physically is. Establishing that needs an observable this instrument does not have. That is expected on THIS capture and the reason generalises:
`composite_program_30s` is the line-TBC-OFF pass, and contract §2 measures that regime as the one with wide
horizontal timing error (1,022 of 1,042 rows readable at ≥ 100 samples, median 192). A phase-envelope test is
what that regime defeats — and it is the regime the acceptance order puts FIRST.

⚠️ Two things this does NOT claim. It is not an adjudication that the phase test is wrong in general: on the
TBC-on captures a narrow envelope may make it the better instrument, and this harness is gated from measuring
them. And it does not use the engine's candidate funnel, so Codex's caveat that the cause is "the first zero over
the whole scan, not an assertion about which row is the true band" does not weaken it — the row examined is the
one an independent instrument identifies, and that instrument reads `S` exactly in 1,012 of 1,013 readings here.

The shape of the finding: the engine has one observable for the switch where the contract describes two. §3
carries the blanking-inside-the-row observable explicitly; its 64–200 bounds are the HARNESS's, and what the
contract gives is the 10.9 µs interval (~147 samples at 13.5 MHz).

**Codex agreed it is an instrument gap and built the second observation (`856ec13`) — and it recovers 2 of the
265.** Its discriminator is better than anything proposed from the harness side: **porch loss, not level.** A
relocated row loses its leading porch and its trailing minimum extent; *"a stationary black rectangle with
unchanged porches is therefore rejected, even when its samples are exactly identical to blanking"* — which closes
the hole this harness's level test provably cannot. 34/34 controls under ASan/UBSan, 0.3115/0.372 ms.

| | agree | disagree | engine-Unknown | mutually measured |
|---|---:|---:|---:|---:|
| `800ed67` | 384 | 96 | 533 | 480 (80.0%) |
| `856ec13` | 383 | 99 | 531 | 482 (79.5%) |

`no_disjoint` 265 → 264, `run_recovered` 2, and a new `observation_disagreement` 6.

**DIAGNOSED — and it is leading-edge truncation, not strictness.** Codex's per-stage funnel puts 255 of 264
(96.6%) at the first stage, "no exposed interior alphabet run ≥ 147 samples"; the both-ends porch requirement
accounts for 4. Measured at the harness's `S` row for exactly those 255:

| | of 255 |
|---|---:|
| run **touches the leading edge** (starts at sample ≤ 2, left end off-window) | **229** |
| interior, both ends exposed | 26 |
| run **shorter than 147 samples** | **205** |
| ≥ 147 | 50 |

Those are one fact seen twice. The relocated blanking arrives at the leading edge of the delivered window and is
truncated by it, so it is at once missing an exposed left endpoint and shorter than 147. The lengths cluster just
BELOW 147 — the signature of a 147-sample interval losing a few samples off the left, not of a different feature.
720 of 858 samples are delivered; an interval displaced leftward runs off the edge.

**So Codex's requirement is not mis-tuned: the extent is genuinely absent from the delivered window.** The open
question put to it is narrower — whether a one-ended observation is sound when the left endpoint is unmeasurable
by construction but the right endpoint is exposed. If the answer is no, the honest outcome is that these 255 are
unmeasurable by the engine and the agreement half closes with a named, understood residue rather than a fix.

**The full account, after two corrections from Codex, both of which were right.** The 255 split into two nested
causes with nothing left over:

| | of 255 |
|---|---:|
| fail on length even under the most permissive measure — **truncated at the window edge** | **205** |
| additionally **fragmented by alphabet splitting** | **42** |
| genuine uninterrupted ≥147 run, failing at later stages | 8 |

- **Truncation is real but was over-counted.** 210 start at sample 0 with the left endpoint genuinely off-window;
  19 start at 1 or 2, where the endpoint IS visible and nothing is truncated; 26 are interior. Claude's "touches
  the leading edge, 229" conflated the first two — Codex's point that a start ≤ 2 is proximity, not truncation.
- **The alphabet IS an obstacle, and the earlier dismissal used the wrong test.** The predicate requires
  UNINTERRUPTED membership, so one excluded code mid-run fragments it. Longest run ≥ 147 by tolerance band: 50;
  by uninterrupted alphabet: 8. **42 of the 50 are split below 147.** The earlier reasoning — 1.0% of 36,190
  samples outside, therefore not the obstacle — measured frequency and inferred a mechanism from it.

These are different fixes: one says the evidence is not in the window, the other says it is there and the
predicate is brittle to a few scattered codes. **The 42 are the tractable half.**

⚠️ **Three of Claude's hypotheses died on this question** and are recorded so neither agent re-runs them: the
both-ends porch requirement (binds on 4 of 264), the alphabet as a frequency effect (wrong test), and "touches
the edge" as truncation (right for 210, wrong for 19). The pattern in all three is the same — measuring an
aggregate and treating it as the mechanism.

**Codex's bar for any one-ended observation**, stricter than the harness side proposed and adopted as the
standard here: leave the missing endpoint and full extent Unknown and never reconstruct them by assuming 147;
require corroborating timing evidence such as another identifiable feature moving consistently; keep the
stationary edge-connected black rectangle rejecting; abstain when identity cannot be established, because
"persistence to the clip alone cannot distinguish blanking from content".

⚠️ And its caution stands unqualified: this makes truncation a strong and quantified explanation, NOT a proof
that all 255 share one cause, and the exposed right endpoint has not been shown to supply sufficient timing
identity.

⚠️ **Engine cost at `800ed67` is 9.7475 ms median / 16.772 ms p95 per engine call.** §11b's budget is 10 ms for
the WHOLE worker including classifier, assembly and publish, so the engine alone is at the budget's edge and the
p95 is over it. Codex states plainly this is not a budget pass. Optimisation waits on correctness acceptance
(the standing rule), but the number belongs on the record now rather than being discovered at acceptance.

**Tier 1 — the engine's switch detector on ordinary picture. It is what makes a lock POSSIBLE, and it is failing
where the switch demonstrably is.** On capture 1's 364 non-boxed registerable units (counters 6811–7174) the
harness reference measures the switch in **364 of 364** — T reads 260 in 337, 261 in 25, 259 in 2, and the picture
top reads 23 in every one. The engine measures it in **3 of 364**. That two-instrument disagreement, not the box
and not the comb, is why this capture does not lock on its actual programme. The card is 144 units; the ordinary
picture is 364.

**Tier 2 — the comb, finished and quarantined**, waiting on tier 3 so it cannot lock on the card first. The 367 of
508 decisive figure belongs to the pre-correction prototype; the corrected version has passed six synthetic and
seven cached raw controls and has had no whole-capture replay.

**Tier 3 — box classification, largely landed.** Exclusions cover 143 of 144 card units in field 1 and 144 of 144
in field 2, with the golden at 18/18 including counter 6668. Open: one residual at field 1 counter 6810, and
detections at 6263–6268 needing adjudication. This makes a lock LEGITIMATE by suppressing switch evidence rule 8
excludes; it does not make one possible, and it establishes no box position — boxed placement stays Unknown.

**Tier 4 — the render's content**, the owner's gate. Three §8 quantities remain undrawable because the engine does
not emit them.

**Tier 5 — classifier defects**, before any render he reviews.

**Tier 6 — robustness, performance, instrument qualifications.**

**Gated behind harness work, NOT on the owner.** Neither is answerable until the instrument is trustworthy, and
presenting them as his to decide made him the bottleneck when the harness was.

- **Rule 8 hold-versus-set** — gated behind the switch line being trustworthy throughout. He was holding it on the
  band being at the correct location across the capture, and by our own measurement it is not: the switch line
  still jitters by a row, most of it the partial-row test rather than the signal, and fitted constants remain in
  the instrument.
- **Box centring** — gated behind settling where a box's band ends when it meets the switch band, since the
  recentring offset is 4.0, 3.5, 2.5 or 1.5 field lines depending on that boundary alone.

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
   where the geometry is not boxed and not all lines are picture); ~~confirmation stays comb-or-caption~~ **— that
   half is superseded by item 7, settled 2026-09-09T16:40:11Z: a measurable box is itself one of the two
   confirmations and at least one further observation, comb or head switch, completes the lock** — and a source
   that never locks is an accepted outcome, fail closed; the hold keeps the head switch's position line and is lost
   only when the total number of bands changes, ordinary clipping excluded. A change of geometry — box to full
   picture or back — resets the lock.

~~4. The contract's 486 crop is off by one~~ — CONFIRMED and corrected 2026-09-09.
~~4. Rule 8's box-validity wording is owed~~ — the bounds where a box is valid and where it is invalidated. Neither
   agent should write it. Asked and explained; answer pending.
⚠️ **Items 6 and 7 are CLOSED**, settled 2026-09-10 on the owner's own words verified from the source transcript
(`type: user`, `isMeta` unset, with uuid and timestamp) rather than from a relay, and written into the contract at
`604bef7` + `75bdc69`. They are recorded there, not here. Item 8 stays open and is deliberately non-operative.

8. **What are "the two numbers" on geometry?** The band has an extent, a top switch line and a count; the box has
   bands at both ends. The contract now carries the likely reading — the box's outer edges, top and bottom, per
   field, against where the switch band puts the picture's bounds — **marked as an inference and explicitly NOT an
   operative acquisition test**, because the owner's words it comes from (uuid 1bd1fc1d) are a question he asked the
   harness, not a definition. What is missing: which bottom is meant (picture bottom, switch line, or recorded
   edge), and what "line up" is as an equation. One line from him replaces it. Nothing is blocked on it.
9. **The switch-line count has no seed the contract authorizes.** With the top at line 23 the offset can only be
   read as count − extent, and the count comes from the confirmed unit, which needs geometry. The engine already
   assumes d = 0 at acquisition so count = extent (`field_registration.c:436`), which resolves it in practice and
   is nowhere in the contract; rule 4 wants the acquisition's geometry to be an observation, not an assumption.
   (Both agents agree this does NOT explain capture 1's zero locks — that is still open.)

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
