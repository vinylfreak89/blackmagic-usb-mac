#!/bin/zsh
# Produce a review copy exclusively from the live frameserver's published
# 480i frames, PCM blocks, and schema-5 decision log. Raw media travels through
# FIFOs and is never materialized. Usage:
#   render_live.sh capture.tpc non_synced_out_dir [pace_us]
set -euo pipefail

CAP=${1:?capture.tpc}
OUT=${2:?non-synced output directory}
# NNEDI is slower than the device on the validation host (~10 input units/s).
# Replay is therefore intentionally slower than realtime; correctness requires
# the live callback path to report zero sheds, not a wall-clock-rate encode.
PACE_US=${3:-50000}
REPO=$(cd "$(dirname "$0")/.." && pwd)
CAP=$(cd "$(dirname "$CAP")" && pwd)/$(basename "$CAP")
OUT=$(mkdir -p "$OUT" && cd "$OUT" && pwd)
WEIGHTS="$HOME/Library/Application Support/blackmagic-usb-mac/nnedi3_weights.bin"
REPLAY="$REPO/src/frameserver/frameserver_replay"
SIDECAR="$OUT/live_registration.csv"
VIDEO="$OUT/live_review.mp4"
OVERLAY="$OUT/live_review_overlay.mp4"
TMP=$(mktemp -d /tmp/blackmagic-render-live.XXXXXX)
VFIFO="$TMP/video.uyvy"
AFIFO="$TMP/audio.s24le"
VPID=""
APID=""

cleanup() {
  exec 8>&- 2>/dev/null || true
  exec 9>&- 2>/dev/null || true
  if [[ -n "$VPID" ]]; then kill "$VPID" 2>/dev/null || true; fi
  if [[ -n "$APID" ]]; then kill "$APID" 2>/dev/null || true; fi
  rm -f "$VFIFO" "$AFIFO"
  rmdir "$TMP" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

[[ -f "$CAP" ]] || { print -u2 "capture does not exist: $CAP"; exit 2; }
[[ -f "$WEIGHTS" ]] || { print -u2 "NNEDI weights do not exist: $WEIGHTS"; exit 2; }
[[ $(stat -f %z "$WEIGHTS") = 13574928 ]] || {
  print -u2 "NNEDI weights have the wrong size: $WEIGHTS"; exit 2
}

make -s -C "$REPO/src/frameserver" frameserver_replay
mkfifo "$VFIFO" "$AFIFO"
# Keep both FIFOs open until replay finishes. This prevents the reader and the
# replay's two fopen calls from deadlocking while ffmpeg probes its first input.
exec 8<> "$VFIFO"
exec 9<> "$AFIFO"

git -C "$REPO" rev-parse HEAD > "$OUT/engine_commit.txt"
date '+%F %T start' > "$OUT/timing.txt"
# Video and audio have independent consumers. A single ffmpeg with two FIFOs
# can deadlock at EOF: one demuxer waits for EOF while the other frameserver
# callback blocks on a full pipe. The two compressed elementary MP4s are small,
# bounded staging artifacts and are stream-copied together after both FIFOs end.
VSTAGE="$OUT/.live_video.mp4"
ASTAGE="$OUT/.live_audio.m4a"
(
  exec 8>&-
  exec 9>&-
  exec ffmpeg -hide_banner -loglevel warning -y \
    -thread_queue_size 512 -probesize 32 -analyzeduration 0 \
    -f rawvideo -pixel_format uyvy422 \
    -video_size 720x480 -framerate 30000/1001 -i "$VFIFO" \
    -map 0:v:0 -an \
    -vf "format=yuv422p,nnedi=weights=$WEIGHTS:field=tf:deint=all:nns=n32:qual=fast,setsar=8/9" \
    -fps_mode passthrough -c:v libx264 -preset veryfast -crf 12 -pix_fmt yuv420p \
    "$VSTAGE"
) > "$OUT/video_ffmpeg.log" 2>&1 &
VPID=$!
(
  exec 8>&-
  exec 9>&-
  exec ffmpeg -hide_banner -loglevel warning -y \
    -thread_queue_size 512 -probesize 32 -analyzeduration 0 \
    -f s24le -ar 48000 -ac 2 -i "$AFIFO" \
    -map 0:a:0 -vn -c:a aac -ar 48000 -ac 2 "$ASTAGE"
) > "$OUT/audio_ffmpeg.log" 2>&1 &
APID=$!

set +e
"$REPLAY" "$CAP" "$SIDECAR" --pace-us "$PACE_US" --ring-mb 256 --pool 64 \
  --dump-uyvy "$VFIFO" --dump-pcm "$AFIFO" --dump-log "$OUT/live_av.csv" \
  > "$OUT/replay.log" 2>&1
REPLAY_RC=$?
set -e
exec 8>&-
exec 9>&-
set +e
wait "$VPID"
VIDEO_RC=$?
wait "$APID"
AUDIO_RC=$?
set -e
VPID=""
APID=""
if (( REPLAY_RC != 0 || VIDEO_RC != 0 || AUDIO_RC != 0 )); then
  print -u2 "live render failed: replay=$REPLAY_RC video=$VIDEO_RC audio=$AUDIO_RC"
  exit 1
fi
ffmpeg -hide_banner -loglevel warning -y -i "$VSTAGE" -i "$ASTAGE" \
  -map 0:v:0 -map 1:a:0 -c copy -movflags +faststart "$VIDEO" \
  > "$OUT/mux.log" 2>&1
rm -f "$VSTAGE" "$ASTAGE"

if ! python3 "$REPO/experiments/overlay_sidecar.py" \
  "$VIDEO" "$SIDECAR" "$OVERLAY" --crf 12 > "$OUT/overlay.log" 2>&1; then
  cat "$OUT/overlay.log" >&2
  exit 1
fi
if ! python3 "$REPO/experiments/render_live_gate.py" \
  "$VIDEO" "$OVERLAY" "$SIDECAR" > "$OUT/gate.log" 2>&1; then
  cat "$OUT/gate.log" >&2
  exit 1
fi
cat "$OUT/gate.log"
date '+%F %T end' >> "$OUT/timing.txt"
print RENDER_LIVE_DONE >> "$OUT/timing.txt"
