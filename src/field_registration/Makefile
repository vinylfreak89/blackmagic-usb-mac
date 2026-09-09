CC ?= clang
CFLAGS ?= -O3 -std=c11 -Wall -Wextra -Werror
CPPFLAGS ?=
LDLIBS ?= -lm

.PHONY: all test legacy-trajectory-test retired-v9-test v10-rule1-test v10-rule3-test v10-rule4-test clean

all: libfieldreg.dylib tests/field_registration_unit tests/cea608_unit tests/field_registration_v10_rule1

libfieldreg.dylib: field_registration.c field_registration.h cea608.c cea608.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -fPIC -dynamiclib field_registration.c cea608.c -o $@ $(LDLIBS)

libcea608.dylib: cea608.c cea608.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -fPIC -dynamiclib cea608.c -o $@ $(LDLIBS)

tests/cea608_unit: cea608.c cea608.h tests/cea608_unit.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -I. cea608.c tests/cea608_unit.c -o $@ $(LDLIBS)

tests/field_registration_unit: field_registration.c field_registration.h cea608.c cea608.h tests/field_registration_unit.c
	$(CC) $(CPPFLAGS) $(CFLAGS) field_registration.c cea608.c tests/field_registration_unit.c -o $@ $(LDLIBS)

# The synthetic-truth golden runs whenever its harness is present (see tests/TRUTH.md).
TRUTH_SRC := $(wildcard tests/field_registration_truth.c)
TRUTH_DEPS := $(if $(TRUTH_SRC),tests/field_registration_truth tests/libfieldreg_truth.dylib tests/registration_truth.raw)

test: tests/field_registration_unit tests/cea608_unit tests/field_registration_v10_rule1 tests/registration_v10_rule1.raw tests/field_registration_v10_rule3 tests/registration_v10_rule3.raw tests/field_registration_v10_rule4 tests/registration_v10_rule4.raw tests/switch_timing_test tests/comb_test tests/unlocked_placement_test
	./tests/field_registration_unit
	./tests/cea608_unit
	./tests/field_registration_v10_rule1 tests/registration_v10_rule1.raw
	./tests/field_registration_v10_rule3 tests/registration_v10_rule3.raw
	./tests/field_registration_v10_rule4 tests/registration_v10_rule4.raw
	./tests/switch_timing_test
	./tests/comb_test
	./tests/unlocked_placement_test

tests/unlocked_placement_test: tests/unlocked_placement_test.c tests/comb_test.c field_registration.c field_registration.h cea608.c cea608.h
	$(CC) $(CPPFLAGS) $(CFLAGS) tests/unlocked_placement_test.c field_registration.c cea608.c -o $@ $(LDLIBS)

tests/comb_test: tests/comb_test.c field_registration.c field_registration.h cea608.c cea608.h
	$(CC) $(CPPFLAGS) $(CFLAGS) tests/comb_test.c field_registration.c cea608.c -o $@ $(LDLIBS)

tests/switch_timing_test: tests/switch_timing_test.c field_registration.c field_registration.h cea608.c cea608.h
	$(CC) $(CPPFLAGS) $(CFLAGS) tests/switch_timing_test.c cea608.c -o $@ $(LDLIBS)

legacy-trajectory-test: tests/field_registration_trajectory tests/registration_trajectory.raw
	./tests/field_registration_trajectory tests/registration_trajectory.raw tests/registration_trajectory.csv

retired-v9-test: tests/field_registration_v9 tests/registration_v9.raw
	./tests/field_registration_v9 tests/registration_v9.raw tests/registration_v9.csv

v10-rule1-test: tests/field_registration_v10_rule1 tests/registration_v10_rule1.raw
	./tests/field_registration_v10_rule1 tests/registration_v10_rule1.raw

v10-rule3-test: tests/field_registration_v10_rule3 tests/registration_v10_rule3.raw
	./tests/field_registration_v10_rule3 tests/registration_v10_rule3.raw

v10-rule4-test: tests/field_registration_v10_rule4 tests/registration_v10_rule4.raw
	./tests/field_registration_v10_rule4 tests/registration_v10_rule4.raw

tests/field_registration_v9: field_registration.c field_registration.h cea608.c cea608.h tests/field_registration_v9.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -I. field_registration.c cea608.c tests/field_registration_v9.c -o $@ $(LDLIBS)

tests/registration_v9.raw: tests/gen_v9_units.py
	python3 tests/gen_v9_units.py --output $@ --truth tests/registration_v9.csv

tests/field_registration_v10_rule1: field_registration.c field_registration.h cea608.c cea608.h tests/field_registration_v10_rule1.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -I. field_registration.c cea608.c tests/field_registration_v10_rule1.c -o $@ $(LDLIBS)

tests/registration_v10_rule1.raw: tests/gen_v10_rule1_units.py tests/gen_v9_units.py
	python3 tests/gen_v10_rule1_units.py --output $@

tests/field_registration_v10_rule3: field_registration.c field_registration.h cea608.c cea608.h tests/field_registration_v10_rule3.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -I. field_registration.c cea608.c tests/field_registration_v10_rule3.c -o $@ $(LDLIBS)

tests/registration_v10_rule3.raw: tests/gen_v10_rule3_units.py tests/gen_v9_units.py
	python3 tests/gen_v10_rule3_units.py --output $@

tests/field_registration_v10_rule4: field_registration.c field_registration.h cea608.c cea608.h tests/field_registration_v10_rule4.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -I. field_registration.c cea608.c tests/field_registration_v10_rule4.c -o $@ $(LDLIBS)

tests/registration_v10_rule4.raw: tests/gen_v10_rule4_units.py tests/gen_v10_rule3_units.py tests/gen_v9_units.py
	python3 tests/gen_v10_rule4_units.py --output $@

tests/field_registration_trajectory: field_registration.c field_registration.h cea608.c cea608.h tests/field_registration_trajectory.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -I. field_registration.c cea608.c tests/field_registration_trajectory.c -o $@ $(LDLIBS)

tests/registration_trajectory.raw: tests/gen_trajectory_units.py tests/gen_registration_units.py
	python3 tests/gen_trajectory_units.py --output $@ --truth tests/registration_trajectory.csv --seed 1414676810 --noise 1

tests/field_registration_truth: field_registration.h tests/field_registration_truth.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -I. tests/field_registration_truth.c -o $@ $(LDLIBS)

tests/libfieldreg_truth.dylib: field_registration.c field_registration.h cea608.c cea608.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -dynamiclib field_registration.c cea608.c -o $@ $(LDLIBS)

tests/registration_truth.raw: tests/gen_registration_units.py
	python3 tests/gen_registration_units.py --output $@ --truth tests/registration_truth.csv --seed 1380271924 --noise 1

tests/field_registration_golden: field_registration.c field_registration.h cea608.c cea608.h tests/field_registration_golden.c
	$(CC) $(CPPFLAGS) $(CFLAGS) field_registration.c cea608.c tests/field_registration_golden.c -o $@ $(LDLIBS)

clean:
	rm -f libfieldreg.dylib libcea608.dylib tests/field_registration_unit tests/field_registration_golden tests/cea608_unit \
		tests/field_registration_trajectory tests/registration_trajectory.raw \
		tests/registration_trajectory.csv tests/field_registration_v9 \
		tests/registration_v9.raw tests/registration_v9.csv \
		tests/field_registration_v10_rule1 tests/registration_v10_rule1.raw \
		tests/field_registration_v10_rule3 tests/registration_v10_rule3.raw \
		tests/field_registration_v10_rule4 tests/registration_v10_rule4.raw
	rm -f tests/switch_timing_test
