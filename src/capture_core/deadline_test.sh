#!/bin/sh
# Deciding tests for the capture_core test deadlines (Codex's review of 9d56376). Each run is capped
# by a separate Python parent, so the child cannot replace the backstop's alarm.
cd "$(dirname "$0")" || exit 1
fails=0
tmp=$(mktemp -d) || exit 1
trap 'rm -rf "$tmp"' EXIT
cap() { python3 ../../scripts/run_deadline.py "$@"; }
check() { if [ "$1" -eq 0 ]; then echo "  PASS  $2"; else echo "  FAIL  $2"; fails=$((fails + 1)); fi; }

# 1. A per-wait deadline names the wait.
cap 5 ./capture_core_test --deadline-probe wait >/dev/null 2>"$tmp/e1"; rc=$?
[ "$rc" -eq 2 ] && grep -q 'waiting for on_end (forced wait probe)' "$tmp/e1"; check $? "per-wait deadline (exit $rc)"

# 2. The whole-test deadline names the last phase (the test takes several seconds).
cap 5 env CC_TEST_TOTAL_S=.1 ./capture_core_test --deadline-probe total >/dev/null 2>"$tmp/e2"; rc=$?
[ "$rc" -eq 2 ] && grep -q 'capture_core_test whole-run deadline' "$tmp/e2"; check $? "parent terminates child that cancels alarm (exit $rc)"
cap 5 ./capture_core_test --deadline-probe hook >/dev/null 2>"$tmp/e3"; rc=$?
[ "$rc" -eq 2 ] && grep -q 'cc_test_after_empty_snapshot' "$tmp/e3"; check $? "worker-hook deadline (exit $rc)"
cap 5 ./test_shim --deadline-probe wait >/dev/null 2>"$tmp/e4"; rc=$?
[ "$rc" -eq 2 ] && grep -q 'shim run_device on_end' "$tmp/e4"; check $? "shim timeout exits before stop (exit $rc)"
cap 5 env SHIM_TEST_TOTAL_S=.1 ./test_shim --deadline-probe total >/dev/null 2>"$tmp/e5"; rc=$?
[ "$rc" -eq 2 ] && grep -q 'capture_core_shim_test whole-run deadline' "$tmp/e5"; check $? "shim parent deadline (exit $rc)"
cap .1 python3 -c 'import signal,time; signal.alarm(0); time.sleep(30)' >/dev/null 2>"$tmp/e6"; rc=$?
[ "$rc" -eq 124 ] && grep -q 'external supervisor' "$tmp/e6"; check $? "outer backstop is independent (exit $rc)"

if [ "$fails" -eq 0 ]; then echo "deadline tests: PASS"; else echo "deadline tests: $fails FAILED"; fi
exit "$fails"
