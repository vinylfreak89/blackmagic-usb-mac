# Picture geometry — draft for owner review

This draft records the owner's September 13–14 reset discussion: recognize the
data-like lines, then locate picture geometry. It is not a shortened v10
contract. Direct quotations and earlier relayed rulings are distinguished;
the questions below remain open. No new detector or numerical limit is chosen.

## First: caption/waveform recognition

The order follows the owner's September 14 words: "right now, we can't even
reliably detect what is caption and what isn't" [1], and "if we can figure
that part out, we can figure out the rest" [2].

**The temporal definition** (direct messages to Claude, September 13 UTC):

- **13:28:04:** "one code near blanking, and one pretty far away from it".
- **13:34:08:** "2 codes. on the edges of those codes there is going to be
  some ramping smear (its sinusoidal) and nothing between them"; "not treating
  these lines as the temporal signals they are".
- **13:35:05:** "walk the line sample by sample. starts with near blanking
  codes. should monotonically rise to a far away from blanking code, stop
  there, and then again gradually fall toward blanking".
- **13:35:55:** "if you read the whole line, and thats the ONLY signal you see,
  its a waveform"; "if you see any other type of signal, its not a waveform".
- **13:37:28:** "the far left isn't always blanking"; it can start at the
  "top" of the waveform, "so either works".
- **13:57:00:** "if there are any codes that do not exist in the ramp up/ramp
  down between those two codes, it isn't a valid waveform". The next message
  corrects "pulse" to "alternate".

**Further descriptions to reconcile with that definition**, not silently
converted into additional pass/fail tests (direct messages to Claude):

- **September 13, 14:27:42–14:28:32:** false signals "fall into blanking sharply
  at the very end of the line", whereas "every real invariant, no matter how
  noisy hits blanking well before the end of the line".
- **14:28:59:** "the head switch is always a chaotic jumbled mess with extremely
  high entropy".
- **14:30:00:** "can you also include chroma as a designator. a real caption or
  VBI line should have very little chroma signal".
- **September 14, 07:26:43:** "Is the problem possibly you are not looking at
  the ramp up and down from black as a stochastic function? The two half’s
  should be symmetric sans noise".

For this recognition experiment the owner also said "stop. do not use the
CEA-608 parity decoder" (September 13, 14:13:24). His requested acceptance was
"run this across every line of all 4 captures and get 0 false positives and
0 false negatives" (14:16:19). His later direction was "Is there something
that’s more empirical though and not limits based? I don’t understand why we
need to fit those limits" (September 14, 11:30:59). These are requested criteria
and direction, not achieved results or permission to fit limits to the examples.

**Implementation transparency:** any measurement beyond the owner's stated
observations must be disclosed when proposed, not silently added and explained
after implementation. This is the rule drawn from his objection in [5]. Which
descriptions above are operative criteria is question 1; no cutoffs or noise
tolerances are supplied by this draft.

## The requested result

1. **Locate the top structure in each field.** The requested pattern is caption
   line 21, then caption/waveform data or blanking at line 22, then picture
   signal. Waveform recognition matters because this is the proposed fixed
   landmark at the top, not because a decoded caption is the end product. The
   owner identifies the examined line-22 blanking as deck-generated, not
   Shuttle-generated. [2]
2. **Locate the bottom bound.** Find the fully blanked line the owner names as
   the lower bound, accounting for the head-switch line as part of the geometry
   being followed. The earlier head-switch ruling and this wording need to be
   reconciled in question 2 below. [1, 2]
3. **Establish field order and alignment.** The intended result is the two
   fields aligned in the right temporal order (TFF or BFF), weaving into a
   coherent 480-line picture. This is automatic work on the delivered raster,
   not raw RF/CVBS processing or manually supplied crops and shifts. [1, 3, 4]

## The relationship to test, not an established detector rule

The owner explicitly introduced this as "my theory (still yet to be tested and
I'm not asking you to right now)": a reliable gauge of the picture, including
the head-switch line, moves up or down as a whole. Only one side of the vertical
bound moving indicates content change rather than movement of the picture.
Upward displacement leaves extra black below; downward displacement leaves
extra black above. The stated line account is no more than 240 picture lines
per field. [1]

Agreement between detector outputs is not itself a demonstration of that
hypothesis. No search range or fitted tolerance is inferred from it. [1, 5]

## Earlier words that narrow the open questions

**Top reference identity.** Direct to Claude, September 13 at 10:01:23:
"the shuttle only modifies 20 and 21. 22 is inserted by the eck" [sic: deck].
The earlier September 10 ruling, preserved as relayed, says "no the regenerated
insert shouldn't count as anything" and "whether they can decode captions,
that could mean the real captions are anywhere from 20,21,22 so that should
say nothing about geometry". Thus recognizing an insert as a waveform does
not make its decoded bytes evidence of the tape's position. This answers the
regenerated-insert part of the former Q1; it is not reopened as a blank choice.

**One-sided motion.** The September 11 ruling, preserved as relayed, is
"hold not unlock and don't shift. only one part of the geometry shifting without
a corresponding shift on the other side is a hold. not a shift." The boxed-source
clarification is "its both sides of the box moving" and "ITS A BOX, not an EDGE
or whatever." These are not rulings about genuinely unavailable geometry;
question 3 distinguishes that gap from the answered one-sided case.

## Questions before this becomes an executable contract

1. **Which waveform properties are the core criteria?** Your "2, 3 tops" [5]
   sits beside descriptions of temporal shape, end-of-line blanking, entropy,
   chroma and symmetry. Which are required decisions, and which are supporting
   observations to inspect? I have not made them five independent tests or
   chosen a smaller subset on your behalf.
2. **How do the bottom descriptions fit together?** September 10, relayed:
   "if a head switch is there, it marks the bottom of the geometry. where there
   is blanking below the head switch thats not part of the bottom geometry."
   September 14, direct: "at the bottom, I'm looking for a fully blanked line"
   [2]. Is the blanked line evidence locating the end of geometry rather than
   a line included in it, or does the reset change the earlier definition?
3. **Does the earlier hold rule carry forward, and what about missing bounds?**
   "hold not unlock and don't shift" answers observed one-sided motion, not
   inability to identify a bound. Does that earlier policy still apply in this
   reset, and what should output do when a bound is genuinely missing or
   ambiguous, before and after an established placement?

## Owner sources

Numbered sources [1]–[5] are direct owner messages on September 14 in Codex
session `01a04be9-6ed7-70a3-b5a6-2b01d44a4f8d`. All timestamps in this document
are UTC. The owner's September 16 clarification identifies the subject as
the attempted reset with Claude, not the earlier v10 contract.

The waveform quotations and September 13 insert attribution were checked in
Claude session `8ad5adc7-a74c-4853-97ac-571007154e12`, `queue-operation` enqueue
records at the timestamps above, excluding system task notifications. Earlier
relayed quotations were checked in `c91a10b:CLAUDE.md` (insert, bottom, hold and
box passages); this verifies their preserved wording, not the original relay's
provenance. The current archive tip's slimmed CLAUDE.md no longer contains all
those quotations. Prior implementation prose is not adopted with them.

- **[1] 12:45:18** — "where do the picture lines move"; the explicitly untested
  paired-boundary theory, head switch, line account and coherent 480-line weave.
- **[2] 12:50:15** — "the truly 'fixed' part of the top of the picture";
  caption/data/blanking sequence, deck attribution and fully blanked bottom line.
- **[3] 13:07:16** — "anything that works with raw waveforms... thats not our class".
- **[4] 13:11:10** — "take human input... the exact thing we are trying to avoid".
- **[5] 12:53:00** — "I didn't create 15 measurements of the signal. I created
  like 2, 3 tops. Claude invented the others... without telling me".
