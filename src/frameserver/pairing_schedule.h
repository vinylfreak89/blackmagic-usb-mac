#ifndef FS_PAIRING_SCHEDULE_H
#define FS_PAIRING_SCHEDULE_H
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
/* Loaded once at open; immutable during streaming. No hot-path allocation. */
typedef struct { uint64_t first; int reversed; char *note; } fs_pairing_row;
typedef struct { fs_pairing_row *rows; size_t count; } fs_pairing_schedule;
/* Load into zero-initialized storage; caller frees after workers have stopped. */
int fs_pairing_load(fs_pairing_schedule *, const char *path);
void fs_pairing_free(fs_pairing_schedule *);
const fs_pairing_row *fs_pairing_find(const fs_pairing_schedule *, uint64_t counter);
int fs_pairing_write_note(FILE *, const char *);
#endif
