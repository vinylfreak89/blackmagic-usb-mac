// publish_copy: publish a finished scratch file to a destination on ANOTHER filesystem, where an
// atomic rename is impossible: exclusive create, full copy, fsync, read back and byte-compare
// against the source, and only then delete the source. Never replaces an existing destination;
// on any failure the partial destination is removed and the source is kept.
// Returns 0 published+verified+source removed; 1 published+verified but the source could not be
// removed; -1 failed (errno set), destination absent, source intact.
// Plain POSIX, no OBS dependency, so it is unit-tested on its own (make test).
#ifndef PUBLISH_COPY_H
#define PUBLISH_COPY_H
int publish_by_copy(const char *src, const char *final);
#endif
