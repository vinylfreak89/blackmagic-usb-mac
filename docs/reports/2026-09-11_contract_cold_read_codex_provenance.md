# Contract review provenance — second round, Codex

## Frozen source

- Contract commit: `5eb9be251bb8339e747a8d5c73c73516edf398b2`.
- Repository path: `docs/geometry_first_engine.md`.
- Git blob: `6696fd56dea669cfa0796783c4492ba49f9c5bb7`.
- SHA-256: `3631179a762a55e124a688bbdf81cea05d0254b8d6a540da413686109e6472c4`.
- Line count: 1,383.
- Snapshot: `/private/tmp/contract-freeze-codex-20260911.TfdNRt/contract.md`.
- Extraction time recorded by the freezer: `2026-09-10T15:11:12Z` (2026-09-11 in Asia/Tokyo).
- Both content hashes were re-derived immediately before dispatch. No working-tree contract was substituted.

## Dispatch and exposure

- Parent: Codex, `/root`.
- Fresh reviewer: `/root/contract_review_round2`, spawned using `fork_turns="none"`, with no model or reasoning override. The earlier `contract_cold_review` agent was not reused.
- The parent has read both previous-round reports and the ensuing discussion. This round's request also supplied the other review's aggregate count and severity distribution; neither was forwarded to the reviewer.
- The parent has not opened this round's Claude report or its provenance. The report's availability and announced hash were not treated as permission to inspect its findings before freezing this review.
- The reviewer was directed to read only the frozen contract and not repository documents, source code, prior reports, Git history/status, web sources, or other artifacts. The task did not supply findings, proposed corrections, target counts, or the parents' reasoning.
- This dispatch configuration withholds conversation history; it does not prove that the platform withheld automatically supplied instructions. The reviewer's actual inherited-context account is recorded in its report and summarized below after completion. Parent exposure and reviewer exposure are distinct.
- No new-round comparison is part of this review. Both new verdicts must be frozen before either new report is exchanged or compared.

## Reviewer task supplied by the parent

> Independently review ONE frozen technical contract for internal coherence and logic. Read only /private/tmp/contract-freeze-codex-20260911.TfdNRt/contract.md (all 1383 lines). Do not open repository files, instructions files, reports, Git history/status, source code, web sources, or other artifacts. Do not seek external validation: assess the document on its own terms. First record what relevant context was automatically supplied to you before opening it, including any repository instructions or project-specific information, and state the resulting limits on independence; absence of citation is not absence of exposure. Do not claim context-free isolation if such material was supplied.
>
> Find consequential contradictions, ambiguous quantities, competing operative rules, undefined interfaces or dependencies that permit materially different implementations. Distinguish a missing empirical method from proof of impossibility and distinguish historical statements from operative rules. Do not force a finding count or assume the document is defective. For each supported finding cite exact document line locations and explain the competing readings and consequence. Note material limitations or apparent tensions you do not count as findings. Describe severity by consequence, not a pass/fail verdict. Do not revise the contract or implement anything.
>
> Write your complete review with apply_patch to /private/tmp/contract-freeze-codex-20260911.TfdNRt/review_codex_frozen.md. After finalizing it, calculate its SHA-256 and do not change it again. In your completion message provide the artifact path, hash, finding count, and actual context/isolation account. Your report will be preserved byte-for-byte by the parent; any later comparison is separate. No other reviewer findings have been supplied in this task. Do not dispatch subagents.

## Completion and preservation

- Reviewer completed and froze `/private/tmp/contract-freeze-codex-20260911.TfdNRt/review_codex_frozen.md` before reporting its hash to the parent. It reported no changes after hashing.
- SHA-256: `629624ebaaf67e4f7c1dc8aa85438d0cbdcc291a38ba61f2e6b8e66aef26e2cb`.
- Repository artifact: `docs/reports/2026-09-11_contract_cold_read_codex.md`, 89 lines, copied without parent edits. `cmp` verified byte-for-byte identity and an independent SHA-256 check matched the reviewer's hash.
- The parent verified the completed artifact and unchanged contract blob at `2026-09-10T15:41:00Z` (2026-09-11 in Asia/Tokyo). This is the parent's verification time, not a claimed timestamp of the reviewer's final write.
- The artifact reports five findings, two explicitly acknowledged unresolved decisions. Counts and consequences are the reviewer's; no severity normalization or comparison has been performed.
- Actual reviewer exposure: automatically supplied project-specific AGENTS.md content covered capture/archival goals, hardware/protocol, transport provenance and damage handling, registration history and estimator limitations, and owner level decisions, along with general system/developer and environment context. This foregrounded project concepts. Artifact access was restricted, but the review was informed by inherited project context, not context-free. No stronger independent-corroboration claim follows merely from withholding reports.
- Sequencing deviation: despite the prompt requiring an exposure record before opening the contract, the reviewer wrote its formal exposure ledger after the first document read. Its report discloses this; the parent did not edit it away or ask for a replacement ledger presented as contemporaneous.
- The reviewer reports that it read all 1,383 source lines, rereading after a truncated response, opened no other input artifacts, and used no web, Git inspection, or subagents.
- The parent first read this report only after the reviewer declared it frozen and the parent verified its hash. The parent's access did not change the frozen report.
- The other side's new report and provenance remain unopened. No new-round comparison has been started. The collaborator's supplied aggregate counts were not used to request a larger report, change findings, or normalize severity.
- After the report was frozen and copied, the engine branch fast-forwarded from `3d691d9` to the collaborator's `5652bea` as required by the shared-branch protocol. This made the other report available in the checkout but did not open it. Only this report, its provenance, and a completion note in CLAUDE.md are authored by the parent in this turn; imported changes are the collaborator's work.

## Operational failures and recovery

- The initial sandboxed tree-lock liveness check returned `zsh:1: operation not permitted: ps`. The authorized read-only retry verified PID 40013 alive, matching this turn's existing `codex:01a04be9` lock. No lock was acquired or stolen.
