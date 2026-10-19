#!/usr/bin/env python3
"""relay.py VIDEO_FIFO LOG_FILE -- streams the replay's frames to ffmpeg (stdout), in counter order, inserting a flat
no-signal fill for any counter the replay did not publish. Frames are matched to the V lines of the growing timing
log; frames read ahead of the log wait in a short queue (the log is buffered by the writer)."""
import os, sys, time
FR=720*480*2; fill=bytes([200,41,110,41])*(720*480//2)
vf=open(sys.argv[1],"rb",buffering=0); logp=sys.argv[2]; out=sys.stdout.buffer
log=None; partial=b""; counters=[]; queue=[]; expect=None; fills=[]; eof=False
def poll_log():
    global log, partial
    if log is None:
        if not os.path.exists(logp): return
        log=open(logp,"rb")
    data=log.read()
    if not data: return
    lines=(partial+data).split(b"\n"); partial=lines.pop()
    for ln in lines:
        if ln.startswith(b"V,"): counters.append(int(ln.split(b",")[1]))
def emit():
    global expect
    while queue and counters:
        c=counters.pop(0); frame=queue.pop(0)
        if expect is not None:
            while expect<c: out.write(fill); fills.append(expect); expect+=1
        out.write(frame); expect=c+1
while True:
    if not eof:
        buf=bytearray()
        while len(buf)<FR:
            b=vf.read(FR-len(buf))
            if not b: eof=True; break
            buf+=b
        if len(buf)==FR: queue.append(bytes(buf))
    poll_log(); emit()
    if eof:
        if not queue: break
        time.sleep(0.2)       # the replay is flushing its last log lines
out.flush()
print(f"relay: filled {len(fills)} frames at counters {fills[:20]}", file=sys.stderr)
