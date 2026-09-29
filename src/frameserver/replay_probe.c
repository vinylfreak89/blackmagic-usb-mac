// replay_probe — see replay_probe.h.
#include "replay_probe.h"
#include "../capture_core/capture_core.h"
#include "../unit_parser/unit_parser.h"
#include <pthread.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>

typedef struct {
    unit_parser *parser;
    int stop_at_first;                 // head probe: the first complete unit is the answer
    _Atomic int found, ended, exhausted; _Atomic int reason;
    uint64_t bytes, window;            // delivery thread: payload seen, and the head run's bound
    uint16_t first, last;              // delivery thread only; read after cc_stop
    pthread_mutex_t m; pthread_cond_t c;
} probe_run;

static void signal_(probe_run *r){ pthread_mutex_lock(&r->m); pthread_cond_broadcast(&r->c); pthread_mutex_unlock(&r->m); }
static void on_video_(void *ctx, const unit_video_observation *u){
    probe_run *r = ctx;
    if (u->kind != UNIT_VIDEO_E801 || u->transport != UNIT_TRANSPORT_COMPLETE) return;
    if (r->stop_at_first && (atomic_load(&r->found) || r->bytes > r->window)) return;   /* first unit only, and only inside the head window */
    if (!atomic_load(&r->found)) r->first = u->counter16;
    r->last = u->counter16;
    atomic_store(&r->found, 1);
    if (r->stop_at_first) signal_(r);
}
static void on_audio_(void *ctx, const unit_audio_observation *a){ (void)ctx; (void)a; }
static void on_packet_(void *ctx, const cc_packet *p){
    probe_run *r = ctx;
    unit_parser_on_packet(r->parser, p);
    r->bytes += p->actual_len;
    if (r->stop_at_first && r->bytes > r->window && !atomic_exchange(&r->exhausted, 1)) signal_(r);   /* no unit near the start */
}
static void on_loss_(void *ctx, uint8_t ep, uint32_t n, uint64_t b){ unit_parser_on_loss(((probe_run *)ctx)->parser, ep, n, b); }
static void on_error_(void *ctx, uint8_t ep, uint32_t seq, int st, int kind){ unit_parser_on_error(((probe_run *)ctx)->parser, ep, seq, st, kind); }
static void on_end_(void *ctx, enum cc_end reason){ probe_run *r = ctx; atomic_store(&r->reason, (int)reason); atomic_store(&r->ended, 1); signal_(r); }

/* One unpaced replay from `offset`: the head run stops at the first complete unit, the tail run
 * reads to the end of the file. The delivery ring holds the whole window, so nothing is shed.
 * 0: found; -1: read completely, no unit (a property of the file); -2: not read completely (open
 * failure, abort, read error, unskippable damage), so nothing is known. */
static int run_(const char *path, uint64_t offset, uint64_t window, int stop_at_first, _Atomic int *abort, uint16_t *first, uint16_t *last){
    probe_run r; memset(&r, 0, sizeof r);
    r.stop_at_first = stop_at_first; r.window = window;
    r.parser = aligned_alloc(unit_parser_alignment(), unit_parser_size());
    if (!r.parser) return -1;
    unit_parser_callbacks pcb = { on_video_, on_audio_, &r };
    unit_parser_init(r.parser, NULL, &pcb);
    unit_parser_begin_epoch(r.parser, 1);
    pthread_mutex_init(&r.m, NULL); pthread_cond_init(&r.c, NULL);
    cc_config cfg; memset(&cfg, 0, sizeof cfg);
    cfg.replay_path = path; cfg.replay_start_offset = offset; cfg.replay_pace_us = 0;
    unsigned mb = (unsigned)((window + (1u << 20) - 1) >> 20) + 4;
    cfg.ring_mb = (int)mb; cfg.replay_readahead_mb = mb < 16 ? (int)mb : 16;
    cc_callbacks cb; memset(&cb, 0, sizeof cb);
    cb.on_packet = on_packet_; cb.on_loss = on_loss_; cb.on_error = on_error_; cb.on_end = on_end_; cb.ctx = &r;
    cc_session *s = NULL; int rc = -2;
    if (cc_open(&s, &cfg, &cb) == CC_OK && cc_start(s) == CC_OK){
        pthread_mutex_lock(&r.m);
        while (!atomic_load(&r.ended) && !(stop_at_first && (atomic_load(&r.found) || atomic_load(&r.exhausted))) && !(abort && atomic_load(abort))){
            struct timespec ts; clock_gettime(CLOCK_REALTIME, &ts); ts.tv_nsec += 100000000;
            if (ts.tv_nsec >= 1000000000){ ts.tv_sec++; ts.tv_nsec -= 1000000000; }
            pthread_cond_timedwait(&r.c, &r.m, &ts);   /* backstop for the abort flag only; the run signals */
        }
        pthread_mutex_unlock(&r.m);
        int aborted = abort && atomic_load(abort);
        cc_stop(s);
        /* The head run's answer is its first unit. The tail run's is its LAST unit, which is the file's
         * only if the run read to the end: an abort, a read error or damage past the skip bound ends it
         * early with an earlier counter, and a too-short timeline is worse than none. */
        int eof = !aborted && atomic_load(&r.ended) && atomic_load(&r.reason) == CC_END_REPLAY_EOF;
        int found = atomic_load(&r.found);
        if (stop_at_first) rc = found ? 0 : eof || atomic_load(&r.exhausted) ? -1 : -2;
        else rc = !eof ? -2 : found ? 0 : -1;
        if (rc == 0){ *first = r.first; *last = r.last; }
    }
    if (s) cc_close(s);
    pthread_mutex_destroy(&r.m); pthread_cond_destroy(&r.c); free(r.parser);
    return rc;
}

int fs_replay_probe(const char *path, uint64_t window_bytes, _Atomic int *abort, fs_replay_span *out){
    memset(out, 0, sizeof *out);
    struct stat st;
    if (!path || stat(path, &st) != 0 || st.st_size <= 0) return -1;
    out->file_bytes = (uint64_t)st.st_size;
    uint64_t w = window_bytes ? window_bytes : (32ull << 20);
    uint16_t a, b; int rc;
    if ((rc = run_(path, 0, w, 1, abort, &a, &b)) == 0){ out->first_counter = a; out->have_first = 1; }
    else if (rc == -2) out->incomplete = 1;
    if (abort && atomic_load(abort)){ out->incomplete = 1; return -1; }
    if ((rc = run_(path, out->file_bytes > w ? out->file_bytes - w : 0, w, 0, abort, &a, &b)) == 0){ out->last_counter = b; out->have_last = 1; }
    else if (rc == -2) out->incomplete = 1;
    if (abort && atomic_load(abort)) out->incomplete = 1;
    return out->have_first && out->have_last ? 0 : -1;
}
