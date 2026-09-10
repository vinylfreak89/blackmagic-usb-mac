# Cold read of `docs/geometry_first_engine.md` — findings

**Provenance.** A subagent read the document with no other material: not the proposal, not the day's
rulings, not either agent's reasoning. It read commit **`4eed79e`** (md5 `d9723e01…`, 97,370 bytes,
verified against `git show`), i.e. BEFORE the two placement fixes in `fb4d7bb`. ⚠️ Its isolation is
PARTIAL: the repository instruction file loads into a subagent automatically and carries today's
conclusions. It noted itself that several defects it saw in a stale first read — head-switch-required
lock, regenerated-rows-absent clash, the implementation gate — were already fixed and it did not
report them.

**36 findings; all five requested categories non-empty.** Its own three most dangerous: #3, #4, #12.

## SEVERE

1. **Three incompatible tests for where the head switch is, unranked.** §1 mandates measuring where
   blanking is OVERWRITTEN at the delivered edges and calls the inside-the-picture method "exactly
   inverted from my intent"; §2 keeps that disavowed method as "the primary one"; §3's *Head switch*
   defines a third (first skew discontinuity scanning down, else S). Rules 2, 3, 8c and 9 all use them.
2. **The mandated edge test has no stated method, and the specification as written is circular.**
   ⚠️ **This finding originally read "can never return anything but Unknown by the document's own statements", and
   that is CORRECTED** (Codex's reviewer, independently, 2026-09-10): a missing identification method and a circular
   specification are not the same thing as fundamental impossibility, and only the first two are established here.
   The document not naming an observable does not prove none exists — which the owner's B1 ruling then demonstrated
   by naming one. The defect is real and was worth finding; the claim of impossibility was mine to withdraw.
   §1: a blank-level run "does not by itself distinguish blanking extension from contiguous dark
   picture… the edge measurement is Unknown". §2: black content "is clipped to exactly the blanking
   level, with the same dither… only geometry can" separate them. §3: head-switch evidence "is an
   INPUT TO THE GEOMETRY". Circular, with no third observable named.
3. **"Switch-line count" is two different quantities.** §3 defines it with "the partial line included"
   and fixed for the lock; rules 4/8c say "the count that decides is the switch lines OTHER THAN THE
   PARTIAL LINE" and that it "MAY EXPAND". Both feed `d = count − extent`, giving different offsets on
   the same unit.
4. **The head-catch ruling and the line account contradict on the same event.** §1: the line lost to
   the band "counts as normal picture geometry… THE OUTPUT PICTURE DOES NOT MOVE. That last clause is
   the acceptance test." But extent grows by one, `d = count − extent` falls by one, the crop origin
   `23 + d` moves, and §3's two readings of d disagree — all three forbidden. §1 also calls the row
   "normal picture geometry" where §3 says band rows are "not picture".
5. **A box's bars both do and do not participate in the geometry; the picture both is and is not
   recentred.** 8a: bars "change nothing in the account", "never recentred". 8a also quotes "centered
   in the middle, which will correct the geometry". 8b: "as if the box didn't exist". §3 *Crop*: "a
   letterboxed picture is centred".
6. **8c forbids and permits measuring the switch on a boxed source in the same subsection**, and "gap"
   carries two incompatible senses (rows between switch and CONTENT, suppressing measurement, versus
   an interval between the box's BOUNDS and the switch, invalidating geometry).
7. **Negative offsets are mandated, rendered, and unconfirmable.** d ≤ 0 is "confirmed by the comb",
   but the comb does not run under a maintained lock and VBI "can confirm 'displaced by +N' and never
   'at zero'".
8. **§1 is declared non-normative while binding rules exist only inside it** — the coordinate system,
   §4's title ("the owner's, from section 1"), and an acceptance criterion found nowhere else.
9. **Box classification rests on an admittedly unmeasured predicate**, and one-ended structurelessness
   gets three dispositions in one paragraph: "is not a box: that is full picture" / "stays Unknown" /
   "lowers confidence and needs corroboration".
10. **The decision margin has no derivation rule and the gate that deferred implementation is removed**,
    while the document still lists the qualification study as incomplete.
11. **§1 withholds captures 2–4; §8 requires every change to be run against all four.**
12. **Two live coordinate systems disagreeing about specific rows.** The header declares
    field-relative and withdraws frame-continuous; §2's table is entirely frame-continuous; §1 forbids
    "263" while `r+4` produces it. Frame-continuous numbers remain throughout the normative text
    (23/286, 283/284, 22/285, 283–525).
13. **Two classes can only be entered by establishing an absence the document says cannot be
    established** — the invalid class's second condition and rule 10's "not applicable".
14. **The comb both licenses the lock and requires the lock to have happened**, and it both "never
    moves a field" (§6) and selects the alignment (§3).
15. **Source references are discarded on a lock-like loss and rebuilt only after re-acquisition,
    which needs them.** Warm-up is scoped to full resets, which a lock-like loss explicitly is not, so
    the post-loss state has no defined name or behaviour.
16. **A fade is required to be measured, forbidden to be measured, and never classified** — "fade"
    does not appear in rule 5's taxonomy.
17. **On a line-TBC-corrected source the contract adopts the one detector it disqualifies in the same
    sentence**, and the mandated switch test has nothing to measure.
18. **§2 adjudicates the switch line as the partial line; §3's fallback places it on the first full
    other-head row** — the exact error §2 says was corrected.

## MODERATE
19. Rule 4's hold test contradicts itself in consecutive sentences; "band" carries four senses.
20. Rule 2 and 8c disagree on the peak disappearing; rule 2's monotonicity is contradicted by §3's own
    worked example (band grows 3 → 4).
21. Field precedence has three incompatible sources.
22. Where the band is undetectable, rule 4 holds the switch position and rule 2 moves it.
23. Three different lists of when the output may move.
24. "The tape's line 22 never renders" versus the 486 mode that renders lines 20–22.
25. The recorded-row test types a 2.0 ratio that §2, the header and §6 all forbid.
26. "fail open" and "fail closed" each used for both dispositions.
27. §8's capture-1 coverage argument is contradicted by §2's measurement of the same rows.
28. §2's clipping claim is unscoped and conflicts with §1's measured levels on capture 1.
29. A caption is authorized to set d by itself and forbidden to act alone.
30. "Picture rows" called a per-source constant while its count differs per field on every source.
31. "Height" used for both the invariant and the variable quantity.

## MINOR
32. The comparator's definition, its eviction rule and "counts never decrement" are three mechanisms.
33. The invalid class's second condition has no stated consequence for the lock.
34. Undefined terms that gate behaviour: "lift-off point", "jump further than expected", "near an
    edge", "band event", "a source's stable interval", "WELL EXPOSED", "static, detailed picture",
    "0x0800", "comb_safe", normal picture vs program, "qualifying"/"qualified".
35. §2 asserts a symmetric result it says was not measured.
36. §8's render spec names two captures where the acceptance set has four.

---

# Dispositions recorded 2026-09-10 (added after freezing; the findings above are unchanged)

This section records what happened to findings, without editing them. A frozen report stays frozen.

**Not reproduced in the cited version; unsupported as stated.** Findings **27** and **29**. Both were
checked against `4eed79e`, the version this reader reviewed, by both agents independently.
- 27 asserts §8's capture-1 coverage argument is contradicted by §2's measurement of the same rows.
  §8 says capture 1 is line-TBC-off so its switch rows are STRUCTURED; §2 says the flat-row
  separation is categorical, 768 flat with the corrector on against 0 with it off. Those agree, and
  no contradicting §2 measurement was located.
- 29 asserts a caption is authorized to set `d` by itself and forbidden to act alone. Every caption
  site says confirmation. Permission for captions **as confirmation** does not authorize captions
  without geometry.

⚠️ These are NOT recorded as "closed by earlier work": that disposition requires a specific
before/after change demonstrating it, and neither has one. "Not reproduced, unsupported as stated"
preserves the frozen finding without inventing either a defect or its repair (Codex's discipline,
adopted).

**Withdrawn attribution.** Finding **11** cites "§1 withholds captures 2–4". No such text exists in
`4eed79e` either. The conflict it describes is real but sits between §8's all-four regression
requirement and the owner's sequencing ruling; it was repaired there.

**Corrected by the other reader.** Finding **24** claimed rule 7's "the tape's line 22 never renders"
contradicts the 486 mode. Codex's reader called them different objects and, on review, BOTH readings
were wrong: the 486 window follows the displacement (`row = first + d + k - 4`), so it covers lines
(20+d)–(262+d) and the tape's line 22 at 22+d is always inside it. It is destroyed only when the
Shuttle's own rows occupy that raster line, i.e. `d ∈ {−2,−1,0}`. So the universal claim in rule 7 is
false in the 486 mode for `d ≥ +1`. Traced in `experiments/review_render.py`, then MEASURED on capture 2
(the EP recording, which sits at d1 = +2), 200 units:

| row | line | mean | sd between units | |
|---|---|---:|---:|---|
| 18 | 22 | 1.375 | 0.011 | device blanking — the tape's line 22 is **not** here |
| 19 | 23 | 37.710 | 15.60 | the tape's caption at d = +2 |
| 20 | 24 | 60.062 | 29.24 | **the tape's line 22, carrying video, inside the window** |

The 486 window is 243 positions per field at **lines (20 + d) … (262 + d)** (contract §8: "lines 20–262 in each
field"), so at d = +2 it runs 22 … 264-equivalent and row 20 is inside it. (⚠️ This sentence has now been wrong
twice. It first read "covers lines 22–264" — the withdrawn frame-continuous numbering, reintroduced by the agent who
had just removed it from the contract. The repair then read "a 243-position window starting at field-relative line
22", which is the d = +2 INSTANCE presented as the definition: at d = 0 the window is 20–262, entirely inside the
field, crossing no boundary at all. First version lost the convention, second lost the variable, one commit apart,
both inside a note about not doing that. The safe form names `d`.) (Row 17, line 21, reads sd 0.125 —
that is the device's insert carrying re-encoded tape bytes, not pass-through, and it is not evidence
either way.)

---

# The sort: what a wording fixes, and what it does not

Findings divide into two kinds and they need different handling. Most are contradictions — one term
defined twice, two rules disagreeing, a coordinate system used two ways — and those are resolved by
deciding which sentence is right and deleting the other. **Six are not.** They describe rules that
cannot be satisfied as written, and no choice of wording makes a circular or unsatisfiable test
terminate. Those are the owner's to rule on, not ours to word around.

## PILE B — no wording resolves these (for the owner)

**B1 (finding 2). RULED AND FIXED — the specification was circular, not impossible.** As written, separating
blanking from clipped dark content was possible "only by geometry" while head-switch evidence is "an INPUT TO THE
GEOMETRY", so the measurement depended on what it feeds. ✅ Owner, 2026-09-10: "remove only by gemoetry. the head
switch is bad horizontal timing, meaning either picture ending up in the blanking window or blanking ending up in
the picture window. full stop." The clause is deleted and the observable named; nothing is circular and no third
observable had to be invented. Applied at `7029d6a`. ⚠️ My report claimed the test could never terminate; that
overclaimed from an unspecified method, and Codex's reviewer was right to separate the three cases.

**B2 (finding 13). Two classes can only be entered by establishing an absence for which no positive
test exists.** The invalid class's second condition requires "positively established absence of the
unstable-timing region", and rule 10's "not applicable" requires established absence of a head
switch — while §3 says "their absence does not establish absence of the region" and §1 says failure
to measure does not establish a switch-free source. As written, neither class can ever be entered,
and §8's overlay spec requires distinguishing them.

**B3 (finding 17). RULED AND FIXED — the same ruling seen twice.** ✅ Owner, 2026-09-10, asked directly: "huh?
yes it does. head switch (as I've defined it) and/or picture going to the end and/or blanking." What a corrector
removes is the NARROW MARKERS, the partial line's displacement and the RF peak; three observables remain. The
flatness-to-row's-end detector stays deck behaviour and is corroboration, never the definition. Applied at
`7029d6a`.

**B4 (finding 10). A threshold is required, its derivation rule does not exist, and both agents are
forbidden from choosing one.** The procedural gate that deferred implementation until the rule existed
was removed on his instruction; the qualification study it was waiting for is still listed incomplete.

**B5 (finding 4). The head-catch ruling and the line account give opposite results on the same event,
and one of them is his stated acceptance test.** Choosing between them is overriding a ruling, which
is his call rather than ours.

**B6 (finding 9). Box classification gates acquisition and rests on a predicate the document says has
not been measured.** Unlike the others this may be an unbuilt instrument rather than an unsatisfiable
rule — but rules 8a, 8b and 12 turn on it now, so whether they are inert until it exists is a ruling.

## PILE A — resolvable by choosing a wording (for the two agents)

Findings 1, 3, 5, 6, 7, 8, 11, 12, 14, 15, 16, 18 (severe); 19–31 (moderate); 32–36 (minor). Each is
a contradiction, a duplicated definition, a term used in two senses, or an undefined term that gates
behaviour. None requires a ruling: each requires deciding which of two existing statements is the
rule and removing the other, or defining a term the document already relies on.

⚠️ Finding 12 (two live coordinate systems) is in this pile but is the largest single edit, since
frame-continuous numbers appear throughout the normative text while the header declares
field-relative and withdraws them.
