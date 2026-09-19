/* Exercise the actual producer's queue-full branch without scheduling races.
 * No session/threads/device: advancing tail explicitly models the consumer.
 * Including the implementation keeps aq_enqueue private in the public API. */
#include "../frameserver.c"
#include "../../obs_plugin/audio_timing.h"
#include <assert.h>

int main(void) {
    frameserver *f=calloc(1,sizeof *f); assert(f);
    f->aq_slots=1; f->aq_cap_frames=2;
    f->aq=calloc(1,sizeof *f->aq); f->aq_pcm=calloc(2,AP_BYTES_PER_FRAME);
    assert(f->aq && f->aq_pcm);
    assert(!pthread_mutex_init(&f->aq_m,NULL)); assert(!pthread_cond_init(&f->aq_c,NULL));
    uint8_t pcm[12]={1}; ap_block b={.n_frames=2,.s24le=pcm,.pts_num=80080};
    shuttle_audio_clock clock={0}; uint64_t ticks;
    aq_enqueue(f,&b); assert(shuttle_audio_time(&clock,&f->aq[0],&ticks)==0);
    atomic_store(&f->aq_tail,1);
    b.correlation_residual=115; aq_enqueue(f,&b);
    assert(shuttle_audio_time(&clock,&f->aq[0],&ticks)==1);
    b.correlation_residual=230; aq_enqueue(f,&b); // full, including a new step
    assert(atomic_load(&f->aq_dropped_blocks)==1);
    atomic_store(&f->aq_tail,2); aq_enqueue(f,&b);
    assert(f->aq[0].flags==AP_FLAG_DROPPED_BEFORE);
    assert(shuttle_audio_time(&clock,&f->aq[0],&ticks)==1 && ticks==80310);
    assert(!memcmp(f->aq[0].s24le,pcm,sizeof pcm));
    // The first block of a genuinely new run is dropped; its break MUST survive.
    b.flags=AP_FLAG_DISCONTINUITY_BEFORE|AP_FLAG_UNANCHORED; aq_enqueue(f,&b);
    b.flags=0; b.correlation_residual=0; aq_enqueue(f,&b); // another dropped block
    atomic_store(&f->aq_tail,3); aq_enqueue(f,&b);
    assert(f->aq[0].flags==(AP_FLAG_DISCONTINUITY_BEFORE|AP_FLAG_DROPPED_BEFORE));
    assert(shuttle_audio_time(&clock,&f->aq[0],&ticks)==0 && ticks==80080);
    atomic_store(&f->aq_tail,4); aq_enqueue(f,&b); assert(f->aq[0].flags==0);
    assert(atomic_load(&f->aq_dropped_blocks)==3 && atomic_load(&f->aq_dropped_frames)==6);
    pthread_cond_destroy(&f->aq_c); pthread_mutex_destroy(&f->aq_m);
    free(f->aq_pcm); free(f->aq); free(f);
    puts("audio queue flags: PASS (drop vs break, hidden step, carried break, cleared flags, PCM/accounting)");
}
