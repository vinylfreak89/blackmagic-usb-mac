#!/bin/sh
# Deciding tests for the capture_core test deadlines (Codex's review of 9d56376). Each run is capped
# with perl's alarm, so a regression shows up as a failure rather than a hang.
cd "$(dirname "$0")" || exit 1
fails=0
tmp=$(mktemp -d) || exit 1
trap 'rm -rf "$tmp"' EXIT
cap() { secs=$1; shift; perl -e 'alarm shift; exec @ARGV' "$secs" "$@"; }
check() { if [ "$1" -eq 0 ]; then echo "  PASS  $2"; else echo "  FAIL  $2"; fails=$((fails + 1)); fi; }
ARGS="fixture.tpc $(cat fixture.expect) fixture_meta.tpc fixture_meta_exhaust.tpc $(cat fixture_meta_exhaust.expect)"

# 1. A per-wait deadline names the wait.
cap 60 env CC_TEST_WAIT_S=0 ./capture_core_test $ARGS >/dev/null 2>"$tmp/e1"; rc=$?
[ "$rc" -eq 2 ] && grep -q 'waiting for on_end (replay run)' "$tmp/e1"; check $? "CC_TEST_WAIT_S=0 fails by name (exit $rc)"

# 2. The whole-test deadline names the last phase (the test takes several seconds).
cap 60 env CC_TEST_TOTAL_S=1 ./capture_core_test $ARGS >/dev/null 2>"$tmp/e2"; rc=$?
[ "$rc" -eq 2 ] && grep -q 'whole test exceeded CC_TEST_TOTAL_S' "$tmp/e2"; check $? "CC_TEST_TOTAL_S=1 fails by name (exit $rc)"

if [ "$fails" -eq 0 ]; then echo "deadline tests: PASS"; else echo "deadline tests: $fails FAILED"; fi
exit "$fails"
