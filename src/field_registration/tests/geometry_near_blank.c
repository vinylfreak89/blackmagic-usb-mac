/* Synthetic thresholds test the mechanism, not a proposed tape setting. */
#include "../geometry_engine.c"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

static void raster(uint8_t *y,int t1,int t2,int hi) {
    memset(y,1,GE_PIXELS);
    for(int k=0;k<2;k++) {
        int top=(k?t2:t1)-4;
        if(top>=0)for(int r=top;r<=top+1;r++)for(int x=40;x<680;x++)
            y[r*720+x]=(x&1)?hi:hi-6;
        for(int r=247+263*k;r<=256+263*k;r++)for(int x=40;x<680;x++)
            y[r*720+x]=(x&1)?90:110;
    }
}
static ge_features features(int top,int bottom) {
    ge_features f={0};
    f.first[0]=f.interpreted_first[0]=top;
    f.first[1]=f.interpreted_first[1]=286;
    f.last[0]=f.bottom[0]=bottom;f.last[1]=f.bottom[1]=523;
    f.blank[0]=f.blank[1]=1;f.top_distance[0]=6;
    for(int k=0;k<2;k++)for(int j=0;j<12;j++)for(int x=0;x<672;x++)
        f.profile[k][j][x]=(251+263*k+j<=f.bottom[k])?800:8;
    return f;
}
int main(void) {
    uint8_t *y=malloc(GE_PIXELS);geometry_engine *g=malloc(ge_size());assert(y&&g);
    assert(ge_top_near_blank==-1);
    for(int reverse=0;reverse<2;reverse++)for(int audit=0;audit<2;audit++) {
        ge_decision out[2];ge_init(g,reverse,audit);ge_top_near_blank=12;
        assert(!ge_current_features(g));
        raster(y,23,286,13);ge_push(g,y,100,0,out);
        for(int c=101;c<=103;c++) {
            raster(y,24,287,13);unsigned n=ge_push(g,y,c,0,out);
            const ge_features *f=ge_current_features(g);
            ge_features measured;ge_measure(y,&measured);
            assert(!memcmp(f->first,measured.first,sizeof f->first));
            assert(!memcmp(f->last,measured.last,sizeof f->last));
            assert(!memcmp(f->bottom,measured.bottom,sizeof f->bottom));
            assert(!memcmp(f->profile,measured.profile,sizeof f->profile));
            assert(!memcmp(f->blank,measured.blank,sizeof f->blank));
            assert(!memcmp(f->hblank_level,measured.hblank_level,sizeof f->hblank_level));
            assert(!memcmp(f->hblank_cols,measured.hblank_cols,sizeof f->hblank_cols));
            assert(f->first[0]==24 && f->first[1]==287);
            assert(f->interpreted_first[0]==23 && f->interpreted_first[1]==286);
            assert(f->top_distance[0]==12 && f->top_distance[1]==12);
            assert(f->top_ignored[0] && f->top_ignored[1]);
            assert(f->motion[0]==GE_TOP_ONLY && f->motion[1]==GE_TOP_ONLY);
            assert(n==1 && out[0].counter==(uint64_t)(c-reverse));
            assert(out[0].first[0]==24 && out[0].first[1]==(reverse&&c==101?286:287));
            assert(out[0].interpreted_first[0]==23 && out[0].interpreted_first[1]==286);
            assert(out[0].top_ignored[0] && out[0].top_ignored[1]==!(reverse&&c==101));
        }
        /* Bright top-only moves are not suppressed; threshold is inclusive. */
        raster(y,24,287,14);ge_push(g,y,104,0,out);
        assert(!g->current.top_ignored[0] && g->current.interpreted_first[0]==24);
        raster(y,25,288,13);ge_top_near_blank=nextafter(12,0);ge_push(g,y,105,0,out);
        assert(!g->current.top_ignored[0] && g->current.interpreted_first[0]==25);
        ge_top_near_blank=12;
        /* Resets, gaps and explicit breaks do not carry an interpreted top. */
        raster(y,26,289,13);ge_push(g,y,106,1,out);
        assert(!g->current.top_ignored[0] && g->current.interpreted_first[0]==26);
        raster(y,27,290,13);ge_push(g,y,108,0,out);
        assert(!g->current.top_ignored[0] && g->current.interpreted_first[0]==27);
        ge_break(g,out);assert(!ge_current_features(g));
        raster(y,28,291,13);ge_push(g,y,109,0,out);
        assert(!g->current.top_ignored[0] && g->current.interpreted_first[0]==28);
        /* Missing top stays missing; after it there is no comparison basis. */
        raster(y,0,0,13);ge_push(g,y,110,0,out);
        assert(!g->current.first[0] && !g->current.interpreted_first[0]);
        assert(isnan(g->current.top_distance[0]) && g->current.motion[0]==GE_UNKNOWN);
        raster(y,24,287,13);ge_push(g,y,111,0,out);
        assert(!g->current.top_ignored[0] && g->current.interpreted_first[0]==24);
        /* Default off remains off even with a negative measured distance. */
        ge_top_near_blank=-1;ge_features a=features(23,260),b=features(24,260);
        b.top_distance[0]=-10;b.motion[0]=classify(&a,&b,0);interpret_top(&a,&b,0);
        assert(b.motion[0]==GE_TOP_ONLY && !b.top_ignored[0] && b.interpreted_first[0]==24);
    }
    ge_top_near_blank=6;
    /* Same-unit genuine bottom-only and tandem moves are never rejected.
     * Feedback is allowed to change the NEXT unit's class and scheduling. */
    for(int top=23;top<=24;top++) {
        ge_features a=features(23,260),b=features(top,261);
        b.motion[0]=classify(&a,&b,0);interpret_top(&a,&b,0);
        assert(b.motion[0]==(top==23?GE_BOTTOM_ONLY:GE_VALID_MOVE));
        assert(!b.top_ignored[0] && b.interpreted_first[0]==top);
    }
    ge_features a=features(23,260),b=features(24,260),c=features(24,261);
    b.motion[0]=classify(&a,&b,0);
    ge_features measured_b=b;interpret_top(&a,&b,0);
    assert(b.top_ignored[0] && b.first[0]==24 && b.interpreted_first[0]==23);
    assert(classify(&measured_b,&c,0)==GE_BOTTOM_ONLY && classify(&b,&c,0)==GE_VALID_MOVE);
    memset(y,1,GE_PIXELS);
    ge_init(g,0,0);c.motion[0]=classify(&measured_b,&c,0);c.motion[1]=GE_NOTHING;
    ge_decision old=frame(g,y,y,&c,&c,102,102);
    ge_init(g,0,0);c.motion[0]=classify(&b,&c,0);
    ge_decision now=frame(g,y,y,&c,&c,102,102);
    assert(old.comb_ran && !now.comb_ran);
    printf("GEOMETRY-NEAR-BLANK PASS: predicate, inclusive cutoff, interpreted run, bright/absent tops, reset/gap, both pairings/audit; unit 102 bottom only -> valid move, comb 1 -> 0\n");
    free(y);free(g);return 0;
}
