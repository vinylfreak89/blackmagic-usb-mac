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
#include <signal.h>
#include <stdatomic.h>
#include <pthread.h>
static int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { fails++; fprintf(stderr, "FAIL: " __VA_ARGS__); fprintf(stderr, "\n"); } } while (0)
static _Atomic int done; static _Atomic uint64_t frames_seen; static _Atomic int sink_stall_us, sink_hold;
static IOSurfaceRef held_surface;
static _Atomic int hook_arm, hook_empty, hook_release;
void fs_test_after_empty_snapshot(frameserver *f){
    (void)f; if(atomic_load(&hook_arm) && !atomic_exchange(&hook_empty,1))
        while(!atomic_load(&hook_release)) usleep(100);
}
void fs_test_before_producer_done(frameserver *f){ (void)f; if(atomic_load(&hook_arm)) atomic_store(&hook_release,1); }
static _Atomic int log_stall_us; static _Atomic int log_stalled;   // storage-stall injection: the first row after arming blocks inside the row lock
static _Atomic int log_break;   // write-failure injection: swap the stream's fd for a pipe with no reader (EPIPE on every write; SIGPIPE ignored), unbuffered so each row fprintf fails
void fs_test_after_log_row(frameserver *f, FILE *log){ (void)f; int st=atomic_exchange(&log_stall_us,0); if(st){ atomic_store(&log_stalled,1); usleep(st); }
    if(atomic_exchange(&log_break,0)){ int p[2]; if(pipe(p)!=0) abort(); close(p[0]); fflush(log); if(dup2(p[1],fileno(log))<0) abort(); close(p[1]); setvbuf(log,NULL,_IONBF,0); } }
static frameserver *g_cb_target; static _Atomic int cb_try, cb_start_rc, cb_stop_rc;   // callback-refusal probe
static _Atomic int end_calls;
static void on_end(void *c, enum cc_end r){ (void)c; (void)r; atomic_fetch_add(&end_calls, 1); done = 1; }
static _Atomic uint64_t audio_frames_seen; static _Atomic int audio_flagged_blocks; static _Atomic uint64_t audio_last_pts; static _Atomic int audio_pts_nonmonotonic;
static _Atomic int audio_sink_stall_us; static _Atomic int audio_after_end; static _Atomic int ordinal_break;
static uint64_t audio_next_ordinal; static int audio_have_next;
#define CORR_MAX 64
static uint64_t corr_ctr[CORR_MAX], corr_pts[CORR_MAX]; static _Atomic int corr_n;   // first block after resync c: its pts is the audio-clock time of unit c
static void audio_sink(void *c, const ap_block *b){ (void)c; atomic_fetch_add(&audio_frames_seen, b->n_frames);
    if (done) atomic_store(&audio_after_end, 1);
    if (audio_have_next && !(b->flags & AP_FLAG_DISCONTINUITY_BEFORE) && b->sample_ordinal != audio_next_ordinal) atomic_store(&ordinal_break, 1);
    audio_next_ordinal = b->sample_ordinal + b->n_frames; audio_have_next = 1;
    if (!(b->flags & AP_FLAG_UNANCHORED) && b->last_resync_counter_ext && atomic_load(&corr_n) < CORR_MAX){ int n = atomic_load(&corr_n); corr_ctr[n] = b->last_resync_counter_ext; corr_pts[n] = b->pts_num; atomic_store(&corr_n, n + 1); }
    int st = atomic_load(&audio_sink_stall_us); if (st) usleep(st);
    if (b->flags & AP_FLAG_DISCONTINUITY_BEFORE) atomic_fetch_add(&audio_flagged_blocks, 1);
    if (!(b->flags & (AP_FLAG_UNANCHORED|AP_FLAG_DISCONTINUITY_BEFORE)) && b->pts_num < atomic_load(&audio_last_pts)) atomic_store(&audio_pts_nonmonotonic, 1);
    if (!(b->flags & AP_FLAG_UNANCHORED)) atomic_store(&audio_last_pts, b->pts_num); }
static uint64_t vf_ctr[CORR_MAX], vf_apts[CORR_MAX]; static _Atomic int vf_n; static _Atomic int video_after_end;
static void sink(void *c, const fp_frame *fr){ (void)c; if (fr->surface) atomic_fetch_add(&frames_seen, 1);
    if (atomic_exchange(&cb_try,0) && g_cb_target){ atomic_store(&cb_start_rc, fs_log_start(g_cb_target,"/tmp/fs_test_from_callback.csv")); atomic_store(&cb_stop_rc, fs_log_stop(g_cb_target)); }
    if (done) atomic_store(&video_after_end, 1);
    if (fr->audio_pts_known && atomic_load(&vf_n) < CORR_MAX){ int n = atomic_load(&vf_n); vf_ctr[n] = fr->counter_ext; vf_apts[n] = fr->audio_pts_num; atomic_store(&vf_n, n + 1); }
    if(atomic_load(&sink_hold)&&!held_surface){ IOSurfaceIncrementUseCount(fr->surface); held_surface=fr->surface; }
    int st = atomic_load(&sink_stall_us); if (st) usleep(st); }   // a slow consumer holds the slot
/* Observation-driven waits (no fixed sleeps): block until the sink has seen `n` more frames than
 * `base`, or the session ended, or a 20 s cap — so the windows below are defined by delivered
 * frames, not wall time, and survive sanitizer slowdowns. */
static int wait_frames(unsigned long long base, unsigned long long n){
    for (int i = 0; i < 2000; i++){ if (atomic_load(&frames_seen) >= base + n) return 1; if (done) return 0; usleep(10000); }
    return 0;
}
typedef struct { frameserver *f; int rc; } fs_stop_arg;
static void *fs_stop_thread(void *p){ fs_stop_arg *a=p; a->rc=fs_stop(a->f); return NULL; }
static int repeat_fixture(const char *src,const char *dst,int copies){
    FILE *in=fopen(src,"rb"),*out=fopen(dst,"wb"); if(!in||!out){ if(in)fclose(in); if(out)fclose(out); return -1; }
    char b[65536];
    for(int i=0;i<copies;i++){
        rewind(in); for(;;){ size_t n=fread(b,1,sizeof b,in); if(n&&fwrite(b,1,n,out)!=n){ fclose(in);fclose(out);return -1; } if(n<sizeof b) break; }
    }
    fclose(in); return fclose(out);
}
static unsigned csv_fields(const char *line){
    unsigned n=1; for(const char *p=line;*p;p++) if(*p==',') n++; return n;
}
int main(int argc, char **argv){
    if (argc < 2){ fprintf(stderr, "usage: %s <fixture.tpc>\n", argv[0]); return 9; }
    signal(SIGPIPE, SIG_IGN);   /* the write-failure injection writes to a reader-less pipe */
    int ring_may_drop = getenv("FS_TEST_EXPECT_RING_DROPS") != NULL;
    char logp[] = "/tmp/fs_test_log_XXXXXX"; int fd = mkstemp(logp); close(fd); unlink(logp);
    fs_config cfg = {0}; cfg.capture.replay_path = argv[1]; cfg.decision_log = logp; cfg.on_end = on_end;
    cfg.sink.on_frame = sink; cfg.pool_units = 4; cfg.surface_pool = 3; cfg.audio_sink.on_block = audio_sink;
    frameserver *f = NULL;
    CHECK(fs_open(&f, &cfg) == 0, "open");
    atomic_store(&hook_arm,!ring_may_drop); atomic_store(&hook_empty,0); atomic_store(&hook_release,0);
    CHECK(fs_start(f) == 0, "start");
    while (!done) usleep(10000);
    CHECK(fs_stop(f) == 0, "stop");
    if(!ring_may_drop) CHECK(atomic_load(&hook_empty),"worker empty-snapshot race hook was not exercised");
    atomic_store(&hook_arm,0);
    fs_stats s; fs_get_stats(f, &s);
    CHECK(s.video_observations > 0, "fixture produced video observations");
    CHECK(s.log_rows+s.dropped_ring_full==s.video_observations+s.ring_gap_rows,
          "sidecar observation/range conservation failed");
    CHECK(s.published + s.dropped_pool_full + s.publisher_dropped == s.exact_units, "exact units are published or counted as drops (%llu+%llu+%llu vs %llu)",
          (unsigned long long)s.published, (unsigned long long)s.dropped_pool_full, (unsigned long long)s.publisher_dropped, (unsigned long long)s.exact_units);
    CHECK(atomic_load(&frames_seen) == s.published, "sink saw every published frame");
    CHECK(s.discontinuity_calls > 0, "hole/short/unframed observations never reached the engine as discontinuities");
    CHECK(s.audio_pcm_records > 0 && s.audio_frames_published == s.audio_pcm_records, "audio conservation: %llu pcm records vs %llu frames published",
          (unsigned long long)s.audio_pcm_records, (unsigned long long)s.audio_frames_published);
    CHECK(!atomic_load(&ordinal_break), "delivered audio blocks are ordinal-contiguous except where flagged");
    CHECK(!atomic_load(&audio_after_end) && !atomic_load(&video_after_end), "no media callback after on_end (on_end means both workers drained)");
    { int matched = 0, mismatched = 0;   // every video frame with an audio-clock pts must agree with the first audio block after that unit's resync
      for (int i = 0; i < atomic_load(&vf_n); i++) for (int j = 0; j < atomic_load(&corr_n); j++) if (corr_ctr[j] == vf_ctr[i]){ if (corr_pts[j] == vf_apts[i]) matched++; else mismatched++; break; }
      CHECK(mismatched == 0 && matched == (int)s.audio_master_frames, "fp_frame.audio_pts_num propagates the audio-clock time (%d matched, %d mismatched, %llu stamped)", matched, mismatched, (unsigned long long)s.audio_master_frames); }
    CHECK(s.audio_discontinuities >= 1, "the fixture's audio hole must surface as a discontinuity");
    CHECK(atomic_load(&audio_frames_seen) == s.audio_frames_published && atomic_load(&audio_flagged_blocks) >= 1, "sink saw every frame and the flagged block");
    CHECK(!atomic_load(&audio_pts_nonmonotonic), "anchored audio pts went backwards within a contiguous run");
    CHECK(s.audio_frames_delivered + s.audio_dropped_frames == s.audio_frames_published && s.audio_dropped_frames == 0,
          "audio queue accounts every frame (delivered %llu + dropped %llu vs published %llu)",
          (unsigned long long)s.audio_frames_delivered, (unsigned long long)s.audio_dropped_frames, (unsigned long long)s.audio_frames_published);
    CHECK(s.audio_master_frames <= s.published, "audio-clock pts count bounded by published frames (%llu of %llu)", (unsigned long long)s.audio_master_frames, (unsigned long long)s.published);
    printf("  audio: %llu blocks, %llu frames, residual [%lld,%lld] ticks, counter gaps %llu, frames with audio-clock pts %llu/%llu\n",
           (unsigned long long)s.audio_blocks, (unsigned long long)s.audio_frames_published, (long long)s.audio_residual_min, (long long)s.audio_residual_max,
           (unsigned long long)s.audio_counter_gaps, (unsigned long long)s.audio_master_frames, (unsigned long long)s.published);

    // Slow audio consumer with a one-block queue: drops happen HERE (explicit, flagged), never upstream.
    done = 0; atomic_store(&frames_seen, 0); atomic_store(&audio_frames_seen, 0); atomic_store(&audio_flagged_blocks, 0);
    atomic_store(&audio_after_end, 0); atomic_store(&video_after_end, 0); audio_have_next = 0;
    atomic_store(&audio_sink_stall_us, 50000);
    fs_config c5 = cfg; c5.decision_log = NULL; c5.audio_queue_blocks = 1;
    frameserver *q = NULL;
    CHECK(fs_open(&q, &c5) == 0, "open (slow audio sink)");
    CHECK(fs_start(q) == 0, "start (slow audio sink)");
    while (!done) usleep(10000);
    CHECK(fs_stop(q) == 0, "stop (slow audio sink)");
    atomic_store(&audio_sink_stall_us, 0);
    fs_stats s5; fs_get_stats(q, &s5);
    CHECK(s5.audio_dropped_blocks > 0, "slow sink with a one-block queue did not exercise the audio drop path");
    CHECK(s5.audio_frames_delivered + s5.audio_dropped_frames == s5.audio_frames_published, "slow sink: every frame delivered or explicitly dropped (%llu+%llu vs %llu)",
          (unsigned long long)s5.audio_frames_delivered, (unsigned long long)s5.audio_dropped_frames, (unsigned long long)s5.audio_frames_published);
    CHECK(s5.audio_frames_published == s5.audio_pcm_records, "slow sink never caused upstream loss in the publisher");
    CHECK(atomic_load(&audio_frames_seen) == s5.audio_frames_delivered, "sink saw exactly the delivered frames");
    CHECK(!atomic_load(&audio_after_end), "slow sink: on_end waited for the audio worker (no block after it)");
    CHECK(atomic_load(&end_calls) == 2, "on_end fired exactly once per started session so far (%d for 2 sessions: main + slow sink)", atomic_load(&end_calls));
    fs_stats c5c; fs_get_stats(q, &c5c); CHECK(c5c.holes == s.holes && c5c.video_observations == s.video_observations, "a slow audio sink must not change what the capture delivered");
    fs_close(q);
    CHECK(s.eligible_observations == s.exact_units+s.eligible_ring_drops,
          "eligible ingress conservation failed");
    if(!ring_may_drop) CHECK(s.short_units + s.holes + s.unframed + s.exact_units + s.other_format + s.no_signal_0800 >= s.video_observations, "every observation classified by transport/kind");
    // log integrity: header + rows, columns as the contract names them
    FILE *L = fopen(logp, "r"); char line[4096]; unsigned rows = 0; int hdr_ok = 0, row_shape_ok = 1; unsigned header_fields = 0;
    while (fgets(line, sizeof line, L)){
        if (rows == 0){ hdr_ok = strstr(line, "interval_id,unsettled,provisional_d1") != NULL && strstr(line, "f1_insert_bytes,f1_insert_relation,f1_parity_candidates") != NULL && strstr(line, "f1_gauge_amplitude,f1_geometry_d,f1_blank_mean") != NULL && strstr(line, "f2_lock_state,f2_zero_source,f2_lock_id") != NULL && strstr(line, "f2_lock_top,f2_lock_height,f2_lock_height_known,f2_clip_state,f2_clip_ceiling") != NULL; header_fields=csv_fields(line); }
        else if(csv_fields(line)!=header_fields) row_shape_ok=0;
        rows++;
    }
    fclose(L); unlink(logp);
    CHECK(hdr_ok, "decision-log header carries the contract fields");
    CHECK(row_shape_ok, "every decision-log row has the schema's %u columns", header_fields);
    CHECK(rows == s.log_rows + 1, "log rows on disk match (%u vs %llu)", rows, (unsigned long long)s.log_rows + 1);
    fs_close(f);

    // F4/F5: with a ONE-slot pool the delivery thread must shed bytes, but every observation
    // still gets a sidecar row, and shed units are marked PoolFull rather than silently absent.
    done = 0; atomic_store(&frames_seen, 0);
    char logp2[] = "/tmp/fs_test_log2_XXXXXX"; fd = mkstemp(logp2); close(fd); unlink(logp2);
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
    if(!ring_may_drop) CHECK(s2.dropped_pool_full > 0, "pool=1 with a stalled consumer did not exercise pool exhaustion");
    CHECK(s2.log_rows+s2.dropped_ring_full==s2.video_observations+s2.ring_gap_rows,
          "pool=1: sidecar observation/range conservation failed");
    if (!ring_may_drop){
        CHECK(s2.log_rows == s2.video_observations, "pool=1: one log row per observation (%llu vs %llu)", (unsigned long long)s2.log_rows, (unsigned long long)s2.video_observations);
        CHECK(s2.exact_units == s.exact_units, "pool size must not change how many exact units were observed (%llu vs %llu)", (unsigned long long)s2.exact_units, (unsigned long long)s.exact_units);
    }
    CHECK(s2.published + s2.dropped_pool_full + s2.publisher_dropped == s2.exact_units, "pool=1: exact units published or counted (%llu+%llu+%llu vs %llu)",
          (unsigned long long)s2.published, (unsigned long long)s2.dropped_pool_full, (unsigned long long)s2.publisher_dropped, (unsigned long long)s2.exact_units);
    CHECK(s2.exact_units + s2.eligible_ring_drops == s2.eligible_observations,
          "eligible conservation: %llu processed + %llu ring-dropped != %llu ingress",
          (unsigned long long)s2.exact_units,(unsigned long long)s2.eligible_ring_drops,
          (unsigned long long)s2.eligible_observations);
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
        char logp3[] = "/tmp/fs_test_log3_XXXXXX"; fd = mkstemp(logp3); close(fd); unlink(logp3);
        char ringcap[]="/tmp/fs_ring_capture_XXXXXX"; fd=mkstemp(ringcap); close(fd);
        CHECK(repeat_fixture(argv[1],ringcap,5)==0,"make repeated ring fixture");
        fs_config c4 = cfg; c4.decision_log = logp3; c4.pool_units = 8;
        c4.capture.replay_path=ringcap;
        c4.capture.replay_pace_us=10000; // loss while stalled, then retained post-gap observations
        atomic_store(&sink_stall_us, 100000);
        frameserver *r = NULL;
        CHECK(fs_open(&r, &c4) == 0, "open (small ring)");
        CHECK(fs_start(r) == 0, "start (small ring)");
        while (!done) usleep(10000);
        CHECK(fs_stop(r) == 0, "stop (small ring)");
        atomic_store(&sink_stall_us, 0);
        fs_stats s4; fs_get_stats(r, &s4);
        CHECK(s4.dropped_ring_full > 0, "small ring with a stalled consumer did not exercise ring exhaustion");
        unsigned long long col_sum = 0, last_ordinal=0; rows = 0;
        int have_last=0, chronology_ok=1, mid_ranges=0;
        L = fopen(logp3, "r");
        while (fgets(line, sizeof line, L)){
            if (rows){
                unsigned long long ord=strtoull(line,NULL,10); char *c=strrchr(line,',');
                unsigned long long n=c?strtoull(c+1,NULL,10):0; col_sum+=n;
                int tail=strstr(line,",RingFullTail,")!=NULL;
                if(n && have_last && tail && ord!=last_ordinal+1) chronology_ok=0;
                if(n && have_last && !tail && ord!=last_ordinal+n+1) chronology_ok=0;
                if(n && !tail) mid_ranges++;
                if(!tail){ last_ordinal=ord; have_last=1; }
            }
            rows++;
        }
        fclose(L); unlink(logp3); unlink(ringcap);
        CHECK(col_sum == s4.ring_drops_logged, "preceding_ring_drops column sum %llu != ring_drops_logged %llu", col_sum, (unsigned long long)s4.ring_drops_logged);
        CHECK(s4.ring_drops_logged == s4.dropped_ring_full, "not every ring drop was logged (%llu vs %llu)",(unsigned long long)s4.ring_drops_logged,(unsigned long long)s4.dropped_ring_full);
        CHECK(chronology_ok,"ring loss range was attached before/away from its actual ordinal gap");
        CHECK(mid_ranges>0,"small-ring fixture produced no retained post-gap row");
        CHECK(s4.exact_units+s4.eligible_ring_drops==s4.eligible_observations,"small-ring eligible conservation failed");
        CHECK(s4.log_rows+s4.dropped_ring_full==s4.video_observations+s4.ring_gap_rows,"sidecar row/range conservation failed");
        fs_close(r);
    }

    // F6: close after start without stop must stop first (ASan/TSan builds prove no use-after-free)
    done = 0;
    frameserver *k = NULL; fs_config c3 = cfg; c3.decision_log = NULL;
    CHECK(fs_open(&k, &c3) == 0, "open (close-without-stop)");
    CHECK(fs_start(k) == 0, "start (close-without-stop)");
    while (!done) usleep(10000);
    fs_close(k);

    // Failed start: replay open happens in cc_start.  It must roll the worker back without
    // presenting on_end for a session that never successfully started.
    done=0; fs_config badcfg=cfg; badcfg.capture.replay_path="/definitely/not/a/capture.tpc"; badcfg.decision_log=NULL;
    frameserver *badf=NULL; CHECK(fs_open(&badf,&badcfg)==0,"open (failed-start fixture)");
    if(badf){ CHECK(fs_start(badf)!=0,"missing replay unexpectedly started"); CHECK(!done,"on_end fired after failed start"); fs_close(badf); }

    // Early fs_open cleanup reaches fs_close before publisher/log/capture exist; initialized
    // synchronization objects make that path defined under ASan/TSan.
    fs_config badlog=cfg; badlog.decision_log="/definitely/not/a/dir/log.csv"; frameserver *badl=NULL;
    CHECK(fs_open(&badl,&badlog)!=0,"invalid log path unexpectedly opened");

    // Two control callers stopping a live paced session must synchronize on the completed join.
    done=0; fs_config concfg=cfg; concfg.decision_log=NULL; concfg.capture.replay_pace_us=100000;
    frameserver *cf=NULL; CHECK(fs_open(&cf,&concfg)==0,"open (concurrent stop)");
    if(cf){
        CHECK(fs_start(cf)==0,"start (concurrent stop)"); usleep(10000);
        fs_stop_arg a={cf,-99},b={cf,-99}; pthread_t ta,tb;
        pthread_create(&ta,NULL,fs_stop_thread,&a); pthread_create(&tb,NULL,fs_stop_thread,&b);
        pthread_join(ta,NULL); pthread_join(tb,NULL);
        CHECK(a.rc==0&&b.rc==0,"concurrent stop results %d/%d",a.rc,b.rc); fs_close(cf);
    }

    // Hold the sole IOSurface so the second exact unit is rejected at the publisher edge; the
    // sidecar must name PublisherFull rather than an ambiguous None.
    done=0; atomic_store(&sink_hold,1); held_surface=NULL;
    char logp4[]="/tmp/fs_test_log4_XXXXXX"; fd=mkstemp(logp4); close(fd); unlink(logp4);
    fs_config pc=cfg; pc.decision_log=logp4; pc.surface_pool=1; frameserver *pf=NULL;
    CHECK(fs_open(&pf,&pc)==0,"open (publisher full)");
    if(pf){
        CHECK(fs_start(pf)==0,"start (publisher full)"); while(!done) usleep(10000); CHECK(fs_stop(pf)==0,"stop (publisher full)");
        fs_stats ps; fs_get_stats(pf,&ps); CHECK(ps.publisher_dropped>0,"publisher exhaustion not exercised");
        unsigned named=0; L=fopen(logp4,"r"); while(fgets(line,sizeof line,L)) if(strstr(line,",PublisherFull,")) named++; fclose(L);
        CHECK(named==ps.publisher_dropped,"PublisherFull rows %u != drops %llu",named,(unsigned long long)ps.publisher_dropped);
        if(held_surface){ IOSurfaceDecrementUseCount(held_surface); held_surface=NULL; }
        fs_close(pf);
    }
    atomic_store(&sink_hold,0); unlink(logp4);

    // Runtime log attachment: a recorder aligns the sidecar to ITS recording. Rows exist only
    // while attached, each file carries exactly one header, ordinals stay monotonic, the gap
    // between two attachments is genuinely unlogged, and every written row is counted.
    done=0; char la[]="/tmp/fs_test_logA_XXXXXX"; fd=mkstemp(la); close(fd); unlink(la); char lb[]="/tmp/fs_test_logB_XXXXXX"; fd=mkstemp(lb); close(fd); unlink(lb);   /* fs_log_start opens exclusively */
    CHECK(argc>=3,"runtime-log test needs the long plain fixture as argv[2]");
    fs_config rc=cfg; rc.decision_log=NULL; rc.capture.replay_path=argc>=3?argv[2]:argv[1]; rc.capture.replay_pace_us=30000; frameserver *rf=NULL;
    CHECK(fs_open(&rf,&rc)==0,"open (runtime log)");
    if(rf&&argc>=3){
        CHECK(fs_log_stop(rf)==-1,"stop with no log attached must fail");
        unsigned long long base=atomic_load(&frames_seen);
        CHECK(fs_start(rf)==0,"start (runtime log)"); CHECK(wait_frames(base,10),"frames before attach A");
        CHECK(fs_log_start(rf,la)==0,"attach A");
        CHECK(fs_log_start(rf,lb)==-1,"second attach while A is attached must fail");
        CHECK(wait_frames(base,30),"frames during A");
        CHECK(fs_log_stop(rf)==0,"detach A"); CHECK(wait_frames(base,45),"frames in the gap");
        CHECK(fs_log_start(rf,lb)==0,"attach B");
        while(!done) usleep(10000);
        CHECK(fs_stop(rf)==0,"stop (runtime log)");
        CHECK(fs_log_start(rf,la)==-1,"attach after stop must fail");
        fs_stats rs; fs_get_stats(rf,&rs);
        unsigned long long rowsA=0,rowsB=0,hdrA=0,hdrB=0,lastA=0,firstB=0,lastB=0; int monoA=1,monoB=1; unsigned long long prev; int first;
        L=fopen(la,"r"); prev=0; first=1; while(fgets(line,sizeof line,L)){ if(!strncmp(line,"ordinal,",8)){hdrA++;continue;} unsigned long long ord=strtoull(line,NULL,10); if(!first&&ord<=prev) monoA=0; prev=ord; first=0; rowsA++; lastA=ord; } fclose(L);
        L=fopen(lb,"r"); prev=0; first=1; while(fgets(line,sizeof line,L)){ if(!strncmp(line,"ordinal,",8)){hdrB++;continue;} unsigned long long ord=strtoull(line,NULL,10); if(first) firstB=ord; if(!first&&ord<=prev) monoB=0; prev=ord; first=0; rowsB++; lastB=ord; } fclose(L);
        CHECK(hdrA==1&&hdrB==1,"each runtime log carries exactly one header (%llu/%llu)",hdrA,hdrB);
        CHECK(rowsA>0&&rowsB>0,"both attachments logged rows (%llu/%llu)",rowsA,rowsB);
        CHECK(monoA&&monoB,"ordinals monotonic within each runtime log");
        CHECK(firstB>lastA+1,"the detached interval is unlogged (A ends %llu, B starts %llu)",lastA,firstB);
        CHECK(rowsA+rowsB==rs.log_rows,"runtime log rows on disk %llu != counted %llu",rowsA+rowsB,(unsigned long long)rs.log_rows);
        CHECK(rs.log_files==2,"log_files %llu != 2",(unsigned long long)rs.log_files);
        CHECK(rs.log_rows<rs.video_observations,"rows must cover only the attached windows (%llu of %llu observations)",(unsigned long long)rs.log_rows,(unsigned long long)rs.video_observations);
        CHECK(rs.log_write_errors==0&&rs.log_close_errors==0,"no log I/O errors expected (%llu/%llu)",(unsigned long long)rs.log_write_errors,(unsigned long long)rs.log_close_errors);
        CHECK(fs_log_start(rf,la)==-1,"attach onto an existing path must fail (never truncate a sidecar)");
        printf("  runtime log: A %llu rows (last ordinal %llu), gap, B %llu rows (%llu..%llu) of %llu observations\n",rowsA,lastA,rowsB,firstB,lastB,(unsigned long long)rs.video_observations);
        fs_close(rf);
    }
    unlink(la); unlink(lb);

    // Callback refusal and storage stall: fs_log_start/stop from the video worker return -1 without
    // deadlock; a row write that stalls (disk hang) stalls the worker and sheds video DOWNSTREAM —
    // PoolFull rows with exact conservation — never acquisition. Rows that failed are never counted.
    done=0; char lc[]="/tmp/fs_test_logC_XXXXXX"; fd=mkstemp(lc); close(fd); unlink(lc);
    fs_config sc=cfg; sc.decision_log=NULL; sc.capture.replay_path=argc>=3?argv[2]:argv[1]; sc.capture.replay_pace_us=8000; sc.pool_units=4; frameserver *sf=NULL;
    CHECK(fs_open(&sf,&sc)==0,"open (stall)");
    if(sf&&argc>=3){
        g_cb_target=sf; atomic_store(&cb_start_rc,99); atomic_store(&cb_stop_rc,99); atomic_store(&cb_try,1);
        unsigned long long sbase=atomic_load(&frames_seen);
        CHECK(fs_start(sf)==0,"start (stall)"); CHECK(wait_frames(sbase,5),"frames before the stall attach");
        CHECK(atomic_load(&cb_start_rc)==-1&&atomic_load(&cb_stop_rc)==-1,"log start/stop from the worker callback must be refused (%d/%d)",atomic_load(&cb_start_rc),atomic_load(&cb_stop_rc));
        atomic_store(&log_stalled,0); atomic_store(&log_stall_us,1500000);
        CHECK(fs_log_start(sf,lc)==0,"attach C");
        while(!done) usleep(10000);
        CHECK(fs_stop(sf)==0,"stop (stall)"); g_cb_target=NULL;
        CHECK(atomic_load(&log_stalled),"the stall hook did not fire");
        fs_stats ss; fs_get_stats(sf,&ss);
        /* Which bounded queue saturates first depends on the build's topology: the 4-slot pool
         * normally, the item ring under RING_ITEMS=2. Either way something is shed and accounted. */
        CHECK(ss.dropped_pool_full+ss.dropped_ring_full>0,"a stalled sidecar write must shed video downstream (pool or ring), got 0");
        CHECK(ss.published+ss.dropped_pool_full+ss.publisher_dropped==ss.exact_units,"conservation under stall: %llu+%llu+%llu != %llu",(unsigned long long)ss.published,(unsigned long long)ss.dropped_pool_full,(unsigned long long)ss.publisher_dropped,(unsigned long long)ss.exact_units);
        /* A long enough stall also fills the item ring; those observations are all PoolFull (the pool
         * filled first) and are accounted in the next row's preceding_ring_drops rather than as rows. */
        unsigned long long poolrows=0,rows=0,obsrows=0,ringdrops=0,firstord=0; int firstrow=1; L=fopen(lc,"r");
        while(fgets(line,sizeof line,L)){ if(!strncmp(line,"ordinal,",8)) continue; rows++; unsigned long long ord=strtoull(line,NULL,10); if(firstrow){firstord=ord;firstrow=0;}
            if(!strstr(line,",RingFullTail,")) obsrows++;   /* the synthetic tail-loss row is a range marker, not an observation */
            if(strstr(line,",PoolFull,")) poolrows++; char *last=strrchr(line,','); if(last) ringdrops+=strtoull(last+1,NULL,10); } fclose(L);
        CHECK(ringdrops==ss.ring_drops_logged,"preceding_ring_drops in the log %llu != ring drops logged %llu",ringdrops,(unsigned long long)ss.ring_drops_logged);
        /* Every observation from the first logged ordinal to the end of the session is either an
         * observation row or range-accounted by a later row's preceding_ring_drops (including the
         * RingFullTail marker): nothing shed during the stall vanishes from the sidecar. */
        CHECK(obsrows+ringdrops==ss.video_observations-firstord,"from ordinal %llu: %llu observation rows + %llu ring-accounted != %llu observations",firstord,obsrows,ringdrops,(unsigned long long)ss.video_observations-firstord);
        CHECK(poolrows<=ss.dropped_pool_full,"PoolFull rows %llu vs pool drops %llu",poolrows,(unsigned long long)ss.dropped_pool_full);
        CHECK(poolrows>0||ringdrops>0,"neither PoolFull rows nor ring-accounted drops appeared in the sidecar");
        CHECK(rows==ss.log_rows,"stall log rows %llu != counted %llu",rows,(unsigned long long)ss.log_rows);
        printf("  stall: %llu published, %llu PoolFull (%llu rows + %llu ring-accounted), %llu rows\n",(unsigned long long)ss.published,(unsigned long long)ss.dropped_pool_full,poolrows,ringdrops,rows);
        fs_close(sf);
    }
    unlink(lc);

    // Write-failure injection: after the first row the stream is redirected to /dev/full; every
    // later row fails, is counted in log_write_errors and NOT in log_rows, and fs_log_stop reports
    // the file as incomplete (-1) so a publisher cannot pass it off as complete.
    done=0; char ld[]="/tmp/fs_test_logD_XXXXXX"; fd=mkstemp(ld); close(fd); unlink(ld);
    fs_config bc=cfg; bc.decision_log=NULL; bc.capture.replay_path=argc>=3?argv[2]:argv[1]; bc.capture.replay_pace_us=8000; frameserver *bf=NULL;
    CHECK(fs_open(&bf,&bc)==0,"open (write failure)");
    if(bf&&argc>=3){
        unsigned long long bbase=atomic_load(&frames_seen);
        CHECK(fs_start(bf)==0,"start (write failure)"); CHECK(wait_frames(bbase,5),"frames before the failing attach");
        atomic_store(&log_break,1); CHECK(fs_log_start(bf,ld)==0,"attach D");
        CHECK(wait_frames(bbase,40),"frames while writes fail");
        CHECK(fs_log_stop(bf)==-1,"fs_log_stop must report a file with failed rows as incomplete");
        fs_stats mid; fs_get_stats(bf,&mid); CHECK(mid.log_last_file_errors>0,"last-file verdict must be nonzero for the broken file");
        /* a second, clean log in the same session, closed by fs_stop: its verdict must be 0 although the session total is not */
        char le[]="/tmp/fs_test_logE_XXXXXX"; fd=mkstemp(le); close(fd); unlink(le);
        CHECK(fs_log_start(bf,le)==0,"attach E (clean after broken)"); CHECK(wait_frames(bbase,60),"frames in the clean log");
        while(!done) usleep(10000); CHECK(fs_stop(bf)==0,"stop (write failure)");
        fs_stats bs; fs_get_stats(bf,&bs);
        CHECK(bs.log_write_errors>0,"injected write failures were not counted");
        CHECK(bs.log_last_file_errors==0,"the clean file closed by fs_stop must have a zero verdict (%llu) despite session errors %llu",(unsigned long long)bs.log_last_file_errors,(unsigned long long)bs.log_write_errors);
        CHECK(bs.log_rows>1,"the clean log wrote rows (%llu)",(unsigned long long)bs.log_rows);
        unlink(le);
        printf("  write failure: %llu rows, %llu write errors, last-file verdict %llu\n",(unsigned long long)bs.log_rows,(unsigned long long)bs.log_write_errors,(unsigned long long)bs.log_last_file_errors);
        fs_close(bf);
    }
    unlink(ld);
    if (fails) printf("FAILURES: %d\n", fails);
    else printf("frameserver tests: PASS (obs %llu, exact %llu, published %llu, short %llu, hole %llu, unframed %llu)\n",
           (unsigned long long)s.video_observations, (unsigned long long)s.exact_units, (unsigned long long)s.published,
           (unsigned long long)s.short_units, (unsigned long long)s.holes, (unsigned long long)s.unframed);
    return fails ? 1 : 0;
}
