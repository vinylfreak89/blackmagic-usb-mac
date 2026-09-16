#!/bin/sh
# Deciding tests for the frameserver deadlines (Codex's review of 9d56376). Every run is itself capped
# with perl's alarm, so a regression shows up as a failure rather than a hang.
cd "$(dirname "$0")/.." || exit 1
FIX=../unit_parser/tests/fixture.tpc
FIXL=../unit_parser/tests/fixture_plain.tpc
fails=0
holder=
tmp=$(mktemp -d) || exit 1
trap '[ -n "$holder" ] && kill "$holder" 2>/dev/null; rm -rf "$tmp"' EXIT
cap() { secs=$1; shift; perl -e 'alarm shift; exec @ARGV' "$secs" "$@"; }
check() { if [ "$1" -eq 0 ]; then echo "  PASS  $2"; else echo "  FAIL  $2"; fails=$((fails + 1)); fi; }

# 1. Slow pacing is not a stall: the limit is never shorter than ten --pace-us intervals.
cap 120 ./frameserver_replay "$FIX" --pace-us 2000000 --stall-s 1 >/dev/null 2>"$tmp/e1"; rc=$?
[ "$rc" -eq 0 ]; check $? "slow pacing (--pace-us 2000000 --stall-s 1) completes (exit $rc)"

# 2. A real stall ends the process by name: the video sink blocks on a FIFO that is open but never read.
mkfifo "$tmp/fifo"
sleep 120 <"$tmp/fifo" & holder=$!
cap 60 ./frameserver_replay "$FIXL" --dump-uyvy "$tmp/fifo" --stall-s 2 >/dev/null 2>"$tmp/e2"; rc=$?
kill "$holder" 2>/dev/null; holder=
[ "$rc" -eq 3 ] && grep -q 'TIMEOUT: no new video or audio record' "$tmp/e2"; check $? "a blocked sink is reported as a stall (exit $rc)"

# 3. A per-wait deadline names the wait.
cap 60 env FS_TEST_WAIT_S=0 ./tests/frameserver_test "$FIX" "$FIXL" >/dev/null 2>"$tmp/e3"; rc=$?
[ "$rc" -eq 2 ] && grep -q 'waiting for on_end (main fixture run)' "$tmp/e3"; check $? "FS_TEST_WAIT_S=0 fails by name (exit $rc)"

# 4. The whole-test deadline covers the rest (joins, fs_stop) and names the last phase.
cap 60 env FS_TEST_TOTAL_S=1 ./tests/frameserver_test "$FIX" "$FIXL" >/dev/null 2>"$tmp/e4"; rc=$?
[ "$rc" -eq 2 ] && grep -q 'whole test exceeded FS_TEST_TOTAL_S' "$tmp/e4"; check $? "FS_TEST_TOTAL_S=1 fails by name (exit $rc)"

if [ "$fails" -eq 0 ]; then echo "deadline tests: PASS"; else echo "deadline tests: $fails FAILED"; fi
exit "$fails"
