#include "tracking_meter_tap.h"
#include <pthread.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define FRAME_BYTES (720 * 480 * 2)

// The frame callback and the measuring thread hand one buffer back and forth:
// slot_state EMPTY -> (callback copies) FULL -> (thread takes) EMPTY. The callback never waits: if
// the slot is still FULL it skips the frame. A condvar wakes the thread on FULL and on stop.
enum { EMPTY = 0, FULL = 1 };
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;   // slot hand-off wake-up, reading and history
static pthread_cond_t wake = PTHREAD_COND_INITIALIZER;
static pthread_t thread;
static int running;                                         // thread exists (guarded by lock)
static int stopping;                                        // ask the thread to finish (guarded by lock)
static _Atomic int active;                                  // read by the frame callback without the lock
static _Atomic int slot_state;
static _Atomic uint64_t offered, measured, skipped_busy, no_reading, last_offer_ns;
static uint8_t *slot, *work;
static tm_window window;
static tm_reading reading;
static double history[TMT_HISTORY][TM_CHANNELS];
static unsigned history_n;

static uint64_t now_ns(void){ return clock_gettime_nsec_np(CLOCK_UPTIME_RAW); }

static void *measure_loop(void *arg){
    (void)arg;
    pthread_setname_np("shuttle-tracking-meter");
    pthread_mutex_lock(&lock);
    for (;;){
        while (!stopping && atomic_load(&slot_state) != FULL) pthread_cond_wait(&wake, &lock);
        if (stopping) break;
        uint8_t *t = slot; slot = work; work = t;          // take the full buffer, give back the spare
        atomic_store(&slot_state, EMPTY);
        pthread_mutex_unlock(&lock);
        tm_frame m; tm_measure_uyvy(work, 720 * 2, &m);     // the measuring, outside the lock
        atomic_fetch_add(&measured, 1);
        if (!m.valid) atomic_fetch_add(&no_reading, 1);
        pthread_mutex_lock(&lock);
        tm_window_add(&window, &m);
        tm_window_read(&window, &reading);
    }
    pthread_mutex_unlock(&lock);
    return NULL;
}

void tmt_start(void){
    pthread_mutex_lock(&lock);
    if (!running){
        if (!slot) slot = malloc(FRAME_BYTES);
        if (!work) work = malloc(FRAME_BYTES);
        if (slot && work){
            tm_window_reset(&window); memset(&reading, 0, sizeof reading);
            history_n = 0; stopping = 0;
            atomic_store(&slot_state, EMPTY);
            atomic_store(&offered, 0); atomic_store(&measured, 0); atomic_store(&skipped_busy, 0); atomic_store(&no_reading, 0);
            if (pthread_create(&thread, NULL, measure_loop, NULL) == 0){ running = 1; atomic_store(&active, 1); }
        }
    }
    pthread_mutex_unlock(&lock);
}

void tmt_stop(void){
    pthread_mutex_lock(&lock);
    atomic_store(&active, 0);
    int join = running;
    if (running){ stopping = 1; pthread_cond_signal(&wake); }
    pthread_mutex_unlock(&lock);
    if (join){
        pthread_join(thread, NULL);
        pthread_mutex_lock(&lock); running = 0; pthread_mutex_unlock(&lock);
    }
}

void tmt_offer(const uint8_t *uyvy, size_t bpr){
    if (!atomic_load(&active)) return;
    uint64_t n = atomic_fetch_add(&offered, 1);
    atomic_store(&last_offer_ns, now_ns());
    if (n % TMT_EVERY) return;
    if (atomic_load(&slot_state) != EMPTY){ atomic_fetch_add(&skipped_busy, 1); return; }
    // The slot is EMPTY, so the thread is not reading it: copy without the lock, then publish.
    for (int r = 0; r < 480; r++) memcpy(slot + (size_t)r * 1440, uyvy + (size_t)r * bpr, 1440);
    pthread_mutex_lock(&lock);
    atomic_store(&slot_state, FULL);
    pthread_cond_signal(&wake);
    pthread_mutex_unlock(&lock);
}

void tmt_snapshot_take(tmt_snapshot *out){
    memset(out, 0, sizeof *out);
    pthread_mutex_lock(&lock);
    out->active = atomic_load(&active);
    uint64_t last = atomic_load(&last_offer_ns);
    out->fresh = last && now_ns() - last < 1500000000ull;
    out->frames_offered = atomic_load(&offered); out->frames_measured = atomic_load(&measured);
    out->frames_skipped_busy = atomic_load(&skipped_busy); out->frames_no_reading = atomic_load(&no_reading);
    out->now = reading;
    if (out->active){                                      // one history point per snapshot
        if (history_n == TMT_HISTORY){ memmove(history[0], history[1], sizeof history[0] * (TMT_HISTORY - 1)); history_n--; }
        for (int c = 0; c < TM_CHANNELS; c++) history[history_n][c] = (out->fresh && reading.valid) ? reading.ratio[c] : 0;
        history_n++;
    }
    out->history_n = history_n;
    memcpy(out->history, history, sizeof history[0] * history_n);
    pthread_mutex_unlock(&lock);
}
