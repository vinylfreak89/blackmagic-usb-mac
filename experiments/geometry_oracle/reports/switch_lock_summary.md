# Geometry-lock census

The comparators are fixed arrays ordered by cumulative count. A hit increments only its own count and bubbles upward; a challenger becomes comparator only after its count passes the incumbent. A new value uses a free slot or replaces the least-counted slot when full; counts never decrement. Only clip and line-22 level use arrays, with 8/8 slots. H and c are fixed constants from the segment seed, not comparators.

A counter discontinuity resets all arrays immediately. A hidden top or switch holds the prior decision and counts. `switch_first_line` and `first_full_other_head_line` remain raw evidence. The first measurable segment unit seeds H and c; only a raw caption or a comb-confirmed hidden-top seed can re-seed them before the next lock-like reset.

## SP recording

- units: 608
- source lock: acquiring: 3, hold: 10, locked: 595
- immediate resets: 0

### Field 1

- field lock: acquiring: 3, hold: 9, locked: 596
- final segment H constant: 237
- final segment c constant: 3
- final segment clip comparator/count/runner-up: 262/602/0
- final segment account switch line: 261
- final segment line-22 level comparator/count/runner-up: 7/11/9
- switch-count classes: hidden: 3, reported-hold: 9, travel: 596
- first-row observations: black22: 47, picture: 561

### Field 2

- field lock: acquiring: 3, hold: 2, locked: 603
- final segment H constant: 236
- final segment c constant: 4
- final segment clip comparator/count/runner-up: 525/608/0
- final segment account switch line: 522
- final segment line-22 level comparator/count/runner-up: -1/0/0
- switch-count classes: hidden: 3, reported-hold: 2, travel: 603
- first-row observations: picture: 608

## EP recording

- units: 621
- source lock: acquiring: 9, hold: 1, locked: 611
- immediate resets: 0

### Field 1

- field lock: acquiring: 9, hold: 1, locked: 611
- final segment H constant: 235
- final segment c constant: 5
- final segment clip comparator/count/runner-up: 262/621/0
- final segment account switch line: 261
- final segment line-22 level comparator/count/runner-up: 20/74/71
- switch-count classes: hidden: 9, reported-hold: 1, travel: 611
- first-row observations: black22: 621

### Field 2

- field lock: acquiring: 7, locked: 614
- final segment H constant: 235
- final segment c constant: 5
- final segment clip comparator/count/runner-up: 525/621/0
- final segment account switch line: 523
- final segment line-22 level comparator/count/runner-up: 24/63/57
- switch-count classes: hidden: 7, travel: 614
- first-row observations: picture: 621

## SP recording, V-stabilize off

- units: 608
- source lock: acquiring: 1, hold: 33, locked: 574
- immediate resets: 0

### Field 1

- field lock: hold: 11, locked: 597
- final segment H constant: 237
- final segment c constant: 3
- final segment clip comparator/count/runner-up: 262/595/5
- final segment account switch line: 260
- final segment line-22 level comparator/count/runner-up: -1/0/0
- switch-count classes: reported-hold: 11, travel: 597
- first-row observations: picture: 608

### Field 2

- field lock: acquiring: 2, hold: 27, locked: 579
- final segment H constant: 237
- final segment c constant: 3
- final segment clip comparator/count/runner-up: 525/582/7
- final segment account switch line: 523
- final segment line-22 level comparator/count/runner-up: -1/0/0
- switch-count classes: hidden: 2, reported-hold: 27, travel: 579
- first-row observations: other-non-picture: 20, picture: 588

## commercial tape

- units: 919
- source lock: acquiring: 706, hold: 211, no-lock: 2
- immediate resets: 2

### Field 1

- field lock: acquiring: 706, locked: 211, no-lock: 2
- final segment H constant: 237
- final segment c constant: 3
- final segment clip comparator/count/runner-up: 262/901/0
- final segment account switch line: 260
- final segment line-22 level comparator/count/runner-up: -1/0/0
- switch-count classes: hidden: 706, reset: 2, travel: 211
- first-row observations: ambiguous: 3, black22: 2, other-non-picture: 12, picture: 901, vbi-or-caption: 1

### Field 2

- field lock: acquiring: 706, hold: 211, no-lock: 2
- final segment H constant: 238
- final segment c constant: 2
- final segment clip comparator/count/runner-up: 525/439/0
- final segment account switch line: 524
- final segment line-22 level comparator/count/runner-up: -1/0/0
- switch-count classes: hidden: 706, reported-hold: 211, reset: 2
- first-row observations: ambiguous: 145, other-non-picture: 16, picture: 758

## SP field-2 continuous minus-one test

Verdict: a continuous field-2 minus-one is rejected. Pulling field 2 down by one inserts the Shuttle-overwritten L285 rather than recovering a source line, and it raises comb energy in every unit with a seven-shift vector. This falsifies the field-sitting-high explanation; the rows do not separately prove whether the remaining band difference is raster half-line geometry or partial-line convention.

- current field-2 top: 286: 595, 287: 13
- L285 present as overwritten blank: 608/608 units
- L285 luma mean range / median: 1.350-1.406 / 1.377
- L285 luma standard-deviation range / median: 0.477-0.491 / 0.485
- comb comparison: field 2 pulled down one: 2, measured tops: 605
- E(field2−1) − E(measured): range / median -3.342407-4.697690 / 2.395196
- field-1 explicit caption/VBI confirmation counts: caption 46, VBI 441

### Deciding raw rows and comb vectors

- unit 20: tops L24/L286; switch evidence L261/L522; comb `-3:14.279536,-2:11.783522,-1:7.839751,0:4.720809,1:7.827952,2:11.693971,3:14.362869`; L284 Y=23.947/41.218 Cstd=0.617; L285 Y=1.380/0.485 Cstd=0.621; L286 Y=115.423/28.467 Cstd=18.116; L287 Y=114.502/27.511 Cstd=16.713; L288 Y=117.394/27.782 Cstd=19.263
- unit 87: tops L24/L287; switch evidence L261/L524; comb `-3:7.893877,-2:6.660991,-1:5.264322,0:3.419033,1:4.100786,2:6.063034,3:7.551185`; L284 Y=23.992/41.311 Cstd=0.644; L285 Y=1.364/0.481 Cstd=0.644; L286 Y=5.456/4.131 Cstd=14.793; L287 Y=112.223/30.814 Cstd=13.022; L288 Y=109.487/32.321 Cstd=17.009
- unit 200: tops L24/L286; switch evidence L261/L522; comb `-3:14.008963,-2:11.655437,-1:8.163421,0:4.823828,1:8.170074,2:11.238931,3:13.660611`; L284 Y=24.027/41.325 Cstd=0.655; L285 Y=1.392/0.488 Cstd=0.571; L286 Y=130.117/31.608 Cstd=27.929; L287 Y=127.483/34.068 Cstd=25.741; L288 Y=128.713/34.286 Cstd=21.994
