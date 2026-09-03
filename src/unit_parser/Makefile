CC ?= clang
CFLAGS ?= -O3 -std=c11 -Wall -Wextra -Werror
CPPFLAGS ?= -I. -I../capture_core

.PHONY: all test test-asan test-tsan clean

all: libunitparser.a

libunitparser.a: unit_parser.o
	ar rcs $@ $^

unit_parser.o: unit_parser.c unit_parser.h ../capture_core/capture_core.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -c unit_parser.c -o $@

tests/fixture.tpc: tests/gen_unit_parser_capture.py
	python3 $< --output $@

# 120 exact units (~91 MB, generated, ignored): long enough for windowed/runtime tests.
tests/fixture_plain.tpc: tests/gen_unit_parser_capture.py
	python3 $< --output $@ --plain-units 120

tests/unit_parser_test: unit_parser.c unit_parser.h tests/unit_parser_test.c
	$(CC) $(CPPFLAGS) $(CFLAGS) unit_parser.c tests/unit_parser_test.c -o $@

test: tests/unit_parser_test tests/fixture.tpc
	./tests/unit_parser_test tests/fixture.tpc

test-asan: tests/fixture.tpc
	$(CC) $(CPPFLAGS) -O1 -g -std=c11 -Wall -Wextra -Werror \
		-fsanitize=address,undefined unit_parser.c tests/unit_parser_test.c \
		-o tests/unit_parser_asan
	./tests/unit_parser_asan tests/fixture.tpc

test-tsan: tests/fixture.tpc
	$(CC) $(CPPFLAGS) -O1 -g -std=c11 -Wall -Wextra -Werror \
		-fsanitize=thread unit_parser.c tests/unit_parser_test.c \
		-o tests/unit_parser_tsan
	./tests/unit_parser_tsan tests/fixture.tpc

clean:
	rm -f unit_parser.o libunitparser.a tests/unit_parser_test \
		tests/unit_parser_asan tests/unit_parser_tsan tests/fixture.tpc tests/fixture_plain.tpc
