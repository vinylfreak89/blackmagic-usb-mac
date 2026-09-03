# capture core + capture CLI. `make test` builds a synthetic fixture and runs the
# suite; `make check CAPTURE=<file.tpc>` replays a real capture through the library.
CC=clang
CFLAGS=-O2 -Wall $(shell pkg-config --cflags libusb-1.0)
TESTFLAGS=-DCAPTURE_CORE_TEST_HOOKS
LIBS=$(shell pkg-config --libs libusb-1.0) -lpthread
CAPTURE?=

shuttle-capture: capture_core.c capture_cli.c capture_core.h
	$(CC) $(CFLAGS) -o $@ capture_core.c capture_cli.c $(LIBS)

check: shuttle-capture
	@test -n "$(CAPTURE)" || { echo 'usage: make check CAPTURE=<capture.tpc>'; exit 2; }
	./shuttle-capture --replay $(CAPTURE) /dev/null

FIXTURE=fixture.tpc
META_FIXTURE=fixture_meta.tpc
META_EXHAUST_FIXTURE=fixture_meta_exhaust.tpc
EXPECT=$(shell cat fixture.expect 2>/dev/null)

$(FIXTURE): gen_packet_capture.py
	python3 gen_packet_capture.py --out $(FIXTURE) --expect fixture.expect --video-transfers 40 --audio-transfers 60 --short-every 97 --xfererr-at 7

$(META_FIXTURE): gen_packet_capture.py
	python3 gen_packet_capture.py --out $(META_FIXTURE) --expect fixture_meta.expect --video-transfers 40 --audio-transfers 60 --short-every 97 --xfererr-at 39

$(META_EXHAUST_FIXTURE): gen_packet_capture.py
	python3 gen_packet_capture.py --out $(META_EXHAUST_FIXTURE) --expect fixture_meta_exhaust.expect --video-transfers 40 --audio-transfers 60 --xfererr-at 39 --xfererr-burst 3000

test: capture_core_test $(FIXTURE) $(META_FIXTURE) $(META_EXHAUST_FIXTURE)
	./capture_core_test $(FIXTURE) $$(cat fixture.expect) $(META_FIXTURE) $(META_EXHAUST_FIXTURE) $$(cat fixture_meta_exhaust.expect)

test-tsan: capture_core.c capture_core_test.c capture_core.h $(FIXTURE) $(META_FIXTURE) $(META_EXHAUST_FIXTURE)
	$(CC) -O1 -g -fsanitize=thread $(CFLAGS) $(TESTFLAGS) -o test_tsan capture_core.c capture_core_test.c $(LIBS)
	./test_tsan $(FIXTURE) $$(cat fixture.expect) $(META_FIXTURE) $(META_EXHAUST_FIXTURE) $$(cat fixture_meta_exhaust.expect)

test-asan: capture_core.c capture_core_test.c capture_core.h $(FIXTURE) $(META_FIXTURE) $(META_EXHAUST_FIXTURE)
	$(CC) -O1 -g -fsanitize=address,undefined $(CFLAGS) $(TESTFLAGS) -o test_asan capture_core.c capture_core_test.c $(LIBS)
	./test_asan $(FIXTURE) $$(cat fixture.expect) $(META_FIXTURE) $(META_EXHAUST_FIXTURE) $$(cat fixture_meta_exhaust.expect)

capture_core_test: capture_core.c capture_core_test.c capture_core.h
	$(CC) $(CFLAGS) $(TESTFLAGS) -o $@ capture_core.c capture_core_test.c $(LIBS)

# Device backend against the replay shim (no libusb linked): init, fleet, resubmission,
# cancellation and teardown run as on hardware, with injected faults. ASan build.
SHIM=../../experiments/libusb_replay_shim.c
test-shim: capture_core.c capture_core_shim_test.c capture_core.h $(SHIM) $(FIXTURE)
	$(CC) -O1 -g -fsanitize=address,undefined $(CFLAGS) -o test_shim capture_core.c capture_core_shim_test.c $(SHIM) -lpthread
	./test_shim $(FIXTURE)

clean:
	rm -f shuttle-capture capture_core_test test_tsan test_asan test_shim *.o fixture.tpc fixture.expect fixture_meta.tpc fixture_meta.expect fixture_meta_exhaust.tpc fixture_meta_exhaust.expect
