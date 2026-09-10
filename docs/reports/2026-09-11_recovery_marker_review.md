# R3 recovery marker: answer and scope

Reviewed harness `1137caca5653bc4dda73d63501b1c9410f2e35a1`, merged as
`b21587b6d29ad4abc07b57662081e67613998592`. Its commit message and queue entry claimed the marker had
already been removed, but the contract was unchanged from `1d124e9`. The dispatch explicitly retracts that
claim. This amendment actually replaces the marker and updates its live queue dispositions together.

## Agreement and corrected proof

YES: a new lock is required before corrective placement resumes after the terminal-black-run invalid-raster
condition. Until acquisition, the general Crop rule requires standard placement. The answer is stated at the
former marker rather than left for another reader to derive. No new owner question is dispatched; my earlier
request for a recovery ruling is withdrawn.

The local owner ruling supplies the premise: "if that condition appears, the whole lock gets reset. it starts
from scratch. that was an invalid signal". The subsequent instruction that registration must not run on invalid
input does not say to preserve the lock expressly reset by that sentence. Inactivity alone would not establish
recovery, but it is not the only evidence in this passage. The proof is LOCAL lock reset plus the GENERAL
pre-lock standard-placement rule, not the scoped one-field-switch instruction.

Rule 13 cannot bear the broader inference in the proposal. Its triggers are `0x0800` or positively absent
regenerated rows. The other invalid-raster condition is a qualifying terminal-black run plus positively absent
head-switch region; its definition does not require either rule-13 trigger. Therefore the proposed assertion
that only transport unit counts survive this different condition does not follow from rule 13. This amendment
does not add a full-engine reset cause or prescribe a storage-erasure mechanism. Rule 13's existing triggers,
enumeration of discarded state and reference-reacquisition requirements remain unchanged.

The owner's words were checked in the repository's recorded quotations. They arrived by relay; the original
transcript was not independently checked in this review. The peer's connective explanation is evaluated as
reasoning, not treated as another owner ruling.

## Boundaries of this change

Only the recovery-marker paragraph changes in the contract. The during-invalid disposition, BOTH-unrecordable
gate, transport timing/status preservation, general Crop rule, rules 8a–8d/12/13, source-level basis and render
requirements are unchanged. Unknown switch evidence with recordable valid picture still does not trigger the
BOTH-unrecordable gate. No engine implementation, measurement instrument or render is changed by this amendment.
The requested merge brings the peer's instruments into this branch; this review does not adjudicate them.

The contract/queue check now finds zero recognized owner markers and zero anchors. That is a statement about
the forms it recognizes, not proof that every prose question or implementation task in the repository is closed.
The old reports keep their historical then-open status; the live queue and CLAUDE.md give the current answer.

## Validation, including failures

`git diff --check` passes. The contract diff contains just the marker-to-answer replacement; rule 13 and the
general Crop rule are unchanged. `AGENTS.md` remains a symlink to `CLAUDE.md`. No engine tests or capture replay
were run for this documentation-only amendment.

`python3 experiments/owner_queue_check.py` exits 0; relevant output verbatim:

```text
contract markers found: 0
queue anchors: 0

Every contract owner-marker has a queue row, and every queue anchor still lands on one.
NOT proof that no question is elsewhere -- see the docstring.
```

Its selftest passed before removing the last marker, but
`python3 experiments/owner_queue_check.py --selftest` now exits 1:

```text
SELFTEST
  negative control (live tree): expect clean ... PASS
  positive 1: UNAVAILABLE -- no queue row matched the expected shape
  positive 2: UNAVAILABLE -- no queue anchor's quote was found in the contract
  positive 3 (a new marker, never mirrored): expect FAIL ... PASS
  positive 4: UNAVAILABLE -- no queue row matched the expected shape
SELFTEST FAILED
```

The controls now derive targets from live questions, but still require at least one to exist. Closing the last
question makes three controls unavailable. An isolated paired marker/anchor fixture is needed for those
mutations when the live set is empty; the real empty-set check should remain. Do not restore an answered
question to keep the controls alive. This is harness follow-up, not a reason to retain the marker.

`python3 experiments/superseded_check.py` exits 0, checking 16 supplied phrasing pairs only. Its selftest fails
both BEFORE and AFTER this amendment. `python3 experiments/superseded_check.py --selftest` exits 1:

```text
SELFTEST
  negative control (current contract): expect clean ... PASS
  positive control (e6b224f, defect live): expect FAIL ... FAIL -- the check cannot see the defect it exists for
SELFTEST FAILED
```

The incoming change retires the B2 pair from `PAIRS`, but the historical positive control still relies on that
pair to detect `e6b224f`'s defect. Current obligations and historical regression fixtures need separate scope:
retiring a current question need not erase the historical detector from its own test. This failure predates the
recovery edit and is not reported as green or silently repaired in a contract-review change.

## Publication blocked

The requested merge and amendment are committed locally. The push to `origin/v10-engine` was rejected before
execution by the approval system; it has not been retried or routed around. Rejection reason verbatim:

```text
This action was rejected due to unacceptable risk.
Reason: Pushing the newly created recovery amendment would export sensitive project documentation to an untrusted remote, but the user authorized pushes generally rather than this specific newly applied contract change and payload.
Do not bypass this rejection through a workaround or indirect execution. Continue with a safer alternative, or carry out checks to prove that the action is authorized or low risk before trying again. Complete unaffected work without asking for confirmation. Report anything that remains blocked, clarify why it was blocked by auto-review, inform the user of the risk and ask for approval.
```

Explicit approval to publish this amendment and its documentation is requested in the handoff. This is the
approval system's risk assessment, not an independently established finding about the remote's trustworthiness.
