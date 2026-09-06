# Row-level adjudication: EP top and commercial-tape switch

All line numbers are NTSC line numbers. Luma measurements are mean/standard
deviation over samples 40–679. Correlations are Pearson correlations over
samples 24–696 against the following row. This report contains no smoothing,
carried coordinate, or substituted measurement.

## 1. EP recording, field-1 top

**Verdict:** the old reference is one line late at the three nominated units.
The supplied earlier engine record is right at those units. The old reference
rule was not rejecting the row because its amplitude was reduced: after finding
one in-field caption row it unconditionally selected `caption + 2`. That fixed
offset skipped a valid first picture row. A separate no-caption fallback has an
activity midpoint, but that path did not decide these units.

| ordinal | counter | line | luma | correlation to next line | reading |
|---:|---:|---:|:---|---:|:---|
| 3 | 1913 | 23 | 26.053/42.668 | 0.142 | VBI-type waveform |
| 3 | 1913 | 24 | 38.386/50.191 | 0.010 | second VBI-type waveform |
| 3 | 1913 | 25 | 84.530/46.195 | 0.981 | first picture row |
| 3 | 1913 | 26 | 106.768/64.706 | — | picture |
| 57 | 1967 | 23 | 57.507/57.444 | -0.134 | caption waveform |
| 57 | 1967 | 24 | 97.660/38.838 | 0.983 | reduced-amplitude first picture row |
| 57 | 1967 | 25 | 127.951/56.208 | — | picture |
| 100 | 2010 | 23 | 65.845/57.923 | -0.147 | caption waveform |
| 100 | 2010 | 24 | 83.486/38.623 | 0.956 | reduced-amplitude first picture row |
| 100 | 2010 | 25 | 122.305/56.857 | — | picture |

The corrected tops are L25, L24, and L24 respectively; the old values were
L26, L25, and L25.

Across all 621 units, correlating the row immediately above the **old** reference
top with that top gives:

| correlation class | units | corrected disposition |
|:---|---:|:---|
| `r >= 0.9` | 180 | all 180 rows become the first picture row |
| `0.4 < r < 0.9` | 213 | 212 become picture; 1 remains VBI-type |
| `r <= 0.4` | 228 | 34 become picture; 194 remain VBI-type |

Correlation is therefore corroboration, not the VBI classifier. The corrected
source-blind rule examines the row immediately after a detected caption. It
accepts that row as picture unless it is independently detected as another
waveform or it is an isolated low-structure row followed by a substantially
brighter, more structured row. This moves 426 old tops up one line and retains
195. Against the supplied earlier engine record, 423 of its 601 one-line
disagreements now agree; 178 remain one line later because the engine accepted
an isolated VBI-type row. The 17 prior agreements remain agreements. Three
earlier engine rows were `no-picture`; the corrected reference retains numeric
raw-row measurements there.

Deciding retained examples are counter 2066, where L25 is 18.141/2.668 with
`r=-0.075` before structured L26; counter 2303, where L24 is 16.789/2.515 with
`r=0.067` before structured L25; and counter 2410, where L25 is 22.267/2.092
with `r=-0.081` before structured L26. The fixed reference starts at L26, L25,
and L26 respectively rather than treating those isolated rows as picture.

The rebuilt field-1 top histogram is L24:207, L25:275, L26:139.

## 2. EP recording, field-2 top

**Verdict:** the reference is right at L288 in all 621 units; the supplied
earlier engine record is two lines early. The signature is not merely low
correlation. L286 has a localized pulse/bar in its left portion and a nearly
flat right span. L287 has run-in bursts in its left portion followed by a low,
flat remainder. These rows do not continue as whole-width picture structure.
The sustained body starts at L288 and normally remains coherent into L289.

| ordinal | counter | row pair | first-row luma | correlation |
|---:|---:|:---|:---|---:|
| 3 | 1913 | L286→L287 | 47.263/47.336 | 0.148 |
| 3 | 1913 | L287→L288 | 29.367/44.417 | 0.231 |
| 3 | 1913 | L288→L289 | 115.951/62.664 | 0.984 |
| 57 | 1967 | L286→L287 | 42.753/44.374 | 0.277 |
| 57 | 1967 | L287→L288 | 25.105/40.663 | 0.359 |
| 57 | 1967 | L288→L289 | 135.600/52.737 | 0.986 |
| 100 | 2010 | L286→L287 | 42.890/44.555 | 0.158 |
| 100 | 2010 | L287→L288 | 25.208/41.410 | 0.237 |
| 100 | 2010 | L288→L289 | 127.021/49.733 | 0.871 |

Capture-wide correlation medians are 0.102 for L286→L287, 0.084 for
L287→L288, and 0.927 for L288→L289. Their ranges are -0.308..0.340,
-0.788..0.493, and 0.531..0.996. The waveform instrument identifies L287 in
all 621 units. The complete top decision is observed in 602 and inferred at
the same L288 coordinate in 19 whose body correlation is weaker.

This is the comparable VBI signature: localized pulse/run-in structure, a flat
remainder, failure to continue as a whole-width row, and a following sustained
body. Decorrelation alone is insufficient because a genuine dark first band can
also be decorrelated from the brighter row below it.

## 3. Commercial tape, field-1 head switch

### What the old `inferred` reading meant

`inferred` with cues `none` did not carry a previous coordinate and did not
derive one from a preset band length. It selected the strongest normalized
row-to-row transition in the measured bottom tail, then a weak partial-row
heuristic could move the boundary to its predecessor. Because no edge, RF, or
AGC cue independently identified that predecessor, the result remained
`inferred`. The defect was that a full other-head row can carry its own
horizontal blanking in the middle of the raster row; the old leading-run and
whole-row tests missed that direct signature, while the weak predecessor test
could report a line too early.

The fixed common path now detects a 64-sample near-blank run between samples 20
and 240 when the same span above and the later part of the current row remain
above the field's measured blank level. That row is the directly observed first
full other-head row. Its predecessor advances `switch_first_line` only when a
structural partial, skew, AGC step, or strong one-third departure directly
supports it. A generic weak transition can no longer advance the boundary.

### Deciding rows

| ordinal | counter | measured rows | verdict |
|---:|---:|:---|:---|
| 630 | 6672 | L258 23.427/2.584; L259 23.445/2.672 (`r=-0.202`, narrow transient at x691); L260 17.345/9.425 (`r=0.012`, MAD 8.222, lag 29, internal blank x82–145 at Y1.391); L261 16.552/9.120 (`r=0.956`) | first full other-head row L260; earliest switch row L260 |
| 700 | 6742 | L258 22.042/3.417; L259 22.630/2.942; L260 22.475/6.439 (`r=0.318`, MAD 3.580, partial); L261 17.556/9.091 (`r=-0.303`, MAD 8.513, internal blank x41–104 at Y1.391); L262 16.067/8.449 (`r=0.976`) | first full other-head row L261; earliest switch row L260 |
| 800 | 6842 | L258 16.930/1.549; L259 17.594/1.459; L260 21.772/21.392 (`r=0.088`, MAD 5.703, transient, skew/AGC partial); L261 13.969/6.746 (`r=0.121`, MAD 9.172, internal blank x56–119 at Y1.375); L262 12.741/6.280 (`r=0.953`) | first full other-head row L261; earliest switch row L260 |

Thus the fixed engine's L260/L261 full-row readings match the raw signature.
The reference's L260 at counters 6742 and 6842 is also correct, but names the
start of the unreliable switch band, including the directly measured partial
row; it is not claiming that L260 is already entirely the other head.

Two prior reference errors are explicit regression witnesses. At counter 6665,
L259 is a normal row (23.581/1.805, MAD 2.063) and L260 contains the internal
blank at x98–161; the old L259 becomes L260. At counter 6903, L259 remains
coherent (`r=0.840`, MAD 4.692), L260 is the supported partial (`r=0.272`, MAD
10.391, lag 26), and L261 contains the internal blank at x39–102; the old L259
becomes L260.

### Stable-interval census

The 582 exact units at ordinal 551 and later have this first-full-other-head
signature:

| signature row | count |
|---:|---:|
| L260 | 67 |
| L261 | 464 |
| unmeasurable | 51 |

Across adjacent units where the signature is measurable on both sides, it
changes four times: ordinal/counter 603/6645 (L261→L260), 646/6688
(L260→L261), 672/6714 (L261→L260), and 696/6738 (L260→L261). It is therefore
not constant from unit to unit.

The rebuilt `switch_first_line` histogram over the same interval is L259:11,
L260:391, L261:143, and unmeasurable:37. The joint census is:

| full other-head row | reference switch row | count |
|---:|---:|---:|
| L261 | L260 | 326 |
| L261 | L261 | 133 |
| L260 | L260 | 42 |
| L260 | L259 | 8 |
| L261 | L259 | 3 |
| L261 | unmeasurable | 2 |
| L260 | unmeasurable | 17 |
| unmeasurable | unmeasurable | 18 |
| unmeasurable | L260 | 23 |
| unmeasurable | L261 | 10 |

The common one-row difference is real semantics: the partial predecessor is
the first unreliable switch-band row, while the internal-blank row is the first
row entirely delivered by the other head.

### Earlier flat-grey `no-picture` interval

For counters 6805–6875 inclusive, the rebuilt reference records:

| field | top histogram and status | switch histogram and status | overall status |
|---:|:---|:---|:---|
| 1 | L23:55 observed; L25:14 inferred; 2 unmeasurable | L260:48, L261:21 observed; 2 unmeasurable | observed:55; censored:14; unmeasurable:2 |
| 2 | L286:70 (55 observed, 15 inferred); 1 unmeasurable | L522:60, L523:10 observed; 1 unmeasurable | observed:55; inferred:15; unmeasurable:1 |

Counter 6842 is a direct witness that flat does not mean absent: field 1 L23,
L24, and L25 are 20.027/1.302, 20.609/1.349, and 19.962/1.427; field 2 L286,
L287, and L288 are 20.200/1.432, 21.670/1.299, and 20.911/1.200. The current
record is top/switch L23/L260 and L286/L522, both observed. Counters 6863–6875
likewise remain measurable despite their low spatial texture: counter 6863 is
L23/L260 and L286/L523, while counter 6875 is L23/L261 and L286/L522, all
observed. Only counter 6818 field 1 and counter 6820 both fields remain
unmeasurable; no coordinate is substituted there.

## Builder and acceptance consequences

The three fixes are covered by synthetic and raw-capture regressions: a picture
row immediately following a caption must survive, an isolated low-structure row
must not; internal mid-row blanking must identify the first full other-head row,
and a flat field with a clear recorded-level boundary against raster blanking
must remain measurable. Counters 6665, 6672, 6742, 6842, 6870, and 6903 retain
their raw distinctions.
All four reference CSVs and their dependent reports were rebuilt through the
same source-blind path.

The earlier commercial-tape assertion remains valid for the observed picture
top: field 1 is L23 in 481 observed units and field 2 is L286 in 356. It is
falsified for switch row and band length. The observed field-1 switch histogram
is L259:7, L260:341, L261:133; field 2 is L522:173, L523:183. The invariant
report now records these as failures instead of aborting or silently counting
them as agreement.

## Objection

I object to applying “one stable value” to the switch row or band length. The
raw full-other-head signature itself moves at counters 6645, 6688, 6714, and
6738 while the accepted observed picture top remains fixed. The evidence at
counter 6672 (full other-head L260) versus counters 6742 and 6842 (full
other-head L261, with partial L260) makes that falsification independent of
either geometry implementation. Stability is supported for picture top, not
for the head-switch boundary.
