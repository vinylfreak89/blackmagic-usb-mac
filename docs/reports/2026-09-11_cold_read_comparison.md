# The two round-2 cold reads, compared

Both verdicts were frozen before either was opened. This is a later analysis by the Claude side and is
**not part of either review**. Neither report was edited.

| | Claude side | Codex side |
|---|---|---|
| report | `2026-09-11_contract_cold_read_claude.md` | `2026-09-11_contract_cold_read_codex.md` |
| sha256 | `f2994a8e…` | `629624eb…` |
| frozen at | `5652bea` | `cea6103` |
| findings | **27** (11 / 11 / 5 by consequence) | **5** |

Both read commit `5eb9be2`'s contract — blob `6696fd56…`, sha `3631179a…` — each side deriving those
values from git independently, and a third session verifying them again.

## 1. The counts are NOT comparable, and the reason is in the prompts

**27 against 5 is mostly a threshold difference, not a disagreement about the document.** The two
briefs set different bars, and neither reader exceeded its own:

- Claude's asked it to "report **every place** where it contradicts itself, defines one term as two
  different quantities, states a rule that cannot be satisfied as written, or relies on a term it
  never defines while gating behaviour on it."
- Codex's asked for "**consequential** contradictions, ambiguous quantities, competing operative
  rules, undefined interfaces… **Do not force a finding count or assume the document is defective.**"

⚠️ **Any reading of "27 versus 5" as one document being 5× worse under one reader is unsupported.**
That number is a property of the instructions at least as much as of the file.

## 2. Codex's reader declared its exclusions, and that is the most useful thing either report contains

Its "material limitations not counted as additional findings" section names, with line numbers, what
it saw and chose not to count. That converts an invisible threshold into a stated one, and it maps
onto Claude-side findings:

| Codex's stated exclusion | Claude-side finding in that area |
|---|---|
| "I do not count every use of 'qualified' as a separate missing algorithm" | several of A3–A5 |
| "I do not report 'the count is fixed' versus that named exception as an independent contradiction" | A2 |
| "Merely placing the tracking and stable-output sentences side by side would not establish a conflict" | A7 |
| "Historical quotations do not override express supersession" | B6, B10, C5 |
| "I do not infer an operational defect merely from the presence of a number" | B5 |
| "removing procedural gates is not a claim that the promised technical correction was delivered" | (the CR-02 material, repaired earlier the same day) |

⚠️ **DECLINED IS NOT ANSWERED, and A2 is the case that shows it.** Codex's reader cites lines 963–966
and 1278–1280, where the accepted expansion IS now carried into rule 4 and the acceptance invariant —
text added earlier the same day — and concludes there is no contradiction between "fixed" and "may
expand". That is correct as far as it goes. **The Claude-side finding is downstream of it**: given the
expansion is permitted and "recorded rather than reported as a disagreement", the document does not say
whether the retained `N` ABSORBS it — and because `d = N − E`, that decides whether the rendered picture
moves by one line at that unit. The exclusion does not reach that question. **Treating a declared
exclusion as a refutation would lose a live finding.**

## 3. Reached by both

- **8b's unresolved boundary.** Codex 4 (optional switch evidence versus the box-contact test when a
  switch exists but its boundary is unresolved) and Claude B3 (agreement licenses acquisition, while an
  unresolved boundary "is not a failure of the test") are the same defect from two directions.
- **The recorded-row definition is unusable as written.** Codex 3 ("last recorded row" does not uniquely
  identify the deck clip) and Claude B11 (the reference population is never obtainable) attack the same
  definition at different points.
- **The invalid class's second condition.** Codex 1 (no settled post-lock output or recovery disposition)
  and Claude C1 (the class announces "two conditions" and enumerates one) are adjacent rather than
  identical — one is about the missing disposition, the other about the missing enumeration.

## 4. Reached by one only

**Codex alone:** its finding 5 (instrument disagreement has two competing adjudication dispositions) has
no Claude-side counterpart. Its finding 2 (caption-only acquisition permits a route whose field
interleave is undetermined) likewise — **and that one is already an OPEN question with the owner**,
marked as such in the contract at the cited lines.

**Claude alone:** the bulk of A1–A11 — the offset equation `d = N − E` being a tautology under one
reading of "switch-line count" (A1), the acquisition-order circularity between the blanking reference,
"picture row" and head-switch identification (A11), the box-invalidation trigger being satisfied by
every unit of a boxed source (A10), the Closure check failing on the document's own worked example (B7).

## 5. The corroboration test, applied as the method note required

The method note was written into the Claude-side provenance **before either report was opened**,
because the temptation to read agreement as confirmation arrives with the reports. It requires
separating findings in areas the project `CLAUDE.md` discusses from findings that are not, since **both
readers were primed by that same file** and neither is the other's blind control.

- **In foregrounded areas** (the switch-line count, the box and its contact test, the head-switch
  region, the comb): Codex 4 ↔ Claude B3, and most of A1–A2, A8–A10, B1. **Agreement here is weak
  evidence** — it is consistent with two readers having been told the same thing.
- **Outside them**: Codex 3 ↔ Claude B11 (the recorded-row definition), Codex 5, Claude B7 and C1–C5.
  **This is the group where agreement means what the exercise was designed to produce**, and it is
  small: essentially one overlap, on the recorded-row definition.

## 6. What this establishes, and what it does not

**Establishes.** One defect is corroborated by two independently-run readers outside the primed areas —
the recorded-row definition does not identify what it is used to identify. Two more are corroborated
inside primed areas and should be treated as likely-real but weakly evidenced. Codex's reader's stated
exclusions give, for the first time, an explicit threshold against which any future review can be
compared.

**Does not establish.** That the document has 27 defects, or 5. That either reader is more reliable.
That agreement in the primed areas is independent. **Neither read was cold** — both readers inherited
the project `CLAUDE.md` automatically and both said so.

⚠️ **The two exposure accounts are NOT of equal standing, and the weaker one is Codex's.** Its
provenance records a **sequencing deviation**: the prompt required the exposure record before the
contract was opened, and the reviewer wrote its formal ledger *after the first read*. Its report
discloses this and the parent did not edit it away or substitute a ledger presented as
contemporaneous — both of which are creditable. But the consequence stands: **that ledger is a
reconstruction rather than a record**, produced by a reader already exposed to the document, which is
exactly what "write it before you look" exists to prevent. The Claude-side ledger was written by the
reviewer before it opened the file, per its brief.
**So where the two accounts of exposure differ, Codex's is the less reliable, and this comparison must
not lean on it as the tighter of the two.** It does not make its five findings wrong; it means its
account of its own priming is itself informed. The structural fix is environmental and is
recorded in `CLAUDE.md`: no subagent spawned in this repository can be a cold reader of this contract,
because the file arrives before the prompt.

⚠️ **This comparison is itself a first pass.** A full reconciliation of 27 against 5 requires reading
both reports' bodies against the frozen text finding by finding; what is above rests on the headings,
Codex's exclusions section, and the four cases checked in the contract directly. It is a map, not a
verdict, and it is not an acceptance of anything.
