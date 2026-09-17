# frameserver: P3 assembly + IOSurface frame publisher. `make test` needs no hardware.
CC ?= clang
CFLAGS ?= -O2 -std=c11 -Wall -Wextra
TESTFLAGS = -DFRAMESERVER_TEST_HOOKS
CPPFLAGS ?= -I. -I../capture_core -I../unit_parser -I../signal_state -I../field_registration
LIBS = $(shell pkg-config --libs libusb-1.0) -lpthread -lm -framework IOSurface -framework CoreFoundation
CORE = ../capture_core/capture_core.c ../unit_parser/unit_parser.c ../signal_state/signal_state.c ../field_registration/field_registration.c ../field_registration/cea608.c
SRCS = frame_publisher.c audio_publisher.c frameserver.c $(CORE)
FIXTURE = ../unit_parser/tests/fixture.tpc
FIXTURE_LONG = ../unit_parser/tests/fixture_plain.tpc   # 120 exact units, for the runtime-log window test

$(FIXTURE): ../unit_parser/tests/gen_unit_parser_capture.py
	python3 $< --output $@

frameserver_replay: $(SRCS) frameserver_replay.c frameserver.h frame_publisher.h ../capture_core/capture_core.h ../tool_deadline.h
	$(CC) $(CPPFLAGS) $(CFLAGS) $(shell pkg-config --cflags libusb-1.0) $(SRCS) frameserver_replay.c -o $@ $(LIBS)

tests/audio_publisher_test: audio_publisher.c audio_publisher.h tests/audio_publisher_test.c ../test_supervisor.h
	$(CC) $(CPPFLAGS) $(CFLAGS) audio_publisher.c tests/audio_publisher_test.c -o $@

tests/frame_publisher_test: frame_publisher.c frame_publisher.h tests/frame_publisher_test.c
	$(CC) $(CPPFLAGS) $(CFLAGS) frame_publisher.c tests/frame_publisher_test.c -o $@ -framework IOSurface -framework CoreFoundation

tests/frameserver_test: $(SRCS) tests/frameserver_test.c frameserver.h ../test_supervisor.h ../test_condition.h
	$(CC) $(CPPFLAGS) $(CFLAGS) $(TESTFLAGS) $(shell pkg-config --cflags libusb-1.0) $(SRCS) tests/frameserver_test.c -o $@ $(LIBS)

test: tests/audio_publisher_test tests/frame_publisher_test tests/frameserver_test $(FIXTURE) $(FIXTURE_LONG)
	./tests/audio_publisher_test
	./tests/frame_publisher_test
	./tests/frameserver_test $(FIXTURE) $(FIXTURE_LONG)

# Deadline behaviour: slow pacing is not a stall, a blocked sink is, and both test deadlines fail by name.
test-deadlines: frameserver_replay tests/frameserver_test tests/replay_completion_test $(FIXTURE) $(FIXTURE_LONG)
	python3 ../../scripts/test_supervisor_test.py
	sh tests/deadline_test.sh
	python3 ../../scripts/transport_deadline_test.py frameserver ./frameserver_replay
	python3 ../../scripts/run_deadline.py 5 ./tests/replay_completion_test
	python3 ../../scripts/test_event_windows.py

.PHONY: test-supervisor
test-supervisor:
	python3 ../../scripts/test_supervisor_test.py

tests/replay_completion_test: $(SRCS) tests/replay_completion_test.c frameserver_replay.c ../tool_deadline.h
	$(CC) $(CPPFLAGS) $(CFLAGS) $(shell pkg-config --cflags libusb-1.0) $(SRCS) tests/replay_completion_test.c -o $@ $(LIBS)

# Item ring of 2 so a stalled consumer exhausts it deterministically (ring-full accounting path).
test-smallring: $(FIXTURE) $(FIXTURE_LONG)
	$(CC) $(CPPFLAGS) -O1 -g -fsanitize=address,undefined -DRING_ITEMS=2 $(TESTFLAGS) -std=c11 -Wall -Wextra $(shell pkg-config --cflags libusb-1.0) $(SRCS) tests/frameserver_test.c -o tests/test_smallring $(LIBS)
	FS_TEST_EXPECT_RING_DROPS=1 ./tests/test_smallring $(FIXTURE) $(FIXTURE_LONG)

test-asan: $(FIXTURE) $(FIXTURE_LONG)
	$(CC) $(CPPFLAGS) -O1 -g -fsanitize=address,undefined -std=c11 -Wall -Wextra audio_publisher.c tests/audio_publisher_test.c -o tests/audio_publisher_asan
	./tests/audio_publisher_asan
	$(CC) $(CPPFLAGS) -O1 -g -fsanitize=address,undefined $(TESTFLAGS) -std=c11 -Wall -Wextra $(shell pkg-config --cflags libusb-1.0) $(SRCS) tests/frameserver_test.c -o tests/test_asan $(LIBS)
	./tests/test_asan $(FIXTURE) $(FIXTURE_LONG)

test-tsan: $(FIXTURE) $(FIXTURE_LONG)
	$(CC) $(CPPFLAGS) -O1 -g -fsanitize=thread -std=c11 -Wall -Wextra audio_publisher.c tests/audio_publisher_test.c -o tests/audio_publisher_tsan
	./tests/audio_publisher_tsan
	$(CC) $(CPPFLAGS) -O1 -g -fsanitize=thread $(TESTFLAGS) -std=c11 -Wall -Wextra $(shell pkg-config --cflags libusb-1.0) $(SRCS) tests/frameserver_test.c -o tests/test_tsan $(LIBS)
	./tests/test_tsan $(FIXTURE) $(FIXTURE_LONG)

../field_registration/tests/registration_v9.raw:
	$(MAKE) -C ../field_registration tests/registration_v9.raw

tests/worker_bench: tests/worker_bench.c frame_publisher.c frame_publisher.h ../signal_state/signal_state.c ../field_registration/field_registration.c ../field_registration/cea608.c
	$(CC) $(CPPFLAGS) -O3 -std=c11 -Wall -Wextra tests/worker_bench.c frame_publisher.c ../signal_state/signal_state.c ../field_registration/field_registration.c ../field_registration/cea608.c -o $@ -lm -framework IOSurface -framework CoreFoundation

bench: tests/worker_bench ../field_registration/tests/registration_v9.raw
	./tests/worker_bench ../field_registration/tests/registration_v9.raw

$(FIXTURE_LONG): ../unit_parser/tests/gen_unit_parser_capture.py
	$(MAKE) -C ../unit_parser tests/fixture_plain.tpc

clean:
	rm -f tests/audio_publisher_asan tests/audio_publisher_tsan
	rm -f frameserver_replay tests/audio_publisher_test tests/frame_publisher_test tests/frameserver_test tests/test_asan tests/test_tsan tests/test_smallring tests/worker_bench
