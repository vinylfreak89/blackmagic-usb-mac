# frameserver: P3 assembly + IOSurface frame publisher. `make test` needs no hardware.
CC ?= clang
CFLAGS ?= -O2 -std=c11 -Wall -Wextra
TESTFLAGS = -DFRAMESERVER_TEST_HOOKS
CPPFLAGS ?= -I. -I../capture_core -I../unit_parser -I../signal_state -I../field_registration
LIBS = $(shell pkg-config --libs libusb-1.0) -lpthread -lm -framework IOSurface -framework CoreFoundation
CORE = ../capture_core/capture_core.c ../unit_parser/unit_parser.c ../signal_state/signal_state.c ../field_registration/field_registration.c
SRCS = frame_publisher.c audio_publisher.c frameserver.c $(CORE)
FIXTURE = ../unit_parser/tests/fixture.tpc
FIXTURE_LONG = ../unit_parser/tests/fixture_plain.tpc   # 120 exact units, for the runtime-log window test

$(FIXTURE): ../unit_parser/tests/gen_unit_parser_capture.py
	python3 $< --output $@

frameserver_replay: $(SRCS) frameserver_replay.c frameserver.h frame_publisher.h
	$(CC) $(CPPFLAGS) $(CFLAGS) $(shell pkg-config --cflags libusb-1.0) $(SRCS) frameserver_replay.c -o $@ $(LIBS)

tests/audio_publisher_test: audio_publisher.c audio_publisher.h tests/audio_publisher_test.c
	$(CC) $(CPPFLAGS) $(CFLAGS) audio_publisher.c tests/audio_publisher_test.c -o $@

tests/frame_publisher_test: frame_publisher.c frame_publisher.h tests/frame_publisher_test.c
	$(CC) $(CPPFLAGS) $(CFLAGS) frame_publisher.c tests/frame_publisher_test.c -o $@ -framework IOSurface -framework CoreFoundation

tests/frameserver_test: $(SRCS) tests/frameserver_test.c frameserver.h
	$(CC) $(CPPFLAGS) $(CFLAGS) $(TESTFLAGS) $(shell pkg-config --cflags libusb-1.0) $(SRCS) tests/frameserver_test.c -o $@ $(LIBS)

test: tests/audio_publisher_test tests/frame_publisher_test tests/frameserver_test $(FIXTURE) $(FIXTURE_LONG)
	./tests/audio_publisher_test
	./tests/frame_publisher_test
	./tests/frameserver_test $(FIXTURE) $(FIXTURE_LONG)

# Item ring of 2 so a stalled consumer exhausts it deterministically (ring-full accounting path).
test-smallring: $(FIXTURE) $(FIXTURE_LONG)
	$(CC) $(CPPFLAGS) -O1 -g -fsanitize=address,undefined -DRING_ITEMS=2 $(TESTFLAGS) -std=c11 -Wall -Wextra $(shell pkg-config --cflags libusb-1.0) $(SRCS) tests/frameserver_test.c -o tests/test_smallring $(LIBS)
	FS_TEST_EXPECT_RING_DROPS=1 ./tests/test_smallring $(FIXTURE) $(FIXTURE_LONG)

test-asan: $(FIXTURE) $(FIXTURE_LONG)
	$(CC) $(CPPFLAGS) -O1 -g -fsanitize=address,undefined $(TESTFLAGS) -std=c11 -Wall -Wextra $(shell pkg-config --cflags libusb-1.0) $(SRCS) tests/frameserver_test.c -o tests/test_asan $(LIBS)
	./tests/test_asan $(FIXTURE) $(FIXTURE_LONG)

test-tsan: $(FIXTURE) $(FIXTURE_LONG)
	$(CC) $(CPPFLAGS) -O1 -g -fsanitize=thread $(TESTFLAGS) -std=c11 -Wall -Wextra $(shell pkg-config --cflags libusb-1.0) $(SRCS) tests/frameserver_test.c -o tests/test_tsan $(LIBS)
	./tests/test_tsan $(FIXTURE) $(FIXTURE_LONG)

$(FIXTURE_LONG): ../unit_parser/tests/gen_unit_parser_capture.py
	$(MAKE) -C ../unit_parser tests/fixture_plain.tpc

clean:
	rm -f frameserver_replay tests/audio_publisher_test tests/frame_publisher_test tests/frameserver_test tests/test_asan tests/test_tsan tests/test_smallring
