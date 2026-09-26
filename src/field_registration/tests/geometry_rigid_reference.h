/* Test-only scalar oracle: the approved pre-optimisation loop, including
 * dy-major/dx-minor first-tie order and the complete far-candidate search. */
#ifndef GEOMETRY_RIGID_REFERENCE_H
#define GEOMETRY_RIGID_REFERENCE_H
#include "../geometry_engine.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static ge_rigid_motion rigid_reference(const uint8_t *current,const uint8_t *previous,
                                      int field,unsigned sums[11][17]) {
    unsigned best=UINT32_MAX,far=UINT32_MAX;
    int bx=0,by=0,off=19+263*field;
    for(int dy=-5;dy<=5;dy++)for(int dx=-8;dx<=8;dx++) {
        unsigned sum=0;
        for(int r=40;r<220;r++) {
            const uint8_t *a=current+(off+r+dy)*720+40+dx,*b=previous+(off+r)*720+40;
            for(int x=0;x<640;x+=2){int d=(int)a[x]-b[x];sum+=(unsigned)(d<0?-d:d);}
        }
        sums[dy+5][dx+8]=sum;
        if(sum<best){best=sum;bx=dx;by=dy;}
    }
    for(int dy=-5;dy<=5;dy++)for(int dx=-8;dx<=8;dx++)
        if((abs(dx-bx)>=2 || abs(dy-by)>=2) && sums[dy+5][dx+8]<far)far=sums[dy+5][dx+8];
    return (ge_rigid_motion){.known=1,.dx=bx,.dy=by,.error=best/(180.0*320),
        .far_error=far/(180.0*320),.clarity=best?(double)far/best:far?INFINITY:1};
}
static void rigid_assert_equal(ge_rigid_motion actual,ge_rigid_motion expected) {
    /* Compare the double representations too: equality alone misses signed zero. */
    if(actual.known!=expected.known || actual.dx!=expected.dx || actual.dy!=expected.dy ||
       memcmp(&actual.error,&expected.error,sizeof(double)) ||
       memcmp(&actual.far_error,&expected.far_error,sizeof(double)) ||
       memcmp(&actual.clarity,&expected.clarity,sizeof(double))) {
        fprintf(stderr,"RIGID MISMATCH actual=%d,%d,%d,%a,%a,%a expected=%d,%d,%d,%a,%a,%a\n",
            actual.known,actual.dx,actual.dy,actual.error,actual.far_error,actual.clarity,
            expected.known,expected.dx,expected.dy,expected.error,expected.far_error,expected.clarity);
        abort();
    }
}
#endif
