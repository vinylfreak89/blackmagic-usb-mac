# SP residual body/comb audit and EP census

All line numbers are NTSC line numbers. Body displacement is measured against the
same raster slot in the preceding unit over the reliable picture body at shifts
`-3..+3`; a value is reported only when best/second energy is at most 0.8.
`U(best,ratio)` preserves an indecisive minimum without treating it as a
measurement. Comb energies are ordered `-3,-2,-1,0,+1,+2,+3` and use the common
same-parity static mask. Luma entries are mean/standard deviation over samples
40–679.

## SP recording: nominated residual units

| unit | field-1 body | field-2 body | tops F1/F2 | switches F1/F2 | comb result | comb energies |
|---:|:---|:---|:---|:---|:---|:---|
| 74 | -1 (0.649) | U(0,0.968) | L23/L286 | L261/L523 | 0 | 8.598060,7.151729,5.542938,3.440272,4.143836,5.571555,7.146872 |
| 75 | U(+1,0.991) | -1 (0.635) | L24/L286 | L262/L522 | 0 | 5.609293,4.229891,3.804317,3.410157,4.930398,6.134066,7.418221 |
| 76 | -1 (0.609) | U(+1,0.951) | L23/L286 | L261/L524 | U(0) | 7.640542,6.357279,4.950453,1.909835,1.910553,4.396089,6.217270 |
| 77 | 0 (0.050) | U(-2,0.983) | L23/L286 | L261/L522 | U(0) | 5.009167,4.241667,4.055000,2.081389,4.426667,5.837500,6.888333 |
| 78 | U(-1,0.942) | U(+1,0.966) | L23/L286 | L259/L523 | 0 | 6.304899,4.989819,4.112577,3.513427,4.016556,4.502849,5.894032 |
| 79 | +1 (0.594) | 0 (0.590) | L23/L286 | L260/L523 | 0 | 7.401668,6.045509,4.403544,3.556716,4.128612,4.504331,6.065533 |
| 80 | 0 (0.591) | 0 (0.612) | L23/L286 | L260/L522 | 0 | 9.464954,8.068051,6.092463,3.818553,5.846576,7.917503,9.472044 |
| 101 | 0 (0.760) | 0 (0.766) | L23/L286 | L260/L523 | 0 | 8.450474,7.094532,5.189943,3.667221,5.092015,6.830019,8.280053 |
| 102 | -1 (0.587) | 0 (0.613) | L23/L286 | L259/L523 | 0 | 7.227289,5.821755,4.525969,3.467177,3.893553,4.314902,5.750576 |
| 103 | 0 (0.574) | 0 (0.716) | L23/L286 | L259/L523 | +1 | 10.190085,8.927196,7.601098,5.371530,4.344512,5.897627,8.051416 |
| 104 | 0 (0.722) | U(0,0.975) | L23/L286 | L259/L523 | U(+2) | 8.700870,7.580433,6.318584,4.531810,4.404969,4.377108,6.102477 |
| 105 | U(+3,0.991) | -1 (0.697) | L25/L286 | L262/L522 | 0 | 6.765859,5.456810,4.339807,3.626308,4.323587,5.578446,6.942558 |
| 106 | -1 (0.714) | 0 (0.585) | L24/L286 | L261/L522 | 0 | 8.927966,7.682543,5.795279,3.985042,6.013871,8.113835,9.928978 |

The comb does not follow the nominated field-body displacement at any of the five
units and then return:

- Field 2 at unit 75: comb remains zero from 74 to 75; 76 is indecisive. Field 1's
  measured geometry moves down one line at 75, so this is not evidence that field 2
  moved beneath a clamped top.
- Field 1 at unit 76: the premise that its top is clamped is false. From 75 to 76,
  its top and switch both move up one line, L24/L262 to L23/L261, exactly with the
  measured body displacement. This is an already-modelled rigid field move; the
  comb at 76 is indecisive because shifts zero and +1 differ by only 0.000718.
- Field 1 at unit 79: comb is zero at 78, 79, and 80, while field 2 measures zero
  body displacement at 79. The +1 body result is content motion; the switch's
  L259→L260 move is independent.
- Field 1 at unit 102: comb stays zero at 101 and 102. It becomes +1 only at 103,
  where both fields measure zero body displacement and all four top/switch
  coordinates remain fixed. Unit 102 is content motion; unit 103 is the separate
  recorded/playback registration departure already recorded by the comb audit.
- Field 2 at unit 105: 104 is indecisive and 105–106 both minimize at zero. Field 2
  has no measured +1 return at 106. Field 1's top/switch simultaneously move
  L23/L259→L25/L262, so this does not establish a clamped field-2 move.

No new crop displacement is justified. Unit 76 field 1 is the sole nominated
physical field displacement, and the reference already follows it.

### Target-unit raw-row boundaries

| unit | field | top | last row before switch | switch | band/blank evidence |
|---:|---:|:---|:---|:---|:---|
| 75 | 1 | L24=111.688/30.825 | L261=85.381/35.857 | L262=22.228/33.573 | L263=1.381/0.498 |
| 75 | 2 | L286=110.552/32.251 | L521=84.477/36.699 | L522=58.359/39.419 | L525=10.611/0.760; L526=1.363/0.500 |
| 76 | 1 | L23=111.369/31.411 | L260=84.030/36.456 | L261=16.195/24.272 | L262=10.887/0.942; L263=1.402/0.503 |
| 76 | 2 | L286=111.463/31.453 | L523=83.853/36.538 | L524=16.166/24.329 | L525=10.841/0.981; L526=1.391/0.507 |
| 79 | 1 | L23=111.905/30.473 | L259=89.139/37.349 | L260=50.380/44.699 | L262=11.292/0.983; L263=1.375/0.487 |
| 79 | 2 | L286=110.600/32.529 | L522=87.495/36.433 | L523=10.119/0.943 | L525=10.275/0.898; L526=1.391/0.534 |
| 102 | 1 | L23=114.375/32.554 | L258=92.525/37.045 | L259=66.916/38.570 | L262=10.383/0.906; L263=1.367/0.492 |
| 102 | 2 | L286=114.970/31.430 | L522=92.575/36.257 | L523=31.144/43.905 | L525=10.977/0.877; L526=1.381/0.532 |
| 105 | 1 | L25=114.319/31.378 | L261=96.428/36.515 | L262=29.202/43.077 | L263=1.363/0.484; L264=1.389/0.488 |
| 105 | 2 | L286=112.706/31.810 | L521=90.467/36.369 | L522=65.856/38.327 | L525=10.186/0.902; L526=1.373/0.503 |

## EP recording census

All 621 units have `cv_inspected` measurements in both fields; none is
unmeasurable. The per-field histograms are:

| field | picture top | first switch row | band length | closure | RF presence |
|---:|:---|:---|:---|:---|:---|
| 1 | L24:207; L25:275; L26:139 | L259:4; L260:263; L261:354 | 4:421; 5:198; 6:1; 7:1 | observed:621 | absent:529; disappeared:25; present:14; reappeared:53 |
| 2 | L288:621 | L522:270; L523:351 | 5:351; 6:270 | observed:621 | absent:527; disappeared:55; present:12; reappeared:27 |

Comb is observed at 330 units and unmeasurable at 291. Of the observations, 107
have shift zero and agree with zero-shift geometry; 223 have shift -1 and
disagree. The complete disagreement list and raw-row witnesses are in
`comb_summary.md`. This changed when the field-1 top correction admitted the
previously excluded first picture row; it is measurement output, not a forced
zero-shift result.

For fixed-top switch transitions, every measurable transition retains its preceding
comb registration. Field 1 has 8 transitions: 1 measurable/unchanged and 7
unmeasurable. Field 2 has 189: 82 measurable/unchanged and 107 unmeasurable. The
complete unit lists by field, switch displacement, and measurability, with three
raw-row witnesses per populated cell, are in `comb_summary.md`.

## Objection

The SP field-1 unit-76 case is not a top-clamped field move. Unit 75 is top/switch
L24/L262 and unit 76 is L23/L261; the reliable body also measures -1. Treating that
unit as evidence for motion hidden beneath an unchanged top contradicts the raw
coordinates. The remaining four nominated units do not produce the requested
comb-follow-and-return signature, so the proposed crop correction is not supported
by this audit.
