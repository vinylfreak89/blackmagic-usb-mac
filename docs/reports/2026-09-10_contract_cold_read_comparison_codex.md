# Contract cold reads: comparison after freezing

This is the parent agent's comparison, not part of either independent review. No contract repair or acceptance decision is made here.

## Inputs and limits

- Codex reviewer: `2026-09-10_contract_cold_read_codex.md`, frozen in `95174e8`, reviewing `fb4d7bb`; 13 findings (4 High, 8 Medium, 1 Low).
- Other report: `45ce2ae:docs/reports/2026-09-10_contract_cold_read.md`, reviewing `4eed79e`; 36 findings (18 Severe, 13 Moderate, 5 Minor).
- The other report was opened only after the Codex review had been frozen, copied unchanged and committed. The parent had previously received the user's summary of several other-side findings, but the no-history reviewer did not receive that summary.
- Both reviewers report PARTIAL isolation because repository instructions were automatically inherited. This comparison makes no claim that either review deserves more weight on isolation grounds.
- The other report says its reviewer had a stale first read and omitted findings already fixed in its later snapshot. That is a provenance difference to retain, not a reason to dismiss its findings.
- The snapshots differ by the two quotation/status placement fixes in `fb4d7bb`. Agreement counts and severity totals are therefore not directly comparable. The original other-side report is used, not subsequent sorting or interpretation of its findings.
- The other report often supplies short summaries rather than exact line evidence. The mapping below is by issue, not a claim of identical proof or severity.

## Findings reached along related routes

| Codex finding | Other finding(s) | Relationship |
|---|---|---|
| CR-01: live coordinate and provenance table conflict | 12 | Direct overlap on live coordinate schemes. CR-01 additionally identifies written rows included in the source/pass-through range. |
| CR-03: head-catch movement versus count equations and acceptance invariants | 3, 4, 19, 20 | Substantial overlap. The other report separately identifies partial-included versus partial-excluded counts; Codex did not freeze that as a standalone finding. Its algebraic head-catch consequence overlaps directly with 4. |
| CR-04: TBC definition preserves and removes displacement | 17 | Related, not identical: Codex isolates conflicting descriptions of the observable; the other report makes a broader detector-disqualification claim. |
| CR-05: fixed recorded-row noise ratio versus per-source derivation | 25 | Direct overlap. Neither review demonstrates that the ratio is wrong on the measured fixtures. |
| CR-08: references rebuilt after reacquisition although needed beforehand | 15 | Direct overlap on lifecycle ordering. Codex explicitly allows that a different meaning of reacquisition could reconcile the text. |
| CR-09: acquisition-only engine comb versus unscoped validation requirements | 7, 14, 23 | Related phase/interface concerns, not identical findings. Codex allows an independently running harness comb and requests explicit responsibility/scope. |
| CR-10: box/bar gap versus switch measurability | 6 | Direct overlap, surviving the placement fixes. The current rule and explanatory history still admit competing readings. |
| CR-11: recorded non-VBI row definition includes excluded switch rows | 4, 30 | Related row-account vocabulary, but the precise classification overlap is distinct. |

## Distinct findings in the Codex report

These are not separately stated in the other report, though some concern adjacent subjects:

- CR-02: a specific head-catch implementation prohibition remains despite removal of the earlier procedural gates. This is distinct from the other report's 10 (missing margin procedure) and 11 (capture-order issue).
- CR-06: a provenance-error unit must emit no engine record, while damage accounting requires an Unknown record and rendering requires sidecar alignment.
- CR-07: the definitions imply `span + extent = clip - 22`, while the asserted identity fixes the sum at 240 and therefore silently requires clip = 262. A variable measured clip needs an explicit missing-tail term or a different extent definition.
- CR-12: picture anywhere inside the held outer box is already normal; the invalidation trigger needs to distinguish newly appearing content in a previously identified bar region from ordinary existing content inside the box.
- CR-13: the blanket ban on windows conflicts with expressly required local spatial measurement windows unless its prohibited scope is named.

## Other-side findings without a matching frozen Codex finding

Other-side IDs: **1, 2, 5, 8, 9, 10, 11, 13, 16, 18, 21, 22, 24, 26, 27, 28, 29, 31, 32, 33, 34, 35, 36**.

They cover detector precedence, claimed identification impossibility, centering, normative status, box classification, margin derivation, acceptance ordering, absence tests, fades, T/S fallback, field precedence, held versus moving boundaries, rendering, fail-open terminology, measurement scope, caption authority, height/comparator definitions, invalid-state consequences and render-spec coverage. Absence from the Codex list is not a rejection or a finding that the issue is resolved.

In particular, other-side finding 5 must be compared with the version difference: the older content-boundary quotation was moved into history in the snapshot Codex reviewed. That accounts for part of the differing evidence, not necessarily all of the centering concern.

## Explicit differences in interpretation

1. **An unnamed method is not proof of impossibility.** Other-side finding 2 says the mandated edge test can never yield anything but Unknown. Codex explicitly declined that inference: the file says brightness evidence alone is insufficient and protects unresolved cases, but an unspecified positive timing-identification method is not proof that none can exist. A possible circular dependency should be stated and tested as a dependency, not promoted to universal physical impossibility. Head-switch evidence being an input to geometry does not itself make it the sole possible input to geometry.
2. **Positive absence and failed detection differ.** Other-side finding 13 should retain the distinction between a missing operational absence method and a proof that positive absence is impossible. Both reviewed text and Codex qualifications expressly preserve Unknown.
3. **One observed bound and one undetected bound are different cases.** Codex did not count the three outcomes in other-side finding 9 as necessarily inconsistent. Positive one-sided geometry, an unresolved second bound, and the need for corroboration must be tested under their stated conditions. Missing qualification details may still be a specification issue.
4. **Tape lines and a generated-row review view need not conflict.** Codex explicitly did not count the blanket rendering contradiction in other-side finding 24: the tape's own line 22 and the device-generated inserts in a diagnostic view are different objects. Any remaining conflict must identify the same object and output mode.
5. **Observation during a fade is compatible with holding geometry.** Codex did not endorse other-side finding 16's claim that fade observation is forbidden. The current rule 5 distinguishes suspended registration from continuing observation. Whether the signal-state taxonomy adequately represents fades remains a separate question.

These are parent comparisons of frozen statements. They do not amend either report or turn either into a pass/fail verdict.

## Disposition

The independent review is preserved unchanged. The two placement fixes at `fb4d7bb` are confirmed; whole-contract coherence is not asserted. Shared findings, distinct findings and disputed inferences should remain separate when planning repairs. No implementation, capture run, or contract amendment was made during this review.

## Read/commit diagnostics

The first attempt to open the other report at the reviewed contract commit returned:

`fatal: path 'docs/reports/2026-09-10_contract_cold_read.md' does not exist in 'fb4d7bb'`

It was subsequently located at its original report commit `45ce2ae` and read there. The first sandboxed attempt to commit the frozen review returned twice (once for staging and once for committing):

`fatal: Unable to create '/Users/vinylfreak89/Documents/blackmagic-usb-mac/.git/worktrees/blackmagic-v10/index.lock': Operation not permitted`

An approved elevated retry succeeded as `95174e8` before the other report was read.
