#!/bin/bash
# plain_render.sh CAPTURE.tpc OUT.mov [WORKDIR]
#
# The plain review render: no overlays, no registration, no H-retiming. Used for the one-play tape
# (2026-10-17 13-48-05) and for test recordings.
#
#   1. frameserver_replay --offline (waits, never drops) with FS_REGISTRATION_OFF=1 FS_HRETIME=0 dumps the
#      published 720x480 UYVY frames, the PCM and the timing log. Picture units that are not whole (a deck in search,
#      unlocked or damaged playback) are shown with the lines they carry (FS_SHOW_PARTIAL=1, as OBS's "show partial"),
#      so picture the Shuttle could not frame is not replaced by fill; PLAIN_RENDER_SHOW_PARTIAL=0 turns that off.
#   2. relay.py places frames on the AUDIO clock: each frame goes to the 1001/30000 s slot nearest its unit's
#      audio-clock time (a unit counter is not time: in the Shuttle's other-format modes it runs ~50-70 per second);
#      a slot no frame reached becomes a flat no-signal frame, and of several frames in one slot the nearest is kept
#      (the others are counted as dropped). It writes schedule.json (start time, slot count) for the mux.
#   3. ffmpeg: TFF, BT.601 limited range, yadif send_field (59.94p), crop 704x480 at x=8, SAR 10/11,
#      ProRes 422 on the VideoToolbox hardware encoder -> a hidden video-only file beside OUT.
#   4. mux.py writes the audio as the device delivered it, continuous from the first frame's audio time,
#      inserting silence only across a transport hole; checks the frame count against the relay's slots, and
#      muxes video + audio in one pass with the index reserved at the front. The video-only file is removed
#      after success.
#
# Refuses to overwrite OUT. WORKDIR (default: a fresh temp dir) holds the FIFO, PCM and timing log;
# it is removed when the render succeeds.
# CAPTURE.tpc may be a FIFO (the replay reads it as a stream). PLAIN_RENDER_DECISION_LOG=FILE also writes the replay's
# decision log (the sidecar's schema) from the same pass; it is not overwritten if it exists.
# PLAIN_RENDER_STALL_S=N: the replay's no-delivery deadline (default 120 s); raise it when the input can pause for longer,
# e.g. a FIFO fed from a cloud volume whose reader waits out dropouts.
set -u
SRC=${1:?usage: plain_render.sh CAPTURE.tpc OUT.mov [WORKDIR]}; OUT=${2:?usage: plain_render.sh CAPTURE.tpc OUT.mov [WORKDIR]}
HERE=$(cd "$(dirname "$0")" && pwd); REPO=$(cd "$HERE/../.." && pwd)
RP="$REPO/src/frameserver/frameserver_replay"
D=${3:-$(mktemp -d "${TMPDIR:-/tmp}/plain_render.XXXXXX")}; mkdir -p "$D"
VOUT="$(dirname "$OUT")/.$(basename "$OUT" .mov).video-only.mov"
[ -e "$OUT" ] && { echo "REFUSE: output exists: $OUT"; exit 2; }
DLOG=${PLAIN_RENDER_DECISION_LOG:-}
[ -n "$DLOG" ] && [ -e "$DLOG" ] && { echo "REFUSE: decision log exists: $DLOG"; exit 2; }
[ -x "$RP" ] || { echo "REFUSE: build $RP first (make -C src/frameserver frameserver_replay)"; exit 2; }
make -C "$REPO/src/frameserver" -q frameserver_replay || { echo "REFUSE: $RP is older than its source; rebuild it"; exit 2; }
# The repo can sit in iCloud-synced ~/Documents: an evicted binary launched while it is still downloading is killed by
# macOS with "Code Signature Invalid" before it runs (2026-10-21). Read it in full first, then check its signature.
cat "$RP" > /dev/null || { echo "REFUSE: could not read $RP"; exit 2; }
codesign -v "$RP" 2>/dev/null || { echo "REFUSE: $RP fails its code-signature check"; exit 2; }
rm -f "$D/v.fifo" "$D/a.s24" "$D/timing.csv" "$D/replay.done" "$D/lost_counters.txt"; mkfifo "$D/v.fifo"; date
# Outputs are emptied in place, never deleted and recreated: JuiceMount (0.4) keeps a deleted file's write handle and its size
# high-water mark per path, so a file recreated where one was deleted can receive writes into the deleted inode, or be reported at
# the old size and crawl while the client reads each block before writing it (2026-10-21, both seen). Creating and truncating to 0
# clears the mark; ffmpeg then writes into that same file (-y).
empty_in_place(){ : > "$1" && truncate -s 0 "$1" && [ "$(stat -f %z "$1")" = 0 ] || { echo "REFUSE: could not empty $1 in place"; exit 2; }; }
empty_in_place "$VOUT"
# Units the host lost, from the capture's own sidecar (<recording>.registration.csv beside <recording>.raw.tpc): the relay
# never repeats a frame across them. Without a sidecar there is nothing to say which gaps are lost data, so holds are off.
SC="${SRC%.raw.tpc}.registration.csv"; LOST=none
if [ "$SC" != "$SRC" ] && [ -f "$SC" ]; then
  python3 - "$SC" "$D/lost_counters.txt" <<'PY' || { echo "REFUSE: could not read lost units from $SC"; exit 2; }
import sys
hdr = None; prev = None; lost = []
for line in open(sys.argv[1]):
    if line.startswith('#'): continue
    r = line.rstrip('\n').split(',')
    if hdr is None: hdr = {h: i for i, h in enumerate(r)}; DR, CE, OC = hdr['drop_reason'], hdr['counter_extended'], hdr['observed_counter']; continue
    c = int(r[CE]) if r[CE] else (int(r[OC]) if r[OC] not in ('', '0') else (prev + 1 if prev is not None else None))
    if r[DR] in ('Hole', 'PoolFull', 'PublisherFull', 'RingFullTail') and c is not None: lost.append(c % 65536)
    if c is not None: prev = c
open(sys.argv[2], 'w').write(''.join('%d\n' % c for c in lost)); print('lost units listed from the sidecar: %d' % len(lost))
PY
  LOST="$D/lost_counters.txt"
else echo "no sidecar beside the capture: single-slot holds are off"; fi
python3 "$HERE/relay.py" "$D/v.fifo" "$D/timing.csv" "$LOST" 2>"$D/relay.log" | ffmpeg -hide_banner -loglevel warning -nostdin \
  -f rawvideo -pix_fmt uyvy422 -s 720x480 -r 30000/1001 -i pipe:0 \
  -vf "setparams=field_mode=tff:range=tv:color_primaries=smpte170m:color_trc=smpte170m:colorspace=smpte170m,yadif=mode=send_field:parity=tff,crop=704:480:8:0,setsar=10/11" \
  -c:v prores_videotoolbox -profile:v standard -an -y "$VOUT" > "$D/ffmpeg.log" 2>&1 & PL=$!
FS_REGISTRATION_OFF=1 FS_HRETIME=0 FS_SHOW_PARTIAL=${PLAIN_RENDER_SHOW_PARTIAL:-1} "$RP" "$SRC" ${DLOG:+"$DLOG"} --offline --pool 32 ${PLAIN_RENDER_STALL_S:+--stall-s "$PLAIN_RENDER_STALL_S"} --dump-uyvy "$D/v.fifo" --dump-pcm "$D/a.s24" --dump-log "$D/timing.csv" > "$D/replay.log" 2>&1
RC=$?; touch "$D/replay.done"
# A replay that died before opening the FIFO leaves the relay blocked opening it: open the write end once without
# blocking, so the relay sees end of file and the pipeline ends (fails) instead of waiting forever.
python3 -c 'import os, sys
try: os.close(os.open(sys.argv[1], os.O_WRONLY | os.O_NONBLOCK))
except OSError: pass' "$D/v.fifo"
wait $PL; FRC=$?; rm -f "$D/v.fifo"; date
echo "replay exit $RC, encode exit $FRC"; grep -E "video obs|published|audio|skipped|failed" "$D/replay.log"; cat "$D/relay.log"
if [ $RC -ne 0 ] || [ $FRC -ne 0 ]; then echo "STAGE 1 FAILED: logs in $D, video-only kept at $VOUT"; exit 1; fi
python3 "$HERE/mux.py" "$D" "$VOUT" "$OUT" || { echo "MUX FAILED: logs in $D, video-only kept at $VOUT"; exit 1; }
rm -f "$VOUT"; [ -z "${3:-}" ] && rm -rf "$D"
date; echo ALL DONE
