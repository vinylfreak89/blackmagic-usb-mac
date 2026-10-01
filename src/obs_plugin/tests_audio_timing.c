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
    /* Steps are whole frames and reported for contiguous delivery. The 2026-09-28 device event:
     * 974 samples lost, residual step 4865 ticks (quantized) -> 973 frames of silence. */
    { shuttle_audio_clock c = {0}; uint64_t t0, t1; int64_t st;
      ap_block x = {.pts_num = 1000000, .correlation_residual = 4376};
      assert(shuttle_audio_time_step(&c,&x,&t0,&st)==0 && st==0);
      x.pts_num += 1601*5; x.correlation_residual = 9241;
      assert(shuttle_audio_time_step(&c,&x,&t1,&st)==1 && st==973 && t1==x.pts_num+973*5);
      int64_t pend=0,gap; uint32_t skip;
      shuttle_audio_plan(st,0,1601,&pend,&gap,&skip); assert(gap==973 && skip==0 && pend==0);
      /* silence ends exactly where the block starts: contiguous for the consumer */
      assert(t1 - (uint64_t)gap*5 == x.pts_num);
      /* early audio: overlap longer than one block carries into the next, a gap cancels it */
      shuttle_audio_plan(-2000,0,1601,&pend,&gap,&skip); assert(gap==0 && skip==1601 && pend==399);
      shuttle_audio_plan(0,0,1601,&pend,&gap,&skip); assert(skip==399 && pend==0);
      shuttle_audio_plan(-10,0,1601,&pend,&gap,&skip); shuttle_audio_plan(5,0,1601,&pend,&gap,&skip); assert(gap==5 && skip==0 && pend==0);
      shuttle_audio_plan(-300,0,100,&pend,&gap,&skip); shuttle_audio_plan(0,1,1601,&pend,&gap,&skip); assert(skip==0 && pend==0); }
    puts("audio timing: PASS (drop, hidden step, quantization, break, unanchored re-anchor, signed step, contiguous step delivery)");
}
