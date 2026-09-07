# Independent score of engine geometry records

Engine input revision: `860b520`.

This is a raw-raster score, not an engine-log-to-reference diff. Records are joined by the 16-bit device counter. Luma is reported as mean/standard deviation over samples 40-679; correlations use samples 24-696; lag entries give best horizontal lag and best/zero-lag MAD. No coordinate is substituted for an unmeasurable observation.

## Reference extension

Every reference now stores `first_full_other_head_line` separately from `switch_first_line`. The first is measured only at or below the earliest unreliable row, using an internal horizontal-blanking run, a persistent three-third step, or a decisive two-sided whole-row lag. It is -1 when none is exposed.

## Objections

None.

# Engine-record score: SP recording

Acceptance verdict: **not accepted**.

Engine rows joined by device counter: 1216; unmatched engine rows: none.

Engine fields are compared with the same numbered raw raster slot at the same counter.

Owner-review disagreement units: 608; counters: 13500-14107.

Shifted woven bwdif frames written: 608 under `reports/engine_run_R_disagreements/sp`.

| counter | reason(s) | shifted bwdif frame |
|---:|:---|:---|
| 13500 | F1 crop L24/L23; F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13500.webp` |
| 13501 | F1 crop L24/L23; F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13501.webp` |
| 13502 | F1 crop L24/L23; F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13502.webp` |
| 13503 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13503.webp` |
| 13504 | F1 S/switch unmeasurable/L262; F1 signature top L24/L23; F2 H 237/236; F2 c 3/4; engine decisive comb -1 at placed crops (ratio 0.490) | `reports/engine_run_R_disagreements/sp/counter_13504.webp` |
| 13505 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13505.webp` |
| 13506 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13506.webp` |
| 13507 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13507.webp` |
| 13508 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13508.webp` |
| 13509 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13509.webp` |
| 13510 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13510.webp` |
| 13511 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13511.webp` |
| 13512 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13512.webp` |
| 13513 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13513.webp` |
| 13514 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13514.webp` |
| 13515 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13515.webp` |
| 13516 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13516.webp` |
| 13517 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13517.webp` |
| 13518 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13518.webp` |
| 13519 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13519.webp` |
| 13520 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13520.webp` |
| 13521 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13521.webp` |
| 13522 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13522.webp` |
| 13523 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13523.webp` |
| 13524 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13524.webp` |
| 13525 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13525.webp` |
| 13526 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13526.webp` |
| 13527 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13527.webp` |
| 13528 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13528.webp` |
| 13529 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13529.webp` |
| 13530 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13530.webp` |
| 13531 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13531.webp` |
| 13532 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13532.webp` |
| 13533 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13533.webp` |
| 13534 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13534.webp` |
| 13535 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13535.webp` |
| 13536 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13536.webp` |
| 13537 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13537.webp` |
| 13538 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13538.webp` |
| 13539 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13539.webp` |
| 13540 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13540.webp` |
| 13541 | F1 S/switch unmeasurable/L262; F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13541.webp` |
| 13542 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13542.webp` |
| 13543 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13543.webp` |
| 13544 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13544.webp` |
| 13545 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13545.webp` |
| 13546 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13546.webp` |
| 13547 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13547.webp` |
| 13548 | F2 H 237/236; F2 c 3/4; engine decisive comb -1 at placed crops (ratio 0.800) | `reports/engine_run_R_disagreements/sp/counter_13548.webp` |
| 13549 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13549.webp` |
| 13550 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13550.webp` |
| 13551 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13551.webp` |
| 13552 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13552.webp` |
| 13553 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13553.webp` |
| 13554 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13554.webp` |
| 13555 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13555.webp` |
| 13556 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13556.webp` |
| 13557 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13557.webp` |
| 13558 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13558.webp` |
| 13559 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13559.webp` |
| 13560 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13560.webp` |
| 13561 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13561.webp` |
| 13562 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13562.webp` |
| 13563 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13563.webp` |
| 13564 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13564.webp` |
| 13565 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13565.webp` |
| 13566 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13566.webp` |
| 13567 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13567.webp` |
| 13568 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13568.webp` |
| 13569 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13569.webp` |
| 13570 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13570.webp` |
| 13571 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13571.webp` |
| 13572 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13572.webp` |
| 13573 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13573.webp` |
| 13574 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13574.webp` |
| 13575 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13575.webp` |
| 13576 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13576.webp` |
| 13577 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13577.webp` |
| 13578 | F1 crop L24/L23; F2 H 237/236; F2 c 3/4; engine decisive comb +2 at placed crops (ratio 0.630) | `reports/engine_run_R_disagreements/sp/counter_13578.webp` |
| 13579 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13579.webp` |
| 13580 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13580.webp` |
| 13581 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13581.webp` |
| 13582 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13582.webp` |
| 13583 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13583.webp` |
| 13584 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13584.webp` |
| 13585 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13585.webp` |
| 13586 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13586.webp` |
| 13587 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13587.webp` |
| 13588 | F2 H 237/236; F2 c 3/4; F2 crop L286/L287 | `reports/engine_run_R_disagreements/sp/counter_13588.webp` |
| 13589 | F2 H 237/236; F2 c 3/4; F2 crop L286/L287 | `reports/engine_run_R_disagreements/sp/counter_13589.webp` |
| 13590 | F2 H 237/236; F2 c 3/4; F2 crop L286/L287 | `reports/engine_run_R_disagreements/sp/counter_13590.webp` |
| 13591 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13591.webp` |
| 13592 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13592.webp` |
| 13593 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13593.webp` |
| 13594 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13594.webp` |
| 13595 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13595.webp` |
| 13596 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13596.webp` |
| 13597 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13597.webp` |
| 13598 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13598.webp` |
| 13599 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13599.webp` |
| 13600 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13600.webp` |
| 13601 | F1 S/first-full L260/L261; F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13601.webp` |
| 13602 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13602.webp` |
| 13603 | F1 S/first-full L259/L260; F1 crop L22/L23; F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13603.webp` |
| 13604 | F1 crop L22/L23; F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13604.webp` |
| 13605 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13605.webp` |
| 13606 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13606.webp` |
| 13607 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13607.webp` |
| 13608 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13608.webp` |
| 13609 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13609.webp` |
| 13610 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13610.webp` |
| 13611 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13611.webp` |
| 13612 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13612.webp` |
| 13613 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13613.webp` |
| 13614 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13614.webp` |
| 13615 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13615.webp` |
| 13616 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13616.webp` |
| 13617 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13617.webp` |
| 13618 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13618.webp` |
| 13619 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13619.webp` |
| 13620 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13620.webp` |
| 13621 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13621.webp` |
| 13622 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13622.webp` |
| 13623 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13623.webp` |
| 13624 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13624.webp` |
| 13625 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13625.webp` |
| 13626 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13626.webp` |
| 13627 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13627.webp` |
| 13628 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13628.webp` |
| 13629 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13629.webp` |
| 13630 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13630.webp` |
| 13631 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13631.webp` |
| 13632 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13632.webp` |
| 13633 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13633.webp` |
| 13634 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13634.webp` |
| 13635 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13635.webp` |
| 13636 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13636.webp` |
| 13637 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13637.webp` |
| 13638 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13638.webp` |
| 13639 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13639.webp` |
| 13640 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13640.webp` |
| 13641 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13641.webp` |
| 13642 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13642.webp` |
| 13643 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13643.webp` |
| 13644 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13644.webp` |
| 13645 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13645.webp` |
| 13646 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13646.webp` |
| 13647 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13647.webp` |
| 13648 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13648.webp` |
| 13649 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13649.webp` |
| 13650 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13650.webp` |
| 13651 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13651.webp` |
| 13652 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13652.webp` |
| 13653 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13653.webp` |
| 13654 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13654.webp` |
| 13655 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13655.webp` |
| 13656 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13656.webp` |
| 13657 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13657.webp` |
| 13658 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13658.webp` |
| 13659 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13659.webp` |
| 13660 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13660.webp` |
| 13661 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13661.webp` |
| 13662 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13662.webp` |
| 13663 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13663.webp` |
| 13664 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13664.webp` |
| 13665 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13665.webp` |
| 13666 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13666.webp` |
| 13667 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13667.webp` |
| 13668 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13668.webp` |
| 13669 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13669.webp` |
| 13670 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13670.webp` |
| 13671 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13671.webp` |
| 13672 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13672.webp` |
| 13673 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13673.webp` |
| 13674 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13674.webp` |
| 13675 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13675.webp` |
| 13676 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13676.webp` |
| 13677 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13677.webp` |
| 13678 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13678.webp` |
| 13679 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13679.webp` |
| 13680 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13680.webp` |
| 13681 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13681.webp` |
| 13682 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13682.webp` |
| 13683 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13683.webp` |
| 13684 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13684.webp` |
| 13685 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13685.webp` |
| 13686 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13686.webp` |
| 13687 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13687.webp` |
| 13688 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13688.webp` |
| 13689 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13689.webp` |
| 13690 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13690.webp` |
| 13691 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13691.webp` |
| 13692 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13692.webp` |
| 13693 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13693.webp` |
| 13694 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13694.webp` |
| 13695 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13695.webp` |
| 13696 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13696.webp` |
| 13697 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13697.webp` |
| 13698 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13698.webp` |
| 13699 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13699.webp` |
| 13700 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13700.webp` |
| 13701 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13701.webp` |
| 13702 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13702.webp` |
| 13703 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13703.webp` |
| 13704 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13704.webp` |
| 13705 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13705.webp` |
| 13706 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13706.webp` |
| 13707 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13707.webp` |
| 13708 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13708.webp` |
| 13709 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13709.webp` |
| 13710 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13710.webp` |
| 13711 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13711.webp` |
| 13712 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13712.webp` |
| 13713 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13713.webp` |
| 13714 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13714.webp` |
| 13715 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13715.webp` |
| 13716 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13716.webp` |
| 13717 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13717.webp` |
| 13718 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13718.webp` |
| 13719 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13719.webp` |
| 13720 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13720.webp` |
| 13721 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13721.webp` |
| 13722 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13722.webp` |
| 13723 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13723.webp` |
| 13724 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13724.webp` |
| 13725 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13725.webp` |
| 13726 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13726.webp` |
| 13727 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13727.webp` |
| 13728 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13728.webp` |
| 13729 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13729.webp` |
| 13730 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13730.webp` |
| 13731 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13731.webp` |
| 13732 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13732.webp` |
| 13733 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13733.webp` |
| 13734 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13734.webp` |
| 13735 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13735.webp` |
| 13736 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13736.webp` |
| 13737 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13737.webp` |
| 13738 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13738.webp` |
| 13739 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13739.webp` |
| 13740 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13740.webp` |
| 13741 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13741.webp` |
| 13742 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13742.webp` |
| 13743 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13743.webp` |
| 13744 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13744.webp` |
| 13745 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13745.webp` |
| 13746 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13746.webp` |
| 13747 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13747.webp` |
| 13748 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13748.webp` |
| 13749 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13749.webp` |
| 13750 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13750.webp` |
| 13751 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13751.webp` |
| 13752 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13752.webp` |
| 13753 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13753.webp` |
| 13754 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13754.webp` |
| 13755 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13755.webp` |
| 13756 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13756.webp` |
| 13757 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13757.webp` |
| 13758 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13758.webp` |
| 13759 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13759.webp` |
| 13760 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13760.webp` |
| 13761 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13761.webp` |
| 13762 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13762.webp` |
| 13763 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13763.webp` |
| 13764 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13764.webp` |
| 13765 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13765.webp` |
| 13766 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13766.webp` |
| 13767 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13767.webp` |
| 13768 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13768.webp` |
| 13769 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13769.webp` |
| 13770 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13770.webp` |
| 13771 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13771.webp` |
| 13772 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13772.webp` |
| 13773 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13773.webp` |
| 13774 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13774.webp` |
| 13775 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13775.webp` |
| 13776 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13776.webp` |
| 13777 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13777.webp` |
| 13778 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13778.webp` |
| 13779 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13779.webp` |
| 13780 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13780.webp` |
| 13781 | F2 H 237/236; F2 S/first-full L521/L522; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13781.webp` |
| 13782 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13782.webp` |
| 13783 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13783.webp` |
| 13784 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13784.webp` |
| 13785 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13785.webp` |
| 13786 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13786.webp` |
| 13787 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13787.webp` |
| 13788 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13788.webp` |
| 13789 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13789.webp` |
| 13790 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13790.webp` |
| 13791 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13791.webp` |
| 13792 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13792.webp` |
| 13793 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13793.webp` |
| 13794 | F2 H 237/236; F2 c 3/4; engine decisive comb +1 at placed crops (ratio 0.550) | `reports/engine_run_R_disagreements/sp/counter_13794.webp` |
| 13795 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13795.webp` |
| 13796 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13796.webp` |
| 13797 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13797.webp` |
| 13798 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13798.webp` |
| 13799 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13799.webp` |
| 13800 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13800.webp` |
| 13801 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13801.webp` |
| 13802 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13802.webp` |
| 13803 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13803.webp` |
| 13804 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13804.webp` |
| 13805 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13805.webp` |
| 13806 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13806.webp` |
| 13807 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13807.webp` |
| 13808 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13808.webp` |
| 13809 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13809.webp` |
| 13810 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13810.webp` |
| 13811 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13811.webp` |
| 13812 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13812.webp` |
| 13813 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13813.webp` |
| 13814 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13814.webp` |
| 13815 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13815.webp` |
| 13816 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13816.webp` |
| 13817 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13817.webp` |
| 13818 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13818.webp` |
| 13819 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13819.webp` |
| 13820 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13820.webp` |
| 13821 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13821.webp` |
| 13822 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13822.webp` |
| 13823 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13823.webp` |
| 13824 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13824.webp` |
| 13825 | F2 H 237/236; F2 S/first-full L523/L522; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13825.webp` |
| 13826 | F2 H 237/236; F2 c 3/4; engine decisive comb -1 at placed crops (ratio 0.790) | `reports/engine_run_R_disagreements/sp/counter_13826.webp` |
| 13827 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13827.webp` |
| 13828 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13828.webp` |
| 13829 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13829.webp` |
| 13830 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13830.webp` |
| 13831 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13831.webp` |
| 13832 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13832.webp` |
| 13833 | F1 S/first-full L261/L260; F1 S/switch L261/L259; F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13833.webp` |
| 13834 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13834.webp` |
| 13835 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13835.webp` |
| 13836 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13836.webp` |
| 13837 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13837.webp` |
| 13838 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13838.webp` |
| 13839 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13839.webp` |
| 13840 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13840.webp` |
| 13841 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13841.webp` |
| 13842 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13842.webp` |
| 13843 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13843.webp` |
| 13844 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13844.webp` |
| 13845 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13845.webp` |
| 13846 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13846.webp` |
| 13847 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13847.webp` |
| 13848 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13848.webp` |
| 13849 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13849.webp` |
| 13850 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13850.webp` |
| 13851 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13851.webp` |
| 13852 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13852.webp` |
| 13853 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13853.webp` |
| 13854 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13854.webp` |
| 13855 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13855.webp` |
| 13856 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13856.webp` |
| 13857 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13857.webp` |
| 13858 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13858.webp` |
| 13859 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13859.webp` |
| 13860 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13860.webp` |
| 13861 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13861.webp` |
| 13862 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13862.webp` |
| 13863 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13863.webp` |
| 13864 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13864.webp` |
| 13865 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13865.webp` |
| 13866 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13866.webp` |
| 13867 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13867.webp` |
| 13868 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13868.webp` |
| 13869 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13869.webp` |
| 13870 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13870.webp` |
| 13871 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13871.webp` |
| 13872 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13872.webp` |
| 13873 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13873.webp` |
| 13874 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13874.webp` |
| 13875 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13875.webp` |
| 13876 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13876.webp` |
| 13877 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13877.webp` |
| 13878 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13878.webp` |
| 13879 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13879.webp` |
| 13880 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13880.webp` |
| 13881 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13881.webp` |
| 13882 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13882.webp` |
| 13883 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13883.webp` |
| 13884 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13884.webp` |
| 13885 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13885.webp` |
| 13886 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13886.webp` |
| 13887 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13887.webp` |
| 13888 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13888.webp` |
| 13889 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13889.webp` |
| 13890 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13890.webp` |
| 13891 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13891.webp` |
| 13892 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13892.webp` |
| 13893 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13893.webp` |
| 13894 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13894.webp` |
| 13895 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13895.webp` |
| 13896 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13896.webp` |
| 13897 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13897.webp` |
| 13898 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13898.webp` |
| 13899 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13899.webp` |
| 13900 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13900.webp` |
| 13901 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13901.webp` |
| 13902 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13902.webp` |
| 13903 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13903.webp` |
| 13904 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13904.webp` |
| 13905 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13905.webp` |
| 13906 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13906.webp` |
| 13907 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13907.webp` |
| 13908 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13908.webp` |
| 13909 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13909.webp` |
| 13910 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13910.webp` |
| 13911 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13911.webp` |
| 13912 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13912.webp` |
| 13913 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13913.webp` |
| 13914 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13914.webp` |
| 13915 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13915.webp` |
| 13916 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13916.webp` |
| 13917 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13917.webp` |
| 13918 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13918.webp` |
| 13919 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13919.webp` |
| 13920 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13920.webp` |
| 13921 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13921.webp` |
| 13922 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13922.webp` |
| 13923 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13923.webp` |
| 13924 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13924.webp` |
| 13925 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13925.webp` |
| 13926 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13926.webp` |
| 13927 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13927.webp` |
| 13928 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13928.webp` |
| 13929 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13929.webp` |
| 13930 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13930.webp` |
| 13931 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13931.webp` |
| 13932 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13932.webp` |
| 13933 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13933.webp` |
| 13934 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13934.webp` |
| 13935 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13935.webp` |
| 13936 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13936.webp` |
| 13937 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13937.webp` |
| 13938 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13938.webp` |
| 13939 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13939.webp` |
| 13940 | F2 H 237/236; F2 c 3/4; F2 crop L286/L287 | `reports/engine_run_R_disagreements/sp/counter_13940.webp` |
| 13941 | F2 H 237/236; F2 c 3/4; F2 crop L286/L287 | `reports/engine_run_R_disagreements/sp/counter_13941.webp` |
| 13942 | F2 H 237/236; F2 c 3/4; F2 crop L286/L287 | `reports/engine_run_R_disagreements/sp/counter_13942.webp` |
| 13943 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13943.webp` |
| 13944 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13944.webp` |
| 13945 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13945.webp` |
| 13946 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13946.webp` |
| 13947 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13947.webp` |
| 13948 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13948.webp` |
| 13949 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13949.webp` |
| 13950 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13950.webp` |
| 13951 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13951.webp` |
| 13952 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13952.webp` |
| 13953 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13953.webp` |
| 13954 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13954.webp` |
| 13955 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13955.webp` |
| 13956 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13956.webp` |
| 13957 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13957.webp` |
| 13958 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13958.webp` |
| 13959 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13959.webp` |
| 13960 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13960.webp` |
| 13961 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13961.webp` |
| 13962 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13962.webp` |
| 13963 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13963.webp` |
| 13964 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13964.webp` |
| 13965 | F1 signature top L24/L23; F2 H 237/236; F2 c 3/4; engine decisive comb -1 at placed crops (ratio 0.500) | `reports/engine_run_R_disagreements/sp/counter_13965.webp` |
| 13966 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13966.webp` |
| 13967 | F2 H 237/236; F2 c 3/4; engine decisive comb -1 at placed crops (ratio 0.720) | `reports/engine_run_R_disagreements/sp/counter_13967.webp` |
| 13968 | F2 H 237/236; F2 c 3/4; F2 crop L286/L287 | `reports/engine_run_R_disagreements/sp/counter_13968.webp` |
| 13969 | F2 H 237/236; F2 c 3/4; F2 crop L286/L287 | `reports/engine_run_R_disagreements/sp/counter_13969.webp` |
| 13970 | F2 H 237/236; F2 c 3/4; F2 crop L286/L287 | `reports/engine_run_R_disagreements/sp/counter_13970.webp` |
| 13971 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13971.webp` |
| 13972 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13972.webp` |
| 13973 | F1 S/first-full L259/L260; F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13973.webp` |
| 13974 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13974.webp` |
| 13975 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13975.webp` |
| 13976 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13976.webp` |
| 13977 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13977.webp` |
| 13978 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13978.webp` |
| 13979 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13979.webp` |
| 13980 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13980.webp` |
| 13981 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13981.webp` |
| 13982 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13982.webp` |
| 13983 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13983.webp` |
| 13984 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13984.webp` |
| 13985 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13985.webp` |
| 13986 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13986.webp` |
| 13987 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13987.webp` |
| 13988 | F1 crop L25/L24; F2 H 237/236; F2 c 3/4; engine decisive comb +1 at placed crops (ratio 0.740) | `reports/engine_run_R_disagreements/sp/counter_13988.webp` |
| 13989 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13989.webp` |
| 13990 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13990.webp` |
| 13991 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13991.webp` |
| 13992 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13992.webp` |
| 13993 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13993.webp` |
| 13994 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13994.webp` |
| 13995 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13995.webp` |
| 13996 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13996.webp` |
| 13997 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13997.webp` |
| 13998 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13998.webp` |
| 13999 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_13999.webp` |
| 14000 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14000.webp` |
| 14001 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14001.webp` |
| 14002 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14002.webp` |
| 14003 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14003.webp` |
| 14004 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14004.webp` |
| 14005 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14005.webp` |
| 14006 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14006.webp` |
| 14007 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14007.webp` |
| 14008 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14008.webp` |
| 14009 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14009.webp` |
| 14010 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14010.webp` |
| 14011 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14011.webp` |
| 14012 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14012.webp` |
| 14013 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14013.webp` |
| 14014 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14014.webp` |
| 14015 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14015.webp` |
| 14016 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14016.webp` |
| 14017 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14017.webp` |
| 14018 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14018.webp` |
| 14019 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14019.webp` |
| 14020 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14020.webp` |
| 14021 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14021.webp` |
| 14022 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14022.webp` |
| 14023 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14023.webp` |
| 14024 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14024.webp` |
| 14025 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14025.webp` |
| 14026 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14026.webp` |
| 14027 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14027.webp` |
| 14028 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14028.webp` |
| 14029 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14029.webp` |
| 14030 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14030.webp` |
| 14031 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14031.webp` |
| 14032 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14032.webp` |
| 14033 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14033.webp` |
| 14034 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14034.webp` |
| 14035 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14035.webp` |
| 14036 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14036.webp` |
| 14037 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14037.webp` |
| 14038 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14038.webp` |
| 14039 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14039.webp` |
| 14040 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14040.webp` |
| 14041 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14041.webp` |
| 14042 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14042.webp` |
| 14043 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14043.webp` |
| 14044 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14044.webp` |
| 14045 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14045.webp` |
| 14046 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14046.webp` |
| 14047 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14047.webp` |
| 14048 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14048.webp` |
| 14049 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14049.webp` |
| 14050 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14050.webp` |
| 14051 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14051.webp` |
| 14052 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14052.webp` |
| 14053 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14053.webp` |
| 14054 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14054.webp` |
| 14055 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14055.webp` |
| 14056 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14056.webp` |
| 14057 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14057.webp` |
| 14058 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14058.webp` |
| 14059 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14059.webp` |
| 14060 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14060.webp` |
| 14061 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14061.webp` |
| 14062 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14062.webp` |
| 14063 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14063.webp` |
| 14064 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14064.webp` |
| 14065 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14065.webp` |
| 14066 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14066.webp` |
| 14067 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14067.webp` |
| 14068 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14068.webp` |
| 14069 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14069.webp` |
| 14070 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14070.webp` |
| 14071 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14071.webp` |
| 14072 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14072.webp` |
| 14073 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14073.webp` |
| 14074 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14074.webp` |
| 14075 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14075.webp` |
| 14076 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14076.webp` |
| 14077 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14077.webp` |
| 14078 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14078.webp` |
| 14079 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14079.webp` |
| 14080 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14080.webp` |
| 14081 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14081.webp` |
| 14082 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14082.webp` |
| 14083 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14083.webp` |
| 14084 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14084.webp` |
| 14085 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14085.webp` |
| 14086 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14086.webp` |
| 14087 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14087.webp` |
| 14088 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14088.webp` |
| 14089 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14089.webp` |
| 14090 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14090.webp` |
| 14091 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14091.webp` |
| 14092 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14092.webp` |
| 14093 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14093.webp` |
| 14094 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14094.webp` |
| 14095 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14095.webp` |
| 14096 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14096.webp` |
| 14097 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14097.webp` |
| 14098 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14098.webp` |
| 14099 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14099.webp` |
| 14100 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14100.webp` |
| 14101 | F1 crop L24/L25; F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14101.webp` |
| 14102 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14102.webp` |
| 14103 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14103.webp` |
| 14104 | F2 H 237/236; F2 S/first-full L522/L523; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14104.webp` |
| 14105 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14105.webp` |
| 14106 | F2 H 237/236; F2 S/switch L520/L522; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14106.webp` |
| 14107 | F2 H 237/236; F2 c 3/4 | `reports/engine_run_R_disagreements/sp/counter_14107.webp` |

## Picture top

### Engine field 1

Agreement histogram (engine minus reference): +0: 606, +1: 2

| engine counter | raw counter/field | engine | reference | verdict | raw top rows |
|---:|:---:|:---|:---|:---|:---|
| 13504 | 13504/F1 | L24 | L23 | reference (VBI/black-line exclusion and picture-row continuity) | waveforms=[21]; L23 21.49/28.00 r_next=0.170 MAD_above=20.12 lag=29(18.20/20.12); L24 3.61/3.52 r_next=-0.075 MAD_above=18.64 lag=-28(16.67/18.64); L25 117.85/28.55 r_next=0.895 MAD_above=114.24 lag=-32(113.25/114.24) |
| 13965 | 13965/F1 | L24 | L23 | reference (VBI/black-line exclusion and picture-row continuity) | waveforms=[21]; L23 26.16/30.81 r_next=0.413 MAD_above=24.80 lag=32(22.12/24.80); L24 5.58/3.55 r_next=-0.255 MAD_above=21.18 lag=-32(18.44/21.18); L25 133.74/41.55 r_next=0.550 MAD_above=128.16 lag=-32(126.89/128.16) |

### Engine field 2

Agreement histogram (engine minus reference): +0: 608

No differences.

## Head-switch row

`S` is scored first against the reference's earliest switch-band row. A difference of one row is the declared partial-predecessor semantic gap. The separate exact check uses the reference's independently measured first-full-other-head row: an internal blanking signature, a persistent three-third step, or a two-sided whole-row time-base step. It remains unmeasurable when none is exposed.

### Engine field 1

S minus reference switch histogram: -1: 4, +0: 504, +1: 97, +2: 1, engine-unmeasurable: 2

Differences beyond the one-row semantic gap:

| engine counter | raw counter/field | S | reference switch | raw tail rows |
|---:|:---:|:---|:---|:---|
| 13833 | 13833/F1 | L261 | L259 | L258 86.37/57.25 r_next=0.986 MAD_above=8.29 lag=0(8.29/8.29); L259 89.26/56.81 r_next=0.988 MAD_above=7.46 lag=0(7.46/7.46); L260 89.24/58.87 r_next=-0.057 MAD_above=7.15 lag=0(7.15/7.15); L261 24.79/29.39 r_next=-0.285 MAD_above=69.18 lag=32(66.57/69.18); L262 10.33/1.03 r_next=0.073 MAD_above=15.41 lag=-32(12.10/15.41); direct-full=L260 (L260 internal blank x=173-236 Y=3.938; above=7.078 following=116.500; gate=4.000) |

First-full-other-head histogram (engine S minus reference): -1: 3, +0: 8, +1: 1, both-unmeasurable: 2, reference-unmeasurable: 594

- +1: counters 13833.  Witnesses: counter 13833: engine L261, direct L260; L260 internal blank x=173-236 Y=3.938; above=7.078 following=116.500; gate=4.000

- -1: counters 13601, 13603, 13973.  Witnesses: counter 13601: engine L260, direct L261; L261 persistent three-third step; thirds=12.876,3.898,3.290; correlation above/next=-0.342/0.706; middle coherence=0.879 / counter 13603: engine L259, direct L260; L260 persistent three-third step; thirds=12.615,3.704,3.113; correlation above/next=-0.369/0.709; middle coherence=0.869 / counter 13973: engine L259, direct L260; L260 persistent three-third step; thirds=8.158,5.267,5.091; correlation above/next=-0.402/0.701; middle coherence=0.914

- reference-unmeasurable: counters 13500-13503, 13505-13540, 13542-13600, 13602, 13605-13763, 13765, 13767, 13769, 13772-13776, 13778-13826, 13828-13832, 13834-13972, 13974-14107.  Witnesses: counter 13500: engine L261, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.921; no internal horizontal blanking run; gate=4.000 / counter 13501: engine L261, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.913; no internal horizontal blanking run; gate=4.000 / counter 13502: engine L261, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.924; no internal horizontal blanking run; gate=4.000

Every numeric first-full disagreement:

| engine counter | raw counter/field | engine S | reference first-full | raw tail rows |
|---:|:---:|:---|:---|:---|
| 13601 | 13601/F1 | L260 | L261 | L259 91.95/36.48 r_next=0.065 MAD_above=9.15 lag=0(9.15/9.15); L260 68.61/38.99 r_next=-0.199 MAD_above=31.55 lag=-3(29.29/31.55); L261 10.72/1.00 r_next=0.402 MAD_above=58.09 lag=-32(55.15/58.09); L262 10.99/1.01 r_next=0.047 MAD_above=0.84 lag=12(0.76/0.84); direct-full=L261 (L261 persistent three-third step; thirds=12.876,3.898,3.290; correlation above/next=-0.342/0.706; middle coherence=0.879) |
| 13603 | 13603/F1 | L259 | L260 | L258 91.34/36.72 r_next=-0.015 MAD_above=8.93 lag=0(8.93/8.93); L259 66.94/39.44 r_next=-0.198 MAD_above=36.78 lag=-9(29.60/36.78); L260 10.92/1.09 r_next=0.431 MAD_above=56.42 lag=-32(53.42/56.42); L261 11.18/0.97 r_next=0.242 MAD_above=0.84 lag=11(0.78/0.84); direct-full=L260 (L260 persistent three-third step; thirds=12.615,3.704,3.113; correlation above/next=-0.369/0.709; middle coherence=0.869) |
| 13833 | 13833/F1 | L261 | L260 | L259 89.26/56.81 r_next=0.988 MAD_above=7.46 lag=0(7.46/7.46); L260 89.24/58.87 r_next=-0.057 MAD_above=7.15 lag=0(7.15/7.15); L261 24.79/29.39 r_next=-0.285 MAD_above=69.18 lag=32(66.57/69.18); L262 10.33/1.03 r_next=0.073 MAD_above=15.41 lag=-32(12.10/15.41); direct-full=L260 (L260 internal blank x=173-236 Y=3.938; above=7.078 following=116.500; gate=4.000) |
| 13973 | 13973/F1 | L259 | L260 | L258 96.28/53.94 r_next=0.053 MAD_above=11.25 lag=-1(10.73/11.25); L259 66.76/47.70 r_next=-0.279 MAD_above=45.71 lag=-13(36.32/45.71); L260 9.79/0.99 r_next=0.395 MAD_above=57.44 lag=-32(56.50/57.44); L261 10.16/0.90 r_next=0.158 MAD_above=0.80 lag=-17(0.77/0.80); direct-full=L260 (L260 persistent three-third step; thirds=8.158,5.267,5.091; correlation above/next=-0.402/0.701; middle coherence=0.914) |

### Engine field 2

S minus reference switch histogram: -2: 1, -1: 28, +0: 372, +1: 207

Differences beyond the one-row semantic gap:

| engine counter | raw counter/field | S | reference switch | raw tail rows |
|---:|:---:|:---|:---|:---|
| 14106 | 14106/F2 | L520 | L522 | L519 85.67/36.48 r_next=0.874 MAD_above=13.10 lag=1(12.31/13.10); L520 84.93/36.63 r_next=0.864 MAD_above=12.39 lag=1(11.21/12.39); L521 84.75/35.95 r_next=0.781 MAD_above=11.93 lag=1(11.66/11.93); L522 79.39/39.04 r_next=-0.332 MAD_above=13.99 lag=-2(11.54/13.99); L523 10.28/1.05 r_next=0.413 MAD_above=69.28 lag=0(69.28/69.28); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.807; no internal horizontal blanking run; gate=4.000) |

First-full-other-head histogram (engine S minus reference): -1: 59, +0: 95, +1: 1, reference-unmeasurable: 453

- +1: counters 13825.  Witnesses: counter 13825: engine L523, direct L522; L522 internal blank x=173-236 Y=2.375; above=8.453 following=61.500; gate=4.000

- -1: counters 13541, 13543, 13549, 13559, 13561-13562, 13568, 13572, 13614, 13634, 13781, 13803, 13805, 13812-13815, 13822-13823, 13828, 13835, 13855-13856, 13859-13860, 13865, 13869, 13874-13875, 13885, 13917, 13929, 13933, 14010, 14013, 14016, 14020-14021, 14029-14030, 14034-14036, 14041-14042, 14044, 14049-14050, 14053-14055, 14058-14059, 14061, 14069, 14078-14079, 14095, 14104.  Witnesses: counter 13541: engine L522, direct L523; L523 persistent three-third step; thirds=6.929,5.724,4.966; correlation above/next=0.092/0.757; middle coherence=0.922 / counter 13543: engine L522, direct L523; L523 persistent three-third step; thirds=6.719,5.349,4.734; correlation above/next=-0.094/0.756; middle coherence=0.917 / counter 13549: engine L522, direct L523; L523 persistent three-third step; thirds=11.346,3.580,8.762; correlation above/next=-0.164/0.728; middle coherence=0.880

- reference-unmeasurable: counters 13500-13502, 13504-13506, 13508-13516, 13518, 13524, 13527-13528, 13531-13532, 13540, 13550, 13557-13558, 13560, 13563-13567, 13569-13570, 13573, 13575-13578, 13580, 13582-13607, 13610-13613, 13615-13621, 13623-13626, 13628, 13631-13632, 13635, 13637-13638, 13640-13645, 13648-13650, 13652-13655, 13661-13662, 13667-13669, 13671-13685, 13687-13749, 13751-13754, 13756-13780, 13782-13794, 13797, 13799-13802, 13804, 13807, 13817-13820, 13830-13834, 13836-13839, 13841-13846, 13849, 13852-13854, 13858, 13862-13864, 13866, 13868, 13870-13873, 13876-13881, 13883-13884, 13886-13913, 13915-13916, 13918-13928, 13931, 13934-14009, 14011-14012, 14014-14015, 14017-14019, 14022-14028, 14031, 14033, 14037-14040, 14043, 14045-14047, 14051-14052, 14063-14067, 14070-14071, 14073-14074, 14076-14077, 14080-14094, 14096-14103, 14105-14107.  Witnesses: counter 13500: engine L523, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.915; no internal horizontal blanking run; gate=4.000 / counter 13501: engine L523, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.919; no internal horizontal blanking run; gate=4.000 / counter 13502: engine L523, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.915; no internal horizontal blanking run; gate=4.000

Every numeric first-full disagreement:

| engine counter | raw counter/field | engine S | reference first-full | raw tail rows |
|---:|:---:|:---|:---|:---|
| 13541 | 13541/F2 | L522 | L523 | L521 93.18/38.15 r_next=0.392 MAD_above=13.73 lag=1(13.36/13.73); L522 76.73/41.89 r_next=0.122 MAD_above=27.81 lag=2(25.62/27.81); L523 10.11/1.00 r_next=0.453 MAD_above=66.72 lag=-32(62.94/66.72); L524 10.49/1.07 r_next=0.118 MAD_above=0.86 lag=1(0.82/0.86); direct-full=L523 (L523 persistent three-third step; thirds=6.929,5.724,4.966; correlation above/next=0.092/0.757; middle coherence=0.922) |
| 13543 | 13543/F2 | L522 | L523 | L521 93.96/39.16 r_next=0.439 MAD_above=13.05 lag=0(13.05/13.05); L522 75.20/41.88 r_next=-0.021 MAD_above=28.08 lag=-2(25.59/28.08); L523 10.01/1.10 r_next=0.504 MAD_above=65.40 lag=-32(61.37/65.40); L524 10.31/1.09 r_next=0.059 MAD_above=0.85 lag=-14(0.83/0.85); direct-full=L523 (L523 persistent three-third step; thirds=6.719,5.349,4.734; correlation above/next=-0.094/0.756; middle coherence=0.917) |
| 13549 | 13549/F2 | L522 | L523 | L521 83.75/35.83 r_next=0.887 MAD_above=9.39 lag=0(9.39/9.39); L522 82.25/35.23 r_next=-0.072 MAD_above=11.78 lag=-3(9.20/11.78); L523 10.09/1.05 r_next=0.462 MAD_above=72.29 lag=32(69.77/72.29); L524 10.31/0.99 r_next=0.143 MAD_above=0.79 lag=-12(0.75/0.79); direct-full=L523 (L523 persistent three-third step; thirds=11.346,3.580,8.762; correlation above/next=-0.164/0.728; middle coherence=0.880) |
| 13559 | 13559/F2 | L522 | L523 | L521 81.59/36.88 r_next=0.916 MAD_above=9.36 lag=0(9.36/9.36); L522 77.47/37.81 r_next=-0.172 MAD_above=11.26 lag=-3(9.37/11.26); L523 10.86/0.98 r_next=0.428 MAD_above=67.07 lag=32(64.61/67.07); L524 11.06/0.88 r_next=0.077 MAD_above=0.72 lag=13(0.69/0.72); direct-full=L523 (L523 persistent three-third step; thirds=11.428,3.096,9.060; correlation above/next=-0.294/0.729; middle coherence=0.888) |
| 13561 | 13561/F2 | L522 | L523 | L521 75.64/37.55 r_next=0.902 MAD_above=10.09 lag=1(9.87/10.09); L522 75.54/37.67 r_next=-0.045 MAD_above=11.39 lag=-3(8.24/11.39); L523 10.38/1.12 r_next=0.433 MAD_above=65.84 lag=32(63.23/65.84); L524 10.93/0.93 r_next=0.050 MAD_above=0.92 lag=9(0.86/0.92); direct-full=L523 (L523 persistent three-third step; thirds=11.209,2.781,9.478; correlation above/next=-0.116/0.754; middle coherence=0.876) |
| 13562 | 13562/F2 | L522 | L523 | L521 79.58/37.85 r_next=0.919 MAD_above=9.35 lag=0(9.35/9.35); L522 79.10/36.60 r_next=-0.026 MAD_above=10.62 lag=-2(9.53/10.62); L523 10.40/1.02 r_next=0.509 MAD_above=69.20 lag=32(66.80/69.20); L524 10.85/1.01 r_next=0.141 MAD_above=0.82 lag=-2(0.81/0.82); direct-full=L523 (L523 persistent three-third step; thirds=11.395,3.013,9.172; correlation above/next=-0.119/0.787; middle coherence=0.875) |
| 13568 | 13568/F2 | L522 | L523 | L521 82.97/38.88 r_next=0.777 MAD_above=8.93 lag=1(8.74/8.93); L522 83.76/36.62 r_next=-0.176 MAD_above=10.37 lag=-2(8.82/10.37); L523 11.09/0.94 r_next=0.401 MAD_above=73.01 lag=32(70.68/73.01); L524 10.99/0.87 r_next=-0.023 MAD_above=0.71 lag=16(0.67/0.71); direct-full=L523 (L523 persistent three-third step; thirds=11.842,3.696,9.391; correlation above/next=-0.281/0.741; middle coherence=0.879) |
| 13572 | 13572/F2 | L522 | L523 | L521 83.68/36.75 r_next=0.812 MAD_above=9.21 lag=0(9.21/9.21); L522 82.85/36.55 r_next=-0.177 MAD_above=16.47 lag=-7(9.86/16.47); L523 11.24/1.06 r_next=0.458 MAD_above=71.80 lag=32(69.38/71.80); L524 11.24/0.96 r_next=-0.036 MAD_above=0.80 lag=-1(0.75/0.80); direct-full=L523 (L523 persistent three-third step; thirds=11.285,3.393,9.434; correlation above/next=-0.284/0.770; middle coherence=0.878) |
| 13614 | 13614/F2 | L522 | L523 | L521 96.14/37.66 r_next=0.377 MAD_above=10.07 lag=0(10.07/10.07); L522 85.17/40.32 r_next=-0.141 MAD_above=21.77 lag=-5(16.60/21.77); L523 10.21/0.88 r_next=0.425 MAD_above=75.08 lag=-32(72.97/75.08); L524 10.82/0.93 r_next=0.201 MAD_above=0.87 lag=-17(0.81/0.87); direct-full=L523 (L523 persistent three-third step; thirds=11.917,4.585,8.088; correlation above/next=-0.256/0.732; middle coherence=0.874) |
| 13634 | 13634/F2 | L522 | L523 | L521 113.70/45.15 r_next=0.340 MAD_above=10.23 lag=0(10.23/10.23); L522 88.71/48.72 r_next=0.041 MAD_above=30.39 lag=-1(30.10/30.39); L523 10.96/1.05 r_next=0.460 MAD_above=78.10 lag=-10(77.99/78.10); L524 11.14/1.04 r_next=0.039 MAD_above=0.80 lag=-13(0.77/0.80); direct-full=L523 (L523 persistent three-third step; thirds=10.106,6.288,10.525; correlation above/next=0.074/0.770; middle coherence=0.973) |
| 13781 | 13781/F2 | L521 | L522 | L520 103.42/46.55 r_next=0.821 MAD_above=15.72 lag=0(15.72/15.72); L521 107.21/45.19 r_next=0.588 MAD_above=17.50 lag=0(17.50/17.50); L522 91.10/54.64 r_next=-0.064 MAD_above=37.73 lag=-16(22.03/37.73); L523 10.27/1.00 r_next=0.348 MAD_above=80.95 lag=-32(80.01/80.95); direct-full=L522 (L522 two-sided whole-row step lag/MAD=-17/18.159/33.870,-16/23.469/32.207; middle coherence=0.918) |
| 13803 | 13803/F2 | L522 | L523 | L521 97.80/55.00 r_next=0.668 MAD_above=8.12 lag=0(8.12/8.12); L522 84.91/53.82 r_next=0.078 MAD_above=20.70 lag=2(18.94/20.70); L523 10.15/1.08 r_next=0.484 MAD_above=75.37 lag=-17(74.67/75.37); L524 10.38/1.18 r_next=0.165 MAD_above=0.90 lag=10(0.81/0.90); direct-full=L523 (L523 persistent three-third step; thirds=6.443,6.098,11.950; correlation above/next=0.103/0.744; middle coherence=0.936) |
| 13805 | 13805/F2 | L522 | L523 | L521 97.31/55.42 r_next=0.579 MAD_above=7.66 lag=0(7.66/7.66); L522 80.67/52.25 r_next=-0.166 MAD_above=23.06 lag=2(21.93/23.06); L523 9.86/1.20 r_next=0.530 MAD_above=71.49 lag=-16(70.80/71.49); L524 9.83/1.20 r_next=0.072 MAD_above=0.89 lag=-13(0.86/0.89); direct-full=L523 (L523 persistent three-third step; thirds=6.299,6.125,10.838; correlation above/next=-0.193/0.737; middle coherence=0.934) |
| 13812 | 13812/F2 | L522 | L523 | L521 106.11/53.48 r_next=0.597 MAD_above=8.92 lag=1(8.71/8.92); L522 88.70/52.68 r_next=0.123 MAD_above=23.11 lag=1(22.38/23.11); L523 9.93/1.19 r_next=0.489 MAD_above=79.33 lag=-16(78.65/79.33); L524 10.01/1.06 r_next=0.088 MAD_above=0.86 lag=13(0.78/0.86); direct-full=L523 (L523 persistent three-third step; thirds=6.328,7.928,9.003; correlation above/next=0.183/0.758; middle coherence=0.927) |
| 13813 | 13813/F2 | L522 | L523 | L521 104.61/53.17 r_next=0.433 MAD_above=7.62 lag=0(7.62/7.62); L522 84.41/52.81 r_next=0.024 MAD_above=31.23 lag=-4(25.59/31.23); L523 9.82/1.08 r_next=0.526 MAD_above=75.01 lag=-9(74.68/75.01); L524 9.92/1.21 r_next=-0.049 MAD_above=0.83 lag=11(0.79/0.83); direct-full=L523 (L523 persistent three-third step; thirds=6.255,7.924,8.235; correlation above/next=0.042/0.749; middle coherence=0.926) |
| 13814 | 13814/F2 | L522 | L523 | L521 95.19/55.51 r_next=0.393 MAD_above=7.83 lag=1(7.46/7.83); L522 75.02/53.81 r_next=-0.059 MAD_above=35.51 lag=-12(23.57/35.51); L523 9.48/1.17 r_next=0.533 MAD_above=66.54 lag=-32(66.07/66.54); L524 9.53/1.16 r_next=0.045 MAD_above=0.87 lag=11(0.80/0.87); direct-full=L523 (L523 persistent three-third step; thirds=5.199,6.468,8.072; correlation above/next=-0.061/0.748; middle coherence=0.931) |
| 13815 | 13815/F2 | L522 | L523 | L521 95.23/55.87 r_next=0.570 MAD_above=7.33 lag=1(7.27/7.33); L522 78.60/54.08 r_next=-0.029 MAD_above=25.73 lag=-4(22.23/25.73); L523 9.72/1.15 r_next=0.572 MAD_above=69.51 lag=-10(69.08/69.51); L524 9.71/1.09 r_next=-0.065 MAD_above=0.77 lag=6(0.72/0.77); direct-full=L523 (L523 persistent three-third step; thirds=5.700,6.282,9.214; correlation above/next=-0.035/0.802; middle coherence=0.932) |
| 13822 | 13822/F2 | L522 | L523 | L521 93.76/54.69 r_next=0.486 MAD_above=7.53 lag=0(7.53/7.53); L522 71.73/51.40 r_next=-0.119 MAD_above=28.15 lag=-3(26.00/28.15); L523 9.73/1.08 r_next=0.546 MAD_above=63.03 lag=-32(62.23/63.03); L524 9.88/1.14 r_next=0.017 MAD_above=0.79 lag=3(0.76/0.79); direct-full=L523 (L523 persistent three-third step; thirds=5.630,5.154,7.736; correlation above/next=-0.172/0.814; middle coherence=0.921) |
| 13823 | 13823/F2 | L522 | L523 | L521 92.68/56.63 r_next=0.400 MAD_above=7.91 lag=0(7.91/7.91); L522 70.31/52.64 r_next=-0.122 MAD_above=35.18 lag=-10(25.11/35.18); L523 9.77/1.10 r_next=0.566 MAD_above=62.11 lag=-32(61.70/62.11); L524 9.70/1.12 r_next=0.042 MAD_above=0.75 lag=-7(0.74/0.75); direct-full=L523 (L523 persistent three-third step; thirds=5.165,5.268,7.651; correlation above/next=-0.160/0.808; middle coherence=0.920) |
| 13825 | 13825/F2 | L523 | L522 | L521 90.42/55.76 r_next=0.567 MAD_above=7.38 lag=0(7.38/7.38); L522 68.29/51.67 r_next=-0.103 MAD_above=25.02 lag=0(25.02/25.02); L523 9.93/1.09 r_next=0.466 MAD_above=60.53 lag=-32(59.60/60.53); L524 10.07/1.05 r_next=0.038 MAD_above=0.85 lag=-14(0.78/0.85); direct-full=L522 (L522 internal blank x=173-236 Y=2.375; above=8.453 following=61.500; gate=4.000) |
| 13828 | 13828/F2 | L522 | L523 | L521 86.45/57.10 r_next=0.642 MAD_above=8.17 lag=0(8.17/8.17); L522 75.13/55.16 r_next=-0.044 MAD_above=22.56 lag=-4(17.43/22.56); L523 10.03/1.01 r_next=0.407 MAD_above=67.41 lag=-32(67.01/67.41); L524 10.14/0.92 r_next=0.032 MAD_above=0.78 lag=-6(0.74/0.78); direct-full=L523 (L523 persistent three-third step; thirds=5.056,5.289,9.494; correlation above/next=-0.069/0.709; middle coherence=0.919) |
| 13835 | 13835/F2 | L522 | L523 | L521 92.76/58.00 r_next=0.563 MAD_above=7.21 lag=0(7.21/7.21); L522 76.42/54.64 r_next=-0.007 MAD_above=24.90 lag=2(24.05/24.90); L523 10.47/0.87 r_next=0.386 MAD_above=67.76 lag=-15(66.82/67.76); L524 10.67/0.90 r_next=0.076 MAD_above=0.74 lag=6(0.71/0.74); direct-full=L523 (L523 persistent three-third step; thirds=5.955,5.217,9.051; correlation above/next=-0.013/0.721; middle coherence=0.919) |
| 13855 | 13855/F2 | L522 | L523 | L521 96.73/57.41 r_next=0.687 MAD_above=8.30 lag=-1(8.24/8.30); L522 86.35/56.96 r_next=-0.026 MAD_above=21.12 lag=-6(14.97/21.12); L523 11.00/1.06 r_next=0.439 MAD_above=76.10 lag=-8(75.75/76.10); L524 11.19/0.91 r_next=-0.088 MAD_above=0.79 lag=10(0.71/0.79); direct-full=L523 (L523 persistent three-third step; thirds=5.986,5.720,12.013; correlation above/next=-0.032/0.729; middle coherence=0.918) |
| 13856 | 13856/F2 | L522 | L523 | L521 96.47/57.15 r_next=0.775 MAD_above=7.86 lag=0(7.86/7.86); L522 88.79/56.96 r_next=-0.022 MAD_above=17.04 lag=-5(12.51/17.04); L523 10.86/0.94 r_next=0.455 MAD_above=78.69 lag=-10(78.31/78.69); L524 11.05/0.98 r_next=0.077 MAD_above=0.76 lag=-20(0.72/0.76); direct-full=L523 (L523 persistent three-third step; thirds=5.701,5.648,12.853; correlation above/next=-0.017/0.758; middle coherence=0.925) |
| 13859 | 13859/F2 | L522 | L523 | L521 101.07/56.90 r_next=0.585 MAD_above=7.08 lag=1(7.08/7.08); L522 80.92/53.98 r_next=-0.078 MAD_above=25.03 lag=-2(23.21/25.03); L523 10.90/0.91 r_next=0.411 MAD_above=70.74 lag=-32(70.11/70.74); L524 10.89/1.01 r_next=0.064 MAD_above=0.76 lag=1(0.72/0.76); direct-full=L523 (L523 persistent three-third step; thirds=6.054,5.538,10.161; correlation above/next=-0.124/0.713; middle coherence=0.920) |
| 13860 | 13860/F2 | L522 | L523 | L521 98.80/56.68 r_next=0.436 MAD_above=7.03 lag=0(7.03/7.03); L522 75.77/54.01 r_next=-0.162 MAD_above=32.19 lag=-8(26.08/32.19); L523 10.73/0.94 r_next=0.390 MAD_above=66.25 lag=-32(65.84/66.25); L524 10.90/0.87 r_next=-0.035 MAD_above=0.73 lag=-17(0.69/0.73); direct-full=L523 (L523 persistent three-third step; thirds=5.580,5.897,8.472; correlation above/next=-0.217/0.718; middle coherence=0.921) |
| 13865 | 13865/F2 | L522 | L523 | L521 97.45/57.76 r_next=0.606 MAD_above=8.61 lag=0(8.61/8.61); L522 82.60/54.94 r_next=-0.102 MAD_above=22.89 lag=-1(21.80/22.89); L523 10.45/1.06 r_next=0.464 MAD_above=72.80 lag=-14(72.49/72.80); L524 10.68/1.01 r_next=0.015 MAD_above=0.82 lag=-11(0.74/0.82); direct-full=L523 (L523 persistent three-third step; thirds=6.101,5.915,10.492; correlation above/next=-0.152/0.747; middle coherence=0.923) |
| 13869 | 13869/F2 | L522 | L523 | L521 99.98/56.97 r_next=0.611 MAD_above=8.51 lag=0(8.51/8.51); L522 84.44/54.52 r_next=0.005 MAD_above=22.63 lag=-2(21.45/22.63); L523 10.87/1.00 r_next=0.502 MAD_above=74.07 lag=-32(73.31/74.07); L524 10.97/0.94 r_next=0.049 MAD_above=0.72 lag=-10(0.68/0.72); direct-full=L523 (L523 persistent three-third step; thirds=6.181,5.780,10.735; correlation above/next=-0.011/0.788; middle coherence=0.923) |
| 13874 | 13874/F2 | L522 | L523 | L521 100.27/56.84 r_next=0.754 MAD_above=8.47 lag=0(8.47/8.47); L522 90.78/56.96 r_next=-0.034 MAD_above=18.53 lag=-4(14.89/18.53); L523 11.03/1.06 r_next=0.439 MAD_above=80.38 lag=-27(79.96/80.38); L524 11.20/1.03 r_next=-0.039 MAD_above=0.83 lag=2(0.78/0.83); direct-full=L523 (L523 persistent three-third step; thirds=6.014,5.851,12.649; correlation above/next=-0.066/0.719; middle coherence=0.919) |
| 13875 | 13875/F2 | L522 | L523 | L521 100.20/56.35 r_next=0.836 MAD_above=7.52 lag=1(7.50/7.52); L522 94.84/57.05 r_next=-0.040 MAD_above=14.82 lag=-5(9.75/14.82); L523 10.43/0.98 r_next=0.431 MAD_above=84.94 lag=32(84.20/84.94); L524 10.97/0.92 r_next=-0.027 MAD_above=0.86 lag=3(0.84/0.86); direct-full=L523 (L523 persistent three-third step; thirds=6.263,5.944,14.016; correlation above/next=-0.050/0.755; middle coherence=0.918) |
| 13885 | 13885/F2 | L522 | L523 | L521 103.55/58.11 r_next=0.923 MAD_above=7.97 lag=0(7.97/7.97); L522 102.17/58.35 r_next=0.103 MAD_above=13.36 lag=-5(7.93/13.36); L523 10.45/1.08 r_next=0.495 MAD_above=91.82 lag=32(87.79/91.82); L524 10.93/1.05 r_next=0.161 MAD_above=0.89 lag=-5(0.87/0.89); direct-full=L523 (L523 persistent three-third step; thirds=7.501,5.874,17.406; correlation above/next=0.131/0.761; middle coherence=0.923) |
| 13917 | 13917/F2 | L522 | L523 | L521 110.77/52.25 r_next=0.605 MAD_above=9.47 lag=0(9.47/9.47); L522 99.24/53.13 r_next=-0.000 MAD_above=21.31 lag=-2(18.71/21.31); L523 10.35/0.94 r_next=0.413 MAD_above=89.14 lag=-13(88.78/89.14); L524 10.68/0.89 r_next=0.107 MAD_above=0.78 lag=8(0.75/0.78); direct-full=L523 (L523 persistent three-third step; thirds=10.416,6.320,13.026; correlation above/next=-0.039/0.716; middle coherence=0.930) |
| 13929 | 13929/F2 | L522 | L523 | L521 101.55/57.10 r_next=0.402 MAD_above=9.77 lag=0(9.77/9.77); L522 85.07/54.68 r_next=-0.113 MAD_above=33.08 lag=-6(25.50/33.08); L523 10.30/0.91 r_next=0.395 MAD_above=74.84 lag=-32(74.26/74.84); L524 10.70/0.93 r_next=0.142 MAD_above=0.80 lag=6(0.79/0.80); direct-full=L523 (L523 persistent three-third step; thirds=6.754,5.506,10.940; correlation above/next=-0.202/0.736; middle coherence=0.926) |
| 13933 | 13933/F2 | L522 | L523 | L521 104.78/55.80 r_next=0.810 MAD_above=9.43 lag=0(9.43/9.43); L522 102.36/56.68 r_next=0.029 MAD_above=18.27 lag=-7(9.89/18.27); L523 10.09/1.00 r_next=0.511 MAD_above=92.67 lag=32(90.58/92.67); L524 10.53/1.05 r_next=0.040 MAD_above=0.81 lag=0(0.81/0.81); direct-full=L523 (L523 persistent three-third step; thirds=8.084,5.826,17.644; correlation above/next=0.043/0.761; middle coherence=0.925) |
| 14010 | 14010/F2 | L522 | L523 | L521 92.35/53.71 r_next=0.586 MAD_above=9.48 lag=0(9.48/9.48); L522 84.55/52.11 r_next=-0.035 MAD_above=22.90 lag=-3(19.86/22.90); L523 10.40/0.89 r_next=0.387 MAD_above=74.41 lag=-32(73.63/74.41); L524 10.62/0.98 r_next=0.151 MAD_above=0.82 lag=11(0.74/0.82); direct-full=L523 (L523 persistent three-third step; thirds=8.704,4.430,10.432; correlation above/next=-0.074/0.710; middle coherence=0.923) |
| 14013 | 14013/F2 | L522 | L523 | L521 93.45/53.69 r_next=0.460 MAD_above=10.42 lag=1(9.93/10.42); L522 84.39/53.03 r_next=-0.057 MAD_above=31.68 lag=-11(18.38/31.68); L523 10.57/0.94 r_next=0.428 MAD_above=74.45 lag=-4(74.27/74.45); L524 10.76/0.91 r_next=0.203 MAD_above=0.77 lag=10(0.71/0.77); direct-full=L523 (L523 persistent three-third step; thirds=7.765,4.890,10.333; correlation above/next=-0.093/0.723; middle coherence=0.917) |
| 14016 | 14016/F2 | L522 | L523 | L521 97.38/54.55 r_next=0.514 MAD_above=11.53 lag=0(11.53/11.53); L522 82.66/51.41 r_next=-0.121 MAD_above=26.20 lag=-2(23.84/26.20); L523 10.55/0.98 r_next=0.435 MAD_above=72.37 lag=-28(71.52/72.37); L524 11.10/0.91 r_next=0.119 MAD_above=0.83 lag=-20(0.80/0.83); direct-full=L523 (L523 persistent three-third step; thirds=8.577,4.698,9.919; correlation above/next=-0.168/0.724; middle coherence=0.920) |
| 14020 | 14020/F2 | L522 | L523 | L521 95.89/54.70 r_next=0.584 MAD_above=13.36 lag=0(13.36/13.36); L522 80.62/51.94 r_next=-0.144 MAD_above=24.06 lag=-3(21.01/24.06); L523 10.71/1.06 r_next=0.471 MAD_above=70.58 lag=-12(69.93/70.58); L524 10.96/1.05 r_next=0.083 MAD_above=0.83 lag=11(0.76/0.83); direct-full=L523 (L523 persistent three-third step; thirds=8.129,3.988,10.270; correlation above/next=-0.212/0.730; middle coherence=0.910) |
| 14021 | 14021/F2 | L522 | L523 | L521 94.33/54.21 r_next=0.672 MAD_above=13.18 lag=0(13.18/13.18); L522 85.53/52.60 r_next=-0.171 MAD_above=19.94 lag=-2(17.99/19.94); L523 10.51/1.00 r_next=0.475 MAD_above=75.34 lag=-32(74.59/75.34); L524 10.60/1.04 r_next=0.140 MAD_above=0.78 lag=5(0.69/0.78); direct-full=L523 (L523 persistent three-third step; thirds=8.183,4.141,10.663; correlation above/next=-0.246/0.798; middle coherence=0.916) |
| 14029 | 14029/F2 | L522 | L523 | L521 121.75/41.81 r_next=0.462 MAD_above=10.72 lag=1(10.61/10.72); L522 113.64/46.68 r_next=-0.314 MAD_above=26.62 lag=-11(14.42/26.62); L523 9.94/1.04 r_next=0.398 MAD_above=103.74 lag=-32(100.79/103.74); L524 10.62/1.03 r_next=0.068 MAD_above=1.01 lag=4(0.95/1.01); direct-full=L523 (L523 persistent three-third step; thirds=10.922,6.710,5.661; correlation above/next=-0.438/0.703; middle coherence=0.867) |
| 14030 | 14030/F2 | L522 | L523 | L521 120.57/42.79 r_next=0.693 MAD_above=12.04 lag=1(11.95/12.04); L522 114.72/45.28 r_next=-0.242 MAD_above=16.85 lag=-2(14.72/16.85); L523 10.07/0.95 r_next=0.479 MAD_above=104.72 lag=-32(102.50/104.72); L524 10.68/1.05 r_next=0.213 MAD_above=0.90 lag=-11(0.88/0.90); direct-full=L523 (L523 persistent three-third step; thirds=10.864,6.868,5.809; correlation above/next=-0.311/0.744; middle coherence=0.862) |
| 14034 | 14034/F2 | L522 | L523 | L521 122.77/41.84 r_next=0.783 MAD_above=12.53 lag=0(12.53/12.53); L522 117.95/41.32 r_next=-0.361 MAD_above=14.41 lag=-3(11.87/14.41); L523 10.77/1.02 r_next=0.465 MAD_above=107.19 lag=-32(105.44/107.19); L524 10.95/1.01 r_next=0.052 MAD_above=0.76 lag=13(0.73/0.76); direct-full=L523 (L523 persistent three-third step; thirds=11.053,6.523,6.521; correlation above/next=-0.466/0.723; middle coherence=0.858) |
| 14035 | 14035/F2 | L522 | L523 | L521 119.14/41.95 r_next=0.592 MAD_above=11.60 lag=-1(11.39/11.60); L522 114.03/43.39 r_next=-0.400 MAD_above=21.72 lag=-8(12.50/21.72); L523 10.57/1.09 r_next=0.533 MAD_above=103.54 lag=-32(100.76/103.54); L524 10.78/1.08 r_next=0.034 MAD_above=0.81 lag=8(0.74/0.81); direct-full=L523 (L523 persistent three-third step; thirds=11.310,6.656,5.936; correlation above/next=-0.513/0.800; middle coherence=0.859) |
| 14036 | 14036/F2 | L522 | L523 | L521 120.20/41.98 r_next=0.654 MAD_above=11.48 lag=0(11.48/11.48); L522 112.86/44.92 r_next=-0.408 MAD_above=18.05 lag=-2(16.24/18.05); L523 10.34/1.16 r_next=0.511 MAD_above=102.58 lag=-32(100.71/102.58); L524 10.58/1.12 r_next=0.111 MAD_above=0.87 lag=15(0.80/0.87); direct-full=L523 (L523 persistent three-third step; thirds=11.054,6.860,5.589; correlation above/next=-0.496/0.752; middle coherence=0.860) |
| 14041 | 14041/F2 | L522 | L523 | L521 120.59/42.12 r_next=0.507 MAD_above=11.85 lag=1(11.41/11.85); L522 113.18/43.85 r_next=-0.326 MAD_above=25.80 lag=-11(11.66/25.80); L523 9.94/0.96 r_next=0.466 MAD_above=103.32 lag=-32(100.55/103.32); L524 10.53/1.04 r_next=0.029 MAD_above=0.91 lag=12(0.84/0.91); direct-full=L523 (L523 persistent three-third step; thirds=11.735,6.572,5.922; correlation above/next=-0.434/0.748; middle coherence=0.869) |
| 14042 | 14042/F2 | L522 | L523 | L521 119.25/40.67 r_next=0.403 MAD_above=10.85 lag=1(10.56/10.85); L522 108.83/47.01 r_next=-0.285 MAD_above=29.40 lag=-12(14.86/29.40); L523 10.08/1.03 r_next=0.508 MAD_above=98.81 lag=-32(95.86/98.81); L524 10.53/1.13 r_next=0.119 MAD_above=0.87 lag=16(0.84/0.87); direct-full=L523 (L523 persistent three-third step; thirds=11.830,6.423,5.120; correlation above/next=-0.444/0.747; middle coherence=0.875) |
| 14044 | 14044/F2 | L522 | L523 | L521 120.09/41.65 r_next=0.417 MAD_above=11.11 lag=1(10.98/11.11); L522 107.55/47.05 r_next=-0.343 MAD_above=29.99 lag=-10(17.48/29.99); L523 9.99/1.02 r_next=0.492 MAD_above=97.60 lag=-32(94.80/97.60); L524 10.75/1.09 r_next=0.126 MAD_above=1.01 lag=-8(0.97/1.01); direct-full=L523 (L523 persistent three-third step; thirds=12.119,6.332,5.122; correlation above/next=-0.450/0.757; middle coherence=0.867) |
| 14049 | 14049/F2 | L522 | L523 | L521 119.52/40.99 r_next=0.509 MAD_above=11.15 lag=1(11.09/11.15); L522 112.70/45.00 r_next=-0.371 MAD_above=24.95 lag=-10(13.91/24.95); L523 10.04/1.04 r_next=0.513 MAD_above=102.68 lag=-32(100.39/102.68); L524 10.88/1.09 r_next=0.007 MAD_above=1.04 lag=0(1.04/1.04); direct-full=L523 (L523 persistent three-third step; thirds=12.610,6.557,5.714; correlation above/next=-0.476/0.785; middle coherence=0.864) |
| 14050 | 14050/F2 | L522 | L523 | L521 120.29/40.63 r_next=0.624 MAD_above=10.41 lag=0(10.41/10.41); L522 109.41/45.58 r_next=-0.353 MAD_above=19.21 lag=-2(17.88/19.21); L523 10.02/0.95 r_next=0.485 MAD_above=99.46 lag=-32(97.52/99.46); L524 10.94/1.06 r_next=0.007 MAD_above=1.08 lag=-12(1.05/1.08); direct-full=L523 (L523 persistent three-third step; thirds=12.715,6.706,5.253; correlation above/next=-0.431/0.791; middle coherence=0.866) |
| 14053 | 14053/F2 | L522 | L523 | L521 120.34/42.03 r_next=0.420 MAD_above=11.80 lag=1(11.28/11.80); L522 110.08/47.47 r_next=-0.371 MAD_above=29.63 lag=-10(16.35/29.63); L523 10.04/1.09 r_next=0.552 MAD_above=100.13 lag=-32(97.38/100.13); L524 10.43/1.19 r_next=0.103 MAD_above=0.86 lag=12(0.84/0.86); direct-full=L523 (L523 persistent three-third step; thirds=12.108,6.228,5.263; correlation above/next=-0.485/0.806; middle coherence=0.859) |
| 14054 | 14054/F2 | L522 | L523 | L521 118.00/41.59 r_next=0.661 MAD_above=11.53 lag=1(10.86/11.53); L522 108.55/44.51 r_next=-0.334 MAD_above=17.88 lag=-2(15.80/17.88); L523 9.66/1.07 r_next=0.482 MAD_above=98.95 lag=-32(97.09/98.95); L524 10.38/1.18 r_next=0.077 MAD_above=1.05 lag=-17(0.95/1.05); direct-full=L523 (L523 persistent three-third step; thirds=12.395,6.267,5.396; correlation above/next=-0.439/0.751; middle coherence=0.870) |
| 14055 | 14055/F2 | L522 | L523 | L521 120.83/40.57 r_next=0.494 MAD_above=10.60 lag=1(10.15/10.60); L522 114.20/43.98 r_next=-0.243 MAD_above=25.28 lag=-11(12.62/25.28); L523 9.93/0.96 r_next=0.415 MAD_above=104.29 lag=-32(101.66/104.29); L524 10.56/1.06 r_next=0.091 MAD_above=0.97 lag=-15(0.92/0.97); direct-full=L523 (L523 persistent three-third step; thirds=12.397,6.185,5.823; correlation above/next=-0.271/0.706; middle coherence=0.853) |
| 14058 | 14058/F2 | L522 | L523 | L521 117.38/41.00 r_next=0.543 MAD_above=11.34 lag=0(11.34/11.34); L522 111.58/42.12 r_next=-0.269 MAD_above=23.05 lag=-11(10.46/23.05); L523 9.75/1.02 r_next=0.471 MAD_above=101.84 lag=-32(99.41/101.84); L524 10.28/1.06 r_next=0.040 MAD_above=0.92 lag=8(0.86/0.92); direct-full=L523 (L523 persistent three-third step; thirds=12.060,6.026,5.962; correlation above/next=-0.348/0.747; middle coherence=0.865) |
| 14059 | 14059/F2 | L522 | L523 | L521 116.66/39.54 r_next=0.629 MAD_above=11.36 lag=1(11.04/11.36); L522 112.28/41.59 r_next=-0.235 MAD_above=20.68 lag=-8(10.84/20.68); L523 9.98/0.95 r_next=0.386 MAD_above=102.30 lag=-32(99.86/102.30); L524 10.35/1.01 r_next=0.141 MAD_above=0.87 lag=10(0.75/0.87); direct-full=L523 (L523 persistent three-third step; thirds=11.364,5.903,5.988; correlation above/next=-0.310/0.714; middle coherence=0.874) |
| 14061 | 14061/F2 | L522 | L523 | L521 116.00/40.61 r_next=0.516 MAD_above=11.52 lag=1(11.48/11.52); L522 108.83/42.07 r_next=-0.319 MAD_above=23.64 lag=-11(12.36/23.64); L523 10.06/0.94 r_next=0.466 MAD_above=98.85 lag=-32(96.34/98.85); L524 10.23/1.00 r_next=0.048 MAD_above=0.74 lag=18(0.65/0.74); direct-full=L523 (L523 persistent three-third step; thirds=11.309,5.978,5.410; correlation above/next=-0.437/0.783; middle coherence=0.875) |
| 14069 | 14069/F2 | L522 | L523 | L521 112.52/40.35 r_next=0.522 MAD_above=11.57 lag=1(11.27/11.57); L522 106.81/41.33 r_next=-0.254 MAD_above=22.74 lag=-10(9.92/22.74); L523 9.89/0.97 r_next=0.440 MAD_above=96.93 lag=-32(94.40/96.93); L524 10.47/1.02 r_next=0.050 MAD_above=0.92 lag=8(0.83/0.92); direct-full=L523 (L523 persistent three-third step; thirds=9.729,6.357,5.998; correlation above/next=-0.375/0.708; middle coherence=0.891) |
| 14078 | 14078/F2 | L522 | L523 | L521 104.49/38.34 r_next=0.255 MAD_above=15.26 lag=0(15.26/15.26); L522 85.16/43.21 r_next=-0.353 MAD_above=34.98 lag=-13(25.34/34.98); L523 9.79/0.97 r_next=0.471 MAD_above=75.45 lag=0(75.45/75.45); L524 10.25/0.96 r_next=0.149 MAD_above=0.79 lag=12(0.77/0.79); direct-full=L523 (L523 persistent three-third step; thirds=10.339,5.363,3.211; correlation above/next=-0.480/0.731; middle coherence=0.844) |
| 14079 | 14079/F2 | L522 | L523 | L521 95.96/35.82 r_next=0.205 MAD_above=14.97 lag=1(14.64/14.97); L522 79.61/40.79 r_next=-0.244 MAD_above=30.46 lag=-11(25.06/30.46); L523 10.13/0.87 r_next=0.448 MAD_above=69.59 lag=0(69.59/69.59); L524 10.30/0.91 r_next=0.132 MAD_above=0.68 lag=11(0.68/0.68); direct-full=L523 (L523 persistent three-third step; thirds=9.700,4.584,2.950; correlation above/next=-0.362/0.778; middle coherence=0.838) |
| 14095 | 14095/F2 | L522 | L523 | L521 83.34/35.87 r_next=0.609 MAD_above=12.70 lag=0(12.70/12.70); L522 76.33/37.25 r_next=-0.472 MAD_above=19.65 lag=-9(11.42/19.65); L523 9.81/1.01 r_next=0.459 MAD_above=66.63 lag=0(66.63/66.63); L524 9.99/0.97 r_next=0.022 MAD_above=0.75 lag=8(0.67/0.75); direct-full=L523 (L523 persistent three-third step; thirds=8.419,3.515,2.660; correlation above/next=-0.647/0.772; middle coherence=0.810) |
| 14104 | 14104/F2 | L522 | L523 | L521 83.29/35.59 r_next=0.769 MAD_above=12.65 lag=1(12.57/12.65); L522 79.65/38.32 r_next=-0.358 MAD_above=13.69 lag=-2(11.38/13.69); L523 10.70/0.92 r_next=0.411 MAD_above=69.05 lag=0(69.05/69.05); L524 10.72/0.95 r_next=0.020 MAD_above=0.73 lag=-5(0.70/0.73); direct-full=L523 (L523 persistent three-third step; thirds=8.402,3.759,2.594; correlation above/next=-0.506/0.711; middle coherence=0.811) |

## Segment constants and applied crop

### Engine field 1

- H engine minus reference: +0: 608; mismatch counters: none.
- c engine minus reference: +0: 608; mismatch counters: none.
- crop engine minus reference: -1: 3, +0: 600, +1: 5; mismatch counters: 13500-13502, 13578, 13603-13604, 13988, 14101.

### Engine field 2

- H engine minus reference: +1: 608; mismatch counters: 13500-14107.
- c engine minus reference: -1: 608; mismatch counters: 13500-14107.
- crop engine minus reference: -1: 9, +0: 599; mismatch counters: 13588-13590, 13940-13942, 13968-13970.

## Comb consistency

Comparable measured pairs: 535; unavailable engine/top pair: 0; contradictions: 4.

| reference counter | comb shift | engine tops | engine-reference top deltas | seven energies |
|---:|---:|:---|:---|:---|
| 13501 | -1 | L24/L286 | +1/+0 | -4:14.120539,-3:11.630827,-2:8.317704,-1:5.008133,0:8.350540,1:11.584305,2:14.059389 |
| 13502 | -1 | L24/L286 | +1/+0 | -4:14.213523,-3:11.656292,-2:7.604525,-1:4.761081,0:7.921401,1:11.601932,2:13.884241 |
| 13988 | +0 | L25/L286 | +1/+0 | -3:10.504111,-2:8.728921,-1:6.360242,0:4.304676,1:6.397122,2:8.837414,3:10.678172 |
| 14101 | +0 | L24/L286 | -1/+0 | -3:15.696590,-2:12.897367,-1:8.523996,0:5.019908,1:8.973943,2:13.809525,3:16.396969 |

# Engine-record score: SP recording, V-stabilize off

Acceptance verdict: **not accepted**.

Engine rows joined by device counter: 1214; unmatched engine rows: none.

For the repaired SP pass, an engine field-1 record is compared with raw slot 2 at the same counter and an engine field-2 record with raw slot 1 at the next counter. All reported line numbers remain NTSC raster-slot lines.

Owner-review disagreement units: 452; counters: 171, 173, 176, 179, 181-182, 185-186, 188, 190-193, 199, 201, 203-204, 208-213, 216, 218, 220-222, 227, 232, 234, 236-237, 239-242, 245-246, 248-250, 252-256, 262, 270-273, 275-290, 293-298, 300-357, 359-370, 372-383, 385-406, 408-413, 415, 419, 421-422, 424-428, 431, 435, 437, 441, 444-445, 447-462, 464-465, 467-474, 476-479, 482, 485-486, 488-490, 492, 494-496, 498, 501, 503-504, 509, 511, 513-516, 518, 521-522, 526-536, 539-542, 544-557, 559-563, 565-568, 570-575, 577-583, 585-603, 605-608, 610, 612, 616, 618, 620-630, 632, 634-637, 643-646, 648, 651-653, 655, 657-689, 691-712, 714-728, 730-748, 750-751, 753-756, 762, 772.

Shifted woven bwdif frames written: 452 under `reports/engine_run_R_disagreements/off`.

| counter | reason(s) | shifted bwdif frame |
|---:|:---|:---|
| 171 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00171.webp` |
| 173 | F1 S/first-full L523/L525 | `reports/engine_run_R_disagreements/off/counter_00173.webp` |
| 176 | F1 S/first-full unmeasurable/L523; F1 S/switch unmeasurable/L523 | `reports/engine_run_R_disagreements/off/counter_00176.webp` |
| 179 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00179.webp` |
| 181 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00181.webp` |
| 182 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00182.webp` |
| 185 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00185.webp` |
| 186 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00186.webp` |
| 188 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00188.webp` |
| 190 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00190.webp` |
| 191 | F1 S/first-full L525/L523; F1 S/switch L525/L523 | `reports/engine_run_R_disagreements/off/counter_00191.webp` |
| 192 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00192.webp` |
| 193 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00193.webp` |
| 199 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00199.webp` |
| 201 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00201.webp` |
| 203 | F1 S/first-full L522/L524 | `reports/engine_run_R_disagreements/off/counter_00203.webp` |
| 204 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00204.webp` |
| 208 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00208.webp` |
| 209 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00209.webp` |
| 210 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00210.webp` |
| 211 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00211.webp` |
| 212 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00212.webp` |
| 213 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00213.webp` |
| 216 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00216.webp` |
| 218 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00218.webp` |
| 220 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00220.webp` |
| 221 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00221.webp` |
| 222 | F2 S/first-full L259/L261; F2 S/switch L259/L261 | `reports/engine_run_R_disagreements/off/counter_00222.webp` |
| 227 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00227.webp` |
| 232 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00232.webp` |
| 234 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00234.webp` |
| 236 | F1 S/first-full L524/L525 | `reports/engine_run_R_disagreements/off/counter_00236.webp` |
| 237 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00237.webp` |
| 239 | F1 S/first-full L524/L525 | `reports/engine_run_R_disagreements/off/counter_00239.webp` |
| 240 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00240.webp` |
| 241 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00241.webp` |
| 242 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00242.webp` |
| 245 | F1 S/first-full L523/L524; F2 S/first-full L261/L262 | `reports/engine_run_R_disagreements/off/counter_00245.webp` |
| 246 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00246.webp` |
| 248 | F1 crop L287/L286; engine decisive comb -1 at placed crops (ratio 0.550) | `reports/engine_run_R_disagreements/off/counter_00248.webp` |
| 249 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00249.webp` |
| 250 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00250.webp` |
| 252 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00252.webp` |
| 253 | F1 S/first-full L522/L524 | `reports/engine_run_R_disagreements/off/counter_00253.webp` |
| 254 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00254.webp` |
| 255 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00255.webp` |
| 256 | F1 S/first-full L522/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00256.webp` |
| 262 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00262.webp` |
| 270 | engine decisive comb +1 at placed crops (ratio 0.580) | `reports/engine_run_R_disagreements/off/counter_00270.webp` |
| 271 | engine decisive comb +1 at placed crops (ratio 0.650) | `reports/engine_run_R_disagreements/off/counter_00271.webp` |
| 272 | F1 S/first-full L524/L525; engine decisive comb +1 at placed crops (ratio 0.600) | `reports/engine_run_R_disagreements/off/counter_00272.webp` |
| 273 | F1 S/first-full L524/L525 | `reports/engine_run_R_disagreements/off/counter_00273.webp` |
| 275 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00275.webp` |
| 276 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00276.webp` |
| 277 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00277.webp` |
| 278 | F1 S/first-full L524/L525 | `reports/engine_run_R_disagreements/off/counter_00278.webp` |
| 279 | F1 S/first-full L524/L525; engine decisive comb +1 at placed crops (ratio 0.580) | `reports/engine_run_R_disagreements/off/counter_00279.webp` |
| 280 | F1 S/first-full L524/L525; engine decisive comb +1 at placed crops (ratio 0.540) | `reports/engine_run_R_disagreements/off/counter_00280.webp` |
| 281 | F1 S/first-full L524/L525; engine decisive comb +1 at placed crops (ratio 0.590) | `reports/engine_run_R_disagreements/off/counter_00281.webp` |
| 282 | F1 S/first-full L524/L525; F2 S/first-full L260/L261; engine decisive comb +1 at placed crops (ratio 0.590) | `reports/engine_run_R_disagreements/off/counter_00282.webp` |
| 283 | F1 S/first-full L524/L525 | `reports/engine_run_R_disagreements/off/counter_00283.webp` |
| 284 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00284.webp` |
| 285 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00285.webp` |
| 286 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00286.webp` |
| 287 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00287.webp` |
| 288 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00288.webp` |
| 289 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00289.webp` |
| 290 | F1 S/first-full L521/L525; F1 S/switch L521/L524; F1 crop L286/L287; engine decisive comb +1 at placed crops (ratio 0.640) | `reports/engine_run_R_disagreements/off/counter_00290.webp` |
| 293 | F1 S/first-full L524/L525; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00293.webp` |
| 294 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00294.webp` |
| 295 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00295.webp` |
| 296 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00296.webp` |
| 297 | F1 S/first-full L524/L525; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00297.webp` |
| 298 | F1 S/first-full L524/L525; F2 S/first-full L260/L261; engine decisive comb +1 at placed crops (ratio 0.750) | `reports/engine_run_R_disagreements/off/counter_00298.webp` |
| 300 | F1 S/first-full L524/L525 | `reports/engine_run_R_disagreements/off/counter_00300.webp` |
| 301 | F1 S/first-full L523/L525; engine decisive comb +1 at placed crops (ratio 0.510) | `reports/engine_run_R_disagreements/off/counter_00301.webp` |
| 302 | F1 S/first-full L523/L525 | `reports/engine_run_R_disagreements/off/counter_00302.webp` |
| 303 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00303.webp` |
| 304 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00304.webp` |
| 305 | F1 S/first-full L524/L525; F2 S/first-full L259/L261; engine decisive comb +1 at placed crops (ratio 0.790) | `reports/engine_run_R_disagreements/off/counter_00305.webp` |
| 306 | F1 S/first-full L524/L525; F2 S/first-full L259/L261; F2 crop L22/L23; reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00306.webp` |
| 307 | F1 S/first-full L524/L525; F2 crop L22/L23; reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00307.webp` |
| 308 | F1 S/first-full L524/L525; F2 crop L22/L23 | `reports/engine_run_R_disagreements/off/counter_00308.webp` |
| 309 | F1 S/first-full L524/L525; F2 crop L22/L23 | `reports/engine_run_R_disagreements/off/counter_00309.webp` |
| 310 | F1 S/first-full L523/L524; F2 crop L22/L23; engine decisive comb -1 at placed crops (ratio 0.450) | `reports/engine_run_R_disagreements/off/counter_00310.webp` |
| 311 | F1 S/first-full L523/L524; F2 S/first-full L260/L261; F2 crop L22/L23 | `reports/engine_run_R_disagreements/off/counter_00311.webp` |
| 312 | F1 S/first-full L523/L524; F2 crop L22/L23; engine decisive comb -1 at placed crops (ratio 0.590) | `reports/engine_run_R_disagreements/off/counter_00312.webp` |
| 313 | F1 S/first-full L524/L525; F2 crop L22/L23 | `reports/engine_run_R_disagreements/off/counter_00313.webp` |
| 314 | F1 S/first-full L524/L525; F2 crop L22/L23; reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00314.webp` |
| 315 | F1 S/first-full L524/L525; F2 crop L22/L23; reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00315.webp` |
| 316 | F1 S/first-full L524/L525; F2 S/first-full L260/L261; F2 crop L22/L23 | `reports/engine_run_R_disagreements/off/counter_00316.webp` |
| 317 | F1 S/first-full L524/L525; F2 S/first-full L260/L261; F2 crop L22/L23; reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00317.webp` |
| 318 | F1 S/first-full L524/L525; F2 crop L22/L23; reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00318.webp` |
| 319 | F1 S/first-full L524/L525; F2 crop L22/L23; reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00319.webp` |
| 320 | F1 S/first-full L524/L525; F2 crop L22/L23; reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00320.webp` |
| 321 | F1 S/first-full L524/L525; F2 S/first-full L260/L261; F2 crop L22/L23; reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00321.webp` |
| 322 | F1 S/first-full L524/L525; F2 S/first-full L260/L261; F2 crop L22/L23; reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00322.webp` |
| 323 | F1 S/first-full L524/L525; F2 crop L22/L23; engine decisive comb -1 at placed crops (ratio 0.650) | `reports/engine_run_R_disagreements/off/counter_00323.webp` |
| 324 | F1 S/first-full L522/L524; F1 crop L285/L286; F2 S/first-full L259/L261; F2 crop L22/L23 | `reports/engine_run_R_disagreements/off/counter_00324.webp` |
| 325 | F1 S/first-full L521/L524; F1 S/switch L521/L523; F1 crop L285/L286; F2 crop L22/L23 | `reports/engine_run_R_disagreements/off/counter_00325.webp` |
| 326 | F1 S/first-full L523/L524; F1 crop L285/L286; F2 crop L22/L23 | `reports/engine_run_R_disagreements/off/counter_00326.webp` |
| 327 | F1 S/first-full L523/L524; F1 crop L285/L286; F2 crop L22/L23 | `reports/engine_run_R_disagreements/off/counter_00327.webp` |
| 328 | F1 S/first-full L524/L525; F1 crop L285/L286; F2 crop L22/L23 | `reports/engine_run_R_disagreements/off/counter_00328.webp` |
| 329 | F1 S/first-full L524/L525; F1 crop L285/L286; F2 crop L22/L23; engine decisive comb +1 at placed crops (ratio 0.550); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00329.webp` |
| 330 | F1 S/first-full L524/L525; F1 crop L285/L286; F2 crop L22/L23; engine decisive comb +1 at placed crops (ratio 0.550); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00330.webp` |
| 331 | F1 S/first-full L524/L525; F1 crop L285/L286; F2 crop L22/L23; engine decisive comb +1 at placed crops (ratio 0.540); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00331.webp` |
| 332 | F1 S/first-full L524/L525; F1 crop L285/L286; F2 S/first-full L260/L261; F2 crop L22/L23; engine decisive comb +1 at placed crops (ratio 0.560); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00332.webp` |
| 333 | F1 S/first-full L524/L525; F2 crop L22/L23; engine decisive comb -1 at placed crops (ratio 0.740) | `reports/engine_run_R_disagreements/off/counter_00333.webp` |
| 334 | F1 S/first-full L522/L524; F1 crop L285/L286; F2 S/first-full L260/L261; F2 crop L22/L23 | `reports/engine_run_R_disagreements/off/counter_00334.webp` |
| 335 | F1 S/first-full L523/L524; F1 crop L285/L286; F2 crop L22/L23 | `reports/engine_run_R_disagreements/off/counter_00335.webp` |
| 336 | F1 S/first-full L523/L525; F1 crop L285/L286; F2 crop L22/L23; reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00336.webp` |
| 337 | F1 S/first-full L524/L525; F1 crop L285/L286; F2 crop L22/L23; engine decisive comb +1 at placed crops (ratio 0.570); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00337.webp` |
| 338 | F1 S/first-full L524/L525; F1 crop L285/L286; F2 crop L22/L23; engine decisive comb +1 at placed crops (ratio 0.540); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00338.webp` |
| 339 | F1 S/first-full L524/L525; F1 crop L285/L286; F2 S/first-full L260/L261; F2 crop L22/L23 | `reports/engine_run_R_disagreements/off/counter_00339.webp` |
| 340 | F1 S/first-full L524/L525; F1 crop L285/L286; F2 S/first-full L260/L261; F2 crop L22/L23; engine decisive comb +2 at placed crops (ratio 0.780) | `reports/engine_run_R_disagreements/off/counter_00340.webp` |
| 341 | F1 S/first-full L524/L525; F1 crop L285/L286; F2 S/first-full L260/L261; F2 crop L22/L23; reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00341.webp` |
| 342 | F1 S/first-full L524/L525; F1 crop L285/L286; F2 S/first-full L260/L261; F2 crop L22/L23; engine decisive comb +1 at placed crops (ratio 0.540); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00342.webp` |
| 343 | F1 S/first-full L524/L525; F1 crop L285/L286; F2 crop L22/L23; engine decisive comb +1 at placed crops (ratio 0.530); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00343.webp` |
| 344 | F1 S/first-full L524/L525; F1 crop L285/L286; F2 S/first-full L260/L261; F2 crop L22/L23; engine decisive comb +1 at placed crops (ratio 0.540); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00344.webp` |
| 345 | F1 S/first-full L524/L525; F1 crop L285/L286; F2 S/first-full L260/L261; F2 crop L22/L23; engine decisive comb +1 at placed crops (ratio 0.540); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00345.webp` |
| 346 | F1 S/first-full L523/L525; F2 crop L22/L23; reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00346.webp` |
| 347 | F1 S/first-full L524/L525; F2 S/first-full L259/L261; F2 crop L22/L23 | `reports/engine_run_R_disagreements/off/counter_00347.webp` |
| 348 | F1 S/first-full L524/L525; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00348.webp` |
| 349 | F1 S/first-full L523/L524; F2 S/first-full L259/L261 | `reports/engine_run_R_disagreements/off/counter_00349.webp` |
| 350 | F1 S/first-full L522/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00350.webp` |
| 351 | F1 S/first-full L524/L525; F2 S/first-full L260/L261; reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00351.webp` |
| 352 | F1 S/first-full L523/L525; engine decisive comb +1 at placed crops (ratio 0.520); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00352.webp` |
| 353 | F1 S/first-full L524/L525; engine decisive comb +1 at placed crops (ratio 0.510); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00353.webp` |
| 354 | engine decisive comb +1 at placed crops (ratio 0.530); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00354.webp` |
| 355 | F1 S/first-full L524/L525; engine decisive comb +1 at placed crops (ratio 0.540); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00355.webp` |
| 356 | F1 S/first-full L524/L525; engine decisive comb +1 at placed crops (ratio 0.530); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00356.webp` |
| 357 | F1 S/first-full L524/L525; F2 S/first-full L260/L261; engine decisive comb +1 at placed crops (ratio 0.530); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00357.webp` |
| 359 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00359.webp` |
| 360 | F1 S/first-full L522/L524 | `reports/engine_run_R_disagreements/off/counter_00360.webp` |
| 361 | F1 S/first-full L524/L525; F2 S/first-full L259/L261; engine decisive comb +1 at placed crops (ratio 0.690) | `reports/engine_run_R_disagreements/off/counter_00361.webp` |
| 362 | F1 S/first-full L523/L525; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00362.webp` |
| 363 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00363.webp` |
| 364 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00364.webp` |
| 365 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00365.webp` |
| 366 | engine decisive comb +1 at placed crops (ratio 0.690); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00366.webp` |
| 367 | engine decisive comb +1 at placed crops (ratio 0.540); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00367.webp` |
| 368 | F1 S/first-full L524/L525; engine decisive comb +1 at placed crops (ratio 0.540); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00368.webp` |
| 369 | F1 S/first-full L524/L525 | `reports/engine_run_R_disagreements/off/counter_00369.webp` |
| 370 | F1 S/first-full L522/L524; F1 crop L287/L286; F2 S/first-full L260/L261; engine decisive comb -1 at placed crops (ratio 0.620) | `reports/engine_run_R_disagreements/off/counter_00370.webp` |
| 372 | F1 S/first-full L523/L524; F2 S/first-full L261/L262 | `reports/engine_run_R_disagreements/off/counter_00372.webp` |
| 373 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00373.webp` |
| 374 | F1 S/first-full L523/L524; F2 S/first-full L260/L262 | `reports/engine_run_R_disagreements/off/counter_00374.webp` |
| 375 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00375.webp` |
| 376 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00376.webp` |
| 377 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00377.webp` |
| 378 | F1 S/switch unmeasurable/L522; engine decisive comb +1 at placed crops (ratio 0.790); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00378.webp` |
| 379 | engine decisive comb +1 at placed crops (ratio 0.520); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00379.webp` |
| 380 | F1 S/switch L525/L522; engine decisive comb +1 at placed crops (ratio 0.540); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00380.webp` |
| 381 | F1 S/switch unmeasurable/L522; F1 crop L287/L286 | `reports/engine_run_R_disagreements/off/counter_00381.webp` |
| 382 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00382.webp` |
| 383 | F1 S/switch unmeasurable/L525; F2 S/first-full L259/L261 | `reports/engine_run_R_disagreements/off/counter_00383.webp` |
| 385 | F1 S/switch unmeasurable/L522; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00385.webp` |
| 386 | F1 S/switch unmeasurable/L522; F2 S/first-full L261/L262 | `reports/engine_run_R_disagreements/off/counter_00386.webp` |
| 387 | F1 S/switch unmeasurable/L522; F2 S/switch L257/L261 | `reports/engine_run_R_disagreements/off/counter_00387.webp` |
| 388 | F1 S/switch unmeasurable/L522; F2 S/switch unmeasurable/L259; F2 crop L23/L22 | `reports/engine_run_R_disagreements/off/counter_00388.webp` |
| 389 | F1 S/switch unmeasurable/L522; F1 crop L286/L285; F2 S/switch unmeasurable/L259; F2 crop L23/L22 | `reports/engine_run_R_disagreements/off/counter_00389.webp` |
| 390 | F1 S/switch unmeasurable/L522; F1 crop L286/L285; F2 S/switch L259/L261; F2 crop L23/L22; engine decisive comb +1 at placed crops (ratio 0.700); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00390.webp` |
| 391 | F1 S/switch unmeasurable/L522; F1 crop L286/L285; F2 S/switch unmeasurable/L262; F2 crop L23/L22; engine decisive comb +1 at placed crops (ratio 0.500); reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/off/counter_00391.webp` |
| 392 | F1 S/switch unmeasurable/L522; F1 crop L286/L285; F2 crop L23/L22 | `reports/engine_run_R_disagreements/off/counter_00392.webp` |
| 393 | F1 S/switch unmeasurable/L522; F1 crop L286/L285; F2 crop L23/L22; engine decisive comb +1 at placed crops (ratio 0.730) | `reports/engine_run_R_disagreements/off/counter_00393.webp` |
| 394 | F1 crop L286/L285; F2 S/switch L258/L262; F2 crop L23/L22 | `reports/engine_run_R_disagreements/off/counter_00394.webp` |
| 395 | F1 S/first-full L523/L524; F1 crop L286/L285; F2 S/switch unmeasurable/L259; F2 crop L24/L22 | `reports/engine_run_R_disagreements/off/counter_00395.webp` |
| 396 | F1 S/first-full unmeasurable/L524; F1 S/switch unmeasurable/L524; F1 crop L286/L285; F2 S/first-full unmeasurable/L261; F2 S/switch unmeasurable/L261; F2 crop L24/L22 | `reports/engine_run_R_disagreements/off/counter_00396.webp` |
| 397 | F1 S/first-full unmeasurable/L524; F1 S/switch unmeasurable/L524; F1 crop L286/L285; F2 crop L24/L22 | `reports/engine_run_R_disagreements/off/counter_00397.webp` |
| 398 | F1 S/switch L524/L522; F1 crop L287/L285; F2 crop L24/L22 | `reports/engine_run_R_disagreements/off/counter_00398.webp` |
| 399 | F1 S/switch L523/L525; F1 crop L286/L285 | `reports/engine_run_R_disagreements/off/counter_00399.webp` |
| 400 | F2 S/first-full L261/L262 | `reports/engine_run_R_disagreements/off/counter_00400.webp` |
| 401 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00401.webp` |
| 402 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00402.webp` |
| 403 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00403.webp` |
| 404 | F2 S/first-full L259/L261; F2 S/switch L259/L261 | `reports/engine_run_R_disagreements/off/counter_00404.webp` |
| 405 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00405.webp` |
| 406 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00406.webp` |
| 408 | F1 S/first-full L522/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00408.webp` |
| 409 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00409.webp` |
| 410 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00410.webp` |
| 411 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00411.webp` |
| 412 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00412.webp` |
| 413 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00413.webp` |
| 415 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00415.webp` |
| 419 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00419.webp` |
| 421 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00421.webp` |
| 422 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00422.webp` |
| 424 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00424.webp` |
| 425 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00425.webp` |
| 426 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00426.webp` |
| 427 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00427.webp` |
| 428 | F1 S/first-full L522/L524 | `reports/engine_run_R_disagreements/off/counter_00428.webp` |
| 431 | F1 S/first-full L522/L523 | `reports/engine_run_R_disagreements/off/counter_00431.webp` |
| 435 | F1 S/first-full L524/L523 | `reports/engine_run_R_disagreements/off/counter_00435.webp` |
| 437 | F1 S/first-full L521/L523; F1 S/switch L521/L523 | `reports/engine_run_R_disagreements/off/counter_00437.webp` |
| 441 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00441.webp` |
| 444 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00444.webp` |
| 445 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00445.webp` |
| 447 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00447.webp` |
| 448 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00448.webp` |
| 449 | F1 S/first-full L521/L524; F1 S/switch L521/L523; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00449.webp` |
| 450 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00450.webp` |
| 451 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00451.webp` |
| 452 | F1 S/first-full L522/L524 | `reports/engine_run_R_disagreements/off/counter_00452.webp` |
| 453 | F1 S/first-full L523/L524; F2 S/first-full L259/L261 | `reports/engine_run_R_disagreements/off/counter_00453.webp` |
| 454 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00454.webp` |
| 455 | F1 S/first-full L522/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00455.webp` |
| 456 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00456.webp` |
| 457 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00457.webp` |
| 458 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00458.webp` |
| 459 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00459.webp` |
| 460 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00460.webp` |
| 461 | F1 S/first-full L523/L524; F2 S/first-full L259/L261 | `reports/engine_run_R_disagreements/off/counter_00461.webp` |
| 462 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00462.webp` |
| 464 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00464.webp` |
| 465 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00465.webp` |
| 467 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00467.webp` |
| 468 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00468.webp` |
| 469 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00469.webp` |
| 470 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00470.webp` |
| 471 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00471.webp` |
| 472 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00472.webp` |
| 473 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00473.webp` |
| 474 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00474.webp` |
| 476 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00476.webp` |
| 477 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00477.webp` |
| 478 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00478.webp` |
| 479 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00479.webp` |
| 482 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00482.webp` |
| 485 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00485.webp` |
| 486 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00486.webp` |
| 488 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00488.webp` |
| 489 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00489.webp` |
| 490 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00490.webp` |
| 492 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00492.webp` |
| 494 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00494.webp` |
| 495 | F2 S/first-full L261/L260; F2 S/switch L261/L259 | `reports/engine_run_R_disagreements/off/counter_00495.webp` |
| 496 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00496.webp` |
| 498 | F2 S/first-full L261/L259; F2 S/switch L261/L259 | `reports/engine_run_R_disagreements/off/counter_00498.webp` |
| 501 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00501.webp` |
| 503 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00503.webp` |
| 504 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00504.webp` |
| 509 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00509.webp` |
| 511 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00511.webp` |
| 513 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00513.webp` |
| 514 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00514.webp` |
| 515 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00515.webp` |
| 516 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00516.webp` |
| 518 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00518.webp` |
| 521 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00521.webp` |
| 522 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00522.webp` |
| 526 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00526.webp` |
| 527 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00527.webp` |
| 528 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00528.webp` |
| 529 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00529.webp` |
| 530 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00530.webp` |
| 531 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00531.webp` |
| 532 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00532.webp` |
| 533 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00533.webp` |
| 534 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00534.webp` |
| 535 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00535.webp` |
| 536 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00536.webp` |
| 539 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00539.webp` |
| 540 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00540.webp` |
| 541 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00541.webp` |
| 542 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00542.webp` |
| 544 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00544.webp` |
| 545 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00545.webp` |
| 546 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00546.webp` |
| 547 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00547.webp` |
| 548 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00548.webp` |
| 549 | F1 S/first-full L522/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00549.webp` |
| 550 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00550.webp` |
| 551 | F1 S/first-full L522/L524 | `reports/engine_run_R_disagreements/off/counter_00551.webp` |
| 552 | F1 S/first-full L522/L524; F2 S/first-full L259/L261 | `reports/engine_run_R_disagreements/off/counter_00552.webp` |
| 553 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00553.webp` |
| 554 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00554.webp` |
| 555 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00555.webp` |
| 556 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00556.webp` |
| 557 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00557.webp` |
| 559 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00559.webp` |
| 560 | F2 S/first-full L259/L261 | `reports/engine_run_R_disagreements/off/counter_00560.webp` |
| 561 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00561.webp` |
| 562 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00562.webp` |
| 563 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00563.webp` |
| 565 | F1 S/first-full L523/L524; F2 S/first-full L259/L261; F2 S/switch L259/L261 | `reports/engine_run_R_disagreements/off/counter_00565.webp` |
| 566 | F1 S/first-full L522/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00566.webp` |
| 567 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00567.webp` |
| 568 | F1 S/first-full L523/L524; F2 S/first-full L259/L261; F2 S/switch L259/L261 | `reports/engine_run_R_disagreements/off/counter_00568.webp` |
| 570 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00570.webp` |
| 571 | F1 S/first-full L522/L524; F2 S/first-full L259/L261; F2 S/switch L259/L261 | `reports/engine_run_R_disagreements/off/counter_00571.webp` |
| 572 | F1 S/first-full L522/L524 | `reports/engine_run_R_disagreements/off/counter_00572.webp` |
| 573 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00573.webp` |
| 574 | F1 S/first-full L525/L524; F1 S/switch L525/L523; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00574.webp` |
| 575 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00575.webp` |
| 577 | F2 S/first-full L261/L262 | `reports/engine_run_R_disagreements/off/counter_00577.webp` |
| 578 | F1 S/first-full L522/L523 | `reports/engine_run_R_disagreements/off/counter_00578.webp` |
| 579 | F1 S/first-full L524/L525; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00579.webp` |
| 580 | F1 S/switch unmeasurable/L525 | `reports/engine_run_R_disagreements/off/counter_00580.webp` |
| 581 | F1 S/switch L525/L523; F2 S/switch unmeasurable/L260 | `reports/engine_run_R_disagreements/off/counter_00581.webp` |
| 582 | F1 S/switch unmeasurable/L523 | `reports/engine_run_R_disagreements/off/counter_00582.webp` |
| 583 | F1 S/switch unmeasurable/L523 | `reports/engine_run_R_disagreements/off/counter_00583.webp` |
| 585 | F1 S/switch unmeasurable/L523; F2 S/switch unmeasurable/L261 | `reports/engine_run_R_disagreements/off/counter_00585.webp` |
| 586 | F1 S/switch unmeasurable/L525 | `reports/engine_run_R_disagreements/off/counter_00586.webp` |
| 587 | F1 S/switch unmeasurable/L523 | `reports/engine_run_R_disagreements/off/counter_00587.webp` |
| 588 | F1 S/switch unmeasurable/L523 | `reports/engine_run_R_disagreements/off/counter_00588.webp` |
| 589 | F1 S/switch L521/L523; F2 S/switch unmeasurable/L261 | `reports/engine_run_R_disagreements/off/counter_00589.webp` |
| 590 | F1 S/switch unmeasurable/L522; F2 S/switch unmeasurable/L260 | `reports/engine_run_R_disagreements/off/counter_00590.webp` |
| 591 | F1 S/switch unmeasurable/L522 | `reports/engine_run_R_disagreements/off/counter_00591.webp` |
| 592 | F1 S/switch unmeasurable/L522 | `reports/engine_run_R_disagreements/off/counter_00592.webp` |
| 593 | F1 S/switch unmeasurable/L522; F2 S/switch L258/L260 | `reports/engine_run_R_disagreements/off/counter_00593.webp` |
| 594 | F1 S/switch unmeasurable/L522; F2 S/switch unmeasurable/L262 | `reports/engine_run_R_disagreements/off/counter_00594.webp` |
| 595 | F1 S/switch unmeasurable/L522 | `reports/engine_run_R_disagreements/off/counter_00595.webp` |
| 596 | F1 S/switch unmeasurable/L523 | `reports/engine_run_R_disagreements/off/counter_00596.webp` |
| 597 | F2 S/first-full L260/L262; engine decisive comb +1 at placed crops (ratio 0.770) | `reports/engine_run_R_disagreements/off/counter_00597.webp` |
| 598 | F1 S/switch unmeasurable/L523; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00598.webp` |
| 599 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00599.webp` |
| 600 | F1 S/first-full L522/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00600.webp` |
| 601 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00601.webp` |
| 602 | F1 S/first-full L523/L525 | `reports/engine_run_R_disagreements/off/counter_00602.webp` |
| 603 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00603.webp` |
| 605 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00605.webp` |
| 606 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00606.webp` |
| 607 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00607.webp` |
| 608 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00608.webp` |
| 610 | F1 S/first-full L522/L523 | `reports/engine_run_R_disagreements/off/counter_00610.webp` |
| 612 | F1 S/first-full L522/L523 | `reports/engine_run_R_disagreements/off/counter_00612.webp` |
| 616 | F1 S/first-full L522/L523 | `reports/engine_run_R_disagreements/off/counter_00616.webp` |
| 618 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00618.webp` |
| 620 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00620.webp` |
| 621 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00621.webp` |
| 622 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00622.webp` |
| 623 | F1 S/first-full L523/L524; F2 S/first-full L258/L261; F2 S/switch L258/L260 | `reports/engine_run_R_disagreements/off/counter_00623.webp` |
| 624 | F1 S/first-full L521/L524; F1 S/switch L521/L523; F2 S/first-full L259/L261; F2 S/switch L259/L261 | `reports/engine_run_R_disagreements/off/counter_00624.webp` |
| 625 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00625.webp` |
| 626 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00626.webp` |
| 627 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00627.webp` |
| 628 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00628.webp` |
| 629 | F1 S/first-full L521/L524; F1 S/switch L521/L523; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00629.webp` |
| 630 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00630.webp` |
| 632 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00632.webp` |
| 634 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00634.webp` |
| 635 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00635.webp` |
| 636 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00636.webp` |
| 637 | F1 S/first-full L522/L523 | `reports/engine_run_R_disagreements/off/counter_00637.webp` |
| 643 | F1 S/first-full L520/L523; F1 S/switch L520/L523 | `reports/engine_run_R_disagreements/off/counter_00643.webp` |
| 644 | F1 S/first-full L523/L524; F2 S/first-full L259/L261 | `reports/engine_run_R_disagreements/off/counter_00644.webp` |
| 645 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00645.webp` |
| 646 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00646.webp` |
| 648 | F1 S/first-full L522/L523; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00648.webp` |
| 651 | F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00651.webp` |
| 652 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00652.webp` |
| 653 | F1 S/first-full L522/L523 | `reports/engine_run_R_disagreements/off/counter_00653.webp` |
| 655 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00655.webp` |
| 657 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00657.webp` |
| 658 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00658.webp` |
| 659 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00659.webp` |
| 660 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00660.webp` |
| 661 | F1 S/first-full L522/L524 | `reports/engine_run_R_disagreements/off/counter_00661.webp` |
| 662 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00662.webp` |
| 663 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00663.webp` |
| 664 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00664.webp` |
| 665 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00665.webp` |
| 666 | F1 S/first-full L523/L524; F2 S/first-full L259/L261 | `reports/engine_run_R_disagreements/off/counter_00666.webp` |
| 667 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00667.webp` |
| 668 | F1 S/first-full L522/L524 | `reports/engine_run_R_disagreements/off/counter_00668.webp` |
| 669 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00669.webp` |
| 670 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00670.webp` |
| 671 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00671.webp` |
| 672 | F1 S/first-full L522/L524 | `reports/engine_run_R_disagreements/off/counter_00672.webp` |
| 673 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00673.webp` |
| 674 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00674.webp` |
| 675 | F1 S/first-full L522/L524 | `reports/engine_run_R_disagreements/off/counter_00675.webp` |
| 676 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00676.webp` |
| 677 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00677.webp` |
| 678 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00678.webp` |
| 679 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00679.webp` |
| 680 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00680.webp` |
| 681 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00681.webp` |
| 682 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00682.webp` |
| 683 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00683.webp` |
| 684 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00684.webp` |
| 685 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00685.webp` |
| 686 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00686.webp` |
| 687 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00687.webp` |
| 688 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00688.webp` |
| 689 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00689.webp` |
| 691 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00691.webp` |
| 692 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00692.webp` |
| 693 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00693.webp` |
| 694 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00694.webp` |
| 695 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00695.webp` |
| 696 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00696.webp` |
| 697 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00697.webp` |
| 698 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00698.webp` |
| 699 | F1 S/first-full L521/L524; F1 S/switch L521/L523 | `reports/engine_run_R_disagreements/off/counter_00699.webp` |
| 700 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00700.webp` |
| 701 | F1 S/first-full L522/L524; F2 S/first-full L258/L261; F2 S/switch L258/L261 | `reports/engine_run_R_disagreements/off/counter_00701.webp` |
| 702 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00702.webp` |
| 703 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00703.webp` |
| 704 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00704.webp` |
| 705 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00705.webp` |
| 706 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00706.webp` |
| 707 | F2 S/first-full L259/L261 | `reports/engine_run_R_disagreements/off/counter_00707.webp` |
| 708 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00708.webp` |
| 709 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00709.webp` |
| 710 | F1 S/first-full L523/L524; F2 S/first-full L259/L261 | `reports/engine_run_R_disagreements/off/counter_00710.webp` |
| 711 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00711.webp` |
| 712 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00712.webp` |
| 714 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00714.webp` |
| 715 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00715.webp` |
| 716 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00716.webp` |
| 717 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00717.webp` |
| 718 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00718.webp` |
| 719 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00719.webp` |
| 720 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00720.webp` |
| 721 | F1 S/first-full L523/L524; F2 S/first-full L259/L261; F2 S/switch L259/L261 | `reports/engine_run_R_disagreements/off/counter_00721.webp` |
| 722 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00722.webp` |
| 723 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00723.webp` |
| 724 | F1 S/first-full L522/L524 | `reports/engine_run_R_disagreements/off/counter_00724.webp` |
| 725 | F1 S/first-full L522/L524 | `reports/engine_run_R_disagreements/off/counter_00725.webp` |
| 726 | F1 S/first-full L522/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00726.webp` |
| 727 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00727.webp` |
| 728 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00728.webp` |
| 730 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00730.webp` |
| 731 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00731.webp` |
| 732 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00732.webp` |
| 733 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00733.webp` |
| 734 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00734.webp` |
| 735 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00735.webp` |
| 736 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00736.webp` |
| 737 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00737.webp` |
| 738 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00738.webp` |
| 739 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00739.webp` |
| 740 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00740.webp` |
| 741 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00741.webp` |
| 742 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00742.webp` |
| 743 | F1 S/first-full L523/L524; F2 S/first-full L260/L261 | `reports/engine_run_R_disagreements/off/counter_00743.webp` |
| 744 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00744.webp` |
| 745 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00745.webp` |
| 746 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00746.webp` |
| 747 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00747.webp` |
| 748 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00748.webp` |
| 750 | F1 S/first-full L524/L525 | `reports/engine_run_R_disagreements/off/counter_00750.webp` |
| 751 | F1 S/first-full L524/L525 | `reports/engine_run_R_disagreements/off/counter_00751.webp` |
| 753 | F1 S/first-full L524/L525; engine decisive comb +1 at placed crops (ratio 0.600) | `reports/engine_run_R_disagreements/off/counter_00753.webp` |
| 754 | F1 S/first-full L524/L525 | `reports/engine_run_R_disagreements/off/counter_00754.webp` |
| 755 | F1 crop L287/L286 | `reports/engine_run_R_disagreements/off/counter_00755.webp` |
| 756 | F1 crop L287/L286; engine decisive comb -1 at placed crops (ratio 0.460) | `reports/engine_run_R_disagreements/off/counter_00756.webp` |
| 762 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00762.webp` |
| 772 | F1 S/first-full L523/L524 | `reports/engine_run_R_disagreements/off/counter_00772.webp` |

## Picture top

### Engine field 1

Agreement histogram (engine minus reference): +0: 607

No differences.

### Engine field 2

Agreement histogram (engine minus reference): +0: 607

No differences.

## Head-switch row

`S` is scored first against the reference's earliest switch-band row. A difference of one row is the declared partial-predecessor semantic gap. The separate exact check uses the reference's independently measured first-full-other-head row: an internal blanking signature, a persistent three-third step, or a two-sided whole-row time-base step. It remains unmeasurable when none is exposed.

### Engine field 1

S minus reference switch histogram: -3: 2, -2: 8, -1: 46, +0: 397, +1: 119, +2: 4, +3: 1, engine-unmeasurable: 30

Differences beyond the one-row semantic gap:

| engine counter | raw counter/field | S | reference switch | raw tail rows |
|---:|:---:|:---|:---|:---|
| 191 | 191/F2 | L525 | L523 | L522 100.00/39.36 r_next=0.209 MAD_above=13.43 lag=1(13.06/13.43); L523 106.22/46.25 r_next=0.834 MAD_above=39.47 lag=-4(38.03/39.47); L524 104.79/48.49 r_next=0.434 MAD_above=15.46 lag=-1(13.45/15.46); L525 78.55/59.95 r_next=-0.010 MAD_above=45.03 lag=0(45.03/45.03); direct-full=L523 (L523 persistent three-third step; thirds=2.945,3.843,4.876; correlation above/next=0.225/0.874; middle coherence=0.925) |
| 290 | 290/F2 | L521 | L524 | L520 95.46/37.36 r_next=0.921 MAD_above=10.92 lag=0(10.92/10.92); L521 91.85/36.63 r_next=0.890 MAD_above=10.34 lag=0(10.34/10.34); L522 94.22/36.64 r_next=0.904 MAD_above=10.55 lag=1(10.46/10.55); L523 93.94/35.85 r_next=-0.035 MAD_above=9.12 lag=0(9.12/9.12); L524 93.46/31.94 r_next=0.185 MAD_above=36.59 lag=-1(35.94/36.59); L525 68.33/44.20 r_next=-0.009 MAD_above=35.61 lag=-2(34.43/35.61); direct-full=L525 (L525 internal blank x=62-125 Y=1.406; above=119.672 following=82.000; gate=4.000) |
| 325 | 325/F2 | L521 | L523 | L520 115.06/46.72 r_next=0.970 MAD_above=9.56 lag=0(9.56/9.56); L521 114.95/47.53 r_next=0.965 MAD_above=8.13 lag=0(8.13/8.13); L522 115.46/46.59 r_next=-0.187 MAD_above=8.72 lag=0(8.72/8.72); L523 82.30/44.10 r_next=0.285 MAD_above=67.41 lag=-29(58.73/67.41); L524 73.71/56.21 r_next=0.910 MAD_above=42.67 lag=-1(42.47/42.67); direct-full=L524 (L524 internal blank x=71-134 Y=1.359; above=104.250 following=70.500; gate=4.000) |
| 380 | 380/F2 | L525 | L522 | L521 98.63/47.07 r_next=0.845 MAD_above=13.55 lag=0(13.55/13.55); L522 99.25/48.50 r_next=0.853 MAD_above=16.56 lag=0(16.56/16.56); L523 101.21/47.46 r_next=0.833 MAD_above=16.65 lag=0(16.65/16.65); L524 101.26/47.97 r_next=0.955 MAD_above=15.82 lag=0(15.82/15.82); L525 99.80/48.38 r_next=0.037 MAD_above=7.09 lag=-1(3.51/7.09); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.918; no internal horizontal blanking run; gate=4.000) |
| 398 | 398/F2 | L524 | L522 | L521 98.64/48.80 r_next=0.839 MAD_above=14.27 lag=0(14.27/14.27); L522 100.63/47.75 r_next=0.857 MAD_above=16.88 lag=0(16.88/16.88); L523 101.61/48.91 r_next=0.952 MAD_above=17.28 lag=0(17.28/17.28); L524 103.07/53.23 r_next=0.998 MAD_above=8.89 lag=0(8.89/8.89); L525 102.48/53.58 r_next=0.008 MAD_above=2.39 lag=0(2.39/2.39); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.918; no internal horizontal blanking run; gate=4.000) |
| 399 | 399/F2 | L523 | L525 | L522 104.78/47.99 r_next=0.977 MAD_above=18.11 lag=0(18.11/18.11); L523 103.04/48.54 r_next=0.969 MAD_above=6.59 lag=0(6.59/6.59); L524 103.15/48.38 r_next=0.727 MAD_above=8.30 lag=-2(3.59/8.30); L525 91.89/53.49 r_next=0.006 MAD_above=17.48 lag=-2(13.68/17.48); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.919; no internal horizontal blanking run; gate=4.000) |
| 437 | 437/F2 | L521 | L523 | L520 99.14/48.02 r_next=0.831 MAD_above=14.75 lag=1(14.44/14.75); L521 100.58/47.67 r_next=0.869 MAD_above=16.74 lag=1(16.73/16.74); L522 104.65/45.29 r_next=-0.036 MAD_above=16.85 lag=-1(16.79/16.85); L523 90.42/63.29 r_next=0.826 MAD_above=69.08 lag=31(66.66/69.08); L524 88.57/63.16 r_next=0.874 MAD_above=23.11 lag=-3(21.34/23.11); direct-full=L523 (L523 persistent three-third step; thirds=8.371,4.230,4.094; correlation above/next=-0.115/0.893; middle coherence=0.920) |
| 449 | 449/F2 | L521 | L523 | L520 98.56/47.33 r_next=0.820 MAD_above=13.49 lag=0(13.49/13.49); L521 103.18/48.88 r_next=0.854 MAD_above=17.36 lag=1(17.23/17.36); L522 104.50/45.26 r_next=0.068 MAD_above=17.18 lag=0(17.18/17.18); L523 110.01/51.60 r_next=0.553 MAD_above=54.66 lag=22(53.28/54.66); L524 88.32/62.25 r_next=0.874 MAD_above=40.12 lag=-3(36.49/40.12); direct-full=L524 (L524 internal blank x=59-122 Y=1.375; above=126.422 following=117.000; gate=4.000) |
| 574 | 574/F2 | L525 | L523 | L522 111.84/53.36 r_next=0.610 MAD_above=7.96 lag=0(7.96/7.96); L523 88.13/47.59 r_next=0.521 MAD_above=33.08 lag=0(33.08/33.08); L524 82.49/47.41 r_next=0.742 MAD_above=33.04 lag=-2(31.73/33.04); L525 78.40/59.83 r_next=0.019 MAD_above=25.08 lag=-2(24.28/25.08); direct-full=L524 (L524 internal blank x=115-178 Y=3.109; above=91.562 following=89.000; gate=4.000) |
| 581 | 581/F2 | L525 | L523 | L522 107.64/56.03 r_next=0.805 MAD_above=9.87 lag=1(9.78/9.87); L523 117.94/46.38 r_next=0.791 MAD_above=18.44 lag=1(18.15/18.44); L524 107.07/38.25 r_next=0.287 MAD_above=13.48 lag=0(13.48/13.48); L525 88.84/41.12 r_next=0.018 MAD_above=30.47 lag=-3(24.50/30.47); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.940; no internal horizontal blanking run; gate=4.000) |
| 589 | 589/F2 | L521 | L523 | L520 113.54/55.20 r_next=0.963 MAD_above=10.20 lag=0(10.20/10.20); L521 114.20/54.48 r_next=0.975 MAD_above=9.71 lag=0(9.71/9.71); L522 115.62/54.76 r_next=0.947 MAD_above=8.52 lag=0(8.52/8.52); L523 118.21/53.35 r_next=0.999 MAD_above=7.36 lag=0(7.36/7.36); L524 118.32/53.49 r_next=0.999 MAD_above=1.75 lag=0(1.75/1.75); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.939; no internal horizontal blanking run; gate=4.000) |
| 624 | 624/F2 | L521 | L523 | L520 92.05/53.66 r_next=0.973 MAD_above=9.35 lag=1(9.18/9.35); L521 94.10/54.47 r_next=0.971 MAD_above=8.85 lag=0(8.85/8.85); L522 96.72/54.25 r_next=0.442 MAD_above=9.51 lag=0(9.51/9.51); L523 70.27/39.52 r_next=0.199 MAD_above=37.68 lag=17(36.03/37.68); L524 62.92/49.60 r_next=0.935 MAD_above=45.23 lag=0(45.23/45.23); direct-full=L524 (L524 internal blank x=65-128 Y=1.359; above=99.078 following=84.000; gate=4.000) |
| 629 | 629/F2 | L521 | L523 | L520 92.97/53.88 r_next=0.975 MAD_above=8.94 lag=0(8.94/8.94); L521 94.06/53.76 r_next=0.978 MAD_above=8.33 lag=1(8.06/8.33); L522 93.81/53.79 r_next=0.274 MAD_above=7.74 lag=0(7.74/7.74); L523 70.53/42.55 r_next=0.247 MAD_above=42.64 lag=6(41.90/42.64); L524 62.73/51.34 r_next=0.920 MAD_above=45.53 lag=-2(45.03/45.53); direct-full=L524 (L524 internal blank x=60-123 Y=1.359; above=93.141 following=84.000; gate=4.000) |
| 643 | 643/F2 | L520 | L523 | L519 89.99/56.62 r_next=0.947 MAD_above=9.91 lag=0(9.91/9.91); L520 90.75/56.07 r_next=0.944 MAD_above=11.50 lag=-1(11.23/11.50); L521 96.24/55.67 r_next=0.962 MAD_above=11.56 lag=0(11.56/11.56); L522 100.46/55.83 r_next=0.135 MAD_above=9.66 lag=0(9.66/9.66); L523 72.67/46.19 r_next=0.766 MAD_above=59.73 lag=18(57.30/59.73); L524 64.55/51.21 r_next=0.950 MAD_above=20.91 lag=-2(19.81/20.91); direct-full=L523 (L523 persistent three-third step; thirds=8.184,4.275,6.936; correlation above/next=0.132/0.771; middle coherence=0.909) |
| 699 | 699/F2 | L521 | L523 | L520 118.52/43.07 r_next=0.913 MAD_above=11.38 lag=1(10.82/11.38); L521 118.50/43.31 r_next=0.909 MAD_above=10.55 lag=1(10.14/10.55); L522 120.15/41.19 r_next=-0.044 MAD_above=9.83 lag=1(9.23/9.83); L523 119.21/49.00 r_next=0.152 MAD_above=53.29 lag=25(48.67/53.29); L524 87.23/60.23 r_next=0.897 MAD_above=50.73 lag=-1(50.66/50.73); direct-full=L524 (L524 internal blank x=58-121 Y=1.359; above=166.719 following=118.000; gate=4.000) |

First-full-other-head histogram (engine S minus reference): -4: 1, -3: 6, -2: 36, -1: 319, +0: 200, +1: 2, +2: 1, both-unmeasurable: 27, engine-unmeasurable: 3, reference-unmeasurable: 12

- +1: counters 435, 574.  Witnesses: counter 435: engine L524, direct L523; L523 internal blank x=71-134 Y=1.641; above=119.625 following=85.000; gate=4.000 / counter 574: engine L525, direct L524; L524 internal blank x=115-178 Y=3.109; above=91.562 following=89.000; gate=4.000

- +2: counters 191.  Witnesses: counter 191: engine L525, direct L523; L523 persistent three-third step; thirds=2.945,3.843,4.876; correlation above/next=0.225/0.874; middle coherence=0.925

- -1: counters 171, 179, 181, 185-186, 188, 190, 192, 199, 204, 208, 211-213, 216, 218, 232, 234, 236-237, 239-242, 245-246, 249, 252, 254-255, 272-273, 275-289, 293-298, 300, 303-323, 326-333, 335, 337-345, 347-349, 351, 353, 355-357, 359, 361, 363-365, 368-369, 372-376, 395, 402, 405, 409, 411-413, 415, 419, 422, 424-427, 431, 444-445, 447-448, 450-451, 453-454, 456, 458-462, 464-465, 467-474, 476-479, 485-486, 488-490, 492, 494, 496, 501, 503-504, 509, 511, 513-516, 518, 521-522, 526-536, 539-542, 544-548, 550, 554, 556-557, 559, 562-563, 565, 568, 570, 575, 578-579, 599, 603, 605, 607-608, 610, 612, 616, 620-623, 625-626, 630, 635-637, 644-646, 648, 652-653, 655, 657-660, 662-667, 669-671, 673-674, 676-689, 691-698, 700, 702-706, 708-712, 714-723, 727-728, 730-748, 750-751, 753-754, 762, 772.  Witnesses: counter 171: engine L523, direct L524; L524 internal blank x=51-114 Y=1.344; above=168.094 following=97.000; gate=4.000 / counter 179: engine L523, direct L524; L524 internal blank x=68-131 Y=1.359; above=139.375 following=81.500; gate=4.000 / counter 181: engine L523, direct L524; L524 internal blank x=66-129 Y=1.359; above=139.797 following=87.000; gate=4.000

- -2: counters 173, 203, 253, 256, 301-302, 324, 334, 336, 346, 350, 352, 360, 362, 370, 408, 428, 437, 452, 455, 549, 551-552, 566, 571-572, 600, 602, 661, 668, 672, 675, 701, 724-726.  Witnesses: counter 173: engine L523, direct L525; L525 internal blank x=63-126 Y=1.453; above=143.641 following=84.000; gate=4.000 / counter 203: engine L522, direct L524; L524 internal blank x=63-126 Y=1.328; above=134.203 following=81.000; gate=4.000 / counter 253: engine L522, direct L524; L524 internal blank x=61-124 Y=1.359; above=129.016 following=76.000; gate=4.000

- -3: counters 325, 449, 624, 629, 643, 699.  Witnesses: counter 325: engine L521, direct L524; L524 internal blank x=71-134 Y=1.359; above=104.250 following=70.500; gate=4.000 / counter 449: engine L521, direct L524; L524 internal blank x=59-122 Y=1.375; above=126.422 following=117.000; gate=4.000 / counter 624: engine L521, direct L524; L524 internal blank x=65-128 Y=1.359; above=99.078 following=84.000; gate=4.000

- -4: counters 290.  Witnesses: counter 290: engine L521, direct L525; L525 internal blank x=62-125 Y=1.406; above=119.672 following=82.000; gate=4.000

- engine-unmeasurable: counters 176, 396-397.  Witnesses: counter 176: engine unmeasurable, direct L523; L523 persistent three-third step; thirds=2.844,3.467,5.121; correlation above/next=0.278/0.802; middle coherence=0.918 / counter 396: engine unmeasurable, direct L524; L524 internal blank x=143-206 Y=3.797; above=149.953 following=83.000; gate=4.000 / counter 397: engine unmeasurable, direct L524; L524 internal blank x=141-204 Y=3.656; above=146.734 following=83.000; gate=4.000

- reference-unmeasurable: counters 172, 174, 380, 382, 384, 394, 398-399, 581, 584, 589, 597.  Witnesses: counter 172: engine L523, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.916; no internal horizontal blanking run; gate=4.000 / counter 174: engine L525, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.919; no internal horizontal blanking run; gate=4.000 / counter 380: engine L525, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.918; no internal horizontal blanking run; gate=4.000

Every numeric first-full disagreement:

| engine counter | raw counter/field | engine S | reference first-full | raw tail rows |
|---:|:---:|:---|:---|:---|
| 171 | 171/F2 | L523 | L524 | L522 101.00/40.42 r_next=0.367 MAD_above=13.36 lag=1(13.20/13.36); L523 117.54/48.17 r_next=0.320 MAD_above=36.87 lag=-6(36.21/36.87); L524 84.02/57.79 r_next=0.967 MAD_above=46.88 lag=-1(46.59/46.88); L525 85.31/59.01 r_next=0.040 MAD_above=8.02 lag=0(8.02/8.02); direct-full=L524 (L524 internal blank x=51-114 Y=1.344; above=168.094 following=97.000; gate=4.000) |
| 173 | 173/F2 | L523 | L525 | L522 101.92/40.59 r_next=0.495 MAD_above=13.67 lag=1(13.49/13.67); L523 101.72/46.18 r_next=0.812 MAD_above=27.46 lag=-1(27.45/27.46); L524 103.10/47.68 r_next=0.371 MAD_above=19.37 lag=0(19.37/19.37); L525 79.24/58.87 r_next=-0.021 MAD_above=44.04 lag=1(43.97/44.04); direct-full=L525 (L525 internal blank x=63-126 Y=1.453; above=143.641 following=84.000; gate=4.000) |
| 179 | 179/F2 | L523 | L524 | L522 97.40/40.64 r_next=0.250 MAD_above=12.97 lag=0(12.97/12.97); L523 106.95/46.26 r_next=0.360 MAD_above=39.13 lag=-2(38.63/39.13); L524 74.82/54.60 r_next=0.885 MAD_above=45.31 lag=-4(42.48/45.31); L525 75.00/55.43 r_next=-0.020 MAD_above=16.77 lag=-3(10.78/16.77); direct-full=L524 (L524 internal blank x=68-131 Y=1.359; above=139.375 following=81.500; gate=4.000) |
| 181 | 181/F2 | L523 | L524 | L522 96.66/40.98 r_next=0.275 MAD_above=13.98 lag=1(13.42/13.98); L523 102.55/41.42 r_next=0.255 MAD_above=37.21 lag=-6(36.14/37.21); L524 76.85/56.48 r_next=0.912 MAD_above=45.75 lag=-3(44.81/45.75); L525 77.28/57.47 r_next=-0.004 MAD_above=15.70 lag=1(15.56/15.70); direct-full=L524 (L524 internal blank x=66-129 Y=1.359; above=139.797 following=87.000; gate=4.000) |
| 185 | 185/F2 | L523 | L524 | L522 99.26/41.05 r_next=0.291 MAD_above=13.46 lag=1(12.81/13.46); L523 99.47/42.30 r_next=0.155 MAD_above=37.42 lag=-5(34.53/37.42); L524 78.58/56.18 r_next=0.875 MAD_above=47.97 lag=-3(46.22/47.97); L525 79.48/58.17 r_next=-0.023 MAD_above=19.05 lag=-2(17.94/19.05); direct-full=L524 (L524 internal blank x=48-111 Y=1.297; above=166.031 following=86.000; gate=4.000) |
| 186 | 186/F2 | L523 | L524 | L522 101.29/40.01 r_next=0.285 MAD_above=13.26 lag=0(13.26/13.26); L523 106.56/42.86 r_next=0.323 MAD_above=36.90 lag=-6(35.55/36.90); L524 76.95/54.32 r_next=0.897 MAD_above=43.04 lag=-1(42.56/43.04); L525 80.30/58.33 r_next=0.014 MAD_above=18.70 lag=0(18.70/18.70); direct-full=L524 (L524 internal blank x=60-123 Y=1.328; above=150.875 following=85.000; gate=4.000) |
| 188 | 188/F2 | L523 | L524 | L522 100.56/39.83 r_next=0.258 MAD_above=13.71 lag=1(13.07/13.71); L523 105.90/45.25 r_next=0.416 MAD_above=39.85 lag=-7(37.51/39.85); L524 74.55/51.82 r_next=0.905 MAD_above=37.93 lag=-1(37.68/37.93); L525 79.34/56.79 r_next=0.003 MAD_above=17.39 lag=0(17.39/17.39); direct-full=L524 (L524 internal blank x=66-129 Y=1.375; above=137.453 following=83.500; gate=4.000) |
| 190 | 190/F2 | L523 | L524 | L522 98.47/38.76 r_next=0.244 MAD_above=12.02 lag=0(12.02/12.02); L523 108.06/45.78 r_next=0.350 MAD_above=39.30 lag=-4(38.36/39.30); L524 73.84/52.04 r_next=0.915 MAD_above=43.38 lag=-1(43.13/43.38); L525 75.70/56.44 r_next=0.030 MAD_above=14.69 lag=0(14.69/14.69); direct-full=L524 (L524 internal blank x=63-126 Y=1.328; above=140.422 following=82.000; gate=4.000) |
| 191 | 191/F2 | L525 | L523 | L522 100.00/39.36 r_next=0.209 MAD_above=13.43 lag=1(13.06/13.43); L523 106.22/46.25 r_next=0.834 MAD_above=39.47 lag=-4(38.03/39.47); L524 104.79/48.49 r_next=0.434 MAD_above=15.46 lag=-1(13.45/15.46); L525 78.55/59.95 r_next=-0.010 MAD_above=45.03 lag=0(45.03/45.03); direct-full=L523 (L523 persistent three-third step; thirds=2.945,3.843,4.876; correlation above/next=0.225/0.874; middle coherence=0.925) |
| 192 | 192/F2 | L523 | L524 | L522 97.60/39.31 r_next=0.319 MAD_above=13.69 lag=0(13.69/13.69); L523 100.16/39.63 r_next=0.256 MAD_above=34.99 lag=-4(33.22/34.99); L524 73.43/54.97 r_next=0.896 MAD_above=45.53 lag=-2(44.37/45.53); L525 74.21/57.17 r_next=-0.006 MAD_above=17.78 lag=0(17.78/17.78); direct-full=L524 (L524 internal blank x=58-121 Y=1.375; above=149.109 following=83.000; gate=4.000) |
| 199 | 199/F2 | L523 | L524 | L522 94.82/39.26 r_next=0.167 MAD_above=12.89 lag=0(12.89/12.89); L523 102.35/46.37 r_next=0.340 MAD_above=43.42 lag=-7(40.28/43.42); L524 70.63/53.34 r_next=0.904 MAD_above=45.51 lag=-2(43.76/45.51); L525 73.41/56.26 r_next=0.038 MAD_above=16.79 lag=-1(16.28/16.79); direct-full=L524 (L524 internal blank x=72-135 Y=1.359; above=124.156 following=77.000; gate=4.000) |
| 203 | 203/F2 | L522 | L524 | L521 96.95/39.40 r_next=0.880 MAD_above=12.48 lag=0(12.48/12.48); L522 95.01/39.09 r_next=0.284 MAD_above=12.75 lag=1(12.71/12.75); L523 96.99/46.72 r_next=0.412 MAD_above=39.66 lag=-5(37.81/39.66); L524 71.15/51.76 r_next=0.919 MAD_above=38.21 lag=-1(37.79/38.21); L525 74.43/54.12 r_next=0.013 MAD_above=15.46 lag=0(15.46/15.46); direct-full=L524 (L524 internal blank x=63-126 Y=1.328; above=134.203 following=81.000; gate=4.000) |
| 204 | 204/F2 | L523 | L524 | L522 93.30/39.41 r_next=0.197 MAD_above=13.32 lag=1(13.20/13.32); L523 100.89/42.87 r_next=0.329 MAD_above=39.31 lag=-3(38.13/39.31); L524 70.49/53.09 r_next=0.919 MAD_above=41.88 lag=-1(41.52/41.88); L525 73.26/53.99 r_next=0.021 MAD_above=14.85 lag=0(14.85/14.85); direct-full=L524 (L524 internal blank x=54-117 Y=1.328; above=147.719 following=79.000; gate=4.000) |
| 208 | 208/F2 | L523 | L524 | L522 94.13/39.66 r_next=0.208 MAD_above=13.90 lag=0(13.90/13.90); L523 101.85/44.75 r_next=0.321 MAD_above=41.24 lag=-3(39.68/41.24); L524 72.37/52.86 r_next=0.907 MAD_above=43.67 lag=-2(43.37/43.67); L525 75.07/55.43 r_next=0.004 MAD_above=15.98 lag=1(15.88/15.98); direct-full=L524 (L524 internal blank x=57-120 Y=1.375; above=144.422 following=80.000; gate=4.000) |
| 211 | 211/F2 | L523 | L524 | L522 94.01/39.14 r_next=0.278 MAD_above=14.03 lag=1(13.93/14.03); L523 96.44/45.77 r_next=0.398 MAD_above=40.64 lag=-7(37.67/40.64); L524 70.35/50.23 r_next=0.912 MAD_above=38.18 lag=-2(36.78/38.18); L525 73.52/54.47 r_next=-0.037 MAD_above=15.39 lag=-1(15.13/15.39); direct-full=L524 (L524 internal blank x=53-116 Y=1.344; above=149.344 following=80.000; gate=4.000) |
| 212 | 212/F2 | L523 | L524 | L522 92.92/38.41 r_next=0.275 MAD_above=14.39 lag=1(14.05/14.39); L523 94.11/48.67 r_next=0.449 MAD_above=42.37 lag=19(41.34/42.37); L524 69.62/51.64 r_next=0.911 MAD_above=35.62 lag=-1(35.44/35.62); L525 74.11/53.73 r_next=-0.023 MAD_above=14.75 lag=0(14.75/14.75); direct-full=L524 (L524 internal blank x=74-137 Y=1.344; above=122.641 following=79.000; gate=4.000) |
| 213 | 213/F2 | L523 | L524 | L522 92.17/39.52 r_next=0.242 MAD_above=13.16 lag=0(13.16/13.16); L523 95.52/47.51 r_next=0.403 MAD_above=42.02 lag=-4(40.01/42.02); L524 69.24/50.59 r_next=0.912 MAD_above=38.09 lag=-2(37.42/38.09); L525 71.81/54.95 r_next=-0.018 MAD_above=15.82 lag=-1(15.13/15.82); direct-full=L524 (L524 internal blank x=50-113 Y=1.375; above=155.922 following=77.500; gate=4.000) |
| 216 | 216/F2 | L523 | L524 | L522 90.72/39.49 r_next=0.214 MAD_above=14.32 lag=1(13.72/14.32); L523 97.59/43.98 r_next=0.323 MAD_above=40.60 lag=-5(38.78/40.60); L524 67.57/50.58 r_next=0.911 MAD_above=41.12 lag=-2(40.19/41.12); L525 71.69/52.75 r_next=0.006 MAD_above=14.50 lag=-1(14.38/14.50); direct-full=L524 (L524 internal blank x=61-124 Y=1.344; above=133.219 following=75.000; gate=4.000) |
| 218 | 218/F2 | L523 | L524 | L522 93.85/38.57 r_next=0.294 MAD_above=12.84 lag=1(12.59/12.84); L523 90.57/42.41 r_next=0.164 MAD_above=36.55 lag=-9(33.52/36.55); L524 71.06/50.35 r_next=0.910 MAD_above=43.26 lag=-3(40.91/43.26); L525 72.18/54.80 r_next=0.017 MAD_above=14.90 lag=0(14.90/14.90); direct-full=L524 (L524 internal blank x=64-127 Y=1.344; above=137.266 following=78.000; gate=4.000) |
| 232 | 232/F2 | L523 | L524 | L522 75.27/37.33 r_next=0.305 MAD_above=8.05 lag=0(8.05/8.05); L523 71.28/31.56 r_next=-0.080 MAD_above=29.55 lag=1(29.51/29.55); L524 57.26/42.47 r_next=0.952 MAD_above=42.23 lag=2(42.13/42.23); L525 64.26/45.71 r_next=0.034 MAD_above=11.87 lag=0(11.87/11.87); direct-full=L524 (L524 internal blank x=54-117 Y=1.375; above=121.172 following=66.000; gate=4.000) |
| 234 | 234/F2 | L523 | L524 | L522 78.15/37.68 r_next=0.171 MAD_above=8.72 lag=0(8.72/8.72); L523 78.15/31.99 r_next=0.046 MAD_above=32.78 lag=1(32.76/32.78); L524 59.47/43.01 r_next=0.936 MAD_above=38.07 lag=-3(37.22/38.07); L525 62.87/47.18 r_next=0.023 MAD_above=12.15 lag=-1(11.72/12.15); direct-full=L524 (L524 internal blank x=65-128 Y=1.297; above=122.609 following=70.000; gate=4.000) |
| 236 | 236/F2 | L524 | L525 | L523 79.64/37.03 r_next=0.140 MAD_above=8.33 lag=0(8.33/8.33); L524 78.46/30.88 r_next=0.097 MAD_above=31.79 lag=0(31.79/31.79); L525 58.54/43.60 r_next=0.012 MAD_above=37.77 lag=-4(37.40/37.77); direct-full=L525 (L525 internal blank x=63-126 Y=1.391; above=123.969 following=69.000; gate=4.000) |
| 237 | 237/F2 | L523 | L524 | L522 80.58/38.03 r_next=0.084 MAD_above=8.95 lag=1(8.16/8.95); L523 79.79/31.98 r_next=0.170 MAD_above=34.67 lag=-1(34.61/34.67); L524 60.31/42.58 r_next=0.930 MAD_above=34.99 lag=-3(33.98/34.99); L525 63.33/47.21 r_next=-0.010 MAD_above=12.60 lag=-1(12.32/12.60); direct-full=L524 (L524 internal blank x=52-115 Y=1.328; above=120.766 following=71.000; gate=4.000) |
| 239 | 239/F2 | L524 | L525 | L523 83.96/38.33 r_next=0.152 MAD_above=9.04 lag=1(8.74/9.04); L524 81.12/33.65 r_next=0.092 MAD_above=33.34 lag=1(33.18/33.34); L525 63.12/45.26 r_next=0.025 MAD_above=38.87 lag=0(38.87/38.87); direct-full=L525 (L525 internal blank x=86-149 Y=1.359; above=117.516 following=75.000; gate=4.000) |
| 240 | 240/F2 | L523 | L524 | L522 82.05/37.25 r_next=0.061 MAD_above=8.01 lag=0(8.01/8.01); L523 84.90/33.31 r_next=0.213 MAD_above=35.69 lag=-1(35.66/35.69); L524 62.34/45.10 r_next=0.948 MAD_above=36.24 lag=-2(35.75/36.24); L525 64.66/46.63 r_next=0.021 MAD_above=11.15 lag=-1(10.95/11.15); direct-full=L524 (L524 internal blank x=60-123 Y=1.359; above=127.906 following=75.000; gate=4.000) |
| 241 | 241/F2 | L523 | L524 | L522 83.75/37.74 r_next=0.050 MAD_above=8.50 lag=0(8.50/8.50); L523 85.52/34.24 r_next=0.249 MAD_above=36.73 lag=30(36.56/36.73); L524 62.77/44.68 r_next=0.947 MAD_above=34.62 lag=1(34.62/34.62); L525 68.91/49.04 r_next=0.027 MAD_above=12.57 lag=0(12.57/12.57); direct-full=L524 (L524 internal blank x=66-129 Y=1.375; above=127.156 following=74.000; gate=4.000) |
| 242 | 242/F2 | L523 | L524 | L522 86.03/36.96 r_next=0.040 MAD_above=9.06 lag=0(9.06/9.06); L523 87.63/35.35 r_next=0.236 MAD_above=37.50 lag=0(37.50/37.50); L524 63.48/45.22 r_next=0.950 MAD_above=35.13 lag=0(35.13/35.13); L525 66.66/47.48 r_next=-0.017 MAD_above=11.09 lag=-1(10.92/11.09); direct-full=L524 (L524 internal blank x=59-122 Y=1.359; above=131.922 following=74.000; gate=4.000) |
| 245 | 245/F2 | L523 | L524 | L522 83.44/37.28 r_next=0.947 MAD_above=8.51 lag=0(8.51/8.51); L523 84.09/36.43 r_next=-0.306 MAD_above=9.40 lag=2(8.26/9.40); L524 61.77/43.08 r_next=0.945 MAD_above=58.17 lag=28(55.45/58.17); L525 66.11/46.49 r_next=0.003 MAD_above=11.63 lag=-2(10.55/11.63); direct-full=L524 (L524 persistent three-third step; thirds=12.313,3.399,4.860; correlation above/next=-0.450/0.969; middle coherence=0.879) |
| 246 | 246/F2 | L523 | L524 | L522 83.93/36.82 r_next=0.575 MAD_above=7.83 lag=0(7.83/7.83); L523 79.47/28.75 r_next=-0.465 MAD_above=19.31 lag=-2(18.06/19.31); L524 62.38/44.20 r_next=0.955 MAD_above=52.35 lag=28(51.29/52.35); L525 66.15/45.42 r_next=0.010 MAD_above=10.57 lag=-1(10.37/10.57); direct-full=L524 (L524 persistent three-third step; thirds=12.856,3.240,2.815; correlation above/next=-0.662/0.970; middle coherence=0.884) |
| 249 | 249/F2 | L523 | L524 | L522 86.91/35.95 r_next=0.499 MAD_above=8.65 lag=0(8.65/8.65); L523 72.58/34.13 r_next=-0.331 MAD_above=24.84 lag=-1(24.70/24.84); L524 63.87/43.67 r_next=0.952 MAD_above=49.45 lag=-2(48.91/49.45); L525 66.29/47.32 r_next=-0.013 MAD_above=10.57 lag=0(10.57/10.57); direct-full=L524 (L524 internal blank x=48-111 Y=1.359; above=127.422 following=76.000; gate=4.000) |
| 252 | 252/F2 | L523 | L524 | L522 86.07/37.01 r_next=0.232 MAD_above=8.27 lag=0(8.27/8.27); L523 83.16/31.18 r_next=-0.074 MAD_above=30.57 lag=0(30.57/30.57); L524 63.02/44.35 r_next=0.957 MAD_above=42.20 lag=1(42.16/42.20); L525 68.38/47.86 r_next=0.013 MAD_above=11.15 lag=0(11.15/11.15); direct-full=L524 (L524 internal blank x=68-131 Y=1.359; above=130.391 following=77.000; gate=4.000) |
| 253 | 253/F2 | L522 | L524 | L521 85.84/37.23 r_next=0.944 MAD_above=8.31 lag=0(8.31/8.31); L522 88.72/36.74 r_next=0.047 MAD_above=8.70 lag=0(8.70/8.70); L523 86.40/36.59 r_next=0.165 MAD_above=35.81 lag=-2(35.55/35.81); L524 64.10/44.43 r_next=0.954 MAD_above=38.56 lag=-2(37.83/38.56); L525 65.94/46.68 r_next=-0.002 MAD_above=10.38 lag=-1(10.35/10.38); direct-full=L524 (L524 internal blank x=61-124 Y=1.359; above=129.016 following=76.000; gate=4.000) |
| 254 | 254/F2 | L523 | L524 | L522 86.88/37.68 r_next=0.071 MAD_above=8.46 lag=0(8.46/8.46); L523 87.00/32.69 r_next=0.057 MAD_above=34.52 lag=-1(34.49/34.52); L524 64.98/44.45 r_next=0.955 MAD_above=37.12 lag=0(37.12/37.12); L525 68.48/47.83 r_next=-0.015 MAD_above=11.25 lag=-1(11.18/11.25); direct-full=L524 (L524 internal blank x=51-114 Y=1.344; above=130.625 following=78.000; gate=4.000) |
| 255 | 255/F2 | L523 | L524 | L522 90.50/36.48 r_next=-0.005 MAD_above=9.15 lag=0(9.15/9.15); L523 90.79/35.67 r_next=0.199 MAD_above=38.73 lag=32(38.49/38.73); L524 64.90/44.14 r_next=0.959 MAD_above=37.58 lag=-2(37.03/37.58); L525 66.80/47.37 r_next=0.009 MAD_above=10.05 lag=-1(9.83/10.05); direct-full=L524 (L524 internal blank x=62-125 Y=1.375; above=132.141 following=79.000; gate=4.000) |
| 256 | 256/F2 | L522 | L524 | L521 89.62/38.34 r_next=0.933 MAD_above=8.99 lag=0(8.99/8.99); L522 87.22/37.46 r_next=-0.004 MAD_above=9.31 lag=0(9.31/9.31); L523 92.44/32.81 r_next=0.189 MAD_above=37.09 lag=0(37.09/37.09); L524 65.14/45.13 r_next=0.953 MAD_above=36.68 lag=-2(36.20/36.68); L525 69.29/49.35 r_next=0.017 MAD_above=11.68 lag=-1(11.45/11.68); direct-full=L524 (L524 internal blank x=64-127 Y=1.406; above=130.969 following=75.000; gate=4.000) |
| 272 | 272/F2 | L524 | L525 | L523 93.62/37.89 r_next=-0.086 MAD_above=8.56 lag=0(8.56/8.56); L524 80.10/43.25 r_next=0.558 MAD_above=49.07 lag=-7(48.70/49.07); L525 67.46/47.86 r_next=-0.006 MAD_above=26.05 lag=-2(24.96/26.05); direct-full=L525 (L525 internal blank x=71-134 Y=1.375; above=91.375 following=80.000; gate=4.000) |
| 273 | 273/F2 | L524 | L525 | L523 92.91/37.35 r_next=-0.069 MAD_above=8.58 lag=-1(8.28/8.58); L524 81.08/45.48 r_next=0.535 MAD_above=49.43 lag=-18(49.28/49.43); L525 68.34/46.29 r_next=-0.010 MAD_above=28.15 lag=-4(25.27/28.15); direct-full=L525 (L525 internal blank x=54-117 Y=1.391; above=128.578 following=82.000; gate=4.000) |
| 275 | 275/F2 | L523 | L524 | L522 92.70/37.43 r_next=-0.021 MAD_above=8.02 lag=0(8.02/8.02); L523 79.59/42.49 r_next=0.506 MAD_above=46.39 lag=-1(46.31/46.39); L524 67.10/47.24 r_next=0.922 MAD_above=27.57 lag=-3(25.91/27.57); L525 69.45/49.64 r_next=0.015 MAD_above=14.29 lag=0(14.29/14.29); direct-full=L524 (L524 internal blank x=69-132 Y=1.406; above=103.703 following=82.000; gate=4.000) |
| 276 | 276/F2 | L523 | L524 | L522 95.61/37.16 r_next=-0.039 MAD_above=9.30 lag=0(9.30/9.30); L523 81.84/43.93 r_next=0.526 MAD_above=48.57 lag=-7(47.42/48.57); L524 64.90/45.47 r_next=0.917 MAD_above=27.62 lag=-2(26.42/27.62); L525 72.99/51.86 r_next=0.003 MAD_above=15.72 lag=-2(15.12/15.72); direct-full=L524 (L524 internal blank x=71-134 Y=1.344; above=97.422 following=76.000; gate=4.000) |
| 277 | 277/F2 | L523 | L524 | L522 93.68/38.35 r_next=-0.102 MAD_above=9.08 lag=0(9.08/9.08); L523 80.37/44.10 r_next=0.507 MAD_above=50.65 lag=-21(49.63/50.65); L524 69.17/49.45 r_next=0.923 MAD_above=29.31 lag=-3(27.35/29.31); L525 72.48/50.88 r_next=0.028 MAD_above=15.31 lag=-1(15.24/15.31); direct-full=L524 (L524 internal blank x=64-127 Y=1.359; above=106.906 following=85.500; gate=4.000) |
| 278 | 278/F2 | L524 | L525 | L523 93.56/37.28 r_next=-0.073 MAD_above=9.20 lag=1(9.16/9.20); L524 82.56/42.16 r_next=0.513 MAD_above=47.67 lag=-21(46.48/47.67); L525 67.83/46.60 r_next=-0.011 MAD_above=26.22 lag=-2(25.00/26.22); direct-full=L525 (L525 internal blank x=68-131 Y=1.375; above=112.203 following=81.000; gate=4.000) |
| 279 | 279/F2 | L524 | L525 | L523 92.79/38.92 r_next=0.061 MAD_above=8.67 lag=0(8.67/8.67); L524 83.88/39.89 r_next=0.312 MAD_above=41.40 lag=5(40.97/41.40); L525 67.70/46.32 r_next=0.044 MAD_above=32.24 lag=-2(31.05/32.24); direct-full=L525 (L525 internal blank x=68-131 Y=1.344; above=138.797 following=82.000; gate=4.000) |
| 280 | 280/F2 | L524 | L525 | L523 91.92/36.50 r_next=0.021 MAD_above=7.78 lag=0(7.78/7.78); L524 85.07/40.35 r_next=0.334 MAD_above=42.96 lag=31(41.72/42.96); L525 67.27/46.11 r_next=0.009 MAD_above=32.35 lag=-2(30.65/32.35); direct-full=L525 (L525 internal blank x=53-116 Y=1.344; above=132.109 following=81.000; gate=4.000) |
| 281 | 281/F2 | L524 | L525 | L523 91.94/37.66 r_next=-0.010 MAD_above=8.28 lag=0(8.28/8.28); L524 82.67/43.37 r_next=0.470 MAD_above=45.70 lag=-2(45.57/45.70); L525 69.82/47.31 r_next=0.021 MAD_above=28.14 lag=-2(27.20/28.14); direct-full=L525 (L525 internal blank x=63-126 Y=1.344; above=134.219 following=85.500; gate=4.000) |
| 282 | 282/F2 | L524 | L525 | L523 92.07/37.13 r_next=0.031 MAD_above=8.00 lag=0(8.00/8.00); L524 88.29/36.30 r_next=0.331 MAD_above=38.88 lag=-1(38.80/38.88); L525 66.90/46.29 r_next=-0.015 MAD_above=32.55 lag=-2(31.87/32.55); direct-full=L525 (L525 internal blank x=65-128 Y=1.359; above=134.859 following=77.500; gate=4.000) |
| 283 | 283/F2 | L524 | L525 | L523 93.19/37.43 r_next=0.059 MAD_above=8.15 lag=0(8.15/8.15); L524 89.72/36.65 r_next=0.299 MAD_above=38.36 lag=0(38.36/38.36); L525 68.66/46.61 r_next=0.068 MAD_above=33.47 lag=-1(32.79/33.47); direct-full=L525 (L525 internal blank x=53-116 Y=1.391; above=132.484 following=82.000; gate=4.000) |
| 284 | 284/F2 | L523 | L524 | L522 97.54/36.78 r_next=0.020 MAD_above=9.13 lag=0(9.13/9.13); L523 99.01/37.16 r_next=0.156 MAD_above=38.80 lag=-1(38.60/38.80); L524 67.96/47.62 r_next=0.965 MAD_above=39.77 lag=-3(38.68/39.77); L525 73.36/51.56 r_next=0.026 MAD_above=10.60 lag=-1(10.13/10.60); direct-full=L524 (L524 internal blank x=51-114 Y=1.312; above=137.000 following=79.000; gate=4.000) |
| 285 | 285/F2 | L523 | L524 | L522 97.80/39.23 r_next=0.044 MAD_above=8.76 lag=0(8.76/8.76); L523 94.83/38.97 r_next=0.236 MAD_above=41.17 lag=-2(40.73/41.17); L524 72.31/48.32 r_next=0.956 MAD_above=36.66 lag=-4(33.95/36.66); L525 75.17/51.20 r_next=-0.041 MAD_above=10.84 lag=-1(10.54/10.84); direct-full=L524 (L524 internal blank x=57-120 Y=1.359; above=139.875 following=87.000; gate=4.000) |
| 286 | 286/F2 | L523 | L524 | L522 96.31/37.81 r_next=-0.005 MAD_above=8.76 lag=0(8.76/8.76); L523 101.30/36.71 r_next=0.193 MAD_above=39.04 lag=30(38.51/39.04); L524 68.96/45.74 r_next=0.957 MAD_above=40.98 lag=-3(39.24/40.98); L525 76.65/52.10 r_next=-0.008 MAD_above=12.78 lag=-2(12.14/12.78); direct-full=L524 (L524 internal blank x=55-118 Y=1.359; above=142.234 following=82.000; gate=4.000) |
| 287 | 287/F2 | L523 | L524 | L522 95.07/39.58 r_next=0.008 MAD_above=10.28 lag=0(10.28/10.28); L523 96.50/37.45 r_next=0.237 MAD_above=40.88 lag=13(39.54/40.88); L524 71.55/47.06 r_next=0.963 MAD_above=37.85 lag=-1(37.76/37.85); L525 74.15/50.90 r_next=0.024 MAD_above=10.89 lag=0(10.89/10.89); direct-full=L524 (L524 internal blank x=55-118 Y=1.391; above=138.125 following=85.000; gate=4.000) |
| 288 | 288/F2 | L523 | L524 | L522 96.38/38.62 r_next=0.057 MAD_above=10.55 lag=0(10.55/10.55); L523 96.39/39.83 r_next=0.253 MAD_above=42.22 lag=14(40.26/42.22); L524 70.40/47.84 r_next=0.960 MAD_above=37.94 lag=-1(37.53/37.94); L525 73.37/50.87 r_next=0.012 MAD_above=10.97 lag=0(10.97/10.97); direct-full=L524 (L524 internal blank x=64-127 Y=1.328; above=142.562 following=83.000; gate=4.000) |
| 289 | 289/F2 | L523 | L524 | L522 94.95/36.93 r_next=-0.008 MAD_above=8.48 lag=0(8.48/8.48); L523 93.88/30.72 r_next=0.271 MAD_above=36.43 lag=1(36.34/36.43); L524 71.15/47.82 r_next=0.958 MAD_above=34.65 lag=-1(34.58/34.65); L525 75.45/49.07 r_next=0.024 MAD_above=10.95 lag=-1(10.88/10.95); direct-full=L524 (L524 internal blank x=55-118 Y=1.375; above=119.531 following=88.000; gate=4.000) |
| 290 | 290/F2 | L521 | L525 | L520 95.46/37.36 r_next=0.921 MAD_above=10.92 lag=0(10.92/10.92); L521 91.85/36.63 r_next=0.890 MAD_above=10.34 lag=0(10.34/10.34); L522 94.22/36.64 r_next=0.904 MAD_above=10.55 lag=1(10.46/10.55); L523 93.94/35.85 r_next=-0.035 MAD_above=9.12 lag=0(9.12/9.12); L524 93.46/31.94 r_next=0.185 MAD_above=36.59 lag=-1(35.94/36.59); L525 68.33/44.20 r_next=-0.009 MAD_above=35.61 lag=-2(34.43/35.61); direct-full=L525 (L525 internal blank x=62-125 Y=1.406; above=119.672 following=82.000; gate=4.000) |
| 293 | 293/F2 | L524 | L525 | L523 93.40/37.55 r_next=-0.104 MAD_above=11.23 lag=-1(11.12/11.23); L524 97.67/39.59 r_next=0.155 MAD_above=41.97 lag=32(41.12/41.97); L525 68.22/43.65 r_next=0.009 MAD_above=42.37 lag=-3(40.92/42.37); direct-full=L525 (L525 internal blank x=62-125 Y=1.391; above=125.969 following=86.500; gate=4.000) |
| 294 | 294/F2 | L523 | L524 | L522 97.12/38.40 r_next=-0.013 MAD_above=7.92 lag=0(7.92/7.92); L523 100.02/35.24 r_next=0.243 MAD_above=38.42 lag=-2(38.05/38.42); L524 72.98/49.54 r_next=0.964 MAD_above=36.51 lag=-1(36.31/36.51); L525 75.44/52.89 r_next=-0.031 MAD_above=10.94 lag=0(10.94/10.94); direct-full=L524 (L524 internal blank x=68-131 Y=1.391; above=140.688 following=86.000; gate=4.000) |
| 295 | 295/F2 | L523 | L524 | L522 96.96/38.27 r_next=0.029 MAD_above=8.47 lag=-1(8.38/8.47); L523 98.61/34.65 r_next=0.190 MAD_above=37.41 lag=0(37.41/37.41); L524 71.29/47.91 r_next=0.961 MAD_above=38.42 lag=-1(38.11/38.42); L525 76.13/51.71 r_next=0.011 MAD_above=11.17 lag=0(11.17/11.17); direct-full=L524 (L524 internal blank x=71-134 Y=1.406; above=136.578 following=87.000; gate=4.000) |
| 296 | 296/F2 | L523 | L524 | L522 95.53/38.76 r_next=0.011 MAD_above=8.67 lag=0(8.67/8.67); L523 99.44/35.77 r_next=0.268 MAD_above=39.05 lag=32(38.74/39.05); L524 69.66/48.74 r_next=0.968 MAD_above=38.03 lag=-1(37.72/38.03); L525 77.73/52.99 r_next=0.009 MAD_above=11.69 lag=0(11.69/11.69); direct-full=L524 (L524 internal blank x=69-132 Y=1.391; above=138.500 following=82.000; gate=4.000) |
| 297 | 297/F2 | L524 | L525 | L523 95.75/37.63 r_next=0.031 MAD_above=7.57 lag=0(7.57/7.57); L524 96.93/36.00 r_next=0.218 MAD_above=37.78 lag=-2(37.41/37.78); L525 70.78/49.23 r_next=-0.023 MAD_above=37.71 lag=-1(37.62/37.71); direct-full=L525 (L525 internal blank x=71-134 Y=1.328; above=138.766 following=83.000; gate=4.000) |
| 298 | 298/F2 | L524 | L525 | L523 95.07/38.16 r_next=0.016 MAD_above=7.99 lag=0(7.99/7.99); L524 97.12/34.52 r_next=0.227 MAD_above=37.37 lag=-1(37.30/37.37); L525 70.19/48.50 r_next=-0.026 MAD_above=36.39 lag=0(36.39/36.39); direct-full=L525 (L525 internal blank x=77-140 Y=1.328; above=136.016 following=82.000; gate=4.000) |
| 300 | 300/F2 | L524 | L525 | L523 105.29/49.49 r_next=0.090 MAD_above=15.06 lag=1(15.00/15.06); L524 80.11/38.98 r_next=0.444 MAD_above=54.68 lag=-26(47.27/54.68); L525 72.42/54.51 r_next=0.024 MAD_above=35.72 lag=0(35.72/35.72); direct-full=L525 (L525 internal blank x=67-130 Y=1.344; above=98.781 following=71.500; gate=4.000) |
| 301 | 301/F2 | L523 | L525 | L522 111.72/46.48 r_next=0.849 MAD_above=11.29 lag=1(10.72/11.29); L523 107.14/49.35 r_next=0.028 MAD_above=15.04 lag=1(14.40/15.04); L524 74.28/40.99 r_next=0.321 MAD_above=59.52 lag=-26(52.47/59.52); L525 72.25/55.74 r_next=-0.018 MAD_above=40.20 lag=-3(38.18/40.20); direct-full=L525 (L525 internal blank x=57-120 Y=1.344; above=93.359 following=66.000; gate=4.000) |
| 302 | 302/F2 | L523 | L525 | L522 113.21/47.35 r_next=0.855 MAD_above=11.44 lag=0(11.44/11.44); L523 105.99/51.16 r_next=0.072 MAD_above=14.94 lag=1(14.80/14.94); L524 79.55/42.81 r_next=0.375 MAD_above=59.20 lag=-27(51.47/59.20); L525 74.58/57.20 r_next=-0.041 MAD_above=39.15 lag=-1(39.02/39.15); direct-full=L525 (L525 internal blank x=56-119 Y=1.359; above=94.250 following=71.000; gate=4.000) |
| 303 | 303/F2 | L523 | L524 | L522 110.54/49.09 r_next=0.122 MAD_above=15.27 lag=1(15.04/15.27); L523 84.99/42.79 r_next=0.406 MAD_above=54.03 lag=-19(47.94/54.03); L524 72.43/56.14 r_next=0.911 MAD_above=38.59 lag=1(38.47/38.59); L525 75.78/58.56 r_next=-0.022 MAD_above=15.67 lag=0(15.67/15.67); direct-full=L524 (L524 internal blank x=71-134 Y=1.391; above=109.297 following=67.000; gate=4.000) |
| 304 | 304/F2 | L523 | L524 | L522 107.00/48.66 r_next=-0.009 MAD_above=14.90 lag=0(14.90/14.90); L523 83.30/42.87 r_next=0.323 MAD_above=56.65 lag=-27(46.35/56.65); L524 73.19/56.00 r_next=0.924 MAD_above=40.07 lag=1(40.05/40.07); L525 75.77/57.63 r_next=0.008 MAD_above=13.83 lag=0(13.83/13.83); direct-full=L524 (L524 internal blank x=73-136 Y=1.359; above=104.828 following=69.000; gate=4.000) |
| 305 | 305/F2 | L524 | L525 | L523 109.67/49.62 r_next=-0.041 MAD_above=14.52 lag=0(14.52/14.52); L524 82.34/41.98 r_next=0.283 MAD_above=59.52 lag=-24(48.57/59.52); L525 72.35/54.59 r_next=-0.003 MAD_above=41.70 lag=-2(40.99/41.70); direct-full=L525 (L525 internal blank x=63-126 Y=1.328; above=100.094 following=70.000; gate=4.000) |
| 306 | 306/F2 | L524 | L525 | L523 113.00/45.86 r_next=-0.076 MAD_above=8.66 lag=0(8.66/8.66); L524 75.27/46.87 r_next=0.356 MAD_above=66.52 lag=-27(56.60/66.52); L525 72.44/54.50 r_next=0.019 MAD_above=39.95 lag=-2(39.14/39.95); direct-full=L525 (L525 internal blank x=59-122 Y=1.438; above=97.234 following=73.000; gate=4.000) |
| 307 | 307/F2 | L524 | L525 | L523 114.34/45.47 r_next=-0.101 MAD_above=8.87 lag=0(8.87/8.87); L524 76.22/46.37 r_next=0.354 MAD_above=66.70 lag=-26(57.51/66.70); L525 71.11/54.28 r_next=-0.026 MAD_above=40.30 lag=-2(38.47/40.30); direct-full=L525 (L525 internal blank x=69-132 Y=1.312; above=105.219 following=68.000; gate=4.000) |
| 308 | 308/F2 | L524 | L525 | L523 113.75/46.48 r_next=-0.099 MAD_above=9.15 lag=0(9.15/9.15); L524 77.59/49.90 r_next=0.346 MAD_above=69.50 lag=-29(59.16/69.50); L525 71.23/53.76 r_next=-0.026 MAD_above=41.54 lag=-2(40.38/41.54); direct-full=L525 (L525 internal blank x=69-132 Y=1.391; above=104.484 following=72.000; gate=4.000) |
| 309 | 309/F2 | L524 | L525 | L523 108.25/49.53 r_next=0.038 MAD_above=16.71 lag=1(16.14/16.71); L524 80.66/43.25 r_next=0.414 MAD_above=59.62 lag=-24(53.08/59.62); L525 73.12/55.42 r_next=-0.001 MAD_above=40.08 lag=-2(39.70/40.08); direct-full=L525 (L525 internal blank x=70-133 Y=1.297; above=107.250 following=67.000; gate=4.000) |
| 310 | 310/F2 | L523 | L524 | L522 107.81/49.20 r_next=0.070 MAD_above=14.95 lag=0(14.95/14.95); L523 77.65/41.17 r_next=0.350 MAD_above=58.35 lag=-19(51.36/58.35); L524 73.87/54.42 r_next=0.888 MAD_above=40.25 lag=-3(38.57/40.25); L525 75.14/57.64 r_next=-0.018 MAD_above=14.88 lag=0(14.88/14.88); direct-full=L524 (L524 internal blank x=72-135 Y=1.375; above=104.391 following=70.500; gate=4.000) |
| 311 | 311/F2 | L523 | L524 | L522 104.15/50.01 r_next=0.115 MAD_above=13.68 lag=0(13.68/13.68); L523 75.78/39.42 r_next=0.360 MAD_above=53.45 lag=-20(47.61/53.45); L524 71.00/54.27 r_next=0.901 MAD_above=38.16 lag=0(38.16/38.16); L525 72.85/56.00 r_next=-0.012 MAD_above=14.49 lag=0(14.49/14.49); direct-full=L524 (L524 internal blank x=70-133 Y=1.391; above=102.562 following=67.500; gate=4.000) |
| 312 | 312/F2 | L523 | L524 | L522 106.53/50.98 r_next=0.054 MAD_above=14.05 lag=0(14.05/14.05); L523 76.67/39.84 r_next=0.334 MAD_above=56.07 lag=-22(46.04/56.07); L524 72.42/53.45 r_next=0.921 MAD_above=37.86 lag=-1(37.37/37.86); L525 76.80/58.34 r_next=0.009 MAD_above=14.66 lag=1(14.19/14.66); direct-full=L524 (L524 internal blank x=65-128 Y=1.328; above=98.625 following=69.000; gate=4.000) |
| 313 | 313/F2 | L524 | L525 | L523 107.14/51.55 r_next=0.026 MAD_above=14.36 lag=0(14.36/14.36); L524 77.76/43.63 r_next=0.297 MAD_above=60.36 lag=-21(51.91/60.36); L525 72.82/54.37 r_next=-0.058 MAD_above=41.21 lag=-2(40.57/41.21); direct-full=L525 (L525 internal blank x=59-122 Y=1.375; above=96.109 following=71.000; gate=4.000) |
| 314 | 314/F2 | L524 | L525 | L523 114.04/45.64 r_next=-0.048 MAD_above=10.82 lag=1(10.65/10.82); L524 79.92/41.89 r_next=0.320 MAD_above=61.43 lag=-20(55.54/61.43); L525 73.14/56.45 r_next=-0.006 MAD_above=40.56 lag=-1(40.38/40.56); direct-full=L525 (L525 internal blank x=63-126 Y=1.375; above=98.125 following=69.500; gate=4.000) |
| 315 | 315/F2 | L524 | L525 | L523 110.63/46.27 r_next=-0.100 MAD_above=9.58 lag=0(9.58/9.58); L524 78.83/44.51 r_next=0.312 MAD_above=62.88 lag=-21(56.04/62.88); L525 72.68/55.29 r_next=-0.023 MAD_above=40.19 lag=-1(40.18/40.19); direct-full=L525 (L525 internal blank x=72-135 Y=1.375; above=107.297 following=68.000; gate=4.000) |
| 316 | 316/F2 | L524 | L525 | L523 114.82/45.00 r_next=-0.062 MAD_above=9.46 lag=0(9.46/9.46); L524 81.60/41.98 r_next=0.282 MAD_above=60.93 lag=-17(54.64/60.93); L525 71.80/54.91 r_next=0.027 MAD_above=41.80 lag=-3(40.27/41.80); direct-full=L525 (L525 internal blank x=69-132 Y=1.359; above=107.531 following=69.000; gate=4.000) |
| 317 | 317/F2 | L524 | L525 | L523 112.45/45.09 r_next=-0.097 MAD_above=9.78 lag=1(9.60/9.78); L524 80.38/43.41 r_next=0.320 MAD_above=62.63 lag=-21(55.34/62.63); L525 71.85/54.60 r_next=-0.019 MAD_above=40.61 lag=-2(40.03/40.61); direct-full=L525 (L525 internal blank x=75-138 Y=1.422; above=108.688 following=68.000; gate=4.000) |
| 318 | 318/F2 | L524 | L525 | L523 114.52/44.84 r_next=-0.087 MAD_above=9.43 lag=0(9.43/9.43); L524 76.04/44.73 r_next=0.373 MAD_above=64.52 lag=-20(58.49/64.52); L525 72.70/55.28 r_next=-0.022 MAD_above=37.45 lag=-2(36.92/37.45); direct-full=L525 (L525 internal blank x=86-149 Y=1.375; above=101.906 following=66.500; gate=4.000) |
| 319 | 319/F2 | L524 | L525 | L523 113.20/45.53 r_next=-0.234 MAD_above=9.06 lag=0(9.06/9.06); L524 88.97/41.94 r_next=0.179 MAD_above=63.24 lag=-23(56.14/63.24); L525 73.29/54.60 r_next=-0.000 MAD_above=45.63 lag=-1(45.39/45.63); direct-full=L525 (L525 internal blank x=77-140 Y=1.344; above=104.906 following=76.000; gate=4.000) |
| 320 | 320/F2 | L524 | L525 | L523 114.24/44.63 r_next=-0.251 MAD_above=8.23 lag=0(8.23/8.23); L524 88.83/42.47 r_next=0.187 MAD_above=63.41 lag=-23(55.77/63.41); L525 71.42/55.97 r_next=0.001 MAD_above=46.80 lag=-2(46.13/46.80); direct-full=L525 (L525 internal blank x=65-128 Y=1.391; above=101.109 following=67.000; gate=4.000) |
| 321 | 321/F2 | L524 | L525 | L523 112.09/45.61 r_next=-0.097 MAD_above=10.44 lag=0(10.44/10.44); L524 87.75/39.71 r_next=0.318 MAD_above=58.14 lag=-21(51.37/58.14); L525 72.77/56.92 r_next=0.005 MAD_above=42.09 lag=-1(41.75/42.09); direct-full=L525 (L525 internal blank x=71-134 Y=1.344; above=106.234 following=69.500; gate=4.000) |
| 322 | 322/F2 | L524 | L525 | L523 112.64/45.36 r_next=-0.124 MAD_above=10.01 lag=0(10.01/10.01); L524 87.58/39.95 r_next=0.323 MAD_above=59.21 lag=32(52.56/59.21); L525 71.97/56.45 r_next=-0.018 MAD_above=41.45 lag=-1(40.84/41.45); direct-full=L525 (L525 internal blank x=70-133 Y=1.344; above=108.375 following=66.500; gate=4.000) |
| 323 | 323/F2 | L524 | L525 | L523 116.09/45.99 r_next=-0.135 MAD_above=9.37 lag=0(9.37/9.37); L524 86.62/39.99 r_next=0.308 MAD_above=60.80 lag=-23(53.30/60.80); L525 75.96/56.86 r_next=-0.025 MAD_above=42.10 lag=-2(41.46/42.10); direct-full=L525 (L525 internal blank x=62-125 Y=1.312; above=99.031 following=70.000; gate=4.000) |
| 324 | 324/F2 | L522 | L524 | L521 115.37/46.40 r_next=0.959 MAD_above=7.74 lag=0(7.74/7.74); L522 115.43/46.24 r_next=-0.176 MAD_above=9.01 lag=0(9.01/9.01); L523 88.78/41.06 r_next=0.194 MAD_above=61.95 lag=-27(54.14/61.95); L524 71.05/56.57 r_next=0.896 MAD_above=45.80 lag=-1(45.57/45.80); L525 75.39/58.53 r_next=-0.005 MAD_above=16.18 lag=0(16.18/16.18); direct-full=L524 (L524 internal blank x=70-133 Y=1.375; above=105.281 following=65.500; gate=4.000) |
| 325 | 325/F2 | L521 | L524 | L520 115.06/46.72 r_next=0.970 MAD_above=9.56 lag=0(9.56/9.56); L521 114.95/47.53 r_next=0.965 MAD_above=8.13 lag=0(8.13/8.13); L522 115.46/46.59 r_next=-0.187 MAD_above=8.72 lag=0(8.72/8.72); L523 82.30/44.10 r_next=0.285 MAD_above=67.41 lag=-29(58.73/67.41); L524 73.71/56.21 r_next=0.910 MAD_above=42.67 lag=-1(42.47/42.67); L525 75.64/57.18 r_next=0.018 MAD_above=14.43 lag=0(14.43/14.43); direct-full=L524 (L524 internal blank x=71-134 Y=1.359; above=104.250 following=70.500; gate=4.000) |
| 326 | 326/F2 | L523 | L524 | L522 116.71/44.81 r_next=-0.116 MAD_above=8.78 lag=0(8.78/8.78); L523 89.83/42.69 r_next=0.204 MAD_above=61.46 lag=-30(54.27/61.46); L524 72.63/56.53 r_next=0.882 MAD_above=45.96 lag=-1(45.59/45.96); L525 74.26/58.17 r_next=-0.008 MAD_above=15.66 lag=0(15.66/15.66); direct-full=L524 (L524 internal blank x=65-128 Y=1.328; above=102.812 following=73.500; gate=4.000) |
| 327 | 327/F2 | L523 | L524 | L522 113.25/46.17 r_next=-0.127 MAD_above=9.10 lag=1(9.02/9.10); L523 90.65/42.40 r_next=0.252 MAD_above=59.96 lag=-27(52.35/59.96); L524 73.48/55.92 r_next=0.900 MAD_above=43.26 lag=-1(43.11/43.26); L525 73.65/58.22 r_next=-0.004 MAD_above=14.32 lag=0(14.32/14.32); direct-full=L524 (L524 internal blank x=65-128 Y=1.375; above=102.531 following=68.000; gate=4.000) |
| 328 | 328/F2 | L524 | L525 | L523 112.98/45.87 r_next=-0.103 MAD_above=9.38 lag=0(9.38/9.38); L524 89.93/43.16 r_next=0.267 MAD_above=60.00 lag=-27(53.04/60.00); L525 72.02/57.24 r_next=0.006 MAD_above=45.13 lag=-1(44.59/45.13); direct-full=L525 (L525 internal blank x=64-127 Y=1.391; above=99.609 following=68.500; gate=4.000) |
| 329 | 329/F2 | L524 | L525 | L523 113.34/45.55 r_next=-0.022 MAD_above=9.15 lag=0(9.15/9.15); L524 90.25/45.87 r_next=0.419 MAD_above=59.65 lag=32(52.18/59.65); L525 73.33/55.65 r_next=-0.011 MAD_above=39.94 lag=0(39.94/39.94); direct-full=L525 (L525 internal blank x=70-133 Y=1.344; above=103.797 following=71.500; gate=4.000) |
| 330 | 330/F2 | L524 | L525 | L523 113.59/45.07 r_next=-0.109 MAD_above=9.70 lag=0(9.70/9.70); L524 86.77/40.02 r_next=0.325 MAD_above=59.52 lag=-24(53.01/59.52); L525 70.81/56.02 r_next=0.033 MAD_above=42.00 lag=-2(41.24/42.00); direct-full=L525 (L525 internal blank x=62-125 Y=1.375; above=100.031 following=65.000; gate=4.000) |
| 331 | 331/F2 | L524 | L525 | L523 116.69/45.90 r_next=-0.038 MAD_above=10.15 lag=0(10.15/10.15); L524 89.68/45.98 r_next=0.426 MAD_above=61.29 lag=32(53.12/61.29); L525 73.80/55.16 r_next=0.032 MAD_above=40.61 lag=-3(39.80/40.61); direct-full=L525 (L525 internal blank x=56-119 Y=1.312; above=95.953 following=70.000; gate=4.000) |
| 332 | 332/F2 | L524 | L525 | L523 114.49/44.13 r_next=-0.071 MAD_above=9.81 lag=0(9.81/9.81); L524 90.39/41.64 r_next=0.366 MAD_above=57.08 lag=-24(50.34/57.08); L525 71.54/56.25 r_next=-0.018 MAD_above=42.32 lag=-2(41.83/42.32); direct-full=L525 (L525 internal blank x=57-120 Y=1.344; above=97.000 following=67.500; gate=4.000) |
| 333 | 333/F2 | L524 | L525 | L523 114.18/46.75 r_next=-0.043 MAD_above=9.15 lag=0(9.15/9.15); L524 89.11/42.61 r_next=0.338 MAD_above=59.19 lag=-23(52.92/59.19); L525 74.37/56.59 r_next=0.001 MAD_above=40.82 lag=0(40.82/40.82); direct-full=L525 (L525 internal blank x=70-133 Y=1.375; above=106.891 following=73.000; gate=4.000) |
| 334 | 334/F2 | L522 | L524 | L521 113.89/47.36 r_next=0.933 MAD_above=7.99 lag=0(7.99/7.99); L522 114.51/44.50 r_next=-0.119 MAD_above=9.70 lag=1(9.47/9.70); L523 84.75/43.76 r_next=0.346 MAD_above=63.50 lag=-31(54.96/63.50); L524 72.93/55.34 r_next=0.879 MAD_above=41.76 lag=-1(40.92/41.76); L525 71.36/56.63 r_next=-0.024 MAD_above=14.25 lag=0(14.25/14.25); direct-full=L524 (L524 internal blank x=65-128 Y=1.344; above=102.141 following=68.000; gate=4.000) |
| 335 | 335/F2 | L523 | L524 | L522 114.99/45.86 r_next=-0.089 MAD_above=10.35 lag=0(10.35/10.35); L523 81.47/44.02 r_next=0.410 MAD_above=64.37 lag=-22(57.95/64.37); L524 73.20/56.57 r_next=0.874 MAD_above=39.43 lag=-3(37.87/39.43); L525 72.79/57.15 r_next=0.038 MAD_above=14.80 lag=-1(13.74/14.80); direct-full=L524 (L524 internal blank x=60-123 Y=1.391; above=99.078 following=69.000; gate=4.000) |
| 336 | 336/F2 | L523 | L525 | L522 114.45/47.57 r_next=0.921 MAD_above=7.50 lag=0(7.50/7.50); L523 114.28/45.51 r_next=-0.062 MAD_above=10.00 lag=0(10.00/10.00); L524 87.52/41.00 r_next=0.423 MAD_above=58.77 lag=-23(53.58/58.77); L525 71.84/55.40 r_next=0.010 MAD_above=39.23 lag=-1(38.46/39.23); direct-full=L525 (L525 internal blank x=71-134 Y=1.406; above=108.188 following=68.000; gate=4.000) |
| 337 | 337/F2 | L524 | L525 | L523 114.89/45.75 r_next=-0.073 MAD_above=10.10 lag=0(10.10/10.10); L524 82.69/41.59 r_next=0.396 MAD_above=62.60 lag=32(55.38/62.60); L525 72.66/56.25 r_next=-0.024 MAD_above=40.93 lag=-2(39.79/40.93); direct-full=L525 (L525 internal blank x=63-126 Y=1.344; above=101.016 following=68.000; gate=4.000) |
| 338 | 338/F2 | L524 | L525 | L523 112.79/45.66 r_next=-0.058 MAD_above=9.18 lag=0(9.18/9.18); L524 87.04/40.69 r_next=0.388 MAD_above=58.04 lag=-22(52.99/58.04); L525 72.65/55.99 r_next=0.031 MAD_above=40.24 lag=-2(39.29/40.24); direct-full=L525 (L525 internal blank x=67-130 Y=1.375; above=106.078 following=67.500; gate=4.000) |
| 339 | 339/F2 | L524 | L525 | L523 115.39/46.18 r_next=-0.177 MAD_above=9.70 lag=1(9.05/9.70); L524 84.91/43.81 r_next=0.240 MAD_above=66.31 lag=-28(56.26/66.31); L525 72.72/57.40 r_next=0.015 MAD_above=45.04 lag=-2(44.52/45.04); direct-full=L525 (L525 internal blank x=72-135 Y=1.375; above=111.234 following=71.000; gate=4.000) |
| 340 | 340/F2 | L524 | L525 | L523 116.50/48.33 r_next=-0.308 MAD_above=7.61 lag=0(7.61/7.61); L524 107.50/37.81 r_next=0.228 MAD_above=60.15 lag=32(51.26/60.15); L525 69.40/53.58 r_next=-0.005 MAD_above=48.63 lag=-3(47.40/48.63); direct-full=L525 (L525 internal blank x=66-129 Y=1.359; above=106.281 following=66.000; gate=4.000) |
| 341 | 341/F2 | L524 | L525 | L523 103.37/47.31 r_next=0.372 MAD_above=18.31 lag=0(18.31/18.31); L524 124.21/49.18 r_next=0.382 MAD_above=47.24 lag=-2(46.25/47.24); L525 87.02/60.77 r_next=0.026 MAD_above=52.46 lag=-2(51.05/52.46); direct-full=L525 (L525 internal blank x=69-132 Y=1.359; above=117.703 following=121.000; gate=4.000) |
| 342 | 342/F2 | L524 | L525 | L523 101.26/46.51 r_next=0.287 MAD_above=17.62 lag=0(17.62/17.62); L524 123.41/45.66 r_next=0.431 MAD_above=47.93 lag=-1(47.50/47.93); L525 86.95/61.48 r_next=-0.011 MAD_above=50.64 lag=-3(48.64/50.64); direct-full=L525 (L525 internal blank x=56-119 Y=1.344; above=116.344 following=119.000; gate=4.000) |
| 343 | 343/F2 | L524 | L525 | L523 104.33/46.80 r_next=0.290 MAD_above=17.15 lag=0(17.15/17.15); L524 122.32/45.69 r_next=0.348 MAD_above=46.55 lag=-3(45.32/46.55); L525 86.28/59.75 r_next=0.022 MAD_above=50.78 lag=-4(47.11/50.78); direct-full=L525 (L525 internal blank x=69-132 Y=1.328; above=120.375 following=112.500; gate=4.000) |
| 344 | 344/F2 | L524 | L525 | L523 100.70/46.40 r_next=0.290 MAD_above=16.50 lag=0(16.50/16.50); L524 125.06/45.17 r_next=0.438 MAD_above=48.00 lag=-2(47.44/48.00); L525 87.27/60.05 r_next=0.013 MAD_above=49.52 lag=-2(48.14/49.52); direct-full=L525 (L525 internal blank x=57-120 Y=1.375; above=115.750 following=117.000; gate=4.000) |
| 345 | 345/F2 | L524 | L525 | L523 102.24/47.08 r_next=0.303 MAD_above=16.57 lag=0(16.57/16.57); L524 120.60/47.58 r_next=0.392 MAD_above=47.78 lag=-1(47.67/47.78); L525 88.02/60.50 r_next=0.023 MAD_above=48.41 lag=-2(47.35/48.41); direct-full=L525 (L525 internal blank x=74-137 Y=1.359; above=116.438 following=117.000; gate=4.000) |
| 346 | 346/F2 | L523 | L525 | L522 100.47/48.38 r_next=0.863 MAD_above=17.00 lag=0(17.00/17.00); L523 99.76/46.92 r_next=0.291 MAD_above=16.51 lag=1(16.51/16.51); L524 123.86/47.70 r_next=0.400 MAD_above=50.42 lag=-1(50.25/50.42); L525 88.21/62.81 r_next=-0.028 MAD_above=51.33 lag=-2(49.69/51.33); direct-full=L525 (L525 internal blank x=60-123 Y=1.422; above=117.266 following=118.000; gate=4.000) |
| 347 | 347/F2 | L524 | L525 | L523 101.85/47.06 r_next=0.183 MAD_above=16.20 lag=0(16.20/16.20); L524 112.91/48.13 r_next=0.458 MAD_above=50.30 lag=-1(50.29/50.30); L525 85.09/61.34 r_next=0.012 MAD_above=47.02 lag=-4(42.79/47.02); direct-full=L525 (L525 internal blank x=69-132 Y=1.328; above=116.906 following=116.000; gate=4.000) |
| 348 | 348/F2 | L524 | L525 | L523 99.57/46.80 r_next=0.320 MAD_above=17.32 lag=0(17.32/17.32); L524 125.20/48.62 r_next=0.407 MAD_above=49.14 lag=-3(48.52/49.14); L525 89.03/62.33 r_next=0.018 MAD_above=52.34 lag=-2(51.30/52.34); direct-full=L525 (L525 internal blank x=72-135 Y=1.375; above=121.281 following=122.500; gate=4.000) |
| 349 | 349/F2 | L523 | L524 | L522 101.39/48.29 r_next=0.349 MAD_above=17.91 lag=0(17.91/17.91); L523 122.22/47.59 r_next=0.405 MAD_above=46.78 lag=0(46.78/46.78); L524 86.59/60.79 r_next=0.895 MAD_above=50.02 lag=-1(49.94/50.02); L525 91.30/68.93 r_next=0.027 MAD_above=20.60 lag=-1(20.45/20.60); direct-full=L524 (L524 internal blank x=75-138 Y=1.328; above=120.516 following=114.500; gate=4.000) |
| 350 | 350/F2 | L522 | L524 | L521 100.81/47.97 r_next=0.873 MAD_above=16.99 lag=1(16.61/16.99); L522 99.30/46.82 r_next=0.332 MAD_above=16.31 lag=-1(16.10/16.31); L523 121.24/46.88 r_next=0.411 MAD_above=47.31 lag=0(47.31/47.31); L524 87.04/62.35 r_next=0.872 MAD_above=50.38 lag=-2(49.41/50.38); L525 90.72/69.87 r_next=0.021 MAD_above=22.94 lag=0(22.94/22.94); direct-full=L524 (L524 internal blank x=68-131 Y=1.328; above=116.578 following=116.000; gate=4.000) |
| 351 | 351/F2 | L524 | L525 | L523 102.68/47.19 r_next=0.368 MAD_above=17.09 lag=0(17.09/17.09); L524 120.79/48.82 r_next=0.400 MAD_above=45.38 lag=-1(45.17/45.38); L525 85.81/61.49 r_next=0.032 MAD_above=52.35 lag=-2(50.86/52.35); direct-full=L525 (L525 internal blank x=68-131 Y=1.344; above=116.688 following=117.500; gate=4.000) |
| 352 | 352/F2 | L523 | L525 | L522 99.87/49.04 r_next=0.868 MAD_above=16.77 lag=0(16.77/16.77); L523 99.21/46.32 r_next=0.257 MAD_above=16.54 lag=0(16.54/16.54); L524 118.38/43.65 r_next=0.415 MAD_above=48.58 lag=-2(48.24/48.58); L525 88.46/62.57 r_next=0.005 MAD_above=49.19 lag=-3(47.11/49.19); direct-full=L525 (L525 internal blank x=58-121 Y=1.344; above=114.047 following=123.000; gate=4.000) |
| 353 | 353/F2 | L524 | L525 | L523 102.06/47.60 r_next=0.278 MAD_above=17.21 lag=0(17.21/17.21); L524 120.02/44.03 r_next=0.439 MAD_above=47.26 lag=-1(47.13/47.26); L525 86.35/60.81 r_next=0.022 MAD_above=47.99 lag=-3(46.49/47.99); direct-full=L525 (L525 internal blank x=68-131 Y=1.344; above=120.812 following=110.000; gate=4.000) |
| 355 | 355/F2 | L524 | L525 | L523 101.67/47.09 r_next=0.359 MAD_above=16.42 lag=1(15.97/16.42); L524 127.58/51.62 r_next=0.368 MAD_above=49.70 lag=-1(49.36/49.70); L525 86.58/60.77 r_next=0.000 MAD_above=55.23 lag=-3(52.96/55.23); direct-full=L525 (L525 internal blank x=62-125 Y=1.453; above=119.219 following=115.000; gate=4.000) |
| 356 | 356/F2 | L524 | L525 | L523 100.07/46.85 r_next=0.271 MAD_above=17.89 lag=0(17.89/17.89); L524 122.19/44.92 r_next=0.408 MAD_above=49.01 lag=-1(48.74/49.01); L525 89.17/61.17 r_next=0.004 MAD_above=48.41 lag=-2(47.59/48.41); direct-full=L525 (L525 internal blank x=54-117 Y=1.406; above=112.578 following=120.000; gate=4.000) |
| 357 | 357/F2 | L524 | L525 | L523 102.64/47.23 r_next=0.228 MAD_above=17.23 lag=0(17.23/17.23); L524 119.55/42.95 r_next=0.553 MAD_above=48.31 lag=-32(47.69/48.31); L525 95.46/56.18 r_next=0.008 MAD_above=36.40 lag=0(36.40/36.40); direct-full=L525 (L525 internal blank x=103-166 Y=3.016; above=119.797 following=114.000; gate=4.000) |
| 359 | 359/F2 | L523 | L524 | L522 105.15/47.66 r_next=0.426 MAD_above=18.05 lag=0(18.05/18.05); L523 121.80/45.96 r_next=0.402 MAD_above=39.11 lag=-2(37.09/39.11); L524 87.83/62.18 r_next=0.815 MAD_above=48.38 lag=-2(45.54/48.38); L525 93.15/70.32 r_next=0.018 MAD_above=27.10 lag=-3(25.05/27.10); direct-full=L524 (L524 internal blank x=68-131 Y=1.391; above=122.000 following=118.500; gate=4.000) |
| 360 | 360/F2 | L522 | L524 | L521 99.15/48.38 r_next=0.841 MAD_above=16.12 lag=0(16.12/16.12); L522 99.24/46.77 r_next=0.152 MAD_above=18.00 lag=0(18.00/18.00); L523 114.96/45.34 r_next=0.570 MAD_above=50.73 lag=-1(50.72/50.73); L524 87.62/61.35 r_next=0.844 MAD_above=37.34 lag=0(37.34/37.34); L525 91.58/67.90 r_next=0.010 MAD_above=23.67 lag=0(23.67/23.67); direct-full=L524 (L524 internal blank x=57-120 Y=1.375; above=111.609 following=118.500; gate=4.000) |
| 361 | 361/F2 | L524 | L525 | L523 100.12/47.21 r_next=0.172 MAD_above=17.76 lag=0(17.76/17.76); L524 115.49/46.32 r_next=0.499 MAD_above=51.25 lag=-1(51.04/51.25); L525 87.49/61.57 r_next=-0.009 MAD_above=44.79 lag=-3(41.98/44.79); direct-full=L525 (L525 internal blank x=66-129 Y=1.391; above=118.328 following=114.000; gate=4.000) |
| 362 | 362/F2 | L523 | L525 | L522 99.43/48.23 r_next=0.850 MAD_above=17.02 lag=1(16.42/17.02); L523 98.81/46.98 r_next=0.151 MAD_above=17.62 lag=0(17.62/17.62); L524 115.47/44.20 r_next=0.484 MAD_above=50.53 lag=-2(50.20/50.53); L525 87.14/60.42 r_next=0.053 MAD_above=44.72 lag=-4(41.05/44.72); direct-full=L525 (L525 internal blank x=70-133 Y=1.359; above=117.516 following=116.500; gate=4.000) |
| 363 | 363/F2 | L523 | L524 | L522 100.83/47.09 r_next=0.339 MAD_above=18.25 lag=0(18.25/18.25); L523 122.91/48.18 r_next=0.408 MAD_above=47.41 lag=-1(46.90/47.41); L524 85.70/62.09 r_next=0.879 MAD_above=51.80 lag=-1(51.38/51.80); L525 92.35/68.76 r_next=-0.019 MAD_above=22.12 lag=-1(21.61/22.12); direct-full=L524 (L524 internal blank x=55-118 Y=1.406; above=116.656 following=117.500; gate=4.000) |
| 364 | 364/F2 | L523 | L524 | L522 100.34/46.80 r_next=0.220 MAD_above=16.97 lag=0(16.97/16.97); L523 117.41/46.20 r_next=0.431 MAD_above=49.46 lag=-1(49.29/49.46); L524 86.74/60.38 r_next=0.874 MAD_above=48.00 lag=-3(46.14/48.00); L525 92.22/68.81 r_next=-0.013 MAD_above=22.27 lag=-2(21.73/22.27); direct-full=L524 (L524 internal blank x=67-130 Y=1.406; above=118.750 following=113.000; gate=4.000) |
| 365 | 365/F2 | L523 | L524 | L522 101.68/45.93 r_next=0.590 MAD_above=17.47 lag=1(17.27/17.47); L523 111.05/53.86 r_next=0.152 MAD_above=32.29 lag=-1(30.92/32.29); L524 86.94/61.58 r_next=0.858 MAD_above=63.34 lag=-4(60.75/63.34); L525 88.35/66.70 r_next=-0.009 MAD_above=23.02 lag=-1(22.68/23.02); direct-full=L524 (L524 persistent three-third step; thirds=8.292,3.531,3.440; correlation above/next=0.145/0.902; middle coherence=0.919) |
| 368 | 368/F2 | L524 | L525 | L523 102.29/47.54 r_next=0.432 MAD_above=17.34 lag=0(17.34/17.34); L524 124.05/49.52 r_next=0.307 MAD_above=42.40 lag=-1(40.91/42.40); L525 85.46/60.43 r_next=0.016 MAD_above=59.30 lag=-4(56.89/59.30); direct-full=L525 (L525 internal blank x=72-135 Y=1.359; above=120.438 following=115.000; gate=4.000) |
| 369 | 369/F2 | L524 | L525 | L523 101.50/47.37 r_next=0.347 MAD_above=16.80 lag=1(16.51/16.80); L524 126.69/47.78 r_next=0.467 MAD_above=47.84 lag=-1(47.64/47.84); L525 99.58/57.20 r_next=0.033 MAD_above=40.67 lag=-2(37.26/40.67); direct-full=L525 (L525 internal blank x=106-169 Y=3.719; above=121.281 following=124.000; gate=4.000) |
| 370 | 370/F2 | L522 | L524 | L521 98.57/48.19 r_next=0.846 MAD_above=17.45 lag=1(16.66/17.45); L522 100.77/47.52 r_next=0.108 MAD_above=17.33 lag=0(17.33/17.33); L523 114.29/47.38 r_next=0.502 MAD_above=53.03 lag=-3(52.18/53.03); L524 85.26/58.78 r_next=0.896 MAD_above=43.54 lag=-4(40.27/43.54); L525 82.40/62.39 r_next=-0.016 MAD_above=15.65 lag=0(15.65/15.65); direct-full=L524 (L524 internal blank x=67-130 Y=1.312; above=118.625 following=109.000; gate=4.000) |
| 372 | 372/F2 | L523 | L524 | L522 101.51/46.76 r_next=0.223 MAD_above=16.95 lag=0(16.95/16.95); L523 116.44/44.51 r_next=0.453 MAD_above=48.25 lag=-1(48.08/48.25); L524 87.12/60.90 r_next=0.874 MAD_above=46.44 lag=-2(45.39/46.44); L525 93.79/68.12 r_next=0.014 MAD_above=21.48 lag=0(21.48/21.48); direct-full=L524 (L524 internal blank x=65-128 Y=1.344; above=116.547 following=115.000; gate=4.000) |
| 373 | 373/F2 | L523 | L524 | L522 100.31/45.87 r_next=0.241 MAD_above=17.19 lag=1(16.95/17.19); L523 116.69/44.89 r_next=0.566 MAD_above=47.29 lag=-1(47.10/47.29); L524 94.97/56.35 r_next=0.749 MAD_above=36.57 lag=-1(35.65/36.57); L525 88.87/68.80 r_next=-0.011 MAD_above=30.07 lag=-1(29.40/30.07); direct-full=L524 (L524 internal blank x=108-171 Y=1.719; above=120.047 following=117.000; gate=4.000) |
| 374 | 374/F2 | L523 | L524 | L522 103.61/47.79 r_next=0.698 MAD_above=18.23 lag=1(18.04/18.23); L523 101.93/48.00 r_next=0.583 MAD_above=22.07 lag=0(22.07/22.07); L524 76.58/59.53 r_next=0.599 MAD_above=31.57 lag=-1(28.36/31.57); L525 89.28/67.13 r_next=0.024 MAD_above=36.30 lag=-2(34.77/36.30); direct-full=L524 (L524 internal blank x=55-118 Y=1.344; above=115.656 following=90.000; gate=4.000) |
| 375 | 375/F2 | L523 | L524 | L522 101.85/46.46 r_next=0.881 MAD_above=17.03 lag=0(17.03/17.03); L523 97.36/49.37 r_next=0.333 MAD_above=11.84 lag=0(11.84/11.84); L524 71.22/58.47 r_next=0.725 MAD_above=44.55 lag=0(44.55/44.55); L525 92.77/68.91 r_next=0.016 MAD_above=34.82 lag=0(34.82/34.82); direct-full=L524 (L524 internal blank x=65-128 Y=1.375; above=115.562 following=81.000; gate=4.000) |
| 376 | 376/F2 | L523 | L524 | L522 103.02/47.11 r_next=0.360 MAD_above=18.10 lag=0(18.10/18.10); L523 125.77/49.94 r_next=0.479 MAD_above=47.83 lag=-2(47.47/47.83); L524 88.88/61.17 r_next=0.810 MAD_above=41.01 lag=0(41.01/41.01); L525 88.40/64.36 r_next=-0.007 MAD_above=23.94 lag=1(23.29/23.94); direct-full=L524 (L524 internal blank x=64-127 Y=1.344; above=115.531 following=118.500; gate=4.000) |
| 395 | 395/F2 | L523 | L524 | L522 103.20/51.81 r_next=0.973 MAD_above=24.49 lag=-1(24.08/24.49); L523 100.03/52.30 r_next=0.456 MAD_above=8.59 lag=-1(4.74/8.59); L524 82.61/62.30 r_next=0.433 MAD_above=42.80 lag=-3(35.44/42.80); L525 23.37/48.23 r_next=0.000 MAD_above=62.63 lag=-4(59.13/62.63); direct-full=L524 (L524 internal blank x=120-183 Y=2.062; above=129.375 following=95.000; gate=4.000) |
| 402 | 402/F2 | L523 | L524 | L522 99.76/47.32 r_next=0.394 MAD_above=15.86 lag=0(15.86/15.86); L523 118.53/44.96 r_next=0.301 MAD_above=41.79 lag=-1(41.31/41.79); L524 87.48/61.40 r_next=0.867 MAD_above=53.75 lag=3(53.40/53.75); L525 92.56/69.44 r_next=0.004 MAD_above=24.63 lag=-2(23.86/24.63); direct-full=L524 (L524 internal blank x=69-132 Y=1.328; above=118.203 following=117.500; gate=4.000) |
| 405 | 405/F2 | L523 | L524 | L522 100.91/47.85 r_next=0.418 MAD_above=15.62 lag=0(15.62/15.62); L523 114.50/40.76 r_next=0.253 MAD_above=36.75 lag=-1(36.00/36.75); L524 84.50/59.48 r_next=0.896 MAD_above=52.19 lag=-1(52.09/52.19); L525 92.67/69.74 r_next=0.011 MAD_above=22.03 lag=-1(21.77/22.03); direct-full=L524 (L524 internal blank x=65-128 Y=1.422; above=116.062 following=113.000; gate=4.000) |
| 408 | 408/F2 | L522 | L524 | L521 99.41/47.43 r_next=0.868 MAD_above=15.54 lag=1(15.09/15.54); L522 100.53/46.36 r_next=0.366 MAD_above=15.74 lag=0(15.74/15.74); L523 116.47/40.86 r_next=0.227 MAD_above=38.77 lag=-2(37.77/38.77); L524 87.69/61.26 r_next=0.902 MAD_above=53.71 lag=-1(53.16/53.71); L525 92.24/66.81 r_next=0.021 MAD_above=19.55 lag=0(19.55/19.55); direct-full=L524 (L524 internal blank x=58-121 Y=1.297; above=117.766 following=113.000; gate=4.000) |
| 409 | 409/F2 | L523 | L524 | L522 100.12/47.83 r_next=0.397 MAD_above=16.57 lag=1(16.51/16.57); L523 116.01/44.17 r_next=0.310 MAD_above=40.58 lag=-2(39.54/40.58); L524 85.85/60.24 r_next=0.891 MAD_above=51.61 lag=-2(51.18/51.61); L525 92.32/67.26 r_next=0.026 MAD_above=21.00 lag=-1(20.46/21.00); direct-full=L524 (L524 internal blank x=60-123 Y=1.297; above=112.938 following=114.000; gate=4.000) |
| 411 | 411/F2 | L523 | L524 | L522 99.40/47.69 r_next=0.352 MAD_above=17.07 lag=1(16.59/17.07); L523 112.78/44.84 r_next=0.269 MAD_above=42.36 lag=-2(40.95/42.36); L524 83.41/61.04 r_next=0.883 MAD_above=53.94 lag=-2(53.44/53.94); L525 91.22/67.08 r_next=0.013 MAD_above=21.58 lag=-1(20.75/21.58); direct-full=L524 (L524 internal blank x=47-110 Y=1.359; above=111.922 following=108.000; gate=4.000) |
| 412 | 412/F2 | L523 | L524 | L522 101.44/47.75 r_next=0.316 MAD_above=16.20 lag=0(16.20/16.20); L523 119.97/45.73 r_next=0.353 MAD_above=45.41 lag=-3(43.81/45.41); L524 85.25/60.64 r_next=0.875 MAD_above=53.43 lag=-3(52.63/53.43); L525 92.14/69.69 r_next=-0.000 MAD_above=22.92 lag=-1(22.79/22.92); direct-full=L524 (L524 internal blank x=46-109 Y=1.375; above=114.641 following=114.500; gate=4.000) |
| 413 | 413/F2 | L523 | L524 | L522 101.85/47.75 r_next=0.382 MAD_above=17.46 lag=0(17.46/17.46); L523 117.56/45.33 r_next=0.342 MAD_above=41.39 lag=-1(41.08/41.39); L524 85.85/60.58 r_next=0.877 MAD_above=51.73 lag=1(51.53/51.73); L525 90.81/68.42 r_next=-0.017 MAD_above=22.17 lag=-1(22.15/22.17); direct-full=L524 (L524 internal blank x=59-122 Y=1.312; above=115.078 following=116.000; gate=4.000) |
| 415 | 415/F2 | L523 | L524 | L522 102.71/47.15 r_next=0.316 MAD_above=16.11 lag=0(16.11/16.11); L523 118.94/43.43 r_next=0.354 MAD_above=42.57 lag=-2(41.54/42.57); L524 86.05/60.38 r_next=0.889 MAD_above=48.94 lag=-1(48.79/48.94); L525 90.54/67.29 r_next=0.006 MAD_above=20.43 lag=-1(20.10/20.43); direct-full=L524 (L524 internal blank x=63-126 Y=1.344; above=118.797 following=112.000; gate=4.000) |
| 419 | 419/F2 | L523 | L524 | L522 99.08/46.87 r_next=0.356 MAD_above=15.63 lag=0(15.63/15.63); L523 115.65/43.45 r_next=0.340 MAD_above=41.68 lag=-1(41.67/41.68); L524 85.27/61.30 r_next=0.885 MAD_above=50.08 lag=-1(50.04/50.08); L525 89.76/66.90 r_next=-0.033 MAD_above=19.79 lag=-1(19.68/19.79); direct-full=L524 (L524 internal blank x=49-112 Y=1.297; above=114.438 following=117.000; gate=4.000) |
| 422 | 422/F2 | L523 | L524 | L522 100.47/47.62 r_next=0.293 MAD_above=16.62 lag=0(16.62/16.62); L523 119.45/42.24 r_next=0.392 MAD_above=45.17 lag=-3(43.79/45.17); L524 87.99/60.95 r_next=0.888 MAD_above=48.55 lag=-2(46.86/48.55); L525 92.44/68.28 r_next=0.041 MAD_above=20.46 lag=-1(20.31/20.46); direct-full=L524 (L524 internal blank x=51-114 Y=1.391; above=112.078 following=116.000; gate=4.000) |
| 424 | 424/F2 | L523 | L524 | L522 97.44/47.14 r_next=0.302 MAD_above=16.42 lag=0(16.42/16.42); L523 111.99/40.99 r_next=0.276 MAD_above=43.55 lag=-3(42.30/43.55); L524 84.68/59.32 r_next=0.876 MAD_above=49.08 lag=-3(46.98/49.08); L525 91.00/68.11 r_next=-0.041 MAD_above=22.12 lag=-2(21.33/22.12); direct-full=L524 (L524 internal blank x=61-124 Y=1.359; above=111.719 following=113.000; gate=4.000) |
| 425 | 425/F2 | L523 | L524 | L522 99.99/46.13 r_next=0.351 MAD_above=16.22 lag=0(16.22/16.22); L523 120.78/43.80 r_next=0.401 MAD_above=43.82 lag=-2(43.41/43.82); L524 85.33/60.32 r_next=0.888 MAD_above=49.27 lag=-3(47.18/49.27); L525 89.58/67.66 r_next=0.048 MAD_above=20.70 lag=-1(20.29/20.70); direct-full=L524 (L524 internal blank x=51-114 Y=1.328; above=112.875 following=111.500; gate=4.000) |
| 426 | 426/F2 | L523 | L524 | L522 98.53/45.82 r_next=0.341 MAD_above=16.00 lag=0(16.00/16.00); L523 119.37/48.23 r_next=0.417 MAD_above=46.53 lag=-3(45.87/46.53); L524 86.93/61.04 r_next=0.877 MAD_above=49.87 lag=-2(48.28/49.87); L525 91.78/67.85 r_next=0.021 MAD_above=21.57 lag=-1(21.22/21.57); direct-full=L524 (L524 internal blank x=51-114 Y=1.328; above=107.984 following=113.000; gate=4.000) |
| 427 | 427/F2 | L523 | L524 | L522 99.77/45.83 r_next=0.372 MAD_above=16.13 lag=0(16.13/16.13); L523 118.65/43.07 r_next=0.427 MAD_above=43.17 lag=-2(42.46/43.17); L524 85.44/61.44 r_next=0.855 MAD_above=47.40 lag=-2(45.51/47.40); L525 90.07/67.70 r_next=0.023 MAD_above=23.22 lag=-3(21.51/23.22); direct-full=L524 (L524 internal blank x=59-122 Y=1.344; above=111.906 following=111.000; gate=4.000) |
| 428 | 428/F2 | L522 | L524 | L521 98.53/48.50 r_next=0.869 MAD_above=17.70 lag=0(17.70/17.70); L522 99.71/45.99 r_next=0.069 MAD_above=16.24 lag=0(16.24/16.24); L523 104.60/50.96 r_next=0.648 MAD_above=53.82 lag=-2(53.61/53.82); L524 85.42/61.37 r_next=0.885 MAD_above=35.01 lag=-2(33.31/35.01); L525 92.76/69.22 r_next=0.002 MAD_above=21.87 lag=-1(21.79/21.87); direct-full=L524 (L524 internal blank x=62-125 Y=1.359; above=115.422 following=112.500; gate=4.000) |
| 431 | 431/F2 | L522 | L523 | L521 100.12/48.24 r_next=0.868 MAD_above=17.14 lag=0(17.14/17.14); L522 102.61/45.62 r_next=-0.021 MAD_above=15.86 lag=1(15.78/15.86); L523 97.10/58.24 r_next=0.772 MAD_above=62.20 lag=32(61.27/62.20); L524 85.50/60.51 r_next=0.896 MAD_above=26.14 lag=-3(23.96/26.14); direct-full=L523 (L523 persistent three-third step; thirds=7.171,3.566,4.164; correlation above/next=-0.110/0.828; middle coherence=0.919) |
| 435 | 435/F2 | L524 | L523 | L522 102.29/46.02 r_next=0.189 MAD_above=16.11 lag=-1(16.08/16.11); L523 82.84/57.82 r_next=0.712 MAD_above=50.38 lag=-1(50.24/50.38); L524 87.68/61.28 r_next=0.887 MAD_above=29.50 lag=-1(29.12/29.50); L525 91.55/69.19 r_next=0.008 MAD_above=21.12 lag=0(21.12/21.12); direct-full=L523 (L523 internal blank x=71-134 Y=1.641; above=119.625 following=85.000; gate=4.000) |
| 437 | 437/F2 | L521 | L523 | L520 99.14/48.02 r_next=0.831 MAD_above=14.75 lag=1(14.44/14.75); L521 100.58/47.67 r_next=0.869 MAD_above=16.74 lag=1(16.73/16.74); L522 104.65/45.29 r_next=-0.036 MAD_above=16.85 lag=-1(16.79/16.85); L523 90.42/63.29 r_next=0.826 MAD_above=69.08 lag=31(66.66/69.08); L524 88.57/63.16 r_next=0.874 MAD_above=23.11 lag=-3(21.34/23.11); direct-full=L523 (L523 persistent three-third step; thirds=8.371,4.230,4.094; correlation above/next=-0.115/0.893; middle coherence=0.920) |
| 444 | 444/F2 | L523 | L524 | L522 102.31/45.85 r_next=0.100 MAD_above=16.29 lag=0(16.29/16.29); L523 102.39/57.47 r_next=0.631 MAD_above=57.56 lag=0(57.56/57.56); L524 85.11/61.07 r_next=0.872 MAD_above=35.27 lag=-3(32.43/35.27); L525 91.87/68.11 r_next=0.030 MAD_above=22.04 lag=-2(21.33/22.04); direct-full=L524 (L524 internal blank x=42-105 Y=1.344; above=125.000 following=113.000; gate=4.000) |
| 445 | 445/F2 | L523 | L524 | L522 103.91/45.59 r_next=0.083 MAD_above=16.64 lag=0(16.64/16.64); L523 105.27/53.25 r_next=0.638 MAD_above=54.61 lag=0(54.61/54.61); L524 89.81/62.39 r_next=0.897 MAD_above=34.26 lag=-1(33.41/34.26); L525 92.62/68.40 r_next=0.007 MAD_above=20.41 lag=-1(20.20/20.41); direct-full=L524 (L524 internal blank x=60-123 Y=1.375; above=104.578 following=121.000; gate=4.000) |
| 447 | 447/F2 | L523 | L524 | L522 102.62/46.21 r_next=0.074 MAD_above=16.91 lag=0(16.91/16.91); L523 103.20/55.62 r_next=0.656 MAD_above=57.17 lag=-2(56.94/57.17); L524 88.02/62.05 r_next=0.874 MAD_above=33.21 lag=-3(30.65/33.21); L525 91.94/69.30 r_next=0.023 MAD_above=22.73 lag=-1(22.20/22.73); direct-full=L524 (L524 internal blank x=61-124 Y=1.344; above=89.641 following=116.000; gate=4.000) |
| 448 | 448/F2 | L523 | L524 | L522 104.05/45.53 r_next=0.101 MAD_above=17.03 lag=0(17.03/17.03); L523 111.85/49.67 r_next=0.546 MAD_above=52.13 lag=30(50.85/52.13); L524 86.76/60.02 r_next=0.869 MAD_above=41.16 lag=-3(39.44/41.16); L525 92.11/68.88 r_next=0.027 MAD_above=22.15 lag=-1(21.08/22.15); direct-full=L524 (L524 internal blank x=64-127 Y=1.375; above=125.344 following=110.000; gate=4.000) |
| 449 | 449/F2 | L521 | L524 | L520 98.56/47.33 r_next=0.820 MAD_above=13.49 lag=0(13.49/13.49); L521 103.18/48.88 r_next=0.854 MAD_above=17.36 lag=1(17.23/17.36); L522 104.50/45.26 r_next=0.068 MAD_above=17.18 lag=0(17.18/17.18); L523 110.01/51.60 r_next=0.553 MAD_above=54.66 lag=22(53.28/54.66); L524 88.32/62.25 r_next=0.874 MAD_above=40.12 lag=-3(36.49/40.12); L525 92.69/67.61 r_next=-0.007 MAD_above=21.44 lag=-1(20.83/21.44); direct-full=L524 (L524 internal blank x=59-122 Y=1.375; above=126.422 following=117.000; gate=4.000) |
| 450 | 450/F2 | L523 | L524 | L522 105.72/46.38 r_next=0.083 MAD_above=18.15 lag=1(17.86/18.15); L523 116.92/49.56 r_next=0.542 MAD_above=54.02 lag=25(52.60/54.02); L524 88.91/61.59 r_next=0.869 MAD_above=41.23 lag=-2(39.07/41.23); L525 92.93/68.17 r_next=0.027 MAD_above=21.30 lag=0(21.30/21.30); direct-full=L524 (L524 internal blank x=59-122 Y=1.375; above=135.578 following=117.000; gate=4.000) |
| 451 | 451/F2 | L523 | L524 | L522 105.01/45.51 r_next=0.024 MAD_above=17.28 lag=-1(17.05/17.28); L523 111.50/49.18 r_next=0.605 MAD_above=53.81 lag=24(52.83/53.81); L524 87.35/61.92 r_next=0.882 MAD_above=37.66 lag=-2(36.56/37.66); L525 92.56/67.60 r_next=-0.016 MAD_above=20.63 lag=0(20.63/20.63); direct-full=L524 (L524 internal blank x=66-129 Y=1.328; above=124.047 following=116.000; gate=4.000) |
| 452 | 452/F2 | L522 | L524 | L521 102.33/46.93 r_next=0.860 MAD_above=17.00 lag=0(17.00/17.00); L522 104.36/45.85 r_next=0.078 MAD_above=15.80 lag=0(15.80/15.80); L523 113.09/49.60 r_next=0.592 MAD_above=53.03 lag=-2(52.73/53.03); L524 85.51/60.67 r_next=0.876 MAD_above=39.55 lag=-3(35.70/39.55); L525 90.33/67.51 r_next=0.013 MAD_above=20.95 lag=-2(20.16/20.95); direct-full=L524 (L524 internal blank x=75-138 Y=1.328; above=123.641 following=109.000; gate=4.000) |
| 453 | 453/F2 | L523 | L524 | L522 105.08/45.92 r_next=0.222 MAD_above=16.07 lag=0(16.07/16.07); L523 119.10/44.34 r_next=0.484 MAD_above=46.50 lag=-2(45.66/46.50); L524 87.26/61.73 r_next=0.887 MAD_above=45.05 lag=-2(43.59/45.05); L525 91.13/68.01 r_next=0.014 MAD_above=20.31 lag=0(20.31/20.31); direct-full=L524 (L524 internal blank x=68-131 Y=1.344; above=121.797 following=114.000; gate=4.000) |
| 454 | 454/F2 | L523 | L524 | L522 102.54/44.40 r_next=0.154 MAD_above=15.09 lag=0(15.09/15.09); L523 114.18/43.43 r_next=0.538 MAD_above=46.89 lag=-3(46.54/46.89); L524 83.61/59.92 r_next=0.890 MAD_above=42.30 lag=-3(39.38/42.30); L525 89.22/67.33 r_next=0.055 MAD_above=20.76 lag=0(20.76/20.76); direct-full=L524 (L524 internal blank x=59-122 Y=1.328; above=116.688 following=106.000; gate=4.000) |
| 455 | 455/F2 | L522 | L524 | L521 101.80/47.49 r_next=0.873 MAD_above=17.88 lag=1(17.44/17.88); L522 103.75/46.52 r_next=0.181 MAD_above=16.12 lag=0(16.12/16.12); L523 114.65/43.78 r_next=0.531 MAD_above=48.07 lag=-2(47.67/48.07); L524 86.39/62.28 r_next=0.853 MAD_above=43.18 lag=-2(41.01/43.18); L525 90.22/67.53 r_next=0.022 MAD_above=22.88 lag=-2(21.62/22.88); direct-full=L524 (L524 internal blank x=46-109 Y=1.391; above=121.312 following=114.500; gate=4.000) |
| 456 | 456/F2 | L523 | L524 | L522 103.15/45.95 r_next=0.283 MAD_above=17.26 lag=0(17.26/17.26); L523 119.14/41.79 r_next=0.449 MAD_above=45.00 lag=-3(43.96/45.00); L524 84.45/59.35 r_next=0.874 MAD_above=46.44 lag=-2(45.40/46.44); L525 89.35/67.38 r_next=-0.004 MAD_above=21.09 lag=0(21.09/21.09); direct-full=L524 (L524 internal blank x=89-152 Y=1.375; above=120.000 following=111.500; gate=4.000) |
| 458 | 458/F2 | L523 | L524 | L522 102.50/46.82 r_next=0.364 MAD_above=16.43 lag=0(16.43/16.43); L523 119.45/45.41 r_next=0.419 MAD_above=44.68 lag=-3(44.01/44.68); L524 85.28/61.33 r_next=0.879 MAD_above=49.72 lag=-3(47.70/49.72); L525 91.74/68.97 r_next=0.033 MAD_above=22.21 lag=-1(21.51/22.21); direct-full=L524 (L524 internal blank x=61-124 Y=1.359; above=118.438 following=111.000; gate=4.000) |
| 459 | 459/F2 | L523 | L524 | L522 101.41/45.95 r_next=0.352 MAD_above=15.39 lag=0(15.39/15.39); L523 118.19/42.74 r_next=0.462 MAD_above=42.57 lag=-1(42.40/42.57); L524 86.68/61.12 r_next=0.885 MAD_above=44.51 lag=0(44.51/44.51); L525 90.45/66.37 r_next=-0.008 MAD_above=20.29 lag=-1(19.89/20.29); direct-full=L524 (L524 internal blank x=60-123 Y=1.391; above=119.828 following=113.000; gate=4.000) |
| 460 | 460/F2 | L523 | L524 | L522 100.38/46.12 r_next=0.318 MAD_above=15.93 lag=0(15.93/15.93); L523 118.85/44.81 r_next=0.481 MAD_above=45.51 lag=-2(44.82/45.51); L524 84.10/60.79 r_next=0.881 MAD_above=46.98 lag=-2(45.68/46.98); L525 89.80/67.30 r_next=0.015 MAD_above=20.34 lag=0(20.34/20.34); direct-full=L524 (L524 internal blank x=83-146 Y=1.297; above=117.516 following=110.000; gate=4.000) |
| 461 | 461/F2 | L523 | L524 | L522 101.32/46.56 r_next=0.323 MAD_above=16.20 lag=0(16.20/16.20); L523 118.13/44.90 r_next=0.476 MAD_above=44.84 lag=-2(44.41/44.84); L524 84.91/59.73 r_next=0.883 MAD_above=46.62 lag=-1(46.36/46.62); L525 90.26/67.75 r_next=0.062 MAD_above=21.40 lag=-1(20.94/21.40); direct-full=L524 (L524 internal blank x=60-123 Y=1.266; above=116.922 following=110.500; gate=4.000) |
| 462 | 462/F2 | L523 | L524 | L522 99.85/46.56 r_next=0.397 MAD_above=16.14 lag=-1(15.99/16.14); L523 123.78/47.35 r_next=0.412 MAD_above=45.79 lag=-2(45.39/45.79); L524 83.90/60.32 r_next=0.900 MAD_above=49.82 lag=-1(49.38/49.82); L525 89.10/66.78 r_next=0.027 MAD_above=18.97 lag=0(18.97/18.97); direct-full=L524 (L524 internal blank x=74-137 Y=1.359; above=116.359 following=110.000; gate=4.000) |
| 464 | 464/F2 | L523 | L524 | L522 97.89/45.52 r_next=0.408 MAD_above=16.25 lag=0(16.25/16.25); L523 122.45/47.27 r_next=0.454 MAD_above=45.91 lag=-2(45.64/45.91); L524 82.33/59.63 r_next=0.888 MAD_above=50.59 lag=-2(49.77/50.59); L525 88.50/67.04 r_next=0.029 MAD_above=20.36 lag=-1(20.23/20.36); direct-full=L524 (L524 internal blank x=67-130 Y=1.328; above=117.359 following=108.000; gate=4.000) |
| 465 | 465/F2 | L523 | L524 | L522 99.23/44.96 r_next=0.318 MAD_above=16.40 lag=0(16.40/16.40); L523 118.04/42.65 r_next=0.419 MAD_above=42.50 lag=0(42.50/42.50); L524 84.36/59.63 r_next=0.881 MAD_above=46.77 lag=-1(46.24/46.77); L525 89.05/66.88 r_next=0.028 MAD_above=21.23 lag=-1(21.15/21.23); direct-full=L524 (L524 internal blank x=53-116 Y=1.312; above=116.250 following=113.000; gate=4.000) |
| 467 | 467/F2 | L523 | L524 | L522 97.87/47.30 r_next=0.152 MAD_above=17.46 lag=1(17.41/17.46); L523 120.57/42.70 r_next=0.369 MAD_above=48.00 lag=0(48.00/48.00); L524 87.55/60.17 r_next=0.895 MAD_above=47.32 lag=-2(46.51/47.32); L525 91.50/64.45 r_next=0.009 MAD_above=19.36 lag=0(19.36/19.36); direct-full=L524 (L524 internal blank x=57-120 Y=1.359; above=116.266 following=115.500; gate=4.000) |
| 468 | 468/F2 | L523 | L524 | L522 98.98/47.47 r_next=0.168 MAD_above=17.16 lag=1(16.55/17.16); L523 119.41/43.45 r_next=0.302 MAD_above=48.07 lag=0(48.07/48.07); L524 87.17/60.53 r_next=0.897 MAD_above=48.98 lag=-2(47.18/48.98); L525 91.27/65.58 r_next=0.014 MAD_above=19.10 lag=0(19.10/19.10); direct-full=L524 (L524 internal blank x=65-128 Y=1.328; above=116.094 following=121.000; gate=4.000) |
| 469 | 469/F2 | L523 | L524 | L522 97.03/54.15 r_next=0.369 MAD_above=7.37 lag=0(7.37/7.37); L523 69.96/40.00 r_next=0.507 MAD_above=45.29 lag=-3(44.97/45.29); L524 61.04/47.89 r_next=0.924 MAD_above=32.46 lag=-2(32.05/32.46); L525 65.96/53.30 r_next=0.018 MAD_above=13.40 lag=0(13.40/13.40); direct-full=L524 (L524 internal blank x=61-124 Y=1.406; above=85.516 following=81.000; gate=4.000) |
| 470 | 470/F2 | L523 | L524 | L522 97.30/55.97 r_next=0.173 MAD_above=7.53 lag=0(7.53/7.53); L523 77.69/42.57 r_next=0.587 MAD_above=48.40 lag=0(48.40/48.40); L524 61.71/49.88 r_next=0.929 MAD_above=31.49 lag=-2(30.86/31.49); L525 67.55/55.57 r_next=-0.013 MAD_above=13.90 lag=0(13.90/13.90); direct-full=L524 (L524 internal blank x=63-126 Y=1.344; above=85.234 following=81.500; gate=4.000) |
| 471 | 471/F2 | L523 | L524 | L522 98.76/54.60 r_next=0.118 MAD_above=7.59 lag=0(7.59/7.59); L523 80.57/41.77 r_next=0.545 MAD_above=50.29 lag=-2(49.89/50.29); L524 62.45/49.92 r_next=0.919 MAD_above=33.30 lag=-1(33.25/33.30); L525 65.58/55.86 r_next=-0.021 MAD_above=14.06 lag=-1(14.01/14.06); direct-full=L524 (L524 internal blank x=60-123 Y=1.406; above=92.250 following=78.000; gate=4.000) |
| 472 | 472/F2 | L523 | L524 | L522 95.05/54.72 r_next=0.287 MAD_above=7.54 lag=0(7.54/7.54); L523 74.06/42.05 r_next=0.605 MAD_above=46.37 lag=0(46.37/46.37); L524 60.40/48.84 r_next=0.932 MAD_above=29.64 lag=-2(28.51/29.64); L525 65.07/54.21 r_next=-0.000 MAD_above=13.90 lag=0(13.90/13.90); direct-full=L524 (L524 internal blank x=63-126 Y=1.359; above=86.578 following=81.500; gate=4.000) |
| 473 | 473/F2 | L523 | L524 | L522 95.94/55.55 r_next=0.210 MAD_above=7.18 lag=1(6.94/7.18); L523 75.97/39.52 r_next=0.672 MAD_above=47.38 lag=17(47.02/47.38); L524 59.61/49.13 r_next=0.924 MAD_above=28.07 lag=-3(27.05/28.07); L525 62.96/54.96 r_next=0.036 MAD_above=13.97 lag=1(13.90/13.97); direct-full=L524 (L524 internal blank x=62-125 Y=1.359; above=86.375 following=78.500; gate=4.000) |
| 474 | 474/F2 | L523 | L524 | L522 97.84/56.10 r_next=0.248 MAD_above=7.44 lag=0(7.44/7.44); L523 79.19/40.78 r_next=0.669 MAD_above=46.61 lag=0(46.61/46.61); L524 60.86/49.10 r_next=0.941 MAD_above=28.83 lag=-2(28.52/28.83); L525 66.94/56.61 r_next=0.036 MAD_above=12.90 lag=1(12.85/12.90); direct-full=L524 (L524 internal blank x=53-116 Y=1.328; above=87.531 following=81.000; gate=4.000) |
| 476 | 476/F2 | L523 | L524 | L522 96.78/55.41 r_next=0.241 MAD_above=7.17 lag=1(7.16/7.17); L523 77.36/39.87 r_next=0.676 MAD_above=47.37 lag=4(46.90/47.37); L524 59.90/48.68 r_next=0.899 MAD_above=28.33 lag=-4(27.11/28.33); L525 65.34/53.47 r_next=-0.023 MAD_above=13.90 lag=0(13.90/13.90); direct-full=L524 (L524 internal blank x=72-135 Y=1.344; above=87.938 following=77.000; gate=4.000) |
| 477 | 477/F2 | L523 | L524 | L522 97.42/54.99 r_next=0.154 MAD_above=7.37 lag=1(7.33/7.37); L523 79.85/38.64 r_next=0.633 MAD_above=49.21 lag=15(48.66/49.21); L524 58.72/49.48 r_next=0.902 MAD_above=31.46 lag=0(31.46/31.46); L525 64.96/54.70 r_next=-0.003 MAD_above=14.89 lag=0(14.89/14.89); direct-full=L524 (L524 internal blank x=64-127 Y=1.359; above=88.141 following=76.000; gate=4.000) |
| 478 | 478/F2 | L523 | L524 | L522 94.16/55.78 r_next=0.144 MAD_above=6.92 lag=0(6.92/6.92); L523 76.76/38.89 r_next=0.579 MAD_above=50.25 lag=19(48.76/50.25); L524 59.01/49.70 r_next=0.927 MAD_above=31.61 lag=-2(31.11/31.61); L525 64.82/53.75 r_next=-0.025 MAD_above=12.98 lag=0(12.98/12.98); direct-full=L524 (L524 internal blank x=51-114 Y=1.312; above=84.047 following=78.000; gate=4.000) |
| 479 | 479/F2 | L523 | L524 | L522 95.40/54.51 r_next=0.168 MAD_above=7.00 lag=0(7.00/7.00); L523 77.10/40.13 r_next=0.564 MAD_above=49.33 lag=16(48.18/49.33); L524 58.89/48.43 r_next=0.939 MAD_above=31.23 lag=-3(30.75/31.23); L525 65.61/54.49 r_next=-0.004 MAD_above=12.83 lag=0(12.83/12.83); direct-full=L524 (L524 internal blank x=74-137 Y=1.344; above=85.469 following=79.000; gate=4.000) |
| 485 | 485/F2 | L523 | L524 | L522 95.27/57.01 r_next=0.252 MAD_above=6.78 lag=0(6.78/6.78); L523 75.79/40.77 r_next=0.655 MAD_above=48.42 lag=0(48.42/48.42); L524 58.51/50.26 r_next=0.958 MAD_above=29.16 lag=-3(27.40/29.16); L525 61.69/53.65 r_next=-0.016 MAD_above=10.15 lag=-1(9.85/10.15); direct-full=L524 (L524 internal blank x=43-106 Y=1.312; above=91.125 following=75.000; gate=4.000) |
| 486 | 486/F2 | L523 | L524 | L522 94.21/56.90 r_next=0.274 MAD_above=7.65 lag=1(7.34/7.65); L523 75.86/41.40 r_next=0.695 MAD_above=47.75 lag=0(47.75/47.75); L524 56.86/48.03 r_next=0.961 MAD_above=26.66 lag=-2(26.01/26.66); L525 60.92/52.92 r_next=-0.026 MAD_above=9.36 lag=0(9.36/9.36); direct-full=L524 (L524 internal blank x=56-119 Y=1.359; above=86.594 following=77.000; gate=4.000) |
| 488 | 488/F2 | L523 | L524 | L522 94.64/55.68 r_next=0.151 MAD_above=7.42 lag=0(7.42/7.42); L523 78.78/41.22 r_next=0.673 MAD_above=50.27 lag=12(49.69/50.27); L524 57.92/50.20 r_next=0.943 MAD_above=29.15 lag=-2(28.58/29.15); L525 59.95/53.90 r_next=0.009 MAD_above=11.87 lag=-1(11.61/11.87); direct-full=L524 (L524 internal blank x=102-165 Y=1.344; above=80.984 following=78.000; gate=4.000) |
| 489 | 489/F2 | L523 | L524 | L522 94.29/55.82 r_next=0.219 MAD_above=6.02 lag=0(6.02/6.02); L523 75.91/39.75 r_next=0.691 MAD_above=49.77 lag=0(49.77/49.77); L524 55.21/48.49 r_next=0.962 MAD_above=27.09 lag=-1(27.02/27.09); L525 57.49/52.86 r_next=-0.008 MAD_above=9.59 lag=-1(9.33/9.59); direct-full=L524 (L524 internal blank x=52-115 Y=1.391; above=83.656 following=72.000; gate=4.000) |
| 490 | 490/F2 | L523 | L524 | L522 92.08/56.55 r_next=0.227 MAD_above=7.15 lag=0(7.15/7.15); L523 76.97/41.39 r_next=0.635 MAD_above=50.14 lag=13(49.93/50.14); L524 53.92/48.29 r_next=0.954 MAD_above=28.96 lag=-2(28.53/28.96); L525 58.38/53.17 r_next=-0.028 MAD_above=11.50 lag=1(11.20/11.50); direct-full=L524 (L524 internal blank x=123-186 Y=1.359; above=88.906 following=74.000; gate=4.000) |
| 492 | 492/F2 | L523 | L524 | L522 91.69/55.39 r_next=0.100 MAD_above=7.09 lag=0(7.09/7.09); L523 76.63/40.27 r_next=0.685 MAD_above=50.50 lag=13(50.15/50.50); L524 52.80/47.58 r_next=0.963 MAD_above=27.84 lag=0(27.84/27.84); L525 54.35/53.60 r_next=0.064 MAD_above=9.81 lag=1(9.81/9.81); direct-full=L524 (L524 internal blank x=95-158 Y=1.297; above=79.625 following=72.000; gate=4.000) |
| 494 | 494/F2 | L523 | L524 | L522 92.10/55.68 r_next=0.174 MAD_above=6.78 lag=0(6.78/6.78); L523 73.94/40.64 r_next=0.682 MAD_above=51.18 lag=15(49.83/51.18); L524 50.71/48.35 r_next=0.972 MAD_above=28.05 lag=-2(27.40/28.05); L525 58.13/53.37 r_next=0.015 MAD_above=9.96 lag=0(9.96/9.96); direct-full=L524 (L524 internal blank x=44-107 Y=1.375; above=86.156 following=69.500; gate=4.000) |
| 496 | 496/F2 | L523 | L524 | L522 89.50/55.94 r_next=0.167 MAD_above=6.84 lag=0(6.84/6.84); L523 69.74/41.09 r_next=0.683 MAD_above=51.21 lag=11(50.95/51.21); L524 53.58/48.73 r_next=0.972 MAD_above=27.17 lag=-1(27.01/27.17); L525 58.67/54.05 r_next=0.025 MAD_above=9.74 lag=0(9.74/9.74); direct-full=L524 (L524 internal blank x=102-165 Y=1.344; above=74.844 following=73.000; gate=4.000) |
| 501 | 501/F2 | L523 | L524 | L522 89.32/57.31 r_next=0.129 MAD_above=6.82 lag=0(6.82/6.82); L523 73.61/45.46 r_next=0.679 MAD_above=51.92 lag=1(51.80/51.92); L524 53.71/49.03 r_next=0.947 MAD_above=27.73 lag=1(27.71/27.73); L525 56.46/55.26 r_next=0.003 MAD_above=11.93 lag=-1(11.90/11.93); direct-full=L524 (L524 internal blank x=45-108 Y=1.391; above=81.156 following=73.000; gate=4.000) |
| 503 | 503/F2 | L523 | L524 | L522 88.93/58.20 r_next=0.351 MAD_above=6.90 lag=0(6.90/6.90); L523 66.36/40.86 r_next=0.689 MAD_above=45.69 lag=2(45.53/45.69); L524 52.79/49.28 r_next=0.964 MAD_above=26.77 lag=0(26.77/26.77); L525 56.13/54.57 r_next=-0.002 MAD_above=10.29 lag=0(10.29/10.29); direct-full=L524 (L524 internal blank x=54-117 Y=1.312; above=77.188 following=71.000; gate=4.000) |
| 504 | 504/F2 | L523 | L524 | L522 87.51/58.70 r_next=0.124 MAD_above=7.38 lag=1(7.06/7.38); L523 74.92/43.47 r_next=0.673 MAD_above=52.80 lag=0(52.80/52.80); L524 53.76/49.61 r_next=0.938 MAD_above=28.46 lag=-1(28.27/28.46); L525 58.40/55.24 r_next=0.039 MAD_above=13.89 lag=-1(13.59/13.89); direct-full=L524 (L524 internal blank x=47-110 Y=1.344; above=84.312 following=68.500; gate=4.000) |
| 509 | 509/F2 | L523 | L524 | L522 92.85/59.23 r_next=0.286 MAD_above=7.91 lag=0(7.91/7.91); L523 74.00/41.42 r_next=0.680 MAD_above=47.94 lag=1(47.87/47.94); L524 59.24/51.05 r_next=0.942 MAD_above=28.68 lag=-2(28.24/28.68); L525 61.13/57.25 r_next=0.010 MAD_above=12.60 lag=-2(11.98/12.60); direct-full=L524 (L524 internal blank x=47-110 Y=1.344; above=86.531 following=79.000; gate=4.000) |
| 511 | 511/F2 | L523 | L524 | L522 93.72/58.42 r_next=0.135 MAD_above=7.07 lag=0(7.07/7.07); L523 78.20/41.45 r_next=0.590 MAD_above=53.40 lag=15(51.35/53.40); L524 59.07/50.61 r_next=0.945 MAD_above=31.05 lag=-2(30.21/31.05); L525 60.84/57.59 r_next=0.015 MAD_above=13.25 lag=-2(12.84/13.25); direct-full=L524 (L524 internal blank x=67-130 Y=1.328; above=84.031 following=79.000; gate=4.000) |
| 513 | 513/F2 | L523 | L524 | L522 98.30/58.76 r_next=0.086 MAD_above=7.24 lag=0(7.24/7.24); L523 82.90/44.09 r_next=0.591 MAD_above=54.45 lag=19(52.97/54.45); L524 61.60/50.79 r_next=0.960 MAD_above=30.76 lag=-2(30.45/30.76); L525 61.56/56.92 r_next=-0.006 MAD_above=11.88 lag=0(11.88/11.88); direct-full=L524 (L524 internal blank x=50-113 Y=1.391; above=87.906 following=83.000; gate=4.000) |
| 514 | 514/F2 | L523 | L524 | L522 98.39/58.25 r_next=0.234 MAD_above=7.20 lag=0(7.20/7.20); L523 80.36/43.59 r_next=0.694 MAD_above=50.72 lag=0(50.72/50.72); L524 60.12/52.56 r_next=0.955 MAD_above=29.94 lag=-1(29.67/29.94); L525 63.95/59.01 r_next=-0.002 MAD_above=12.95 lag=0(12.95/12.95); direct-full=L524 (L524 internal blank x=55-118 Y=1.375; above=93.391 following=82.000; gate=4.000) |
| 515 | 515/F2 | L523 | L524 | L522 98.85/60.01 r_next=0.230 MAD_above=7.03 lag=0(7.03/7.03); L523 79.32/41.84 r_next=0.686 MAD_above=51.84 lag=-1(51.83/51.84); L524 62.95/53.04 r_next=0.957 MAD_above=28.85 lag=0(28.85/28.85); L525 64.06/58.31 r_next=-0.032 MAD_above=12.28 lag=0(12.28/12.28); direct-full=L524 (L524 internal blank x=52-115 Y=1.344; above=88.453 following=87.000; gate=4.000) |
| 516 | 516/F2 | L523 | L524 | L522 98.95/59.57 r_next=0.230 MAD_above=6.81 lag=0(6.81/6.81); L523 78.19/42.37 r_next=0.684 MAD_above=50.90 lag=0(50.90/50.90); L524 60.84/52.87 r_next=0.947 MAD_above=30.83 lag=-3(29.53/30.83); L525 66.22/57.96 r_next=-0.001 MAD_above=13.18 lag=-1(13.02/13.18); direct-full=L524 (L524 internal blank x=60-123 Y=1.344; above=88.578 following=75.500; gate=4.000) |
| 518 | 518/F2 | L523 | L524 | L522 99.89/58.34 r_next=0.187 MAD_above=7.26 lag=0(7.26/7.26); L523 80.90/42.50 r_next=0.691 MAD_above=51.95 lag=2(51.71/51.95); L524 60.05/52.47 r_next=0.952 MAD_above=28.07 lag=0(28.07/28.07); L525 64.27/59.11 r_next=0.015 MAD_above=13.05 lag=-1(12.83/13.05); direct-full=L524 (L524 internal blank x=61-124 Y=1.344; above=90.734 following=81.500; gate=4.000) |
| 521 | 521/F2 | L523 | L524 | L522 99.65/58.47 r_next=0.263 MAD_above=7.63 lag=1(7.05/7.63); L523 79.03/43.08 r_next=0.668 MAD_above=49.94 lag=-1(49.93/49.94); L524 62.73/52.40 r_next=0.969 MAD_above=29.57 lag=-4(26.76/29.57); L525 65.39/56.99 r_next=-0.005 MAD_above=9.50 lag=-1(9.42/9.50); direct-full=L524 (L524 internal blank x=47-110 Y=1.359; above=91.578 following=83.500; gate=4.000) |
| 522 | 522/F2 | L523 | L524 | L522 99.28/58.42 r_next=0.143 MAD_above=7.22 lag=0(7.22/7.22); L523 82.53/41.30 r_next=0.665 MAD_above=52.90 lag=11(52.17/52.90); L524 60.80/51.89 r_next=0.970 MAD_above=30.04 lag=-2(29.41/30.04); L525 65.71/58.17 r_next=0.037 MAD_above=10.91 lag=-1(10.36/10.91); direct-full=L524 (L524 internal blank x=54-117 Y=1.328; above=90.828 following=78.000; gate=4.000) |
| 526 | 526/F2 | L523 | L524 | L522 97.09/59.22 r_next=0.368 MAD_above=7.12 lag=0(7.12/7.12); L523 73.47/42.28 r_next=0.613 MAD_above=46.31 lag=1(46.29/46.31); L524 62.62/52.82 r_next=0.968 MAD_above=30.00 lag=-2(29.43/30.00); L525 66.64/57.36 r_next=0.007 MAD_above=10.75 lag=0(10.75/10.75); direct-full=L524 (L524 internal blank x=55-118 Y=1.312; above=90.484 following=84.000; gate=4.000) |
| 527 | 527/F2 | L523 | L524 | L522 96.11/59.10 r_next=0.357 MAD_above=7.26 lag=1(7.00/7.26); L523 73.87/42.98 r_next=0.654 MAD_above=46.99 lag=0(46.99/46.99); L524 62.86/52.43 r_next=0.969 MAD_above=28.44 lag=-1(28.31/28.44); L525 65.50/55.62 r_next=0.002 MAD_above=9.82 lag=0(9.82/9.82); direct-full=L524 (L524 internal blank x=45-108 Y=1.375; above=89.266 following=85.000; gate=4.000) |
| 528 | 528/F2 | L523 | L524 | L522 98.36/57.76 r_next=0.384 MAD_above=7.05 lag=0(7.05/7.05); L523 77.07/41.49 r_next=0.589 MAD_above=45.16 lag=-2(44.99/45.16); L524 60.72/51.27 r_next=0.955 MAD_above=30.48 lag=-3(29.44/30.48); L525 66.34/57.67 r_next=0.005 MAD_above=12.51 lag=-1(12.38/12.51); direct-full=L524 (L524 internal blank x=57-120 Y=1.281; above=92.875 following=80.000; gate=4.000) |
| 529 | 529/F2 | L523 | L524 | L522 97.51/58.45 r_next=0.351 MAD_above=8.48 lag=1(8.25/8.48); L523 77.91/43.39 r_next=0.651 MAD_above=45.75 lag=-2(45.68/45.75); L524 61.39/51.62 r_next=0.957 MAD_above=28.49 lag=-2(27.82/28.49); L525 67.03/57.33 r_next=0.026 MAD_above=12.51 lag=0(12.51/12.51); direct-full=L524 (L524 internal blank x=54-117 Y=1.281; above=90.422 following=80.000; gate=4.000) |
| 530 | 530/F2 | L523 | L524 | L522 99.64/57.95 r_next=0.144 MAD_above=7.61 lag=0(7.61/7.61); L523 84.60/41.80 r_next=0.663 MAD_above=51.92 lag=-1(51.85/51.92); L524 61.36/51.37 r_next=0.960 MAD_above=29.45 lag=-1(29.27/29.45); L525 65.99/57.98 r_next=0.003 MAD_above=11.81 lag=0(11.81/11.81); direct-full=L524 (L524 internal blank x=40-103 Y=1.391; above=96.219 following=80.000; gate=4.000) |
| 531 | 531/F2 | L523 | L524 | L522 99.79/59.46 r_next=0.175 MAD_above=7.03 lag=0(7.03/7.03); L523 81.55/40.54 r_next=0.627 MAD_above=53.31 lag=7(52.88/53.31); L524 61.58/51.48 r_next=0.958 MAD_above=29.79 lag=-2(29.04/29.79); L525 67.43/57.83 r_next=0.035 MAD_above=12.33 lag=-1(12.00/12.33); direct-full=L524 (L524 internal blank x=55-118 Y=1.375; above=91.469 following=80.000; gate=4.000) |
| 532 | 532/F2 | L523 | L524 | L522 97.88/58.49 r_next=0.129 MAD_above=7.53 lag=0(7.53/7.53); L523 82.10/42.97 r_next=0.601 MAD_above=53.89 lag=10(53.26/53.89); L524 60.48/52.16 r_next=0.961 MAD_above=30.63 lag=0(30.63/30.63); L525 65.28/57.68 r_next=0.027 MAD_above=11.30 lag=0(11.30/11.30); direct-full=L524 (L524 internal blank x=41-104 Y=1.375; above=91.625 following=82.000; gate=4.000) |
| 533 | 533/F2 | L523 | L524 | L522 98.79/57.91 r_next=0.204 MAD_above=6.68 lag=0(6.68/6.68); L523 80.64/42.22 r_next=0.669 MAD_above=50.65 lag=-1(50.56/50.65); L524 61.94/51.91 r_next=0.956 MAD_above=28.74 lag=-2(27.37/28.74); L525 64.53/57.75 r_next=-0.034 MAD_above=11.46 lag=-1(11.24/11.46); direct-full=L524 (L524 internal blank x=44-107 Y=1.312; above=92.406 following=80.500; gate=4.000) |
| 534 | 534/F2 | L523 | L524 | L522 99.84/58.93 r_next=0.122 MAD_above=6.93 lag=0(6.93/6.93); L523 86.04/41.69 r_next=0.642 MAD_above=52.88 lag=-1(52.81/52.88); L524 62.54/51.66 r_next=0.964 MAD_above=30.99 lag=-3(30.06/30.99); L525 67.40/58.07 r_next=0.001 MAD_above=11.64 lag=-1(11.57/11.64); direct-full=L524 (L524 internal blank x=46-109 Y=1.297; above=94.109 following=83.000; gate=4.000) |
| 535 | 535/F2 | L523 | L524 | L522 98.70/57.86 r_next=0.258 MAD_above=7.73 lag=1(7.45/7.73); L523 81.73/42.70 r_next=0.675 MAD_above=49.67 lag=0(49.67/49.67); L524 61.87/52.95 r_next=0.955 MAD_above=29.97 lag=-3(28.69/29.97); L525 67.08/57.01 r_next=0.033 MAD_above=12.76 lag=-1(12.51/12.76); direct-full=L524 (L524 internal blank x=42-105 Y=1.344; above=99.078 following=81.000; gate=4.000) |
| 536 | 536/F2 | L523 | L524 | L522 98.00/58.81 r_next=0.370 MAD_above=7.01 lag=1(6.97/7.01); L523 78.14/41.18 r_next=0.629 MAD_above=45.98 lag=-2(45.80/45.98); L524 62.27/52.53 r_next=0.967 MAD_above=28.77 lag=-4(27.25/28.77); L525 66.62/58.09 r_next=-0.059 MAD_above=11.08 lag=0(11.08/11.08); direct-full=L524 (L524 internal blank x=47-110 Y=1.375; above=90.844 following=82.500; gate=4.000) |
| 539 | 539/F2 | L523 | L524 | L522 100.19/58.62 r_next=0.408 MAD_above=7.18 lag=1(7.14/7.18); L523 76.17/43.92 r_next=0.616 MAD_above=45.57 lag=0(45.57/45.57); L524 61.54/50.99 r_next=0.964 MAD_above=30.67 lag=-3(29.99/30.67); L525 66.42/59.01 r_next=0.003 MAD_above=12.91 lag=0(12.91/12.91); direct-full=L524 (L524 internal blank x=52-115 Y=1.391; above=88.578 following=79.000; gate=4.000) |
| 540 | 540/F2 | L523 | L524 | L522 100.07/58.01 r_next=0.322 MAD_above=7.03 lag=0(7.03/7.03); L523 79.74/41.12 r_next=0.657 MAD_above=46.83 lag=-1(46.76/46.83); L524 62.15/52.56 r_next=0.956 MAD_above=29.25 lag=-2(28.23/29.25); L525 65.93/57.44 r_next=0.030 MAD_above=11.47 lag=0(11.47/11.47); direct-full=L524 (L524 internal blank x=44-107 Y=1.359; above=94.969 following=83.500; gate=4.000) |
| 541 | 541/F2 | L523 | L524 | L522 99.58/58.53 r_next=0.234 MAD_above=7.59 lag=1(7.33/7.59); L523 79.78/42.23 r_next=0.680 MAD_above=50.67 lag=-1(50.59/50.67); L524 62.45/52.78 r_next=0.957 MAD_above=29.00 lag=-1(28.89/29.00); L525 66.69/57.61 r_next=-0.017 MAD_above=12.47 lag=0(12.47/12.47); direct-full=L524 (L524 internal blank x=53-116 Y=1.328; above=91.984 following=83.000; gate=4.000) |
| 542 | 542/F2 | L523 | L524 | L522 99.91/59.06 r_next=0.083 MAD_above=7.08 lag=0(7.08/7.08); L523 87.54/42.69 r_next=0.634 MAD_above=53.03 lag=-1(53.00/53.03); L524 62.32/51.06 r_next=0.959 MAD_above=31.43 lag=-1(31.02/31.43); L525 65.79/57.44 r_next=0.044 MAD_above=12.13 lag=0(12.13/12.13); direct-full=L524 (L524 internal blank x=60-123 Y=1.344; above=93.656 following=83.500; gate=4.000) |
| 544 | 544/F2 | L523 | L524 | L522 99.80/58.34 r_next=0.101 MAD_above=7.84 lag=0(7.84/7.84); L523 83.78/44.34 r_next=0.665 MAD_above=53.43 lag=-2(53.30/53.43); L524 60.98/51.65 r_next=0.963 MAD_above=30.42 lag=-3(29.64/30.42); L525 67.15/56.61 r_next=0.016 MAD_above=11.39 lag=-1(11.20/11.39); direct-full=L524 (L524 internal blank x=94-157 Y=1.375; above=89.797 following=81.000; gate=4.000) |
| 545 | 545/F2 | L523 | L524 | L522 100.27/58.23 r_next=0.186 MAD_above=7.00 lag=0(7.00/7.00); L523 78.93/46.32 r_next=0.673 MAD_above=52.04 lag=0(52.04/52.04); L524 62.81/51.29 r_next=0.955 MAD_above=28.63 lag=-1(28.26/28.63); L525 65.09/57.36 r_next=-0.021 MAD_above=12.41 lag=0(12.41/12.41); direct-full=L524 (L524 internal blank x=44-107 Y=1.359; above=89.594 following=82.000; gate=4.000) |
| 546 | 546/F2 | L523 | L524 | L522 100.08/59.11 r_next=0.310 MAD_above=8.05 lag=0(8.05/8.05); L523 81.40/40.92 r_next=0.640 MAD_above=46.95 lag=0(46.95/46.95); L524 62.36/51.78 r_next=0.956 MAD_above=29.55 lag=-2(29.00/29.55); L525 66.22/57.29 r_next=0.008 MAD_above=12.60 lag=0(12.60/12.60); direct-full=L524 (L524 internal blank x=51-114 Y=1.281; above=93.547 following=84.000; gate=4.000) |
| 547 | 547/F2 | L523 | L524 | L522 99.04/58.08 r_next=0.386 MAD_above=6.83 lag=1(6.70/6.83); L523 75.35/46.89 r_next=0.583 MAD_above=44.79 lag=0(44.79/44.79); L524 59.11/51.20 r_next=0.934 MAD_above=33.83 lag=-1(33.51/33.83); L525 65.54/57.76 r_next=0.031 MAD_above=14.65 lag=-3(14.24/14.65); direct-full=L524 (L524 internal blank x=50-113 Y=1.422; above=91.453 following=80.000; gate=4.000) |
| 548 | 548/F2 | L523 | L524 | L522 100.14/58.59 r_next=0.556 MAD_above=7.44 lag=1(7.42/7.44); L523 73.63/44.95 r_next=0.473 MAD_above=37.67 lag=0(37.67/37.67); L524 60.50/51.61 r_next=0.935 MAD_above=38.15 lag=-1(37.95/38.15); L525 65.31/57.67 r_next=-0.018 MAD_above=15.53 lag=-2(15.19/15.53); direct-full=L524 (L524 internal blank x=62-125 Y=1.438; above=95.594 following=77.000; gate=4.000) |
| 549 | 549/F2 | L522 | L524 | L521 100.62/58.55 r_next=0.986 MAD_above=7.34 lag=0(7.34/7.34); L522 101.25/58.64 r_next=0.589 MAD_above=7.19 lag=1(6.68/7.19); L523 68.85/46.89 r_next=0.483 MAD_above=38.71 lag=-2(38.54/38.71); L524 63.52/53.46 r_next=0.944 MAD_above=38.37 lag=-3(37.44/38.37); L525 66.25/58.19 r_next=0.019 MAD_above=13.34 lag=-1(12.83/13.34); direct-full=L524 (L524 internal blank x=44-107 Y=1.375; above=94.078 following=85.000; gate=4.000) |
| 550 | 550/F2 | L523 | L524 | L522 99.88/57.48 r_next=0.568 MAD_above=6.94 lag=0(6.94/6.94); L523 65.31/47.76 r_next=0.389 MAD_above=39.35 lag=0(39.35/39.35); L524 64.23/53.09 r_next=0.950 MAD_above=43.71 lag=-4(42.37/43.71); L525 67.55/57.45 r_next=0.001 MAD_above=12.25 lag=0(12.25/12.25); direct-full=L524 (L524 internal blank x=64-127 Y=1.391; above=94.297 following=80.000; gate=4.000) |
| 551 | 551/F2 | L522 | L524 | L521 102.91/58.21 r_next=0.988 MAD_above=7.89 lag=0(7.89/7.89); L522 103.26/57.65 r_next=0.584 MAD_above=6.95 lag=0(6.95/6.95); L523 71.45/46.77 r_next=0.452 MAD_above=36.87 lag=0(36.87/36.87); L524 64.40/51.75 r_next=0.942 MAD_above=38.74 lag=-4(36.70/38.74); L525 69.54/58.96 r_next=0.025 MAD_above=14.33 lag=-1(14.16/14.33); direct-full=L524 (L524 internal blank x=55-118 Y=1.344; above=95.594 following=86.000; gate=4.000) |
| 552 | 552/F2 | L522 | L524 | L521 103.23/58.80 r_next=0.988 MAD_above=7.31 lag=0(7.31/7.31); L522 102.86/58.70 r_next=0.524 MAD_above=6.71 lag=1(6.45/6.71); L523 73.43/47.55 r_next=0.435 MAD_above=40.01 lag=1(39.99/40.01); L524 65.82/52.22 r_next=0.950 MAD_above=41.55 lag=-4(40.52/41.55); L525 67.45/58.13 r_next=0.027 MAD_above=13.26 lag=0(13.26/13.26); direct-full=L524 (L524 internal blank x=56-119 Y=1.344; above=95.625 following=85.000; gate=4.000) |
| 554 | 554/F2 | L523 | L524 | L522 102.21/59.14 r_next=0.553 MAD_above=7.30 lag=0(7.30/7.30); L523 68.29/45.53 r_next=0.415 MAD_above=39.25 lag=-1(39.24/39.25); L524 64.03/53.30 r_next=0.949 MAD_above=42.34 lag=-3(41.17/42.34); L525 68.82/57.85 r_next=-0.020 MAD_above=13.54 lag=1(13.53/13.54); direct-full=L524 (L524 internal blank x=50-113 Y=1.297; above=91.594 following=83.000; gate=4.000) |
| 556 | 556/F2 | L523 | L524 | L522 102.13/59.14 r_next=0.507 MAD_above=7.62 lag=0(7.62/7.62); L523 72.45/50.12 r_next=0.430 MAD_above=40.39 lag=0(40.39/40.39); L524 64.40/52.66 r_next=0.959 MAD_above=42.33 lag=-3(41.16/42.33); L525 69.44/59.01 r_next=-0.003 MAD_above=12.25 lag=0(12.25/12.25); direct-full=L524 (L524 internal blank x=62-125 Y=1.422; above=91.812 following=83.000; gate=4.000) |
| 557 | 557/F2 | L523 | L524 | L522 102.01/58.87 r_next=0.586 MAD_above=7.14 lag=0(7.14/7.14); L523 69.45/49.31 r_next=0.413 MAD_above=38.75 lag=0(38.75/38.75); L524 66.22/53.28 r_next=0.953 MAD_above=42.65 lag=-1(42.50/42.65); L525 71.38/60.03 r_next=0.026 MAD_above=13.74 lag=-1(13.43/13.74); direct-full=L524 (L524 internal blank x=50-113 Y=1.312; above=95.656 following=89.000; gate=4.000) |
| 559 | 559/F2 | L523 | L524 | L522 103.17/59.24 r_next=0.482 MAD_above=8.00 lag=0(8.00/8.00); L523 75.92/49.99 r_next=0.373 MAD_above=41.69 lag=2(41.42/41.69); L524 64.17/52.09 r_next=0.954 MAD_above=45.62 lag=-3(44.60/45.62); L525 68.57/56.96 r_next=0.003 MAD_above=10.92 lag=0(10.92/10.92); direct-full=L524 (L524 internal blank x=53-116 Y=1.359; above=94.062 following=82.000; gate=4.000) |
| 562 | 562/F2 | L523 | L524 | L522 103.78/57.19 r_next=0.478 MAD_above=9.61 lag=1(9.35/9.61); L523 75.89/48.01 r_next=0.418 MAD_above=38.85 lag=0(38.85/38.85); L524 65.30/52.89 r_next=0.953 MAD_above=42.51 lag=-3(41.29/42.51); L525 70.91/59.70 r_next=0.024 MAD_above=13.02 lag=0(13.02/13.02); direct-full=L524 (L524 internal blank x=45-108 Y=1.406; above=95.453 following=85.500; gate=4.000) |
| 563 | 563/F2 | L523 | L524 | L522 115.78/49.92 r_next=0.390 MAD_above=8.54 lag=0(8.54/8.54); L523 98.41/42.62 r_next=0.513 MAD_above=36.95 lag=-4(35.58/36.95); L524 77.11/54.52 r_next=0.940 MAD_above=39.54 lag=-3(37.86/39.54); L525 80.74/57.61 r_next=0.023 MAD_above=13.33 lag=-2(12.93/13.33); direct-full=L524 (L524 internal blank x=53-116 Y=1.312; above=93.609 following=92.000; gate=4.000) |
| 565 | 565/F2 | L523 | L524 | L522 109.63/55.46 r_next=0.418 MAD_above=10.36 lag=0(10.36/10.36); L523 83.45/45.80 r_next=0.455 MAD_above=43.02 lag=1(42.74/43.02); L524 65.39/52.80 r_next=0.949 MAD_above=39.98 lag=-1(39.91/39.98); L525 70.96/59.26 r_next=-0.043 MAD_above=13.02 lag=0(13.02/13.02); direct-full=L524 (L524 internal blank x=55-118 Y=1.344; above=94.859 following=83.000; gate=4.000) |
| 566 | 566/F2 | L522 | L524 | L521 105.12/57.81 r_next=0.952 MAD_above=11.91 lag=0(11.91/11.91); L522 108.10/54.71 r_next=0.394 MAD_above=11.11 lag=1(10.97/11.11); L523 82.24/42.75 r_next=0.404 MAD_above=43.15 lag=12(41.52/43.15); L524 66.14/52.20 r_next=0.950 MAD_above=40.38 lag=-2(39.68/40.38); L525 72.83/59.17 r_next=-0.015 MAD_above=13.55 lag=-1(13.33/13.55); direct-full=L524 (L524 internal blank x=55-118 Y=1.375; above=96.031 following=86.000; gate=4.000) |
| 568 | 568/F2 | L523 | L524 | L522 105.39/58.27 r_next=0.377 MAD_above=8.67 lag=0(8.67/8.67); L523 79.37/45.49 r_next=0.400 MAD_above=44.89 lag=12(44.87/44.89); L524 68.39/52.47 r_next=0.953 MAD_above=41.78 lag=-4(40.57/41.78); L525 73.06/57.93 r_next=0.005 MAD_above=12.04 lag=-2(11.71/12.04); direct-full=L524 (L524 internal blank x=53-116 Y=1.344; above=97.797 following=89.000; gate=4.000) |
| 570 | 570/F2 | L523 | L524 | L522 102.97/58.56 r_next=0.120 MAD_above=8.95 lag=0(8.95/8.95); L523 86.45/44.98 r_next=0.567 MAD_above=52.78 lag=10(52.72/52.78); L524 64.25/53.00 r_next=0.965 MAD_above=36.44 lag=-2(36.07/36.44); L525 69.47/59.06 r_next=0.031 MAD_above=11.92 lag=0(11.92/11.92); direct-full=L524 (L524 internal blank x=60-123 Y=1.328; above=98.484 following=86.000; gate=4.000) |
| 571 | 571/F2 | L522 | L524 | L521 103.16/59.39 r_next=0.978 MAD_above=8.64 lag=0(8.64/8.64); L522 106.11/57.83 r_next=0.328 MAD_above=8.91 lag=1(8.86/8.91); L523 80.00/44.11 r_next=0.493 MAD_above=46.92 lag=-1(46.84/46.92); L524 65.52/53.66 r_next=0.950 MAD_above=36.85 lag=-1(36.56/36.85); L525 68.06/59.25 r_next=-0.031 MAD_above=11.87 lag=0(11.87/11.87); direct-full=L524 (L524 internal blank x=57-120 Y=1.375; above=98.453 following=85.500; gate=4.000) |
| 572 | 572/F2 | L522 | L524 | L521 102.02/59.68 r_next=0.986 MAD_above=8.40 lag=0(8.40/8.40); L522 103.56/58.82 r_next=0.137 MAD_above=7.35 lag=0(7.35/7.35); L523 84.45/41.18 r_next=0.624 MAD_above=53.66 lag=13(51.04/53.66); L524 65.08/52.48 r_next=0.938 MAD_above=32.85 lag=-3(32.08/32.85); L525 69.91/59.73 r_next=-0.001 MAD_above=14.67 lag=-1(14.34/14.67); direct-full=L524 (L524 internal blank x=56-119 Y=1.391; above=91.672 following=86.000; gate=4.000) |
| 574 | 574/F2 | L525 | L524 | L523 88.13/47.59 r_next=0.521 MAD_above=33.08 lag=0(33.08/33.08); L524 82.49/47.41 r_next=0.742 MAD_above=33.04 lag=-2(31.73/33.04); L525 78.40/59.83 r_next=0.019 MAD_above=25.08 lag=-2(24.28/25.08); direct-full=L524 (L524 internal blank x=115-178 Y=3.109; above=91.562 following=89.000; gate=4.000) |
| 575 | 575/F2 | L523 | L524 | L522 112.32/54.68 r_next=0.323 MAD_above=10.48 lag=1(10.19/10.48); L523 95.13/37.98 r_next=0.675 MAD_above=43.36 lag=13(42.07/43.36); L524 70.67/51.43 r_next=0.924 MAD_above=29.40 lag=0(29.40/29.40); L525 74.40/57.67 r_next=0.029 MAD_above=15.13 lag=1(14.50/15.13); direct-full=L524 (L524 internal blank x=55-118 Y=1.297; above=94.812 following=87.000; gate=4.000) |
| 578 | 578/F2 | L522 | L523 | L521 108.93/55.41 r_next=0.963 MAD_above=9.44 lag=0(9.44/9.44); L522 111.31/55.28 r_next=0.284 MAD_above=9.06 lag=0(9.06/9.06); L523 95.81/39.09 r_next=0.884 MAD_above=44.20 lag=15(42.10/44.20); L524 90.77/43.21 r_next=0.974 MAD_above=11.62 lag=0(11.62/11.62); direct-full=L523 (L523 persistent three-third step; thirds=3.523,4.466,6.639; correlation above/next=0.310/0.908; middle coherence=0.938) |
| 579 | 579/F2 | L524 | L525 | L523 106.30/49.15 r_next=0.915 MAD_above=31.84 lag=0(31.84/31.84); L524 100.17/54.59 r_next=0.705 MAD_above=11.49 lag=-2(8.53/11.49); L525 74.11/56.59 r_next=0.005 MAD_above=29.18 lag=-1(27.50/29.18); direct-full=L525 (L525 internal blank x=56-119 Y=1.359; above=95.750 following=92.000; gate=4.000) |
| 599 | 599/F2 | L523 | L524 | L522 108.53/58.04 r_next=0.969 MAD_above=8.54 lag=0(8.54/8.54); L523 105.21/59.80 r_next=0.315 MAD_above=6.84 lag=0(6.84/6.84); L524 89.32/55.04 r_next=0.823 MAD_above=50.73 lag=1(50.62/50.73); L525 76.35/55.09 r_next=-0.020 MAD_above=16.40 lag=-1(14.57/16.40); direct-full=L524 (L524 persistent three-third step; thirds=3.744,6.255,4.670; correlation above/next=0.303/0.857; middle coherence=0.931) |
| 600 | 600/F2 | L522 | L524 | L521 106.05/59.08 r_next=0.974 MAD_above=9.05 lag=0(9.05/9.05); L522 106.62/59.32 r_next=0.836 MAD_above=8.62 lag=0(8.62/8.62); L523 105.88/54.07 r_next=0.237 MAD_above=17.19 lag=-1(15.72/17.19); L524 66.42/54.18 r_next=0.928 MAD_above=65.18 lag=15(62.69/65.18); L525 73.00/59.15 r_next=0.043 MAD_above=15.35 lag=-2(14.85/15.35); direct-full=L524 (L524 persistent three-third step; thirds=8.001,5.312,6.403; correlation above/next=0.225/0.966; middle coherence=0.927) |
| 602 | 602/F2 | L523 | L525 | L522 102.57/58.75 r_next=0.671 MAD_above=8.63 lag=0(8.63/8.63); L523 81.57/49.46 r_next=0.662 MAD_above=28.77 lag=-1(28.22/28.77); L524 76.93/47.50 r_next=0.737 MAD_above=23.28 lag=-1(22.23/23.28); L525 60.43/58.85 r_next=0.023 MAD_above=25.99 lag=0(25.99/25.99); direct-full=L525 (L525 internal blank x=58-121 Y=1.375; above=94.578 following=72.000; gate=4.000) |
| 603 | 603/F2 | L523 | L524 | L522 108.05/58.13 r_next=0.056 MAD_above=8.92 lag=0(8.92/8.92); L523 89.36/42.52 r_next=0.607 MAD_above=54.23 lag=16(51.25/54.23); L524 69.15/54.89 r_next=0.937 MAD_above=35.05 lag=-1(35.00/35.05); L525 72.33/58.30 r_next=-0.026 MAD_above=13.90 lag=-1(13.90/13.90); direct-full=L524 (L524 internal blank x=57-120 Y=1.391; above=96.250 following=92.000; gate=4.000) |
| 605 | 605/F2 | L523 | L524 | L522 108.85/58.43 r_next=0.482 MAD_above=9.00 lag=0(9.00/9.00); L523 81.88/47.99 r_next=0.434 MAD_above=39.67 lag=-1(38.81/39.67); L524 68.43/54.39 r_next=0.956 MAD_above=45.22 lag=-4(43.21/45.22); L525 71.66/59.08 r_next=0.019 MAD_above=11.50 lag=0(11.50/11.50); direct-full=L524 (L524 internal blank x=60-123 Y=1.344; above=97.234 following=91.000; gate=4.000) |
| 607 | 607/F2 | L523 | L524 | L522 107.21/57.38 r_next=0.157 MAD_above=9.00 lag=0(9.00/9.00); L523 86.63/42.80 r_next=0.613 MAD_above=51.63 lag=15(50.24/51.63); L524 70.23/54.83 r_next=0.944 MAD_above=34.40 lag=-2(33.23/34.40); L525 74.45/62.47 r_next=0.026 MAD_above=15.19 lag=0(15.19/15.19); direct-full=L524 (L524 internal blank x=59-122 Y=1.422; above=94.953 following=89.000; gate=4.000) |
| 608 | 608/F2 | L523 | L524 | L522 103.35/55.68 r_next=0.018 MAD_above=8.04 lag=0(8.04/8.04); L523 93.21/38.80 r_next=0.548 MAD_above=52.99 lag=9(51.88/52.99); L524 66.13/51.48 r_next=0.932 MAD_above=37.28 lag=-3(35.41/37.28); L525 73.67/57.02 r_next=0.001 MAD_above=14.15 lag=-1(14.15/14.15); direct-full=L524 (L524 internal blank x=52-115 Y=1.359; above=100.469 following=86.000; gate=4.000) |
| 610 | 610/F2 | L522 | L523 | L521 99.75/55.60 r_next=0.984 MAD_above=9.25 lag=0(9.25/9.25); L522 101.76/57.70 r_next=0.142 MAD_above=7.77 lag=0(7.77/7.77); L523 65.61/48.68 r_next=0.880 MAD_above=68.49 lag=32(64.72/68.49); L524 63.87/49.37 r_next=0.941 MAD_above=13.85 lag=-2(13.13/13.85); direct-full=L523 (L523 persistent three-third step; thirds=12.246,4.970,6.614; correlation above/next=0.158/0.914; middle coherence=0.922) |
| 612 | 612/F2 | L522 | L523 | L521 100.57/55.84 r_next=0.981 MAD_above=9.87 lag=1(9.70/9.87); L522 102.08/56.29 r_next=0.145 MAD_above=7.80 lag=0(7.80/7.80); L523 66.22/50.21 r_next=0.900 MAD_above=69.38 lag=32(64.14/69.38); L524 63.86/50.50 r_next=0.934 MAD_above=11.85 lag=-2(10.16/11.85); direct-full=L523 (L523 persistent three-third step; thirds=13.379,5.184,5.762; correlation above/next=0.155/0.970; middle coherence=0.920) |
| 616 | 616/F2 | L522 | L523 | L521 95.15/54.15 r_next=0.918 MAD_above=10.93 lag=1(10.27/10.93); L522 103.27/55.26 r_next=0.068 MAD_above=12.19 lag=0(12.19/12.19); L523 65.61/50.33 r_next=0.939 MAD_above=70.81 lag=28(62.57/70.81); L524 67.43/52.36 r_next=0.942 MAD_above=11.36 lag=-1(10.83/11.36); direct-full=L523 (L523 persistent three-third step; thirds=13.043,4.979,6.645; correlation above/next=0.054/0.971; middle coherence=0.920) |
| 620 | 620/F2 | L523 | L524 | L522 97.53/55.70 r_next=0.159 MAD_above=9.37 lag=0(9.37/9.37); L523 82.15/42.32 r_next=0.681 MAD_above=52.27 lag=20(47.71/52.27); L524 66.02/50.41 r_next=0.932 MAD_above=26.58 lag=-4(25.54/26.58); L525 71.29/56.09 r_next=0.017 MAD_above=12.82 lag=-2(12.05/12.82); direct-full=L524 (L524 internal blank x=49-112 Y=1.328; above=96.453 following=88.000; gate=4.000) |
| 621 | 621/F2 | L523 | L524 | L522 98.04/56.22 r_next=0.134 MAD_above=9.50 lag=1(9.04/9.50); L523 87.05/37.71 r_next=0.567 MAD_above=48.51 lag=20(43.62/48.51); L524 66.23/50.39 r_next=0.934 MAD_above=32.90 lag=-3(31.21/32.90); L525 72.44/56.57 r_next=0.020 MAD_above=13.53 lag=-2(12.84/13.53); direct-full=L524 (L524 internal blank x=55-118 Y=1.375; above=96.234 following=92.000; gate=4.000) |
| 622 | 622/F2 | L523 | L524 | L522 96.70/55.56 r_next=0.169 MAD_above=8.30 lag=0(8.30/8.30); L523 87.22/38.77 r_next=0.561 MAD_above=46.31 lag=22(43.02/46.31); L524 63.46/50.16 r_next=0.936 MAD_above=34.16 lag=-2(32.89/34.16); L525 71.92/57.53 r_next=-0.013 MAD_above=14.70 lag=0(14.70/14.70); direct-full=L524 (L524 internal blank x=63-126 Y=1.375; above=99.109 following=85.000; gate=4.000) |
| 623 | 623/F2 | L523 | L524 | L522 94.79/54.54 r_next=0.265 MAD_above=7.18 lag=0(7.18/7.18); L523 76.15/37.45 r_next=0.316 MAD_above=42.59 lag=6(41.29/42.59); L524 65.29/51.25 r_next=0.943 MAD_above=40.29 lag=-1(40.05/40.29); L525 65.73/54.47 r_next=0.004 MAD_above=11.43 lag=0(11.43/11.43); direct-full=L524 (L524 internal blank x=68-131 Y=1.375; above=95.109 following=90.000; gate=4.000) |
| 624 | 624/F2 | L521 | L524 | L520 92.05/53.66 r_next=0.973 MAD_above=9.35 lag=1(9.18/9.35); L521 94.10/54.47 r_next=0.971 MAD_above=8.85 lag=0(8.85/8.85); L522 96.72/54.25 r_next=0.442 MAD_above=9.51 lag=0(9.51/9.51); L523 70.27/39.52 r_next=0.199 MAD_above=37.68 lag=17(36.03/37.68); L524 62.92/49.60 r_next=0.935 MAD_above=45.23 lag=0(45.23/45.23); L525 67.00/54.34 r_next=-0.008 MAD_above=12.64 lag=-2(12.57/12.64); direct-full=L524 (L524 internal blank x=65-128 Y=1.359; above=99.078 following=84.000; gate=4.000) |
| 625 | 625/F2 | L523 | L524 | L522 93.49/54.10 r_next=0.500 MAD_above=8.73 lag=0(8.73/8.73); L523 67.01/36.70 r_next=0.192 MAD_above=34.67 lag=1(34.63/34.67); L524 62.24/47.94 r_next=0.903 MAD_above=43.83 lag=0(43.83/43.83); L525 66.70/54.48 r_next=0.025 MAD_above=13.17 lag=0(13.17/13.17); direct-full=L524 (L524 internal blank x=55-118 Y=1.328; above=93.688 following=89.000; gate=4.000) |
| 626 | 626/F2 | L523 | L524 | L522 92.59/53.78 r_next=0.476 MAD_above=7.64 lag=0(7.64/7.64); L523 65.29/38.21 r_next=0.155 MAD_above=35.46 lag=-1(35.46/35.46); L524 57.60/45.89 r_next=0.887 MAD_above=43.43 lag=0(43.43/43.43); L525 68.21/54.29 r_next=0.017 MAD_above=16.65 lag=-1(16.58/16.65); direct-full=L524 (L524 internal blank x=63-126 Y=1.359; above=95.000 following=79.000; gate=4.000) |
| 629 | 629/F2 | L521 | L524 | L520 92.97/53.88 r_next=0.975 MAD_above=8.94 lag=0(8.94/8.94); L521 94.06/53.76 r_next=0.978 MAD_above=8.33 lag=1(8.06/8.33); L522 93.81/53.79 r_next=0.274 MAD_above=7.74 lag=0(7.74/7.74); L523 70.53/42.55 r_next=0.247 MAD_above=42.64 lag=6(41.90/42.64); L524 62.73/51.34 r_next=0.920 MAD_above=45.53 lag=-2(45.03/45.53); L525 68.10/56.44 r_next=-0.001 MAD_above=14.62 lag=-1(14.51/14.62); direct-full=L524 (L524 internal blank x=60-123 Y=1.359; above=93.141 following=84.000; gate=4.000) |
| 630 | 630/F2 | L523 | L524 | L522 96.24/54.53 r_next=0.384 MAD_above=9.06 lag=0(9.06/9.06); L523 71.95/41.95 r_next=0.341 MAD_above=40.31 lag=18(39.48/40.31); L524 63.85/49.48 r_next=0.921 MAD_above=39.76 lag=-1(39.51/39.76); L525 67.63/56.48 r_next=0.017 MAD_above=13.75 lag=0(13.75/13.75); direct-full=L524 (L524 internal blank x=67-130 Y=1.484; above=91.781 following=87.000; gate=4.000) |
| 635 | 635/F2 | L523 | L524 | L522 100.22/54.42 r_next=0.047 MAD_above=11.52 lag=1(11.13/11.52); L523 85.30/40.57 r_next=0.646 MAD_above=51.53 lag=19(48.87/51.53); L524 63.81/50.47 r_next=0.950 MAD_above=29.96 lag=-2(28.45/29.96); L525 68.67/57.51 r_next=0.034 MAD_above=12.49 lag=0(12.49/12.49); direct-full=L524 (L524 internal blank x=63-126 Y=1.391; above=96.562 following=84.000; gate=4.000) |
| 636 | 636/F2 | L523 | L524 | L522 98.79/55.10 r_next=0.089 MAD_above=10.32 lag=0(10.32/10.32); L523 79.26/44.50 r_next=0.603 MAD_above=56.15 lag=20(53.10/56.15); L524 64.69/50.68 r_next=0.938 MAD_above=27.65 lag=-4(24.75/27.65); L525 71.61/56.48 r_next=0.009 MAD_above=12.46 lag=-1(12.44/12.46); direct-full=L524 (L524 internal blank x=59-122 Y=1.344; above=111.469 following=86.000; gate=4.000) |
| 637 | 637/F2 | L522 | L523 | L521 93.64/54.57 r_next=0.944 MAD_above=10.87 lag=0(10.87/10.87); L522 97.66/55.62 r_next=0.156 MAD_above=10.75 lag=1(9.90/10.75); L523 72.59/49.10 r_next=0.737 MAD_above=60.50 lag=22(58.16/60.50); L524 65.20/50.34 r_next=0.944 MAD_above=20.11 lag=-2(18.93/20.11); direct-full=L523 (L523 persistent three-third step; thirds=8.984,4.466,6.500; correlation above/next=0.145/0.745; middle coherence=0.915) |
| 643 | 643/F2 | L520 | L523 | L519 89.99/56.62 r_next=0.947 MAD_above=9.91 lag=0(9.91/9.91); L520 90.75/56.07 r_next=0.944 MAD_above=11.50 lag=-1(11.23/11.50); L521 96.24/55.67 r_next=0.962 MAD_above=11.56 lag=0(11.56/11.56); L522 100.46/55.83 r_next=0.135 MAD_above=9.66 lag=0(9.66/9.66); L523 72.67/46.19 r_next=0.766 MAD_above=59.73 lag=18(57.30/59.73); L524 64.55/51.21 r_next=0.950 MAD_above=20.91 lag=-2(19.81/20.91); direct-full=L523 (L523 persistent three-third step; thirds=8.184,4.275,6.936; correlation above/next=0.132/0.771; middle coherence=0.909) |
| 644 | 644/F2 | L523 | L524 | L522 97.47/55.99 r_next=0.101 MAD_above=8.63 lag=0(8.63/8.63); L523 79.30/43.08 r_next=0.662 MAD_above=55.93 lag=18(53.09/55.93); L524 62.52/50.26 r_next=0.955 MAD_above=26.65 lag=-2(25.45/26.65); L525 68.35/57.62 r_next=-0.001 MAD_above=11.40 lag=-1(11.10/11.40); direct-full=L524 (L524 internal blank x=62-125 Y=1.438; above=104.250 following=86.000; gate=4.000) |
| 645 | 645/F2 | L523 | L524 | L522 96.88/56.23 r_next=0.101 MAD_above=8.25 lag=0(8.25/8.25); L523 81.72/43.23 r_next=0.697 MAD_above=54.78 lag=15(52.27/54.78); L524 63.32/51.08 r_next=0.950 MAD_above=26.47 lag=-1(26.28/26.47); L525 70.27/56.63 r_next=-0.016 MAD_above=11.99 lag=-1(11.79/11.99); direct-full=L524 (L524 internal blank x=47-110 Y=1.422; above=96.500 following=88.000; gate=4.000) |
| 646 | 646/F2 | L523 | L524 | L522 95.79/55.76 r_next=0.069 MAD_above=8.51 lag=0(8.51/8.51); L523 81.41/43.53 r_next=0.621 MAD_above=56.19 lag=16(53.02/56.19); L524 63.03/51.09 r_next=0.950 MAD_above=27.65 lag=-2(26.00/27.65); L525 68.22/56.58 r_next=0.027 MAD_above=11.28 lag=-1(11.00/11.28); direct-full=L524 (L524 internal blank x=61-124 Y=1.391; above=106.812 following=85.000; gate=4.000) |
| 648 | 648/F2 | L522 | L523 | L521 95.70/55.72 r_next=0.966 MAD_above=10.77 lag=0(10.77/10.77); L522 98.75/55.65 r_next=0.144 MAD_above=8.65 lag=0(8.65/8.65); L523 71.44/47.89 r_next=0.801 MAD_above=61.27 lag=17(59.04/61.27); L524 65.00/51.35 r_next=0.944 MAD_above=19.56 lag=-3(17.82/19.56); direct-full=L523 (L523 persistent three-third step; thirds=9.344,4.286,6.556; correlation above/next=0.153/0.822; middle coherence=0.910) |
| 652 | 652/F2 | L523 | L524 | L522 96.27/55.91 r_next=0.112 MAD_above=8.03 lag=0(8.03/8.03); L523 79.26/44.37 r_next=0.673 MAD_above=54.42 lag=17(51.30/54.42); L524 63.65/49.97 r_next=0.943 MAD_above=26.74 lag=-2(26.17/26.74); L525 68.88/57.17 r_next=0.003 MAD_above=12.72 lag=-1(12.59/12.72); direct-full=L524 (L524 internal blank x=61-124 Y=1.375; above=104.500 following=88.000; gate=4.000) |
| 653 | 653/F2 | L522 | L523 | L521 94.01/52.69 r_next=0.933 MAD_above=10.51 lag=0(10.51/10.51); L522 96.30/54.90 r_next=0.076 MAD_above=10.83 lag=1(10.34/10.83); L523 80.14/42.65 r_next=0.718 MAD_above=54.51 lag=21(51.12/54.51); L524 63.21/49.85 r_next=0.943 MAD_above=24.74 lag=-1(24.40/24.74); direct-full=L523 (L523 persistent three-third step; thirds=6.842,4.452,6.378; correlation above/next=0.069/0.715; middle coherence=0.913) |
| 655 | 655/F2 | L523 | L524 | L522 95.78/54.23 r_next=0.094 MAD_above=9.87 lag=0(9.87/9.87); L523 78.98/41.46 r_next=0.691 MAD_above=53.01 lag=23(49.08/53.01); L524 60.86/49.60 r_next=0.941 MAD_above=25.53 lag=-1(25.49/25.53); L525 67.17/55.64 r_next=0.004 MAD_above=12.09 lag=0(12.09/12.09); direct-full=L524 (L524 internal blank x=61-124 Y=1.344; above=94.469 following=84.000; gate=4.000) |
| 657 | 657/F2 | L523 | L524 | L522 96.01/54.86 r_next=0.101 MAD_above=10.94 lag=0(10.94/10.94); L523 77.50/42.12 r_next=0.676 MAD_above=54.44 lag=23(50.17/54.44); L524 62.73/49.72 r_next=0.945 MAD_above=25.53 lag=-2(24.96/25.53); L525 66.29/55.82 r_next=-0.024 MAD_above=11.75 lag=1(11.69/11.75); direct-full=L524 (L524 internal blank x=63-126 Y=1.375; above=96.125 following=83.000; gate=4.000) |
| 658 | 658/F2 | L523 | L524 | L522 96.28/54.94 r_next=0.066 MAD_above=8.32 lag=0(8.32/8.32); L523 75.71/42.08 r_next=0.614 MAD_above=55.71 lag=21(51.74/55.71); L524 64.31/50.26 r_next=0.925 MAD_above=28.59 lag=0(28.59/28.59); L525 67.86/56.36 r_next=-0.007 MAD_above=13.77 lag=0(13.77/13.77); direct-full=L524 (L524 internal blank x=64-127 Y=1.344; above=95.891 following=87.000; gate=4.000) |
| 659 | 659/F2 | L523 | L524 | L522 97.13/54.63 r_next=0.072 MAD_above=9.33 lag=1(9.25/9.33); L523 80.16/41.65 r_next=0.574 MAD_above=52.76 lag=17(49.11/52.76); L524 61.43/49.51 r_next=0.930 MAD_above=31.10 lag=-2(30.66/31.10); L525 64.48/54.02 r_next=0.004 MAD_above=12.03 lag=-1(11.77/12.03); direct-full=L524 (L524 internal blank x=75-138 Y=1.328; above=94.531 following=82.000; gate=4.000) |
| 660 | 660/F2 | L523 | L524 | L522 94.16/55.09 r_next=-0.035 MAD_above=7.60 lag=0(7.60/7.60); L523 79.88/38.20 r_next=0.441 MAD_above=53.51 lag=22(48.34/53.51); L524 64.74/49.12 r_next=0.922 MAD_above=34.84 lag=-2(34.42/34.84); L525 66.42/54.36 r_next=0.032 MAD_above=12.98 lag=1(12.93/12.98); direct-full=L524 (L524 internal blank x=53-116 Y=1.328; above=95.375 following=87.000; gate=4.000) |
| 661 | 661/F2 | L522 | L524 | L521 95.25/53.63 r_next=0.981 MAD_above=8.17 lag=0(8.17/8.17); L522 94.43/55.09 r_next=0.037 MAD_above=7.57 lag=0(7.57/7.57); L523 78.41/37.95 r_next=0.437 MAD_above=51.10 lag=21(46.49/51.10); L524 63.91/50.39 r_next=0.922 MAD_above=35.46 lag=-3(34.48/35.46); L525 67.15/55.50 r_next=0.059 MAD_above=13.39 lag=-1(13.17/13.39); direct-full=L524 (L524 internal blank x=61-124 Y=1.391; above=91.656 following=85.000; gate=4.000) |
| 662 | 662/F2 | L523 | L524 | L522 94.38/54.98 r_next=0.014 MAD_above=8.42 lag=1(8.23/8.42); L523 80.55/38.11 r_next=0.430 MAD_above=51.81 lag=20(47.61/51.81); L524 63.35/49.94 r_next=0.930 MAD_above=36.15 lag=-3(35.26/36.15); L525 67.93/54.97 r_next=-0.005 MAD_above=13.09 lag=-1(13.01/13.09); direct-full=L524 (L524 internal blank x=59-122 Y=1.328; above=96.453 following=86.000; gate=4.000) |
| 663 | 663/F2 | L523 | L524 | L522 91.37/53.80 r_next=-0.003 MAD_above=8.03 lag=1(7.88/8.03); L523 79.24/35.06 r_next=0.513 MAD_above=49.39 lag=18(46.89/49.39); L524 58.82/46.42 r_next=0.851 MAD_above=32.30 lag=-1(32.12/32.30); L525 65.59/53.11 r_next=0.012 MAD_above=14.55 lag=-2(14.16/14.55); direct-full=L524 (L524 internal blank x=74-137 Y=1.359; above=96.219 following=81.000; gate=4.000) |
| 664 | 664/F2 | L523 | L524 | L522 94.17/54.65 r_next=0.001 MAD_above=8.59 lag=1(8.16/8.59); L523 80.86/35.18 r_next=0.463 MAD_above=49.25 lag=25(45.56/49.25); L524 59.62/46.88 r_next=0.866 MAD_above=35.38 lag=-4(34.27/35.38); L525 69.00/54.73 r_next=0.023 MAD_above=15.41 lag=0(15.41/15.41); direct-full=L524 (L524 internal blank x=71-134 Y=1.391; above=94.406 following=83.000; gate=4.000) |
| 665 | 665/F2 | L523 | L524 | L522 92.41/53.53 r_next=-0.010 MAD_above=7.32 lag=0(7.32/7.32); L523 79.86/36.54 r_next=0.524 MAD_above=50.36 lag=32(46.14/50.36); L524 58.93/46.70 r_next=0.876 MAD_above=32.86 lag=-2(32.31/32.86); L525 66.53/54.81 r_next=-0.009 MAD_above=15.69 lag=-2(15.08/15.69); direct-full=L524 (L524 internal blank x=64-127 Y=1.344; above=95.531 following=83.000; gate=4.000) |
| 666 | 666/F2 | L523 | L524 | L522 92.39/54.72 r_next=0.037 MAD_above=7.38 lag=0(7.38/7.38); L523 76.58/35.88 r_next=0.435 MAD_above=50.89 lag=32(46.73/50.89); L524 56.45/45.13 r_next=0.865 MAD_above=33.46 lag=-2(32.78/33.46); L525 65.12/53.13 r_next=0.038 MAD_above=15.12 lag=-2(14.38/15.12); direct-full=L524 (L524 internal blank x=65-128 Y=1.391; above=90.094 following=78.000; gate=4.000) |
| 667 | 667/F2 | L523 | L524 | L522 93.73/54.58 r_next=-0.032 MAD_above=8.10 lag=1(8.09/8.10); L523 78.06/34.60 r_next=0.523 MAD_above=50.87 lag=32(45.94/50.87); L524 58.24/46.39 r_next=0.871 MAD_above=32.46 lag=-1(32.13/32.46); L525 66.49/53.81 r_next=0.018 MAD_above=15.63 lag=0(15.63/15.63); direct-full=L524 (L524 internal blank x=71-134 Y=1.328; above=94.453 following=80.000; gate=4.000) |
| 668 | 668/F2 | L522 | L524 | L521 94.54/53.04 r_next=0.981 MAD_above=9.20 lag=1(8.85/9.20); L522 95.04/53.80 r_next=-0.034 MAD_above=6.55 lag=0(6.55/6.55); L523 82.89/38.10 r_next=0.372 MAD_above=50.66 lag=25(46.49/50.66); L524 59.45/44.83 r_next=0.872 MAD_above=36.40 lag=-2(35.30/36.40); L525 65.64/53.42 r_next=0.000 MAD_above=14.62 lag=-1(14.31/14.62); direct-full=L524 (L524 internal blank x=61-124 Y=1.344; above=95.609 following=84.000; gate=4.000) |
| 669 | 669/F2 | L523 | L524 | L522 91.93/53.60 r_next=-0.057 MAD_above=7.97 lag=0(7.97/7.97); L523 75.25/34.41 r_next=0.524 MAD_above=51.76 lag=32(46.91/51.76); L524 60.00/45.92 r_next=0.878 MAD_above=29.72 lag=-2(29.30/29.72); L525 64.22/53.09 r_next=0.029 MAD_above=14.39 lag=0(14.39/14.39); direct-full=L524 (L524 internal blank x=52-115 Y=1.422; above=92.859 following=84.000; gate=4.000) |
| 670 | 670/F2 | L523 | L524 | L522 93.08/54.41 r_next=0.025 MAD_above=7.95 lag=0(7.95/7.95); L523 75.58/36.98 r_next=0.509 MAD_above=51.97 lag=31(48.39/51.97); L524 60.40/44.86 r_next=0.880 MAD_above=30.36 lag=-1(30.15/30.36); L525 65.12/54.30 r_next=-0.001 MAD_above=15.44 lag=-2(14.98/15.44); direct-full=L524 (L524 internal blank x=59-122 Y=1.344; above=93.984 following=83.000; gate=4.000) |
| 671 | 671/F2 | L523 | L524 | L522 93.17/53.41 r_next=-0.072 MAD_above=7.12 lag=0(7.12/7.12); L523 82.39/37.10 r_next=0.385 MAD_above=51.33 lag=27(46.16/51.33); L524 58.90/44.97 r_next=0.862 MAD_above=35.47 lag=0(35.47/35.47); L525 64.35/54.02 r_next=0.001 MAD_above=15.60 lag=1(15.53/15.60); direct-full=L524 (L524 internal blank x=59-122 Y=1.359; above=97.016 following=82.000; gate=4.000) |
| 672 | 672/F2 | L522 | L524 | L521 94.90/53.33 r_next=0.980 MAD_above=7.76 lag=0(7.76/7.76); L522 93.94/54.10 r_next=0.002 MAD_above=7.25 lag=0(7.25/7.25); L523 79.39/35.37 r_next=0.495 MAD_above=49.59 lag=32(45.45/49.59); L524 61.06/46.24 r_next=0.884 MAD_above=32.60 lag=-3(31.61/32.60); L525 68.13/55.33 r_next=0.017 MAD_above=14.76 lag=-1(14.57/14.76); direct-full=L524 (L524 internal blank x=64-127 Y=1.375; above=96.016 following=84.000; gate=4.000) |
| 673 | 673/F2 | L523 | L524 | L522 95.64/53.90 r_next=-0.116 MAD_above=7.94 lag=0(7.94/7.94); L523 83.18/41.07 r_next=0.449 MAD_above=53.81 lag=28(49.98/53.81); L524 59.85/45.54 r_next=0.876 MAD_above=35.16 lag=0(35.16/35.16); L525 66.54/54.75 r_next=0.042 MAD_above=14.84 lag=-1(14.80/14.84); direct-full=L524 (L524 internal blank x=63-126 Y=1.344; above=93.391 following=83.000; gate=4.000) |
| 674 | 674/F2 | L523 | L524 | L522 96.03/53.32 r_next=-0.010 MAD_above=8.29 lag=1(8.02/8.29); L523 78.29/36.09 r_next=0.467 MAD_above=49.73 lag=24(46.12/49.73); L524 59.60/47.81 r_next=0.863 MAD_above=34.38 lag=-2(33.85/34.38); L525 67.69/54.46 r_next=0.008 MAD_above=16.40 lag=0(16.40/16.40); direct-full=L524 (L524 internal blank x=68-131 Y=1.312; above=92.547 following=80.000; gate=4.000) |
| 675 | 675/F2 | L522 | L524 | L521 91.54/53.42 r_next=0.981 MAD_above=7.97 lag=0(7.97/7.97); L522 94.73/54.19 r_next=0.013 MAD_above=7.76 lag=0(7.76/7.76); L523 78.96/34.91 r_next=0.498 MAD_above=48.77 lag=26(45.51/48.77); L524 60.15/47.07 r_next=0.869 MAD_above=32.73 lag=-2(32.12/32.73); L525 64.78/53.55 r_next=0.043 MAD_above=14.47 lag=-1(14.12/14.47); direct-full=L524 (L524 internal blank x=49-112 Y=1.297; above=92.672 following=78.500; gate=4.000) |
| 676 | 676/F2 | L523 | L524 | L522 92.99/53.78 r_next=-0.027 MAD_above=6.97 lag=0(6.97/6.97); L523 78.72/36.50 r_next=0.464 MAD_above=50.19 lag=32(47.11/50.19); L524 58.91/47.18 r_next=0.876 MAD_above=34.01 lag=0(34.01/34.01); L525 66.59/54.43 r_next=0.004 MAD_above=14.92 lag=-2(14.50/14.92); direct-full=L524 (L524 internal blank x=72-135 Y=1.297; above=89.641 following=83.000; gate=4.000) |
| 677 | 677/F2 | L523 | L524 | L522 94.14/54.19 r_next=-0.025 MAD_above=7.33 lag=0(7.33/7.33); L523 78.24/36.00 r_next=0.442 MAD_above=51.03 lag=28(46.62/51.03); L524 57.72/45.58 r_next=0.873 MAD_above=32.28 lag=0(32.28/32.28); L525 64.45/54.28 r_next=0.015 MAD_above=15.35 lag=0(15.35/15.35); direct-full=L524 (L524 internal blank x=63-126 Y=1.328; above=92.312 following=81.000; gate=4.000) |
| 678 | 678/F2 | L523 | L524 | L522 91.00/54.36 r_next=0.014 MAD_above=8.16 lag=0(8.16/8.16); L523 78.51/37.31 r_next=0.382 MAD_above=50.40 lag=24(46.14/50.40); L524 60.55/47.82 r_next=0.931 MAD_above=34.39 lag=-1(34.34/34.39); L525 65.30/54.58 r_next=0.018 MAD_above=11.93 lag=-2(11.91/11.93); direct-full=L524 (L524 internal blank x=67-130 Y=1.344; above=92.906 following=82.000; gate=4.000) |
| 679 | 679/F2 | L523 | L524 | L522 94.89/54.35 r_next=0.012 MAD_above=7.64 lag=0(7.64/7.64); L523 77.27/36.78 r_next=0.454 MAD_above=51.10 lag=20(47.61/51.10); L524 63.60/48.75 r_next=0.946 MAD_above=33.02 lag=-2(32.34/33.02); L525 68.22/55.24 r_next=0.030 MAD_above=11.39 lag=-1(11.29/11.39); direct-full=L524 (L524 internal blank x=63-126 Y=1.344; above=93.594 following=86.500; gate=4.000) |
| 680 | 680/F2 | L523 | L524 | L522 94.81/54.85 r_next=0.052 MAD_above=9.50 lag=1(9.25/9.50); L523 81.52/39.53 r_next=0.500 MAD_above=50.98 lag=24(47.20/50.98); L524 62.03/49.48 r_next=0.931 MAD_above=32.15 lag=0(32.15/32.15); L525 68.15/54.67 r_next=-0.004 MAD_above=12.75 lag=-1(12.66/12.75); direct-full=L524 (L524 internal blank x=47-110 Y=1.375; above=91.953 following=84.000; gate=4.000) |
| 681 | 681/F2 | L523 | L524 | L522 96.28/55.33 r_next=0.093 MAD_above=8.65 lag=0(8.65/8.65); L523 78.94/39.70 r_next=0.612 MAD_above=51.45 lag=18(48.00/51.45); L524 62.22/49.43 r_next=0.944 MAD_above=28.06 lag=-2(27.87/28.06); L525 66.62/55.01 r_next=-0.012 MAD_above=11.39 lag=0(11.39/11.39); direct-full=L524 (L524 internal blank x=62-125 Y=1.312; above=93.969 following=84.000; gate=4.000) |
| 682 | 682/F2 | L523 | L524 | L522 95.92/55.44 r_next=0.032 MAD_above=10.00 lag=0(10.00/10.00); L523 83.71/39.49 r_next=0.497 MAD_above=51.45 lag=19(47.02/51.45); L524 63.56/49.96 r_next=0.935 MAD_above=33.80 lag=-2(33.02/33.80); L525 69.91/56.06 r_next=-0.011 MAD_above=12.30 lag=-2(11.87/12.30); direct-full=L524 (L524 internal blank x=64-127 Y=1.344; above=94.703 following=86.000; gate=4.000) |
| 683 | 683/F2 | L523 | L524 | L522 95.16/55.24 r_next=0.100 MAD_above=9.72 lag=0(9.72/9.72); L523 88.66/41.31 r_next=0.532 MAD_above=49.89 lag=21(45.21/49.89); L524 64.23/49.99 r_next=0.934 MAD_above=32.94 lag=-1(32.78/32.94); L525 67.06/54.83 r_next=0.002 MAD_above=11.47 lag=-1(11.39/11.47); direct-full=L524 (L524 internal blank x=61-124 Y=1.453; above=96.922 following=86.000; gate=4.000) |
| 684 | 684/F2 | L523 | L524 | L522 92.74/54.60 r_next=0.057 MAD_above=10.49 lag=0(10.49/10.49); L523 85.11/39.10 r_next=0.606 MAD_above=50.17 lag=20(44.94/50.17); L524 60.78/49.00 r_next=0.942 MAD_above=32.27 lag=-1(32.07/32.27); L525 67.06/55.00 r_next=0.023 MAD_above=11.70 lag=0(11.70/11.70); direct-full=L524 (L524 internal blank x=47-110 Y=1.359; above=95.469 following=84.000; gate=4.000) |
| 685 | 685/F2 | L523 | L524 | L522 99.55/54.89 r_next=0.044 MAD_above=11.12 lag=0(11.12/11.12); L523 85.93/38.93 r_next=0.612 MAD_above=51.15 lag=21(47.34/51.15); L524 65.24/51.79 r_next=0.944 MAD_above=30.63 lag=-2(29.87/30.63); L525 67.32/55.75 r_next=-0.003 MAD_above=11.03 lag=-1(11.01/11.03); direct-full=L524 (L524 internal blank x=53-116 Y=1.359; above=92.406 following=89.000; gate=4.000) |
| 686 | 686/F2 | L523 | L524 | L522 98.11/54.88 r_next=0.089 MAD_above=11.50 lag=0(11.50/11.50); L523 81.27/41.53 r_next=0.698 MAD_above=52.81 lag=19(48.90/52.81); L524 63.47/49.57 r_next=0.946 MAD_above=25.26 lag=-1(25.20/25.26); L525 67.83/56.20 r_next=0.020 MAD_above=12.07 lag=1(11.96/12.07); direct-full=L524 (L524 internal blank x=67-130 Y=1.344; above=94.016 following=83.000; gate=4.000) |
| 687 | 687/F2 | L523 | L524 | L522 96.28/55.59 r_next=0.092 MAD_above=10.42 lag=0(10.42/10.42); L523 82.80/41.07 r_next=0.692 MAD_above=51.89 lag=31(48.55/51.89); L524 63.31/50.31 r_next=0.957 MAD_above=27.58 lag=-2(26.62/27.58); L525 66.39/55.10 r_next=0.014 MAD_above=9.13 lag=0(9.13/9.13); direct-full=L524 (L524 internal blank x=66-129 Y=1.391; above=93.594 following=84.000; gate=4.000) |
| 688 | 688/F2 | L523 | L524 | L522 99.91/56.23 r_next=0.118 MAD_above=9.30 lag=1(9.14/9.30); L523 81.12/42.00 r_next=0.630 MAD_above=53.08 lag=15(50.94/53.08); L524 65.03/51.29 r_next=0.941 MAD_above=28.08 lag=-2(26.76/28.08); L525 70.10/57.20 r_next=0.007 MAD_above=11.08 lag=-1(10.36/11.08); direct-full=L524 (L524 internal blank x=55-118 Y=1.328; above=94.156 following=88.000; gate=4.000) |
| 689 | 689/F2 | L523 | L524 | L522 96.99/56.70 r_next=0.079 MAD_above=10.14 lag=1(10.12/10.14); L523 81.47/43.93 r_next=0.609 MAD_above=55.15 lag=16(52.74/55.15); L524 64.08/50.64 r_next=0.949 MAD_above=29.96 lag=-2(29.20/29.96); L525 67.35/56.36 r_next=-0.001 MAD_above=10.92 lag=0(10.92/10.92); direct-full=L524 (L524 internal blank x=54-117 Y=1.359; above=93.719 following=87.000; gate=4.000) |
| 691 | 691/F2 | L523 | L524 | L522 96.78/55.64 r_next=0.129 MAD_above=11.61 lag=1(11.22/11.61); L523 77.45/40.59 r_next=0.659 MAD_above=52.31 lag=19(50.81/52.31); L524 64.09/50.71 r_next=0.954 MAD_above=26.66 lag=-1(26.32/26.66); L525 66.61/54.91 r_next=0.062 MAD_above=10.92 lag=0(10.92/10.92); direct-full=L524 (L524 internal blank x=56-119 Y=1.312; above=93.141 following=85.000; gate=4.000) |
| 692 | 692/F2 | L523 | L524 | L522 95.05/56.54 r_next=0.090 MAD_above=10.44 lag=1(10.22/10.44); L523 84.44/38.75 r_next=0.591 MAD_above=50.58 lag=23(48.44/50.58); L524 64.58/51.64 r_next=0.950 MAD_above=31.30 lag=-1(31.17/31.30); L525 67.70/55.64 r_next=-0.009 MAD_above=11.50 lag=-1(11.44/11.50); direct-full=L524 (L524 internal blank x=49-112 Y=1.328; above=94.969 following=85.000; gate=4.000) |
| 693 | 693/F2 | L523 | L524 | L522 93.63/56.33 r_next=0.061 MAD_above=11.17 lag=1(10.91/11.17); L523 84.43/38.19 r_next=0.588 MAD_above=50.81 lag=22(48.28/50.81); L524 62.75/51.30 r_next=0.945 MAD_above=31.70 lag=0(31.70/31.70); L525 64.87/54.47 r_next=0.027 MAD_above=10.52 lag=0(10.52/10.52); direct-full=L524 (L524 internal blank x=57-120 Y=1.406; above=95.234 following=86.000; gate=4.000) |
| 694 | 694/F2 | L523 | L524 | L522 119.75/42.68 r_next=0.031 MAD_above=9.56 lag=1(9.31/9.56); L523 124.72/49.66 r_next=0.138 MAD_above=53.61 lag=28(48.35/53.61); L524 87.44/59.82 r_next=0.898 MAD_above=50.80 lag=0(50.80/50.80); L525 91.71/64.07 r_next=0.024 MAD_above=18.15 lag=0(18.15/18.15); direct-full=L524 (L524 internal blank x=58-121 Y=1.406; above=170.188 following=111.000; gate=4.000) |
| 695 | 695/F2 | L523 | L524 | L522 122.07/41.98 r_next=0.005 MAD_above=10.40 lag=1(10.29/10.40); L523 123.07/48.38 r_next=0.158 MAD_above=52.54 lag=25(47.36/52.54); L524 87.16/61.90 r_next=0.913 MAD_above=50.13 lag=-2(49.27/50.13); L525 92.04/64.69 r_next=0.040 MAD_above=16.50 lag=-1(15.93/16.50); direct-full=L524 (L524 internal blank x=48-111 Y=1.359; above=165.875 following=111.000; gate=4.000) |
| 696 | 696/F2 | L523 | L524 | L522 120.81/42.58 r_next=0.019 MAD_above=10.66 lag=1(10.36/10.66); L523 124.84/47.72 r_next=0.188 MAD_above=51.99 lag=27(47.98/51.99); L524 88.29/61.32 r_next=0.898 MAD_above=49.23 lag=0(49.23/49.23); L525 93.93/65.13 r_next=0.010 MAD_above=17.32 lag=1(17.26/17.32); direct-full=L524 (L524 internal blank x=63-126 Y=1.375; above=169.016 following=112.000; gate=4.000) |
| 697 | 697/F2 | L523 | L524 | L522 121.46/42.43 r_next=-0.021 MAD_above=10.47 lag=1(10.09/10.47); L523 123.58/48.66 r_next=0.155 MAD_above=52.53 lag=28(46.64/52.53); L524 88.12/60.41 r_next=0.903 MAD_above=51.87 lag=-2(51.43/51.87); L525 94.26/65.42 r_next=-0.008 MAD_above=19.08 lag=0(19.08/19.08); direct-full=L524 (L524 internal blank x=65-128 Y=1.344; above=167.672 following=117.000; gate=4.000) |
| 698 | 698/F2 | L523 | L524 | L522 121.70/42.28 r_next=-0.006 MAD_above=9.60 lag=1(9.55/9.60); L523 119.24/50.21 r_next=0.146 MAD_above=52.48 lag=26(48.43/52.48); L524 87.82/61.81 r_next=0.902 MAD_above=52.70 lag=0(52.70/52.70); L525 93.16/65.08 r_next=0.027 MAD_above=17.62 lag=0(17.62/17.62); direct-full=L524 (L524 internal blank x=64-127 Y=1.422; above=166.516 following=115.500; gate=4.000) |
| 699 | 699/F2 | L521 | L524 | L520 118.52/43.07 r_next=0.913 MAD_above=11.38 lag=1(10.82/11.38); L521 118.50/43.31 r_next=0.909 MAD_above=10.55 lag=1(10.14/10.55); L522 120.15/41.19 r_next=-0.044 MAD_above=9.83 lag=1(9.23/9.83); L523 119.21/49.00 r_next=0.152 MAD_above=53.29 lag=25(48.67/53.29); L524 87.23/60.23 r_next=0.897 MAD_above=50.73 lag=-1(50.66/50.73); L525 90.82/64.06 r_next=0.018 MAD_above=18.01 lag=-1(17.54/18.01); direct-full=L524 (L524 internal blank x=58-121 Y=1.359; above=166.719 following=118.000; gate=4.000) |
| 700 | 700/F2 | L523 | L524 | L522 119.27/42.12 r_next=0.022 MAD_above=9.93 lag=1(9.51/9.93); L523 120.96/47.38 r_next=0.174 MAD_above=50.77 lag=32(45.93/50.77); L524 86.25/61.36 r_next=0.888 MAD_above=50.17 lag=-1(49.84/50.17); L525 92.80/65.01 r_next=-0.011 MAD_above=20.06 lag=1(19.78/20.06); direct-full=L524 (L524 internal blank x=58-121 Y=1.422; above=167.797 following=109.000; gate=4.000) |
| 701 | 701/F2 | L522 | L524 | L521 119.02/42.81 r_next=0.920 MAD_above=10.23 lag=0(10.23/10.23); L522 121.35/41.83 r_next=0.044 MAD_above=10.08 lag=1(9.65/10.08); L523 120.79/47.89 r_next=0.170 MAD_above=50.89 lag=30(46.68/50.89); L524 88.07/61.26 r_next=0.907 MAD_above=49.75 lag=-2(49.43/49.75); L525 92.96/64.73 r_next=0.014 MAD_above=16.47 lag=1(16.15/16.47); direct-full=L524 (L524 internal blank x=61-124 Y=1.422; above=165.531 following=115.500; gate=4.000) |
| 702 | 702/F2 | L523 | L524 | L522 121.96/41.84 r_next=0.030 MAD_above=9.20 lag=1(8.88/9.20); L523 122.94/47.42 r_next=0.151 MAD_above=50.90 lag=25(47.67/50.90); L524 88.24/61.09 r_next=0.904 MAD_above=50.97 lag=-1(50.51/50.97); L525 94.17/66.39 r_next=0.018 MAD_above=18.89 lag=1(18.58/18.89); direct-full=L524 (L524 internal blank x=63-126 Y=1.359; above=168.125 following=110.500; gate=4.000) |
| 703 | 703/F2 | L523 | L524 | L522 121.35/41.77 r_next=0.029 MAD_above=10.31 lag=1(9.47/10.31); L523 122.84/47.66 r_next=0.165 MAD_above=50.20 lag=27(47.39/50.20); L524 89.65/61.15 r_next=0.907 MAD_above=49.38 lag=0(49.38/49.38); L525 90.85/63.59 r_next=0.036 MAD_above=16.35 lag=1(16.34/16.35); direct-full=L524 (L524 internal blank x=64-127 Y=1.406; above=168.609 following=116.500; gate=4.000) |
| 704 | 704/F2 | L523 | L524 | L522 122.96/42.50 r_next=0.033 MAD_above=9.46 lag=1(9.40/9.46); L523 124.69/47.98 r_next=0.172 MAD_above=50.93 lag=24(47.03/50.93); L524 87.00/61.28 r_next=0.900 MAD_above=52.92 lag=1(52.78/52.92); L525 91.79/64.03 r_next=0.046 MAD_above=18.55 lag=0(18.55/18.55); direct-full=L524 (L524 internal blank x=65-128 Y=1.375; above=170.484 following=116.000; gate=4.000) |
| 705 | 705/F2 | L523 | L524 | L522 120.94/41.73 r_next=0.017 MAD_above=8.50 lag=1(8.10/8.50); L523 120.40/46.00 r_next=0.159 MAD_above=50.19 lag=31(46.11/50.19); L524 88.90/62.47 r_next=0.900 MAD_above=50.63 lag=0(50.63/50.63); L525 91.43/64.29 r_next=0.034 MAD_above=17.33 lag=1(16.76/17.33); direct-full=L524 (L524 internal blank x=53-116 Y=1.312; above=165.188 following=112.500; gate=4.000) |
| 706 | 706/F2 | L523 | L524 | L522 118.24/40.58 r_next=0.017 MAD_above=9.21 lag=1(8.85/9.21); L523 120.70/45.68 r_next=0.173 MAD_above=49.39 lag=25(46.38/49.39); L524 86.05/59.88 r_next=0.910 MAD_above=48.77 lag=0(48.77/48.77); L525 91.88/64.59 r_next=-0.012 MAD_above=17.83 lag=0(17.83/17.83); direct-full=L524 (L524 internal blank x=66-129 Y=1.359; above=166.891 following=111.500; gate=4.000) |
| 708 | 708/F2 | L523 | L524 | L522 119.90/40.55 r_next=-0.015 MAD_above=9.29 lag=1(9.25/9.29); L523 119.03/47.38 r_next=0.177 MAD_above=50.50 lag=24(46.13/50.50); L524 86.64/61.18 r_next=0.912 MAD_above=49.23 lag=-1(48.88/49.23); L525 91.71/64.16 r_next=-0.001 MAD_above=17.37 lag=-1(17.25/17.37); direct-full=L524 (L524 internal blank x=54-117 Y=1.281; above=165.688 following=113.000; gate=4.000) |
| 709 | 709/F2 | L523 | L524 | L522 120.41/41.36 r_next=0.114 MAD_above=9.44 lag=1(9.09/9.44); L523 126.37/47.22 r_next=0.161 MAD_above=48.50 lag=24(46.03/48.50); L524 88.14/61.55 r_next=0.901 MAD_above=52.47 lag=-1(52.13/52.47); L525 92.76/64.89 r_next=0.056 MAD_above=17.82 lag=0(17.82/17.82); direct-full=L524 (L524 internal blank x=55-118 Y=1.328; above=165.391 following=112.000; gate=4.000) |
| 710 | 710/F2 | L523 | L524 | L522 120.57/41.10 r_next=0.096 MAD_above=9.80 lag=1(9.22/9.80); L523 125.42/46.60 r_next=0.147 MAD_above=49.29 lag=32(47.65/49.29); L524 88.58/61.77 r_next=0.891 MAD_above=50.79 lag=0(50.79/50.79); L525 92.69/63.89 r_next=0.039 MAD_above=19.83 lag=1(19.55/19.83); direct-full=L524 (L524 internal blank x=51-114 Y=1.328; above=163.078 following=112.500; gate=4.000) |
| 711 | 711/F2 | L523 | L524 | L522 121.72/41.32 r_next=-0.020 MAD_above=10.05 lag=1(9.77/10.05); L523 116.69/47.92 r_next=0.158 MAD_above=51.94 lag=26(47.93/51.94); L524 87.04/61.34 r_next=0.898 MAD_above=50.81 lag=1(50.78/50.81); L525 93.07/64.19 r_next=-0.004 MAD_above=18.27 lag=0(18.27/18.27); direct-full=L524 (L524 internal blank x=51-114 Y=1.328; above=161.797 following=108.000; gate=4.000) |
| 712 | 712/F2 | L523 | L524 | L522 119.33/41.51 r_next=-0.001 MAD_above=9.80 lag=1(9.77/9.80); L523 121.67/46.37 r_next=0.200 MAD_above=50.49 lag=26(45.50/50.49); L524 86.60/62.15 r_next=0.893 MAD_above=50.54 lag=-1(50.04/50.54); L525 92.47/63.53 r_next=0.017 MAD_above=19.41 lag=-1(19.24/19.41); direct-full=L524 (L524 internal blank x=52-115 Y=1.359; above=168.484 following=111.000; gate=4.000) |
| 714 | 714/F2 | L523 | L524 | L522 118.98/41.14 r_next=0.019 MAD_above=8.85 lag=1(8.49/8.85); L523 121.25/47.65 r_next=0.203 MAD_above=51.62 lag=25(46.59/51.62); L524 85.99/59.86 r_next=0.900 MAD_above=48.44 lag=-2(47.92/48.44); L525 91.78/63.87 r_next=-0.011 MAD_above=17.94 lag=-1(17.38/17.94); direct-full=L524 (L524 internal blank x=62-125 Y=1.344; above=168.578 following=116.000; gate=4.000) |
| 715 | 715/F2 | L523 | L524 | L522 119.57/41.26 r_next=0.022 MAD_above=9.99 lag=1(9.73/9.99); L523 115.44/51.14 r_next=0.220 MAD_above=52.64 lag=26(48.87/52.64); L524 86.57/59.63 r_next=0.914 MAD_above=46.12 lag=-2(45.57/46.12); L525 91.76/63.09 r_next=0.029 MAD_above=16.83 lag=0(16.83/16.83); direct-full=L524 (L524 internal blank x=64-127 Y=1.422; above=166.531 following=111.500; gate=4.000) |
| 716 | 716/F2 | L523 | L524 | L522 117.62/40.76 r_next=0.049 MAD_above=8.97 lag=1(8.57/8.97); L523 123.12/46.89 r_next=0.138 MAD_above=50.42 lag=30(45.88/50.42); L524 85.60/60.58 r_next=0.893 MAD_above=52.07 lag=-2(51.44/52.07); L525 89.70/61.72 r_next=-0.026 MAD_above=17.99 lag=-1(17.48/17.99); direct-full=L524 (L524 internal blank x=57-120 Y=1.359; above=162.531 following=109.000; gate=4.000) |
| 717 | 717/F2 | L523 | L524 | L522 119.30/40.76 r_next=0.101 MAD_above=9.91 lag=1(9.22/9.91); L523 121.98/49.70 r_next=0.186 MAD_above=50.65 lag=24(47.87/50.65); L524 87.43/60.29 r_next=0.904 MAD_above=49.76 lag=0(49.76/49.76); L525 91.33/64.01 r_next=0.022 MAD_above=16.65 lag=-1(16.27/16.65); direct-full=L524 (L524 internal blank x=52-115 Y=1.375; above=163.422 following=113.500; gate=4.000) |
| 718 | 718/F2 | L523 | L524 | L522 121.27/40.94 r_next=0.067 MAD_above=10.47 lag=1(10.20/10.47); L523 124.88/48.56 r_next=0.174 MAD_above=50.83 lag=29(47.30/50.83); L524 86.75/60.15 r_next=0.910 MAD_above=49.72 lag=0(49.72/49.72); L525 92.12/63.51 r_next=-0.031 MAD_above=17.13 lag=0(17.13/17.13); direct-full=L524 (L524 internal blank x=61-124 Y=1.312; above=165.812 following=111.000; gate=4.000) |
| 719 | 719/F2 | L523 | L524 | L522 120.60/40.69 r_next=0.048 MAD_above=10.33 lag=1(9.95/10.33); L523 122.23/47.88 r_next=0.156 MAD_above=50.22 lag=32(46.90/50.22); L524 87.00/59.58 r_next=0.902 MAD_above=51.20 lag=-2(50.32/51.20); L525 90.13/62.50 r_next=-0.009 MAD_above=16.95 lag=-1(16.85/16.95); direct-full=L524 (L524 internal blank x=47-110 Y=1.438; above=160.047 following=109.500; gate=4.000) |
| 720 | 720/F2 | L523 | L524 | L522 119.46/41.14 r_next=0.013 MAD_above=10.31 lag=1(9.72/10.31); L523 125.15/48.50 r_next=0.155 MAD_above=52.87 lag=23(49.29/52.87); L524 85.90/59.91 r_next=0.900 MAD_above=51.90 lag=-2(51.25/51.90); L525 90.09/63.37 r_next=-0.006 MAD_above=18.15 lag=-1(18.05/18.15); direct-full=L524 (L524 internal blank x=55-118 Y=1.422; above=165.875 following=112.000; gate=4.000) |
| 721 | 721/F2 | L523 | L524 | L522 118.45/40.64 r_next=0.013 MAD_above=9.80 lag=1(9.43/9.80); L523 115.84/46.68 r_next=0.199 MAD_above=50.07 lag=21(45.09/50.07); L524 85.04/60.76 r_next=0.884 MAD_above=46.39 lag=-2(45.25/46.39); L525 86.95/60.82 r_next=-0.002 MAD_above=16.94 lag=-1(16.74/16.94); direct-full=L524 (L524 internal blank x=46-109 Y=1.328; above=155.203 following=113.000; gate=4.000) |
| 722 | 722/F2 | L523 | L524 | L522 118.87/40.37 r_next=0.019 MAD_above=10.16 lag=1(9.43/10.16); L523 116.20/47.74 r_next=0.228 MAD_above=51.56 lag=25(47.19/51.56); L524 86.62/60.17 r_next=0.918 MAD_above=46.18 lag=-3(44.51/46.18); L525 89.52/61.93 r_next=-0.024 MAD_above=16.02 lag=0(16.02/16.02); direct-full=L524 (L524 internal blank x=53-116 Y=1.422; above=162.078 following=111.000; gate=4.000) |
| 723 | 723/F2 | L523 | L524 | L522 120.39/40.11 r_next=0.004 MAD_above=9.84 lag=1(9.28/9.84); L523 118.67/46.50 r_next=0.174 MAD_above=50.58 lag=27(45.33/50.58); L524 85.39/59.64 r_next=0.891 MAD_above=48.13 lag=-1(47.71/48.13); L525 88.73/62.00 r_next=0.056 MAD_above=16.55 lag=1(16.50/16.55); direct-full=L524 (L524 internal blank x=58-121 Y=1.297; above=165.031 following=114.000; gate=4.000) |
| 724 | 724/F2 | L522 | L524 | L521 121.61/41.35 r_next=0.920 MAD_above=10.08 lag=1(9.74/10.08); L522 120.45/40.40 r_next=-0.012 MAD_above=9.45 lag=1(8.89/9.45); L523 119.52/47.77 r_next=0.199 MAD_above=52.08 lag=22(45.77/52.08); L524 85.18/59.71 r_next=0.905 MAD_above=48.95 lag=-2(48.02/48.95); L525 89.43/62.31 r_next=0.035 MAD_above=16.80 lag=0(16.80/16.80); direct-full=L524 (L524 internal blank x=83-146 Y=1.406; above=164.969 following=107.500; gate=4.000) |
| 725 | 725/F2 | L522 | L524 | L521 117.03/41.21 r_next=0.914 MAD_above=9.82 lag=0(9.82/9.82); L522 119.17/40.39 r_next=0.021 MAD_above=9.98 lag=1(9.65/9.98); L523 116.92/46.28 r_next=0.178 MAD_above=50.22 lag=21(45.29/50.22); L524 84.88/59.37 r_next=0.887 MAD_above=48.00 lag=-2(47.00/48.00); L525 87.52/62.30 r_next=0.009 MAD_above=18.18 lag=-1(17.78/18.18); direct-full=L524 (L524 internal blank x=59-122 Y=1.312; above=164.312 following=114.500; gate=4.000) |
| 726 | 726/F2 | L522 | L524 | L521 117.72/41.21 r_next=0.922 MAD_above=9.14 lag=1(9.05/9.14); L522 117.53/39.43 r_next=-0.040 MAD_above=9.03 lag=1(8.82/9.03); L523 113.85/46.52 r_next=0.171 MAD_above=50.84 lag=24(45.17/50.84); L524 83.67/59.45 r_next=0.888 MAD_above=48.93 lag=0(48.93/48.93); L525 87.48/61.49 r_next=0.035 MAD_above=18.25 lag=1(18.08/18.25); direct-full=L524 (L524 internal blank x=49-112 Y=1.312; above=155.188 following=103.000; gate=4.000) |
| 727 | 727/F2 | L523 | L524 | L522 116.67/40.59 r_next=0.020 MAD_above=9.63 lag=1(9.60/9.63); L523 117.83/47.30 r_next=0.155 MAD_above=49.84 lag=27(46.33/49.84); L524 84.79/58.67 r_next=0.896 MAD_above=47.90 lag=-1(47.65/47.90); L525 86.78/61.48 r_next=0.005 MAD_above=16.65 lag=-1(16.19/16.65); direct-full=L524 (L524 internal blank x=55-118 Y=1.375; above=162.469 following=110.000; gate=4.000) |
| 728 | 728/F2 | L523 | L524 | L522 116.70/40.61 r_next=-0.061 MAD_above=9.38 lag=0(9.38/9.38); L523 114.12/46.60 r_next=0.151 MAD_above=51.68 lag=23(45.57/51.68); L524 84.80/59.74 r_next=0.907 MAD_above=48.58 lag=2(48.22/48.58); L525 86.96/61.47 r_next=0.038 MAD_above=15.95 lag=0(15.95/15.95); direct-full=L524 (L524 internal blank x=52-115 Y=1.375; above=159.609 following=107.500; gate=4.000) |
| 730 | 730/F2 | L523 | L524 | L522 116.26/40.63 r_next=0.127 MAD_above=10.09 lag=1(9.68/10.09); L523 121.73/45.13 r_next=0.170 MAD_above=45.85 lag=22(43.96/45.85); L524 82.69/59.12 r_next=0.899 MAD_above=50.71 lag=0(50.71/50.71); L525 87.54/62.42 r_next=0.008 MAD_above=17.10 lag=1(16.78/17.10); direct-full=L524 (L524 internal blank x=52-115 Y=1.391; above=160.438 following=108.000; gate=4.000) |
| 731 | 731/F2 | L523 | L524 | L522 116.36/39.94 r_next=0.129 MAD_above=8.98 lag=0(8.98/8.98); L523 118.90/43.98 r_next=0.147 MAD_above=44.84 lag=25(42.40/44.84); L524 83.64/58.64 r_next=0.900 MAD_above=48.72 lag=-1(48.69/48.72); L525 86.20/60.59 r_next=-0.032 MAD_above=16.60 lag=-1(16.20/16.60); direct-full=L524 (L524 internal blank x=52-115 Y=1.375; above=156.109 following=107.500; gate=4.000) |
| 732 | 732/F2 | L523 | L524 | L522 113.73/40.14 r_next=0.040 MAD_above=10.08 lag=1(9.69/10.08); L523 116.83/45.97 r_next=0.164 MAD_above=48.88 lag=32(45.37/48.88); L524 81.06/57.97 r_next=0.894 MAD_above=49.24 lag=1(49.22/49.24); L525 85.84/61.08 r_next=0.035 MAD_above=17.71 lag=0(17.71/17.71); direct-full=L524 (L524 internal blank x=48-111 Y=1.391; above=152.328 following=107.000; gate=4.000) |
| 733 | 733/F2 | L523 | L524 | L522 114.54/40.38 r_next=0.093 MAD_above=8.96 lag=1(8.73/8.96); L523 116.04/47.12 r_next=0.144 MAD_above=48.67 lag=23(45.81/48.67); L524 82.89/58.27 r_next=0.885 MAD_above=48.62 lag=-1(48.50/48.62); L525 85.73/60.85 r_next=-0.036 MAD_above=18.73 lag=-2(18.00/18.73); direct-full=L524 (L524 internal blank x=84-147 Y=1.359; above=158.219 following=106.000; gate=4.000) |
| 734 | 734/F2 | L523 | L524 | L522 114.78/40.33 r_next=-0.008 MAD_above=10.37 lag=1(9.70/10.37); L523 115.66/42.99 r_next=0.163 MAD_above=48.14 lag=24(44.36/48.14); L524 83.06/58.08 r_next=0.902 MAD_above=46.83 lag=0(46.83/46.83); L525 88.41/61.05 r_next=0.020 MAD_above=17.05 lag=1(17.04/17.05); direct-full=L524 (L524 internal blank x=76-139 Y=1.266; above=158.297 following=108.500; gate=4.000) |
| 735 | 735/F2 | L523 | L524 | L522 115.95/40.11 r_next=0.055 MAD_above=9.03 lag=0(9.03/9.03); L523 116.25/46.27 r_next=0.177 MAD_above=49.39 lag=31(44.87/49.39); L524 83.57/58.74 r_next=0.894 MAD_above=48.26 lag=1(48.13/48.26); L525 86.71/60.95 r_next=0.055 MAD_above=16.30 lag=0(16.30/16.30); direct-full=L524 (L524 internal blank x=69-132 Y=1.375; above=156.766 following=110.500; gate=4.000) |
| 736 | 736/F2 | L523 | L524 | L522 113.45/39.93 r_next=0.004 MAD_above=9.29 lag=1(9.21/9.29); L523 114.23/45.33 r_next=0.175 MAD_above=48.99 lag=26(44.54/48.99); L524 81.62/58.17 r_next=0.899 MAD_above=48.18 lag=0(48.18/48.18); L525 86.61/61.71 r_next=0.020 MAD_above=16.76 lag=-1(16.58/16.76); direct-full=L524 (L524 internal blank x=52-115 Y=1.328; above=157.422 following=104.500; gate=4.000) |
| 737 | 737/F2 | L523 | L524 | L522 116.69/40.53 r_next=0.006 MAD_above=9.94 lag=1(9.65/9.94); L523 115.97/44.79 r_next=0.150 MAD_above=47.85 lag=26(44.46/47.85); L524 83.78/58.21 r_next=0.907 MAD_above=47.50 lag=0(47.50/47.50); L525 87.99/61.70 r_next=0.003 MAD_above=16.85 lag=1(16.75/16.85); direct-full=L524 (L524 internal blank x=73-136 Y=1.375; above=159.922 following=110.500; gate=4.000) |
| 738 | 738/F2 | L523 | L524 | L522 113.69/39.62 r_next=-0.033 MAD_above=10.05 lag=1(9.42/10.05); L523 113.85/45.08 r_next=0.256 MAD_above=49.08 lag=26(43.74/49.08); L524 83.19/58.79 r_next=0.857 MAD_above=41.57 lag=0(41.57/41.57); L525 86.90/61.47 r_next=0.031 MAD_above=20.62 lag=1(20.42/20.62); direct-full=L524 (L524 internal blank x=61-124 Y=1.406; above=156.859 following=113.000; gate=4.000) |
| 739 | 739/F2 | L523 | L524 | L522 114.70/39.22 r_next=-0.016 MAD_above=9.41 lag=1(8.75/9.41); L523 114.03/45.56 r_next=0.168 MAD_above=48.81 lag=24(45.41/48.81); L524 83.28/58.89 r_next=0.908 MAD_above=47.67 lag=-1(47.65/47.67); L525 87.00/60.18 r_next=0.035 MAD_above=16.07 lag=0(16.07/16.07); direct-full=L524 (L524 internal blank x=52-115 Y=1.328; above=157.859 following=106.000; gate=4.000) |
| 740 | 740/F2 | L523 | L524 | L522 113.36/40.80 r_next=-0.011 MAD_above=10.20 lag=1(9.88/10.20); L523 113.87/45.30 r_next=0.159 MAD_above=49.62 lag=25(45.04/49.62); L524 81.74/58.29 r_next=0.894 MAD_above=48.37 lag=0(48.37/48.37); L525 86.08/60.36 r_next=0.044 MAD_above=16.67 lag=0(16.67/16.67); direct-full=L524 (L524 internal blank x=60-123 Y=1.359; above=157.172 following=108.500; gate=4.000) |
| 741 | 741/F2 | L523 | L524 | L522 113.95/39.00 r_next=-0.027 MAD_above=9.37 lag=0(9.37/9.37); L523 112.34/46.02 r_next=0.121 MAD_above=49.89 lag=32(43.73/49.89); L524 82.83/57.36 r_next=0.906 MAD_above=47.91 lag=2(47.23/47.91); L525 86.37/60.51 r_next=-0.001 MAD_above=16.15 lag=0(16.15/16.15); direct-full=L524 (L524 internal blank x=62-125 Y=1.344; above=158.547 following=103.000; gate=4.000) |
| 742 | 742/F2 | L523 | L524 | L522 114.02/40.56 r_next=0.028 MAD_above=9.36 lag=1(9.13/9.36); L523 112.85/45.28 r_next=0.198 MAD_above=49.49 lag=25(44.89/49.49); L524 81.86/58.74 r_next=0.894 MAD_above=46.74 lag=-1(46.61/46.74); L525 85.65/61.55 r_next=0.018 MAD_above=17.62 lag=0(17.62/17.62); direct-full=L524 (L524 internal blank x=113-176 Y=1.344; above=135.828 following=105.000; gate=4.000) |
| 743 | 743/F2 | L523 | L524 | L522 112.34/39.61 r_next=0.011 MAD_above=9.48 lag=0(9.48/9.48); L523 111.32/45.60 r_next=0.180 MAD_above=48.38 lag=26(45.10/48.38); L524 81.09/57.69 r_next=0.896 MAD_above=46.27 lag=-2(45.56/46.27); L525 82.03/58.59 r_next=-0.002 MAD_above=15.85 lag=0(15.85/15.85); direct-full=L524 (L524 internal blank x=52-115 Y=1.312; above=154.406 following=107.000; gate=4.000) |
| 744 | 744/F2 | L523 | L524 | L522 111.06/40.47 r_next=-0.008 MAD_above=11.12 lag=1(10.51/11.12); L523 113.65/44.52 r_next=0.177 MAD_above=48.86 lag=24(47.28/48.86); L524 81.71/56.90 r_next=0.898 MAD_above=46.33 lag=-2(45.79/46.33); L525 82.20/59.25 r_next=-0.001 MAD_above=15.45 lag=1(15.22/15.45); direct-full=L524 (L524 internal blank x=51-114 Y=1.391; above=149.469 following=106.000; gate=4.000) |
| 745 | 745/F2 | L523 | L524 | L522 108.90/38.47 r_next=-0.024 MAD_above=9.73 lag=1(9.40/9.73); L523 109.45/44.61 r_next=0.174 MAD_above=48.52 lag=27(45.99/48.52); L524 79.13/56.41 r_next=0.888 MAD_above=46.89 lag=-2(45.81/46.89); L525 79.98/57.49 r_next=-0.040 MAD_above=16.03 lag=0(16.03/16.03); direct-full=L524 (L524 internal blank x=55-118 Y=1.328; above=152.719 following=105.500; gate=4.000) |
| 746 | 746/F2 | L523 | L524 | L522 108.42/39.30 r_next=-0.049 MAD_above=12.07 lag=1(11.49/12.07); L523 110.17/42.94 r_next=0.214 MAD_above=48.13 lag=28(46.73/48.13); L524 78.76/54.21 r_next=0.916 MAD_above=43.15 lag=-1(43.11/43.15); L525 80.80/58.16 r_next=0.010 MAD_above=14.65 lag=1(14.52/14.65); direct-full=L524 (L524 internal blank x=52-115 Y=1.375; above=143.391 following=107.000; gate=4.000) |
| 747 | 747/F2 | L523 | L524 | L522 110.52/39.39 r_next=-0.121 MAD_above=11.78 lag=0(11.78/11.78); L523 107.83/42.24 r_next=0.237 MAD_above=51.23 lag=11(48.46/51.23); L524 77.90/53.84 r_next=0.912 MAD_above=42.29 lag=-2(41.98/42.29); L525 80.69/57.10 r_next=-0.013 MAD_above=14.72 lag=-1(14.58/14.72); direct-full=L524 (L524 internal blank x=92-155 Y=1.297; above=147.047 following=94.000; gate=4.000) |
| 748 | 748/F2 | L523 | L524 | L522 105.11/39.07 r_next=-0.168 MAD_above=14.87 lag=0(14.87/14.87); L523 97.71/42.36 r_next=0.371 MAD_above=52.07 lag=25(49.49/52.07); L524 74.89/50.71 r_next=0.924 MAD_above=34.37 lag=-2(33.76/34.37); L525 78.92/55.25 r_next=0.006 MAD_above=13.73 lag=0(13.73/13.73); direct-full=L524 (L524 internal blank x=57-120 Y=1.375; above=117.188 following=91.000; gate=4.000) |
| 750 | 750/F2 | L524 | L525 | L523 100.06/36.96 r_next=-0.120 MAD_above=12.25 lag=1(11.71/12.25); L524 92.45/38.77 r_next=0.326 MAD_above=45.60 lag=10(43.06/45.60); L525 69.65/47.86 r_next=0.003 MAD_above=35.86 lag=-1(35.55/35.86); direct-full=L525 (L525 internal blank x=51-114 Y=1.328; above=94.516 following=80.000; gate=4.000) |
| 751 | 751/F2 | L524 | L525 | L523 94.27/36.67 r_next=-0.186 MAD_above=14.50 lag=0(14.50/14.50); L524 84.26/39.38 r_next=0.497 MAD_above=48.15 lag=10(46.08/48.15); L525 64.62/45.18 r_next=0.017 MAD_above=29.92 lag=-2(29.40/29.92); direct-full=L525 (L525 internal blank x=72-135 Y=1.344; above=91.922 following=77.000; gate=4.000) |
| 753 | 753/F2 | L524 | L525 | L523 89.59/35.77 r_next=-0.008 MAD_above=14.66 lag=1(13.84/14.66); L524 85.27/37.46 r_next=0.517 MAD_above=39.54 lag=-1(39.53/39.54); L525 68.51/46.45 r_next=0.010 MAD_above=28.15 lag=-2(27.30/28.15); direct-full=L525 (L525 internal blank x=51-114 Y=1.391; above=69.094 following=80.500; gate=4.000) |
| 754 | 754/F2 | L524 | L525 | L523 89.37/35.57 r_next=0.047 MAD_above=11.96 lag=1(11.22/11.96); L524 85.52/34.26 r_next=0.553 MAD_above=36.31 lag=-1(36.18/36.31); L525 67.72/46.02 r_next=-0.007 MAD_above=27.05 lag=-2(25.93/27.05); direct-full=L525 (L525 internal blank x=60-123 Y=1.359; above=74.828 following=79.000; gate=4.000) |
| 762 | 762/F2 | L523 | L524 | L522 87.04/33.72 r_next=0.505 MAD_above=10.11 lag=1(9.59/10.11); L523 97.26/35.80 r_next=0.266 MAD_above=26.93 lag=-2(26.62/26.93); L524 69.02/48.33 r_next=0.926 MAD_above=35.88 lag=-1(35.76/35.88); L525 70.56/52.38 r_next=0.039 MAD_above=10.22 lag=1(10.16/10.22); direct-full=L524 (L524 internal blank x=53-116 Y=1.344; above=97.219 following=83.500; gate=4.000) |
| 772 | 772/F2 | L523 | L524 | L522 83.90/35.13 r_next=0.152 MAD_above=10.64 lag=1(9.34/10.64); L523 85.85/42.75 r_next=0.567 MAD_above=36.93 lag=0(36.93/36.93); L524 70.98/49.48 r_next=0.927 MAD_above=25.45 lag=-1(25.10/25.45); L525 78.08/55.11 r_next=0.030 MAD_above=12.88 lag=0(12.88/12.88); direct-full=L524 (L524 internal blank x=90-153 Y=1.344; above=116.297 following=89.500; gate=4.000) |

### Engine field 2

S minus reference switch histogram: -4: 2, -3: 1, -2: 10, -1: 63, +0: 223, +1: 296, +2: 2, engine-unmeasurable: 10

Differences beyond the one-row semantic gap:

| engine counter | raw counter/field | S | reference switch | raw tail rows |
|---:|:---:|:---|:---|:---|
| 222 | 223/F1 | L259 | L261 | L258 84.30/35.67 r_next=0.950 MAD_above=8.08 lag=0(8.08/8.08); L259 83.03/35.70 r_next=0.849 MAD_above=8.52 lag=0(8.52/8.52); L260 80.66/34.55 r_next=-0.247 MAD_above=13.32 lag=5(8.29/13.32); L261 60.82/47.16 r_next=0.899 MAD_above=56.75 lag=-32(54.71/56.75); L262 58.05/45.04 r_next=0.028 MAD_above=12.36 lag=-5(10.08/12.36); direct-full=L261 (L261 persistent three-third step; thirds=10.747,3.806,4.769; correlation above/next=-0.271/0.936; middle coherence=0.884) |
| 387 | 388/F1 | L257 | L261 | L256 96.89/49.88 r_next=0.887 MAD_above=9.74 lag=0(9.74/9.74); L257 97.95/47.89 r_next=0.881 MAD_above=13.98 lag=1(13.45/13.98); L258 101.16/47.82 r_next=0.856 MAD_above=14.88 lag=0(14.88/14.88); L259 102.45/47.22 r_next=0.857 MAD_above=15.92 lag=0(15.92/15.92); L260 97.45/49.93 r_next=0.899 MAD_above=16.86 lag=-1(16.79/16.86); L261 98.94/48.76 r_next=0.229 MAD_above=13.00 lag=-1(12.09/13.00); L262 103.05/50.54 r_next=-0.010 MAD_above=45.39 lag=0(45.39/45.39); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.919; no internal horizontal blanking run; gate=4.000) |
| 390 | 391/F1 | L259 | L261 | L258 101.50/48.07 r_next=0.863 MAD_above=17.08 lag=0(17.08/17.08); L259 98.33/51.28 r_next=0.996 MAD_above=17.24 lag=0(17.24/17.24); L260 96.80/51.70 r_next=0.573 MAD_above=3.72 lag=0(3.72/3.72); L261 101.06/54.65 r_next=0.293 MAD_above=30.49 lag=-1(28.65/30.49); L262 17.53/40.78 r_next=0.007 MAD_above=83.69 lag=0(83.69/83.69); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.914; no internal horizontal blanking run; gate=4.000) |
| 394 | 395/F1 | L258 | L262 | L257 106.84/48.31 r_next=0.953 MAD_above=18.23 lag=0(18.23/18.23); L258 103.97/47.80 r_next=0.996 MAD_above=7.23 lag=0(7.23/7.23); L259 102.21/47.94 r_next=0.996 MAD_above=2.84 lag=0(2.84/2.84); L260 102.50/48.53 r_next=0.721 MAD_above=2.96 lag=0(2.96/2.96); L261 92.18/51.87 r_next=0.622 MAD_above=12.50 lag=0(12.50/12.50); L262 44.82/61.63 r_next=0.023 MAD_above=49.01 lag=0(49.01/49.01); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.917; no internal horizontal blanking run; gate=4.000) |
| 404 | 405/F1 | L259 | L261 | L258 97.36/47.96 r_next=0.849 MAD_above=14.58 lag=0(14.58/14.58); L259 100.08/45.51 r_next=0.837 MAD_above=16.45 lag=0(16.45/16.45); L260 97.96/47.38 r_next=-0.295 MAD_above=18.76 lag=-4(13.52/18.76); L261 84.92/57.13 r_next=0.868 MAD_above=70.78 lag=32(63.87/70.78); L262 82.33/59.52 r_next=-0.001 MAD_above=19.45 lag=2(17.34/19.45); direct-full=L261 (L261 persistent three-third step; thirds=9.639,3.092,4.088; correlation above/next=-0.332/0.908; middle coherence=0.915) |
| 495 | 496/F1 | L261 | L259 | L258 91.90/55.74 r_next=0.990 MAD_above=8.38 lag=0(8.38/8.38); L259 90.58/55.54 r_next=0.935 MAD_above=6.27 lag=0(6.27/6.27); L260 85.72/58.20 r_next=0.227 MAD_above=11.55 lag=0(11.55/11.55); L261 45.07/43.64 r_next=0.940 MAD_above=60.40 lag=0(60.40/60.40); L262 46.31/44.71 r_next=0.016 MAD_above=8.68 lag=0(8.68/8.68); direct-full=L260 (L260 internal blank x=177-240 Y=3.312; above=8.344 following=107.500; gate=4.000) |
| 498 | 499/F1 | L261 | L259 | L258 89.94/55.97 r_next=0.982 MAD_above=8.53 lag=0(8.53/8.53); L259 85.25/56.39 r_next=0.897 MAD_above=8.55 lag=0(8.55/8.55); L260 78.63/51.69 r_next=0.037 MAD_above=12.73 lag=1(12.37/12.73); L261 47.10/43.73 r_next=0.945 MAD_above=58.60 lag=-30(56.81/58.60); L262 47.96/45.69 r_next=0.010 MAD_above=9.22 lag=0(9.22/9.22); direct-full=L259 (L259 internal blank x=177-240 Y=3.766; above=9.203 following=106.000; gate=4.000) |
| 565 | 566/F1 | L259 | L261 | L258 105.25/56.53 r_next=0.961 MAD_above=12.90 lag=0(12.90/12.90); L259 108.56/55.90 r_next=0.886 MAD_above=10.53 lag=0(10.53/10.53); L260 104.22/56.75 r_next=0.209 MAD_above=10.51 lag=-1(10.40/10.51); L261 62.20/50.63 r_next=0.886 MAD_above=68.87 lag=32(67.11/68.87); L262 60.17/50.71 r_next=0.047 MAD_above=13.88 lag=1(13.87/13.88); direct-full=L261 (L261 persistent three-third step; thirds=9.272,4.736,8.684; correlation above/next=0.153/0.908; middle coherence=0.937) |
| 568 | 569/F1 | L259 | L261 | L258 104.67/59.15 r_next=0.978 MAD_above=10.40 lag=0(10.40/10.40); L259 105.76/58.01 r_next=0.949 MAD_above=8.23 lag=0(8.23/8.23); L260 105.68/59.19 r_next=0.126 MAD_above=10.08 lag=-2(8.20/10.08); L261 61.04/49.71 r_next=0.909 MAD_above=72.59 lag=32(70.12/72.59); L262 62.13/52.14 r_next=-0.007 MAD_above=14.06 lag=-2(13.40/14.06); direct-full=L261 (L261 persistent three-third step; thirds=9.516,5.147,8.668; correlation above/next=0.105/0.930; middle coherence=0.939) |
| 571 | 572/F1 | L259 | L261 | L258 101.68/60.47 r_next=0.979 MAD_above=10.45 lag=0(10.45/10.45); L259 104.01/57.98 r_next=0.943 MAD_above=8.63 lag=0(8.63/8.63); L260 98.37/54.73 r_next=0.048 MAD_above=10.15 lag=-1(9.42/10.15); L261 60.21/49.89 r_next=0.958 MAD_above=69.87 lag=-25(69.18/69.87); L262 62.08/49.97 r_next=-0.009 MAD_above=10.61 lag=1(10.50/10.61); direct-full=L261 (L261 persistent three-third step; thirds=9.271,5.521,8.041; correlation above/next=0.018/0.972; middle coherence=0.933) |
| 593 | 594/F1 | L258 | L260 | L257 110.03/57.56 r_next=0.960 MAD_above=8.14 lag=0(8.14/8.14); L258 108.87/58.43 r_next=0.975 MAD_above=10.26 lag=0(10.26/10.26); L259 111.56/58.50 r_next=0.868 MAD_above=8.69 lag=0(8.69/8.69); L260 103.07/51.35 r_next=0.950 MAD_above=16.64 lag=-3(13.48/16.64); L261 99.74/50.64 r_next=0.968 MAD_above=9.02 lag=-2(4.02/9.02); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.940; no internal horizontal blanking run; gate=4.000) |
| 623 | 624/F1 | L258 | L260 | L257 93.25/53.69 r_next=0.965 MAD_above=9.48 lag=0(9.48/9.48); L258 95.10/53.65 r_next=0.979 MAD_above=8.63 lag=0(8.63/8.63); L259 98.11/52.94 r_next=0.954 MAD_above=7.75 lag=1(7.70/7.75); L260 92.47/54.52 r_next=0.055 MAD_above=11.22 lag=-2(10.29/11.22); L261 60.98/47.29 r_next=0.906 MAD_above=64.61 lag=-12(62.74/64.61); direct-full=L261 (L261 persistent three-third step; thirds=11.409,3.433,7.667; correlation above/next=0.048/0.923; middle coherence=0.908) |
| 624 | 625/F1 | L259 | L261 | L258 94.69/53.88 r_next=0.981 MAD_above=9.41 lag=1(9.29/9.41); L259 95.14/54.02 r_next=0.960 MAD_above=7.52 lag=0(7.52/7.52); L260 94.93/55.81 r_next=0.064 MAD_above=9.54 lag=-2(8.40/9.54); L261 58.50/47.30 r_next=0.913 MAD_above=65.66 lag=-32(63.54/65.66); L262 56.81/47.27 r_next=0.041 MAD_above=11.45 lag=0(11.45/11.45); direct-full=L261 (L261 persistent three-third step; thirds=11.115,3.143,8.207; correlation above/next=0.066/0.923; middle coherence=0.911) |
| 701 | 702/F1 | L258 | L261 | L257 117.25/42.99 r_next=0.924 MAD_above=11.03 lag=1(10.42/11.03); L258 118.51/43.39 r_next=0.925 MAD_above=10.06 lag=1(10.05/10.06); L259 121.92/42.73 r_next=0.819 MAD_above=9.78 lag=0(9.78/9.78); L260 114.32/41.89 r_next=-0.458 MAD_above=14.23 lag=0(14.23/14.23); L261 88.87/61.87 r_next=0.902 MAD_above=76.90 lag=15(75.60/76.90); L262 87.49/61.05 r_next=0.016 MAD_above=15.23 lag=0(15.23/15.23); direct-full=L261 (L261 internal blank x=76-139 Y=1.312; above=165.094 following=118.500; gate=4.000) |
| 721 | 722/F1 | L259 | L261 | L258 117.64/42.18 r_next=0.911 MAD_above=10.01 lag=1(9.77/10.01); L259 120.00/40.33 r_next=0.800 MAD_above=9.53 lag=1(9.34/9.53); L260 110.15/40.20 r_next=-0.480 MAD_above=15.48 lag=-1(15.07/15.48); L261 84.81/59.65 r_next=0.892 MAD_above=73.66 lag=-31(72.29/73.66); L262 84.73/59.28 r_next=0.007 MAD_above=15.96 lag=-1(15.68/15.96); direct-full=L261 (L261 internal blank x=69-132 Y=1.344; above=160.234 following=103.500; gate=4.000) |

First-full-other-head histogram (engine S minus reference): -3: 2, -2: 24, -1: 128, +0: 428, +1: 1, +2: 1, both-unmeasurable: 9, engine-unmeasurable: 1, reference-unmeasurable: 13

- +1: counters 495.  Witnesses: counter 495: engine L261, direct L260; L260 internal blank x=177-240 Y=3.312; above=8.344 following=107.500; gate=4.000

- +2: counters 498.  Witnesses: counter 498: engine L261, direct L259; L259 internal blank x=177-240 Y=3.766; above=9.203 following=106.000; gate=4.000

- -1: counters 171, 181-182, 186, 192-193, 201, 209-210, 220-221, 227, 245, 250, 256, 262, 282, 293, 297-298, 311, 316-317, 321-322, 332, 334, 339-342, 344-345, 348, 350-351, 357, 362-363, 365, 370, 372-373, 377, 382, 385-386, 400-403, 406, 408-411, 421, 426-427, 441, 445, 449-450, 455, 457, 462, 477, 482, 522, 533-534, 536, 540-541, 545-549, 553-556, 561, 563, 566-567, 570, 573-575, 577, 579, 598, 600-601, 606, 608, 618, 620, 622, 625-629, 632, 634, 648, 651, 658, 677, 680, 682-683, 685, 689, 692, 695, 703, 705, 714, 716, 719, 723, 726, 736, 743.  Witnesses: counter 171: engine L260, direct L261; L261 persistent three-third step; thirds=6.889,3.842,4.591; correlation above/next=-0.058/0.917; middle coherence=0.918 / counter 181: engine L260, direct L261; L261 persistent three-third step; thirds=6.599,3.120,4.151; correlation above/next=0.044/0.935; middle coherence=0.926 / counter 182: engine L260, direct L261; L261 persistent three-third step; thirds=6.718,3.274,4.496; correlation above/next=-0.019/0.928; middle coherence=0.923

- -2: counters 222, 305-306, 324, 347, 349, 361, 374, 383, 404, 453, 461, 552, 560, 565, 568, 571, 597, 624, 644, 666, 707, 710, 721.  Witnesses: counter 222: engine L259, direct L261; L261 persistent three-third step; thirds=10.747,3.806,4.769; correlation above/next=-0.271/0.936; middle coherence=0.884 / counter 305: engine L259, direct L261; L261 persistent three-third step; thirds=10.137,2.985,5.704; correlation above/next=0.263/0.904; middle coherence=0.973 / counter 306: engine L259, direct L261; L261 persistent three-third step; thirds=11.186,3.664,4.700; correlation above/next=0.252/0.831; middle coherence=0.974

- -3: counters 623, 701.  Witnesses: counter 623: engine L258, direct L261; L261 persistent three-third step; thirds=11.409,3.433,7.667; correlation above/next=0.048/0.923; middle coherence=0.908 / counter 701: engine L258, direct L261; L261 internal blank x=76-139 Y=1.312; above=165.094 following=118.500; gate=4.000

- engine-unmeasurable: counters 396.  Witnesses: counter 396: engine unmeasurable, direct L261; L261 internal blank x=141-204 Y=3.750; above=146.953 following=83.500; gate=4.000

- reference-unmeasurable: counters 387, 390, 392-394, 397, 586-588, 591, 593, 595-596.  Witnesses: counter 387: engine L257, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.919; no internal horizontal blanking run; gate=4.000 / counter 390: engine L259, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.914; no internal horizontal blanking run; gate=4.000 / counter 392: engine L260, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.919; no internal horizontal blanking run; gate=4.000

Every numeric first-full disagreement:

| engine counter | raw counter/field | engine S | reference first-full | raw tail rows |
|---:|:---:|:---|:---|:---|
| 171 | 172/F1 | L260 | L261 | L259 103.17/40.57 r_next=0.588 MAD_above=13.08 lag=0(13.08/13.08); L260 85.14/41.62 r_next=-0.003 MAD_above=25.06 lag=-2(23.68/25.06); L261 77.22/55.73 r_next=0.874 MAD_above=55.90 lag=-32(54.55/55.90); L262 71.72/56.12 r_next=-0.031 MAD_above=18.34 lag=0(18.34/18.34); direct-full=L261 (L261 persistent three-third step; thirds=6.889,3.842,4.591; correlation above/next=-0.058/0.917; middle coherence=0.918) |
| 181 | 182/F1 | L260 | L261 | L259 100.41/39.71 r_next=0.801 MAD_above=11.98 lag=0(11.98/11.98); L260 93.87/41.04 r_next=0.092 MAD_above=16.80 lag=-1(16.73/16.80); L261 78.71/54.59 r_next=0.908 MAD_above=51.96 lag=-13(49.99/51.96); L262 72.69/55.28 r_next=0.025 MAD_above=15.29 lag=0(15.29/15.29); direct-full=L261 (L261 persistent three-third step; thirds=6.599,3.120,4.151; correlation above/next=0.044/0.935; middle coherence=0.926) |
| 182 | 183/F1 | L260 | L261 | L259 102.42/39.66 r_next=0.688 MAD_above=12.61 lag=0(12.61/12.61); L260 87.65/40.05 r_next=0.055 MAD_above=21.52 lag=-1(20.55/21.52); L261 76.24/53.38 r_next=0.890 MAD_above=52.61 lag=-32(49.47/52.61); L262 74.95/58.17 r_next=0.025 MAD_above=18.21 lag=0(18.21/18.21); direct-full=L261 (L261 persistent three-third step; thirds=6.718,3.274,4.496; correlation above/next=-0.019/0.928; middle coherence=0.923) |
| 186 | 187/F1 | L260 | L261 | L259 103.21/39.36 r_next=0.622 MAD_above=13.28 lag=0(13.28/13.28); L260 87.64/40.91 r_next=0.027 MAD_above=24.34 lag=-2(22.49/24.34); L261 75.48/55.85 r_next=0.867 MAD_above=55.90 lag=-18(53.75/55.90); L262 72.00/54.22 r_next=-0.026 MAD_above=19.12 lag=-1(18.88/19.12); direct-full=L261 (L261 persistent three-third step; thirds=6.877,3.373,4.754; correlation above/next=-0.053/0.908; middle coherence=0.923) |
| 192 | 193/F1 | L260 | L261 | L259 101.44/38.60 r_next=0.758 MAD_above=12.99 lag=0(12.99/12.99); L260 90.57/39.66 r_next=0.133 MAD_above=18.67 lag=-1(17.73/18.67); L261 74.40/55.89 r_next=0.902 MAD_above=51.56 lag=-15(50.78/51.56); L262 71.14/52.30 r_next=0.013 MAD_above=15.72 lag=0(15.72/15.72); direct-full=L261 (L261 persistent three-third step; thirds=6.697,3.934,3.457; correlation above/next=0.059/0.927; middle coherence=0.916) |
| 193 | 194/F1 | L260 | L261 | L259 99.92/39.02 r_next=0.785 MAD_above=13.04 lag=0(13.04/13.04); L260 90.17/38.86 r_next=0.148 MAD_above=18.16 lag=-1(17.37/18.16); L261 75.89/53.45 r_next=0.899 MAD_above=49.24 lag=-8(48.10/49.24); L262 70.37/55.34 r_next=0.039 MAD_above=15.69 lag=1(15.60/15.69); direct-full=L261 (L261 persistent three-third step; thirds=6.477,3.531,3.467; correlation above/next=0.095/0.927; middle coherence=0.926) |
| 201 | 202/F1 | L260 | L261 | L259 95.42/39.01 r_next=0.672 MAD_above=12.60 lag=1(12.56/12.60); L260 81.43/38.29 r_next=0.120 MAD_above=21.81 lag=-2(20.45/21.81); L261 70.59/51.85 r_next=0.916 MAD_above=49.36 lag=-5(47.89/49.36); L262 66.97/51.97 r_next=0.041 MAD_above=13.35 lag=0(13.35/13.35); direct-full=L261 (L261 persistent three-third step; thirds=6.315,3.307,3.772; correlation above/next=0.055/0.948; middle coherence=0.913) |
| 209 | 210/F1 | L260 | L261 | L259 93.07/38.53 r_next=0.640 MAD_above=12.50 lag=1(12.28/12.50); L260 83.27/37.94 r_next=0.176 MAD_above=22.79 lag=-2(20.12/22.79); L261 71.64/51.82 r_next=0.910 MAD_above=47.58 lag=0(47.58/47.58); L262 66.71/51.16 r_next=0.045 MAD_above=14.14 lag=0(14.14/14.14); direct-full=L261 (L261 persistent three-third step; thirds=5.973,3.387,3.759; correlation above/next=0.116/0.939; middle coherence=0.928) |
| 210 | 211/F1 | L260 | L261 | L259 93.60/39.22 r_next=0.623 MAD_above=13.12 lag=0(13.12/13.12); L260 86.69/39.58 r_next=0.116 MAD_above=21.54 lag=-1(20.43/21.54); L261 69.47/51.89 r_next=0.893 MAD_above=50.83 lag=-1(50.71/50.83); L262 68.38/53.59 r_next=-0.001 MAD_above=15.40 lag=0(15.40/15.40); direct-full=L261 (L261 persistent three-third step; thirds=6.134,3.239,4.455; correlation above/next=0.055/0.930; middle coherence=0.919) |
| 220 | 221/F1 | L260 | L261 | L259 83.18/35.94 r_next=0.910 MAD_above=8.33 lag=0(8.33/8.33); L260 81.79/35.54 r_next=-0.237 MAD_above=10.47 lag=-3(8.18/10.47); L261 58.07/44.38 r_next=0.945 MAD_above=56.83 lag=-32(54.26/56.83); L262 58.79/45.15 r_next=0.016 MAD_above=10.29 lag=2(8.98/10.29); direct-full=L261 (L261 persistent three-third step; thirds=10.675,3.248,5.151; correlation above/next=-0.326/0.970; middle coherence=0.887) |
| 221 | 222/F1 | L260 | L261 | L259 83.64/34.90 r_next=0.942 MAD_above=8.93 lag=0(8.93/8.93); L260 81.96/35.47 r_next=-0.259 MAD_above=8.70 lag=-1(7.97/8.70); L261 59.94/44.80 r_next=0.941 MAD_above=56.68 lag=-32(54.95/56.68); L262 57.37/44.83 r_next=0.028 MAD_above=10.18 lag=3(9.17/10.18); direct-full=L261 (L261 persistent three-third step; thirds=11.523,3.348,4.904; correlation above/next=-0.355/0.967; middle coherence=0.880) |
| 222 | 223/F1 | L259 | L261 | L258 84.30/35.67 r_next=0.950 MAD_above=8.08 lag=0(8.08/8.08); L259 83.03/35.70 r_next=0.849 MAD_above=8.52 lag=0(8.52/8.52); L260 80.66/34.55 r_next=-0.247 MAD_above=13.32 lag=5(8.29/13.32); L261 60.82/47.16 r_next=0.899 MAD_above=56.75 lag=-32(54.71/56.75); L262 58.05/45.04 r_next=0.028 MAD_above=12.36 lag=-5(10.08/12.36); direct-full=L261 (L261 persistent three-third step; thirds=10.747,3.806,4.769; correlation above/next=-0.271/0.936; middle coherence=0.884) |
| 227 | 228/F1 | L260 | L261 | L259 83.47/35.64 r_next=0.811 MAD_above=8.10 lag=0(8.10/8.10); L260 80.13/35.57 r_next=-0.303 MAD_above=15.00 lag=7(9.24/15.00); L261 59.02/45.76 r_next=0.897 MAD_above=57.25 lag=-30(55.19/57.25); L262 54.75/44.98 r_next=0.016 MAD_above=12.79 lag=-6(9.41/12.79); direct-full=L261 (L261 persistent three-third step; thirds=10.989,3.709,5.272; correlation above/next=-0.333/0.936; middle coherence=0.880) |
| 245 | 246/F1 | L261 | L262 | L260 83.00/36.07 r_next=0.060 MAD_above=9.20 lag=0(9.20/9.20); L261 79.51/30.89 r_next=0.310 MAD_above=32.24 lag=1(32.09/32.24); L262 64.03/48.55 r_next=0.016 MAD_above=34.48 lag=0(34.48/34.48); direct-full=L262 (L262 internal blank x=79-142 Y=1.391; above=115.906 following=70.000; gate=4.000) |
| 250 | 251/F1 | L260 | L261 | L259 83.75/36.94 r_next=0.932 MAD_above=9.05 lag=0(9.05/9.05); L260 86.19/35.84 r_next=-0.255 MAD_above=10.03 lag=-2(8.75/10.03); L261 60.82/47.19 r_next=0.943 MAD_above=60.71 lag=-32(58.70/60.71); L262 63.34/47.86 r_next=0.021 MAD_above=11.20 lag=2(9.98/11.20); direct-full=L261 (L261 persistent three-third step; thirds=11.040,3.435,5.566; correlation above/next=-0.341/0.970; middle coherence=0.884) |
| 256 | 257/F1 | L260 | L261 | L259 85.11/37.46 r_next=0.560 MAD_above=8.36 lag=0(8.36/8.36); L260 75.87/29.83 r_next=-0.245 MAD_above=19.54 lag=-1(19.28/19.54); L261 66.08/48.67 r_next=0.960 MAD_above=50.22 lag=-32(49.22/50.22); L262 65.98/49.22 r_next=0.048 MAD_above=9.62 lag=0(9.62/9.62); direct-full=L261 (L261 internal blank x=94-157 Y=1.344; above=115.938 following=73.000; gate=4.000) |
| 262 | 263/F1 | L260 | L261 | L259 88.83/37.02 r_next=0.556 MAD_above=9.20 lag=0(9.20/9.20); L260 74.32/31.86 r_next=-0.115 MAD_above=21.87 lag=0(21.87/21.87); L261 67.15/50.31 r_next=0.960 MAD_above=48.72 lag=-18(48.47/48.72); L262 66.46/50.38 r_next=0.051 MAD_above=9.94 lag=0(9.94/9.94); direct-full=L261 (L261 internal blank x=120-183 Y=1.328; above=103.375 following=74.500; gate=4.000) |
| 282 | 283/F1 | L260 | L261 | L259 93.57/36.72 r_next=0.722 MAD_above=8.96 lag=0(8.96/8.96); L260 84.58/34.07 r_next=-0.221 MAD_above=16.04 lag=-2(13.83/16.04); L261 67.66/50.33 r_next=0.959 MAD_above=55.34 lag=-28(52.90/55.34); L262 70.20/51.09 r_next=0.049 MAD_above=10.59 lag=-1(9.98/10.59); direct-full=L261 (L261 persistent three-third step; thirds=10.499,3.659,3.515; correlation above/next=-0.331/0.981; middle coherence=0.880) |
| 293 | 294/F1 | L260 | L261 | L259 93.52/36.43 r_next=0.638 MAD_above=10.28 lag=-1(10.12/10.28); L260 90.80/38.15 r_next=-0.154 MAD_above=17.23 lag=-3(14.12/17.23); L261 70.67/49.93 r_next=0.942 MAD_above=56.83 lag=-27(56.08/56.83); L262 70.67/50.44 r_next=0.030 MAD_above=11.09 lag=-1(10.87/11.09); direct-full=L261 (L261 persistent three-third step; thirds=13.964,3.442,5.094; correlation above/next=-0.198/0.963; middle coherence=0.900) |
| 297 | 298/F1 | L260 | L261 | L259 99.56/38.66 r_next=0.741 MAD_above=8.31 lag=0(8.31/8.31); L260 90.39/36.53 r_next=-0.229 MAD_above=14.24 lag=-1(13.86/14.24); L261 70.80/52.17 r_next=0.967 MAD_above=59.89 lag=-28(58.30/59.89); L262 73.97/52.92 r_next=0.050 MAD_above=10.18 lag=0(10.18/10.18); direct-full=L261 (L261 persistent three-third step; thirds=14.360,4.406,4.579; correlation above/next=-0.306/0.983; middle coherence=0.899) |
| 298 | 299/F1 | L260 | L261 | L259 96.76/37.68 r_next=0.750 MAD_above=9.01 lag=-1(8.88/9.01); L260 90.88/35.00 r_next=-0.222 MAD_above=13.12 lag=-1(12.39/13.12); L261 70.06/52.26 r_next=0.967 MAD_above=59.71 lag=-29(56.71/59.71); L262 71.02/52.02 r_next=-0.015 MAD_above=9.70 lag=0(9.70/9.70); direct-full=L261 (L261 persistent three-third step; thirds=14.225,4.299,4.710; correlation above/next=-0.309/0.984; middle coherence=0.902) |
| 305 | 306/F1 | L259 | L261 | L258 113.79/46.75 r_next=0.951 MAD_above=8.52 lag=0(8.52/8.52); L259 115.66/45.72 r_next=0.443 MAD_above=9.78 lag=0(9.78/9.78); L260 90.31/46.79 r_next=0.233 MAD_above=31.13 lag=-1(30.80/31.13); L261 69.47/54.38 r_next=0.890 MAD_above=51.70 lag=-7(50.35/51.70); L262 71.29/56.73 r_next=-0.001 MAD_above=16.36 lag=0(16.36/16.36); direct-full=L261 (L261 persistent three-third step; thirds=10.137,2.985,5.704; correlation above/next=0.263/0.904; middle coherence=0.973) |
| 306 | 307/F1 | L259 | L261 | L258 113.24/46.62 r_next=0.962 MAD_above=7.59 lag=0(7.59/7.59); L259 112.34/47.40 r_next=0.489 MAD_above=8.15 lag=0(8.15/8.15); L260 93.30/42.50 r_next=0.256 MAD_above=27.16 lag=-1(26.52/27.16); L261 65.95/54.51 r_next=0.833 MAD_above=52.23 lag=-2(51.77/52.23); L262 74.39/57.21 r_next=-0.006 MAD_above=19.80 lag=0(19.80/19.80); direct-full=L261 (L261 persistent three-third step; thirds=11.186,3.664,4.700; correlation above/next=0.252/0.831; middle coherence=0.974) |
| 311 | 312/F1 | L260 | L261 | L259 108.48/50.26 r_next=0.636 MAD_above=14.12 lag=0(14.12/14.12); L260 91.60/43.28 r_next=0.199 MAD_above=23.68 lag=0(23.68/23.68); L261 68.19/53.39 r_next=0.925 MAD_above=52.58 lag=-9(51.87/52.58); L262 72.21/56.37 r_next=0.012 MAD_above=14.72 lag=0(14.72/14.72); direct-full=L261 (L261 persistent three-third step; thirds=9.680,2.947,6.045; correlation above/next=0.236/0.944; middle coherence=0.980) |
| 316 | 317/F1 | L260 | L261 | L259 114.25/46.11 r_next=0.364 MAD_above=9.05 lag=1(8.94/9.05); L260 89.40/44.67 r_next=0.020 MAD_above=31.27 lag=-2(30.04/31.27); L261 70.47/54.74 r_next=0.888 MAD_above=59.43 lag=-12(56.68/59.43); L262 72.11/56.98 r_next=-0.022 MAD_above=17.65 lag=-1(17.32/17.65); direct-full=L261 (L261 persistent three-third step; thirds=12.704,3.904,4.794; correlation above/next=0.044/0.910; middle coherence=0.976) |
| 317 | 318/F1 | L260 | L261 | L259 115.11/45.46 r_next=0.372 MAD_above=8.47 lag=0(8.47/8.47); L260 90.00/43.02 r_next=0.035 MAD_above=31.27 lag=-2(30.09/31.27); L261 67.95/54.15 r_next=0.897 MAD_above=57.85 lag=-9(57.26/57.85); L262 71.08/56.84 r_next=-0.013 MAD_above=15.72 lag=0(15.72/15.72); direct-full=L261 (L261 persistent three-third step; thirds=12.741,3.900,4.471; correlation above/next=0.047/0.908; middle coherence=0.972) |
| 321 | 322/F1 | L260 | L261 | L259 115.24/45.78 r_next=0.656 MAD_above=7.79 lag=0(7.79/7.79); L260 102.36/41.73 r_next=-0.141 MAD_above=17.71 lag=0(17.71/17.71); L261 72.50/56.94 r_next=0.882 MAD_above=69.21 lag=-8(68.71/69.21); L262 70.62/55.68 r_next=-0.013 MAD_above=16.61 lag=0(16.61/16.61); direct-full=L261 (L261 persistent three-third step; thirds=14.338,4.516,5.908; correlation above/next=-0.146/0.906; middle coherence=0.972) |
| 322 | 323/F1 | L260 | L261 | L259 114.21/45.95 r_next=0.631 MAD_above=8.10 lag=0(8.10/8.10); L260 101.48/43.78 r_next=-0.184 MAD_above=21.29 lag=-2(19.12/21.29); L261 70.47/57.71 r_next=0.878 MAD_above=71.87 lag=-30(70.63/71.87); L262 73.40/54.96 r_next=0.033 MAD_above=17.50 lag=-1(17.23/17.50); direct-full=L261 (L261 persistent three-third step; thirds=14.782,4.642,6.444; correlation above/next=-0.178/0.902; middle coherence=0.972) |
| 324 | 325/F1 | L259 | L261 | L258 115.61/46.52 r_next=0.972 MAD_above=8.51 lag=0(8.51/8.51); L259 115.88/46.31 r_next=0.647 MAD_above=7.89 lag=0(7.89/7.89); L260 103.92/43.27 r_next=-0.108 MAD_above=19.81 lag=-2(18.37/19.81); L261 70.04/56.02 r_next=0.869 MAD_above=67.65 lag=-4(66.18/67.65); L262 74.79/57.12 r_next=-0.006 MAD_above=18.35 lag=-1(18.25/18.35); direct-full=L261 (L261 persistent three-third step; thirds=14.056,3.542,6.257; correlation above/next=-0.105/0.880; middle coherence=0.970) |
| 332 | 333/F1 | L260 | L261 | L259 116.03/46.16 r_next=0.675 MAD_above=7.74 lag=1(7.69/7.74); L260 105.22/45.86 r_next=-0.161 MAD_above=18.50 lag=-1(17.41/18.50); L261 69.74/58.76 r_next=0.873 MAD_above=72.65 lag=32(71.34/72.65); L262 70.56/55.91 r_next=-0.015 MAD_above=17.44 lag=-1(17.16/17.44); direct-full=L261 (L261 persistent three-third step; thirds=13.219,4.256,7.366; correlation above/next=-0.147/0.907; middle coherence=0.971) |
| 334 | 335/F1 | L260 | L261 | L259 115.80/45.44 r_next=0.459 MAD_above=9.02 lag=1(8.57/9.02); L260 97.10/44.72 r_next=-0.066 MAD_above=26.26 lag=-1(25.99/26.26); L261 72.01/57.45 r_next=0.884 MAD_above=64.51 lag=-6(64.04/64.51); L262 68.35/54.42 r_next=-0.017 MAD_above=15.64 lag=1(15.45/15.64); direct-full=L261 (L261 persistent three-third step; thirds=13.257,3.488,5.286; correlation above/next=-0.054/0.923; middle coherence=0.970) |
| 339 | 340/F1 | L260 | L261 | L259 114.31/47.54 r_next=0.787 MAD_above=7.54 lag=0(7.54/7.54); L260 107.62/43.09 r_next=0.086 MAD_above=15.31 lag=-1(14.57/15.31); L261 71.69/57.89 r_next=0.769 MAD_above=65.84 lag=-1(65.57/65.84); L262 73.24/57.86 r_next=-0.047 MAD_above=24.17 lag=0(24.17/24.17); direct-full=L261 (L261 persistent three-third step; thirds=12.306,4.156,6.133; correlation above/next=0.002/0.750; middle coherence=0.970) |
| 340 | 341/F1 | L260 | L261 | L259 100.85/47.90 r_next=0.757 MAD_above=18.08 lag=1(17.71/18.08); L260 102.98/50.28 r_next=-0.126 MAD_above=22.39 lag=-1(21.64/22.39); L261 86.80/59.76 r_next=0.875 MAD_above=69.22 lag=-18(66.28/69.22); L262 85.80/61.50 r_next=0.032 MAD_above=18.96 lag=0(18.96/18.96); direct-full=L261 (L261 persistent three-third step; thirds=9.429,3.360,3.937; correlation above/next=-0.208/0.907; middle coherence=0.915) |
| 341 | 342/F1 | L260 | L261 | L259 100.64/48.28 r_next=0.783 MAD_above=18.29 lag=0(18.29/18.29); L260 99.03/48.18 r_next=-0.144 MAD_above=21.96 lag=-3(19.21/21.96); L261 86.29/59.72 r_next=0.862 MAD_above=68.57 lag=-19(66.39/68.57); L262 86.40/62.32 r_next=0.014 MAD_above=20.38 lag=-1(19.63/20.38); direct-full=L261 (L261 persistent three-third step; thirds=9.152,3.103,4.061; correlation above/next=-0.242/0.887; middle coherence=0.913) |
| 342 | 343/F1 | L260 | L261 | L259 99.72/47.30 r_next=0.769 MAD_above=16.66 lag=1(16.37/16.66); L260 102.86/49.71 r_next=-0.140 MAD_above=21.03 lag=-2(19.67/21.03); L261 86.19/59.48 r_next=0.889 MAD_above=69.41 lag=-28(65.94/69.41); L262 85.15/60.71 r_next=0.026 MAD_above=18.08 lag=0(18.08/18.08); direct-full=L261 (L261 persistent three-third step; thirds=9.804,3.178,4.032; correlation above/next=-0.221/0.915; middle coherence=0.914) |
| 344 | 345/F1 | L260 | L261 | L259 100.03/47.57 r_next=0.833 MAD_above=17.60 lag=0(17.60/17.60); L260 101.43/48.24 r_next=-0.125 MAD_above=18.88 lag=-1(17.93/18.88); L261 86.76/60.88 r_next=0.874 MAD_above=69.01 lag=-19(65.32/69.01); L262 87.03/61.74 r_next=0.039 MAD_above=19.31 lag=1(19.16/19.31); direct-full=L261 (L261 persistent three-third step; thirds=9.389,3.420,3.821; correlation above/next=-0.212/0.906; middle coherence=0.917) |
| 345 | 346/F1 | L260 | L261 | L259 101.46/46.35 r_next=0.748 MAD_above=16.59 lag=0(16.59/16.59); L260 99.56/49.37 r_next=-0.095 MAD_above=23.32 lag=-3(19.77/23.32); L261 84.33/58.97 r_next=0.890 MAD_above=67.24 lag=-18(64.50/67.24); L262 87.08/61.33 r_next=-0.002 MAD_above=17.81 lag=0(17.81/17.81); direct-full=L261 (L261 persistent three-third step; thirds=9.142,3.213,3.535; correlation above/next=-0.175/0.915; middle coherence=0.909) |
| 347 | 348/F1 | L259 | L261 | L258 98.35/47.93 r_next=0.841 MAD_above=15.11 lag=0(15.11/15.11); L259 102.62/46.69 r_next=0.719 MAD_above=17.50 lag=0(17.50/17.50); L260 100.53/50.50 r_next=-0.125 MAD_above=24.56 lag=-3(21.64/24.56); L261 85.67/58.12 r_next=0.878 MAD_above=68.71 lag=-19(64.60/68.71); L262 85.74/62.42 r_next=0.000 MAD_above=18.53 lag=-1(17.77/18.53); direct-full=L261 (L261 persistent three-third step; thirds=9.325,3.108,4.047; correlation above/next=-0.198/0.907; middle coherence=0.916) |
| 348 | 349/F1 | L260 | L261 | L259 101.00/46.95 r_next=0.841 MAD_above=17.73 lag=0(17.73/17.73); L260 95.78/50.86 r_next=-0.176 MAD_above=19.49 lag=-2(17.54/19.49); L261 85.39/59.45 r_next=0.864 MAD_above=70.46 lag=-21(67.76/70.46); L262 84.30/60.20 r_next=-0.006 MAD_above=18.43 lag=0(18.43/18.43); direct-full=L261 (L261 persistent three-third step; thirds=9.394,3.330,3.935; correlation above/next=-0.252/0.896; middle coherence=0.918) |
| 349 | 350/F1 | L259 | L261 | L258 99.00/47.97 r_next=0.842 MAD_above=16.09 lag=0(16.09/16.09); L259 100.86/46.62 r_next=0.730 MAD_above=17.60 lag=0(17.60/17.60); L260 97.00/51.68 r_next=-0.137 MAD_above=22.16 lag=-2(19.99/22.16); L261 84.81/58.34 r_next=0.871 MAD_above=70.01 lag=-17(66.45/70.01); L262 85.43/61.93 r_next=-0.040 MAD_above=19.32 lag=-2(18.10/19.32); direct-full=L261 (L261 persistent three-third step; thirds=9.728,3.259,4.507; correlation above/next=-0.217/0.903; middle coherence=0.921) |
| 350 | 351/F1 | L260 | L261 | L259 100.74/47.73 r_next=0.850 MAD_above=16.93 lag=0(16.93/16.93); L260 94.46/49.44 r_next=-0.147 MAD_above=17.08 lag=-1(16.96/17.08); L261 86.30/58.86 r_next=0.885 MAD_above=68.97 lag=-17(66.03/68.97); L262 84.09/61.36 r_next=-0.039 MAD_above=19.37 lag=0(19.37/19.37); direct-full=L261 (L261 persistent three-third step; thirds=9.321,3.143,4.110; correlation above/next=-0.236/0.918; middle coherence=0.916) |
| 351 | 352/F1 | L260 | L261 | L259 100.57/47.06 r_next=0.712 MAD_above=16.66 lag=0(16.66/16.66); L260 96.66/49.74 r_next=-0.126 MAD_above=24.66 lag=-3(21.96/24.66); L261 85.24/58.56 r_next=0.870 MAD_above=67.47 lag=-20(63.86/67.47); L262 84.65/60.84 r_next=0.016 MAD_above=19.39 lag=-2(17.46/19.39); direct-full=L261 (L261 persistent three-third step; thirds=9.257,3.092,3.848; correlation above/next=-0.205/0.904; middle coherence=0.914) |
| 357 | 358/F1 | L260 | L261 | L259 103.72/47.07 r_next=0.726 MAD_above=16.85 lag=1(16.72/16.85); L260 101.93/51.02 r_next=-0.142 MAD_above=24.43 lag=-3(21.08/24.43); L261 85.77/59.31 r_next=0.846 MAD_above=70.76 lag=-20(66.65/70.76); L262 85.49/61.57 r_next=0.030 MAD_above=21.64 lag=-1(21.01/21.64); direct-full=L261 (L261 persistent three-third step; thirds=9.476,3.252,4.194; correlation above/next=-0.231/0.892; middle coherence=0.915) |
| 361 | 362/F1 | L259 | L261 | L258 98.43/47.33 r_next=0.833 MAD_above=14.15 lag=0(14.15/14.15); L259 101.65/46.83 r_next=0.722 MAD_above=16.87 lag=0(16.87/16.87); L260 101.52/48.37 r_next=-0.104 MAD_above=25.30 lag=-3(22.49/25.30); L261 84.43/59.86 r_next=0.868 MAD_above=66.75 lag=-18(62.69/66.75); L262 85.19/61.05 r_next=0.006 MAD_above=19.93 lag=-1(19.46/19.93); direct-full=L261 (L261 persistent three-third step; thirds=9.591,3.236,3.510; correlation above/next=-0.170/0.903; middle coherence=0.914) |
| 362 | 363/F1 | L260 | L261 | L259 97.32/47.32 r_next=0.706 MAD_above=16.99 lag=0(16.99/16.99); L260 100.07/49.48 r_next=-0.134 MAD_above=24.79 lag=-3(22.32/24.79); L261 84.38/58.73 r_next=0.872 MAD_above=68.16 lag=-20(64.66/68.16); L262 84.36/60.54 r_next=-0.018 MAD_above=19.39 lag=-1(18.42/19.39); direct-full=L261 (L261 persistent three-third step; thirds=9.255,3.046,4.053; correlation above/next=-0.205/0.908; middle coherence=0.913) |
| 363 | 364/F1 | L260 | L261 | L259 99.30/47.38 r_next=0.686 MAD_above=15.89 lag=0(15.89/15.89); L260 100.71/51.53 r_next=-0.066 MAD_above=24.30 lag=-2(23.24/24.30); L261 82.53/57.34 r_next=0.882 MAD_above=67.77 lag=-19(64.60/67.77); L262 85.85/59.57 r_next=0.005 MAD_above=19.27 lag=0(19.27/19.27); direct-full=L261 (L261 persistent three-third step; thirds=9.166,2.924,4.144; correlation above/next=-0.158/0.915; middle coherence=0.916) |
| 365 | 366/F1 | L260 | L261 | L259 103.94/46.21 r_next=0.837 MAD_above=17.33 lag=1(17.30/17.33); L260 98.91/49.52 r_next=-0.115 MAD_above=18.95 lag=-2(17.23/18.95); L261 87.07/58.17 r_next=0.877 MAD_above=66.54 lag=-20(63.79/66.54); L262 83.53/61.13 r_next=-0.025 MAD_above=19.82 lag=0(19.82/19.82); direct-full=L261 (L261 persistent three-third step; thirds=8.918,2.503,3.950; correlation above/next=-0.198/0.908; middle coherence=0.911) |
| 370 | 371/F1 | L260 | L261 | L259 99.33/46.52 r_next=0.745 MAD_above=18.00 lag=0(18.00/18.00); L260 98.27/49.86 r_next=0.012 MAD_above=23.75 lag=-2(21.59/23.75); L261 78.68/60.77 r_next=0.772 MAD_above=62.63 lag=-2(60.40/62.63); L262 84.54/60.73 r_next=-0.011 MAD_above=27.78 lag=-1(27.22/27.78); direct-full=L261 (L261 internal blank x=89-152 Y=1.375; above=112.828 following=118.500; gate=4.000) |
| 372 | 373/F1 | L261 | L262 | L260 97.98/49.53 r_next=0.402 MAD_above=22.29 lag=-2(20.90/22.29); L261 99.74/51.00 r_next=0.316 MAD_above=37.99 lag=-2(35.50/37.99); L262 83.77/60.18 r_next=-0.012 MAD_above=51.12 lag=-2(50.50/51.12); direct-full=L262 (L262 internal blank x=76-139 Y=1.391; above=109.719 following=113.000; gate=4.000) |
| 373 | 374/F1 | L260 | L261 | L259 102.78/47.42 r_next=0.631 MAD_above=17.01 lag=0(17.01/17.01); L260 105.72/52.26 r_next=-0.031 MAD_above=27.62 lag=-3(24.23/27.62); L261 83.62/58.89 r_next=0.855 MAD_above=67.30 lag=-19(65.80/67.30); L262 84.30/62.55 r_next=0.045 MAD_above=21.90 lag=-2(20.61/21.90); direct-full=L261 (L261 persistent three-third step; thirds=9.560,2.684,3.727; correlation above/next=-0.101/0.890; middle coherence=0.917) |
| 374 | 375/F1 | L260 | L262 | L259 99.28/46.91 r_next=0.775 MAD_above=18.30 lag=0(18.30/18.30); L260 96.07/50.18 r_next=0.175 MAD_above=23.11 lag=-3(20.83/23.11); L261 106.82/47.81 r_next=0.489 MAD_above=48.35 lag=-2(46.05/48.35); L262 82.57/61.37 r_next=0.001 MAD_above=43.48 lag=-2(42.75/43.48); direct-full=L262 (L262 internal blank x=107-170 Y=1.359; above=114.922 following=111.000; gate=4.000) |
| 377 | 378/F1 | L260 | L261 | L259 99.36/47.33 r_next=0.710 MAD_above=18.25 lag=1(17.76/18.25); L260 102.19/50.90 r_next=-0.100 MAD_above=23.34 lag=-1(22.43/23.34); L261 84.72/60.22 r_next=0.850 MAD_above=69.97 lag=-19(67.72/69.97); L262 83.87/60.59 r_next=0.024 MAD_above=22.00 lag=0(22.00/22.00); direct-full=L261 (L261 persistent three-third step; thirds=9.362,3.044,4.061; correlation above/next=-0.170/0.896; middle coherence=0.917) |
| 382 | 383/F1 | L260 | L261 | L259 103.05/48.20 r_next=0.824 MAD_above=16.16 lag=0(16.16/16.16); L260 97.50/49.68 r_next=-0.167 MAD_above=20.11 lag=-2(17.86/20.11); L261 86.07/60.39 r_next=0.852 MAD_above=70.18 lag=-20(67.10/70.18); L262 86.89/63.91 r_next=0.026 MAD_above=21.93 lag=0(21.93/21.93); direct-full=L261 (L261 persistent three-third step; thirds=9.485,3.607,3.950; correlation above/next=-0.243/0.889; middle coherence=0.919) |
| 383 | 384/F1 | L259 | L261 | L258 99.56/48.06 r_next=0.837 MAD_above=16.27 lag=0(16.27/16.27); L259 102.11/46.56 r_next=0.817 MAD_above=17.14 lag=0(17.14/17.14); L260 95.47/48.74 r_next=-0.146 MAD_above=20.02 lag=-3(17.17/20.02); L261 87.30/61.34 r_next=0.881 MAD_above=69.95 lag=-22(67.41/69.95); L262 87.19/62.97 r_next=0.003 MAD_above=15.61 lag=0(15.61/15.61); direct-full=L261 (L261 persistent three-third step; thirds=9.114,3.239,4.475; correlation above/next=-0.208/0.903; middle coherence=0.915) |
| 385 | 386/F1 | L260 | L261 | L259 102.20/47.30 r_next=0.898 MAD_above=17.04 lag=0(17.04/17.04); L260 97.65/45.36 r_next=-0.025 MAD_above=14.77 lag=-1(14.23/14.77); L261 90.06/55.64 r_next=0.790 MAD_above=53.94 lag=0(53.94/53.94); L262 88.01/60.81 r_next=-0.021 MAD_above=26.10 lag=-1(25.83/26.10); direct-full=L261 (L261 internal blank x=112-175 Y=1.391; above=119.547 following=120.000; gate=4.000) |
| 386 | 387/F1 | L261 | L262 | L260 99.08/47.27 r_next=0.947 MAD_above=16.87 lag=-1(16.77/16.87); L261 95.91/47.90 r_next=0.199 MAD_above=10.36 lag=-2(4.34/10.36); L262 65.56/56.93 r_next=0.015 MAD_above=50.46 lag=-2(48.55/50.46); direct-full=L262 (L262 internal blank x=92-155 Y=1.359; above=110.578 following=73.000; gate=4.000) |
| 400 | 401/F1 | L261 | L262 | L260 98.75/47.03 r_next=0.113 MAD_above=16.77 lag=-2(15.50/16.77); L261 110.69/45.26 r_next=0.459 MAD_above=46.30 lag=-2(45.20/46.30); L262 82.81/60.82 r_next=0.021 MAD_above=44.09 lag=-1(44.05/44.09); direct-full=L262 (L262 internal blank x=102-165 Y=1.344; above=115.734 following=115.000; gate=4.000) |
| 401 | 402/F1 | L260 | L261 | L259 99.87/47.31 r_next=0.885 MAD_above=17.11 lag=0(17.11/17.11); L260 97.79/47.52 r_next=-0.223 MAD_above=15.80 lag=-2(13.89/15.80); L261 85.77/60.94 r_next=0.861 MAD_above=71.76 lag=-32(66.42/71.76); L262 85.14/61.02 r_next=-0.011 MAD_above=18.75 lag=0(18.75/18.75); direct-full=L261 (L261 persistent three-third step; thirds=9.412,3.165,4.416; correlation above/next=-0.279/0.889; middle coherence=0.913) |
| 402 | 403/F1 | L260 | L261 | L259 100.19/46.33 r_next=0.891 MAD_above=16.79 lag=0(16.79/16.79); L260 99.10/46.85 r_next=-0.252 MAD_above=15.18 lag=-2(13.90/15.18); L261 82.11/59.02 r_next=0.824 MAD_above=71.19 lag=30(66.90/71.19); L262 81.63/60.84 r_next=0.015 MAD_above=23.29 lag=3(21.24/23.29); direct-full=L261 (L261 persistent three-third step; thirds=9.468,3.323,4.135; correlation above/next=-0.302/0.874; middle coherence=0.914) |
| 403 | 404/F1 | L260 | L261 | L259 100.47/46.10 r_next=0.842 MAD_above=17.54 lag=0(17.54/17.54); L260 95.55/46.00 r_next=-0.301 MAD_above=17.51 lag=-4(13.45/17.51); L261 84.05/59.36 r_next=0.849 MAD_above=71.80 lag=32(64.70/71.80); L262 82.15/61.05 r_next=-0.009 MAD_above=21.91 lag=2(19.83/21.91); direct-full=L261 (L261 persistent three-third step; thirds=9.339,3.514,4.300; correlation above/next=-0.345/0.892; middle coherence=0.912) |
| 404 | 405/F1 | L259 | L261 | L258 97.36/47.96 r_next=0.849 MAD_above=14.58 lag=0(14.58/14.58); L259 100.08/45.51 r_next=0.837 MAD_above=16.45 lag=0(16.45/16.45); L260 97.96/47.38 r_next=-0.295 MAD_above=18.76 lag=-4(13.52/18.76); L261 84.92/57.13 r_next=0.868 MAD_above=70.78 lag=32(63.87/70.78); L262 82.33/59.52 r_next=-0.001 MAD_above=19.45 lag=2(17.34/19.45); direct-full=L261 (L261 persistent three-third step; thirds=9.639,3.092,4.088; correlation above/next=-0.332/0.908; middle coherence=0.915) |
| 406 | 407/F1 | L260 | L261 | L259 99.81/47.07 r_next=0.806 MAD_above=16.91 lag=0(16.91/16.91); L260 98.08/47.05 r_next=-0.288 MAD_above=20.07 lag=-4(15.40/20.07); L261 84.55/59.45 r_next=0.842 MAD_above=72.74 lag=31(66.18/72.74); L262 83.39/59.33 r_next=-0.012 MAD_above=21.87 lag=2(19.60/21.87); direct-full=L261 (L261 persistent three-third step; thirds=9.789,3.574,4.339; correlation above/next=-0.339/0.887; middle coherence=0.917) |
| 408 | 409/F1 | L260 | L261 | L259 99.12/46.35 r_next=0.884 MAD_above=17.60 lag=-1(17.57/17.60); L260 96.86/47.48 r_next=-0.277 MAD_above=15.46 lag=-2(14.39/15.46); L261 83.06/59.04 r_next=0.848 MAD_above=71.91 lag=30(65.50/71.91); L262 83.76/60.31 r_next=0.011 MAD_above=20.59 lag=3(18.16/20.59); direct-full=L261 (L261 persistent three-third step; thirds=9.329,3.560,4.236; correlation above/next=-0.313/0.896; middle coherence=0.911) |
| 409 | 410/F1 | L260 | L261 | L259 100.82/46.64 r_next=0.825 MAD_above=17.74 lag=0(17.74/17.74); L260 95.67/46.66 r_next=-0.291 MAD_above=18.57 lag=-4(13.42/18.57); L261 84.20/58.93 r_next=0.871 MAD_above=71.00 lag=31(64.34/71.00); L262 81.56/59.93 r_next=0.038 MAD_above=19.00 lag=2(16.93/19.00); direct-full=L261 (L261 persistent three-third step; thirds=9.531,3.285,4.393; correlation above/next=-0.329/0.909; middle coherence=0.918) |
| 410 | 411/F1 | L260 | L261 | L259 102.12/46.31 r_next=0.870 MAD_above=18.11 lag=0(18.11/18.11); L260 96.71/46.39 r_next=-0.255 MAD_above=15.88 lag=-2(13.59/15.88); L261 81.69/56.65 r_next=0.875 MAD_above=68.45 lag=30(63.04/68.45); L262 81.81/60.00 r_next=0.019 MAD_above=19.22 lag=2(16.95/19.22); direct-full=L261 (L261 persistent three-third step; thirds=9.246,2.892,4.144; correlation above/next=-0.287/0.914; middle coherence=0.916) |
| 411 | 412/F1 | L260 | L261 | L259 102.22/47.79 r_next=0.876 MAD_above=17.26 lag=1(17.15/17.26); L260 95.95/45.44 r_next=-0.266 MAD_above=16.60 lag=-2(14.54/16.60); L261 80.96/57.39 r_next=0.893 MAD_above=69.47 lag=29(63.27/69.47); L262 83.45/60.31 r_next=0.059 MAD_above=16.55 lag=0(16.55/16.55); direct-full=L261 (L261 persistent three-third step; thirds=9.019,3.250,4.065; correlation above/next=-0.301/0.921; middle coherence=0.916) |
| 421 | 422/F1 | L260 | L261 | L259 104.42/46.93 r_next=0.870 MAD_above=17.14 lag=1(17.11/17.14); L260 98.75/47.05 r_next=-0.257 MAD_above=16.93 lag=-2(16.00/16.93); L261 84.76/59.03 r_next=0.887 MAD_above=71.84 lag=32(65.50/71.84); L262 85.44/61.81 r_next=0.028 MAD_above=17.55 lag=-1(17.53/17.55); direct-full=L261 (L261 persistent three-third step; thirds=9.345,3.555,4.137; correlation above/next=-0.329/0.912; middle coherence=0.918) |
| 426 | 427/F1 | L260 | L261 | L259 100.95/45.80 r_next=0.818 MAD_above=16.61 lag=0(16.61/16.61); L260 96.67/48.00 r_next=-0.202 MAD_above=19.51 lag=-2(16.80/19.51); L261 83.55/58.31 r_next=0.869 MAD_above=70.42 lag=-21(65.56/70.42); L262 84.76/60.77 r_next=-0.030 MAD_above=18.96 lag=-1(17.95/18.96); direct-full=L261 (L261 persistent three-third step; thirds=9.326,3.377,4.237; correlation above/next=-0.268/0.897; middle coherence=0.916) |
| 427 | 428/F1 | L260 | L261 | L259 98.61/47.00 r_next=0.773 MAD_above=16.25 lag=0(16.25/16.25); L260 95.01/49.24 r_next=-0.131 MAD_above=22.04 lag=-2(19.90/22.04); L261 83.74/58.95 r_next=0.878 MAD_above=68.89 lag=-21(65.30/68.89); L262 82.15/59.49 r_next=-0.012 MAD_above=18.55 lag=-1(17.83/18.55); direct-full=L261 (L261 persistent three-third step; thirds=9.356,3.241,4.064; correlation above/next=-0.201/0.907; middle coherence=0.918) |
| 441 | 442/F1 | L260 | L261 | L259 100.67/45.96 r_next=0.675 MAD_above=17.91 lag=0(17.91/17.91); L260 105.76/48.37 r_next=-0.024 MAD_above=26.60 lag=-1(25.70/26.60); L261 82.95/57.45 r_next=0.884 MAD_above=62.59 lag=-20(61.47/62.59); L262 81.66/59.92 r_next=0.031 MAD_above=17.78 lag=-1(17.56/17.78); direct-full=L261 (L261 persistent three-third step; thirds=9.252,3.058,2.615; correlation above/next=-0.083/0.915; middle coherence=0.915) |
| 445 | 446/F1 | L260 | L261 | L259 102.59/46.01 r_next=0.690 MAD_above=18.88 lag=1(18.76/18.88); L260 108.55/46.63 r_next=-0.067 MAD_above=24.74 lag=-1(24.23/24.74); L261 87.04/60.14 r_next=0.894 MAD_above=65.36 lag=-21(61.63/65.36); L262 85.91/60.61 r_next=0.011 MAD_above=17.31 lag=-1(17.15/17.31); direct-full=L261 (L261 persistent three-third step; thirds=9.543,3.340,2.868; correlation above/next=-0.137/0.919; middle coherence=0.917) |
| 449 | 450/F1 | L260 | L261 | L259 104.76/47.08 r_next=0.696 MAD_above=17.78 lag=0(17.78/17.78); L260 108.27/47.81 r_next=-0.083 MAD_above=25.83 lag=-1(25.34/25.83); L261 88.83/59.78 r_next=0.916 MAD_above=64.91 lag=-19(62.41/64.91); L262 83.35/60.16 r_next=0.021 MAD_above=15.15 lag=0(15.15/15.15); direct-full=L261 (L261 persistent three-third step; thirds=9.670,2.956,2.698; correlation above/next=-0.154/0.939; middle coherence=0.912) |
| 450 | 451/F1 | L260 | L261 | L259 104.13/45.77 r_next=0.668 MAD_above=18.57 lag=0(18.57/18.57); L260 107.71/46.75 r_next=-0.096 MAD_above=26.90 lag=-2(25.14/26.90); L261 85.88/57.91 r_next=0.897 MAD_above=64.11 lag=-18(60.78/64.11); L262 84.57/59.97 r_next=0.017 MAD_above=17.13 lag=-2(16.26/17.13); direct-full=L261 (L261 persistent three-third step; thirds=9.217,2.708,2.885; correlation above/next=-0.149/0.925; middle coherence=0.908) |
| 453 | 454/F1 | L259 | L261 | L258 101.80/45.57 r_next=0.813 MAD_above=15.18 lag=1(15.16/15.18); L259 104.57/44.93 r_next=0.758 MAD_above=17.53 lag=0(17.53/17.53); L260 99.12/49.18 r_next=-0.108 MAD_above=22.48 lag=-3(19.27/22.48); L261 85.26/59.38 r_next=0.891 MAD_above=67.89 lag=-21(65.30/67.89); L262 81.83/59.07 r_next=0.024 MAD_above=17.40 lag=-1(16.22/17.40); direct-full=L261 (L261 persistent three-third step; thirds=8.957,3.409,3.404; correlation above/next=-0.174/0.922; middle coherence=0.916) |
| 455 | 456/F1 | L260 | L261 | L259 105.10/46.46 r_next=0.637 MAD_above=17.70 lag=0(17.70/17.70); L260 105.67/49.46 r_next=-0.084 MAD_above=27.52 lag=-2(25.55/27.52); L261 84.87/59.16 r_next=0.875 MAD_above=67.19 lag=-19(65.82/67.19); L262 82.82/59.42 r_next=0.043 MAD_above=18.69 lag=-1(18.51/18.69); direct-full=L261 (L261 persistent three-third step; thirds=9.205,3.132,3.543; correlation above/next=-0.150/0.907; middle coherence=0.907) |
| 457 | 458/F1 | L260 | L261 | L259 101.78/45.82 r_next=0.789 MAD_above=16.07 lag=0(16.07/16.07); L260 95.28/49.60 r_next=-0.170 MAD_above=21.73 lag=-2(18.91/21.73); L261 82.74/58.24 r_next=0.880 MAD_above=70.64 lag=-20(66.05/70.64); L262 81.22/60.25 r_next=-0.001 MAD_above=18.35 lag=-1(17.52/18.35); direct-full=L261 (L261 persistent three-third step; thirds=9.054,3.461,4.092; correlation above/next=-0.238/0.907; middle coherence=0.914) |
| 461 | 462/F1 | L259 | L261 | L258 97.93/46.66 r_next=0.826 MAD_above=16.55 lag=0(16.55/16.55); L259 101.95/46.07 r_next=0.820 MAD_above=17.88 lag=1(17.75/17.88); L260 94.35/49.50 r_next=-0.114 MAD_above=19.69 lag=-1(19.15/19.69); L261 82.59/59.09 r_next=0.874 MAD_above=68.08 lag=-20(65.58/68.08); L262 82.50/60.52 r_next=0.005 MAD_above=18.32 lag=-1(18.28/18.32); direct-full=L261 (L261 persistent three-third step; thirds=9.299,3.324,3.718; correlation above/next=-0.184/0.901; middle coherence=0.917) |
| 462 | 463/F1 | L260 | L261 | L259 102.34/46.07 r_next=0.810 MAD_above=17.43 lag=-1(17.36/17.43); L260 96.50/50.65 r_next=-0.142 MAD_above=20.36 lag=-1(19.47/20.36); L261 82.08/58.17 r_next=0.887 MAD_above=68.60 lag=-19(66.25/68.60); L262 82.89/59.02 r_next=-0.029 MAD_above=16.56 lag=0(16.56/16.56); direct-full=L261 (L261 persistent three-third step; thirds=9.298,3.326,3.728; correlation above/next=-0.212/0.911; middle coherence=0.912) |
| 477 | 478/F1 | L260 | L261 | L259 95.52/54.46 r_next=0.889 MAD_above=7.20 lag=1(7.15/7.20); L260 87.66/50.61 r_next=0.104 MAD_above=14.63 lag=-2(12.66/14.63); L261 53.52/45.62 r_next=0.886 MAD_above=59.38 lag=-9(58.05/59.38); L262 53.78/47.00 r_next=-0.021 MAD_above=12.67 lag=-1(12.41/12.67); direct-full=L261 (L261 persistent three-third step; thirds=7.679,5.325,7.089; correlation above/next=0.082/0.904; middle coherence=0.935) |
| 482 | 483/F1 | L260 | L261 | L259 102.09/52.67 r_next=0.944 MAD_above=6.73 lag=0(6.73/6.73); L260 96.42/49.55 r_next=0.378 MAD_above=10.47 lag=1(10.41/10.47); L261 60.87/48.44 r_next=0.934 MAD_above=48.58 lag=-1(48.55/48.58); L262 58.80/49.82 r_next=0.010 MAD_above=10.90 lag=0(10.90/10.90); direct-full=L261 (L261 persistent three-third step; thirds=6.293,4.838,3.999; correlation above/next=0.395/0.953; middle coherence=0.930) |
| 495 | 496/F1 | L261 | L260 | L259 90.58/55.54 r_next=0.935 MAD_above=6.27 lag=0(6.27/6.27); L260 85.72/58.20 r_next=0.227 MAD_above=11.55 lag=0(11.55/11.55); L261 45.07/43.64 r_next=0.940 MAD_above=60.40 lag=0(60.40/60.40); L262 46.31/44.71 r_next=0.016 MAD_above=8.68 lag=0(8.68/8.68); direct-full=L260 (L260 internal blank x=177-240 Y=3.312; above=8.344 following=107.500; gate=4.000) |
| 498 | 499/F1 | L261 | L259 | L258 89.94/55.97 r_next=0.982 MAD_above=8.53 lag=0(8.53/8.53); L259 85.25/56.39 r_next=0.897 MAD_above=8.55 lag=0(8.55/8.55); L260 78.63/51.69 r_next=0.037 MAD_above=12.73 lag=1(12.37/12.73); L261 47.10/43.73 r_next=0.945 MAD_above=58.60 lag=-30(56.81/58.60); L262 47.96/45.69 r_next=0.010 MAD_above=9.22 lag=0(9.22/9.22); direct-full=L259 (L259 internal blank x=177-240 Y=3.766; above=9.203 following=106.000; gate=4.000) |
| 522 | 523/F1 | L260 | L261 | L259 99.34/58.43 r_next=0.953 MAD_above=6.79 lag=0(6.79/6.79); L260 93.60/55.24 r_next=0.127 MAD_above=9.58 lag=0(9.58/9.58); L261 55.17/48.66 r_next=0.957 MAD_above=63.01 lag=-1(63.00/63.01); L262 54.99/49.31 r_next=-0.019 MAD_above=9.43 lag=0(9.43/9.43); direct-full=L261 (L261 persistent three-third step; thirds=7.446,5.481,6.783; correlation above/next=0.110/0.968; middle coherence=0.924) |
| 533 | 534/F1 | L260 | L261 | L259 99.55/58.46 r_next=0.888 MAD_above=7.62 lag=1(7.41/7.62); L260 90.12/52.56 r_next=0.027 MAD_above=14.77 lag=-1(13.94/14.77); L261 55.54/47.80 r_next=0.937 MAD_above=64.34 lag=-27(61.43/64.34); L262 54.18/49.54 r_next=-0.015 MAD_above=10.22 lag=-2(9.58/10.22); direct-full=L261 (L261 persistent three-third step; thirds=7.619,5.431,7.617; correlation above/next=-0.003/0.954; middle coherence=0.922) |
| 534 | 535/F1 | L260 | L261 | L259 98.70/58.48 r_next=0.917 MAD_above=7.38 lag=1(7.28/7.38); L260 90.96/52.67 r_next=0.063 MAD_above=11.93 lag=-1(11.71/11.93); L261 55.24/48.06 r_next=0.945 MAD_above=62.71 lag=-28(60.60/62.71); L262 54.63/49.42 r_next=-0.015 MAD_above=10.62 lag=0(10.62/10.62); direct-full=L261 (L261 persistent three-third step; thirds=7.873,5.255,6.846; correlation above/next=0.032/0.958; middle coherence=0.924) |
| 536 | 537/F1 | L260 | L261 | L259 97.81/59.04 r_next=0.914 MAD_above=7.23 lag=0(7.23/7.23); L260 91.17/52.32 r_next=0.073 MAD_above=13.55 lag=-1(12.61/13.55); L261 56.58/48.44 r_next=0.926 MAD_above=62.50 lag=-32(61.79/62.50); L262 55.86/49.50 r_next=0.032 MAD_above=11.91 lag=-2(10.78/11.91); direct-full=L261 (L261 persistent three-third step; thirds=7.998,5.144,6.902; correlation above/next=0.047/0.947; middle coherence=0.925) |
| 540 | 541/F1 | L260 | L261 | L259 99.78/58.26 r_next=0.939 MAD_above=7.89 lag=0(7.89/7.89); L260 96.57/57.21 r_next=0.218 MAD_above=11.43 lag=-1(10.46/11.43); L261 57.16/48.38 r_next=0.936 MAD_above=63.15 lag=-3(62.92/63.15); L262 56.20/50.23 r_next=0.007 MAD_above=10.95 lag=-2(10.17/10.95); direct-full=L261 (L261 persistent three-third step; thirds=7.820,5.021,7.198; correlation above/next=0.206/0.955; middle coherence=0.925) |
| 541 | 542/F1 | L260 | L261 | L259 98.78/58.66 r_next=0.948 MAD_above=6.96 lag=0(6.96/6.96); L260 94.88/54.69 r_next=0.146 MAD_above=10.37 lag=-2(9.43/10.37); L261 57.47/47.76 r_next=0.941 MAD_above=61.78 lag=-2(61.61/61.78); L262 55.92/50.40 r_next=0.024 MAD_above=10.86 lag=-1(10.66/10.86); direct-full=L261 (L261 persistent three-third step; thirds=7.618,5.263,6.295; correlation above/next=0.133/0.959; middle coherence=0.922) |
| 545 | 546/F1 | L260 | L261 | L259 101.05/58.06 r_next=0.952 MAD_above=6.99 lag=0(6.99/6.99); L260 96.78/56.79 r_next=0.176 MAD_above=10.27 lag=-1(10.12/10.27); L261 59.47/49.51 r_next=0.935 MAD_above=64.00 lag=-1(63.88/64.00); L262 54.35/48.38 r_next=0.023 MAD_above=11.27 lag=0(11.27/11.27); direct-full=L261 (L261 persistent three-third step; thirds=7.850,5.265,6.868; correlation above/next=0.162/0.950; middle coherence=0.924) |
| 546 | 547/F1 | L260 | L261 | L259 99.63/57.57 r_next=0.960 MAD_above=6.42 lag=0(6.42/6.42); L260 96.27/56.80 r_next=0.190 MAD_above=7.82 lag=0(7.82/7.82); L261 55.32/48.13 r_next=0.934 MAD_above=64.46 lag=-2(64.14/64.46); L262 54.24/49.07 r_next=-0.004 MAD_above=11.57 lag=0(11.57/11.57); direct-full=L261 (L261 persistent three-third step; thirds=7.631,5.369,7.487; correlation above/next=0.174/0.946; middle coherence=0.922) |
| 547 | 548/F1 | L260 | L261 | L259 102.64/57.89 r_next=0.983 MAD_above=6.59 lag=0(6.59/6.59); L260 98.52/58.05 r_next=0.186 MAD_above=8.00 lag=-1(7.34/8.00); L261 57.75/48.44 r_next=0.936 MAD_above=63.82 lag=-13(63.47/63.82); L262 54.27/48.57 r_next=-0.019 MAD_above=11.51 lag=0(11.51/11.51); direct-full=L261 (L261 persistent three-third step; thirds=7.492,5.349,7.701; correlation above/next=0.217/0.945; middle coherence=0.921) |
| 548 | 549/F1 | L260 | L261 | L259 100.37/57.87 r_next=0.979 MAD_above=6.92 lag=0(6.92/6.92); L260 98.28/57.19 r_next=0.172 MAD_above=8.66 lag=-1(8.15/8.66); L261 55.70/48.41 r_next=0.924 MAD_above=64.71 lag=-2(64.61/64.71); L262 55.81/49.30 r_next=-0.009 MAD_above=12.38 lag=0(12.38/12.38); direct-full=L261 (L261 persistent three-third step; thirds=7.557,5.169,7.597; correlation above/next=0.198/0.935; middle coherence=0.921) |
| 549 | 550/F1 | L260 | L261 | L259 101.12/57.94 r_next=0.985 MAD_above=7.53 lag=0(7.53/7.53); L260 97.14/58.53 r_next=0.170 MAD_above=7.83 lag=-1(7.79/7.83); L261 57.21/48.47 r_next=0.934 MAD_above=64.38 lag=0(64.38/64.38); L262 55.47/49.49 r_next=-0.006 MAD_above=11.32 lag=-1(11.25/11.32); direct-full=L261 (L261 persistent three-third step; thirds=7.355,5.245,7.429; correlation above/next=0.195/0.948; middle coherence=0.920) |
| 552 | 553/F1 | L259 | L261 | L258 103.10/59.73 r_next=0.988 MAD_above=8.37 lag=0(8.37/8.37); L259 103.52/59.15 r_next=0.941 MAD_above=7.19 lag=0(7.19/7.19); L260 100.34/58.07 r_next=0.152 MAD_above=11.15 lag=-4(7.00/11.15); L261 58.49/50.26 r_next=0.923 MAD_above=67.76 lag=-32(67.41/67.76); L262 57.70/49.24 r_next=-0.021 MAD_above=11.47 lag=2(10.92/11.47); direct-full=L261 (L261 persistent three-third step; thirds=8.659,5.302,8.720; correlation above/next=0.170/0.948; middle coherence=0.910) |
| 553 | 554/F1 | L260 | L261 | L259 103.12/59.08 r_next=0.981 MAD_above=6.77 lag=0(6.77/6.77); L260 99.22/59.45 r_next=0.131 MAD_above=8.46 lag=-1(7.41/8.46); L261 58.38/48.85 r_next=0.919 MAD_above=67.78 lag=-25(66.61/67.78); L262 57.35/49.25 r_next=0.022 MAD_above=11.16 lag=1(10.80/11.16); direct-full=L261 (L261 persistent three-third step; thirds=8.778,5.344,8.509; correlation above/next=0.148/0.941; middle coherence=0.913) |
| 554 | 555/F1 | L260 | L261 | L259 102.35/58.18 r_next=0.982 MAD_above=6.88 lag=0(6.88/6.88); L260 100.11/58.20 r_next=0.132 MAD_above=8.12 lag=-1(7.51/8.12); L261 55.52/49.25 r_next=0.902 MAD_above=68.91 lag=-13(68.60/68.91); L262 55.24/48.46 r_next=-0.031 MAD_above=12.45 lag=2(12.02/12.45); direct-full=L261 (L261 persistent three-third step; thirds=8.613,5.164,8.901; correlation above/next=0.150/0.932; middle coherence=0.911) |
| 555 | 556/F1 | L260 | L261 | L259 101.33/60.19 r_next=0.960 MAD_above=6.93 lag=0(6.93/6.93); L260 99.90/60.38 r_next=0.146 MAD_above=9.95 lag=-3(6.87/9.95); L261 59.26/50.60 r_next=0.932 MAD_above=69.15 lag=-30(69.08/69.15); L262 58.59/51.27 r_next=-0.003 MAD_above=11.93 lag=2(11.44/11.93); direct-full=L261 (L261 persistent three-third step; thirds=8.924,5.656,8.208; correlation above/next=0.161/0.953; middle coherence=0.927) |
| 556 | 557/F1 | L260 | L261 | L259 102.87/59.24 r_next=0.968 MAD_above=7.26 lag=0(7.26/7.26); L260 102.68/59.06 r_next=0.114 MAD_above=8.93 lag=-2(6.76/8.93); L261 59.99/51.58 r_next=0.899 MAD_above=70.85 lag=22(69.57/70.85); L262 58.34/51.48 r_next=-0.006 MAD_above=13.60 lag=3(12.47/13.60); direct-full=L261 (L261 persistent three-third step; thirds=9.097,5.571,8.593; correlation above/next=0.131/0.931; middle coherence=0.927) |
| 560 | 561/F1 | L259 | L261 | L258 104.56/58.83 r_next=0.983 MAD_above=9.81 lag=0(9.81/9.81); L259 105.35/57.56 r_next=0.968 MAD_above=7.42 lag=0(7.42/7.42); L260 104.29/57.66 r_next=0.056 MAD_above=9.46 lag=-2(7.66/9.46); L261 59.90/50.09 r_next=0.933 MAD_above=72.50 lag=-28(70.20/72.50); L262 59.55/50.95 r_next=0.039 MAD_above=9.91 lag=-1(9.90/9.91); direct-full=L261 (L261 persistent three-third step; thirds=10.869,5.401,8.962; correlation above/next=0.078/0.948; middle coherence=0.926) |
| 561 | 562/F1 | L260 | L261 | L259 105.68/58.53 r_next=0.973 MAD_above=8.23 lag=0(8.23/8.23); L260 102.50/57.62 r_next=0.074 MAD_above=9.87 lag=-2(8.20/9.87); L261 61.14/51.41 r_next=0.929 MAD_above=71.30 lag=-27(69.01/71.30); L262 60.28/51.57 r_next=0.007 MAD_above=10.68 lag=-1(10.39/10.68); direct-full=L261 (L261 persistent three-third step; thirds=10.571,5.374,8.575; correlation above/next=0.100/0.946; middle coherence=0.930) |
| 563 | 564/F1 | L260 | L261 | L259 117.15/49.57 r_next=0.967 MAD_above=9.25 lag=0(9.25/9.25); L260 112.76/51.11 r_next=0.261 MAD_above=8.98 lag=-1(8.18/8.98); L261 70.11/50.71 r_next=0.920 MAD_above=61.83 lag=11(59.38/61.83); L262 67.90/50.30 r_next=0.024 MAD_above=12.33 lag=-1(12.18/12.33); direct-full=L261 (L261 persistent three-third step; thirds=10.275,3.096,8.765; correlation above/next=0.318/0.951; middle coherence=0.928) |
| 565 | 566/F1 | L259 | L261 | L258 105.25/56.53 r_next=0.961 MAD_above=12.90 lag=0(12.90/12.90); L259 108.56/55.90 r_next=0.886 MAD_above=10.53 lag=0(10.53/10.53); L260 104.22/56.75 r_next=0.209 MAD_above=10.51 lag=-1(10.40/10.51); L261 62.20/50.63 r_next=0.886 MAD_above=68.87 lag=32(67.11/68.87); L262 60.17/50.71 r_next=0.047 MAD_above=13.88 lag=1(13.87/13.88); direct-full=L261 (L261 persistent three-third step; thirds=9.272,4.736,8.684; correlation above/next=0.153/0.908; middle coherence=0.937) |
| 566 | 567/F1 | L260 | L261 | L259 106.99/56.34 r_next=0.959 MAD_above=9.82 lag=0(9.82/9.82); L260 104.41/56.11 r_next=0.100 MAD_above=9.55 lag=0(9.55/9.55); L261 62.56/50.70 r_next=0.885 MAD_above=69.03 lag=32(67.16/69.03); L262 62.26/51.19 r_next=-0.006 MAD_above=13.73 lag=-2(12.62/13.73); direct-full=L261 (L261 persistent three-third step; thirds=9.057,4.721,8.660; correlation above/next=0.119/0.904; middle coherence=0.936) |
| 567 | 568/F1 | L260 | L261 | L259 105.25/57.96 r_next=0.937 MAD_above=7.92 lag=0(7.92/7.92); L260 106.27/60.83 r_next=0.181 MAD_above=10.65 lag=-2(8.80/10.65); L261 61.51/50.03 r_next=0.923 MAD_above=73.61 lag=32(69.20/73.61); L262 60.48/50.76 r_next=-0.005 MAD_above=12.45 lag=-1(12.44/12.45); direct-full=L261 (L261 persistent three-third step; thirds=9.840,5.257,8.895; correlation above/next=0.144/0.941; middle coherence=0.941) |
| 568 | 569/F1 | L259 | L261 | L258 104.67/59.15 r_next=0.978 MAD_above=10.40 lag=0(10.40/10.40); L259 105.76/58.01 r_next=0.949 MAD_above=8.23 lag=0(8.23/8.23); L260 105.68/59.19 r_next=0.126 MAD_above=10.08 lag=-2(8.20/10.08); L261 61.04/49.71 r_next=0.909 MAD_above=72.59 lag=32(70.12/72.59); L262 62.13/52.14 r_next=-0.007 MAD_above=14.06 lag=-2(13.40/14.06); direct-full=L261 (L261 persistent three-third step; thirds=9.516,5.147,8.668; correlation above/next=0.105/0.930; middle coherence=0.939) |
| 570 | 571/F1 | L260 | L261 | L259 102.90/58.56 r_next=0.904 MAD_above=9.47 lag=0(9.47/9.47); L260 98.31/57.01 r_next=-0.012 MAD_above=11.85 lag=-1(11.64/11.85); L261 61.00/49.16 r_next=0.924 MAD_above=72.77 lag=-10(72.20/72.77); L262 59.05/49.56 r_next=-0.008 MAD_above=12.83 lag=-1(12.81/12.83); direct-full=L261 (L261 persistent three-third step; thirds=9.398,5.776,8.310; correlation above/next=-0.043/0.944; middle coherence=0.929) |
| 571 | 572/F1 | L259 | L261 | L258 101.68/60.47 r_next=0.979 MAD_above=10.45 lag=0(10.45/10.45); L259 104.01/57.98 r_next=0.943 MAD_above=8.63 lag=0(8.63/8.63); L260 98.37/54.73 r_next=0.048 MAD_above=10.15 lag=-1(9.42/10.15); L261 60.21/49.89 r_next=0.958 MAD_above=69.87 lag=-25(69.18/69.87); L262 62.08/49.97 r_next=-0.009 MAD_above=10.61 lag=1(10.50/10.61); direct-full=L261 (L261 persistent three-third step; thirds=9.271,5.521,8.041; correlation above/next=0.018/0.972; middle coherence=0.933) |
| 573 | 574/F1 | L260 | L261 | L259 110.05/52.57 r_next=0.924 MAD_above=9.37 lag=0(9.37/9.37); L260 106.98/53.26 r_next=0.231 MAD_above=11.70 lag=-1(11.55/11.70); L261 66.20/49.94 r_next=0.905 MAD_above=61.76 lag=2(61.71/61.76); L262 65.78/51.78 r_next=0.017 MAD_above=14.01 lag=0(14.01/14.01); direct-full=L261 (L261 persistent three-third step; thirds=7.910,4.432,8.055; correlation above/next=0.242/0.930; middle coherence=0.937) |
| 574 | 575/F1 | L260 | L261 | L259 112.86/52.81 r_next=0.826 MAD_above=8.92 lag=0(8.92/8.92); L260 103.23/46.92 r_next=0.074 MAD_above=17.19 lag=-2(14.47/17.19); L261 66.00/50.44 r_next=0.898 MAD_above=62.81 lag=32(59.79/62.81); L262 66.75/50.57 r_next=0.010 MAD_above=14.07 lag=-1(13.77/14.07); direct-full=L261 (L261 persistent three-third step; thirds=8.351,4.238,8.362; correlation above/next=0.044/0.922; middle coherence=0.936) |
| 575 | 576/F1 | L260 | L261 | L259 112.08/53.84 r_next=0.920 MAD_above=9.82 lag=1(9.48/9.82); L260 109.63/54.58 r_next=0.228 MAD_above=12.65 lag=-2(11.17/12.65); L261 67.62/52.31 r_next=0.903 MAD_above=64.17 lag=32(62.45/64.17); L262 66.02/53.09 r_next=-0.001 MAD_above=14.14 lag=0(14.14/14.14); direct-full=L261 (L261 persistent three-third step; thirds=9.193,4.060,8.582; correlation above/next=0.233/0.928; middle coherence=0.938) |
| 577 | 578/F1 | L261 | L262 | L260 102.05/50.48 r_next=0.345 MAD_above=16.17 lag=-1(15.42/16.17); L261 90.71/45.06 r_next=0.763 MAD_above=34.32 lag=0(34.32/34.32); L262 70.06/56.16 r_next=0.021 MAD_above=27.27 lag=1(26.51/27.27); direct-full=L262 (L262 internal blank x=77-140 Y=1.344; above=87.000 following=90.000; gate=4.000) |
| 579 | 580/F1 | L260 | L261 | L259 109.28/55.32 r_next=0.848 MAD_above=9.88 lag=0(9.88/9.88); L260 100.56/48.20 r_next=0.047 MAD_above=16.80 lag=-1(16.00/16.80); L261 67.56/51.19 r_next=0.905 MAD_above=62.62 lag=-12(60.07/62.62); L262 63.90/50.13 r_next=-0.009 MAD_above=12.89 lag=1(12.61/12.89); direct-full=L261 (L261 persistent three-third step; thirds=8.935,4.380,7.990; correlation above/next=0.038/0.940; middle coherence=0.932) |
| 597 | 598/F1 | L260 | L262 | L259 108.11/58.55 r_next=0.945 MAD_above=8.26 lag=0(8.26/8.26); L260 100.79/53.41 r_next=0.762 MAD_above=12.30 lag=-1(11.93/12.30); L261 89.93/48.90 r_next=0.402 MAD_above=18.98 lag=-3(15.58/18.98); L262 47.81/50.89 r_next=0.038 MAD_above=50.29 lag=-3(48.85/50.29); direct-full=L262 (L262 internal blank x=70-133 Y=1.359; above=88.891 following=62.000; gate=4.000) |
| 598 | 599/F1 | L260 | L261 | L259 106.77/58.55 r_next=0.940 MAD_above=8.26 lag=0(8.26/8.26); L260 101.09/55.24 r_next=0.041 MAD_above=12.76 lag=-2(10.74/12.76); L261 64.46/52.03 r_next=0.907 MAD_above=69.41 lag=-12(67.96/69.41); L262 64.88/53.21 r_next=-0.016 MAD_above=14.92 lag=-3(13.23/14.92); direct-full=L261 (L261 persistent three-third step; thirds=7.593,5.788,7.456; correlation above/next=0.012/0.938; middle coherence=0.932) |
| 600 | 601/F1 | L260 | L261 | L259 104.30/58.53 r_next=0.901 MAD_above=9.05 lag=0(9.05/9.05); L260 101.19/53.80 r_next=0.030 MAD_above=15.04 lag=-2(12.72/15.04); L261 62.41/52.25 r_next=0.892 MAD_above=70.43 lag=-6(70.12/70.43); L262 60.02/51.02 r_next=-0.009 MAD_above=14.62 lag=0(14.62/14.62); direct-full=L261 (L261 persistent three-third step; thirds=8.674,5.433,7.749; correlation above/next=-0.011/0.911; middle coherence=0.927) |
| 601 | 602/F1 | L260 | L261 | L259 102.71/59.32 r_next=0.925 MAD_above=8.92 lag=0(8.92/8.92); L260 102.59/56.51 r_next=0.076 MAD_above=12.13 lag=-1(11.53/12.13); L261 61.52/51.44 r_next=0.916 MAD_above=71.07 lag=-2(71.04/71.07); L262 59.71/50.09 r_next=-0.000 MAD_above=12.82 lag=0(12.82/12.82); direct-full=L261 (L261 persistent three-third step; thirds=8.439,5.141,8.956; correlation above/next=0.046/0.933; middle coherence=0.930) |
| 606 | 607/F1 | L260 | L261 | L259 107.22/56.29 r_next=0.905 MAD_above=9.41 lag=-1(9.30/9.41); L260 99.13/51.55 r_next=-0.037 MAD_above=14.76 lag=-2(12.35/14.76); L261 64.54/53.01 r_next=0.940 MAD_above=71.28 lag=-32(65.33/71.28); L262 62.93/52.69 r_next=0.008 MAD_above=12.09 lag=0(12.09/12.09); direct-full=L261 (L261 persistent three-third step; thirds=11.059,5.319,7.997; correlation above/next=-0.066/0.958; middle coherence=0.930) |
| 608 | 609/F1 | L260 | L261 | L259 102.30/55.72 r_next=0.907 MAD_above=7.11 lag=0(7.11/7.11); L260 96.98/50.24 r_next=-0.003 MAD_above=14.25 lag=-2(12.72/14.25); L261 61.45/49.12 r_next=0.894 MAD_above=65.91 lag=-4(64.31/65.91); L262 62.46/50.25 r_next=0.019 MAD_above=12.68 lag=-1(12.15/12.68); direct-full=L261 (L261 persistent three-third step; thirds=10.898,5.082,5.764; correlation above/next=-0.005/0.921; middle coherence=0.921) |
| 618 | 619/F1 | L260 | L261 | L259 100.89/54.55 r_next=0.480 MAD_above=10.45 lag=0(10.45/10.45); L260 73.05/45.53 r_next=0.123 MAD_above=34.50 lag=-2(33.02/34.50); L261 60.58/48.97 r_next=0.911 MAD_above=50.35 lag=-2(49.77/50.35); L262 61.38/49.93 r_next=-0.003 MAD_above=11.85 lag=-2(11.30/11.85); direct-full=L261 (L261 internal blank x=71-134 Y=1.328; above=92.234 following=81.000; gate=4.000) |
| 620 | 621/F1 | L260 | L261 | L259 95.97/54.28 r_next=0.740 MAD_above=8.59 lag=1(8.29/8.59); L260 91.56/52.43 r_next=0.026 MAD_above=20.03 lag=-2(18.88/20.03); L261 60.85/47.88 r_next=0.929 MAD_above=64.15 lag=-2(63.95/64.15); L262 60.14/48.23 r_next=-0.005 MAD_above=9.90 lag=0(9.90/9.90); direct-full=L261 (L261 persistent three-third step; thirds=10.751,4.452,7.089; correlation above/next=-0.012/0.941; middle coherence=0.928) |
| 622 | 623/F1 | L260 | L261 | L259 94.63/54.04 r_next=0.862 MAD_above=7.60 lag=0(7.60/7.60); L260 89.96/52.60 r_next=0.042 MAD_above=12.51 lag=-1(12.36/12.51); L261 59.03/47.16 r_next=0.913 MAD_above=63.85 lag=-20(59.00/63.85); L262 57.65/47.41 r_next=-0.022 MAD_above=12.01 lag=0(12.01/12.01); direct-full=L261 (L261 persistent three-third step; thirds=11.047,3.137,8.289; correlation above/next=0.005/0.927; middle coherence=0.910) |
| 623 | 624/F1 | L258 | L261 | L257 93.25/53.69 r_next=0.965 MAD_above=9.48 lag=0(9.48/9.48); L258 95.10/53.65 r_next=0.979 MAD_above=8.63 lag=0(8.63/8.63); L259 98.11/52.94 r_next=0.954 MAD_above=7.75 lag=1(7.70/7.75); L260 92.47/54.52 r_next=0.055 MAD_above=11.22 lag=-2(10.29/11.22); L261 60.98/47.29 r_next=0.906 MAD_above=64.61 lag=-12(62.74/64.61); L262 56.70/47.12 r_next=0.020 MAD_above=12.95 lag=-1(12.81/12.95); direct-full=L261 (L261 persistent three-third step; thirds=11.409,3.433,7.667; correlation above/next=0.048/0.923; middle coherence=0.908) |
| 624 | 625/F1 | L259 | L261 | L258 94.69/53.88 r_next=0.981 MAD_above=9.41 lag=1(9.29/9.41); L259 95.14/54.02 r_next=0.960 MAD_above=7.52 lag=0(7.52/7.52); L260 94.93/55.81 r_next=0.064 MAD_above=9.54 lag=-2(8.40/9.54); L261 58.50/47.30 r_next=0.913 MAD_above=65.66 lag=-32(63.54/65.66); L262 56.81/47.27 r_next=0.041 MAD_above=11.45 lag=0(11.45/11.45); direct-full=L261 (L261 persistent three-third step; thirds=11.115,3.143,8.207; correlation above/next=0.066/0.923; middle coherence=0.911) |
| 625 | 626/F1 | L260 | L261 | L259 94.00/53.79 r_next=0.971 MAD_above=7.17 lag=0(7.17/7.17); L260 92.73/54.21 r_next=-0.014 MAD_above=8.61 lag=-1(7.92/8.61); L261 55.82/43.59 r_next=0.861 MAD_above=66.02 lag=-31(64.68/66.02); L262 54.85/45.34 r_next=0.014 MAD_above=13.54 lag=0(13.54/13.54); direct-full=L261 (L261 persistent three-third step; thirds=10.369,3.329,8.743; correlation above/next=-0.042/0.867; middle coherence=0.921) |
| 626 | 627/F1 | L260 | L261 | L259 96.02/52.59 r_next=0.971 MAD_above=6.80 lag=0(6.80/6.80); L260 92.71/54.80 r_next=-0.030 MAD_above=8.63 lag=-1(7.75/8.63); L261 54.91/42.50 r_next=0.876 MAD_above=66.84 lag=-12(66.04/66.84); L262 56.82/45.53 r_next=0.037 MAD_above=12.25 lag=0(12.25/12.25); direct-full=L261 (L261 persistent three-third step; thirds=10.455,3.208,9.047; correlation above/next=-0.065/0.880; middle coherence=0.923) |
| 627 | 628/F1 | L260 | L261 | L259 96.57/54.16 r_next=0.958 MAD_above=7.72 lag=0(7.72/7.72); L260 90.97/55.05 r_next=0.083 MAD_above=11.05 lag=-2(10.07/11.05); L261 57.88/47.26 r_next=0.909 MAD_above=63.51 lag=-32(62.14/63.51); L262 57.13/47.52 r_next=0.054 MAD_above=12.13 lag=0(12.13/12.13); direct-full=L261 (L261 persistent three-third step; thirds=10.697,3.318,8.209; correlation above/next=0.085/0.926; middle coherence=0.923) |
| 628 | 629/F1 | L260 | L261 | L259 97.43/53.90 r_next=0.953 MAD_above=8.07 lag=1(7.41/8.07); L260 93.10/54.89 r_next=0.069 MAD_above=10.25 lag=-2(9.06/10.25); L261 55.92/46.86 r_next=0.901 MAD_above=64.65 lag=-32(62.42/64.65); L262 59.25/48.36 r_next=0.033 MAD_above=12.74 lag=-1(12.54/12.74); direct-full=L261 (L261 persistent three-third step; thirds=11.217,3.089,7.897; correlation above/next=0.067/0.917; middle coherence=0.924) |
| 629 | 630/F1 | L260 | L261 | L259 94.42/53.81 r_next=0.930 MAD_above=7.56 lag=0(7.56/7.56); L260 90.07/55.79 r_next=0.111 MAD_above=10.31 lag=-1(9.56/10.31); L261 58.46/46.10 r_next=0.893 MAD_above=62.22 lag=-27(60.65/62.22); L262 56.17/48.53 r_next=0.028 MAD_above=12.95 lag=0(12.95/12.95); direct-full=L261 (L261 persistent three-third step; thirds=10.822,3.287,7.699; correlation above/next=0.095/0.916; middle coherence=0.919) |
| 632 | 633/F1 | L260 | L261 | L259 93.57/54.09 r_next=0.911 MAD_above=8.55 lag=0(8.55/8.55); L260 97.65/54.15 r_next=0.138 MAD_above=10.61 lag=0(10.61/10.61); L261 60.90/49.29 r_next=0.932 MAD_above=63.99 lag=-13(63.25/63.99); L262 57.18/48.19 r_next=0.011 MAD_above=10.65 lag=0(10.65/10.65); direct-full=L261 (L261 persistent three-third step; thirds=10.240,4.247,7.473; correlation above/next=0.110/0.943; middle coherence=0.917) |
| 634 | 635/F1 | L260 | L261 | L259 95.34/54.27 r_next=0.652 MAD_above=8.00 lag=0(8.00/8.00); L260 87.54/50.66 r_next=-0.062 MAD_above=21.29 lag=-1(20.36/21.29); L261 58.52/49.02 r_next=0.937 MAD_above=65.97 lag=-32(65.15/65.97); L262 59.50/48.19 r_next=0.012 MAD_above=10.61 lag=-1(10.18/10.61); direct-full=L261 (L261 persistent three-third step; thirds=11.370,4.446,7.242; correlation above/next=-0.126/0.953; middle coherence=0.925) |
| 644 | 645/F1 | L259 | L261 | L258 94.84/54.96 r_next=0.961 MAD_above=12.70 lag=-1(12.63/12.70); L259 95.67/54.76 r_next=0.666 MAD_above=9.44 lag=0(9.44/9.44); L260 83.80/46.37 r_next=0.015 MAD_above=21.70 lag=0(21.70/21.70); L261 58.35/48.00 r_next=0.938 MAD_above=57.96 lag=-2(57.34/57.96); L262 57.37/48.78 r_next=0.013 MAD_above=10.04 lag=-1(10.03/10.04); direct-full=L261 (L261 persistent three-third step; thirds=10.544,4.601,4.668; correlation above/next=-0.080/0.951; middle coherence=0.915) |
| 648 | 649/F1 | L260 | L261 | L259 96.67/56.07 r_next=0.628 MAD_above=9.02 lag=0(9.02/9.02); L260 85.25/47.47 r_next=0.000 MAD_above=23.72 lag=-1(23.53/23.72); L261 57.78/49.02 r_next=0.924 MAD_above=60.27 lag=-3(59.56/60.27); L262 59.37/49.82 r_next=0.022 MAD_above=11.15 lag=0(11.15/11.15); direct-full=L261 (L261 persistent three-third step; thirds=10.817,4.486,5.127; correlation above/next=-0.074/0.938; middle coherence=0.916) |
| 651 | 652/F1 | L260 | L261 | L259 96.14/55.76 r_next=0.635 MAD_above=9.45 lag=0(9.45/9.45); L260 81.47/45.98 r_next=0.037 MAD_above=24.50 lag=0(24.50/24.50); L261 59.65/49.02 r_next=0.946 MAD_above=57.92 lag=-2(57.31/57.92); L262 59.35/49.21 r_next=0.012 MAD_above=9.63 lag=0(9.63/9.63); direct-full=L261 (L261 persistent three-third step; thirds=9.935,4.664,4.592; correlation above/next=-0.059/0.955; middle coherence=0.921) |
| 658 | 659/F1 | L260 | L261 | L259 92.39/54.08 r_next=0.718 MAD_above=8.50 lag=0(8.50/8.50); L260 86.33/48.52 r_next=0.001 MAD_above=19.72 lag=-1(19.04/19.72); L261 56.03/46.24 r_next=0.908 MAD_above=61.18 lag=-5(60.74/61.18); L262 57.13/47.00 r_next=0.015 MAD_above=11.03 lag=-1(10.55/11.03); direct-full=L261 (L261 persistent three-third step; thirds=10.615,3.856,6.506; correlation above/next=-0.058/0.921; middle coherence=0.924) |
| 666 | 667/F1 | L259 | L261 | L258 94.00/53.42 r_next=0.979 MAD_above=9.40 lag=1(9.33/9.40); L259 93.34/53.56 r_next=0.611 MAD_above=7.44 lag=0(7.44/7.44); L260 76.87/43.74 r_next=-0.075 MAD_above=21.20 lag=-1(20.72/21.20); L261 54.51/42.41 r_next=0.882 MAD_above=57.47 lag=-13(53.94/57.47); L262 55.74/44.55 r_next=0.028 MAD_above=12.83 lag=0(12.83/12.83); direct-full=L261 (L261 persistent three-third step; thirds=10.631,3.080,6.608; correlation above/next=-0.231/0.899; middle coherence=0.926) |
| 677 | 678/F1 | L260 | L261 | L259 93.72/54.16 r_next=0.544 MAD_above=7.70 lag=1(7.29/7.70); L260 74.01/44.71 r_next=-0.060 MAD_above=24.82 lag=-1(24.09/24.82); L261 54.70/44.11 r_next=0.915 MAD_above=57.01 lag=-20(56.58/57.01); L262 57.96/47.73 r_next=-0.003 MAD_above=11.53 lag=-1(11.06/11.53); direct-full=L261 (L261 persistent three-third step; thirds=10.608,3.086,6.469; correlation above/next=-0.161/0.923; middle coherence=0.918) |
| 680 | 681/F1 | L260 | L261 | L259 94.01/54.19 r_next=0.716 MAD_above=8.11 lag=0(8.11/8.11); L260 82.49/47.71 r_next=0.033 MAD_above=19.43 lag=-1(19.07/19.43); L261 57.49/46.22 r_next=0.940 MAD_above=59.39 lag=-3(59.21/59.39); L262 57.07/47.48 r_next=-0.003 MAD_above=10.14 lag=0(10.14/10.14); direct-full=L261 (L261 persistent three-third step; thirds=10.488,3.988,6.687; correlation above/next=-0.027/0.950; middle coherence=0.924) |
| 682 | 683/F1 | L260 | L261 | L259 91.70/54.93 r_next=0.727 MAD_above=9.39 lag=0(9.39/9.39); L260 86.75/47.71 r_next=0.016 MAD_above=19.47 lag=-1(18.86/19.47); L261 58.89/48.29 r_next=0.928 MAD_above=61.18 lag=-6(60.49/61.18); L262 60.25/48.63 r_next=0.018 MAD_above=11.96 lag=-1(11.85/11.96); direct-full=L261 (L261 persistent three-third step; thirds=10.798,4.447,6.428; correlation above/next=-0.041/0.943; middle coherence=0.922) |
| 683 | 684/F1 | L260 | L261 | L259 93.94/55.08 r_next=0.759 MAD_above=8.53 lag=0(8.53/8.53); L260 90.20/55.26 r_next=0.075 MAD_above=20.06 lag=-1(19.91/20.06); L261 58.77/48.49 r_next=0.941 MAD_above=64.72 lag=-4(64.58/64.72); L262 57.80/47.17 r_next=0.028 MAD_above=9.81 lag=-1(9.47/9.81); direct-full=L261 (L261 persistent three-third step; thirds=10.115,4.333,7.193; correlation above/next=0.037/0.952; middle coherence=0.924) |
| 685 | 686/F1 | L260 | L261 | L259 96.32/55.10 r_next=0.794 MAD_above=11.14 lag=1(11.13/11.14); L260 89.86/48.04 r_next=0.002 MAD_above=17.10 lag=0(17.10/17.10); L261 60.05/48.43 r_next=0.947 MAD_above=61.48 lag=-2(60.99/61.48); L262 57.98/48.84 r_next=0.011 MAD_above=10.46 lag=-2(10.44/10.46); direct-full=L261 (L261 persistent three-third step; thirds=10.134,4.625,6.176; correlation above/next=-0.076/0.957; middle coherence=0.914) |
| 689 | 690/F1 | L260 | L261 | L259 97.04/55.37 r_next=0.679 MAD_above=9.62 lag=0(9.62/9.62); L260 82.21/45.90 r_next=0.014 MAD_above=21.95 lag=1(21.73/21.95); L261 58.39/47.71 r_next=0.941 MAD_above=57.95 lag=-2(57.24/57.95); L262 57.82/48.24 r_next=0.010 MAD_above=10.28 lag=0(10.28/10.28); direct-full=L261 (L261 persistent three-third step; thirds=10.351,4.574,4.437; correlation above/next=-0.076/0.954; middle coherence=0.917) |
| 692 | 693/F1 | L260 | L261 | L259 94.08/54.36 r_next=0.721 MAD_above=11.60 lag=0(11.60/11.60); L260 83.66/47.44 r_next=-0.065 MAD_above=18.82 lag=0(18.82/18.82); L261 57.52/47.87 r_next=0.973 MAD_above=62.92 lag=-32(61.08/62.92); L262 60.28/48.31 r_next=-0.011 MAD_above=8.08 lag=0(8.08/8.08); direct-full=L261 (L261 persistent three-third step; thirds=9.637,3.999,7.110; correlation above/next=-0.144/0.983; middle coherence=0.918) |
| 695 | 696/F1 | L260 | L261 | L259 121.76/41.40 r_next=0.783 MAD_above=10.67 lag=1(10.41/10.67); L260 111.11/41.29 r_next=-0.476 MAD_above=17.29 lag=-1(16.14/17.29); L261 88.10/61.42 r_next=0.907 MAD_above=74.33 lag=-10(73.11/74.33); L262 87.06/60.69 r_next=0.020 MAD_above=14.67 lag=-1(14.15/14.67); direct-full=L261 (L261 internal blank x=107-170 Y=1.391; above=148.688 following=117.000; gate=4.000) |
| 701 | 702/F1 | L258 | L261 | L257 117.25/42.99 r_next=0.924 MAD_above=11.03 lag=1(10.42/11.03); L258 118.51/43.39 r_next=0.925 MAD_above=10.06 lag=1(10.05/10.06); L259 121.92/42.73 r_next=0.819 MAD_above=9.78 lag=0(9.78/9.78); L260 114.32/41.89 r_next=-0.458 MAD_above=14.23 lag=0(14.23/14.23); L261 88.87/61.87 r_next=0.902 MAD_above=76.90 lag=15(75.60/76.90); L262 87.49/61.05 r_next=0.016 MAD_above=15.23 lag=0(15.23/15.23); direct-full=L261 (L261 internal blank x=76-139 Y=1.312; above=165.094 following=118.500; gate=4.000) |
| 703 | 704/F1 | L260 | L261 | L259 120.60/41.83 r_next=0.739 MAD_above=11.02 lag=1(10.95/11.02); L260 109.08/43.18 r_next=-0.474 MAD_above=17.58 lag=-1(17.46/17.58); L261 87.66/62.05 r_next=0.911 MAD_above=78.06 lag=-10(75.79/78.06); L262 88.56/60.78 r_next=0.010 MAD_above=14.21 lag=0(14.21/14.21); direct-full=L261 (L261 internal blank x=94-157 Y=1.375; above=162.656 following=113.000; gate=4.000) |
| 705 | 706/F1 | L260 | L261 | L259 122.03/41.49 r_next=0.854 MAD_above=10.56 lag=0(10.56/10.56); L260 116.64/42.46 r_next=-0.490 MAD_above=13.08 lag=-1(12.74/13.08); L261 87.64/62.34 r_next=0.909 MAD_above=81.79 lag=-10(80.08/81.79); L262 87.40/60.71 r_next=0.029 MAD_above=14.74 lag=-1(13.96/14.74); direct-full=L261 (L261 persistent three-third step; thirds=9.738,6.701,3.277; correlation above/next=-0.534/0.936; middle coherence=0.862) |
| 707 | 708/F1 | L259 | L261 | L258 120.30/42.49 r_next=0.923 MAD_above=10.57 lag=1(10.12/10.57); L259 121.02/41.46 r_next=0.818 MAD_above=10.45 lag=1(10.26/10.45); L260 116.21/42.51 r_next=-0.460 MAD_above=14.76 lag=0(14.76/14.76); L261 86.84/60.94 r_next=0.971 MAD_above=78.08 lag=-30(76.69/78.08); L262 87.35/61.02 r_next=0.029 MAD_above=8.13 lag=1(6.40/8.13); direct-full=L261 (L261 persistent three-third step; thirds=9.587,6.473,2.947; correlation above/next=-0.507/0.982; middle coherence=0.865) |
| 710 | 711/F1 | L259 | L261 | L258 119.94/42.36 r_next=0.919 MAD_above=9.90 lag=1(9.49/9.90); L259 119.83/41.06 r_next=0.852 MAD_above=9.65 lag=1(9.57/9.65); L260 115.73/42.26 r_next=-0.481 MAD_above=12.07 lag=1(11.94/12.07); L261 87.37/61.06 r_next=0.910 MAD_above=78.67 lag=-25(76.98/78.67); L262 87.86/59.89 r_next=0.043 MAD_above=15.43 lag=1(15.38/15.43); direct-full=L261 (L261 persistent three-third step; thirds=10.706,6.835,3.087; correlation above/next=-0.529/0.937; middle coherence=0.875) |
| 714 | 715/F1 | L260 | L261 | L259 119.61/40.69 r_next=0.799 MAD_above=10.39 lag=1(10.27/10.39); L260 111.10/42.02 r_next=-0.460 MAD_above=14.97 lag=0(14.97/14.97); L261 88.04/60.86 r_next=0.894 MAD_above=76.02 lag=-32(74.11/76.02); L262 88.39/59.17 r_next=0.049 MAD_above=15.28 lag=0(15.28/15.28); direct-full=L261 (L261 internal blank x=73-136 Y=1.391; above=164.500 following=117.500; gate=4.000) |
| 716 | 717/F1 | L260 | L261 | L259 120.57/40.72 r_next=0.841 MAD_above=10.11 lag=0(10.11/10.11); L260 112.63/41.21 r_next=-0.484 MAD_above=13.45 lag=0(13.45/13.45); L261 86.31/61.85 r_next=0.893 MAD_above=78.38 lag=-30(75.49/78.38); L262 87.41/60.81 r_next=0.015 MAD_above=16.61 lag=1(16.57/16.61); direct-full=L261 (L261 persistent three-third step; thirds=10.543,6.899,2.547; correlation above/next=-0.534/0.921; middle coherence=0.877) |
| 719 | 720/F1 | L260 | L261 | L259 118.09/41.43 r_next=0.794 MAD_above=9.17 lag=0(9.17/9.17); L260 109.76/41.18 r_next=-0.474 MAD_above=14.86 lag=0(14.86/14.86); L261 86.00/60.98 r_next=0.897 MAD_above=75.87 lag=-12(74.77/75.87); L262 87.43/59.67 r_next=0.004 MAD_above=15.40 lag=1(15.25/15.40); direct-full=L261 (L261 internal blank x=80-143 Y=1.344; above=162.578 following=113.000; gate=4.000) |
| 721 | 722/F1 | L259 | L261 | L258 117.64/42.18 r_next=0.911 MAD_above=10.01 lag=1(9.77/10.01); L259 120.00/40.33 r_next=0.800 MAD_above=9.53 lag=1(9.34/9.53); L260 110.15/40.20 r_next=-0.480 MAD_above=15.48 lag=-1(15.07/15.48); L261 84.81/59.65 r_next=0.892 MAD_above=73.66 lag=-31(72.29/73.66); L262 84.73/59.28 r_next=0.007 MAD_above=15.96 lag=-1(15.68/15.96); direct-full=L261 (L261 internal blank x=69-132 Y=1.344; above=160.234 following=103.500; gate=4.000) |
| 723 | 724/F1 | L260 | L261 | L259 119.23/41.21 r_next=0.823 MAD_above=11.40 lag=2(10.08/11.40); L260 112.48/41.34 r_next=-0.459 MAD_above=14.10 lag=-1(13.71/14.10); L261 84.29/59.68 r_next=0.892 MAD_above=76.52 lag=11(75.12/76.52); L262 83.79/58.10 r_next=0.008 MAD_above=16.60 lag=-1(16.31/16.60); direct-full=L261 (L261 persistent three-third step; thirds=10.795,6.384,2.922; correlation above/next=-0.503/0.921; middle coherence=0.866) |
| 726 | 727/F1 | L260 | L261 | L259 120.70/40.56 r_next=0.822 MAD_above=9.85 lag=1(9.38/9.85); L260 112.40/41.17 r_next=-0.503 MAD_above=15.03 lag=-1(14.85/15.03); L261 84.78/59.47 r_next=0.889 MAD_above=75.99 lag=-12(73.61/75.99); L262 84.76/58.74 r_next=0.036 MAD_above=15.62 lag=-1(15.49/15.62); direct-full=L261 (L261 internal blank x=92-155 Y=1.328; above=163.203 following=111.000; gate=4.000) |
| 736 | 737/F1 | L260 | L261 | L259 114.63/40.45 r_next=0.841 MAD_above=9.85 lag=0(9.85/9.85); L260 107.97/40.13 r_next=-0.491 MAD_above=13.20 lag=0(13.20/13.20); L261 83.40/58.62 r_next=0.893 MAD_above=75.26 lag=-8(73.17/75.26); L262 82.70/57.25 r_next=0.018 MAD_above=15.66 lag=-1(15.34/15.66); direct-full=L261 (L261 persistent three-third step; thirds=9.358,6.512,2.613; correlation above/next=-0.532/0.925; middle coherence=0.866) |
| 743 | 744/F1 | L260 | L261 | L259 115.14/39.84 r_next=0.813 MAD_above=9.85 lag=0(9.85/9.85); L260 106.68/40.38 r_next=-0.527 MAD_above=15.41 lag=-2(14.61/15.41); L261 80.78/58.21 r_next=0.890 MAD_above=77.01 lag=-26(74.01/77.01); L262 80.65/56.45 r_next=0.024 MAD_above=15.92 lag=-2(14.89/15.92); direct-full=L261 (L261 persistent three-third step; thirds=9.885,6.919,2.849; correlation above/next=-0.570/0.922; middle coherence=0.876) |

## Segment constants and applied crop

### Engine field 1

- H engine minus reference: +0: 607; mismatch counters: none.
- c engine minus reference: +0: 607; mismatch counters: none.
- crop engine minus reference: -1: 22, +0: 569, +1: 15, +2: 1; mismatch counters: 248, 290, 324-332, 334-345, 370, 381, 389-399, 755-756.

### Engine field 2

- H engine minus reference: +0: 607; mismatch counters: none.
- c engine minus reference: +0: 607; mismatch counters: none.
- crop engine minus reference: -1: 42, +0: 554, +1: 7, +2: 4; mismatch counters: 306-347, 388-398.

## Comb consistency

Comparable measured pairs: 517; unavailable engine/top pair: 0; contradictions: 14.

| reference counter | comb shift | engine tops | engine-reference top deltas | seven energies |
|---:|---:|:---|:---|:---|
| 248 | +0 | L23/L287 | +0/+1 | -3:9.331157,-2:7.863174,-1:5.819401,0:3.861268,1:5.870023,2:8.210887,3:9.847854 |
| 290 | +0 | L23/L286 | +0/-1 | -3:8.992875,-2:7.362705,-1:5.178685,0:3.542219,1:5.000597,2:6.971136,3:8.560777 |
| 307 | +1 | L22/L286 | -1/+0 | -3:13.880210,-2:11.526084,-1:9.676218,0:6.372993,1:4.964904,2:6.459976,3:9.944452 |
| 310 | +0 | L22/L286 | -1/+0 | -3:10.406049,-2:8.352013,-1:5.557972,0:3.671015,1:5.023283,2:7.798165,3:10.086428 |
| 311 | +0 | L22/L286 | -1/+0 | -3:9.655446,-2:7.842826,-1:5.249148,0:3.682184,1:4.885237,2:7.144885,3:8.271613 |
| 312 | +0 | L22/L286 | -1/+0 | -3:10.553896,-2:8.413113,-1:5.672416,0:4.180133,1:5.322583,2:7.594846,3:9.641738 |
| 315 | +1 | L22/L286 | -1/+0 | -3:14.685623,-2:12.165170,-1:10.478564,0:7.120439,1:5.301116,2:7.612300,3:10.594584 |
| 318 | +1 | L22/L286 | -1/+0 | -3:13.597174,-2:12.027884,-1:9.361037,0:6.435611,1:5.138736,2:6.567912,3:8.768679 |
| 320 | +1 | L22/L286 | -1/+0 | -3:14.926882,-2:12.246314,-1:9.626264,0:7.099796,1:5.425512,2:7.238065,3:9.768991 |
| 322 | +1 | L22/L286 | -1/+0 | -3:14.208431,-2:11.908598,-1:9.392380,0:6.340570,1:5.025627,2:6.440376,3:9.631741 |
| 346 | +1 | L22/L286 | -1/+0 | -3:17.470642,-2:15.024319,-1:12.228327,0:8.740936,1:6.294050,2:8.544500,3:11.935600 |
| 370 | +0 | L23/L287 | +0/+1 | -3:13.609653,-2:11.352225,-1:7.720136,0:4.497510,1:7.793200,2:11.640150,3:14.345895 |
| 388 | +0 | L23/L286 | +1/+0 | -3:14.687718,-2:12.321897,-1:8.485854,0:4.851996,1:7.866098,2:11.563477,3:14.324781 |
| 399 | +0 | L23/L286 | +0/+1 | -3:12.563135,-2:9.587488,-1:6.027559,0:4.093962,1:6.487143,2:9.690465,3:12.146569 |

# Engine-record score: commercial tape

Acceptance verdict: **not accepted**.

Engine rows joined by device counter: 1838; unmatched engine rows: 6042/F1, 6042/F2.

Engine fields are compared with the same numbered raw raster slot at the same counter.

Owner-review disagreement units: 919; counters: 6253-6254, 6257, 6259-7174.

Shifted woven bwdif frames written: 919 under `reports/engine_run_R_disagreements/commercial`.

| counter | reason(s) | shifted bwdif frame |
|---:|:---|:---|
| 6253 | F1 S/switch unmeasurable/L262; F2 S/switch unmeasurable/L524 | `reports/engine_run_R_disagreements/commercial/counter_06253.webp` |
| 6254 | F1 S/switch unmeasurable/L262; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06254.webp` |
| 6257 | F1 S/switch unmeasurable/L261; F1 signature top L23/L24; F2 S/switch unmeasurable/L524 | `reports/engine_run_R_disagreements/commercial/counter_06257.webp` |
| 6259 | F1 S/switch unmeasurable/L261; F1 signature top L23/L24; F2 S/switch unmeasurable/L524 | `reports/engine_run_R_disagreements/commercial/counter_06259.webp` |
| 6260 | F1 H 239/237; F1 c 1/3; F1 signature top L23/L24; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06260.webp` |
| 6261 | F1 H 239/237; F1 c 1/3; F1 signature top L23/L24; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06261.webp` |
| 6262 | F1 H 239/237; F1 c 1/3; F1 signature top L23/L24; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06262.webp` |
| 6263 | F1 H 239/237; F1 c 1/3; F1 signature top L23/L24; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06263.webp` |
| 6264 | F1 H 239/237; F1 c 1/3; F1 signature top L23/L24; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06264.webp` |
| 6265 | F1 H 239/237; F1 c 1/3; F1 signature top L23/L24; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06265.webp` |
| 6266 | F1 H 239/237; F1 c 1/3; F1 signature top L23/L24; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06266.webp` |
| 6267 | F1 H 239/237; F1 c 1/3; F1 signature top L23/L24; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06267.webp` |
| 6268 | F1 H 239/237; F1 S/switch unmeasurable/L262; F1 c 1/3; F1 signature top L23/L24; F2 H 239/238; F2 S/switch unmeasurable/L524; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06268.webp` |
| 6269 | F1 H 239/237; F1 S/switch L240/L261; F1 c 1/3; F2 H 239/238; F2 S/switch L502/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06269.webp` |
| 6270 | F1 H 239/237; F1 S/switch L239/L262; F1 c 1/3; F2 H 239/238; F2 S/switch L512/L522; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06270.webp` |
| 6271 | F1 H 239/237; F1 S/switch L137/L262; F1 c 1/3; F2 H 239/238; F2 S/switch L511/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06271.webp` |
| 6272 | F1 H 239/237; F1 S/switch L115/L262; F1 c 1/3; F2 H 239/238; F2 S/switch L522/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06272.webp` |
| 6273 | F1 H 239/237; F1 S/switch L259/L262; F1 c 1/3; F2 H 239/238; F2 S/switch L522/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06273.webp` |
| 6274 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06274.webp` |
| 6275 | F1 H 239/237; F1 S/switch unmeasurable/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06275.webp` |
| 6276 | F1 H 239/237; F1 S/switch unmeasurable/L258; F1 c 1/3; F2 H 239/238; F2 S/switch unmeasurable/L521; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06276.webp` |
| 6277 | F1 H 239/237; F1 S/switch unmeasurable/L261; F1 c 1/3; F2 H 239/238; F2 S/switch L518/L524; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06277.webp` |
| 6278 | F1 H 239/237; F1 S/switch L194/L261; F1 c 1/3; F2 H 239/238; F2 S/switch L339/L522; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06278.webp` |
| 6279 | F1 H 239/237; F1 S/switch L75/L259; F1 c 1/3; F2 H 239/238; F2 S/switch unmeasurable/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06279.webp` |
| 6280 | F1 H 239/237; F1 S/switch L207/L261; F1 c 1/3; F1 signature top L23/L24; F2 H 239/238; F2 S/switch unmeasurable/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06280.webp` |
| 6281 | F1 H 239/237; F1 S/switch L215/L261; F1 c 1/3; F2 H 239/238; F2 S/switch unmeasurable/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06281.webp` |
| 6282 | F1 H 239/237; F1 S/switch L212/L261; F1 c 1/3; F1 signature top L23/L24; F2 H 239/238; F2 S/switch unmeasurable/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06282.webp` |
| 6283 | F1 H 239/237; F1 S/switch L213/L259; F1 c 1/3; F1 signature top L23/L24; F2 H 239/238; F2 S/switch unmeasurable/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06283.webp` |
| 6284 | F1 H 239/237; F1 S/switch L215/L259; F1 c 1/3; F1 signature top L23/L24; F2 H 239/238; F2 S/switch unmeasurable/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06284.webp` |
| 6285 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 S/switch unmeasurable/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06285.webp` |
| 6286 | F1 H 239/237; F1 S/switch unmeasurable/L262; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06286.webp` |
| 6287 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06287.webp` |
| 6288 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06288.webp` |
| 6289 | F1 H 239/237; F1 S/switch L239/L262; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06289.webp` |
| 6290 | F1 H 239/237; F1 S/switch L136/L262; F1 c 1/3; F2 H 239/238; F2 S/switch L495/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06290.webp` |
| 6291 | F1 H 239/237; F1 S/switch L96/L260; F1 c 1/3; F2 H 239/238; F2 S/switch L495/L523; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06291.webp` |
| 6292 | F1 H 239/237; F1 S/switch L252/L259; F1 c 1/3; F2 H 239/238; F2 S/switch L496/L523; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06292.webp` |
| 6293 | F1 H 239/237; F1 S/switch unmeasurable/L262; F1 c 1/3; F2 H 239/238; F2 S/switch L500/L524; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06293.webp` |
| 6294 | F1 H 239/237; F1 S/switch L102/L262; F1 c 1/3; F2 H 239/238; F2 S/switch L501/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06294.webp` |
| 6295 | F1 H 239/237; F1 S/switch unmeasurable/L261; F1 c 1/3; F2 H 239/238; F2 S/switch L521/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06295.webp` |
| 6296 | F1 H 239/237; F1 S/switch L244/L260; F1 c 1/3; F2 H 239/238; F2 S/switch unmeasurable/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06296.webp` |
| 6297 | F1 H 239/237; F1 S/switch L133/L261; F1 c 1/3; F2 H 239/238; F2 S/switch L429/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06297.webp` |
| 6298 | F1 H 239/237; F1 S/switch L175/L261; F1 c 1/3; F2 H 239/238; F2 S/switch L398/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06298.webp` |
| 6299 | F1 H 239/237; F1 S/switch L149/L262; F1 c 1/3; F2 H 239/238; F2 S/switch L350/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06299.webp` |
| 6300 | F1 H 239/237; F1 S/switch L191/L259; F1 c 1/3; F2 H 239/238; F2 S/switch L454/L522; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06300.webp` |
| 6301 | F1 H 239/237; F1 S/switch L191/L259; F1 c 1/3; F2 H 239/238; F2 S/switch L345/L522; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06301.webp` |
| 6302 | F1 H 239/237; F1 S/switch L165/L262; F1 c 1/3; F2 H 239/238; F2 S/switch L429/L523; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06302.webp` |
| 6303 | F1 H 239/237; F1 S/switch L170/L262; F1 c 1/3; F2 H 239/238; F2 S/switch L415/L523; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06303.webp` |
| 6304 | F1 H 239/237; F1 S/switch L146/L262; F1 c 1/3; F2 H 239/238; F2 S/switch L396/L523; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06304.webp` |
| 6305 | F1 H 239/237; F1 S/switch L137/L259; F1 c 1/3; F2 H 239/238; F2 S/switch L390/L524; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06305.webp` |
| 6306 | F1 H 239/237; F1 S/switch L116/L260; F1 c 1/3; F2 H 239/238; F2 S/switch L379/L523; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06306.webp` |
| 6307 | F1 H 239/237; F1 S/switch L116/L260; F1 c 1/3; F2 H 239/238; F2 S/switch L382/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06307.webp` |
| 6308 | F1 H 239/237; F1 S/switch L114/L262; F1 c 1/3; F2 H 239/238; F2 S/switch L372/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06308.webp` |
| 6309 | F1 H 239/237; F1 S/switch L116/L260; F1 c 1/3; F2 H 239/238; F2 S/switch L372/L524; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06309.webp` |
| 6310 | F1 H 239/237; F1 S/switch L111/L261; F1 c 1/3; F2 H 239/238; F2 S/switch L373/L523; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06310.webp` |
| 6311 | F1 H 239/237; F1 S/switch L107/L262; F1 c 1/3; F2 H 239/238; F2 S/switch L370/L522; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06311.webp` |
| 6312 | F1 H 239/237; F1 S/switch L107/L262; F1 c 1/3; F2 H 239/238; F2 S/switch L370/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06312.webp` |
| 6313 | F1 H 239/237; F1 S/switch L109/L261; F1 c 1/3; F2 H 239/238; F2 S/switch L365/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06313.webp` |
| 6314 | F1 H 239/237; F1 S/switch L108/L261; F1 c 1/3; F2 H 239/238; F2 S/switch unmeasurable/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06314.webp` |
| 6315 | F1 H 239/237; F1 S/switch L121/L261; F1 c 1/3; F2 H 239/238; F2 S/switch L518/L524; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06315.webp` |
| 6316 | F1 H 239/237; F1 S/switch L108/L259; F1 c 1/3; F2 H 239/238; F2 S/switch L520/L524; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06316.webp` |
| 6317 | F1 H 239/237; F1 S/switch L244/L259; F1 c 1/3; F2 H 239/238; F2 S/switch unmeasurable/L521; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06317.webp` |
| 6318 | F1 H 239/237; F1 S/switch L110/L262; F1 c 1/3; F2 H 239/238; F2 S/switch L517/L522; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06318.webp` |
| 6319 | F1 H 239/237; F1 S/switch L111/L259; F1 c 1/3; F2 H 239/238; F2 S/switch unmeasurable/L524; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06319.webp` |
| 6320 | F1 H 239/237; F1 S/switch L256/L261; F1 c 1/3; F2 H 239/238; F2 S/switch L505/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06320.webp` |
| 6321 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 S/switch L519/L523; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06321.webp` |
| 6322 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 S/switch unmeasurable/L522; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06322.webp` |
| 6323 | F1 H 239/237; F1 S/switch unmeasurable/L259; F1 c 1/3; F2 H 239/238; F2 S/switch unmeasurable/L523; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06323.webp` |
| 6324 | F1 H 239/237; F1 S/switch unmeasurable/L258; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06324.webp` |
| 6325 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 S/switch unmeasurable/L524; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06325.webp` |
| 6326 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06326.webp` |
| 6327 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06327.webp` |
| 6328 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06328.webp` |
| 6329 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06329.webp` |
| 6330 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06330.webp` |
| 6331 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06331.webp` |
| 6332 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06332.webp` |
| 6333 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06333.webp` |
| 6334 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06334.webp` |
| 6335 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06335.webp` |
| 6336 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06336.webp` |
| 6337 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06337.webp` |
| 6338 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06338.webp` |
| 6339 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06339.webp` |
| 6340 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06340.webp` |
| 6341 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06341.webp` |
| 6342 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06342.webp` |
| 6343 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06343.webp` |
| 6344 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06344.webp` |
| 6345 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 S/switch unmeasurable/L524; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06345.webp` |
| 6346 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06346.webp` |
| 6347 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06347.webp` |
| 6348 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06348.webp` |
| 6349 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06349.webp` |
| 6350 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06350.webp` |
| 6351 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06351.webp` |
| 6352 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06352.webp` |
| 6353 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06353.webp` |
| 6354 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06354.webp` |
| 6355 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06355.webp` |
| 6356 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06356.webp` |
| 6357 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06357.webp` |
| 6358 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06358.webp` |
| 6359 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06359.webp` |
| 6360 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06360.webp` |
| 6361 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06361.webp` |
| 6362 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06362.webp` |
| 6363 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06363.webp` |
| 6364 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 S/switch L524/L521; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06364.webp` |
| 6365 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 S/switch L524/L522; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06365.webp` |
| 6366 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06366.webp` |
| 6367 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 S/switch unmeasurable/L524; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06367.webp` |
| 6368 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06368.webp` |
| 6369 | F1 H 239/237; F1 S/switch unmeasurable/L261; F1 c 1/3; F2 H 239/238; F2 S/switch unmeasurable/L525; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06369.webp` |
| 6370 | F1 H 239/237; F1 S/switch unmeasurable/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06370.webp` |
| 6371 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06371.webp` |
| 6372 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06372.webp` |
| 6373 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06373.webp` |
| 6374 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06374.webp` |
| 6375 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06375.webp` |
| 6376 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06376.webp` |
| 6377 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06377.webp` |
| 6378 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06378.webp` |
| 6379 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06379.webp` |
| 6380 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06380.webp` |
| 6381 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06381.webp` |
| 6382 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06382.webp` |
| 6383 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06383.webp` |
| 6384 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06384.webp` |
| 6385 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06385.webp` |
| 6386 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06386.webp` |
| 6387 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06387.webp` |
| 6388 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06388.webp` |
| 6389 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06389.webp` |
| 6390 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06390.webp` |
| 6391 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06391.webp` |
| 6392 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06392.webp` |
| 6393 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06393.webp` |
| 6394 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06394.webp` |
| 6395 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06395.webp` |
| 6396 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06396.webp` |
| 6397 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06397.webp` |
| 6398 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06398.webp` |
| 6399 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06399.webp` |
| 6400 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06400.webp` |
| 6401 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06401.webp` |
| 6402 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06402.webp` |
| 6403 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06403.webp` |
| 6404 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06404.webp` |
| 6405 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06405.webp` |
| 6406 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06406.webp` |
| 6407 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06407.webp` |
| 6408 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06408.webp` |
| 6409 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06409.webp` |
| 6410 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06410.webp` |
| 6411 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06411.webp` |
| 6412 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06412.webp` |
| 6413 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06413.webp` |
| 6414 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06414.webp` |
| 6415 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06415.webp` |
| 6416 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06416.webp` |
| 6417 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06417.webp` |
| 6418 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06418.webp` |
| 6419 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06419.webp` |
| 6420 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06420.webp` |
| 6421 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06421.webp` |
| 6422 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06422.webp` |
| 6423 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06423.webp` |
| 6424 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06424.webp` |
| 6425 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06425.webp` |
| 6426 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06426.webp` |
| 6427 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06427.webp` |
| 6428 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06428.webp` |
| 6429 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06429.webp` |
| 6430 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06430.webp` |
| 6431 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06431.webp` |
| 6432 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06432.webp` |
| 6433 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06433.webp` |
| 6434 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06434.webp` |
| 6435 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06435.webp` |
| 6436 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06436.webp` |
| 6437 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06437.webp` |
| 6438 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06438.webp` |
| 6439 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06439.webp` |
| 6440 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06440.webp` |
| 6441 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06441.webp` |
| 6442 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06442.webp` |
| 6443 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06443.webp` |
| 6444 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06444.webp` |
| 6445 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06445.webp` |
| 6446 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06446.webp` |
| 6447 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06447.webp` |
| 6448 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06448.webp` |
| 6449 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06449.webp` |
| 6450 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06450.webp` |
| 6451 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06451.webp` |
| 6452 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06452.webp` |
| 6453 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06453.webp` |
| 6454 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06454.webp` |
| 6455 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06455.webp` |
| 6456 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06456.webp` |
| 6457 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06457.webp` |
| 6458 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06458.webp` |
| 6459 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06459.webp` |
| 6460 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06460.webp` |
| 6461 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06461.webp` |
| 6462 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06462.webp` |
| 6463 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06463.webp` |
| 6464 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06464.webp` |
| 6465 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06465.webp` |
| 6466 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06466.webp` |
| 6467 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06467.webp` |
| 6468 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06468.webp` |
| 6469 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06469.webp` |
| 6470 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06470.webp` |
| 6471 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06471.webp` |
| 6472 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06472.webp` |
| 6473 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06473.webp` |
| 6474 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06474.webp` |
| 6475 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06475.webp` |
| 6476 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06476.webp` |
| 6477 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06477.webp` |
| 6478 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06478.webp` |
| 6479 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06479.webp` |
| 6480 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06480.webp` |
| 6481 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06481.webp` |
| 6482 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06482.webp` |
| 6483 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06483.webp` |
| 6484 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06484.webp` |
| 6485 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06485.webp` |
| 6486 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06486.webp` |
| 6487 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06487.webp` |
| 6488 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06488.webp` |
| 6489 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06489.webp` |
| 6490 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06490.webp` |
| 6491 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06491.webp` |
| 6492 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06492.webp` |
| 6493 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06493.webp` |
| 6494 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06494.webp` |
| 6495 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06495.webp` |
| 6496 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06496.webp` |
| 6497 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06497.webp` |
| 6498 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06498.webp` |
| 6499 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06499.webp` |
| 6500 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06500.webp` |
| 6501 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06501.webp` |
| 6502 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06502.webp` |
| 6503 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06503.webp` |
| 6504 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06504.webp` |
| 6505 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06505.webp` |
| 6506 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06506.webp` |
| 6507 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06507.webp` |
| 6508 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06508.webp` |
| 6509 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06509.webp` |
| 6510 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06510.webp` |
| 6511 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06511.webp` |
| 6512 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06512.webp` |
| 6513 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06513.webp` |
| 6514 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06514.webp` |
| 6515 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06515.webp` |
| 6516 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06516.webp` |
| 6517 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06517.webp` |
| 6518 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06518.webp` |
| 6519 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06519.webp` |
| 6520 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06520.webp` |
| 6521 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06521.webp` |
| 6522 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06522.webp` |
| 6523 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06523.webp` |
| 6524 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06524.webp` |
| 6525 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06525.webp` |
| 6526 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06526.webp` |
| 6527 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06527.webp` |
| 6528 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06528.webp` |
| 6529 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06529.webp` |
| 6530 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06530.webp` |
| 6531 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06531.webp` |
| 6532 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06532.webp` |
| 6533 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06533.webp` |
| 6534 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06534.webp` |
| 6535 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06535.webp` |
| 6536 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06536.webp` |
| 6537 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06537.webp` |
| 6538 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06538.webp` |
| 6539 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06539.webp` |
| 6540 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06540.webp` |
| 6541 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06541.webp` |
| 6542 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06542.webp` |
| 6543 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06543.webp` |
| 6544 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06544.webp` |
| 6545 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06545.webp` |
| 6546 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06546.webp` |
| 6547 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06547.webp` |
| 6548 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06548.webp` |
| 6549 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06549.webp` |
| 6550 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06550.webp` |
| 6551 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06551.webp` |
| 6552 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06552.webp` |
| 6553 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06553.webp` |
| 6554 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06554.webp` |
| 6555 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06555.webp` |
| 6556 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06556.webp` |
| 6557 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06557.webp` |
| 6558 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06558.webp` |
| 6559 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06559.webp` |
| 6560 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06560.webp` |
| 6561 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06561.webp` |
| 6562 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06562.webp` |
| 6563 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06563.webp` |
| 6564 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06564.webp` |
| 6565 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06565.webp` |
| 6566 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06566.webp` |
| 6567 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06567.webp` |
| 6568 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06568.webp` |
| 6569 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06569.webp` |
| 6570 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06570.webp` |
| 6571 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06571.webp` |
| 6572 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06572.webp` |
| 6573 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06573.webp` |
| 6574 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06574.webp` |
| 6575 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06575.webp` |
| 6576 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06576.webp` |
| 6577 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06577.webp` |
| 6578 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06578.webp` |
| 6579 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06579.webp` |
| 6580 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06580.webp` |
| 6581 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06581.webp` |
| 6582 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06582.webp` |
| 6583 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06583.webp` |
| 6584 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06584.webp` |
| 6585 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06585.webp` |
| 6586 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06586.webp` |
| 6587 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06587.webp` |
| 6588 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06588.webp` |
| 6589 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06589.webp` |
| 6590 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06590.webp` |
| 6591 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06591.webp` |
| 6592 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06592.webp` |
| 6593 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06593.webp` |
| 6594 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06594.webp` |
| 6595 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06595.webp` |
| 6596 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06596.webp` |
| 6597 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06597.webp` |
| 6598 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06598.webp` |
| 6599 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06599.webp` |
| 6600 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06600.webp` |
| 6601 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06601.webp` |
| 6602 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06602.webp` |
| 6603 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06603.webp` |
| 6604 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06604.webp` |
| 6605 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06605.webp` |
| 6606 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06606.webp` |
| 6607 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06607.webp` |
| 6608 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06608.webp` |
| 6609 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06609.webp` |
| 6610 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06610.webp` |
| 6611 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06611.webp` |
| 6612 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06612.webp` |
| 6613 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06613.webp` |
| 6614 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06614.webp` |
| 6615 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06615.webp` |
| 6616 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06616.webp` |
| 6617 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06617.webp` |
| 6618 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06618.webp` |
| 6619 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06619.webp` |
| 6620 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06620.webp` |
| 6621 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06621.webp` |
| 6622 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06622.webp` |
| 6623 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06623.webp` |
| 6624 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06624.webp` |
| 6625 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06625.webp` |
| 6626 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06626.webp` |
| 6627 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06627.webp` |
| 6628 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06628.webp` |
| 6629 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06629.webp` |
| 6630 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06630.webp` |
| 6631 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06631.webp` |
| 6632 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06632.webp` |
| 6633 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06633.webp` |
| 6634 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06634.webp` |
| 6635 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06635.webp` |
| 6636 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06636.webp` |
| 6637 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06637.webp` |
| 6638 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06638.webp` |
| 6639 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06639.webp` |
| 6640 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06640.webp` |
| 6641 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06641.webp` |
| 6642 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06642.webp` |
| 6643 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06643.webp` |
| 6644 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06644.webp` |
| 6645 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06645.webp` |
| 6646 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06646.webp` |
| 6647 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06647.webp` |
| 6648 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287; engine decisive comb -3 at placed crops (ratio 0.580) | `reports/engine_run_R_disagreements/commercial/counter_06648.webp` |
| 6649 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06649.webp` |
| 6650 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287; engine decisive comb -3 at placed crops (ratio 0.700) | `reports/engine_run_R_disagreements/commercial/counter_06650.webp` |
| 6651 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06651.webp` |
| 6652 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06652.webp` |
| 6653 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06653.webp` |
| 6654 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06654.webp` |
| 6655 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06655.webp` |
| 6656 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06656.webp` |
| 6657 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06657.webp` |
| 6658 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06658.webp` |
| 6659 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06659.webp` |
| 6660 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06660.webp` |
| 6661 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06661.webp` |
| 6662 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06662.webp` |
| 6663 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06663.webp` |
| 6664 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06664.webp` |
| 6665 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06665.webp` |
| 6666 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06666.webp` |
| 6667 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06667.webp` |
| 6668 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06668.webp` |
| 6669 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06669.webp` |
| 6670 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06670.webp` |
| 6671 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06671.webp` |
| 6672 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06672.webp` |
| 6673 | F1 H 239/237; F1 c 1/3; F1 signature top L23/L25; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06673.webp` |
| 6674 | F1 H 239/237; F1 c 1/3; F1 signature top L23/L25; F2 H 239/238; F2 S/first-full unmeasurable/L523; F2 S/switch unmeasurable/L522; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06674.webp` |
| 6675 | F1 H 239/237; F1 c 1/3; F1 signature top L23/L25; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06675.webp` |
| 6676 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06676.webp` |
| 6677 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06677.webp` |
| 6678 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06678.webp` |
| 6679 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06679.webp` |
| 6680 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06680.webp` |
| 6681 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06681.webp` |
| 6682 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06682.webp` |
| 6683 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06683.webp` |
| 6684 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06684.webp` |
| 6685 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06685.webp` |
| 6686 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06686.webp` |
| 6687 | F1 H 239/237; F1 S/first-full L261/L260; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06687.webp` |
| 6688 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06688.webp` |
| 6689 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06689.webp` |
| 6690 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06690.webp` |
| 6691 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06691.webp` |
| 6692 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06692.webp` |
| 6693 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06693.webp` |
| 6694 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06694.webp` |
| 6695 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06695.webp` |
| 6696 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06696.webp` |
| 6697 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06697.webp` |
| 6698 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 S/first-full L524/L523; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06698.webp` |
| 6699 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06699.webp` |
| 6700 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06700.webp` |
| 6701 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06701.webp` |
| 6702 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06702.webp` |
| 6703 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06703.webp` |
| 6704 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06704.webp` |
| 6705 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06705.webp` |
| 6706 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06706.webp` |
| 6707 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06707.webp` |
| 6708 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06708.webp` |
| 6709 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06709.webp` |
| 6710 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06710.webp` |
| 6711 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06711.webp` |
| 6712 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06712.webp` |
| 6713 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06713.webp` |
| 6714 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06714.webp` |
| 6715 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06715.webp` |
| 6716 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06716.webp` |
| 6717 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06717.webp` |
| 6718 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06718.webp` |
| 6719 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06719.webp` |
| 6720 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06720.webp` |
| 6721 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06721.webp` |
| 6722 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06722.webp` |
| 6723 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06723.webp` |
| 6724 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06724.webp` |
| 6725 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06725.webp` |
| 6726 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06726.webp` |
| 6727 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06727.webp` |
| 6728 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06728.webp` |
| 6729 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06729.webp` |
| 6730 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06730.webp` |
| 6731 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06731.webp` |
| 6732 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06732.webp` |
| 6733 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06733.webp` |
| 6734 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06734.webp` |
| 6735 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06735.webp` |
| 6736 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06736.webp` |
| 6737 | F1 H 239/237; F1 S/first-full L261/L260; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06737.webp` |
| 6738 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06738.webp` |
| 6739 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06739.webp` |
| 6740 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06740.webp` |
| 6741 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06741.webp` |
| 6742 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06742.webp` |
| 6743 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06743.webp` |
| 6744 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06744.webp` |
| 6745 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06745.webp` |
| 6746 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06746.webp` |
| 6747 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06747.webp` |
| 6748 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06748.webp` |
| 6749 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 S/first-full L524/L523; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06749.webp` |
| 6750 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06750.webp` |
| 6751 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06751.webp` |
| 6752 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06752.webp` |
| 6753 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06753.webp` |
| 6754 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 S/first-full L524/L523; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06754.webp` |
| 6755 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06755.webp` |
| 6756 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06756.webp` |
| 6757 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06757.webp` |
| 6758 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06758.webp` |
| 6759 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06759.webp` |
| 6760 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06760.webp` |
| 6761 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06761.webp` |
| 6762 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06762.webp` |
| 6763 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06763.webp` |
| 6764 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06764.webp` |
| 6765 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06765.webp` |
| 6766 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06766.webp` |
| 6767 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06767.webp` |
| 6768 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06768.webp` |
| 6769 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06769.webp` |
| 6770 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06770.webp` |
| 6771 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06771.webp` |
| 6772 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06772.webp` |
| 6773 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06773.webp` |
| 6774 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06774.webp` |
| 6775 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06775.webp` |
| 6776 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 S/first-full unmeasurable/L523; F2 S/switch unmeasurable/L522; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06776.webp` |
| 6777 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06777.webp` |
| 6778 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06778.webp` |
| 6779 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06779.webp` |
| 6780 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06780.webp` |
| 6781 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06781.webp` |
| 6782 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06782.webp` |
| 6783 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06783.webp` |
| 6784 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06784.webp` |
| 6785 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06785.webp` |
| 6786 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06786.webp` |
| 6787 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06787.webp` |
| 6788 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06788.webp` |
| 6789 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06789.webp` |
| 6790 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06790.webp` |
| 6791 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06791.webp` |
| 6792 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06792.webp` |
| 6793 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06793.webp` |
| 6794 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06794.webp` |
| 6795 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06795.webp` |
| 6796 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06796.webp` |
| 6797 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06797.webp` |
| 6798 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06798.webp` |
| 6799 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06799.webp` |
| 6800 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06800.webp` |
| 6801 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06801.webp` |
| 6802 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06802.webp` |
| 6803 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06803.webp` |
| 6804 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06804.webp` |
| 6805 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06805.webp` |
| 6806 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06806.webp` |
| 6807 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06807.webp` |
| 6808 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06808.webp` |
| 6809 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06809.webp` |
| 6810 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06810.webp` |
| 6811 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06811.webp` |
| 6812 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287; engine decisive comb -2 at placed crops (ratio 0.710) | `reports/engine_run_R_disagreements/commercial/counter_06812.webp` |
| 6813 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06813.webp` |
| 6814 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06814.webp` |
| 6815 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06815.webp` |
| 6816 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06816.webp` |
| 6817 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06817.webp` |
| 6818 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06818.webp` |
| 6819 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06819.webp` |
| 6820 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; F2 signature top L286/L287 | `reports/engine_run_R_disagreements/commercial/counter_06820.webp` |
| 6821 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06821.webp` |
| 6822 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06822.webp` |
| 6823 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06823.webp` |
| 6824 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06824.webp` |
| 6825 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06825.webp` |
| 6826 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06826.webp` |
| 6827 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06827.webp` |
| 6828 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06828.webp` |
| 6829 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06829.webp` |
| 6830 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06830.webp` |
| 6831 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06831.webp` |
| 6832 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06832.webp` |
| 6833 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06833.webp` |
| 6834 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06834.webp` |
| 6835 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06835.webp` |
| 6836 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06836.webp` |
| 6837 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06837.webp` |
| 6838 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06838.webp` |
| 6839 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06839.webp` |
| 6840 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06840.webp` |
| 6841 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06841.webp` |
| 6842 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06842.webp` |
| 6843 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06843.webp` |
| 6844 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06844.webp` |
| 6845 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06845.webp` |
| 6846 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06846.webp` |
| 6847 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06847.webp` |
| 6848 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06848.webp` |
| 6849 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06849.webp` |
| 6850 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06850.webp` |
| 6851 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06851.webp` |
| 6852 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06852.webp` |
| 6853 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06853.webp` |
| 6854 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06854.webp` |
| 6855 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06855.webp` |
| 6856 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06856.webp` |
| 6857 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06857.webp` |
| 6858 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06858.webp` |
| 6859 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06859.webp` |
| 6860 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06860.webp` |
| 6861 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06861.webp` |
| 6862 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06862.webp` |
| 6863 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 S/first-full unmeasurable/L523; F2 S/switch unmeasurable/L523; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06863.webp` |
| 6864 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06864.webp` |
| 6865 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06865.webp` |
| 6866 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06866.webp` |
| 6867 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06867.webp` |
| 6868 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06868.webp` |
| 6869 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06869.webp` |
| 6870 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06870.webp` |
| 6871 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06871.webp` |
| 6872 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06872.webp` |
| 6873 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06873.webp` |
| 6874 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06874.webp` |
| 6875 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06875.webp` |
| 6876 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06876.webp` |
| 6877 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2; engine decisive comb -3 at placed crops (ratio 0.780) | `reports/engine_run_R_disagreements/commercial/counter_06877.webp` |
| 6878 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06878.webp` |
| 6879 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06879.webp` |
| 6880 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 S/first-full L522/L523; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06880.webp` |
| 6881 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06881.webp` |
| 6882 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06882.webp` |
| 6883 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06883.webp` |
| 6884 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06884.webp` |
| 6885 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06885.webp` |
| 6886 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06886.webp` |
| 6887 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06887.webp` |
| 6888 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06888.webp` |
| 6889 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06889.webp` |
| 6890 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06890.webp` |
| 6891 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06891.webp` |
| 6892 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06892.webp` |
| 6893 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06893.webp` |
| 6894 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06894.webp` |
| 6895 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06895.webp` |
| 6896 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06896.webp` |
| 6897 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06897.webp` |
| 6898 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06898.webp` |
| 6899 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06899.webp` |
| 6900 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06900.webp` |
| 6901 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06901.webp` |
| 6902 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06902.webp` |
| 6903 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06903.webp` |
| 6904 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06904.webp` |
| 6905 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06905.webp` |
| 6906 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06906.webp` |
| 6907 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06907.webp` |
| 6908 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06908.webp` |
| 6909 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06909.webp` |
| 6910 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06910.webp` |
| 6911 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06911.webp` |
| 6912 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06912.webp` |
| 6913 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06913.webp` |
| 6914 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06914.webp` |
| 6915 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06915.webp` |
| 6916 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06916.webp` |
| 6917 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06917.webp` |
| 6918 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06918.webp` |
| 6919 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06919.webp` |
| 6920 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06920.webp` |
| 6921 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06921.webp` |
| 6922 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06922.webp` |
| 6923 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06923.webp` |
| 6924 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06924.webp` |
| 6925 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06925.webp` |
| 6926 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06926.webp` |
| 6927 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06927.webp` |
| 6928 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06928.webp` |
| 6929 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06929.webp` |
| 6930 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06930.webp` |
| 6931 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 S/first-full L522/L523; F2 c 1/2; engine decisive comb +2 at placed crops (ratio 0.800) | `reports/engine_run_R_disagreements/commercial/counter_06931.webp` |
| 6932 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06932.webp` |
| 6933 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 S/first-full L522/L523; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06933.webp` |
| 6934 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06934.webp` |
| 6935 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06935.webp` |
| 6936 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06936.webp` |
| 6937 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06937.webp` |
| 6938 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06938.webp` |
| 6939 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06939.webp` |
| 6940 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06940.webp` |
| 6941 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06941.webp` |
| 6942 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06942.webp` |
| 6943 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06943.webp` |
| 6944 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06944.webp` |
| 6945 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06945.webp` |
| 6946 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06946.webp` |
| 6947 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06947.webp` |
| 6948 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06948.webp` |
| 6949 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06949.webp` |
| 6950 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06950.webp` |
| 6951 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06951.webp` |
| 6952 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06952.webp` |
| 6953 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06953.webp` |
| 6954 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06954.webp` |
| 6955 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06955.webp` |
| 6956 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06956.webp` |
| 6957 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06957.webp` |
| 6958 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06958.webp` |
| 6959 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06959.webp` |
| 6960 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06960.webp` |
| 6961 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06961.webp` |
| 6962 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06962.webp` |
| 6963 | F1 H 239/237; F1 S/first-full L260/L261; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06963.webp` |
| 6964 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06964.webp` |
| 6965 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06965.webp` |
| 6966 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06966.webp` |
| 6967 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06967.webp` |
| 6968 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06968.webp` |
| 6969 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06969.webp` |
| 6970 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06970.webp` |
| 6971 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06971.webp` |
| 6972 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06972.webp` |
| 6973 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06973.webp` |
| 6974 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06974.webp` |
| 6975 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06975.webp` |
| 6976 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06976.webp` |
| 6977 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06977.webp` |
| 6978 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06978.webp` |
| 6979 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06979.webp` |
| 6980 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06980.webp` |
| 6981 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06981.webp` |
| 6982 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06982.webp` |
| 6983 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06983.webp` |
| 6984 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06984.webp` |
| 6985 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06985.webp` |
| 6986 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06986.webp` |
| 6987 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06987.webp` |
| 6988 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06988.webp` |
| 6989 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06989.webp` |
| 6990 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06990.webp` |
| 6991 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06991.webp` |
| 6992 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06992.webp` |
| 6993 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06993.webp` |
| 6994 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06994.webp` |
| 6995 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06995.webp` |
| 6996 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06996.webp` |
| 6997 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06997.webp` |
| 6998 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06998.webp` |
| 6999 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_06999.webp` |
| 7000 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07000.webp` |
| 7001 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07001.webp` |
| 7002 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07002.webp` |
| 7003 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07003.webp` |
| 7004 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07004.webp` |
| 7005 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07005.webp` |
| 7006 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07006.webp` |
| 7007 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07007.webp` |
| 7008 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07008.webp` |
| 7009 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07009.webp` |
| 7010 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07010.webp` |
| 7011 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07011.webp` |
| 7012 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07012.webp` |
| 7013 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07013.webp` |
| 7014 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07014.webp` |
| 7015 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07015.webp` |
| 7016 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07016.webp` |
| 7017 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07017.webp` |
| 7018 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07018.webp` |
| 7019 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07019.webp` |
| 7020 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07020.webp` |
| 7021 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07021.webp` |
| 7022 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07022.webp` |
| 7023 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07023.webp` |
| 7024 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07024.webp` |
| 7025 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07025.webp` |
| 7026 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07026.webp` |
| 7027 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07027.webp` |
| 7028 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07028.webp` |
| 7029 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07029.webp` |
| 7030 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07030.webp` |
| 7031 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07031.webp` |
| 7032 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07032.webp` |
| 7033 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07033.webp` |
| 7034 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07034.webp` |
| 7035 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07035.webp` |
| 7036 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07036.webp` |
| 7037 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07037.webp` |
| 7038 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07038.webp` |
| 7039 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07039.webp` |
| 7040 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07040.webp` |
| 7041 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07041.webp` |
| 7042 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07042.webp` |
| 7043 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07043.webp` |
| 7044 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07044.webp` |
| 7045 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07045.webp` |
| 7046 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07046.webp` |
| 7047 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07047.webp` |
| 7048 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07048.webp` |
| 7049 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07049.webp` |
| 7050 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07050.webp` |
| 7051 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07051.webp` |
| 7052 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07052.webp` |
| 7053 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07053.webp` |
| 7054 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07054.webp` |
| 7055 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07055.webp` |
| 7056 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07056.webp` |
| 7057 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07057.webp` |
| 7058 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07058.webp` |
| 7059 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07059.webp` |
| 7060 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07060.webp` |
| 7061 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07061.webp` |
| 7062 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07062.webp` |
| 7063 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07063.webp` |
| 7064 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07064.webp` |
| 7065 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07065.webp` |
| 7066 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07066.webp` |
| 7067 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07067.webp` |
| 7068 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07068.webp` |
| 7069 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07069.webp` |
| 7070 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07070.webp` |
| 7071 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07071.webp` |
| 7072 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07072.webp` |
| 7073 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07073.webp` |
| 7074 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07074.webp` |
| 7075 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07075.webp` |
| 7076 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07076.webp` |
| 7077 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07077.webp` |
| 7078 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07078.webp` |
| 7079 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07079.webp` |
| 7080 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07080.webp` |
| 7081 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07081.webp` |
| 7082 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07082.webp` |
| 7083 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07083.webp` |
| 7084 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07084.webp` |
| 7085 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07085.webp` |
| 7086 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07086.webp` |
| 7087 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07087.webp` |
| 7088 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07088.webp` |
| 7089 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07089.webp` |
| 7090 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07090.webp` |
| 7091 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07091.webp` |
| 7092 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07092.webp` |
| 7093 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07093.webp` |
| 7094 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07094.webp` |
| 7095 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07095.webp` |
| 7096 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07096.webp` |
| 7097 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07097.webp` |
| 7098 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07098.webp` |
| 7099 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07099.webp` |
| 7100 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07100.webp` |
| 7101 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07101.webp` |
| 7102 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07102.webp` |
| 7103 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07103.webp` |
| 7104 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07104.webp` |
| 7105 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07105.webp` |
| 7106 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07106.webp` |
| 7107 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07107.webp` |
| 7108 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07108.webp` |
| 7109 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07109.webp` |
| 7110 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07110.webp` |
| 7111 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07111.webp` |
| 7112 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07112.webp` |
| 7113 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07113.webp` |
| 7114 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07114.webp` |
| 7115 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07115.webp` |
| 7116 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07116.webp` |
| 7117 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07117.webp` |
| 7118 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07118.webp` |
| 7119 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07119.webp` |
| 7120 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07120.webp` |
| 7121 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07121.webp` |
| 7122 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07122.webp` |
| 7123 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07123.webp` |
| 7124 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07124.webp` |
| 7125 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07125.webp` |
| 7126 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07126.webp` |
| 7127 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07127.webp` |
| 7128 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07128.webp` |
| 7129 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07129.webp` |
| 7130 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07130.webp` |
| 7131 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07131.webp` |
| 7132 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07132.webp` |
| 7133 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07133.webp` |
| 7134 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07134.webp` |
| 7135 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07135.webp` |
| 7136 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07136.webp` |
| 7137 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07137.webp` |
| 7138 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07138.webp` |
| 7139 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07139.webp` |
| 7140 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07140.webp` |
| 7141 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07141.webp` |
| 7142 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07142.webp` |
| 7143 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07143.webp` |
| 7144 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07144.webp` |
| 7145 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07145.webp` |
| 7146 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07146.webp` |
| 7147 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07147.webp` |
| 7148 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07148.webp` |
| 7149 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07149.webp` |
| 7150 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07150.webp` |
| 7151 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07151.webp` |
| 7152 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07152.webp` |
| 7153 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07153.webp` |
| 7154 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07154.webp` |
| 7155 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07155.webp` |
| 7156 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07156.webp` |
| 7157 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07157.webp` |
| 7158 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07158.webp` |
| 7159 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07159.webp` |
| 7160 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07160.webp` |
| 7161 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07161.webp` |
| 7162 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07162.webp` |
| 7163 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07163.webp` |
| 7164 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07164.webp` |
| 7165 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07165.webp` |
| 7166 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07166.webp` |
| 7167 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07167.webp` |
| 7168 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07168.webp` |
| 7169 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07169.webp` |
| 7170 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07170.webp` |
| 7171 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07171.webp` |
| 7172 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07172.webp` |
| 7173 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07173.webp` |
| 7174 | F1 H 239/237; F1 c 1/3; F2 H 239/238; F2 c 1/2 | `reports/engine_run_R_disagreements/commercial/counter_07174.webp` |

## Picture top

### Engine field 1

Agreement histogram (engine minus reference): -2: 3, -1: 15, +0: 901

| engine counter | raw counter/field | engine | reference | verdict | raw top rows |
|---:|:---:|:---|:---|:---|:---|
| 6257 | 6257/F1 | L23 | L24 | reference (first structured/dark-picture row) | waveforms=[21]; L23 4.88/1.07 r_next=0.001 MAD_above=3.51 lag=-32(3.48/3.51); L24 25.82/1.09 r_next=0.351 MAD_above=20.94 lag=-32(20.90/20.94); L25 25.32/1.11 r_next=0.403 MAD_above=1.14 lag=9(1.12/1.14) |
| 6259 | 6259/F1 | L23 | L24 | reference (first structured/dark-picture row) | waveforms=[21]; L23 4.88/1.04 r_next=-0.009 MAD_above=3.48 lag=-31(3.48/3.48); L24 25.77/1.10 r_next=0.357 MAD_above=20.89 lag=-32(20.87/20.89); L25 25.20/1.21 r_next=0.450 MAD_above=1.21 lag=32(1.16/1.21) |
| 6260 | 6260/F1 | L23 | L24 | reference (first structured/dark-picture row) | waveforms=[21]; L23 4.47/0.97 r_next=-0.015 MAD_above=3.10 lag=-32(3.08/3.10); L24 25.55/1.10 r_next=0.343 MAD_above=21.08 lag=-32(21.02/21.08); L25 24.97/1.19 r_next=0.454 MAD_above=1.21 lag=10(1.16/1.21) |
| 6261 | 6261/F1 | L23 | L24 | reference (first structured/dark-picture row) | waveforms=[21]; L23 4.80/0.94 r_next=0.018 MAD_above=3.41 lag=-32(3.39/3.41); L24 25.90/1.13 r_next=0.357 MAD_above=21.10 lag=-24(21.06/21.10); L25 25.54/1.13 r_next=0.431 MAD_above=1.15 lag=14(1.10/1.15) |
| 6262 | 6262/F1 | L23 | L24 | reference (first structured/dark-picture row) | waveforms=[21]; L23 4.70/0.89 r_next=0.041 MAD_above=3.35 lag=-32(3.34/3.35); L24 25.65/1.17 r_next=0.367 MAD_above=20.95 lag=-27(20.92/20.95); L25 25.17/1.10 r_next=0.389 MAD_above=1.13 lag=5(1.08/1.13) |
| 6263 | 6263/F1 | L23 | L24 | reference (first structured/dark-picture row) | waveforms=[21]; L23 4.80/0.95 r_next=0.076 MAD_above=3.43 lag=0(3.43/3.43); L24 25.83/1.13 r_next=0.288 MAD_above=21.03 lag=-32(21.01/21.03); L25 25.31/1.27 r_next=0.446 MAD_above=1.22 lag=27(1.21/1.22) |
| 6264 | 6264/F1 | L23 | L24 | reference (first structured/dark-picture row) | waveforms=[21]; L23 4.67/0.91 r_next=0.098 MAD_above=3.29 lag=-32(3.28/3.29); L24 25.63/1.16 r_next=0.372 MAD_above=20.96 lag=-25(20.93/20.96); L25 25.16/1.14 r_next=0.341 MAD_above=1.17 lag=-6(1.13/1.17) |
| 6265 | 6265/F1 | L23 | L24 | reference (first structured/dark-picture row) | waveforms=[21]; L23 4.83/1.00 r_next=0.102 MAD_above=3.45 lag=17(3.44/3.45); L24 25.99/1.05 r_next=0.412 MAD_above=21.15 lag=0(21.15/21.15); L25 25.72/1.19 r_next=0.392 MAD_above=1.11 lag=-32(1.01/1.11) |
| 6266 | 6266/F1 | L23 | L24 | reference (first structured/dark-picture row) | waveforms=[21]; L23 5.30/1.00 r_next=0.075 MAD_above=3.92 lag=-29(3.91/3.92); L24 26.70/1.06 r_next=0.365 MAD_above=21.40 lag=0(21.40/21.40); L25 26.17/1.18 r_next=0.428 MAD_above=1.20 lag=-25(1.09/1.20) |
| 6267 | 6267/F1 | L23 | L24 | reference (first structured/dark-picture row) | waveforms=[21]; L23 5.05/1.04 r_next=-0.021 MAD_above=3.68 lag=-31(3.66/3.68); L24 26.34/1.03 r_next=0.392 MAD_above=21.29 lag=-1(21.29/21.29); L25 26.02/1.20 r_next=0.340 MAD_above=1.10 lag=-4(1.03/1.10) |
| 6268 | 6268/F1 | L23 | L24 | reference (first structured/dark-picture row) | waveforms=[21]; L23 5.17/1.16 r_next=0.075 MAD_above=3.82 lag=-32(3.79/3.82); L24 26.64/1.43 r_next=0.291 MAD_above=21.46 lag=-23(21.41/21.46); L25 26.11/1.19 r_next=0.307 MAD_above=1.42 lag=28(1.31/1.42) |
| 6280 | 6280/F1 | L23 | L24 | reference (first structured/dark-picture row) | waveforms=[21, 23]; L23 2.02/1.23 r_next=0.031 MAD_above=0.93 lag=-23(0.90/0.93); L24 17.65/1.43 r_next=0.003 MAD_above=15.63 lag=14(15.59/15.63); L25 17.00/1.40 r_next=0.044 MAD_above=1.67 lag=32(1.47/1.67) |
| 6282 | 6282/F1 | L23 | L24 | reference (first structured/dark-picture row) | waveforms=[21]; L23 4.30/1.44 r_next=-0.086 MAD_above=2.94 lag=32(2.89/2.94); L24 21.45/1.49 r_next=0.032 MAD_above=17.14 lag=-7(17.12/17.14); L25 19.79/1.47 r_next=0.064 MAD_above=2.18 lag=5(2.07/2.18) |
| 6283 | 6283/F1 | L23 | L24 | reference (first structured/dark-picture row) | waveforms=[21]; L23 4.28/1.36 r_next=-0.000 MAD_above=2.91 lag=17(2.89/2.91); L24 21.58/1.30 r_next=0.009 MAD_above=17.31 lag=32(17.30/17.31); L25 20.59/1.32 r_next=0.150 MAD_above=1.71 lag=25(1.54/1.71) |
| 6284 | 6284/F1 | L23 | L24 | reference (first structured/dark-picture row) | waveforms=[21]; L23 4.80/1.34 r_next=-0.098 MAD_above=3.43 lag=20(3.41/3.43); L24 22.82/1.43 r_next=0.011 MAD_above=18.02 lag=28(18.00/18.02); L25 21.44/1.17 r_next=-0.048 MAD_above=1.83 lag=23(1.71/1.83) |
| 6673 | 6673/F1 | L23 | L25 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[21]; L23 4.38/3.33 r_next=-0.541 MAD_above=3.12 lag=27(2.92/3.12); L24 6.78/5.72 r_next=-0.442 MAD_above=6.94 lag=-32(6.38/6.94); L25 16.74/3.84 r_next=0.082 MAD_above=10.77 lag=-30(10.74/10.77); L26 14.39/3.16 r_next=0.094 MAD_above=4.29 lag=-28(3.93/4.29) |
| 6674 | 6674/F1 | L23 | L25 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[21]; L23 4.50/3.29 r_next=-0.458 MAD_above=3.27 lag=21(3.11/3.27); L24 6.16/5.09 r_next=-0.500 MAD_above=6.14 lag=-30(5.67/6.14); L25 15.34/4.03 r_next=0.143 MAD_above=10.25 lag=-22(9.90/10.25); L26 13.41/3.40 r_next=0.130 MAD_above=4.20 lag=-32(3.92/4.20) |
| 6675 | 6675/F1 | L23 | L25 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[21]; L23 4.42/3.55 r_next=-0.320 MAD_above=3.18 lag=28(3.03/3.18); L24 5.82/5.17 r_next=-0.283 MAD_above=5.63 lag=-22(5.30/5.63); L25 13.43/4.65 r_next=0.192 MAD_above=9.14 lag=-13(9.09/9.14); L26 11.66/3.80 r_next=0.082 MAD_above=4.42 lag=14(4.34/4.42) |

### Engine field 2

Agreement histogram (engine minus reference): -1: 172, +0: 747

| engine counter | raw counter/field | engine | reference | verdict | raw top rows |
|---:|:---:|:---|:---|:---|:---|
| 6254 | 6254/F2 | L286 | L287 | reference (first structured/dark-picture row) | waveforms=[284]; L286 5.28/1.01 r_next=-0.047 MAD_above=3.93 lag=-19(3.91/3.93); L287 26.48/1.10 r_next=0.817 MAD_above=21.20 lag=1(21.20/21.20); L288 26.27/1.26 r_next=0.417 MAD_above=1.22 lag=-20(1.09/1.22) |
| 6646 | 6646/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 3.43/1.42 r_next=-0.027 MAD_above=2.10 lag=30(2.06/2.10); L287 21.10/1.29 r_next=-0.093 MAD_above=17.67 lag=32(17.59/17.67); L288 20.29/1.23 r_next=0.134 MAD_above=1.59 lag=-25(1.38/1.59) |
| 6647 | 6647/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 3.04/1.46 r_next=-0.149 MAD_above=1.78 lag=-16(1.73/1.78); L287 20.91/1.41 r_next=0.205 MAD_above=17.87 lag=8(17.84/17.87); L288 20.00/1.11 r_next=0.094 MAD_above=1.46 lag=2(1.45/1.46) |
| 6648 | 6648/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.81/1.32 r_next=-0.043 MAD_above=1.55 lag=-27(1.48/1.55); L287 20.95/1.24 r_next=0.167 MAD_above=18.14 lag=-29(18.09/18.14); L288 19.69/1.30 r_next=0.084 MAD_above=1.63 lag=31(1.62/1.63) |
| 6649 | 6649/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.26/1.11 r_next=-0.114 MAD_above=1.10 lag=15(1.07/1.10); L287 19.99/1.24 r_next=0.081 MAD_above=17.73 lag=32(17.70/17.73); L288 19.39/1.23 r_next=0.078 MAD_above=1.42 lag=-30(1.31/1.42) |
| 6650 | 6650/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.62/1.33 r_next=-0.014 MAD_above=1.43 lag=27(1.38/1.43); L287 20.13/1.35 r_next=0.136 MAD_above=17.51 lag=-16(17.50/17.51); L288 19.12/1.20 r_next=-0.065 MAD_above=1.57 lag=26(1.49/1.57) |
| 6651 | 6651/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.66/1.32 r_next=-0.118 MAD_above=1.46 lag=-1(1.40/1.46); L287 20.11/1.32 r_next=0.006 MAD_above=17.45 lag=-30(17.39/17.45); L288 19.21/1.10 r_next=-0.053 MAD_above=1.50 lag=-7(1.38/1.50) |
| 6652 | 6652/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.37/1.18 r_next=-0.042 MAD_above=1.18 lag=-8(1.15/1.18); L287 20.17/1.30 r_next=0.016 MAD_above=17.80 lag=29(17.77/17.80); L288 19.27/1.12 r_next=0.039 MAD_above=1.48 lag=-10(1.37/1.48) |
| 6653 | 6653/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284, 286]; L286 2.52/1.42 r_next=0.050 MAD_above=1.32 lag=-23(1.28/1.32); L287 20.43/1.67 r_next=-0.106 MAD_above=17.92 lag=32(17.92/17.92); L288 20.10/1.63 r_next=0.027 MAD_above=1.94 lag=-32(1.63/1.94) |
| 6654 | 6654/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 3.15/1.59 r_next=-0.045 MAD_above=1.90 lag=-22(1.84/1.90); L287 21.17/1.79 r_next=0.047 MAD_above=18.02 lag=5(18.01/18.02); L288 21.20/1.71 r_next=0.115 MAD_above=1.86 lag=5(1.73/1.86) |
| 6655 | 6655/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.76/1.54 r_next=-0.155 MAD_above=1.53 lag=-29(1.49/1.53); L287 20.97/1.77 r_next=-0.065 MAD_above=18.21 lag=-27(18.13/18.21); L288 20.73/1.72 r_next=-0.155 MAD_above=2.05 lag=-16(1.70/2.05) |
| 6656 | 6656/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 3.25/1.60 r_next=0.023 MAD_above=1.94 lag=-6(1.92/1.94); L287 21.50/1.60 r_next=0.046 MAD_above=18.24 lag=28(18.20/18.24); L288 21.42/1.85 r_next=-0.008 MAD_above=1.85 lag=-14(1.78/1.85) |
| 6657 | 6657/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284, 286]; L286 2.86/1.54 r_next=0.044 MAD_above=1.62 lag=32(1.60/1.62); L287 20.35/1.78 r_next=-0.009 MAD_above=17.49 lag=32(17.42/17.49); L288 20.41/1.69 r_next=-0.031 MAD_above=1.93 lag=-17(1.67/1.93) |
| 6658 | 6658/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284, 286]; L286 3.45/1.74 r_next=-0.020 MAD_above=2.16 lag=-6(2.13/2.16); L287 21.29/1.99 r_next=0.141 MAD_above=17.84 lag=11(17.77/17.84); L288 21.02/1.74 r_next=0.093 MAD_above=1.93 lag=-27(1.88/1.93) |
| 6659 | 6659/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.87/1.55 r_next=0.010 MAD_above=1.63 lag=-8(1.61/1.63); L287 20.91/1.89 r_next=0.097 MAD_above=18.04 lag=15(18.00/18.04); L288 20.58/1.74 r_next=-0.078 MAD_above=1.97 lag=-17(1.86/1.97) |
| 6664 | 6664/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.92/1.01 r_next=0.048 MAD_above=0.85 lag=32(0.80/0.85); L287 22.53/1.89 r_next=0.183 MAD_above=20.61 lag=-6(20.59/20.61); L288 23.17/2.16 r_next=0.284 MAD_above=2.17 lag=-7(1.99/2.17) |
| 6665 | 6665/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.95/1.09 r_next=-0.007 MAD_above=0.89 lag=-28(0.82/0.89); L287 22.00/1.92 r_next=0.187 MAD_above=20.05 lag=-5(20.04/20.05); L288 23.09/2.17 r_next=0.292 MAD_above=2.33 lag=-11(2.28/2.33) |
| 6666 | 6666/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.07/1.09 r_next=0.046 MAD_above=1.01 lag=18(0.91/1.01); L287 21.78/1.99 r_next=0.211 MAD_above=19.72 lag=-5(19.70/19.72); L288 22.16/2.20 r_next=0.137 MAD_above=2.07 lag=-24(1.93/2.07) |
| 6667 | 6667/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.02/1.15 r_next=-0.064 MAD_above=0.94 lag=30(0.89/0.94); L287 19.79/2.04 r_next=0.062 MAD_above=17.76 lag=-13(17.74/17.76); L288 20.85/2.42 r_next=0.147 MAD_above=2.66 lag=-5(2.40/2.66) |
| 6668 | 6668/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.99/1.15 r_next=0.085 MAD_above=0.94 lag=-1(0.87/0.94); L287 19.24/2.19 r_next=0.038 MAD_above=17.25 lag=17(17.15/17.25); L288 19.66/2.05 r_next=-0.001 MAD_above=2.35 lag=23(2.16/2.35) |
| 6669 | 6669/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.22/1.40 r_next=0.043 MAD_above=1.10 lag=31(1.00/1.10); L287 18.46/2.35 r_next=0.078 MAD_above=16.24 lag=10(16.23/16.24); L288 18.38/2.32 r_next=0.038 MAD_above=2.46 lag=-13(2.29/2.46) |
| 6670 | 6670/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.98/1.05 r_next=0.034 MAD_above=0.91 lag=-28(0.83/0.91); L287 17.93/1.93 r_next=0.235 MAD_above=15.95 lag=1(15.95/15.95); L288 17.12/2.15 r_next=0.166 MAD_above=2.16 lag=-29(2.10/2.16) |
| 6671 | 6671/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.56/1.67 r_next=-0.088 MAD_above=1.41 lag=9(1.33/1.41); L287 16.18/2.35 r_next=0.051 MAD_above=13.61 lag=0(13.61/13.61); L288 16.41/2.68 r_next=0.092 MAD_above=2.72 lag=6(2.56/2.72) |
| 6672 | 6672/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.84/1.80 r_next=-0.149 MAD_above=1.65 lag=19(1.58/1.65); L287 16.43/3.53 r_next=0.112 MAD_above=13.59 lag=-31(13.55/13.59); L288 15.68/2.88 r_next=0.169 MAD_above=3.40 lag=-25(3.09/3.40) |
| 6673 | 6673/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 3.05/2.11 r_next=-0.112 MAD_above=1.85 lag=-23(1.77/1.85); L287 13.96/3.91 r_next=0.086 MAD_above=10.96 lag=3(10.94/10.96); L288 14.29/4.00 r_next=0.080 MAD_above=3.88 lag=1(3.87/3.88) |
| 6674 | 6674/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.37/1.99 r_next=0.056 MAD_above=1.26 lag=9(1.26/1.26); L287 12.57/3.46 r_next=0.003 MAD_above=10.26 lag=-17(10.22/10.26); L288 10.80/3.60 r_next=-0.054 MAD_above=4.24 lag=-13(3.75/4.24) |
| 6675 | 6675/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.40/1.74 r_next=-0.062 MAD_above=1.29 lag=-19(1.24/1.29); L287 11.96/3.57 r_next=0.103 MAD_above=9.62 lag=-20(9.53/9.62); L288 12.13/3.15 r_next=0.045 MAD_above=3.60 lag=-7(3.38/3.60) |
| 6676 | 6676/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.76/2.21 r_next=-0.056 MAD_above=1.61 lag=25(1.56/1.61); L287 12.02/3.85 r_next=0.207 MAD_above=9.38 lag=11(9.24/9.38); L288 11.34/3.41 r_next=-0.026 MAD_above=3.67 lag=18(3.58/3.67) |
| 6677 | 6677/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.22/1.42 r_next=0.037 MAD_above=1.13 lag=27(1.08/1.13); L287 11.06/3.29 r_next=0.039 MAD_above=8.87 lag=-24(8.73/8.87); L288 10.44/3.46 r_next=0.015 MAD_above=3.63 lag=-9(3.37/3.63) |
| 6678 | 6678/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.46/1.73 r_next=0.009 MAD_above=1.37 lag=-5(1.27/1.37); L287 11.09/2.81 r_next=0.041 MAD_above=8.69 lag=-30(8.64/8.69); L288 10.66/2.57 r_next=0.084 MAD_above=2.92 lag=26(2.67/2.92) |
| 6679 | 6679/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.07/1.17 r_next=-0.011 MAD_above=0.98 lag=9(0.94/0.98); L287 9.26/2.56 r_next=0.095 MAD_above=7.23 lag=14(7.19/7.23); L288 9.82/2.36 r_next=0.129 MAD_above=2.61 lag=3(2.50/2.61) |
| 6680 | 6680/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.31/1.37 r_next=0.072 MAD_above=1.17 lag=26(1.11/1.17); L287 10.77/2.29 r_next=0.002 MAD_above=8.46 lag=13(8.45/8.46); L288 9.56/2.34 r_next=-0.134 MAD_above=2.73 lag=-9(2.50/2.73) |
| 6681 | 6681/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.42/1.32 r_next=0.078 MAD_above=1.25 lag=24(1.21/1.25); L287 10.16/2.62 r_next=0.139 MAD_above=7.75 lag=-13(7.74/7.75); L288 10.70/2.32 r_next=0.024 MAD_above=2.59 lag=24(2.47/2.59) |
| 6682 | 6682/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.43/1.33 r_next=-0.007 MAD_above=1.29 lag=27(1.24/1.29); L287 11.20/2.43 r_next=0.160 MAD_above=8.77 lag=0(8.77/8.77); L288 10.21/2.08 r_next=0.066 MAD_above=2.49 lag=-2(2.41/2.49) |
| 6683 | 6683/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.39/1.31 r_next=0.050 MAD_above=1.24 lag=-29(1.19/1.24); L287 10.60/2.18 r_next=0.204 MAD_above=8.21 lag=0(8.21/8.21); L288 11.13/2.12 r_next=-0.019 MAD_above=2.26 lag=9(2.23/2.26) |
| 6684 | 6684/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.13/1.15 r_next=-0.042 MAD_above=1.04 lag=32(0.98/1.04); L287 10.57/2.13 r_next=0.054 MAD_above=8.44 lag=-10(8.41/8.44); L288 10.27/2.01 r_next=-0.005 MAD_above=2.33 lag=-24(2.03/2.33) |
| 6685 | 6685/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.94/1.11 r_next=0.002 MAD_above=0.89 lag=-21(0.83/0.89); L287 9.69/1.86 r_next=0.219 MAD_above=7.76 lag=-25(7.72/7.76); L288 9.70/1.90 r_next=0.192 MAD_above=1.88 lag=1(1.84/1.88) |
| 6686 | 6686/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.11/1.12 r_next=0.006 MAD_above=0.98 lag=-31(0.94/0.98); L287 10.29/1.66 r_next=0.060 MAD_above=8.17 lag=0(8.17/8.17); L288 9.85/1.81 r_next=0.244 MAD_above=1.98 lag=9(1.71/1.98) |
| 6687 | 6687/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.25/1.13 r_next=-0.003 MAD_above=1.07 lag=21(1.01/1.07); L287 10.42/1.79 r_next=0.167 MAD_above=8.17 lag=-11(8.16/8.17); L288 10.05/1.95 r_next=0.176 MAD_above=1.95 lag=11(1.84/1.95) |
| 6688 | 6688/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.16/1.10 r_next=-0.032 MAD_above=1.02 lag=20(0.98/1.02); L287 10.09/1.78 r_next=0.281 MAD_above=7.93 lag=-11(7.92/7.93); L288 10.40/1.70 r_next=0.185 MAD_above=1.66 lag=-1(1.65/1.66) |
| 6689 | 6689/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.00/0.96 r_next=0.006 MAD_above=0.86 lag=-4(0.84/0.86); L287 9.95/1.58 r_next=0.030 MAD_above=7.94 lag=-2(7.94/7.94); L288 10.28/1.63 r_next=0.283 MAD_above=1.79 lag=-30(1.55/1.79) |
| 6690 | 6690/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.36/1.04 r_next=-0.003 MAD_above=1.16 lag=-27(1.11/1.16); L287 10.40/1.71 r_next=0.177 MAD_above=8.04 lag=-16(7.99/8.04); L288 9.68/1.79 r_next=0.312 MAD_above=1.83 lag=22(1.78/1.83) |
| 6691 | 6691/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.96/0.97 r_next=-0.044 MAD_above=0.91 lag=-29(0.83/0.91); L287 9.68/1.52 r_next=0.126 MAD_above=7.72 lag=-15(7.66/7.72); L288 10.19/1.46 r_next=0.149 MAD_above=1.61 lag=20(1.58/1.61) |
| 6692 | 6692/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.05/0.96 r_next=0.054 MAD_above=0.93 lag=-31(0.89/0.93); L287 10.54/1.46 r_next=0.128 MAD_above=8.49 lag=-27(8.43/8.49); L288 10.11/1.45 r_next=0.176 MAD_above=1.55 lag=-24(1.44/1.55) |
| 6693 | 6693/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.10/0.94 r_next=0.019 MAD_above=0.95 lag=-32(0.90/0.95); L287 9.99/1.38 r_next=0.055 MAD_above=7.88 lag=-8(7.87/7.88); L288 10.29/1.50 r_next=0.137 MAD_above=1.62 lag=-25(1.43/1.62) |
| 6694 | 6694/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.96/0.92 r_next=0.022 MAD_above=0.88 lag=6(0.80/0.88); L287 9.80/1.45 r_next=0.085 MAD_above=7.84 lag=26(7.80/7.84); L288 10.20/1.41 r_next=0.185 MAD_above=1.62 lag=26(1.47/1.62) |
| 6695 | 6695/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.75/0.81 r_next=0.021 MAD_above=0.70 lag=-8(0.62/0.70); L287 8.94/1.37 r_next=0.044 MAD_above=7.19 lag=-11(7.19/7.19); L288 9.63/1.49 r_next=0.040 MAD_above=1.73 lag=28(1.59/1.73) |
| 6696 | 6696/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.10/0.94 r_next=0.078 MAD_above=0.95 lag=22(0.88/0.95); L287 10.60/1.60 r_next=0.074 MAD_above=8.50 lag=-6(8.50/8.50); L288 10.78/1.54 r_next=0.141 MAD_above=1.72 lag=-19(1.47/1.72) |
| 6697 | 6697/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.61/0.70 r_next=-0.012 MAD_above=0.60 lag=9(0.58/0.60); L287 9.75/1.28 r_next=0.208 MAD_above=8.14 lag=-5(8.13/8.14); L288 10.30/1.40 r_next=0.148 MAD_above=1.47 lag=32(1.42/1.47) |
| 6698 | 6698/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.90/0.87 r_next=0.014 MAD_above=0.82 lag=-7(0.77/0.82); L287 10.33/1.29 r_next=0.113 MAD_above=8.43 lag=-21(8.42/8.43); L288 10.13/1.39 r_next=0.071 MAD_above=1.48 lag=-15(1.26/1.48) |
| 6699 | 6699/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.92/0.91 r_next=0.102 MAD_above=0.83 lag=13(0.79/0.83); L287 9.97/1.29 r_next=0.090 MAD_above=8.05 lag=-25(8.04/8.05); L288 9.58/1.38 r_next=0.230 MAD_above=1.49 lag=26(1.34/1.49) |
| 6700 | 6700/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.06/1.00 r_next=-0.030 MAD_above=0.93 lag=-26(0.84/0.93); L287 10.94/1.48 r_next=0.144 MAD_above=8.87 lag=-18(8.85/8.87); L288 10.50/1.49 r_next=0.238 MAD_above=1.55 lag=-23(1.47/1.55) |
| 6701 | 6701/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.82/0.84 r_next=-0.056 MAD_above=0.79 lag=11(0.68/0.79); L287 10.23/1.25 r_next=0.221 MAD_above=8.41 lag=-32(8.37/8.41); L288 10.31/1.39 r_next=0.184 MAD_above=1.29 lag=0(1.29/1.29) |
| 6702 | 6702/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.96/0.90 r_next=0.064 MAD_above=0.84 lag=-17(0.81/0.84); L287 10.58/1.37 r_next=0.263 MAD_above=8.62 lag=-32(8.61/8.62); L288 10.58/1.49 r_next=0.218 MAD_above=1.42 lag=-3(1.40/1.42) |
| 6703 | 6703/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.04/0.92 r_next=-0.014 MAD_above=0.90 lag=-26(0.86/0.90); L287 9.62/1.41 r_next=0.203 MAD_above=7.58 lag=5(7.57/7.58); L288 10.43/1.29 r_next=-0.031 MAD_above=1.50 lag=2(1.49/1.50) |
| 6704 | 6704/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.00/0.93 r_next=-0.014 MAD_above=0.83 lag=-3(0.82/0.83); L287 10.51/1.46 r_next=0.199 MAD_above=8.51 lag=-14(8.46/8.51); L288 10.78/1.23 r_next=0.061 MAD_above=1.40 lag=-17(1.31/1.40) |
| 6705 | 6705/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.33/0.95 r_next=0.067 MAD_above=1.10 lag=27(1.07/1.10); L287 10.56/1.32 r_next=0.088 MAD_above=8.22 lag=8(8.22/8.22); L288 11.20/1.40 r_next=0.101 MAD_above=1.55 lag=25(1.45/1.55) |
| 6706 | 6706/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.97/0.89 r_next=-0.058 MAD_above=0.85 lag=22(0.80/0.85); L287 10.61/1.26 r_next=0.153 MAD_above=8.64 lag=0(8.64/8.64); L288 10.75/1.40 r_next=0.174 MAD_above=1.42 lag=-4(1.39/1.42) |
| 6707 | 6707/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.12/0.97 r_next=0.025 MAD_above=0.96 lag=21(0.92/0.96); L287 10.60/1.32 r_next=0.064 MAD_above=8.49 lag=-13(8.47/8.49); L288 10.75/1.23 r_next=0.037 MAD_above=1.36 lag=-12(1.19/1.36) |
| 6708 | 6708/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.95/0.86 r_next=-0.040 MAD_above=0.83 lag=-17(0.80/0.83); L287 10.44/1.24 r_next=0.132 MAD_above=8.49 lag=0(8.49/8.49); L288 10.80/1.29 r_next=0.092 MAD_above=1.37 lag=21(1.27/1.37) |
| 6709 | 6709/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.78/0.77 r_next=-0.030 MAD_above=0.71 lag=-3(0.66/0.71); L287 10.46/1.38 r_next=0.149 MAD_above=8.68 lag=0(8.68/8.68); L288 11.08/1.38 r_next=0.153 MAD_above=1.53 lag=-12(1.38/1.53) |
| 6710 | 6710/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.85/0.85 r_next=-0.039 MAD_above=0.78 lag=-8(0.75/0.78); L287 10.68/1.37 r_next=0.123 MAD_above=8.83 lag=-18(8.80/8.83); L288 10.09/1.58 r_next=0.009 MAD_above=1.62 lag=-13(1.52/1.62) |
| 6711 | 6711/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.85/0.87 r_next=0.016 MAD_above=0.76 lag=9(0.72/0.76); L287 9.92/1.36 r_next=0.119 MAD_above=8.07 lag=-1(8.07/8.07); L288 9.61/1.34 r_next=-0.047 MAD_above=1.46 lag=-5(1.37/1.46) |
| 6712 | 6712/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.93/0.93 r_next=-0.038 MAD_above=0.85 lag=-14(0.80/0.85); L287 10.30/1.47 r_next=0.106 MAD_above=8.38 lag=-4(8.36/8.38); L288 9.93/1.69 r_next=0.149 MAD_above=1.71 lag=31(1.59/1.71) |
| 6713 | 6713/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.72/0.78 r_next=-0.049 MAD_above=0.67 lag=13(0.64/0.67); L287 9.77/1.42 r_next=0.058 MAD_above=8.06 lag=-30(8.02/8.06); L288 9.72/1.46 r_next=0.107 MAD_above=1.58 lag=-25(1.42/1.58) |
| 6714 | 6714/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.29/1.11 r_next=-0.020 MAD_above=1.11 lag=32(1.07/1.11); L287 10.79/1.69 r_next=0.054 MAD_above=8.51 lag=3(8.51/8.51); L288 9.92/1.71 r_next=0.043 MAD_above=1.99 lag=32(1.93/1.99) |
| 6715 | 6715/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.30/1.32 r_next=0.033 MAD_above=1.15 lag=7(1.09/1.15); L287 10.38/1.82 r_next=0.002 MAD_above=8.10 lag=21(8.06/8.10); L288 10.45/1.80 r_next=-0.080 MAD_above=2.08 lag=-32(1.88/2.08) |
| 6716 | 6716/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.57/1.52 r_next=-0.093 MAD_above=1.39 lag=20(1.33/1.39); L287 10.52/1.87 r_next=0.018 MAD_above=7.97 lag=25(7.93/7.97); L288 10.41/2.02 r_next=0.109 MAD_above=2.14 lag=5(2.04/2.14) |
| 6717 | 6717/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.10/1.12 r_next=-0.098 MAD_above=0.97 lag=31(0.97/0.97); L287 9.81/1.99 r_next=0.178 MAD_above=7.72 lag=-14(7.70/7.72); L288 10.26/1.82 r_next=0.028 MAD_above=2.00 lag=31(1.86/2.00) |
| 6718 | 6718/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.06/1.07 r_next=-0.080 MAD_above=0.94 lag=10(0.91/0.94); L287 9.51/2.04 r_next=0.027 MAD_above=7.46 lag=-15(7.42/7.46); L288 9.53/2.51 r_next=-0.051 MAD_above=2.54 lag=19(2.22/2.54) |
| 6719 | 6719/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.24/1.26 r_next=-0.092 MAD_above=1.13 lag=3(1.07/1.13); L287 9.15/2.22 r_next=0.185 MAD_above=6.91 lag=-5(6.90/6.91); L288 10.13/2.31 r_next=0.093 MAD_above=2.38 lag=-2(2.30/2.38) |
| 6720 | 6720/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.26/1.25 r_next=0.044 MAD_above=1.15 lag=27(1.04/1.15); L287 8.95/1.89 r_next=0.021 MAD_above=6.69 lag=1(6.69/6.69); L288 9.47/2.19 r_next=0.110 MAD_above=2.27 lag=30(2.00/2.27) |
| 6721 | 6721/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.31/1.38 r_next=0.042 MAD_above=1.19 lag=-16(1.12/1.19); L287 10.07/2.37 r_next=0.081 MAD_above=7.75 lag=-15(7.73/7.75); L288 10.12/2.00 r_next=0.098 MAD_above=2.38 lag=22(2.17/2.38) |
| 6722 | 6722/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.80/1.49 r_next=0.008 MAD_above=1.56 lag=30(1.49/1.56); L287 11.39/1.59 r_next=0.025 MAD_above=8.60 lag=-9(8.59/8.60); L288 11.35/1.99 r_next=0.030 MAD_above=2.03 lag=24(1.78/2.03) |
| 6723 | 6723/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.21/1.22 r_next=0.150 MAD_above=1.08 lag=-20(1.04/1.08); L287 10.65/2.00 r_next=0.150 MAD_above=8.45 lag=-10(8.44/8.45); L288 11.05/1.72 r_next=0.074 MAD_above=2.07 lag=-27(1.80/2.07) |
| 6724 | 6724/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.35/1.35 r_next=-0.014 MAD_above=1.20 lag=-25(1.16/1.20); L287 10.67/1.90 r_next=0.098 MAD_above=8.31 lag=0(8.31/8.31); L288 11.07/1.79 r_next=-0.022 MAD_above=2.02 lag=-16(1.92/2.02) |
| 6725 | 6725/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.38/1.30 r_next=-0.065 MAD_above=1.24 lag=-32(1.17/1.24); L287 10.08/1.64 r_next=0.139 MAD_above=7.71 lag=-4(7.70/7.71); L288 10.63/2.12 r_next=0.142 MAD_above=2.04 lag=-8(1.99/2.04) |
| 6726 | 6726/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.30/1.21 r_next=-0.017 MAD_above=1.15 lag=10(1.12/1.15); L287 10.18/1.61 r_next=0.080 MAD_above=7.88 lag=-6(7.86/7.88); L288 9.82/1.83 r_next=0.079 MAD_above=1.91 lag=-29(1.83/1.91) |
| 6727 | 6727/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.98/1.04 r_next=-0.000 MAD_above=0.90 lag=11(0.85/0.90); L287 9.95/2.06 r_next=-0.058 MAD_above=7.98 lag=-32(7.94/7.98); L288 9.90/2.33 r_next=0.073 MAD_above=2.51 lag=14(2.23/2.51) |
| 6728 | 6728/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.99/1.06 r_next=-0.009 MAD_above=0.92 lag=-9(0.87/0.92); L287 9.42/1.70 r_next=0.185 MAD_above=7.43 lag=-32(7.38/7.43); L288 9.68/2.56 r_next=0.033 MAD_above=2.17 lag=-9(2.09/2.17) |
| 6729 | 6729/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.93/1.10 r_next=0.157 MAD_above=0.90 lag=30(0.85/0.90); L287 9.71/1.95 r_next=0.163 MAD_above=7.78 lag=-31(7.76/7.78); L288 9.90/1.77 r_next=0.133 MAD_above=1.91 lag=3(1.80/1.91) |
| 6730 | 6730/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.20/1.14 r_next=0.059 MAD_above=1.04 lag=32(0.98/1.04); L287 10.10/2.01 r_next=0.062 MAD_above=7.90 lag=-11(7.89/7.90); L288 9.17/1.89 r_next=0.052 MAD_above=2.21 lag=-16(2.03/2.21) |
| 6731 | 6731/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.47/1.51 r_next=-0.035 MAD_above=1.34 lag=32(1.28/1.34); L287 9.93/1.74 r_next=0.026 MAD_above=7.48 lag=-20(7.46/7.48); L288 9.85/2.03 r_next=0.104 MAD_above=2.10 lag=-10(1.86/2.10) |
| 6732 | 6732/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.38/1.33 r_next=-0.115 MAD_above=1.24 lag=15(1.19/1.24); L287 10.54/2.07 r_next=0.099 MAD_above=8.18 lag=-22(8.14/8.18); L288 10.22/1.76 r_next=0.096 MAD_above=2.07 lag=8(1.94/2.07) |
| 6733 | 6733/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.13/1.39 r_next=0.005 MAD_above=1.00 lag=29(0.92/1.00); L287 9.31/1.76 r_next=0.166 MAD_above=7.21 lag=1(7.21/7.21); L288 9.44/1.75 r_next=-0.017 MAD_above=1.80 lag=15(1.71/1.80) |
| 6734 | 6734/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.95/1.01 r_next=0.125 MAD_above=0.86 lag=-23(0.80/0.86); L287 10.32/1.93 r_next=0.094 MAD_above=8.38 lag=1(8.38/8.38); L288 10.47/1.67 r_next=0.208 MAD_above=1.98 lag=-30(1.87/1.98) |
| 6735 | 6735/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.90/1.01 r_next=0.075 MAD_above=0.86 lag=12(0.77/0.86); L287 9.62/1.95 r_next=0.074 MAD_above=7.72 lag=-3(7.71/7.72); L288 10.31/1.62 r_next=0.005 MAD_above=1.95 lag=-22(1.75/1.95) |
| 6736 | 6736/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.36/1.24 r_next=-0.111 MAD_above=1.21 lag=-32(1.13/1.21); L287 9.90/1.71 r_next=0.100 MAD_above=7.55 lag=24(7.53/7.55); L288 9.87/1.37 r_next=0.011 MAD_above=1.63 lag=-31(1.53/1.63) |
| 6737 | 6737/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.14/1.07 r_next=-0.080 MAD_above=0.98 lag=-23(0.97/0.98); L287 9.99/1.85 r_next=0.172 MAD_above=7.85 lag=-18(7.82/7.85); L288 10.17/1.52 r_next=-0.023 MAD_above=1.75 lag=-4(1.63/1.75) |
| 6738 | 6738/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.37/1.10 r_next=-0.125 MAD_above=1.17 lag=30(1.11/1.17); L287 9.76/1.68 r_next=0.234 MAD_above=7.39 lag=0(7.39/7.39); L288 9.12/1.49 r_next=-0.043 MAD_above=1.67 lag=1(1.67/1.67) |
| 6739 | 6739/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.98/0.96 r_next=-0.012 MAD_above=0.90 lag=18(0.83/0.90); L287 9.92/1.61 r_next=0.185 MAD_above=7.93 lag=5(7.91/7.93); L288 9.99/1.54 r_next=0.085 MAD_above=1.62 lag=16(1.44/1.62) |
| 6740 | 6740/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.65/0.79 r_next=-0.005 MAD_above=0.66 lag=-27(0.60/0.66); L287 9.65/1.52 r_next=0.134 MAD_above=8.00 lag=-28(7.96/8.00); L288 9.53/1.50 r_next=0.158 MAD_above=1.62 lag=8(1.44/1.62) |
| 6741 | 6741/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.04/1.00 r_next=0.072 MAD_above=0.93 lag=16(0.88/0.93); L287 9.81/1.57 r_next=0.172 MAD_above=7.77 lag=-6(7.77/7.77); L288 9.11/1.44 r_next=0.235 MAD_above=1.66 lag=-10(1.48/1.66) |
| 6742 | 6742/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.78/0.80 r_next=0.004 MAD_above=0.73 lag=29(0.65/0.73); L287 9.44/1.24 r_next=0.137 MAD_above=7.66 lag=4(7.66/7.66); L288 9.16/1.38 r_next=0.149 MAD_above=1.44 lag=7(1.30/1.44) |
| 6743 | 6743/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.80/0.86 r_next=-0.032 MAD_above=0.75 lag=30(0.67/0.75); L287 8.81/1.35 r_next=0.054 MAD_above=7.01 lag=1(7.00/7.01); L288 9.61/1.35 r_next=0.122 MAD_above=1.60 lag=-27(1.51/1.60) |
| 6744 | 6744/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.89/0.86 r_next=-0.088 MAD_above=0.80 lag=26(0.72/0.80); L287 9.20/1.33 r_next=0.203 MAD_above=7.31 lag=0(7.31/7.31); L288 9.99/1.26 r_next=0.194 MAD_above=1.39 lag=-17(1.34/1.39) |
| 6745 | 6745/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.75/0.80 r_next=0.062 MAD_above=0.72 lag=28(0.66/0.72); L287 8.83/1.33 r_next=0.146 MAD_above=7.08 lag=-1(7.08/7.08); L288 9.43/1.32 r_next=-0.019 MAD_above=1.45 lag=-18(1.34/1.45) |
| 6746 | 6746/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.70/0.76 r_next=0.140 MAD_above=0.64 lag=-10(0.60/0.64); L287 9.57/1.42 r_next=0.122 MAD_above=7.87 lag=-1(7.87/7.87); L288 9.68/1.35 r_next=0.172 MAD_above=1.52 lag=16(1.29/1.52) |
| 6747 | 6747/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.83/0.86 r_next=0.025 MAD_above=0.76 lag=-17(0.72/0.76); L287 10.00/1.27 r_next=0.158 MAD_above=8.17 lag=-32(8.15/8.17); L288 9.72/1.34 r_next=0.105 MAD_above=1.40 lag=32(1.29/1.40) |
| 6748 | 6748/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.61/0.70 r_next=-0.060 MAD_above=0.59 lag=15(0.53/0.59); L287 9.98/1.23 r_next=0.137 MAD_above=8.37 lag=0(8.37/8.37); L288 9.76/1.27 r_next=0.285 MAD_above=1.36 lag=-17(1.21/1.36) |
| 6749 | 6749/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.00/0.92 r_next=-0.071 MAD_above=0.88 lag=-14(0.85/0.88); L287 10.20/1.27 r_next=0.160 MAD_above=8.20 lag=-16(8.19/8.20); L288 10.17/1.31 r_next=0.210 MAD_above=1.34 lag=-1(1.33/1.34) |
| 6750 | 6750/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.11/0.98 r_next=-0.081 MAD_above=0.95 lag=-4(0.92/0.95); L287 10.12/1.22 r_next=0.101 MAD_above=8.01 lag=0(8.01/8.01); L288 9.74/1.54 r_next=0.164 MAD_above=1.51 lag=16(1.44/1.51) |
| 6751 | 6751/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.93/0.91 r_next=-0.028 MAD_above=0.82 lag=28(0.78/0.82); L287 9.62/1.32 r_next=0.128 MAD_above=7.69 lag=0(7.69/7.69); L288 9.39/1.45 r_next=0.146 MAD_above=1.47 lag=29(1.37/1.47) |
| 6752 | 6752/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.81/0.85 r_next=0.059 MAD_above=0.73 lag=8(0.71/0.73); L287 9.43/1.39 r_next=0.162 MAD_above=7.62 lag=-32(7.62/7.62); L288 9.52/1.27 r_next=-0.106 MAD_above=1.38 lag=23(1.30/1.38) |
| 6753 | 6753/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.94/0.97 r_next=-0.059 MAD_above=0.83 lag=-10(0.79/0.83); L287 10.19/1.39 r_next=0.128 MAD_above=8.26 lag=-7(8.24/8.26); L288 10.27/1.46 r_next=0.095 MAD_above=1.57 lag=-9(1.43/1.57) |
| 6754 | 6754/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.15/1.01 r_next=-0.098 MAD_above=0.96 lag=-8(0.95/0.96); L287 10.19/1.36 r_next=0.122 MAD_above=8.04 lag=-8(8.03/8.04); L288 9.51/1.40 r_next=0.151 MAD_above=1.63 lag=16(1.49/1.63) |
| 6755 | 6755/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.89/0.89 r_next=0.091 MAD_above=0.79 lag=12(0.77/0.79); L287 9.99/1.31 r_next=0.206 MAD_above=8.10 lag=0(8.10/8.10); L288 10.23/1.41 r_next=0.143 MAD_above=1.36 lag=18(1.30/1.36) |
| 6756 | 6756/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.82/0.86 r_next=-0.012 MAD_above=0.74 lag=6(0.69/0.74); L287 9.90/1.16 r_next=0.247 MAD_above=8.09 lag=0(8.09/8.09); L288 9.59/1.27 r_next=0.274 MAD_above=1.22 lag=16(1.17/1.22) |
| 6757 | 6757/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.57/0.69 r_next=-0.027 MAD_above=0.57 lag=15(0.54/0.57); L287 9.71/1.24 r_next=0.221 MAD_above=8.14 lag=-4(8.14/8.14); L288 9.37/1.48 r_next=0.116 MAD_above=1.36 lag=1(1.35/1.36) |
| 6758 | 6758/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.01/1.01 r_next=-0.041 MAD_above=0.91 lag=-2(0.87/0.91); L287 9.90/1.26 r_next=0.337 MAD_above=7.89 lag=-8(7.87/7.89); L288 9.70/1.34 r_next=0.173 MAD_above=1.25 lag=3(1.21/1.25) |
| 6759 | 6759/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.93/1.01 r_next=-0.087 MAD_above=0.89 lag=-22(0.83/0.89); L287 9.44/1.29 r_next=0.211 MAD_above=7.51 lag=-32(7.50/7.51); L288 9.24/1.40 r_next=0.082 MAD_above=1.41 lag=-27(1.37/1.41) |
| 6760 | 6760/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.86/0.90 r_next=-0.017 MAD_above=0.80 lag=-15(0.72/0.80); L287 9.47/1.22 r_next=0.139 MAD_above=7.62 lag=-31(7.61/7.62); L288 9.48/1.41 r_next=0.034 MAD_above=1.42 lag=-26(1.28/1.42) |
| 6761 | 6761/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.69/0.82 r_next=-0.034 MAD_above=0.67 lag=2(0.63/0.67); L287 9.24/1.41 r_next=0.139 MAD_above=7.55 lag=-6(7.54/7.55); L288 9.38/1.46 r_next=0.245 MAD_above=1.52 lag=-16(1.46/1.52) |
| 6762 | 6762/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.84/0.85 r_next=-0.096 MAD_above=0.73 lag=27(0.72/0.73); L287 9.62/1.38 r_next=0.212 MAD_above=7.78 lag=28(7.77/7.78); L288 9.52/1.41 r_next=0.087 MAD_above=1.38 lag=1(1.37/1.38) |
| 6763 | 6763/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.11/1.04 r_next=0.046 MAD_above=0.97 lag=11(0.93/0.97); L287 9.66/1.26 r_next=0.192 MAD_above=7.55 lag=-4(7.54/7.55); L288 9.74/1.41 r_next=0.148 MAD_above=1.43 lag=-16(1.36/1.43) |
| 6764 | 6764/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.00/0.98 r_next=0.005 MAD_above=0.88 lag=25(0.84/0.88); L287 9.94/1.36 r_next=0.109 MAD_above=7.94 lag=-11(7.92/7.94); L288 9.90/1.56 r_next=0.108 MAD_above=1.59 lag=-9(1.30/1.59) |
| 6765 | 6765/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.93/0.97 r_next=-0.121 MAD_above=0.86 lag=-17(0.81/0.86); L287 9.34/1.47 r_next=0.163 MAD_above=7.41 lag=-28(7.40/7.41); L288 9.63/1.55 r_next=0.012 MAD_above=1.56 lag=-10(1.49/1.56) |
| 6766 | 6766/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.98/0.92 r_next=-0.102 MAD_above=0.87 lag=-19(0.81/0.87); L287 9.66/1.44 r_next=0.134 MAD_above=7.67 lag=-1(7.67/7.67); L288 9.62/1.44 r_next=0.098 MAD_above=1.52 lag=16(1.49/1.52) |
| 6767 | 6767/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.12/0.99 r_next=-0.017 MAD_above=0.99 lag=24(0.89/0.99); L287 9.83/1.51 r_next=0.197 MAD_above=7.70 lag=-6(7.69/7.70); L288 10.08/1.52 r_next=0.127 MAD_above=1.56 lag=25(1.49/1.56) |
| 6768 | 6768/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.81/0.84 r_next=-0.033 MAD_above=0.76 lag=9(0.72/0.76); L287 9.93/1.37 r_next=0.158 MAD_above=8.12 lag=-9(8.08/8.12); L288 9.77/1.37 r_next=0.095 MAD_above=1.40 lag=2(1.38/1.40) |
| 6769 | 6769/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.15/1.03 r_next=-0.054 MAD_above=1.00 lag=-6(0.94/1.00); L287 9.48/1.41 r_next=0.093 MAD_above=7.33 lag=-8(7.33/7.33); L288 9.98/1.45 r_next=0.075 MAD_above=1.65 lag=-27(1.41/1.65) |
| 6770 | 6770/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.12/1.00 r_next=-0.133 MAD_above=0.97 lag=11(0.91/0.97); L287 10.05/1.28 r_next=0.117 MAD_above=7.93 lag=2(7.93/7.93); L288 9.52/1.33 r_next=0.099 MAD_above=1.45 lag=-16(1.34/1.45) |
| 6771 | 6771/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.83/0.89 r_next=0.088 MAD_above=0.76 lag=24(0.73/0.76); L287 9.60/1.47 r_next=0.076 MAD_above=7.77 lag=-32(7.74/7.77); L288 9.27/1.71 r_next=0.131 MAD_above=1.73 lag=-7(1.60/1.73) |
| 6772 | 6772/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.85/0.88 r_next=-0.001 MAD_above=0.80 lag=-1(0.74/0.80); L287 8.87/1.41 r_next=0.142 MAD_above=7.02 lag=-7(7.01/7.02); L288 8.08/1.56 r_next=0.048 MAD_above=1.70 lag=6(1.55/1.70) |
| 6773 | 6773/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.72/0.82 r_next=-0.026 MAD_above=0.70 lag=26(0.64/0.70); L287 9.05/1.42 r_next=0.122 MAD_above=7.33 lag=-29(7.28/7.33); L288 9.39/1.61 r_next=0.019 MAD_above=1.62 lag=3(1.50/1.62) |
| 6774 | 6774/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.90/0.92 r_next=0.082 MAD_above=0.82 lag=-18(0.78/0.82); L287 9.44/1.40 r_next=0.094 MAD_above=7.53 lag=-30(7.51/7.53); L288 8.70/1.51 r_next=0.086 MAD_above=1.62 lag=3(1.61/1.62) |
| 6775 | 6775/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.78/0.84 r_next=0.000 MAD_above=0.73 lag=1(0.69/0.73); L287 8.27/1.67 r_next=0.024 MAD_above=6.49 lag=-28(6.47/6.49); L288 9.25/1.33 r_next=0.071 MAD_above=1.87 lag=-24(1.71/1.87) |
| 6776 | 6776/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.16/1.06 r_next=0.005 MAD_above=1.00 lag=-30(0.97/1.00); L287 9.22/1.45 r_next=0.140 MAD_above=7.07 lag=-28(7.02/7.07); L288 9.59/1.37 r_next=0.071 MAD_above=1.58 lag=-21(1.43/1.58) |
| 6777 | 6777/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.87/0.88 r_next=-0.002 MAD_above=0.81 lag=21(0.72/0.81); L287 8.84/1.62 r_next=0.105 MAD_above=6.97 lag=-30(6.93/6.97); L288 9.35/1.31 r_next=0.238 MAD_above=1.67 lag=-18(1.49/1.67) |
| 6778 | 6778/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.95/0.92 r_next=-0.182 MAD_above=0.87 lag=-26(0.81/0.87); L287 9.21/1.38 r_next=0.110 MAD_above=7.26 lag=-24(7.24/7.26); L288 9.28/1.30 r_next=0.003 MAD_above=1.42 lag=-7(1.35/1.42) |
| 6779 | 6779/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.79/0.82 r_next=0.077 MAD_above=0.73 lag=26(0.69/0.73); L287 9.29/1.43 r_next=0.172 MAD_above=7.50 lag=1(7.50/7.50); L288 9.11/1.33 r_next=0.232 MAD_above=1.41 lag=-1(1.38/1.41) |
| 6780 | 6780/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.62/0.72 r_next=-0.104 MAD_above=0.61 lag=-20(0.55/0.61); L287 8.97/1.38 r_next=0.157 MAD_above=7.36 lag=14(7.34/7.36); L288 8.54/1.41 r_next=0.184 MAD_above=1.47 lag=-12(1.41/1.47) |
| 6781 | 6781/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.03/1.01 r_next=0.010 MAD_above=0.92 lag=8(0.88/0.92); L287 9.06/1.29 r_next=0.071 MAD_above=7.03 lag=-6(7.02/7.03); L288 8.54/1.37 r_next=0.169 MAD_above=1.49 lag=-28(1.37/1.49) |
| 6782 | 6782/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.69/0.83 r_next=-0.038 MAD_above=0.67 lag=30(0.63/0.67); L287 7.78/1.37 r_next=0.168 MAD_above=6.09 lag=17(6.08/6.09); L288 8.20/1.27 r_next=0.129 MAD_above=1.43 lag=-32(1.38/1.43) |
| 6783 | 6783/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.66/0.71 r_next=0.068 MAD_above=0.66 lag=-27(0.57/0.66); L287 9.07/1.27 r_next=0.096 MAD_above=7.41 lag=-16(7.39/7.41); L288 9.01/1.35 r_next=0.195 MAD_above=1.43 lag=12(1.32/1.43) |
| 6784 | 6784/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.83/0.84 r_next=-0.064 MAD_above=0.78 lag=-13(0.72/0.78); L287 9.36/1.49 r_next=0.109 MAD_above=7.53 lag=-1(7.52/7.53); L288 9.25/1.35 r_next=0.082 MAD_above=1.49 lag=-16(1.45/1.49) |
| 6785 | 6785/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.72/0.94 r_next=-0.012 MAD_above=0.70 lag=-2(0.66/0.70); L287 8.38/1.45 r_next=0.136 MAD_above=6.67 lag=-16(6.66/6.67); L288 9.05/1.51 r_next=0.028 MAD_above=1.60 lag=-2(1.59/1.60) |
| 6786 | 6786/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.68/0.76 r_next=0.020 MAD_above=0.66 lag=-12(0.59/0.66); L287 8.74/1.37 r_next=0.062 MAD_above=7.06 lag=-10(7.05/7.06); L288 8.70/1.40 r_next=0.125 MAD_above=1.45 lag=-1(1.43/1.45) |
| 6787 | 6787/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.52/0.59 r_next=0.096 MAD_above=0.55 lag=-32(0.49/0.55); L287 8.13/1.35 r_next=0.148 MAD_above=6.61 lag=-1(6.61/6.61); L288 8.46/1.44 r_next=0.202 MAD_above=1.50 lag=-17(1.36/1.50) |
| 6788 | 6788/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.66/0.78 r_next=0.024 MAD_above=0.66 lag=30(0.60/0.66); L287 8.38/1.40 r_next=0.302 MAD_above=6.72 lag=-4(6.72/6.72); L288 9.07/1.30 r_next=0.229 MAD_above=1.42 lag=0(1.42/1.42) |
| 6789 | 6789/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.65/0.80 r_next=-0.019 MAD_above=0.64 lag=2(0.60/0.64); L287 8.91/1.45 r_next=0.125 MAD_above=7.27 lag=-17(7.23/7.27); L288 8.92/1.40 r_next=0.170 MAD_above=1.50 lag=-32(1.32/1.50) |
| 6790 | 6790/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.65/0.79 r_next=0.023 MAD_above=0.64 lag=21(0.62/0.64); L287 9.15/1.70 r_next=0.131 MAD_above=7.50 lag=-18(7.45/7.50); L288 8.92/1.43 r_next=0.062 MAD_above=1.64 lag=-19(1.49/1.64) |
| 6791 | 6791/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.88/0.94 r_next=-0.125 MAD_above=0.82 lag=3(0.77/0.82); L287 9.24/1.39 r_next=0.222 MAD_above=7.36 lag=-32(7.32/7.36); L288 9.68/1.52 r_next=0.037 MAD_above=1.47 lag=1(1.44/1.47) |
| 6792 | 6792/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.79/0.91 r_next=0.014 MAD_above=0.76 lag=28(0.72/0.76); L287 9.12/1.38 r_next=0.025 MAD_above=7.33 lag=-29(7.27/7.33); L288 9.27/1.40 r_next=0.176 MAD_above=1.59 lag=20(1.35/1.59) |
| 6793 | 6793/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.71/0.78 r_next=0.017 MAD_above=0.66 lag=-29(0.63/0.66); L287 8.98/1.48 r_next=0.165 MAD_above=7.27 lag=-27(7.26/7.27); L288 9.06/1.25 r_next=0.047 MAD_above=1.37 lag=2(1.33/1.37) |
| 6794 | 6794/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.78/0.82 r_next=0.072 MAD_above=0.71 lag=27(0.69/0.71); L287 9.47/1.41 r_next=0.174 MAD_above=7.69 lag=-24(7.65/7.69); L288 8.64/1.35 r_next=-0.040 MAD_above=1.54 lag=18(1.45/1.54) |
| 6795 | 6795/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 2.13/1.02 r_next=-0.011 MAD_above=1.00 lag=1(0.95/1.00); L287 9.69/1.42 r_next=0.076 MAD_above=7.56 lag=-10(7.52/7.56); L288 9.58/1.59 r_next=-0.018 MAD_above=1.60 lag=7(1.45/1.60) |
| 6796 | 6796/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.90/0.93 r_next=-0.045 MAD_above=0.82 lag=26(0.74/0.82); L287 9.62/1.37 r_next=0.006 MAD_above=7.72 lag=-9(7.69/7.72); L288 9.04/1.76 r_next=0.233 MAD_above=1.79 lag=32(1.64/1.79) |
| 6797 | 6797/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.85/0.81 r_next=-0.042 MAD_above=0.76 lag=-30(0.73/0.76); L287 9.30/1.26 r_next=0.248 MAD_above=7.45 lag=-21(7.41/7.45); L288 9.51/1.47 r_next=0.142 MAD_above=1.39 lag=16(1.28/1.39) |
| 6798 | 6798/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.63/0.76 r_next=0.032 MAD_above=0.64 lag=4(0.57/0.64); L287 9.63/1.40 r_next=0.232 MAD_above=8.00 lag=-32(7.98/8.00); L288 9.55/1.45 r_next=0.098 MAD_above=1.46 lag=-2(1.45/1.46) |
| 6799 | 6799/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.62/0.74 r_next=-0.017 MAD_above=0.61 lag=18(0.57/0.61); L287 9.51/1.50 r_next=0.051 MAD_above=7.88 lag=-7(7.87/7.88); L288 10.03/1.54 r_next=0.075 MAD_above=1.69 lag=18(1.54/1.69) |
| 6800 | 6800/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.72/0.80 r_next=-0.036 MAD_above=0.65 lag=23(0.65/0.65); L287 10.16/1.47 r_next=0.212 MAD_above=8.43 lag=-30(8.39/8.43); L288 10.68/1.67 r_next=0.216 MAD_above=1.63 lag=-4(1.58/1.63) |
| 6801 | 6801/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.57/0.67 r_next=-0.069 MAD_above=0.58 lag=18(0.55/0.58); L287 10.18/1.44 r_next=0.097 MAD_above=8.60 lag=-23(8.59/8.60); L288 10.08/1.59 r_next=0.172 MAD_above=1.56 lag=-21(1.49/1.56) |
| 6802 | 6802/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.55/0.67 r_next=0.001 MAD_above=0.60 lag=-8(0.53/0.60); L287 11.43/1.78 r_next=0.280 MAD_above=9.88 lag=-21(9.83/9.88); L288 11.63/1.52 r_next=0.155 MAD_above=1.65 lag=-9(1.51/1.65) |
| 6803 | 6803/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.52/0.70 r_next=0.049 MAD_above=0.53 lag=27(0.50/0.53); L287 13.19/1.77 r_next=0.318 MAD_above=11.67 lag=-31(11.62/11.67); L288 14.38/1.83 r_next=0.256 MAD_above=1.99 lag=-4(1.94/1.99) |
| 6804 | 6804/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.56/0.70 r_next=-0.034 MAD_above=0.56 lag=26(0.53/0.56); L287 14.01/1.77 r_next=0.180 MAD_above=12.45 lag=-23(12.43/12.45); L288 15.04/1.81 r_next=0.376 MAD_above=2.17 lag=9(2.01/2.17) |
| 6805 | 6805/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.56/0.70 r_next=-0.081 MAD_above=0.57 lag=18(0.54/0.57); L287 13.06/1.54 r_next=0.304 MAD_above=11.50 lag=-30(11.47/11.50); L288 14.89/1.66 r_next=0.177 MAD_above=2.21 lag=-1(2.20/2.21) |
| 6806 | 6806/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.47/0.59 r_next=0.010 MAD_above=0.53 lag=-17(0.48/0.53); L287 14.64/1.59 r_next=0.209 MAD_above=13.17 lag=-19(13.17/13.17); L288 14.69/1.78 r_next=0.224 MAD_above=1.78 lag=17(1.68/1.78) |
| 6807 | 6807/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.49/0.62 r_next=0.047 MAD_above=0.55 lag=24(0.51/0.55); L287 15.61/1.64 r_next=0.209 MAD_above=14.12 lag=-9(14.12/14.12); L288 16.48/1.82 r_next=0.170 MAD_above=1.89 lag=-12(1.83/1.89) |
| 6808 | 6808/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.49/0.60 r_next=0.009 MAD_above=0.51 lag=-15(0.48/0.51); L287 16.59/1.54 r_next=0.225 MAD_above=15.10 lag=29(15.07/15.10); L288 17.31/1.61 r_next=0.148 MAD_above=1.60 lag=4(1.54/1.60) |
| 6809 | 6809/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.57/0.69 r_next=-0.092 MAD_above=0.62 lag=16(0.53/0.62); L287 17.53/1.76 r_next=0.264 MAD_above=15.96 lag=-1(15.96/15.96); L288 19.36/1.49 r_next=0.110 MAD_above=2.23 lag=28(2.20/2.23) |
| 6810 | 6810/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.59/0.71 r_next=0.025 MAD_above=0.62 lag=25(0.56/0.62); L287 19.38/1.62 r_next=0.216 MAD_above=17.79 lag=32(17.77/17.79); L288 19.97/1.55 r_next=0.279 MAD_above=1.81 lag=-12(1.65/1.81) |
| 6811 | 6811/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.50/0.60 r_next=0.034 MAD_above=0.53 lag=-31(0.49/0.53); L287 19.69/1.50 r_next=0.186 MAD_above=18.19 lag=0(18.19/18.19); L288 19.88/1.63 r_next=0.087 MAD_above=1.63 lag=-6(1.51/1.63) |
| 6812 | 6812/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.58/0.82 r_next=-0.002 MAD_above=0.62 lag=28(0.51/0.62); L287 21.25/1.64 r_next=0.178 MAD_above=19.68 lag=0(19.68/19.68); L288 21.36/1.43 r_next=0.289 MAD_above=1.69 lag=19(1.57/1.69) |
| 6813 | 6813/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.41/0.53 r_next=0.010 MAD_above=0.47 lag=29(0.45/0.47); L287 22.24/1.38 r_next=0.404 MAD_above=20.83 lag=-32(20.82/20.83); L288 22.88/1.52 r_next=0.456 MAD_above=1.49 lag=1(1.43/1.49) |
| 6814 | 6814/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.65/0.77 r_next=-0.064 MAD_above=0.66 lag=30(0.60/0.66); L287 22.99/1.41 r_next=0.300 MAD_above=21.35 lag=-24(21.33/21.35); L288 24.05/1.38 r_next=0.332 MAD_above=1.64 lag=32(1.61/1.64) |
| 6815 | 6815/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.58/0.69 r_next=0.025 MAD_above=0.62 lag=-5(0.56/0.62); L287 22.49/1.61 r_next=0.330 MAD_above=20.91 lag=-4(20.91/20.91); L288 22.61/1.52 r_next=0.226 MAD_above=1.56 lag=-5(1.45/1.56) |
| 6816 | 6816/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.60/0.73 r_next=0.046 MAD_above=0.62 lag=-17(0.57/0.62); L287 22.35/1.61 r_next=0.270 MAD_above=20.75 lag=18(20.75/20.75); L288 22.64/1.64 r_next=0.202 MAD_above=1.73 lag=-13(1.56/1.73) |
| 6817 | 6817/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.61/0.74 r_next=0.048 MAD_above=0.62 lag=-10(0.57/0.62); L287 22.06/1.52 r_next=0.319 MAD_above=20.45 lag=24(20.44/20.45); L288 22.99/1.67 r_next=0.183 MAD_above=1.73 lag=-12(1.65/1.73) |
| 6818 | 6818/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.72/0.86 r_next=0.035 MAD_above=0.70 lag=-32(0.67/0.70); L287 22.83/1.48 r_next=0.096 MAD_above=21.11 lag=30(21.10/21.11); L288 22.62/1.27 r_next=0.299 MAD_above=1.49 lag=-12(1.29/1.49) |
| 6819 | 6819/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.65/0.78 r_next=0.072 MAD_above=0.66 lag=-12(0.62/0.66); L287 22.63/1.44 r_next=0.251 MAD_above=20.98 lag=17(20.96/20.98); L288 23.48/1.40 r_next=0.108 MAD_above=1.62 lag=-1(1.57/1.62) |
| 6820 | 6820/F2 | L286 | L287 | engine (stable signal-lock geometry; dark boundary is picture) | waveforms=[284]; L286 1.56/0.65 r_next=-0.017 MAD_above=0.54 lag=23(0.52/0.54); L287 22.67/1.39 r_next=0.003 MAD_above=21.11 lag=-31(21.10/21.11); L288 23.24/1.48 r_next=0.132 MAD_above=1.74 lag=-13(1.57/1.74) |

## Head-switch row

`S` is scored first against the reference's earliest switch-band row. A difference of one row is the declared partial-predecessor semantic gap. The separate exact check uses the reference's independently measured first-full-other-head row: an internal blanking signature, a persistent three-third step, or a two-sided whole-row time-base step. It remains unmeasurable when none is exposed.

### Engine field 1

S minus reference switch histogram: -184: 1, -164: 1, -160: 1, -155: 2, -153: 1, -152: 2, -151: 1, -150: 1, -148: 2, -147: 1, -144: 3, -140: 1, -128: 1, -126: 1, -125: 1, -122: 1, -116: 1, -113: 1, -97: 1, -92: 1, -86: 1, -68: 2, -67: 1, -54: 1, -49: 1, -46: 2, -44: 1, -23: 2, -21: 1, -16: 1, -15: 1, -7: 1, -5: 1, -3: 1, -1: 7, +0: 486, +1: 369, engine-unmeasurable: 15

Differences beyond the one-row semantic gap:

| engine counter | raw counter/field | S | reference switch | raw tail rows |
|---:|:---:|:---|:---|:---|
| 6269 | 6269/F1 | L240 | L261 | L239 23.70/2.23 r_next=0.187 MAD_above=7.60 lag=0(7.60/7.60); L240 23.65/1.06 r_next=0.439 MAD_above=1.52 lag=26(1.38/1.52); L241 23.57/1.09 r_next=0.453 MAD_above=1.05 lag=24(0.88/1.05); L247 22.78/1.19 r_next=0.496 MAD_above=1.19 lag=7(1.12/1.19); L248 22.56/1.21 r_next=0.404 MAD_above=1.06 lag=2(1.05/1.06); L249 22.60/1.19 r_next=0.453 MAD_above=1.12 lag=-7(1.01/1.12); L250 22.23/1.35 r_next=0.526 MAD_above=1.17 lag=6(1.09/1.17); L251 21.92/1.18 r_next=0.597 MAD_above=1.05 lag=6(1.01/1.05); L252 22.33/1.25 r_next=0.531 MAD_above=1.02 lag=-1(1.01/1.02); L253 22.25/1.35 r_next=0.513 MAD_above=1.14 lag=-29(1.04/1.14); L254 22.46/1.29 r_next=0.555 MAD_above=1.21 lag=-14(1.08/1.21); L255 22.70/1.28 r_next=0.498 MAD_above=1.14 lag=-10(1.11/1.14); L256 22.96/1.22 r_next=0.472 MAD_above=1.10 lag=-18(1.04/1.10); L257 22.93/1.17 r_next=0.503 MAD_above=1.07 lag=-32(1.03/1.07); L258 23.10/1.24 r_next=0.511 MAD_above=1.00 lag=1(0.98/1.00); L259 23.14/1.28 r_next=0.489 MAD_above=1.02 lag=-2(1.00/1.02); L260 23.14/1.15 r_next=0.410 MAD_above=1.08 lag=2(1.03/1.08); L261 22.18/1.54 r_next=0.572 MAD_above=1.50 lag=-14(1.40/1.50); L262 21.55/1.42 r_next=-0.006 MAD_above=1.25 lag=6(1.18/1.25); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.931; no internal horizontal blanking run; gate=4.000) |
| 6270 | 6270/F1 | L239 | L262 | L238 27.10/2.97 r_next=0.311 MAD_above=1.30 lag=0(1.30/1.30); L239 25.01/1.33 r_next=0.404 MAD_above=2.69 lag=0(2.69/2.69); L240 24.82/1.17 r_next=0.397 MAD_above=1.24 lag=-10(1.20/1.24); L247 24.53/1.19 r_next=0.390 MAD_above=1.12 lag=7(1.05/1.12); L248 23.76/1.25 r_next=0.419 MAD_above=1.34 lag=-7(1.29/1.34); L249 23.77/1.17 r_next=0.495 MAD_above=1.18 lag=-4(1.12/1.18); L250 23.41/1.30 r_next=0.552 MAD_above=1.12 lag=-1(1.12/1.12); L251 23.40/1.36 r_next=0.551 MAD_above=1.05 lag=-3(1.02/1.05); L252 23.80/1.17 r_next=0.502 MAD_above=1.13 lag=0(1.13/1.13); L253 23.06/1.36 r_next=0.525 MAD_above=1.31 lag=-12(1.22/1.31); L254 23.32/1.16 r_next=0.597 MAD_above=1.12 lag=-13(1.07/1.12); L255 23.85/1.25 r_next=0.493 MAD_above=1.10 lag=-4(1.05/1.10); L256 23.83/1.19 r_next=0.457 MAD_above=1.12 lag=-9(1.02/1.12); L257 24.23/1.08 r_next=0.364 MAD_above=1.09 lag=2(1.09/1.09); L258 24.36/1.10 r_next=0.475 MAD_above=1.09 lag=28(0.99/1.09); L259 24.64/1.16 r_next=0.475 MAD_above=0.98 lag=0(0.98/0.98); L260 24.49/1.10 r_next=0.398 MAD_above=1.03 lag=-4(1.02/1.03); L261 24.32/1.29 r_next=0.440 MAD_above=1.18 lag=-12(1.06/1.18); L262 23.92/1.34 r_next=-0.013 MAD_above=1.25 lag=-4(1.23/1.25); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.872; no internal horizontal blanking run; gate=4.000) |
| 6271 | 6271/F1 | L137 | L262 | L136 22.11/1.92 r_next=0.058 MAD_above=1.82 lag=-26(1.64/1.82); L137 21.74/1.36 r_next=0.037 MAD_above=1.80 lag=27(1.69/1.80); L138 21.84/1.24 r_next=0.019 MAD_above=1.41 lag=-26(1.33/1.41); L247 21.23/1.21 r_next=0.085 MAD_above=1.27 lag=-20(1.18/1.27); L248 20.41/1.30 r_next=0.030 MAD_above=1.50 lag=-23(1.40/1.50); L249 20.25/1.34 r_next=0.081 MAD_above=1.45 lag=28(1.27/1.45); L250 20.42/1.24 r_next=0.043 MAD_above=1.37 lag=-7(1.31/1.37); L251 20.16/1.14 r_next=-0.066 MAD_above=1.30 lag=-12(1.26/1.30); L252 19.98/1.12 r_next=0.224 MAD_above=1.32 lag=-20(1.15/1.32); L253 19.63/1.32 r_next=-0.016 MAD_above=1.21 lag=1(1.20/1.21); L254 19.68/1.32 r_next=0.177 MAD_above=1.45 lag=22(1.40/1.45); L255 19.79/1.42 r_next=0.161 MAD_above=1.41 lag=-5(1.26/1.41); L256 19.51/1.28 r_next=-0.067 MAD_above=1.36 lag=0(1.36/1.36); L257 19.62/1.26 r_next=-0.004 MAD_above=1.49 lag=-30(1.31/1.49); L258 18.74/1.26 r_next=0.131 MAD_above=1.55 lag=-17(1.42/1.55); L259 19.40/1.19 r_next=-0.010 MAD_above=1.38 lag=19(1.29/1.38); L260 19.59/1.20 r_next=0.165 MAD_above=1.32 lag=23(1.24/1.32); L261 19.83/1.25 r_next=-0.057 MAD_above=1.25 lag=0(1.25/1.25); L262 19.28/1.30 r_next=-0.023 MAD_above=1.51 lag=12(1.39/1.51); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.056; no internal horizontal blanking run; gate=4.000) |
| 6272 | 6272/F1 | L115 | L262 | L114 18.92/2.13 r_next=0.168 MAD_above=3.21 lag=30(2.83/3.21); L115 19.02/1.95 r_next=0.153 MAD_above=2.16 lag=-29(1.99/2.16); L116 19.32/1.75 r_next=-0.116 MAD_above=1.93 lag=0(1.93/1.93); L247 19.13/1.22 r_next=0.109 MAD_above=1.37 lag=-31(1.20/1.37); L248 19.36/1.22 r_next=0.067 MAD_above=1.28 lag=2(1.27/1.28); L249 18.93/1.10 r_next=0.070 MAD_above=1.29 lag=-31(1.20/1.29); L250 18.91/1.26 r_next=0.032 MAD_above=1.25 lag=28(1.06/1.25); L251 18.77/1.31 r_next=0.139 MAD_above=1.39 lag=-18(1.31/1.39); L252 18.83/1.32 r_next=0.082 MAD_above=1.35 lag=25(1.31/1.35); L253 18.86/1.23 r_next=0.047 MAD_above=1.36 lag=-30(1.27/1.36); L254 18.67/1.14 r_next=-0.175 MAD_above=1.27 lag=6(1.19/1.27); L255 18.32/1.22 r_next=0.195 MAD_above=1.45 lag=28(1.24/1.45); L256 18.83/1.33 r_next=0.112 MAD_above=1.33 lag=4(1.29/1.33); L257 18.73/1.07 r_next=-0.055 MAD_above=1.27 lag=-32(1.22/1.27); L258 18.85/1.07 r_next=0.019 MAD_above=1.21 lag=-24(1.07/1.21); L259 18.59/1.05 r_next=0.013 MAD_above=1.17 lag=-9(1.00/1.17); L260 18.73/1.14 r_next=0.042 MAD_above=1.22 lag=17(1.10/1.22); L261 18.62/1.17 r_next=-0.060 MAD_above=1.22 lag=-20(1.20/1.22); L262 17.83/1.14 r_next=0.044 MAD_above=1.43 lag=29(1.32/1.43); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.058; no internal horizontal blanking run; gate=4.000) |
| 6273 | 6273/F1 | L259 | L262 | L258 16.89/3.25 r_next=-0.045 MAD_above=3.02 lag=-27(2.85/3.02); L259 16.82/1.48 r_next=-0.088 MAD_above=2.73 lag=28(2.49/2.73); L260 17.10/1.32 r_next=0.071 MAD_above=1.63 lag=-18(1.36/1.63); L261 16.96/1.34 r_next=0.137 MAD_above=1.43 lag=-5(1.32/1.43); L262 15.24/2.71 r_next=0.037 MAD_above=2.74 lag=-12(2.50/2.74); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.051; no internal horizontal blanking run; gate=4.000) |
| 6278 | 6278/F1 | L194 | L261 | L193 4.56/1.91 r_next=0.249 MAD_above=1.97 lag=-7(1.85/1.97); L194 5.31/1.82 r_next=-0.018 MAD_above=2.03 lag=2(1.99/2.03); L195 5.19/1.80 r_next=-0.012 MAD_above=2.05 lag=11(1.70/2.05); L247 6.70/1.57 r_next=0.038 MAD_above=1.67 lag=2(1.61/1.67); L248 5.69/1.50 r_next=0.055 MAD_above=1.88 lag=-5(1.70/1.88); L249 6.47/1.56 r_next=0.056 MAD_above=1.76 lag=-6(1.65/1.76); L250 6.12/1.46 r_next=-0.079 MAD_above=1.64 lag=-18(1.58/1.64); L251 5.11/1.41 r_next=-0.043 MAD_above=1.82 lag=22(1.63/1.82); L252 6.33/1.60 r_next=0.096 MAD_above=1.98 lag=24(1.82/1.98); L253 5.71/1.54 r_next=-0.097 MAD_above=1.69 lag=25(1.60/1.69); L254 6.26/1.37 r_next=0.032 MAD_above=1.82 lag=-21(1.54/1.82); L255 6.28/1.51 r_next=0.065 MAD_above=1.56 lag=-21(1.43/1.56); L256 6.58/1.51 r_next=0.048 MAD_above=1.64 lag=15(1.49/1.64); L257 5.94/1.71 r_next=0.164 MAD_above=1.83 lag=-5(1.71/1.83); L258 6.70/1.44 r_next=0.093 MAD_above=1.76 lag=-1(1.74/1.76); L259 6.42/1.68 r_next=0.011 MAD_above=1.69 lag=28(1.56/1.69); L260 6.71/1.41 r_next=-0.096 MAD_above=1.67 lag=28(1.60/1.67); L261 5.61/1.51 r_next=0.075 MAD_above=1.96 lag=-32(1.74/1.96); L262 6.35/1.56 r_next=-0.008 MAD_above=1.78 lag=31(1.55/1.78); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.072; no internal horizontal blanking run; gate=4.000) |
| 6279 | 6279/F1 | L75 | L259 | L74 9.85/3.52 r_next=-0.005 MAD_above=3.80 lag=-7(3.27/3.80); L75 9.52/1.77 r_next=0.118 MAD_above=3.09 lag=-21(2.87/3.09); L76 9.69/1.78 r_next=0.179 MAD_above=1.96 lag=-16(1.85/1.96); L247 8.76/1.27 r_next=0.132 MAD_above=1.53 lag=24(1.38/1.53); L248 8.75/1.28 r_next=-0.009 MAD_above=1.27 lag=-1(1.27/1.27); L249 8.91/1.43 r_next=0.035 MAD_above=1.46 lag=8(1.31/1.46); L250 8.59/1.27 r_next=0.100 MAD_above=1.43 lag=-32(1.32/1.43); L251 8.66/1.30 r_next=-0.072 MAD_above=1.30 lag=13(1.27/1.30); L252 8.57/1.17 r_next=-0.064 MAD_above=1.40 lag=32(1.24/1.40); L253 8.43/1.18 r_next=0.017 MAD_above=1.32 lag=-10(1.11/1.32); L254 8.17/1.39 r_next=-0.001 MAD_above=1.40 lag=-9(1.28/1.40); L255 8.23/1.28 r_next=0.129 MAD_above=1.48 lag=-18(1.34/1.48); L256 8.23/1.34 r_next=-0.078 MAD_above=1.37 lag=12(1.30/1.37); L257 7.97/1.27 r_next=0.051 MAD_above=1.48 lag=29(1.30/1.48); L258 8.10/1.33 r_next=0.122 MAD_above=1.38 lag=-23(1.28/1.38); L259 7.91/1.24 r_next=-0.001 MAD_above=1.34 lag=-22(1.31/1.34); L260 7.85/1.19 r_next=0.149 MAD_above=1.32 lag=-28(1.19/1.32); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.081; no internal horizontal blanking run; gate=4.000) |
| 6280 | 6280/F1 | L207 | L261 | L206 9.69/2.19 r_next=0.488 MAD_above=1.98 lag=3(1.93/1.98); L207 9.64/1.84 r_next=0.441 MAD_above=1.72 lag=0(1.72/1.72); L208 10.44/1.80 r_next=0.298 MAD_above=1.98 lag=10(1.80/1.98); L247 10.88/1.28 r_next=-0.039 MAD_above=1.59 lag=-16(1.39/1.59); L248 11.28/1.58 r_next=-0.047 MAD_above=1.69 lag=-16(1.47/1.69); L249 11.10/1.46 r_next=0.214 MAD_above=1.73 lag=7(1.58/1.73); L250 11.30/1.44 r_next=0.139 MAD_above=1.46 lag=23(1.37/1.46); L251 10.83/1.41 r_next=0.088 MAD_above=1.54 lag=-31(1.37/1.54); L252 10.49/1.33 r_next=0.129 MAD_above=1.48 lag=13(1.40/1.48); L253 10.67/1.45 r_next=0.025 MAD_above=1.42 lag=0(1.42/1.42); L254 10.45/1.31 r_next=0.140 MAD_above=1.51 lag=-12(1.40/1.51); L255 10.40/1.24 r_next=0.089 MAD_above=1.28 lag=6(1.15/1.28); L256 10.49/1.29 r_next=0.231 MAD_above=1.31 lag=27(1.23/1.31); L257 10.32/1.59 r_next=0.142 MAD_above=1.40 lag=0(1.40/1.40); L258 10.51/1.30 r_next=-0.011 MAD_above=1.48 lag=-1(1.46/1.48); L259 10.35/1.43 r_next=-0.032 MAD_above=1.53 lag=-12(1.33/1.53); L260 10.62/1.59 r_next=-0.070 MAD_above=1.68 lag=16(1.45/1.68); L261 10.40/1.51 r_next=0.138 MAD_above=1.77 lag=-15(1.57/1.77); L262 10.66/1.34 r_next=-0.001 MAD_above=1.45 lag=24(1.44/1.45); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.070; no internal horizontal blanking run; gate=4.000) |
| 6281 | 6281/F1 | L215 | L261 | L214 13.09/2.23 r_next=0.449 MAD_above=2.17 lag=16(2.12/2.17); L215 12.95/1.63 r_next=0.270 MAD_above=2.05 lag=12(1.76/2.05); L216 12.25/1.83 r_next=0.104 MAD_above=2.07 lag=25(1.93/2.07); L247 12.20/1.35 r_next=-0.119 MAD_above=1.53 lag=-13(1.37/1.53); L248 12.35/1.31 r_next=-0.090 MAD_above=1.57 lag=-9(1.38/1.57); L249 11.80/1.40 r_next=0.078 MAD_above=1.68 lag=25(1.37/1.68); L250 12.10/1.28 r_next=0.057 MAD_above=1.46 lag=30(1.30/1.46); L251 11.77/1.28 r_next=0.066 MAD_above=1.43 lag=2(1.38/1.43); L252 11.86/1.25 r_next=0.028 MAD_above=1.36 lag=-5(1.28/1.36); L253 11.90/1.42 r_next=0.050 MAD_above=1.46 lag=4(1.41/1.46); L254 11.66/1.25 r_next=0.044 MAD_above=1.46 lag=11(1.34/1.46); L255 12.08/1.40 r_next=0.112 MAD_above=1.43 lag=-27(1.32/1.43); L256 12.06/1.42 r_next=-0.020 MAD_above=1.45 lag=-13(1.39/1.45); L257 12.08/1.28 r_next=0.011 MAD_above=1.47 lag=15(1.38/1.47); L258 11.64/1.45 r_next=0.034 MAD_above=1.53 lag=-17(1.41/1.53); L259 11.40/1.37 r_next=0.082 MAD_above=1.55 lag=22(1.33/1.55); L260 11.14/1.38 r_next=-0.045 MAD_above=1.46 lag=-18(1.38/1.46); L261 11.80/1.25 r_next=0.067 MAD_above=1.60 lag=-13(1.38/1.60); L262 11.95/1.28 r_next=-0.010 MAD_above=1.38 lag=-21(1.20/1.38); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.093; no internal horizontal blanking run; gate=4.000) |
| 6282 | 6282/F1 | L212 | L261 | L211 14.26/2.42 r_next=0.564 MAD_above=2.19 lag=14(2.08/2.19); L212 14.33/1.81 r_next=0.108 MAD_above=1.99 lag=3(1.81/1.99); L213 13.97/1.53 r_next=-0.001 MAD_above=2.03 lag=18(1.68/2.03); L247 14.15/1.43 r_next=-0.077 MAD_above=1.53 lag=24(1.35/1.53); L248 14.06/1.27 r_next=0.033 MAD_above=1.56 lag=-10(1.37/1.56); L249 13.94/1.37 r_next=0.020 MAD_above=1.43 lag=24(1.27/1.43); L250 14.16/1.34 r_next=0.035 MAD_above=1.52 lag=-15(1.37/1.52); L251 13.47/1.31 r_next=0.033 MAD_above=1.55 lag=-20(1.51/1.55); L252 13.93/1.40 r_next=0.079 MAD_above=1.52 lag=-16(1.44/1.52); L253 13.96/1.38 r_next=0.192 MAD_above=1.49 lag=-20(1.41/1.49); L254 13.60/1.35 r_next=0.213 MAD_above=1.38 lag=-3(1.35/1.38); L255 13.79/1.37 r_next=-0.036 MAD_above=1.35 lag=-3(1.34/1.35); L256 13.69/1.45 r_next=0.006 MAD_above=1.58 lag=29(1.37/1.58); L257 13.63/1.33 r_next=0.089 MAD_above=1.53 lag=26(1.37/1.53); L258 13.00/1.40 r_next=0.078 MAD_above=1.51 lag=6(1.41/1.51); L259 13.15/1.31 r_next=0.089 MAD_above=1.43 lag=-2(1.39/1.43); L260 13.27/1.26 r_next=-0.044 MAD_above=1.41 lag=-6(1.24/1.41); L261 13.35/1.41 r_next=0.097 MAD_above=1.54 lag=-26(1.36/1.54); L262 13.38/1.31 r_next=-0.026 MAD_above=1.45 lag=4(1.39/1.45); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.083; no internal horizontal blanking run; gate=4.000) |
| 6283 | 6283/F1 | L213 | L259 | L212 14.25/2.51 r_next=0.678 MAD_above=1.69 lag=0(1.69/1.69); L213 14.62/2.21 r_next=0.564 MAD_above=1.95 lag=32(1.86/1.95); L214 15.10/1.67 r_next=0.228 MAD_above=1.99 lag=31(1.80/1.99); L247 15.57/1.40 r_next=-0.093 MAD_above=1.50 lag=-32(1.34/1.50); L248 15.60/1.14 r_next=0.125 MAD_above=1.47 lag=-15(1.27/1.47); L249 15.30/1.33 r_next=0.019 MAD_above=1.31 lag=24(1.22/1.31); L250 15.13/1.33 r_next=0.034 MAD_above=1.45 lag=-8(1.30/1.45); L251 14.22/1.34 r_next=-0.027 MAD_above=1.59 lag=-11(1.51/1.59); L252 14.43/1.19 r_next=-0.002 MAD_above=1.44 lag=32(1.28/1.44); L253 14.94/1.17 r_next=0.118 MAD_above=1.36 lag=28(1.25/1.36); L254 14.88/1.44 r_next=0.170 MAD_above=1.33 lag=-7(1.23/1.33); L255 14.62/1.30 r_next=0.017 MAD_above=1.38 lag=-9(1.34/1.38); L256 14.59/1.26 r_next=0.005 MAD_above=1.44 lag=-9(1.27/1.44); L257 14.21/1.10 r_next=0.128 MAD_above=1.34 lag=-8(1.19/1.34); L258 14.45/1.39 r_next=-0.145 MAD_above=1.30 lag=2(1.29/1.30); L259 14.22/1.40 r_next=0.095 MAD_above=1.70 lag=-11(1.43/1.70); L260 14.16/1.34 r_next=0.109 MAD_above=1.37 lag=-4(1.34/1.37); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.096; no internal horizontal blanking run; gate=4.000) |
| 6284 | 6284/F1 | L215 | L259 | L214 14.54/2.29 r_next=0.674 MAD_above=2.06 lag=11(1.88/2.06); L215 15.31/1.87 r_next=0.508 MAD_above=1.85 lag=1(1.81/1.85); L216 15.15/1.62 r_next=0.166 MAD_above=1.67 lag=1(1.61/1.67); L247 15.61/1.23 r_next=0.012 MAD_above=1.30 lag=9(1.26/1.30); L248 15.63/1.11 r_next=0.245 MAD_above=1.25 lag=26(1.11/1.25); L249 15.31/1.28 r_next=0.006 MAD_above=1.17 lag=25(1.13/1.17); L250 15.37/1.15 r_next=0.079 MAD_above=1.34 lag=7(1.17/1.34); L251 15.01/1.37 r_next=0.058 MAD_above=1.34 lag=-18(1.29/1.34); L252 15.14/1.19 r_next=0.145 MAD_above=1.36 lag=30(1.29/1.36); L253 15.35/1.11 r_next=-0.032 MAD_above=1.13 lag=-4(1.12/1.13); L254 15.16/1.15 r_next=0.148 MAD_above=1.24 lag=-13(1.11/1.24); L255 15.03/1.14 r_next=-0.146 MAD_above=1.16 lag=-12(1.14/1.16); L256 14.99/1.13 r_next=0.043 MAD_above=1.29 lag=29(1.10/1.29); L257 14.63/1.13 r_next=0.085 MAD_above=1.25 lag=-26(1.12/1.25); L258 15.28/1.26 r_next=-0.056 MAD_above=1.35 lag=22(1.33/1.35); L259 15.10/1.27 r_next=0.184 MAD_above=1.37 lag=-16(1.28/1.37); L260 14.95/1.21 r_next=0.116 MAD_above=1.21 lag=-3(1.17/1.21); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.085; no internal horizontal blanking run; gate=4.000) |
| 6289 | 6289/F1 | L239 | L262 | L238 16.15/2.50 r_next=0.217 MAD_above=2.48 lag=-21(2.08/2.48); L239 15.83/1.41 r_next=-0.106 MAD_above=1.93 lag=0(1.93/1.93); L240 16.14/1.34 r_next=-0.073 MAD_above=1.59 lag=9(1.43/1.59); L247 16.40/1.17 r_next=0.063 MAD_above=1.28 lag=25(1.24/1.28); L248 16.50/1.22 r_next=0.011 MAD_above=1.28 lag=-4(1.20/1.28); L249 16.33/1.22 r_next=-0.115 MAD_above=1.35 lag=28(1.28/1.35); L250 16.36/1.24 r_next=-0.083 MAD_above=1.37 lag=11(1.27/1.37); L251 16.34/1.29 r_next=0.053 MAD_above=1.49 lag=23(1.31/1.49); L252 16.58/1.30 r_next=0.008 MAD_above=1.40 lag=-32(1.28/1.40); L253 16.54/1.19 r_next=0.114 MAD_above=1.36 lag=20(1.19/1.36); L254 16.67/1.27 r_next=0.052 MAD_above=1.28 lag=19(1.19/1.28); L255 16.84/1.36 r_next=-0.052 MAD_above=1.38 lag=22(1.28/1.38); L256 17.12/1.40 r_next=-0.152 MAD_above=1.57 lag=7(1.38/1.57); L257 16.74/1.38 r_next=0.003 MAD_above=1.68 lag=32(1.43/1.68); L258 17.42/1.35 r_next=0.167 MAD_above=1.65 lag=27(1.41/1.65); L259 17.31/1.53 r_next=0.121 MAD_above=1.46 lag=-25(1.45/1.46); L260 17.35/1.38 r_next=-0.040 MAD_above=1.47 lag=6(1.45/1.47); L261 17.14/1.47 r_next=-0.048 MAD_above=1.60 lag=-16(1.36/1.60); L262 17.33/1.46 r_next=-0.009 MAD_above=1.71 lag=30(1.45/1.71); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.144; no internal horizontal blanking run; gate=4.000) |
| 6290 | 6290/F1 | L136 | L262 | L135 18.24/0.96 r_next=0.131 MAD_above=0.89 lag=0(0.89/0.89); L136 17.82/1.04 r_next=0.011 MAD_above=1.05 lag=-22(1.01/1.05); L137 17.95/0.95 r_next=0.041 MAD_above=1.09 lag=30(0.93/1.09); L247 16.60/1.32 r_next=0.058 MAD_above=1.39 lag=23(1.28/1.39); L248 16.37/1.15 r_next=0.088 MAD_above=1.34 lag=-8(1.25/1.34); L249 15.96/1.19 r_next=-0.057 MAD_above=1.27 lag=29(1.13/1.27); L250 16.54/1.20 r_next=-0.091 MAD_above=1.45 lag=27(1.32/1.45); L251 16.56/1.27 r_next=-0.016 MAD_above=1.42 lag=19(1.27/1.42); L252 16.38/1.21 r_next=-0.045 MAD_above=1.38 lag=-31(1.24/1.38); L253 16.77/1.19 r_next=0.026 MAD_above=1.43 lag=29(1.23/1.43); L254 16.44/1.26 r_next=-0.057 MAD_above=1.36 lag=20(1.22/1.36); L255 16.42/1.26 r_next=0.023 MAD_above=1.41 lag=25(1.23/1.41); L256 16.38/1.32 r_next=-0.084 MAD_above=1.33 lag=7(1.19/1.33); L257 16.10/1.26 r_next=-0.037 MAD_above=1.45 lag=18(1.37/1.45); L258 16.56/1.29 r_next=0.117 MAD_above=1.50 lag=31(1.28/1.50); L259 16.23/1.27 r_next=0.040 MAD_above=1.32 lag=0(1.32/1.32); L260 16.56/1.27 r_next=0.170 MAD_above=1.39 lag=25(1.29/1.39); L261 16.55/1.40 r_next=0.070 MAD_above=1.32 lag=28(1.29/1.32); L262 16.90/1.38 r_next=-0.025 MAD_above=1.51 lag=29(1.45/1.51); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.174; no internal horizontal blanking run; gate=4.000) |
| 6291 | 6291/F1 | L96 | L260 | L95 17.76/2.92 r_next=0.131 MAD_above=3.17 lag=31(2.73/3.17); L96 16.55/1.97 r_next=0.110 MAD_above=2.73 lag=-8(2.61/2.73); L97 17.05/1.83 r_next=0.086 MAD_above=1.93 lag=27(1.90/1.93); L247 16.15/1.33 r_next=0.009 MAD_above=1.48 lag=32(1.34/1.48); L248 16.15/1.21 r_next=0.112 MAD_above=1.40 lag=-31(1.33/1.40); L249 15.75/1.23 r_next=-0.034 MAD_above=1.29 lag=26(1.28/1.29); L250 16.23/1.29 r_next=-0.063 MAD_above=1.46 lag=28(1.23/1.46); L251 16.33/1.35 r_next=0.056 MAD_above=1.52 lag=-25(1.36/1.52); L252 16.22/1.32 r_next=0.000 MAD_above=1.42 lag=-24(1.33/1.42); L253 16.61/1.25 r_next=0.016 MAD_above=1.43 lag=28(1.24/1.43); L254 16.37/1.28 r_next=-0.027 MAD_above=1.41 lag=20(1.34/1.41); L255 16.20/1.33 r_next=0.043 MAD_above=1.44 lag=14(1.32/1.44); L256 16.27/1.13 r_next=-0.078 MAD_above=1.33 lag=32(1.18/1.33); L257 16.05/1.25 r_next=-0.033 MAD_above=1.27 lag=28(1.19/1.27); L258 16.40/1.29 r_next=0.052 MAD_above=1.43 lag=24(1.25/1.43); L259 16.08/1.32 r_next=-0.040 MAD_above=1.41 lag=22(1.32/1.41); L260 16.57/1.30 r_next=0.152 MAD_above=1.50 lag=17(1.40/1.50); L261 16.42/1.19 r_next=0.074 MAD_above=1.27 lag=-2(1.22/1.27); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.177; no internal horizontal blanking run; gate=4.000) |
| 6292 | 6292/F1 | L252 | L259 | L251 17.16/2.56 r_next=-0.633 MAD_above=3.32 lag=-32(3.06/3.32); L252 15.03/2.68 r_next=-0.699 MAD_above=3.59 lag=-32(3.32/3.59); L253 16.76/2.74 r_next=-0.455 MAD_above=3.61 lag=32(3.41/3.61); L254 15.40/2.49 r_next=-0.288 MAD_above=3.45 lag=32(2.80/3.45); L255 16.74/3.17 r_next=-0.494 MAD_above=3.60 lag=32(2.48/3.60); L256 15.97/2.90 r_next=-0.390 MAD_above=4.24 lag=32(2.83/4.24); L257 15.64/3.91 r_next=-0.608 MAD_above=4.63 lag=32(3.01/4.63); L258 15.85/4.21 r_next=-0.388 MAD_above=5.80 lag=32(4.00/5.80); L259 15.37/4.83 r_next=-0.739 MAD_above=6.13 lag=32(3.25/6.13); L260 14.86/5.45 r_next=-0.879 MAD_above=7.86 lag=32(5.91/7.86); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.194; no internal horizontal blanking run; gate=4.000) |
| 6294 | 6294/F1 | L102 | L262 | L101 18.74/1.50 r_next=0.068 MAD_above=1.57 lag=-3(1.48/1.57); L102 18.07/1.34 r_next=0.165 MAD_above=1.63 lag=-20(1.39/1.63); L103 18.56/1.41 r_next=0.101 MAD_above=1.42 lag=21(1.32/1.42); L247 15.77/1.35 r_next=0.129 MAD_above=1.50 lag=31(1.29/1.50); L248 16.08/1.29 r_next=0.002 MAD_above=1.32 lag=3(1.28/1.32); L249 16.32/1.30 r_next=0.057 MAD_above=1.41 lag=24(1.28/1.41); L250 15.77/1.23 r_next=0.065 MAD_above=1.41 lag=-21(1.28/1.41); L251 16.41/1.22 r_next=0.030 MAD_above=1.40 lag=-8(1.35/1.40); L252 16.10/1.27 r_next=0.110 MAD_above=1.32 lag=28(1.21/1.32); L253 16.02/1.19 r_next=0.032 MAD_above=1.29 lag=-12(1.10/1.29); L254 15.83/1.41 r_next=0.023 MAD_above=1.39 lag=-11(1.27/1.39); L255 16.05/1.23 r_next=-0.033 MAD_above=1.40 lag=15(1.27/1.40); L256 16.00/1.37 r_next=-0.047 MAD_above=1.44 lag=25(1.24/1.44); L257 16.02/1.56 r_next=0.031 MAD_above=1.57 lag=15(1.32/1.57); L258 16.28/1.25 r_next=0.058 MAD_above=1.47 lag=29(1.42/1.47); L259 16.26/1.51 r_next=0.090 MAD_above=1.45 lag=28(1.36/1.45); L260 16.36/1.32 r_next=0.051 MAD_above=1.54 lag=32(1.34/1.54); L261 16.37/1.61 r_next=-0.060 MAD_above=1.57 lag=25(1.49/1.57); L262 16.84/1.37 r_next=-0.014 MAD_above=1.77 lag=-30(1.63/1.77); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.245; no internal horizontal blanking run; gate=4.000) |
| 6296 | 6296/F1 | L244 | L260 | L243 16.94/2.69 r_next=-0.016 MAD_above=2.22 lag=-30(2.08/2.22); L244 17.30/1.42 r_next=-0.144 MAD_above=2.23 lag=32(2.05/2.23); L245 17.32/1.42 r_next=0.194 MAD_above=1.61 lag=-20(1.41/1.61); L247 16.49/1.48 r_next=0.212 MAD_above=1.72 lag=-29(1.51/1.72); L248 16.89/1.47 r_next=0.098 MAD_above=1.48 lag=16(1.43/1.48); L249 17.18/1.41 r_next=-0.004 MAD_above=1.50 lag=-18(1.37/1.50); L250 17.66/1.46 r_next=-0.074 MAD_above=1.67 lag=-21(1.40/1.67); L251 17.63/1.43 r_next=0.179 MAD_above=1.67 lag=24(1.31/1.67); L252 18.05/1.37 r_next=0.148 MAD_above=1.43 lag=26(1.37/1.43); L253 17.67/1.57 r_next=0.073 MAD_above=1.52 lag=32(1.38/1.52); L254 17.59/1.54 r_next=0.117 MAD_above=1.66 lag=-16(1.49/1.66); L255 18.00/1.49 r_next=0.285 MAD_above=1.64 lag=13(1.60/1.64); L256 18.11/1.48 r_next=0.071 MAD_above=1.37 lag=3(1.32/1.37); L257 17.87/1.45 r_next=0.146 MAD_above=1.59 lag=14(1.45/1.59); L258 17.60/1.42 r_next=0.135 MAD_above=1.48 lag=-4(1.36/1.48); L259 18.16/1.58 r_next=0.034 MAD_above=1.63 lag=-12(1.46/1.63); L260 18.00/1.50 r_next=0.003 MAD_above=1.75 lag=19(1.56/1.75); L261 18.43/1.46 r_next=-0.099 MAD_above=1.65 lag=-4(1.56/1.65); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.246; no internal horizontal blanking run; gate=4.000) |
| 6297 | 6297/F1 | L133 | L261 | L132 19.03/1.12 r_next=0.157 MAD_above=1.18 lag=15(1.11/1.18); L133 18.87/1.16 r_next=0.157 MAD_above=1.17 lag=-6(1.11/1.17); L134 18.83/1.10 r_next=0.318 MAD_above=1.13 lag=27(0.95/1.13); L247 17.44/1.36 r_next=0.026 MAD_above=1.47 lag=28(1.24/1.47); L248 17.25/1.40 r_next=0.081 MAD_above=1.51 lag=-18(1.30/1.51); L249 17.30/1.21 r_next=0.044 MAD_above=1.41 lag=23(1.26/1.41); L250 17.56/1.36 r_next=0.121 MAD_above=1.45 lag=-15(1.22/1.45); L251 17.33/1.30 r_next=0.083 MAD_above=1.37 lag=-4(1.30/1.37); L252 17.92/1.24 r_next=0.230 MAD_above=1.41 lag=-15(1.33/1.41); L253 17.51/1.36 r_next=0.128 MAD_above=1.26 lag=2(1.25/1.26); L254 17.60/1.35 r_next=0.004 MAD_above=1.40 lag=-16(1.29/1.40); L255 17.70/1.32 r_next=0.130 MAD_above=1.49 lag=12(1.34/1.49); L256 17.66/1.40 r_next=0.075 MAD_above=1.36 lag=16(1.29/1.36); L257 17.43/1.31 r_next=0.173 MAD_above=1.45 lag=-25(1.34/1.45); L258 17.21/1.37 r_next=0.169 MAD_above=1.35 lag=10(1.30/1.35); L259 17.47/1.31 r_next=0.149 MAD_above=1.37 lag=-30(1.32/1.37); L260 17.59/1.39 r_next=-0.037 MAD_above=1.36 lag=-19(1.31/1.36); L261 17.84/1.50 r_next=0.112 MAD_above=1.65 lag=14(1.50/1.65); L262 17.79/1.38 r_next=-0.012 MAD_above=1.50 lag=5(1.42/1.50); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.240; no internal horizontal blanking run; gate=4.000) |
| 6298 | 6298/F1 | L175 | L261 | L174 18.51/3.24 r_next=0.164 MAD_above=3.15 lag=11(2.91/3.15); L175 17.79/1.94 r_next=0.104 MAD_above=2.65 lag=1(2.62/2.65); L176 18.55/1.56 r_next=0.223 MAD_above=1.85 lag=17(1.74/1.85); L247 17.75/1.15 r_next=0.133 MAD_above=1.18 lag=-9(1.04/1.18); L248 17.57/1.20 r_next=0.157 MAD_above=1.24 lag=-7(1.12/1.24); L249 17.57/1.16 r_next=0.003 MAD_above=1.16 lag=-2(1.13/1.16); L250 17.75/1.16 r_next=0.106 MAD_above=1.29 lag=20(1.14/1.29); L251 17.37/1.19 r_next=0.113 MAD_above=1.23 lag=29(1.18/1.23); L252 17.70/1.22 r_next=0.243 MAD_above=1.28 lag=20(1.07/1.28); L253 17.66/1.19 r_next=0.096 MAD_above=1.13 lag=20(1.11/1.13); L254 17.75/1.15 r_next=0.066 MAD_above=1.25 lag=21(1.09/1.25); L255 17.69/1.25 r_next=0.125 MAD_above=1.33 lag=-13(1.15/1.33); L256 17.51/1.06 r_next=0.216 MAD_above=1.18 lag=-20(1.07/1.18); L257 17.47/1.05 r_next=0.084 MAD_above=1.01 lag=-4(1.00/1.01); L258 17.32/1.19 r_next=0.249 MAD_above=1.16 lag=-15(1.04/1.16); L259 17.29/1.10 r_next=0.193 MAD_above=1.04 lag=0(1.04/1.04); L260 17.34/1.24 r_next=0.081 MAD_above=1.15 lag=15(1.10/1.15); L261 17.31/1.20 r_next=0.030 MAD_above=1.29 lag=-6(1.24/1.29); L262 17.16/1.16 r_next=-0.051 MAD_above=1.24 lag=21(1.16/1.24); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.240; no internal horizontal blanking run; gate=4.000) |
| 6299 | 6299/F1 | L149 | L262 | L148 21.01/1.55 r_next=-0.025 MAD_above=1.65 lag=-4(1.59/1.65); L149 20.71/1.45 r_next=-0.108 MAD_above=1.69 lag=-21(1.55/1.69); L150 20.53/1.32 r_next=0.033 MAD_above=1.56 lag=-28(1.43/1.56); L247 19.27/1.35 r_next=0.173 MAD_above=1.51 lag=-4(1.50/1.51); L248 19.33/1.48 r_next=0.042 MAD_above=1.41 lag=24(1.37/1.41); L249 18.77/1.27 r_next=-0.120 MAD_above=1.57 lag=-12(1.41/1.57); L250 18.74/1.44 r_next=0.090 MAD_above=1.61 lag=-28(1.26/1.61); L251 18.76/1.31 r_next=0.137 MAD_above=1.42 lag=-9(1.33/1.42); L252 18.61/1.32 r_next=-0.034 MAD_above=1.29 lag=3(1.26/1.29); L253 18.65/1.31 r_next=0.087 MAD_above=1.48 lag=-25(1.26/1.48); L254 18.52/1.69 r_next=0.236 MAD_above=1.64 lag=-8(1.49/1.64); L255 18.78/1.48 r_next=0.133 MAD_above=1.56 lag=-12(1.52/1.56); L256 18.97/1.53 r_next=0.191 MAD_above=1.56 lag=-16(1.39/1.56); L257 18.73/1.52 r_next=0.283 MAD_above=1.54 lag=28(1.49/1.54); L258 18.50/1.30 r_next=0.122 MAD_above=1.34 lag=-6(1.30/1.34); L259 18.38/1.48 r_next=0.259 MAD_above=1.49 lag=-17(1.35/1.49); L260 18.31/1.53 r_next=0.211 MAD_above=1.40 lag=2(1.37/1.40); L261 18.22/1.35 r_next=0.027 MAD_above=1.41 lag=3(1.37/1.41); L262 18.23/1.56 r_next=-0.027 MAD_above=1.58 lag=18(1.47/1.58); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.199; no internal horizontal blanking run; gate=4.000) |
| 6300 | 6300/F1 | L191 | L259 | L190 19.26/2.42 r_next=0.212 MAD_above=2.55 lag=12(2.32/2.55); L191 19.68/1.59 r_next=0.175 MAD_above=2.07 lag=-4(1.92/2.07); L192 19.58/1.79 r_next=0.079 MAD_above=1.70 lag=3(1.67/1.70); L247 19.30/1.07 r_next=0.089 MAD_above=1.12 lag=-22(1.02/1.12); L248 19.45/1.09 r_next=0.273 MAD_above=1.15 lag=-25(1.06/1.15); L249 19.58/1.17 r_next=0.097 MAD_above=1.05 lag=3(1.03/1.05); L250 19.32/1.05 r_next=0.249 MAD_above=1.16 lag=29(1.05/1.16); L251 19.16/1.10 r_next=0.134 MAD_above=1.01 lag=13(1.00/1.01); L252 19.31/1.07 r_next=0.041 MAD_above=1.10 lag=-1(1.04/1.10); L253 19.08/1.14 r_next=0.129 MAD_above=1.20 lag=6(1.08/1.20); L254 19.18/1.09 r_next=0.103 MAD_above=1.14 lag=-22(0.95/1.14); L255 18.94/1.08 r_next=0.245 MAD_above=1.14 lag=-31(1.09/1.14); L256 18.91/1.19 r_next=0.211 MAD_above=1.08 lag=-4(1.05/1.08); L257 18.90/1.30 r_next=0.096 MAD_above=1.23 lag=-9(1.19/1.23); L258 18.77/1.14 r_next=0.111 MAD_above=1.28 lag=12(1.23/1.28); L259 18.73/1.24 r_next=0.250 MAD_above=1.23 lag=24(1.09/1.23); L260 18.79/1.11 r_next=0.143 MAD_above=1.13 lag=-1(1.10/1.13); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.196; no internal horizontal blanking run; gate=4.000) |
| 6301 | 6301/F1 | L191 | L259 | L190 19.33/2.41 r_next=0.122 MAD_above=2.47 lag=10(2.27/2.47); L191 19.76/1.54 r_next=0.121 MAD_above=2.12 lag=-4(1.96/2.12); L192 19.42/1.77 r_next=0.045 MAD_above=1.76 lag=19(1.68/1.76); L247 19.52/1.05 r_next=0.156 MAD_above=1.09 lag=31(1.00/1.09); L248 19.76/1.18 r_next=0.222 MAD_above=1.16 lag=-22(1.06/1.16); L249 19.68/1.18 r_next=0.084 MAD_above=1.16 lag=-7(1.11/1.16); L250 19.62/1.08 r_next=0.270 MAD_above=1.19 lag=24(1.07/1.19); L251 19.42/1.20 r_next=0.192 MAD_above=1.04 lag=0(1.04/1.04); L252 19.29/1.11 r_next=0.023 MAD_above=1.12 lag=-13(1.07/1.12); L253 19.12/1.12 r_next=0.097 MAD_above=1.21 lag=22(1.10/1.21); L254 19.32/1.13 r_next=0.115 MAD_above=1.17 lag=-23(1.05/1.17); L255 19.09/1.13 r_next=0.224 MAD_above=1.18 lag=29(1.10/1.18); L256 19.08/1.24 r_next=0.186 MAD_above=1.13 lag=-12(1.07/1.13); L257 19.01/1.28 r_next=0.164 MAD_above=1.24 lag=-9(1.17/1.24); L258 19.13/1.15 r_next=0.084 MAD_above=1.23 lag=-5(1.19/1.23); L259 19.03/1.30 r_next=0.272 MAD_above=1.29 lag=27(1.17/1.29); L260 19.14/1.20 r_next=0.142 MAD_above=1.19 lag=5(1.13/1.19); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.201; no internal horizontal blanking run; gate=4.000) |
| 6302 | 6302/F1 | L165 | L262 | L164 20.07/2.01 r_next=0.041 MAD_above=2.16 lag=-6(2.02/2.16); L165 20.19/1.83 r_next=0.017 MAD_above=2.08 lag=13(1.90/2.08); L166 20.12/1.60 r_next=0.133 MAD_above=1.85 lag=25(1.63/1.85); L247 18.59/1.01 r_next=0.115 MAD_above=1.06 lag=-9(0.96/1.06); L248 19.16/1.02 r_next=0.199 MAD_above=1.13 lag=31(1.04/1.13); L249 19.15/1.13 r_next=0.148 MAD_above=1.04 lag=28(0.99/1.04); L250 19.02/1.13 r_next=0.279 MAD_above=1.13 lag=17(1.03/1.13); L251 18.62/0.99 r_next=0.207 MAD_above=0.99 lag=0(0.99/0.99); L252 18.60/0.93 r_next=0.033 MAD_above=0.89 lag=-6(0.84/0.89); L253 18.49/1.00 r_next=0.114 MAD_above=1.05 lag=12(0.95/1.05); L254 18.58/1.11 r_next=0.150 MAD_above=1.08 lag=-25(0.97/1.08); L255 18.44/1.03 r_next=0.157 MAD_above=1.08 lag=-19(0.96/1.08); L256 18.43/1.12 r_next=0.281 MAD_above=1.07 lag=-6(0.96/1.07); L257 18.46/1.12 r_next=0.244 MAD_above=1.01 lag=14(0.96/1.01); L258 18.48/0.96 r_next=0.123 MAD_above=0.97 lag=-6(0.92/0.97); L259 18.33/1.18 r_next=0.257 MAD_above=1.11 lag=-19(0.98/1.11); L260 18.34/0.92 r_next=0.135 MAD_above=0.98 lag=0(0.98/0.98); L261 18.22/0.94 r_next=0.040 MAD_above=0.93 lag=-5(0.89/0.93); L262 18.48/1.01 r_next=0.016 MAD_above=1.04 lag=24(0.97/1.04); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.180; no internal horizontal blanking run; gate=4.000) |
| 6303 | 6303/F1 | L170 | L262 | L169 19.52/2.18 r_next=0.054 MAD_above=2.29 lag=5(2.18/2.29); L170 18.85/1.88 r_next=0.024 MAD_above=2.20 lag=-8(2.11/2.20); L171 18.43/1.57 r_next=0.056 MAD_above=1.99 lag=26(1.77/1.99); L247 18.82/0.93 r_next=0.218 MAD_above=0.97 lag=-27(0.92/0.97); L248 19.32/1.05 r_next=0.263 MAD_above=0.99 lag=27(0.89/0.99); L249 19.28/1.15 r_next=0.160 MAD_above=1.03 lag=26(1.00/1.03); L250 18.90/0.97 r_next=0.205 MAD_above=1.11 lag=24(0.99/1.11); L251 18.95/1.07 r_next=0.178 MAD_above=0.97 lag=24(0.93/0.97); L252 18.76/0.98 r_next=0.248 MAD_above=0.99 lag=20(0.92/0.99); L253 18.99/1.10 r_next=0.113 MAD_above=1.03 lag=-4(0.94/1.03); L254 18.98/1.01 r_next=0.203 MAD_above=1.07 lag=-18(0.94/1.07); L255 18.84/0.99 r_next=0.157 MAD_above=1.00 lag=-4(0.91/1.00); L256 18.61/1.02 r_next=0.307 MAD_above=1.01 lag=-17(0.91/1.01); L257 18.73/1.00 r_next=0.141 MAD_above=0.89 lag=6(0.85/0.89); L258 18.70/0.88 r_next=0.098 MAD_above=0.92 lag=10(0.86/0.92); L259 18.67/1.03 r_next=0.257 MAD_above=0.99 lag=23(0.89/0.99); L260 18.88/0.90 r_next=0.113 MAD_above=0.88 lag=0(0.88/0.88); L261 18.73/0.87 r_next=0.163 MAD_above=0.87 lag=-6(0.83/0.87); L262 19.03/1.07 r_next=-0.085 MAD_above=0.96 lag=30(0.93/0.96); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.212; no internal horizontal blanking run; gate=4.000) |
| 6304 | 6304/F1 | L146 | L262 | L145 17.92/2.07 r_next=0.090 MAD_above=2.54 lag=12(2.20/2.54); L146 18.13/1.58 r_next=0.065 MAD_above=1.92 lag=-4(1.81/1.92); L147 18.30/1.55 r_next=0.080 MAD_above=1.71 lag=-24(1.53/1.71); L247 18.96/0.94 r_next=0.077 MAD_above=0.88 lag=29(0.87/0.88); L248 19.02/0.92 r_next=0.116 MAD_above=0.91 lag=28(0.88/0.91); L249 19.14/0.95 r_next=0.239 MAD_above=0.96 lag=15(0.91/0.96); L250 18.94/1.07 r_next=0.354 MAD_above=0.98 lag=29(0.89/0.98); L251 18.85/1.05 r_next=0.215 MAD_above=0.90 lag=-2(0.90/0.90); L252 18.83/0.91 r_next=0.115 MAD_above=0.94 lag=2(0.89/0.94); L253 18.73/0.93 r_next=0.182 MAD_above=0.92 lag=5(0.90/0.92); L254 18.73/0.95 r_next=0.192 MAD_above=0.91 lag=-24(0.88/0.91); L255 18.51/0.96 r_next=0.130 MAD_above=0.94 lag=19(0.89/0.94); L256 18.05/1.06 r_next=0.291 MAD_above=1.06 lag=-14(1.01/1.06); L257 18.41/1.04 r_next=0.204 MAD_above=0.99 lag=2(0.96/0.99); L258 18.60/0.95 r_next=0.215 MAD_above=0.97 lag=30(0.87/0.97); L259 18.47/1.08 r_next=0.167 MAD_above=0.98 lag=-15(0.89/0.98); L260 18.50/0.86 r_next=0.089 MAD_above=0.97 lag=6(0.87/0.97); L261 18.32/0.97 r_next=0.084 MAD_above=0.95 lag=4(0.86/0.95); L262 18.44/1.01 r_next=0.036 MAD_above=1.03 lag=-14(0.96/1.03); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.232; no internal horizontal blanking run; gate=4.000) |
| 6305 | 6305/F1 | L137 | L259 | L136 19.84/1.60 r_next=0.132 MAD_above=1.75 lag=5(1.64/1.75); L137 19.58/1.40 r_next=0.189 MAD_above=1.54 lag=-29(1.44/1.54); L138 19.23/1.26 r_next=0.150 MAD_above=1.32 lag=26(1.23/1.32); L247 18.66/1.21 r_next=0.064 MAD_above=1.21 lag=31(1.10/1.21); L248 18.80/1.23 r_next=0.118 MAD_above=1.28 lag=22(1.13/1.28); L249 18.89/1.12 r_next=0.076 MAD_above=1.20 lag=28(1.12/1.20); L250 18.81/1.09 r_next=0.123 MAD_above=1.14 lag=-8(1.04/1.14); L251 19.06/1.10 r_next=0.068 MAD_above=1.13 lag=1(1.10/1.13); L252 19.06/1.02 r_next=0.104 MAD_above=1.09 lag=16(0.96/1.09); L253 18.54/1.16 r_next=0.112 MAD_above=1.22 lag=18(1.07/1.22); L254 18.26/1.09 r_next=0.082 MAD_above=1.18 lag=-19(0.98/1.18); L255 18.13/1.02 r_next=0.218 MAD_above=1.08 lag=22(0.98/1.08); L256 18.46/1.09 r_next=0.115 MAD_above=1.04 lag=32(1.01/1.04); L257 18.67/1.04 r_next=0.094 MAD_above=1.08 lag=19(1.00/1.08); L258 18.31/1.04 r_next=0.148 MAD_above=1.13 lag=-23(1.00/1.13); L259 18.04/1.11 r_next=0.225 MAD_above=1.12 lag=-22(1.00/1.12); L260 17.97/1.15 r_next=0.261 MAD_above=1.10 lag=24(0.98/1.10); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.242; no internal horizontal blanking run; gate=4.000) |
| 6306 | 6306/F1 | L116 | L260 | L115 17.99/4.36 r_next=0.108 MAD_above=3.25 lag=-6(2.95/3.25); L116 18.94/1.55 r_next=0.114 MAD_above=2.85 lag=2(2.80/2.85); L117 19.04/1.57 r_next=0.088 MAD_above=1.59 lag=11(1.48/1.59); L247 18.56/1.08 r_next=0.144 MAD_above=1.13 lag=-31(1.04/1.13); L248 18.61/1.20 r_next=0.146 MAD_above=1.12 lag=4(1.08/1.12); L249 18.61/1.15 r_next=0.132 MAD_above=1.14 lag=-7(1.11/1.14); L250 18.55/1.05 r_next=0.054 MAD_above=1.11 lag=18(1.07/1.11); L251 18.46/1.09 r_next=0.100 MAD_above=1.10 lag=-30(0.98/1.10); L252 18.72/1.11 r_next=0.176 MAD_above=1.15 lag=22(1.05/1.15); L253 18.53/1.15 r_next=0.081 MAD_above=1.08 lag=-3(1.04/1.08); L254 18.33/1.14 r_next=0.065 MAD_above=1.22 lag=-16(0.97/1.22); L255 18.10/1.10 r_next=0.148 MAD_above=1.12 lag=-9(1.04/1.12); L256 18.12/1.16 r_next=0.136 MAD_above=1.11 lag=3(1.02/1.11); L257 18.19/1.21 r_next=0.139 MAD_above=1.20 lag=-7(1.12/1.20); L258 18.26/1.09 r_next=0.175 MAD_above=1.13 lag=23(1.07/1.13); L259 18.07/1.13 r_next=0.127 MAD_above=1.13 lag=5(1.05/1.13); L260 18.05/1.08 r_next=0.139 MAD_above=1.12 lag=11(1.06/1.12); L261 18.01/1.12 r_next=0.091 MAD_above=1.06 lag=-5(1.00/1.06); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.217; no internal horizontal blanking run; gate=4.000) |
| 6307 | 6307/F1 | L116 | L260 | L115 17.62/4.34 r_next=0.103 MAD_above=3.30 lag=26(2.96/3.30); L116 18.67/1.51 r_next=0.105 MAD_above=2.90 lag=2(2.86/2.90); L117 18.76/1.66 r_next=0.094 MAD_above=1.64 lag=-6(1.51/1.64); L247 18.47/1.10 r_next=0.124 MAD_above=1.17 lag=-29(1.12/1.17); L248 18.62/1.18 r_next=0.163 MAD_above=1.16 lag=9(1.09/1.16); L249 18.67/1.17 r_next=0.073 MAD_above=1.15 lag=-7(1.09/1.15); L250 18.59/1.13 r_next=0.103 MAD_above=1.20 lag=14(1.12/1.20); L251 18.40/1.15 r_next=0.076 MAD_above=1.18 lag=-29(1.04/1.18); L252 18.66/1.15 r_next=0.108 MAD_above=1.23 lag=21(1.14/1.23); L253 18.57/1.18 r_next=0.014 MAD_above=1.18 lag=28(1.11/1.18); L254 18.39/1.19 r_next=0.063 MAD_above=1.32 lag=-18(1.03/1.32); L255 18.12/1.12 r_next=0.208 MAD_above=1.15 lag=21(1.05/1.15); L256 18.26/1.23 r_next=0.163 MAD_above=1.10 lag=2(1.08/1.10); L257 18.32/1.31 r_next=0.158 MAD_above=1.29 lag=-4(1.19/1.29); L258 18.23/1.13 r_next=0.175 MAD_above=1.18 lag=-7(1.15/1.18); L259 17.97/1.20 r_next=0.121 MAD_above=1.16 lag=3(1.14/1.16); L260 17.93/1.14 r_next=0.096 MAD_above=1.17 lag=7(1.07/1.17); L261 18.04/1.14 r_next=0.149 MAD_above=1.13 lag=-7(1.05/1.13); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.225; no internal horizontal blanking run; gate=4.000) |
| 6308 | 6308/F1 | L114 | L262 | L113 19.08/2.48 r_next=0.181 MAD_above=2.38 lag=-23(2.16/2.38); L114 17.94/1.99 r_next=0.086 MAD_above=2.47 lag=-29(2.39/2.47); L115 18.28/1.99 r_next=0.047 MAD_above=2.20 lag=32(1.99/2.20); L247 17.15/1.21 r_next=0.222 MAD_above=1.26 lag=32(1.15/1.26); L248 17.36/1.13 r_next=0.208 MAD_above=1.13 lag=-5(1.12/1.13); L249 17.19/1.19 r_next=0.164 MAD_above=1.14 lag=28(1.04/1.14); L250 17.12/1.20 r_next=0.073 MAD_above=1.22 lag=-7(1.08/1.22); L251 16.97/1.10 r_next=0.037 MAD_above=1.25 lag=15(1.05/1.25); L252 17.28/1.18 r_next=0.162 MAD_above=1.26 lag=15(1.10/1.26); L253 17.13/1.20 r_next=0.073 MAD_above=1.21 lag=7(1.11/1.21); L254 16.99/1.18 r_next=0.149 MAD_above=1.23 lag=23(1.07/1.23); L255 16.69/1.16 r_next=0.152 MAD_above=1.18 lag=-19(1.08/1.18); L256 16.69/1.09 r_next=0.086 MAD_above=1.13 lag=27(1.01/1.13); L257 16.74/1.03 r_next=0.117 MAD_above=1.10 lag=6(1.01/1.10); L258 16.76/1.15 r_next=0.178 MAD_above=1.13 lag=-19(1.06/1.13); L259 16.68/1.14 r_next=0.072 MAD_above=1.11 lag=-14(1.08/1.11); L260 16.69/1.11 r_next=0.121 MAD_above=1.14 lag=26(1.07/1.14); L261 16.76/1.16 r_next=0.174 MAD_above=1.13 lag=-8(1.01/1.13); L262 16.99/1.60 r_next=-0.038 MAD_above=1.38 lag=-7(1.33/1.38); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.273; no internal horizontal blanking run; gate=4.000) |
| 6309 | 6309/F1 | L116 | L260 | L115 18.86/2.17 r_next=0.006 MAD_above=2.09 lag=-4(2.02/2.09); L116 17.84/1.96 r_next=-0.012 MAD_above=2.43 lag=23(2.20/2.43); L117 18.04/1.92 r_next=0.100 MAD_above=2.20 lag=-7(1.87/2.20); L247 17.41/1.24 r_next=0.068 MAD_above=1.16 lag=19(1.05/1.16); L248 17.52/1.11 r_next=0.127 MAD_above=1.24 lag=32(1.05/1.24); L249 17.29/1.09 r_next=0.230 MAD_above=1.16 lag=30(1.04/1.16); L250 17.40/1.10 r_next=0.140 MAD_above=1.04 lag=-11(0.98/1.04); L251 17.27/1.19 r_next=0.102 MAD_above=1.15 lag=12(1.00/1.15); L252 17.01/1.13 r_next=0.067 MAD_above=1.23 lag=29(1.06/1.23); L253 17.15/1.03 r_next=0.047 MAD_above=1.12 lag=19(1.03/1.12); L254 17.05/1.06 r_next=0.133 MAD_above=1.12 lag=-26(1.01/1.12); L255 16.83/1.09 r_next=0.160 MAD_above=1.07 lag=-20(1.02/1.07); L256 16.66/1.02 r_next=0.178 MAD_above=1.01 lag=-4(0.97/1.01); L257 16.49/0.96 r_next=0.231 MAD_above=0.96 lag=-17(0.92/0.96); L258 16.68/1.04 r_next=0.127 MAD_above=0.95 lag=-8(0.84/0.95); L259 16.66/1.01 r_next=-0.011 MAD_above=1.06 lag=-19(0.97/1.06); L260 16.64/1.10 r_next=0.073 MAD_above=1.16 lag=7(1.02/1.16); L261 16.73/1.11 r_next=0.102 MAD_above=1.17 lag=-7(1.04/1.17); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.288; no internal horizontal blanking run; gate=4.000) |
| 6310 | 6310/F1 | L111 | L261 | L110 18.63/2.32 r_next=0.174 MAD_above=2.09 lag=28(1.95/2.09); L111 18.72/1.94 r_next=0.221 MAD_above=2.16 lag=-21(2.01/2.16); L112 18.97/1.96 r_next=0.099 MAD_above=1.88 lag=1(1.88/1.88); L247 16.79/1.29 r_next=0.120 MAD_above=1.29 lag=-19(1.17/1.29); L248 16.27/1.18 r_next=0.187 MAD_above=1.35 lag=11(1.26/1.35); L249 16.67/1.32 r_next=0.083 MAD_above=1.31 lag=23(1.23/1.31); L250 16.29/1.16 r_next=0.094 MAD_above=1.35 lag=32(1.27/1.35); L251 16.19/1.32 r_next=0.125 MAD_above=1.28 lag=31(1.19/1.28); L252 16.12/1.18 r_next=0.135 MAD_above=1.22 lag=7(1.21/1.22); L253 16.36/1.13 r_next=0.137 MAD_above=1.16 lag=2(1.15/1.16); L254 16.52/1.35 r_next=0.104 MAD_above=1.26 lag=9(1.20/1.26); L255 16.32/1.31 r_next=0.119 MAD_above=1.38 lag=-25(1.20/1.38); L256 16.12/1.16 r_next=0.163 MAD_above=1.26 lag=15(1.11/1.26); L257 16.43/1.19 r_next=0.179 MAD_above=1.18 lag=-21(1.14/1.18); L258 16.18/1.13 r_next=0.161 MAD_above=1.14 lag=-6(1.09/1.14); L259 16.26/1.11 r_next=0.093 MAD_above=1.09 lag=26(1.02/1.09); L260 16.35/1.20 r_next=0.171 MAD_above=1.19 lag=-22(1.06/1.19); L261 16.71/1.30 r_next=0.242 MAD_above=1.28 lag=14(1.25/1.28); L262 16.52/1.15 r_next=0.006 MAD_above=1.15 lag=-2(1.14/1.15); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.315; no internal horizontal blanking run; gate=4.000) |
| 6311 | 6311/F1 | L107 | L262 | L106 17.50/2.02 r_next=0.041 MAD_above=2.70 lag=-7(2.38/2.70); L107 17.47/1.79 r_next=0.121 MAD_above=2.14 lag=22(1.95/2.14); L108 17.81/1.66 r_next=0.086 MAD_above=1.86 lag=32(1.70/1.86); L247 16.45/1.13 r_next=0.118 MAD_above=1.27 lag=15(1.14/1.27); L248 16.28/1.24 r_next=0.248 MAD_above=1.19 lag=13(1.09/1.19); L249 16.20/1.38 r_next=0.106 MAD_above=1.24 lag=1(1.17/1.24); L250 16.22/1.14 r_next=0.035 MAD_above=1.28 lag=-6(1.22/1.28); L251 15.85/1.13 r_next=0.072 MAD_above=1.25 lag=-8(1.11/1.25); L252 16.01/1.13 r_next=0.227 MAD_above=1.20 lag=-30(1.12/1.20); L253 16.29/1.22 r_next=0.046 MAD_above=1.13 lag=3(1.10/1.13); L254 16.21/1.22 r_next=0.181 MAD_above=1.24 lag=-10(1.13/1.24); L255 16.20/1.12 r_next=0.139 MAD_above=1.14 lag=-3(1.08/1.14); L256 15.98/1.18 r_next=0.063 MAD_above=1.16 lag=15(1.06/1.16); L257 16.20/1.17 r_next=0.121 MAD_above=1.23 lag=28(1.17/1.23); L258 15.90/1.13 r_next=0.095 MAD_above=1.23 lag=-22(1.06/1.23); L259 16.26/1.10 r_next=0.005 MAD_above=1.20 lag=26(1.12/1.20); L260 16.01/1.16 r_next=0.112 MAD_above=1.25 lag=-23(1.10/1.25); L261 16.62/1.07 r_next=0.164 MAD_above=1.21 lag=32(1.16/1.21); L262 16.04/1.24 r_next=0.000 MAD_above=1.26 lag=-12(1.20/1.26); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.299; no internal horizontal blanking run; gate=4.000) |
| 6312 | 6312/F1 | L107 | L262 | L106 18.53/2.57 r_next=0.010 MAD_above=2.59 lag=15(2.38/2.59); L107 17.93/1.85 r_next=0.143 MAD_above=2.60 lag=-17(2.19/2.60); L108 18.26/1.63 r_next=0.109 MAD_above=1.84 lag=1(1.82/1.84); L247 16.32/1.07 r_next=0.158 MAD_above=1.20 lag=30(1.15/1.20); L248 16.31/1.24 r_next=0.144 MAD_above=1.16 lag=3(1.10/1.16); L249 15.85/1.30 r_next=0.189 MAD_above=1.32 lag=-7(1.19/1.32); L250 16.32/1.26 r_next=0.129 MAD_above=1.29 lag=2(1.27/1.29); L251 16.16/1.19 r_next=0.069 MAD_above=1.24 lag=24(1.12/1.24); L252 16.41/1.04 r_next=0.099 MAD_above=1.19 lag=-32(1.07/1.19); L253 16.65/1.22 r_next=0.157 MAD_above=1.18 lag=24(1.08/1.18); L254 16.43/1.27 r_next=0.109 MAD_above=1.23 lag=-21(1.15/1.23); L255 16.33/1.19 r_next=0.155 MAD_above=1.27 lag=-21(1.17/1.27); L256 16.27/1.30 r_next=0.126 MAD_above=1.26 lag=-10(1.16/1.26); L257 16.37/1.19 r_next=0.073 MAD_above=1.28 lag=18(1.17/1.28); L258 16.15/1.21 r_next=0.063 MAD_above=1.29 lag=26(1.17/1.29); L259 16.12/1.14 r_next=0.165 MAD_above=1.20 lag=-12(1.14/1.20); L260 15.89/1.11 r_next=0.060 MAD_above=1.09 lag=-3(1.04/1.09); L261 16.24/1.23 r_next=0.068 MAD_above=1.27 lag=15(1.16/1.27); L262 15.88/1.28 r_next=0.036 MAD_above=1.38 lag=-6(1.20/1.38); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.285; no internal horizontal blanking run; gate=4.000) |
| 6313 | 6313/F1 | L109 | L261 | L108 18.69/2.00 r_next=0.053 MAD_above=2.27 lag=23(1.87/2.27); L109 18.49/1.93 r_next=0.125 MAD_above=2.11 lag=31(1.96/2.11); L110 18.93/1.92 r_next=0.318 MAD_above=2.06 lag=-25(1.85/2.06); L247 17.76/1.43 r_next=0.040 MAD_above=1.67 lag=-18(1.62/1.67); L248 17.84/1.41 r_next=0.163 MAD_above=1.56 lag=18(1.38/1.56); L249 17.54/1.64 r_next=0.079 MAD_above=1.56 lag=-15(1.47/1.56); L250 17.56/1.39 r_next=0.076 MAD_above=1.62 lag=-27(1.49/1.62); L251 17.63/1.39 r_next=0.079 MAD_above=1.49 lag=29(1.36/1.49); L252 17.92/1.39 r_next=0.103 MAD_above=1.49 lag=-26(1.33/1.49); L253 17.77/1.45 r_next=0.020 MAD_above=1.47 lag=16(1.42/1.47); L254 17.51/1.44 r_next=0.216 MAD_above=1.60 lag=-16(1.40/1.60); L255 17.53/1.48 r_next=0.021 MAD_above=1.41 lag=-2(1.40/1.41); L256 17.71/1.36 r_next=0.018 MAD_above=1.61 lag=-12(1.31/1.61); L257 17.31/1.45 r_next=0.037 MAD_above=1.55 lag=-11(1.37/1.55); L258 17.27/1.35 r_next=0.143 MAD_above=1.53 lag=-8(1.38/1.53); L259 17.51/1.44 r_next=0.011 MAD_above=1.47 lag=-1(1.45/1.47); L260 17.03/1.51 r_next=0.117 MAD_above=1.68 lag=-12(1.50/1.68); L261 18.09/1.57 r_next=0.306 MAD_above=1.85 lag=-24(1.78/1.85); L262 17.58/1.42 r_next=-0.028 MAD_above=1.40 lag=0(1.40/1.40); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.278; no internal horizontal blanking run; gate=4.000) |
| 6314 | 6314/F1 | L108 | L261 | L107 18.04/2.02 r_next=0.058 MAD_above=2.05 lag=30(1.93/2.05); L108 19.35/1.80 r_next=0.060 MAD_above=2.25 lag=16(2.12/2.25); L109 19.12/1.61 r_next=-0.055 MAD_above=1.85 lag=-29(1.65/1.85); L247 17.80/1.31 r_next=0.100 MAD_above=1.49 lag=-11(1.32/1.49); L248 17.92/1.35 r_next=0.137 MAD_above=1.44 lag=-20(1.27/1.44); L249 17.68/1.40 r_next=0.095 MAD_above=1.46 lag=-10(1.33/1.46); L250 17.11/1.37 r_next=0.154 MAD_above=1.53 lag=-22(1.35/1.53); L251 17.53/1.37 r_next=0.110 MAD_above=1.40 lag=13(1.37/1.40); L252 17.79/1.36 r_next=-0.010 MAD_above=1.44 lag=-9(1.33/1.44); L253 17.80/1.34 r_next=0.166 MAD_above=1.44 lag=23(1.33/1.44); L254 17.95/1.26 r_next=0.181 MAD_above=1.30 lag=-2(1.27/1.30); L255 17.65/1.50 r_next=0.056 MAD_above=1.36 lag=8(1.35/1.36); L256 17.48/1.46 r_next=0.020 MAD_above=1.58 lag=-27(1.37/1.58); L257 17.69/1.45 r_next=-0.020 MAD_above=1.60 lag=21(1.37/1.60); L258 17.58/1.48 r_next=0.144 MAD_above=1.63 lag=-3(1.51/1.63); L259 18.15/1.34 r_next=0.054 MAD_above=1.49 lag=3(1.47/1.49); L260 17.73/1.45 r_next=0.045 MAD_above=1.54 lag=-32(1.39/1.54); L261 18.45/1.42 r_next=0.143 MAD_above=1.65 lag=29(1.58/1.65); L262 18.07/1.40 r_next=-0.003 MAD_above=1.47 lag=-3(1.36/1.47); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.278; no internal horizontal blanking run; gate=4.000) |
| 6315 | 6315/F1 | L121 | L261 | L120 20.17/1.44 r_next=0.024 MAD_above=1.35 lag=-1(1.28/1.35); L121 20.02/1.19 r_next=0.153 MAD_above=1.46 lag=-32(1.28/1.46); L122 19.83/1.33 r_next=0.165 MAD_above=1.26 lag=14(1.13/1.26); L247 18.90/1.41 r_next=0.152 MAD_above=1.47 lag=-1(1.41/1.47); L248 18.88/1.39 r_next=0.134 MAD_above=1.47 lag=19(1.40/1.47); L249 18.63/1.60 r_next=0.191 MAD_above=1.55 lag=25(1.42/1.55); L250 18.28/1.31 r_next=0.113 MAD_above=1.45 lag=0(1.45/1.45); L251 18.70/1.42 r_next=0.155 MAD_above=1.49 lag=-17(1.41/1.49); L252 18.38/1.33 r_next=0.133 MAD_above=1.45 lag=12(1.34/1.45); L253 18.44/1.26 r_next=0.090 MAD_above=1.33 lag=5(1.26/1.33); L254 18.23/1.21 r_next=0.074 MAD_above=1.26 lag=5(1.21/1.26); L255 18.28/1.43 r_next=0.209 MAD_above=1.41 lag=32(1.26/1.41); L256 18.26/1.53 r_next=0.058 MAD_above=1.46 lag=6(1.43/1.46); L257 18.18/1.45 r_next=0.156 MAD_above=1.60 lag=-7(1.41/1.60); L258 18.12/1.39 r_next=0.056 MAD_above=1.49 lag=-3(1.40/1.49); L259 18.63/1.38 r_next=0.033 MAD_above=1.53 lag=-15(1.35/1.53); L260 18.18/1.52 r_next=-0.064 MAD_above=1.61 lag=25(1.48/1.61); L261 18.55/1.26 r_next=0.092 MAD_above=1.65 lag=14(1.41/1.65); L262 18.36/1.33 r_next=0.034 MAD_above=1.36 lag=-6(1.26/1.36); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.267; no internal horizontal blanking run; gate=4.000) |
| 6316 | 6316/F1 | L108 | L259 | L107 21.08/2.11 r_next=0.103 MAD_above=2.29 lag=24(2.14/2.29); L108 21.32/1.89 r_next=-0.010 MAD_above=2.10 lag=-26(1.71/2.10); L109 20.87/1.72 r_next=0.024 MAD_above=2.07 lag=-10(1.80/2.07); L247 19.32/1.42 r_next=-0.027 MAD_above=1.55 lag=-8(1.52/1.55); L248 18.57/1.42 r_next=-0.058 MAD_above=1.71 lag=-18(1.49/1.71); L249 20.75/1.82 r_next=0.114 MAD_above=2.61 lag=20(2.41/2.61); L250 21.14/1.67 r_next=0.186 MAD_above=1.81 lag=-1(1.79/1.81); L251 21.06/1.59 r_next=0.103 MAD_above=1.57 lag=-3(1.52/1.57); L252 20.81/1.50 r_next=0.029 MAD_above=1.66 lag=-19(1.54/1.66); L253 20.51/1.68 r_next=0.123 MAD_above=1.80 lag=-24(1.48/1.80); L254 20.45/1.61 r_next=0.065 MAD_above=1.71 lag=23(1.58/1.71); L255 20.16/1.56 r_next=0.060 MAD_above=1.70 lag=32(1.59/1.70); L256 20.16/1.53 r_next=0.044 MAD_above=1.64 lag=28(1.43/1.64); L257 20.15/1.51 r_next=0.032 MAD_above=1.65 lag=25(1.51/1.65); L258 19.88/1.57 r_next=0.045 MAD_above=1.66 lag=-28(1.46/1.66); L259 19.05/1.49 r_next=0.161 MAD_above=1.83 lag=-29(1.71/1.83); L260 19.33/1.47 r_next=0.019 MAD_above=1.53 lag=-9(1.36/1.53); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.218; no internal horizontal blanking run; gate=4.000) |
| 6317 | 6317/F1 | L244 | L259 | L243 19.65/2.01 r_next=0.129 MAD_above=1.84 lag=-3(1.71/1.84); L244 21.57/1.63 r_next=0.084 MAD_above=2.51 lag=29(2.33/2.51); L245 20.89/1.71 r_next=-0.025 MAD_above=1.82 lag=-24(1.64/1.82); L247 21.07/1.45 r_next=0.034 MAD_above=1.54 lag=-12(1.45/1.54); L248 20.43/1.64 r_next=0.031 MAD_above=1.76 lag=-18(1.62/1.76); L249 21.06/1.55 r_next=0.187 MAD_above=1.86 lag=18(1.53/1.86); L250 21.15/1.52 r_next=-0.053 MAD_above=1.52 lag=-21(1.48/1.52); L251 21.08/1.41 r_next=0.038 MAD_above=1.65 lag=28(1.37/1.65); L252 20.65/1.61 r_next=-0.063 MAD_above=1.69 lag=-19(1.54/1.69); L253 20.71/1.57 r_next=0.037 MAD_above=1.80 lag=-15(1.47/1.80); L254 20.24/1.31 r_next=0.065 MAD_above=1.61 lag=-22(1.50/1.61); L255 20.51/1.19 r_next=0.152 MAD_above=1.36 lag=31(1.30/1.36); L256 20.99/1.44 r_next=0.031 MAD_above=1.40 lag=28(1.31/1.40); L257 20.52/1.32 r_next=0.113 MAD_above=1.53 lag=-22(1.34/1.53); L258 20.35/1.50 r_next=0.073 MAD_above=1.44 lag=-8(1.33/1.44); L259 19.89/1.42 r_next=0.183 MAD_above=1.62 lag=27(1.41/1.62); L260 19.92/1.42 r_next=0.144 MAD_above=1.39 lag=-1(1.37/1.39); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.265; no internal horizontal blanking run; gate=4.000) |
| 6318 | 6318/F1 | L110 | L262 | L109 20.70/1.69 r_next=0.081 MAD_above=1.99 lag=-26(1.65/1.99); L110 20.48/1.48 r_next=0.121 MAD_above=1.67 lag=28(1.58/1.67); L111 20.43/1.52 r_next=0.087 MAD_above=1.60 lag=30(1.39/1.60); L247 19.07/1.52 r_next=0.148 MAD_above=1.47 lag=-12(1.38/1.47); L248 18.73/1.42 r_next=0.171 MAD_above=1.55 lag=20(1.40/1.55); L249 18.82/1.50 r_next=0.053 MAD_above=1.48 lag=6(1.40/1.48); L250 19.05/1.68 r_next=0.123 MAD_above=1.79 lag=-17(1.52/1.79); L251 19.27/1.47 r_next=0.096 MAD_above=1.66 lag=9(1.57/1.66); L252 19.20/1.50 r_next=0.012 MAD_above=1.57 lag=-23(1.44/1.57); L253 19.20/1.50 r_next=0.154 MAD_above=1.70 lag=30(1.42/1.70); L254 18.90/1.36 r_next=0.090 MAD_above=1.44 lag=-32(1.42/1.44); L255 19.03/1.46 r_next=0.209 MAD_above=1.49 lag=27(1.35/1.49); L256 19.34/1.48 r_next=0.092 MAD_above=1.40 lag=-2(1.39/1.40); L257 19.05/1.51 r_next=0.298 MAD_above=1.58 lag=5(1.48/1.58); L258 19.22/1.35 r_next=0.161 MAD_above=1.34 lag=-1(1.32/1.34); L259 18.99/1.39 r_next=0.144 MAD_above=1.38 lag=7(1.28/1.38); L260 19.02/1.31 r_next=0.122 MAD_above=1.39 lag=26(1.32/1.39); L261 19.41/1.42 r_next=0.132 MAD_above=1.43 lag=9(1.33/1.43); L262 18.81/1.49 r_next=-0.019 MAD_above=1.56 lag=6(1.47/1.56); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.262; no internal horizontal blanking run; gate=4.000) |
| 6319 | 6319/F1 | L111 | L259 | L110 20.19/1.36 r_next=0.159 MAD_above=1.62 lag=17(1.43/1.62); L111 19.72/1.48 r_next=0.211 MAD_above=1.47 lag=-6(1.41/1.47); L112 19.43/1.85 r_next=0.150 MAD_above=1.71 lag=-4(1.63/1.71); L247 17.10/1.54 r_next=0.150 MAD_above=1.86 lag=-21(1.78/1.86); L248 17.46/1.40 r_next=0.082 MAD_above=1.52 lag=20(1.39/1.52); L249 17.57/1.31 r_next=0.026 MAD_above=1.43 lag=12(1.30/1.43); L250 18.04/1.44 r_next=0.156 MAD_above=1.50 lag=5(1.37/1.50); L251 18.20/1.43 r_next=0.096 MAD_above=1.47 lag=-2(1.39/1.47); L252 18.44/1.47 r_next=0.177 MAD_above=1.55 lag=-12(1.33/1.55); L253 18.68/1.34 r_next=0.139 MAD_above=1.42 lag=-19(1.34/1.42); L254 18.69/1.42 r_next=0.067 MAD_above=1.38 lag=-28(1.26/1.38); L255 18.77/1.51 r_next=0.139 MAD_above=1.54 lag=-9(1.35/1.54); L256 17.20/1.38 r_next=-0.020 MAD_above=1.92 lag=-31(1.82/1.92); L257 16.98/1.59 r_next=0.025 MAD_above=1.64 lag=27(1.47/1.64); L258 17.30/1.51 r_next=0.168 MAD_above=1.69 lag=32(1.52/1.69); L259 17.89/1.24 r_next=0.025 MAD_above=1.47 lag=-4(1.40/1.47); L260 18.20/1.37 r_next=0.090 MAD_above=1.40 lag=-14(1.29/1.40); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.292; no internal horizontal blanking run; gate=4.000) |
| 6320 | 6320/F1 | L256 | L261 | L255 18.14/1.43 r_next=0.042 MAD_above=1.36 lag=21(1.25/1.36); L256 17.83/1.47 r_next=0.024 MAD_above=1.60 lag=-16(1.39/1.60); L257 17.64/1.56 r_next=-0.100 MAD_above=1.69 lag=27(1.51/1.69); L258 17.36/1.78 r_next=0.064 MAD_above=2.00 lag=-14(1.63/2.00); L259 15.99/1.46 r_next=0.137 MAD_above=2.06 lag=16(1.93/2.06); L260 16.64/1.73 r_next=-0.046 MAD_above=1.73 lag=9(1.67/1.73); L261 16.98/1.50 r_next=-0.009 MAD_above=1.87 lag=-9(1.62/1.87); L262 16.12/1.51 r_next=-0.002 MAD_above=1.83 lag=-9(1.60/1.83); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.249; no internal horizontal blanking run; gate=4.000) |

First-full-other-head histogram (engine S minus reference): -1: 47, +0: 482, +1: 2, both-unmeasurable: 15, reference-unmeasurable: 373

- +1: counters 6687, 6737.  Witnesses: counter 6687: engine L261, direct L260; L260 internal blank x=111-174 Y=2.375; above=25.266 following=21.000; gate=4.000 / counter 6737: engine L261, direct L260; L260 internal blank x=94-157 Y=1.672; above=27.016 following=22.000; gate=4.000

- -1: counters 6886, 6888-6889, 6891, 6899-6905, 6907-6909, 6912-6917, 6919, 6929-6931, 6933-6938, 6940-6941, 6943-6945, 6948-6957, 6959, 6963.  Witnesses: counter 6886: engine L260, direct L261; L261 persistent three-third step; thirds=23.463,2.537,3.125; correlation above/next=-0.213/0.982; middle coherence=0.964 / counter 6888: engine L260, direct L261; L261 internal blank x=34-97 Y=1.328; above=43.156 following=38.000; gate=4.000 / counter 6889: engine L260, direct L261; L261 internal blank x=44-107 Y=1.328; above=44.250 following=39.000; gate=4.000

- reference-unmeasurable: counters 6260-6267, 6269-6274, 6278-6285, 6287-6292, 6294, 6296-6322, 6325-6368, 6371-6643.  Witnesses: counter 6260: engine L262, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.945; no internal horizontal blanking run; gate=4.000 / counter 6261: engine L262, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.949; no internal horizontal blanking run; gate=4.000 / counter 6262: engine L262, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.949; no internal horizontal blanking run; gate=4.000

Every numeric first-full disagreement:

| engine counter | raw counter/field | engine S | reference first-full | raw tail rows |
|---:|:---:|:---|:---|:---|
| 6687 | 6687/F1 | L261 | L260 | L259 22.49/3.16 r_next=-0.329 MAD_above=1.83 lag=-7(1.75/1.83); L260 19.72/8.02 r_next=0.567 MAD_above=6.67 lag=-6(6.49/6.67); L261 17.32/9.56 r_next=0.963 MAD_above=4.15 lag=-7(4.10/4.15); L262 17.38/9.80 r_next=-0.007 MAD_above=1.87 lag=1(1.82/1.87); direct-full=L260 (L260 internal blank x=111-174 Y=2.375; above=25.266 following=21.000; gate=4.000) |
| 6737 | 6737/F1 | L261 | L260 | L259 22.14/3.25 r_next=-0.469 MAD_above=1.93 lag=-8(1.81/1.93); L260 19.74/8.81 r_next=0.643 MAD_above=7.35 lag=32(7.16/7.35); L261 18.32/9.65 r_next=0.965 MAD_above=3.42 lag=-16(3.29/3.42); L262 16.49/8.45 r_next=0.034 MAD_above=2.53 lag=1(2.52/2.53); direct-full=L260 (L260 internal blank x=94-157 Y=1.672; above=27.016 following=22.000; gate=4.000) |
| 6886 | 6886/F1 | L260 | L261 | L259 38.58/2.65 r_next=-0.103 MAD_above=1.83 lag=2(1.81/1.83); L260 36.32/7.27 r_next=-0.201 MAD_above=4.42 lag=-12(4.27/4.42); L261 23.83/14.10 r_next=0.976 MAD_above=14.60 lag=-32(13.46/14.60); L262 22.11/13.64 r_next=0.041 MAD_above=2.54 lag=0(2.54/2.54); direct-full=L261 (L261 persistent three-third step; thirds=23.463,2.537,3.125; correlation above/next=-0.213/0.982; middle coherence=0.964) |
| 6888 | 6888/F1 | L260 | L261 | L259 43.80/3.65 r_next=-0.160 MAD_above=2.38 lag=-1(2.35/2.38); L260 41.43/6.68 r_next=-0.291 MAD_above=5.36 lag=-6(5.21/5.36); L261 27.45/16.44 r_next=0.977 MAD_above=15.81 lag=-31(14.93/15.81); L262 26.02/16.10 r_next=0.020 MAD_above=2.89 lag=0(2.89/2.89); direct-full=L261 (L261 internal blank x=34-97 Y=1.328; above=43.156 following=38.000; gate=4.000) |
| 6889 | 6889/F1 | L260 | L261 | L259 45.77/3.96 r_next=-0.039 MAD_above=2.20 lag=0(2.20/2.20); L260 43.48/4.91 r_next=-0.276 MAD_above=5.06 lag=19(4.79/5.06); L261 28.71/17.08 r_next=0.981 MAD_above=15.26 lag=32(14.00/15.26); L262 28.02/17.19 r_next=-0.008 MAD_above=2.60 lag=2(2.60/2.60); direct-full=L261 (L261 internal blank x=44-107 Y=1.328; above=44.250 following=39.000; gate=4.000) |
| 6891 | 6891/F1 | L260 | L261 | L259 52.17/3.88 r_next=-0.045 MAD_above=2.29 lag=0(2.29/2.29); L260 48.67/6.68 r_next=-0.307 MAD_above=5.79 lag=1(5.76/5.79); L261 33.93/20.07 r_next=0.986 MAD_above=17.40 lag=32(15.90/17.40); L262 32.35/19.69 r_next=0.020 MAD_above=2.60 lag=0(2.60/2.60); direct-full=L261 (L261 internal blank x=38-101 Y=1.312; above=49.938 following=46.000; gate=4.000) |
| 6899 | 6899/F1 | L260 | L261 | L259 67.13/8.30 r_next=0.202 MAD_above=3.08 lag=1(2.94/3.08); L260 68.66/21.31 r_next=-0.069 MAD_above=11.96 lag=-11(11.83/11.96); L261 43.86/27.30 r_next=0.982 MAD_above=29.02 lag=29(26.85/29.02); L262 43.07/27.11 r_next=0.003 MAD_above=3.78 lag=1(3.67/3.78); direct-full=L261 (L261 persistent three-third step; thirds=39.810,10.012,6.012; correlation above/next=-0.052/0.987; middle coherence=0.993) |
| 6900 | 6900/F1 | L260 | L261 | L259 70.33/10.25 r_next=0.330 MAD_above=3.52 lag=1(3.49/3.52); L260 67.76/11.90 r_next=-0.510 MAD_above=9.92 lag=1(9.87/9.92); L261 42.17/26.35 r_next=0.981 MAD_above=28.46 lag=31(26.90/28.46); L262 38.45/24.65 r_next=0.019 MAD_above=4.82 lag=0(4.82/4.82); direct-full=L261 (L261 persistent three-third step; thirds=42.304,5.003,7.267; correlation above/next=-0.519/0.985; middle coherence=0.994) |
| 6901 | 6901/F1 | L260 | L261 | L259 69.81/10.04 r_next=0.104 MAD_above=3.49 lag=0(3.49/3.49); L260 73.05/22.45 r_next=-0.048 MAD_above=14.53 lag=1(14.52/14.53); L261 35.36/22.78 r_next=0.977 MAD_above=38.48 lag=31(37.27/38.48); L262 33.10/21.66 r_next=-0.006 MAD_above=3.90 lag=1(3.73/3.90); direct-full=L261 (L261 persistent three-third step; thirds=41.582,18.379,12.072; correlation above/next=-0.021/0.982; middle coherence=0.994) |
| 6902 | 6902/F1 | L260 | L261 | L259 74.10/9.54 r_next=0.359 MAD_above=3.36 lag=0(3.36/3.36); L260 72.53/11.70 r_next=-0.453 MAD_above=9.63 lag=1(9.59/9.63); L261 50.67/31.63 r_next=0.985 MAD_above=28.53 lag=32(26.08/28.53); L262 46.76/29.81 r_next=0.016 MAD_above=5.00 lag=1(4.91/5.00); direct-full=L261 (L261 persistent three-third step; thirds=43.209,4.643,5.164; correlation above/next=-0.455/0.989; middle coherence=0.994) |
| 6903 | 6903/F1 | L260 | L261 | L259 76.32/10.03 r_next=0.272 MAD_above=4.69 lag=1(4.69/4.69); L260 74.35/12.89 r_next=-0.416 MAD_above=10.39 lag=28(10.10/10.39); L261 50.08/30.97 r_next=0.990 MAD_above=29.05 lag=32(26.99/29.05); L262 47.99/30.21 r_next=0.044 MAD_above=3.53 lag=1(3.44/3.53); direct-full=L261 (L261 persistent three-third step; thirds=45.904,4.364,5.027; correlation above/next=-0.430/0.993; middle coherence=0.995) |
| 6904 | 6904/F1 | L260 | L261 | L259 80.63/10.29 r_next=0.098 MAD_above=5.15 lag=0(5.15/5.15); L260 85.80/21.82 r_next=-0.033 MAD_above=14.96 lag=-1(14.91/14.96); L261 38.03/24.89 r_next=0.981 MAD_above=47.82 lag=32(46.49/47.82); L262 36.81/24.68 r_next=0.034 MAD_above=3.44 lag=1(3.27/3.44); direct-full=L261 (L261 persistent three-third step; thirds=52.762,19.523,17.470; correlation above/next=-0.021/0.987; middle coherence=0.995) |
| 6905 | 6905/F1 | L260 | L261 | L259 80.47/11.21 r_next=0.275 MAD_above=5.98 lag=0(5.98/5.98); L260 77.44/12.65 r_next=-0.424 MAD_above=11.45 lag=-2(11.09/11.45); L261 50.75/32.04 r_next=0.983 MAD_above=31.48 lag=32(28.28/31.48); L262 47.28/30.72 r_next=-0.022 MAD_above=5.09 lag=-1(5.08/5.09); direct-full=L261 (L261 persistent three-third step; thirds=45.833,6.341,5.475; correlation above/next=-0.420/0.987; middle coherence=0.995) |
| 6907 | 6907/F1 | L260 | L261 | L259 83.43/12.21 r_next=0.376 MAD_above=5.01 lag=0(5.01/5.01); L260 84.86/13.96 r_next=-0.459 MAD_above=11.68 lag=-2(11.44/11.68); L261 60.95/39.61 r_next=0.984 MAD_above=35.62 lag=32(32.56/35.62); L262 59.69/38.56 r_next=0.022 MAD_above=4.93 lag=1(4.84/4.93); direct-full=L261 (L261 persistent three-third step; thirds=52.707,6.478,6.633; correlation above/next=-0.458/0.988; middle coherence=0.995) |
| 6908 | 6908/F1 | L260 | L261 | L259 86.22/12.96 r_next=0.367 MAD_above=4.96 lag=0(4.96/4.96); L260 85.77/15.88 r_next=-0.457 MAD_above=12.75 lag=32(12.56/12.75); L261 62.77/40.29 r_next=0.983 MAD_above=36.51 lag=32(32.99/36.51); L262 59.10/37.72 r_next=0.028 MAD_above=6.28 lag=0(6.28/6.28); direct-full=L261 (L261 persistent three-third step; thirds=55.275,7.066,7.080; correlation above/next=-0.464/0.988; middle coherence=0.996) |
| 6909 | 6909/F1 | L260 | L261 | L259 85.47/14.26 r_next=0.399 MAD_above=6.25 lag=1(6.19/6.25); L260 87.51/16.12 r_next=-0.475 MAD_above=13.65 lag=1(13.65/13.65); L261 62.32/38.15 r_next=0.977 MAD_above=36.45 lag=32(31.80/36.45); L262 54.04/34.68 r_next=0.060 MAD_above=8.95 lag=1(8.87/8.95); direct-full=L261 (L261 persistent three-third step; thirds=54.633,6.992,8.101; correlation above/next=-0.473/0.983; middle coherence=0.996) |
| 6912 | 6912/F1 | L260 | L261 | L259 90.48/15.59 r_next=0.253 MAD_above=6.88 lag=0(6.88/6.88); L260 83.26/22.83 r_next=-0.317 MAD_above=17.27 lag=-32(15.94/17.27); L261 50.27/32.01 r_next=0.981 MAD_above=40.91 lag=32(37.63/40.91); L262 48.00/30.45 r_next=0.009 MAD_above=4.74 lag=0(4.74/4.74); direct-full=L261 (L261 persistent three-third step; thirds=52.910,8.553,16.670; correlation above/next=-0.340/0.987; middle coherence=0.996) |
| 6913 | 6913/F1 | L260 | L261 | L259 85.20/14.33 r_next=0.169 MAD_above=7.10 lag=1(6.89/7.10); L260 86.23/25.61 r_next=-0.133 MAD_above=18.21 lag=29(17.11/18.21); L261 56.66/34.47 r_next=0.970 MAD_above=38.14 lag=30(34.99/38.14); L262 52.86/33.06 r_next=-0.004 MAD_above=6.53 lag=1(6.34/6.53); direct-full=L261 (L261 persistent three-third step; thirds=52.094,12.401,11.003; correlation above/next=-0.126/0.977; middle coherence=0.996) |
| 6914 | 6914/F1 | L260 | L261 | L259 87.12/14.33 r_next=0.017 MAD_above=6.91 lag=1(6.82/6.91); L260 88.80/22.28 r_next=-0.059 MAD_above=17.06 lag=29(16.97/17.06); L261 60.33/36.72 r_next=0.962 MAD_above=37.18 lag=32(34.69/37.18); L262 53.87/33.72 r_next=0.031 MAD_above=8.84 lag=1(8.56/8.84); direct-full=L261 (L261 persistent three-third step; thirds=49.325,13.047,9.435; correlation above/next=-0.054/0.969; middle coherence=0.997) |
| 6915 | 6915/F1 | L260 | L261 | L259 89.04/16.10 r_next=0.353 MAD_above=8.12 lag=0(8.12/8.12); L260 80.93/16.60 r_next=-0.379 MAD_above=15.72 lag=-1(15.60/15.72); L261 59.02/35.79 r_next=0.967 MAD_above=34.07 lag=32(32.43/34.07); L262 53.95/32.52 r_next=0.010 MAD_above=7.73 lag=2(7.51/7.73); direct-full=L261 (L261 persistent three-third step; thirds=47.776,8.217,8.772; correlation above/next=-0.410/0.974; middle coherence=0.996) |
| 6916 | 6916/F1 | L260 | L261 | L259 88.27/16.52 r_next=0.181 MAD_above=8.77 lag=2(7.98/8.77); L260 87.83/22.99 r_next=-0.146 MAD_above=18.90 lag=15(17.35/18.90); L261 59.05/34.90 r_next=0.968 MAD_above=37.82 lag=32(35.70/37.82); L262 51.89/30.93 r_next=0.023 MAD_above=8.53 lag=1(8.46/8.53); direct-full=L261 (L261 persistent three-third step; thirds=48.810,9.523,15.311; correlation above/next=-0.166/0.976; middle coherence=0.997) |
| 6917 | 6917/F1 | L260 | L261 | L259 88.23/14.71 r_next=0.011 MAD_above=9.14 lag=2(8.93/9.14); L260 80.01/22.14 r_next=-0.264 MAD_above=19.66 lag=11(17.63/19.66); L261 48.79/29.60 r_next=0.970 MAD_above=39.54 lag=32(36.17/39.54); L262 47.74/28.94 r_next=0.041 MAD_above=4.65 lag=1(4.54/4.65); direct-full=L261 (L261 persistent three-third step; thirds=49.890,11.840,16.340; correlation above/next=-0.317/0.978; middle coherence=0.997) |
| 6919 | 6919/F1 | L260 | L261 | L259 88.43/14.89 r_next=0.172 MAD_above=9.75 lag=2(9.45/9.75); L260 79.76/19.12 r_next=-0.260 MAD_above=16.91 lag=-2(16.83/16.91); L261 53.93/32.31 r_next=0.974 MAD_above=34.36 lag=32(33.09/34.36); L262 51.25/31.46 r_next=0.038 MAD_above=5.58 lag=1(5.55/5.58); direct-full=L261 (L261 persistent three-third step; thirds=49.854,8.970,9.584; correlation above/next=-0.326/0.980; middle coherence=0.996) |
| 6929 | 6929/F1 | L260 | L261 | L259 90.04/15.20 r_next=0.083 MAD_above=8.03 lag=1(7.87/8.03); L260 83.35/17.08 r_next=-0.214 MAD_above=17.12 lag=-2(16.70/17.12); L261 52.88/32.21 r_next=0.971 MAD_above=36.10 lag=32(34.64/36.10); L262 47.28/29.33 r_next=0.042 MAD_above=7.22 lag=1(7.13/7.22); direct-full=L261 (L261 persistent three-third step; thirds=50.610,9.854,11.748; correlation above/next=-0.300/0.979; middle coherence=0.997) |
| 6930 | 6930/F1 | L260 | L261 | L259 89.53/12.70 r_next=0.255 MAD_above=4.94 lag=0(4.94/4.94); L260 81.67/19.51 r_next=-0.468 MAD_above=15.71 lag=12(15.63/15.71); L261 54.95/33.84 r_next=0.985 MAD_above=38.64 lag=32(35.53/38.64); L262 46.66/29.29 r_next=0.004 MAD_above=8.68 lag=1(8.53/8.68); direct-full=L261 (L261 persistent three-third step; thirds=53.547,12.573,10.322; correlation above/next=-0.530/0.990; middle coherence=0.997) |
| 6931 | 6931/F1 | L260 | L261 | L259 93.47/14.52 r_next=-0.193 MAD_above=5.28 lag=0(5.28/5.28); L260 85.53/22.09 r_next=-0.168 MAD_above=19.57 lag=-28(17.33/19.57); L261 52.51/32.48 r_next=0.972 MAD_above=38.94 lag=22(36.71/38.94); L262 48.26/30.48 r_next=0.000 MAD_above=6.11 lag=1(6.02/6.11); direct-full=L261 (L261 persistent three-third step; thirds=52.257,11.752,11.975; correlation above/next=-0.192/0.977; middle coherence=0.997) |
| 6933 | 6933/F1 | L260 | L261 | L259 91.19/15.46 r_next=0.278 MAD_above=6.75 lag=0(6.75/6.75); L260 86.91/14.93 r_next=-0.342 MAD_above=14.29 lag=-31(12.65/14.29); L261 54.20/32.83 r_next=0.965 MAD_above=36.23 lag=32(34.66/36.23); L262 48.70/30.19 r_next=0.039 MAD_above=7.39 lag=1(7.29/7.39); direct-full=L261 (L261 persistent three-third step; thirds=52.981,8.106,12.239; correlation above/next=-0.374/0.973; middle coherence=0.997) |
| 6934 | 6934/F1 | L260 | L261 | L259 92.35/14.81 r_next=0.080 MAD_above=7.31 lag=1(7.14/7.31); L260 77.65/24.16 r_next=-0.456 MAD_above=22.64 lag=-29(21.48/22.64); L261 52.00/31.70 r_next=0.973 MAD_above=38.21 lag=32(36.44/38.21); L262 46.11/29.03 r_next=0.026 MAD_above=7.04 lag=1(6.83/7.04); direct-full=L261 (L261 persistent three-third step; thirds=55.240,9.621,12.409; correlation above/next=-0.466/0.981; middle coherence=0.997) |
| 6935 | 6935/F1 | L260 | L261 | L259 94.74/15.79 r_next=0.021 MAD_above=8.58 lag=2(8.21/8.58); L260 81.22/30.28 r_next=-0.120 MAD_above=26.71 lag=-32(25.67/26.71); L261 48.65/29.96 r_next=0.952 MAD_above=39.78 lag=-22(38.52/39.78); L262 44.89/28.43 r_next=0.003 MAD_above=6.70 lag=1(6.54/6.70); direct-full=L261 (L261 persistent three-third step; thirds=55.445,14.506,7.577; correlation above/next=-0.114/0.961; middle coherence=0.997) |
| 6936 | 6936/F1 | L260 | L261 | L259 92.34/15.40 r_next=0.051 MAD_above=7.92 lag=2(7.24/7.92); L260 94.40/28.56 r_next=-0.008 MAD_above=21.46 lag=-32(19.05/21.46); L261 57.33/34.85 r_next=0.973 MAD_above=43.31 lag=32(41.37/43.31); L262 49.22/30.95 r_next=0.016 MAD_above=9.23 lag=0(9.23/9.23); direct-full=L261 (L261 persistent three-third step; thirds=53.756,11.530,18.254; correlation above/next=0.014/0.980; middle coherence=0.997) |
| 6937 | 6937/F1 | L260 | L261 | L259 90.64/15.27 r_next=0.101 MAD_above=8.66 lag=2(7.81/8.66); L260 86.92/21.51 r_next=-0.131 MAD_above=19.25 lag=10(17.83/19.25); L261 54.28/33.11 r_next=0.973 MAD_above=39.08 lag=32(35.78/39.08); L262 47.39/29.17 r_next=-0.009 MAD_above=7.97 lag=1(7.80/7.97); direct-full=L261 (L261 persistent three-third step; thirds=50.272,10.721,14.034; correlation above/next=-0.102/0.981; middle coherence=0.997) |
| 6938 | 6938/F1 | L260 | L261 | L259 91.18/16.10 r_next=-0.123 MAD_above=9.10 lag=1(8.69/9.10); L260 86.26/20.43 r_next=-0.161 MAD_above=20.03 lag=12(18.72/20.03); L261 50.51/31.57 r_next=0.956 MAD_above=40.03 lag=32(37.85/40.03); L262 43.84/27.99 r_next=0.008 MAD_above=8.41 lag=2(7.86/8.41); direct-full=L261 (L261 persistent three-third step; thirds=52.844,12.314,12.452; correlation above/next=-0.182/0.968; middle coherence=0.997) |
| 6940 | 6940/F1 | L260 | L261 | L259 90.92/15.68 r_next=-0.076 MAD_above=7.16 lag=0(7.16/7.16); L260 88.19/24.91 r_next=-0.098 MAD_above=20.54 lag=-31(19.99/20.54); L261 48.41/29.41 r_next=0.965 MAD_above=43.29 lag=32(40.43/43.29); L262 42.13/26.86 r_next=0.020 MAD_above=7.70 lag=0(7.70/7.70); direct-full=L261 (L261 persistent three-third step; thirds=50.331,19.141,14.732; correlation above/next=-0.082/0.974; middle coherence=0.997) |
| 6941 | 6941/F1 | L260 | L261 | L259 91.98/14.36 r_next=0.218 MAD_above=6.72 lag=0(6.72/6.72); L260 81.42/18.19 r_next=-0.431 MAD_above=17.48 lag=-1(17.47/17.48); L261 55.95/33.69 r_next=0.962 MAD_above=37.97 lag=32(33.19/37.97); L262 49.41/31.10 r_next=0.057 MAD_above=8.17 lag=2(7.97/8.17); direct-full=L261 (L261 persistent three-third step; thirds=50.934,12.497,11.344; correlation above/next=-0.455/0.970; middle coherence=0.997) |
| 6943 | 6943/F1 | L260 | L261 | L259 90.22/14.52 r_next=0.259 MAD_above=6.15 lag=1(5.85/6.15); L260 89.22/18.43 r_next=-0.511 MAD_above=15.05 lag=21(14.77/15.05); L261 48.58/28.86 r_next=0.963 MAD_above=44.81 lag=32(41.75/44.81); L262 42.37/26.49 r_next=0.039 MAD_above=7.44 lag=2(7.10/7.44); direct-full=L261 (L261 persistent three-third step; thirds=55.741,15.601,17.244; correlation above/next=-0.557/0.976; middle coherence=0.997) |
| 6944 | 6944/F1 | L260 | L261 | L259 91.80/15.32 r_next=0.013 MAD_above=6.75 lag=1(6.68/6.75); L260 85.70/20.56 r_next=-0.161 MAD_above=17.92 lag=-23(17.25/17.92); L261 43.48/26.73 r_next=0.955 MAD_above=44.22 lag=32(41.63/44.22); L262 36.65/23.73 r_next=0.045 MAD_above=8.05 lag=2(7.80/8.05); direct-full=L261 (L261 persistent three-third step; thirds=47.345,19.608,17.567; correlation above/next=-0.155/0.966; middle coherence=0.997) |
| 6945 | 6945/F1 | L260 | L261 | L259 91.42/16.25 r_next=0.055 MAD_above=7.58 lag=1(7.56/7.58); L260 81.09/20.96 r_next=-0.211 MAD_above=20.12 lag=-27(18.50/20.12); L261 49.70/29.73 r_next=0.960 MAD_above=36.92 lag=32(33.90/36.92); L262 44.81/27.96 r_next=-0.035 MAD_above=7.03 lag=2(6.63/7.03); direct-full=L261 (L261 persistent three-third step; thirds=47.497,14.025,11.256; correlation above/next=-0.200/0.971; middle coherence=0.997) |
| 6948 | 6948/F1 | L260 | L261 | L259 90.39/14.22 r_next=0.081 MAD_above=6.86 lag=1(6.84/6.86); L260 77.20/18.38 r_next=-0.419 MAD_above=19.67 lag=-2(19.60/19.67); L261 52.79/30.99 r_next=0.959 MAD_above=35.42 lag=32(30.98/35.42); L262 45.29/27.78 r_next=0.035 MAD_above=8.81 lag=1(8.78/8.81); direct-full=L261 (L261 persistent three-third step; thirds=45.603,13.423,9.991; correlation above/next=-0.404/0.965; middle coherence=0.997) |
| 6949 | 6949/F1 | L260 | L261 | L259 90.19/15.75 r_next=0.102 MAD_above=8.51 lag=1(8.44/8.51); L260 78.71/16.77 r_next=-0.457 MAD_above=18.98 lag=5(18.26/18.98); L261 43.81/27.09 r_next=0.964 MAD_above=39.53 lag=32(36.07/39.53); L262 39.92/25.20 r_next=-0.023 MAD_above=5.99 lag=0(5.99/5.99); direct-full=L261 (L261 persistent three-third step; thirds=47.609,12.753,16.103; correlation above/next=-0.482/0.973; middle coherence=0.997) |
| 6950 | 6950/F1 | L260 | L261 | L259 91.56/15.78 r_next=0.212 MAD_above=9.51 lag=1(9.23/9.51); L260 82.27/18.64 r_next=-0.467 MAD_above=17.27 lag=1(17.25/17.27); L261 50.71/30.51 r_next=0.942 MAD_above=38.32 lag=29(35.65/38.32); L262 42.58/26.16 r_next=-0.004 MAD_above=10.20 lag=3(9.94/10.20); direct-full=L261 (L261 persistent three-third step; thirds=50.745,11.470,12.122; correlation above/next=-0.492/0.958; middle coherence=0.997) |
| 6951 | 6951/F1 | L260 | L261 | L259 88.67/16.09 r_next=0.193 MAD_above=9.73 lag=1(9.30/9.73); L260 81.39/19.84 r_next=-0.347 MAD_above=17.65 lag=1(17.60/17.65); L261 51.36/30.47 r_next=0.948 MAD_above=37.71 lag=32(35.01/37.71); L262 45.15/27.80 r_next=0.002 MAD_above=8.77 lag=2(8.35/8.77); direct-full=L261 (L261 persistent three-third step; thirds=50.035,12.311,11.623; correlation above/next=-0.373/0.963; middle coherence=0.996) |
| 6952 | 6952/F1 | L260 | L261 | L259 88.52/15.37 r_next=0.023 MAD_above=9.91 lag=1(9.50/9.91); L260 87.90/26.08 r_next=-0.133 MAD_above=20.19 lag=2(20.03/20.19); L261 53.37/32.04 r_next=0.952 MAD_above=41.70 lag=32(38.55/41.70); L262 45.65/28.10 r_next=0.010 MAD_above=9.36 lag=1(9.10/9.36); direct-full=L261 (L261 persistent three-third step; thirds=51.978,16.540,11.624; correlation above/next=-0.135/0.963; middle coherence=0.997) |
| 6953 | 6953/F1 | L260 | L261 | L259 88.63/14.20 r_next=0.211 MAD_above=7.16 lag=1(7.10/7.16); L260 82.72/16.02 r_next=-0.450 MAD_above=15.27 lag=4(15.05/15.27); L261 54.53/32.55 r_next=0.964 MAD_above=35.98 lag=32(32.45/35.98); L262 48.25/29.32 r_next=0.020 MAD_above=8.43 lag=2(7.95/8.43); direct-full=L261 (L261 persistent three-third step; thirds=50.800,10.118,10.640; correlation above/next=-0.468/0.972; middle coherence=0.997) |
| 6954 | 6954/F1 | L260 | L261 | L259 89.70/14.47 r_next=0.188 MAD_above=5.90 lag=0(5.90/5.90); L260 81.10/19.08 r_next=-0.438 MAD_above=17.63 lag=8(17.39/17.63); L261 53.50/32.11 r_next=0.969 MAD_above=37.48 lag=32(34.40/37.48); L262 46.35/28.79 r_next=0.041 MAD_above=8.71 lag=1(8.53/8.71); direct-full=L261 (L261 persistent three-third step; thirds=52.426,11.249,9.783; correlation above/next=-0.453/0.977; middle coherence=0.997) |
| 6955 | 6955/F1 | L260 | L261 | L259 91.71/15.70 r_next=0.004 MAD_above=7.01 lag=0(7.01/7.01); L260 84.95/15.52 r_next=-0.423 MAD_above=17.06 lag=-32(16.33/17.06); L261 54.45/32.60 r_next=0.975 MAD_above=36.71 lag=32(33.12/36.71); L262 50.25/30.82 r_next=0.017 MAD_above=6.23 lag=0(6.23/6.23); direct-full=L261 (L261 persistent three-third step; thirds=51.500,10.218,11.403; correlation above/next=-0.451/0.981; middle coherence=0.997) |
| 6956 | 6956/F1 | L260 | L261 | L259 91.95/15.67 r_next=0.004 MAD_above=7.71 lag=1(7.46/7.71); L260 85.09/14.97 r_next=-0.387 MAD_above=17.61 lag=-32(15.79/17.61); L261 53.02/31.97 r_next=0.963 MAD_above=37.40 lag=32(34.11/37.40); L262 47.54/29.88 r_next=-0.005 MAD_above=7.77 lag=2(7.29/7.77); direct-full=L261 (L261 persistent three-third step; thirds=50.614,11.399,11.166; correlation above/next=-0.397/0.973; middle coherence=0.997) |
| 6957 | 6957/F1 | L260 | L261 | L259 88.93/15.07 r_next=0.139 MAD_above=9.04 lag=2(8.53/9.04); L260 83.53/21.20 r_next=-0.431 MAD_above=18.92 lag=6(18.76/18.92); L261 83.58/49.12 r_next=0.976 MAD_above=50.31 lag=32(48.61/50.31); L262 78.66/46.60 r_next=-0.057 MAD_above=8.97 lag=2(8.12/8.97); direct-full=L261 (L261 persistent three-third step; thirds=59.420,19.423,22.952; correlation above/next=-0.453/0.982; middle coherence=0.997) |
| 6959 | 6959/F1 | L260 | L261 | L259 86.92/14.50 r_next=0.251 MAD_above=7.83 lag=1(7.68/7.83); L260 85.98/21.96 r_next=-0.391 MAD_above=16.94 lag=1(16.80/16.94); L261 62.36/38.14 r_next=0.962 MAD_above=40.34 lag=31(37.74/40.34); L262 54.61/33.03 r_next=-0.007 MAD_above=10.38 lag=2(10.20/10.38); direct-full=L261 (L261 persistent three-third step; thirds=55.621,10.817,11.439; correlation above/next=-0.411/0.971; middle coherence=0.997) |
| 6963 | 6963/F1 | L260 | L261 | L259 87.88/13.83 r_next=0.245 MAD_above=7.83 lag=1(7.54/7.83); L260 80.71/21.32 r_next=-0.414 MAD_above=17.69 lag=1(17.56/17.69); L261 78.64/47.89 r_next=0.983 MAD_above=49.77 lag=32(46.35/49.77); L262 79.03/46.17 r_next=0.023 MAD_above=6.48 lag=0(6.48/6.48); direct-full=L261 (L261 persistent three-third step; thirds=54.776,23.782,21.456; correlation above/next=-0.414/0.987; middle coherence=0.997) |

### Engine field 2

S minus reference switch histogram: -183: 1, -177: 1, -175: 1, -160: 1, -155: 1, -153: 1, -152: 2, -150: 1, -144: 1, -143: 1, -134: 1, -127: 2, -108: 1, -96: 1, -94: 1, -68: 1, -30: 1, -28: 1, -27: 1, -24: 2, -23: 1, -20: 1, -14: 1, -10: 1, -6: 2, -5: 1, -4: 3, -3: 2, -1: 6, +0: 438, +1: 413, +2: 1, +3: 1, engine-unmeasurable: 25

Differences beyond the one-row semantic gap:

| engine counter | raw counter/field | S | reference switch | raw tail rows |
|---:|:---:|:---|:---|:---|
| 6269 | 6269/F2 | L502 | L525 | L501 29.40/5.03 r_next=0.482 MAD_above=1.60 lag=0(1.60/1.60); L502 25.90/1.86 r_next=0.274 MAD_above=3.94 lag=0(3.94/3.94); L503 24.64/1.12 r_next=0.428 MAD_above=1.78 lag=-6(1.74/1.78); L510 24.07/1.10 r_next=0.477 MAD_above=1.04 lag=-30(0.98/1.04); L511 23.91/1.13 r_next=0.441 MAD_above=0.96 lag=-2(0.94/0.96); L512 23.40/1.09 r_next=0.409 MAD_above=1.10 lag=-6(1.04/1.10); L513 23.39/1.11 r_next=0.461 MAD_above=1.04 lag=-9(0.99/1.04); L514 23.31/1.17 r_next=0.476 MAD_above=1.02 lag=29(0.92/1.02); L515 22.93/1.30 r_next=0.497 MAD_above=1.09 lag=24(1.03/1.09); L516 23.02/1.22 r_next=0.425 MAD_above=1.06 lag=-2(1.05/1.06); L517 23.23/1.08 r_next=0.343 MAD_above=1.05 lag=2(1.01/1.05); L518 23.18/1.02 r_next=0.435 MAD_above=1.05 lag=-16(0.93/1.05); L519 23.15/1.07 r_next=0.601 MAD_above=0.97 lag=1(0.94/0.97); L520 23.70/1.21 r_next=0.543 MAD_above=0.97 lag=0(0.97/0.97); L521 23.82/1.10 r_next=0.531 MAD_above=0.97 lag=-6(0.94/0.97); L522 23.70/0.97 r_next=0.508 MAD_above=0.93 lag=4(0.86/0.93); L523 23.88/1.12 r_next=0.571 MAD_above=0.93 lag=-25(0.92/0.93); L524 23.53/1.51 r_next=0.407 MAD_above=1.14 lag=-15(1.04/1.14); L525 23.82/1.23 r_next=0.016 MAD_above=1.38 lag=14(1.31/1.38); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.910; no internal horizontal blanking run; gate=4.000) |
| 6270 | 6270/F2 | L512 | L522 | L511 22.21/1.40 r_next=0.154 MAD_above=1.31 lag=-1(1.27/1.31); L512 21.87/1.30 r_next=0.161 MAD_above=1.47 lag=10(1.25/1.47); L513 21.54/1.37 r_next=0.005 MAD_above=1.39 lag=-28(1.33/1.39); L514 21.11/1.34 r_next=-0.041 MAD_above=1.58 lag=-12(1.39/1.58); L515 20.71/1.25 r_next=0.106 MAD_above=1.60 lag=24(1.33/1.60); L516 20.17/1.38 r_next=0.262 MAD_above=1.50 lag=-11(1.42/1.50); L517 19.98/1.46 r_next=0.021 MAD_above=1.43 lag=1(1.38/1.43); L518 19.84/1.47 r_next=0.177 MAD_above=1.64 lag=32(1.42/1.64); L519 20.05/1.55 r_next=0.203 MAD_above=1.56 lag=-3(1.52/1.56); L520 19.88/1.36 r_next=0.086 MAD_above=1.54 lag=7(1.52/1.54); L521 19.79/1.36 r_next=0.036 MAD_above=1.46 lag=-4(1.44/1.46); L522 18.89/1.74 r_next=0.049 MAD_above=1.89 lag=-16(1.63/1.89); L523 19.43/1.47 r_next=0.245 MAD_above=1.82 lag=25(1.70/1.82); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.194; no internal horizontal blanking run; gate=4.000) |
| 6271 | 6271/F2 | L511 | L525 | L510 20.07/1.54 r_next=0.048 MAD_above=1.62 lag=26(1.41/1.62); L511 19.75/1.58 r_next=-0.055 MAD_above=1.70 lag=11(1.58/1.70); L512 19.31/1.53 r_next=0.037 MAD_above=1.84 lag=32(1.61/1.84); L513 19.18/1.47 r_next=0.189 MAD_above=1.69 lag=7(1.51/1.69); L514 18.76/1.48 r_next=0.006 MAD_above=1.51 lag=3(1.47/1.51); L515 18.11/1.73 r_next=0.111 MAD_above=1.89 lag=-15(1.74/1.89); L516 18.39/1.52 r_next=0.021 MAD_above=1.77 lag=30(1.67/1.77); L517 18.22/1.35 r_next=0.031 MAD_above=1.58 lag=-24(1.40/1.58); L518 18.05/1.45 r_next=0.031 MAD_above=1.53 lag=24(1.38/1.53); L519 17.63/1.65 r_next=-0.019 MAD_above=1.69 lag=-5(1.62/1.69); L520 17.18/1.49 r_next=-0.007 MAD_above=1.81 lag=25(1.54/1.81); L521 17.29/1.54 r_next=0.054 MAD_above=1.70 lag=23(1.50/1.70); L522 17.73/1.39 r_next=-0.126 MAD_above=1.60 lag=25(1.52/1.60); L523 17.16/1.46 r_next=0.045 MAD_above=1.71 lag=24(1.49/1.71); L524 17.06/1.48 r_next=0.209 MAD_above=1.60 lag=-23(1.45/1.60); L525 16.54/1.99 r_next=-0.016 MAD_above=1.87 lag=-29(1.60/1.87); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.049; no internal horizontal blanking run; gate=4.000) |
| 6272 | 6272/F2 | L522 | L525 | L521 16.85/3.30 r_next=-0.021 MAD_above=3.07 lag=-27(2.87/3.07); L522 16.98/1.41 r_next=-0.083 MAD_above=2.75 lag=30(2.44/2.75); L523 17.12/1.27 r_next=0.000 MAD_above=1.55 lag=-17(1.27/1.55); L524 17.24/1.17 r_next=0.156 MAD_above=1.35 lag=17(1.23/1.35); L525 15.40/2.77 r_next=-0.015 MAD_above=2.77 lag=-10(2.60/2.77); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.050; no internal horizontal blanking run; gate=4.000) |
| 6273 | 6273/F2 | L522 | L525 | L521 16.93/3.28 r_next=-0.031 MAD_above=3.08 lag=32(2.91/3.08); L522 16.90/1.35 r_next=-0.071 MAD_above=2.71 lag=31(2.45/2.71); L523 17.19/1.28 r_next=0.029 MAD_above=1.49 lag=-17(1.28/1.49); L524 17.10/1.24 r_next=0.107 MAD_above=1.40 lag=18(1.26/1.40); L525 15.53/2.68 r_next=-0.018 MAD_above=2.67 lag=-8(2.49/2.67); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.065; no internal horizontal blanking run; gate=4.000) |
| 6277 | 6277/F2 | L518 | L524 | L517 4.31/1.37 r_next=-0.086 MAD_above=1.79 lag=31(1.41/1.79); L518 4.99/1.63 r_next=0.012 MAD_above=1.81 lag=24(1.62/1.81); L519 4.58/1.39 r_next=0.134 MAD_above=1.73 lag=26(1.54/1.73); L520 4.96/1.35 r_next=0.147 MAD_above=1.42 lag=15(1.37/1.42); L521 4.68/1.31 r_next=0.064 MAD_above=1.35 lag=-4(1.31/1.35); L522 5.13/1.31 r_next=0.094 MAD_above=1.44 lag=31(1.32/1.44); L523 4.49/1.28 r_next=0.123 MAD_above=1.44 lag=29(1.28/1.44); L524 5.41/1.50 r_next=0.255 MAD_above=1.57 lag=16(1.50/1.57); L525 5.61/1.34 r_next=-0.006 MAD_above=1.35 lag=3(1.34/1.35); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.055; no internal horizontal blanking run; gate=4.000) |
| 6278 | 6278/F2 | L339 | L522 | L338 7.66/2.12 r_next=-0.038 MAD_above=2.43 lag=16(2.14/2.43); L339 7.12/1.94 r_next=-0.076 MAD_above=2.43 lag=21(2.16/2.43); L340 7.50/1.93 r_next=-0.033 MAD_above=2.22 lag=28(1.88/2.22); L510 8.59/1.56 r_next=-0.009 MAD_above=1.57 lag=4(1.48/1.57); L511 8.81/1.49 r_next=-0.040 MAD_above=1.71 lag=21(1.58/1.71); L512 8.66/1.38 r_next=-0.009 MAD_above=1.58 lag=32(1.44/1.58); L513 8.45/1.39 r_next=0.005 MAD_above=1.49 lag=-11(1.40/1.49); L514 8.04/1.50 r_next=0.014 MAD_above=1.65 lag=-32(1.48/1.65); L515 8.31/1.40 r_next=0.012 MAD_above=1.58 lag=-20(1.41/1.58); L516 8.07/1.44 r_next=-0.006 MAD_above=1.52 lag=-16(1.40/1.52); L517 7.77/1.46 r_next=0.056 MAD_above=1.66 lag=10(1.44/1.66); L518 8.50/1.39 r_next=0.063 MAD_above=1.62 lag=4(1.59/1.62); L519 8.48/1.55 r_next=0.115 MAD_above=1.62 lag=31(1.55/1.62); L520 8.29/1.31 r_next=-0.158 MAD_above=1.50 lag=-28(1.41/1.50); L521 8.02/1.39 r_next=-0.209 MAD_above=1.59 lag=-10(1.32/1.59); L522 8.68/1.39 r_next=0.044 MAD_above=1.79 lag=31(1.51/1.79); L523 8.42/1.60 r_next=0.019 MAD_above=1.67 lag=9(1.58/1.67); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.061; no internal horizontal blanking run; gate=4.000) |
| 6290 | 6290/F2 | L495 | L525 | L494 16.11/2.57 r_next=0.580 MAD_above=2.13 lag=7(1.86/2.13); L495 16.00/1.63 r_next=0.397 MAD_above=1.98 lag=18(1.64/1.98); L496 16.13/1.80 r_next=0.068 MAD_above=1.82 lag=-16(1.63/1.82); L510 16.02/1.61 r_next=0.192 MAD_above=1.63 lag=12(1.46/1.63); L511 16.20/1.55 r_next=0.123 MAD_above=1.58 lag=5(1.52/1.58); L512 16.02/1.47 r_next=-0.085 MAD_above=1.58 lag=-8(1.45/1.58); L513 16.51/1.60 r_next=0.107 MAD_above=1.83 lag=18(1.52/1.83); L514 16.17/1.66 r_next=0.074 MAD_above=1.69 lag=0(1.69/1.69); L515 15.98/1.72 r_next=0.001 MAD_above=1.77 lag=-8(1.61/1.77); L516 16.15/1.64 r_next=0.066 MAD_above=1.84 lag=24(1.65/1.84); L517 16.21/1.61 r_next=0.203 MAD_above=1.68 lag=-9(1.55/1.68); L518 16.48/1.33 r_next=0.066 MAD_above=1.50 lag=2(1.43/1.50); L519 16.31/1.72 r_next=0.006 MAD_above=1.65 lag=-6(1.52/1.65); L520 15.99/1.70 r_next=0.104 MAD_above=1.91 lag=12(1.74/1.91); L521 16.31/1.66 r_next=0.041 MAD_above=1.73 lag=-6(1.66/1.73); L522 16.15/1.73 r_next=0.203 MAD_above=1.82 lag=18(1.65/1.82); L523 16.10/1.88 r_next=0.132 MAD_above=1.76 lag=-1(1.75/1.76); L524 15.45/2.00 r_next=0.045 MAD_above=2.02 lag=-6(1.90/2.02); L525 15.71/1.48 r_next=-0.034 MAD_above=1.83 lag=4(1.83/1.83); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.143; no internal horizontal blanking run; gate=4.000) |
| 6291 | 6291/F2 | L495 | L523 | L494 15.93/2.62 r_next=0.605 MAD_above=2.31 lag=8(2.00/2.31); L495 15.90/1.71 r_next=0.260 MAD_above=2.10 lag=25(1.73/2.10); L496 15.86/1.65 r_next=0.015 MAD_above=1.79 lag=12(1.60/1.79); L510 16.05/1.49 r_next=0.083 MAD_above=1.67 lag=-22(1.51/1.67); L511 15.68/1.57 r_next=0.125 MAD_above=1.59 lag=-16(1.44/1.59); L512 15.79/1.68 r_next=0.098 MAD_above=1.59 lag=-14(1.53/1.59); L513 16.17/1.60 r_next=0.075 MAD_above=1.66 lag=19(1.60/1.66); L514 15.89/1.58 r_next=0.064 MAD_above=1.71 lag=27(1.58/1.71); L515 15.79/1.75 r_next=-0.082 MAD_above=1.72 lag=-6(1.60/1.72); L516 15.85/1.52 r_next=0.097 MAD_above=1.84 lag=-14(1.54/1.84); L517 15.66/1.50 r_next=0.096 MAD_above=1.60 lag=14(1.52/1.60); L518 15.47/1.88 r_next=0.014 MAD_above=1.68 lag=5(1.57/1.68); L519 15.57/1.66 r_next=-0.043 MAD_above=1.75 lag=-2(1.68/1.75); L520 15.82/1.64 r_next=0.154 MAD_above=1.92 lag=10(1.69/1.92); L521 15.91/1.82 r_next=0.152 MAD_above=1.57 lag=-2(1.53/1.57); L522 15.57/1.73 r_next=0.053 MAD_above=1.76 lag=32(1.70/1.76); L523 15.80/1.94 r_next=0.137 MAD_above=1.95 lag=26(1.59/1.95); L524 15.54/1.77 r_next=0.115 MAD_above=1.98 lag=-9(1.75/1.98); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.166; no internal horizontal blanking run; gate=4.000) |
| 6292 | 6292/F2 | L496 | L523 | L495 17.08/2.01 r_next=0.584 MAD_above=1.98 lag=17(1.77/1.98); L496 16.82/1.77 r_next=0.676 MAD_above=2.09 lag=11(1.80/2.09); L497 16.82/1.58 r_next=0.492 MAD_above=1.74 lag=10(1.69/1.74); L510 16.72/1.48 r_next=0.148 MAD_above=1.56 lag=-9(1.50/1.56); L511 16.41/1.34 r_next=-0.097 MAD_above=1.52 lag=29(1.38/1.52); L512 16.46/1.47 r_next=0.138 MAD_above=1.55 lag=-25(1.35/1.55); L513 16.85/1.70 r_next=0.198 MAD_above=1.64 lag=-28(1.55/1.64); L514 16.53/1.55 r_next=0.059 MAD_above=1.66 lag=-30(1.60/1.66); L515 16.54/1.46 r_next=0.059 MAD_above=1.64 lag=-30(1.43/1.64); L516 16.62/1.54 r_next=0.056 MAD_above=1.65 lag=-28(1.47/1.65); L517 16.13/1.38 r_next=0.025 MAD_above=1.63 lag=31(1.48/1.63); L518 16.17/1.70 r_next=-0.042 MAD_above=1.66 lag=-15(1.47/1.66); L519 15.95/1.71 r_next=-0.128 MAD_above=1.87 lag=30(1.61/1.87); L520 16.36/1.75 r_next=0.086 MAD_above=2.10 lag=-27(1.78/2.10); L521 16.48/2.00 r_next=0.196 MAD_above=1.86 lag=32(1.75/1.86); L522 16.13/1.70 r_next=-0.009 MAD_above=1.74 lag=-32(1.64/1.74); L523 16.45/1.85 r_next=-0.018 MAD_above=1.96 lag=25(1.75/1.96); L524 16.21/1.73 r_next=-0.076 MAD_above=2.01 lag=20(1.76/2.01); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.159; no internal horizontal blanking run; gate=4.000) |
| 6293 | 6293/F2 | L500 | L524 | L499 17.62/2.02 r_next=0.729 MAD_above=2.02 lag=-32(1.78/2.02); L500 17.32/1.94 r_next=0.637 MAD_above=1.89 lag=31(1.73/1.89); L501 17.31/1.58 r_next=0.338 MAD_above=1.88 lag=7(1.62/1.88); L510 16.50/1.60 r_next=0.076 MAD_above=1.67 lag=30(1.54/1.67); L511 16.55/1.40 r_next=0.048 MAD_above=1.58 lag=-7(1.45/1.58); L512 16.42/1.37 r_next=-0.020 MAD_above=1.43 lag=25(1.40/1.43); L513 16.77/1.38 r_next=0.188 MAD_above=1.53 lag=26(1.43/1.53); L514 16.51/1.30 r_next=0.111 MAD_above=1.35 lag=22(1.33/1.35); L515 16.66/1.49 r_next=0.069 MAD_above=1.45 lag=-2(1.39/1.45); L516 16.11/1.28 r_next=-0.031 MAD_above=1.54 lag=24(1.42/1.54); L517 15.96/1.39 r_next=0.201 MAD_above=1.54 lag=25(1.25/1.54); L518 15.95/1.46 r_next=0.002 MAD_above=1.42 lag=19(1.36/1.42); L519 15.75/1.55 r_next=0.071 MAD_above=1.63 lag=-9(1.45/1.63); L520 16.10/1.62 r_next=0.093 MAD_above=1.73 lag=18(1.61/1.73); L521 16.44/1.35 r_next=0.093 MAD_above=1.55 lag=27(1.49/1.55); L522 16.25/1.56 r_next=-0.029 MAD_above=1.57 lag=-29(1.43/1.57); L523 16.67/1.74 r_next=0.139 MAD_above=1.90 lag=27(1.59/1.90); L524 16.10/1.61 r_next=0.065 MAD_above=1.83 lag=-9(1.64/1.83); L525 16.10/1.48 r_next=0.036 MAD_above=1.60 lag=-7(1.51/1.60); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.203; no internal horizontal blanking run; gate=4.000) |
| 6294 | 6294/F2 | L501 | L525 | L500 14.63/2.11 r_next=0.591 MAD_above=2.24 lag=-3(2.11/2.24); L501 15.66/1.71 r_next=0.400 MAD_above=2.00 lag=32(1.95/2.00); L502 15.81/1.72 r_next=-0.002 MAD_above=1.79 lag=8(1.58/1.79); L510 16.76/1.49 r_next=0.069 MAD_above=1.70 lag=-5(1.53/1.70); L511 17.07/1.64 r_next=0.136 MAD_above=1.72 lag=28(1.52/1.72); L512 17.14/1.62 r_next=0.118 MAD_above=1.61 lag=-5(1.53/1.61); L513 17.58/1.63 r_next=0.034 MAD_above=1.75 lag=-6(1.65/1.75); L514 17.40/1.74 r_next=0.247 MAD_above=1.79 lag=-7(1.72/1.79); L515 17.64/1.67 r_next=0.226 MAD_above=1.65 lag=2(1.58/1.65); L516 17.07/1.59 r_next=0.080 MAD_above=1.58 lag=-1(1.54/1.58); L517 17.17/1.57 r_next=0.037 MAD_above=1.60 lag=1(1.58/1.60); L518 16.82/1.47 r_next=0.031 MAD_above=1.65 lag=-8(1.43/1.65); L519 17.07/1.81 r_next=0.255 MAD_above=1.77 lag=-6(1.52/1.77); L520 17.23/1.84 r_next=-0.066 MAD_above=1.72 lag=-1(1.72/1.72); L521 17.09/1.69 r_next=-0.046 MAD_above=2.00 lag=-8(1.82/2.00); L522 17.09/1.66 r_next=0.056 MAD_above=1.89 lag=-27(1.67/1.89); L523 17.58/1.60 r_next=-0.001 MAD_above=1.78 lag=-5(1.66/1.78); L524 17.50/1.76 r_next=-0.004 MAD_above=1.90 lag=-21(1.64/1.90); L525 17.63/1.78 r_next=0.027 MAD_above=2.00 lag=-21(1.82/2.00); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.199; no internal horizontal blanking run; gate=4.000) |
| 6295 | 6295/F2 | L521 | L525 | L520 17.08/2.01 r_next=-0.040 MAD_above=2.03 lag=-25(1.83/2.03); L521 16.13/1.78 r_next=0.451 MAD_above=2.30 lag=-17(2.05/2.30); L522 16.71/1.60 r_next=0.416 MAD_above=1.84 lag=27(1.74/1.84); L523 17.25/1.60 r_next=0.083 MAD_above=1.80 lag=-13(1.66/1.80); L524 17.85/1.62 r_next=-0.094 MAD_above=1.84 lag=-6(1.68/1.84); L525 18.38/1.83 r_next=0.012 MAD_above=2.07 lag=8(1.76/2.07); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.232; no internal horizontal blanking run; gate=4.000) |
| 6297 | 6297/F2 | L429 | L525 | L428 18.40/1.28 r_next=0.076 MAD_above=1.34 lag=14(1.19/1.34); L429 18.21/1.30 r_next=0.176 MAD_above=1.33 lag=-32(1.29/1.33); L430 18.10/1.48 r_next=0.061 MAD_above=1.36 lag=-1(1.35/1.36); L510 17.12/1.50 r_next=0.100 MAD_above=1.67 lag=4(1.61/1.67); L511 16.96/1.56 r_next=-0.007 MAD_above=1.57 lag=-4(1.50/1.57); L512 17.25/1.33 r_next=0.119 MAD_above=1.60 lag=-7(1.39/1.60); L513 17.09/1.55 r_next=0.116 MAD_above=1.50 lag=-17(1.43/1.50); L514 17.45/1.44 r_next=-0.070 MAD_above=1.59 lag=32(1.45/1.59); L515 17.23/1.36 r_next=0.060 MAD_above=1.57 lag=15(1.35/1.57); L516 16.86/1.26 r_next=0.151 MAD_above=1.37 lag=1(1.32/1.37); L517 17.13/1.55 r_next=0.131 MAD_above=1.42 lag=32(1.32/1.42); L518 17.15/1.28 r_next=0.064 MAD_above=1.46 lag=26(1.40/1.46); L519 17.05/1.43 r_next=-0.028 MAD_above=1.45 lag=20(1.23/1.45); L520 16.90/1.38 r_next=0.112 MAD_above=1.61 lag=-19(1.34/1.61); L521 16.95/1.36 r_next=0.127 MAD_above=1.45 lag=-18(1.28/1.45); L522 16.79/1.32 r_next=0.031 MAD_above=1.38 lag=14(1.29/1.38); L523 16.77/1.38 r_next=0.041 MAD_above=1.50 lag=14(1.26/1.50); L524 17.02/1.38 r_next=0.093 MAD_above=1.45 lag=28(1.39/1.45); L525 15.20/1.49 r_next=0.033 MAD_above=2.15 lag=-16(2.02/2.15); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.214; no internal horizontal blanking run; gate=4.000) |
| 6298 | 6298/F2 | L398 | L525 | L397 19.58/1.12 r_next=0.246 MAD_above=1.10 lag=-13(0.95/1.10); L398 19.42/1.08 r_next=0.234 MAD_above=1.04 lag=-32(0.95/1.04); L399 19.42/1.05 r_next=0.235 MAD_above=0.98 lag=0(0.98/0.98); L510 17.69/1.38 r_next=0.201 MAD_above=1.53 lag=22(1.38/1.53); L511 17.63/1.55 r_next=0.136 MAD_above=1.48 lag=-6(1.38/1.48); L512 17.51/1.38 r_next=0.099 MAD_above=1.50 lag=26(1.38/1.50); L513 17.35/1.45 r_next=0.089 MAD_above=1.50 lag=8(1.32/1.50); L514 17.37/1.31 r_next=0.142 MAD_above=1.51 lag=-26(1.34/1.51); L515 17.29/1.33 r_next=0.110 MAD_above=1.35 lag=-21(1.27/1.35); L516 17.19/1.30 r_next=0.155 MAD_above=1.38 lag=-32(1.35/1.38); L517 17.33/1.36 r_next=0.089 MAD_above=1.37 lag=4(1.36/1.37); L518 17.28/1.30 r_next=0.096 MAD_above=1.43 lag=32(1.23/1.43); L519 17.21/1.34 r_next=0.032 MAD_above=1.40 lag=21(1.09/1.40); L520 17.21/1.33 r_next=0.241 MAD_above=1.49 lag=-26(1.27/1.49); L521 17.08/1.39 r_next=0.206 MAD_above=1.32 lag=-7(1.22/1.32); L522 17.07/1.43 r_next=0.078 MAD_above=1.40 lag=2(1.39/1.40); L523 17.08/1.49 r_next=0.048 MAD_above=1.59 lag=19(1.45/1.59); L524 17.48/1.35 r_next=0.069 MAD_above=1.55 lag=-32(1.34/1.55); L525 16.40/1.58 r_next=0.027 MAD_above=1.89 lag=-13(1.67/1.89); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.197; no internal horizontal blanking run; gate=4.000) |
| 6299 | 6299/F2 | L350 | L525 | L349 20.81/2.14 r_next=0.007 MAD_above=2.29 lag=-27(2.24/2.29); L350 20.16/1.69 r_next=0.018 MAD_above=2.13 lag=-7(1.94/2.13); L351 20.45/1.80 r_next=0.188 MAD_above=1.91 lag=16(1.70/1.91); L510 19.22/1.20 r_next=0.160 MAD_above=1.24 lag=-22(1.12/1.24); L511 19.37/1.32 r_next=0.071 MAD_above=1.24 lag=12(1.20/1.24); L512 19.24/1.20 r_next=0.168 MAD_above=1.39 lag=23(1.13/1.39); L513 18.85/1.30 r_next=0.183 MAD_above=1.28 lag=0(1.28/1.28); L514 19.03/1.24 r_next=0.159 MAD_above=1.29 lag=19(1.26/1.29); L515 18.89/1.37 r_next=0.042 MAD_above=1.35 lag=5(1.23/1.35); L516 18.91/1.32 r_next=0.111 MAD_above=1.44 lag=-15(1.25/1.44); L517 18.68/1.22 r_next=0.194 MAD_above=1.34 lag=-6(1.24/1.34); L518 18.70/1.43 r_next=0.225 MAD_above=1.29 lag=29(1.16/1.29); L519 19.07/1.58 r_next=0.013 MAD_above=1.48 lag=2(1.45/1.48); L520 18.53/1.19 r_next=0.156 MAD_above=1.58 lag=16(1.33/1.58); L521 18.47/1.33 r_next=-0.044 MAD_above=1.30 lag=-32(1.20/1.30); L522 18.49/1.25 r_next=-0.051 MAD_above=1.48 lag=-16(1.28/1.48); L523 18.38/1.23 r_next=0.138 MAD_above=1.41 lag=11(1.12/1.41); L524 18.38/1.28 r_next=0.014 MAD_above=1.30 lag=4(1.22/1.30); L525 19.69/1.40 r_next=-0.051 MAD_above=1.80 lag=31(1.75/1.80); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.235; no internal horizontal blanking run; gate=4.000) |
| 6300 | 6300/F2 | L454 | L522 | L453 19.32/2.42 r_next=0.195 MAD_above=2.51 lag=-12(2.33/2.51); L454 19.64/1.62 r_next=0.107 MAD_above=2.09 lag=-4(1.97/2.09); L455 19.44/1.78 r_next=0.013 MAD_above=1.80 lag=4(1.74/1.80); L510 19.40/1.04 r_next=0.022 MAD_above=1.07 lag=27(0.99/1.07); L511 19.58/1.13 r_next=0.248 MAD_above=1.18 lag=-27(1.06/1.18); L512 19.62/1.16 r_next=0.149 MAD_above=1.08 lag=2(1.04/1.08); L513 19.55/1.10 r_next=0.270 MAD_above=1.18 lag=31(1.08/1.18); L514 19.30/1.26 r_next=0.243 MAD_above=1.12 lag=14(1.06/1.12); L515 19.21/1.02 r_next=0.081 MAD_above=1.08 lag=-19(1.03/1.08); L516 19.09/1.14 r_next=0.168 MAD_above=1.11 lag=4(1.02/1.11); L517 19.30/1.12 r_next=0.098 MAD_above=1.12 lag=-23(1.05/1.12); L518 18.96/1.05 r_next=0.273 MAD_above=1.15 lag=15(1.06/1.15); L519 18.89/1.15 r_next=0.248 MAD_above=1.02 lag=-5(0.96/1.02); L520 19.01/1.32 r_next=0.189 MAD_above=1.17 lag=8(1.12/1.17); L521 19.10/1.14 r_next=0.126 MAD_above=1.24 lag=11(1.18/1.24); L522 18.81/1.27 r_next=0.232 MAD_above=1.24 lag=26(1.09/1.24); L523 19.05/1.14 r_next=0.151 MAD_above=1.14 lag=3(1.12/1.14); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.195; no internal horizontal blanking run; gate=4.000) |
| 6301 | 6301/F2 | L345 | L522 | L344 20.60/1.39 r_next=0.068 MAD_above=1.42 lag=-31(1.26/1.42); L345 20.44/1.39 r_next=0.099 MAD_above=1.49 lag=29(1.37/1.49); L346 20.45/1.29 r_next=0.027 MAD_above=1.39 lag=25(1.34/1.39); L510 19.14/1.19 r_next=0.075 MAD_above=1.28 lag=30(1.21/1.28); L511 19.22/1.18 r_next=0.188 MAD_above=1.25 lag=12(1.12/1.25); L512 19.21/1.30 r_next=0.175 MAD_above=1.19 lag=-24(1.16/1.19); L513 19.15/1.19 r_next=0.165 MAD_above=1.24 lag=-28(1.19/1.24); L514 19.20/1.15 r_next=0.243 MAD_above=1.17 lag=-29(1.04/1.17); L515 19.04/1.19 r_next=0.197 MAD_above=1.10 lag=-16(1.04/1.10); L516 18.96/1.23 r_next=0.124 MAD_above=1.15 lag=-29(1.05/1.15); L517 18.89/1.09 r_next=0.115 MAD_above=1.16 lag=25(1.07/1.16); L518 18.47/1.22 r_next=0.226 MAD_above=1.24 lag=-17(1.10/1.24); L519 18.47/1.23 r_next=0.233 MAD_above=1.19 lag=-12(1.06/1.19); L520 18.71/1.28 r_next=0.255 MAD_above=1.18 lag=-2(1.13/1.18); L521 18.39/1.12 r_next=0.033 MAD_above=1.17 lag=-10(1.16/1.17); L522 18.39/1.21 r_next=0.201 MAD_above=1.30 lag=-13(1.07/1.30); L523 18.45/1.23 r_next=0.168 MAD_above=1.20 lag=-2(1.15/1.20); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.240; no internal horizontal blanking run; gate=4.000) |
| 6302 | 6302/F2 | L429 | L523 | L428 19.43/2.29 r_next=-0.064 MAD_above=2.45 lag=-26(2.26/2.45); L429 19.93/1.91 r_next=-0.053 MAD_above=2.49 lag=-17(2.22/2.49); L430 19.97/1.93 r_next=0.084 MAD_above=2.21 lag=32(1.93/2.21); L510 18.60/1.15 r_next=0.134 MAD_above=1.25 lag=-25(1.12/1.25); L511 18.52/1.08 r_next=0.164 MAD_above=1.14 lag=-18(1.00/1.14); L512 18.56/1.19 r_next=0.051 MAD_above=1.10 lag=27(1.03/1.10); L513 18.49/1.08 r_next=0.100 MAD_above=1.22 lag=-18(1.07/1.22); L514 18.24/1.10 r_next=0.144 MAD_above=1.19 lag=-14(1.01/1.19); L515 18.49/1.11 r_next=0.256 MAD_above=1.13 lag=29(1.01/1.13); L516 18.27/1.06 r_next=0.184 MAD_above=1.02 lag=-4(0.97/1.02); L517 18.17/1.04 r_next=0.220 MAD_above=1.00 lag=1(0.96/1.00); L518 18.19/1.13 r_next=0.264 MAD_above=1.05 lag=-1(1.01/1.05); L519 17.93/1.08 r_next=0.095 MAD_above=1.06 lag=-10(0.98/1.06); L520 17.85/1.13 r_next=0.148 MAD_above=1.15 lag=19(0.98/1.15); L521 17.98/0.98 r_next=0.085 MAD_above=1.08 lag=-7(0.99/1.08); L522 17.96/1.17 r_next=0.167 MAD_above=1.12 lag=-14(1.03/1.12); L523 18.13/1.09 r_next=0.188 MAD_above=1.12 lag=-6(1.06/1.12); L524 17.99/1.10 r_next=0.242 MAD_above=1.07 lag=-22(0.97/1.07); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.200; no internal horizontal blanking run; gate=4.000) |
| 6303 | 6303/F2 | L415 | L523 | L414 19.95/2.16 r_next=-0.025 MAD_above=1.93 lag=-21(1.79/1.93); L415 20.34/1.77 r_next=0.030 MAD_above=2.14 lag=-18(1.93/2.14); L416 20.07/1.89 r_next=0.074 MAD_above=2.01 lag=19(1.80/2.01); L510 18.89/1.02 r_next=0.113 MAD_above=1.01 lag=3(0.97/1.01); L511 18.81/1.04 r_next=0.157 MAD_above=1.08 lag=-19(0.89/1.08); L512 18.81/1.12 r_next=0.072 MAD_above=1.02 lag=-13(0.94/1.02); L513 18.86/0.94 r_next=0.089 MAD_above=1.07 lag=-32(0.94/1.07); L514 18.82/0.95 r_next=0.192 MAD_above=0.95 lag=-31(0.90/0.95); L515 18.55/1.01 r_next=0.209 MAD_above=0.95 lag=23(0.93/0.95); L516 18.44/1.00 r_next=0.224 MAD_above=0.95 lag=-16(0.89/0.95); L517 18.15/0.92 r_next=0.101 MAD_above=0.90 lag=1(0.85/0.90); L518 18.05/0.96 r_next=0.228 MAD_above=0.95 lag=24(0.87/0.95); L519 18.19/1.03 r_next=0.138 MAD_above=0.95 lag=18(0.92/0.95); L520 18.28/1.02 r_next=0.264 MAD_above=1.02 lag=25(0.95/1.02); L521 18.14/0.91 r_next=0.248 MAD_above=0.92 lag=-31(0.88/0.92); L522 18.16/1.11 r_next=0.187 MAD_above=0.97 lag=3(0.90/0.97); L523 18.20/1.01 r_next=0.195 MAD_above=1.02 lag=-7(0.93/1.02); L524 18.25/0.98 r_next=0.145 MAD_above=0.95 lag=-1(0.90/0.95); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.216; no internal horizontal blanking run; gate=4.000) |
| 6304 | 6304/F2 | L396 | L523 | L395 20.59/2.75 r_next=0.119 MAD_above=2.76 lag=20(2.52/2.76); L396 19.88/1.87 r_next=0.017 MAD_above=2.33 lag=-29(2.30/2.33); L397 20.10/1.86 r_next=0.164 MAD_above=1.95 lag=32(1.75/1.95); L510 18.80/0.95 r_next=0.294 MAD_above=0.89 lag=4(0.85/0.89); L511 18.64/0.88 r_next=0.067 MAD_above=0.82 lag=-22(0.80/0.82); L512 18.87/0.94 r_next=0.118 MAD_above=0.93 lag=24(0.86/0.93); L513 18.83/0.93 r_next=0.146 MAD_above=0.93 lag=-6(0.89/0.93); L514 18.72/1.06 r_next=0.335 MAD_above=1.00 lag=24(0.91/1.00); L515 18.73/1.00 r_next=0.115 MAD_above=0.90 lag=-2(0.90/0.90); L516 18.74/0.84 r_next=0.137 MAD_above=0.90 lag=22(0.83/0.90); L517 18.46/0.88 r_next=0.211 MAD_above=0.84 lag=-8(0.82/0.84); L518 18.43/0.97 r_next=0.170 MAD_above=0.87 lag=1(0.85/0.87); L519 18.17/0.99 r_next=0.189 MAD_above=0.96 lag=16(0.89/0.96); L520 17.87/0.99 r_next=0.258 MAD_above=0.98 lag=-13(0.90/0.98); L521 18.23/1.04 r_next=0.229 MAD_above=0.97 lag=-2(0.94/0.97); L522 18.13/0.97 r_next=0.232 MAD_above=0.93 lag=1(0.88/0.93); L523 18.19/1.07 r_next=0.211 MAD_above=0.95 lag=6(0.91/0.95); L524 18.35/0.94 r_next=0.155 MAD_above=0.96 lag=10(0.93/0.96); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.259; no internal horizontal blanking run; gate=4.000) |
| 6305 | 6305/F2 | L390 | L524 | L389 18.27/2.28 r_next=-0.198 MAD_above=2.15 lag=-13(2.01/2.15); L390 18.74/1.57 r_next=0.189 MAD_above=2.11 lag=10(1.93/2.11); L391 18.92/1.50 r_next=0.084 MAD_above=1.58 lag=31(1.44/1.58); L510 18.49/0.96 r_next=0.262 MAD_above=0.95 lag=-23(0.89/0.95); L511 18.45/1.03 r_next=0.237 MAD_above=0.93 lag=-4(0.88/0.93); L512 18.36/0.97 r_next=0.151 MAD_above=0.94 lag=-22(0.88/0.94); L513 18.18/0.94 r_next=0.151 MAD_above=0.94 lag=-3(0.90/0.94); L514 18.10/0.99 r_next=0.174 MAD_above=0.94 lag=29(0.87/0.94); L515 18.16/1.10 r_next=0.137 MAD_above=1.04 lag=-3(0.98/1.04); L516 18.21/1.01 r_next=0.149 MAD_above=1.03 lag=-25(0.95/1.03); L517 18.20/0.97 r_next=0.147 MAD_above=0.97 lag=-18(0.88/0.97); L518 18.08/0.93 r_next=0.196 MAD_above=0.93 lag=24(0.87/0.93); L519 17.70/0.92 r_next=0.183 MAD_above=0.93 lag=-2(0.90/0.93); L520 17.77/0.91 r_next=0.152 MAD_above=0.87 lag=6(0.84/0.87); L521 17.92/0.98 r_next=0.138 MAD_above=0.93 lag=1(0.92/0.93); L522 18.06/1.02 r_next=0.109 MAD_above=1.03 lag=12(0.92/1.03); L523 17.76/0.99 r_next=0.004 MAD_above=1.07 lag=31(0.98/1.07); L524 17.99/1.00 r_next=0.137 MAD_above=1.09 lag=-13(0.97/1.09); L525 17.78/1.09 r_next=0.083 MAD_above=1.05 lag=6(1.01/1.05); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.284; no internal horizontal blanking run; gate=4.000) |
| 6306 | 6306/F2 | L379 | L523 | L378 18.00/4.41 r_next=0.101 MAD_above=3.38 lag=26(3.05/3.38); L379 18.90/1.58 r_next=0.136 MAD_above=2.93 lag=2(2.88/2.93); L380 18.95/1.65 r_next=0.066 MAD_above=1.68 lag=-5(1.58/1.68); L510 18.38/1.11 r_next=0.131 MAD_above=1.15 lag=-30(1.10/1.15); L511 18.40/1.19 r_next=0.134 MAD_above=1.17 lag=17(1.12/1.17); L512 18.53/1.17 r_next=0.062 MAD_above=1.19 lag=-7(1.08/1.19); L513 18.34/1.12 r_next=0.110 MAD_above=1.20 lag=19(1.12/1.20); L514 18.27/1.19 r_next=0.065 MAD_above=1.19 lag=-29(1.11/1.19); L515 18.58/1.15 r_next=0.164 MAD_above=1.22 lag=22(1.12/1.22); L516 18.22/1.20 r_next=0.079 MAD_above=1.20 lag=-5(1.14/1.20); L517 18.13/1.15 r_next=0.065 MAD_above=1.26 lag=-12(1.05/1.26); L518 17.73/1.17 r_next=0.207 MAD_above=1.17 lag=-10(1.07/1.17); L519 17.99/1.20 r_next=0.110 MAD_above=1.16 lag=6(1.12/1.16); L520 18.09/1.24 r_next=0.169 MAD_above=1.26 lag=-5(1.22/1.26); L521 18.00/1.11 r_next=0.150 MAD_above=1.14 lag=-5(1.09/1.14); L522 17.92/1.19 r_next=0.062 MAD_above=1.15 lag=3(1.12/1.15); L523 17.83/1.15 r_next=0.134 MAD_above=1.23 lag=24(1.17/1.23); L524 17.78/1.16 r_next=0.170 MAD_above=1.13 lag=31(1.10/1.13); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.226; no internal horizontal blanking run; gate=4.000) |
| 6307 | 6307/F2 | L382 | L525 | L381 20.23/2.32 r_next=0.047 MAD_above=2.15 lag=26(2.06/2.15); L382 19.82/1.74 r_next=0.049 MAD_above=2.29 lag=-23(2.09/2.29); L383 19.31/1.81 r_next=0.071 MAD_above=1.97 lag=7(1.74/1.97); L510 17.82/1.03 r_next=0.165 MAD_above=1.04 lag=-25(1.00/1.04); L511 17.95/1.15 r_next=0.230 MAD_above=1.11 lag=31(1.00/1.11); L512 17.78/1.10 r_next=0.240 MAD_above=1.09 lag=-11(0.97/1.09); L513 17.55/1.15 r_next=0.233 MAD_above=1.06 lag=-3(1.05/1.06); L514 17.56/1.11 r_next=0.105 MAD_above=1.10 lag=-7(1.06/1.10); L515 17.49/1.21 r_next=0.109 MAD_above=1.23 lag=-29(1.10/1.23); L516 17.57/1.11 r_next=0.128 MAD_above=1.19 lag=29(1.08/1.19); L517 17.35/1.04 r_next=0.191 MAD_above=1.08 lag=-16(1.00/1.08); L518 17.27/1.15 r_next=0.167 MAD_above=1.05 lag=11(0.98/1.05); L519 17.12/1.05 r_next=0.164 MAD_above=1.08 lag=-9(0.99/1.08); L520 17.15/1.12 r_next=0.111 MAD_above=1.11 lag=21(0.98/1.11); L521 17.16/1.10 r_next=0.248 MAD_above=1.13 lag=-5(1.06/1.13); L522 17.32/1.12 r_next=0.136 MAD_above=1.03 lag=-2(1.01/1.03); L523 16.98/1.02 r_next=0.043 MAD_above=1.12 lag=-26(1.08/1.12); L524 17.13/1.03 r_next=0.100 MAD_above=1.10 lag=-21(0.99/1.10); L525 17.03/1.05 r_next=0.017 MAD_above=1.06 lag=24(0.91/1.06); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.282; no internal horizontal blanking run; gate=4.000) |
| 6308 | 6308/F2 | L372 | L525 | L371 20.21/1.83 r_next=0.115 MAD_above=3.80 lag=-24(3.52/3.80); L372 19.59/1.88 r_next=0.174 MAD_above=1.97 lag=14(1.87/1.97); L373 19.37/2.00 r_next=0.175 MAD_above=1.94 lag=-26(1.86/1.94); L510 16.90/1.25 r_next=0.199 MAD_above=1.29 lag=21(1.19/1.29); L511 17.04/1.30 r_next=0.130 MAD_above=1.29 lag=28(1.20/1.29); L512 17.55/1.19 r_next=0.073 MAD_above=1.32 lag=11(1.24/1.32); L513 17.76/1.19 r_next=0.021 MAD_above=1.25 lag=-18(1.17/1.25); L514 17.71/1.41 r_next=0.190 MAD_above=1.43 lag=26(1.29/1.43); L515 18.31/1.23 r_next=0.176 MAD_above=1.43 lag=22(1.36/1.43); L516 18.31/1.37 r_next=0.083 MAD_above=1.33 lag=28(1.22/1.33); L517 18.13/1.33 r_next=0.153 MAD_above=1.46 lag=15(1.23/1.46); L518 17.92/1.33 r_next=0.145 MAD_above=1.36 lag=-30(1.30/1.36); L519 17.91/1.39 r_next=0.232 MAD_above=1.34 lag=-31(1.24/1.34); L520 18.18/1.46 r_next=0.207 MAD_above=1.35 lag=4(1.34/1.35); L521 18.07/1.31 r_next=0.112 MAD_above=1.34 lag=0(1.34/1.34); L522 18.47/1.50 r_next=0.158 MAD_above=1.55 lag=-6(1.41/1.55); L523 18.28/1.38 r_next=0.199 MAD_above=1.45 lag=-29(1.39/1.45); L524 17.85/1.41 r_next=0.107 MAD_above=1.41 lag=-4(1.35/1.41); L525 18.41/1.38 r_next=-0.036 MAD_above=1.51 lag=6(1.41/1.51); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.249; no internal horizontal blanking run; gate=4.000) |
| 6309 | 6309/F2 | L372 | L524 | L371 18.68/2.89 r_next=-0.021 MAD_above=3.28 lag=-25(2.94/3.28); L372 17.01/1.67 r_next=0.217 MAD_above=2.93 lag=25(2.73/2.93); L373 17.29/1.77 r_next=0.081 MAD_above=1.69 lag=0(1.69/1.69); L510 16.15/1.19 r_next=0.142 MAD_above=1.24 lag=-4(1.10/1.24); L511 16.78/1.37 r_next=0.225 MAD_above=1.42 lag=12(1.28/1.42); L512 16.73/1.23 r_next=0.017 MAD_above=1.22 lag=1(1.21/1.22); L513 17.10/1.28 r_next=0.054 MAD_above=1.37 lag=30(1.20/1.37); L514 17.26/1.25 r_next=0.123 MAD_above=1.36 lag=29(1.24/1.36); L515 17.81/1.26 r_next=0.199 MAD_above=1.36 lag=5(1.20/1.36); L516 17.87/1.35 r_next=0.102 MAD_above=1.30 lag=3(1.25/1.30); L517 17.70/1.41 r_next=0.214 MAD_above=1.43 lag=29(1.22/1.43); L518 17.56/1.35 r_next=0.127 MAD_above=1.36 lag=5(1.23/1.36); L519 17.34/1.38 r_next=-0.046 MAD_above=1.39 lag=-32(1.23/1.39); L520 17.21/1.44 r_next=0.094 MAD_above=1.57 lag=21(1.38/1.57); L521 17.12/1.45 r_next=0.141 MAD_above=1.48 lag=-13(1.41/1.48); L522 17.17/1.40 r_next=-0.016 MAD_above=1.44 lag=-5(1.33/1.44); L523 17.05/1.56 r_next=-0.028 MAD_above=1.65 lag=21(1.39/1.65); L524 17.23/1.55 r_next=0.165 MAD_above=1.75 lag=-25(1.56/1.75); L525 17.37/1.63 r_next=0.007 MAD_above=1.58 lag=-2(1.51/1.58); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.248; no internal horizontal blanking run; gate=4.000) |
| 6310 | 6310/F2 | L373 | L523 | L372 15.18/2.10 r_next=0.105 MAD_above=2.22 lag=-26(2.18/2.22); L373 15.77/1.93 r_next=0.048 MAD_above=2.15 lag=8(2.02/2.15); L374 16.34/1.98 r_next=-0.030 MAD_above=2.14 lag=-16(1.90/2.14); L510 16.19/1.38 r_next=0.163 MAD_above=1.32 lag=-1(1.32/1.32); L511 16.36/1.48 r_next=0.105 MAD_above=1.45 lag=-26(1.38/1.45); L512 16.54/1.20 r_next=0.172 MAD_above=1.41 lag=-5(1.36/1.41); L513 16.84/1.60 r_next=-0.008 MAD_above=1.40 lag=32(1.39/1.40); L514 17.02/1.33 r_next=0.061 MAD_above=1.49 lag=23(1.33/1.49); L515 17.15/1.40 r_next=0.168 MAD_above=1.51 lag=27(1.34/1.51); L516 17.12/1.28 r_next=0.088 MAD_above=1.36 lag=-8(1.28/1.36); L517 17.10/1.27 r_next=0.201 MAD_above=1.28 lag=8(1.18/1.28); L518 16.90/1.35 r_next=0.074 MAD_above=1.25 lag=2(1.22/1.25); L519 16.70/1.46 r_next=0.118 MAD_above=1.49 lag=32(1.36/1.49); L520 16.51/1.30 r_next=0.205 MAD_above=1.45 lag=21(1.30/1.45); L521 16.47/1.31 r_next=0.117 MAD_above=1.20 lag=0(1.20/1.20); L522 16.23/1.48 r_next=-0.021 MAD_above=1.43 lag=29(1.43/1.43); L523 16.17/1.40 r_next=0.176 MAD_above=1.57 lag=6(1.40/1.57); L524 16.42/1.37 r_next=0.134 MAD_above=1.38 lag=1(1.36/1.38); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.268; no internal horizontal blanking run; gate=4.000) |
| 6311 | 6311/F2 | L370 | L522 | L369 19.20/3.96 r_next=0.117 MAD_above=3.74 lag=-4(3.54/3.74); L370 16.34/2.00 r_next=0.361 MAD_above=3.81 lag=-32(3.75/3.81); L371 16.50/1.72 r_next=0.567 MAD_above=1.95 lag=-6(1.81/1.95); L510 16.62/1.36 r_next=0.084 MAD_above=1.40 lag=-4(1.37/1.40); L511 16.88/1.38 r_next=0.155 MAD_above=1.43 lag=-3(1.38/1.43); L512 16.54/1.38 r_next=0.138 MAD_above=1.40 lag=2(1.38/1.40); L513 16.84/1.21 r_next=0.130 MAD_above=1.35 lag=20(1.30/1.35); L514 17.35/1.85 r_next=0.139 MAD_above=1.56 lag=-15(1.36/1.56); L515 17.31/1.31 r_next=0.042 MAD_above=1.56 lag=6(1.49/1.56); L516 17.15/1.35 r_next=0.183 MAD_above=1.44 lag=17(1.28/1.44); L517 16.99/1.34 r_next=0.201 MAD_above=1.33 lag=-28(1.29/1.33); L518 17.05/1.58 r_next=0.158 MAD_above=1.43 lag=-7(1.36/1.43); L519 17.18/1.51 r_next=0.209 MAD_above=1.57 lag=-22(1.45/1.57); L520 17.02/1.39 r_next=0.106 MAD_above=1.48 lag=1(1.42/1.48); L521 16.89/1.46 r_next=-0.069 MAD_above=1.46 lag=1(1.45/1.46); L522 16.64/1.47 r_next=0.128 MAD_above=1.62 lag=11(1.50/1.62); L523 16.59/1.28 r_next=0.105 MAD_above=1.36 lag=18(1.33/1.36); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.254; no internal horizontal blanking run; gate=4.000) |
| 6312 | 6312/F2 | L370 | L525 | L369 18.81/2.06 r_next=0.175 MAD_above=2.07 lag=-3(2.03/2.07); L370 17.71/1.82 r_next=-0.017 MAD_above=2.14 lag=-30(2.10/2.14); L371 17.53/1.47 r_next=0.106 MAD_above=1.90 lag=21(1.70/1.90); L510 16.90/1.42 r_next=0.123 MAD_above=1.51 lag=-23(1.45/1.51); L511 17.02/1.52 r_next=0.010 MAD_above=1.49 lag=32(1.47/1.49); L512 16.91/1.48 r_next=-0.025 MAD_above=1.70 lag=17(1.51/1.70); L513 16.95/1.35 r_next=0.159 MAD_above=1.56 lag=22(1.36/1.56); L514 17.15/1.63 r_next=0.066 MAD_above=1.51 lag=-5(1.35/1.51); L515 17.00/1.63 r_next=0.079 MAD_above=1.76 lag=21(1.61/1.76); L516 17.09/1.38 r_next=0.050 MAD_above=1.58 lag=-10(1.43/1.58); L517 16.86/1.39 r_next=0.125 MAD_above=1.51 lag=25(1.33/1.51); L518 16.95/1.44 r_next=0.024 MAD_above=1.46 lag=-5(1.40/1.46); L519 17.11/1.54 r_next=0.101 MAD_above=1.59 lag=-14(1.47/1.59); L520 16.84/1.46 r_next=0.207 MAD_above=1.59 lag=-19(1.49/1.59); L521 16.72/1.57 r_next=0.253 MAD_above=1.49 lag=-1(1.47/1.49); L522 16.79/1.51 r_next=0.201 MAD_above=1.45 lag=-1(1.45/1.45); L523 16.79/1.25 r_next=0.131 MAD_above=1.33 lag=2(1.27/1.33); L524 17.30/1.45 r_next=0.190 MAD_above=1.47 lag=-32(1.38/1.47); L525 17.30/1.46 r_next=-0.031 MAD_above=1.46 lag=3(1.46/1.46); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.259; no internal horizontal blanking run; gate=4.000) |
| 6313 | 6313/F2 | L365 | L525 | L364 17.99/2.28 r_next=0.316 MAD_above=3.54 lag=19(3.33/3.54); L365 17.60/1.53 r_next=0.564 MAD_above=2.03 lag=-3(1.94/2.03); L366 18.40/1.92 r_next=0.211 MAD_above=1.90 lag=32(1.80/1.90); L510 17.49/1.61 r_next=-0.026 MAD_above=1.79 lag=12(1.51/1.79); L511 17.55/1.42 r_next=0.060 MAD_above=1.72 lag=20(1.51/1.72); L512 17.27/1.36 r_next=0.060 MAD_above=1.53 lag=21(1.34/1.53); L513 17.42/1.35 r_next=0.084 MAD_above=1.49 lag=18(1.33/1.49); L514 17.87/1.55 r_next=0.095 MAD_above=1.57 lag=13(1.47/1.57); L515 17.87/1.61 r_next=0.051 MAD_above=1.68 lag=-18(1.54/1.68); L516 17.85/1.49 r_next=0.078 MAD_above=1.64 lag=-32(1.44/1.64); L517 17.55/1.59 r_next=0.115 MAD_above=1.63 lag=-4(1.50/1.63); L518 17.70/1.77 r_next=0.078 MAD_above=1.74 lag=-8(1.69/1.74); L519 17.48/1.69 r_next=0.057 MAD_above=1.82 lag=19(1.74/1.82); L520 16.93/1.48 r_next=0.052 MAD_above=1.69 lag=25(1.56/1.69); L521 16.82/1.38 r_next=0.110 MAD_above=1.53 lag=7(1.44/1.53); L522 17.11/1.54 r_next=0.090 MAD_above=1.55 lag=7(1.49/1.55); L523 16.61/1.27 r_next=0.140 MAD_above=1.55 lag=3(1.46/1.55); L524 17.17/1.34 r_next=0.067 MAD_above=1.46 lag=23(1.38/1.46); L525 17.56/1.50 r_next=-0.011 MAD_above=1.51 lag=6(1.41/1.51); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.262; no internal horizontal blanking run; gate=4.000) |
| 6315 | 6315/F2 | L518 | L524 | L517 18.87/2.63 r_next=0.141 MAD_above=2.66 lag=-23(2.32/2.66); L518 19.41/1.89 r_next=-0.186 MAD_above=2.45 lag=-10(2.23/2.45); L519 18.17/1.80 r_next=0.217 MAD_above=2.27 lag=-9(2.00/2.27); L520 18.39/1.73 r_next=-0.050 MAD_above=1.76 lag=2(1.71/1.76); L521 18.32/1.70 r_next=0.654 MAD_above=1.79 lag=-7(1.67/1.79); L522 18.69/1.97 r_next=0.715 MAD_above=1.97 lag=3(1.84/1.97); L523 18.74/1.92 r_next=0.571 MAD_above=1.91 lag=-24(1.81/1.91); L524 18.97/1.90 r_next=0.299 MAD_above=1.96 lag=-4(1.83/1.96); L525 19.50/1.64 r_next=0.010 MAD_above=1.98 lag=32(1.85/1.98); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.230; no internal horizontal blanking run; gate=4.000) |
| 6316 | 6316/F2 | L520 | L524 | L519 19.48/2.03 r_next=-0.116 MAD_above=2.18 lag=-6(2.01/2.18); L520 19.85/1.85 r_next=-0.137 MAD_above=2.37 lag=-9(1.98/2.37); L521 19.54/2.17 r_next=0.733 MAD_above=2.14 lag=17(1.91/2.14); L522 19.80/2.34 r_next=0.726 MAD_above=1.89 lag=3(1.77/1.89); L523 20.24/2.38 r_next=0.621 MAD_above=2.02 lag=29(1.97/2.02); L524 20.90/1.71 r_next=0.248 MAD_above=2.04 lag=-10(1.79/2.04); L525 21.21/1.61 r_next=0.020 MAD_above=2.12 lag=-16(1.59/2.12); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.199; no internal horizontal blanking run; gate=4.000) |
| 6318 | 6318/F2 | L517 | L522 | L516 17.51/2.07 r_next=0.082 MAD_above=2.05 lag=-32(1.85/2.05); L517 17.63/1.66 r_next=0.070 MAD_above=1.95 lag=-5(1.85/1.95); L518 17.88/1.70 r_next=0.022 MAD_above=1.77 lag=23(1.60/1.77); L519 18.29/1.70 r_next=0.268 MAD_above=1.89 lag=9(1.69/1.89); L520 18.18/1.76 r_next=0.113 MAD_above=1.75 lag=-1(1.73/1.75); L521 18.14/1.96 r_next=0.153 MAD_above=2.06 lag=21(1.87/2.06); L522 17.45/2.20 r_next=0.766 MAD_above=2.23 lag=28(1.89/2.23); L523 17.60/2.49 r_next=0.781 MAD_above=1.71 lag=2(1.70/1.71); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.241; no internal horizontal blanking run; gate=4.000) |
| 6320 | 6320/F2 | L505 | L525 | L504 16.64/2.01 r_next=0.200 MAD_above=1.92 lag=26(1.78/1.92); L505 16.24/1.61 r_next=0.089 MAD_above=1.73 lag=15(1.71/1.73); L506 16.15/1.68 r_next=0.203 MAD_above=1.75 lag=26(1.54/1.75); L510 15.82/1.86 r_next=0.201 MAD_above=1.91 lag=27(1.70/1.91); L511 16.17/1.80 r_next=0.108 MAD_above=1.81 lag=27(1.68/1.81); L512 16.43/1.62 r_next=0.180 MAD_above=1.78 lag=24(1.65/1.78); L513 16.23/1.85 r_next=0.215 MAD_above=1.71 lag=29(1.58/1.71); L514 16.13/1.70 r_next=0.182 MAD_above=1.75 lag=7(1.66/1.75); L515 16.50/1.95 r_next=0.198 MAD_above=1.81 lag=22(1.60/1.81); L516 16.64/1.86 r_next=0.315 MAD_above=1.83 lag=5(1.81/1.83); L517 16.48/1.70 r_next=0.151 MAD_above=1.69 lag=4(1.64/1.69); L518 16.67/1.99 r_next=0.199 MAD_above=1.92 lag=-18(1.72/1.92); L519 16.75/1.81 r_next=0.170 MAD_above=1.86 lag=-6(1.63/1.86); L520 16.86/1.90 r_next=0.264 MAD_above=1.84 lag=30(1.54/1.84); L521 16.98/1.85 r_next=0.214 MAD_above=1.65 lag=26(1.60/1.65); L522 16.72/2.00 r_next=0.137 MAD_above=1.88 lag=9(1.71/1.88); L523 16.43/1.75 r_next=0.195 MAD_above=1.96 lag=13(1.80/1.96); L524 16.45/1.88 r_next=0.137 MAD_above=1.82 lag=28(1.79/1.82); L525 16.88/1.98 r_next=-0.013 MAD_above=1.89 lag=32(1.71/1.89); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.237; no internal horizontal blanking run; gate=4.000) |
| 6321 | 6321/F2 | L519 | L523 | L518 1.43/0.57 r_next=-0.012 MAD_above=0.76 lag=-32(0.68/0.76); L519 1.51/0.78 r_next=0.027 MAD_above=0.58 lag=17(0.49/0.58); L520 1.59/0.83 r_next=-0.037 MAD_above=0.67 lag=-15(0.64/0.67); L521 1.66/0.86 r_next=0.035 MAD_above=0.78 lag=23(0.66/0.78); L522 1.74/0.89 r_next=0.220 MAD_above=0.81 lag=-22(0.75/0.81); L523 1.80/1.09 r_next=-0.021 MAD_above=0.85 lag=22(0.83/0.85); L524 1.76/0.89 r_next=0.066 MAD_above=0.97 lag=-13(0.81/0.97); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.004; no internal horizontal blanking run; gate=4.000) |
| 6364 | 6364/F2 | L524 | L521 | L520 1.39/0.49 r_next=-0.016 MAD_above=0.47 lag=-16(0.44/0.47); L521 1.39/0.49 r_next=0.012 MAD_above=0.48 lag=6(0.43/0.48); L522 3.13/1.66 r_next=0.100 MAD_above=1.83 lag=-4(1.82/1.83); L523 3.75/0.80 r_next=-0.045 MAD_above=1.18 lag=-4(1.15/1.18); L524 4.98/0.78 r_next=-0.053 MAD_above=1.39 lag=-12(1.32/1.39); L525 5.51/0.69 r_next=0.018 MAD_above=0.92 lag=-14(0.82/0.92); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.003; no internal horizontal blanking run; gate=4.000) |
| 6365 | 6365/F2 | L524 | L522 | L521 1.39/0.49 r_next=-0.006 MAD_above=0.47 lag=-5(0.41/0.47); L522 3.16/2.43 r_next=0.046 MAD_above=1.87 lag=-16(1.85/1.87); L523 3.76/0.78 r_next=0.048 MAD_above=1.23 lag=-15(1.20/1.23); L524 5.00/0.82 r_next=0.018 MAD_above=1.35 lag=28(1.34/1.35); L525 5.61/0.71 r_next=0.014 MAD_above=0.92 lag=-8(0.86/0.92); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.004; no internal horizontal blanking run; gate=4.000) |

First-full-other-head histogram (engine S minus reference): -1: 3, +0: 523, +1: 3, both-unmeasurable: 22, engine-unmeasurable: 3, reference-unmeasurable: 365

- +1: counters 6698, 6749, 6754.  Witnesses: counter 6698: engine L524, direct L523; L523 internal blank x=92-155 Y=1.609; above=27.438 following=22.000; gate=4.000 / counter 6749: engine L524, direct L523; L523 internal blank x=104-167 Y=2.109; above=26.531 following=22.000; gate=4.000 / counter 6754: engine L524, direct L523; L523 internal blank x=107-170 Y=2.062; above=26.469 following=22.000; gate=4.000

- -1: counters 6880, 6931, 6933.  Witnesses: counter 6880: engine L522, direct L523; L523 persistent three-third step; thirds=10.661,2.593,2.799; correlation above/next=0.348/0.925; middle coherence=0.880 / counter 6931: engine L522, direct L523; L523 persistent three-third step; thirds=56.597,10.035,18.536; correlation above/next=-0.259/0.919; middle coherence=0.997 / counter 6933: engine L522, direct L523; L523 persistent three-third step; thirds=56.883,22.439,19.534; correlation above/next=-0.279/0.986; middle coherence=0.997

- engine-unmeasurable: counters 6674, 6776, 6863.  Witnesses: counter 6674: engine unmeasurable, direct L523; L523 internal blank x=64-127 Y=1.375; above=25.906 following=23.000; gate=4.000 / counter 6776: engine unmeasurable, direct L523; L523 internal blank x=58-121 Y=1.328; above=27.281 following=22.000; gate=4.000 / counter 6863: engine unmeasurable, direct L523; L523 internal blank x=63-126 Y=1.391; above=16.109 following=16.000; gate=4.000

- reference-unmeasurable: counters 6254, 6260-6267, 6269-6275, 6277-6278, 6286-6295, 6297-6313, 6315-6316, 6318, 6320-6321, 6324, 6326-6344, 6346-6366, 6368, 6370-6642.  Witnesses: counter 6254: engine L525, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.935; no internal horizontal blanking run; gate=4.000 / counter 6260: engine L525, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.925; no internal horizontal blanking run; gate=4.000 / counter 6261: engine L525, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.924; no internal horizontal blanking run; gate=4.000

Every numeric first-full disagreement:

| engine counter | raw counter/field | engine S | reference first-full | raw tail rows |
|---:|:---:|:---|:---|:---|
| 6698 | 6698/F2 | L524 | L523 | L522 22.99/3.06 r_next=-0.414 MAD_above=1.55 lag=-4(1.48/1.55); L523 19.74/10.84 r_next=0.474 MAD_above=7.83 lag=22(7.74/7.83); L524 17.83/9.69 r_next=0.985 MAD_above=3.55 lag=-6(3.25/3.55); L525 17.72/9.59 r_next=0.023 MAD_above=1.26 lag=-1(1.23/1.26); direct-full=L523 (L523 internal blank x=92-155 Y=1.609; above=27.438 following=22.000; gate=4.000) |
| 6749 | 6749/F2 | L524 | L523 | L522 22.55/3.29 r_next=-0.169 MAD_above=1.40 lag=1(1.40/1.40); L523 20.43/15.24 r_next=0.242 MAD_above=8.31 lag=19(8.23/8.31); L524 17.79/9.60 r_next=0.981 MAD_above=4.26 lag=-3(4.16/4.26); L525 17.78/9.54 r_next=-0.026 MAD_above=1.32 lag=-1(1.29/1.32); direct-full=L523 (L523 internal blank x=104-167 Y=2.109; above=26.531 following=22.000; gate=4.000) |
| 6754 | 6754/F2 | L524 | L523 | L522 22.62/3.07 r_next=-0.081 MAD_above=1.36 lag=-1(1.35/1.36); L523 21.55/18.95 r_next=0.110 MAD_above=8.37 lag=8(8.28/8.37); L524 17.15/9.18 r_next=0.980 MAD_above=5.24 lag=-1(5.23/5.24); L525 17.41/9.36 r_next=-0.029 MAD_above=1.47 lag=1(1.44/1.47); direct-full=L523 (L523 internal blank x=107-170 Y=2.062; above=26.469 following=22.000; gate=4.000) |
| 6880 | 6880/F2 | L522 | L523 | L521 26.10/2.81 r_next=0.185 MAD_above=1.87 lag=-5(1.71/1.87); L522 26.26/5.08 r_next=0.222 MAD_above=2.36 lag=-5(2.02/2.36); L523 19.83/10.45 r_next=0.916 MAD_above=7.95 lag=32(6.95/7.95); L524 17.53/9.34 r_next=0.866 MAD_above=2.95 lag=13(2.90/2.95); direct-full=L523 (L523 persistent three-third step; thirds=10.661,2.593,2.799; correlation above/next=0.348/0.925; middle coherence=0.880) |
| 6931 | 6931/F2 | L522 | L523 | L521 92.33/14.34 r_next=0.704 MAD_above=6.80 lag=0(6.80/6.80); L522 95.69/16.03 r_next=-0.201 MAD_above=8.28 lag=-3(7.25/8.28); L523 58.84/35.35 r_next=0.906 MAD_above=41.07 lag=32(39.40/41.07); L524 51.95/31.91 r_next=0.717 MAD_above=9.27 lag=-1(9.19/9.27); direct-full=L523 (L523 persistent three-third step; thirds=56.597,10.035,18.536; correlation above/next=-0.259/0.919; middle coherence=0.997) |
| 6933 | 6933/F2 | L522 | L523 | L521 89.36/15.11 r_next=0.642 MAD_above=9.10 lag=1(9.03/9.10); L522 89.40/19.34 r_next=-0.211 MAD_above=10.45 lag=-2(9.21/10.45); L523 85.84/50.89 r_next=0.979 MAD_above=48.47 lag=21(46.11/48.47); L524 81.27/48.19 r_next=0.798 MAD_above=8.07 lag=0(8.07/8.07); direct-full=L523 (L523 persistent three-third step; thirds=56.883,22.439,19.534; correlation above/next=-0.279/0.986; middle coherence=0.997) |

## Segment constants and applied crop

### Engine field 1

- H engine minus reference: +2: 915, both-unmeasurable: 4; mismatch counters: 6260-7174.
- c engine minus reference: -2: 915, both-unmeasurable: 4; mismatch counters: 6260-7174.
- crop engine minus reference: +0: 915, engine-unmeasurable: 4; mismatch counters: 6253-6254, 6257, 6259.

### Engine field 2

- H engine minus reference: +1: 916, both-unmeasurable: 2, engine-unmeasurable: 1; mismatch counters: 6253-6254, 6260-7174.
- c engine minus reference: -1: 916, both-unmeasurable: 2, engine-unmeasurable: 1; mismatch counters: 6253-6254, 6260-7174.
- crop engine minus reference: +0: 916, engine-unmeasurable: 3; mismatch counters: 6253, 6257, 6259.

## Comb consistency

Comparable measured pairs: 231; unavailable engine/top pair: 0; contradictions: 0.

## Commercial-tape stable interval (counter 6593 onward)

### Field 1

Engine top: L23: 582.

Reference top: L23: 582.

Engine signature top: L23: 582.

Reference signature top: L23: 579, L25: 3.

Reference observed top only: L23: 582.

First numeric engine top: counter 6593 L23; first observed reference top: counter 6593 L23.

Engine S: L259: 1, L260: 136, L261: 443, L262: 2.

Reference first-full-other-head row: L260: 67, L261: 464, unmeasurable: 51.

Engine S changes (57): 6600-6602, 6604-6608, 6613, 6615-6616, 6618, 6620-6625, 6627, 6629-6630, 6636-6639, 6645, 6687, 6714, 6737, 6886-6888, 6890-6892, 6899, 6906-6907, 6910, 6912, 6918-6920, 6929, 6932-6933, 6939-6940, 6942-6943, 6946, 6948, 6958-6960, 6963-6964. Reference first-full changes (4): 6645, 6688, 6714, 6738. Shared=6645, 6714, missing=6688, 6738, extra=6600-6602, 6604-6608, 6613, 6615-6616, 6618, 6620-6625, 6627, 6629-6630, 6636-6639, 6687, 6737, 6886-6888, 6890-6892, 6899, 6906-6907, 6910, 6912, 6918-6920, 6929, 6932-6933, 6939-6940, 6942-6943, 6946, 6948, 6958-6960, 6963-6964.

Engine-top unmeasurable counters: none.

Engine-S unmeasurable counters: none.

Reference-top unmeasurable counters: none.

Reference first-full unmeasurable counters: 6593-6643.

First-full raw-signature change witnesses:

| counter | engine S before/at | direct signature before/at | raw rows at change |
|---:|:---|:---|:---|
| 6645 | L261/L260 | L261/L260 | before: L259 15.79/1.12 r_next=0.135 MAD_above=1.14 lag=26(1.02/1.14); L260 15.12/5.09 r_next=-0.127 MAD_above=2.45 lag=7(2.37/2.45); L261 13.29/6.79 r_next=0.948 MAD_above=6.23 lag=32(5.76/6.23); L262 13.50/7.01 r_next=0.010 MAD_above=1.65 lag=6(1.53/1.65); at: L259 17.31/1.31 r_next=-0.090 MAD_above=1.53 lag=26(1.38/1.53); L260 14.21/8.29 r_next=0.643 MAD_above=5.19 lag=31(4.68/5.19); L261 13.15/6.87 r_next=0.968 MAD_above=2.41 lag=-14(1.73/2.41); L262 13.42/6.95 r_next=0.021 MAD_above=1.32 lag=0(1.32/1.32) |
| 6688 | L261/L261 | L260/L261 | before: L259 22.49/3.16 r_next=-0.329 MAD_above=1.83 lag=-7(1.75/1.83); L260 19.72/8.02 r_next=0.567 MAD_above=6.67 lag=-6(6.49/6.67); L261 17.32/9.56 r_next=0.963 MAD_above=4.15 lag=-7(4.10/4.15); L262 17.38/9.80 r_next=-0.007 MAD_above=1.87 lag=1(1.82/1.87); at: L259 22.93/3.21 r_next=-0.168 MAD_above=1.82 lag=-5(1.60/1.82); L260 21.83/6.74 r_next=0.306 MAD_above=5.15 lag=26(5.09/5.15); L261 17.63/9.63 r_next=0.970 MAD_above=5.53 lag=0(5.53/5.53); L262 16.86/9.32 r_next=0.025 MAD_above=1.84 lag=1(1.77/1.84) |
| 6714 | L261/L260 | L261/L260 | before: L259 22.84/2.93 r_next=0.292 MAD_above=1.28 lag=-2(1.27/1.28); L260 26.95/16.00 r_next=-0.201 MAD_above=5.83 lag=20(5.63/5.83); L261 17.47/9.14 r_next=0.979 MAD_above=10.23 lag=31(9.70/10.23); L262 17.46/9.15 r_next=0.030 MAD_above=1.33 lag=0(1.33/1.33); at: L259 22.88/3.16 r_next=-0.330 MAD_above=1.67 lag=4(1.63/1.67); L260 19.58/13.32 r_next=0.399 MAD_above=8.52 lag=32(7.62/8.52); L261 17.47/9.44 r_next=0.978 MAD_above=3.46 lag=-32(2.66/3.46); L262 17.09/9.27 r_next=0.034 MAD_above=1.45 lag=0(1.45/1.45) |
| 6738 | L261/L261 | L260/L261 | before: L259 22.14/3.25 r_next=-0.469 MAD_above=1.93 lag=-8(1.81/1.93); L260 19.74/8.81 r_next=0.643 MAD_above=7.35 lag=32(7.16/7.35); L261 18.32/9.65 r_next=0.965 MAD_above=3.42 lag=-16(3.29/3.42); L262 16.49/8.45 r_next=0.034 MAD_above=2.53 lag=1(2.52/2.53); at: L259 22.50/3.63 r_next=0.090 MAD_above=1.63 lag=3(1.56/1.63); L260 23.98/18.06 r_next=-0.123 MAD_above=7.12 lag=32(6.88/7.12); L261 18.08/9.43 r_next=0.976 MAD_above=7.57 lag=-1(7.56/7.57); L262 17.02/8.97 r_next=0.013 MAD_above=1.75 lag=1(1.75/1.75) |

### Field 2

Engine top: L286: 582.

Reference top: L286: 582.

Engine signature top: L286: 579, L287: 3.

Reference signature top: L286: 408, L287: 174.

Reference observed top only: L286: 442.

First numeric engine top: counter 6593 L286; first observed reference top: counter 6593 L286.

Engine S: L522: 5, L523: 545, L524: 19, L525: 10, unmeasurable: 3.

Reference first-full-other-head row: L523: 518, L524: 14, unmeasurable: 50.

Engine S changes (16): 6594, 6604-6605, 6607, 6644-6645, 6698, 6708, 6749, 6755, 6880-6881, 6931-6934. Reference first-full changes (6): 6644-6645, 6699, 6708, 6750, 6754. Shared=6644-6645, 6708, missing=6699, 6750, 6754, extra=6594, 6604-6605, 6607, 6698, 6749, 6755, 6880-6881, 6931-6934.

Engine-top unmeasurable counters: none.

Engine-S unmeasurable counters: 6674, 6776, 6863.

Reference-top unmeasurable counters: none.

Reference first-full unmeasurable counters: 6593-6642.

First-full raw-signature change witnesses:

| counter | engine S before/at | direct signature before/at | raw rows at change |
|---:|:---|:---|:---|
| 6644 | L523/L524 | L523/L524 | before: L522 16.55/1.41 r_next=-0.034 MAD_above=2.10 lag=32(1.85/2.10); L523 11.75/6.00 r_next=0.899 MAD_above=5.15 lag=0(5.15/5.15); L524 12.10/6.31 r_next=0.927 MAD_above=1.85 lag=-8(1.78/1.85); L525 11.70/6.11 r_next=-0.011 MAD_above=1.64 lag=-1(1.63/1.64); at: L522 16.58/1.08 r_next=0.130 MAD_above=1.22 lag=10(1.14/1.22); L523 16.21/3.18 r_next=-0.210 MAD_above=1.85 lag=-5(1.82/1.85); L524 13.45/6.91 r_next=0.967 MAD_above=5.65 lag=32(5.13/5.65); L525 13.61/7.07 r_next=-0.003 MAD_above=1.30 lag=2(1.24/1.30) |
| 6645 | L524/L523 | L524/L523 | before: L522 16.58/1.08 r_next=0.130 MAD_above=1.22 lag=10(1.14/1.22); L523 16.21/3.18 r_next=-0.210 MAD_above=1.85 lag=-5(1.82/1.85); L524 13.45/6.91 r_next=0.967 MAD_above=5.65 lag=32(5.13/5.65); L525 13.61/7.07 r_next=-0.003 MAD_above=1.30 lag=2(1.24/1.30); at: L522 17.05/1.20 r_next=-0.308 MAD_above=1.10 lag=1(1.08/1.10); L523 13.42/6.90 r_next=0.973 MAD_above=4.98 lag=30(4.44/4.98); L524 13.57/6.97 r_next=0.744 MAD_above=1.16 lag=-1(1.15/1.16); L525 14.33/5.98 r_next=0.008 MAD_above=2.23 lag=-32(1.52/2.23) |
| 6699 | L524/L524 | L523/L524 | before: L522 22.99/3.06 r_next=-0.414 MAD_above=1.55 lag=-4(1.48/1.55); L523 19.74/10.84 r_next=0.474 MAD_above=7.83 lag=22(7.74/7.83); L524 17.83/9.69 r_next=0.985 MAD_above=3.55 lag=-6(3.25/3.55); L525 17.72/9.59 r_next=0.023 MAD_above=1.26 lag=-1(1.23/1.26); at: L522 23.27/3.23 r_next=0.163 MAD_above=1.50 lag=-2(1.48/1.50); L523 25.98/19.19 r_next=-0.230 MAD_above=6.88 lag=32(6.78/6.88); L524 17.91/9.75 r_next=0.980 MAD_above=9.24 lag=1(9.22/9.24); L525 16.87/9.24 r_next=0.026 MAD_above=1.58 lag=3(1.53/1.58) |
| 6708 | L524/L523 | L524/L523 | before: L522 22.54/3.09 r_next=0.101 MAD_above=1.53 lag=-6(1.42/1.53); L523 24.47/12.43 r_next=-0.144 MAD_above=5.85 lag=32(5.60/5.85); L524 17.89/9.66 r_next=0.981 MAD_above=7.79 lag=-4(7.67/7.79); L525 17.10/9.26 r_next=0.007 MAD_above=1.50 lag=-1(1.48/1.50); at: L522 22.64/3.20 r_next=-0.277 MAD_above=1.30 lag=0(1.30/1.30); L523 18.83/9.76 r_next=0.231 MAD_above=8.47 lag=32(7.56/8.47); L524 17.98/9.59 r_next=0.975 MAD_above=2.37 lag=-15(1.88/2.37); L525 17.88/9.53 r_next=0.038 MAD_above=1.58 lag=-2(1.52/1.58) |
| 6750 | L524/L524 | L523/L524 | before: L522 22.55/3.29 r_next=-0.169 MAD_above=1.40 lag=1(1.40/1.40); L523 20.43/15.24 r_next=0.242 MAD_above=8.31 lag=19(8.23/8.31); L524 17.79/9.60 r_next=0.981 MAD_above=4.26 lag=-3(4.16/4.26); L525 17.78/9.54 r_next=-0.026 MAD_above=1.32 lag=-1(1.29/1.32); at: L522 22.68/3.22 r_next=-0.052 MAD_above=1.52 lag=-7(1.48/1.52); L523 22.91/9.34 r_next=0.067 MAD_above=6.00 lag=28(5.82/6.00); L524 17.93/9.75 r_next=0.981 MAD_above=6.22 lag=-1(6.16/6.22); L525 17.68/9.63 r_next=-0.013 MAD_above=1.38 lag=3(1.36/1.38) |
| 6754 | L524/L524 | L524/L523 | before: L522 23.60/3.40 r_next=0.002 MAD_above=1.67 lag=9(1.64/1.67); L523 23.75/6.05 r_next=-0.212 MAD_above=4.48 lag=5(4.45/4.48); L524 18.05/9.95 r_next=0.980 MAD_above=8.56 lag=-29(7.21/8.56); L525 18.48/10.24 r_next=0.013 MAD_above=1.53 lag=-1(1.45/1.53); at: L522 22.62/3.07 r_next=-0.081 MAD_above=1.36 lag=-1(1.35/1.36); L523 21.55/18.95 r_next=0.110 MAD_above=8.37 lag=8(8.28/8.37); L524 17.15/9.18 r_next=0.980 MAD_above=5.24 lag=-1(5.23/5.24); L525 17.41/9.36 r_next=-0.029 MAD_above=1.47 lag=1(1.44/1.47) |

### Field-2 dark-first-row audit

Across 582 stable units, line 286 and line 287 row means correlate at 0.998610 over samples 24-696. Line 286 is below luma 8 in 191 units; the longest consecutive run is counters 6645-6820 (176 units).

The reference signature test nominated line 287 in 174 units, but the account retained line 286 in all of them because the bottom geometry did not move. Verdict: line 286 is the dark first picture row; the provisional grey-line classification does not move the crop.

Deciding rows:

- counter 6645: L286 3.37/1.52 r_next=0.066 MAD_above=2.04 lag=-23(2.00/2.04); L287 21.92/1.22 r_next=-0.016 MAD_above=18.54 lag=-3(18.54/18.54); L288 21.25/1.11 r_next=0.062 MAD_above=1.41 lag=-15(1.24/1.41); L289 20.67/1.31 r_next=0.155 MAD_above=1.36 lag=31(1.25/1.36)

- counter 6672: L286 2.84/1.80 r_next=-0.149 MAD_above=1.65 lag=19(1.58/1.65); L287 16.43/3.53 r_next=0.112 MAD_above=13.59 lag=-31(13.55/13.59); L288 15.68/2.88 r_next=0.169 MAD_above=3.40 lag=-25(3.09/3.40); L289 17.20/2.73 r_next=-0.053 MAD_above=3.15 lag=-31(3.03/3.15)

- counter 6742: L286 1.78/0.80 r_next=0.004 MAD_above=0.73 lag=29(0.65/0.73); L287 9.44/1.24 r_next=0.137 MAD_above=7.66 lag=4(7.66/7.66); L288 9.16/1.38 r_next=0.149 MAD_above=1.44 lag=7(1.30/1.44); L289 9.38/1.63 r_next=-0.082 MAD_above=1.60 lag=23(1.42/1.60)

# Engine-record score: EP recording

Acceptance verdict: **not accepted**.

Engine rows joined by device counter: 1242; unmatched engine rows: none.

Engine fields are compared with the same numbered raw raster slot at the same counter.

Owner-review disagreement units: 621; counters: 1910-2530.

Shifted woven bwdif frames written: 621 under `reports/engine_run_R_disagreements/ep`.

| counter | reason(s) | shifted bwdif frame |
|---:|:---|:---|
| 1910 | F1 H 236/235; F1 c 4/5; F1 crop L26/L23; F2 crop L288/L286 | `reports/engine_run_R_disagreements/ep/counter_01910.webp` |
| 1911 | F1 H 236/235; F1 c 4/5; F1 crop L26/L23; F2 crop L288/L286 | `reports/engine_run_R_disagreements/ep/counter_01911.webp` |
| 1912 | F1 H 236/235; F1 c 4/5; F1 crop L26/L23; F2 crop L288/L286 | `reports/engine_run_R_disagreements/ep/counter_01912.webp` |
| 1913 | F1 H 236/235; F1 c 4/5; F1 crop L26/L23; F2 crop L288/L286 | `reports/engine_run_R_disagreements/ep/counter_01913.webp` |
| 1914 | F1 H 236/235; F1 c 4/5; F1 crop L25/L23; F2 crop L288/L286 | `reports/engine_run_R_disagreements/ep/counter_01914.webp` |
| 1915 | F1 H 236/235; F1 c 4/5; F1 crop L26/L23; F2 crop L288/L286 | `reports/engine_run_R_disagreements/ep/counter_01915.webp` |
| 1916 | F1 H 236/235; F1 c 4/5; F1 crop L25/L23; F2 crop L288/L286 | `reports/engine_run_R_disagreements/ep/counter_01916.webp` |
| 1917 | F1 H 236/235; F1 c 4/5; F1 crop L25/L23 | `reports/engine_run_R_disagreements/ep/counter_01917.webp` |
| 1918 | F1 H 236/235; F1 c 4/5; F1 crop L25/L23 | `reports/engine_run_R_disagreements/ep/counter_01918.webp` |
| 1919 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01919.webp` |
| 1920 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01920.webp` |
| 1921 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01921.webp` |
| 1922 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01922.webp` |
| 1923 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01923.webp` |
| 1924 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01924.webp` |
| 1925 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01925.webp` |
| 1926 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01926.webp` |
| 1927 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01927.webp` |
| 1928 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01928.webp` |
| 1929 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_01929.webp` |
| 1930 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01930.webp` |
| 1931 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01931.webp` |
| 1932 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01932.webp` |
| 1933 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01933.webp` |
| 1934 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01934.webp` |
| 1935 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01935.webp` |
| 1936 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01936.webp` |
| 1937 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01937.webp` |
| 1938 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01938.webp` |
| 1939 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01939.webp` |
| 1940 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01940.webp` |
| 1941 | F1 H 236/235; F1 S/switch L261/L259; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01941.webp` |
| 1942 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01942.webp` |
| 1943 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01943.webp` |
| 1944 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01944.webp` |
| 1945 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01945.webp` |
| 1946 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01946.webp` |
| 1947 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01947.webp` |
| 1948 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01948.webp` |
| 1949 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01949.webp` |
| 1950 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_01950.webp` |
| 1951 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01951.webp` |
| 1952 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01952.webp` |
| 1953 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01953.webp` |
| 1954 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01954.webp` |
| 1955 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01955.webp` |
| 1956 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01956.webp` |
| 1957 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01957.webp` |
| 1958 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01958.webp` |
| 1959 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01959.webp` |
| 1960 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01960.webp` |
| 1961 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01961.webp` |
| 1962 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01962.webp` |
| 1963 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01963.webp` |
| 1964 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01964.webp` |
| 1965 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01965.webp` |
| 1966 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01966.webp` |
| 1967 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01967.webp` |
| 1968 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01968.webp` |
| 1969 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01969.webp` |
| 1970 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01970.webp` |
| 1971 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01971.webp` |
| 1972 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01972.webp` |
| 1973 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01973.webp` |
| 1974 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01974.webp` |
| 1975 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01975.webp` |
| 1976 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01976.webp` |
| 1977 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01977.webp` |
| 1978 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01978.webp` |
| 1979 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01979.webp` |
| 1980 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01980.webp` |
| 1981 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01981.webp` |
| 1982 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01982.webp` |
| 1983 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01983.webp` |
| 1984 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26; engine decisive comb -1 at placed crops (ratio 0.220) | `reports/engine_run_R_disagreements/ep/counter_01984.webp` |
| 1985 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26; engine decisive comb -1 at placed crops (ratio 0.170) | `reports/engine_run_R_disagreements/ep/counter_01985.webp` |
| 1986 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01986.webp` |
| 1987 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_01987.webp` |
| 1988 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01988.webp` |
| 1989 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01989.webp` |
| 1990 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01990.webp` |
| 1991 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01991.webp` |
| 1992 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01992.webp` |
| 1993 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01993.webp` |
| 1994 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01994.webp` |
| 1995 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01995.webp` |
| 1996 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01996.webp` |
| 1997 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01997.webp` |
| 1998 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_01998.webp` |
| 1999 | F1 H 236/235; F1 c 4/5; F1 crop L26/L25; engine decisive comb +1 at placed crops (ratio 0.380) | `reports/engine_run_R_disagreements/ep/counter_01999.webp` |
| 2000 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02000.webp` |
| 2001 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02001.webp` |
| 2002 | F1 H 236/235; F1 c 4/5; F1 crop L26/L25; engine decisive comb +1 at placed crops (ratio 0.410) | `reports/engine_run_R_disagreements/ep/counter_02002.webp` |
| 2003 | F1 H 236/235; F1 c 4/5; F1 crop L26/L25; engine decisive comb +1 at placed crops (ratio 0.260) | `reports/engine_run_R_disagreements/ep/counter_02003.webp` |
| 2004 | F1 H 236/235; F1 c 4/5; F1 crop L26/L25; engine decisive comb +1 at placed crops (ratio 0.230) | `reports/engine_run_R_disagreements/ep/counter_02004.webp` |
| 2005 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02005.webp` |
| 2006 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02006.webp` |
| 2007 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02007.webp` |
| 2008 | F1 H 236/235; F1 c 4/5; F1 crop L26/L25; engine decisive comb +1 at placed crops (ratio 0.650) | `reports/engine_run_R_disagreements/ep/counter_02008.webp` |
| 2009 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02009.webp` |
| 2010 | F1 H 236/235; F1 c 4/5; F1 crop L26/L25; engine decisive comb +1 at placed crops (ratio 0.550) | `reports/engine_run_R_disagreements/ep/counter_02010.webp` |
| 2011 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02011.webp` |
| 2012 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02012.webp` |
| 2013 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02013.webp` |
| 2014 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02014.webp` |
| 2015 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02015.webp` |
| 2016 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02016.webp` |
| 2017 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02017.webp` |
| 2018 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02018.webp` |
| 2019 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02019.webp` |
| 2020 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02020.webp` |
| 2021 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26; engine decisive comb -1 at placed crops (ratio 0.240) | `reports/engine_run_R_disagreements/ep/counter_02021.webp` |
| 2022 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02022.webp` |
| 2023 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02023.webp` |
| 2024 | F1 H 236/235; F1 c 4/5; F1 crop L26/L25; engine decisive comb +1 at placed crops (ratio 0.390) | `reports/engine_run_R_disagreements/ep/counter_02024.webp` |
| 2025 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02025.webp` |
| 2026 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02026.webp` |
| 2027 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26; F2 crop L286/L288; F2 signature top L286/L288 | `reports/engine_run_R_disagreements/ep/counter_02027.webp` |
| 2028 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02028.webp` |
| 2029 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02029.webp` |
| 2030 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02030.webp` |
| 2031 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02031.webp` |
| 2032 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02032.webp` |
| 2033 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523; F2 crop L286/L288; F2 signature top L286/L288; engine decisive comb +2 at placed crops (ratio 0.240) | `reports/engine_run_R_disagreements/ep/counter_02033.webp` |
| 2034 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02034.webp` |
| 2035 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02035.webp` |
| 2036 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02036.webp` |
| 2037 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02037.webp` |
| 2038 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02038.webp` |
| 2039 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02039.webp` |
| 2040 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02040.webp` |
| 2041 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02041.webp` |
| 2042 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02042.webp` |
| 2043 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02043.webp` |
| 2044 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02044.webp` |
| 2045 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02045.webp` |
| 2046 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02046.webp` |
| 2047 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02047.webp` |
| 2048 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02048.webp` |
| 2049 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02049.webp` |
| 2050 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02050.webp` |
| 2051 | F1 H 236/235; F1 S/switch L259/L261; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02051.webp` |
| 2052 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02052.webp` |
| 2053 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02053.webp` |
| 2054 | F1 H 236/235; F1 c 4/5; F2 S/switch L521/L523 | `reports/engine_run_R_disagreements/ep/counter_02054.webp` |
| 2055 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02055.webp` |
| 2056 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02056.webp` |
| 2057 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02057.webp` |
| 2058 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02058.webp` |
| 2059 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02059.webp` |
| 2060 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02060.webp` |
| 2061 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02061.webp` |
| 2062 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02062.webp` |
| 2063 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02063.webp` |
| 2064 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02064.webp` |
| 2065 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02065.webp` |
| 2066 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02066.webp` |
| 2067 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02067.webp` |
| 2068 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02068.webp` |
| 2069 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02069.webp` |
| 2070 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02070.webp` |
| 2071 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02071.webp` |
| 2072 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02072.webp` |
| 2073 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02073.webp` |
| 2074 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02074.webp` |
| 2075 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02075.webp` |
| 2076 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02076.webp` |
| 2077 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02077.webp` |
| 2078 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02078.webp` |
| 2079 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02079.webp` |
| 2080 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02080.webp` |
| 2081 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02081.webp` |
| 2082 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02082.webp` |
| 2083 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26; engine decisive comb -1 at placed crops (ratio 0.380) | `reports/engine_run_R_disagreements/ep/counter_02083.webp` |
| 2084 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02084.webp` |
| 2085 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02085.webp` |
| 2086 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02086.webp` |
| 2087 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02087.webp` |
| 2088 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02088.webp` |
| 2089 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02089.webp` |
| 2090 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02090.webp` |
| 2091 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02091.webp` |
| 2092 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02092.webp` |
| 2093 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02093.webp` |
| 2094 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02094.webp` |
| 2095 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02095.webp` |
| 2096 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02096.webp` |
| 2097 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02097.webp` |
| 2098 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02098.webp` |
| 2099 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02099.webp` |
| 2100 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02100.webp` |
| 2101 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02101.webp` |
| 2102 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02102.webp` |
| 2103 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02103.webp` |
| 2104 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02104.webp` |
| 2105 | F1 H 236/235; F1 c 4/5; F2 S/switch L521/L523 | `reports/engine_run_R_disagreements/ep/counter_02105.webp` |
| 2106 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02106.webp` |
| 2107 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02107.webp` |
| 2108 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02108.webp` |
| 2109 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02109.webp` |
| 2110 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02110.webp` |
| 2111 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02111.webp` |
| 2112 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02112.webp` |
| 2113 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02113.webp` |
| 2114 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02114.webp` |
| 2115 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02115.webp` |
| 2116 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02116.webp` |
| 2117 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02117.webp` |
| 2118 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02118.webp` |
| 2119 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02119.webp` |
| 2120 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02120.webp` |
| 2121 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02121.webp` |
| 2122 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02122.webp` |
| 2123 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02123.webp` |
| 2124 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02124.webp` |
| 2125 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02125.webp` |
| 2126 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02126.webp` |
| 2127 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02127.webp` |
| 2128 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02128.webp` |
| 2129 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02129.webp` |
| 2130 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02130.webp` |
| 2131 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02131.webp` |
| 2132 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02132.webp` |
| 2133 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02133.webp` |
| 2134 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02134.webp` |
| 2135 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02135.webp` |
| 2136 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02136.webp` |
| 2137 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02137.webp` |
| 2138 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02138.webp` |
| 2139 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02139.webp` |
| 2140 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02140.webp` |
| 2141 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02141.webp` |
| 2142 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02142.webp` |
| 2143 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02143.webp` |
| 2144 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02144.webp` |
| 2145 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02145.webp` |
| 2146 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02146.webp` |
| 2147 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02147.webp` |
| 2148 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02148.webp` |
| 2149 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02149.webp` |
| 2150 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02150.webp` |
| 2151 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02151.webp` |
| 2152 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02152.webp` |
| 2153 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02153.webp` |
| 2154 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02154.webp` |
| 2155 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02155.webp` |
| 2156 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02156.webp` |
| 2157 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02157.webp` |
| 2158 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02158.webp` |
| 2159 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02159.webp` |
| 2160 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02160.webp` |
| 2161 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02161.webp` |
| 2162 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02162.webp` |
| 2163 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02163.webp` |
| 2164 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02164.webp` |
| 2165 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02165.webp` |
| 2166 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02166.webp` |
| 2167 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02167.webp` |
| 2168 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02168.webp` |
| 2169 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02169.webp` |
| 2170 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02170.webp` |
| 2171 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02171.webp` |
| 2172 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02172.webp` |
| 2173 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02173.webp` |
| 2174 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02174.webp` |
| 2175 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02175.webp` |
| 2176 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02176.webp` |
| 2177 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02177.webp` |
| 2178 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02178.webp` |
| 2179 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02179.webp` |
| 2180 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02180.webp` |
| 2181 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02181.webp` |
| 2182 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02182.webp` |
| 2183 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02183.webp` |
| 2184 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02184.webp` |
| 2185 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02185.webp` |
| 2186 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02186.webp` |
| 2187 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02187.webp` |
| 2188 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02188.webp` |
| 2189 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02189.webp` |
| 2190 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02190.webp` |
| 2191 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02191.webp` |
| 2192 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02192.webp` |
| 2193 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02193.webp` |
| 2194 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02194.webp` |
| 2195 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02195.webp` |
| 2196 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02196.webp` |
| 2197 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02197.webp` |
| 2198 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02198.webp` |
| 2199 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02199.webp` |
| 2200 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02200.webp` |
| 2201 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02201.webp` |
| 2202 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02202.webp` |
| 2203 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02203.webp` |
| 2204 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02204.webp` |
| 2205 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02205.webp` |
| 2206 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02206.webp` |
| 2207 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02207.webp` |
| 2208 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02208.webp` |
| 2209 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02209.webp` |
| 2210 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02210.webp` |
| 2211 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02211.webp` |
| 2212 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02212.webp` |
| 2213 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02213.webp` |
| 2214 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02214.webp` |
| 2215 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02215.webp` |
| 2216 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02216.webp` |
| 2217 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02217.webp` |
| 2218 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02218.webp` |
| 2219 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02219.webp` |
| 2220 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02220.webp` |
| 2221 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02221.webp` |
| 2222 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02222.webp` |
| 2223 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02223.webp` |
| 2224 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02224.webp` |
| 2225 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02225.webp` |
| 2226 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02226.webp` |
| 2227 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02227.webp` |
| 2228 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02228.webp` |
| 2229 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02229.webp` |
| 2230 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02230.webp` |
| 2231 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02231.webp` |
| 2232 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02232.webp` |
| 2233 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02233.webp` |
| 2234 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02234.webp` |
| 2235 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02235.webp` |
| 2236 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02236.webp` |
| 2237 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02237.webp` |
| 2238 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02238.webp` |
| 2239 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02239.webp` |
| 2240 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02240.webp` |
| 2241 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02241.webp` |
| 2242 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02242.webp` |
| 2243 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02243.webp` |
| 2244 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02244.webp` |
| 2245 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02245.webp` |
| 2246 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02246.webp` |
| 2247 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02247.webp` |
| 2248 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02248.webp` |
| 2249 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02249.webp` |
| 2250 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02250.webp` |
| 2251 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02251.webp` |
| 2252 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02252.webp` |
| 2253 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02253.webp` |
| 2254 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02254.webp` |
| 2255 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02255.webp` |
| 2256 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02256.webp` |
| 2257 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02257.webp` |
| 2258 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02258.webp` |
| 2259 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02259.webp` |
| 2260 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02260.webp` |
| 2261 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02261.webp` |
| 2262 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02262.webp` |
| 2263 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02263.webp` |
| 2264 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02264.webp` |
| 2265 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02265.webp` |
| 2266 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02266.webp` |
| 2267 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02267.webp` |
| 2268 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02268.webp` |
| 2269 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02269.webp` |
| 2270 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02270.webp` |
| 2271 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02271.webp` |
| 2272 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02272.webp` |
| 2273 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02273.webp` |
| 2274 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02274.webp` |
| 2275 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02275.webp` |
| 2276 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02276.webp` |
| 2277 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02277.webp` |
| 2278 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02278.webp` |
| 2279 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02279.webp` |
| 2280 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02280.webp` |
| 2281 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02281.webp` |
| 2282 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02282.webp` |
| 2283 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02283.webp` |
| 2284 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02284.webp` |
| 2285 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02285.webp` |
| 2286 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02286.webp` |
| 2287 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02287.webp` |
| 2288 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02288.webp` |
| 2289 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02289.webp` |
| 2290 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02290.webp` |
| 2291 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02291.webp` |
| 2292 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02292.webp` |
| 2293 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02293.webp` |
| 2294 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02294.webp` |
| 2295 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02295.webp` |
| 2296 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02296.webp` |
| 2297 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02297.webp` |
| 2298 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02298.webp` |
| 2299 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02299.webp` |
| 2300 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02300.webp` |
| 2301 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02301.webp` |
| 2302 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02302.webp` |
| 2303 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02303.webp` |
| 2304 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02304.webp` |
| 2305 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02305.webp` |
| 2306 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02306.webp` |
| 2307 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02307.webp` |
| 2308 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02308.webp` |
| 2309 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02309.webp` |
| 2310 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02310.webp` |
| 2311 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02311.webp` |
| 2312 | F1 H 236/235; F1 c 4/5; engine decisive comb +3 at placed crops (ratio 0.480) | `reports/engine_run_R_disagreements/ep/counter_02312.webp` |
| 2313 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02313.webp` |
| 2314 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02314.webp` |
| 2315 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02315.webp` |
| 2316 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02316.webp` |
| 2317 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02317.webp` |
| 2318 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02318.webp` |
| 2319 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02319.webp` |
| 2320 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02320.webp` |
| 2321 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02321.webp` |
| 2322 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02322.webp` |
| 2323 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02323.webp` |
| 2324 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02324.webp` |
| 2325 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02325.webp` |
| 2326 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02326.webp` |
| 2327 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02327.webp` |
| 2328 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02328.webp` |
| 2329 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02329.webp` |
| 2330 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02330.webp` |
| 2331 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02331.webp` |
| 2332 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02332.webp` |
| 2333 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02333.webp` |
| 2334 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02334.webp` |
| 2335 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02335.webp` |
| 2336 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02336.webp` |
| 2337 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02337.webp` |
| 2338 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02338.webp` |
| 2339 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02339.webp` |
| 2340 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02340.webp` |
| 2341 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02341.webp` |
| 2342 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02342.webp` |
| 2343 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02343.webp` |
| 2344 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02344.webp` |
| 2345 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02345.webp` |
| 2346 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02346.webp` |
| 2347 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02347.webp` |
| 2348 | F1 H 236/235; F1 S/switch L262/L259; F1 c 4/5; F1 crop L26/L25; reference comb/placed-crop disagreement | `reports/engine_run_R_disagreements/ep/counter_02348.webp` |
| 2349 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02349.webp` |
| 2350 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02350.webp` |
| 2351 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02351.webp` |
| 2352 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02352.webp` |
| 2353 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02353.webp` |
| 2354 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02354.webp` |
| 2355 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02355.webp` |
| 2356 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02356.webp` |
| 2357 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02357.webp` |
| 2358 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02358.webp` |
| 2359 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02359.webp` |
| 2360 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02360.webp` |
| 2361 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02361.webp` |
| 2362 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02362.webp` |
| 2363 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02363.webp` |
| 2364 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02364.webp` |
| 2365 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02365.webp` |
| 2366 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02366.webp` |
| 2367 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02367.webp` |
| 2368 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02368.webp` |
| 2369 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02369.webp` |
| 2370 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02370.webp` |
| 2371 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02371.webp` |
| 2372 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02372.webp` |
| 2373 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02373.webp` |
| 2374 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02374.webp` |
| 2375 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02375.webp` |
| 2376 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02376.webp` |
| 2377 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02377.webp` |
| 2378 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02378.webp` |
| 2379 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02379.webp` |
| 2380 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02380.webp` |
| 2381 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02381.webp` |
| 2382 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02382.webp` |
| 2383 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02383.webp` |
| 2384 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02384.webp` |
| 2385 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02385.webp` |
| 2386 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02386.webp` |
| 2387 | F1 H 236/235; F1 c 4/5; engine decisive comb -1 at placed crops (ratio 0.530) | `reports/engine_run_R_disagreements/ep/counter_02387.webp` |
| 2388 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02388.webp` |
| 2389 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02389.webp` |
| 2390 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02390.webp` |
| 2391 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02391.webp` |
| 2392 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02392.webp` |
| 2393 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02393.webp` |
| 2394 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02394.webp` |
| 2395 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02395.webp` |
| 2396 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02396.webp` |
| 2397 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02397.webp` |
| 2398 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02398.webp` |
| 2399 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02399.webp` |
| 2400 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02400.webp` |
| 2401 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02401.webp` |
| 2402 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02402.webp` |
| 2403 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02403.webp` |
| 2404 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02404.webp` |
| 2405 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02405.webp` |
| 2406 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02406.webp` |
| 2407 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02407.webp` |
| 2408 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02408.webp` |
| 2409 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02409.webp` |
| 2410 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02410.webp` |
| 2411 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02411.webp` |
| 2412 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02412.webp` |
| 2413 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02413.webp` |
| 2414 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02414.webp` |
| 2415 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02415.webp` |
| 2416 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02416.webp` |
| 2417 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02417.webp` |
| 2418 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02418.webp` |
| 2419 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02419.webp` |
| 2420 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02420.webp` |
| 2421 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02421.webp` |
| 2422 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02422.webp` |
| 2423 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02423.webp` |
| 2424 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02424.webp` |
| 2425 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02425.webp` |
| 2426 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02426.webp` |
| 2427 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02427.webp` |
| 2428 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02428.webp` |
| 2429 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02429.webp` |
| 2430 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02430.webp` |
| 2431 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02431.webp` |
| 2432 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02432.webp` |
| 2433 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02433.webp` |
| 2434 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02434.webp` |
| 2435 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02435.webp` |
| 2436 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02436.webp` |
| 2437 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02437.webp` |
| 2438 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02438.webp` |
| 2439 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02439.webp` |
| 2440 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02440.webp` |
| 2441 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02441.webp` |
| 2442 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02442.webp` |
| 2443 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02443.webp` |
| 2444 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02444.webp` |
| 2445 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02445.webp` |
| 2446 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02446.webp` |
| 2447 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02447.webp` |
| 2448 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02448.webp` |
| 2449 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02449.webp` |
| 2450 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02450.webp` |
| 2451 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02451.webp` |
| 2452 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02452.webp` |
| 2453 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02453.webp` |
| 2454 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02454.webp` |
| 2455 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02455.webp` |
| 2456 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02456.webp` |
| 2457 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02457.webp` |
| 2458 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02458.webp` |
| 2459 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02459.webp` |
| 2460 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02460.webp` |
| 2461 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02461.webp` |
| 2462 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02462.webp` |
| 2463 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02463.webp` |
| 2464 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02464.webp` |
| 2465 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02465.webp` |
| 2466 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02466.webp` |
| 2467 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02467.webp` |
| 2468 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02468.webp` |
| 2469 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02469.webp` |
| 2470 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02470.webp` |
| 2471 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02471.webp` |
| 2472 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02472.webp` |
| 2473 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02473.webp` |
| 2474 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02474.webp` |
| 2475 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02475.webp` |
| 2476 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02476.webp` |
| 2477 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02477.webp` |
| 2478 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02478.webp` |
| 2479 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02479.webp` |
| 2480 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02480.webp` |
| 2481 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02481.webp` |
| 2482 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02482.webp` |
| 2483 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02483.webp` |
| 2484 | F1 H 236/235; F1 c 4/5; F2 S/switch L521/L523 | `reports/engine_run_R_disagreements/ep/counter_02484.webp` |
| 2485 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02485.webp` |
| 2486 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26; engine decisive comb -1 at placed crops (ratio 0.660) | `reports/engine_run_R_disagreements/ep/counter_02486.webp` |
| 2487 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02487.webp` |
| 2488 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02488.webp` |
| 2489 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02489.webp` |
| 2490 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02490.webp` |
| 2491 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02491.webp` |
| 2492 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02492.webp` |
| 2493 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02493.webp` |
| 2494 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02494.webp` |
| 2495 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02495.webp` |
| 2496 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26; engine decisive comb -1 at placed crops (ratio 0.540) | `reports/engine_run_R_disagreements/ep/counter_02496.webp` |
| 2497 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02497.webp` |
| 2498 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02498.webp` |
| 2499 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02499.webp` |
| 2500 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02500.webp` |
| 2501 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02501.webp` |
| 2502 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02502.webp` |
| 2503 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02503.webp` |
| 2504 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02504.webp` |
| 2505 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02505.webp` |
| 2506 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02506.webp` |
| 2507 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02507.webp` |
| 2508 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02508.webp` |
| 2509 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02509.webp` |
| 2510 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02510.webp` |
| 2511 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02511.webp` |
| 2512 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02512.webp` |
| 2513 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02513.webp` |
| 2514 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02514.webp` |
| 2515 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02515.webp` |
| 2516 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02516.webp` |
| 2517 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02517.webp` |
| 2518 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02518.webp` |
| 2519 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02519.webp` |
| 2520 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02520.webp` |
| 2521 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02521.webp` |
| 2522 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02522.webp` |
| 2523 | F1 H 236/235; F1 c 4/5; F2 crop L286/L288; F2 signature top L286/L288; engine decisive comb +2 at placed crops (ratio 0.470) | `reports/engine_run_R_disagreements/ep/counter_02523.webp` |
| 2524 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02524.webp` |
| 2525 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02525.webp` |
| 2526 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02526.webp` |
| 2527 | F1 H 236/235; F1 c 4/5; F1 crop L25/L26 | `reports/engine_run_R_disagreements/ep/counter_02527.webp` |
| 2528 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02528.webp` |
| 2529 | F1 H 236/235; F1 c 4/5 | `reports/engine_run_R_disagreements/ep/counter_02529.webp` |
| 2530 | F1 H 236/235; F1 c 4/5; F2 S/first-full L522/L523 | `reports/engine_run_R_disagreements/ep/counter_02530.webp` |

## Picture top

### Engine field 1

Agreement histogram (engine minus reference): +0: 621

No differences.

### Engine field 2

Agreement histogram (engine minus reference): -2: 3, +0: 618

| engine counter | raw counter/field | engine | reference | verdict | raw top rows |
|---:|:---:|:---|:---|:---|:---|
| 2027 | 2027/F2 | L286 | L288 | reference (VBI/black-line exclusion and picture-row continuity) | waveforms=[284, 287]; L286 41.75/44.38 r_next=0.268 MAD_above=40.41 lag=0(40.41/40.41); L287 25.28/41.22 r_next=-0.033 MAD_above=34.07 lag=-32(28.99/34.07); L288 151.40/26.43 r_next=0.913 MAD_above=128.69 lag=15(128.35/128.69); L289 147.61/27.80 r_next=0.940 MAD_above=7.83 lag=0(7.83/7.83) |
| 2033 | 2033/F2 | L286 | L288 | reference (VBI/black-line exclusion and picture-row continuity) | waveforms=[284, 287]; L286 42.31/43.23 r_next=0.132 MAD_above=40.97 lag=0(40.97/40.97); L287 25.90/41.38 r_next=-0.031 MAD_above=37.65 lag=-32(29.45/37.65); L288 150.67/26.07 r_next=0.932 MAD_above=127.63 lag=14(127.00/127.63); L289 149.11/26.39 r_next=0.924 MAD_above=6.97 lag=0(6.97/6.97) |
| 2523 | 2523/F2 | L286 | L288 | reference (VBI/black-line exclusion and picture-row continuity) | waveforms=[284, 287]; L286 53.71/51.69 r_next=-0.019 MAD_above=52.38 lag=-32(48.80/52.38); L287 20.22/35.11 r_next=-0.016 MAD_above=49.99 lag=31(37.98/49.99); L288 165.55/18.41 r_next=0.965 MAD_above=145.33 lag=17(145.19/145.33); L289 167.15/18.23 r_next=0.946 MAD_above=3.50 lag=-1(3.49/3.50) |

## Head-switch row

`S` is scored first against the reference's earliest switch-band row. A difference of one row is the declared partial-predecessor semantic gap. The separate exact check uses the reference's independently measured first-full-other-head row: an internal blanking signature, a persistent three-third step, or a two-sided whole-row time-base step. It remains unmeasurable when none is exposed.

### Engine field 1

S minus reference switch histogram: -2: 1, -1: 8, +0: 481, +1: 129, +2: 1, +3: 1

Differences beyond the one-row semantic gap:

| engine counter | raw counter/field | S | reference switch | raw tail rows |
|---:|:---:|:---|:---|:---|
| 1941 | 1941/F1 | L261 | L259 | L258 85.98/31.53 r_next=0.994 MAD_above=3.33 lag=1(3.28/3.33); L259 84.72/32.35 r_next=0.104 MAD_above=2.74 lag=1(2.72/2.74); L260 43.71/37.32 r_next=-0.286 MAD_above=41.42 lag=-32(40.54/41.42); L261 11.12/0.99 r_next=0.016 MAD_above=33.12 lag=-32(30.54/33.12); L262 10.39/0.65 r_next=0.041 MAD_above=1.06 lag=-31(1.02/1.06); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.985; no internal horizontal blanking run; gate=4.000) |
| 2051 | 2051/F1 | L259 | L261 | L258 127.69/82.07 r_next=0.999 MAD_above=1.96 lag=-1(1.93/1.96); L259 127.77/82.00 r_next=0.999 MAD_above=1.82 lag=-1(1.68/1.82); L260 128.26/82.27 r_next=-0.423 MAD_above=1.91 lag=-1(1.81/1.91); L261 18.28/15.72 r_next=-0.045 MAD_above=111.82 lag=-4(111.19/111.82); L262 11.67/0.93 r_next=-0.008 MAD_above=7.33 lag=-31(7.06/7.33); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.978; no internal horizontal blanking run; gate=4.000) |
| 2348 | 2348/F1 | L262 | L259 | L258 36.63/16.56 r_next=0.452 MAD_above=8.46 lag=0(8.46/8.46); L259 31.64/12.12 r_next=0.514 MAD_above=10.37 lag=0(10.37/10.37); L260 34.83/14.14 r_next=0.158 MAD_above=8.52 lag=-32(8.12/8.52); L261 21.78/14.76 r_next=-0.132 MAD_above=16.39 lag=32(15.14/16.39); L262 10.96/0.79 r_next=-0.012 MAD_above=11.27 lag=-32(10.02/11.27); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.997; no internal horizontal blanking run; gate=4.000) |

First-full-other-head histogram (engine S minus reference): +0: 1, reference-unmeasurable: 620

- reference-unmeasurable: counters 1910-2488, 2490-2530.  Witnesses: counter 1910: engine L262, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.984; no internal horizontal blanking run; gate=4.000 / counter 1911: engine L262, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.982; no internal horizontal blanking run; gate=4.000 / counter 1912: engine L262, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.980; no internal horizontal blanking run; gate=4.000

### Engine field 2

S minus reference switch histogram: -2: 3, -1: 119, +0: 378, +1: 121

Differences beyond the one-row semantic gap:

| engine counter | raw counter/field | S | reference switch | raw tail rows |
|---:|:---:|:---|:---|:---|
| 2054 | 2054/F2 | L521 | L523 | L520 125.42/82.16 r_next=0.999 MAD_above=1.97 lag=-1(1.81/1.97); L521 125.67/81.67 r_next=0.999 MAD_above=2.03 lag=-1(2.03/2.03); L522 124.93/82.28 r_next=0.438 MAD_above=2.42 lag=2(2.12/2.42); L523 11.33/0.85 r_next=0.207 MAD_above=113.60 lag=32(109.83/113.60); L524 11.69/0.78 r_next=0.004 MAD_above=0.81 lag=-25(0.74/0.81); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.977; no internal horizontal blanking run; gate=4.000) |
| 2105 | 2105/F2 | L521 | L523 | L520 122.83/82.99 r_next=0.999 MAD_above=2.22 lag=-1(2.18/2.22); L521 122.68/82.76 r_next=0.995 MAD_above=1.84 lag=-1(1.74/1.84); L522 124.09/82.64 r_next=0.418 MAD_above=2.92 lag=-4(1.80/2.92); L523 11.33/0.98 r_next=0.296 MAD_above=112.79 lag=32(109.00/112.79); L524 11.80/0.88 r_next=-0.098 MAD_above=0.91 lag=-28(0.82/0.91); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.975; no internal horizontal blanking run; gate=4.000) |
| 2484 | 2484/F2 | L521 | L523 | L520 67.08/33.20 r_next=0.971 MAD_above=4.06 lag=1(3.60/4.06); L521 67.89/32.64 r_next=0.751 MAD_above=4.48 lag=1(4.07/4.48); L522 67.26/31.58 r_next=-0.285 MAD_above=13.61 lag=-13(4.12/13.61); L523 12.30/0.98 r_next=0.222 MAD_above=54.96 lag=-32(52.49/54.96); L524 12.62/0.86 r_next=-0.043 MAD_above=0.90 lag=11(0.77/0.90); direct-full=unmeasurable (no independently exposed full other-head row; middle coherence=0.985; no internal horizontal blanking run; gate=4.000) |

First-full-other-head histogram (engine S minus reference): -1: 24, +0: 34, reference-unmeasurable: 563

- -1: counters 1929, 1950, 2033, 2042, 2044, 2047, 2073, 2138, 2192, 2225, 2257, 2435, 2468, 2473, 2475, 2482, 2488, 2492, 2499, 2502, 2507, 2521-2522, 2530.  Witnesses: counter 1929: engine L522, direct L523; L523 persistent three-third step; thirds=55.822,55.931,32.774; correlation above/next=0.326/0.723; middle coherence=0.944 / counter 1950: engine L522, direct L523; L523 persistent three-third step; thirds=18.077,21.120,37.378; correlation above/next=0.117/0.707; middle coherence=0.990 / counter 2033: engine L522, direct L523; L523 persistent three-third step; thirds=10.659,49.645,55.946; correlation above/next=0.176/0.708; middle coherence=0.981

- reference-unmeasurable: counters 1910-1921, 1923-1925, 1927-1928, 1930-1932, 1934-1949, 1951-1963, 1967, 1969-1970, 1972, 1974-1978, 1980-1985, 1988-1989, 1991-2009, 2012-2032, 2034-2041, 2043, 2045-2046, 2048-2072, 2074-2137, 2139-2146, 2148-2162, 2164-2187, 2189-2190, 2193-2224, 2227, 2229-2256, 2258-2308, 2310-2365, 2368-2371, 2373-2384, 2386-2396, 2398-2434, 2437-2467, 2469-2472, 2474, 2476-2481, 2483-2484, 2486-2487, 2490-2491, 2493-2494, 2496-2497, 2500, 2503-2505, 2508-2520, 2523-2529.  Witnesses: counter 1910: engine L523, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.986; no internal horizontal blanking run; gate=4.000 / counter 1911: engine L523, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.983; no internal horizontal blanking run; gate=4.000 / counter 1912: engine L523, direct unmeasurable; no independently exposed full other-head row; middle coherence=0.982; no internal horizontal blanking run; gate=4.000

Every numeric first-full disagreement:

| engine counter | raw counter/field | engine S | reference first-full | raw tail rows |
|---:|:---:|:---|:---|:---|
| 1929 | 1929/F2 | L522 | L523 | L521 84.33/27.47 r_next=0.917 MAD_above=3.34 lag=0(3.34/3.34); L522 83.73/27.95 r_next=0.172 MAD_above=6.67 lag=-3(3.39/6.67); L523 10.36/0.88 r_next=0.408 MAD_above=73.37 lag=-32(72.70/73.37); L524 11.04/0.85 r_next=0.033 MAD_above=0.89 lag=4(0.87/0.89); direct-full=L523 (L523 persistent three-third step; thirds=55.822,55.931,32.774; correlation above/next=0.326/0.723; middle coherence=0.944) |
| 1950 | 1950/F2 | L522 | L523 | L521 93.52/43.60 r_next=0.879 MAD_above=7.07 lag=-2(6.88/7.07); L522 92.29/43.06 r_next=0.094 MAD_above=8.88 lag=-6(6.12/8.88); L523 12.28/1.02 r_next=0.433 MAD_above=80.00 lag=32(79.11/80.00); L524 12.89/0.95 r_next=-0.074 MAD_above=0.94 lag=-21(0.83/0.94); direct-full=L523 (L523 persistent three-third step; thirds=18.077,21.120,37.378; correlation above/next=0.117/0.707; middle coherence=0.990) |
| 2033 | 2033/F2 | L522 | L523 | L521 139.79/73.17 r_next=0.996 MAD_above=3.20 lag=0(3.20/3.20); L522 142.29/72.01 r_next=0.157 MAD_above=3.95 lag=-3(3.39/3.95); L523 11.72/0.90 r_next=0.341 MAD_above=130.57 lag=32(127.79/130.57); L524 12.53/0.85 r_next=-0.040 MAD_above=1.03 lag=-24(0.94/1.03); direct-full=L523 (L523 persistent three-third step; thirds=10.659,49.645,55.946; correlation above/next=0.176/0.708; middle coherence=0.981) |
| 2042 | 2042/F2 | L522 | L523 | L521 136.33/75.96 r_next=0.996 MAD_above=3.98 lag=0(3.98/3.98); L522 136.82/74.87 r_next=0.244 MAD_above=3.57 lag=2(3.15/3.57); L523 11.78/0.93 r_next=0.426 MAD_above=125.05 lag=32(122.02/125.05); L524 12.26/0.92 r_next=-0.063 MAD_above=0.82 lag=-29(0.80/0.82); direct-full=L523 (L523 persistent three-third step; thirds=8.378,55.079,57.209; correlation above/next=0.291/0.781; middle coherence=0.987) |
| 2044 | 2044/F2 | L522 | L523 | L521 136.84/76.23 r_next=0.995 MAD_above=3.85 lag=0(3.85/3.85); L522 139.96/74.48 r_next=0.235 MAD_above=4.40 lag=-5(3.31/4.40); L523 12.35/0.98 r_next=0.402 MAD_above=127.61 lag=32(124.62/127.61); L524 12.59/0.95 r_next=-0.074 MAD_above=0.80 lag=-20(0.68/0.80); direct-full=L523 (L523 persistent three-third step; thirds=8.538,59.190,62.049; correlation above/next=0.282/0.710; middle coherence=0.985) |
| 2047 | 2047/F2 | L522 | L523 | L521 129.86/81.13 r_next=0.995 MAD_above=1.88 lag=0(1.88/1.88); L522 131.63/80.22 r_next=0.342 MAD_above=3.37 lag=-4(2.34/3.37); L523 12.13/0.92 r_next=0.422 MAD_above=119.50 lag=32(116.12/119.50); L524 12.39/1.01 r_next=-0.057 MAD_above=0.82 lag=2(0.76/0.82); direct-full=L523 (L523 persistent three-third step; thirds=3.966,57.292,56.734; correlation above/next=0.432/0.705; middle coherence=0.986) |
| 2073 | 2073/F2 | L522 | L523 | L521 124.51/82.55 r_next=0.992 MAD_above=1.78 lag=-1(1.69/1.78); L522 126.00/82.76 r_next=0.299 MAD_above=3.51 lag=-5(2.01/3.51); L523 11.64/0.94 r_next=0.355 MAD_above=114.37 lag=32(110.51/114.37); L524 12.10/0.95 r_next=-0.059 MAD_above=0.91 lag=-30(0.81/0.91); direct-full=L523 (L523 persistent three-third step; thirds=2.509,42.347,56.251; correlation above/next=0.408/0.729; middle coherence=0.978) |
| 2138 | 2138/F2 | L522 | L523 | L521 127.52/82.42 r_next=0.996 MAD_above=1.91 lag=-1(1.89/1.91); L522 129.28/81.76 r_next=0.362 MAD_above=3.20 lag=-6(2.21/3.20); L523 11.13/0.95 r_next=0.426 MAD_above=118.15 lag=32(114.72/118.15); L524 11.51/1.04 r_next=-0.082 MAD_above=0.85 lag=-26(0.79/0.85); direct-full=L523 (L523 persistent three-third step; thirds=3.111,58.301,56.440; correlation above/next=0.430/0.719; middle coherence=0.986) |
| 2192 | 2192/F2 | L522 | L523 | L521 131.78/68.53 r_next=0.993 MAD_above=3.05 lag=0(3.05/3.05); L522 131.37/70.00 r_next=0.412 MAD_above=4.65 lag=-6(3.15/4.65); L523 11.89/1.01 r_next=0.493 MAD_above=119.49 lag=32(115.84/119.49); L524 12.17/0.99 r_next=-0.206 MAD_above=0.79 lag=6(0.77/0.79); direct-full=L523 (L523 persistent three-third step; thirds=7.335,39.697,60.218; correlation above/next=0.498/0.747; middle coherence=0.978) |
| 2225 | 2225/F2 | L522 | L523 | L521 121.74/80.56 r_next=0.993 MAD_above=2.42 lag=-1(2.40/2.42); L522 122.19/80.72 r_next=0.358 MAD_above=3.92 lag=-5(2.58/3.92); L523 11.69/0.97 r_next=0.415 MAD_above=110.50 lag=32(106.44/110.50); L524 11.94/1.01 r_next=-0.063 MAD_above=0.81 lag=5(0.77/0.81); direct-full=L523 (L523 persistent three-third step; thirds=2.973,31.845,55.955; correlation above/next=0.470/0.713; middle coherence=0.977) |
| 2257 | 2257/F2 | L522 | L523 | L521 119.65/79.93 r_next=0.998 MAD_above=2.41 lag=-1(2.35/2.41); L522 118.86/80.30 r_next=0.248 MAD_above=2.85 lag=2(2.43/2.85); L523 11.16/0.98 r_next=0.414 MAD_above=107.72 lag=32(103.46/107.72); L524 11.75/0.93 r_next=-0.169 MAD_above=0.92 lag=5(0.88/0.92); direct-full=L523 (L523 persistent three-third step; thirds=3.769,28.607,55.279; correlation above/next=0.314/0.711; middle coherence=0.975) |
| 2435 | 2435/F2 | L522 | L523 | L521 51.30/19.33 r_next=0.934 MAD_above=4.91 lag=0(4.91/4.91); L522 51.74/19.28 r_next=0.142 MAD_above=4.84 lag=-3(4.35/4.84); L523 12.69/0.94 r_next=0.424 MAD_above=39.05 lag=32(38.70/39.05); L524 12.95/0.91 r_next=-0.123 MAD_above=0.78 lag=-19(0.73/0.78); direct-full=L523 (L523 persistent three-third step; thirds=7.416,9.979,17.082; correlation above/next=0.181/0.710; middle coherence=0.980) |
| 2468 | 2468/F2 | L522 | L523 | L521 63.83/17.66 r_next=0.828 MAD_above=4.05 lag=1(3.81/4.05); L522 62.62/18.05 r_next=0.276 MAD_above=4.14 lag=-2(3.72/4.14); L523 12.25/0.88 r_next=0.371 MAD_above=50.37 lag=3(50.33/50.37); L524 12.67/0.91 r_next=0.007 MAD_above=0.83 lag=4(0.76/0.83); direct-full=L523 (L523 persistent three-third step; thirds=18.804,16.563,9.568; correlation above/next=0.384/0.730; middle coherence=0.990) |
| 2473 | 2473/F2 | L522 | L523 | L521 64.75/25.91 r_next=0.862 MAD_above=4.75 lag=1(4.58/4.75); L522 64.61/25.42 r_next=-0.071 MAD_above=7.72 lag=-4(5.22/7.72); L523 12.35/0.95 r_next=0.397 MAD_above=52.26 lag=-32(50.70/52.26); L524 12.75/0.93 r_next=0.033 MAD_above=0.81 lag=-23(0.77/0.81); direct-full=L523 (L523 persistent three-third step; thirds=27.718,12.532,7.848; correlation above/next=-0.166/0.713; middle coherence=0.992) |
| 2475 | 2475/F2 | L522 | L523 | L521 64.59/28.35 r_next=0.969 MAD_above=5.06 lag=2(4.83/5.06); L522 64.26/26.93 r_next=-0.179 MAD_above=4.68 lag=-2(4.11/4.68); L523 12.48/1.01 r_next=0.404 MAD_above=51.78 lag=-32(49.60/51.78); L524 12.72/0.95 r_next=0.080 MAD_above=0.81 lag=-23(0.75/0.81); direct-full=L523 (L523 persistent three-third step; thirds=28.812,9.077,7.127; correlation above/next=-0.209/0.703; middle coherence=0.991) |
| 2482 | 2482/F2 | L522 | L523 | L521 69.29/32.43 r_next=0.955 MAD_above=4.31 lag=1(4.17/4.31); L522 69.13/32.90 r_next=-0.374 MAD_above=5.05 lag=-2(3.79/5.05); L523 12.82/1.03 r_next=0.429 MAD_above=56.31 lag=-32(53.63/56.31); L524 12.72/0.93 r_next=0.191 MAD_above=0.78 lag=6(0.71/0.78); direct-full=L523 (L523 persistent three-third step; thirds=22.385,6.539,5.115; correlation above/next=-0.498/0.756; middle coherence=0.985) |
| 2488 | 2488/F2 | L522 | L523 | L521 63.54/31.94 r_next=0.886 MAD_above=3.05 lag=0(3.05/3.05); L522 62.88/29.87 r_next=-0.384 MAD_above=7.08 lag=-6(2.98/7.08); L523 12.82/0.85 r_next=0.382 MAD_above=50.05 lag=-32(47.41/50.05); L524 12.90/0.94 r_next=-0.105 MAD_above=0.74 lag=9(0.68/0.74); direct-full=L523 (L523 persistent three-third step; thirds=19.323,6.456,3.464; correlation above/next=-0.499/0.760; middle coherence=0.983) |
| 2492 | 2492/F2 | L522 | L523 | L521 62.58/32.61 r_next=0.902 MAD_above=4.36 lag=0(4.36/4.36); L522 62.38/33.98 r_next=-0.334 MAD_above=7.70 lag=-5(5.02/7.70); L523 12.67/0.95 r_next=0.429 MAD_above=49.71 lag=-32(47.04/49.71); L524 12.90/0.94 r_next=-0.060 MAD_above=0.77 lag=11(0.71/0.77); direct-full=L523 (L523 persistent three-third step; thirds=18.063,6.729,2.806; correlation above/next=-0.427/0.711; middle coherence=0.982) |
| 2499 | 2499/F2 | L522 | L523 | L521 62.75/33.71 r_next=0.948 MAD_above=3.92 lag=0(3.92/3.92); L522 63.67/34.73 r_next=-0.402 MAD_above=5.44 lag=-2(4.72/5.44); L523 13.08/1.06 r_next=0.498 MAD_above=50.61 lag=-32(48.05/50.61); L524 13.41/1.04 r_next=0.089 MAD_above=0.81 lag=7(0.73/0.81); direct-full=L523 (L523 persistent three-third step; thirds=20.094,6.540,3.093; correlation above/next=-0.473/0.779; middle coherence=0.982) |
| 2502 | 2502/F2 | L522 | L523 | L521 61.87/32.91 r_next=0.974 MAD_above=4.98 lag=0(4.98/4.98); L522 61.65/32.03 r_next=-0.400 MAD_above=3.80 lag=-2(3.21/3.80); L523 12.93/1.01 r_next=0.466 MAD_above=48.72 lag=-32(46.39/48.72); L524 12.84/0.97 r_next=-0.028 MAD_above=0.76 lag=6(0.73/0.76); direct-full=L523 (L523 persistent three-third step; thirds=20.059,5.883,3.538; correlation above/next=-0.487/0.755; middle coherence=0.984) |
| 2507 | 2507/F2 | L522 | L523 | L521 66.90/35.43 r_next=0.947 MAD_above=3.42 lag=0(3.42/3.42); L522 65.10/34.46 r_next=-0.346 MAD_above=5.85 lag=-6(2.84/5.85); L523 12.65/0.93 r_next=0.423 MAD_above=52.45 lag=-32(48.70/52.45); L524 12.92/1.00 r_next=-0.070 MAD_above=0.79 lag=-23(0.77/0.79); direct-full=L523 (L523 persistent three-third step; thirds=22.070,5.588,4.017; correlation above/next=-0.398/0.721; middle coherence=0.984) |
| 2521 | 2521/F2 | L522 | L523 | L521 72.94/37.09 r_next=0.961 MAD_above=2.46 lag=0(2.46/2.46); L522 73.17/36.97 r_next=-0.394 MAD_above=4.55 lag=-5(2.41/4.55); L523 13.45/1.01 r_next=0.464 MAD_above=59.72 lag=-32(56.13/59.72); L524 13.41/0.90 r_next=0.146 MAD_above=0.75 lag=8(0.73/0.75); direct-full=L523 (L523 persistent three-third step; thirds=23.449,10.914,4.408; correlation above/next=-0.440/0.727; middle coherence=0.984) |
| 2522 | 2522/F2 | L522 | L523 | L521 74.00/37.91 r_next=0.960 MAD_above=2.52 lag=1(2.44/2.52); L522 73.76/37.32 r_next=-0.259 MAD_above=4.90 lag=-4(3.75/4.90); L523 12.92/1.01 r_next=0.416 MAD_above=60.84 lag=-32(57.30/60.84); L524 13.03/1.03 r_next=-0.002 MAD_above=0.83 lag=8(0.75/0.83); direct-full=L523 (L523 persistent three-third step; thirds=23.434,11.825,4.226; correlation above/next=-0.318/0.705; middle coherence=0.985) |
| 2530 | 2530/F2 | L522 | L523 | L521 78.38/36.34 r_next=0.974 MAD_above=2.55 lag=0(2.55/2.55); L522 77.78/36.08 r_next=-0.283 MAD_above=3.54 lag=-3(2.38/3.54); L523 12.13/0.96 r_next=0.415 MAD_above=65.65 lag=-32(62.29/65.65); L524 12.40/0.95 r_next=-0.127 MAD_above=0.80 lag=6(0.76/0.80); direct-full=L523 (L523 persistent three-third step; thirds=24.337,13.989,4.926; correlation above/next=-0.310/0.745; middle coherence=0.986) |

## Segment constants and applied crop

### Engine field 1

- H engine minus reference: +1: 621; mismatch counters: 1910-2530.
- c engine minus reference: -1: 621; mismatch counters: 1910-2530.
- crop engine minus reference: -1: 109, +0: 495, +1: 8, +2: 4, +3: 5; mismatch counters: 1910-1922, 1933, 1937, 1940, 1947-1950, 1953-1960, 1962, 1966, 1969, 1976, 1983-1985, 1987, 1999, 2002-2004, 2008, 2010, 2012, 2014, 2020-2021, 2024, 2027, 2029, 2032, 2035, 2039, 2044, 2051, 2059, 2063, 2065, 2071, 2074, 2077, 2083, 2087, 2098, 2107, 2114, 2125, 2128, 2135, 2148, 2152, 2156, 2159, 2163, 2166, 2170, 2177, 2179, 2186, 2197, 2199, 2203, 2207, 2213, 2217, 2225, 2235, 2238, 2240, 2245, 2249, 2251, 2263, 2265, 2269, 2271, 2283, 2292, 2295, 2297, 2301, 2315-2316, 2348, 2364, 2371, 2379, 2383, 2391, 2395, 2425, 2433, 2437, 2444, 2447, 2450, 2479-2483, 2485-2486, 2496, 2514, 2518, 2527.

### Engine field 2

- H engine minus reference: +0: 621; mismatch counters: none.
- c engine minus reference: +0: 621; mismatch counters: none.
- crop engine minus reference: -2: 3, +0: 611, +2: 7; mismatch counters: 1910-1916, 2027, 2033, 2523.

## Comb consistency

Comparable measured pairs: 371; unavailable engine/top pair: 0; contradictions: 69.

| reference counter | comb shift | engine tops | engine-reference top deltas | seven energies |
|---:|---:|:---|:---|:---|
| 1958 | +0 | L25/L288 | -1/+0 | -3:3.636018,-2:2.569826,-1:1.814970,0:1.370068,1:1.858553,2:2.959696,3:4.325238 |
| 1959 | +0 | L25/L288 | -1/+0 | -3:4.099129,-2:2.909372,-1:2.032837,0:1.482172,1:2.044592,2:3.135518,3:4.534647 |
| 1960 | +0 | L25/L288 | -1/+0 | -3:4.533296,-2:3.136873,-1:2.036025,0:1.239238,1:1.604194,2:2.736227,3:4.197827 |
| 1966 | +0 | L25/L288 | -1/+0 | -3:4.638797,-2:3.120372,-1:1.984378,0:1.248392,1:1.593386,2:2.532201,3:3.862507 |
| 1969 | +0 | L25/L288 | -1/+0 | -3:5.431118,-2:3.718215,-1:2.336577,0:1.381726,1:2.012068,2:3.519354,3:5.227288 |
| 1976 | +0 | L25/L288 | -1/+0 | -3:5.021707,-2:3.454768,-1:2.305776,0:1.610424,1:2.043262,2:3.320199,3:5.080885 |
| 1987 | +0 | L25/L288 | -1/+0 | -3:5.508502,-2:3.757600,-1:2.332124,0:1.321031,1:1.861373,2:3.282070,3:5.068344 |
| 1999 | +0 | L26/L288 | +1/+0 | -3:5.915755,-2:4.069001,-1:2.602225,0:1.538184,1:1.925000,2:3.400748,3:5.239861 |
| 2004 | +0 | L26/L288 | +1/+0 | -3:5.242704,-2:3.632175,-1:2.310726,0:1.399145,1:1.861879,2:3.273722,3:4.860428 |
| 2008 | +0 | L26/L288 | +1/+0 | -3:4.446631,-2:2.997413,-1:1.958453,0:1.370102,1:1.764429,2:2.852943,3:4.302223 |
| 2010 | +0 | L26/L288 | +1/+0 | -3:4.711020,-2:3.165365,-1:2.059990,0:1.416274,1:1.886912,2:3.144679,3:4.762387 |
| 2012 | +0 | L25/L288 | -1/+0 | -3:5.377848,-2:3.577110,-1:2.169017,0:1.172786,1:1.745061,2:3.230337,3:5.061993 |
| 2014 | +0 | L25/L288 | -1/+0 | -3:5.892273,-2:4.037770,-1:2.520801,0:1.345342,1:1.996345,2:3.580920,3:5.473850 |
| 2020 | +0 | L25/L288 | -1/+0 | -3:5.607387,-2:3.892715,-1:2.416274,0:1.308218,1:2.017228,2:3.635755,3:5.434740 |
| 2021 | +0 | L25/L288 | -1/+0 | -3:6.054257,-2:4.147009,-1:2.488774,0:1.304075,1:1.986073,2:3.737081,3:5.820622 |
| 2024 | +0 | L26/L288 | +1/+0 | -3:5.426374,-2:3.639748,-1:2.285166,0:1.235977,1:1.727941,2:2.962706,3:4.576048 |
| 2027 | +0 | L25/L286 | -1/-2 | -3:4.642749,-2:3.408041,-1:2.205439,0:1.261621,1:1.996987,2:3.470402,3:5.159712 |
| 2029 | +0 | L25/L288 | -1/+0 | -3:4.376851,-2:3.161658,-1:1.992937,0:1.115952,1:1.889922,2:3.154151,3:4.542077 |
| 2044 | +0 | L25/L288 | -1/+0 | -3:4.710673,-2:3.447447,-1:2.194724,0:1.291364,1:1.819280,2:2.848714,3:3.952097 |
| 2051 | +0 | L25/L288 | -1/+0 | -3:5.204640,-2:3.738465,-1:2.394769,0:1.411714,1:1.873675,2:2.986401,3:4.276221 |
| 2063 | +0 | L25/L288 | -1/+0 | -3:5.870240,-2:4.321271,-1:2.779112,0:1.672184,1:2.271575,2:3.715841,3:5.209692 |
| 2065 | +0 | L25/L288 | -1/+0 | -3:5.376429,-2:3.911091,-1:2.572857,0:1.475536,1:2.079028,2:3.394901,3:4.892222 |
| 2071 | +0 | L25/L288 | -1/+0 | -3:5.339910,-2:3.837010,-1:2.475962,0:1.588145,1:2.152273,2:3.487645,3:5.012649 |
| 2074 | +0 | L25/L288 | -1/+0 | -3:4.946619,-2:3.606628,-1:2.385167,0:1.579336,1:2.067118,2:3.312274,3:4.720639 |
| 2077 | +0 | L25/L288 | -1/+0 | -3:5.612028,-2:4.007558,-1:2.461419,0:1.220054,1:1.877539,2:3.406942,3:4.903899 |
| 2083 | +0 | L25/L288 | -1/+0 | -3:4.771338,-2:3.337176,-1:2.201554,0:1.354203,1:2.002203,2:3.232851,3:4.549500 |
| 2087 | +0 | L25/L288 | -1/+0 | -3:5.027439,-2:3.623509,-1:2.443943,0:1.548714,1:2.000445,2:3.077199,3:4.511705 |
| 2098 | +0 | L25/L288 | -1/+0 | -3:4.535437,-2:3.232656,-1:2.088717,0:1.201634,1:1.834574,2:3.190092,3:4.516433 |
| 2107 | +0 | L25/L288 | -1/+0 | -3:5.022818,-2:3.670089,-1:2.409189,0:1.396960,1:1.906507,2:3.171784,3:4.535048 |
| 2114 | +0 | L25/L288 | -1/+0 | -3:4.983550,-2:3.490462,-1:2.127394,0:1.059140,1:1.641180,2:2.960129,3:4.429661 |
| 2125 | +0 | L25/L288 | -1/+0 | -3:4.876887,-2:3.488210,-1:2.261771,0:1.395422,1:1.785781,2:2.894768,3:4.224514 |
| 2128 | +0 | L25/L288 | -1/+0 | -3:5.191584,-2:3.719480,-1:2.413265,0:1.405967,1:1.802531,2:3.085652,3:4.482686 |
| 2135 | +0 | L25/L288 | -1/+0 | -3:4.846856,-2:3.450085,-1:2.155395,0:1.230422,1:1.864516,2:3.224842,3:4.708605 |
| 2156 | +0 | L25/L288 | -1/+0 | -3:4.215716,-2:2.940371,-1:1.867421,0:1.070302,1:1.491548,2:2.494917,3:3.722149 |
| 2159 | +0 | L25/L288 | -1/+0 | -3:4.347600,-2:3.214878,-1:2.128839,0:1.331161,1:1.690431,2:2.620033,3:3.867467 |
| 2166 | +0 | L25/L288 | -1/+0 | -3:4.357807,-2:3.190405,-1:2.132150,0:1.293945,1:1.666107,2:2.459230,3:3.555992 |
| 2186 | +0 | L25/L288 | -1/+0 | -3:5.384608,-2:3.973849,-1:2.619164,0:1.685024,1:2.181056,2:3.379008,3:4.773047 |
| 2197 | +0 | L25/L288 | -1/+0 | -3:4.882580,-2:3.412592,-1:2.254386,0:1.493872,1:2.112776,2:3.649884,3:5.346762 |
| 2199 | +0 | L25/L288 | -1/+0 | -3:4.357610,-2:3.078247,-1:2.040828,0:1.304251,1:1.963489,2:3.389419,3:4.966653 |
| 2203 | +0 | L25/L288 | -1/+0 | -3:4.192791,-2:2.951606,-1:1.809994,0:1.089294,1:1.636636,2:2.789362,3:4.063844 |
| 2207 | +0 | L25/L288 | -1/+0 | -3:5.036042,-2:3.678867,-1:2.474617,0:1.641157,1:2.203455,2:3.403854,3:4.859403 |
| 2213 | +0 | L25/L288 | -1/+0 | -3:5.548477,-2:3.988562,-1:2.556117,0:1.508968,1:2.135832,2:3.676784,3:5.274483 |
| 2217 | +0 | L25/L288 | -1/+0 | -3:5.409194,-2:3.887595,-1:2.491724,0:1.381548,1:2.146371,2:3.639482,3:5.194480 |
| 2225 | +0 | L25/L288 | -1/+0 | -3:5.508794,-2:4.049434,-1:2.746150,0:1.702007,1:2.260384,2:3.497069,3:4.836198 |
| 2235 | +0 | L25/L288 | -1/+0 | -3:5.081907,-2:3.497801,-1:2.133938,0:1.290379,1:1.765064,2:3.080704,3:4.582542 |
| 2238 | +0 | L25/L288 | -1/+0 | -3:5.334522,-2:3.768562,-1:2.346527,0:1.432374,1:2.091379,2:3.341165,3:4.668959 |
| 2240 | +0 | L25/L288 | -1/+0 | -3:4.929086,-2:3.525575,-1:2.188725,0:1.188421,1:1.956423,2:3.400798,3:4.797627 |
| 2245 | +0 | L25/L288 | -1/+0 | -3:5.216080,-2:3.654113,-1:2.306282,0:1.313033,1:1.893851,2:3.257461,3:4.597329 |
| 2249 | +0 | L25/L288 | -1/+0 | -3:5.040634,-2:3.599632,-1:2.223413,0:1.221878,1:1.807041,2:3.116472,3:4.522024 |
| 2263 | +0 | L25/L288 | -1/+0 | -3:5.956554,-2:4.386685,-1:2.770781,0:1.423213,1:2.210032,2:3.817887,3:5.493786 |
| 2265 | +0 | L25/L288 | -1/+0 | -3:6.068372,-2:4.490212,-1:2.903503,0:1.627717,1:2.359819,2:3.851370,3:5.547080 |
| 2269 | +0 | L25/L288 | -1/+0 | -3:5.650169,-2:4.066903,-1:2.655195,0:1.542980,1:2.160542,2:3.719383,3:5.497548 |
| 2271 | +0 | L25/L288 | -1/+0 | -3:5.389071,-2:3.778479,-1:2.327442,0:1.151540,1:1.951631,2:3.389764,3:4.866213 |
| 2283 | +0 | L25/L288 | -1/+0 | -3:5.193639,-2:3.752342,-1:2.463358,0:1.457561,1:1.857850,2:2.910528,3:4.102332 |
| 2292 | +0 | L25/L288 | -1/+0 | -3:5.000252,-2:3.651452,-1:2.483617,0:1.594863,1:2.218493,2:3.518417,3:4.929183 |
| 2295 | +0 | L25/L288 | -1/+0 | -3:5.219655,-2:3.798750,-1:2.376603,0:1.213505,1:1.865917,2:3.336630,3:5.019463 |
| 2297 | +0 | L25/L288 | -1/+0 | -3:5.755502,-2:4.252923,-1:2.768292,0:1.590182,1:2.262283,2:3.789142,3:5.447742 |
| 2301 | +0 | L25/L288 | -1/+0 | -3:5.843898,-2:4.270664,-1:2.880240,0:1.869229,1:2.445901,2:3.847526,3:5.271533 |
| 2315 | +0 | L25/L288 | -1/+0 | -3:3.089247,-2:2.787357,-1:2.456121,0:1.885202,1:3.712897,2:6.562729,3:9.083898 |
| 2348 | -1 | L26/L288 | +1/+0 | -4:11.623318,-3:8.028867,-2:4.704730,-1:2.242836,0:3.905298,1:7.455535,2:10.982902 |
| 2395 | +0 | L25/L288 | -1/+0 | -3:4.141565,-2:3.152744,-1:2.148139,0:1.285101,1:1.721426,2:2.611377,3:3.655734 |
| 2425 | +0 | L25/L288 | -1/+0 | -3:3.277632,-2:2.446755,-1:1.732605,0:1.316659,1:1.732340,2:2.514197,3:3.284206 |
| 2437 | +0 | L25/L288 | -1/+0 | -3:3.445574,-2:2.647045,-1:1.860881,0:1.221381,1:1.698195,2:2.590801,3:3.464660 |
| 2444 | +0 | L25/L288 | -1/+0 | -3:3.418915,-2:2.585759,-1:1.815778,0:1.261707,1:1.748350,2:2.676734,3:3.634403 |
| 2447 | +0 | L25/L288 | -1/+0 | -3:2.947588,-2:2.496773,-1:1.917420,0:1.298585,1:1.706807,2:2.440148,3:3.138509 |
| 2496 | +0 | L25/L288 | -1/+0 | -3:4.131272,-2:3.075377,-1:2.258579,0:1.740182,1:2.178550,2:2.996073,3:3.920657 |
| 2514 | +0 | L25/L288 | -1/+0 | -3:4.054493,-2:3.109661,-1:2.144623,0:1.411187,1:1.772991,2:2.654749,3:3.616030 |
| 2518 | +0 | L25/L288 | -1/+0 | -3:3.810466,-2:3.017336,-1:2.169906,0:1.647867,1:2.114745,2:3.046993,3:4.023126 |
| 2527 | +0 | L25/L288 | -1/+0 | -3:3.520092,-2:2.628911,-1:1.873081,0:1.381220,1:1.743416,2:2.545554,3:3.596672 |
