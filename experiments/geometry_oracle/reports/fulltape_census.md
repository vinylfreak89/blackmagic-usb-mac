# Geometry oracle — whole-tape census

This is a measurement census, not an engine verdict.

- Exact units: **86,293**
- Transport ordinal range: **0–86,295**
- Internal device-short ordinal holes: **4, 9, 190**
- Relocks: **300, 43,737**
- Placement-forbidden annotated units: **53**
- Exact same-field repeats: **0**
- Measurable static-comb rows: **86,292**
- Oracle runtime: **1792.563 s** (**20.773 ms/exact unit**)

Four device-short periods precede the first exact unit. The three short periods inside
the exact-unit span remain visible as ordinal holes rather than shifting event labels.

| Field | Recorded top | Picture top | Any 608 waveform | Any parity-decoded 608 | Unique off-insert tape 608 | Black band | Exact bottom | Exact height | Last recorded | Flat raster | Exact repeat |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 86,273 | 86,272 | 86,273 | 86,156 | 40,169 | 22,120 | 86,273 | 51,081 | 86,274 | 268 | 0 |
| 2 | 86,271 | 86,269 | 86,274 | 86,270 | 112 | 3,647 | 86,271 | 86,164 | 86,274 | 265 | 0 |

## Top-status census

- Field 1: `measured` 51,081, `unmeasurable` 21, `vbi_ambiguous` 35,191
- Field 2: `measured` 86,164, `unmeasurable` 24, `vbi_ambiguous` 105

## Event census

- `Black`: 1
- `Garbage`: 1
- `Mute`: 29
- `PreSnow`: 1
- `Program`: 86,240
- `Relock`: 2
- `Snow`: 19
