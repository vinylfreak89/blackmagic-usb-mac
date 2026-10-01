# Registration: per-frame evidence plan (draft for the owner, 2026-10-01)

Plan, with a first implementation behind `GE_EVIDENCE=1` (off by default). Built from tvc2 (the commercial tape) with registration on,
replayed through today's engine (162,633 units, 0 holes, 0 drops), and checked against fixture A's
approved decision log. Every number below is from that work; the instruments live in the session
scratchpad and their conclusions are recorded here.

## What goes wrong today

1. **The placement offset is a 30-frame majority vote.** Confidence is a yes/no per frame; the anchor is
   the most common field-2 offset among the last 30 confident frames. A real change has to outnumber the
   old value inside the window: 24 frames (0.8 s) late at tvc2 29:10.28, and late again on release.
2. **The comb latches.** Once the comb sets a relative correction it is held until the measured tops
   change. On tvc2, 2,993 frames were held on an unmoved raster; on those frames the comb itself backed the
   held offset only 41% of the time (26% near-tie, 33% preferred the raster's placement).
3. **The comb follows vertical motion.** In a camera tilt the comb's optimum is half the frame-to-frame
   motion, because field 2 is captured 1/60 s later. tvc2 38.3-38.8 s: both fields move -2 to -4 lines per
   frame, the comb optimum is -1.2 to -1.9, and comb minus half the motion is about 0 on every frame.
4. **The motion check can be blinded by a static overlay.** At tvc2 38.64 s the title fades in over the
   still-tilting background; the engine's motion reading drops to 0, the picture is judged still, the still
   trigger fires and adopts the motion-driven -1 for one frame, then the latch holds it for three more.
5. **Scrolling credits pull the comb.** Fixture A EP credits (47:30-47:45): the comb follows the scroll
   (-3 on 380 of 449 frames) and the engine places field 1 at +2 to +5. The static parts of those frames
   are genuinely one line out (clean at relative -1, combed at 0 and at -3).
6. **The wrong field is moved.** The engine always corrects relative alignment by moving field 1. At tvc2
   52:51 one field at a time jumps 0.8-0.9 line, alternating fields; when field 2 is the one that jumped,
   moving field 1 fixes the weave but moves the whole picture the wrong way.

Not registration errors, recorded so they are not re-investigated:
- Where the raster really moves as a whole (tvc2 29:10-29:24, the picture starts at 28/290-291 under a
  near-black band): a common-mode question for stabilization, left alone here (owner).
- tvc2 52:43-52:58, a slowed-down scene whose fields are offset by about half a line, alternating in a
  cadence: whole-line registration cannot fix it; the goal is to stop thrashing there, not to cure it.
- Still-trigger frames are not deck-repeated frames: they differ from the previous frame by 1.4-4.8 codes,
  like ordinary quiet frames (1.2-3.8); a repeat would be near 0.

## The design (owner, 2026-10-01)

**Every frame decides from its own evidence, by confidence, not by counting.**

- Each measurement is an element that proposes a placement and carries a confidence factor computed from
  the measurement itself:
  - each field's measured top (how cleanly its top waveform was recognised);
  - the comb (depth and sharpness of its minimum: best against second best);
  - agreement between the two fields' top waveforms;
  - per-field motion against the same field one frame earlier (which field moved, and by how much).
- Each candidate placement collects the confidence of the elements backing it. The highest wins.
- **The previous decision competes as one more candidate with its own confidence** (owner's (b)): a single
  strong frame overrides it at once; a frame whose evidence is all weak keeps it rather than flipping on
  noise; when weak evidence opposes it while the stronger values agree with it, nothing changes.
- **No 30-frame vote and no comb latch.** A frame decided by the comb does not carry into the next frame; if
  the next frame's comb is confident, it decides again, otherwise the other evidence decides.
- **When the tops cannot be measured** (fades from black, near-black frames), the last measured raster is
  the fallback, never the last comb answer.
- **A confidence that cannot be measured on a source is replaced by that source's current one** (owner, 2026-10-01: "its fine if fixture A can't do it. it just means that that confidence value
  can't participate so fixture A maintains its current method"). The tops confidence was calibrated on tvc2,
  which carries NTSC setup (black about 16 codes above blanking), by checking the waveform top against a
  level-based top. Fixture A has no setup, so that check may not exist there. Where it cannot be measured,
  only the tops confidence reverts to the approved engine's: the yes/no test behind its vote (tops measured in
  both fields, a comb basin at the census, waveform pair correlation, no blank line inside the top), with its
  weight taken from how often that test is right on fixture A. Everything else in this design applies to
  fixture A too (owner: "you still have the changes we discussed about how decisions are made. no more of the
  overvoting that causes lagged decisions, that should still go in"): per-frame decisions by confidence, no
  30-frame vote, no latch, the previous decision as a weighted candidate, the static-tile comb with
  motion lowering its confidence, and moving the field that actually moved rather than always field 1 ("fixture A will still get the combing fix though and HOPEFULLY it doesn't
  change too many registrations"). Which tops confidence applies is decided per frame, like
  everything else (owner: "the only thing left out would be the proper NTSC setup we are discussing, and even
  that is still a per frame decision"): a frame whose setup-based check can be measured uses it, one whose
  check cannot uses the approved test. The approved-engine bound
  applies: fewer than 100 changed comb decisions and 500 changed placements, each change beyond it shown
  to the owner.

## Motion: comb confidence comes from what is not moving

- Split each field into tiles (the classifier's 15x15 grid is a candidate) and measure each tile's vertical
  shift against the same field one frame earlier, to a fraction of a line.
- A tile is **moving** when its shift is sustained (same direction on consecutive frames), **static** when it
  stays still in both fields across those frames.
- **Vertical motion anywhere in the field lowers the comb's confidence** (owner). The refinement the owner
  accepted: **the comb is measured over static tiles only.** Checked on the instrument:
  - tvc2 fade-in 38.2-39.0: static-tile comb -0.10..+0.23 on every frame (the title and logo), against the
    whole-frame comb's -1..-1.9. The four jittery frames would not happen.
  - fixture A EP credits: static-tile comb -1 on 323 of 336 frames, which the raw weave confirms; 113 frames
    have no static tile and give the comb no confidence at all.
  - fixture A SP credits (23:30-23:45, still cards): all measures agree on 0.
  - tvc2 52:43-52:58: static-tile comb is nearly flat (best/second 1.06 at the median), so its confidence
    is low and the raster's placement holds instead of thrashing.
- **Which field to move:** when matching tiles in both fields shift together it is shared motion and the
  comb ignores it; when one field's tiles jump and the other's do not (tvc2 52:51), that field is the one to
  correct.
- Risk to test: a static overlay that was itself mis-mastered against the video would steer a static-only
  comb. Keep "motion anywhere lowers comb confidence" as the rule; static-only is the variant under test.

## Still to measure before code (no invented numbers)

- What makes a tile measurable (the instrument used a fixed curve-depth ratio of 1.5; it must come from the
  tile's own noise).
- The static and moving boundaries (the instrument used 0.5 line).
- How element confidences combine into a candidate's score, and how the previous decision's confidence
  blends after a frame wins or loses.

## Test plan

- tvc2 first: the title fade-in (38.2-39.0), 52:43-52:58, 52:57-53:08 (the 324-frame hold), 50:36 (vertical
  motion the comb mistook), 29:10-29:24 (unchanged by design), and the whole-tape counts above.
- Then captures 1-4 and the whole fixture A tape against the approved decision log, within the owner's
  bound: fewer than 100 changed comb decisions and fewer than 500 changed placement decisions, unless a
  change is a fix the owner confirms.
- Whole-worker CPU from `make -C src/frameserver bench` within the 10 ms budget; the per-tile motion is the
  new cost to watch.

## Confidences, not gates (owner, 2026-10-01)

"it should be a confidence based normalized decision, not a single yes/no/unknown for the deciders" (his list of
examples was illustrative: "I don't know all the elements of the engine"). Every decider becomes a normalized
confidence; a surviving fixed number becomes the unit of a scale, learned from the tape's running spread where possible.

| Decider today | Becomes |
|---|---|
| Top accepted (waveform bar 0.45, clamp) | the top's step size against the field's running step spread |
| Top mistimed (spill / full-width blanking run) | edge departure against the running edge spread; gap width against 147 |
| Tops' trust (runtime share; "decisive" gate still, margin >= 2) | each observation weighted by the comb's confidence |
| Comb strength (0 / 1.7 / 4.6 at margins 1.05, 1.4) | depth below the runner-up, symmetry of the minimum, share of rows timed |
| Motion downgrades the comb one step | how well measured motion explains the comb's disagreement (equal vs half: measure) |
| Tile measurable (detail >= 1.3 x residual) | the ratio as the tile's weight |
| Tile static / moving (0.4 line) | the tile's shift against its own match noise |
| Row timed for the comb (spill, gap, edge > 4 off a 20-row standard) | each row weighted by its timing confidence |
| Edge measurable (20-80% rise in 8, picture >= 40, coarse 20) | rise time and level as continuous edge quality |
| Previous decision (last frame's fresh support; tie keeps it) | carries the last frame's decision margin |
| No-evidence fallback (raster or previous, by rule) | disappears: raster weighted by trust competes with the carried previous |
| Which field moved (jump beats the other by 0.4) | probability per field from both jumps against their noise |
| Absolute placement (30-frame vote) | per-frame candidates: field-2 top with its confidence, previous anchor carried |
| Classifier resets | transport facts stay hard; appearance changes may lower the carried previous |

## Order of work (owner)

Registration cleanup (this plan), then H-timing correction, then stabilization.
