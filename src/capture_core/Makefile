# capture core + capture CLI. `make test` builds a synthetic fixture and runs the
# suite; `make check CAPTURE=<file.tpc>` replays a real capture through the library.
CC=clang
CFLAGS=-O2 -Wall $(shell pkg-config --cflags libusb-1.0)
TESTFLAGS=-DCAPTURE_CORE_TEST_HOOKS
LIBS=$(shell pkg-config --libs libusb-1.0) -lpthread -framework CoreFoundation
CAPTURE?=

# IOUSBHost backend (cfg.usb_backend / --iousbhost): the Objective-C side and its frameworks.
IH_SRC=capture_iousbhost.m
IH_FLAGS=-DCC_WITH_IOUSBHOST -fobjc-arc
IH_LIBS=-framework Foundation -framework IOKit -framework IOUSBHost

shuttle-capture: capture_core.c capture_cli.c capture_core.h capture_iousbhost.h $(IH_SRC) ../tool_deadline.h
	$(CC) $(CFLAGS) $(IH_FLAGS) -o $@ capture_core.c $(IH_SRC) capture_cli.c $(LIBS) $(IH_LIBS)

# Measurement build only: CC_DEBUG_HOLD_AT/MS hold the USB event thread (libusb) or completion queue (IOUSBHost)
# once (unread-slot census). Never installed.
shuttle-capture-hold: capture_core.c capture_cli.c capture_core.h capture_iousbhost.h $(IH_SRC) ../tool_deadline.h
	$(CC) $(CFLAGS) $(IH_FLAGS) -DCC_DEBUG_HOLD -o $@ capture_core.c $(IH_SRC) capture_cli.c $(LIBS) $(IH_LIBS)

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

async_sink_test: capture_core.c async_sink_test.c capture_core.h
	$(CC) -O1 -g -fsanitize=address,undefined $(CFLAGS) -o $@ capture_core.c async_sink_test.c $(LIBS)

# measurement tool, not part of `test`: async_sink_bench PATH SECONDS utility|user BUSY_THREADS
async_sink_bench: capture_core.c async_sink_bench.c capture_core.h
	$(CC) -O2 $(CFLAGS) -o $@ capture_core.c async_sink_bench.c $(LIBS)

test: capture_core_test async_sink_test $(FIXTURE) $(META_FIXTURE) $(META_EXHAUST_FIXTURE)
	./async_sink_test
	./capture_core_test $(FIXTURE) $$(cat fixture.expect) $(META_FIXTURE) $(META_EXHAUST_FIXTURE) $$(cat fixture_meta_exhaust.expect)

test-tsan: capture_core.c capture_core_test.c capture_core.h $(FIXTURE) $(META_FIXTURE) $(META_EXHAUST_FIXTURE)
	$(CC) -O1 -g -fsanitize=thread $(CFLAGS) $(TESTFLAGS) -o test_tsan capture_core.c capture_core_test.c $(LIBS)
	./test_tsan $(FIXTURE) $$(cat fixture.expect) $(META_FIXTURE) $(META_EXHAUST_FIXTURE) $$(cat fixture_meta_exhaust.expect)

test-asan: capture_core.c capture_core_test.c capture_core.h $(FIXTURE) $(META_FIXTURE) $(META_EXHAUST_FIXTURE)
	$(CC) -O1 -g -fsanitize=address,undefined $(CFLAGS) $(TESTFLAGS) -o test_asan capture_core.c capture_core_test.c $(LIBS)
	./test_asan $(FIXTURE) $$(cat fixture.expect) $(META_FIXTURE) $(META_EXHAUST_FIXTURE) $$(cat fixture_meta_exhaust.expect)

# Both test deadlines fail by name.
test-deadlines: shuttle-capture capture_core_test test_shim $(FIXTURE) $(META_FIXTURE) $(META_EXHAUST_FIXTURE)
	python3 ../../scripts/test_supervisor_test.py
	sh deadline_test.sh
	python3 ../../scripts/transport_deadline_test.py capture ./shuttle-capture

.PHONY: test-supervisor
test-supervisor:
	python3 ../../scripts/test_supervisor_test.py

capture_core_test: capture_core.c capture_core_test.c capture_core.h ../test_supervisor.h ../test_liveness.h ../test_condition.h
	$(CC) $(CFLAGS) $(TESTFLAGS) -o $@ capture_core.c capture_core_test.c $(LIBS)

# Device backend against the replay shim (no libusb linked): init, fleet, resubmission,
# cancellation and teardown run as on hardware, with injected faults. ASan build.
SHIM=../../experiments/libusb_replay_shim.c
test_shim: capture_core.c capture_core_shim_test.c capture_core.h $(SHIM) ../test_supervisor.h
	$(CC) -O1 -g -fsanitize=address,undefined $(CFLAGS) -o test_shim capture_core.c capture_core_shim_test.c $(SHIM) -lpthread -framework CoreFoundation
SCHED_FIXTURE=fixture_sched.tpc
$(SCHED_FIXTURE): gen_packet_capture.py
	python3 gen_packet_capture.py --out $(SCHED_FIXTURE) --expect fixture_sched.expect --video-transfers 250 --audio-transfers 400 --bus-interleave
test-shim: test_shim $(FIXTURE) $(SCHED_FIXTURE)
	./test_shim $(FIXTURE) $(SCHED_FIXTURE)

# capture_core's IOUSBHost glue against a scripted mock of the ih_* interface (no device), under TSan.
test-iousbhost: capture_core.c capture_core_ih_test.c capture_iousbhost_mock.c capture_iousbhost_mock.h capture_iousbhost.h capture_core.h
	$(CC) -O1 -g -fsanitize=thread $(CFLAGS) -DCC_WITH_IOUSBHOST -o test_ih capture_core.c capture_iousbhost_mock.c capture_core_ih_test.c $(LIBS)
	./test_ih

clean:
	rm -f shuttle-capture shuttle-capture-hold test_ih capture_core_test test_tsan test_asan test_shim *.o fixture.tpc fixture.expect fixture_meta.tpc fixture_meta.expect fixture_meta_exhaust.tpc fixture_meta_exhaust.expect fixture_sched.tpc fixture_sched.expect
