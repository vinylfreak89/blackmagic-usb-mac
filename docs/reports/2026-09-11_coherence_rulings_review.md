# Review of the owner-ruling proposals after the plain-comb change

Reviewed harness commit `70c67464b4dc10b68bdda66c2d4bb6b8e85a6809`, merged into the engine branch as
`c9dbddf1b2bff5db32bfdafcd670edaf434564e5`. The engine under review is the plain-comb implementation
`2a06c9e9f655d9a371d58292e4eae4ab6533c6b9`; the merge did not change that engine or the contract.
This is adjudication, not implementation or a render review. Owner quotations below were supplied through
the peer's dispatch; the full coherence quotation in Part 2B was supplied there, not independently located
verbatim in the merged files. The peer's new capture censuses were not remeasured by this review.

The subsequent withdrawal of Part 2C governs this review: no line-number amendment, fixed-position search,
or new owner question is proposed for 6(b). The instrument is unchanged.

## Part 1: the proposed contract amendments

**Invalid raster / R3: agree to narrow the marker, not erase the recovery question.** State that positively
established invalid NTSC is outside registration's operating domain. An uncertain measurement of a valid
raster is not that condition. Keep the owner's two statements together; engine inactivity does not establish
that retained state is valid, discarded, or irrelevant when processing resumes. Do not import rule 5's
held-crop behaviour, nor claim that an inactive registration engine specifies the downstream output by itself.
The already queued question remains: when good video returns, must it find a new lock before correcting again?

**Absence / R2b: agree to the positive timing test; amend the claim that it dissolves observability.** Compare
the line's timing against its own horizontal blanking. Positively established normal placement of picture and
blanking establishes absence of the head-switch-like timing error; failure to detect relocated blanking does
not. Retain the owner's location qualifier, bottom before **deck, device or other blanking**, rather than
narrowing it to regenerated blanking alone. Elsewhere the skew is ordinary horizontal tearing. A ruling
specifies the test; it does not establish that the current instrument can answer it on every sample. Censored
or unresolved observations stay Unknown. This is not approval of `own_blanking_census.py`.

**Caption-only precedence: agree to valid VBI as the owner-named evidence, with provenance and coordinates
explicit.** The amendment must say what it means for line 21 to be at 21 in both fields and 22 to be blank in
both: source VBI evaluated against the candidate placement is not interchangeable with the Shuttle's generated
21/22, or with 21/22 composed by the renderer. The existing rewind control already excludes generated-row
presence alone as source-lock evidence. If the intended new rule is that generated VBI alone supplies the
missing interleave evidence, that conflicts with an existing rule and needs an explicit owner resolution;
do not infer it from the short answer. Keep physical field/time identity, crop interleave, and the comb's
calibrated zero distinct. A caption-only interleave decision does not silently manufacture a comb calibration.

**The exclusion of a peak or partial line: agree to repair the existing definition and absence clause
together.** An identified head-switch peak/partial row can constitute a valid one-line region. No full
other-head successor row is required to make that region exist. An arbitrary amplitude extremum is not thereby
identified as an RF switch peak. Remove the exclusion rather than adding its opposite beside it.

**The “nothing above 23 reaches us” sentence: amend the object/coordinate scope, not the device-origin
measurement.** The very next sentence describes tape line 22 reaching delivered line 23 at +1, tape line 21
reaching 23 at +2, and tape line 21 reaching 24 at +3. Thus the first sentence is overbroad as written. Suggested
replacement substance: at zero displacement those tape VBI positions are overwritten, except for decoded and
re-encoded caption bytes; identified tape VBI that survives displacement into the pass-through window remains
available for placement on its proper 486 output lines. The output instruction does not establish survival in
the Shuttle's delivered lines 20–22, and overwritten samples cannot be recovered by changing their labels.
This is a separate provenance/render amendment from the one-line head-switch repair; both may share a commit
after their actual replacement wording is agreed. Neither licenses an unreviewed rewrite of all 480/486 rules.

## Part 2A: one-sided motion

Agree with the owner's operative consequence: a one-sided change in the geometry being tracked does not
authorize a displacement or break the lock. It should be implemented as one coherent disposition, with tests
for both the applied placement and retained lock. But the claim that current code exhibits both failures is
not reproduced. One is active; the named second path is historical.

`v10_decide_field` applies `measurement->top - origin` without requiring a corresponding bottom movement.
`expected_bottom` contributes to loss reporting, not authorization of that move. A diagnostic using the existing
synthetic `comb_test.c` fixture acquires at (0,0), then changes only field 1's first delivered picture row to
blank. The result is:

```text
before f1 top=23 bottom=259 applied=(0,0) lock=1
top-only f1 top=24 bottom=259 applied=(1,0) lock=1 reason=SwitchCountConflict comb=not_evaluated
```

This falsifies one-sided placement holding on a constructed input. It does not claim a measured capture event.
The lock survives, and the comb correctly is not evaluated under the maintained lock. Searching current
`src/field_registration` for `FIELDREG_MODE_LOCK_BROKEN` finds only its enum declaration and display-name case,
not an assignment. There is a separate live reset on `box_detected` in `fieldreg_process`; that is not proof
of a generic top-only `LockBroken` disposition. Do not repair a historical path as though it still executes.

The diagnostic was compiled with the current engine and CEA-608 implementation (`clang -O3 -std=c11
-Wall -Wextra -Werror ... -lm`) and exited zero while printing the falsifying result. Its complete scratch
translation unit, reproducible against the reviewed tree, was:

```c
#define main historical_comb_main
#include "/private/tmp/blackmagic-v10/src/field_registration/tests/comb_test.c"
#undef main
int main(void)
{
    fieldreg_init(&engine, NULL);
    make_unit(0, 0, false);
    fieldreg_decision before = run();
    for (int x = 0; x < 720; ++x) {
        unit[48 + 19 * 1440 + 2 * x] = 128;
        unit[48 + 19 * 1440 + 2 * x + 1] = 2;
    }
    fieldreg_decision after = run();
    printf("before f1 top=%d bottom=%d applied=(%d,%d) lock=%d\n",
           before.field[0].raw_top + 4, before.field[0].raw_bottom + 4,
           before.applied_d1, before.applied_d2, before.geometry_lock_known);
    printf("top-only f1 top=%d bottom=%d applied=(%d,%d) lock=%d reason=%s comb=%s\n",
           after.field[0].raw_top + 4, after.field[0].raw_bottom + 4,
           after.applied_d1, after.applied_d2, after.geometry_lock_known,
           fieldreg_mode_name(after.field[0].reason),
           fieldreg_comb_check_name(after.comb_check));
    return 0;
}
```

The implementation must track the same identified geometry through time, with its uncertainty and censoring.
An endpoint that is Unknown is not an endpoint positively observed stationary. Nor are a content edge, the
head-switch partial row and the delivery clip automatically the same bottom landmark. The existing head-catch
ruling permits independent switch motion. Requiring two newly measurable endpoints on every unit would also
silently restore a mandatory-switch requirement where the owner expressly removed one.

The v9 caption regression is relevant history, not authority to restore v9 placement policy. A positively
identified tape VBI landmark is different evidence from a dark top crossing a level threshold. Preserve that
distinction and the owner's explicit VBI exception; do not let caption presence override positively conflicting
geometry, which the current Source lock definition forbids.

**One scope question remains before a blanket amendment.** Rule 8a releases geometry on a bar edge moving at
steady exposure and on picture positively appearing in a previously identified bar; rule 12 releases its lock
after such invalidation. “Any one-sided movement never unlocks” would also cover these unless the tracked
outer geometry and the box's internal bar/content boundaries are distinguished. Recommended reading: hold
placement and lock for unilateral tracking changes; preserve independently established box invalidation and
source-loss rules. Whether the new ruling instead removes the existing box-invalidation release is an output
policy question, queued in plain words rather than decided by this review.

## Part 2B: coherence and the positive default

Agree that picture filling the delivered field supplies its geometry candidate without demanding a switch;
this is consistent with rule 11's existing full-window seed. It is not a measurement that no earlier tape
picture was overwritten. Keep the candidate, confirmation and maintained placement distinct. The current
engine now can acquire through plain comb without a measurable switch, but its top-only tracking decision
above fails the new coherence obligation; it does not retain a qualified bottom counterpart for that decision.

On the comb route, the first confirming comb establishes the retained placement. “First comb” must not become
a mandatory extra confirmation on the still-permitted caption route. Under a maintained lock the comb remains
off. Coherence is required of the identified geometry, not the incidental positions of every dark edge.
Preserve the owner's “262,263” wording if quoted, but do not introduce field-relative line 263 into operative
coordinates: the current device pass-through window is 23–262 in each field; field 1's 262.5 is written blanking.

## Subsequent withdrawal and the remaining measurement limit

Part 2C's proposed correction is withdrawn, not renumbered: the owner was naming the **tape's line 22**, not
delivered row 22. Its observed position, wherever the identified object survives inside the picture, is a
readout. No replacement with line 23, the withdrawn field-2 label 286, or “first pass-through position” is made
or proposed. No owner question about that line identity remains.

Separately, the quoted 0.48 versus 2.24–47.08 whole-row standard deviations are not yet a validated tape-blanking
identifier. Across-row variance includes picture structure, edges and horizontal blanking, not just noise.
Ordinary source picture can differ strongly from synthetic device blanking while containing no tape VBI at all.
“Different from the device control” does not establish “this is the tape's blanking”, much less its line identity.
The instrument and observations can remain; the identity/uncertainty test needs appropriate source-blanking and
ordinary-picture controls. No threshold or new detector is implemented here.
