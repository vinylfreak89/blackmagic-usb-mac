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

**→ The 1,013 of 1,013 result and the 963 → 1,009 → 1,012 → 1,013 progression now live in CLAUDE.md §14, with
their two limits. The extreme-value pattern behind the fixes, and the census-ceiling finding, are in
LEARNINGS.md. This file keeps only what is still open.**

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

**CHARACTERISED on raw rows, 2026-09-10 — one shape, not several (description only; no rule was written).**
Sampled 13 across the class, both fields, counters 6674 to 7172. In every one the disputed line (the harness's
`T`) is ordinary picture and `S` carries the relocated blanking:

| | disputed line | line `S` |
|---|---|---|
| longest blank-level run | 1, 2, 2, 3, 3, 4, 4, 5, 8, 9, 9, 21, 27 | 100, 108, 110, 140, 140, 144, 150, 156, 157, 157, 158, 159, 160 |
| profile | full content in every bin, no blanking structure | blanking at the start |

It holds in dark scenes (means 22–27) and bright ones (79–112) alike, so the class is ONE fault with ONE shape
and the engine is right on all 13 sampled. That is worth knowing on its own: nobody should go looking for
several rules.

⚠️ **The discriminator this shape suggests is ALREADY FALSIFIED — the measurement and the reason are recorded
in CLAUDE.md §14 as a ruled-out route, because it is the first thing a future pass will try.** Short form: net
−186, and low blank-run is a property both populations share. **What remains OPEN here is only that the
separating observable is unknown**; no candidate was written, deliberately.

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

⚠️ **"Two nested causes" and "the 42 are the tractable half" are BOTH WRONG — Codex's cross-tab, 2026-09-10.**
The counts reproduce exactly, but they are not separate physical causes: **33 of the 42 are edge-connected even
with tolerance**, and 36 of the 205 short runs start inside the window.

| longest-run result | starts 0 | starts 1–2 | starts ≥3 | total |
|---|---:|---:|---:|---:|
| under 147 even with tolerance | 169 | 15 | 21 | 205 |
| reaches 147 with tolerance, not exact membership | **33** | 4 | 5 | 42 |
| reaches 147 with exact membership | 8 | 0 | 0 | 8 |

Only **9** of the 42 offer two exposed endpoints, so the "tractable half" is at most 9 readings, not 42. The error
was treating start position and run length as independent partitions because they had been measured separately —
the same fault as the three hypotheses above, one level up: no cross-tabulation.

**The tolerance ablation recovers 9 candidates and 0 readings**, and the broader variant raises whole-capture
observation disagreements from 6 to 19. Codex declines to promote either variant and that is the right call. Its
controls held throughout: 34/34 in every variant, plus 0 false positives across ten new scattered-code negatives
including stationary interior AND edge-connected black rectangles. So tolerance is not unsafe — it simply does
not help.

⚠️ Codex's qualifier, carried unrounded: **"This does not establish fundamental unmeasurability."** A start of
zero records censoring or edge connection, NOT proof that those samples are physically blanking rather than dark
content.

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

**OPEN — four gaps between the owner's 2026-09-10 rule-8 ruling and the code, reported to him 2026-09-10.**
His ruling: the bounds are the head switch's; the switch point disappearing after acquisition does not move the
top line; the hold's test is the count of switch lines OTHER THAN the partial line; from no bounds a valid switch
geometry acquires them (measured horizontal skew and/or the partial line, ± the RF peak); and the count MAY
EXPAND where the partial was not present from the beginning.

1. **Both instruments count the partial line, his test excludes it.** Engine:
   `observed_switch_line_count = band_extent + visible_d` (`field_registration.c:475`). Harness:
   `n_sw = clip - T + 1` with `T = sw-1 if partial` (`switch_geometry.py:524,526`).
   **Measured on capture 1** — a partial is present in 87.6% of field-1 and 90.9% of field-2 readings, so it is
   the norm rather than an exception:

   | | including the partial (both instruments) | excluding it (his test) |
   |---|---|---|
   | field 1 | 3×470, 2×29, 4×9 — 38 off the mode | 2×465, 3×43 — **43 off** |
   | field 2 | 4×443, 3×62 — 62 off the mode | 3×489, 2×16 — **16 off** |

   Across the capture his test roughly halves the hold-invalidating events, 100 → 59 — but that is entirely
   field 2. Field 1 goes the other way, 38 → 43.
   **WHY field 1 worsens, measured 2026-09-10 — his rule is EXPOSING a harness fault, not causing one.** Of the
   43 field-1 readings off-mode under his rule, **34 have no partial line detected** and 9 have one. A field-1
   reading with no partial is **54%** likely to be off-mode; one with a partial is **2.0%** — a 27× difference.
   Field 2 has **zero** of its 46 no-partial readings off-mode.
   The arithmetic: with no partial detected every switched line counts, so the tally runs one higher than when a
   partial is excluded. Field 2's no-partial readings all place the switch on the same line and stay consistent;
   **field 1's split roughly half-and-half between two lines, and the suspect half places the switch one line
   HIGHER — exactly where an undetected partial would put it.**
   ⚠️⚠️ **CONFIRMED BY THE OWNER FROM THE IMAGES, and it is worse than missed detection — the harness both
   MISSES and INVENTS half-and-half lines, and the discriminator is BRIGHTNESS** (owner, 2026-09-10, shown eight
   greyscale renders of NTSC lines 255–262 and asked nothing else: "Pictures 1-6 … all look like they have half
   lines to me. They are the 6 where luma is darker over all. 7 and 8 do not appear to have half lines. Are you
   sure there are only 2 controls").
   His discriminator measured across the whole capture — field body brightness against what the harness reported:

   | | readings | median brightness |
   |---|---:|---:|
   | field 1, half-and-half line reported | 445 | 107.6 |
   | field 1, none reported | 63 | **56.7** |
   | field 2, half-and-half line reported | 459 | 108.3 |
   | field 2, none reported | 46 | **55.5** |

   The no-half-line readings are **half as bright**, 51 and 53 luma darker at the median, in both fields
   independently. **A level dependency in a test that is meant to be level-independent.**
   **And the opposite error is real too, which nobody had raised.** On counters 7012 and 7174 the harness reported
   a half-and-half line at line 260 and placed the switch at 261 because of it. Line 260 carries NO black gap
   anywhere across its width there — 55–108 and 59–130 across all 24 measured steps, widest gap 3 samples — while
   line 261 drops to 1.4 with a gap 144 wide. The switch falls cleanly between the two and no line is
   half-and-half. **The harness invented one.**
   ⚠️ So the cause is a brightness-dependent partial test: MISSING them on dark fields and INVENTING them on
   bright ones. Not a defect in the owner's rule. And it rests
   on the one quantity nothing has independently verified: the census validated the fully-switched line, never the
   partial identification (Codex's caveat, same day). Confirming it needs raw rows on those 34, which is the
   parked partial-row question.
2. **Expansion is flagged as a conflict.** `field_registration.c:924-930` sets `switch_count_conflict` on ANY
   difference from the frozen count; he says expansion is accepted where the partial was not there from the start.
3. **Nothing re-acquires.** A count conflict is reported and the lock stands. His ruling makes the hold invalid
   and requires the switch geometry's bounds to be re-acquired.
4. **The acquisition routes he named do not exist** — but the framing below is corrected twice by Codex, and
   both corrections matter. Neither the comb site (`:665`) nor the caption site (`:920`) implements
   head-switch-bound acquisition or the head-switch confirmation route his ruling names. The RF peak is indeed
   absent (`rf_peak_line` / `rf_peak_position` declared, initialised to −1, never assigned — A20), **but it is
   OPTIONAL under his ruling** ("with or without the RF peak"), so its absence is not itself the gap.
   ⚠️ **Claude wrote "the engine acquires at one site". There are TWO** — the comb path at `:665` and the caption
   path at `:920`. This is the identical error already recorded in `LEARNINGS.md` ("There is exactly one
   lock-acquisition site and it requires a caption" — there are two), made a second time from the same kind of
   partial read, with only the line number moved.
   ⚠️ **And acquiring SWITCH BOUNDS is not the same as acquiring a SOURCE LOCK** (Codex, 2026-09-10). His ruling
   is about the switch geometry's bounds. A source lock still requires geometry plus another observation, per §3.
   Conflating the two would let a bounds acquisition manufacture a lock, which no ruling licenses.

## Pile A — the cold reads' wording findings (both readers)

Two frozen cold reads exist and they are **not** the post-freeze pair the owner's sequencing calls
for. Mine reviewed `4eed79e` (36 findings), Codex's reviewed `fb4d7bb` (13, prefixed CR). Both are
INPUT to pile A; the freeze-then-both-read run is still owed and neither agent has done it.
Both readers report PARTIAL isolation (repository instructions inherited); neither claims more.

**Closed 2026-09-10, each by a landed edit with a guard probe:**

| finding | what it was | closed by |
|---|---|---|
| 12 | two live coordinate systems | `91ac8db`, `77a6711` — table rebuilt on one field-relative line column |
| CR-01 | the table classified three written rows as source | `77a6711` — measured per row; §1's line account was right |
| CR-07 | the line account silently required clip = 262 | `496afb9` — `P = C − 22 − N`, both identities |
| 30 | "picture rows" called a per-source constant | `496afb9` — `P` is per-FIELD by construction |
| 5 | box bars both do and do not recentre | `c9552ee` — half was stale; Crop clause repaired |
| CR-12 | box invalidation fired on ordinary box content | `c9552ee` — scoped to a previously identified bar region |

**Pile A from Claude's reader is closed, dispositioned, or with the owner (2026-09-10).** Landed since the table
above: 19, 20, 22 (`960b5ff`), 8, 11 (`0942d8b`), 25, 28 (`ab1b711`), 23, 32, 35, 36 (`1ff7482`). Dispositioned
without editing the frozen report: 24, 27, 29, and 11's withdrawn attribution. Audited rather than defined: 34
(`docs/reports/2026-09-10_terminology_audit.md`). With the owner: 6/CR-10, 7, 24.

**Of Codex's 13, all worked (2026-09-10/11):** CR-01, CR-02, CR-05, CR-06, CR-07, CR-09, CR-12 and CR-13 landed;
CR-03, CR-04 and CR-11 landed after Codex reopened them; **CR-08 verified closed** (the rebuilding-order conflict is
repaired — references are qualified before supporting reacquisition); CR-10 is with the owner.

⚠️ **FOUR of the five I had treated as "closed by overlap" were NOT closed**, and Codex named the surviving text in
each. I had flagged that disposition as a judgement rather than a verified before/after; it was wrong, and the
lesson is in CLAUDE.md — a labelled guess in a tracker is still read as a status by whoever plans from it.

⚠️ **Codex has NOT signed off on the file.** Its exact words: "review the actual resulting diff before freezing;
this response is not sign-off on an unwritten version." The diff is `869d34f..HEAD` for the last five items and
`8d389ab..HEAD` for the day (244 insertions, 70 deletions); it is with Codex now. **Nothing is frozen, and my
reader is dispatched only after Codex freezes**, per the owner's sequencing.

**Engine work CR-06 and the terminology audit put on Codex's side:** rule 9 says the comb is not measured under a
maintained lock; `field_registration.c:984` calls `comb_confirm` UNCONDITIONALLY on every unit, with no lock-state
guard. So that rule is required behaviour the engine does not implement, and `comb_safe`'s repair is an execution-path
change as well as a record/schema one.

**Engineering work the terminology audit produced, none of it the owner's:**
- `comb_safe` conflates "evaluated and disagreed" with "never evaluated", and rule 9 makes the second the ordinary
  case under a maintained lock. §8 burns it into the review overlay. Engine state, so Codex's.
- "lift-off point" — 8c's hold criterion rests on an absence nothing defines or implements.
- "band event" — gates a report in §1, zero hits in `src/`.
- "static, detailed picture", "jump further than expected", "near an edge" — missing empirical qualification;
  must NOT be closed by fitting a threshold.

**Codex's comparison disputes five of my reader's inferences** (findings 2, 9, 13, 16, 24) — mostly
that a missing method is not a proof of impossibility. Queued, neither conceded nor contested.

**A defect found while working the above, not from either reader:** rule 4 says its earlier wording
"is kept in the quotation that follows as history" and **there is no following quotation**; the
phrase appears nowhere else in the document. Raised with Codex; restoring or dropping it is a
guess about intent, so it needs agreement.

## Harness coordinate migration — NOT to be done yet

`experiments/coordinate_audit.py` lists the harness scripts that still convert rows to lines by
adding 4, the withdrawn convention (wrong for every row of field 2 and for field 1's rows 259 and
522-524). **15 of 54.** CLAUDE.md §14 forbids flipping the harness before the writer/schema
migration and coordinated handoff, because both agents compare exports. Until then the contract's
§1 says field-relative and the harness CSVs and panels say frame-continuous, so **no harness line
number may be quoted as field-relative**. `experiments/field_lines_py.py` is the tested mirror to
migrate onto; `field_lines_py_test.py` compiles `field_lines.h` and compares all 525 rows.

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
| A23 | The contract's second reading of `d`, count minus extent, is not implemented — `geometry_d = top - origin` (`:792`) is the only one. On capture 1 the top reads 23/286 in every stable unit, so the implemented reading is degenerate there and the informative one is absent | contract rule 3 | not implemented; **tier 2** |
| A18 | ✅ **ANSWERED 2026-09-10 — this item's owner-policy blocker is lifted; the engine work is outstanding.** A source lock never requires head-switch evidence; the head switch is an input to the geometry rather than a confirmation; the both-fields rule is source VALIDITY and fires only on positively established asymmetry, never on abstention. The characterisation below was also wrong before it was answered: the contract at HEAD already carried the conditional (`ca47a1c` amended it), so the engine trailed the contract rather than implementing it faithfully — and the two gates are not identical, the comb path requiring a measurable switch in both fields and the caption path one in the field being acquired. Removing this blocker does not remove every independent tier-1 gate. Original text: **BOTH acquisition sites require a measurable switch on both fields** (`field_registration.c:601–602` for the comb path, `:834` for the caption path), so no source lacking one can lock — boxed pictures, where rule 8 forbids measuring it, and line-TBC-corrected passes, where the owner says there is none. **This is not an engine defect: the contract's Source lock definition requires it in the owner's own words** ("at a unit whose switch line and band are measurable"). The contract contradicts itself and neither agent may resolve it | contract §3 Source lock against §2 and rule 8 | ✅ **ANSWERED 2026-09-10; this item's owner-policy blocker is lifted.** The engine still requires the switch at both acquisition sites, so the implementation is outstanding. Other tier-1 gates are unaffected by this item closing |
| A19 | The band is not held when the switch is undetectable: absent detection must hold the band, invalidated only when the line count below the head switch changes | contract rule 4 | not implemented; **tier 1** |
| A20 | **RF-peak confirmation is unimplemented** — there is no detector at all (`field_registration.c:344` initialises both peak fields to −1 and nothing assigns them; `measure_switch:186` uses displaced blanking intervals, not the peak). Claude's "the detector assumes one polarity" was wrong: it tests neither polarity. The record's `f*_rf_peak_line/position` columns are therefore always −1. Building one needs local-departure evidence that separates a genuine peak from an ordinary picture edge, with goldens for BOTH polarities — the owner's black-polarity observation stands and has not been searched for | contract §2 | not built; switch-detector coverage on the non-boxed units |
| A24 | ⚠️ **PARTLY ANSWERED 2026-09-10; still tier 1.** The invalidation condition is given (picture positively established within the held bounds) and the validity bounds are in the contract (extent measured while well exposed and HELD; a fade never invalidates; a band edge moving while the level is steady releases). **"Must open up to the full picture" below is WRONG** — owner, 2026-09-10: "no it doesn't need to open up to a full picture. it can open up to whatever is on the screen. but it must be bounded." What remains is detector work, not policy: qualifying "well exposed", measuring the fade, and telling genuine picture entering the bounds from exposure-dependent detectability. Original text: A box is not invariant — when the mask changes the geometry must open up to the full picture. The box needs defined bounds for where it is valid and where it is invalidated, and it lives through the fade, which is measured rather than treated as noise | contract rule 8 (wording owed) | **policy answered 2026-09-10 and in the contract; the detectors are not built — tier 1.** Outstanding: qualifying "well exposed", measuring the fade, and telling genuine picture entering the bounds from exposure-dependent detectability |

## B. Harness (Claude writes, Codex reviews)

| # | item | where it is written down | state |
|---|---|---|---|
| B1 | The four references, one commit each, in the acceptance order — **1 of 4 done** | contract §8; `experiments/geometry_oracle/REFERENCE_SPEC.md` states every column's raw-row derivation | PARTLY — capture 1 only. Its reference is built and its invariant CHECKED: 0 violations (`stable_interval_check.py`, 508 units from counter 6667, both fields measurable in all 508). Captures 2, 3 and 4 not started — they follow capture 1's acceptance |
| B6 | Horizontal-timing instrument for the owner's line-TBC mechanism | measurements belong in CLAUDE.md and are NOT yet written there | ran. **Within-capture: NULL** — field-1 jitter does not predict which units misregister (Cohen d −0.14 and +0.23, both opposite to the prediction). **Switch band: TBC-off is 27% rougher** (2.765 against 2.180), where the field body showed no difference at all (2.013/2.006) — the setting acting where it is documented to act. ⚠️ The null is not a refutation: the instrument measures the TBC's OUTPUT, downstream of the correction. **Capture 1 is unmeasurable by it and loosening the gate does not fix it** — the edge-peak gate trades validity for coverage: at 6.0, 453 of 920 units and the located edge sits at 9.45 samples where NTSC geometry predicts ~9; at 3.0, 752 units but the edge drifts to 7.44; at 1.5, 917 units at 7.02 with 583 outside a plausible 8–12. Lower gates are finding noise peaks, not line starts. Low-contrast material needs a different edge estimator, NOT a looser threshold |
| B7 | Box detection across the four captures | `experiments/box_census.py`, `experiments/box_panel.py` | census done, title-graphic false positive rejected, and the integer-denominator qualification is now understood and worked around (the threshold is a fraction of the field's own structured level, so the fade no longer moves the band). Remaining: per-row `h` overlaps far more than the region statistic suggested, so it is the band STRUCTURE — a run anchored at the field edge, in both fields, with sustained content between — carrying the census, not the per-row threshold |
| B3 | The render changes | contract §8 | PARTLY: capture 1 renders end to end at `1d66719` — 919 units, 720×486, colour, band below the picture, band edges as margin ticks, running line, audio in sync to 8 ms. Remaining against §8: the 525-line raster panel beside the picture; the graph traces d1/d2 but not the band's two edges per field; the machine read-back is not run over it; the identity-strip label overlaps the strip. The band also lacks gauge line and decoded bytes, geometry `d`, clip line, the conservation equation and `comb_safe` — all present in the record — and pedestal, the line-22 level with its comparator count and the horizontal phase, which the engine does not emit at all |
| B4 | The acceptance runs | contract §8 | blocked on B1 and the engine |

## ⚠️ THE PROFILING STOP IS NOT NEXT — its second precondition is not met (corrected 2026-09-11)

The owner's gate, verbatim (2026-09-10T08:22:59Z): *"once this is done and once **the engine and harness agree
semantically** HARD STOP before moving forward on anything until the entirety of the live engine is profiled. I'm
not asking for optimizations. I'm asking for profiling numbers."* And: *"I told you to finish getting what we
discussed in, then profile."*

⚠️ **Provenance of the two halves, kept apart.** The owner's words above reached this session as a RELAY from a
peer session that read them in a transcript; they are not owner input to this session and were not verified here.
**What IS verified from this repository is the part that decides the sequencing**: CLAUDE.md:2510 and the six keys
below. So the correction does not rest on the relay — even without the quote, the project's own record says the
agreement condition is open.

**Two preconditions, and the second is neither pile A nor the cold reads.** "The engine and harness agree
semantically" is Track 1's agreement condition, and **CLAUDE.md:2510 records in its own words that it is NOT
closed.** This session had been treating profiling as the next item; that was wrong, and the error came from
carrying the gate without its precondition.

**What actually holds it open: six T disagreements**, all on capture 1, all the same shape — the phase reader says
T = S (no partial line), the run reader says T = S − 1 (the row above S is partial). All six agree on S.
`src/field_registration/tests/RUN_TIMING.md:88`:

| counter / field | phase T/S | run T/S |
|---|---|---|
| 6681 / 1 | 260/260 | 259/260 |
| 6700 / 1 | 261/261 | 260/261 |
| 6704 / 2 | 524/524 | 523/524 |
| 6722 / 1 | 260/260 | 259/260 |
| 6749 / 1 | 261/261 | 260/261 |
| 6785 / 1 | 261/261 | 260/261 |

Contract §2 adjudicated that the partial line IS the switch line, so which reader is right decides T, and T feeds
the line account. `experiments/t_adjudication.py` prints the raw rows for all six with both readers' own
quantities side by side — the looking step CLAUDE.md requires before any edge claim. **It computes no verdict:
this is a two-agent adjudication.**

**The profiling scope work already done is not wasted and is not the gate opening.** That the live path carries no
instruments, that the bench's gate is vacuous, and that no recorded timing states its load are findings about the
profiling stop that stand whenever it opens.

## Owner rulings 2026-09-10, reconciled from the transcript (watchdog, one-time owner-authorised edit)

**Why this section exists.** The watchdog's own queues lost items and its audit method was a phrase search, which
reports a ruling as "recorded nowhere" when the wording differs and cannot tell a CONFLICT from a SILENCE. The
owner authorised one override to reconcile everything discussed on 2026-09-10 into this file. Every row is his
words with the timestamp; status is what a re-check by MEANING found, not by phrase.

| # | his words (2026-09-10) | status |
|---|---|---|
| 1 | 10:20:30 — "when a source is locked, then its geometry is known, **comb should not need to run**... so comb should not be an all the time running thing" | **OPEN** — the engine measures the comb on every unit; `field_registration.c:984` calls `comb_confirm` with no lock-state guard. Rule 9 already states the requirement. |
| 2 | 17:06 — "fix the fucking combing... a regular simple comb energy algo... there doesn't need to be a mask or other garbage" | **IN FLIGHT** (Codex `bzxtaxua7`) |
| 3 | 17:08 — "settle the S and T... get the measurement of the head switch band right" | OPEN |
| 4 | 17:2x — "**the only render I want is one that is produced from a locked capture on cap 1**. then it may continue on by profiling" | OPEN — sets the order: comb → lock → render → profile |
| 5 | 16:13 — "your understanding of rule 8c is correct. close it. **yes of course it may feed `d`**" | LANDED (8c's OPEN marker is gone) |
| 6 | 16:13 — "**a peak or partial line is a head switch full and valid. head switch may only be 1 line**" | OPEN — contract ~:809 still excludes them; he ruled at 16:15 "if it does the contract is wrong" |
| 7 | 16:13 — "**the lines own horizontal blanking is the thing that compares it to**. thats the answer to your absensce part" | OPEN — `:812` still reads `OPEN, and with the owner` |
| 8 | 16:16/16:17 — "the whole lock gets reset... **it throws away nothing. it maintains nothing. the whole engine shouldn't run** because that is an invariant that isn't valid NTSC" | OPEN — `:800` still reads `UNSETTLED and with the owner` |
| 9 | 16:13 — "line 21 being at line 21 on both and line 22 being blank on both... **in other words a valid VBI**" | OPEN — `:1027` still reads `OPEN, and with the owner` |
| 10 | 16:13 — "**for the 480 render it never renders. yes the 486 render obviously always renders** either the shuttles or the tapes 20-22" | OPEN |
| 11 | 16:13 — "**the comb is only to maintain the lock**... if it means X lines are missing because they are in the regenerated blanking... **rendered as black**... the proper 20-22 **placed on top of that in a 486 render**... exception is if 22 shifts below the real 22 and contains real picture... **if we actually determine real picture lines are gone, they should be blanked out**" | OPEN |
| 12 | 09:16:24 — "in any 486 line renders, **real line 20-22 overwrite the shuttles**" | **OPEN AND IN CONFLICT** with `:451`, which says nothing the tape carries above line 23 reaches us. A conflict, not a silence. |
| 13 | 09:18:05 — "for the test renders... **a valid result should keep the first 6 lines vertically stable in position... always**" | **PARTIAL** — `:167` carries "the output picture does not move", a different observable. No render shown to him today was measured against this. |
| 14 | 11:13:09 — "it should **draw the bounding box** when it finds it on top of the picture. keeping its field colors... **purple**... **transparentish**" | OPEN (implemented per the harness, not yet in the contract) |
| 15 | 04:54:51 — "luma stills... **slowed down 5x as a video, both fields side by side**" | **FALLBACK ONLY** — condition: if the peak-near-the-left-edge account fails to explain the switch line appearing to jump to 259. Superseded in practice by the temporal frame. |
| 16 | 11:05:15 — "if they get `0x0800` or lose the regenerated lines, **they go get it again**" | OPEN |
| 17 | 12:50:38 B4 — "isn't that **determined from source and/or device and/or horizontal blanking**" | OPEN |
| 18 | 12:50:38 B5 — "It depends how it falls off. If the horizontally mistimed field is **within normal variance** defined elsewhere that we've already agreed to" | OPEN |
| 19 | 12:50:38 B6 — "**the harness has a test and definition for what boxed vs structured vs unbounded is**" | OPEN |
| 20 | 17:0x — "**its not categorical. its an expectation**... its what I saw quickly scrubbing the video but I generally did see occasional half timed lines" | OPEN — §2 records his EXPECTATION as a measurement. Fix the provenance, not the strength; Codex's 11-vs-1,957 is the measurement and the eleven are corroborated by his own viewing. |
| 21 | 17:00 — "**THESE ARE NOT PICTURES. They are representations of a signal across time**, thats why a .5 row never made sense to me... its half of a horizontal one"; 17:00:57 — "the ribbon is actually **the sweep moving back into its own horizontal blanking interval**" | OPEN — the frame the definitions sit inside; not in the contract |
| 22 | 17:02 — "**the RF peak is the liftoff**... the skew is because the servo is trying to lock timing of this frame to the other head... **its some of the other fields signal ending up timed to this field**"; 17:0x — "which is why **the peak disappears in the line TBC on captures (mostly)**... fixture A... **their recorded timing was trash**" | OPEN — competing account (phase step introduced by the TBC rather than head geometry) is separated by the V-stabilize A/B, already captured |
| 23 | 16:58 — "**well the TOP skew row is**" (T) | OPEN — and the DOWNWARD reading of it was the watchdog's invention: measured, a downward scan agrees with the engine's T 0% of the time, landing ~236 rows high; the upward run reaching the clip gets 71.5% exact |
| 24 | 11:02:49 — "it needs to decide on **the black reference**" | **SATISFIED** under different wording: contract's *Source-measured levels*. Recorded because the watchdog reported it open on a phrase search. |
| 25 | 09:41:23 — "**the location of the partial line and/or RF peak should not jump**. It should have a normal excursion when a line disappears" | **LANDED** `:164` |
| 26 | 10:49:16 — "**a head switch existing is the bottom of the tape. thats PHYSICS**" | **LANDED** `:446`/`:702`/`:960` |

**⚠️ RETRACTED, and it must not be quoted again once the comb work clears (owner, 2026-09-10):** the claim that
`switch_measurable` gating acquisition "excludes capture 1's best evidence" because all 182 gate-open units are card
units. His ruling: *"the comb does not need a switch to open. it is one of the ORs. the contract directly
contradicts this. the switch sets or fixes geometry only IF IT IS PRESENT. secondly, the target measurements are old
and stale and because it didn't know how to measure a headswitch, shouldn't be true."* The 182 figure was produced by
a switch measurer since shown to be measuring the wrong thing, and an independent measurement on the same capture
finds displaced blanking in 222 of 240 programme field-readings. The `switch_measurable` condition on the two
acquisition sites is a code defect against rule 9, not a constraint to design around.

**The profiling stop, four items** (its second precondition — engine and harness agreeing semantically — is not met;
see the section below): the live path carries NO timing instruments (zero `clock_gettime`/`mach_absolute_time` in
`frameserver.c`, `frame_publisher.c`, `audio_publisher.c`, `unit_parser.c`, `field_registration.c`,
`signal_state.c`); `make bench`, named in §11b as the regression gate, reports `registration_calls 0, gated 10000`
and cannot fail the budget however slow registration becomes; no ms/unit figure on record is comparable to §11b's
"reference M3 P-core, single-threaded" (all taken under unrecorded load, measured at 4.5-6.75 with Chrome at 97%);
and three decisions are with the owner — scope (per-stage or worker total), fixture (194 looped units or a real
slice), host (quiesce before the real run).

## Blocked on the owner

### ⚠️ WITHDRAWN — the ":531 tension" was my seventh fixed-place-to-look defect, not a rule/source conflict

Owner: **"LINES ARE TEMPORAL NOT SPATIAL. of course if you measure across the row and average you aren't going to
find it."**

I reported that contract `:531`'s named reference — the source's own blanking on its good picture lines — is
"often unmeasurable on capture 1", and put it on his list as a conflict between a rule and a source. **It is
neither. The reference is there on essentially every row; I was looking in a fixed place instead of at each row's
own instant.**

**Verified independently, capture 1 bright programme (6960-6969), 1,010 mid-picture rows of field 1**, finding each
row's transition as its own steepest fall and reading after it:

| | value |
|---|---|
| rows examined | 1,010 |
| rows with no sample at the device level after their transition | **32 (3.2%)** |
| the SOURCE's own blanking | mean **1.410**, sd **0.492** |
| the DEVICE's fill | mean 1.3808, sd 0.0058 |
| each row's transition | median sample **716**, p10 715, p90 718 |

**The reference exists on 978 of 1,010 rows**, where my fixed-window hunt returned 51.97 — picture. And the
transition sits within a **three-sample** spread across rows, so it is a common slew rather than many rows
transitioning at different times.
⚠️ Two honest differences from the relayed version: it reported **0** rows without a usable sample and I measure
**32**, and it reported the level at 1.540 where I measure **1.410**. Both are above the device fill; CLAUDE.md's
recorded range for this quantity is 1.459-1.53, so mine sits a little below it and the relay's a little above.
Different transition-finders, same conclusion — but "essentially every row", not "every row".

**Consequences:**
1. **The `:531` item comes OFF his list.** There is nothing to reconcile and nothing to send Codex as a conflict.
2. **Every number taken tonight against the DEVICE's fill should be re-taken against the source's own blanking**,
   read per row at its own transition — my threshold tables included. The mean-versus-median ruling is unaffected:
   it concerns the statistic, not the reference, and the engine already computes the mean.
3. ⚠️ **A real measurement caveat, not a contract one:** on bright content only one or two samples per row sit at
   blanking after the transition, so a single row gives a reference of sd **0.492** against the device fill's
   **0.0058** — about eighty times noisier. If a tighter per-unit reference is needed, accumulate **across rows at
   each row's own instant**, which is not the same as averaging a fixed column range and is exactly the
   distinction that broke both attempts.

⚠️ **This is the SEVENTH instance of one defect tonight**, and the count is the finding: a positive-only sign
filter, a fixed 48-sample ramp window, a boundary search bounded to `b0 − 60`, a fixed row for 6(b), a hardcoded
column 706, a window from 580, and now a fixed window for the blanking reference. Every one reached for **a place
to look** instead of letting the signal's own timing say when.

### :1027 and :451 ANSWERED — and :451 was never a contract contradiction. My error, verified.

**:1027 — caption-only acquisition.** His words: *"D1 - combing. yes a lock may exist without combing. but it is
still registered once and then held. it is an adjustment to geometry. remember the rule is geometry and one or more
other signal"*. Three things, the third general: a lock MAY exist without the comb; the comb is **registered once
and held**, an adjustment to geometry rather than a per-unit input; and the acquisition rule is **geometry AND one
or more other signal** — which one is not fixed, none is mandatory.
**Checked in the code, and what landed already implements it:** `comb_zero_candidate` is ENGINE state (`e->`), set
once at `field_registration.c:597` during acquisition and read at `:641` to set `out->parity_bias` whenever
`parity_state == CALIBRATED`. So the result genuinely persists as a held adjustment — it is not merely "not
evaluated" under a maintained lock, which is a different and weaker thing. Codex's `2a06c9e` gating plus this
persistence is D1's structure. **Only the WORDING is owed**: it must say registered-once-and-held rather than
leaving it to be re-derived from two code paths.

⚠️ **:451 — I PUT A CONTRADICTION ON HIS LIST THAT DOES NOT EXIST.** His answer: *"D3 - that contradiction is true
in the normal non displaced V-Sync. if V-Sync is displaced, yes the tapes real content reaches us because it
appears N lines below where the shuttles insert is"*.
**And the contract already says exactly that — in `:451`'s OWN NEXT SENTENCE**, which I did not read:

> "Nothing the tape carries above line 23 reaches us except the re-encoded bytes on the insert. **The tape's own
> VBI becomes visible only when the field is displaced downward: at +1 its black line 22 appears on line 23 (luma
> 4–7 on fixture A), at +2 its line 21 on 23, at +3 its line 20 on 23 and its line 21 on 24.**"

So there was never a conflict inside the contract. The conflict was between his UNQUALIFIED instruction and
`:451`'s first sentence **read alone** — and CLAUDE.md already names this defect class, in its inverse form:
sentences that read correctly alone and mislead together. Here I read one alone and manufactured a contradiction
its neighbour resolves. **This item comes OFF his morning list.**
**Where the repair actually belongs: the RENDER rule, not `:451`.** The 486 overwrite is CONDITIONAL ON A MEASURED
DISPLACEMENT, and at d = 0 there is nothing to overwrite with.

### :812 ANSWERED — fail closed. Implementation status of its four clauses, checked in the code

> "then if you can't record a head switch or other valid picture, then it is an NTSC destroying signal and the
> registration does not run (preserving its timing only but recording no decisions and setting no levels)"

⚠️ **The conjunction is the trap and it must survive into the contract text: BOTH must fail** — no head switch
recordable AND no other valid picture recordable. **An unresolved head switch with valid picture present is NOT
this condition.** Reading it as "unresolved switch ⇒ invalid raster" is the one-name-two-quantities defect this
project keeps hitting, and it would fire the reset on ordinary units.

**Clause 4 — "setting no levels" — is the one with the sharpest consequence, and it is ALREADY SATISFIED BY
CONSTRUCTION in the engine as written.** A poisoned level reference would be silent: every later measurement is
made against it and nothing downstream would show the corruption. Checked:
`field_registration.c:359-366` computes `blank_mean` into the per-call **measurement** struct from that unit's own
blanking rows, and divides. **There is no cross-unit level accumulation in engine state to poison** — the only
carried per-field value that is level-adjacent is `body_reference_top` (`:799`), and that is a POSITION, not a
level. So clause 4 needs no new mechanism, only a test that keeps it true.

⚠️ **Clause 3 — "recording no decisions" — is NOT satisfied, and the site is specific.** `:831` sets
`state->previous_measured_top = measurement->top` inside the geometry-placement branch. That is the engine's
temporal witness, carried to the next unit and read at `:915-916` to decide whether the top moved. **A unit that
runs the geometry path on an NTSC-destroying raster writes that witness**, so the next unit's "did the top move"
test is taken against a raster the ruling says the engine should not have operated on. It is not a logged decision
in the sidecar sense, but it is state a later decision is made from, which is what clause 3 exists to prevent.
The three exits at `:836`, `:842` and `:660` already set it to −1, so the mechanism for not writing it exists and
the new condition needs to reach one of them.

**Clause 2 — "preserving its timing only" — must not be conflated with dropping the unit.** Counter continuity,
PTS and the audio correlation are untouched; the transport record stays complete. This project has already been
bitten by the inverse (a gated unit publishing a held crop that scored as if applied), so the record must
distinguish *not run* from *ran and produced nothing* from *absent*.

**Contract work:** `:812`'s fail-open sentence — "Failure to identify a landmark or a region does not establish
absence; unresolved evidence remains Unknown" — is now wrong for this case and must be REPLACED, not amended
beside. The marker comes off. Check what the document says about unresolved switch evidence everywhere it says
anything, and make its answer unique.

### ⚠️ WITHDRAWN — the 6(b) "wrong line" proposal below is MY MISREADING, not a defect in his rule

Owner, 2026-09-11: *"AGAIN.... as I've said many times. the line 22 is when the tape's line 22 wanders into the
image... NOT the regenerated line 22. of course thats going to always be stable... thats another well no fucking
duh"*.

**"The tape's line 22" names AN OBJECT CARRIED ON THE TAPE, not a raster position.** I measured RASTER line 22 —
which the device writes unconditionally — found it stable across 1,092 readings, and reported that as a correction
to his rule. It is not a correction; it is the thing he calls obvious.

**The finding is WITHDRAWN, not renumbered.** 6(b) should NOT read "line 23 / 286", and NOT "the first
pass-through position" either: **both still name a fixed place to look**, which is the same defect one level down
and **the third instance in this thread** — a fixed window for the ramp, a bounded search for the boundary, now a
fixed row for the VBI test. His rule needs no line-number amendment from me.

**What the test actually is:** does a row bearing the TAPE'S OWN blanking — identified as the tape's by being
discrete from the device's — appear ANYWHERE INSIDE THE PICTURE? Its position is not a parameter of the test.
**Its position IS THE READOUT: where it lands is the displacement.** That is why he wrote it as proof positive that
the tape's geometry CHANGED rather than as a row to inspect.

⚠️ **A second, separate defect in the same measurement**, worth keeping distinct from the misreading: averaging
raster line 23 across units gives +42.21 on fixture A at row sd 47.08. **That is PICTURE, not the tape's blanking**,
which CLAUDE.md puts at Y 4–7. If the tape's line 22 enters the image in only some units, a per-unit average is
dominated by the units where it does not. The census measures the mean level of a raster row where the test is the
per-unit PRESENCE of an identified object.

**What survives and is worth keeping: the noise-character discriminator.** Device-written rows carry sd 0.48,
source-carried rows 2.24–47.08 — a 4× to 98× separation in character alone, per unit, with no level typed in. That
is a sound answer to "is this row the device's or the tape's", which is exactly the identification step the real
test needs. Keep the instrument; drop the fixed row it was pointed at.

The superseded proposal is kept below because the method is what was wrong, and its raster measurements are still
correct measurements of the raster.

### PROPOSAL — the coherence ruling's 6(b) names the wrong line, and the contract already says why

His coherence ruling (2026-09-11) gives one exception to the hold: the tape's own vertical interval entering the
picture is proof positive the tape's geometry changed, in two forms — (a) a waveform becoming decodable on line 20
or 21, and **(b) "the tapes own blanking which is discrete from device blanking enters on line 22"**.

**The mechanism is sound and its discriminator is measured and strong. The LINE is off by one.**

**Measured, per unit, against each unit's own device blanking rows** — a per-unit comparison against a measured
reference, never a typed-in cut, as *Source-measured levels* and rule 4 require:

| | capture 1 (card) | fixture A | capture 4 (SP, V-stab off) | device's own rows |
|---|---:|---:|---:|---:|
| **line 22** above device blank | **+0.00** | **+0.00** | **−0.00** | — |
| line 22 row sd | **0.48** | **0.48** | **0.48** | **0.48** |
| **line 23** above device blank | +1.77 | **+42.21** | **+109.36** | — |
| line 23 row sd | 2.24 | **47.08** | **33.58** | 0.48 |

**Line 22 is device blanking on all 1,092 field-readings across three captures — p10 to p90 of ±0.01, with the
device's own dither sd of 0.48 exactly.** Nothing the tape carries reaches it.
**And the contract already states the reason**, §2's table at `:349`: `| 22 | 18 | 281 | blanking, Y 1.4 |
Shuttle |` — line 22's origin is the Shuttle, unconditionally, unlike lines 20 and 21 which are qualified "when its
decoder has sync". **So the tape's blanking cannot enter on line 22: the device overwrites it.**

**Where it DOES become visible is line 23**, the first pass-through position — and CLAUDE.md already records the
observable there, on fixture A's displaced intro: "the tape's own black line 22 (Y ≈ 4–7, above the 1.4 blanking)
sits at row 19", and row 19 is NTSC **line 23**. His observable is real; it surfaces one line below where the
wording puts it, because the device destroys the row above it.

**RECOMMENDATION:** 6(b) should read **line 23 (and 286 in field 2)**, or better, "the first pass-through
position", so it stays correct if the raster description ever changes. The discriminator itself needs no
amendment — device-written blanking carries the dither sd of 0.48 and source-carried content at line 23 measures
2.24 to 47.08, a four- to ninety-eight-fold separation in noise character alone, per unit, with no level typed in.

⚠️ **Its strength varies with content and that bounds it:** on capture 1's dark card top, line 23 sits only +1.77
above blanking at sd 2.24 — separable, but not by the margin fixture A and capture 4 give. A source whose picture
begins genuinely black at line 23 is the case where 6(b) is weakest, and it has not been exercised.
⚠️ I have NOT verified 6(a) — whether a waveform becomes decodable on line 20 or 21 — and those lines are
conditionally Shuttle-written ("when its decoder has sync"), which is a different situation from line 22's
unconditional one and may not carry the same conclusion.

### ⚠️ ACCEPTED — and one thing found while preparing it to land that he should see before it does

He accepted all three parts ("accepted"). Two things from the landing sweep, one good and one that qualifies my
own proposal.

**GOOD: the engine already complies.** `field_registration.c:359-366` accumulates `blank_mean` by summing
`row_mean` over the blanking rows and dividing — it is already the mean, not the median. Part 2 needs no engine
change, only the contract naming what the code already does.

⚠️ **THE QUALIFICATION: my proposal named the DEVICE's blanking, and contract `:531` names the SOURCE's.** Its
words: "The blanking reference is established from qualified blanking intervals on the current source's good
picture lines… **device-generated fill never establishes it**", quoting him: "find the blanking on the good lines
of picture, thats your blanking interval the head switch needs to be measured inside of". **Every measurement I
took tonight used the device's regenerated rows** (7-15 / 270-278), which is the reference `:531` forbids. The
mean-versus-median ruling is unaffected — it is a question about the statistic, whichever reference is used — but
the reference my tables were built on is the wrong one.

⚠️ **And the source's reference is NOT reliably available on capture 1**, which is why this matters rather than
being a tidy-up. Measured over 1,016 field-readings, hunting each good picture row's own lowest sustained trailing
level with no threshold and no hardcoded column: it returns **51.97 with sd 41.58** — that is picture, not
blanking. Many of this capture's picture rows have no clean trailing blanking in the delivered window at all,
which is independently corroborated: `switch_without_shift.py` excludes **194 of 484** readings as unaskable
because the learned reference admits a one-sample run.
So on capture 1 the contract's named reference is often unmeasurable while the device's fill is always available
at 1.3756 with sd 0.0037. **That is a real tension between `:531` and this source, and it should be his to see
rather than resolved by quietly using the reference he forbade.**
⚠️ Two of my three attempts at measuring the source reference were themselves the fixed-place-to-look defect —
first a hardcoded column 706, then a trailing window from 580. The number above is from the version that hunts
the level instead, and it is reported as a negative result rather than a value.

### PROPOSAL — the level-threshold BASIS, reconciled as he asked (2026-09-11, overnight)

His instruction: *"thats tricky. I will leave it to it to reconcile and propose."* So this is a proposal with the
measurement behind it and a recommendation, not a settled question.

**The disagreement was two tables giving different tops for the same rasters.** One used an ABSOLUTE cut, the other
one RELATIVE to the device's blanking. **Measured, it is a THREE-way ambiguity, not two** — because "relative to
blanking" does not say WHICH STATISTIC of the blanking rows:

| basis | value of a nominal "3" | field 1 line 23 (level 4.02) reads as |
|---|---:|---|
| absolute | 3.00 | picture |
| median of the blanking rows + 3 | 4.00 | **borderline** — its range is 3.22–5.55 |
| mean of the blanking rows + 3 | 4.38 | blanking |

The same rows give median **1.0000** (sd 0.0000) and mean **1.3754** (sd 0.0036) — 0.375 codes apart on a dithered
constant — and field 1's line 23 sits at 4.02, so the three cuts bracket it three ways. **Specifying "relative"
without specifying the statistic reproduces the same ambiguity one level down.**

**What the choice costs, 146 units × 2 fields, at matched nominal thresholds:**

| nominal threshold | readings where the two bases disagree |
|---:|---:|
| 3 | 73 (25%) |
| 4 | 103 (35%) |
| 6 | 9 (3%) |
| 8 | 70 (24%) |
| 12 | 73 (25%) |

**RECOMMENDATION, three parts:**

1. **The basis is RELATIVE to the source's own measured blanking**, and this is not a preference — the contract's
   own *Source-measured levels* rule already requires it ("The engine establishes, for the source in front of it,
   what blanking is… No contract value, header constant or calibration file carries them") and rule 4 forbids
   typed-in numbers. **An absolute cut is a magic number and is already prohibited.**
2. **The statistic must be named with it.** Recommend the MEAN, because the device writes a *dithered* constant —
   CLAUDE.md records the lag-1 autocorrelation of −0.33 as the dither signature — and the mean recovers the written
   level (1.375) where the median quantises it to 1.0 and discards the dither entirely. The median's sd of exactly
   0.0000 is the tell: it is not measuring a level, it is reporting the modal integer.
3. ⚠️ **And the contract should rest nothing on a level-threshold top.** Measured over the same 146 units, field 1's
   top ranges over FIVE lines (23 to 28) across thresholds, and at a single threshold gives three different answers
   across units. No choice of basis repairs that. **His one-sided-motion ruling already contains the consequence** —
   a top-only move is a hold, so the fragility does not reach the crop — and that containment, rather than a better
   threshold, is what makes the top usable at all.

⚠️ **What this proposal does NOT settle:** which nominal threshold. That is gated behind the top detector's own
work, and picking one against these 146 units would be fitting to the fixture.

### OPEN — R3's recovery half, Codex's wording, added 2026-09-11

Codex does not accept that "the whole engine shouldn't run" closes the recovery question, and I agree: it neither
cancels "starts from scratch" nor says what happens when good video returns. Its exact question, attributed to it
and to be put in plain words:

> "When good video returns, does 'starts from scratch' still apply — must it find a new lock before correcting the
> picture again?"

⚠️ Do not import rule 5's shape to answer it: that would import rule 5's held-crop behaviour with it.

### ✅ 2026-09-11 — ALL SIX ANSWERED. Relayed, not heard directly by this session.

⚠️ **Provenance, stated before the content because it bounds what may be done with it.** These arrived through the
peer session "Watchdog brief builder", not from the owner in this conversation. Project practice treats his QUOTED
WORDS in a relay as authoritative and the relaying agent's connective tissue as not — and that distinction earned
its keep here: the watchdog issued a gloss on item 3, then withdrew it as "the wrong axis" after he corrected it.
His quotes are verbatim below; every gloss is attributed. **None of these is applied to the contract by this note.**
A contract edit needs agreement with Codex (§14), and the two that contradict the current text need it most.

**1. The switch below a box's bar — CLOSED, and it also answers the narrowed follow-up.**
> "yes your understanding of rule 8c is correct. close it. yes of course it may feed `d`."

So 8c's "below = separated by a gap" reading is confirmed, and the narrowed question — given contact holds and the
switch is measured, may that switch's position feed `d` through the line account, or is it good only for the
box-contact test — is answered YES, it may feed `d`. Findings 6 and CR-10 close on this.

**2. The invalid-raster condition / B2's residue — the CONTRACT IS WRONG and he says so directly.**
> "no a peak or partial line is a head switch full and valid. head switch may only be 1 line. perfectly fucking
> fine. a head switch region is anywhere horizontal timing skews blanking, either picture into it, or blanking into
> picture. idk how many times I need to repeat this to you. Holy shit, the lines own horizontal blanking is the
> thing that compares it to. thats the answer to your absensce part. if all the blanking and all the picture belong
> where they belong, it aint a head switch like area. if its somewhere other than the fucking bottom before the
> deck, device or [other] blanking, its not a head switch. its normal horizontal tearing."

and, on being told this contradicts the contract:
> "2 shouldn't contradict the contract. if it does the contract is wrong. The head switch is a band of horizontal
> timing error at the bottom and how that error skews should have fucking covered it. if it was only one lines
> timing that leaked, oh well."

**This is a REPAIR to §3's existing definition, not a new exception bolted onto it** — his §3 definition (a band of
horizontal timing error at the bottom, and how that error skews blanking into picture or picture into blanking)
already covers the one-line case, and the wording that excludes "a peak or a partial line" from the object whose
absence is required is an incorrect narrowing of his own rule. The absence test he supplies is concrete and is the
operative one: **compare against the line's OWN horizontal blanking**; all blanking and all picture where they
belong ⇒ not a head-switch area; skew anywhere other than the bottom before the regenerated blanking ⇒ ordinary
horizontal tearing, not a head switch.

**3. The terminal-black-run disposition — CLOSED, and his SECOND sentence supersedes the first reading of it.**
> "if that condition appears, the whole lock gets reset. it starts from scratch. that was an invalid signal"

then, correcting the relay's gloss:
> "it throws away nothing. it maintains nothing. the whole engine shouldn't run because that is an invariant that
> isn't valid NTSC"

⚠️ **So there is no retain-versus-discard decision to implement, because nothing is running to make one.** The
watchdog's own framing — "this discards it", set against the fade rule as hold-versus-discard — was withdrawn by
its author as the wrong axis. Take his two sentences together: the raster is not valid NTSC, so the engine has no
business operating on it; the lock is neither carried forward nor deliberately torn down, and the question of what
survives does not arise.
⚠️ His reason is a statement about the SIGNAL — "an invariant that isn't valid NTSC" — not about the engine's
confidence. An uncertain engine on a VALID raster is a different case and must not be routed here.
⚠️ The nearest existing shape is **rule 5's gate** (registration does not run on a raster that is not normal
picture, while observation continues), for the same kind of reason. Whether it IS rule 5's gate or a sibling is a
wording decision for the two agents; if unsettled, it goes back as one line rather than as an inference. It is NOT
rule 8a/12's hold-and-reassess, and NOT a bookkeeping reset that enumerates state to clear — he rejects both halves
of the second explicitly.

**4 and 5 — he considers answered by his earlier VBI and 480/486 rulings** ("answered by you I think", "same").

**6. Negative offsets and the comb.**
> "the comb is only to maintain the lock. if combing says thats the only way to lock, thems the breaks. thats the
> valid picture geometry. if it means X lines are missing because they are in the regenerated blanking, then they
> are in the regenerated blanking and that means the regenerated blanking plus any padding that gets the right
> fucking lines should be rendered as black, missing picture and the proper 20-22 should be placed on top of that
> in a 486 render to maintain compliance. The ONLY exception is if sometimes 22 shifts below the real 22 and it
> contains real picture and not caption garbage then it MAY be rendered. its a broken recording but so be it. that
> should be the top of the 480 render. if we actually determine real picture lines are gone, they should be
> blanked out."

**And one correction of his that is about process, recorded because it binds both agents.** Told that a
contract paragraph had carried two framings for a day and that "one thing lands on you first", he replied:
> "that sounds like your fuck up."

He is right, and it generalises: an amend-by-addition defect of ours is not an item for his queue, and dressing one
as a question wastes the attention the queue exists to spend. Log it, do not escalate it.

**His standing correction on HOW to ask, which cost a round to learn.** Item 3 first went to him as "when this
condition occurs after a lock, should the output retain the last corrective placement or bypass correction, which
learned state remains valid, and does recovery require reacquisition before correction resumes?" — every noun a
term of art, none of them named. His reply: *"3 is making my head hurt. what condition. what corrective placement.
what learned state. ENGLISH"*. Re-put in plain words it was answered immediately. **If a question cannot be asked
without four in-house nouns, it is not ready to ask.**

⚠️ **A two-stores state now EXISTS between this queue and the contract, deliberately, and it must not be left
standing.** These rows read ANSWERED while the contract still carries its three `OPEN, and with the owner` markers,
so `owner_queue_check.py` still reports 3 and 3 — correctly, because the contract genuinely still says they are
open. Removing those markers is a contract edit and needs agreement with Codex (§14), and two of the answers change
contract text rather than just closing a question. **Until that edit lands, the contract is the store that is
WRONG and this one is right — the opposite of the usual direction, and the reason to close it quickly.**


⚠️ **THREE MORE live only as inline markers in the contract and were never mirrored here (found 2026-09-11 by the
watchdog session, which noticed the queue said three while six were open).** This section is the QUEUE; a question
that exists only in the contract is invisible to whoever hands him the list, and the count staying at three across
the day was coincidence, not substitution. Pointers, per this file's rule that it holds no content:

| question | anchor (a STABLE quote from the marker; line numbers drift) | state |
|---|---|---|
| **B2's residue** — the disposition when the invalid-raster condition's absence cannot be established | `OPEN, and with the owner` … "his ruling settles the OBJECT whose absence is required" | ⚠️ **REFRAMED 2026-09-10 and the reframing must travel with it**: the question is the DISPOSITION when absence cannot be established, NOT whether it can be. Observability is empirical and is not his to rule on. Handing him the older framing asks him to rule on a measurement. |
| **Terminal-black-run disposition** | `UNSETTLED and with the owner` … "rule 13 not naming this" | intact: "should the output retain the last corrective placement or bypass correction, which learned state remains valid, and does recovery require reacquisition before correction resumes?" |
| **Caption-only precedence** | `OPEN, and with the owner:` … "on a caption-only acquisition, what independently established evidence determines" | intact: what evidence determines the required field interleave; if unavailable, may the lock exist without it, and what placement and rendering is permitted? |

⚠️ **The anchors are quotes, not line numbers, and that is the second defect this section had.** The first version
of these rows cited "contract lines 1015-1018"; by the time `experiments/owner_queue_check.py` was written the
marker had moved to 1027 — **drifted nine lines in a few hours of editing** — while the other two were inside a
two-line slack. A pointer that looks correct and lands in the wrong passage is worse than a missing one. The check
matches on the quoted phrase and reports drift in both directions.

**A fourth was withdrawn rather than asked** (Codex, 2026-09-10): whether a box's fixed extent is taken once from a
well-exposed unit and held or re-measured per unit. **Rule 8a already answers it** — "measured while the picture is
WELL EXPOSED, and it is HELD" — and supplies the fade discriminator. Same class as the three above: a question that
looks open because its answer is not where one would look for it.


**Two more, added 2026-09-10, in Codex's wording so neither agent's preferred consequence is baked in.**

**(a) The 486 render and the tape's line 22.** Rule 7 says "the tape's line 22 never renders". Traced in
`review_render.py` and measured on capture 2 (d1 = +2), that is false in the 486 mode: the window follows the
displacement, so the tape's line 22 is inside it and carries video (row 20, mean 60.06, sd 29.24, against device
blanking at row 18, sd 0.011). It is destroyed only where the Shuttle's own rows occupy that raster line.
*Codex's recommendation, to be put to him rather than implemented:* scope the prohibition to the 480-line picture
output and keep the diagnostic 486 window unmasked, since the expanded window's whole value is the evidence it
exposes. Either choice is a deliverable preference, which is his.
⚠️ The measurement supports what is DISPLAYED there; it does not independently establish that row's tape-line
identity.

**(b) Negative offsets under a maintained lock.** The definition of `d` says a `d ≤ 0` reading is "confirmed by the
comb"; rule 9 says the comb is not measured under a maintained lock; rule 9 also says the band's extent alone never
moves anything. Claude framed the consequence as "a negative offset can only be acquired, never tracked"; Codex
rejected that framing — rule 9 explicitly allows geometry tracking without rerunning the comb, "extent alone" can
mean an unqualified observation rather than every extent-based estimate, and uncertainty does not itself establish
loss of lock. The question, neutrally:

> "Under a maintained lock, may a qualified extent-based displacement update corrective placement without fresh comb
> confirmation? If not, is placement held unresolved, and what independently established event permits
> reacquisition?"


**The switch below a box's bar — added 2026-09-10, both agents at the limit of what they can decide.**
Codex's wording, to be put to him as asked:

> "Where an independently identified switch region lies below a box's bar, does the intervening bar prohibit using
> that switch for displacement through the line account, or only prohibit treating the switch as the immediately
> adjacent content boundary? Observation and the box-contact test remain available subject to their own
> qualifications."

Why it cannot be settled between us: his words are "a head switch placed below the actual video is unreliable and
shouldn't be measured at all", which reads categorical. Claude argued it cannot be categorical, because 8b's contact
test exists FOR boxed sources and a bar is exactly a region between content and switch, so a categorical reading
makes 8b inoperable on the class it was written for. Codex accepts that reductio only as far as it goes — it shows a
bar cannot CATEGORICALLY exclude the switch from the contact test; it does not show that every observed switch
qualifies for that test, nor that a bar necessarily disqualifies the displacement reading. Deciding the rest would be
inferring policy from structure on his behalf. Findings 6 and CR-10 close on his answer.


Neither agent may resolve these; the process sends contract conflicts to him.

**Cleared 2026-09-10 — items 4, 5 and 8 are ANSWERED. Their rows below are marked ANSWERED in place rather than
deleted, so the questions and their answers stay together; A18 above is answered too.**
Item 4, rule 8's box-validity wording: a box must be bounded (one end only is full picture), it is invalidated by
picture positively established within its held bounds, its extent is measured well exposed and held, and a fade
never invalidates. Item 8, "the two numbers": the box's outer bottom bound against the head-switch region, "lining
up" being contact with no intervening source-blanking interval. Item 5, VBI as a confirmation alongside captions:
the confirmations are the comb and captions/VBI, one class. A18, the switch requirement at both acquisition sites:
the head switch is a geometry input rather than a confirmation and a lock never requires one — this was a
tier-1 gate and this item's block is lifted, though the engine still implements the old requirement and that work
is outstanding. Other tier-1 items are unaffected by it closing.
All four are now in the contract; see its Source lock, Comb and rules 11-13.

4. ✅ **ANSWERED 2026-09-10 — in the contract, rule 8 and the Box definition.** A box must be BOUNDED; a
   structureless band at one end only is full picture, not a weaker box. Its extent is measured while the picture is
   well exposed and HELD. A fade never invalidates — a band edge that appears to move because the picture dimmed is
   exposure-dependent detectability — while a band edge moving at a steady level releases the geometry, and picture
   positively established within the held bounds invalidates the box. Replacement geometry is then measured, opening
   to whatever is on the screen rather than necessarily to full picture. Original text: **Rule 8's box-validity
   wording is owed** — the bounds where a box is valid and where it is invalidated. Neither agent should write it.
   Asked and explained; answer pending. (Was struck through while its own text said
   pending; un-struck 2026-09-10. The duplicate second "4." was the 486-crop item, which is genuinely closed and
   has been removed — its correction lives in CLAUDE.md §11.)
8. ✅ **ANSWERED 2026-09-10 — in the contract, rule 8.** The two quantities are the box's lower OUTER boundary —
   its bar, not its content — and the head-switch region; they "line up" when they meet with no intervening
   source-blanking interval. A demonstrated intervening interval prevents a new acquisition; an unresolved boundary
   does not establish contact and is not a failure of the test. The owner: "box is the bounds of the box, not the
   content inside the box", and "if the box doesn't touch the head switch, then its not valid geometry. simple.
   basically if there's a blanking interval that sits between the box and the head switch thats garbage." The
   earlier bottom-must-land-ABOVE-the-band formulation is withdrawn, and `experiments/box_vs_switch.py`, which
   measured the content bottom rather than the box's, is retracted. Original text: **What are "the two numbers" on
   geometry?** The band has an extent, a top switch line and a count; the box has bands at both ends. The contract
   previously carried a likely reading — the box's outer edges, top and bottom, per
   field, against where the switch band puts the picture's bounds — **marked as an inference and explicitly NOT an
   operative acquisition test**, because the owner's words it comes from (uuid 1bd1fc1d) are a question he asked the
   harness, not a definition. What is missing: which bottom is meant (picture bottom, switch line, or recorded
   edge), and what "line up" is as an equation. One line from him replaces it. Nothing is blocked on it.
9. **The switch-line count's acquisition is still unreconciled — and this item misdescribed the code.** ⚠️ Two
   corrections, 2026-09-10. First, the contract now authorizes a starting geometry CANDIDATE (rule 11, the seed:
   lines 23-262 with the band optional), which closes the seed half — but a candidate is not a measurement, and
   starting at 23 does not by itself establish d = 0 or authorize freezing count = extent. Second, the claim that
   "the engine already assumes d = 0 at acquisition so count = extent (`field_registration.c:436`)" is WRONG on both
   the line and the behaviour: line 436 is the box observation, and the count is computed at `:474-476` as
   `visible_d = m->top - origin` then `band_extent + visible_d` — derived from the measured top, not assumed zero.
   What remains open is reconciling the count's acquisition with the confirmed geometry and with the rule excluding
   the partial line. (Both agents agree this does NOT explain capture 1's zero locks — that is still open.)

5. ✅ **ANSWERED 2026-09-10 — in the contract, Source lock.** Yes: the permitted confirmations are the comb and
   qualified captions/VBI, one class, and nothing else. A lock is valid geometry plus one of those two, ideally
   both. Original text: **Is VBI a confirmation signal alongside captions?** The owner raised it himself: "isn't VBI another confirmation
   signal? ... caption and VBI are kind of part of the same class I think". It would give a caption-less source a
   second confirmation. Answered back to him with the asymmetry that decides it; his ruling pending.

## Qualification audit (2026-09-10) — the contract's `qualified` sites

The contract states the durable requirement (§3, *Qualification*): each qualification applies to a named
observation and decision, repetition alone does not remove systematic error, and qualification for one purpose does
not establish qualification for another. This is the dated audit of where the word is used and what each use would
have to establish. **The shared adjective is not itself the defect** — these are several tests. The defects to
guard against are a use with no identifiable criteria, and evidence satisfying one qualification being silently
credited to another.

25 whole-word occurrences (24 lowercase, one capitalised at the head-switch definition). Against at least six
kinds of object:

| object | what a test would have to establish | state |
|---|---|---|
| source-reference provenance and representativeness | that the sampled rows represent the source's blanking rather than device fill or clipped content | not built |
| caption / VBI semantics | parity, off-insert position, line 22 properly blanked, data rather than skew | stated in Source lock; not built as a test |
| timing-landmark identity | that the landmark tracked across fields is the SAME landmark | not built; B5's prerequisite |
| picture-boundary identity and uncertainty | that the detector found the boundary rather than an exposure artefact | not built; "well exposed" |
| displacement-estimator applicability | that the boundary used represents displacement of the retained geometry rather than independent switch motion | not built; B5 |
| retained-reference validity after a transition | that a reference measured under the old lock still describes the source | not built |

**Two of these are unbuilt MEASUREMENTS rather than naming work**, and they are the ones where an artefact may
swamp the signal: qualifying "well exposed" (the box census records the extent moving 5-10 lines with exposure
against 1-3 lines of genuine displacement — a warning, not a measured ratio, and magnitude alone does not settle
separability), and qualifying "structureless" (flat-within-one-code fires only on the device's synthetic rows;
vertical coherence rates text as more coherent than noise; the horizontal-spread statistic's level-independence
claim was withdrawn on 2026-09-10 when its denominator was found to pin at 1.0).

Also gating behaviour without operational definitions: "lift-off point" (holds the switch's bounds, rule 8c),
"static, detailed picture" (whether the comb reads), "a source's stable interval" (§8's invariants).

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
