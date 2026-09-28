/* async_file: bytes arrive exactly and in order across ring wraps; a hung disk never blocks the
 * stream; an overflow or a write error fails every later write and the close, never thins the file
 * silently; an existing file is never truncated. */
#include "../async_file.h"
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static int fails;
#define CHECK(c, ...) do { if (!(c)) { fails++; fprintf(stderr, "FAIL: " __VA_ARGS__); fprintf(stderr, "\n"); } } while (0)

static pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER; static pthread_cond_t cv = PTHREAD_COND_INITIALIZER;
static int mode, hung, release_disk, calls; static size_t max_write;   /* mode 0 pass, 1 hang, 2 fail */
static ssize_t disk(int fd, const void *b, size_t n){
    pthread_mutex_lock(&m); calls++; if (n > max_write) max_write = n;
    if (mode == 2){ pthread_mutex_unlock(&m); errno = ENOSPC; return -1; }
    if (mode == 1){
        hung = 1; pthread_cond_broadcast(&cv);
        struct timespec ts; clock_gettime(CLOCK_REALTIME, &ts); ts.tv_sec += 60;   /* deadline: a missing release fails loudly */
        while (!release_disk) if (pthread_cond_timedwait(&cv, &m, &ts)){ fprintf(stderr, "FAIL: disk never released\n"); _exit(2); }
    }
    pthread_mutex_unlock(&m);
    return write(fd, b, n > 7 ? 7 : n);   /* short writes: the writer must loop */
}
static void set_mode(int md){ pthread_mutex_lock(&m); mode = md; hung = 0; release_disk = 0; calls = 0; max_write = 0; pthread_mutex_unlock(&m); }
static void release(void){ pthread_mutex_lock(&m); release_disk = 1; pthread_cond_broadcast(&cv); pthread_mutex_unlock(&m); }
static void wait_hung(void){
    pthread_mutex_lock(&m); struct timespec ts; clock_gettime(CLOCK_REALTIME, &ts); ts.tv_sec += 60;
    while (!hung) if (pthread_cond_timedwait(&cv, &m, &ts)){ fprintf(stderr, "FAIL: writer never reached the disk\n"); _exit(2); }
    pthread_mutex_unlock(&m);
}
static double now(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
static size_t file_size(const char *p){ FILE *f = fopen(p, "rb"); if (!f) return 0; fseek(f, 0, SEEK_END); long n = ftell(f); fclose(f); return (size_t)n; }

int main(void){
    fs_async_file_test_write = disk;
    char path[] = "/tmp/async_file_test_XXXXXX"; int fd = mkstemp(path); close(fd); unlink(path);

    /* 1. Round trip under a hung disk: 4 KiB ring, rows well past its size in total, written while the
     * disk hangs (they must not block), then the disk returns and the file is byte-exact. */
    set_mode(1);
    FILE *f = fs_async_fopen_excl(path, 4096, 100);
    CHECK(f != NULL, "open"); if (!f) return 1;
    CHECK(fprintf(f, "row %d %s\n", 0, "first") > 0, "first row");
    wait_hung();
    double t0 = now(); int ok = 1;
    for (int i = 1; i < 60; i++) if (fprintf(f, "row %d %s\n", i, "while the disk hangs") < 0) ok = 0;   /* 60 rows < 4096 B */
    double took = now() - t0;
    CHECK(ok && !ferror(f), "rows written while the disk hangs must succeed");
    CHECK(took < 0.5, "rows blocked on a hung disk (%.3f s)", took);
    release();
    char expect[1 << 16]; size_t el = 0;
    el += (size_t)snprintf(expect + el, sizeof expect - el, "row %d %s\n", 0, "first");
    for (int i = 1; i < 60; i++) el += (size_t)snprintf(expect + el, sizeof expect - el, "row %d %s\n", i, "while the disk hangs");
    for (int i = 60; i < 600; i++){   /* ~20 KiB through a 4 KiB ring: wraps many times */
        char r[64]; int n = snprintf(r, sizeof r, "row %d after the disk returned\n", i);
        memcpy(expect + el, r, (size_t)n); el += (size_t)n;
        if (fputs(r, f) == EOF){ CHECK(0, "a write failed with the disk healthy (row %d)", i); break; }
        /* keep the 4 KiB ring from overflowing (that is case 3): let the 7-byte writer reach within 2 KiB */
        double t1 = now();
        while (el > 2048 && file_size(path) < el - 2048){ if (now() - t1 > 60){ fprintf(stderr, "FAIL: writer stalled\n"); _exit(2); } usleep(200); }
    }
    CHECK(fclose(f) == 0, "close after a clean run must succeed");
    CHECK(max_write <= 100, "a write of %zu bytes exceeded the chunk", max_write);
    {
        FILE *r = fopen(path, "rb"); char got[1 << 16]; size_t gl = r ? fread(got, 1, sizeof got, r) : 0; if (r) fclose(r);
        CHECK(gl == el && !memcmp(got, expect, el), "file is not byte-exact (%zu vs %zu bytes)", gl, el);
    }

    /* 2. Existing file: refused, untouched. */
    size_t before = file_size(path);
    errno = 0; FILE *g = fs_async_fopen_excl(path, 4096, 100);
    CHECK(g == NULL && errno == EEXIST, "an existing file must be refused with EEXIST (got %p, errno %d)", (void *)g, errno);
    CHECK(file_size(path) == before, "the refused open changed the existing file");
    unlink(path);

    /* 3. Overflow: disk hung, ring 4 KiB, 8 KiB of rows. Writes past capacity fail and keep failing;
     * the close fails; nothing after the refusal reaches the file. */
    set_mode(1);
    f = fs_async_fopen_excl(path, 4096, 100); CHECK(f != NULL, "open (overflow)"); if (!f) return 1;
    fputs("x\n", f); wait_hung();
    int first_fail = -1;
    for (int i = 0; i < 200; i++){ int bad = fprintf(f, "overflow row %04d padding padding\n", i) < 0; if (bad && first_fail < 0) first_fail = i; if (!bad && first_fail >= 0){ CHECK(0, "row %d succeeded after the overflow at %d", i, first_fail); break; } }
    CHECK(first_fail > 0, "the ring never overflowed (first failure %d)", first_fail);
    CHECK(ferror(f), "the stream error flag must be set after an overflow");
    release();
    CHECK(fclose(f) == EOF, "close after an overflow must report the file incomplete");
    unlink(path);

    /* 4. Write error: every write fails; the first write after the error has been seen fails; close fails. */
    set_mode(2);
    f = fs_async_fopen_excl(path, 4096, 100); CHECK(f != NULL, "open (write error)"); if (!f) return 1;
    fputs("first\n", f);
    for (int spin = 0; spin < 2000; spin++){ pthread_mutex_lock(&m); int c = calls; pthread_mutex_unlock(&m); if (c) break; usleep(1000); }
    usleep(20000);   /* the writer records the error right after the failed call */
    CHECK(fputs("second\n", f) == EOF, "a write after a disk error must fail");
    CHECK(fclose(f) == EOF, "close after a disk error must report the file incomplete");
    unlink(path);

    if (fails){ printf("async_file tests: %d FAILURES\n", fails); return 1; }
    printf("async_file tests: PASS\n"); return 0;
}
