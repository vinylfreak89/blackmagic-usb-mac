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

## The headline: `comb_safe` conflates two opposite meanings

`field_registration.c:697` — `out->comb_safe = settled && out->comb_check == FIELDREG_COMB_AGREE;`
with `FIELDREG_COMB_NOT_APPLICABLE = 0, AGREE, DISAGREE, FLAT`.

So **`comb_safe == false` means EITHER "the comb was evaluated and disagreed" OR "the comb was never
evaluated"** — and under a maintained lock the comb is deliberately not measured (rule 9), so the
second is the ordinary case. The contract burns this flag into the review overlay (§8's render spec)
where a reader will take it as a property of the frame.

This is the "missing is not a value" defect: a flag that conflates *confirmed bad* with *couldn't
tell*. **Disposition B** — the overlay must distinguish evaluated-and-disagreed from not-evaluated,
and the contract must say which it shows. Codex flagged the object/phase mismatch; the enum confirms it.

## The rest

| term | sites | disposition | basis |
|---|---|---|---|
| `0x0800` | 2 | **A** | the device's no-signal format code, measured and described in CLAUDE.md §5–6. Same object, same phase. Point at it. |
| `comb_safe` | 1 | **B** | above. |
| "normal picture" (vs "program") | 9 | **A**, with a naming repair | rule 5 defines the gate operationally — "where the signal-state layer does not report program". The contract then uses two names for one gate. One name, pointing at rule 5. |
| "a source's stable interval" | 1 | **A/C** | `experiments/stable_interval_check.py` gives an operational test, but its interval is a PER-SOURCE constant (capture 1's is counter ≥ 6667). The contract should say the interval is measured per source, not name one. |
| "static, detailed picture" | 1 | **C** | implemented (`static_comb_test.c` has `real_picture_fluctuation_does_not_discard_static_detail` and `linear_pan_has_no_static_detail`), but CLAUDE.md records the calibration as UNRESOLVED — the recalibrated mask still preferred a wrong +2 on a coherent pan. What counts as satisfying it is not established. |
| "WELL EXPOSED" | 2 | **C + D**, split | the empirical half (what exposure makes the box's extent readable) is measurable and unmeasured. The half it feeds — whether a box's fixed value is taken once from a well-exposed unit and held under the lock, or re-measured per unit — is POLICY, and CLAUDE.md already records it as the open design question. Only the second is his. |
| "lift-off point" | 2 | **B** | 8c makes the hold turn on its ABSENCE, and nothing implements or defines it: `grep -rn lift-off src/` finds one hit, in `SWITCH_UNKNOWNS.md`, which itself records "or a lift-off classifier. Those questions remain open." A hold criterion resting on an undefined absence. |
| "jump further than expected" | 1 | **C** | §1's TEMPORAL SOUNDNESS test. "Expected" is not stated; CLAUDE.md records the partial line's travel as one row, so it is likely definable from measurements already in hand rather than needing a ruling. |
| "near an edge" | 1 | **C** | same passage, same footing. |
| "band event" | 1 | **B** | §1 says a sound departure "should not register as a band event", so the term gates a report, and nothing defines or implements it (`band_event`: 0 hits in `src/`). |

## What this changes

**Nothing is an owner question except one half of "WELL EXPOSED"**, which is already on his list. The
rest is engineering: two things to implement or state (`comb_safe`'s two meanings, "lift-off point",
"band event"), three to qualify by measurement, two to point at existing definitions, and one naming
repair.

⚠️ This audit does not fix anything. It sorts. Each B and C row is work, and the C rows in particular
must not be closed by inventing a threshold — "static, detailed picture" is exactly where a fitted
constant would look like a definition.
