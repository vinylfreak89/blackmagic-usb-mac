/* White-box state-transition controls: real comb, explicit census features.
 * Including the implementation exposes no production test API. */
#include "../geometry_engine.c"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

static ge_features features(int top) {
    ge_features f={0};
    f.first[0]=top;f.first[1]=286;
    f.last[0]=260;f.last[1]=523;f.bottom[0]=260;f.bottom[1]=523;
    f.motion[0]=f.motion[1]=GE_NOTHING;
    return f;
}
/* This test supplies census features directly, without top interpretation. */
static ge_decision measured_frame(geometry_engine *g,const uint8_t *ty,const uint8_t *by,
                                 ge_features *t,ge_features *b,uint64_t tc,uint64_t bc) {
    memcpy(t->interpreted_first,t->first,sizeof t->first);
    memcpy(b->interpreted_first,b->first,sizeof b->first);
    return frame(g,ty,by,t,b,tc,bc);
}
int main(void) {
    uint8_t *top=malloc(GE_PIXELS),*bottom=calloc(GE_PIXELS,1),*flat=calloc(GE_PIXELS,1);
    geometry_engine *g=malloc(ge_size());assert(top&&bottom&&flat&&g);
    unsigned rng=71;
    for(unsigned i=0;i<GE_PIXELS;i++){rng=rng*1664525u+1013904223u;top[i]=(uint8_t)(rng>>24);}
    for(int r=30;r<=240;r++)for(int x=24;x<696;x++)
        bottom[(r+259)*720+x]=(top[(r-4)*720+x]+top[(r-3)*720+x])/2;
    assert(ge_comb(top,bottom).shift==0 && ge_comb(top,bottom).decided);
    for(int audit=0;audit<2;audit++)for(int reverse=0;reverse<2;reverse++) {
        ge_init(g,reverse,audit);
        ge_features t=features(24),b=features(24);
        t.motion[0]=GE_UNKNOWN; // initial measurement derives +1 against st=-1
        ge_decision o=measured_frame(g,top,bottom,&t,&b,100+reverse,100);
        assert(o.held==1 && o.published_d==0 && g->basis_valid);
        t.motion[0]=GE_NOTHING;
        o=measured_frame(g,top,bottom,&t,&b,101+reverse,101); // confirmation
        assert(o.held==1 && !g->provisional);
        o=measured_frame(g,top,bottom,&t,&b,102+reverse,102);
        assert(!o.comb_ran && o.published_d==0 && o.held==1);
        // Top moves even though both motion classes say valid move. A tied
        // comb cannot restore +1; the new census st=0 is published instead.
        t.first[0]=23;t.motion[0]=b.motion[1]=GE_VALID_MOVE;
        o=measured_frame(g,flat,flat,&t,&b,103+reverse,103);
        assert((o.triggers&GE_BASIS_CHANGED) && o.comb_ran && !o.comb.decided);
        assert(o.held==0 && o.published_d==0 && !g->provisional && !g->basis_valid);
        o=measured_frame(g,top,bottom,&t,&b,104+reverse,104);
        assert(!o.comb_ran && o.published_d==0); // no audit-only adoption
        // A bottom-field top change invalidates independently, including when
        // both tops translate together and their difference is unchanged.
        g->held=1;g->provisional=1;g->basis_valid=1;
        g->basis_first[0]=23;g->basis_first[1]=286;
        t.first[0]=24;b.first[1]=287;
        o=measured_frame(g,flat,flat,&t,&b,105+reverse,105);
        assert((o.triggers&GE_BASIS_CHANGED) && !o.held && !g->provisional);
        g->held=1;g->basis_valid=1;
        g->basis_first[0]=24;g->basis_first[1]=287;b.first[1]=288;
        o=measured_frame(g,flat,flat,&t,&b,105+reverse,105);
        assert((o.triggers&GE_BASIS_CHANGED) && !o.held && o.published_d==1);
        b.first[1]=287;
        // Decided re-derivation records the new basis. Losing a measured top
        // clears it, while existing missing-placement fallback is preserved.
        t.motion[0]=GE_UNKNOWN;
        o=measured_frame(g,top,bottom,&t,&b,106+reverse,106);
        assert(o.comb.decided && g->basis_valid && g->basis_first[1]==287);
        int previous_d1=o.frame_d1,previous_d2=o.frame_d2;
        b.first[1]=0;
        o=measured_frame(g,flat,flat,&t,&b,107+reverse,107);
        assert((o.triggers&GE_BASIS_CHANGED) && (o.triggers&GE_UNMEASURABLE));
        assert(!g->basis_valid && !g->held);
        assert(o.frame_d1==previous_d1 && o.frame_d2==previous_d2);
        t.first[0]=0;
        o=measured_frame(g,flat,flat,&t,&b,108+reverse,108);
        assert(!o.comb.decided && o.frame_d1==previous_d1 && o.frame_d2==previous_d2);
        g->basis_valid=1;g->basis_first[0]=24;g->held=1;
        ge_decision out[2];ge_break(g,out);
        assert(!g->basis_valid && !g->held && !g->basis_first[0]);
    }
    free(top);free(bottom);free(flat);free(g);
    puts("GEOMETRY-BASIS: top changes, abstention, re-derivation, missing top, reset, audit invariance PASS");
    return 0;
}
