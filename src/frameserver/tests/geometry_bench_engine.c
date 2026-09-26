/* Compile the unchanged engine in its normal separate translation unit.
 * This test-only accessor observes whether this input unit ran either search. */
#include "../../field_registration/geometry_engine.c"
unsigned geometry_bench_searches(const geometry_engine *g) {
    return (unsigned)g->previous.rigid[0].known+(unsigned)g->previous.rigid[1].known;
}
