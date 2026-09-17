#!/usr/bin/env python3
"""Deciding failures for test-only overlap and replay windows (no capture needed)."""
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
FS = ROOT / "src/frameserver"


def failure(command, env, text):
    run = subprocess.run(command, env={**os.environ, **env}, text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    texts = (text,) if isinstance(text, str) else text
    assert run.returncode == 2 and any(t in run.stdout for t in texts), (run.returncode, run.stdout)
    observed = next(line for line in run.stdout.splitlines() if any(t in line for t in texts))
    print(f"PASS: expected exit {run.returncode}: {observed}")


with tempfile.TemporaryDirectory(prefix="event-window-tests-") as temp:
    # Remove the reader half of the handshake. A scheduled-but-nonparticipating
    # reader must not let the fixed number of writer rounds earn a pass.
    source = (FS / "tests/audio_publisher_test.c").read_text()
    old = "stressctx *c = arg;"
    assert source.count(old) == 1
    source = source.replace(old, "(void)arg; return NULL;\n    stressctx *c = arg;")
    for old, new in (("../audio_publisher.h", FS / "audio_publisher.h"),
                     ("../../test_supervisor.h", ROOT / "src/test_supervisor.h")):
        source = source.replace(f'"{old}"', f'"{new}"')
    mutant = Path(temp) / "audio.c"
    mutant.write_text(source)
    binary = Path(temp) / "audio"
    subprocess.run(["cc", "-O1", "-std=c11", str(mutant),
                    str(FS / "audio_publisher.c"), "-o", str(binary)], check=True)
    failure([str(binary)], {"AP_TEST_WAIT_S": ".2"},
            "seqlock stress missing reader/writer overlap")

fixture = ROOT / "src/unit_parser/tests"
command = [str(FS / "tests/frameserver_test"), str(fixture / "fixture.tpc"),
           str(fixture / "fixture_plain.tpc")]
failure(command, {"FS_TEST_CLEAN_WINDOW": "ended", "FS_TEST_WAIT_S": "2"},
        "rows in the clean log: session ended before required rows")
failure(command, {"FS_TEST_CLEAN_WINDOW": "paused", "FS_TEST_WAIT_S": "2"},
        ("FAIL: TIMEOUT: rows in the clean log",
         "FAIL: TIMEOUT: log window producer release after 40 rows"))

# A's 20 rows alone require >=2 seconds of injected work, while each item
# pauses only 0.1s. A one-second TOTAL wait fails; a one-second STALL wait passes.
start = time.monotonic()
run = subprocess.run(command, env={**os.environ, "FS_TEST_WAIT_S": "1",
                     "FS_TEST_ITEM_DELAY_US": "100000"}, text=True,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
elapsed = time.monotonic() - start
assert run.returncode == 0, (run.returncode, run.stdout)
assert "A 20 rows" in run.stdout and "B 75 rows" in run.stdout, run.stdout
assert elapsed > 2, elapsed
print(f"PASS: slow progressing windows, stall limit 1s, total {elapsed:.2f}s, exit 0")
