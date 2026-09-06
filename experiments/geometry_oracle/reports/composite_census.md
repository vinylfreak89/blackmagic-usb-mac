# Geometry oracle — commercial composite capture census

This is a measurement census, not an engine verdict.

- Exact units: **919**
- Transport ordinal range: **0–921**
- Internal device-short ordinal holes: **2, 3, 5**
- Relocks: **none annotated for this capture**
- Placement-forbidden annotated units: **0**
- Exact same-field repeats: **0**
- Measurable static-comb rows: **918**
- Oracle runtime: **18.720 s** (**20.370 ms/exact unit**)
- Input SHA-256: `483b53b1ec302577a94dcd7fb79e1f814e18fef02329c1bd2db9c07b6cef61d5`
- Reference SHA-256: `95c6d6b22915ee5c019cae01491fc1a6304f77e28535654dfc3c3a94351dedb7`

The CAP1 provenance walk completed with no sequence gaps, completion inversions, packet-index
errors, packet-status errors, HostLoss records, TransferError records, or control-truth-loss
markers. The video stream contains 919 exact 756,048-byte marker intervals, seven short
marker-delimited intervals, and leading/trailing fragments. Thus the capture contains 919—not
920—exact oracle units. The short periods inside the exact-unit span remain visible as ordinal
holes rather than shifting counter-derived ordinals.

| Field | Recorded top | Picture top | Any 608 waveform | Any parity-decoded 608 | Unique off-insert tape 608 | Black band | Exact bottom | Exact height | Last recorded | Flat raster | Exact repeat |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 914 | 701 | 919 | 919 | 2 | 228 | 918 | 701 | 919 | 303 | 0 |
| 2 | 914 | 880 | 919 | 919 | 0 | 156 | 918 | 880 | 919 | 306 | 0 |

## Picture-top histogram

- Field 1: line 23: 462; 24: 55; 25: 24; 27: 1; 28: 125; 29: 1; 32: 1;
  40: 1; 42: 1; 44: 3; 45: 3; 46: 1; 47: 1; 49: 1; 50: 1; 259: 1;
  260: 19.
- Field 2: line 286: 667; 287: 56; 288: 14; 289: 2; 290: 97; 291: 33;
  299: 1; 301: 1; 308: 1; 309: 2; 310: 1; 311: 2; 312: 1; 523: 2.

## Top-status census

- Field 1: `measured` 701, `unmeasurable` 215, `vbi_ambiguous` 3.
- Field 2: `measured` 880, `unmeasurable` 38, `vbi_ambiguous` 1.

## Event census

- `Program`: 919.
- Relock annotations: none.
- Placement-forbidden annotations: none.
