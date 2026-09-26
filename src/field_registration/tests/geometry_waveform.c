#include "../geometry_engine.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void line(uint8_t *y,int r,int invert) {
    for(int x=40;x<680;x++)y[r*720+x]=(uint8_t)(1+((x&1)^invert));
}
int main(void) {
    uint8_t *y=malloc(GE_PIXELS);assert(y);
    ge_config config=ge_default_config();
    assert(config.wave_bar==.45 && config.wave_clamp==5);
    for(int k=0;k<2;k++) {
        memset(y,7,GE_PIXELS);int off=263*k;
        ge_wave_result w=ge_wave_scan(y,k,.45);
        assert(!w.first && w.step==0 && w.max_step==0);
        for(int r=19+off;r<37+off;r++)line(y,r,0);
        w=ge_wave_scan(y,k,.45);
        assert(w.first==23+off && w.step==1 && w.max_step==1);
        assert(!ge_wave_scan(y,k,1).first); /* strict, not inclusive */
        assert(ge_wave_scan(y,k,nextafter(1,0)).first==23+off);
        line(y,30+off,1); /* a later step of 2 must not replace the first */
        w=ge_wave_scan(y,k,.45);
        assert(w.first==23+off && w.step==1 && w.max_step==2);
        /* Window's earliest possible result is 22 (synthetic, not tape claim). */
        memset(y,7,GE_PIXELS);line(y,17+off,0);line(y,18+off,1);
        w=ge_wave_scan(y,k,.45);assert(w.first==22+off && w.step==1);
        for(int d=-6;d<=6;d++) {
            w.first=23+off+d;
            assert(ge_wave_accept(w,k,5)==(d>=-5 && d<=5));
        }
        w.first=0;assert(!ge_wave_accept(w,k,100));
        /* Integration: raw top stays visible when discarded; its accepted
         * census slot is unavailable, never rounded to the clamp boundary. */
        memset(y,7,GE_PIXELS);
        for(int r=25+off;r<37+off;r++)line(y,r,0);
        ge_features f;ge_measure(y,&f,&config);
        assert(f.wave[k].first==29+off && !f.first[k]);
        assert(f.wave_status[k]==GE_WAVE_DISCARDED);
        assert(f.wave_status[1-k]==GE_WAVE_ABSTAIN);
        config.wave_clamp=6;ge_measure(y,&f,&config);config.wave_clamp=5;
        assert(f.first[k]==29+off && f.wave_status[k]==GE_WAVE_ACCEPTED);
    }
    free(y);puts("WAVEFORM PASS: first not largest, strict bar, zero variance, both fields, symmetric clamp, explicit discard/abstain");
    return 0;
}
