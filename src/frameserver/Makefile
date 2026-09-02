# frameserver: P3 assembly + IOSurface frame publisher. `make test` needs no hardware.
CC ?= clang
CFLAGS ?= -O2 -std=c11 -Wall -Wextra
CPPFLAGS ?= -I. -I../capture_core -I../unit_parser -I../signal_state -I../field_registration
LIBS = $(shell pkg-config --libs libusb-1.0) -lpthread -lm -framework IOSurface -framework CoreFoundation
CORE = ../capture_core/capture_core.c ../unit_parser/unit_parser.c ../signal_state/signal_state.c ../field_registration/field_registration.c
SRCS = frame_publisher.c frameserver.c $(CORE)
FIXTURE = ../unit_parser/tests/fixture.tpc

$(FIXTURE): ../unit_parser/tests/gen_unit_parser_capture.py
	python3 $< --output $@

frameserver_replay: $(SRCS) frameserver_replay.c frameserver.h frame_publisher.h
	$(CC) $(CPPFLAGS) $(CFLAGS) $(shell pkg-config --cflags libusb-1.0) $(SRCS) frameserver_replay.c -o $@ $(LIBS)

tests/frame_publisher_test: frame_publisher.c frame_publisher.h tests/frame_publisher_test.c
	$(CC) $(CPPFLAGS) $(CFLAGS) frame_publisher.c tests/frame_publisher_test.c -o $@ -framework IOSurface -framework CoreFoundation

tests/frameserver_test: $(SRCS) tests/frameserver_test.c frameserver.h
	$(CC) $(CPPFLAGS) $(CFLAGS) $(shell pkg-config --cflags libusb-1.0) $(SRCS) tests/frameserver_test.c -o $@ $(LIBS)

test: tests/frame_publisher_test tests/frameserver_test $(FIXTURE)
	./tests/frame_publisher_test
	./tests/frameserver_test $(FIXTURE)

test-asan: $(FIXTURE)
	$(CC) $(CPPFLAGS) -O1 -g -fsanitize=address,undefined -std=c11 -Wall -Wextra $(shell pkg-config --cflags libusb-1.0) $(SRCS) tests/frameserver_test.c -o tests/test_asan $(LIBS)
	./tests/test_asan $(FIXTURE)

test-tsan: $(FIXTURE)
	$(CC) $(CPPFLAGS) -O1 -g -fsanitize=thread -std=c11 -Wall -Wextra $(shell pkg-config --cflags libusb-1.0) $(SRCS) tests/frameserver_test.c -o tests/test_tsan $(LIBS)
	./tests/test_tsan $(FIXTURE)

clean:
	rm -f frameserver_replay tests/frame_publisher_test tests/frameserver_test tests/test_asan tests/test_tsan
