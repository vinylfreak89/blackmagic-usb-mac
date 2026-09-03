// Pipeline invariants on the parser's synthetic fixture (exact units, a device-short unit, a
// HostLoss hole, a marker split across packets, counter wrap, unframed tails):
//   every video observation yields exactly one log row; every exact unit is either published
//   or counted as a drop; non-eligible units are never published; the pipeline drains.
//   Then with a one-slot pool: rows are never lost to pool exhaustion (PoolFull rows), stop is
//   idempotent, and close-after-start is safe.
#include "../frameserver.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdatomic.h>
static int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { fails++; fprintf(stderr, "FAIL: " __VA_ARGS__); fprintf(stderr, "\n"); } } while (0)
static _Atomic int done; static _Atomic uint64_t frames_seen; static _Atomic int sink_stall_us;
static void on_end(void *c, enum cc_end r){ (void)c; (void)r; done = 1; }
static void sink(void *c, const fp_frame *fr){ (void)c; if (fr->surface) atomic_fetch_add(&frames_seen, 1);
    int st = atomic_load(&sink_stall_us); if (st) usleep(st); }   // a slow consumer holds the slot
int main(int argc, char **argv){
    if (argc < 2){ fprintf(stderr, "usage: %s <fixture.tpc>\n", argv[0]); return 9; }
    char logp[] = "/tmp/fs_test_log_XXXXXX"; int fd = mkstemp(logp); close(fd);
    fs_config cfg = {0}; cfg.capture.replay_path = argv[1]; cfg.decision_log = logp; cfg.on_end = on_end;
    cfg.sink.on_frame = sink; cfg.pool_units = 4; cfg.surface_pool = 3;
    frameserver *f = NULL;
    CHECK(fs_open(&f, &cfg) == 0, "open");
    CHECK(fs_start(f) == 0, "start");
    while (!done) usleep(10000);
    CHECK(fs_stop(f) == 0, "stop");
    fs_stats s; fs_get_stats(f, &s);
    CHECK(s.video_observations > 0, "fixture produced video observations");
    CHECK(s.log_rows == s.video_observations, "one log row per observation (%llu vs %llu)", (unsigned long long)s.log_rows, (unsigned long long)s.video_observations);
    CHECK(s.published + s.dropped_pool_full + s.publisher_dropped == s.exact_units, "exact units are published or counted as drops (%llu+%llu+%llu vs %llu)",
          (unsigned long long)s.published, (unsigned long long)s.dropped_pool_full, (unsigned long long)s.publisher_dropped, (unsigned long long)s.exact_units);
    CHECK(atomic_load(&frames_seen) == s.published, "sink saw every published frame");
    CHECK(s.discontinuity_calls > 0, "hole/short/unframed observations never reached the engine as discontinuities");
    CHECK(s.eligible_observations == s.exact_units, "eligible ingress %llu != exact units %llu with no ring drops",
          (unsigned long long)s.eligible_observations, (unsigned long long)s.exact_units);
    CHECK(s.short_units + s.holes + s.unframed + s.exact_units + s.other_format + s.no_signal_0800 >= s.video_observations, "every observation classified by transport/kind");
    // log integrity: header + rows, columns as the contract names them
    FILE *L = fopen(logp, "r"); char line[1024]; unsigned rows = 0; int hdr_ok = 0;
    while (fgets(line, sizeof line, L)){ if (rows == 0) hdr_ok = strstr(line, "interval_id,unsettled,provisional_d1") != NULL; rows++; }
    fclose(L); unlink(logp);
    CHECK(hdr_ok, "decision-log header carries the contract fields");
    CHECK(rows == s.log_rows + 1, "log rows on disk match (%u vs %llu)", rows, (unsigned long long)s.log_rows + 1);
    fs_close(f);

    // F4/F5: with a ONE-slot pool the delivery thread must shed bytes, but every observation
    // still gets a sidecar row, and shed units are marked PoolFull rather than silently absent.
    done = 0; atomic_store(&frames_seen, 0);
    char logp2[] = "/tmp/fs_test_log2_XXXXXX"; fd = mkstemp(logp2); close(fd);
    fs_config c2 = cfg; c2.decision_log = logp2; c2.pool_units = 1;
    atomic_store(&sink_stall_us, 200000);   // slot held ~200 ms per unit: the next unit MUST find the pool full
    frameserver *g = NULL;
    CHECK(fs_open(&g, &c2) == 0, "open (pool=1)");
    CHECK(fs_start(g) == 0, "start (pool=1)");
    while (!done) usleep(10000);
    CHECK(fs_stop(g) == 0, "stop (pool=1)");
    CHECK(fs_stop(g) == 0, "second stop is an idempotent no-op");
    atomic_store(&sink_stall_us, 0);
    fs_stats s2; fs_get_stats(g, &s2);
    CHECK(s2.dropped_pool_full > 0, "pool=1 with a stalled consumer did not exercise pool exhaustion");
    int ring_may_drop = getenv("FS_TEST_EXPECT_RING_DROPS") != NULL;   // -DRING_ITEMS=2 build
    CHECK(s2.log_rows + s2.dropped_ring_full == s2.video_observations, "pool=1: every observation is a row or a counted ring drop (%llu+%llu vs %llu)",
          (unsigned long long)s2.log_rows, (unsigned long long)s2.dropped_ring_full, (unsigned long long)s2.video_observations);
    if (!ring_may_drop){
        CHECK(s2.log_rows == s2.video_observations, "pool=1: one log row per observation (%llu vs %llu)", (unsigned long long)s2.log_rows, (unsigned long long)s2.video_observations);
        CHECK(s2.exact_units == s.exact_units, "pool size must not change how many exact units were observed (%llu vs %llu)", (unsigned long long)s2.exact_units, (unsigned long long)s.exact_units);
    }
    CHECK(s2.published + s2.dropped_pool_full + s2.publisher_dropped >= s2.exact_units, "pool=1: exact units published or counted (%llu+%llu+%llu vs %llu)",
          (unsigned long long)s2.published, (unsigned long long)s2.dropped_pool_full, (unsigned long long)s2.publisher_dropped, (unsigned long long)s2.exact_units);
    if (!ring_may_drop)
        CHECK(s2.published + s2.dropped_pool_full + s2.publisher_dropped == s2.exact_units, "pool=1: drop accounting exact without ring drops");
    CHECK(s2.pool_high_water <= 1, "pool high-water bounded by pool size (%u)", s2.pool_high_water);
    unsigned poolfull_rows = 0; rows = 0;
    L = fopen(logp2, "r");
    while (fgets(line, sizeof line, L)){ if (rows && strstr(line, ",PoolFull,")) poolfull_rows++; rows++; }
    fclose(L); unlink(logp2);
    if (!ring_may_drop){
        CHECK(poolfull_rows == s2.dropped_pool_full, "every pool-full drop is an explicit PoolFull sidecar row (%u vs %llu)", poolfull_rows, (unsigned long long)s2.dropped_pool_full);
        CHECK(s2.discontinuity_calls > s.discontinuity_calls, "a shed unit must reach the engine as a discontinuity");
    } else CHECK(poolfull_rows <= s2.dropped_pool_full, "more PoolFull rows than drops");
    fs_close(g);

    // Ring exhaustion (built with -DRING_ITEMS=2 by `make test-smallring`): drops are counted AND
    // folded into the next row's preceding_ring_drops column so they are locatable in time.
    if (getenv("FS_TEST_EXPECT_RING_DROPS")){
        done = 0; atomic_store(&frames_seen, 0);
        char logp3[] = "/tmp/fs_test_log3_XXXXXX"; fd = mkstemp(logp3); close(fd);
        fs_config c4 = cfg; c4.decision_log = logp3; c4.pool_units = 8;
        atomic_store(&sink_stall_us, 200000);
        frameserver *r = NULL;
        CHECK(fs_open(&r, &c4) == 0, "open (small ring)");
        CHECK(fs_start(r) == 0, "start (small ring)");
        while (!done) usleep(10000);
        CHECK(fs_stop(r) == 0, "stop (small ring)");
        atomic_store(&sink_stall_us, 0);
        fs_stats s4; fs_get_stats(r, &s4);
        CHECK(s4.dropped_ring_full > 0, "small ring with a stalled consumer did not exercise ring exhaustion");
        unsigned long long col_sum = 0; rows = 0;
        L = fopen(logp3, "r");
        while (fgets(line, sizeof line, L)){ if (rows){ char *c = strrchr(line, ','); if (c) col_sum += strtoull(c + 1, NULL, 10); } rows++; }
        fclose(L); unlink(logp3);
        CHECK(col_sum == s4.ring_drops_logged, "preceding_ring_drops column sum %llu != ring_drops_logged %llu", col_sum, (unsigned long long)s4.ring_drops_logged);
        CHECK(s4.ring_drops_logged <= s4.dropped_ring_full, "logged ring drops exceed counted");
        CHECK(s4.eligible_observations >= s4.exact_units, "ingress denominator below processed exact units");
        fs_close(r);
    }

    // F6: close after start without stop must stop first (ASan/TSan builds prove no use-after-free)
    done = 0;
    frameserver *k = NULL; fs_config c3 = cfg; c3.decision_log = NULL;
    CHECK(fs_open(&k, &c3) == 0, "open (close-without-stop)");
    CHECK(fs_start(k) == 0, "start (close-without-stop)");
    while (!done) usleep(10000);
    fs_close(k);
    if (fails) printf("FAILURES: %d\n", fails);
    else printf("frameserver tests: PASS (obs %llu, exact %llu, published %llu, short %llu, hole %llu, unframed %llu)\n",
           (unsigned long long)s.video_observations, (unsigned long long)s.exact_units, (unsigned long long)s.published,
           (unsigned long long)s.short_units, (unsigned long long)s.holes, (unsigned long long)s.unframed);
    return fails ? 1 : 0;
}
