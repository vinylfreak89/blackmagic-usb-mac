/* capture_iousbhost: the Shuttle through Apple's IOUSBHost framework instead of libusb, with every isochronous read
 * scheduled at an explicit bus frame number. libusb's Darwin backend picks the frame itself and moves a late
 * resubmission past frames it never reads, so those frames could only be inferred (capture_core's unread-slot model).
 * Here each endpoint's reads are queued at consecutive frames. A read lying wholly in the past is refused by macOS
 * (measured 2026-10-17); it is queued a few frames ahead, and the frames between are an exact count, handed over with
 * the transfer they precede. A read only partly in the past is accepted and its past packets fail with
 * kIOReturnIsoTooOld; those are counted per transfer, against a prediction from the frame it was queued at. Internal to capture_core (built with
 * -DCC_WITH_IOUSBHOST); plain C interface. */
#ifndef CAPTURE_IOUSBHOST_H
#define CAPTURE_IOUSBHOST_H
#include <stddef.h>
#include <stdint.h>
typedef struct ih_dev ih_dev;
typedef struct {
    void *ctx;
    /* Completions, ticks and fatal reports run on one serial dispatch queue (QOS_CLASS_USER_INTERACTIVE), so they
     * are one producer; the queue's thread can change between calls. Device-termination notices arrive on
     * IOUSBHost's own queue and are moved onto this one. The only exception: a fatal report during ih_start runs
     * on ih_start's caller, inside the queue (dispatch_sync). Nothing is called before
     * ih_start, after ih_go only data flows, and nothing after ih_stop returns. */
    /* Before a transfer's packets: its IOReturn, the frames left unread just before it (exact; 0 normally), and its
     * packets that macOS failed as past due when it was queued (kIOReturnIsoTooOld; they follow as DATA records
     * with that status). */
    void (*on_transfer)(void *ctx, int ep_index, uint32_t seq, int ioreturn, uint64_t unread_frames, uint32_t too_old);
    /* ok: the packet completed (a short packet is ok); actual is 0 when not ok */
    void (*on_packet)(void *ctx, int ep_index, uint32_t seq, int pkt_index, int ok, uint32_t status,
                      uint32_t req, uint32_t actual, const uint8_t *data);
    void (*on_tick)(void *ctx);     /* once a second */
    /* A completed transfer could not be requeued for a reason other than lateness; it is retried every millisecond
     * until the deadline. Called once per requeue (the first refusal), seq: that transfer's last one. */
    void (*on_submit_failed)(void *ctx, int ep_index, uint32_t seq, int ioreturn);
    /* The session cannot go on: the device left (reason 1, ioreturn 0) or a transfer could not be queued within
     * the deadline (reason 2, with the IOReturn, endpoint and seq). Each reason at most once (a reason 1 after a
     * reason 2 still comes: an unplug can fail a requeue before its notice arrives); requeuing stops. */
    void (*on_fatal)(void *ctx, int reason, int ioreturn, int ep_index, uint32_t seq);
    /* A line for the session's diagnosis log (rare: one per unread-frame gap). Optional. */
    void (*on_diag)(void *ctx, const char *line);
} ih_callbacks;
typedef struct {
    uint64_t submits[2], late_resubmits[2], unread_frames[2];
    uint64_t unread_delivered[2];   /* of unread_frames, handed over with on_transfer; the rest were on transfers */
    uint64_t unread_at_stop[2];     /*   aborted at the stop (past the stream's end): delivered + at_stop == unread */
    uint64_t too_old[2];            /* packets failed as past due when queued (also DATA records with that status) */
    uint64_t too_old_mismatch[2];   /* transfers whose too-old count differed from the prediction (see on_diag) */
    uint64_t submit_failures[2], resubmit_recovered[2];   /* refused attempts (each retry), requeues that recovered */
    uint64_t completions[2], aborted[2];
    int fleet[2];                   /* transfers in flight per endpoint when the stop began */
    int transfers, transfers_freed; /* allocated (both endpoints) / released by us at ih_stop (none if incomplete) */
    int incomplete;                 /* the queue did not drain within 5 s of the abort: callbacks were cut off */
    int device_gone;                /* a termination notice arrived at any time before ih_stop returned */
    /* Bus check: the kernel's completion time of each transfer's last packet steps by the transfer's frames from one
     * transfer to the next, plus any unread gap. Largest departure from that over gap-free steps, in ms, and the
     * largest across a gap (the gap's own reading, see on_diag); steps measured. */
    double step_dev_ms[2], gap_dev_ms[2];
    uint64_t steps[2];
} ih_stats;
/* Open the Shuttle and run the start sequence (alt 0, mode words, alt 1 -> alt 2, mode word, latch). Both iso
 * endpoints must have bInterval 1 (8 packets per 1 ms frame), or it refuses. 0 or a negative capture_core error
 * (CC_ERR_NODEVICE / CC_ERR_USB); err gets a description. */
int  ih_open(ih_dev **out, uint32_t mode_word, uint32_t r4, uint32_t latch, char *err, size_t errn);
/* Queue `xfers` transfers per endpoint at consecutive frames, the first ones held back from the callbacks until
 * ih_go (the hardware reads meanwhile; 512 ms are queued). npk: a multiple of 8 (one frame). A refusal here is
 * fatal at once; later ones are retried for deadline_ms. On failure the caller still calls ih_stop. */
int  ih_start(ih_dev *d, const ih_callbacks *cb, int xfers, int v_npk, int v_pkt, int a_npk, int a_pkt,
              int deadline_ms, char *err, size_t errn);
void ih_go(ih_dev *d);              /* start the callbacks (after a successful ih_start) */
/* Stop requeuing, abort both pipes, wait until no callback can run any more, select alt 0, release the transfers.
 * Without ih_go (a failed or refused start) completions are discarded, never handed over. Each wait has a 5 s
 * backstop: after it, callbacks are cut off and st->incomplete is set (then never call ih_close). Never call it
 * from a callback. */
void ih_stop(ih_dev *d, ih_stats *st);
void ih_close(ih_dev *d);
#endif
