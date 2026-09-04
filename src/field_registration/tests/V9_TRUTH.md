# Registration v9 synthetic truth

`gen_v9_units.py` encodes the clean-sheet live contract independently of the
implementation. Its CEA-608 rows use the measured 13.5 MHz sampling geometry:
seven 503.5 kHz run-in cycles, `001` start bits, two LSB-first bytes with odd
parity. The fixture covers:

- coincident null and data line 21;
- immediate per-field `+1/+2/+3` placement, plateaus, returns, and clipping;
- parity authority over dark/unmeasurable picture content;
- the measured field-2 smeared-XDS fallback and its no-candidate hold;
- rejection of parity-invalid vertical copies and hold on two valid candidates;
- insert absence;
- two-unit geometry-lock acquisition, rigid per-unit movement, conservation
  failure on a height change, and re-acquisition without moving the crop; and
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

`confidence` is deliberately binary in v9: `1` means at least one field has
an accepted displacement observation, and `0` means neither does. It is not a
probability and does not assign an invented intermediate score to a one-field
observation.

The fixture deliberately landed before the v9 implementation. The old v7
engine must fail it; that red result proves the test distinguishes the new
contract rather than merely preserving prior output.
