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
    /* An end without picture units near it (a capture ending with the deck off): 40 MiB of audio-only
     * records after the fixture. The default window finds nothing in the last 32 MiB and widens to
     * 256 MiB; an explicit 32 MiB window does not widen. */
    {
        char tpath[] = "/tmp/replay_probe_tail_XXXXXX"; int fd = mkstemp(tpath);
        FILE *in = fopen(p, "rb"); static uint8_t buf[1 << 20]; size_t got;
        while (fd >= 0 && in && (got = fread(buf, 1, sizeof buf, in)) > 0) if (write(fd, buf, got) != (ssize_t)got) break;
        if (in) fclose(in);
        memset(buf, 0, sizeof buf);
        for (uint32_t seq = 0; fd >= 0 && seq < 20480; seq++){   /* 20,480 x (24 + 2048) B = 42.4 MB */
            uint8_t rec[24 + 2048] = {0}; uint32_t magic = 0x31504143u, req = 2048, act = 2048;
            memcpy(rec, &magic, 4); rec[4] = 0; rec[5] = 0x84; memcpy(rec + 8, &seq, 4); memcpy(rec + 16, &req, 4); memcpy(rec + 20, &act, 4);
            if (write(fd, rec, sizeof rec) != (ssize_t)sizeof rec) break;
        }
        if (fd >= 0) close(fd);
        CHECK(fs_replay_probe(tpath, 0, NULL, &sp) == 0 && sp.last_counter == 118, "a unit-less 40 MiB tail: widened probe found last %s%u", sp.have_last ? "" : "(none) ", sp.last_counter);
        CHECK(fs_replay_probe(tpath, 32u << 20, NULL, &sp) != 0 && !sp.have_last, "an explicit 32 MiB window widened (found last %u)", sp.last_counter);
        unlink(tpath);
    }
    _Atomic int abort_now = 1;
    CHECK(fs_replay_probe(p, 0, &abort_now, &sp) != 0, "an aborted probe reported success");

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
