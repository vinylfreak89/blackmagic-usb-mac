// publish_copy: publish a finished scratch file to a destination on ANOTHER filesystem, where a
// cross-filesystem rename is impossible. The copy is staged on the DESTINATION filesystem under a
// random ".partial-*" name next to the final path (so the final name is never visible until it is
// complete), fsynced, read back and byte-compared against the source (read-full on both sides, so
// legal short reads cannot fail a byte-identical file), then renamed into place with
// renamex_np(RENAME_EXCL) — the final name is never replaced — and only then is the source deleted.
//
// What "published" means here: the destination FILESYSTEM has acknowledged the bytes (fsync of the
// file and its directory). On a write-back cloud volume that is cache-visible equality, not proof
// of remote durability; the caller decides whether to keep the source until the volume reports
// its uploads complete.
//
// Returns:  0 published, verified, source removed
//           1 published and verified, but the source could not be removed
//          -1 failed before or during staging; the staging file was removed; source intact
//          -2 failed AND the staging file could not be removed (errno from the cleanup); source intact
// Plain POSIX, no OBS dependency, reentrant (no static state), unit-tested on its own (make test).
#ifndef PUBLISH_COPY_H
#define PUBLISH_COPY_H
int publish_by_copy(const char *src, const char *final);
// Test hook (weak): called at named steps; a test returns nonzero to make that step fail.
enum publish_step { PUB_STEP_WRITE = 1, PUB_STEP_FSYNC, PUB_STEP_REOPEN, PUB_STEP_COMPARE, PUB_STEP_RENAME, PUB_STEP_CLEANUP, PUB_STEP_UNLINK_SRC };
extern int (*publish_copy_test_fail)(enum publish_step step);
#endif
