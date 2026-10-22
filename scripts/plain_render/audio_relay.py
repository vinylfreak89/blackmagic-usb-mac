#!/usr/bin/env python3
"""audio_relay.py D AUDIO_FIFO -- the render's audio, streamed to ffmpeg while the replay runs: the device's samples as
delivered, against the video timeline relay.py builds on the audio clock (D/a0.json, published by relay.py at its first frame).
Placement (as mux.py's was): the first block goes where its audio-clock time falls against a0, trimmed (across as many
blocks as that takes) or led by silence, and every later block follows the previous one with no gap: the device's samples
are continuous unless a break says otherwise. At every break (DISCONTINUITY_BEFORE: a transport hole, unframed data or an
epoch change alike) the audio goes where the next anchored block's time puts it, because relay.py places the video by that
same anchor: silence fills the gap when the anchor is later than the samples so far, and when it is earlier the audio stays
contiguous and the overlap is recorded. The unanchored blocks between are held and written after the silence.
That holds only for an anchor that can be trusted. A resync counter that is not running at the video rate (the Shuttle's
other-format modes step it ~50-70 times a second; 2026-10-21 such anchors put ~41 s of silence into continuous audio) gives
an anchor whose time is wrong. So the anchored block and the next few are read before deciding: the anchor is trusted only
when every complete resync interval among them holds TRUST_LO..TRUST_HI samples (1601.6 at 48 kHz, 29.97 fps) and the
counter steps by exactly one. An untrusted break keeps the audio contiguous and is recorded by name (counter, implied gap).
(mux.py filled every break only if the replay had a hole anywhere, and never otherwise.)
Reads D/timing.csv (its A lines) and D/a.s24 as the replay writes them, waiting (kqueue) on the file it needs to grow and on
D itself, whose change wakes it the moment a0.json or replay.done appears; a 1 s ceiling only covers a missed event. The
replay's exit (D/replay.done) ends the stream. Writes D/audio.json: samples
written, silence inserted (counter, samples), discontinuities, re-anchors earlier than the audio. Exit 3 if the audio ends
before the first frame or the replay ended without the files the log promised."""
import json, os, select, sys
D, FIFO = sys.argv[1], sys.argv[2]
DISC, UNANCHORED, COUNTER_GAP = 1, 4, 8
TRUST_LO, TRUST_HI, TRUST_INTERVALS = 1594, 1609, 3         # samples per resync interval; intervals needed after the anchor
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

pos = 0; ins = []; discs = 0; overlaps = []; untrusted = []; skip = 0
def put(data):
    global pos
    out.write(data); pos += len(data) // 6

def trusted(blocks):
    """the anchor (blocks[0]) is trusted: the resync intervals that start at it and after it, as far as the blocks reach
    complete ones, hold TRUST_LO..TRUST_HI samples each, the counter steps by one, and TRUST_INTERVALS of them are seen"""
    groups = []                                     # [counter, samples] per resync, in order
    for b in blocks:
        if b['flags'] & COUNTER_GAP and groups: return False
        if groups and b['ctr'] == groups[-1][0]: groups[-1][1] += b['n']
        elif groups and b['ctr'] != groups[-1][0] + 1: return False
        else: groups.append([b['ctr'], b['n']])
    complete = groups[:-1]                          # the last interval may still be growing
    return len(complete) >= TRUST_INTERVALS and all(TRUST_LO <= n <= TRUST_HI for _, n in complete)

def settle(held, look):
    """a break's held unanchored blocks, then its anchored block and lookahead: placed by the anchor if it is trusted"""
    if look:
        a = look[0]; at = round((a['pnum'] - a0) / 5); before = pos + sum(len(h['data']) // 6 for h in held)
        if not trusted(look): untrusted.append((a['ctr'], at - before))
        elif at > before: put(b'\0' * ((at - before) * 6)); ins.append((a['ctr'], at - before))
        elif at < before: overlaps.append((a['ctr'], before - at))
    for b in held + look: put(b['data'])

held = None; look = None                            # a break in progress: unanchored blocks, then anchored ones
reader_closed = False
try:
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
        b = dict(pnum=pnum, n=len(data) // 6, flags=flags, ctr=ctr, data=data)
        if flags & DISC:
            discs += 1
            if held is not None: settle(held, look)     # the previous break, settled with what it had
            held, look = [], []
        if held is None: put(data); continue
        if not look and flags & UNANCHORED: held.append(b); continue
        look.append(b)
        if len(look) >= TRUST_INTERVALS + 1: settle(held, look); held = look = None
    if held is not None: settle(held, look)
except BrokenPipeError:
    # ffmpeg stops reading at the end of the shorter stream (-shortest): the video ended first and the rest of the audio
    # has nowhere to go. That is the end of the render's audio, not a failure; ffmpeg's own exit says whether it was well.
    reader_closed = True
    os.dup2(os.open(os.devnull, os.O_WRONLY), out.fileno())          # the buffered tail goes nowhere instead of erroring at exit
out.close()
if skip: fail('the audio ended %d samples before the first frame' % skip)
json.dump(dict(samples=pos, discontinuities=discs, silence_inserted=ins, reanchors_earlier=overlaps, untrusted_breaks=untrusted,
               ended_by_reader=reader_closed), open(os.path.join(D, 'audio.json'), 'w'))
print('audio_relay: %d samples (%.2f s)%s; %d audio breaks; silence inserted (counter, samples): %s; re-anchors earlier than the audio '
      '(counter, samples, left contiguous): %s; untrusted anchors (counter, implied samples, left contiguous): %s' % (pos, pos / 48000,
      ', the rest not taken by ffmpeg (the video ended first)' if reader_closed else '', discs, ins, overlaps, untrusted), file=sys.stderr)
