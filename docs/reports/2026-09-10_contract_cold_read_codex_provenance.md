# Codex contract cold-read provenance

- Reviewed contract: `fb4d7bb:docs/geometry_first_engine.md`.
- Contract Git blob: `cf8cd45149153e80e6164dafa3b9cbc70861d882`.
- Contract SHA-256: `62ba541cf019ab561ce9a55037d00e9df24ec489fd83bd138521b71b42f79597`.
- Neutral snapshot: `/tmp/contract-review.lcdyuA/contract.md`; byte identity checked by Git blob hash before dispatch.
- Reviewer: `/root/contract_cold_review`, spawned with `fork_turns="none"` and no model override.
- Reviewer was instructed to read only the neutral document and to freeze before sharing findings. It was not given the other review, the proposal, the owner's rulings separately, or the parent conversation.
- Isolation is PARTIAL. The reviewer reports automatically inherited repository instructions and project measurements. No claim of stronger isolation than the other reviewer is made.
- The parent had received the user's summary of the other review before dispatch. That summary was not passed to this reviewer. The parent did not open the other review before this report was frozen.
- Frozen artifact: `2026-09-10_contract_cold_read_codex.md`, copied byte-for-byte from the reviewer's scratch artifact without parent edits.
- Frozen artifact SHA-256: `251aa635118512b9cab2b2ec2a465735b53ad351c5fb9b0bf48bafb7c312f788`.
- Aggregate: 13 findings, 4 High / 8 Medium / 1 Low. Severity labels are this reviewer's, not normalized against the other review.
- Any comparison is a subsequent parent analysis in a separate artifact, not part of this independent review.

## Placement review

The parent separately inspected the diff from `4eed79e` to `fb4d7bb`. The earlier content-boundary quotation is now historical, and the signal-state architecture sentence is explicitly labelled operative. This confirms those two corrections, not a whole-contract coherence verdict.

## Workspace checks

No contract, engine, capture, instruction file, or pre-existing untracked fixture was changed. The existing orchestrator-owned tree lock was checked. The initial sandboxed process check returned `zsh:2: operation not permitted: ps`; a permitted escalated read-only process check verified PID 1083 was live. The AGENTS.md symlink remained intact.
