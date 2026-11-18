/* tpc_play — a .tpc replayed through the frameserver for a player: frames and sound on stdout, nothing on disk.
 *
 *   tpc_play probe FILE
 *       One JSON line: {"file_bytes":..,"units":..,"first16":..,"first_counter":..,"last_counter":..} (rt_timeline,
 *       the OBS seek bar's), or {"error":".."} and exit 1.
 *   tpc_play play FILE [--start-unit U --units N --first16 F] [--registration on|off] [--hretime 0|1]
 *                      [--partial 0|1] [--repair 0|1] [--first-line F1,F2]
 *       Replays FILE from near unit U (byte offset U/N of the file, aligned forward to a whole transfer: the time
 *       shown comes from the frames' own counters) and writes records to stdout until the file ends or stdout
 *       closes. Defaults are the plain render's: registration off, H-retiming off, partial frames shown, repair on,
 *       nominal first line.
 *
 * Records: u32 type, u32 payload length (little-endian), payload.
 *   1 VIDEO  u64 ticks (audio clock, 1/240000 s), u64 counter_ext, u64 unit (index since the file's first complete
 *            unit, or ~0 unknown), u8 transport (enum fp_transport), i8 d1, i8 d2, u8 estimated (no resync for this
 *            unit yet: time one period after the previous frame), u32 unavailable_rows, then 720*480*2 bytes '2vuy'.
 *   2 AUDIO  u64 ticks, u32 frames, u32 flags (enum ap_flags), then frames * 2 float32 (L, R).
 *   3 END    JSON text: {"reason":..,"published":..,"holes":..,"short_units":..,"repaired":..,...}
 *
 * Pacing is the reader's. The frameserver runs offline (offline_backpressure): when stdout is not read, the writes
 * block, the frameserver waits, the replay waits, and nothing is shed. A player stops reading once it holds enough
 * ahead of its playhead, and that is pause and flow control at once. Times are those OBS gets (audio_timing.h):
 * sound on the publisher's sample-contiguous clock, each frame at its own unit's audio-clock time.
 */
#include "frameserver.h"
#include "frame_publisher.h"
#include "audio_publisher.h"
#include "replay_probe.h"
#include "../obs_plugin/audio_timing.h"
#include "../obs_plugin/replay_timeline.h"
#include <errno.h>
#include <inttypes.h>
#include <pthread.h>
#include <signal.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

enum { REC_VIDEO = 1, REC_AUDIO = 2, REC_END = 3 };
#define VIDEO_BYTES ((size_t)FP_FRAME_WIDTH * FP_FRAME_HEIGHT * 2)

static pthread_mutex_t g_out = PTHREAD_MUTEX_INITIALIZER;
static _Atomic int g_out_closed;                       /* the reader went away: stop writing, end the replay */
static pthread_mutex_t g_end_m = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t g_end_c = PTHREAD_COND_INITIALIZER;
static int g_ended; static enum cc_end g_reason;

static rt_timeline g_tl; static int g_have_tl; static uint64_t g_start_unit;
static shuttle_video_clock g_vclock; static shuttle_audio_clock g_aclock;   /* each touched by one worker only */
static uint64_t g_frames_out;
static uint8_t *g_vrec;                                /* header + one frame, video worker only */
static uint8_t *g_arec; static size_t g_arec_cap;      /* audio worker only */

static int write_all(const void *p, size_t n){
    const uint8_t *b = p;
    while (n){
        ssize_t w = write(STDOUT_FILENO, b, n);
        if (w < 0){ if (errno == EINTR) continue; return -1; }
        b += w; n -= (size_t)w;
    }
    return 0;
}
static void put32(uint8_t *p, uint32_t v){ memcpy(p, &v, 4); }
static void put64(uint8_t *p, uint64_t v){ memcpy(p, &v, 8); }
/* One record, whole, under the output lock (two workers write). A failed write is the reader leaving. */
static void emit(uint32_t type, const uint8_t *payload, uint32_t len){
    if (atomic_load(&g_out_closed)) return;
    uint8_t h[8]; put32(h, type); put32(h + 4, len);
    pthread_mutex_lock(&g_out);
    int bad = write_all(h, 8) || write_all(payload, len);
    pthread_mutex_unlock(&g_out);
    if (bad) atomic_store(&g_out_closed, 1);
}

static void on_frame(void *ctx, const fp_frame *fr){
    (void)ctx;
    if (!fr->surface || atomic_load(&g_out_closed)) return;
    int est = 0;
    uint64_t t = shuttle_video_time(&g_vclock, fr->audio_pts_known, fr->audio_pts_num,
                                    fr->transport == FP_TRANSPORT_SHORT ? AP_TICKS_PER_UNIT / 2 : AP_TICKS_PER_UNIT,
                                    (uint64_t)((__uint128_t)fr->pts_num * AP_PTS_DEN / fr->pts_den), &est);
    uint64_t unit = ~(uint64_t)0;
    if (g_have_tl) unit = rt_resolve(&g_tl, (uint16_t)fr->counter_ext, (int64_t)(g_start_unit + g_frames_out));
    g_frames_out++;
    uint8_t *h = g_vrec;
    put64(h, t); put64(h + 8, fr->counter_ext); put64(h + 16, unit);
    h[24] = fr->transport; h[25] = (uint8_t)fr->d1; h[26] = (uint8_t)fr->d2; h[27] = (uint8_t)est;
    put32(h + 28, fr->unavailable_rows);
    IOSurfaceLock(fr->surface, kIOSurfaceLockReadOnly, NULL);
    const uint8_t *base = IOSurfaceGetBaseAddress(fr->surface); size_t bpr = IOSurfaceGetBytesPerRow(fr->surface);
    for (unsigned y = 0; y < FP_FRAME_HEIGHT; y++) memcpy(h + 32 + (size_t)y * FP_FRAME_WIDTH * 2, base + y * bpr, FP_FRAME_WIDTH * 2);
    IOSurfaceUnlock(fr->surface, kIOSurfaceLockReadOnly, NULL);
    emit(REC_VIDEO, h, (uint32_t)(32 + VIDEO_BYTES));
}

static void on_audio(void *ctx, const ap_block *b){
    (void)ctx;
    uint64_t ticks;
    if (atomic_load(&g_out_closed) || shuttle_audio_time(&g_aclock, b, &ticks) < 0) return;   /* not yet on the timeline */
    size_t need = 16 + (size_t)b->n_frames * 8;
    if (need > g_arec_cap){ uint8_t *n = realloc(g_arec, need); if (!n) return; g_arec = n; g_arec_cap = need; }
    put64(g_arec, ticks); put32(g_arec + 8, b->n_frames); put32(g_arec + 12, b->flags);
    const uint8_t *p = b->s24le; float *o = (float *)(void *)(g_arec + 16);
    for (uint32_t i = 0; i < b->n_frames; i++){
        int32_t l = (int32_t)((uint32_t)p[0] << 8 | (uint32_t)p[1] << 16 | (uint32_t)p[2] << 24);
        int32_t r = (int32_t)((uint32_t)p[3] << 8 | (uint32_t)p[4] << 16 | (uint32_t)p[5] << 24);
        o[2 * i] = (float)l / 2147483648.0f; o[2 * i + 1] = (float)r / 2147483648.0f; p += AP_BYTES_PER_FRAME;
    }
    emit(REC_AUDIO, g_arec, (uint32_t)need);
}

static void on_end(void *ctx, enum cc_end r){
    (void)ctx;
    pthread_mutex_lock(&g_end_m); g_ended = 1; g_reason = r; pthread_cond_broadcast(&g_end_c); pthread_mutex_unlock(&g_end_m);
}

static int probe(const char *path){
    fs_replay_span sp; memset(&sp, 0, sizeof sp);
    int ok = fs_replay_probe(path, 0, NULL, &sp) == 0;
    rt_timeline tl;
    if (!ok || rt_init(&tl, sp.file_bytes, sp.first_counter, sp.last_counter) != 0){
        printf("{\"error\":\"%s\"}\n", sp.incomplete ? "the file could not be read to its end" :
               !sp.have_first ? "no complete picture unit near the start of the file" : "no complete picture unit near the end of the file");
        return 1;
    }
    printf("{\"file_bytes\":%" PRIu64 ",\"units\":%" PRIu64 ",\"first16\":%u,\"first_counter\":%u,\"last_counter\":%u}\n",
           tl.file_bytes, tl.units, tl.first16, sp.first_counter, sp.last_counter);
    return 0;
}

static int flag01(const char *v, const char *name){
    if (!strcmp(v, "1") || !strcmp(v, "on")) return 1;
    if (!strcmp(v, "0") || !strcmp(v, "off")) return 0;
    fprintf(stderr, "%s: expected on/off or 1/0, got %s\n", name, v); exit(2);
}

/* Reader gone (EOF on stdout's pipe surfaces as EPIPE): end the replay at once rather than run to the file's end. */
static void *closed_watch(void *arg){
    frameserver *f = arg;
    while (!atomic_load(&g_out_closed)){
        pthread_mutex_lock(&g_end_m); int e = g_ended; pthread_mutex_unlock(&g_end_m);
        if (e) return NULL;
        usleep(50000);                                  /* liveness backstop only: the end itself is signalled */
    }
    (void)f; on_end(NULL, CC_END_STOPPED);
    return NULL;
}

int main(int argc, char **argv){
    signal(SIGPIPE, SIG_IGN);
    if (argc >= 3 && !strcmp(argv[1], "probe")) return probe(argv[2]);
    if (argc < 3 || strcmp(argv[1], "play")){
        fprintf(stderr, "usage: tpc_play probe FILE | tpc_play play FILE [--start-unit U --units N --first16 F] [--registration on|off]"
                        " [--hretime 0|1] [--partial 0|1] [--repair 0|1] [--first-line F1,F2]\n");
        return 2;
    }
    const char *path = argv[2];
    fs_config cfg; memset(&cfg, 0, sizeof cfg);
    cfg.registration_off = 1; cfg.hretime = 0; cfg.show_partial = 1; cfg.repair_units = 1;
    uint64_t units = 0; long first16 = -1;
    for (int i = 3; i < argc; i += 2){
        const char *a = argv[i], *v = i + 1 < argc ? argv[i + 1] : NULL;
        if (!v){ fprintf(stderr, "%s needs a value\n", a); return 2; }
        if (!strcmp(a, "--start-unit")) g_start_unit = strtoull(v, NULL, 10);
        else if (!strcmp(a, "--units")) units = strtoull(v, NULL, 10);
        else if (!strcmp(a, "--first16")) first16 = strtol(v, NULL, 10);
        else if (!strcmp(a, "--registration")) cfg.registration_off = !flag01(v, a);
        else if (!strcmp(a, "--hretime")) cfg.hretime = flag01(v, a);
        else if (!strcmp(a, "--partial")) cfg.show_partial = flag01(v, a);
        else if (!strcmp(a, "--repair")) cfg.repair_units = flag01(v, a);
        else if (!strcmp(a, "--first-line")){
            if (sscanf(v, "%d,%d", &cfg.first_line_f1, &cfg.first_line_f2) != 2){ fprintf(stderr, "--first-line: expected F1,F2\n"); return 2; }
        } else { fprintf(stderr, "unknown option %s\n", a); return 2; }
    }
    if (!cfg.registration_off) cfg.repair_units = 0;    /* the frameserver refuses repair with registration on */
    struct stat st;
    if (stat(path, &st) != 0){ fprintf(stderr, "%s: %s\n", path, strerror(errno)); return 1; }
    if (units && first16 >= 0){
        g_tl.file_bytes = (uint64_t)st.st_size; g_tl.units = units; g_tl.first16 = (uint16_t)first16; g_have_tl = 1;
        if (g_start_unit > units) g_start_unit = units;
    } else g_start_unit = 0;
    g_vrec = malloc(32 + VIDEO_BYTES);
    if (!g_vrec) return 1;

    cfg.capture.replay_path = path;
    cfg.capture.replay_pace_us = 0;                     /* the reader paces (see the top) */
    cfg.capture.replay_start_offset = g_have_tl ? rt_offset(&g_tl, g_start_unit) : 0;
    cfg.offline_backpressure = 1;
    cfg.surface_pool = 6;
    cfg.sink.on_frame = on_frame; cfg.audio_sink.on_block = on_audio;
    cfg.on_end = on_end;
    frameserver *f = NULL;
    if (fs_open(&f, &cfg) != 0){ fprintf(stderr, "frameserver open failed: %s\n", path); return 1; }
    if (fs_start(f) != 0){ fprintf(stderr, "frameserver start failed\n"); fs_close(f); return 1; }
    pthread_t w; pthread_create(&w, NULL, closed_watch, f);
    pthread_mutex_lock(&g_end_m);
    while (!g_ended) pthread_cond_wait(&g_end_c, &g_end_m);
    enum cc_end reason = g_reason;
    pthread_mutex_unlock(&g_end_m);
    int reader_gone = atomic_load(&g_out_closed);
    fs_stop(f);
    pthread_join(w, NULL);
    fs_stats s; fs_get_stats(f, &s);
    char js[1024];
    int n = snprintf(js, sizeof js, "{\"reason\":\"%s\",\"published\":%" PRIu64 ",\"exact_units\":%" PRIu64 ",\"short_units\":%" PRIu64
                     ",\"holes\":%" PRIu64 ",\"partial_shown\":%" PRIu64 ",\"repaired\":%" PRIu64 ",\"repair_declined\":%" PRIu64
                     ",\"no_signal_0800\":%" PRIu64 ",\"audio_frames\":%" PRIu64 ",\"audio_dropped_frames\":%" PRIu64 "}",
                     reader_gone ? "reader_closed" : reason == CC_END_REPLAY_EOF ? "eof" : reason == CC_END_STOPPED ? "stopped" : "error",
                     s.published, s.exact_units, s.short_units, s.holes, s.partial_shown, s.repaired_units, s.repair_declined,
                     s.no_signal_0800, s.audio_frames_delivered, s.audio_dropped_frames);
    if (!reader_gone) emit(REC_END, (const uint8_t *)js, (uint32_t)n);
    fprintf(stderr, "tpc_play: %s\n", js);
    fs_close(f);
    return 0;
}
