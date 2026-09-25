CC ?= clang
CFLAGS ?= -O3 -std=c11 -Wall -Wextra -Werror
CPPFLAGS ?=
LDLIBS ?= -lm

.PHONY: all test v9-test v9-fixture clean

all: libfieldreg.dylib tests/field_registration_unit tests/cea608_unit tests/field_registration_v9

tests/geometry_probe: geometry_engine.c geometry_engine.h tests/geometry_probe.c
	$(CC) $(CPPFLAGS) $(CFLAGS) geometry_engine.c tests/geometry_probe.c -o $@ $(LDLIBS)

tests/hblank_probe: geometry_engine.c geometry_engine.h geometry_tool_controls.h tests/hblank_probe.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -I. -DGE_HBLANK geometry_engine.c tests/hblank_probe.c -o $@ $(LDLIBS)

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

geometry-test: tests/geometry_unit tests/geometry_probe tests/geometry_basis tests/geometry_waveform tests/geometry_rejection tests/geometry_vote tests/hblank_probe
	./tests/geometry_unit
	./tests/geometry_basis
	./tests/geometry_waveform
	./tests/geometry_rejection
	./tests/geometry_vote
	python3 ../../scripts/test_waveform_controls.py ./tests/hblank_probe

libfieldreg.dylib: field_registration.c field_registration.h cea608.c cea608.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -fPIC -dynamiclib field_registration.c cea608.c -o $@ $(LDLIBS)

libcea608.dylib: cea608.c cea608.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -fPIC -dynamiclib cea608.c -o $@ $(LDLIBS)

tests/cea608_unit: cea608.c cea608.h tests/cea608_unit.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -I. cea608.c tests/cea608_unit.c -o $@ $(LDLIBS)

tests/field_registration_unit: field_registration.c field_registration.h cea608.c cea608.h tests/field_registration_unit.c
	$(CC) $(CPPFLAGS) $(CFLAGS) field_registration.c cea608.c tests/field_registration_unit.c -o $@ $(LDLIBS)

test: tests/field_registration_unit tests/cea608_unit tests/field_registration_v9 tests/registration_v9.raw tests/registration_v9.csv
	python3 tests/test_fixture_publication.py
	./tests/field_registration_unit
	./tests/cea608_unit
	./tests/field_registration_v9 tests/registration_v9.raw tests/registration_v9.csv

v9-test: tests/field_registration_v9 tests/registration_v9.raw tests/registration_v9.csv
	./tests/field_registration_v9 tests/registration_v9.raw tests/registration_v9.csv

tests/field_registration_v9: field_registration.c field_registration.h cea608.c cea608.h tests/field_registration_v9.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -I. field_registration.c cea608.c tests/field_registration_v9.c -o $@ $(LDLIBS)

# Shared prerequisite works with macOS make 3.81, without grouped targets.
v9-fixture:
	python3 tests/ensure_v9_fixture.py

tests/registration_v9.raw tests/registration_v9.csv: v9-fixture
	@test -f $@

clean:
	rm -f tests/hblank_probe tests/geometry_basis tests/geometry_guards tests/geometry_waveform
	rm -f tests/geometry_rejection tests/geometry_vote
	rm -f libfieldreg.dylib libcea608.dylib tests/field_registration_unit tests/cea608_unit tests/field_registration_v9 \
		tests/registration_v9.raw tests/registration_v9.csv tests/.registration_v9.complete
