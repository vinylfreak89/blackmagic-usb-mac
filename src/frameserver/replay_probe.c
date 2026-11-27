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

enum { RUN_FIRST, RUN_TO_EOF, RUN_LAST_IN };   /* first unit within the bound / last unit to the end / last unit within the bound */
#define SAMPLE_MAX (4ull << 20)                /* a sample of a stretch: ~5 units of stream, enough to hold a complete one */
#define SEARCH_DEFAULT (2ull << 30)            /* ~90 s of NTSC stream from each end */
#define UNIT_FILE_BYTES 807324ull              /* file bytes per unit (replay_timeline.h's nominal): a unit's start, from its end */

typedef struct {
    unit_parser *parser;
    int mode;
    _Atomic int found, ended, exhausted; _Atomic int reason;
    uint64_t bytes, window;            // delivery thread: payload seen, and the run's bound (RUN_FIRST, RUN_LAST_IN)
    uint16_t first, last;              // delivery thread only; read after cc_stop
    uint64_t first_at, last_at;        // payload bytes seen when the first / last unit completed
    pthread_mutex_t m; pthread_cond_t c;
} probe_run;

static void signal_(probe_run *r){ pthread_mutex_lock(&r->m); pthread_cond_broadcast(&r->c); pthread_mutex_unlock(&r->m); }
static void on_video_(void *ctx, const unit_video_observation *u){
    probe_run *r = ctx;
    if (u->kind != UNIT_VIDEO_E801 || u->transport != UNIT_TRANSPORT_COMPLETE) return;
    if (r->mode != RUN_TO_EOF && r->bytes > r->window) return;                 /* only inside the bounded window */
    if (r->mode == RUN_FIRST && atomic_load(&r->found)) return;               /* first unit only */
    if (!atomic_load(&r->found)){ r->first = u->counter16; r->first_at = r->bytes; }
    r->last = u->counter16; r->last_at = r->bytes;
    atomic_store(&r->found, 1);
    if (r->mode == RUN_FIRST) signal_(r);
}
static void on_audio_(void *ctx, const unit_audio_observation *a){ (void)ctx; (void)a; }
static void on_packet_(void *ctx, const cc_packet *p){
    probe_run *r = ctx;
    unit_parser_on_packet(r->parser, p);
    r->bytes += p->actual_len;
    if (r->mode != RUN_TO_EOF && r->bytes > r->window && !atomic_exchange(&r->exhausted, 1)) signal_(r);   /* the window is read */
}
static void on_loss_(void *ctx, uint8_t ep, uint32_t n, uint64_t b){ unit_parser_on_loss(((probe_run *)ctx)->parser, ep, n, b); }
static void on_error_(void *ctx, uint8_t ep, uint32_t seq, int st, int kind){ unit_parser_on_error(((probe_run *)ctx)->parser, ep, seq, st, kind); }
static void on_end_(void *ctx, enum cc_end reason){ probe_run *r = ctx; atomic_store(&r->reason, (int)reason); atomic_store(&r->ended, 1); signal_(r); }

/* One unpaced replay from `offset`: RUN_FIRST stops at the first complete unit within `window` bytes, RUN_TO_EOF
 * reads to the end of the file for its last unit, RUN_LAST_IN reads `window` bytes for the last unit inside them.
 * The delivery ring holds the whole window, so nothing is shed. *at: the file offset of the answer unit's start,
 * estimated from the payload read before it completed (seek positions only; a few units either way).
 * 0: found; -1: read completely, no unit (a property of the file); -2: not read completely (open failure, abort,
 * read error, unskippable damage), so nothing is known. */
static int run_(const char *path, uint64_t offset, uint64_t window, int mode, _Atomic int *abort, uint16_t *counter, uint64_t *at){
    probe_run r; memset(&r, 0, sizeof r);
    r.mode = mode; r.window = window;
    r.parser = aligned_alloc(unit_parser_alignment(), unit_parser_size());
    if (!r.parser) return -2;   /* nothing read: unknown, not absent */
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
        while (!atomic_load(&r.ended) && !(mode == RUN_FIRST && atomic_load(&r.found)) && !(mode != RUN_TO_EOF && atomic_load(&r.exhausted)) && !(abort && atomic_load(abort))){
            struct timespec ts; clock_gettime(CLOCK_REALTIME, &ts); ts.tv_nsec += 100000000;
            if (ts.tv_nsec >= 1000000000){ ts.tv_sec++; ts.tv_nsec -= 1000000000; }
            pthread_cond_timedwait(&r.c, &r.m, &ts);   /* backstop for the abort flag only; the run signals */
        }
        pthread_mutex_unlock(&r.m);
        int aborted = abort && atomic_load(abort);
        cc_stop(s);
        /* RUN_FIRST's answer is its first unit. RUN_TO_EOF's is its LAST unit, which is the file's only if the run
         * read to the end: an abort, a read error or damage past the skip bound ends it early with an earlier
         * counter, and a too-short timeline is worse than none. RUN_LAST_IN's is the last unit of a window it read
         * whole (or to the end of the file). */
        int eof = !aborted && atomic_load(&r.ended) && atomic_load(&r.reason) == CC_END_REPLAY_EOF;
        int found = atomic_load(&r.found), whole = !aborted && (eof || atomic_load(&r.exhausted));
        if (mode == RUN_FIRST) rc = found ? 0 : whole ? -1 : -2;
        else if (mode == RUN_TO_EOF) rc = !eof ? -2 : found ? 0 : -1;
        else rc = !whole ? -2 : found ? 0 : -1;
        if (rc == 0){
            uint64_t done = mode == RUN_FIRST ? r.first_at : r.last_at;
            *counter = mode == RUN_FIRST ? r.first : r.last;
            *at = offset + (done > UNIT_FILE_BYTES ? done - UNIT_FILE_BYTES : 0);
        }
    }
    if (s) cc_close(s);
    pthread_mutex_destroy(&r.m); pthread_cond_destroy(&r.c); free(r.parser);
    return rc;
}

/* The first unit after a stretch without picture at the start: samples every `w` bytes on (a few MB each) until one
 * holds a unit, then the first unit after the last empty sample. The stretch is the deck off or stopped, read
 * sparsely so the probe stays light beside a playing replay. Gives up after `search` bytes. */
static int search_head_(const char *path, uint64_t file, uint64_t w, uint64_t search, _Atomic int *abort, uint16_t *c, uint64_t *at){
    uint64_t S = w < SAMPLE_MAX ? w : SAMPLE_MAX;
    for (uint64_t k = 1; k * w < search && k * w + S <= file; k++){
        if (abort && atomic_load(abort)) return -2;
        int rc = run_(path, k * w, S, RUN_FIRST, abort, c, at);
        if (rc == -2) return -2;
        if (rc == 0){
            if (k == 1) return 0;                                   /* [0, w) was read whole: this is the first */
            return run_(path, (k - 1) * w + S, w, RUN_FIRST, abort, c, at);   /* the first lies after the last empty sample */
        }
    }
    return -1;
}
/* The last unit before a stretch without picture at the end, the same way backwards: the sample ending k*w bytes
 * before the end of the file, then the last unit before the first empty sample after it. */
static int search_tail_(const char *path, uint64_t file, uint64_t w, uint64_t search, _Atomic int *abort, uint16_t *c, uint64_t *at){
    uint64_t S = w < SAMPLE_MAX ? w : SAMPLE_MAX;
    for (uint64_t k = 1; k * w < search && k * w + S <= file; k++){
        if (abort && atomic_load(abort)) return -2;
        uint64_t off = file - k * w - S;
        int rc = run_(path, off, S, RUN_LAST_IN, abort, c, at);
        if (rc == -2) return -2;
        if (rc == 0){
            if (k == 1) return 0;                                   /* [file - w, file) was read whole: this is the last */
            return run_(path, off, w + S, RUN_LAST_IN, abort, c, at);         /* up to the next sample, which was empty */
        }
    }
    return -1;
}

int fs_replay_probe_ex(const char *path, uint64_t window_bytes, uint64_t search_bytes, _Atomic int *abort, fs_replay_span *out){
    memset(out, 0, sizeof *out);
    struct stat st;
    if (!path){ out->incomplete = 1; return -1; }
    if (stat(path, &st) != 0){ out->incomplete = 1; return -1; }   /* unreadable now (a network volume): unknown, not absent */
    if (st.st_size <= 0) return -1;                                /* empty: a clean absence; a size change probes again */
    out->file_bytes = (uint64_t)st.st_size;
    uint64_t w = window_bytes ? window_bytes : (32ull << 20), search = search_bytes ? search_bytes : SEARCH_DEFAULT;
    uint16_t c; uint64_t at; int rc;
    if ((rc = run_(path, 0, w, RUN_FIRST, abort, &c, &at)) == -1) rc = search_head_(path, out->file_bytes, w, search, abort, &c, &at);
    if (rc == 0){ out->first_counter = c; out->first_offset = at; out->have_first = 1; }
    else if (rc == -2) out->incomplete = 1;
    if (abort && atomic_load(abort)){ out->incomplete = 1; return -1; }
    if ((rc = run_(path, out->file_bytes > w ? out->file_bytes - w : 0, w, RUN_TO_EOF, abort, &c, &at)) == -1)
        rc = search_tail_(path, out->file_bytes, w, search, abort, &c, &at);
    if (rc == 0){ out->last_counter = c; out->last_offset = at; out->have_last = 1; }
    else if (rc == -2) out->incomplete = 1;
    if (abort && atomic_load(abort)) out->incomplete = 1;
    if (out->have_first && out->have_last && out->last_offset <= out->first_offset){ out->first_offset = 0; out->last_offset = out->file_bytes; }
    return out->have_first && out->have_last ? 0 : -1;
}
int fs_replay_probe(const char *path, uint64_t window_bytes, _Atomic int *abort, fs_replay_span *out){
    return fs_replay_probe_ex(path, window_bytes, 0, abort, out);
}
