# Running geometry-lock census

The comparators are fixed arrays ordered by cumulative count. A hit increments only its own count and bubbles upward; a challenger becomes comparator only after its count passes the incumbent. A new value uses a free slot or replaces the least-counted slot when full; counts never decrement. The band array has 8 slots, and the first-row-state array has 8 slots. These are memory capacities, not decision constants.

A counter discontinuity resets both arrays immediately. A hidden top or switch holds the prior decision and counts. `switch_first_line` and `first_full_other_head_line` remain raw evidence. Locked geometry uses the running band comparator; `comparator-1` is partial-line travel, values above it are `band+`, and values below `comparator-1` are `dropped` or `fell-out` displacement evidence.

## SP recording

- units: 608
- source lock: acquiring: 98, hold: 506, locked: 1, no-lock: 3
- immediate resets: 0

### Field 1

- field lock: acquiring: 98, hold: 495, locked: 12, no-lock: 3
- observed S..clip band rows: -1: 596, 2: 1, 3: 10, 4: 1
- final segment band comparator/count/runner-up: 3/10/1
- final segment switch height/projected line: 237/260
- final segment first-row comparator/count/runner-up: black22/347/122
- asymmetric band classes: band+: 2, hidden: 596, travel: 10
- first-row observations: black22: 484, other-non-picture: 2, picture: 122

### Field 2

- field lock: hold: 450, locked: 155, no-lock: 3
- observed S..clip band rows: -1: 453, 3: 120, 4: 35
- final segment band comparator/count/runner-up: 3/120/35
- final segment switch height/projected line: 237/523
- final segment first-row comparator/count/runner-up: picture/598/4
- asymmetric band classes: band+: 22, hidden: 453, travel: 133
- first-row observations: black22: 4, picture: 604

## EP recording

- units: 621
- source lock: acquiring: 567, hold: 41, locked: 1, no-lock: 12
- immediate resets: 0

### Field 1

- field lock: acquiring: 567, hold: 41, locked: 1, no-lock: 12
- observed S..clip band rows: -1: 620, 2: 1
- final segment band comparator/count/runner-up: 2/1/0
- final segment switch height/projected line: 238/264
- final segment first-row comparator/count/runner-up: picture/414/154
- asymmetric band classes: hidden: 620, travel: 1
- first-row observations: black22: 195, picture: 426

### Field 2

- field lock: hold: 551, locked: 58, no-lock: 12
- observed S..clip band rows: -1: 563, 3: 51, 4: 7
- final segment band comparator/count/runner-up: 3/51/7
- final segment switch height/projected line: 237/525
- final segment first-row comparator/count/runner-up: picture/590/0
- asymmetric band classes: band+: 4, hidden: 563, travel: 54
- first-row observations: ambiguous: 19, picture: 602

## SP recording, V-stabilize off

- units: 608
- source lock: hold: 41, locked: 567
- immediate resets: 0

### Field 1

- field lock: hold: 22, locked: 586
- observed S..clip band rows: -1: 22, 1: 12, 2: 572, 3: 1, 4: 1
- final segment band comparator/count/runner-up: 2/572/12
- final segment switch height/projected line: 238/261
- final segment first-row comparator/count/runner-up: picture/606/2
- asymmetric band classes: band+: 2, hidden: 22, travel: 584
- first-row observations: black22: 2, picture: 606

### Field 2

- field lock: hold: 39, locked: 569
- observed S..clip band rows: -1: 39, 1: 81, 2: 406, 3: 81, 4: 1
- final segment band comparator/count/runner-up: 2/406/81
- final segment switch height/projected line: 238/524
- final segment first-row comparator/count/runner-up: picture/573/0
- asymmetric band classes: band+: 82, hidden: 39, travel: 487
- first-row observations: ambiguous: 15, other-non-picture: 20, picture: 573

## commercial tape

- units: 919
- source lock: acquiring: 1, hold: 20, locked: 511, no-lock: 387
- immediate resets: 2

### Field 1

- field lock: acquiring: 1, hold: 19, locked: 512, no-lock: 387
- observed S..clip band rows: -1: 407, 2: 462, 3: 50
- final segment band comparator/count/runner-up: 2/462/50
- final segment switch height/projected line: 238/261
- final segment first-row comparator/count/runner-up: picture/492/0
- asymmetric band classes: band+: 2, hidden: 405, reset: 2, travel: 510
- first-row observations: ambiguous: 2, black22: 13, other-non-picture: 22, picture: 567, unmeasurable: 315

### Field 2

- field lock: hold: 19, locked: 513, no-lock: 387
- observed S..clip band rows: -1: 406, 2: 14, 3: 499
- final segment band comparator/count/runner-up: 3/499/14
- final segment switch height/projected line: 237/523
- final segment first-row comparator/count/runner-up: picture/356/0
- asymmetric band classes: hidden: 404, reset: 2, travel: 513
- first-row observations: ambiguous: 158, picture: 452, unmeasurable: 309

## SP field-2 continuous minus-one test

Verdict: a continuous field-2 minus-one is rejected. Pulling field 2 down by one inserts the Shuttle-overwritten L285 rather than recovering a source line, and it raises comb energy in every unit with a seven-shift vector. This falsifies the field-sitting-high explanation; the rows do not separately prove whether the remaining band difference is raster half-line geometry or partial-line convention.

- current field-2 top: 286: 604, 287: 4
- L285 present as overwritten blank: 608/608 units
- L285 luma mean range / median: 1.350-1.406 / 1.377
- L285 luma standard-deviation range / median: 0.477-0.491 / 0.485
- comb comparison: measured tops: 607
- E(field2−1) − E(measured): range / median 0.256595-4.697690 / 2.420552
- field-1 explicit caption/VBI confirmation counts: caption 46, VBI 4

### Deciding raw rows and comb vectors

- unit 20: tops L24/L286; switch evidence L261/L522; comb `-3:14.279536,-2:11.783522,-1:7.839751,0:4.720809,1:7.827952,2:11.693971,3:14.362869`; L284 Y=23.947/41.218 Cstd=0.617; L285 Y=1.380/0.485 Cstd=0.621; L286 Y=115.423/28.467 Cstd=18.116; L287 Y=114.502/27.511 Cstd=16.713; L288 Y=117.394/27.782 Cstd=19.263
- unit 87: tops L24/L287; switch evidence L261/L524; comb `-3:7.893877,-2:6.660991,-1:5.264322,0:3.419033,1:4.100786,2:6.063034,3:7.551185`; L284 Y=23.992/41.311 Cstd=0.644; L285 Y=1.364/0.481 Cstd=0.644; L286 Y=5.456/4.131 Cstd=14.793; L287 Y=112.223/30.814 Cstd=13.022; L288 Y=109.487/32.321 Cstd=17.009
- unit 200: tops L24/L286; switch evidence L261/L522; comb `-3:14.008963,-2:11.655437,-1:8.163421,0:4.823828,1:8.170074,2:11.238931,3:13.660611`; L284 Y=24.027/41.325 Cstd=0.655; L285 Y=1.392/0.488 Cstd=0.571; L286 Y=130.117/31.608 Cstd=27.929; L287 Y=127.483/34.068 Cstd=25.741; L288 Y=128.713/34.286 Cstd=21.994
