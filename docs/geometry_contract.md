# Picture geometry — draft for owner review

This draft records the owner's September 14 reset discussion: identify where
the picture moves, using its top and bottom landmarks. It is not a shortened
version of the v10 contract. No detector or correction policy is selected here;
the questions below remain open.

## The requested result

1. **Locate the top structure in each field.** The requested pattern is caption
   line 21, then caption/waveform data or blanking at line 22, then picture
   signal. Waveform recognition matters because this is the proposed fixed
   landmark at the top, not because a decoded caption is the end product. The
   owner identifies the examined line-22 blanking as deck-generated, not
   Shuttle-generated. [2]
2. **Locate the bottom bound.** Find the fully blanked line the owner names as
   the lower bound, accounting for the head-switch line as part of the geometry
   being followed. The exact boundary intended is question 2 below. [1, 2]
3. **Establish field order and alignment.** The intended result is the two
   fields aligned in the right temporal order (TFF or BFF), weaving into a
   coherent 480-line picture. This is automatic work on the delivered raster,
   not raw-waveform decoding or manually supplied crops and shifts. [1, 3, 4]

## The relationship to test, not an established detector rule

The owner explicitly introduced this as "my theory (still yet to be tested and
I'm not asking you to right now)": a reliable gauge of the picture, including
the head-switch line, moves up or down as a whole. Only one side of the vertical
bound moving indicates content change rather than movement of the picture.
Upward displacement leaves extra black below; downward displacement leaves
extra black above. The stated line account is no more than 240 picture lines
per field. [1]

This draft preserves that hypothesis without treating agreement between two
detector outputs as its demonstration. It does not turn it into a hold/unlock
rule, a search range, or a set of fitted tolerances. Those would be additional
implementation decisions, not words supplied in this discussion. [1, 5]

## Questions before this becomes an executable contract

1. **Which top references move?** In the "line 21 ... line 22 ... then signal"
   pattern [2], are 21/22 the tape-carried objects to follow, the regenerated
   Shuttle/deck references against which picture is located, or both in
   distinct roles? CLAUDE.md §7 records that the Shuttle re-encodes 21/284 and
   can do so despite source displacement; those are not interchangeable gauges.
2. **Which fully blanked line is the bottom bound?** Does "at the bottom, I'm
   looking for a fully blanked line" [2] mean the first fully blanked line
   following the head-switch region, with the switch included inside the
   measured bounds [1]? I have not supplied that endpoint definition myself.
3. **What happens when a bound cannot be established?** The discussion gives
   the desired coherent picture [1], but not an output policy for missing or
   ambiguous geometry. Should correction retain a previously established
   placement, use standard placement, or have another disposition? No v10
   hold/reset/fallback rule has been imported to answer this.

## Owner sources

Direct owner messages in Codex session
`01a04be9-6ed7-70a3-b5a6-2b01d44a4f8d`; all timestamps below are UTC on
2026-09-14. The owner's September 16 clarification identifies the subject as
the attempted reset with Claude, not the earlier v10 contract.

- **[1] 12:45:18** — "where do the picture lines move"; the explicitly untested
  paired-boundary theory, head switch, line account and coherent 480-line weave.
- **[2] 12:50:15** — "the truly 'fixed' part of the top of the picture";
  caption/data/blanking sequence, deck attribution and fully blanked bottom line.
- **[3] 13:07:16** — "anything that works with raw waveforms... thats not our class".
- **[4] 13:11:10** — "take human input... the exact thing we are trying to avoid".
- **[5] 12:53:00** — "I didn't create 15 measurements of the signal. I created
  like 2, 3 tops. Claude invented the others... without telling me".
