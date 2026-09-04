CC ?= clang
CFLAGS ?= -O3 -std=c11 -Wall -Wextra -Werror
CPPFLAGS ?= -I. -I../unit_parser -I../capture_core
LDLIBS ?= -lm

.PHONY: all test test-asan test-tsan clean

all: libsignalstate.a libsignalstate.dylib

libsignalstate.a: signal_state.o
	ar rcs $@ $^

libsignalstate.dylib: signal_state.c signal_state.h ../unit_parser/unit_parser.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -fPIC -dynamiclib signal_state.c -o $@ $(LDLIBS)

signal_state.o: signal_state.c signal_state.h ../unit_parser/unit_parser.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -c signal_state.c -o $@

tests/signal_state_test: signal_state.c signal_state.h tests/signal_state_test.c
	$(CC) $(CPPFLAGS) $(CFLAGS) signal_state.c tests/signal_state_test.c -o $@ $(LDLIBS)

test: tests/signal_state_test
	./tests/signal_state_test

test-asan:
	$(CC) $(CPPFLAGS) -O1 -g -std=c11 -Wall -Wextra -Werror \
		-DSIGNAL_STATE_SANITIZED -fsanitize=address,undefined signal_state.c tests/signal_state_test.c \
		-o tests/signal_state_asan $(LDLIBS)
	./tests/signal_state_asan

test-tsan:
	$(CC) $(CPPFLAGS) -O1 -g -std=c11 -Wall -Wextra -Werror \
		-DSIGNAL_STATE_SANITIZED -fsanitize=thread signal_state.c tests/signal_state_test.c \
		-o tests/signal_state_tsan $(LDLIBS)
	./tests/signal_state_tsan

clean:
	rm -f signal_state.o libsignalstate.a libsignalstate.dylib tests/signal_state_test \
		tests/signal_state_asan tests/signal_state_tsan
