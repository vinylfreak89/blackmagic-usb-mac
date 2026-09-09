# Contract internal-consistency audit — 2026-09-10

A subagent read `docs/geometry_first_engine.md` cold, with no other file and no code, and was asked for
internal logical faults only: direct contradictions, circularity, unsatisfiable preconditions, terms carrying
two meanings, cross-references that misstate their target, settled/open mismatches, and rules that force the
violation of another rule. It also had to trace six scenarios by hand through §4 and say whether the rules
give one answer.

It returned 24 findings. **Every one below was then checked against the cited lines by hand before it was
written down here.** Several did not survive; they are recorded as rejected with the reason, because a
rejected finding that is not written down gets re-raised.

Nothing in the contract was edited on the strength of this audit. Under the v10 process the contract is
edited only by agreement between both agents, and where it is genuinely ambiguous the owner is asked.

---

## Confirmed — these block or mislead

### 1. Rule 8 forbids measuring the quantity rule 8 now requires. **Claude introduced this tonight.**

`:443-449` — "**A head switch separated from the picture by a gap is not measured** … **A box's own band IS
that gap**", and `:338` — "a boxed picture's framing below the gap is deliberately unmeasured under rule 8."

`:453-458` — "if the two numbers on geometry LINE UP (**the head switch band** and the boxed geometry), then
this is valid geometry and can write a new picture".

On a boxed picture the head switch is not measured; the acquisition test compares the head-switch band against
the boxed geometry. An unmeasured band has no value to compare. The two sit eleven lines apart inside one rule.

This is the owner's 2026-09-10 ruling written on top of his earlier one without reconciling them. Two readings:
(a) the newer ruling supersedes "not measured" for the box case — the switch is measured on a boxed picture and
the gap rule applies only to a switch below ordinary video; (b) the switch stays unmeasured and "the two numbers"
means something other than the band. Reading (a) is the one his words support ("a measurable head switch is
evidence FOR a lock"), but choosing between them is his call, not ours. **Owner decision.**

Also uncovered: the document never says what "the two numbers" are. The band has an extent, a top switch line
and a count (`:280-282`, `:295-296`, `:297-298`); the box has bands at both ends (`:429-430`). Which pair is
compared, in what units, is not stated.

### 2. The boxed-acquisition path contradicts what a lock's confirmation may be. **Claude introduced this tonight.**

`:325-326` — "**Source lock**: exists only after at least one confirmation that the geometry is correct —
combing, captions, or both".

`:458-460` — "**Agreeing, they are valid geometry and MAY set a new acquisition** … Disagreeing, the unit holds
and may not acquire."

The agreement path offers two *geometry* observations and no comb and no caption. Rule 4 (`:392-393`) permits
that; §3 Source lock forbids it. Same unit, opposite verdicts, and the verdict decides whether the output
picture may move. **Owner decision.**

### 3. The switch-line count has no seed, and that is what blocks capture 1.

`:293-294` — "When the top reads line 23 … (a **clamped top**) … d = the switch-line count minus the band's
extent (≤ 0)".
`:297-298` — "**Switch-line count**: … **taken at the confirmed unit** and kept for the lock (never re-learned)".
`:392-393` — a lock is acquired on two or more observations, **at least one of which must be geometry**.

For a source whose top reads line 23, d can only be read as count − extent. The count exists only from the
confirmed unit. The confirmed unit requires geometry, i.e. requires d. Neither can go first.

**Capture 1's reference reads top = 23 in 508 of 508 units in field 1 and 286 in 508 of 508 in field 2**, so it
is the clamped-top case throughout. The contract does not say how the count is seeded at a first lock.

⚠️ **Corrected after Codex checked its own engine (2026-09-10).** This entry first said the circularity is "the one
on capture 1's critical path". That is not supported and is withdrawn. The engine already bypasses the deadlock
with an implicit seed: `field_registration.c:436` computes `visible_d = top - origin` and then
`observed_count = extent + visible_d`, so a top at 23/286 yields d = 0 and count = extent without ever
distinguishing a clamped top, and that count is installed at confirmation by both acquisition paths
(`:628` comb, `:882` caption). Codex: "the contract circularity is **not a literal acquisition deadlock in the
implementation** … It therefore cannot alone explain zero commercial locks."

What survives, and both agents agree on it: the engine's seed is an assumption the contract does not authorize.
Standard fallback placement (`:365`) does not make zero an *observed* geometry, and rule 4 requires the
acquisition's geometry to be an observation. So the gap is real and it is the owner's to settle — but it is a
correctness question about what the first lock is entitled to assume, not the explanation for capture 1 failing
to lock. That explanation is still open. **Owner decision.**

The same shape, smaller: the band's extent runs "to the clip" (`:295-296`) and the clip is "measured per source
as the last recorded row's **constant**" (`:308-310`). A per-source constant does not exist at unit 1.

### 4. A switchless source that is not boxed and whose picture does not reach the last row can never lock.

`:54` (owner, §1) — "Some recordings show no head switch at all … **so a lock must never be conditioned on one.**"
`:334-338` — "a source lock requires a measurable head switch line and band **only where the geometry is not
boxed and not all lines are picture**."

The exemption covers boxed sources and full-raster pictures. A switchless source that is neither — a line-TBC
pass with torn timing below the picture, which is exactly the case `:54` names — falls outside the exemption and
is therefore conditioned on a head switch it does not have. That is the conditioning `:54` forbids.

Downstream, such a source also loses rule 3's picture bottom ("the row above the switch line", `:391`), loses
"Picture rows = 240 − switch-line count" (`:301-302`), and loses the clamped-top branch of d (`:293-294`). No
alternative is given for any of them. **Owner decision.**

### 5. §2 forbids a typed ratio for the recorded-row test; §3 types one.

`:173-174` — "The Shuttle's regenerated rows and recorded rows separate on chroma noise …, with a clear gap
between them; **the separation, not a typed ratio, is what the recorded-row test uses**."
`:198-199` — "**Recorded row**: … chroma noise **above twice the blanking rows'** (section 2's measured gap, the
test set at its lower bound)".

§3 cites §2 as its authority for a number §2 refuses to supply — and §2 stated its gap without a value ("a clear
gap between them"), so the citation could not supply it either. By the document's own rule at `:8-9` ("Every number
is a standard, a measurement on the captures (stated with its value), or a memory capacity; any other number in
the code is a defect") the typed 2x was a defect.

✅ **Settled by both agents, 2026-09-10, and the contract is edited.** §2 now states the measured values (regenerated
rows at most 1.48x the blanking rows', recorded rows at least 2.02x). Codex made one correction to the proposed
wording that was worth having: **2.0 is not the gap's lower bound** — the lower bound is 2.02 — so §3's claim that
the test is "set at its lower bound" was itself false and is replaced by "sits inside that observed gap, and NOT at
its lower bound". The engine's `>2.0x` at `field_registration.c:405` is unchanged; this documents an existing
measurement-backed threshold with no behaviour change. Neither agent re-measured the gap this turn; the values are
the ones recorded in CLAUDE.md.

### 6. Rule 6 gives no way to tell ordinary VHS flagging from disqualifying horizontal damage.

`:416-417` — "**A unit carrying a horizontal timing error other than its own head switch may not be the confirmed
unit**: it holds, and the lock's constants are taken from a clean unit".
`:153-157` — flagging is measured as a property of **a VHS field's first lines**, present on every unit.

Read literally, no VHS unit can ever be the confirmed unit. §9 closes the case in the other direction —
`:610-612` "the V-stabilize-off pass's flagged first lines are recorded, non-VBI rows and therefore picture; the
top is read through the flagging" — but rule 6's operative text carries no magnitude, extent or duration
separating the two, and §6 (`:499`) forbids inventing one ("no thresholds that are not a stated measurement").

The audit's stronger claim — that no source can confirm at all — is **rejected**: §9's closure governs ordinary
flagging. What survives is the missing discriminator in rule 6's own text.

### 7. Rule 10 mandates a distinction with no method.

`:482` — "Not applicable (no head switch on the source) is distinct from unmeasurable."

A switchless source and a source whose band is unmeasurable present identically at every unit. Nothing in the
document says how "the source has none" is established, and the two answers route differently through §3 Source
lock (`:334-339`) and through the deliverable render (`:549-550`, "absent where the band is not measurable and
omitted where the source has none"). A numbered rule with no test behind it.

### 8. The crop after a reset has two answers, and they differ by a visible jump.

`:405-406` (rule 5) — "the engine measures nothing and places nothing … **the crop stays where it was**".
`:365` (§3 Crop) — "**before a lock, standard placement**."
`:424` (rule 8) — "The output picture never moves except at a segment's initial lock and after a re-acquisition".

At the unit where picture returns after a lock-like loss, the signal-state layer reports program again and there
is no lock. `:365` puts the crop at standard placement, which moves the visible picture at a unit rule 8 does not
permit; `:405-406` holds a crop derived from a lock that `:407-408` destroyed. §8's "nothing is placed on snow"
(`:522-523`) supports the hold. The document does not choose.

### 9. §8's top-is-constant invariant is checked over an interval it does not define.

`:520-524` — "through **a source's stable interval** the top is constant … **The units at which each holds are
read from the run, not written here.**"

An invariant whose scope is read from the run it is checking cannot fail, and it is the pass/fail criterion for
all four acceptance captures. (In practice the harness has been reading it over the whole registerable range,
which is a stricter test than the text requires — capture 1 passed it at 0 violations. The gap is in the wording,
not in what was run.)

---

## Real but lower consequence

- **A zero comb reading is claimed to confirm a lock it cannot confirm.** `:367-368` — "it confirms a lock when
  it reads zero at the placed crops"; `:373-374` — "The comb constrains the two fields' relative registration
  only, so where both fields are ambiguous by the same amount it cannot decide and there is no lock." A zero
  reading confirms the *relative* registration and says nothing about a common-mode displacement, so `:367` is
  too strong as written and could license a wrong lock on a commonly-displaced source (the EP recording at
  (+2,+2) is exactly that source, and its comb census abstains for exactly this reason).
- **"The placed crops" is undefined** (`:367`). Read as *standard* placement it deadlocks any unequally displaced
  source; read as *the crops geometry proposes* it works. The audit called this a circularity; on the natural
  reading it is not one, but the term should be pinned. The three-candidate re-measure at `:371-372` is supplied
  for one case only.
- **"at least three rows long"** (`:239-241`) decides whether a unit is a full lock-like reset, and is not a
  standard, not a stated measurement, and not a memory capacity — a defect by `:8-9`. Owner-accepted 2026-09-09,
  so it may be intended as his constant; it is not sourced as one.
- **Rule 4 holds the switch position where §3 records it Unknown.** `:396-397` "the head switch's POSITION LINE
  is HELD" against `:277-278` "the unit's switch line is Unknown". Different values in the same record column
  (§5, `:487-488`).
- **"Regenerated rows" names two row sets**, both wired to a lock-like loss: the blanking rows 7–15 / 270–278
  (`:200-201`) and the timing/insert lines 20/21 and 283/284 (`:352-355`). §2's table (`:128-130`) lists the
  first unconditionally and the second "when its decoder has sync", so the trigger at `:356-357` either never
  fires or fires on every sync loss depending on which set is meant.
- **On a boxed unit "picture row" takes two values.** `:425` "a boxed picture's bars are recorded picture rows
  inside the 240 and change nothing in the account" against `:430-431` "the top of the picture SHOULD be the
  'WARNING' label". If the bars are picture rows, §3's picture top is the first bar and there is no boxed
  geometry to compare in finding 1's test.
- **Box classification is load-bearing and its measurement is admitted not to exist.** `:432-433` states the
  predicate; `:439-442` says "What makes a region structureless is a measurement neither agent has yet". "Box"
  appears nowhere in §3 Definitions.
- **"Centred".** `:364-365` "a letterboxed picture is centred" and `:431-432` "centered in the middle, which
  will correct the geometry" against `:462-463` "is never recentred" (added tonight from the owner's ruling).
  `:425-426` tries to hold both with "centred as the source centred it". The words are reconcilable; an
  implementer reading only §3 Crop would centre the box.

## Rejected after checking

- **"The comb can never confirm, so no source can ever lock."** Depends on reading "the placed crops" as standard
  placement. Rejected as a deadlock; kept above as an undefined term.
- **"The all-lines-are-picture waiver leaves the top as the only evidence, which `:333` forbids."** Over-read: the
  waiver removes the switch as *geometry*; comb or captions still supply the second observation, and `:333`
  forbids a unit confirming *only* the top.
- **"Rule 6 disqualifies every VHS unit from confirming."** Over-read; §9's closure at `:610-612` governs ordinary
  flagging. The narrower gap is kept as finding 6.
- **Cross-references.** The audit checked every "rule N" and "(section N)" pointer and found none that misstates
  its target. Independently spot-checked at `:294`, `:388`, `:412`, `:470`, `:472`.

## Scenario verdicts, as returned and as checked

| scenario | verdict |
|---|---|
| A. first unit, nothing locked, switch measurable | ambiguous — two answers for the applied crop; the count is circular (finding 3); the clip constant is uncovered at unit 1 |
| B. source with no visible head switch | contradictory — three different answers depending on the passage read (finding 4) |
| C. box agrees, then disagrees, then fades | uncomputable at stage 1 (findings 1, 2); the fade's first unit is ambiguous by the contract's own admission (`:437-438`) |
| D. torn raster after a lock | horizontal tearing: one answer. Vertical tear: ambiguous — whether the tear detector sits inside rule 5's gate is uncovered |
| E. twenty units of snow, then picture | ambiguous — the crop during and after has two answers (finding 8); re-acquisition needs a horizontal-phase distribution `:231-232` says is rebuilt after re-acquisition |
| F. comb confirms, geometry unmeasurable | **one answer.** Rule 1, rule 9 and §6 agree: the crop does not move, the position is Unknown, the comb reading is recorded. The only scenario the rules resolve cleanly |

