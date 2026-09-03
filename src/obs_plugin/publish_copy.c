#include "publish_copy.h"
#include <fcntl.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <libgen.h>

int (*publish_copy_test_fail)(enum publish_step step) = NULL;
ssize_t (*publish_copy_test_read)(int fd, void *buf, size_t n) = NULL;
#define FAIL_AT(step) (publish_copy_test_fail && publish_copy_test_fail(step))
ssize_t (*publish_copy_test_write)(int fd, const void *buf, size_t n) = NULL;
int (*publish_copy_test_close)(int fd) = NULL;
static ssize_t do_read(int fd, void *buf, size_t n){ return publish_copy_test_read ? publish_copy_test_read(fd, buf, n) : read(fd, buf, n); }
static ssize_t do_write(int fd, const void *buf, size_t n){ return publish_copy_test_write ? publish_copy_test_write(fd, buf, n) : write(fd, buf, n); }
static int do_close_out(int fd){ return publish_copy_test_close ? publish_copy_test_close(fd) : close(fd); }

/* read exactly `want` bytes unless EOF; returns bytes read (< want only at EOF), -1 on error */
static ssize_t read_full(int fd, char *buf, size_t want){
    size_t got = 0;
    while (got < want){ ssize_t n = do_read(fd, buf + got, want - got); if (n < 0){ if (errno == EINTR) continue; return -1; } if (n == 0) break; got += (size_t)n; }
    return (ssize_t)got;
}
static int write_full(int fd, const char *buf, size_t len){
    size_t off = 0;
    while (off < len){ ssize_t w = do_write(fd, buf + off, len - off); if (w < 0){ if (errno == EINTR) continue; return -1; } if (w == 0){ errno = EIO; return -1; } off += (size_t)w; }
    return 0;
}
static int fsync_dir_of(const char *path){
    char *copy = strdup(path); if (!copy) return -1;
    int d = open(dirname(copy), O_RDONLY); free(copy); if (d < 0) return -1;
    int rc = fsync(d); int e = errno; close(d); errno = e; return rc;   /* some filesystems refuse fsync on a directory: treated as best effort by the caller */
}

int publish_by_copy(const char *src, const char *final){
    enum { BUF = 1 << 16 };
    char *buf = malloc(BUF), *b2 = malloc(BUF);
    char staging[4096]; int e = 0, ok = 1, staged = 0;
    if (!buf || !b2){ free(buf); free(b2); errno = ENOMEM; return -1; }
    int in = open(src, O_RDONLY); if (in < 0){ e = errno; free(buf); free(b2); errno = e; return -1; }
    /* random staging name beside the final path, exclusive: a crash leaves an obvious .partial-* that never blocks a retry */
    int out = -1;
    for (int attempt = 0; attempt < 8 && out < 0; attempt++){
        snprintf(staging, sizeof staging, "%s.partial-%08x%08x", final, (unsigned)arc4random(), (unsigned)arc4random());
        out = open(staging, O_WRONLY | O_CREAT | O_EXCL, 0644);
        if (out < 0 && errno != EEXIST) break;
    }
    if (out < 0){ e = errno; close(in); free(buf); free(b2); errno = e; return -1; }
    staged = 1;
    ssize_t n;
    while (ok && (n = read_full(in, buf, BUF)) != 0){
        if (n < 0){ ok = 0; e = errno; break; }
        if (FAIL_AT(PUB_STEP_WRITE) || write_full(out, buf, (size_t)n) != 0){ ok = 0; e = errno ? errno : EIO; break; }
        if ((size_t)n < BUF) break;
    }
    if (ok && (FAIL_AT(PUB_STEP_FSYNC) || fsync(out) != 0)){ ok = 0; e = errno ? errno : EIO; }
    if (do_close_out(out) != 0 && ok){ ok = 0; e = errno ? errno : EIO; }
    if (ok){   /* verify: read-full both sides, byte-compare */
        int chk = FAIL_AT(PUB_STEP_REOPEN) ? -1 : open(staging, O_RDONLY);
        if (chk < 0){ ok = 0; e = errno ? errno : EIO; }
        else {
            if (lseek(in, 0, SEEK_SET) != 0){ ok = 0; e = errno; }
            while (ok){
                ssize_t a = read_full(in, buf, BUF), b = read_full(chk, b2, BUF);
                if (a < 0 || b < 0){ ok = 0; e = errno; break; }
                if (a != b || (a > 0 && memcmp(buf, b2, (size_t)a) != 0) || FAIL_AT(PUB_STEP_COMPARE)){ ok = 0; e = EIO; break; }
                if ((size_t)a < BUF) break;
            }
            close(chk);
        }
    }
    close(in); free(buf); free(b2);
    if (ok && (FAIL_AT(PUB_STEP_RENAME) || renamex_np(staging, final, RENAME_EXCL) != 0)){ ok = 0; e = errno ? errno : EEXIST; }
    if (!ok){
        if (staged && (FAIL_AT(PUB_STEP_CLEANUP) || unlink(staging) != 0)){ if (!errno) errno = EIO; return -2; }
        errno = e; return -1;
    }
    if (FAIL_AT(PUB_STEP_DIRSYNC) || fsync_dir_of(final) != 0) return 1;   /* published, but the directory entry may not be durable yet: keep the source */
    if (FAIL_AT(PUB_STEP_UNLINK_SRC) || unlink(src) != 0) return 1;
    return 0;
}
