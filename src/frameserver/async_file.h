#ifndef FS_ASYNC_FILE_H
#define FS_ASYNC_FILE_H
/* A stdio FILE whose bytes reach the disk on a dedicated writer thread.
 *
 * Why: the decision-log row used to be written on the video worker, so a storage stall (a busy disk, a
 * cloud volume backing up) stalled frame delivery. Measured 2026-09-28: sidecar writes of 280–943 ms
 * under fsync'd load, each one a late handoff to OBS of the same size. Now the worker only copies into a
 * preallocated ring; the writer thread does the write(2) calls, at most `chunk` bytes each.
 *
 * Overflow is never silent: once the ring cannot take a write, that write and every later one fail
 * (the stdio error flag is set, so the caller counts it), and fclose() returns EOF. The file is then
 * incomplete by construction and the caller must treat it so. A write(2) error is handled the same way.
 * Only the stream's own writes reach the ring; fclose() drains it, joins the writer, fsyncs and closes.
 */
#include <stdio.h>
#include <stddef.h>
#include <sys/types.h>

/* Create `path` exclusively (O_EXCL: an existing file is never truncated). NULL on failure, errno set. */
FILE *fs_async_fopen_excl(const char *path, size_t ring_bytes, size_t chunk);

/* Test hook: replaces write(2) in the writer thread when non-NULL (stall and failure injection). */
extern ssize_t (*fs_async_file_test_write)(int fd, const void *buf, size_t n);
#endif
