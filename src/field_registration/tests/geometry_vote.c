/* Exact vote and fill boundary tests; captured content is not a fixture. */
#include "../geometry_engine.c"
#include <assert.h>
#include <stdio.h>
static uint8_t y[GE_PIXELS];
static ge_decision input(geometry_engine *g,int top,int confident,int engine) {
    ge_features t={0},b={0};t.first[0]=23+top;b.first[1]=286+top;
    ge_decision o={.frame_d2=engine,.frame_d1=engine-1,.published_d=1};
    o.rejection=(ge_comb_evidence){.basin=confident,.floor_lo=0,.floor_hi=1};
    vote_anchor(g,&o,&t,&b,y,y);return o;
}
static void votes(void) {
    geometry_engine g;ge_init(&g,0,0);ge_anchor_vote=1;
    ge_decision o=input(&g,2,0,4);assert(o.vote_anchor==4 && !o.vote_count);
    o=input(&g,2,0,5);assert(o.vote_anchor==4 && !o.vote_count); /* empty holds */
    o=input(&g,2,1,4);assert(o.vote_anchor==2 && o.vote_winner_count==1);
    o=input(&g,3,1,4);assert(o.vote_anchor==2 && o.vote_count==2); /* current tie */
    o=input(&g,3,1,4);assert(o.vote_anchor==3 && o.vote_winner_count==2);
    o=input(&g,5,0,5);assert(o.vote_anchor==3 && o.vote_count==3 && !o.vote_confident);
    for(int i=0;i<30;i++)o=input(&g,1,1,5);
    assert(o.vote_anchor==1 && o.vote_count==30 && o.vote_winner_count==30);
    assert(o.frame_d2-o.frame_d1==1 && o.vote_engine_anchor==5);
    /* Most recent tied, then first tied in chronological window order. */
    g.vote_count=4;int a[]={2,2,3,3};memcpy(g.vote_values,a,sizeof a);g.vote_anchor=9;
    o=input(&g,0,0,0);assert(o.vote_anchor==3);
    int b[]={2,2,3,3,4};g.vote_count=5;memcpy(g.vote_values,b,sizeof b);g.vote_anchor=9;
    o=input(&g,0,0,0);assert(o.vote_anchor==2);
    reset_frame_state(&g);o=input(&g,0,0,4);assert(!o.vote_count && o.vote_anchor==2);
    ge_decision out[2];ge_break(&g,out);o=input(&g,0,0,5);
    assert(!g.vote_count && o.vote_anchor==2 && o.anchor_source==GE_SOURCE_VOTE);
    ge_break(&g,out);ge_set_pairing(&g,1);o=input(&g,0,0,5);
    assert(!g.vote_count && o.vote_anchor==2 && g.reverse);
    ge_init(&g,1,0);o=input(&g,0,0,5);assert(!g.vote_count && o.vote_anchor==5);
    ge_anchor_vote=0;o=input(&g,2,1,4);assert(o.frame_d2==4 && o.frame_d1==3 && !g.vote_count);
}
static void fills(void) {
    memset(y,1,sizeof y);
    /* Outside the body cannot alter the reference. Exact +10 is insufficient. */
    for(int r=7;r<=15;r++)for(int x=0;x<40;x++)y[r*720+x]=250;
    memset(y+18*720+40,11,640);
    for(int r=19;r<=20;r++)for(int x=40;x<680;x++)y[r*720+x]=12+(x%2)*20;
    ge_level_result v=ge_level_scan(y,0,5,0);
    assert(v.first==23 && v.reference==1 && v.mean==22 && v.sd==10 && v.corr_below==1 && v.accepted);
    assert(ge_level_scan(y,0,0,0).accepted); /* top 23 remains within clamp zero */
    memset(y+20*720+40,1,640);
    v=ge_level_scan(y,0,5,1);assert(v.first==23 && v.corr_below==0 && !v.accepted); /* sd==10 */
    memset(y+19*720+40,12,640);v=ge_level_scan(y,0,5,1);assert(v.accepted && v.sd==0);
    assert(!ge_level_scan(y,0,5,0).accepted); /* flat off */
    memset(y,1,sizeof y);
    for(int r=25;r<=26;r++)for(int x=40;x<680;x++)y[r*720+x]=20+(x%2)*20;
    v=ge_level_scan(y,0,5,0);assert(v.first==29 && !v.accepted);
    assert(ge_level_scan(y,0,6,0).accepted);
    /* A first rejected candidate cannot fall through to a later coherent row. */
    memset(y+18*720+40,12,640);v=ge_level_scan(y,0,5,0);assert(v.first==22 && !v.accepted);
}
static void ownership(void) {
    geometry_engine g;ge_init(&g,1,0);ge_anchor_vote=ge_level_fill=1;
    ge_features top={0},bottom={0};bottom.first[1]=286;
    top.wave_status[0]=GE_WAVE_ABSTAIN;top.level[0]=(ge_level_result){.first=23,.accepted=1};
    bottom.level[0]=(ge_level_result){.first=28,.accepted=1};
    ge_decision o={.rejection={.basin=1,.floor_lo=0,.floor_hi=0}};
    vote_anchor(&g,&o,&top,&bottom,y,y);assert(o.vote_confident && o.vote_top[0]==23);
    top.wave_status[0]=GE_WAVE_DISCARDED;
    vote_anchor(&g,&o,&top,&bottom,y,y);assert(!o.vote_confident && !o.vote_top[0]);
    top.wave_status[0]=GE_WAVE_ABSTAIN;ge_level_fill=0;
    vote_anchor(&g,&o,&top,&bottom,y,y);assert(!o.vote_confident);
}
static void paired_tops(void) {
    static uint8_t by[GE_PIXELS];
    memset(y,1,sizeof y);memset(by,1,sizeof by);
    /* Orthogonal +/-1 patterns: B=3*A+4*C has Pearson exactly 3/5.
     * Other unit's field 1 and neighboring rows remain flat decoys. */
    for(int x=0;x<640;x++) {
        int a=x%2?1:-1,c=x%4<2?1:-1;
        y[19*720+40+x]=100+10*a;
        by[283*720+40+x]=100+3*a+4*c;
    }
    geometry_engine g;ge_init(&g,1,0);ge_anchor_vote=1;ge_vote_pair=1;
    ge_features t={0},b={0};t.first[0]=23;b.first[1]=287; /* st=+1 */
    ge_decision o={.rejection={.basin=1,.floor_lo=0,.floor_hi=0}};
    vote_anchor(&g,&o,&t,&b,y,by);
    assert(o.vote_rB==.6 && o.vote_pair_pass && o.vote_confident && o.vote_anchor==1);
    ge_vote_pair_min=nextafter(.6,1);
    vote_anchor(&g,&o,&t,&b,y,by);assert(!o.vote_pair_pass && !o.vote_confident);
    ge_vote_pair_min=.6;o.rejection.floor_lo=2;o.rejection.floor_hi=2;
    vote_anchor(&g,&o,&t,&b,y,by);assert(o.vote_pair_pass && !o.vote_confident); /* no low widening */
    o.rejection.floor_lo=-1;o.rejection.floor_hi=-1;
    vote_anchor(&g,&o,&t,&b,y,by);assert(!o.vote_confident); /* high +2 rejected */
    o.rejection.floor_lo=0;o.rejection.floor_hi=0;
    vote_anchor(&g,&o,&t,&b,by,by);assert(o.vote_rB==0 && !o.vote_confident); /* wrong source */
    vote_anchor(&g,&o,&t,&b,y,y);assert(o.vote_rB==0 && !o.vote_confident);
    ge_vote_pair=0;vote_anchor(&g,&o,&t,&b,NULL,NULL);
    assert(isnan(o.vote_rB) && !o.vote_confident); /* exact old floor, no reads */
    ge_vote_pair=1;ge_anchor_vote=0;
    vote_anchor(&g,&o,&t,&b,NULL,NULL);assert(isnan(o.vote_rB));
    ge_vote_pair=0;
}
int main(void) {votes();fills();ownership();paired_tops();puts("GEOMETRY-VOTE PASS");return 0;}
