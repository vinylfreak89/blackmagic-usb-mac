# HANDBACK — v10: roles reversed back, two new worktrees, acceptance in a fixed order

Written 2026-09-07 20:20 JST from the owner's redirect of 20:00 JST. This file is the standing instruction for both
agents on the v10 branches; it lives at the root of both worktrees. The owner's words are quoted; everything else is
the setup that carries them out.

## 1. The owner's redirect (20:00 JST, verbatim where quoted)

> you didn't review each other. this is the biggest failing I think and the thing that started progressing main
> forward partially (until that ran off the rails too). … Not keeping your repos in sync is a BIG cause of the miss.
> also, I flipped roles which was clearly a mistake. I was always kind of iffy about you going python first. I liked
> the fact that Codex was starting from C.

> The roles reverse again. when codex comes back these two worktrees get frozen in time and you get two new
> worktrees. You will start from the best working engine v10, operating off the new contract. Branch that from main
> plus what is needed from these two worktrees in the best way you see fit. Codex will go back to owing the code, you
> owning the test harness, the with the final output being the side by side renders as we've been doing.

> First test will be commercial tape, EP recording, SP recording, then SP no vstabilize recording. Once these 4 are
> passed in order, and when any new engine change or test change is made, it is produced against each one in order
> to ensure no regressions, then you will proceed to the whole tape.

The three-tree comparison the owner accepted as accurate is `docs/reports/2026-09-07_three_tree_comparison.md`
(on the harness branch). Its findings that this setup answers: mutual review was dropped; the two agents never held
the same document; the reference moved as fast as the engine; no engine after 09:36 was scored by the other
instrument; no whole-tape run and no cost measurement existed on the experiment.

## 2. Roles

- **Codex owns the code**: the registration engine in C, `src/field_registration/`, starting from main's merged
  round-10 engine (`5b6ae68` merged into main; main HEAD `753b1d2`) — the best working engine on record (comb
  misregistered 165 of 86,293 unit pairs on the whole tape; parity 40,208 agree, 0 disagree) — rewritten to the
  contract in section 3. Its goldens (`tests/`, failing-first) stay Codex's. Codex reports ms/unit (median, p95)
  with every engine change (CLAUDE.md §11b).
- **Claude owns the test harness**: the references built from the raw rows, the scoring of every engine record by
  device counter, the invariants, the renders and their machine read-backs, and the acceptance verdicts. Claude's
  tools live under `experiments/` on the harness branch; the Python engine `experiments/switch_geometry.py` is
  carried as a second, independent instrument for the harness, never as the product.
- **Mutual review is back** (CLAUDE.md §14, the owner 2026-09-05: "same rule applies as before with y'all both code
  reviewing each other"): every engine change is reviewed by Claude for code and intent in whole-system context
  before merge; every harness change is reviewed by Codex the same way. A mismatch is decided by a deterministic
  test or a raw-row measurement; an interpretation question ends the turn and goes to the owner.
- **The contract is the owner's words.** `docs/geometry_first_engine.md` at its dcca9ea wording (2026-09-07 16:19),
  the last version both agents had read and agreed on with the owner's 15:40 and 16:20 rulings recorded. Neither
  agent edits it alone: a proposed change is put to the other agent with the owner's quote and the measurement it
  rests on; if both reach extreme confidence it is edited in place and the commit says what changed and why; if not,
  the turn ends and the owner is asked. Wording is settled before code is written to it. When code and contract
  disagree, the disagreement is interrogated (which is wrong, shown by a measurement), never melded.
- **Repos stay in sync.** Both branches are pushed on every commit; each agent pulls the other's branch before a
  review or a dispatch; a review is of a pushed commit named by hash. The contract file must be byte-identical on
  both branches at all times (checked by `diff` in every review). Mechanism: each agent begins a turn by merging the
  other's pushed branch into its own (`git merge`, never a rewrite of a pushed branch), so both branches carry both
  agents' work; `CLAUDE.md` and `HANDBACK.md` are held identical the same way.

## 3. The contract

`docs/geometry_first_engine.md` (identical on both branches). Sections: 1 the owner's rules verbatim; 2 what the
captures show; 3 definitions; 4 rules; 5 the record; 6 what the engine does not have; 7 reserved; 8 acceptance; 9 open.
The owner's answers to the five questions Claude asked at 19:2x are in the transcript and bind the reading of the
contract. Claude's summary, corrected after Codex's read (turn 1) and the owner's 20:56 ruling: the switch-line
count is the lock's constant, taken at the confirmed unit and kept until a reset, a change reported, never re-learned
(owner, 20:56: "the comparator was at line 22. you extended it to the head switch (wrongly) on your own"); the only
running-count comparator is the level of the tape's line 22 (12:52); a caption may CONFIRM the segment's first unit
(the lock's confirmation) and never places a unit against measurable geometry, a disagreement logged, geometry wins;
"237" is 240 minus the source's switch-line count and d is a signed offset (the 16:03 interpretation the owner agreed
to, in `/private/tmp/hw-session/briefs/antecedents_1253_1603.md`); the rewind is unlocked because nothing confirms
it; snow and relocks are the signal-state layer's events, and the offline record is produced by the replay path that
runs that layer (`frameserver_replay`), so it needs no separate input; the comparator's "fixed number" is its array
of eight slots, counts never decrement. Open for the owner (asked 21:07): whether significant clean picture luma
also confirms a first lock (his 2026-09-06 22:13) or the later "combing, captions or both" (13:29) is exhaustive;
contract section 9. Everything else in the contract was settled by both agents at extreme confidence (Codex turn 2,
21:12) and edited in place.

## 4. Worktrees and branches

| who | worktree | branch | base |
|---|---|---|---|
| Codex (engine) | `/private/tmp/blackmagic-v10` | `v10-engine` | main `753b1d2` + the contract (`c31bb4b`) |
| Claude (harness) | `/Users/vinylfreak89/Documents/blackmagic-usb-mac` (the desktop session's primary checkout, so the session loads this branch's `CLAUDE.md`; moved from `/private/tmp/blackmagic-v10-harness` at 20:42 JST) | `v10-harness` | main + Codex's committed harness (`geometry-first-harness` to `84446cd`) + the contract, the engine-side tools and today's reports from the frozen engine branch (`fe011be`) |

Frozen when Codex's current turn returns (no further commits; kept for the record): `geometry-first-engine`
(branch ref only, no worktree since 20:42 JST; HEAD `bc2931f`, pushed; rewound to the dcca9ea contract at `6696fa4`)
and `geometry-first-harness` (`/private/tmp/blackmagic-v9`, HEAD `84446cd`, Codex's turn 17 returned 20:2x JST: run R
scored "not accepted on any capture", the 2,600 owner-review bwdif frames at
`experiments/geometry_oracle/reports/engine_run_R_disagreements/` (2,600 `.webp`, untracked from the v10 branches at 20:42 JST — render frames are scratch, `*.webp` and `*.mov` now ignored; they remain at `84446cd` and in the frozen worktree `/private/tmp/blackmagic-v9`), no contract objections; its final committed
harness is carried into `v10-harness`). `AGENTS.md` is a symlink to `CLAUDE.md` in every worktree. Merges to main go through mutual review;
main stays the measured fallback (round 10) until v10 passes the whole tape.

Codex works from its original thread, with its writes in the v10 engine worktree; Claude creates no Codex threads.
One dispatch at a time, its reply read before the next; the owner says when the first v10 dispatch goes out.

Both agents may examine the frozen experiment branches (`geometry-first-engine`, `geometry-first-harness`) and the
reports for learnings — the owner, 20:2x JST: "the other context does have permission to examine the experiment.
there may be real learnings there, but have it approach with caution". The experiment's engine, its reference
builder's later semantics, and every constant it fitted are not carried; its measurements on the raw rows (section 2
of the contract, the census tools, the three-tree comparison) are.

## 5. Acceptance: four captures in order, then the whole tape

The order is the owner's: (1) the commercial tape, (2) the EP recording, (3) the SP recording, (4) the SP recording
with the deck's V-stabilize off. A capture is passed when the engine's record agrees with the harness's reference on
every unit the reference can measure, the capture's invariants hold, and the side-by-side render's machine read-back
shows the rendered picture still except at the moves rule 8 of the contract allows. Any engine change and any
harness change is re-run against all four in this order before it is accepted (no regressions), and only when all
four pass does the whole-tape run (86,293 units, zero drops, the parity and comb instruments of main's rounds) begin.

### The four captures

| # | name | file | units | origin |
|---|---|---|---|---|
| 1 | commercial tape (composite input) | `/Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/composite_program_30s.tpc` (748 MB) | 920 exact (919 counters) | captured 2026-09-03 over composite; stable picture from device counter 6593 (the tape rewinds before it) |
| 2 | EP recording | `/private/tmp/hw-session/w_2100s.tpc` (502 MB) | 621 | `tpc_slice.py` of `captures/fulltape.cap6` from byte 50811602237 (the 2,100 s passage of fixture A's second recording) |
| 3 | SP recording | `/private/tmp/hw-session/w_300s.tpc` (491 MB) | 608 | `tpc_slice.py` of `captures/fulltape.cap6` from byte 7260000813 (the 300 s passage of fixture A's first recording) |
| 4 | SP, V-stabilize off | `/private/tmp/hw-session/sp_vstab_off_slice.tpc` (492 MB) | 607–608 | `tpc_slice.py` of `/private/tmp/hw-session/sp_vstab_off_45s.tpc` (1.11 GB, captured 2026-09-07 with the deck's line TBC off) from byte 118585912; the Shuttle pairs this capture's fields one later (its slot 1 is the original's field 2 of the previous unit; measured, section 2 of the contract), so the harness re-pairs it (`--repair` / `--repair-slots`) |

Whole tape: `captures/fulltape.cap6` (69.7 GB, byte-complete; CLAUDE.md §6). Its device counters 4506…; the
harness's whole-tape instruments from main: `experiments/line21_truth.py`, `experiments/v9_acceptance.py`,
`experiments/relative_comb_audit.py` (main's parity and comb acceptance), `experiments/render_fulltape.sh`.

Re-creating a slice (record-aligned; the SESSION note inside each slice names its origin):

```bash
python3 experiments/tpc_slice.py /Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/fulltape.cap6 /private/tmp/hw-session/w_300s.tpc --start-bytes 7260000813 --video-bytes 491000000
```

`/private/tmp/hw-session/` is scratch (not synced, not backed up): if it is gone, re-cut the slices as above; the
V-stabilize-off capture must be re-taken from the deck if lost (30–45 s, S-Video, `shuttle-capture`).

### The harness's artifacts (Claude's)

- References per capture (raw-row measurements, one row per device counter): Codex's committed builder
  `experiments/geometry_oracle/build_reference.py` and its `reports/reference_*.csv` at `84446cd` (its run-R score
  and census in `reports/engine_run_R_score.md` and `reports/reference_v3_summary.md`) are the starting point; the harness owner re-derives them from the contract and states, per column, the raw-row measurement behind
  it. The commercial tape's stable-interval invariant (top 23/286 constant from counter 6593, the switch-line count
  constant, the switch line moving only within the partial line's one-row travel) is an external test assertion,
  never a builder input.
- Scoring by device counter: `experiments/compare_records.py` (engine record vs reference; `--repair-slots` for
  capture 4), `experiments/stable_interval_check.py` (capture 1's invariant).
- Renders and read-backs: `experiments/sg_to_render_csv.py` → `experiments/field_pair_review.py --mode stabilized
  --vscale 2` (two captures × two fields per frame, rows doubled, red = picture top and bottom, yellow = the band
  bottom; the side-by-side renders "as we've been doing"), read back by `experiments/stabilized_readback.py` on every
  frame before anyone looks. The owner's per-unit examination of a true disagreement: one bwdif frame of the two
  crops as placed, labelled with unit, counter, both origins and the comb reading (contract section 8).
- Measurement tools: `experiments/first_row_level_census.py` (a row's level across units: a VBI row is
  content-independent, a picture row tracks the row below), `experiments/cc608_decode.py`,
  `experiments/packet_capture_reader.py`.
- The engine's record columns are defined by the contract's section 5; the harness joins by `counter`, never by
  unit index.

### The engine's artifacts (Codex's)

- `src/field_registration/` (C, allocation-free, fixed arrays; CLAUDE.md §11b budget 10 ms/unit on the M3),
  its goldens under `tests/`, the sidecar record per unit with the contract's section-5 fields, and the replay path
  (`frameserver_replay`, paced; CLAUDE.md §6 and §11) that produces the record for a capture.

## 6. Order of work

1. Codex's turn 17 returns → both old worktrees frozen (this file records their HEADs).
2. Both agents read the contract on their own branch, confirm the files are identical, and read the owner's
   transcript answers (section 3 above); any interpretation that is not at extreme confidence for both ends the turn
   and goes to the owner. No code until the wording is settled.
3. Claude produces the four references and the invariant tests for the four captures, in order, each with its
   raw-row derivation, reviewed by Codex.
4. Codex writes v10 to the contract from main's round-10 engine, with failing-first goldens, reviewed by Claude.
5. Every engine or harness change: run captures 1→4 in order, score, render, read back; regressions block.
6. All four passed → the whole tape, main's instruments, the watch copy from the live path with its record burned in.

## 7. The plan (stated 20:42 JST 2026-09-07; owner, 20:5x: "both of you must agree fully on the stated plan before beginning")

The owner's words that bind it (20:5x JST): "before either of you start work, make sure you are in agreement on how to
proceed. understand you may reference any of your prior work, including uncommitted either from this thread or the
other one as valid ideas may still be present. if there is any disagreement, especially on the contract that you are
unable to resolve the ambiguity on yourselves ask me"; and: "same applies as before that going 'captions first' was
the wrong reasoning you led yourselves to so that has not changed"; "keep the worktrees in sync rather than letting
them drift".

0. **Settle the words first; no code.** Codex merges `v10-harness` into `v10-engine` and reviews the CLAUDE.md and
   HANDBACK changes by hash. Both agents confirm, from the owner's verbatim messages
   (`/private/tmp/hw-session/briefs/owner_messages_2026-09-07_1230-2030.md`, extracted by script), the reading of his
   five 19:32 questions summarised in section 3; the contract's preamble and section 8 are corrected to the v10
   roles by agreement (Claude proposes the wording, Codex confirms or objects); every contract sentence either agent
   cannot hold at extreme confidence is listed with the sentence and the two readings; the lists go to the owner in
   one message. Nothing else starts until both agents have written "agreed in full" against this section.
1. **Claude: the four references, in the acceptance order, one commit each**, from the raw rows by the contract's
   definitions (section 3): per unit per field the picture top, the VBI rows above it with their signatures, the
   switch line, S, the band's extent and count, the clip, the closure, the caption line when visible, the comb of the
   two fields at the reference's own placement, and the measurability class (observed / unmeasurable / not
   applicable) — never a substituted number. Starting points: Codex's committed builder
   `experiments/geometry_oracle/build_reference.py` and `reports/reference_*.csv` at `84446cd`, and Claude's Python
   instrument `experiments/switch_geometry.py` as a second, independent reading; every column's raw-row derivation is
   stated in the reference report, and every constant is a standard, a stated measurement on the captures, or
   labelled a defect. The invariant tests: capture 1's stable interval from counter 6593 (`stable_interval_check.py`,
   an external assertion, never a builder input); the fixture-A invariants of contract section 8 for the whole tape
   later. The render and read-back path is exercised on the reference itself (a stabilized side-by-side render of
   the reference's own placement, read back on every frame) before any engine record exists. Codex reviews each
   commit (code and intent, whole system) and objects with the deciding unit; a disagreement about what a row IS is
   decided on the raw rows by both agents.
2. **Codex, in parallel: v10 in C from main's round-10 engine, rewritten to the contract**, one rule at a time with a
   failing-first golden per rule; the record per contract section 5, joined by device counter; the replay path
   (`frameserver_replay`, paced, zero drops) producing the record for a capture; ms/unit (median, p95) per commit
   against the §11b budget. Each commit names the contract sentence it implements. Claude reviews each commit (code
   and intent, whole system). No constant that is not a standard, a stated measurement or a memory capacity. Codex's
   contract-versus-round-10 gap list (its turn 1, 2026-09-07 20:57) is the checklist: remove what the contract
   prohibits, build what it requires, one reviewed commit per rule.
3. **Acceptance, capture 1, then 2, 3, 4, in that order** (harness runs, both agents read): the engine's record vs the
   reference by counter (`compare_records.py`), the capture's invariants, the stabilized side-by-side render
   (`sg_to_render_csv.py` → `field_pair_review.py --mode stabilized --vscale 2`) with its machine read-back on every
   frame (`stabilized_readback.py`), then the owner looks. A measurement disagreement (what a row is) is decided on
   the raw rows by both; a true disagreement (the settled comb against the placed crops, or the two instruments
   against each other on a unit after the rows were read) goes to the owner as one labelled bwdif frame per unit,
   adjudicated by neither agent. A capture passes when the record agrees with the reference on every unit the
   reference can measure, the invariants hold, and the read-back shows the picture still except at rule 8's moves.
   Any later engine or harness change re-runs 1→4 in order; a regression blocks it.
4. **All four passed → the whole tape**: 86,293 units, zero drops, main's parity and comb instruments
   (`line21_truth.py`, `v9_acceptance.py`, `relative_comb_audit.py`), the watch copy from the live path with its
   record burned in; the owner's sign-off.

Throughout: each turn begins by merging the other's pushed branch; one Codex dispatch at a time, its reply read
before the next; a review is of a pushed hash; the contract changes only by agreement, else the owner; no round
without a premise check (CLAUDE.md §14); raw panels before numbers; a machine reads every render back before anyone
looks; timestamps only from a checked clock; no program content in the repo.

**Agreement record:** Claude — agreed in full, 20:42 JST. Codex — (pending its turn).
