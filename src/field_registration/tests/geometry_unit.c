#include "../geometry_engine.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(void) {
    uint8_t *a=malloc(GE_PIXELS),*b=malloc(GE_PIXELS);
    geometry_engine *g=malloc(ge_size());assert(a&&b&&g);
    unsigned rng=71;
    for(unsigned i=0;i<GE_PIXELS;i++){rng=rng*1664525u+1013904223u;a[i]=(uint8_t)(rng>>24);}
    for(int d=-5;d<=5;d++) {
        memset(b,0,GE_PIXELS);
        for(int r=30;r<=240;r++)for(int x=24;x<696;x++)
            b[(r+259+d)*720+x]=(a[(r-4)*720+x]+a[(r-3)*720+x])/2;
        ge_comb_result c=ge_comb(a,b);
        assert(c.shift==d && c.decided && isinf(c.margin));
    }
    memset(a,1,GE_PIXELS);ge_features f;ge_measure(a,&f);
    assert(!f.first[0]&&!f.first[1]&&!f.last[0]&&!f.last[1]&&!f.bottom[0]&&!f.bottom[1]);
    ge_comb_result c=ge_comb(a,a);assert(!c.decided && c.margin==1);
    ge_decision out[2];ge_init(g,0,0);
    assert(ge_push(g,a,10,1,out)==1 && out[0].d1==0 && out[0].d2==0 && out[0].comb_ran);
    ge_init(g,1,0);
    assert(ge_push(g,a,10,1,out)==0);
    assert(ge_push(g,a,11,0,out)==1 && out[0].counter==10 && out[0].top_unit==11 && out[0].unused1 && !out[0].unused2);
    assert(ge_push(g,a,13,0,out)==1 && out[0].counter==11 && !out[0].has_frame && out[0].unused2);
    assert(ge_break(g,out)==1 && out[0].counter==13 && out[0].unused1 && out[0].unused2);
    assert(ge_break(g,out)==0);
    free(a);free(b);free(g);puts("GEOMETRY-UNIT: shifts, abstention, pairing, gap, flush PASS");return 0;
}
