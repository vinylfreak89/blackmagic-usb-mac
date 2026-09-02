// Pipeline invariants on the parser's synthetic fixture (exact units, a device-short unit, a
// HostLoss hole, a marker split across packets, counter wrap, unframed tails):
//   every video observation yields exactly one log row; every exact unit is either published
//   or counted as a drop; non-eligible units are never published; the pipeline drains.
#include "../frameserver.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdatomic.h>
static int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { fails++; fprintf(stderr, "FAIL: " __VA_ARGS__); fprintf(stderr, "\n"); } } while (0)
static _Atomic int done; static _Atomic uint64_t frames_seen;
static void on_end(void *c, enum cc_end r){ (void)c; (void)r; done = 1; }
static void sink(void *c, const fp_frame *fr){ (void)c; if (fr->surface) atomic_fetch_add(&frames_seen, 1); }
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
    CHECK(s.short_units + s.holes + s.unframed + s.exact_units + s.other_format + s.no_signal_0800 >= s.video_observations, "every observation classified by transport/kind");
    // log integrity: header + rows, columns as the contract names them
    FILE *L = fopen(logp, "r"); char line[1024]; unsigned rows = 0; int hdr_ok = 0;
    while (fgets(line, sizeof line, L)){ if (rows == 0) hdr_ok = strstr(line, "interval_id,unsettled,provisional_d1") != NULL; rows++; }
    fclose(L); unlink(logp);
    CHECK(hdr_ok, "decision-log header carries the contract fields");
    CHECK(rows == s.log_rows + 1, "log rows on disk match (%u vs %llu)", rows, (unsigned long long)s.log_rows + 1);
    fs_close(f);
    if (fails) printf("FAILURES: %d\n", fails);
    else printf("frameserver tests: PASS (obs %llu, exact %llu, published %llu, short %llu, hole %llu, unframed %llu)\n",
           (unsigned long long)s.video_observations, (unsigned long long)s.exact_units, (unsigned long long)s.published,
           (unsigned long long)s.short_units, (unsigned long long)s.holes, (unsigned long long)s.unframed);
    return fails ? 1 : 0;
}
