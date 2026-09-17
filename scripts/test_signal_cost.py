#!/usr/bin/env python3
"""Mutate the real cost gate: waiting is free, CPU work is not. No captures."""
import re
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SS = ROOT / "src/signal_state"
SOURCE = (SS / "tests/signal_state_test.c").read_text()
SITE = "/* Cost-control mutations insert work here, inside the measured region. */"
assert SOURCE.count(SITE) == 1
SLEEP = "struct timespec pause = {0, 10000000}; assert(nanosleep(&pause, NULL) == 0);"
# Independently read thread CPU time: mutating the gate's clock must not change
# the injected workload's meaning. Seven ms per iteration exceeds the 5ms gate.
BUSY = """
        struct timespec started, current;
        assert(clock_gettime(CLOCK_THREAD_CPUTIME_ID, &started) == 0);
        do {
            assert(clock_gettime(CLOCK_THREAD_CPUTIME_ID, &current) == 0);
        } while ((current.tv_sec - started.tv_sec) * 1000000000LL +
                 current.tv_nsec - started.tv_nsec < 7000000LL);
"""


def check(folder, name, injection, fails=False, wall_clock=False):
    source = SOURCE.replace(SITE, injection)
    if wall_clock:
        old = "clock_gettime(CLOCK_THREAD_CPUTIME_ID, &value)"
        assert source.count(old) == 1
        source = source.replace(old, "clock_gettime(CLOCK_MONOTONIC, &value)")
    path = folder / f"{name}.c"
    path.write_text(source)
    binary = folder / name
    subprocess.run(["cc", "-O3", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-I", str(SS), str(SS / "signal_state.c"), str(path),
                    "-lm", "-o", str(binary)], check=True)
    start = time.monotonic()
    run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
    elapsed = time.monotonic() - start
    match = re.search(r"CPU cost=([0-9.]+) us/unit", run.stdout)
    assert match, (name, run.returncode, run.stdout, run.stderr)
    cost = float(match[1])
    if fails:
        assert run.returncode != 0 and "microseconds < 5000.0" in run.stderr, (name, run)
        assert cost > 5000 and "signal_state_test: PASS" not in run.stdout, (name, run)
    else:
        assert run.returncode == 0 and cost < 5000, (name, run)
        assert "signal_state_test: PASS" in run.stdout, (name, run)
    if injection == SLEEP:
        assert elapsed >= 1.0, (name, elapsed)
    print(f"PASS {name}: exit={run.returncode}, gate={cost:.3f} us/unit, "
          f"wall={elapsed:.3f}s", flush=True)


with tempfile.TemporaryDirectory(prefix="signal-cost-controls-") as temp:
    folder = Path(temp)
    check(folder, "baseline", "")
    check(folder, "sleep", SLEEP)
    check(folder, "busy", BUSY, fails=True)
    # Positive control: restoring the old wall clock rejects the same sleep.
    check(folder, "old-clock-sleep", SLEEP, fails=True, wall_clock=True)
