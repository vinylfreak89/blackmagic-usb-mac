// replay_timeline.h on the tape-1 capture's measured span and on constructed wraps.
#include "replay_timeline.h"
#include <stdio.h>
static int fails;
#define CHECK(c, ...) do{ if(!(c)){ fails++; fprintf(stderr,"FAIL: "); fprintf(stderr,__VA_ARGS__); fprintf(stderr,"\n"); } }while(0)
int main(void){
    rt_timeline t;
    /* tape 1 (probe, 2026-09-29): 131,298,574,971 B, first counter 2763, last 34323 -> 162,632 units, 90:26.5 */
    CHECK(rt_init(&t, 131298574971ull, 2763, 34323) == 0 && t.units == 162632, "tape-1 units %llu", (unsigned long long)t.units);
    CHECK(rt_ms(t.units) == 5426487, "tape-1 duration %lld ms", (long long)rt_ms(t.units));
    /* seek: the unit at a time, and its byte offset, stay proportional */
    uint64_t u = rt_unit_at_ms(&t, 45 * 60 * 1000);
    CHECK(u == 80920, "unit at 45:00 is %llu (the first unit at or after it)", (unsigned long long)u);
    for (uint64_t k = 0; k <= t.units; k += 7) if (rt_unit_at_ms(&t, rt_ms(k)) != k){ CHECK(0, "rt_unit_at_ms(rt_ms(%llu)) = %llu", (unsigned long long)k, (unsigned long long)rt_unit_at_ms(&t, rt_ms(k))); break; }
    CHECK(rt_unit_at_ms(&t, rt_ms(t.units)) == t.units, "a seek to the shown end lands on the last unit");
    CHECK(rt_offset(&t, u) > 65200000000ull && rt_offset(&t, u) < 65400000000ull, "offset of 45:00: %llu", (unsigned long long)rt_offset(&t, u));
    CHECK(rt_unit_at_ms(&t, -5) == 0 && rt_unit_at_ms(&t, 99999999) == t.units, "clamped at both ends");
    /* resolve: a counter seen a few units from the estimate, across a 16-bit wrap */
    uint16_t c = (uint16_t)(2763 + 80919 + 3);
    CHECK(rt_resolve(&t, c, 80919) == 80922, "resolved %llu", (unsigned long long)rt_resolve(&t, c, 80919));
    c = (uint16_t)(2763 + 62773 - 2);   /* 65534: just before the counter wraps */
    CHECK(rt_resolve(&t, c, 62773) == 62771 && rt_resolve(&t, (uint16_t)(c + 5), 62773) == 62776, "across the wrap");
    CHECK(rt_resolve(&t, 2763, 0) == 0 && rt_resolve(&t, 2760, 0) == 0, "never before unit 0");
    CHECK(rt_resolve(&t, (uint16_t)(2763 + 162632 + 5), 162630) == 162632, "never past the last unit");
    CHECK(rt_resolve(&t, (uint16_t)(2763 + 50000 - 205), 50000) == 49795, "a counter within the slack is believed");
    CHECK(rt_resolve(&t, (uint16_t)(2763 + 50000 + 20000), 50000) == 50000, "a counter 20,000 units from the frame count (a counter restart) is not");
    CHECK(rt_consistent(&t), "tape 1 is consistent");
    /* the wrap count: short files, and a file whose last counter is below its first */
    CHECK(rt_init(&t, 807324ull * 1000, 100, 1100) == 0 && t.units == 1000, "short file %llu", (unsigned long long)t.units);
    CHECK(rt_init(&t, 807324ull * 70000, 60000, (uint16_t)(60000 + 70000)) == 0 && t.units == 70000, "one wrap %llu", (unsigned long long)t.units);
    CHECK(rt_init(&t, 807324ull * 70000 * 101 / 100, 60000, (uint16_t)(60000 + 70000)) == 0 && t.units == 70000 && rt_consistent(&t), "1%% off the nominal rate: the counters stand");
    CHECK(rt_init(&t, 1000, 5, 5) != 0, "no units: unknown");
    /* a counter restart inside a file: 100,000 units of bytes but a span of 30,000 counters */
    CHECK(rt_init(&t, 807324ull * 100000, 1000, 31000) == 0 && !rt_consistent(&t) && t.units == 100000, "counter restart: units %llu approx %d", (unsigned long long)t.units, t.approx);
    printf(fails ? "REPLAY TIMELINE: %d FAILURES\n" : "REPLAY TIMELINE PASS\n", fails);
    return fails ? 1 : 0;
}
