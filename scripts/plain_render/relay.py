#!/usr/bin/env python3
"""relay.py VIDEO_FIFO LOG_FILE [LOST_COUNTERS|none] -- streams the replay's frames to ffmpeg (stdout) on the AUDIO clock. Output slot s covers
[a0 + s*8008, a0 + (s+1)*8008) ticks of 1/240000 s (one NTSC frame, 1001/30000 s), a0 being the first frame's audio time.
Each published frame is placed by its unit's audio-clock time (the V line's audio_pts_num), never by its counter: a unit
counter is not time (in the Shuttle's other-format modes it steps ~50-70 times a second, 2026-10-21), the audio clock is.
A slot gets the frame nearest its start; a frame whose slot holds a nearer one is dropped. A frame continues the slot sequence
of the frame before it (that slot plus the units between them) unless that puts it more than 3/4 of a slot from its own
time, where it takes its nearest slot: after a field-framed unit every later frame can sit half a slot off the grid, and
nearest-slot rounding then flipped with a few ticks of jitter, dropping one frame and leaving two slots to the no-signal
fill, a blue flash at a wrong-length unit (2026-11-19, 12 in one render). A single empty slot between two
frames repeats the frame before it (counted as held), as a TBC would: a deck in search or unlocked sends each field as a
~257-line unit followed by a 5-line stub that is not picture, and a fill there flashes every other frame (2026-10-21, owner's
choice). Never across lost data: LOST_COUNTERS lists the 16-bit counters of units the host lost (from the capture's sidecar);
a gap that spans one keeps its fill, counted. 'none' (no sidecar to say) turns holds off. Two or more empty slots in a row get
a flat no-signal fill, so real dropouts stay visible, with one exception: the Shuttle losing lock. When the tape's sync
breaks for a moment (an edit, 2026-11-19: 0.13-0.30 s at four places in one capture) the Shuttle declares no input and sends
its own no-signal units (format 0x0800) between cut-off picture units; nothing of the tape is in them. A gap of at most
LOCK_LOSS_MAX slots whose units, as the replay's U lines name them, are only such units (at least one no-signal unit, the
rest short, unframed or of another format), with nothing the host lost (no hole, no ring or pool loss, no sidecar-listed
loss), repeats the frame before it, as a frame synchroniser would (owner's choice, 2026-11-19; counted as held_lock_loss).
Anything else in the gap, or a longer one, keeps its fill. A frame without an audio time (audio_pts_known 0) is placed one counter step after the previous frame
(counted as estimated). Frames are matched to the V lines of the growing timing log; frames read ahead of the log wait in
a short queue (the log is buffered by the writer).
plain_render.sh creates replay.done beside the log once the replay has exited: frames still unmatched after the log's last
lines are then an error (exit 3), never an endless wait (2026-10-20: a replay that died mid-stream left this waiting 10 h).
Writes schedule.json beside the log: a0 (ticks), slots written, frames placed/dropped/estimated, fill slots (and fill_runs: each run of fill as [first slot, slots], also printed with its time), and the largest
distance between a placed frame's audio time and its slot start. As soon as the first frame is placed, a0.json beside the log
holds a0, so audio_relay.py can place the audio against the same timeline while the render runs."""
import os, sys, time, json
FR = 720 * 480 * 2; fill = bytes([200, 41, 110, 41]) * (720 * 480 // 2); SLOT = 8008
vf = open(sys.argv[1], "rb", buffering=0); logp = sys.argv[2]; out = sys.stdout.buffer
lostarg = sys.argv[3] if len(sys.argv) > 3 else "none"; holds_on = lostarg != "none"
lost = sorted({int(x) % 65536 for x in open(lostarg).read().split()}) if holds_on else []
log = None; partial = b""; vlines = []; queue = []; eof = False
LOCK_LOSS_MAX = 15   # slots (0.5 s): a lock loss held; the longest measured was 9 (2026-11-19); a stopped deck or tape end is far longer
units = []           # U lines not yet behind the last frame written: (log line number, counter, format, kind, transport, host lost)
lineno = 0
a0 = None; prev = None; nxt = 0; pending = None
SNAP = 0.75     # slots: a frame further than this from its sequence slot takes its nearest slot instead (inclusive)
seq = None      # (slot, ticks) of the last frame given a slot
st = dict(snapped=0, placed=0, dropped=0, estimated=0, filled=0, held=0, not_held_lost=0, held_lock_loss=0, max_dev_ticks=0, holds_on=holds_on); last = None
fill_runs = []   # [first slot, slots] of every run of no-signal fill, in output order
lock_runs = []   # [first slot, slots] of every run held across the Shuttle's lock loss
def lost_between(c1, c2):
    """a lost unit's 16-bit counter lies strictly between frame counters c1 < c2"""
    span = (c2 - c1) % 65536
    return any(0 < (c - c1) % 65536 < span for c in lost)
def lock_loss(n1, c1, n2, c2):
    """whether the units between the frame of counter c1 (log line n1) and that of c2 (n2) are only the Shuttle's lock loss:
    at least one no-signal unit (kind 1), the others short, unframed or of another format, and nothing the host lost"""
    span = (c2 - c1) % 65536
    between = [u for u in units if (n1 < u[0] < n2 and u[1] % 65536 not in (c1 % 65536, c2 % 65536)) or (u[0] > n1 and 0 < (u[1] - c1) % 65536 < span)]
    if any(u[5] or u[3] < 0 or u[4] == 1 for u in between): return False          # host loss, ring loss or a hole
    if any(u[3] == 0 and u[4] == 0 for u in between): return False                # a whole picture unit not shown
    return any(u[3] == 1 for u in between) and not lost_between(c1, c2)
def poll_log():
    global log, partial
    if log is None:
        if not os.path.exists(logp): return
        log = open(logp, "rb")
    data = log.read()
    if not data: return
    lines = (partial + data).split(b"\n"); partial = lines.pop()
    global lineno
    for ln in lines:
        lineno += 1
        if ln.startswith(b"V,"): vlines.append([int(x) for x in ln.split(b",")[1:9]] + [lineno])
        elif ln.startswith(b"U,"): units.append((lineno,) + tuple(int(x) for x in ln.split(b",")[1:6]))
def audio_time(v):
    """ticks on the audio clock for V line v = counter, pts_num, pts_den, d1, d2, transport, audio_pts_known, audio_pts_num"""
    global prev
    if v[6]: t = v[7]
    elif prev is None: t = v[1] * 240000 // v[2]; st["estimated"] += 1
    else: t = prev[1] + (v[0] - prev[0]) * SLOT; st["estimated"] += 1
    prev = (v[0], t); return t
def emit(slot, frame, counter, n):
    global nxt, last, units
    if slot - nxt == 1 and last is not None and holds_on:
        if lost_between(last[1], counter): st["not_held_lost"] += 1
        else: out.write(last[0]); st["held"] += 1; nxt += 1
    elif 2 <= slot - nxt <= LOCK_LOSS_MAX and last is not None and holds_on and lock_loss(last[2], last[1], n, counter):
        lock_runs.append([nxt, slot - nxt])
        while nxt < slot: out.write(last[0]); st["held_lock_loss"] += 1; nxt += 1
    if nxt < slot:
        if fill_runs and fill_runs[-1][0] + fill_runs[-1][1] == nxt: fill_runs[-1][1] += slot - nxt
        else: fill_runs.append([nxt, slot - nxt])
    while nxt < slot: out.write(fill); st["filled"] += 1; nxt += 1
    out.write(frame); nxt += 1; last = (frame, counter, n)
    units = [u for u in units if u[0] > n]
def place():
    global a0, pending, seq
    while queue and vlines:
        v = vlines.pop(0); frame = queue.pop(0); t = audio_time(v)
        if a0 is None:
            a0 = t; p = os.path.join(os.path.dirname(logp) or ".", "a0.json")
            json.dump(dict(a0_ticks=a0), open(p + ".new", "w")); os.replace(p + ".new", p)   # published whole, never half-written
        x = (t - a0) / SLOT; s = round(x)
        if seq is not None:
            k = seq[0] + round((t - seq[1]) / SLOT)
            if abs(k - x) <= SNAP: s = k
            else: st["snapped"] += 1
        s = max(0, s); seq = (s, t); dev = abs(t - (a0 + s * SLOT))
        if pending is None or s > pending[0]:
            if pending is not None: emit(pending[0], pending[1], pending[3], pending[4]); st["placed"] += 1; st["max_dev_ticks"] = max(st["max_dev_ticks"], pending[2])
            if s < nxt: st["dropped"] += 1; pending = None; continue      # the slot was already written
            pending = (s, frame, dev, v[0], v[8])
        elif s == pending[0]:
            st["dropped"] += 1
            if dev < pending[2]: pending = (s, frame, dev, v[0], v[8])
        else: st["dropped"] += 1                                         # earlier than the held slot: never written back
while True:
    if not eof:
        buf = bytearray()
        while len(buf) < FR:
            b = vf.read(FR - len(buf))
            if not b: eof = True; break
            buf += b
        if len(buf) == FR: queue.append(bytes(buf))
    poll_log(); place()
    if eof:
        if not queue: break
        if os.path.exists(os.path.join(os.path.dirname(logp) or ".", "replay.done")):
            poll_log(); place()
            if queue:
                print(f"relay: FAILED: the replay exited with {len(queue)} frames it never logged", file=sys.stderr); sys.exit(3)
            break
        time.sleep(0.2)       # the replay is flushing its last log lines
if pending is not None: emit(pending[0], pending[1], pending[3], pending[4]); st["placed"] += 1; st["max_dev_ticks"] = max(st["max_dev_ticks"], pending[2])
out.flush()
st.update(a0_ticks=a0, slots=nxt, fill_runs=fill_runs, lock_runs=lock_runs)
json.dump(st, open(os.path.join(os.path.dirname(logp) or ".", "schedule.json"), "w"))
print("relay: %d slots on the audio clock: %d frames placed, %d dropped (another frame was nearer the slot), %d estimated (no audio time), "
      "%d held (one empty slot: previous frame repeated%s), %d not held (lost data in the gap), %d held across the Shuttle's lock loss, %d filled; %d re-placed off the sequence "
      "(more than 3/4 slot from it); largest placement error %.2f ms" % (
      nxt, st["placed"], st["dropped"], st["estimated"], st["held"], "" if holds_on else "; OFF: no sidecar lists lost units", st["not_held_lost"], st["held_lock_loss"], st["filled"],
      st["snapped"], st["max_dev_ticks"] / 240), file=sys.stderr)
def at(slot): t = slot * 1001 / 30000; return "%d:%05.2f" % (t // 60, t % 60)
for s0, n in lock_runs:
    print("relay: held across the Shuttle's lock loss at %s for %d slot%s (%d frames, %.2f s)" % (at(s0), n, "" if n == 1 else "s", 2 * n, n * 1001 / 30000), file=sys.stderr)
for s0, n in fill_runs:     # each slot is two frames of the 59.94 fps render
    print("relay: no-signal fill at %s for %d slot%s (%d frames, %.2f s)" % (at(s0), n, "" if n == 1 else "s", 2 * n, n * 1001 / 30000), file=sys.stderr)
