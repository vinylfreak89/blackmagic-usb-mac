/* Diagnostic-only scheduler perturbation on real replay input. This is a
 * permitted writer preemption, not a production delay or altered observation.
 * Report its miss rate separately from unperturbed replay measurements. */
#include "../audio_publisher.h"
#include <sched.h>
void ap_test_correlation_writing(audio_publisher *p,uint64_t counter){
    (void)p;(void)counter;sched_yield();
}
