/* Exactness, not an image-quality test. Captured pairs are also checked by the
 * geometry_worker_verify against this same scalar oracle. */
#include "../geometry_engine.c"
#include "geometry_rigid_reference.h"
#include <assert.h>
#include <stdio.h>
static uint8_t current[GE_PIXELS],previous[GE_PIXELS];
static unsigned pairs;
static uint32_t rng=0x93564217;
static uint8_t random_byte(void) {
    rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return (uint8_t)(rng>>24);
}
static void check(int field) {
    unsigned expected_sums[11][17],actual_sums[11][17];
    ge_rigid_motion expected=rigid_reference(current,previous,field,expected_sums);
    ge_rigid_motion actual=ge_rigid_measure(current,previous,field);
    rigid_assert_equal(actual,expected);
    rigid_sums(current,previous,field,actual_sums);
    assert(!memcmp(actual_sums,expected_sums,sizeof actual_sums));
    pairs++;
}
int main(void) {
    for(unsigned k=0;k<3;k++) {
        memset(previous,k==2?7:0,sizeof previous);
        memset(current,k==1?255:k==2?8:0,sizeof current);
        for(int f=0;f<2;f++) {
            check(f);
            ge_rigid_motion m=ge_rigid_measure(current,previous,f);
            assert(m.dx==-8 && m.dy==-5 && m.clarity==1);
            assert(m.error==(k==1?255:k==2?1:0));
        }
    }
    for(unsigned k=0;k<64;k++) {
        for(unsigned i=0;i<GE_PIXELS;i++) {
            previous[i]=random_byte();current[i]=random_byte();
            if(k%4==0){previous[i]&=3;current[i]&=3;}
            if(k%4==1){previous[i]=(i%720)&1?255:0;current[i]=(i/720)&1?255:0;}
        }
        check(0);check(1);
    }
    /* Every candidate, both fields, including odd dx, range endpoints and
     * best=0/far>0 (infinite clarity). Poison all unselected samples. */
    for(unsigned i=0;i<GE_PIXELS;i++)previous[i]=random_byte();
    for(int f=0;f<2;f++)for(int dy=-5;dy<=5;dy++)for(int dx=-8;dx<=8;dx++) {
        memset(current,0,sizeof current);int off=19+263*f;
        for(int r=40;r<220;r++)for(int x=40;x<680;x+=2)
            current[(off+r+dy)*720+x+dx]=previous[(off+r)*720+x];
        check(f);
        ge_rigid_motion m=ge_rigid_measure(current,previous,f);
        assert(m.dx==dx && m.dy==dy && m.error==0 && m.far_error>0 && isinf(m.clarity));
    }
    /* Isolated extrema at each sampled corner expose row/column bound mistakes. */
    for(int f=0;f<2;f++)for(int row=40;row<=219;row+=179)for(int x=40;x<=678;x+=638) {
        memset(previous,0,sizeof previous);memset(current,0,sizeof current);
        previous[(19+263*f+row)*720+x]=255;check(f);
        current[(19+263*f+row)*720+x]=255;check(f);
    }
    printf("GEOMETRY-RIGID PASS pairs=%u candidate_sums=%u\n",pairs,pairs*187);
}
