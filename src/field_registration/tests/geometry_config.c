/* Instance isolation, initialization validation, and bounded configuration. */
#include "../geometry_engine.c"
#include <assert.h>
#include <pthread.h>
#include <stdio.h>

static uint8_t y[GE_PIXELS];
typedef struct { geometry_engine *g; int first; } task;
static void *run(void *opaque) {
    task *t=opaque;ge_decision out[2];
    for(unsigned i=0;i<8;i++) {
        assert(ge_push(t->g,y,100+i,i==0,out)==1);
        assert(out[0].first[0]==t->first);
    }
    return NULL;
}
int main(void) {
    ge_config c=ge_default_config();assert(ge_config_valid(&c));
    assert(c.wave_bar==.45 && c.wave_clamp==5 && c.comb_reject==2 && c.comb_basin_factor==1.5);
    assert(c.vote_window==30 && c.vote_pair_min==.6 && c.bottom_flat_margin==3);
    assert(c.blankspot_tolerance==2 && c.rigid_min==2 && c.rigid_clarity==1.3);
    geometry_engine *a=malloc(ge_size()),*b=malloc(ge_size());assert(a && b);
    assert(!ge_init(a,0,0,NULL));c.wave_bar=2;
    assert(!ge_init(b,0,0,&c));c.wave_bar=-2;
    assert(ge_get_config(a)->wave_bar==.45 && ge_get_config(b)->wave_bar==2);
    memset(y,1,sizeof y);
    for(int k=0;k<2;k++)for(int r=19;r<=20;r++)for(int x=40;x<680;x++)
        y[(r+263*k)*720+x]=20+(x%2)*60;
    task ta={a,23},tb={b,0};pthread_t t1,t2;
    assert(!pthread_create(&t1,NULL,run,&ta));assert(!pthread_create(&t2,NULL,run,&tb));
    assert(!pthread_join(t1,NULL));assert(!pthread_join(t2,NULL));
    ge_decision out[2];ge_break(b,out);ge_set_pairing(b,1);
    assert(ge_get_config(b)->wave_bar==2 && b->reverse && !b->vote_count);
    ge_config saved=*ge_get_config(a),bad=saved;bad.vote_window=0;
    assert(ge_init(a,0,0,&bad)==-1 && !memcmp(ge_get_config(a),&saved,sizeof saved));
    bad=saved;bad.vote_window=GE_VOTE_CAPACITY+1;assert(!ge_config_valid(&bad));
    bad=saved;bad.wave_bar=NAN;assert(!ge_config_valid(&bad));
    bad=saved;bad.comb_basin_factor=.9;assert(!ge_config_valid(&bad));
    bad=saved;bad.blankspot_tolerance=-1;assert(!ge_config_valid(&bad));
    bad=saved;bad.rigid_min=0;assert(!ge_config_valid(&bad));
    /* New numeric controls affect their instrument, not another instance. */
    ge_comb_result comb={.shift=0,.margin=1};
    for(int i=0;i<11;i++)comb.energies[i]=10;
    comb.energies[5]=1;comb.energies[6]=1.6;
    c=saved;c.comb_basin_factor=2;
    assert(ge_comb_examine(&comb,0,&saved).floor_hi==0);
    assert(ge_comb_examine(&comb,0,&c).floor_hi==1);
    ge_rigid_motion motion={.known=1,.dy=2,.clarity=1.3};
    assert(rigid_vertical(&motion,&saved));c.rigid_min=3;
    assert(!rigid_vertical(&motion,&c));
    c=saved;c.vote_window=2;assert(!ge_init(a,0,0,&c));
    ge_features top={0},bottom={0};top.first[0]=23;bottom.first[1]=286;
    for(int i=0;i<4;i++) {
        ge_decision d={.rejection={.basin=1,.floor_lo=0,.floor_hi=0}};
        vote_anchor(a,&d,&top,&bottom,y,y);assert(d.vote_confident && d.vote_count==(i?2:1));
    }
    free(a);free(b);puts("GEOMETRY-CONFIG PASS: defaults, owned copy, concurrent isolation, reset, validation, tunables");
}
