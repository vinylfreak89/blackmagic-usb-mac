#ifndef FS_FIELD_ORDER_H
#define FS_FIELD_ORDER_H
#include <stdint.h>

/* Raw transport-slot scene-cut observer, NOT a spatial parity estimator.
 * Worker-owned, allocated once only when enabled; never sees repaired pixels. */
enum { FO_WIDTH=720, FO_ROWS=60, FO_HISTORY=30, FO_WARMUP=8 };
typedef struct {
    double change[2], threshold[2];
    uint64_t cut_first;
    unsigned spikes, votes;
    int measured, ready, event; /* event: 0 none, 1 aligned, 2 reversed, 3 ambiguous */
    int confirmed;
} fo_evidence;
typedef struct {
    uint8_t previous[2][FO_ROWS*FO_WIDTH];
    double history[2][FO_HISTORY];
    unsigned count, cursor;
    uint64_t counter, epoch, first;
    int have_previous, episode, last_verdict;
    unsigned votes;
} fo_detector;

void fo_reset(fo_detector *d);
/* y is the untouched 525x720 storage raster. broken excludes counter aliases,
 * host loss and incomplete units, even if extended counters look consecutive. */
fo_evidence fo_observe(fo_detector *d,const uint8_t *y,uint64_t counter,
                       uint64_t epoch,int broken);
#endif
