/* Publication-only trajectory: synthetic decisions, no tape-derived thresholds. */
#include "../geometry_engine.c"
#include <assert.h>
#include <stdio.h>

static ge_decision step(geometry_engine *g,int d1,int d2,int m1,int m2,int known) {
    ge_decision o={.has_frame=1,.frame_d1=d1,.frame_d2=d2,.d1=d1,.d2=d2,
        .published_d=d2-d1,.vote_anchor=d2,.vote_engine_anchor=d2+1,
        .anchor_source=GE_SOURCE_VOTE,.relative_source=GE_SOURCE_COMB,
        .comb_ran=1,.held=2,.triggers=GE_T1};
    o.vertical[0]=(ge_vertical_motion){.known=known,.shift=m1};
    o.vertical[1]=(ge_vertical_motion){.known=known,.shift=m2};
    o.comb=(ge_comb_result){.shift=d2-d1,.decided=1,.margin=3};
    ge_decision before=o;int held=g->held,last=g->last_d,last2=g->last_d2,anchor=g->vote_anchor;
    field2_jitter(g,&o);
    assert(o.frame_d2-o.frame_d1==before.published_d);
    assert(o.d1==o.frame_d1 && o.d2==o.frame_d2);
    assert(g->held==held && g->last_d==last && g->last_d2==last2 && g->vote_anchor==anchor);
    ge_decision normalized=o;
    normalized.frame_d1=normalized.d1=d1;normalized.frame_d2=normalized.d2=d2;
    normalized.anchor_source=before.anchor_source;
    assert(!memcmp(&before,&normalized,sizeof before));
    return o;
}
static void pair(ge_decision o,int a,int b) {assert(o.frame_d1==a && o.frame_d2==b);}
int main(void) {
    geometry_engine *g=malloc(ge_size());assert(g);
    ge_config cfg=ge_default_config();ge_init(g,0,&cfg);
    pair(step(g,0,0,0,0,1),0,0);pair(step(g,-1,0,0,1,1),-1,0);
    assert(!g->jitter_known && !g->jitter_compensation); /* off is inert */
    cfg.field2_jitter=1;ge_init(g,0,&cfg);
    pair(step(g,0,0,0,1,1),0,0); /* no previous frame */
    ge_decision o=step(g,-1,0,0,1,1);pair(o,0,1);
    assert(o.anchor_source==GE_SOURCE_FIELD2_JITTER && o.vote_anchor==0);
    pair(step(g,-1,0,0,0,1),0,1); /* hold */
    pair(step(g,-2,0,0,1,1),0,2); /* another matching step */
    pair(step(g,-1,0,0,-1,1),0,1); /* partial return with relative change */
    pair(step(g,0,0,0,-1,1),0,0); /* complete return */
    assert(!g->jitter_compensation);
    pair(step(g,2,0,0,-2,1),0,-2); /* both signs */
    pair(step(g,2,0,0,1,1),0,-2); /* partial motion alone is not a new decision */
    pair(step(g,2,0,0,2,1),2,0); /* inverse motion without normal change */
    pair(step(g,1,0,0,1,1),2,1);
    pair(step(g,3,0,1,0,1),3,0); /* different field/reason clears */
    pair(step(g,2,0,0,1,1),3,1);
    pair(step(g,3,1,0,1,1),3,1); /* anchor change clears */
    assert(!g->jitter_compensation);
    pair(step(g,2,1,0,2,1),2,1); /* wrong magnitude */
    pair(step(g,1,1,1,1,1),1,1); /* both fields move */
    pair(step(g,0,1,0,1,0),0,1); /* unknown */
    pair(step(g,-1,1,0,1,1),0,2);
    reset_frame_state(g);pair(step(g,-2,1,0,1,1),-2,1);
    pair(step(g,-3,1,0,1,1),-2,2);
    ge_decision out[2];ge_break(g,out);assert(!g->jitter_known && !g->jitter_compensation);
    pair(step(g,0,0,0,0,1),0,0);pair(step(g,-1,0,0,1,1),0,1);
    ge_set_pairing(g,1);assert(!g->jitter_known && !g->jitter_compensation);
    pair(step(g,0,0,0,1,1),0,0);pair(step(g,-1,0,0,1,1),0,1);
    free(g);puts("GEOMETRY-JITTER PASS: off identity, both signs, hold/return, other moves, unknowns, resets, unchanged relative/vote/comb state");
}
