# Registration v9 synthetic truth

`gen_v9_units.py` encodes the clean-sheet live contract independently of the
implementation. Its CEA-608 rows use the measured 13.5 MHz sampling geometry:
seven 503.5 kHz run-in cycles, `001` start bits, two LSB-first bytes with odd
parity. The fixture covers:

- coincident null and data line 21;
- immediate per-field `+1/+2/+3` placement, plateaus, returns, and clipping;
- a decoded caption moving from line 23 to 24 while picture top and body stay
  fixed (`CaptionOnlyMotion`), the matching rigid-move control, and the
  censored-bottom case where a still top/body remain sufficient testimony;
- cold false-parity anchor isolation, same-unit edge corroboration, and the
  second-consecutive-parity route to a changed segment zero;
- parity authority over dark/unmeasurable picture content;
- the measured narrow field-2 XDS fallback, right-side bleed and short-bar
  variant, plus false-positive guards for left-heavy picture texture and
  consecutive picture rows that resemble the coarse weak-caption envelope;
- rejection of parity-invalid vertical copies and geometry placement under
  two valid candidates when top plus the one-unit body witness agree;
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

The round-three body-witness additions freeze the only bounded temporal
measurement in v9: two-dimensional luma over 160 picture rows is compared at
integer vertical shifts -3..+3 against the immediately previous unit, with
MAD at most 25 required. The fixture's horizontally textured body has an
intentionally flat row-mean profile, so a one-dimensional shortcut cannot
pass. It covers both directions of caption/body disagreement, two-unit
post-hold latch prevention, and a first-line-brightness flicker over a still
body. Earlier controls also cover geometry recovery under ambiguous line 21,
gauge conflict, bottom conservation failure, and an otherwise
out-of-policy-range top. A discontinuity clears both the witness and its last
measured position, keeps the last applied pair, and makes a pictureless next
unit an explicitly unmeasurable hold.

`confidence` is deliberately binary in v9: `1` means at least one field has
an accepted displacement observation, and `0` means neither does. It is not a
probability and does not assign an invented intermediate score to a one-field
observation.

The fixture deliberately landed before each implementation step. The original
v9 engine scored 126/132 on the 2-D additions; that red result proves these
cases distinguish the corrected contract rather than merely preserve prior
output.

The round-8 cases separate abstention from contradiction. A parity gauge is
not vetoed by a tied or absent body witness. For geometry, a tied body leaves
comb to corroborate or veto the changed top when comb is measurable; flat or
unavailable comb leaves the top authoritative and names the decision
`TopOnly`. A half-static synthetic field proves the veto without allowing comb
to move a crop independently. These additions fail 183/186 before the engine
change and pass 186/186 after it.

Round 10 separates a bounded relative crop correction from every learned
zero. Three consecutive decisive `+1` static-comb readings install exactly
one `+1` correction on field 2 when field 1 is parity-placed. Repeated `+1`
readings cannot accumulate it. The correction survives a content/byte
discontinuity, while `fieldreg_begin_segment()` (signal relock) clears it.

Round 11 separates presentation history from the last evidence-backed good
geometry. A `TopOnly` move cannot overwrite a saved parity placement;
contradictory units hold that saved placement, and the next parity-backed
clean unit emits exactly one `DamageCleared` transition at the signed crop
difference.
