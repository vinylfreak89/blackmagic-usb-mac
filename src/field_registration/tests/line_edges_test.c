/* Known answers for the per-line edge measurement (line_edges.h). Rows are built to the shapes
 * seen on tvc2 2026-10-01: a normal line (falloff near sample 10), picture spilling into sample 0,
 * a late line (blank to ~75), the full blanking interval mid-row, and dark picture ramping up. */
#include "../line_edges.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static uint8_t row[LE_WIDTH];
static void fill(int from,int to,int v){for(int x=from;x<to;x++)row[x]=(uint8_t)v;}

int main(void) {
    le_line o;const double blank=1;
    /* Normal: blank 0-9, rise at 10-11, picture 100 to 711, blank to the end. */
    fill(0,720,1);fill(11,712,100);row[10]=50;row[712]=50;
    le_measure_line(row,blank,&o);
    assert(o.left_state==LE_MEASURED && fabsf(o.left-10.0f)<0.6f);
    assert(o.right_state==LE_MEASURED && fabsf(o.right-712.0f)<0.6f);
    assert(o.gap_start<0);
    /* Spill: picture from sample 0. */
    fill(0,720,1);fill(0,712,100);row[712]=50;
    le_measure_line(row,blank,&o);assert(o.left_state==LE_SPILL && isnan(o.left));
    /* Late: blank to 74, then picture. */
    fill(0,720,1);fill(75,712,100);row[74]=50;row[712]=50;
    le_measure_line(row,blank,&o);assert(o.left_state==LE_MEASURED && fabsf(o.left-74.0f)<0.6f);
    /* Mid-row blanking: previous line's picture 0-359, blanking 360-506 (147), next line's picture after. */
    fill(0,720,100);fill(360,507,1);row[359]=50;row[507]=50;
    le_measure_line(row,blank,&o);
    assert(o.left_state==LE_SPILL && o.right_state==LE_SPILL);
    assert(o.gap_start==360 && o.gap_end==507 && o.gap_sharp);
    /* Dark picture ramping up from blanking at 2 codes/sample (20->80% over ~14 samples; the
     * measured falloff takes 2-7, dark picture ramping up 9-10): not a falloff. */
    fill(0,720,1);for(int x=10;x<55;x++)row[x]=(uint8_t)(1+(x-10)*2);fill(55,712,91);
    le_measure_line(row,blank,&o);assert(o.left_state==LE_UNMEASURED && isnan(o.left));
    /* Dim picture below the picture minimum: unmeasured, not mistimed. */
    fill(0,720,1);fill(11,712,30);
    le_measure_line(row,blank,&o);assert(o.left_state==LE_UNMEASURED);
    puts("LINE-EDGES PASS: normal, spill, late, mid-row blanking, ramp, dim");
    return 0;
}
