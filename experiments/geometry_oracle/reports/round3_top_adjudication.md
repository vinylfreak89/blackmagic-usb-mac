# Geometry oracle — round-3 top adjudication

This report records independent raw-raster measurements. Coordinates are NTSC lines. The
candidate row and following row statistics use luma samples 40–679; chroma deviation is measured
against regenerated neutral. All six candidate rows exceeded the regenerated-chroma gate and
were therefore decoder-originated.

## Requested ordinals

All six fields had blanking mean 1.0 and robust noise 0.25. `Old gap/top` names the superseded
forward-search result. `Recorded/picture` names the replacement two-edge measurement.

| Ordinal | Old gap/top | Active top | Candidate mean/std | Candidate chroma/gate | Following mean/std | Recorded/picture | Raw-supported picture top |
|---:|---|---:|---|---|---|---|---:|
| 420 | 25/26 | 23 | 154.059/21.053 | 16.618/0.671 | 154.706/19.735 | 23/23 | 23 |
| 5,453 | —/23 | 23 | 5.828/3.764 | 9.435/0.674 | 143.883/27.195 | 23/24 | 24 |
| 12,183 | 23/24 | 23 | 5.114/3.424 | 9.625/0.678 | 102.261/37.955 | 23/24 | 24 |
| 14,894 | —/23 | 23 | 8.105/4.450 | 9.310/0.671 | 163.883/16.681 | 23/24 | 24 |
| 18,210 | 23/24 | 23 | 5.180/4.291 | 15.538/0.672 | 108.103/36.536 | 23/24 | 24 |
| 20,799 | 23/24 | 23 | 5.584/4.213 | 9.329/0.682 | 105.547/11.651 | 23/24 | 24 |

The raw channels disagreed with the proposed adjudication at 12,183, 18,210, and 20,799: line 23
was a flat recorded-black row, not picture texture continuous with line 24. They agreed that the
old oracle was wrong at 5,453 and 14,894. At 420, line 23 was high-level textured picture and the
old forward search incorrectly promoted the dimmer in-picture line 25 to a gap; the picture top
was measurable at 23.

## Whole-tape definition change

The table compares the old `top_line` with the new `picture_top_line` by transport ordinal.
`Validity` is a valid-to-invalid change; rows invalid in both references are shown separately and
are not counted as changed.

| Field | ≤−4 | −3 | −2 | −1 | 0 | +1 | +2 | +3 | ≥+4 | Validity | Both invalid | Changed |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,676 | 235 | 329 | 24,510 | 56,555 | 2,591 | 15 | 46 | 315 | 1 | 20 | 29,718 |
| 2 | 3,166 | 92 | 625 | 285 | 81,442 | 47 | 273 | 12 | 327 | 2 | 22 | 4,829 |

The dominant field-1 change was −1 because the removed heuristic had searched forward across
twelve rows and commonly selected a darker row inside valid picture. Larger changes were chiefly
flat/dark rasters where that same search could run deep into the field; the new reference exposes
those as late or unmeasurable picture onsets rather than pretending the intermediate row was line
22.

## Re-scored `be08bba` clamped crops

Buckets are `published start − reference top`.

| Field | Authority | Scored | <−3 | −3 | −2 | −1 | 0 | +1 | +2 | +3 | >+3 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | caption | 40,167 | 6 | 0 | 73 | 326 | 39,762 | 0 | 0 | 0 | 0 |
| 1 | waveform | 1,602 | 0 | 34 | 395 | 482 | 365 | 326 | 0 | 0 | 0 |
| 1 | geometry | 44,450 | 252 | 172 | 10 | 8,238 | 30,476 | 2,985 | 1,831 | 486 | 0 |
| 2 | caption | 110 | 87 | 0 | 0 | 0 | 23 | 0 | 0 | 0 | 0 |
| 2 | waveform | 35,249 | 0 | 35 | 511 | 38 | 18,849 | 15,816 | 0 | 0 | 0 |
| 2 | geometry | 50,857 | 253 | 7 | 187 | 120 | 43,039 | 4,710 | 923 | 1,618 | 0 |

The scorer joined 86,293 exact units, excluded 53 placement-forbidden units, and reported 39,921
disagreeing field decisions. Published transitions were 5,487/1,547 for fields 1/2; 4,815/63
coincided with a reference-top change. The clamped input contained no out-of-raster crops.
