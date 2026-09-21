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
    // Horizontal reference: column 1 equals the allowed median and is kept;
    // column 2 exceeds it and stops selection. Each field is independent.
    memset(a,1,GE_PIXELS);
    for(int k=0;k<2;k++)for(int r=18+263*k;r<=261+263*k;r++) {
        a[r*720]=8;a[r*720+1]=9;a[r*720+2]=10;
    }
    for(int x=40;x<680;x++) {
        a[19*720+x]=a[20*720+x]=(x&1)?60:80;
        a[282*720+x]=(x&1)?3:9; // hi == derived level: rejected
        a[283*720+x]=a[284*720+x]=(x&1)?10:20;
    }
    for(int x=40;x<240;x++)a[258*720+x]=8; // 31.25% lit, BELOW derived level
    ge_measure(a,&f);
    assert(f.hblank_cols[0]==2 && f.hblank_cols[1]==2);
    assert(f.hblank_level[0]==9 && f.hblank_level[1]==9);
    assert(f.blank[0]==1 && f.blank[1]==1);
    assert(f.first[0]==23 && f.first[1]==287 && f.last[0]==262);
    // Reversed logging carries the source unit's own provenance, not its partner's.
    ge_init(g,1,0);assert(ge_push(g,a,20,1,out)==0);
    memcpy(b,a,GE_PIXELS);
    for(int r=18;r<=261;r++){b[r*720]=18;b[r*720+1]=19;b[r*720+2]=20;}
    assert(ge_push(g,b,21,0,out)==1);
    assert(out[0].counter==20 && out[0].hblank_level[0]==9 && out[0].hblank_cols[0]==2);
    assert(ge_break(g,out)==1 && out[0].counter==21 && out[0].hblank_level[0]==19 && out[0].hblank_cols[0]==2);
    memset(a,1,GE_PIXELS);ge_measure(a,&f);
    assert(f.hblank_cols[0]==24 && f.hblank_level[0]==1);
    for(int r=18;r<=261;r++)a[r*720+1]=3;
    ge_measure(a,&f);assert(f.hblank_cols[0]==1 && f.hblank_level[0]==1);
    free(a);free(b);free(g);puts("GEOMETRY-UNIT: shifts, abstention, pairing, gap, flush PASS");return 0;
}
