/* Same engine/optimisation flags as production, with test-only thread CPU
 * instrumentation. No clocks, counters or extra branch in a production build. */
#include <assert.h>
#include <stdint.h>
#include <time.h>
static uint64_t rigid_ns;
#ifdef GE_RIGID_VERIFY
#include "../../field_registration/tests/geometry_rigid_reference.h"
static uint64_t rigid_counter,rigid_verified;
void geometry_bench_rigid_unit(uint64_t counter) { rigid_counter=counter; }
uint64_t geometry_bench_rigid_verified(void) { return rigid_verified; }
#endif
static uint64_t geometry_bench_rigid_begin(void) {
    struct timespec t;assert(!clock_gettime(CLOCK_THREAD_CPUTIME_ID,&t));
    return (uint64_t)t.tv_sec*1000000000u+(uint64_t)t.tv_nsec;
}
static void geometry_bench_rigid_end(uint64_t begin) {
    rigid_ns+=geometry_bench_rigid_begin()-begin;
}
#ifdef GE_RIGID_VERIFY
static void geometry_bench_rigid_check(const uint8_t *current,const uint8_t *previous,
                                      int field,const ge_rigid_motion *result) {
    unsigned sums[11][17];
    ge_rigid_motion expected=rigid_reference(current,previous,field,sums);
    if(result->known!=expected.known || result->dx!=expected.dx || result->dy!=expected.dy ||
       memcmp(&result->error,&expected.error,sizeof(double)) ||
       memcmp(&result->far_error,&expected.far_error,sizeof(double)) ||
       memcmp(&result->clarity,&expected.clarity,sizeof(double)))
        fprintf(stderr,"RIGID VERIFY counter=%llu field=%d\n",(unsigned long long)rigid_counter,field+1);
    rigid_assert_equal(*result,expected);rigid_verified++;
}
#endif
#define GE_RIGID_PROFILE
#include "../../field_registration/geometry_engine.c"
uint64_t geometry_bench_rigid_take(void) {
    uint64_t result=rigid_ns;rigid_ns=0;return result;
}
unsigned geometry_bench_searches(const geometry_engine *g) {
    return (unsigned)g->previous.rigid[0].known+(unsigned)g->previous.rigid[1].known;
}
