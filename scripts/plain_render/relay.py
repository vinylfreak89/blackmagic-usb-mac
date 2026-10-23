#!/usr/bin/env python3
"""relay.py VIDEO_FIFO LOG_FILE [LOST_COUNTERS|none] -- streams the replay's frames to ffmpeg (stdout) on the AUDIO clock. Output slot s covers
[a0 + s*8008, a0 + (s+1)*8008) ticks of 1/240000 s (one NTSC frame, 1001/30000 s), a0 being the first frame's audio time.
Each published frame is placed by its unit's audio-clock time (the V line's audio_pts_num), never by its counter: a unit
counter is not time (in the Shuttle's other-format modes it steps ~50-70 times a second, 2026-10-21), the audio clock is.
A slot gets the frame nearest its start; a frame whose slot holds a nearer one is dropped. A single empty slot between two
frames repeats the frame before it (counted as held), as a TBC would: a deck in search or unlocked sends each field as a
~257-line unit followed by a 5-line stub that is not picture, and a fill there flashes every other frame (2026-10-21, owner's
choice). Never across lost data: LOST_COUNTERS lists the 16-bit counters of units the host lost (from the capture's sidecar);
a gap that spans one keeps its fill, counted. 'none' (no sidecar to say) turns holds off. Two or more empty slots in a row get
a flat no-signal fill, so real dropouts stay visible. A frame without an audio time (audio_pts_known 0) is placed one counter step after the previous frame
(counted as estimated). Frames are matched to the V lines of the growing timing log; frames read ahead of the log wait in
a short queue (the log is buffered by the writer).
plain_render.sh creates replay.done beside the log once the replay has exited: frames still unmatched after the log's last
lines are then an error (exit 3), never an endless wait (2026-10-20: a replay that died mid-stream left this waiting 10 h).
Writes schedule.json beside the log: a0 (ticks), slots written, frames placed/dropped/estimated, fill slots, and the largest
distance between a placed frame's audio time and its slot start. As soon as the first frame is placed, a0.json beside the log
holds a0, so audio_relay.py can place the audio against the same timeline while the render runs."""
import os, sys, time, json
FR = 720 * 480 * 2; fill = bytes([200, 41, 110, 41]) * (720 * 480 // 2); SLOT = 8008
vf = open(sys.argv[1], "rb", buffering=0); logp = sys.argv[2]; out = sys.stdout.buffer
lostarg = sys.argv[3] if len(sys.argv) > 3 else "none"; holds_on = lostarg != "none"
lost = sorted({int(x) % 65536 for x in open(lostarg).read().split()}) if holds_on else []
log = None; partial = b""; vlines = []; queue = []; eof = False
a0 = None; prev = None; nxt = 0; pending = None
st = dict(placed=0, dropped=0, estimated=0, filled=0, held=0, not_held_lost=0, max_dev_ticks=0, holds_on=holds_on); last = None
def lost_between(c1, c2):
    """a lost unit's 16-bit counter lies strictly between frame counters c1 < c2"""
    span = (c2 - c1) % 65536
    return any(0 < (c - c1) % 65536 < span for c in lost)
def poll_log():
    global log, partial
    if log is None:
        if not os.path.exists(logp): return
        log = open(logp, "rb")
    data = log.read()
    if not data: return
    lines = (partial + data).split(b"\n"); partial = lines.pop()
    for ln in lines:
        if ln.startswith(b"V,"): vlines.append([int(x) for x in ln.split(b",")[1:9]])
def audio_time(v):
    """ticks on the audio clock for V line v = counter, pts_num, pts_den, d1, d2, transport, audio_pts_known, audio_pts_num"""
    global prev
    if v[6]: t = v[7]
    elif prev is None: t = v[1] * 240000 // v[2]; st["estimated"] += 1
    else: t = prev[1] + (v[0] - prev[0]) * SLOT; st["estimated"] += 1
    prev = (v[0], t); return t
def emit(slot, frame, counter):
    global nxt, last
    if slot - nxt == 1 and last is not None and holds_on:
        if lost_between(last[1], counter): st["not_held_lost"] += 1
        else: out.write(last[0]); st["held"] += 1; nxt += 1
    while nxt < slot: out.write(fill); st["filled"] += 1; nxt += 1
    out.write(frame); nxt += 1; last = (frame, counter)
def place():
    global a0, pending
    while queue and vlines:
        v = vlines.pop(0); frame = queue.pop(0); t = audio_time(v)
        if a0 is None:
            a0 = t; p = os.path.join(os.path.dirname(logp) or ".", "a0.json")
            json.dump(dict(a0_ticks=a0), open(p + ".new", "w")); os.replace(p + ".new", p)   # published whole, never half-written
        s = max(0, round((t - a0) / SLOT)); dev = abs(t - (a0 + s * SLOT))
        if pending is None or s > pending[0]:
            if pending is not None: emit(pending[0], pending[1], pending[3]); st["placed"] += 1; st["max_dev_ticks"] = max(st["max_dev_ticks"], pending[2])
            if s < nxt: st["dropped"] += 1; pending = None; continue      # the slot was already written
            pending = (s, frame, dev, v[0])
        elif s == pending[0]:
            st["dropped"] += 1
            if dev < pending[2]: pending = (s, frame, dev, v[0])
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
if pending is not None: emit(pending[0], pending[1], pending[3]); st["placed"] += 1; st["max_dev_ticks"] = max(st["max_dev_ticks"], pending[2])
out.flush()
st.update(a0_ticks=a0, slots=nxt)
json.dump(st, open(os.path.join(os.path.dirname(logp) or ".", "schedule.json"), "w"))
print("relay: %d slots on the audio clock: %d frames placed, %d dropped (another frame was nearer the slot), %d estimated (no audio time), "
      "%d held (one empty slot: previous frame repeated%s), %d not held (lost data in the gap), %d filled; largest placement error %.2f ms" % (
      nxt, st["placed"], st["dropped"], st["estimated"], st["held"], "" if holds_on else "; OFF: no sidecar lists lost units", st["not_held_lost"], st["filled"], st["max_dev_ticks"] / 240), file=sys.stderr)
