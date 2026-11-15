/* The fake IOUSBHost the backend test builds capture_iousbhost.m against (-DIH_FAKE, see ih_fake_iousbhost.m):
 * included by the backend after the real headers, so its IOKit registry calls reach the fake device instead of
 * the bus, and the IOUSBHost classes it uses are the fake's (the framework is not linked). The bus clock is real
 * time, one frame per millisecond; every packet carries its microframe number, so a test can account for every
 * microframe. */
#ifndef IH_FAKE_IOKIT_H
#define IH_FAKE_IOKIT_H
#include <IOKit/IOKitLib.h>
#include <stdatomic.h>
#include <stdint.h>

io_service_t ih_fake_get_matching(mach_port_t port, CFDictionaryRef matching);
kern_return_t ih_fake_release(io_object_t o);
kern_return_t ih_fake_children(io_registry_entry_t e, const io_name_t plane, io_iterator_t *it);
io_object_t ih_fake_next(io_iterator_t it);
boolean_t ih_fake_conforms(io_object_t o, const io_name_t cls);
CFTypeRef ih_fake_property(io_registry_entry_t e, CFStringRef key, CFAllocatorRef a, IOOptionBits o);
#define IOServiceGetMatchingService ih_fake_get_matching
#define IOObjectRelease ih_fake_release
#define IORegistryEntryGetChildIterator ih_fake_children
#define IOIteratorNext ih_fake_next
#define IOObjectConformsTo ih_fake_conforms
#define IORegistryEntryCreateCFProperty ih_fake_property

/* test controls */
typedef struct {
    _Atomic int absent;             /* no device on the bus */
    _Atomic int busy;               /* another process holds it open: opening fails with kIOReturnExclusiveAccess */
    _Atomic int refuse[2];          /* the next N enqueues per endpoint are refused with kIOReturnNoResources */
    _Atomic int refuse_all[2];      /* every enqueue is refused that way */
    _Atomic long enqueues[2], refusals[2], too_old_packets[2];
    _Atomic int abort_delay_ms;     /* aborted transfers complete this late */
    _Atomic int gone;               /* set by ih_fake_terminate: every enqueue fails with kIOReturnNoDevice */
    _Atomic uint64_t queue_end[2];  /* out: the frame after the last accepted transfer per endpoint */
    _Atomic long completions[2];
    /* the late_at-th completion (1-based) is held on the completion queue until the bus is late_k frames past the
     * end of what is queued, so that transfer's requeue lands exactly that late (the backlog then catches up) */
    _Atomic long late_at[2]; _Atomic int late_k[2];
    /* a dead link with the device still attached (as measured 2026-11-10): while set, each transfer that falls due
     * completes with kIOReturnNoResources on the transfer and every packet, no data, no earlier than dead_spacing_ms
     * after the previous such completion on either endpoint (the kernel's ~2 s procession); enqueues are accepted */
    _Atomic int link_dead, dead_spacing_ms;
    _Atomic int dead_left[2];       /* also fail the next N completions per endpoint (counts down) */
    _Atomic int dead_pkt_ok;        /* the failed transfers' packets say Success with no data (the transfer still fails) */
    /* nonzero: the link dies at this bus frame (with link_dead set). A transfer wholly before it completes normally;
     * the one spanning it keeps its earlier packets' data and fails the rest (measured 2026-11-15: the kernel's first
     * failed completion on each endpoint was such a transfer); later ones fail wholly */
    _Atomic uint64_t dead_from_frame;
    _Atomic long dead_partial[2];   /* out: failed completions that delivered packets before the death frame */
    _Atomic uint64_t first_dead_ms; /* out: CLOCK_UPTIME_RAW ms of the first failed completion on either endpoint */
    _Atomic long dead_completions[2];
    _Atomic uint64_t dead_next_ns;  /* internal: the procession's next free slot */
} ih_fake_controls;
extern ih_fake_controls ih_fake;
void ih_fake_terminate(void);       /* deliver kIOMessageServiceIsTerminated on an internal queue */
uint64_t ih_fake_frame_now(void);
extern _Atomic long ih_fake_xfer_deallocs;   /* the backend's transfer objects deallocated, all sessions */
#endif
