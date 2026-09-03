#!/bin/zsh
# Gate for replacing captures/fulltape_render.{mp4,_registration.csv} with a new render: every check prints PASS/FAIL. Usage: render_fulltape_gate.sh <out_dir>
R=$(cd "$(dirname "$0")/.." && pwd); OUT=${1:?render_out_dir}; fails=0
chk(){ if [ "$1" = 0 ]; then echo "PASS $2"; else echo "FAIL $2"; fails=$((fails+1)); fi }
[ -f $OUT/fulltape_render.mp4 ] && [ -f $OUT/fulltape_render_registration.csv ]; chk $? "outputs exist"
grep -q RENDER_DONE $OUT/timing.txt; chk $? "render script completed"
grep -q 'Traceback\|Error:\|error:' $OUT/render.log; [ $? -ne 0 ]; chk $? "render log has no Python traceback or error (census lines like counter_errors=0 are not errors)"
ffmpeg -v error -xerror -i $OUT/fulltape_render.mp4 -f null - 2> $OUT/decode.log; chk $? "full decode with -xerror clean"
newd=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $OUT/fulltape_render.mp4); oldd=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $R/captures/fulltape_render.mp4)
python3 -c "import sys; n,o=float('$newd'),float('$oldd'); sys.exit(0 if abs(n-o)<0.1 else 1)"; chk $? "duration matches the previous render ($newd vs $oldd s)"
newr=$(wc -l < $OUT/fulltape_render_registration.csv); oldr=$(wc -l < $R/captures/fulltape_render_registration.csv)
[ "$newr" = "$oldr" ]; chk $? "sidecar row count matches ($newr vs $oldr)"
nfr=$(ffprobe -v error -select_streams v -count_packets -show_entries stream=nb_read_packets -of csv=p=0 $OUT/fulltape_render.mp4)
python3 -c "import sys; sys.exit(0 if abs(int('$nfr') - 2*(int('$newr')-1)) <= 4 else 1)"; chk $? "video frames ≈ 2 x sidecar units ($nfr vs $(( 2*(newr-1) )))"
python3 - <<PY
import csv,collections,sys
rows=list(csv.DictReader(open('$OUT/fulltape_render_registration.csv')))
pairs=[(r.get('applied_d1'),r.get('applied_d2')) for r in rows]
trans=sum(1 for i in range(1,len(pairs)) if pairs[i]!=pairs[i-1]); blips=sum(1 for i in range(1,len(pairs)-1) if pairs[i]!=pairs[i-1] and pairs[i+1]==pairs[i-1])
rel=sum(1 for r in rows if r.get('relative_only') in ('1','True','true'))
print(f"  sidecar: {len(rows)} rows, {trans} applied-phase transitions, {blips} one-unit flips, {rel} relative-only rows, pairs {collections.Counter(pairs).most_common(5)}")
PY
echo "gate failures: $fails"; [ $fails = 0 ] && echo GATE_PASS || echo GATE_FAIL
