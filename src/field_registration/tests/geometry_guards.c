/* Test the actual instruments, including their private picture/first helpers. */
#include "../geometry_engine.c"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
static void body(uint8_t *p,int a,int b) {
    for(int x=40;x<680;x++)p[x]=(x&1)?a:b;
}
int main(void) {
    uint8_t *y=malloc(GE_PIXELS);assert(y);memset(y,1,GE_PIXELS);
    uint8_t *a=y+19*720,*b=a+720;
    assert(ge_top_margin==0 && ge_top_guard==0 && ge_top_plain23==1 && ge_top_runin==1);
    body(a,100,106);body(b,200,200);
    for(int g=0;g<5;g++){
        ge_top_guard=g;assert(picture(y,19,1,1)==(g<3));
        assert(picture(y,19,1,0)); // bottom consults no instrument
    }
    body(a,10,110);
    for(int g=0;g<5;g++){ge_top_guard=g;assert(picture(y,19,1,1)==(g==1));}
    // Absolute tolerance inclusive at 20%, at least 11 chunks, next row only.
    memset(a+40,120,640);memset(b+40,100,640);
    assert(chunk_agreement(a+40,b+40));
    memset(a+40,80,640);assert(chunk_agreement(a+40,b+40));
    memset(a+40,121,640);assert(!chunk_agreement(a+40,b+40));
    memset(a+40,100,11*40);assert(chunk_agreement(a+40,b+40));
    memset(a+40,121,40);assert(!chunk_agreement(a+40,b+40));
    body(a,100,110);body(b,100,120);ge_top_guard=4;
    assert(!picture(y,19,1,1)); // ratio exactly .5
    body(a,100,111);assert(picture(y,19,1,1));
    body(a,100,139);assert(picture(y,19,1,1));
    body(a,100,140);assert(!picture(y,19,1,1)); // ratio exactly 2
    body(a,100,104);ge_top_margin=-1000;
    for(int g=0;g<5;g++){ge_top_guard=g;assert(!picture(y,19,1,1));} // spread never optional
    body(a,110,120);ge_top_margin=5;ge_top_guard=1;
    assert(!picture(y,19,115,1));
    assert(picture(y,19,nextafter(115,-INFINITY),1));
    ge_top_margin=1000;assert(picture(y,19,1,0)); // margin cannot reach bottom
    ge_top_margin=0;
    // Plain23 evidence is still measured when its re-search is disabled.
    memset(y,1,GE_PIXELS);body(a,10,20);body(b,30,40);ge_features on,off;
    ge_top_guard=0;ge_measure(y,&on);ge_top_plain23=0;ge_measure(y,&off);
    assert(!on.plain23 && !off.plain23 && on.rule_first==23 && off.rule_first==23);
    assert(on.auto_first==24 && on.first[0]==24 && off.auto_first==23 && off.first[0]==23);
    // A sinusoidal preceding row has >.5 run-in, but no body picture. Keep the
    // first rows identical while toggling only the run-in placement increment.
    memset(y,1,GE_PIXELS);ge_top_plain23=1;ge_top_guard=1;
    body(y+20*720,60,80);body(y+283*720,60,80);body(y+282*720,10,20);
    for(int x=0;x<238;x++)y[19*720+x]=(uint8_t)(30+20*sin(2*3.14159265358979323846*x/26.81));
    // Force the leading pulse out of the picture search via the amplitude bar.
    ge_top_margin=55;ge_top_runin=1;ge_measure(y,&on);
    ge_top_runin=0;ge_measure(y,&off);
    assert(on.runin>=.5 && on.runin==off.runin);
    assert(on.rule_first==off.rule_first && on.auto_first==off.auto_first);
    assert(on.first[0]==off.first[0]+1);
    // All knobs leave bottom measurements/profiles and derived levels unchanged.
    for(int g=0;g<5;g++)for(int p=0;p<2;p++)for(int r=0;r<2;r++) {
        ge_top_guard=g;ge_top_plain23=p;ge_top_runin=r;ge_measure(y,&off);
        assert(!memcmp(on.last,off.last,sizeof on.last));
        assert(!memcmp(on.bottom,off.bottom,sizeof on.bottom));
        assert(!memcmp(on.profile,off.profile,sizeof on.profile));
        assert(!memcmp(on.blank,off.blank,sizeof on.blank));
        assert(!memcmp(on.hblank_level,off.hblank_level,sizeof on.hblank_level));
        assert(!memcmp(on.hblank_cols,off.hblank_cols,sizeof on.hblank_cols));
    }
    free(y);puts("GEOMETRY-GUARDS: five instruments, boundaries, spread, plain23/run-in evidence, protected bottom PASS");
    return 0;
}
