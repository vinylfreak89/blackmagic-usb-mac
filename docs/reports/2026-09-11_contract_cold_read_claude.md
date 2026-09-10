# Internal-coherence review of `frozen/contract.md`

## 0. Isolation — stated honestly, and it is not clean

**I cannot claim a context-free read of this document, and it would be the most damaging error in this
exercise to imply otherwise.**

What I was asked for: read one file — `/private/tmp/.../coldread/frozen/contract.md`, 1,383 lines — and report
its internal defects, citing only that file.

What was supplied to me automatically, without my asking, before I opened it:

- The user's **global `CLAUDE.md`** (working rules, unrelated to this contract's subject matter).
- The **project `CLAUDE.md`** — a very long document about this exact project, which discusses this exact
  contract, names it, quotes the same owner rulings, and records the same disputes (the switch-line count,
  the box census and `box_vs_switch.py`'s retraction, the head-switch region, the comb's static mask, the
  "one name, several quantities" defect class, the colour-burst ruling, the v10 process and roles).
  **This means several of the areas I examined were foregrounded for me before I read a line of the target
  file**, and some distinctions I draw below may be ones that document already draws.
- A **memory index** of ~30 memory-file titles for this project.
- **Git status**: branch `v10-harness`, plus five recent commit subjects, two of which name subject matter I
  report on ("the switch-line disagreement, resolved on the raw rows, with one contract figure now in
  question"; "Correct a false pass: the gate score read the crop, not whether registration ran").
- MCP server instructions and a skills listing (irrelevant here).

What I did **not** do: I did not open the repository, git history, the source code, `docs/v10_pending.md`,
`experiments/`, `briefs/`, `field_lines.h`, `CLAUDE.md` as a *source for this report*, or the web. **Every
quotation and line number below comes from the frozen file alone**, and no finding rests on anything I knew
from the supplied context. But "I did not cite it" is not "I did not know it", and the honest description of
this read is *informed*, not *cold*.

Where the target file refers to `CLAUDE.md`, `docs/v10_pending.md`, `experiments/*`, `field_lines.h` or
`briefs/*`, I treated those references as unresolvable and said so rather than filling them in.

---

## 1. Summary

**27 findings.**

- **Tier A — placement, loss-accounting or mathematical validity: 11** (A1–A11)
- **Tier B — a decision or an operative rule: 11** (B1–B11)
- **Tier C — narrower scope or documentation: 5** (C1–C5)

Ranking is by what two implementations would *do* differently, not by how wrong the wording looks. Tier A
items change where the picture is placed, whether a line is counted as picture or lost, or make an equation
degenerate. Tier B items change a decision (whether a lock is acquired, whether a hold survives, whether a
number may be written). Tier C items are scope or presentation.

Two conventions I follow throughout, from the brief:

- Where the document fails to name an observable, I say it fails to name one. I do not conclude that no
  observable exists.
- Passages the document marks superseded, withdrawn or historical are not counted. I count a superseded
  statement only where it stands **unmarked** beside its replacement (B6, B10, C5).

---

## TIER A — placement, loss-accounting, mathematical validity

### A1. "Switch-line count" names two different quantities inside its own defining sentence, and under one of them the offset equation `d = N − E` is a tautology that yields no value

**The finding.** The single sentence that defines the switch-line count defines it both as a constant taken
once at the lock and as a quantity measured on every unit as `E + d`; substituting the second into the offset
definition `d = N − E` gives `d = d`, so the offset is determinate under one reading and vacuous under the
other.

**Competing passages.**

> **Switch-line count**: the field's number of head-switch lines, taken
> at the confirmed unit and kept for the lock (never re-learned; owner, 20:56), **measured per unit as the band's
> extent + d** (the lines past the clip are the offset's); a unit whose measurement differs from the lock's count is
> reported (rule 2).  — lines 684–687

> ... d = the switch-line count minus the band's extent (≤ 0), confirmed by the comb (rule 9).  — lines 681–682

> `P = C − 22 − N`, where `C` is the field's qualified clip line and `N` its **retained** switch-line count. This
> follows from `E = C − T + 1`, `L = T − 23` and the qualified displacement relation `d = N − E`  — lines 689–691

Rule 2 resolves it in one direction and thereby confirms the two quantities are distinct:

> Under the qualified `d = N − E` the general relation is `ΔE = ΔN − Δd`, so **with the retained count `N`
> unchanged** `ΔE = −Δd`  — lines 950–951

And §5 records both quantities as separate fields of the record:

> the span, the picture rows and **the band count; the lock's switch-line count**  — line 1224

**What an implementer would do differently.** Reading 1 (`N` = the retained lock constant, as lines 689–691 and
950–951 say): `d = N − E` returns a signed offset, and a unit whose per-unit measurement differs is *reported*.
Reading 2 (`N` = "the field's number of head-switch lines, measured per unit"): the engine measures `N` as
`E + d` and then computes `d = N − E`, which reproduces whatever `d` it already had — the clamped-top branch
of the offset definition silently becomes a no-op and the crop never moves upward at all. The defining
sentence supports both, and it is the sentence an implementer reads first.

---

### A2. The lock's switch-line count is "never re-learned" and is simultaneously permitted to expand — and the offset equation turns that disagreement into a one-line placement difference

**The finding.** Three passages say the lock's count is fixed until a reset; two say it may expand; because
`d = N − E`, whether the retained `N` absorbs an accepted expansion decides whether the rendered picture moves
by one line at that unit.

**Competing passages.**

> taken at the confirmed unit and kept for the lock (**never re-learned**; owner, 20:56)  — lines 684–685

> The lock's constant, the switch-line count, is taken at the confirmed unit and **kept until a reset,
> never re-learned**  — lines 963–964

> The source's **switch-line count is fixed**; the top switch line is the only variable one  — line 949

against

> - **The switch-line count MAY EXPAND** where the partial was not present from the beginning, and that is
>   accepted rather than a fault.  — lines 1103–1104

> the **lock's switch-line count is constant except for 8c's accepted expansion**, which is recorded and is not a
> violation of this invariant  — lines 1279–1280

Rule 4's qualification addresses only *reporting*, not the value:

> 8c's accepted expansion is the one qualification: **it is recorded rather than reported as a disagreement**,
> it must meet its own evidence requirements, and unchanged placement does not establish them.  — lines 964–966

**What an implementer would do differently.** Under "never re-learned", an accepted expansion leaves `N` alone
while `E` grows by one, so `d = N − E` falls by one and the crop moves up one line — the picture jumps.
Under §8's invariant (which explicitly exempts the lock's count from constancy for this event), `N` grows with
`E` and `d` is unchanged — the picture is still. §8's own acceptance criterion is "the render's machine
read-back shows the picture still except at the moves rule 8 allows" (lines 1249–1250), so the two readings
disagree about whether the capture passes.

---

### A3. §3 defines **Displacement** as exactly the reading §3 elsewhere establishes is unqualified — and as the behaviour it names as the engine's current defect

**The finding.** The `Displacement` entry defines the quantity as the top against line 23; twenty lines
earlier the same section says that at a clamped top `top − 23 = 0` is "a constraint, not an observed zero",
and names `geometry_d = top − origin` as what the engine does today and what the entry forbids.

**Competing passages.**

> - **Displacement**: the picture top against its standard line, 23 in each field.  — line 715

> **Within the displacement decision: two independently qualified observations feeding one result.** A top-based
> displacement **only where the source's picture origin is IDENTIFIED** — at a clamped top, `top − 23 = 0` is a
> constraint, not an observed zero.  — lines 911–913

> ⚠️ **WHAT THE ENGINE DOES TODAY, which is outcome (1) unconditionally.** `field_registration.c` computes
> `geometry_d = top − origin` and applies it whenever the geometry is measurable and the crop fits the raster
> ... which is **the reading this entry establishes is unqualified**.  — lines 917–922

> `top − 23` cannot read upward displacement, because rule 11 is that an earlier start cannot be established
> from evidence the Shuttle overwrote.  — lines 887–888

**What an implementer would do differently.** An implementer working from the `Displacement` definition
computes `top − 23` on every unit and applies it — which is precisely the behaviour lines 917–922 identify as
the defect. An implementer working from lines 911–916 applies a top-based reading only where the picture
origin is identified and otherwise returns outcome (4), Unknown, holding placement. The definition is
one line long and sits in the definitions section; the qualification is 200 lines earlier in a bullet headed
"THE DISPLACEMENT DECISION IS INCOMPLETE".

---

### A4. Rule 9 orders the offset to be read from `count − extent` **every unit**, unconditionally, while the displacement entry says that reading is unqualified and the outcome is Unknown

**The finding.** The operative rule states the two-reading procedure with no qualification and no abstention
path; the definitions section says the extent-based reading is usable only when separately qualified and
otherwise yields outcome (4).

**Competing passages.**

> The **offset is read every unit** from the bands above the picture, or, with the top at line 23, from the band's
> extent against the switch-line count (definition of d)  — lines 1139–1141

against

> `count − extent` from the observed top **reads a head-catch excursion and the partial's disappearance as
> displacement**.  — lines 887–888

> An extent-based one only where the boundary is **qualified to represent displacement of the retained geometry
> rather than independent switch motion**. ... One qualified, it is used under its stated conditions. **Neither,
> outcome (4).**  — lines 913–916

> (4) **unresolved** — displacement Unknown, the placement-hold rule applies, and holding placement is NOT
> evidence that displacement was zero.  — lines 906–907

Rule 2 carries the qualification; rule 9 does not:

> **Switch-position change represents picture displacement only where the displacement qualification establishes
> that relationship.**  — line 946

**What an implementer would do differently.** Under rule 9 the engine produces an offset on every unit and
places the crop from it, including on units where the band moved and the picture did not. Under lines 911–916
the engine abstains on those units, records Unknown, and holds. The difference is a per-unit crop move on
exactly the units §1's head-catch ruling says must not move the picture. Rule 9 is inside "§4. Rules (the
owner's, from section 1; **the engine implements**, the harness checks)" — an implementer has every reason to
treat it as the operative text.

---

### A5. "Per unit the two readings of d must agree" cannot be satisfied at a clamped top without forcing `d = 0`, which annuls the branch it is attached to

**The finding.** The offset definition is a case split — bands-above when the top is below 23, `count − extent`
when the top reads 23 — and by the document's own definition of "bands above the picture" the first reading is
necessarily 0 at a clamped top, so requiring both readings to agree per unit forces `d = 0` in exactly the case
the second branch exists to express.

**Competing passages.**

> When the picture top sits below line 23, d = the bands above the picture ... **When the top reads line 23** the
> picture may sit at or above it (a **clamped top** ...): **d = the switch-line count minus the band's extent
> (≤ 0)**  — lines 679–682

> **Bands above the picture**: the recorded rows between line 23 and the picture top **that are not the Shuttle's**.
> — lines 699–700

> **Per unit the two readings of d — the bands above the picture, and count − extent — must agree** ("most
> important is agreement").  — lines 697–698

> most important is agreement (owner)  — line 1143

**Why they cannot both hold.** At a clamped top the picture's first line is at or above line 23 and lies in the
Shuttle's regenerated rows, so the set "recorded rows between line 23 and the picture top that are not the
Shuttle's" is empty: reading one is 0. Reading two is `N − E ≤ 0` and is negative whenever the branch is doing
any work. Requiring agreement per unit therefore admits only `d = 0`.

**What an implementer would do differently.** Implementer A computes both readings on every unit and treats
disagreement as a violation — which fires on every genuinely upward-displaced unit and blocks the correction.
Implementer B applies the case split, computes only the applicable reading, and never compares them. A third
reading (from lines 911–916, "Both qualified, they must agree within measurement uncertainty") makes agreement
conditional on both being qualified — but lines 697–698 and 1143 say "per unit" and "most important is
agreement" with no such condition.

---

### A6. Negative `d` is defined as "confirmed by the comb", and no confirmation route the document permits can confirm it — while three passages specify how to render it

**The finding.** The clamped-top branch of `d` requires comb confirmation; the comb is (a) not measured under a
maintained lock and (b) common-mode blind; captions and VBI can confirm only downward displacement. So for a
common-mode upward displacement, and for *any* upward displacement under a maintained lock, no permitted
confirmation exists — while the crop, rule 7 and §1 all specify the output for `d = −1`, `−2` and `−3`.

**Competing passages.**

The requirement:

> d = the switch-line count minus the band's extent (≤ 0), **confirmed by the comb (rule 9)**.  — line 682

> Blank lines under the picture could indicate that the field sits high and **need confirmation — by the comb at
> acquisition or reacquisition, or by a qualified caption** ...; **the band's extent alone never moves anything**
> — lines 1138–1139

> Missing bottom lines alone do not establish displacement: they are treated as padding **unless qualified caption
> or comb evidence establishes otherwise**.  — lines 1161–1162

The two routes, closed:

> **Comb measurement and picture-preserving alignment selection occur during acquisition and reacquisition only**
> ... **Under a maintained lock the comb is not measured**  — lines 862–865

> The comb is **common-mode blind and a zero never asserts `d = 0`** — lines 861–862

> the comb constrains the two fields' relative registration only, so **where both fields are ambiguous by the same
> amount the COMB CANNOT CONFIRM THAT CANDIDATE**.  — lines 880–882

> the tape's own VBI is above the delivered window at zero displacement and appears only when the field is
> displaced downward, so it **can confirm "displaced by +N" and never "at zero"**  — lines 761–762

> A caption whose row lies in the pass-through region (line 23 or below) is the tape's own line 21 and gives
> **d = its line − 21** directly.  — lines 788–789

The output that is nonetheless specified:

> the crop takes the picture's first line to it, so its field-relative origin is **23 + d for every sign of d** ...
> the render's line 23 is the source's real line 23 wherever it landed ... **its blank at −1, its caption insert at
> −2, its timing line at −3**  — lines 828–831

> at a negative offset the render's first line is whatever the Shuttle put at 23 + d  — line 1015

**What an implementer would do differently.** Implementer A treats the confirmation requirement as binding:
an upward-displaced field is never corrected (no route can confirm it), the picture's top lines stay lost, and
rule 7's negative-offset rendering is dead code. Implementer B treats the confirmation requirement as applying
to *acquisition* only and applies `d < 0` under a maintained lock from the extent reading alone — which
lines 1138–1139 forbid ("the band's extent alone never moves anything"). This is loss-accounting as well as
placement: under A the lines above the crop are permanently discarded.

---

### A7. What is rendered after a lock-like loss — standard placement, or the last placement held — is stated both ways, and one of them moves the output at a moment rule 8 does not allow

**The finding.** Three passages say that with no lock the picture sits at standard placement; rule 8 says the
output picture never moves except at an initial lock and after a re-acquisition; a lock-like loss removes the
lock without being either of those.

**Competing passages.**

> Tracking breaks only on a vertically torn raster or a lost lock — both are one class: old geometry invalid,
> **back to zero**, re-acquire when the lock returns.  — lines 216–217

> without it the picture **stays at standard placement (line 23)** and the record says there was not enough to lock
> on.  — lines 232–233

> **before a lock, standard placement.**  — lines 834–835

against

> **8. The output picture never moves except at a segment's initial lock and after a re-acquisition.**  — line 1018

> **Lock-like loss**: snow-like signal, a vertical tear (cross-program or true), a signal-state relock or splice; a
> unit event, both fields. **It resets the geometry and the engine continues.**  — lines 792–794

> **"Output" below means the stabilized visible picture the owner watches, not the crop-origin metadata.**
> — line 1277

> initial acquisition or reacquisition may establish placement ... and **invalidation alone supplies neither
> replacement geometry nor permission to apply it; nothing is placed on snow**  — lines 1285–1287

**What an implementer would do differently.** Implementer A resets the crop to 23/23 the moment the lock is
lost: on a source that was being corrected at `d = +2`, the visible picture jumps two lines at the loss and
jumps back at re-acquisition — two moves, one of which rule 8 does not list. Implementer B holds the last
applied crop through the unlocked interval and moves only at re-acquisition — one move, rule-8 compliant, but
contradicting "before a lock, standard placement" for the whole interval. §8's acceptance test reads the
render back for exactly this ("the picture still except at the moves rule 8 allows", lines 1249–1250), so the
two implementations produce different verdicts on the same capture. The document raises the "held versus
bypassed" distinction explicitly for the invalid class (lines 802–806, marked UNSETTLED with the owner) and
nowhere for lock-like loss.

---

### A8. "Band's extent" is measured from "the top switch line" without saying whether that is the current observed line or the retained/held one — and the two differ on precisely the units where the hold is doing its work

**The finding.** `E` is defined from "the top switch line"; the document elsewhere insists the currently
observed switch line and the retained boundary are different objects and that a held boundary survives an
unmeasurable observation. `d = N − E` therefore has two values on every held unit.

**Competing passages.**

> **Band's extent**: **the rows from the top switch line to the clip, inclusive** — the switch lines and whatever
> black or blank rows lie under them; counted per field.  — lines 683–684

> This follows from `E = C − T + 1`  — line 690

against

> **The current observed T is distinct from the RETAINED switch bounds: an unmeasurable current T does not erase a
> previously qualified held boundary.**  — lines 662–663

> A retained switch boundary is not a fresh observation, and **the disappearance of its marker does not by itself
> move or erase that boundary**  — lines 947–948

> **Where it is absent the head switch's POSITION LINE is HELD, not removed**  — lines 967–968

> - **Held**: the switch point disappearing after acquisition does not move the top line. **The line that WAS the
>   partial line stays the top line** even though it is no longer partial.  — lines 1096–1097

> **If neither is measurable, the unit's switch line is Unknown and the lock's count is not substituted as an
> observation.**  — lines 665–666

**What an implementer would do differently.** Implementer A computes `E` from the current observed `T`: on a
held unit `T` is Unknown, so `E` is Unknown, so `d` is Unknown and the crop holds. Implementer B computes `E`
from the retained boundary: `E` is available on every unit, `d = N − E` returns a value, and the crop is
placed. The two disagree about whether a held unit produces a placement at all — and where the observed and
retained lines differ by one, they disagree about the placement by one line.

---

### A9. The line the band sheds is "normal picture" under the head-catch ruling and still the top switch line under 8c and rule 2 — with rule 3 putting the picture bottom above it

**The finding.** Two rules classify the same line oppositely for the same observation (the switch marker
ceasing to appear on it), and the document names no observable that separates "the switch moved off this line"
from "the switch point disappeared while the boundary is held".

**Competing passages.**

> the line the picture "lost" to the band **counts as normal picture geometry**, no hold is taken on the switch,
> and THE OUTPUT PICTURE DOES NOT MOVE.  — lines 166–167

> The band's edge falls off a line and **that line becomes normal picture - the picture GAINS one**; or the edge
> moves up onto a line and that line stops being normal picture - the picture LOSES one. Both are valid and expected
> ... and NEITHER is a lost lock, a hold, or a geometry change.  — lines 175–178

against

> - **Held**: the switch point disappearing after acquisition does not move the top line. **The line that WAS the
>   partial line stays the top line even though it is no longer partial.**  — lines 1096–1097

> [Switch line] **keeps being the switch line when the peak moves into the other field or disappears off the edge,
> even if it then holds a fully stable line of picture**  — lines 653–654

> 3. The line account is conserved; **the picture bottom is the row above the switch line**; lines past the clip are
>    lost.  — line 960

And the document states that membership cannot be decided independently:

> membership is not independently observable: **the band's lines have no persistent identifiers**, so deciding which
> of this unit's rows belong to the frozen band requires already knowing the displacement.  — lines 889–891

**What an implementer would do differently.** Implementer A (head-catch ruling) extends the picture bottom by
one line, counts the line in the picture's account, and renders it. Implementer B (8c/rule 2/rule 3) keeps the
line as the top switch line, renders one fewer line of picture, and leaves the account unchanged. One line of
recorded picture is delivered or discarded on every such event, and `P`, `E` and the band count all differ by
one. I note the document does not name an observable separating the two events; I do not claim none exists.

---

### A10. 8a's box-invalidation trigger is satisfied by every unit of a boxed source under the document's own definition of "Picture row"

**The finding.** 8a says the box's bars *are* recorded picture rows, and eleven lines earlier says that picture
positively established in a previously identified bar region invalidates the box — so under §3's definition of
a picture row the trigger is true on every unit of every boxed source.

**Competing passages.**

> **Picture positively established IN A PREVIOUSLY IDENTIFIED BAR REGION also invalidates the box (rule 12)**;
> ordinary content inside the box's own content area does not, since carrying content there is what a box IS.
> — lines 1045–1046

> A boxed picture's bars **are recorded picture rows inside the 240** and change nothing in the account
> — lines 1050–1051

> - **Picture row**: **a recorded row that is neither a VBI row nor a row of the head-switch region.**  — line 562

> - **Recorded row**: a pass-through row that came through the analog decoder ... **or luma above the blank**;
>   padding is neither.  — lines 491–494

Rule 12 uses the owner's phrasing, which is a third term again:

> "not just a transition event, mute or fade. if the boxed geometry becomes invalid, then it should reset as well.
> mute fade, **or actual picture appearing in the letterbox-like area bounds**"  — lines 1170–1171

**What an implementer would do differently.** Implementer A applies §3's definition literally: bar rows satisfy
"picture row", the invalidation trigger fires on the first unit after the box is identified, the box geometry
and its lock are released (rule 12, lines 1183–1184), and a boxed source can never hold a box. Implementer B
reads "picture" here as visible content/structure — a quantity the document does not define anywhere — and the
box survives until structure appears in the bars. Rule 12's consequence is release of the geometry *and* the
lock, so the two implementations differ over whether a boxed source is ever locked at all, which in turn gates
8b's acquisition route.

---

### A11. The blanking reference is acquired from "good picture lines", a picture row is defined by excluding head-switch rows, and head-switch rows are identified against the blanking reference — the document gives no order in which the three can be acquired

**The finding.** Three definitions each take one of the others as an input, and warm-up holds registration
inactive until the required references are qualified; the document states no acquisition order and does not
name an observable that breaks the cycle.

**Competing passages.**

> **The blanking reference** is established from **qualified blanking intervals on the current source's good picture
> lines** and supplies both level and variability ... "the CORRECT thing to do is find the blanking on the good
> lines of picture, thats your blanking interval the head switch needs to be measured inside of"  — lines 531–534

> **The same reference serves the head switch's horizontal extent** and the black of the invalid-raster test.
> — lines 535–536

> - **Picture row**: a recorded row that is **neither a VBI row nor a row of the head-switch region.** ⚠️ The
>   head-switch exclusion **is load-bearing** and was missing  — lines 562–563

> - **Head switch**: **the region affected by the other field's horizontal timing intruding into this field** ...
>   **Qualified horizontal-timing departure** ... may supply EVIDENCE about it  — lines 646–649

> - **Warm-up**: **the phase in which REQUIRED source references are not yet qualified.** Observation and reference
>   acquisition continue while **registration and corrective placement are inactive.**  — lines 540–541

The document does cut an adjacent circularity, which shows the class is recognised:

> ⚠️ **"Only geometry can" is DELETED** (owner, 2026-09-10, cutting the circularity a cold read found: **the switch
> measurement cannot depend on geometry when head-switch evidence is an input to geometry**).  — lines 436–438

**What an implementer would do differently.** Implementer A seeds the blanking reference from rows chosen by
position (the document supplies one such population: "The Shuttle's regenerated blanking rows — lines 11–19 of
each field ... are the reference when present", lines 499–500) — but §3 forbids exactly that ("device-generated
fill never establishes it", line 534). Implementer B waits for "good picture lines", which cannot be
identified without the head-switch exclusion, which needs the reference: warm-up never completes and
registration never runs on any source. I am not claiming no acquisition order exists; I am reporting that the
document specifies none while gating all behaviour on the result.

---

## TIER B — a decision or an operative rule

### B1. Within five lines, 8c says a boxed source's switch is not measured and is measured like any other

**The finding.** 8c excludes a switch separated from the picture by a gap, 8d rules that a box's bar between
content and switch *is* such a gap, and 8c also states that a boxed source's switch is measured like any other.

**Competing passages.**

> A head switch separated from the picture by a GAP **is not measured** (owner ... "where there is a gap
> between the head switch and picture content, not a head switch directly touching the picture").  — lines 1081–1083

> **A boxed source's switch IS measured like any other; a box does not make it unmeasurable.**  — line 1086

> asked whether the rows between a card's last content row and its switch line count as a gap, **"Yes they count as
> a gap"**, then "But why they count as a gap is important. They are part of a box" — establishes why **those rows
> separate CONTENT from the switch for the purpose of measuring the switch against picture**. It does not make the
> box's own bar a disqualifying gap for the BOX  — lines 1117–1121

**What an implementer would do differently.** Implementer A suppresses the switch measurement on boxed units
(1081–1083 + 1117–1119): the band count, `E`, 8b's contact test and the invalid-raster region test all go
Unknown on every boxed unit. Implementer B measures it (1086) and the box route works. 8b independently
*requires* the switch to be located on a boxed source ("the box's lower OUTER boundary must meet it", line
1066), which only Implementer B can satisfy. 8d's distinction is between the box's validity and measuring the
switch *against picture* — but 8c's opening sentence says "is not measured", unqualified.

---

### B2. Rule 6 bars any unit carrying a horizontal timing error other than its own head switch from being the confirmed unit, and §2 records exactly such an error on the first lines of every field of the two line-TBC-off acceptance captures

**The finding.** Flagging is described as "a horizontal timing error" present in the first lines of every field
with the line TBC off; rule 6 disqualifies a unit carrying such an error from being the confirmed unit; two of
the four acceptance captures are line-TBC-off.

**Competing passages.**

> **A unit carrying a horizontal timing error other than its own head switch may not be the confirmed unit**: it
> holds, and the lock's constants are taken from a clean unit (owner, 2026-09-09: "other horizontal timing error
> should result in a hold rather than a lock").  — lines 1010–1012

> with it off the picture starts on its standard line, **the first lines carry a horizontal timing error that varies
> along the row (flagging)**  — lines 482–483

> the top rows of each field (lines 23–34) carry end levels of median 4.6–6.6 and p95 52–63 above blanking ... **the
> flagging of a VHS field's first lines**  — lines 443–445

> **The commercial capture has the deck's line TBC OFF**  — line 1261

> (4) the SP recording with the deck's V-stabilize off  — lines 1247–1248

against

> Closed 2026-09-07 21:12 (both agents): the V-stabilize-off pass's **flagged first lines are recorded, non-VBI rows
> and therefore picture; the top is read through the flagging; the horizontal error is not the engine's**  — lines
> 1381–1383

**What an implementer would do differently.** Implementer A applies rule 6 literally: on captures 1 and 4 every
unit carries flagging, so no unit may be the confirmed unit, no lock is ever acquired, and the picture stays at
standard placement for the whole capture (which rule 1 says is correct behaviour, line 944). Implementer B
treats flagging as excluded from "horizontal timing error" per §9's closed item and locks normally. The first
capture in the acceptance order is decided by which reading is taken.

---

### B3. 8b says agreement licenses acquisition and that an unresolved boundary "is not a failure of the test" — leaving unresolved contact as either permitting or blocking acquisition

**The finding.** The contact test is stated as a two-outcome rule (agree → may acquire, disagree → hold), and
the third outcome is described only by what it is not.

**Competing passages.**

> **Agreeing, they are valid geometry and MAY set a new acquisition. Disagreeing, the unit holds and may not
> acquire.** **A demonstrated intervening interval prevents a new acquisition; an UNRESOLVED boundary does not
> establish contact and is not a failure of the test.**  — lines 1073–1075

> "if the two numbers on geometry LINE UP ... then this is valid geometry and can write a new picture ... **if they
> DONT line up, then no, it can not become a new acquisition, only a hold.**"  — lines 1069–1072

**What an implementer would do differently.** Implementer A reads the licence as positive ("Agreeing ... MAY set
a new acquisition") and blocks acquisition on an unresolved boundary — a boxed source whose switch boundary is
Unknown never locks. Implementer B reads the prohibition as exhaustive ("A demonstrated intervening interval
prevents a new acquisition") and acquires on an unresolved boundary, moving the rendered picture. The
consequence is whether an unresolved unit can move the output — the highest-stakes act in the document.

---

### B4. The hold's test counts "switch lines other than the partial line", and the document does not say whether the line that stops being partial enters that count — the event that triggers the hold could invalidate it

**The finding.** 8c's hold is triggered by the switch point disappearing and is tested by the count of
non-partial switch lines; whether the ex-partial line now counts as a non-partial switch line decides whether
the hold survives its own trigger.

**Competing passages.**

> "**if the switch point disappears after being acquired and the number of switch lines other than the partial line
> doesn't change, the partial line that is no longer partial should stay the top line.** If the total number of
> lines changes other than the partial line, then that hold is invalid"  — lines 1090–1093

> - **The hold's test is the count of switch lines OTHER THAN the partial line.** Unchanged, the hold stands.
>   Changed, the hold is invalid and the switch geometry's bounds are re-acquired. **A change in the partial line
>   itself does not invalidate it.**  — lines 1098–1100

> **The hold is lost when the count of SWITCH LINES OTHER THAN THE PARTIAL LINE changes**  — line 969

And the definition that decides membership counts the partial line in:

> **Switch lines / the band**: the head-switch lines counted from the top switch line down, **the partial line
> included** (owner)  — lines 668–669

**What an implementer would do differently.** Implementer A tracks "the partial line" as a role held by
identity: when it stops being partial it keeps that role, the non-partial count is unchanged, and the hold
stands — which is 8c's stated intent. Implementer B computes the count per unit as "switch lines that are not
currently partial": the ex-partial line joins it, the count rises by one, "that hold is invalid and the bounds
of the switch geometry need to be reacquired". Under B the hold can never survive the event it is defined for.

---

### B5. The contract requires two typed decision thresholds that its own header, rule 4 and §6 forbid the code to contain

**The finding.** A vertical tear must be "at least three rows long" and an invalid raster needs "more than 24
qualifying terminal lines"; neither is a standard, a stated measurement on the captures, or a memory capacity,
and §6 bans thresholds that are not a stated measurement.

**Competing passages.**

> **Every number is a standard (NTSC, SMPTE RP-202, CEA-608), a measurement on the captures (stated with its value),
> or a memory capacity; any other number in the code is a defect.**  — lines 17–18

> **no thresholds that are not a stated measurement.**  — lines 1238–1239

> **No magic numbers, no per-source constants typed in.**  — lines 980–981

> **Neither instrument may independently choose a cutoff**, and a decision margin is derived and qualified from the
> source rather than typed in  — line 98

> **No count appears here, because a number written in a definition becomes an expectation to match**  — lines
> 670–671

against

> a departure is a tear only when it (a) returns to the field's stable timing, **(b) is at least three rows long**,
> and (c) has stable readable rows above it.  — lines 593–594

> The condition itself: **a trailing black run of more than 24 qualifying terminal lines** AND positively
> established absence of the head-switch REGION within them  — lines 807–808

**What an implementer would do differently.** Implementer A writes `3` and `24` into the engine and implements
the two rules as specified — and ships two numbers the header calls defects. Implementer B refuses to type
them, derives them from the source, and implements a tear detector and an invalid-raster test whose thresholds
differ from the contract's, changing which units are classified as tears and which rasters disable the engine.
There is no third option in the text: both rules are stated with their constants and both bans are stated
without exception.

---

### B6. "Geometry is the authority" stands unmarked in §1 against rule 1's "Geometry is a guess not a lock"

**The finding.** §1's Intent paragraph makes geometry decisive and confirmation a fallback for cases geometry
cannot settle; rule 1 makes geometry a proposal that never moves the output without confirmation. The Intent
paragraph carries no local supersession marking, though §1's preamble says status is marked passage by passage.

**Competing passages.**

> **Intent (2026-09-04/06).** **Geometry is the authority.** Each field's active picture area ... measured on every
> unit **places the crop**. Everything else (the tape's line 21, its black line 22, static comb, any temporal
> witness) **exists only to confirm that reading where geometry alone cannot decide**  — lines 211–213

against

> 1. **Geometry PROPOSES; independent confirmation licenses acquisition; only a lock moves the rendered picture**
>    (owner, 2026-09-10: "**Geometry is a guess not a lock.** A comb safe and/or caption safe/VBI ... result or
>    adjustment make it into a lock. Only after lock does it move the rendered frame's location.")  — lines 941–943

> 4. **A lock is acquired on two or more independent observations, at least one of which must be geometry**  — line
>    961

The preamble that should have marked it:

> Historical and explicitly superseded passages here preserve provenance and do not independently impose current
> requirements — **their status is marked locally, passage by passage** ... The line-numbering convention immediately
> below IS current.  — lines 24–26

(The adjacent sentence about confirmation *is* locally marked — "⚠️ **SUPERSEDED IN TWO WAYS — read §3 Source
lock, not this sentence.**", line 233 — which is what makes the unmarked sentences beside it read as current.)

**What an implementer would do differently.** Implementer A places the crop from measured geometry on every
unit and seeks confirmation only where geometry is ambiguous — which is what lines 917–922 describe the engine
doing today and call the forbidden behaviour. Implementer B never moves the output without a confirmed lock.
Note the Intent paragraph is not wholly historical: rule 8's sentence is copied from it verbatim (lines 219–220
vs 1018), so an implementer has grounds to read the whole paragraph as current.

---

### B7. The "Closure" check, as stated, fails on the document's own worked example

**The finding.** Closure says a field is 240 lines and the expected bottom is top + 239, and names that the
closure check — while the picture bottom is the row above the switch line, which is above top + 239 by the size
of the band in every one of the document's worked cases.

**Competing passages.**

> - **Closure**: a field is 240 lines; **top + 239 is the expected bottom**; rows past the clip are lost (owner). The
>   **picture bottom placed by the engine is the row above the switch line**; the expected bottom is the closure
>   check.  — lines 703–704

> Worked with three lines: **offset 0, picture 23–259, band 260–262 (3 + 0)**  — line 687

At offset 0 the top is 23, so top + 239 = 262, while the picture bottom is 259. The document does not say what
the expected bottom is compared *against*.

**What an implementer would do differently.** Implementer A implements the check as `picture_bottom == top +
239` and reports a closure violation on every unit of every source with a head switch. Implementer B implements
it as the account closing — span + extent = `C − 22` — which passes on the same units. The first produces a
capture-wide failure report; the second produces none.

---

### B8. "Band" names the head-switch band, the account's bands above and below the picture, and the box's bars — and 8a's release trigger reads as a contradiction of the head-catch ruling if the switch band is meant

**The finding.** Four different regions are called bands; 8a's "a band edge moving while the level is steady
does release the geometry" is stated without saying which, and the head-switch band's top edge is expected to
move by a line or two without releasing anything.

**Competing passages.**

> **A band edge moving WHILE THE LEVEL IS STEADY does release the geometry.** The two look identical at the first
> unit and one means hold while the other means release.  — lines 1043–1044

> rule 8a has two invalidation triggers, **picture appearing within previously established bar regions AND a band
> edge moving while the level is steady**  — lines 1202–1203

against

> a band that moves by a line or two is **NOT a fault and NOT a lock loss** ... **NEITHER is a lost lock, a hold, or
> a geometry change.**  — lines 163, 178

and the other senses:

> **Bands above the picture**: the recorded rows between line 23 and the picture top that are not the Shuttle's.
> **Bands below**: the band's extent.  — lines 699–700

> the two quantities the account uses are the **count of RECORDED LINES ABOVE THE PICTURE** and the **OBSERVED BAND
> EXTENT** below it, and neither is a count of separate regions  — lines 971–973

> A box's bands — where they fall and how many rows they run — are source dependent  — lines 1053–1054

> the **metrics band** of `experiments/overlay_sidecar.py`  — line 1309

**What an implementer would do differently.** Implementer A scopes 8a's trigger to the box's bars (its
surrounding context) and lets the switch band's edge move freely. Implementer B applies the sentence as
written to any band edge, so an ordinary head-catch excursion at steady level releases the geometry — which
§1 says explicitly is not a geometry change. The consequence is a spurious geometry release, and under
rule 12 (lines 1183–1184) a released geometry takes the lock with it.

---

### B9. A change of boxing is a "change of geometry" that resets the lock, and rule 5b equates a change of geometry with lock-like loss — whose definition is a closed list that omits boxing

**The finding.** The same event is scoped two ways: as a lock-like loss (a unit event resetting both fields at
once) and as invalidation of "the affected geometry" (which rule 12 and §8 treat as per-field/per-box, with
reacquisition).

**Competing passages.**

> **A change of geometry resets the lock**: bounding-box geometry becoming full picture, or full picture plus a
> head-switch band, or the reverse.  — lines 782–783

> **Lock-like loss**: snow-like signal, a vertical tear (cross-program or true), a signal-state relock or splice; a
> unit event, both fields.  — lines 792–793

> 5b. A loss of source lock or a lock-like loss (**the owner's "change of geometry"**, 2026-09-07 afternoon) resets
>    the GEOMETRY immediately, **both fields at once**  — lines 998–999

> Once invalidation is established **the affected geometry and lock are released** and replacement geometry requires
> acquisition.  — lines 1183–1184

> including **reacquisition following a positively established change of boxing**  — lines 1285–1286

**What an implementer would do differently.** Implementer A treats a boxing change as a lock-like loss: both
fields reset at that unit, references discarded ("A lock-like loss (rule 5b) discards them with the lock",
line 582), warm-up re-entered. Implementer B releases only the affected field's box geometry and lock and
reacquires, keeping the other field's state and the source references. The two differ in how much learned
state survives a letterbox change and in whether the unaffected field's picture moves.

---

### B10. §1 carries the owner's "the number of switch lines below the top line either stays constant or decreases" unmarked, against rule 4's "changes" and 8c's expansion

**The finding.** Three statements about the same count are in force: it may only stay constant or decrease
(§1, unmarked); any change invalidates the hold (rule 4, 8c); it may expand (8c).

**Competing passages.**

> **The number of switch lines below the top line either stays constant or decreases.** The top switch line should be
> the only variable one as that's the actual area of travel.  — lines 290–291

against

> **The hold is lost when the count of SWITCH LINES OTHER THAN THE PARTIAL LINE changes**  — line 969

> - **The switch-line count MAY EXPAND** where the partial was not present from the beginning  — line 1103

**What an implementer would do differently.** Implementer A treats a decrease as normal (§1) and only an
increase as notable. Implementer B invalidates the hold on any change including a decrease (rule 4), and
accepts an increase in the specific expansion case (8c) — the exact opposite polarity from §1 in both
directions. Which units re-acquire their switch bounds differs accordingly.

---

### B11. "Recorded row" is qualified against a "recorded rows" reference population the document never says how to obtain

**The finding.** The definition distinguishes recorded from regenerated rows by chroma noise measured against
two "independently identified reference populations", one of which (the regenerated rows) is identified by
fixed position and the other of which is the class being defined.

**Competing passages.**

> - **Recorded row**: a pass-through row that came through the analog decoder, **told from the Shuttle's regenerated
>   rows by the decoder's noise: chroma noise qualified against the independently identified reference populations
>   for the CURRENT source — the regenerated rows and the recorded rows** ..., or luma above the blank  — lines
>   491–494

> The Shuttle's regenerated blanking rows — **lines 11–19 of each field, storage rows 7–15 and 270–278** — are the
> reference when present  — lines 499–500

> §2's measured separation on capture 1 (regenerated at most 1.48x the blanking rows', recorded at least 2.02x) and
> the historical 2.0x test that sat inside that gap **belong to the implementation and evidence record, not to this
> definition**  — lines 494–497

**What an implementer would do differently.** Implementer A uses the second disjunct ("or luma above the
blank") as the operative test and never builds the chroma populations — which classifies a black picture row
at blanking level as regenerated, and §2 records that "in those regions no level test separated content from
blanking" (lines 435–436). Implementer B builds the chroma test and must seed the recorded-row population from
somewhere the document does not name. Since "Bands above the picture" is defined as a count of *recorded* rows
(line 699), the choice propagates directly into `d`. I report that the document does not name the method; I do
not claim one cannot exist.

---

## TIER C — narrower scope or documentation

### C1. The invalid class announces "Two conditions" and states only the first where it enumerates them

**The finding.** "SECOND," is immediately followed by a disposition note rather than a condition; the second
condition appears nine lines later after two ⚠️ paragraphs.

> **Two conditions put a raster there. FIRST, the regenerated rows absent** — their absence must be POSITIVELY
> ESTABLISHED ... **SECOND, ⚠️ its disposition after a lock is UNSETTLED and with the owner** — rule 13 not naming
> this condition establishes only that it does not expressly mandate the full reset  — lines 798–801

> **The condition itself:** a trailing black run of more than 24 qualifying terminal lines AND positively
> established absence of the head-switch REGION within them  — lines 807–808

**What an implementer would do differently.** A reader taking "SECOND" at face value implements one condition
plus an open question and never implements the black-run test at all; a reader who reaches line 807 implements
two. The nested ⚠️ paragraphs (802–820) sit between the label and its referent.

---

### C2. The 720×486 review window is specified both as fixed raster lines 20–262 and as following the placed crop

**The finding.** "As placed" and "lines 20–262 in each field" name different windows at any nonzero `d`, and
the stated purpose (seeing the Shuttle's inserts) holds only for the fixed reading.

> the **720×486 output as placed** (CLAUDE.md §11's alternate mode: **lines 20–262 in each field**, 243 lines per
> field, **so each field carries its timing insert, its caption insert and its regenerated black above the picture**
> — three lines above and none below, in both fields ... So what landed on the caption and VBI rows is visible.
> — lines 1296–1300

Against the crop rule, which moves the window with the picture:

> the crop takes the picture's first line to it, so its field-relative origin is **23 + d for every sign of d**
> — lines 828–829

**What an implementer would do differently.** Implementer A renders fixed raster lines 20–262 (the Shuttle's
timing line and insert always visible, the picture sliding within the frame). Implementer B renders
`20 + d`…`262 + d` (the picture stable, the three rows above it being whatever the tape put there). The
reviewer sees a different artifact on every displaced unit, and this is the artifact §8 makes the acceptance
instrument.

---

### C3. The acceptance render's cadence is stated as two fields per unit while every other statement about the review artifacts requires exactly one frame per unit

> Each capture's render (**two fields per unit, rows doubled**, red = picture top and bottom, yellow = the band
> bottom) is read back by machine on every frame  — line 1289

> **Alignment.** The band is aligned to the picture by construction **ONLY when the video holds exactly one frame per
> sidecar row from the first row, and the tool refuses anything else.**  — lines 1332–1333

> Deinterlaced with **bwdif in `send_frame` mode, one frame per unit, 29.97p**  — line 1339

**What an implementer would do differently.** If the acceptance render emits two frames per unit, the alignment
guard "refuses anything else" and the render cannot carry the sidecar band; if it emits one frame containing
both fields with rows doubled, it passes. The sentence supports both.

---

### C4. §5 disposes of provenance errors with a bare "fail closed", which §3 declares is not an executable disposition

> **Provenance errors fail closed.**  — lines 1227–1228

> - **"Fail open" and "fail closed" are DESCRIPTIVE terms, not executable dispositions.** ... **Each rule therefore
>   states separately** whether delivery continues, whether a record is emitted, whether an existing placement is
>   held or correction bypassed, and whether learned state is retained or reset.  — lines 503–508

**What an implementer would do differently.** Taken alone, §5's sentence is ambiguous across the four axes §3
enumerates — in particular whether the record is emitted. §3's own Provenance-error entry does state them
separately (lines 707–714, "fail closed on the measurement, never on the record"), so this is a documentation
inconsistency rather than an unresolved decision; I rank it last for that reason.

---

### C5. §1's preamble promises that status is marked "passage by passage", and several §1 passages that conflict with §3/§4 carry no local marking

> Historical and explicitly superseded passages here preserve provenance and do not independently impose current
> requirements — **their status is marked locally, passage by passage**, because a global statement cannot resolve a
> paragraph that contradicts itself. **The line-numbering convention immediately below IS current.**  — lines 24–26

Unmarked §1 passages that conflict with later text, both reported above: "**Geometry is the authority** ...
Everything else ... exists only to confirm that reading where geometry alone cannot decide" (lines 211–213, vs
rule 1 at 941–943 — B6), and "**The number of switch lines below the top line either stays constant or
decreases**" (lines 290–291, vs rule 4 at 969 and 8c at 1103 — B10).

**What an implementer would do differently.** Because §1 marks *some* passages locally and explicitly (line 37,
line 233, lines 266, 612–616, 818–820), the absence of a marking reads as a positive statement that a passage
is current. An implementer taking that inference treats the two passages above as operative; one who reads
§1 as wholly historical ignores them — but the preamble forbids that reading too ("this section is neither
purely source material nor wholly operative", line 23).

---

## 2. Things I deliberately did NOT count as findings

Recorded so the count is honest about its boundaries:

- **`d = N − E` reading a head-catch excursion as displacement.** Contradictory, but flagged in place at lines
  885–891. I counted only the *unflagged* operative site (rule 9 — A4).
- **"Precedence" naming three quantities.** The document flags it itself, names all three, and marks the open
  question for the owner (lines 1022–1030).
- **"Picture row" admitting head-switch rows.** Self-flagged at lines 562–567.
- **"Qualified" carrying six objects.** The document states this and says the shared adjective is not the
  defect (lines 512–521). I looked for uses with no identifiable criteria and report one gating case
  ("good picture lines", A11) and one population case (B11); I did not count the adjective itself.
- **"Fail open" and "fail closed" describing the same behaviour in opposite words** (lines 781 vs 824–825) —
  explicitly reconciled at lines 503–511.
- **The comb's `comb_safe` boolean, the `comb_check` enum, and the engine calling `comb_confirm` every unit** —
  all marked as proposed-not-implemented (lines 850–856).
- **"Well exposed" having no test** — self-marked as open detector work (lines 1199–1200), and a missing method
  is not a finding under the brief.
- **The header's number taxonomy vs the illustrative measurements in §2** — those are stated with their values,
  which the taxonomy permits. Only the two decision thresholds are counted (B5).
- **`262.5 + 24 = 23.5`** (line 823). Under the field-relative convention this reads as advancing 24 lines from
  field 1's last half line into the next field's 23.5, which is consistent. I found no arithmetic error.
- **The line/row mapping** (lines 7–14, 199–209, the §2 table at 342–351, the 263-row offset at 1298–1299).
  I checked every mapping and every count — 1 + 9 + 9 + 2 + 1 + 240 = 262, field 1 + 1 = 263, line 1 twenty
  rows above the caption row under the wrap, 243 × 2 = 486, 279 − 16 = 263 — and all of them are consistent.
- **The algebra of `E = C − T + 1`, `L = T − 23`, `d = N − E`, `P = L − d = C − 22 − N`, `L = C − 22 − E`** —
  I verified each substitution and the three worked examples at lines 687–689. The identities are sound. The
  defects I report are about *which quantity* is substituted (A1, A8), not about the algebra.
