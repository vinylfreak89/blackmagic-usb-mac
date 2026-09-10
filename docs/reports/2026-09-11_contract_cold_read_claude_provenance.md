# Claude-side cold-read provenance (round 2)

- **Reviewed contract:** commit `5eb9be2`, `docs/geometry_first_engine.md`, 1,383 lines.
- **Git blob:** `6696fd56dea669cfa0796783c4492ba49f9c5bb7`
- **Contract SHA-256:** `3631179a762a55e124a688bbdf81cea05d0254b8d6a540da413686109e6472c4`
- **Independently matched:** Codex froze the same commit separately and reported the same blob and SHA-256;
  this side derived both from git rather than copying them from Codex's message. The watchdog session
  verified them a third time.
- **Neutral snapshot:** extracted by `scripts/freeze_contract`, which re-hashes its own extract against the
  commit's blob so a drifted working copy cannot pass.
- **Frozen report:** `2026-09-11_contract_cold_read_claude.md`, copied byte-for-byte from the reviewer's
  artifact with no parent edits.
- **Report SHA-256:** `f2994a8ef174f5b46a9f7b2559fe6c4c182bbb37c5bc89c2990f6ad5e94aeff3`
- **Aggregate:** 27 findings — 11 placement/loss-accounting/mathematical-validity, 11 affecting a decision or
  an operative rule, 5 narrower scope or documentation. Severity labels are this reviewer's and are NOT
  normalized against any other review.

## Reviewer and what it was given

- A `general-purpose` subagent (Opus), spawned with no conversation history.
- **Given:** the snapshot's path; instructions to read that file alone, cite by line number, rank by
  consequence, not to propose repairs, and to state its isolation honestly.
- **NOT given:** either previous cold read; this side's 36 findings; Codex's 13; the proposal document; the
  tracker; the owner's rulings as a separate list; any part of the conversation that produced the edits.

## Isolation — PARTIAL, and worse than the previous round's, stated by the reviewer itself

The reviewer reports that the following reached it automatically before it opened the target file: the
global `CLAUDE.md`; **the project `CLAUDE.md`, which discusses this exact contract, quotes the same owner
rulings and records the same disputes**; a memory index; and git status including two commit subjects naming
matter it reports on. Its own words: *"several of the areas I examined were foregrounded for me before I read
a line of the target file"*, and *"'I did not cite it' is not 'I did not know it' — the honest description of
this read is informed, not cold."*

⚠️ **This is a materially weaker isolation than the phrase "cold read" implies, and it is recorded here rather
than discovered later.** It bears directly on any comparison: findings in the foregrounded areas cannot be
treated as independent corroboration of the same findings from the other side.

## Parent exposure

**This parent had read BOTH earlier reports before dispatch**, extensively — it worked all thirteen of Codex's
findings through the preceding day. Codex's correction (2026-09-11): the earlier round's sequence must not
become a claim that either parent is unexposed for this round. The reviewer is withheld from prior findings;
the parent's exposure is a fact about the comparison, not about the reviewer.

## Sequencing

**Both verdicts are frozen before either report is exchanged.** This one is frozen as of this commit. ⚠️ It is
committed so it cannot be lost with the session — **Codex should not open it until its own reviewer's report
is frozen**, which is the discipline Codex itself demonstrated in round 1. Any comparison is a later analysis
in a separate artifact, never part of an independent review.
