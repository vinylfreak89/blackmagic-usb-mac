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
enum cc_loss_kind { CC_LOSS_RING = 0,         /* delivery-ring overflow: packets that crossed the bus, then shed */
                    CC_LOSS_UNSCHEDULED = 1,   /* USB slots never read (.tpc HostLoss pkt_index CC_PI_UNSCHEDULED) */
                    CC_LOSS_UNSCHEDULED_LATE = 2, /* the same, found after the affected data went by (CC_PI_UNSCHEDULED_LATE) */
                    CC_LOSS_UNCLOSED = 3,      /* the capture ended without closing (CC_PI_UNCLOSED, replayed) */
                    CC_LOSS_HOLE = 4 };        /* bytes missing there, packets unknown (CC_PI_HOLE, replayed; bytes in the call) */
enum cc_error_kind { CC_ERROR_TRANSFER = 0, CC_ERROR_SUBMIT = 1,
                     CC_ERROR_CONTROL_LOSS = 2 };

#define CC_DEFAULT_READAHEAD_MB 256  /* replay read-ahead when replay_readahead_mb is 0: ~11 s of stream */
/* HostLoss records whose pkt_index is CC_PI_UNSCHEDULED report USB slots that were never read: macOS moved a late
 * resubmission past them, so no transfer, error or sequence gap records the loss. req_len = packets, from libusb's
 * own scheduling rule mirrored at submit (an estimate: the host clock stands in for the bus frame), actual_len = 0
 * (bytes unknown), submit_seq = the transfer the gap precedes; the record comes just before that transfer's data. */
#define CC_PI_UNSCHEDULED 0xFFFDu
/* The same loss found only after the data it precedes was delivered: after a failed submit, whether libusb advanced
 * its queue end (unread slots) or the event thread was merely held up cannot be told from one completion, so the
 * next ones decide, and by then the transfer the gap precedes has gone by. submit_seq still names that transfer; the
 * record itself arrives later in the stream, so a reader locates the gap by seq, never by the record's position
 * (the unit parser does not flag the unit in progress for it). */
#define CC_PI_UNSCHEDULED_LATE 0xFFFCu
/* The last record of a capture whose writer ended without closing, written by cc_spill_recover after the spilled
 * records it recovered: whatever was still in memory then is lost, amount unknown (packets/bytes 0 = unknown). */
#define CC_PI_UNCLOSED 0xFFFAu
#define CC_XFERS_PER_ENDPOINT 32  /* isochronous transfers kept queued per endpoint (video: 32 x 16 ms = 512 ms ahead) */
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
    // Optional; when set it is called INSTEAD of on_loss, for the same events, with their enum cc_loss_kind and, for
    // CC_LOSS_UNSCHEDULED, the submit_seq of the transfer the gap precedes (it arrives just before that transfer's
    // packets). Sinks use it to write the record back as captured.
    void (*on_loss_ex)(void *ctx, uint8_t endpoint, uint32_t packets, uint64_t bytes, int kind, uint32_t seq);
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
    uint64_t replay_start_offset; // replay: begin at this byte offset of the file (0 = its start). The replay walks
                                // forward to the first record that begins a whole video transfer (pkt_index 0)
                                // and delivers from there; the bytes before it are counted in replay_align_bytes,
                                // not reported as corruption. Records are self-describing, so any offset works.
    // setup_off clears the 7.5 IRE setup bit, applied once at start-up (the Shuttle ignores it mid-stream): ON (the
    // default, every capture before) maps NTSC-M's 7.5 IRE black to code 16; OFF maps 0 IRE there (black lifted
    // ~16 codes), NTSC-J. The Shuttle has no input gain controls (owner, 2026-10-07): register 4 is written as the
    // driver writes it, 80 80 80 00, never as a user setting. The session note records the mode word.
    int setup_off;
    // replay_block_when_full: replay only (cc_open refuses it for a device). When the delivery ring is full the replay
    // WAITS for the consumer instead of recording host loss, so an offline render whose consumer is slow (a busy CPU, a
    // network volume) runs slower and never loses data. A real device cannot wait: there the ring overflow stays HostLoss.
    int replay_block_when_full;
} cc_config;

// Lifecycle: open -> start -> (callbacks) -> stop -> close.
// start() allocates the delivery buffer before launching either worker; allocation failure
// is synchronous and produces no on_end. Success follows complete fleet submission (CC_XFERS_PER_ENDPOINT per endpoint). stop()
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
// Bytes of tagged records waiting in the delivery ring now (one race-free pair of atomic loads; diagnostic): data the
// backend has handed over that the delivery thread has not yet passed to the callbacks.
size_t cc_ring_pending(const cc_session *s);
// Replay only: hold delivery (paused != 0) or resume it. The pacer stops at the next video-transfer
// boundary, after that transfer is delivered, and waits for resume or stop; on resume its deadlines
// restart from the resume time, so no burst follows. The read-ahead keeps filling while paused.
// CC_ERR_STATE for a device session (a live capture cannot be held; the device keeps streaming).
int cc_replay_pause(cc_session *s, int paused);
const char *cc_strerror(int err);
// The mode word the device start-up sent (it carries the input select and the setup bit). Replay sessions return -1.
int cc_start_info(const cc_session *s, uint32_t *mode_word);
// The mode word cc_open sends for this configuration (input select and setup bit): the one place it is computed.
uint32_t cc_mode_word(const cc_config *cfg);

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
    uint64_t replay_align_bytes;    // replay_start_offset > 0: bytes walked past to reach the first whole video transfer
    uint64_t replay_space_waits;    // replay_block_when_full: times the replay waited for the consumer (never data lost)
    uint64_t unscheduled_events;    // device: gaps of never-read USB slots found (see CC_PI_UNSCHEDULED), all endpoints; one record can carry two
    uint64_t unscheduled_late;      // of those, found only after their data went by (CC_PI_UNSCHEDULED_LATE records)
    uint64_t unclosed_marks;        // replay: CC_PI_UNCLOSED records met (the capture ended without closing there)
    uint64_t hole_marks, hole_bytes; // replay: CC_PI_HOLE records met, and the bytes they say are missing
    uint64_t unscheduled_packets[2];// [0]=video [1]=audio: slots never read (libusb's Darwin scheduling rule, +-1 frame)
    int rt_event_thread;            // device: 1 if the USB event thread got real-time scheduling at start
    int rt_libusb_threads;          // device: libusb-internal threads promoted (expected 1: org.libusb.device-hotplug)
    int rt_event_at_stop;           // device: 1 if the event thread's real-time policy reads back at the end (can survive a demotion)
    int rt_priority_at_stop;        // device: the event thread's scheduled priority at the end (real-time queues >= 97; -1 unknown)
    int rt_priority_min;            // device: its lowest, sampled once a second and at the end: under 97 = it lost real time at some point
    uint64_t schedule_shifts, schedule_shift_frames; // device: completions persistently later than the model (it missed a gap); not placed
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
// The ring is mapped memory whose pages are handed back to the system as the writer drains them, so its cost is
// the backlog, not its size; this needs a ring that is a whole number of pages (otherwise it keeps its memory). The
// producer then takes a zero-fill fault on its first copy into each page. Free space is published in steps of up to
// 1 MiB, so the producer may see that much less than is free. Close drains the whole backlog before it returns.
// The destination is created exclusively (never replaces a file). Single producer: calls into
// the callbacks must not race each other (the capture delivery thread is the only producer).
typedef struct cc_async_sink cc_async_sink;
typedef struct {
    uint64_t records, bytes_written;     // records accepted into the ring; bytes the writer wrote
    uint64_t lost_packets[2], lost_bytes[2];  // [0]=video [1]=audio DATA dropped by this sink
    uint64_t control_dropped;            // loss/error/tick records that found no room
    uint64_t discarded_after_error;      // bytes the writer drained without writing after a failure
    size_t high_water, max_write;        // ring occupancy peak (against the exact drain position); largest single write issued
    int io_error;                        // errno of the first failed write/fsync/close, 0 if none
    // Why the writer fell behind, when it did. A write call that blocks shows in the write times. A writer that was
    // not running shows in max_ready_gap_ns if it stopped between two writes, and in max_wake_backlog (the bytes it
    // found waiting when it came back from its idle wait; divide by the stream rate for the time away) if it
    // stopped while idle, which is where a writer that keeps up spends its time. max_wake_backlog has a floor: a
    // burst handed over while the writer wakes reads as its size (about 1.3 MB for 128 packets). A writer stopped
    // between seeing data and starting its write shows in neither. Each run of dropped packets is one
    // episode, and at its first dropped packet the writer was either inside a write call (for how long) or not.
    uint64_t writes, write_ns, max_write_ns, slow_writes;   // slow: a write call longer than 100 ms
    uint64_t max_ready_gap_ns;           // longest time from one write returning to the next starting, data waiting
    uint64_t loss_episodes, loss_in_write, max_in_write_at_loss_ns;
    uint64_t max_wake_backlog;           // bytes
    // Ring memory handed back to the system as it drained (see below); a refused hand-back ends the capture's
    // completeness: the sink stops freeing space, counts what it drops, and close returns CC_ERR_IO (ENOMEM).
    uint64_t released_bytes, release_failures;
    // The local spill (cc_async_sink_open_spill). spill_state: 1 on (it may still have no room: cc_async_sink_spill_room); 0 not configured, or the destination is on the
    // spill's own volume; -errno: the directory was unusable, so memory was the only buffer. spill_error: the errno
    // that turned it off mid-capture (the bytes of that write stayed in memory: nothing is lost by it).
    int spill_state, spill_error;
    uint64_t spill_bytes, spill_peak;        // bytes that went through the local disk; most on disk at once
    uint64_t spill_segments;                 // segment files created
    uint64_t spill_floor_refusals;           // times a new segment was refused because it would break the free-space floor
    uint64_t spill_max_write_ns;             // longest local spill write
    // Spilled chunks the local disk would not give back: each is replaced in the file by HostLoss records
    // (pkt_index 0xFFFB) carrying exactly the packets and bytes it held, and the capture goes on. Loss records inside
    // it fold into those counts (an unread-slot record's kind and seq are not kept); its other records count as dropped.
    uint64_t spill_read_errors, spill_read_lost_packets[2], spill_read_lost_bytes[2];
} cc_async_sink_stats;
int  cc_async_sink_open (cc_async_sink **out, const char *path, const char *session_note,
                         size_t ring_bytes, size_t write_chunk);
// A destination on another volume (a network share) can stall for seconds or minutes. With a spill, once the
// memory backlog reaches `after` bytes the oldest of it moves to segment files in `dir` on the local disk and is
// delivered from there, in order, so a stalled destination costs local disk space instead of the capture. The spill
// always leaves `floor` bytes free on its volume; beyond that memory is the only buffer and overflow is HostLoss.
// Segments are deleted as they are delivered and at close. A destination on the spill's own volume gets no spill.
typedef struct {
    const char *dir;      // local, non-synced directory (created 0700 if absent); NULL: no spill
    uint64_t floor;       // free bytes always left on the spill volume; 0: 32 GB (32e9)
    size_t after;         // memory backlog at which bytes start going to disk; 0: ring/16 within [8 MiB, 256 MiB]
    size_t segment;       // bytes per segment file; 0: 128 MiB
} cc_async_sink_spill;
int  cc_async_sink_open_spill(cc_async_sink **out, const char *path, const char *session_note,
                              size_t ring_bytes, size_t write_chunk, const cc_async_sink_spill *spill);
int  cc_async_sink_spill_state(const cc_async_sink *k);   // as cc_async_sink_stats.spill_state, from open on
// Free bytes above the floor on the spill volume at open (under one segment: the spill cannot grow now); and the
// segment files of writers that are gone (undelivered capture bytes; counted, never deleted by the sink).
int64_t cc_async_sink_spill_room(const cc_async_sink *k);
void cc_async_sink_spill_stale(const cc_async_sink *k, uint64_t *files, uint64_t *bytes);
// A writer that ended without closing (a crash) leaves its undelivered spill in the spill directory, with a
// manifest naming its destination. This puts it where it belongs: for each such writer (its manifest lock is free),
// the undelivered records are appended to the destination in order (a record cut by the crash is removed first and
// what already arrived is skipped), followed by a CC_PI_UNCLOSED HostLoss; the appended bytes are read back, and only
// then are the segments and manifest deleted. It appends in pieces of at most 1 MiB, each read back and recorded in
// the manifest, so a stop or failure resumes exactly at the next run. Anything it cannot do keeps them and is
// logged. Run it at start-up (shuttle-capture and the OBS plugin do); log(ctx, line) gets one line per writer (NULL:
// stderr); *stop (optional) is checked between pieces; *progress (optional) counts bytes appended. 0, or -EPERM for
// a spill directory that is not this user's private one. Known limit: this covers a process that died (the kernel
// kept what it wrote). A system crash or power loss is not covered: the spill directories live in /private/tmp,
// which macOS clears at restart, and the destination then simply ends where its last flushed write did, unmarked.
typedef struct { unsigned recovered, kept, failed; uint64_t bytes; } cc_spill_recover_stats;
// The on-disk form: <spill dir>/<dest name>.p<pid>.<tag>.manifest next to its segments <...>.spill<6 digits>.
// A segment is chunks, each a cc_spill_chunk_s header (its records' stream position and length) and whole records.
// next_seg/next_off is the header of the first chunk not yet delivered; delta is destination bytes minus stream
// bytes so far, so that chunk belongs at destination offset spos + delta.
#define CC_SPILL_MANIFEST_MAGIC "CCSPILL1"
#define CC_SPILL_CHUNK_MAGIC 0x43534343u   /* "CCSC" */
struct cc_spill_manifest_s { char magic[8]; uint32_t version, pid; uint64_t next_seg, next_off; int64_t delta; char dest[1024]; };
struct cc_spill_chunk_s { uint32_t magic, len; uint64_t spos; };
/* HostLoss written by recovery where bytes are missing whose packets are unknown: actual_len = bytes (a chunk the
 * crash cut short in the destination, or spilled records that cannot be read). */
#define CC_PI_HOLE 0xFFF9u
int  cc_spill_recover(const char *dir, void (*log)(void *ctx, const char *line), void *ctx, const _Atomic int *stop,
                      _Atomic uint64_t *progress, cc_spill_recover_stats *st);
extern ssize_t (*cc_spill_recover_test_write)(int fd, const void *buf, size_t n, off_t off);   /* recovery's writes */
// Bytes the writer has finished with (written + discarded): a close that drains a backlog advances it.
uint64_t cc_async_sink_progress(cc_async_sink *k);
void cc_async_sink_callbacks(cc_async_sink *k, cc_callbacks *out); // packet/loss/error/tick
// Stop accepting, drain everything accepted (memory and spill) to the destination and join the writer threads;
// the sink stays valid, so cc_async_sink_progress can be watched from another thread meanwhile. Call it from one
// thread, after the producer has stopped; close calls it if it has not run.
int  cc_async_sink_finish(cc_async_sink *k);
// Drains everything accepted, joins the writer, fsyncs and closes; fills *st (may be NULL).
int  cc_async_sink_close(cc_async_sink *k, cc_async_sink_stats *st);
// Test hook: when set, the writer's write() goes through it (stall / short-write / failure).
extern ssize_t (*cc_async_sink_test_write)(int fd, const void *buf, size_t n);
extern int (*cc_async_sink_test_fsync)(int fd);   /* test hook for the periodic flush */
extern ssize_t (*cc_async_sink_test_spill_write)(int fd, const void *buf, size_t n, off_t off);   /* spill writes */
extern uint64_t (*cc_async_sink_test_free)(const char *dir);   /* free bytes on the spill volume */
extern ssize_t (*cc_async_sink_test_spill_read)(int fd, void *buf, size_t n, off_t off);   /* spill reads */
extern int cc_async_sink_test_spill_any_volume;   /* spill even onto the destination's own volume */
extern size_t cc_async_sink_sync_every;            /* bytes between flushes (default 256 MiB); 0: only at close */
// The writer thread's QoS class (default QOS_CLASS_UTILITY); read once when the sink opens. For measurement.
extern int cc_async_sink_writer_qos;

#ifdef __cplusplus
}
#endif
#endif
