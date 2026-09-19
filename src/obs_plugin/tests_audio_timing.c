#include "audio_timing.h"
#include <assert.h>
#include <stdio.h>

int main(void) {
    shuttle_audio_clock s = {0}; uint64_t t;
    ap_block b = {.pts_num=80080};
    assert(shuttle_audio_time(&s,&b,&t)==0 && t==80080);
    b.correlation_residual=115;
    assert(shuttle_audio_time(&s,&b,&t)==1 && t==80195);
    b.flags=AP_FLAG_DROPPED_BEFORE;
    assert(shuttle_audio_time(&s,&b,&t)==0 && t==80195); // old correction survives a drop
    b.correlation_residual=230;
    assert(shuttle_audio_time(&s,&b,&t)==1 && t==80310); // step inside dropped blocks survives
    b.correlation_residual=233;
    assert(shuttle_audio_time(&s,&b,&t)==0 && t==80310); // quantization is not a step
    b.flags=AP_FLAG_DISCONTINUITY_BEFORE|AP_FLAG_DROPPED_BEFORE; b.correlation_residual=0;
    assert(shuttle_audio_time(&s,&b,&t)==0 && t==80080); // real break survives queue loss
    b.flags=0; b.correlation_residual=115;
    assert(shuttle_audio_time(&s,&b,&t)==1 && t==80195);
    b.flags=AP_FLAG_UNANCHORED|AP_FLAG_DISCONTINUITY_BEFORE;
    assert(shuttle_audio_time(&s,&b,&t)==-1 && !s.have_residual && !s.applied_ticks);
    b.flags=0; b.correlation_residual=0;
    assert(shuttle_audio_time(&s,&b,&t)==0 && t==80080); // no repeated break flag at anchor
    b.correlation_residual=-15;
    assert(shuttle_audio_time(&s,&b,&t)==1 && t==80065); // preserve signed step policy
    puts("audio timing: PASS (drop, hidden step, quantization, break, unanchored re-anchor, signed step)");
}
