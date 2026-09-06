# Raw-row answers for the top and comb questions

All line numbers are NTSC line numbers. Luma entries are mean/standard deviation over
samples 40–679. Chroma is the mean absolute U/V distance from regenerated neutral.
Comb energies are listed in shift order `-3,-2,-1,0,+1,+2,+3`; lower is better.

## 1. Commercial-tape field-1 top at units 635–759

The top is L23, not L28. L20–L21 are generated waveform rows, L22 is regenerated
blank, and L23–L27 are a continuous recorded, non-VBI dark band. The chroma distance
of that band is four to six times the regenerated-blank value even though its luma is
dark. L28 is only the first brighter row, not the first picture row.

Across all 125 units, the median and range are:

| line | luma mean median (range) | luma std median (range) | chroma median (range) |
|---:|---:|---:|---:|
| 23 | 3.964 (3.369–5.361) | 2.959 (2.336–3.776) | 1.836 (1.469–2.732) |
| 24 | 4.258 (3.612–5.791) | 3.326 (2.733–4.608) | 1.811 (1.401–2.533) |
| 25 | 10.144 (8.409–11.752) | 1.866 (1.446–3.717) | 1.933 (1.376–2.890) |
| 26 | 9.558 (7.756–11.073) | 1.561 (1.226–3.638) | 1.947 (1.478–2.719) |
| 27 | 9.750 (8.391–11.502) | 1.936 (1.425–3.661) | 2.115 (1.481–2.867) |
| 28 | 17.103 (11.688–18.592) | 9.177 (6.765–9.795) | 2.085 (1.539–2.690) |

Three unit witnesses, with each cell `mean/std/chroma`:

| unit | L22 | L23 | L24 | L25 | L26 | L27 | L28 |
|---:|:---|:---|:---|:---|:---|:---|:---|
| 635 | 1.369/0.482/0.421 | 3.862/3.188/2.358 | 5.322/4.579/2.189 | 11.034/3.665/2.243 | 9.286/3.435/2.037 | 10.875/3.536/2.540 | 17.538/9.072/2.328 |
| 700 | 1.380/0.485/0.414 | 3.786/2.831/1.904 | 3.938/3.024/1.831 | 9.386/1.833/1.871 | 9.062/1.575/1.746 | 9.144/1.840/2.061 | 15.747/8.845/2.094 |
| 759 | 1.384/0.486/0.429 | 3.820/2.836/1.957 | 3.987/3.162/1.987 | 10.988/1.804/2.349 | 9.869/1.488/2.168 | 10.944/2.052/2.090 | 17.148/7.847/2.000 |

The previous builder did not implement the dark-band ruling: it selected the first
picture-level luma onset and called the delayed result inferred. The revised builder
selects the first chroma-confirmed recorded row when at least three consecutive
non-VBI dark rows precede the brighter onset. All 125 units now have top L23.

## 2. Long comb offsets

### Commercial tape, units 635–759

This was a reference error, not inter-field misregistration. With the old L28 field-1
top, each witness minimizes at +3. With the raw-row L23 top, each minimizes at zero:

| unit | field-1 top | -3 | -2 | -1 | 0 | +1 | +2 | +3 | best |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 635 | old L28 | 19.634800 | 15.800736 | 12.161082 | 5.763254 | 5.445448 | 3.896631 | 3.204164 | +3 |
| 635 | raw L23 | 10.492887 | 6.943973 | 2.403798 | 1.963114 | 3.212043 | 6.454872 | 10.294535 | 0 |
| 700 | old L28 | 19.865597 | 16.127750 | 13.320058 | 9.600519 | 8.033212 | 5.343288 | 4.040442 | +3 |
| 700 | raw L23 | 7.629357 | 4.865915 | 2.219305 | 1.887654 | 3.438915 | 6.981975 | 11.243263 | 0 |
| 759 | old L28 | 12.043201 | 8.053687 | 5.859813 | 2.608691 | 2.148135 | 1.793044 | 1.491265 | +3 |
| 759 | raw L23 | 6.029564 | 3.121214 | 1.340780 | 1.226615 | 2.063312 | 4.310926 | 7.248534 | 0 |

Every one of the 125 corrected energy vectors has its minimum at zero. Of those,
104 pass the static/texture/decisiveness gates and 21 remain unmeasurable rather than
being assigned a shift.

### SP recording with V-stabilize off

This is genuine one-line inter-field displacement, not a wrong-partner artifact. The
old within-transport-unit ordering is physical slot 1 then slot 2 and normally expects
zero. The source-aligned ordering is slot 2 of unit `u` then slot 1 of unit `u+1`;
because that reverses raster parity, its normal geometric expectation is +1. The same
56 questioned units move from best +1 in the first ordering to best 0 in the second:
their departure from the applicable expectation remains one line.

| unit | pairing | expected | -3 | -2 | -1 | 0 | +1 | +2 | +3 | best |
|---:|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 89 | within slots | 0 | 9.227597 | 8.541274 | 7.292624 | 4.964197 | 4.346641 | 5.635007 | 7.777666 | +1 |
| 89 | source pair | +1 | 9.350044 | 7.880302 | 5.867253 | 3.869158 | 5.746634 | 7.897161 | 9.364110 | 0 |
| 100 | within slots | 0 | 11.640637 | 10.264158 | 8.360745 | 5.748763 | 5.010687 | 6.156451 | 8.147355 | +1 |
| 100 | source pair | +1 | 9.216341 | 7.633511 | 5.820759 | 4.404630 | 6.216643 | 8.057262 | 9.223660 | 0 |
| 108 | within slots | 0 | 12.240008 | 10.866971 | 8.886954 | 6.305631 | 5.519269 | 6.791464 | 8.546745 | +1 |
| 108 | source pair | +1 | 9.796139 | 8.454252 | 6.532600 | 4.874536 | 6.855328 | 8.721749 | 10.296652 | 0 |

The 56 units are 89, 99–102, 108–112, 129–131, 135–137, 143–144,
146–149, 152, 158–162, 166–168, 170–177, 181–187, 191, 196–198,
208–210, 221, and 580–581. Source-pair raw-row witnesses are:

| unit | first parity: current slot 2 | second parity: following slot 1 |
|---:|:---|:---|
| 89 | top L286=4.270/3.886; L523=89.747/37.566; switch L524=63.605/43.775; L526 blank=1.373/0.530 | top L23=108.128/30.877; L259=87.287/37.721; switch L260=70.350/33.505; L263 blank=1.380/0.495 |
| 100 | top L286=19.169/32.003; L523=92.972/37.206; switch L524=77.122/45.385; L526 blank=1.370/0.502 | top L23=110.664/31.456; L259=92.808/36.986; switch L260=81.272/29.720; L263 blank=1.387/0.494 |
| 108 | top L286=17.398/31.271; L523=92.792/38.920; switch L524=83.878/39.888; L526 blank=1.373/0.515 | top L23=107.534/30.447; L259=94.047/37.407; switch L260=76.528/31.313; L263 blank=1.389/0.516 |

The revised CSV records that source partner and its expected +1 ordering explicitly.
Across the capture the measurable source-pair result is: +1/agree 455, 0/disagree
115, +2/disagree 1; 37 are unmeasurable.

## 3. SP recording unit 103

This is a genuine isolated registration departure. Units 102 and 103 have identical
geometry: field 1 top/switch L23/L259 and field 2 L286/L523. Unit 102 minimizes at
zero (energy 3.467177); unit 103 minimizes at +1:

| unit | -3 | -2 | -1 | 0 | +1 | +2 | +3 | best |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 103 | 10.190085 | 8.927196 | 7.601098 | 5.371530 | 4.344512 | 5.897627 | 8.051416 | +1 |

The deciding reliable spans are field 1 L23–L258 and field 2 L286–L522.
Boundary rows are field 1 L23=109.273/31.615, L258=91.341/36.717,
switch L259=66.936/39.435, blank L263=1.394/0.501; field 2
L286=114.573/32.204, L522=93.864/36.477, switch L523=29.714/42.922,
blank L526=1.380/0.531. Neither top nor switch moved, so this is not a
geometry-coordinate error.

## 4. SP field-2 top correction

Units 87, 258, 439, and 467 now have top L287. In each, L286 is a dark recorded
non-picture row and L287 begins structured picture; the same-slot body moves +1.
The source-field-parity gate prevents the analogous dark first picture rows in the
half-field-phased off pass from being reclassified.

| unit | L286 luma | L287 luma | same-slot body energy best/second | body ratio |
|---:|:---|:---|:---|---:|
| 87 | 5.456/4.131 | 112.223/30.814 | 6.847/7.009 | 0.977 |
| 258 | 3.758/3.160 | 124.836/31.692 | 9.295/9.941 | 0.935 |
| 439 | 6.045/3.928 | 140.872/36.176 | 10.973/11.808 | 0.929 |
| 467 | 5.688/4.273 | 134.306/43.282 | 7.242/7.546 | 0.960 |

The rebuilt SP field-2 top histogram is L286: 604 and L287: 4.
