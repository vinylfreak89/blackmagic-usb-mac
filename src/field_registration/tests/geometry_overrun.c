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
        /* Keep the comb's lowest sampled bottom row identical across the
         * 23->24 onset: row 284 is inside shift -5's search aperture. */
        if(top && top<=24)for(int x=40;x<680;x++)y[(21+263*k)*720+x]=(x&1)?80:100;
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
        {23,260,23,259,0,0},{24,262,23,259,0,0},
        {20,260,21,260,0,0},{20,260,22,260,1,1},
        {0,260,24,260,0,0},{23,0,24,260,0,0},
        {23,260,0,260,0,0},{23,260,24,0,0,0}};
    for(unsigned i=0;i<sizeof cases/sizeof *cases;i++)for(int k=0;k<2;k++) {
        a=features(cases[i][0],cases[i][1]);b=features(cases[i][2],cases[i][3]);
        ge_features original=b;gate_top(&a,&b,k,1);
        assert(b.top_overrun_veto[k]==cases[i][4] && b.top_ignored[k]==cases[i][5]);
        assert(b.interpreted_first[k]==(cases[i][4]?a.interpreted_first[k]:original.first[k]));
        assert(!memcmp(b.first,original.first,sizeof b.first) && !memcmp(b.last,original.last,sizeof b.last));
    }
    for(int k=0;k<2;k++) {
        a=features(23,260);b=features(24,260);gate_top(&a,&b,k,0);
        assert(!b.top_overrun_veto[k] && b.overrun_terms[k]==(GE_OV_ALL^GE_OV_SAME_COMB));
        b=features(24,260);b.bottom[k]++;gate_top(&a,&b,k,1);
        assert(!b.top_overrun_veto[k] && b.overrun_terms[k]==(GE_OV_ALL^GE_OV_BOTTOM_STILL));
        b=features(23,259);gate_top(&a,&b,k,1);
        assert(!b.top_overrun_veto[k] && b.overrun_terms[k]==(GE_OV_ALL^GE_OV_TOP_MOVED));
        b=features(24,260);b.bottom[k]=0;gate_top(&a,&b,k,1);
        assert(!b.top_overrun_veto[k] && !(b.overrun_terms[k]&GE_OV_HISTORY));
    }
    uint8_t *y=malloc(GE_PIXELS),*bottom=calloc(GE_PIXELS,1);
    geometry_engine *g=malloc(ge_size());assert(y&&bottom&&g);ge_decision out[2];
    for(int reverse=0;reverse<2;reverse++)for(int audit=0;audit<2;audit++) {
        ge_init(g,reverse,audit);raster(y,23);ge_push(g,y,100,0,out);
        ge_push(g,y,101,0,out);assert(!out[0].top_overrun_veto[0] && !out[0].top_overrun_veto[1]);
        for(int c=102;c<=104;c++) {
            raster(y,24);ge_push(g,y,c,0,out);const ge_features *f=ge_current_features(g);
            assert(f->first[0]==24 && f->interpreted_first[0]==23 && f->top_overrun_veto[0]);
            assert(f->first[1]==287 && f->interpreted_first[1]==(reverse?287:286));
            assert(f->top_overrun_veto[1]==!reverse); /* no future-frame consult */
            assert(out[0].first[0]==24 && out[0].interpreted_first[0]==23 && out[0].top_overrun_veto[0]);
            assert(out[0].top_overrun_veto[1]==!(reverse&&c==102));
            const ge_features *done=ge_completed_features(g);assert(done);
            assert(done->interpreted_first[1]==286);
        }
        /* No stale interpretation through explicit reset, counter gap, no top. */
        raster(y,25);ge_push(g,y,105,1,out);assert(g->current.interpreted_first[0]==25);
        assert(!out[0].prev_comb_known && !out[0].top_overrun_veto[0] && !out[0].top_overrun_veto[1]);
        raster(y,26);ge_push(g,y,107,0,out);assert(g->current.interpreted_first[0]==26);
        raster(y,0);ge_push(g,y,108,0,out);assert(!g->current.interpreted_first[0] && !g->current.top_overrun_veto[0]);
        raster(y,27);ge_push(g,y,109,0,out);assert(g->current.interpreted_first[0]==27);
        ge_break(g,out);assert(!g->frame_previous_valid);
    }
    /* Equal winners are sufficient even when both searches abstain. */
    memset(y,1,GE_PIXELS);memset(bottom,1,GE_PIXELS);ge_init(g,0,0);
    a=features(23,261);b=features(24,261);g->frame_previous=a;g->frame_previous_valid=1;
    g->previous_comb=ge_comb(y,bottom);assert(g->previous_comb.margin==1);
    ge_decision low=gated_frame(g,y,bottom,&b,&b,101,101);
    assert(!low.comb.decided && low.top_overrun_veto[0] && low.top_overrun_veto[1]);
    /* The comb can override census placement AFTER a refusal. Synthetic shift
     * -1 is exact/decided; rejecting top 28 to 23 still publishes top 24. */
    unsigned rng=71;
    for(unsigned i=0;i<GE_PIXELS;i++){rng=rng*1664525u+1013904223u;y[i]=(uint8_t)(rng>>24);}
    for(int r=30;r<=240;r++)for(int x=24;x<696;x++)
        bottom[(r+258)*720+x]=(y[(r-4)*720+x]+y[(r-3)*720+x])/2;
    assert(ge_comb(y,bottom).shift==-1 && ge_comb(y,bottom).decided);
    a=features(23,261);b=features(28,261);ge_init(g,0,0);
    g->frame_previous=a;g->frame_previous_valid=1;g->previous_comb=ge_comb(y,bottom);
    ge_decision d=gated_frame(g,y,bottom,&b,&a,101,100);
    assert(d.comb_ran && d.comb.decided && d.frame_d1==1 && d.frame_d2==0);
    assert(d.first[0]==28 && d.interpreted_first[0]==23 && d.top_overrun_veto[0]);
    free(y);free(bottom);free(g);
    puts("GEOMETRY-OVERRUN PASS: independent comb/top/bottom terms, geometry, missing/reset/gap, interpreted history, frame-owned reverse timing, low-confidence equality, comb authority");
    return 0;
}
