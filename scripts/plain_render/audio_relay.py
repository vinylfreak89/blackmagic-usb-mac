#!/usr/bin/env python3
"""audio_relay.py D AUDIO_FIFO -- the render's audio, streamed to ffmpeg while the replay runs: the device's samples as
delivered, against the video timeline relay.py builds on the audio clock (D/a0.json, published by relay.py at its first frame).
Placement (as mux.py's was): the first block goes where its audio-clock time falls against a0, trimmed (across as many
blocks as that takes) or led by silence, and every later block follows the previous one with no gap: the device's samples
are continuous unless the transport lost some. Silence is inserted only across a transport hole: a block flagged
DISCONTINUITY_BEFORE and HOLE_BEFORE ends the run, the next anchored block's time says how many samples are missing, and
the unanchored blocks before it are held and written after the silence. Other discontinuities (unframed data, an epoch
change) are counted and the audio stays contiguous. (mux.py judged this by the whole replay's hole count, so in a file with
any hole every discontinuity was treated as one; the hole flag judges each break by its own cause.)
Reads D/timing.csv (its A lines) and D/a.s24 as the replay writes them, waiting (kqueue) on the file it needs to grow and on
D itself, whose change wakes it the moment a0.json or replay.done appears; a 1 s ceiling only covers a missed event. The
replay's exit (D/replay.done) ends the stream. Writes D/audio.json: samples
written, silence inserted (counter, samples), discontinuities, re-anchors earlier than the audio. Exit 3 if the audio ends
before the first frame or the replay ended without the files the log promised."""
import json, os, select, sys
D, FIFO = sys.argv[1], sys.argv[2]
DISC, UNANCHORED, HOLE = 1, 4, 32
logp, pcmp, a0p, donep = (os.path.join(D, n) for n in ('timing.csv', 'a.s24', 'a0.json', 'replay.done'))
kq = select.kqueue(); dir_fd = os.open(D, os.O_RDONLY)

def wait_for(file_fd=None):
    """until the file grows, or a file appears in D (a0.json, replay.done, the dumps), or 1 s passes (a ceiling for a missed event)"""
    evs = [select.kevent(fd, filter=select.KQ_FILTER_VNODE, flags=select.KQ_EV_ADD | select.KQ_EV_CLEAR | select.KQ_EV_ONESHOT,
                         fflags=select.KQ_NOTE_WRITE | select.KQ_NOTE_EXTEND) for fd in (file_fd, dir_fd) if fd is not None]
    kq.control(evs, 1, 1.0)

def fail(m):
    print('audio_relay: FAILED: ' + m, file=sys.stderr); sys.exit(3)

out = open(FIFO, 'wb')          # first: ffmpeg's open of this input waits for a writer, and the video must not wait on it
while not os.path.exists(a0p):  # the video timeline's origin, set by relay.py at the first frame it places
    if os.path.exists(donep) and not os.path.exists(a0p): fail('the replay ended before any frame was placed')
    wait_for()
a0 = json.load(open(a0p))['a0_ticks']

log = None; partial = b''; pcm = None
def a_lines():
    """the A lines of the timing log, as the replay writes them; ends after the replay exits and the log is read"""
    global log, partial
    while True:
        if log is None and os.path.exists(logp): log = open(logp, 'rb')
        data = log.read() if log else b''
        if data:
            lines = (partial + data).split(b'\n'); partial = lines.pop()
            for ln in lines:
                if ln.startswith(b'A,'): yield [int(x) for x in ln.split(b',')[1:8]]
            continue
        if os.path.exists(donep):
            data = log.read() if log else b''
            if not data:
                if partial.startswith(b'A,'): yield [int(x) for x in partial.split(b',')[1:8]]
                return
            partial += data; continue
        wait_for(log.fileno() if log else None)

def samples(n):
    """the next n samples of the PCM dump, waiting for the replay to write them"""
    global pcm
    want = n * 6; got = bytearray()
    while len(got) < want:
        if pcm is None and os.path.exists(pcmp): pcm = open(pcmp, 'rb')
        b = pcm.read(want - len(got)) if pcm else b''
        if b: got += b; continue
        if os.path.exists(donep):
            b = pcm.read(want - len(got)) if pcm else b''
            if not b: fail('the PCM dump ended %d bytes short of its log' % (want - len(got)))
            got += b; continue
        wait_for(pcm.fileno() if pcm else None)
    return bytes(got)

pos = 0; ins = []; discs = 0; holes = 0; overlaps = []; held = []; waiting = False; skip = 0
def put(data):
    global pos
    out.write(data); pos += len(data) // 6
for k, (ordinal, pnum, pden, n, flags, ctr, res) in enumerate(a_lines()):
    if pden != 240000: fail('unexpected audio timebase %d' % pden)
    data = samples(n)
    if k == 0:
        at = round((pnum - a0) / 5)                 # 5 ticks per sample
        if at > 0: put(b'\0' * (at * 6))
        else: skip = -at                            # audio from before the first frame: dropped, across as many blocks as it spans
    if skip:
        d = min(skip, len(data) // 6); data = data[d * 6:]; skip -= d
        if not data: continue
    if k == 0: put(data); continue
    if flags & DISC:
        discs += 1
        if flags & HOLE: holes += 1; waiting = True
    if waiting:
        if flags & UNANCHORED: held.append(data); continue
        at = round((pnum - a0) / 5); before = pos + sum(len(h) // 6 for h in held)
        if at > before: put(b'\0' * ((at - before) * 6)); ins.append((ctr, at - before))
        elif at < before: overlaps.append((ctr, before - at))
        for h in held: put(h)
        held = []; waiting = False
    put(data)
for h in held: put(h)
out.close()
if skip: fail('the audio ended %d samples before the first frame' % skip)
json.dump(dict(samples=pos, discontinuities=discs, holes=holes, silence_inserted=ins, reanchors_earlier=overlaps), open(os.path.join(D, 'audio.json'), 'w'))
print('audio_relay: %d samples (%.2f s); %d audio discontinuities, %d at transport holes; silence inserted at holes (counter, samples): %s; '
      're-anchors earlier than the audio (counter, samples, left contiguous): %s' % (pos, pos / 48000, discs, holes, ins, overlaps), file=sys.stderr)
