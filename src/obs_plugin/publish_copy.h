// publish_copy: publish a finished scratch file to a destination on ANOTHER filesystem, where a
// cross-filesystem rename is impossible. The copy is staged on the DESTINATION filesystem under a
// random ".partial-*" name next to the final path (so the final name is never visible until it is
// complete), fsynced, read back and byte-compared against the source (read-full on both sides, so
// legal short reads cannot fail a byte-identical file), then renamed into place with
// renamex_np(RENAME_EXCL) — the final name is never replaced — and only then is the source deleted.
//
// What "published" means here: the destination FILESYSTEM has acknowledged the bytes (fsync of the
// file; fsync of its directory is attempted and, if it fails, the source is kept and 1 is
// returned). On a write-back cloud volume that is cache-visible equality, not proof of remote
// durability — the volume's own upload state says when it is remote; this API cannot see it.
//
// Returns:  0 published, verified, source removed
//           1 published and verified, but the source was kept: it could not be removed, or the
//             directory fsync failed (the entry may not be durable yet)
//          -1 failed before or during staging; the staging file was removed; source intact
//          -2 failed AND the staging file could not be removed (errno from the cleanup); source intact
// Plain POSIX, no OBS dependency, reentrant (no static state), unit-tested on its own (make test).
#ifndef PUBLISH_COPY_H
#define PUBLISH_COPY_H
int publish_by_copy(const char *src, const char *final);
// Test hook (weak): called at named steps; a test returns nonzero to make that step fail.
enum publish_step { PUB_STEP_WRITE = 1, PUB_STEP_FSYNC, PUB_STEP_REOPEN, PUB_STEP_COMPARE, PUB_STEP_RENAME, PUB_STEP_CLEANUP, PUB_STEP_DIRSYNC, PUB_STEP_UNLINK_SRC };
extern int (*publish_copy_test_fail)(enum publish_step step);
// Test hook: when set, every read() the helper issues goes through it (short-read / EINTR injection).
#include <sys/types.h>
extern ssize_t (*publish_copy_test_read)(int fd, void *buf, size_t n);
// Test hooks: every write() and the close() of the staging file go through these when set
// (partial-write / EINTR / zero-byte-write and close-failure injection).
extern ssize_t (*publish_copy_test_write)(int fd, const void *buf, size_t n);
extern int (*publish_copy_test_close)(int fd);
#endif
