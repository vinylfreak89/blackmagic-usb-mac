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
    if (done) atomic_store(&video_after_end, 1);
    if (fr->audio_pts_known && atomic_load(&vf_n) < CORR_MAX){ int n = atomic_load(&vf_n); vf_ctr[n] = fr->counter_ext; vf_apts[n] = fr->audio_pts_num; atomic_store(&vf_n, n + 1); }
    if(atomic_load(&sink_hold)&&!held_surface){ IOSurfaceIncrementUseCount(fr->surface); held_surface=fr->surface; }
    int st = atomic_load(&sink_stall_us); if (st) usleep(st); }   // a slow consumer holds the slot
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
int main(int argc, char **argv){
    if (argc < 2){ fprintf(stderr, "usage: %s <fixture.tpc>\n", argv[0]); return 9; }
    int ring_may_drop = getenv("FS_TEST_EXPECT_RING_DROPS") != NULL;
    char logp[] = "/tmp/fs_test_log_XXXXXX"; int fd = mkstemp(logp); close(fd);
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
        char logp3[] = "/tmp/fs_test_log3_XXXXXX"; fd = mkstemp(logp3); close(fd);
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
    char logp4[]="/tmp/fs_test_log4_XXXXXX"; fd=mkstemp(logp4); close(fd);
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
    if (fails) printf("FAILURES: %d\n", fails);
    else printf("frameserver tests: PASS (obs %llu, exact %llu, published %llu, short %llu, hole %llu, unframed %llu)\n",
           (unsigned long long)s.video_observations, (unsigned long long)s.exact_units, (unsigned long long)s.published,
           (unsigned long long)s.short_units, (unsigned long long)s.holes, (unsigned long long)s.unframed);
    return fails ? 1 : 0;
}
