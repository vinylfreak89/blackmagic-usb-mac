#!/bin/zsh
# Whole-tape watch copy + registration sidecar from the CURRENT engine, the recipe behind
# captures/fulltape_render.{mp4,_registration.csv}: capture_render.py over the tagged capture,
# v9 line-21 registration through libfieldreg.dylib built from this tree (no tunables), NNEDI bob 59.94p,
# 720x480 SAR 8:9, CRF 12 veryfast, stereo AAC. Runs ~1-2 h on an M3. Writes to a non-synced
# scratch directory (writer output rule); publish into captures/ only after the gate checks.
#   render_fulltape.sh <capture.cap6> <out_dir>
set -e
CAP=$(cd "$(dirname "${1:?capture}")" && pwd)/$(basename "$1"); OUT=${2:?out_dir}; REPO=$(cd "$(dirname "$0")/.." && pwd)   # absolute: the script cds before rendering
WEIGHTS="$HOME/Library/Application Support/blackmagic-usb-mac/nnedi3_weights.bin"
mkdir -p "$OUT"; cd "$REPO/src/field_registration" && make -s libfieldreg.dylib >/dev/null
cd "$REPO/src/signal_state" && make -s libsignalstate.dylib >/dev/null
git -C "$REPO" rev-parse HEAD > "$OUT/engine_commit.txt"; date '+%F %T start' >> "$OUT/timing.txt"
python3 "$REPO/experiments/capture_render.py" "$CAP" --input-format tagged \
  --render "$OUT/fulltape_render.mp4" --scratch-dir "$OUT/staging" --render-size 720x480 --render-sar 8:9 \
  --render-crf 12 --render-preset veryfast --adaptive-registration \
  --registration-library "$REPO/src/field_registration/libfieldreg.dylib" \
  --signal-state-library "$REPO/src/signal_state/libsignalstate.dylib" \
  --deinterlacer nnedi --nnedi-weights "$WEIGHTS" \
  --tagged-start-unit 4 --decision-log "$OUT/fulltape_render_registration.csv" > "$OUT/render.log" 2>&1
date '+%F %T end' >> "$OUT/timing.txt"; echo RENDER_DONE >> "$OUT/timing.txt"
