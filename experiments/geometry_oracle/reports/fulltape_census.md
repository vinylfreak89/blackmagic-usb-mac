# Geometry oracle — whole-tape census

This is a measurement census, not an engine verdict.

- Exact units: **86,293**
- Transport ordinal range: **0–86,295**
- Internal device-short ordinal holes: **4, 9, 190**
- Relocks: **300, 43,737**
- Placement-forbidden annotated units: **53**
- Exact same-field repeats: **0**
- Measurable static-comb rows: **86,292**
- Oracle runtime: **1747.442 s** (**20.250 ms/exact unit**)

Four device-short periods precede the first exact unit. The three short periods inside
the exact-unit span remain visible as ordinal holes rather than shifting event labels.

| Field | Measurable top | Any 608 waveform | Any parity-decoded 608 | Unique off-insert tape 608 | Black-gap line | Exact bottom | Exact height | Exact repeat |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 73,652 | 86,274 | 86,156 | 40,169 | 45,309 | 86,273 | 73,652 | 0 |
| 2 | 86,180 | 86,274 | 86,270 | 112 | 29,247 | 86,271 | 86,180 | 0 |

## Top-status census

- Field 1: `measured` 73,652, `unmeasurable` 20, `vbi_ambiguous` 12,621
- Field 2: `measured` 86,180, `unmeasurable` 22, `vbi_ambiguous` 91

## Event census

- `Black`: 1
- `Garbage`: 1
- `Mute`: 29
- `PreSnow`: 1
- `Program`: 86,240
- `Relock`: 2
- `Snow`: 19
