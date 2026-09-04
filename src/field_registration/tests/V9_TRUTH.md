# Registration v9 synthetic truth

`gen_v9_units.py` encodes the clean-sheet live contract independently of the
implementation. Its CEA-608 rows use the measured 13.5 MHz sampling geometry:
seven 503.5 kHz run-in cycles, `001` start bits, two LSB-first bytes with odd
parity. The fixture covers:

- coincident null and data line 21;
- immediate per-field `+1/+2/+3` placement, plateaus, returns, and clipping;
- a decoded caption moving from line 23 to 24 while both picture edges stay
  fixed (`CaptionOnlyMotion`), the matching rigid-move control, and the
  censored-bottom control where caption authority remains;
- cold false-parity anchor isolation, same-unit edge corroboration, and the
  second-consecutive-parity route to a changed segment zero;
- parity authority over dark/unmeasurable picture content;
- the measured narrow field-2 XDS fallback, right-side bleed and short-bar
  variant, plus false-positive guards for left-heavy picture texture and
  consecutive picture rows that resemble the coarse weak-caption envelope;
- rejection of parity-invalid vertical copies and hold on two valid candidates;
- insert absence;
- immediate standard-origin geometry placement, rigid per-unit movement, and
  conservation failure on a height/content change without redefining zero; and
- invalid transport rejection.

Review-round additions decide four lock-policy details that an applied-pair-only
fixture cannot see:

- a parity-gauged `+2/+3` alternation with a clipped bottom reaches and remains
  `Locked`, with `comb_safe` true from its third unit, even when an unrelated
  bright VBI band appears above the displaced line-21 gauge;
- non-null insert data cannot reset a live nonzero geometry lock;
- line-22 data is not mistaken for a one-line displacement, and a one-line
  parity/geometry disagreement is a named hold; and
- a one-unit insert dropout holds without destroying either field lock.
- a missing weak field-2 gauge cannot change placement while a shortened
  bottom has made the clip ceiling uncertain.

Round-two additions pin the corrected gauge hierarchy:

- non-null data re-encoded on the insert is provenance only; rigid geometry
  still applies a `+1` placement;
- parity `+2` re-anchors the standard zero immediately when the gauged picture
  origin proves that source geometry differs, after which a non-rigid envelope
  holds and a rigid `+1` envelope follows that gold zero;
- standard-origin geometry applies immediately, including a top move whose
  bottom is censored by the deck's near-blank clip band; and
- two `Locked` state machines with only standard zeroes do not claim
  `comb_safe` on an unmeasurable unit.

The root-C/D additions pin the remaining direct-placement rules: each segment
starts at the standard line-23/286 picture zero rather than learning position
from content; a field at either standard origin is placed from its first unit;
one-line clip-band flicker cannot move that top decision; and picture at Y=10
is measurable against a Y=2 blanking floor while mute/black remains
unmeasurable.

`confidence` is deliberately binary in v9: `1` means at least one field has
an accepted displacement observation, and `0` means neither does. It is not a
probability and does not assign an invented intermediate score to a one-field
observation.

The fixture deliberately landed before the v9 implementation. The old v7
engine must fail it; that red result proves the test distinguishes the new
contract rather than merely preserving prior output.
