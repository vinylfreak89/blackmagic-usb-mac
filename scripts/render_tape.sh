#!/bin/bash
# Whole-tape review render: frameserver replay (registration + H-retime as configured by the caller's GE_* /
# FS_HRETIME* environment) spooling the published 480i frames losslessly, then the overlay render from those
# actual pixels (ProRes 422, VideoToolbox), then strip/tick validation and a status file.
#
# Usage: render_tape.sh NAME CAPTURE.tpc OUTDIR REPLAY_BINARY [PAIRING_SCHEDULE.csv]
# Writes OUTDIR/NAME.mov, OUTDIR/NAME_registration.csv, OUTDIR/NAME.mov.status.json. The spool and PCM are
# working files in OUTDIR, deleted after validation passes. Any replay hole or drop stops the render: the
# published frames would not be the engine's whole output. PACE_US (default 16000, real time) paces the replay
# so the lossless spool, written to a cloud volume, keeps up: at 8000 with the range coder the dump fell behind
# and the ring dropped 438 of 650 capture-4 units under load. SPOOLDIR puts the spool and PCM on a faster disk:
# two spools writing to the cloud volume at once blocked fixture A's publish worker (491 ring drops, 2026-10-02).
set -u -o pipefail   # bash 3.2: empty arrays expand as ${a[@]+"${a[@]}"} under set -u
NAME=$1 CAPTURE=$2 OUT=$3 BIN=$4 SCHED=${5:-}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
SPOOL="${SPOOLDIR:-$OUT}/$NAME.spool.mkv" PCM="${SPOOLDIR:-$OUT}/$NAME.pcm" SIDE="$OUT/$NAME"_registration.csv FIFO=$(mktemp -u)
VIDEO="$OUT/$NAME.mov" LOG="$OUT/$NAME.render.log"
for f in "$SPOOL" "$PCM" "$SIDE" "$VIDEO" "$VIDEO.status.json"; do rm -f "$f"; done   # replace outright, no backups
mkfifo "$FIFO" || exit 1
ffmpeg -hide_banner -loglevel error -f rawvideo -pix_fmt uyvy422 -s 720x480 -r 30000/1001 -i "$FIFO" \
       -c:v ffv1 -level 3 -slices 16 "$SPOOL" &
ENC=$!
trap 'kill $ENC 2>/dev/null; rm -f "$FIFO"' EXIT   # a replay that never opens the FIFO must not strand the encoder
SCHEDARG=(); RENDARG=()
if [ -n "$SCHED" ]; then SCHEDARG=(--pairing-schedule "$SCHED"); RENDARG=(--pairing-schedule "$SCHED"); fi
echo "== $(date) replay $NAME" | tee "$LOG"
env | grep -E '^(GE_|FS_)' | sort | tee -a "$LOG"
"$BIN" "$CAPTURE" "$SIDE" --pace-us ${PACE_US:-16000} ${SCHEDARG[@]+"${SCHEDARG[@]}"} --dump-uyvy "$FIFO" --dump-pcm "$PCM" >>"$LOG" 2>&1
RC=$?; wait $ENC; ERC=$?; rm -f "$FIFO"
grep -E "video obs|published|audio sink" "$LOG"
if [ $RC -ne 0 ] || [ $ERC -ne 0 ]; then echo "FAILED replay rc=$RC encoder rc=$ERC" | tee -a "$LOG"; exit 1; fi
if ! grep -q " hole 0 " "$LOG" || ! grep -q "dropped(pool) 0 dropped(ring) 0 dropped(surfaces) 0" "$LOG"; then
    echo "FAILED: holes or drops in the replay" | tee -a "$LOG"; exit 1; fi
echo "== $(date) render $NAME" | tee -a "$LOG"
python3 "$ROOT/experiments/geometry_render.py" "$CAPTURE" "$VIDEO" --engine-log "$SIDE" --published-uyvy "$SPOOL" \
        --pcm "$PCM" --codec prores ${RENDARG[@]+"${RENDARG[@]}"} >>"$LOG" 2>&1 || { echo "FAILED render" | tee -a "$LOG"; exit 1; }
tail -2 "$LOG"
echo "== $(date) validate $NAME" | tee -a "$LOG"
REV=$(git -C "$ROOT" rev-parse HEAD)
python3 "$ROOT/scripts/tape_render_status.py" --engine-commit "$REV" --renderer-commit "$REV" "$NAME" "$VIDEO" "$SIDE" \
        2>&1 | tee -a "$LOG" | tail -1
grep -q '"state": "READY"' "$VIDEO.status.json" || { echo "FAILED validation (spool kept)" | tee -a "$LOG"; exit 1; }
rm -f "$SPOOL" "$PCM"
echo "== $(date) done $NAME" | tee -a "$LOG"
