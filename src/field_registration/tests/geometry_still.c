/* Entry 39: exact SAD, unit/frame ownership, confidence removal and authority. */
#include "../geometry_engine.c"
#include <assert.h>
#include <stdio.h>
static uint8_t y[GE_PIXELS],z[GE_PIXELS],b[GE_PIXELS];
static void randomize(void) {
    unsigned rng=71;
    for(unsigned i=0;i<GE_PIXELS;i++){rng=rng*1664525u+1013904223u;y[i]=(uint8_t)(rng>>24);}
}
static void motion(void) {
    randomize();
    for(int field=0;field<2;field++)for(int s=-5;s<=5;s++) {
        memcpy(z,y,sizeof z);int off=19+263*field;
        for(int r=40;r<220;r++)memcpy(z+(off+r+s)*720+40,y+(off+r)*720+40,640);
        ge_vertical_motion v=ge_motion_measure(z,y,field);
        assert(v.known && v.shift==s && v.error==0 && v.second_error>0);
    }
    memset(z,7,sizeof z);ge_vertical_motion v=ge_motion_measure(z,z,0);
    assert(v.shift==0 && v.error==0 && v.second_error==0); /* exact eleven-way tie */
    for(int reverse=0;reverse<2;reverse++) {
        geometry_engine g;ge_decision o[2];ge_init(&g,reverse,0);
        ge_push(&g,y,100,0,o);assert(!g.previous.vertical[0].known);
        unsigned n=ge_push(&g,y,101,0,o);assert(n==1);
        assert(o[0].vertical[0].known && o[0].vertical[1].known==!reverse);
        assert(o[0].picture_motion==(reverse?GE_PICTURE_UNKNOWN:GE_PICTURE_STILL));
        ge_push(&g,y,102,0,o);assert(o[0].picture_motion==GE_PICTURE_STILL);
        ge_push(&g,y,103,1,o);assert(o[0].picture_motion==GE_PICTURE_UNKNOWN);
        ge_push(&g,y,105,0,o);assert(!g.previous.vertical[0].known);
        ge_break(&g,o);ge_push(&g,y,106,0,o);assert(!g.previous.vertical[0].known);
    }
}
static void rigid_motion(void) {
    randomize();
    const int shifts[][2]={{0,2},{0,-3},{-8,-5},{8,5},{3,2}};
    for(int k=0;k<2;k++)for(unsigned i=0;i<sizeof shifts/sizeof *shifts;i++) {
        int dx=shifts[i][0],dy=shifts[i][1],off=19+263*k;
        memset(z,0,sizeof z); /* no second zero-SAD unshifted copy on even columns */
        for(int r=40;r<220;r++)for(int x=40;x<680;x+=2)
            z[(off+r+dy)*720+x+dx]=y[(off+r)*720+x];
        ge_rigid_motion q=ge_rigid_measure(z,y,k);
        assert(q.known && q.dx==dx && q.dy==dy && q.error==0 && q.far_error>0 && isinf(q.clarity));
        assert(rigid_vertical(&q)==(dx==0));
    }
    memset(z,7,sizeof z);ge_rigid_motion q=ge_rigid_measure(z,z,0);
    assert(q.dx==-8 && q.dy==-5 && q.error==0 && q.far_error==0 && q.clarity==1);
    q=(ge_rigid_motion){.known=1,.dy=2,.clarity=1.3};assert(rigid_vertical(&q));
    q.clarity=nextafter(1.3,0);assert(!rigid_vertical(&q));
    q.clarity=2;q.dy=1;assert(!rigid_vertical(&q));
    q.dy=-2;q.known=0;assert(!rigid_vertical(&q));
    memcpy(z,y,sizeof z);
    for(int k=0;k<2;k++)for(int r=40;r<220;r++)
        memcpy(z+(19+263*k+r+(k?-3:2))*720+40,y+(19+263*k+r)*720+40,640);
    for(int reverse=0;reverse<2;reverse++) {
        geometry_engine g;ge_decision o[2];ge_init(&g,reverse,0);
        ge_push(&g,y,100,0,o);assert(!g.previous.rigid[0].known);
        ge_push(&g,z,101,0,o);
        assert(o[0].rigid[0].known && o[0].rigid[0].dy==2);
        assert(o[0].rigid[1].known==!reverse);
        ge_push(&g,y,102,0,o);
        assert(o[0].rigid[0].dy==-2 && o[0].rigid[1].dy==(reverse?-3:3));
        ge_push(&g,z,103,1,o);assert(!o[0].rigid[0].known);
        ge_push(&g,y,105,0,o);assert(!g.previous.rigid[0].known);
    }
}
static void blankspots(void) {
    memset(y,200,sizeof y);memset(b,200,sizeof b);
    ge_features t={0},f={0};t.first[0]=25;f.first[1]=288;f.blank[1]=1;
    for(int x=40;x<680;x++)y[21*720+x]=b[284*720+x]=20+(x%2)*60;
    {
        geometry_engine g;ge_init(&g,0,1);
        ge_decision o={.rejection={.basin=1,.floor_lo=0,.floor_hi=0}};
        vote_anchor(&g,&o,&t,&f,y,b);
        assert(!o.vote_confident);
        assert(!o.vote_blankspot_pass && o.vote_blankspot_line==286);
    }
    b[282*720+40]=3;b[283*720+679]=3; /* inclusive, first/last body samples */
    geometry_engine g;ge_init(&g,1,1);
    ge_decision o={.rejection={.basin=1,.floor_lo=0,.floor_hi=0}};
    vote_anchor(&g,&o,&t,&f,y,b);assert(o.vote_blankspot_pass && o.vote_confident);
    b[283*720+679]=4;b[283*720+680]=1; /* outside body cannot rescue */
    vote_anchor(&g,&o,&t,&f,y,b);assert(!o.vote_confident && o.vote_blankspot_line==287);
    f.first[1]=286;t.first[0]=23;
    for(int x=40;x<680;x++)y[19*720+x]=b[282*720+x]=20+(x%2)*60;
    vote_anchor(&g,&o,&t,&f,y,b);assert(o.vote_confident && o.vote_blankspot_pass);
    o.rejection.basin=0;vote_anchor(&g,&o,&t,&f,y,b);assert(!o.vote_confident);
}
static void authority(void) {
    randomize();memset(b,0,sizeof b);
    for(int r=30;r<=240;r++)for(int x=24;x<696;x++)
        b[(r+259)*720+x]=(y[(r-4)*720+x]+y[(r-3)*720+x])/2;
    ge_comb_result c=ge_comb(y,b);assert(c.shift==0 && c.decided);
    ge_features t={0},f={0};t.first[0]=24;f.first[1]=286; /* census -1 */
    t.last[0]=260;f.last[1]=522;t.bottom[0]=260;f.bottom[1]=522;
    t.motion[0]=f.motion[1]=GE_NOTHING; /* census agrees at both edges, no trigger */
    t.vertical[0].known=f.vertical[1].known=1;
    for(int audit=0;audit<2;audit++)for(int state=0;state<3;state++) {
        geometry_engine g;ge_init(&g,0,audit);
        t.vertical[0].known=state!=0;t.vertical[0].shift=state==2?1:0;
        ge_decision o=frame(&g,y,b,&t,&f,100,100);
        if(state==1)assert(o.still_trigger && (o.triggers&GE_STILL) && o.published_d==0 && o.held==1);
        else assert(!o.still_trigger && o.published_d==-1 && !o.held);
        t.motion[0]=GE_UNKNOWN;ge_init(&g,0,audit);o=frame(&g,y,b,&t,&f,100,100);
        assert(o.comb_ran && !o.comb_suppressed && o.published_d==0 && o.held==1);
        t.motion[0]=GE_NOTHING;
    }
    /* Even an undecided, otherwise-refusing verdict is blocked on motion. */
    geometry_engine g={.held=1,.basis_valid=1};
    ge_decision o={.comb_ran=1,.comb_suppressed=1,.comb={.shift=0,.margin=1}};
    for(int i=0;i<11;i++)o.comb.energies[i]=10;
    o.comb.energies[5]=o.comb.energies[6]=1;
    int d=-1,d2=2;reject_placement(&g,&o,&d,&d2);
    assert(!o.rejected && o.rejection.basin && o.rejection.ratio==10 && g.held==1 && g.basis_valid);
    /* Both frame-owned 2-D results must pass; vertical-only magnitude cannot rescue. */
    t.motion[0]=GE_UNKNOWN;t.vertical[0].known=f.vertical[1].known=1;
    t.vertical[0].shift=f.vertical[1].shift=2;
    for(int state=0;state<7;state++) {
        t.rigid[0]=f.rigid[1]=(ge_rigid_motion){.known=1,.dy=2,.clarity=1.3};
        if(state==1)t.rigid[0].known=0;
        if(state==2)f.rigid[1].known=0;
        if(state==3)t.rigid[0].dx=1;
        if(state==4)f.rigid[1].dy=1;
        if(state==5)f.rigid[1].clarity=nextafter(1.3,0);
        if(state==6)t.vertical[0].known=0;
        ge_init(&g,0,1);ge_decision d=frame(&g,y,b,&t,&f,101,100);
        assert(d.comb_suppressed==(state==0));
        if(!state)assert(d.published_d==-1 && !d.held && !d.rejected);
        else assert(d.published_d==0 && d.held==1);
    }
}
int main(void){motion();rigid_motion();blankspots();authority();puts("GEOMETRY-STILL PASS");}
