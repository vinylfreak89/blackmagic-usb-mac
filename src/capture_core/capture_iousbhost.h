/* capture_iousbhost: the Shuttle through Apple's IOUSBHost framework instead of libusb, with every isochronous read
 * scheduled at an explicit bus frame number. libusb's Darwin backend picks the frame itself and moves a late
 * resubmission past frames it never reads, so those frames could only be inferred (capture_core's unread-slot model).
 * Here each endpoint's reads are queued at consecutive frames; a read whose frame has already passed is refused by
 * macOS (measured 2026-10-17: "Unable to enqueue IO."), is rescheduled a few frames ahead, and the frames between are
 * an exact count, handed over with the transfer they precede. Internal to capture_core (built with
 * -DCC_WITH_IOUSBHOST); plain C interface. */
#ifndef CAPTURE_IOUSBHOST_H
#define CAPTURE_IOUSBHOST_H
#include <stddef.h>
#include <stdint.h>
typedef struct ih_dev ih_dev;
typedef struct {
    void *ctx;
    /* All callbacks run on one serial dispatch queue (QOS_CLASS_USER_INTERACTIVE), so they are one producer; the
     * queue's thread can change between calls. */
    /* Before a transfer's packets: its IOReturn, and the frames left unread just before it (exact; 0 normally). */
    void (*on_transfer)(void *ctx, int ep_index, uint32_t seq, int ioreturn, uint64_t unread_frames);
    /* ok: the packet completed (a short packet is ok); actual is 0 when not ok */
    void (*on_packet)(void *ctx, int ep_index, uint32_t seq, int pkt_index, int ok, uint32_t status,
                      uint32_t req, uint32_t actual, const uint8_t *data);
    void (*on_tick)(void *ctx);     /* once a second */
    /* The session cannot go on: the device left (reason 1, ioreturn 0) or a transfer could not be queued (reason 2,
     * with the IOReturn and the transfer's endpoint and seq). Called once; requeuing stops; the caller stops. */
    void (*on_fatal)(void *ctx, int reason, int ioreturn, int ep_index, uint32_t seq);
    /* A line for the session's diagnosis log (rare: one per unread-frame gap). Optional. */
    void (*on_diag)(void *ctx, const char *line);
} ih_callbacks;
typedef struct {
    uint64_t submits[2], late_resubmits[2], unread_frames[2];
    uint64_t completions[2], aborted[2];
    int fleet[2];                   /* transfers in flight per endpoint when the stop began */
    /* Bus check: the kernel's completion time of each transfer's last packet steps by the transfer's frames from one
     * transfer to the next, plus any unread gap. Largest departure from that over gap-free steps, in ms, and the
     * largest across a gap (the gap's own reading, see on_diag); steps measured. */
    double step_dev_ms[2], gap_dev_ms[2];
    uint64_t steps[2];
    int transfers;                  /* allocated (both endpoints) */
    int incomplete;                 /* transfers still in flight 5 s after the abort: callbacks were cut off */
} ih_stats;
/* Open the Shuttle and run the start sequence (alt 0, mode words, alt 1 -> alt 2, mode word, latch). Both iso
 * endpoints must have bInterval 1 (8 packets per 1 ms frame), or it refuses. 0 or a negative capture_core error
 * (CC_ERR_NODEVICE / CC_ERR_USB); err gets a description. */
int  ih_open(ih_dev **out, uint32_t mode_word, uint32_t r4, uint32_t latch, char *err, size_t errn);
/* Queue `xfers` transfers per endpoint at consecutive frames and keep them queued until ih_stop. npk: a multiple
 * of 8 (one frame). On failure the caller still calls ih_stop. */
int  ih_start(ih_dev *d, const ih_callbacks *cb, int xfers, int v_npk, int v_pkt, int a_npk, int a_pkt, char *err, size_t errn);
/* Stop requeuing, abort both pipes, wait until no callback can run any more (5 s backstop: then callbacks are cut
 * off and st->incomplete is set), select alt 0. */
void ih_stop(ih_dev *d, ih_stats *st);
void ih_close(ih_dev *d);
#endif
