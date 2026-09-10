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
2. **The mandated edge test can never return anything but Unknown, by the document's own statements.**
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
