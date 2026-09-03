#include "publish_copy.h"
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>

int publish_by_copy(const char *src, const char *final){
    int in = open(src, O_RDONLY); if (in < 0) return -1;
    int out = open(final, O_WRONLY | O_CREAT | O_EXCL, 0644); if (out < 0){ int e = errno; close(in); errno = e; return -1; }
    static char buf[1 << 16], b2[1 << 16];   /* single-threaded use by design (called under the plugin's transition mutex) */
    ssize_t n; int ok = 1; int e = 0;
    while ((n = read(in, buf, sizeof buf)) > 0){
        ssize_t off = 0;
        while (off < n){ ssize_t w = write(out, buf + off, (size_t)(n - off)); if (w <= 0){ ok = 0; e = errno; break; } off += w; }
        if (!ok) break;
    }
    if (n < 0){ ok = 0; e = errno; }
    if (ok && fsync(out) != 0){ ok = 0; e = errno; }
    if (close(out) != 0 && ok){ ok = 0; e = errno; }
    if (ok){   /* verify: byte-compare the published file against the scratch original */
        int chk = open(final, O_RDONLY);
        if (chk < 0){ ok = 0; e = errno; }
        else {
            if (lseek(in, 0, SEEK_SET) != 0){ ok = 0; e = errno; }
            while (ok){
                ssize_t a = read(in, buf, sizeof buf), b = read(chk, b2, sizeof b2);
                if (a < 0 || b < 0){ ok = 0; e = errno; break; }
                if (a != b || (a > 0 && memcmp(buf, b2, (size_t)a) != 0)){ ok = 0; e = EIO; break; }
                if (a == 0) break;
            }
            close(chk);
        }
    }
    close(in);
    if (!ok){ unlink(final); errno = e; return -1; }
    return unlink(src) == 0 ? 0 : 1;
}
