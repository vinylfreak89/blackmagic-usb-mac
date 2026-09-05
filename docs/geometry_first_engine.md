# Geometry-first registration engine — design (2026-09-06 02:08 JST)

Branch `geometry-first`. Claude writes this engine; Codex writes the validation harness
(`docs/geometry_first_harness_brief.md`); neither reads the other's prior work. Per §14 the
design is derived below from two sources only — the owner's contract and the measured reference
raster — before any C is written. Every number is marked **raster** (derived from the measured
reference), **standard** (SMPTE RP-202 / CEA-608), or **default** (a tape-fitted value that must be
replaced or justified later). NTSC line numbers in prose; unit rows only in the tables.

## 1. The contract (owner, 2026-09-04/06, verbatim intent)

Geometry is the authority. Each field's active picture area — its top edge, bottom edge and
height — measured on every unit places the crop. Everything else (the tape's line 21, its black
line 22, static comb, any temporal witness) exists only to confirm that reading where geometry
alone cannot decide: (1) the head-switch region makes the bottom edge noisy and field-to-field
inconsistent; (2) geometry does not say which field's lines interleave on top — field precedence
is settled once per lock and held; (3) boxed pictures have their own geometry, centred in the
raster, and black level is not assumed constant. Tracking breaks only on a vertically torn
raster or a lost lock — both are one class: old geometry invalid, back to zero, re-acquire when
the lock returns. Horizontal tearing is not a geometry event. Dropout or RF noise that hides an
edge keeps the previous decision and re-evaluates when it clears. Line 22 never renders. The
output picture never moves except at a segment's initial lock and after such a re-acquisition.

## 2. The reference raster (measured 2026-09-05 on the locked no-source capture)

| unit rows | NTSC lines | content | source |
|---|---|---|---|
| 0–6, 261–269, 523–524 | 4–10, 265–273, 527–528 | padding, Y 16.0 / C 128.0 exactly | Shuttle |
| 7–15, 270–278 | 11–19, 274–282 | blanking, Y 1.4 ± 0.5 within a row, 0.01 unit to unit | Shuttle |
| 16, 279 | 20, 283 | timing pulse pattern | Shuttle |
| 17, 280 | 21, 284 | null CEA-608 insert (re-encodes what it decodes at the standard line) | Shuttle |
| 18, 281 | 22, 285 | blanking, Y 1.4 | Shuttle |
| 19–260, 282–522 | 23–264, 286–526 | pass-through: the source | tape/deck |

Consequences that the engine is built on:
- Nothing the tape carries above line 23 (286) reaches us. The tape's VBI becomes visible only
  when a displacement pushes it into the pass-through region: at displacement +2 the tape's
  line 21 appears on line 23; at +3 its line 20 appears on line 23 and its line 21 on 24; at +1
  its line 21 lands on the Shuttle's blanked line 22 and is invisible, while its black line 22
  appears on line 23 (measured: Y 4–7, above the 1.4 blanking, below any picture). At 0 the
  Shuttle re-encodes the tape's line 21 on its own insert.
- The picture's first RP-202 line is therefore the first pass-through row that is neither a
  VBI-type row (a 608 waveform, the tape's line 20 pattern, a black row) nor blanking. **Line 22
  never renders (standard):** if the first picture-carrying row sits directly under the tape's
  line-21 position, or directly under a black row that sits where line 22 would be, it is line 22
  and the crop starts one row lower.

## 3. Measurements, per unit, per field (all from the raw raster)

1. **Row luma profile** over the pass-through rows: mean and within-row std, at 640 samples per
   row. Blanking floor: 1.4 (**raster**). A row is *dark* if its mean ≤ floor + 8 (**default**: the
   tape's black line measures 4–7; a night scene at 10 is picture — the darkest picture row on
   fixture A; to be replaced by the field's own black level once boxing detection exists). A row
   is *picture* if it is not dark and not VBI-type.
2. **VBI-type rows:** a row that decodes as CEA-608 with valid parity (**standard**, my
   `cc608_decode.py` algorithm re-implemented in C: run-in by correlation at 1.986 µs cells,
   start bits 0,0,1, 16 LSB-first bits, odd parity per byte, amplitude gate 35 — **default**); a
   row with the timing-pattern signature of the Shuttle's line 20 (**raster**, by template match
   against the regenerated row 16); a run-in-only row (7 cycles, no start bits — the tape's line
   20 as seen at +3).
3. **Top edge:** the first pass-through row r such that r, r+1, r+2 are picture rows
   (**default**: three rows, so a single bright leak does not count). **Displacement top**:
   d_top = r − 19 (f1) / r − 282 (f2), then the line-22 correction of §2 if applicable.
4. **Tape's line 21 (when visible):** the unique parity-valid row off the insert ⇒ d_cap = row −
   17 (f1) / row − 280 (f2) (**standard**). Not an authority: a confirmation of d_top (it must equal
   d_top, or d_top + 1 when line 22 carries video in this recording).
5. **Tape's black line 22 (when visible):** the last dark row between the insert region and the
   top edge ⇒ d_gap = row − 18 (**raster**). Confirmation of d_top; also decides the line-22
   correction (a dark row directly above the top edge is the tape's line 22, so the top edge is
   already line 23).
6. **Bottom edge and height:** the last picture row before the padding, searched from the top
   edge downward; rows 257–260 / 519–522 are the head-switch band (**raster**: the four near-blank
   lines) and count as *uncertain*. Height = bottom − top + 1. Used only as a consistency check
   and for boxing detection, never for placement (owner: the bottom is noisy).
7. **Body continuity witness:** the vertical shift (−6..+6) of the field's picture body against
   the previous unit's same field, in two halves (upper/lower). Used only to (a) detect a
   splice/lost lock — one half still matches the previous unit while the other is a new picture
   (unit 300), or the two halves move by different amounts with the raster edges continuous —
   and (b) corroborate a one-line change of d_top when the caption and gap are both absent.
8. **Static comb between the two published crops:** once per lock, on the first units with
   ≥ 3% static detail (**default**), the relative shift (−3..+3) that minimises comb energy; this
   fixes FIELD PRECEDENCE (which field's picture line is above the other's). Thereafter a per-unit
   check only; disagreement is logged, never acted on per unit; a persistent disagreement (≥ 8
   units, **default**) with both edges stable flags the lock for re-acquisition.

## 4. Decision, per unit

For each field independently:
- If the top edge is measurable: d = d_top (with the line-22 correction). If a caption or gap is
  visible and disagrees with d_top by exactly the line-22 ambiguity, the recording's "line 22
  carries video" flag is set for the segment and d_top is corrected by it thereafter
  (**segment constant, learned once, boolean, not numeric**). Any other disagreement is logged
  (`VbiDisagrees`) and geometry wins.
- If the top edge is not measurable (torn, dark, snow): keep the previous d for this field
  (`EdgeHidden`), re-evaluate next unit. This is the owner's "keep the previous decision".
- If the body witness shows a splice or the classifier reports signal loss: mark the lock lost
  (`LockLost`), output the previous crop for this unit (nothing measurable), and on the next unit
  with a measurable top place fresh — the old d is not consulted (`Reacquired`, with the jump
  recorded). Field precedence is re-measured after every re-acquisition.
- Boxing: if height changes while top and bottom move symmetrically, the aperture is placed from
  the active area's centre (`Boxed`), not from the top edge (**owner**); until implemented, logged.

The output pair `(d1, d2)` is applied to the crops at rows 19+d1 / 282+d2, 240 lines each;
reading into the padding is legal black (**owner**). Sidecar: per field d, reason, top row,
bottom row, height, caption row, gap row, body shift per half, line-22 flag, lock state,
precedence, comb check — every decision with its evidence.

## 5. What this engine deliberately does not have

No zero re-anchoring, no learned numeric offsets, no evidence-voting hierarchy, no body-witness
veto of a measurable top, no persistent comb correction, no saved-geometry hold on absent
evidence, no top-reliability history. Each was measured to fit fixture A rather than the raster
(archaeology Part II). If one of them turns out to be needed, it comes back with a derivation.

## 6. Acceptance (Codex's harness, independently built)

Whole tape: crop starts on the picture's first RP-202 line by the oracle's reading (agree /
off-by-n / abstain per field); output moves only at units 300/301 and 43,737/43,738 (fixture A's
two relocks) and at real boxing changes; field precedence constant within a lock; no placement on
the snow/mute units 43,686–43,736; every hold named with its cause. Then the live-path watch copy
with the sidecar burned in, for the owner.

## 7. Revision from the raw panels (2026-09-06 05:30 JST, prototype `experiments/geometry_first_proto.py` at `be08bba`)

Every rule below replaced one in §3–§4 after a class panel (`experiments/class_panels.py`, raw rows of the units in
each decision class) contradicted the metric that had proposed it. Constants are labelled RASTER (measured on the
regenerated raster), STANDARD, or DEFAULT (fitted, to be replaced by a per-source measurement).

- **Rows are RECORDED or REGENERATED, decided against the unit's own blanking rows.** The Shuttle's regenerated rows
  (blanking, the two inserts, row 18) are chroma 128 exactly with sub-unit spread in every unit; every row that came
  through the analog decoder, black content included (luma 2–9), carries the decoder's chroma offset and noise
  (125–127). Thresholds are multiples of the blanking rows' own row-to-row spread (RASTER), never fixed levels. This
  makes the recorded region's first row measurable on black scenes and flat walls, where every luma-level test failed.
- **The top is the first recorded row that continues into the picture for two links** (row→row+1 and row+1→row+2,
  on 8-px horizontally smoothed rows, by correlation or by a difference at noise level). A VBI waveform (the tape's
  line-20 pulses, a parity-failed caption, the smeared XDS bar, the data line) never continues into the picture, but
  adjacent waveforms resemble EACH OTHER (measured: XDS bar vs run-in fragment, pulses vs caption), hence two links.
  Parity-valid captions are recognised as such (`cea608`); nothing else about a VBI row is assumed.
- **Recorded black above the picture is a BAND with two edges** (band start, picture start), reported as such; one
  raster cannot say whether it is the tape's blanking lines (field displaced by the band's height) or a black picture
  top. The caption decides when present (picture = caption+2, STANDARD); else the lock holds when it lies inside the
  band; else a single black row is read as the tape's black line 22 (fixture A's captions validated that 309/309,
  DEFAULT) and a deeper band as picture (golden rule: the recorded region is the picture until a gauge says otherwise).
- **Line 22 is never rendered (STANDARD RP-202).** A caption one row above the picture start marks that row as line
  22 whether it is black (gap) or attenuated video; only the video case sets the per-segment state used when no
  caption is visible. (A double count between the gap and video paths on the intro was the first panel-found bug.)
- **Field 2 without a gauge takes the relative static comb only among the admissible candidates of its black band.**
  A comb minimum cannot separate a displaced field from a source-side inter-field error; unconstrained it moved field
  2 to −1 at 05:00, below the recorded region, which is geometrically impossible.
- **The bottom is the last recorded row** (the deck's clip line: 262/525 on both fixtures, so height = 240 − d), no
  corridor of any width; the head-switch partial line under the last full picture line is reported with its split
  column and is picture. The commercial tape's picture runs to 262/525 and fixture A's to 260/522 plus the partial
  line: per source, measured per unit.
- **A flat raster holds.** Body median smoothed correlation 0.00 and row difference 0.1–0.3 (deck mute, pause, fade)
  against 0.90–0.95 / 1–11 on pictures (DEFAULT 0.3 / 1.0): no edge exists to measure.
- **Removed:** the three-consecutive-continuous-rows requirement (a content edge inside the first rows broke it),
  `bottom_uncertain` and the `hs` corridor constants, the luma-only `DARK` picture test, and the `runin`/`ccenv`/`bar`
  heuristics (the two-link rule and the regenerated/recorded split make them unnecessary).

Slice results at `be08bba` (applied pairs, units): 01:26 (1,0) 44 / (0,0) 30 / (2,0) 5; 05:00 (1,0) 373 / (0,0) 199 /
(2,0) 34; 35:00 (3,2) 357 / (2,2) 263; 37:01 (3,2) 244 / (2,2) 82; 45:00 (3,2) 614 / (2,2) 6; minute 43 (3,2) 306 of
319; commercial tape (0,0) 896 of 920 with every transition inside the first 47 units (rewind tail). The 35:00 +2/+3
alternation is the caption moving with the picture; the crop lands two lines under it every unit (panel-confirmed).
Not yet handled: snow and torn rasters are the signal-state layer's call (the frameserver's classifier), not
geometry's; the prototype only holds on flat rasters and torn top strips.
