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

The fixture deliberately landed before the v9 implementation. The old v7
engine must fail it; that red result proves the test distinguishes the new
contract rather than merely preserving prior output.
