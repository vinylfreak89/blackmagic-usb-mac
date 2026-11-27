// replay_probe and replay start offset on the plain synthetic fixture (120 exact units, counters
// 0..119, all video records first, then audio). The last unit has no following marker, so the
// last COMPLETE unit is 118. A replay started mid-file publishes its first frame from the first
// unit whose marker follows the offset.
#include "../frameserver.h"
#include "../replay_probe.h"
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <pthread.h>
#include <unistd.h>
#include <stdlib.h>

static int fails;
#ifdef CAPTURE_CORE_TEST_HOOKS
/* capture_core test hooks: every read passes through, except that a read reaching past fail_near_end
 * (a file offset, 0 = off) fails with EIO, as a network volume can. */
#include <errno.h>
static _Atomic uint64_t fail_near_end;
ssize_t cc_test_replay_read(int fd, void *buf, size_t n){
    uint64_t at = atomic_load(&fail_near_end);
    off_t pos = lseek(fd, 0, SEEK_CUR);
    if (at && pos >= 0 && (uint64_t)pos + n > at){ errno = EIO; return -1; }
    return read(fd, buf, n);
}
void cc_test_destroyed(void){} void cc_test_data_resumed(void){} void cc_test_after_empty_snapshot(cc_session *s){ (void)s; }
void cc_test_before_backend_done(cc_session *s){ (void)s; } int cc_test_fail_delivery_allocation(size_t b){ (void)b; return 0; }
void cc_test_ring_loss(void){} void cc_test_recorded_error(void){} void cc_test_meta_exhausted(void){} void cc_test_input_done(void){}
void cc_test_packet_progress(void){} void cc_test_replay_prefill_wait(void){} void cc_test_replay_paused(uint64_t b){ (void)b; }
#endif
#define CHECK(c, ...) do{ if(!(c)){ fails++; fprintf(stderr,"FAIL: "); fprintf(stderr,__VA_ARGS__); fprintf(stderr,"\n"); } }while(0)
static _Atomic int ended; static uint64_t first_counter = UINT64_MAX, frames;
static pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER; static pthread_cond_t c = PTHREAD_COND_INITIALIZER;
static void on_frame(void *ctx, const fp_frame *f){ (void)ctx; if (first_counter == UINT64_MAX) first_counter = f->counter_ext; frames++; }
static void on_end(void *ctx, enum cc_end r){ (void)ctx; (void)r; pthread_mutex_lock(&m); atomic_store(&ended, 1); pthread_cond_broadcast(&c); pthread_mutex_unlock(&m); }

int main(int argc, char **argv){
    if (argc < 2){ fprintf(stderr, "usage: %s fixture_plain.tpc\n", argv[0]); return 9; }
    const char *p = argv[1]; struct stat st; stat(p, &st);
    fs_replay_span sp;
    CHECK(fs_replay_probe(p, 0, NULL, &sp) == 0, "probe failed");
    CHECK(sp.file_bytes == (uint64_t)st.st_size, "file bytes %llu", (unsigned long long)sp.file_bytes);
    CHECK(sp.have_first && sp.first_counter == 0, "first counter %u", sp.first_counter);
    CHECK(sp.have_last && sp.last_counter == 118, "last counter %u (the last complete unit is 118)", sp.last_counter);
    /* a tail window smaller than the file still finds the end: the fixture ends with its whole audio stream
     * (120 units x ~1601.6 records x 24 B, about 4.6 MB), so 16 MiB reaches about 15 units of video */
    CHECK(fs_replay_probe(p, 16u << 20, NULL, &sp) == 0 && sp.last_counter == 118 && sp.first_counter == 0, "small-window probe: first %u last %u", sp.first_counter, sp.last_counter);
    /* a head window too small to hold a unit finds no first counter */
    CHECK(fs_replay_probe(p, 1u << 16, NULL, &sp) != 0 && !sp.have_first, "a 64 KiB head window cannot hold a 756,048-byte unit, yet found counter %u", sp.first_counter);
    /* Ends without picture units near them (a capture that starts or ends with the deck off or stopped): ~42 MB of
     * stream with no picture unit after the fixture, then before it. Like a real no-input stretch it carries both
     * endpoints, in whole transfers (8 packets of 2 KiB of video with no marker, then 8 of 8 audio records), so a
     * replay started inside it lands on a video transfer at once; the numbering runs on across the join (after the
     * fixture: on from far past its last transfer; before it: the fixture's own transfers renumbered past the
     * padding's). The last (first) 32 MiB hold no unit; the probe samples further in and finds unit 118 (0), placed
     * within a few units of where it is. A search bound short of the picture is a clean absence (not incomplete),
     * so the plugin does not retry it. */
    {
        uint64_t per_unit_f = 756048 + 24ull * 756048 / 15360;     /* file bytes per unit in the fixture's video run */
        enum { PAIRS = 2400, VPK = 8, VLEN = 2048, APK = 8, ALEN = 192 };
        static uint8_t buf[1 << 16];
        uint64_t pad = (uint64_t)PAIRS * (VPK * (24 + VLEN) + APK * (24 + ALEN));   /* 42.6 MB */
        for (int head = 0; head < 2; head++){
            char tpath[] = "/tmp/replay_probe_end_XXXXXX"; int fd = mkstemp(tpath); int ok = fd >= 0;
            FILE *in = fopen(p, "rb");
            for (int part = 0; part < 2 && ok; part++){
                if ((part == 0) == (head == 1)){
                    uint32_t base = head ? 0 : 1000000;
                    for (uint32_t t = 0; t < PAIRS && ok; t++)
                        for (int ep = 0; ep < 2 && ok; ep++)
                            for (uint32_t k = 0; k < (ep ? APK : VPK) && ok; k++){
                                uint8_t h[24] = {0}; uint32_t magic = 0x31504143u, len = ep ? ALEN : VLEN, sq = base + t; uint16_t pi = (uint16_t)k;
                                memcpy(h, &magic, 4); h[4] = 0; h[5] = ep ? 0x84 : 0x83; memcpy(h + 6, &pi, 2); memcpy(h + 8, &sq, 4);
                                memcpy(h + 16, &len, 4); memcpy(h + 20, &len, 4);
                                memset(buf, 0, len);
                                ok = write(fd, h, 24) == 24 && write(fd, buf, len) == (ssize_t)len;
                            }
                } else {
                    uint8_t h[24];
                    while (ok && in && fread(h, 1, 24, in) == 24){
                        uint32_t al, sq; memcpy(&al, h + 20, 4); memcpy(&sq, h + 8, 4);
                        size_t n = (h[4] == 0 || h[4] == 3) ? al : 0;
                        if (n > sizeof buf || (n && fread(buf, 1, n, in) != n)){ ok = 0; break; }
                        if (head && (h[4] == 0 || h[4] == 2)){ sq += PAIRS; memcpy(h + 8, &sq, 4); }
                        ok = write(fd, h, 24) == 24 && (!n || write(fd, buf, n) == (ssize_t)n);
                    }
                }
            }
            if (in) fclose(in);
            if (fd >= 0) close(fd);
            CHECK(ok, "could not write the %s test file", head ? "head" : "tail");
            uint64_t base = head ? pad : 0;
            int rc = fs_replay_probe(tpath, 0, NULL, &sp);
            CHECK(rc == 0 && sp.have_first && sp.first_counter == 0 && sp.have_last && sp.last_counter == 118 && !sp.incomplete,
                  "a unit-less 42 MB %s: rc %d first %d/%u last %d/%u incomplete %d", head ? "head" : "tail", rc, sp.have_first, sp.first_counter, sp.have_last, sp.last_counter, sp.incomplete);
            int64_t e0 = (int64_t)sp.first_offset - (int64_t)base, e1 = (int64_t)sp.last_offset - (int64_t)(base + 118 * per_unit_f);
            CHECK(e0 > -3 * (int64_t)per_unit_f && e0 < 3 * (int64_t)per_unit_f && e1 > -3 * (int64_t)per_unit_f && e1 < 3 * (int64_t)per_unit_f,
                  "%s case: first unit placed %+lld bytes, last %+lld bytes from where they are (a few units allowed)", head ? "head" : "tail", (long long)e0, (long long)e1);
            CHECK(fs_replay_probe_ex(tpath, 0, 32u << 20, NULL, &sp) != 0 && (head ? !sp.have_first : !sp.have_last) && !sp.incomplete,
                  "a search bound short of the picture (%s): first %d last %d incomplete %d", head ? "head" : "tail", sp.have_first, sp.have_last, sp.incomplete);
            unlink(tpath);
        }
    }
    CHECK(fs_replay_probe("/nonexistent/volume/capture.tpc", 0, NULL, &sp) != 0 && sp.incomplete, "an unreadable path must be unknown (incomplete), not a clean absence: incomplete %d", sp.incomplete);
    _Atomic int abort_now = 1;
    CHECK(fs_replay_probe(p, 0, &abort_now, &sp) != 0 && sp.incomplete, "an aborted probe reported success or a known absence");
#ifdef CAPTURE_CORE_TEST_HOOKS
    /* A read error 4 MiB before the end: the tail run has seen units, but not the last one. That is
     * "incomplete", never a span ending at an earlier counter. */
    atomic_store(&fail_near_end, (uint64_t)st.st_size - (4u << 20));
    CHECK(fs_replay_probe(p, 0, NULL, &sp) != 0 && !sp.have_last && sp.incomplete, "a read error before the end: have_last %d (last %u) incomplete %d", sp.have_last, sp.last_counter, sp.incomplete);
    atomic_store(&fail_near_end, 0);
#endif

    /* Start offset through the whole frameserver: 40.5 units into the video stream (each 756,048-byte unit
     * is 49.2 packets of 15,360 B plus 24-byte tags), the first published unit is 41 or 42. */
    uint64_t per_unit = 756048 + 24ull * 756048 / 15360;
    fs_config cfg; memset(&cfg, 0, sizeof cfg);
    cfg.capture.replay_path = p; cfg.capture.replay_start_offset = per_unit * 81 / 2;
    cfg.sink.on_frame = on_frame; cfg.on_end = on_end;
    frameserver *f = NULL;
    CHECK(fs_open(&f, &cfg) == 0 && fs_start(f) == 0, "open/start at an offset");
    pthread_mutex_lock(&m); while (!atomic_load(&ended)) pthread_cond_wait(&c, &m); pthread_mutex_unlock(&m);
    fs_stats s; fs_stop(f); fs_get_stats(f, &s); fs_close(f);
    CHECK(first_counter == 41 || first_counter == 42, "first published unit after the offset: %llu, expected 41 or 42", (unsigned long long)first_counter);
    CHECK(frames == 119 - first_counter, "published %llu frames after the offset, expected %llu", (unsigned long long)frames, (unsigned long long)(119 - first_counter));
    printf(fails ? "REPLAY PROBE: %d FAILURES\n" : "REPLAY PROBE PASS\n", fails);
    return fails ? 1 : 0;
}
