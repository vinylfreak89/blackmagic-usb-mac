# Picture geometry — draft for owner review

This draft records the owner's September 13–14 reset discussion: recognize the
data-like lines, then locate picture geometry. It is not a shortened v10
contract. Direct quotations and earlier relayed rulings are distinguished.
The owner's subsequent answers [6] settle the dispositions below and commission
empirical recognition work; they do not establish detector performance.

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
after implementation. This is the rule drawn from his objection in [5]. Asked
which descriptions are the core criteria, the owner answered [6]:

> I don't know. I want codex to analyze this fresh. given the real signal and
> false positives/negatives we came to in our session, what is the simplest
> engine that covers the most cases. what is the accuracy and specificity rate.
> ideally, it will be a simple algorithm

Thus the next step is an empirical comparison, with independently established
truth and counts behind the rates, not another list of owner-selected clauses.
No cutoffs or noise tolerances are supplied by this draft.

## The requested result

1. **Locate the top structure in each field.** The requested pattern is caption
   line 21, then caption/waveform data or blanking at line 22, then picture
   signal. Waveform recognition matters because this is the proposed fixed
   landmark at the top, not because a decoded caption is the end product. The
   deck attribution is a current hypothesis, as qualified in [6] below. [2]
2. **Locate the bottom bound.** Find the fully blanked line the owner names as
   the lower bound, accounting for the head-switch line as part of the geometry
   being followed. The owner's clarification below identifies which blanked
   line is meant. [1, 2, 6]
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

## Top reference: device position is not tape position

The owner's answer [6] supplies the current working assumption:

> line 20/21 are fixed shuttle references. these are the physical NTSC line
> 20/21 locations. the current hypothesis is that the deck itself is generating
> line 22 not the shuttle. As far as we have been able to see so far, if captions
> land within 2 lines of line 21 in the actual raster, the shuttle generates them
> on line 21. therefore, line 23 captions (the tape's VSYNC shifted) shows
> duplicate captions. therefore, the existence of captions can only be an
> indicator the real line 21 VSYNC is are close by, not actually at line 21.
> we have to assume for now that if there is no other line 21, that what is on
> the tape is at least close and non-fully blanked rows are just normal picture

**Measurement beside that qualified account:** `c91a10b:CLAUDE.md`, §11's v9
VBI paragraphs, records 91 units with a rigid +1 picture displacement,
re-encoded data at raster line 21 and no raw caption elsewhere in the field.
At +2/+3 the raw caption appeared at 23/24 while the Shuttle's 21 carried its
null-byte insert. Two caption-shaped lines did not mean duplicate data.
Those observations do not establish a symmetric ±2 decoding window. They are
historical measurements, not a substitute for the owner's words or permission
to use the parity decoder in this recognition experiment.

## Bottom bound

The owner's clarification [6] is:

> the first fully blanked line that does not contain any elements of picture or
> head switch. so it needs to be pedestal or blanking level luma. probably below
> Y=32 for NTSC-M on this deck

Y=32 is the owner's estimate to test, **not a settled cutoff**. This describes
the blanked line bounding the picture/head-switch region, not a blank line
inside that region.

## Geometry validation experiment, not a bottom-bound detector

The owner commissioned an empirical check [6]:

> again I don't know. we need to empirically test this, probably with a very
> simple combing engine as a proxy to detect where the picture -should- go...
> and really, combing detection needs to be a normal deinterlace algorithm,
> nothing fancy.

He corrected the dispatch's bottom-bound framing in a subsequent message [7]:

> this has nothing to do with the bottom bound. this is fully about checking
> our geometry calculations. it is NOT at this time intended to be a final part
> of the engine but that is still tbd.

The plain deinterlacer-style comb check is therefore proposed to validate
computed geometry, not locate its bottom or become an engine component.
Recognition comes first; this check is to be proposed before it is run.

## Unavailable geometry, one-sided motion and reset

**One-sided motion.** The September 11 ruling, preserved as relayed, is
"hold not unlock and don't shift. only one part of the geometry shifting without
a corresponding shift on the other side is a hold. not a shift." The boxed-source
clarification is "its both sides of the box moving" and "ITS A BOX, not an EDGE
or whatever."

The new answers [6] distinguish unavailable geometry and reset:

> if geometry can not be established, the output should not shift. this should
> be printed in the registration sidecar, but no shifting should be performed.

> if there is a reset, then no the hold rule does not apply. if there is no lock
> yet, do nothing, as stated above

Do not infer a shift from a missing measurement, or carry the hold rule across
a reset. These answers do not themselves define additional reset triggers.

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
- **[6] September 16 dispatch to Codex** — the owner's six answers, supplied
  verbatim by Claude: three answering `daa2817`, then three answering
  `6f5939f`. These are relayed quotations, not a new direct transcript check.
  The neighbouring historical VBI measurement was checked in `c91a10b`.
- **[7] Subsequent correction in this turn** — the owner's clarification of
  the comb check's purpose, relayed verbatim by Claude.
