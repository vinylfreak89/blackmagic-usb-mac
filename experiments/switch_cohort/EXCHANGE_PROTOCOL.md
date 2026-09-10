# Blind exchange: the protocol, and the two holes found in its first use

The contract entry of 2026-09-10 requires that both agents adjudicate the cohort independently:
panels, keys and criteria exchanged **without verdicts**, each side freezing its own before any
comparison. The first use of that protocol leaked in two ways. Both are recorded here because the
fix is not obvious from the requirement.

## Hole 1 — an aggregate can be unanimous

The first exchange asked the other agent for counts only, never per-key verdicts, so that this
side's adjudication could not be contaminated. That works whenever the result is mixed. It fails
completely when the result is unanimous: "0 of 768 identifiable, all excluded on L2" states the
verdict for every one of the 768 keys as surely as the table would.

**Fix.** Neither side reports ANY summary of its verdicts until both are frozen and committed. The
report after freezing may be as detailed as you like; the report before it must be confined to
"frozen, N keys covered, committed as <hash>".

## Hole 2 — a linked worktree is not an isolation boundary

The second exchange assumed that because this working tree did not contain the other agent's
verdict file, adjudicators working here could not reach it. That is false, and it was verified
rather than assumed:

    git worktree list
      /Users/vinylfreak89/Documents/blackmagic-usb-mac   [v10-harness]
      /private/tmp/blackmagic-v10                        [v10-engine]

The engine tree is a LINKED WORKTREE of this repository, not a separate clone. One object
database, one ref store. So `v10-engine` is a local branch here, `git show v10-engine:<path>`
resolves from this directory, and the other agent's file also sits at a plain world-readable
absolute path. Checking out an older commit isolates nothing.

**Fix.** Isolation must be structural, not instructed. Either
  - adjudicate before the other side commits, so there is nothing to reach; or
  - copy the panels and criteria to a directory outside the repository and give the adjudicator
    only that; or
  - exchange verdicts through a channel that does not share an object store.
An adjudicator told not to look is not blind. That standard is already this project's, applied to
Codex; it applies to any adjudicator, including this side's own.

## What agreement and disagreement are worth

If an adjudicator's isolation cannot be certified, its **agreement** with the other side is weak
evidence - it is what a contaminated reader would produce anyway. Its **disagreement** is strong,
because contamination pulls towards agreement rather than away from it. Report which of the two a
given comparison rests on rather than reporting a match rate.

## One thing deliberately not done

This side has NOT read the other agent's per-key verdict file, before or after learning it was
reachable. Only its aggregate, which it reported, is known here. That is recorded so the later
comparison can say what was and was not in this context when it was written.
