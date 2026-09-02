// frameserver_replay <capture.tpc> [decision_log.csv] — run the whole P3 pipeline on a
// recorded capture (no hardware) and print the accounting. Exit 0 when the pipeline drained.
#include "frameserver.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdatomic.h>
static _Atomic int done;
static void on_end(void *c, enum cc_end r){ (void)c; done = 1 + (int)r; }
int main(int argc, char **argv){
    if (argc < 2){ fprintf(stderr, "usage: %s <capture.tpc> [decision_log.csv]\n", argv[0]); return 9; }
    fs_config cfg = {0}; cfg.capture.replay_path = argv[1]; cfg.decision_log = argc > 2 ? argv[2] : NULL;
    cfg.on_end = on_end;
    frameserver *f = NULL;
    if (fs_open(&f, &cfg) != 0){ fprintf(stderr, "open failed\n"); return 1; }
    if (fs_start(f) != 0){ fprintf(stderr, "start failed\n"); return 1; }
    while (!done) usleep(20000);
    fs_stop(f);
    fs_stats s; fs_get_stats(f, &s);
    printf("video obs %llu | exact %llu short %llu hole %llu unframed %llu other %llu 0x0800 %llu\n",
        (unsigned long long)s.video_observations, (unsigned long long)s.exact_units, (unsigned long long)s.short_units,
        (unsigned long long)s.holes, (unsigned long long)s.unframed, (unsigned long long)s.other_format, (unsigned long long)s.no_signal_0800);
    printf("published %llu | dropped(pool) %llu dropped(surfaces) %llu | unsettled %llu | begin_segment %llu discontinuity %llu | log rows %llu | pool high %u\n",
        (unsigned long long)s.published, (unsigned long long)s.dropped_pool_full, (unsigned long long)s.publisher_dropped,
        (unsigned long long)s.unsettled_units, (unsigned long long)s.begin_segment_calls, (unsigned long long)s.discontinuity_calls,
        (unsigned long long)s.log_rows, s.pool_high_water);
    printf("audio records %llu (resync %llu)\n", (unsigned long long)s.audio_records, (unsigned long long)s.audio_resync);
    fs_close(f);
    return 0;
}
