#!/bin/bash
# plain_render.sh [--replace] CAPTURE.tpc OUT.mov [WORKDIR]
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
#   3. audio_relay.py streams the audio as the device delivered it, continuous from the first frame's audio time
#      (a0.json, published by relay.py at its first frame), inserting silence only across a transport hole.
#   4. ONE ffmpeg takes both: TFF, BT.601 limited range, yadif send_field (59.94p), crop 704x480 at x=8, SAR 10/11,
#      ProRes 422 on the VideoToolbox hardware encoder, PCM S24 audio, into a hidden file beside OUT with the index at the
#      end, as ffmpeg writes a .mov by default (and OBS does). Its frame count is checked against the relay's slots from
#      the index alone, then it takes OUT's name. Until 2026-10-22 the video went to a video-only file and a second pass
#      re-read it all to mux the audio in with the index at the front: a second full read and write of every render.
#
# Refuses to overwrite OUT unless --replace; with it, OUT is untouched until the new render has passed its checks. WORKDIR (default: a fresh temp dir) holds the FIFO, PCM and timing log;
# it is removed when the render succeeds.
# A capture on the JuiceFS share (/Volumes/zpool) is read through scripts/juicefs/checked_read.py, which passes the replay each
# piece only after proving it against the SHA-1 the object store lists (JuiceFS 1.4.1 can hand back another block's data as a
# successful read: juicedata/juicefs#7499); a piece that never matches fails the render. PLAIN_RENDER_CHECKED_READ=0 turns this off.
# A local copy of a capture on the share (same file name and exact size in /Volumes/zpool) is checked the same way: its bytes
# are proven against the share file's blocks, so nothing is downloaded and the copy itself is proven intact.
# CAPTURE.tpc may be a FIFO (the replay reads it as a stream). PLAIN_RENDER_DECISION_LOG=FILE also writes the replay's
# decision log (the sidecar's schema) from the same pass; it is not overwritten if it exists.
# PLAIN_RENDER_STALL_S=N: the replay's no-delivery deadline (default 120 s); raise it when the input can pause for longer,
# e.g. a FIFO fed from a cloud volume whose reader waits out dropouts.
set -u
# The whole script is one function, called on the last line: bash reads and parses all of it before running any of it.
# Run as plain lines, bash reads the file as it goes, so an edit during a render makes the running render execute
# the new file from the old byte offset (2026-10-21: an edit mid-render ended one with "unexpected EOF").
main() {
REPLACE=""; [ "${1:-}" = "--replace" ] && { REPLACE=--replace; shift; }
SRC=${1:?usage: plain_render.sh [--replace] CAPTURE.tpc OUT.mov [WORKDIR]}; OUT=${2:?usage: plain_render.sh [--replace] CAPTURE.tpc OUT.mov [WORKDIR]}
HERE=$(cd "$(dirname "$0")" && pwd); REPO=$(cd "$HERE/../.." && pwd)
RP="$REPO/src/frameserver/frameserver_replay"
D=${3:-$(mktemp -d "${TMPDIR:-/tmp}/plain_render.XXXXXX")}; mkdir -p "$D"
PART="$(dirname "$OUT")/.$(basename "$OUT" .mov).partial.mov"
# An existing output is never touched unless --replace is given; then it stays intact until the new render has passed its
# checks and takes its name.
[ -e "$OUT" ] && [ -z "$REPLACE" ] && { echo "REFUSE: output exists: $OUT (add --replace to overwrite it)"; exit 2; }
[ -e "$OUT" ] && [ ! -f "$OUT" ] && { echo "REFUSE: output exists and is not a file: $OUT"; exit 2; }
DLOG=${PLAIN_RENDER_DECISION_LOG:-}
[ -n "$DLOG" ] && [ -e "$DLOG" ] && { echo "REFUSE: decision log exists: $DLOG"; exit 2; }
[ -x "$RP" ] || { echo "REFUSE: build $RP first (make -C src/frameserver frameserver_replay)"; exit 2; }
make -C "$REPO/src/frameserver" -q frameserver_replay || { echo "REFUSE: $RP is older than its source; rebuild it"; exit 2; }
# The repo can sit in iCloud-synced ~/Documents: an evicted binary launched while it is still downloading is killed by
# macOS with "Code Signature Invalid" before it runs (2026-10-21). Read it in full first, then check its signature.
cat "$RP" > /dev/null || { echo "REFUSE: could not read $RP"; exit 2; }
codesign -v "$RP" 2>/dev/null || { echo "REFUSE: $RP fails its code-signature check"; exit 2; }
rm -f "$D/v.fifo" "$D/a.fifo" "$D/cap.fifo" "$D/a.s24" "$D/timing.csv" "$D/replay.done" "$D/a0.json" "$D/schedule.json" "$D/audio.json" "$D/lost_counters.txt" "$D/checked_read.rc"
mkfifo "$D/v.fifo" "$D/a.fifo"; date
# Outputs are emptied in place, never deleted and recreated: JuiceMount (0.4) keeps a deleted file's write handle and its size
# high-water mark per path, so a file recreated where one was deleted can receive writes into the deleted inode, or be reported at
# the old size and crawl while the client reads each block before writing it (2026-10-21, both seen). Creating and truncating to 0
# clears the mark; ffmpeg then writes into that same file (-y).
empty_in_place(){ : > "$1" && truncate -s 0 "$1" && [ "$(stat -f %z "$1")" = 0 ] || { echo "REFUSE: could not empty $1 in place"; exit 2; }; }
empty_in_place "$PART"
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
python3 "$HERE/audio_relay.py" "$D" "$D/a.fifo" 2>"$D/audio_relay.log" & AP=$!
python3 "$HERE/relay.py" "$D/v.fifo" "$D/timing.csv" "$LOST" 2>"$D/relay.log" | ffmpeg -hide_banner -loglevel warning -nostdin \
  -thread_queue_size 64 -f rawvideo -pix_fmt uyvy422 -s 720x480 -r 30000/1001 -i pipe:0 \
  -thread_queue_size 4096 -f s24le -ar 48000 -ac 2 -i "$D/a.fifo" \
  -map 0:v -map 1:a \
  -vf "setparams=field_mode=tff:range=tv:color_primaries=smpte170m:color_trc=smpte170m:colorspace=smpte170m,yadif=mode=send_field:parity=tff,crop=704:480:8:0,setsar=10/11" \
  -c:v prores_videotoolbox -profile:v standard -c:a pcm_s24le -shortest -f mov -y "$PART" > "$D/ffmpeg.log" 2>&1 & PL=$!
# The replay's input: the capture itself, or a FIFO fed by the checked reader. If the checked reader ends without opening the
# FIFO (a setup error), the write end is opened once without blocking so the replay sees end of file instead of waiting forever.
RSRC="$SRC"; CRP=""
CHK="$SRC"; CRARGS=()
case "$SRC" in /Volumes/zpool/*) ;; *)
  POOL="/Volumes/zpool/$(basename "$SRC")"
  if [ -f "$POOL" ] && [ -f "$SRC" ] && [ "$(stat -f %z "$POOL")" = "$(stat -f %z "$SRC")" ]; then
    CHK="$POOL"; CRARGS=(--bytes-from "$SRC"); echo "local copy of $POOL: its blocks are checked against the share's"
  fi;; esac
case "$CHK" in /Volumes/zpool/*) if [ "${PLAIN_RENDER_CHECKED_READ:-1}" != 0 ]; then
  mkfifo "$D/cap.fifo"; RSRC="$D/cap.fifo"
  { python3 "$REPO/scripts/juicefs/checked_read.py" "$CHK" ${CRARGS[@]+"${CRARGS[@]}"} --out "$D/cap.fifo" --report "$D/checked_read.json" 2>"$D/checked_read.log"
    echo $? > "$D/checked_read.rc"
    python3 -c 'import os, sys
try: os.close(os.open(sys.argv[1], os.O_WRONLY | os.O_NONBLOCK))
except OSError: pass' "$D/cap.fifo"; } & CRP=$!
fi;; esac
FS_REGISTRATION_OFF=1 FS_HRETIME=0 FS_SHOW_PARTIAL=${PLAIN_RENDER_SHOW_PARTIAL:-1} "$RP" "$RSRC" ${DLOG:+"$DLOG"} --offline --pool 32 ${PLAIN_RENDER_STALL_S:+--stall-s "$PLAIN_RENDER_STALL_S"} --dump-uyvy "$D/v.fifo" --dump-pcm "$D/a.s24" --dump-log "$D/timing.csv" > "$D/replay.log" 2>&1
RC=$?; touch "$D/replay.done"
CRC=0; if [ -n "$CRP" ]; then wait $CRP; CRC=$(cat "$D/checked_read.rc" 2>/dev/null || echo 9); rm -f "$D/cap.fifo"; tail -1 "$D/checked_read.log"; fi
# A replay that died before opening the FIFO leaves the relay blocked opening it: open the write end once without
# blocking, so the relay sees end of file and the pipeline ends (fails) instead of waiting forever.
python3 -c 'import os, sys
try: os.close(os.open(sys.argv[1], os.O_WRONLY | os.O_NONBLOCK))
except OSError: pass' "$D/v.fifo"
wait $PL; FRC=$?
# An ffmpeg that ended early leaves the audio relay blocked on its FIFO: open the read end once without blocking, so it ends (fails).
python3 -c 'import os, sys
try: os.close(os.open(sys.argv[1], os.O_RDONLY | os.O_NONBLOCK))
except OSError: pass' "$D/a.fifo"
wait $AP; ARC=$?; rm -f "$D/v.fifo" "$D/a.fifo"; date
echo "replay exit $RC, encode exit $FRC, audio exit $ARC"; grep -E "video obs|published|audio|skipped|failed" "$D/replay.log"; cat "$D/relay.log" "$D/audio_relay.log"
if [ "$CRC" != 0 ]; then echo "CHECKED READ FAILED (exit $CRC): the capture was not proven intact; see $D/checked_read.log and $D/checked_read.json. Render not finished."; exit 1; fi
if [ $RC -ne 0 ] || [ $FRC -ne 0 ] || [ $ARC -ne 0 ]; then echo "RENDER FAILED: logs in $D, the unfinished render kept at $PART"; exit 1; fi
python3 "$HERE/finish.py" "$D" "$PART" "$OUT" || { echo "RENDER FAILED: logs in $D, the unfinished render kept at $PART"; exit 1; }
[ -z "${3:-}" ] && rm -rf "$D"
date; echo ALL DONE
}
main "$@"; exit $?
