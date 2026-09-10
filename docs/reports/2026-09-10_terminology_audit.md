# Terminology audit — finding 34's undefined terms that gate behaviour

Cold-read finding 34 lists eleven terms the contract uses to gate behaviour without defining. This
audits each into a disposition. **The dispositions are Codex's, including the distinction it added
that matters most: a missing measurement method is NOT automatically an owner question.** Three
different things hide under "undefined":

| disposition | what it means | who |
|---|---|---|
| **A. Defined elsewhere** | a definition exists and governs the SAME OBJECT AND PHASE | point at it |
| **B. Missing implementation** | the rule is clear, nothing implements or states it | engineering |
| **C. Missing empirical qualification** | what would satisfy it is not established by measurement | engineering |
| **D. Unresolved policy** | no measurement settles it; it is a choice about behaviour | the owner |

An existing identifier is not sufficient for A. It must govern the same object and the same phase —
which `comb_safe` does not, and that is the sharpest thing this audit found.

## The headline: `comb_safe` is a boolean where three separate facts are needed — and the engine does not implement rule 9

`field_registration.c:697` — `out->comb_safe = settled && out->comb_check == FIELDREG_COMB_AGREE;`
with `FIELDREG_COMB_NOT_APPLICABLE = 0, AGREE, DISAGREE, FLAT`.

**`comb_safe == false` covers four different situations**, and one of them is not a comb result at all:
AGREE *while not settled*; DISAGREE; FLAT (no decidable evidence); NOT_APPLICABLE (never evaluated).
§8 burns this single boolean into the review overlay, where a reader takes it as a property of the
frame.

⚠️ **"Confirmed bad" is too strong for the DISAGREE case** (Codex's correction to this audit's first
version): a comb disagreement is not a verdict that the source frame is bad. What the overlay needs is
three facts kept apart — **whether evaluation occurred**, **its result or its inability to decide**,
and **the reason** — with lock state shown separately rather than folded in. Substituting the existing
`comb_check` enum is NOT sufficient on its own: it does not establish that every current
NOT_APPLICABLE and FLAT path carries the meaning the overlay would then assert.

⚠️ **And this is not an overlay relabel. MEASURED in the engine (2026-09-10):**
`field_registration.c:984` calls `comb_confirm(engine, raster, measurement, out)` **unconditionally on
every unit**, with no lock-state guard at the call site. Rule 9 says "under a maintained lock the
engine tracks geometry and does NOT measure the comb". **So COMB NOT EVALUATED under a maintained lock
is REQUIRED behaviour that this code does not implement** — the audit's first version treated it as
the ordinary case, which is policy read as implementation. The work is a record/schema change *and* an
execution-path change, not a label.

## The rest

| term | disposition | basis |
|---|---|---|
| `0x0800` | **A** | the device's no-signal format code, measured and described in CLAUDE.md §5–6. Same object, same phase. Point at it. |
| `comb_safe` | **B** | above — and the execution path, not only the record. |
| "normal picture" (vs "program") | **A**, with a naming repair | rule 5 defines the gate operationally — "where the signal-state layer does not report program". The contract then uses two names for one gate. |
| "a source's stable interval" | **B** | ⚠️ corrected: `experiments/stable_interval_check.py` TESTS a supplied interval; it does not establish how an interval is independently IDENTIFIED. So this is not "defined elsewhere" — the identification procedure is missing, and its per-source nature (capture 1's is counter ≥ 6667) is a property of the source, not of the term. |
| "static, detailed picture" | **C** | implemented (`static_comb_test.c`), but CLAUDE.md records the calibration as UNRESOLVED — the recalibrated mask still preferred a wrong +2 on a coherent pan. What satisfies it is not established. |
| "WELL EXPOSED" | **already answered — not open** | ⚠️ corrected: this audit's first version sent "held versus re-measured per unit" to the owner. **Rule 8a already answers it** — the extent is measured well exposed and HELD, with reassessment and invalidation elsewhere, and 8a supplies the discriminator: a fade shows the level falling while the band edges stay put and invalidates nothing; only an edge moving *while the level is steady* releases the geometry. What remains is detector work (how "well exposed" is qualified, how the fade is measured), not a ruling. |
| "lift-off point" | **B/C, distinguished** | 8c makes the hold turn on its ABSENCE. ⚠️ corrected: `grep` finding one hit does NOT establish that no equivalent implementation exists, nor that the term lacks a complete semantic definition. Two separate gaps — a missing DEFINITION and possibly-missing CODE — and they must not be conflated. |
| "jump further than expected" | **C** | §1's TEMPORAL SOUNDNESS test. ⚠️ corrected: "the partial line's one-row travel" does NOT define it. Temporal qualification also concerns the identified boundary's HORIZONTAL movement, censoring, and field order (CLAUDE.md's B5 prerequisite). |
| "near an edge" | **C** | same passage, same footing, same correction. |
| "band event" | **B/C, distinguished** | §1 says a sound departure "should not register as a band event", so it gates a report. Zero hits for `band_event` in `src/` — which, as above, is evidence about that identifier and not about whether equivalent behaviour exists. |

## What this changes

**Nothing here is an owner question.** The audit's first version sent one half of "WELL EXPOSED" to
him; rule 8a already answers it, and that is withdrawn. Everything else is engineering, in two kinds
Codex's distinction keeps apart: **missing implementation or specification** (`comb_safe`'s three
facts and rule 9's execution path, "lift-off point", "band event") and **missing empirical
qualification** ("static, detailed picture", "jump further than expected", "near an edge", the
stable interval's identification procedure).

⚠️ This audit sorts; it fixes nothing. Two standing cautions:
- The **C** rows must not be closed by inventing a threshold. "Static, detailed picture" is exactly
  where a fitted constant would look like a definition.
- **Absence of an identifier is evidence about that identifier.** It establishes neither that a term
  lacks a definition nor that no equivalent code exists, and this audit's first version used it for
  both.
