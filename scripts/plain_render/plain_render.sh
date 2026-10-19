#!/bin/bash
# plain_render.sh CAPTURE.tpc OUT.mov [WORKDIR]
#
# The plain review render: no overlays, no registration, no H-retiming. Used for the one-play tape
# (2026-10-17 13-48-05) and for test recordings.
#
#   1. frameserver_replay --offline (waits, never drops) with FS_REGISTRATION_OFF=1 FS_HRETIME=0 dumps the
#      published 720x480 UYVY frames, the PCM and the timing log.
#   2. relay.py places frames by unit counter; a counter the replay did not publish becomes a flat
#      no-signal frame, so timing holds.
#   3. ffmpeg: TFF, BT.601 limited range, yadif send_field (59.94p), crop 704x480 at x=8, SAR 10/11,
#      ProRes 422 on the VideoToolbox hardware encoder -> a hidden video-only file beside OUT.
#   4. mux.py places the audio against the first frame by its own clock, inserts the samples the device
#      did not supply once where the A/V residual steps, checks the frame count, and muxes video + audio
#      in one pass with the index reserved at the front. The video-only file is removed after success.
#
# Refuses to overwrite OUT. WORKDIR (default: a fresh temp dir) holds the FIFO, PCM and timing log;
# it is removed when the render succeeds.
set -u
SRC=${1:?usage: plain_render.sh CAPTURE.tpc OUT.mov [WORKDIR]}; OUT=${2:?usage: plain_render.sh CAPTURE.tpc OUT.mov [WORKDIR]}
HERE=$(cd "$(dirname "$0")" && pwd); REPO=$(cd "$HERE/../.." && pwd)
RP="$REPO/src/frameserver/frameserver_replay"
D=${3:-$(mktemp -d "${TMPDIR:-/tmp}/plain_render.XXXXXX")}; mkdir -p "$D"
VOUT="$(dirname "$OUT")/.$(basename "$OUT" .mov).video-only.mov"
[ -e "$OUT" ] && { echo "REFUSE: output exists: $OUT"; exit 2; }
[ -x "$RP" ] || { echo "REFUSE: build $RP first (make -C src/frameserver frameserver_replay)"; exit 2; }
make -C "$REPO/src/frameserver" -q frameserver_replay || { echo "REFUSE: $RP is older than its source; rebuild it"; exit 2; }
rm -f "$D/v.fifo" "$D/a.s24" "$D/timing.csv" "$VOUT"; mkfifo "$D/v.fifo"; date
python3 "$HERE/relay.py" "$D/v.fifo" "$D/timing.csv" 2>"$D/relay.log" | ffmpeg -hide_banner -loglevel warning -nostdin \
  -f rawvideo -pix_fmt uyvy422 -s 720x480 -r 30000/1001 -i pipe:0 \
  -vf "setparams=field_mode=tff:range=tv:color_primaries=smpte170m:color_trc=smpte170m:colorspace=smpte170m,yadif=mode=send_field:parity=tff,crop=704:480:8:0,setsar=10/11" \
  -c:v prores_videotoolbox -profile:v standard -an "$VOUT" > "$D/ffmpeg.log" 2>&1 & PL=$!
FS_REGISTRATION_OFF=1 FS_HRETIME=0 "$RP" "$SRC" --offline --pool 32 --dump-uyvy "$D/v.fifo" --dump-pcm "$D/a.s24" --dump-log "$D/timing.csv" > "$D/replay.log" 2>&1
RC=$?; wait $PL; FRC=$?; rm -f "$D/v.fifo"; date
echo "replay exit $RC, encode exit $FRC"; grep -E "video obs|published|audio|skipped|failed" "$D/replay.log"; cat "$D/relay.log"
if [ $RC -ne 0 ] || [ $FRC -ne 0 ]; then echo "STAGE 1 FAILED: logs in $D, video-only kept at $VOUT"; exit 1; fi
python3 "$HERE/mux.py" "$D" "$VOUT" "$OUT" || { echo "MUX FAILED: logs in $D, video-only kept at $VOUT"; exit 1; }
rm -f "$VOUT"; [ -z "${3:-}" ] && rm -rf "$D"
date; echo ALL DONE
