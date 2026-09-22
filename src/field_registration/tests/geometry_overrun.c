/* Threshold-free census policy, not a final-published-crop veto. */
#include "../geometry_engine.c"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
static ge_features features(int top,int last) {
    ge_features f={0};
    for(int k=0;k<2;k++) {
        f.first[k]=f.interpreted_first[k]=top?top+263*k:0;
        f.last[k]=last?last+263*k:0;f.bottom[k]=260+263*k;
        f.motion[k]=GE_NOTHING;
    }
    return f;
}
static void raster(uint8_t *y,int top) {
    memset(y,1,GE_PIXELS);
    for(int k=0;k<2;k++) {
        if(top)for(int r=top-4+263*k;r<=top-3+263*k;r++)for(int x=40;x<680;x++)
            y[r*720+x]=(x&1)?80:100;
        for(int r=247+263*k;r<=257+263*k;r++)for(int x=40;x<680;x++)
            y[r*720+x]=(x&1)?90:110;
    }
}
int main(void) {
    assert(GE_FIELD_LINES==240 && !ge_top_overrun_veto && ge_top_near_blank==-1);
    ge_features a=features(23,260),b=features(24,260);
    interpret_top(&a,&b,0);assert(b.interpreted_first[0]==24 && !b.top_overrun_veto[0]);
    ge_top_overrun_veto=1;
    /* old top/last, new top/last, predicate, actual substitution */
    const int cases[][6]={{23,260,24,260,1,1},{23,260,24,261,0,0},
        {23,260,23,259,1,0},{24,262,23,259,0,0},
        {20,260,21,260,0,0},{20,260,22,260,1,1},
        {0,260,24,260,0,0},{23,0,24,260,0,0},
        {23,260,0,260,0,0},{23,260,24,0,0,0}};
    for(unsigned i=0;i<sizeof cases/sizeof *cases;i++)for(int k=0;k<2;k++) {
        a=features(cases[i][0],cases[i][1]);b=features(cases[i][2],cases[i][3]);
        ge_features original=b;interpret_top(&a,&b,k);
        assert(b.top_overrun_veto[k]==cases[i][4] && b.top_ignored[k]==cases[i][5]);
        assert(b.interpreted_first[k]==(cases[i][4]?a.interpreted_first[k]:original.first[k]));
        assert(!memcmp(b.first,original.first,sizeof b.first) && !memcmp(b.last,original.last,sizeof b.last));
    }
    uint8_t *y=malloc(GE_PIXELS),*bottom=calloc(GE_PIXELS,1);
    geometry_engine *g=malloc(ge_size());assert(y&&bottom&&g);ge_decision out[2];
    for(int reverse=0;reverse<2;reverse++)for(int audit=0;audit<2;audit++) {
        ge_init(g,reverse,audit);raster(y,23);ge_push(g,y,100,0,out);
        for(int c=101;c<=103;c++) {
            raster(y,24);ge_push(g,y,c,0,out);const ge_features *f=ge_current_features(g);
            assert(f->first[0]==24 && f->interpreted_first[0]==23 && f->top_overrun_veto[0]);
            assert(f->first[1]==287 && f->interpreted_first[1]==286 && f->top_overrun_veto[1]);
            assert(out[0].first[0]==24 && out[0].interpreted_first[0]==23 && out[0].top_overrun_veto[0]);
            assert(out[0].top_overrun_veto[1]==!(reverse&&c==101));
        }
        /* No stale interpretation through explicit reset, counter gap, no top. */
        raster(y,25);ge_push(g,y,104,1,out);assert(g->current.interpreted_first[0]==25);
        raster(y,26);ge_push(g,y,106,0,out);assert(g->current.interpreted_first[0]==26);
        raster(y,0);ge_push(g,y,107,0,out);assert(!g->current.interpreted_first[0] && !g->current.top_overrun_veto[0]);
        raster(y,27);ge_push(g,y,108,0,out);assert(g->current.interpreted_first[0]==27);
    }
    /* The comb can override census placement AFTER a refusal. Synthetic shift
     * -1 is exact/decided; rejecting top 28 to 23 still publishes top 24. */
    unsigned rng=71;
    for(unsigned i=0;i<GE_PIXELS;i++){rng=rng*1664525u+1013904223u;y[i]=(uint8_t)(rng>>24);}
    for(int r=30;r<=240;r++)for(int x=24;x<696;x++)
        bottom[(r+258)*720+x]=(y[(r-4)*720+x]+y[(r-3)*720+x])/2;
    assert(ge_comb(y,bottom).shift==-1 && ge_comb(y,bottom).decided);
    a=features(23,261);b=features(28,261);interpret_top(&a,&b,0);
    assert(b.top_overrun_veto[0] && b.interpreted_first[0]==23);
    b.motion[0]=GE_TOP_ONLY;ge_init(g,0,0);
    ge_decision d=frame(g,y,bottom,&b,&a,101,100);
    assert(d.comb_ran && d.comb.decided && d.frame_d1==1 && d.frame_d2==0);
    assert(d.first[0]==28 && d.interpreted_first[0]==23 && d.top_overrun_veto[0]);
    free(y);free(bottom);free(g);
    puts("GEOMETRY-OVERRUN PASS: 240-line census, both predicate terms, tandem, clipping, no-op, missing/reset/gap, interpreted history, both pairings, comb remains authoritative");
    return 0;
}
