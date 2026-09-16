#!/bin/sh
# Deciding tests for the frameserver deadlines (Codex's review of 9d56376). Every run is itself capped
# by a separate Python parent, so the child's alarms cannot cancel the backstop.
cd "$(dirname "$0")/.." || exit 1
FIX=../unit_parser/tests/fixture.tpc
FIXL=../unit_parser/tests/fixture_plain.tpc
fails=0
holder=
tmp=$(mktemp -d) || exit 1
trap '[ -n "$holder" ] && kill "$holder" 2>/dev/null; rm -rf "$tmp"' EXIT
cap() { python3 ../../scripts/run_deadline.py "$@"; }
check() { if [ "$1" -eq 0 ]; then echo "  PASS  $2"; else echo "  FAIL  $2"; fails=$((fails + 1)); fi; }

# 1. Slow pacing is not a stall: the limit is never shorter than ten --pace-us intervals.
cap 120 ./frameserver_replay "$FIX" --pace-us 2000000 --stall-s 1 >/dev/null 2>"$tmp/e1"; rc=$?
[ "$rc" -eq 0 ]; check $? "slow pacing (--pace-us 2000000 --stall-s 1) completes (exit $rc)"

# 2. A real stall ends the process by name: the video sink blocks on a FIFO that is open but never read.
mkfifo "$tmp/fifo"
sleep 120 <"$tmp/fifo" & holder=$!
cap 60 ./frameserver_replay "$FIXL" --dump-uyvy "$tmp/fifo" --stall-s 2 >/dev/null 2>"$tmp/e2"; rc=$?
kill "$holder" 2>/dev/null; holder=
[ "$rc" -eq 3 ] && grep -q 'no capture-core packet delivery' "$tmp/e2"; check $? "a blocked sink is reported as a stall (exit $rc)"

# 3. A per-wait deadline names the wait.
cap 5 ./tests/frameserver_test --deadline-probe wait >/dev/null 2>"$tmp/e3"; rc=$?
[ "$rc" -eq 2 ] && grep -q 'waiting for on_end (forced wait probe)' "$tmp/e3"; check $? "per-wait deadline fails by name (exit $rc)"

# 4. The whole-test deadline covers the rest (joins, fs_stop) and names the last phase.
cap 5 env FS_TEST_TOTAL_S=.1 ./tests/frameserver_test --deadline-probe total >/dev/null 2>"$tmp/e4"; rc=$?
[ "$rc" -eq 2 ] && grep -q 'frameserver_test whole-run deadline' "$tmp/e4"; check $? "parent terminates child that cancels alarm (exit $rc)"
cap 5 ./tests/frameserver_test --deadline-probe hook >/dev/null 2>"$tmp/e5"; rc=$?
[ "$rc" -eq 2 ] && grep -q 'fs_test_after_empty_snapshot' "$tmp/e5"; check $? "worker-hook deadline (exit $rc)"

if [ "$fails" -eq 0 ]; then echo "deadline tests: PASS"; else echo "deadline tests: $fails FAILED"; fi
exit "$fails"
