/* Same-unit bottom rule: no recorded picture is embedded in the fixture. */
#include "../geometry_engine.c"
#include <assert.h>
#include <stdio.h>
static uint8_t y[GE_PIXELS];
static void body(int row,int value){memset(y+row*720+40,value,640);}
static void check_field(int k) {
    int off=263*k;ge_bottom_evidence e;
    memset(y,10,sizeof y);ge_bottom_flat=1;ge_bottom_flat_margin=3;
    assert(bottom_scan(y,k,1,&e)==0 && e.rule==GE_BOTTOM_UNKNOWN);
    assert(e.measured && e.p5==10 && e.p50==10 && e.p95==10);
    body(257+off,13); /* uniform picture: median difference exactly 3 */
    assert(bottom_scan(y,k,1,&e)==261+off && e.rule==GE_BOTTOM_FLAT_REFERENCE);
    body(257+off,10);memset(y+(257+off)*720+40,13,64); /* partial high side */
    assert(bottom_scan(y,k,1,&e)==261+off);
    body(257+off,10);memset(y+(257+off)*720+40,7,64); /* low side */
    assert(bottom_scan(y,k,1,&e)==261+off);
    body(257+off,10);body(237+off,13);
    assert(bottom_scan(y,k,1,&e)==241+off); /* inclusive scan limit */
    body(237+off,10);body(236+off,100);
    assert(bottom_scan(y,k,1,&e)==0); /* outside scan */
    body(257+off,13);ge_bottom_flat_margin=3+5e-10;
    assert(bottom_scan(y,k,1,&e)==261+off); /* representation tolerance */
    ge_bottom_flat_margin=3+2e-9;
    assert(bottom_scan(y,k,1,&e)==0);
    body(257+off,10);y[(257+off)*720+40+607]=13;
    memset(y+(257+off)*720+40+608,14,32);ge_bottom_flat_margin=3.05;
    assert(bottom_scan(y,k,1,&e)==261+off); /* interpolated 13.05 minus 10 */
    ge_bottom_flat_margin=3;
    /* Nonqualifying F: old spread/amplitude test and asymmetric last input row. */
    for(int x=0;x<640;x++)y[(258+off)*720+40+x]=10+(x%2)*10;
    body(259+off,10);memset(y+(259+off)*720+40,30,200);
    assert(bottom_scan(y,k,1,&e)==(k?525:263) && e.rule==GE_BOTTOM_FALLBACK);
    ge_bottom_flat=0;
    assert(bottom_scan(y,k,1,&e)==262+off && !e.measured && e.rule==GE_BOTTOM_FALLBACK);
    ge_bottom_flat=1;body(258+off,10);body(257+off,13);
    assert(bottom_scan(y,k,1,&e)==261+off); /* qualified F never judges row below it */
    memset(y,10,sizeof y);body(257+off,20);
    memset(y+(258+off)*720+40,14,64);
    assert(bottom_scan(y,k,1,&e)==261+off && e.p95-e.p5==4);
    memset(y+(258+off)*720+40,15,64);
    assert(bottom_scan(y,k,1,&e)==262+off && e.rule==GE_BOTTOM_FALLBACK);
}
int main(void){
    check_field(0);check_field(1);
    ge_bottom_flat=0;ge_features old,new;ge_measure(y,&old);
    ge_bottom_flat=1;ge_measure(y,&new);
    memcpy(new.last,old.last,sizeof old.last);
    assert(!memcmp(&old,&new,offsetof(ge_features,bottom_evidence)));
    geometry_engine g;ge_init(&g,1,1);ge_decision out[2];
    assert(!ge_push(&g,y,100,0,out));
    body(258,20);body(257,23);body(521,30);body(520,33);
    assert(ge_push(&g,y,101,0,out)==1);
    assert(out[0].top_unit==101 && out[0].counter==100);
    assert(out[0].bottom_evidence[0].p50==20 && out[0].bottom_evidence[1].p50==10);
    puts("GEOMETRY-BOTTOM PASS: inclusive levels, partial lines, unknown, bounds, half-line fallback, off identity, frame ownership");
}
