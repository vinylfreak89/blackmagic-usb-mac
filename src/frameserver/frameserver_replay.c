// frameserver_replay <capture.tpc> [decision_log.csv] [--pace-us N] [--ring-mb N] [--pool N]
//                    [--dump-uyvy FILE] [--dump-pcm FILE] [--dump-log FILE] [--limit-units N] [--stall-s N]
//                    [--start-offset BYTES]
// frameserver_replay --probe <capture.tpc>   print the file's first and last unit counters (replay_probe.h)
//                    [--pair-next | --pairing-schedule FILE]
// Approved geometry is the default; --geometry-v11 / --audit-comb are compatibility no-ops.
// Run the whole P3 pipeline on a recorded capture (no hardware) and print the accounting.
// --dump-*: write exactly what the frameserver publishes — every 480i UYVY frame (720x480x2 B,
// TFF, registration-corrected) and every delivered PCM block (S24LE stereo) — as an ordinary
// downstream consumer would receive them, plus a log of per-frame/per-block timestamps for A/V
// alignment (video pts = counter*1001/30000; audio pts in 1/240000 s per audio_publisher.h).
// --limit-units N stops after N published frames (from the control thread, never a callback).
// Unpaced replay streams at disk speed and deliberately overloads the live path (holes and
// drops are then REAL and reported); --pace-us 16000 is the device's own cadence (realtime),
// 8000 is 2x. Exit 3 on no completed capture-core packet delivery for --stall-s seconds
// (default 120) or ten --pace-us intervals, whichever is longer. Empty packets count.
// Blocking startup, stop, file flush/close and final output each have a 60 s watchdog
// (FS_LIFECYCLE_S overrides for tests). Timeout outputs are incomplete, never a clean result.
#include "frameserver.h"
#include "replay_probe.h"
#include "../field_registration/geometry_tool_controls.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdatomic.h>
#include <time.h>
#include <signal.h>
#include <IOSurface/IOSurface.h>
#include "../tool_deadline.h"
static _Atomic int done;
static double stall_s = 120;
static void on_end(void *c, enum cc_end r){ (void)c; done = 1 + (int)r; }
static FILE *g_vdump, *g_adump, *g_log; static _Atomic unsigned long long g_frames; static unsigned long long g_limit;
static frameserver *g_fs; static uint64_t g_handoff_limit_ns, g_last_handoff, g_late, g_worst;
#define LATE_MAX 4096
typedef struct { uint64_t counter, gap; fs_handoff_timing h; } late_event;
static late_event g_late_ev[LATE_MAX]; static size_t g_late_n;
static void handoff_check(const fp_frame *fr){
    if(!g_handoff_limit_ns) return;
    uint64_t now=clock_gettime_nsec_np(CLOCK_UPTIME_RAW), gap=g_last_handoff?now-g_last_handoff:0;
    g_last_handoff=now;
    if(gap>g_worst) g_worst=gap;
    if(gap<=g_handoff_limit_ns) return;
    g_late++;
    /* recorded, printed after the run: a stderr write here is a disk write on the worker, and under
     * disk load it made the NEXT handoff late (every large gap in the first stress run followed one) */
    if(g_late_n<LATE_MAX){ late_event *e=&g_late_ev[g_late_n++]; e->counter=fr->counter_ext; e->gap=gap; fs_handoff_timing_get(g_fs,&e->h); }
}
static void handoff_report(void){
    for(size_t i=0;i<g_late_n;i++){ const late_event *e=&g_late_ev[i]; const fs_handoff_timing *h=&e->h;
        fprintf(stderr,"LATE counter %llu gap %.1f ms | since prev %.1f: idle %.1f classify %.1f registration %.1f h-retiming %.1f sidecar %.1f other %.1f; %u items; queued %.1f\n",
                (unsigned long long)e->counter,e->gap/1e6,h->since_prev_ns/1e6,h->idle_ns/1e6,h->classify_ns/1e6,h->geometry_ns/1e6,h->hretime_ns/1e6,h->log_ns/1e6,h->other_ns/1e6,h->items,h->queue_wait_ns/1e6); }
    if(g_late>g_late_n) fprintf(stderr,"LATE: %llu more not recorded (first %d kept)\n",(unsigned long long)(g_late-g_late_n),LATE_MAX);
}
static void dump_frame(void *c, const fp_frame *fr){
    (void)c; handoff_check(fr); if (!fr->surface) return;
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
    ge_config geometry=ge_default_config();
    if(!ge_tool_controls_from_env(&geometry))return 2;
    ge_tool_controls_echo(stderr,&geometry);
    tool_deadline_start("frameserver_replay",3);
    double lifecycle_s=tool_seconds(getenv("FS_LIFECYCLE_S"),60);
    tool_guard("open outputs / fs_open / fs_start",lifecycle_s);
    if (argc < 2){ fprintf(stderr, "usage: %s <capture.tpc> [decision_log.csv] [--pace-us N] [--ring-mb N] [--pool N]\n", argv[0]); return 9; }
    if (argc == 3 && !strcmp(argv[1], "--probe")){
        fs_replay_span sp; int rc = fs_replay_probe(argv[2], 0, NULL, &sp);
        printf("file_bytes %llu first_counter %s%u last_counter %s%u\n", (unsigned long long)sp.file_bytes,
               sp.have_first ? "" : "(none) ", sp.first_counter, sp.have_last ? "" : "(none) ", sp.last_counter);
        return rc == 0 ? 0 : 1;
    }
    fs_config cfg = {0}; cfg.geometry_config=&geometry; cfg.capture.replay_path = argv[1]; cfg.on_end = on_end;
    const char *retime=getenv("FS_HRETIME");
    if(retime && strcmp(retime,"0") && strcmp(retime,"1")) {
        fputs("FS_HRETIME must be 0 or 1\n",stderr);return 2;
    }
    cfg.hretime=retime && !strcmp(retime,"1");
    cfg.show_partial=getenv("FS_SHOW_PARTIAL") && !strcmp(getenv("FS_SHOW_PARTIAL"),"1");
    const char *regoff=getenv("FS_REGISTRATION_OFF");
    if(regoff && strcmp(regoff,"0") && strcmp(regoff,"1")) {
        fputs("FS_REGISTRATION_OFF must be 0 or 1\n",stderr);return 2;
    }
    cfg.registration_off=regoff && !strcmp(regoff,"1");
    for (int i = 2; i < argc; i++){
        if (!strcmp(argv[i], "--pace-us") && i + 1 < argc) cfg.capture.replay_pace_us = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--ring-mb") && i + 1 < argc) cfg.capture.ring_mb = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--pool") && i + 1 < argc) cfg.pool_units = (unsigned)atoi(argv[++i]);
        else if (!strcmp(argv[i], "--geometry-v11")) {} /* compatibility; now the default */
        else if (!strcmp(argv[i], "--pair-next")) cfg.geometry_pair_next=1;
        else if (!strcmp(argv[i], "--pairing-schedule")) {
            if(i+1==argc || argv[i+1][0]=='-' || cfg.pairing_schedule){fprintf(stderr,"--pairing-schedule requires one FILE\n");return 9;}
            cfg.pairing_schedule=argv[++i];
        }
        else if (!strcmp(argv[i], "--audit-comb")) {} /* comb evidence is always measured */
        else if (!strcmp(argv[i], "--dump-uyvy") && i + 1 < argc){ g_vdump = fopen(argv[++i], "wb"); if (!g_vdump){ perror("dump-uyvy"); return 1; } }
        else if (!strcmp(argv[i], "--dump-pcm") && i + 1 < argc){ g_adump = fopen(argv[++i], "wb"); if (!g_adump){ perror("dump-pcm"); return 1; } }
        else if (!strcmp(argv[i], "--dump-log") && i + 1 < argc){ g_log = fopen(argv[++i], "w"); if (!g_log){ perror("dump-log"); return 1; }
            fprintf(g_log, "kind,counter_or_ordinal,pts_num,pts_den,d1_or_frames,d2_or_flags,transport_or_resync,audio_pts_known_or_residual,audio_pts_num\n"); }
        else if (!strcmp(argv[i], "--limit-units") && i + 1 < argc) g_limit = strtoull(argv[++i], NULL, 10);
        else if (!strcmp(argv[i], "--start-offset") && i + 1 < argc) cfg.capture.replay_start_offset = strtoull(argv[++i], NULL, 10);
        else if (!strcmp(argv[i], "--stall-s") && i + 1 < argc) stall_s = tool_seconds(argv[++i],120);
        else if (argv[i][0] != '-') cfg.decision_log = argv[i];
    }
    if(cfg.pairing_schedule && cfg.geometry_pair_next){fprintf(stderr,"--pairing-schedule and --pair-next are mutually exclusive\n");return 9;}
    { const char *lim=getenv("FS_HANDOFF_LOG_MS"); if(lim&&*lim) g_handoff_limit_ns=(uint64_t)(atof(lim)*1e6); }
    if (g_vdump || g_log || g_limit || g_handoff_limit_ns) cfg.sink.on_frame = dump_frame;
    if (g_adump || g_log) cfg.audio_sink.on_block = dump_audio;
    frameserver *f = NULL;
    { const char *dg=getenv("FS_REPLAY_DIAG"); cfg.capture.replay_diag=dg&&*dg&&strcmp(dg,"0"); }   /* capture-core stall diagnosis to stderr */
    if (fs_open(&f, &cfg) != 0){ fprintf(stderr, "open failed\n"); return 1; }
    g_fs = f;
    if (fs_start(f) != 0){ fprintf(stderr, "start failed\n"); return 1; }
    const char *tee_path=getenv("FS_TEE");   /* test/diagnostic: raw .tpc tee of the replayed stream */
    if(tee_path && *tee_path && fs_tee_start(f,tee_path,"frameserver tee v1 input=replay",256u<<20)!=0){ fprintf(stderr,"tee start failed: %s\n",tee_path); return 1; }
    tool_guard(NULL,0);
    double limit=tool_stall_seconds(stall_s,cfg.capture.replay_pace_us);
    uint64_t seen = fs_packets_delivered(f); double last_progress = tool_clock();
    while (!done){
        if (g_limit && atomic_load(&g_frames) >= g_limit) break;
        usleep(20000);
#ifdef REPLAY_TEST_HOOKS
        extern void replay_test_after_sleep(_Atomic int *ended);
        replay_test_after_sleep(&done);
#endif
        if (done) break;
        uint64_t now = fs_packets_delivered(f);
        if (now != seen){ seen = now; last_progress = tool_clock(); continue; }
        if (tool_clock() - last_progress >= limit && !done)
            tool_timeout("no capture-core packet delivery before stall deadline; output incomplete");
    }
    tool_guard("fs_stop",lifecycle_s);
    fs_stop(f);
    if(g_handoff_limit_ns) handoff_report();
    if(g_handoff_limit_ns) fprintf(stderr,"handoffs: %llu later than %.0f ms, worst gap %.1f ms\n",(unsigned long long)g_late,g_handoff_limit_ns/1e6,g_worst/1e6);
    tool_guard("flush/close dump outputs",lifecycle_s);
    if (g_vdump && fclose(g_vdump)) perror("dump-uyvy close");
    if (g_adump && fclose(g_adump)) perror("dump-pcm close");
    if (g_log && fclose(g_log)) perror("dump-log close");
    tool_guard("final accounting/output and fs_close",lifecycle_s);
    fs_stats s; fs_get_stats(f, &s);
    printf("video obs %llu | exact %llu short %llu hole %llu unframed %llu other %llu 0x0800 %llu\n",
        (unsigned long long)s.video_observations, (unsigned long long)s.exact_units, (unsigned long long)s.short_units,
        (unsigned long long)s.holes, (unsigned long long)s.unframed, (unsigned long long)s.other_format, (unsigned long long)s.no_signal_0800);
    if(s.partial_shown) printf("search frames shown from units that were not whole: %llu\n",(unsigned long long)s.partial_shown);
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
    fflush(stdout); fflush(stderr); /* Still guarded, including normal process cleanup. */
    return 0;
}
