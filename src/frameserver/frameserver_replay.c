// frameserver_replay <capture.tpc> [decision_log.csv] [--pace-us N] [--ring-mb N] [--pool N]
//                    [--dump-uyvy FILE] [--dump-pcm FILE] [--dump-log FILE] [--limit-units N]
// Run the whole P3 pipeline on a recorded capture (no hardware) and print the accounting.
// --dump-*: write exactly what the frameserver publishes — every 480i UYVY frame (720x480x2 B,
// TFF, registration-corrected) and every delivered PCM block (S24LE stereo) — as an ordinary
// downstream consumer would receive them, plus a log of per-frame/per-block timestamps for A/V
// alignment (video pts = counter*1001/30000; audio pts in 1/240000 s per audio_publisher.h).
// --limit-units N stops after N published frames (from the control thread, never a callback).
// Unpaced replay streams at disk speed and deliberately overloads the live path (holes and
// drops are then REAL and reported); --pace-us 16000 is the device's own cadence (realtime),
// 8000 is 2x. Exit 0 when the pipeline drained.
#include "frameserver.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdatomic.h>
#include <IOSurface/IOSurface.h>
static _Atomic int done;
static void on_end(void *c, enum cc_end r){ (void)c; done = 1 + (int)r; }
static FILE *g_vdump, *g_adump, *g_log; static _Atomic unsigned long long g_frames; static unsigned long long g_limit;
static void dump_frame(void *c, const fp_frame *fr){
    (void)c; if (!fr->surface) return;
    if (g_vdump){
        IOSurfaceLock(fr->surface, kIOSurfaceLockReadOnly, NULL);
        const uint8_t *base = IOSurfaceGetBaseAddress(fr->surface); size_t bpr = IOSurfaceGetBytesPerRow(fr->surface);
        for (unsigned y = 0; y < FP_FRAME_HEIGHT; y++) fwrite(base + (size_t)y * bpr, 1, FP_FRAME_WIDTH * 2, g_vdump);
        IOSurfaceUnlock(fr->surface, kIOSurfaceLockReadOnly, NULL);
    }
    if (g_log) fprintf(g_log, "V,%llu,%llu,%u,%d,%d,%u,%d,%llu\n", (unsigned long long)fr->counter_ext, (unsigned long long)fr->pts_num, fr->pts_den,
                       fr->d1, fr->d2, fr->transport, fr->audio_pts_known, (unsigned long long)fr->audio_pts_num);
    atomic_fetch_add(&g_frames, 1);
}
static void dump_audio(void *c, const ap_block *b){
    (void)c;
    if (g_adump) fwrite(b->s24le, AP_BYTES_PER_FRAME, b->n_frames, g_adump);
    if (g_log) fprintf(g_log, "A,%llu,%llu,%u,%u,%u,%llu,%lld\n", (unsigned long long)b->sample_ordinal, (unsigned long long)b->pts_num, b->pts_den,
                       b->n_frames, b->flags, (unsigned long long)b->last_resync_counter_ext, (long long)b->correlation_residual);
}
int main(int argc, char **argv){
    if (argc < 2){ fprintf(stderr, "usage: %s <capture.tpc> [decision_log.csv] [--pace-us N] [--ring-mb N] [--pool N]\n", argv[0]); return 9; }
    fs_config cfg = {0}; cfg.capture.replay_path = argv[1]; cfg.on_end = on_end;
    for (int i = 2; i < argc; i++){
        if (!strcmp(argv[i], "--pace-us") && i + 1 < argc) cfg.capture.replay_pace_us = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--ring-mb") && i + 1 < argc) cfg.capture.ring_mb = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--pool") && i + 1 < argc) cfg.pool_units = (unsigned)atoi(argv[++i]);
        else if (!strcmp(argv[i], "--dump-uyvy") && i + 1 < argc){ g_vdump = fopen(argv[++i], "wb"); if (!g_vdump){ perror("dump-uyvy"); return 1; } }
        else if (!strcmp(argv[i], "--dump-pcm") && i + 1 < argc){ g_adump = fopen(argv[++i], "wb"); if (!g_adump){ perror("dump-pcm"); return 1; } }
        else if (!strcmp(argv[i], "--dump-log") && i + 1 < argc){ g_log = fopen(argv[++i], "w"); if (!g_log){ perror("dump-log"); return 1; }
            fprintf(g_log, "kind,counter_or_ordinal,pts_num,pts_den,d1_or_frames,d2_or_flags,transport_or_resync,audio_pts_known_or_residual,audio_pts_num\n"); }
        else if (!strcmp(argv[i], "--limit-units") && i + 1 < argc) g_limit = strtoull(argv[++i], NULL, 10);
        else if (argv[i][0] != '-') cfg.decision_log = argv[i];
    }
    if (g_vdump || g_log) cfg.sink.on_frame = dump_frame;
    if (g_adump || g_log) cfg.audio_sink.on_block = dump_audio;
    frameserver *f = NULL;
    if (fs_open(&f, &cfg) != 0){ fprintf(stderr, "open failed\n"); return 1; }
    if (fs_start(f) != 0){ fprintf(stderr, "start failed\n"); return 1; }
    while (!done){ if (g_limit && atomic_load(&g_frames) >= g_limit) break; usleep(20000); }
    fs_stop(f);
    if (g_vdump && fclose(g_vdump)) perror("dump-uyvy close");
    if (g_adump && fclose(g_adump)) perror("dump-pcm close");
    if (g_log && fclose(g_log)) perror("dump-log close");
    fs_stats s; fs_get_stats(f, &s);
    printf("video obs %llu | exact %llu short %llu hole %llu unframed %llu other %llu 0x0800 %llu\n",
        (unsigned long long)s.video_observations, (unsigned long long)s.exact_units, (unsigned long long)s.short_units,
        (unsigned long long)s.holes, (unsigned long long)s.unframed, (unsigned long long)s.other_format, (unsigned long long)s.no_signal_0800);
    printf("published %llu | dropped(pool) %llu dropped(ring) %llu dropped(surfaces) %llu | unsettled %llu | begin_segment %llu discontinuity %llu | log rows %llu | pool high %u\n",
        (unsigned long long)s.published, (unsigned long long)s.dropped_pool_full, (unsigned long long)s.dropped_ring_full, (unsigned long long)s.publisher_dropped,
        (unsigned long long)s.unsettled_units, (unsigned long long)s.begin_segment_calls, (unsigned long long)s.discontinuity_calls,
        (unsigned long long)s.log_rows, s.pool_high_water);
    printf("eligible ingress %llu = processed exact %llu + eligible ring loss %llu | ring loss logged %llu in %llu terminal range rows\n",
        (unsigned long long)s.eligible_observations,(unsigned long long)s.exact_units,
        (unsigned long long)s.eligible_ring_drops,(unsigned long long)s.ring_drops_logged,
        (unsigned long long)s.ring_gap_rows);
    printf("audio records %llu (resync %llu) | pcm %llu -> published %llu frames in %llu blocks (unanchored %llu, discontinuities %llu)\n",
        (unsigned long long)s.audio_records, (unsigned long long)s.audio_resync, (unsigned long long)s.audio_pcm_records,
        (unsigned long long)s.audio_frames_published, (unsigned long long)s.audio_blocks,
        (unsigned long long)s.audio_blocks_unanchored, (unsigned long long)s.audio_discontinuities);
    printf("audio sink: delivered %llu blocks / %llu frames, dropped %llu / %llu | counter gaps %llu | residual [%lld, %lld] ticks | frames with audio-clock pts %llu\n",
        (unsigned long long)s.audio_blocks_delivered, (unsigned long long)s.audio_frames_delivered,
        (unsigned long long)s.audio_dropped_blocks, (unsigned long long)s.audio_dropped_frames,
        (unsigned long long)s.audio_counter_gaps, (long long)s.audio_residual_min, (long long)s.audio_residual_max,
        (unsigned long long)s.audio_master_frames);
    fs_close(f);
    return 0;
}
