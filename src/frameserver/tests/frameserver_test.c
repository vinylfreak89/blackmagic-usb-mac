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
#include <time.h>
#include "../../test_supervisor.h"
#include "../../test_liveness.h"
static int fails = 0;
extern void fs_test_reuse_worker_ids(frameserver *f);
static _Atomic int destroyed;
void fs_test_destroyed(void){ atomic_fetch_add(&destroyed,1); }
#define CHECK(c, ...) do { if (!(c)) { fails++; fprintf(stderr, "FAIL: " __VA_ARGS__); fprintf(stderr, "\n"); } } while (0)
static _Atomic int done; static _Atomic uint64_t frames_seen; static _Atomic int sink_hold;
/* These three log scenarios admit one observation at a time, with explicit
 * completed-row boundaries. No pool/ring size or replay speed defines a window.
 * The worker hook is AFTER process_item releases the log lock and pool slot. */
static test_liveness live=TEST_LIVENESS_INIT("FS_TEST_WAIT_S");
static int window_active, window_inflight, window_ended;
static uint64_t window_rows, window_limit;
static void window_begin(uint64_t limit){
    pthread_mutex_lock(&live.mutex);
    window_active=1; window_inflight=window_ended=0; window_rows=0; window_limit=limit;
    pthread_mutex_unlock(&live.mutex);
}
static void window_release(uint64_t limit,int active){
    pthread_mutex_lock(&live.mutex); window_limit=limit; window_active=active;
    test_live_note_locked(&live); pthread_mutex_unlock(&live.mutex);
}
void fs_test_before_video(frameserver *f){
    (void)f; double begun=test_now();
    pthread_mutex_lock(&live.mutex);
    while(window_active&&(window_inflight||window_rows>=window_limit)){
        char name[96]; snprintf(name,sizeof name,"log window producer release after %llu rows",(unsigned long long)window_rows);
        test_live_wait(&live,begun,name);
    }
    if(window_active) window_inflight=1;
    test_live_note_locked(&live);
    pthread_mutex_unlock(&live.mutex);
}
void fs_test_after_item(frameserver *f){
    (void)f;
    /* Test-only slow-progress control: no change to admission or row accounting. */
    const char *delay=getenv("FS_TEST_ITEM_DELAY_US");
    if(delay) usleep((useconds_t)strtoul(delay,NULL,10));
    pthread_mutex_lock(&live.mutex);
    if(window_active){ window_inflight=0; window_rows++; }
    test_live_note_locked(&live);
    pthread_mutex_unlock(&live.mutex);
}
static void window_wait(uint64_t rows,const char *name){
    double begun=test_now(); pthread_mutex_lock(&live.mutex);
    while(window_rows<rows){
        if(window_ended){ fprintf(stderr,"FAIL: %s: session ended before required rows\n",name); _exit(2); }
        test_live_wait(&live,begun,name);
    }
    pthread_mutex_unlock(&live.mutex);
}
enum { DROP_POOL=1, DROP_RING=2, DROP_AUDIO=4, RING_DRAINED=8 };
static int drops_seen, producer_finished, ring_wait_requested;
static int video_hold_mask, audio_hold_mask;
static _Atomic int log_hold_mask;
static IOSurfaceRef held_surface;
static _Atomic int hook_arm, hook_empty, hook_release;
/* Every wait here has a stall deadline: FS_TEST_WAIT_S seconds without progress, default 60. On expiry the test fails loudly,
 * names the wait and exits at once (exit 2). A silent timeout would turn a hang into a false pass, and
 * carrying on would likely hang again in fs_stop. */
static void reset_drops(void){
    pthread_mutex_lock(&live.mutex); drops_seen=0; producer_finished=0; ring_wait_requested=0; pthread_mutex_unlock(&live.mutex);
}
static void note_drop(int kind){
    pthread_mutex_lock(&live.mutex); drops_seen|=kind; test_live_note_locked(&live); pthread_mutex_unlock(&live.mutex);
}
void fs_test_pool_drop(void){ note_drop(DROP_POOL); }
void fs_test_audio_drop(void){ note_drop(DROP_AUDIO); }
static void hold_until_drop(int mask, const char *site){
    if(!mask) return;
    double begun=test_now();
    pthread_mutex_lock(&live.mutex);
    while(!(drops_seen&mask)){
        if(producer_finished){
            fprintf(stderr,"FAIL: %s: producer ended before required drop (mask %d)\n",site,mask);
            _exit(2);
        }
        test_live_wait(&live,begun,site);
    }
    pthread_mutex_unlock(&live.mutex);
}
void fs_test_ring_drop(void){
    /* In the dedicated ring test, guarantee a retained post-gap row: let the
     * worker drain after the first loss before the producer resumes. */
    pthread_mutex_lock(&live.mutex);
    int wait=video_hold_mask==DROP_RING && !ring_wait_requested;
    if(wait) ring_wait_requested=1;
    pthread_mutex_unlock(&live.mutex);
    note_drop(DROP_RING);
    if(wait) hold_until_drop(RING_DRAINED,"post-ring-loss drain");
}
static void wait_for_end(const char *what){
    char name[128]; snprintf(name,sizeof name,"waiting for on_end (%s)",what);
    double begun=test_now(); pthread_mutex_lock(&live.mutex);
    while(!done) test_live_wait(&live,begun,name);
    pthread_mutex_unlock(&live.mutex);
}
void fs_test_after_empty_snapshot(frameserver *f){
    pthread_mutex_lock(&live.mutex);
    if(ring_wait_requested && !(drops_seen&RING_DRAINED)){ drops_seen|=RING_DRAINED; test_live_note_locked(&live); }
    (void)f; if(atomic_load(&hook_arm) && !atomic_exchange(&hook_empty,1)){
        double begun=test_now();
        while(!atomic_load(&hook_release))
            test_live_wait(&live,begun,"fs_test_after_empty_snapshot: fs_test_before_producer_done never released the worker");
    }
    pthread_mutex_unlock(&live.mutex);
}
void fs_test_before_producer_done(frameserver *f){ (void)f; pthread_mutex_lock(&live.mutex);
    if(atomic_load(&hook_arm)) atomic_store(&hook_release,1);
    producer_finished=1; test_live_note_locked(&live); pthread_mutex_unlock(&live.mutex); }
static _Atomic int log_stalled;   // storage-stall injection: first row after arming holds the row lock until a drop
static _Atomic int log_break;   // write-failure injection: swap the stream's fd for a pipe with no reader (EPIPE on every write; SIGPIPE ignored), unbuffered so each row fprintf fails
void fs_test_after_log_row(frameserver *f, FILE *log){ (void)f; int mask=atomic_exchange(&log_hold_mask,0); if(mask){ atomic_store(&log_stalled,1); hold_until_drop(mask,"sidecar hold"); }
    if(atomic_exchange(&log_break,0)){ int p[2]; if(pipe(p)!=0) abort(); close(p[0]); fflush(log); if(dup2(p[1],fileno(log))<0) abort(); close(p[1]); setvbuf(log,NULL,_IONBF,0); } }
static frameserver *g_cb_target; static _Atomic int cb_try, cb_start_rc, cb_stop_rc;   // callback-refusal probe
static _Atomic int cb_life_rc, audio_life_try, audio_life_rc, end_life_try, end_life_rc;
static const char *callback_log;
static _Atomic int end_calls;
static void on_end(void *c, enum cc_end r){ (void)c; (void)r;
    if(atomic_exchange(&end_life_try,0)){ end_life_rc=fs_stop(g_cb_target); fs_close(g_cb_target); }
    atomic_fetch_add(&end_calls, 1); done = 1;
    pthread_mutex_lock(&live.mutex); window_ended=1; test_live_note_locked(&live); pthread_mutex_unlock(&live.mutex); }
static _Atomic uint64_t audio_frames_seen; static _Atomic int audio_flagged_blocks; static _Atomic uint64_t audio_last_pts; static _Atomic int audio_pts_nonmonotonic;
static _Atomic int audio_after_end; static _Atomic int ordinal_break;
static uint64_t audio_next_ordinal; static int audio_have_next;
#define CORR_MAX 64
static uint64_t corr_ctr[CORR_MAX], corr_pts[CORR_MAX]; static _Atomic int corr_n;   // first block after resync c: its pts is the audio-clock time of unit c
static void audio_sink(void *c, const ap_block *b){ (void)c; atomic_fetch_add(&audio_frames_seen, b->n_frames);
    test_live_note(&live);
    if(atomic_exchange(&audio_life_try,0)){ audio_life_rc=fs_stop(g_cb_target); fs_close(g_cb_target); }
    if (done) atomic_store(&audio_after_end, 1);
    if (audio_have_next && !(b->flags & (AP_FLAG_DISCONTINUITY_BEFORE|AP_FLAG_DROPPED_BEFORE)) && b->sample_ordinal != audio_next_ordinal) atomic_store(&ordinal_break, 1);
    audio_next_ordinal = b->sample_ordinal + b->n_frames; audio_have_next = 1;
    if (!(b->flags & AP_FLAG_UNANCHORED) && b->last_resync_counter_ext && atomic_load(&corr_n) < CORR_MAX){ int n = atomic_load(&corr_n); corr_ctr[n] = b->last_resync_counter_ext; corr_pts[n] = b->pts_num; atomic_store(&corr_n, n + 1); }
    hold_until_drop(audio_hold_mask,"audio queue hold");
    if (b->flags & AP_FLAG_DISCONTINUITY_BEFORE) atomic_fetch_add(&audio_flagged_blocks, 1);
    if (!(b->flags & (AP_FLAG_UNANCHORED|AP_FLAG_DISCONTINUITY_BEFORE)) && b->pts_num < atomic_load(&audio_last_pts)) atomic_store(&audio_pts_nonmonotonic, 1);
    if (!(b->flags & AP_FLAG_UNANCHORED)) atomic_store(&audio_last_pts, b->pts_num); }
static uint64_t vf_ctr[CORR_MAX], vf_apts[CORR_MAX]; static _Atomic int vf_n; static _Atomic int video_after_end;
static void sink(void *c, const fp_frame *fr){ (void)c; if (fr->surface) atomic_fetch_add(&frames_seen, 1);
    if (atomic_exchange(&cb_try,0) && g_cb_target){
        cb_life_rc=fs_stop(g_cb_target); fs_close(g_cb_target);
        atomic_store(&cb_start_rc, fs_log_start(g_cb_target,callback_log)); atomic_store(&cb_stop_rc, fs_log_stop(g_cb_target)); }
    if (done) atomic_store(&video_after_end, 1);
    if (fr->audio_pts_known && atomic_load(&vf_n) < CORR_MAX){ int n = atomic_load(&vf_n); vf_ctr[n] = fr->counter_ext; vf_apts[n] = fr->audio_pts_num; atomic_store(&vf_n, n + 1); }
    if(atomic_load(&sink_hold)&&!held_surface){ IOSurfaceIncrementUseCount(fr->surface); held_surface=fr->surface; }
    hold_until_drop(video_hold_mask,"video slot hold"); }
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
    test_supervise(argv, "FS_TEST_TOTAL_S", "frameserver_test");
    if (argc == 3 && !strcmp(argv[1], "--deadline-probe")) {
        if (!strcmp(argv[2], "total")) { alarm(0); for (;;) pause(); }
        setenv("FS_TEST_WAIT_S", "0", 1);
        if (!strcmp(argv[2], "hook")) { hook_arm=1; fs_test_after_empty_snapshot(NULL); }
        else wait_for_end("forced wait probe");
        return 99;
    }
    if (argc < 2){ fprintf(stderr, "usage: %s <fixture.tpc>\n", argv[0]); return 9; }
    signal(SIGPIPE, SIG_IGN);   /* the write-failure injection writes to a reader-less pipe */
    int ring_may_drop = getenv("FS_TEST_EXPECT_RING_DROPS") != NULL;
    char logp[] = "/tmp/fs_test_log_XXXXXX"; int fd = mkstemp(logp); close(fd); unlink(logp);
    char cbpath[]="/tmp/fs_test_callback_XXXXXX"; fd=mkstemp(cbpath); close(fd); unlink(cbpath); callback_log=cbpath;
    fs_config cfg = {0}; cfg.capture.replay_path = argv[1]; cfg.decision_log = logp; cfg.on_end = on_end;
    cfg.sink.on_frame = sink; cfg.pool_units = 4; cfg.surface_pool = 3; cfg.audio_sink.on_block = audio_sink;
    frameserver *f = NULL;
    CHECK(fs_open(&f, &cfg) == 0, "open");
    atomic_store(&hook_arm,!ring_may_drop); atomic_store(&hook_empty,0); atomic_store(&hook_release,0);
    CHECK(fs_start(f) == 0, "start");
    wait_for_end("main fixture run");
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
    reset_drops(); audio_hold_mask=DROP_AUDIO;
    fs_config c5 = cfg; c5.decision_log = NULL; c5.audio_queue_blocks = 1;
    frameserver *q = NULL;
    CHECK(fs_open(&q, &c5) == 0, "open (slow audio sink)");
    CHECK(fs_start(q) == 0, "start (slow audio sink)");
    wait_for_end("slow audio sink run");
    CHECK(fs_stop(q) == 0, "stop (slow audio sink)");
    audio_hold_mask=0;
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
    FILE *L = fopen(logp, "r"); char line[16384]; unsigned rows = 0; int hdr_ok = 0, row_shape_ok = 1; unsigned header_fields = 0;
    while (fgets(line, sizeof line, L)){
        if (rows == 0){ hdr_ok = strstr(line, "frame_d1,frame_d2,f1_first,f2_first") != NULL && strstr(line, "vote_confident,vote_anchor,vote_engine_anchor") != NULL && strstr(line, "rigid_dx_f1,rigid_dy_f1") != NULL; header_fields=csv_fields(line); }
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
    reset_drops(); video_hold_mask=ring_may_drop?DROP_POOL|DROP_RING:DROP_POOL;
    frameserver *g = NULL;
    CHECK(fs_open(&g, &c2) == 0, "open (pool=1)");
    CHECK(fs_start(g) == 0, "start (pool=1)");
    wait_for_end("one-slot pool run");
    CHECK(fs_stop(g) == 0, "stop (pool=1)");
    CHECK(fs_stop(g) == 0, "second stop is an idempotent no-op");
    video_hold_mask=0;
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
        reset_drops(); video_hold_mask=DROP_RING;
        frameserver *r = NULL;
        CHECK(fs_open(&r, &c4) == 0, "open (small ring)");
        CHECK(fs_start(r) == 0, "start (small ring)");
        wait_for_end("small-ring run");
        CHECK(fs_stop(r) == 0, "stop (small ring)");
        video_hold_mask=0;
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
    /* Exercise the shared log guard independently of lifecycle rejection:
     * logging is allowed on this OPEN session despite deliberately aliased IDs. */
    fs_test_reuse_worker_ids(k);
    CHECK(fs_log_start(k,cbpath)==0,"external log start with aliased worker IDs");
    CHECK(fs_log_stop(k)==0,"external log stop with aliased worker IDs");
    unlink(cbpath);
    // No attached log and a fresh path: callback-start refusal cannot pass merely
    // because a file already exists or a log is already attached. Stop refusal is
    // separately checked with an attached log in the sidecar-stall session below.
    g_cb_target=k; atomic_store(&cb_start_rc,99); atomic_store(&cb_try,1);
    cb_life_rc=audio_life_rc=end_life_rc=99; audio_life_try=end_life_try=1;
    CHECK(fs_start(k) == 0, "start (close-without-stop)");
    wait_for_end("close-without-stop run");
    CHECK(atomic_load(&cb_start_rc)==-1,"log start from callback with no attached log must be refused");
    CHECK(cb_life_rc==-1 && audio_life_rc==-1 && end_life_rc==-1,
          "video/audio/end callbacks must refuse stop (%d/%d/%d)",(int)cb_life_rc,(int)audio_life_rc,(int)end_life_rc);
    fs_close(k);
    g_cb_target=NULL;

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
        CHECK(a.rc==0&&b.rc==0,"concurrent stop results %d/%d",a.rc,b.rc);
        fs_test_reuse_worker_ids(cf);
        CHECK(fs_stop(cf)==0,"external stop with reused worker IDs must succeed");
        int before=destroyed; fs_close(cf);
        CHECK(destroyed==before+1,"external close with reused worker IDs must destroy session");
    }

    // Hold the sole IOSurface so the second exact unit is rejected at the publisher edge; the
    // sidecar must name PublisherFull rather than an ambiguous None.
    done=0; atomic_store(&sink_hold,1); held_surface=NULL;
    char logp4[]="/tmp/fs_test_log4_XXXXXX"; fd=mkstemp(logp4); close(fd); unlink(logp4);
    fs_config pc=cfg; pc.decision_log=logp4; pc.surface_pool=1; frameserver *pf=NULL;
    CHECK(fs_open(&pf,&pc)==0,"open (publisher full)");
    if(pf){
        CHECK(fs_start(pf)==0,"start (publisher full)"); wait_for_end("publisher-full run"); CHECK(fs_stop(pf)==0,"stop (publisher full)");
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
    fs_config rc=cfg; rc.decision_log=NULL; rc.capture.replay_path=argc>=3?argv[2]:argv[1]; rc.capture.replay_pace_us=0; frameserver *rf=NULL;
    CHECK(fs_open(&rf,&rc)==0,"open (runtime log)");
    if(rf&&argc>=3){
        CHECK(fs_log_stop(rf)==-1,"stop with no log attached must fail");
        window_begin(10);
        CHECK(fs_start(rf)==0,"start (runtime log)"); window_wait(10,"rows before attach A");
        CHECK(fs_log_start(rf,la)==0,"attach A");
        CHECK(fs_log_start(rf,lb)==-1,"second attach while A is attached must fail");
        window_release(30,1); window_wait(30,"rows during A");
        CHECK(fs_log_stop(rf)==0,"detach A"); window_release(45,1); window_wait(45,"rows in the gap");
        CHECK(fs_log_start(rf,lb)==0,"attach B");
        window_release(0,0); /* Final boundary: B logs all remaining observations, including drops. */
        wait_for_end("runtime-log run");
        CHECK(fs_stop(rf)==0,"stop (runtime log)");
        window_release(0,0);
        CHECK(fs_log_start(rf,la)==-1,"attach after stop must fail");
        fs_stats rs; fs_get_stats(rf,&rs);
        unsigned long long rowsA=0,rowsB=0,obsB=0,gapsB=0,hdrA=0,hdrB=0,lastA=0,firstB=0,lastB=0; int monoA=1,monoB=1; unsigned long long prev; int first;
        L=fopen(la,"r"); prev=0; first=1; while(fgets(line,sizeof line,L)){ if(!strncmp(line,"ordinal,",8)){hdrA++;continue;} unsigned long long ord=strtoull(line,NULL,10); if(!first&&ord<=prev) monoA=0; prev=ord; first=0; rowsA++; lastA=ord; } fclose(L);
        L=fopen(lb,"r"); prev=0; first=1; while(fgets(line,sizeof line,L)){ if(!strncmp(line,"ordinal,",8)){hdrB++;continue;} unsigned long long ord=strtoull(line,NULL,10); if(first) firstB=ord; if(!first&&ord<=prev) monoB=0; prev=ord; first=0; rowsB++; lastB=ord;
            if(!strstr(line,",RingFullTail,")) obsB++;
            char *last=strrchr(line,','); if(last) gapsB+=strtoull(last+1,NULL,10);
        } fclose(L);
        CHECK(hdrA==1&&hdrB==1,"each runtime log carries exactly one header (%llu/%llu)",hdrA,hdrB);
        CHECK(rowsA>0&&rowsB>0,"both attachments logged rows (%llu/%llu)",rowsA,rowsB);
        /* Normal ring holds the entire remaining fixture, including PoolFull
         * rows. The deliberate two-slot ring instead records loss ranges. */
        CHECK(rowsA==20&&obsB+gapsB==75,"event-defined A/B observations changed (%llu/%llu+%llu)",rowsA,obsB,gapsB);
        if(!ring_may_drop) CHECK(rowsB==75,"B must contain exactly 75 rows (%llu)",rowsB);
        CHECK(gapsB==rs.dropped_ring_full,"B loss ranges %llu != ring drops %llu",gapsB,(unsigned long long)rs.dropped_ring_full);
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
    // Account from session start, including ring losses before the stall is armed.
    fs_config sc=cfg; sc.decision_log=lc; sc.capture.replay_path=argc>=3?argv[2]:argv[1]; sc.capture.replay_pace_us=0; sc.pool_units=4; frameserver *sf=NULL;
    CHECK(fs_open(&sf,&sc)==0,"open (stall)");
    if(sf&&argc>=3){
        g_cb_target=sf; atomic_store(&cb_start_rc,99); atomic_store(&cb_stop_rc,99); atomic_store(&cb_try,1);
        window_begin(5);
        CHECK(fs_start(sf)==0,"start (stall)"); window_wait(5,"rows before arming the sidecar stall");
        CHECK(atomic_load(&cb_start_rc)==-1&&atomic_load(&cb_stop_rc)==-1,"log start/stop from the worker callback must be refused (%d/%d)",atomic_load(&cb_start_rc),atomic_load(&cb_stop_rc));
        reset_drops(); atomic_store(&log_stalled,0); atomic_store(&log_hold_mask,DROP_POOL|DROP_RING);
        window_release(0,0); /* Deliberately free-running: this scenario requires pressure. */
        wait_for_end("log-stall run");
        CHECK(fs_stop(sf)==0,"stop (stall)"); g_cb_target=NULL;
        CHECK(atomic_load(&log_stalled),"the stall hook did not fire");
        fs_stats ss; fs_get_stats(sf,&ss);
        /* Which bounded queue saturates first depends on the build's topology: the 4-slot pool
         * normally, the item ring under RING_ITEMS=2. Either way something is shed and accounted. */
        CHECK(ss.dropped_pool_full+ss.dropped_ring_full>0,"a stalled sidecar write must shed video downstream (pool or ring), got 0");
        CHECK(ss.published+ss.dropped_pool_full+ss.publisher_dropped==ss.exact_units,"conservation under stall: %llu+%llu+%llu != %llu",(unsigned long long)ss.published,(unsigned long long)ss.dropped_pool_full,(unsigned long long)ss.publisher_dropped,(unsigned long long)ss.exact_units);
        /* Any item-ring losses are accounted in the next row's preceding_ring_drops
         * rather than as individual rows. The hold requires a drop, not a duration. */
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
    fs_config bc=cfg; bc.decision_log=NULL; bc.capture.replay_path=argc>=3?argv[2]:argv[1]; bc.capture.replay_pace_us=0; frameserver *bf=NULL;
    CHECK(fs_open(&bf,&bc)==0,"open (write failure)");
    if(bf&&argc>=3){
        window_begin(5);
        CHECK(fs_start(bf)==0,"start (write failure)"); window_wait(5,"rows before the failing attach");
        atomic_store(&log_break,1); CHECK(fs_log_start(bf,ld)==0,"attach D");
        window_release(40,1); window_wait(40,"rows while writes fail");
        CHECK(fs_log_stop(bf)==-1,"fs_log_stop must report a file with failed rows as incomplete");
        fs_stats mid; fs_get_stats(bf,&mid); CHECK(mid.log_last_file_errors>0,"last-file verdict must be nonzero for the broken file");
        /* a second, clean log in the same session, closed by fs_stop: its verdict must be 0 although the session total is not */
        char le[]="/tmp/fs_test_logE_XXXXXX"; fd=mkstemp(le); close(fd); unlink(le);
        CHECK(fs_log_start(bf,le)==0,"attach E (clean after broken)");
        const char *fault=getenv("FS_TEST_CLEAN_WINDOW");
        window_release(fault&&!strcmp(fault,"paused")?40:60,1);
        if(fault&&!strcmp(fault,"ended")) window_release(0,0);
        window_wait(fault&&!strcmp(fault,"ended")?UINT64_MAX:60,"rows in the clean log");
        window_release(0,0); /* No further attach/detach boundary. */
        wait_for_end("write-failure run"); CHECK(fs_stop(bf)==0,"stop (write failure)");
        window_release(0,0);
        fs_stats bs; fs_get_stats(bf,&bs);
        CHECK(bs.log_write_errors>0,"injected write failures were not counted");
        CHECK(bs.log_last_file_errors==0,"the clean file closed by fs_stop must have a zero verdict (%llu) despite session errors %llu",(unsigned long long)bs.log_last_file_errors,(unsigned long long)bs.log_write_errors);
        CHECK(bs.log_rows>1,"the clean log wrote rows (%llu)",(unsigned long long)bs.log_rows);
        unlink(le);
        printf("  write failure: %llu rows, %llu write errors, last-file verdict %llu\n",(unsigned long long)bs.log_rows,(unsigned long long)bs.log_write_errors,(unsigned long long)bs.log_last_file_errors);
        fs_close(bf);
    }
    unlink(ld);
    unlink(cbpath);
    if (fails) printf("FAILURES: %d\n", fails);
    else printf("frameserver tests: PASS (obs %llu, exact %llu, published %llu, short %llu, hole %llu, unframed %llu)\n",
           (unsigned long long)s.video_observations, (unsigned long long)s.exact_units, (unsigned long long)s.published,
           (unsigned long long)s.short_units, (unsigned long long)s.holes, (unsigned long long)s.unframed);
    return fails ? 1 : 0;
}
