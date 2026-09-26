CC ?= clang
CFLAGS ?= -O3 -std=c11 -Wall -Wextra -Werror
CPPFLAGS ?=
LDLIBS ?= -lm

.PHONY: all test clean

all: tests/hblank_probe libcea608.dylib tests/cea608_unit

tests/hblank_probe: geometry_engine.c geometry_engine.h geometry_tool_controls.h tests/hblank_probe.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -I. geometry_engine.c tests/hblank_probe.c -o $@ $(LDLIBS)

tests/geometry_unit: geometry_engine.c geometry_engine.h tests/geometry_unit.c
	$(CC) $(CPPFLAGS) $(CFLAGS) geometry_engine.c tests/geometry_unit.c -o $@ $(LDLIBS)

.PHONY: geometry-test
tests/geometry_basis: geometry_engine.c geometry_engine.h tests/geometry_basis.c
	$(CC) $(CPPFLAGS) $(CFLAGS) tests/geometry_basis.c -o $@ $(LDLIBS)

tests/geometry_waveform: geometry_engine.c geometry_engine.h tests/geometry_waveform.c
	$(CC) $(CPPFLAGS) $(CFLAGS) geometry_engine.c tests/geometry_waveform.c -o $@ $(LDLIBS)

tests/geometry_rejection: geometry_engine.c geometry_engine.h tests/geometry_rejection.c
	$(CC) $(CPPFLAGS) $(CFLAGS) tests/geometry_rejection.c -o $@ $(LDLIBS)

tests/geometry_vote: geometry_engine.c geometry_engine.h tests/geometry_vote.c
	$(CC) $(CPPFLAGS) $(CFLAGS) tests/geometry_vote.c -o $@ $(LDLIBS)

tests/geometry_bottom: geometry_engine.c geometry_engine.h tests/geometry_bottom.c
	$(CC) $(CPPFLAGS) $(CFLAGS) tests/geometry_bottom.c -o $@ $(LDLIBS)

tests/geometry_still: geometry_engine.c geometry_engine.h tests/geometry_still.c
	$(CC) $(CPPFLAGS) $(CFLAGS) tests/geometry_still.c -o $@ $(LDLIBS)

tests/geometry_config: geometry_engine.c geometry_engine.h tests/geometry_config.c
	$(CC) $(CPPFLAGS) $(CFLAGS) tests/geometry_config.c -o $@ $(LDLIBS) -lpthread

geometry-test: tests/geometry_unit tests/geometry_basis tests/geometry_waveform tests/geometry_rejection tests/geometry_vote tests/geometry_bottom tests/geometry_still tests/geometry_config tests/hblank_probe
	./tests/geometry_unit
	./tests/geometry_basis
	./tests/geometry_waveform
	./tests/geometry_rejection
	./tests/geometry_vote
	./tests/geometry_bottom
	./tests/geometry_still
	./tests/geometry_config
	python3 ../../scripts/test_waveform_controls.py ./tests/hblank_probe

libcea608.dylib: cea608.c cea608.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -fPIC -dynamiclib cea608.c -o $@ $(LDLIBS)

tests/cea608_unit: cea608.c cea608.h tests/cea608_unit.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -I. cea608.c tests/cea608_unit.c -o $@ $(LDLIBS)

test: geometry-test tests/cea608_unit
	./tests/cea608_unit

clean:
	rm -f tests/hblank_probe tests/geometry_unit tests/geometry_basis tests/geometry_waveform tests/geometry_config
	rm -f tests/geometry_rejection tests/geometry_vote
	rm -f tests/geometry_bottom
	rm -f tests/geometry_still
	rm -f libcea608.dylib tests/cea608_unit
