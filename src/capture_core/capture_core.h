// capture_core — the capture core as a library (design doc §8, productized from capture_tagged_bench).
//
// One callback API over two interchangeable backends:
//   device backend  — libusb isochronous capture from the Intensity Shuttle
//   replay backend  — a recorded .tpc stream, byte-identical delivery
// Consumers cannot tell them apart; that is the point (§8 property 9).
//
// Threading contract: callbacks fire on ONE internal delivery thread, never on
// the USB event thread. A callback that blocks stalls delivery but can never
// stall acquisition — overflow becomes an explicit on_loss(), never a silent
// drop (§8 properties 1, 6, 7). All shared state is atomic; the event thread
// does memcpy + counters only.
#ifndef CAPTURE_CORE_H
#define CAPTURE_CORE_H
#include <stdint.h>
#include <sys/types.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct cc_session cc_session;

enum cc_input  { CC_INPUT_SVIDEO = 0, CC_INPUT_COMPOSITE = 1, CC_INPUT_COMPONENT = 2 };
enum cc_end    { CC_END_STOPPED = 0, CC_END_DEVICE_GONE = 1, CC_END_REPLAY_EOF = 2,
                 CC_END_WRITE_FAILED = 3, CC_END_TRANSFER_FAILED = 4,
                 CC_END_INTERNAL_ERROR = 5 };
enum cc_err    { CC_OK = 0, CC_ERR_ARGS = -1, CC_ERR_NODEVICE = -2, CC_ERR_USB = -3,
                 CC_ERR_NOMEM = -4, CC_ERR_STATE = -5, CC_ERR_IO = -6 };
enum cc_error_kind { CC_ERROR_TRANSFER = 0, CC_ERROR_SUBMIT = 1,
                     CC_ERROR_CONTROL_LOSS = 2 };

#define CC_DEFAULT_READAHEAD_MB 256  /* replay read-ahead when replay_readahead_mb is 0: ~11 s of stream */
#define CC_DEFAULT_RING_MB 256  /* delivery ring when ring_mb is 0; the frameserver sizes its unit pool from it */
#define CC_EP_VIDEO 0x83
#define CC_EP_AUDIO 0x84

// One isochronous packet, exactly as the transport delivered it. `data` is
// valid only for the duration of the callback — copy what you keep.
typedef struct {
    uint8_t  endpoint;      // CC_EP_VIDEO / CC_EP_AUDIO
    uint16_t pkt_index;     // index within its transfer
    uint32_t submit_seq;    // per-endpoint transfer submission sequence
    uint32_t status;        // libusb packet status (0 = completed)
    uint32_t req_len;
    uint32_t actual_len;    // may be 0 — zero-length packets ARE delivered
    const uint8_t *data;
} cc_packet;

typedef struct {
    // Required. Packets carry submission sequence + packet index. The current Darwin backend
    // publishes libusb callback-completion order; consumers that require submission order must
    // reorder/validate from those tags until the inversion replay test justifies moving that
    // policy into this layer.
    void (*on_packet)(void *ctx, const cc_packet *pkt);
    // Optional. Explicit host-side loss (delivery ring overflow): the packets
    // existed and are GONE; the archive must record a hole here. A very large contiguous
    // interval may arrive as adjacent aggregate chunks; sum packet/byte counts across them.
    void (*on_loss)(void *ctx, uint8_t endpoint, uint32_t packets, uint64_t bytes);
    // Optional. Transfer, resubmit, or control-truth-loss marker. `error_kind` is an
    // enum cc_error_kind; CONTROL_LOSS corresponds to .tpc pkt_index=0xFFFE/status=UINT32_MAX.
    // The fleet is never silently shrunk; failures are retried internally.
    void (*on_error)(void *ctx, uint8_t endpoint, uint32_t submit_seq,
                     int status, int error_kind);
    // Optional. ~1 Hz heartbeat with elapsed milliseconds (stall forensics).
    void (*on_tick)(void *ctx, uint32_t elapsed_ms);
    // Required. Fires exactly once; after it returns no callback will fire.
    void (*on_end)(void *ctx, enum cc_end reason);
    void *ctx;
} cc_callbacks;

typedef struct {
    enum cc_input input;        // device backend: which analog input
    int ring_mb;                // delivery ring, 0 => CC_DEFAULT_RING_MB
    const char *replay_path;    // non-NULL => replay backend reading this .tpc
    int replay_pace_us;         // replay: usleep per transfer (0 = as fast as possible;
                                // 16000 ~= the device's real video cadence)
    int resubmit_deadline_ms;   // device: 0 => 2000; persistent failure ends the whole session.
                                // This is deliberately stricter than host-overflow continuation:
                                // one parked transfer means future scheduled slots are absent.
    int fail_stop_on_control_loss; // 0: mark not-clean once and continue; nonzero: marker + stop
    int replay_readahead_mb;    // replay: file read-ahead ring, 0 => CC_DEFAULT_READAHEAD_MB. A reader
                                // thread fills it ahead of the pacer, so a slow read (a network volume)
                                // drains the ring instead of delaying delivery. A read error ends the
                                // session with CC_END_INTERNAL_ERROR, never as a silent end of file.
    int replay_diag;            // replay: nonzero reports a stall diagnosis at the end (diag_log, else stderr): waits on an
                                // empty read-ahead ring (file too slow), slow reads, late pacer wake-ups
    void (*diag_log)(void *ctx, const char *line); // optional: receives diagnosis lines instead of stderr
    void *diag_ctx;
} cc_config;

// Lifecycle: open -> start -> (callbacks) -> stop -> close.
// start() allocates the delivery buffer before launching either worker; allocation failure
// is synchronous and produces no on_end. Success follows complete 8+8 fleet submission. stop()
// cancels in-flight transfers, drains and joins; it is idempotent and concurrent stop/close
// callers wait for the elected stopper. Calling stop/close from a library callback is forbidden
// and fails/leaks safely rather than self-joining. close performs stop if needed.
int  cc_open (cc_session **out, const cc_config *cfg, const cc_callbacks *cb);
int  cc_start(cc_session *s);
int  cc_stop (cc_session *s);
void cc_close(cc_session *s);
// Completed on_packet deliveries, both endpoints, including zero-length packets.
// One race-free atomic load during streaming; unlike cc_get_stats. Updated by the
// delivery thread only, after the callback returns, never in the libusb hot path.
uint64_t cc_packets_delivered(const cc_session *s);
const char *cc_strerror(int err);

typedef struct {
    uint64_t bytes[2];              // [0]=video [1]=audio payload delivered
    uint64_t lost_bytes[2];         // explicit ring-overflow loss: CUMULATIVE (confessed + still pending)
    uint64_t lost_packets[2];
    long iso_errors, transfer_errors, resubmit_failures, resubmit_recovered;
    long zero_len_packets, short_packets;
    size_t ring_high_water, ring_size;
    int fleet[2], fleet_size;       // live transfers per endpoint / configured
    long transfers_allocated, transfers_freed;   // device backend: equal after cc_stop (leak invariant)
    long control_records_dropped;   // HostLoss/TransferError/TICK/SESSION records that found no ring space (reserve exhausted)
    long control_loss_markers;      // terminal 0xFFFE marker emitted (0 or 1 per session)
    int  teardown_incomplete;       // libusb never proved quiescence at stop: cc_close leaks the session deliberately
    long replay_corrupt_spans;      // replay: unparseable stretches of the file skipped to the next valid record
    uint64_t replay_corrupt_bytes;  //   (each also reported through diag_log / stderr with its file offset)
} cc_stats;
// Snapshot of plain backend-thread counters: authoritative after cc_stop; a live call during
// streaming is a racy diagnostic read (values may be momentarily inconsistent), never corrupting.
void cc_get_stats(const cc_session *s, cc_stats *out);

// Convenience sink: a callback set that writes the tagged .tpc format
// (capture_tagged_bench-compatible: DATA/HostLoss/TransferError/SESSION/TICK records).
// Chain: pass its callbacks to cc_open, or call from your own callbacks.
typedef struct cc_tagged_sink cc_tagged_sink;
int  cc_tagged_sink_open (cc_tagged_sink **out, const char *path, const char *session_note);
void cc_tagged_sink_callbacks(cc_tagged_sink *k, cc_callbacks *out); // fills `out`
int  cc_tagged_sink_close(cc_tagged_sink *k);   // returns CC_ERR_IO on any failed write

// Buffered sink (tee): the same .tpc records, but the callbacks only copy into a bounded byte
// ring and a writer thread does the I/O, in writes of at most write_chunk bytes. A stalled or
// slow destination (a network/cloud volume) never blocks the caller: when the ring cannot take a
// DATA record the packet is dropped and counted, and one HostLoss record per endpoint (exact
// packets/bytes, split at 32 bits) is written before that endpoint's next DATA record, so the
// file says precisely what it lacks. Control records that do not fit are counted. A write
// failure is sticky: later records are discarded and counted, and close reports CC_ERR_IO.
// The destination is created exclusively (never replaces a file). Single producer: calls into
// the callbacks must not race each other (the capture delivery thread is the only producer).
typedef struct cc_async_sink cc_async_sink;
typedef struct {
    uint64_t records, bytes_written;     // records accepted into the ring; bytes the writer wrote
    uint64_t lost_packets[2], lost_bytes[2];  // [0]=video [1]=audio DATA dropped by this sink
    uint64_t control_dropped;            // loss/error/tick records that found no room
    uint64_t discarded_after_error;      // bytes the writer drained without writing after a failure
    size_t high_water, max_write;        // ring occupancy peak; largest single write issued
    int io_error;                        // errno of the first failed write/fsync/close, 0 if none
} cc_async_sink_stats;
int  cc_async_sink_open (cc_async_sink **out, const char *path, const char *session_note,
                         size_t ring_bytes, size_t write_chunk);
void cc_async_sink_callbacks(cc_async_sink *k, cc_callbacks *out); // packet/loss/error/tick
// Drains everything accepted, joins the writer, fsyncs and closes; fills *st (may be NULL).
int  cc_async_sink_close(cc_async_sink *k, cc_async_sink_stats *st);
// Test hook: when set, the writer's write() goes through it (stall / short-write / failure).
extern ssize_t (*cc_async_sink_test_write)(int fd, const void *buf, size_t n);

#ifdef __cplusplus
}
#endif
#endif
