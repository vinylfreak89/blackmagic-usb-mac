CC ?= clang
CFLAGS ?= -O3 -std=c11 -Wall -Wextra -Werror
CPPFLAGS ?=
LDLIBS ?= -lm

.PHONY: all test clean

all: tests/field_registration_unit tests/field_registration_golden

tests/field_registration_unit: field_registration.c field_registration.h tests/field_registration_unit.c
	$(CC) $(CPPFLAGS) $(CFLAGS) field_registration.c tests/field_registration_unit.c -o $@ $(LDLIBS)

# The synthetic-truth golden runs whenever its harness is present (see tests/TRUTH.md).
TRUTH_SRC := $(wildcard tests/field_registration_truth.c)
TRUTH_DEPS := $(if $(TRUTH_SRC),tests/field_registration_truth tests/libfieldreg_truth.dylib tests/registration_truth.raw)

test: tests/field_registration_unit $(TRUTH_DEPS)
	./tests/field_registration_unit
	$(if $(TRUTH_SRC),./tests/field_registration_truth --library tests/libfieldreg_truth.dylib --raw tests/registration_truth.raw --truth tests/registration_truth.csv)

tests/field_registration_truth: field_registration.h tests/field_registration_truth.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -I. tests/field_registration_truth.c -o $@ $(LDLIBS)

tests/libfieldreg_truth.dylib: field_registration.c field_registration.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -dynamiclib field_registration.c -o $@ $(LDLIBS)

tests/registration_truth.raw: tests/gen_registration_units.py
	python3 tests/gen_registration_units.py --output $@ --truth tests/registration_truth.csv --seed 1380271924 --noise 1

tests/field_registration_golden: field_registration.c field_registration.h tests/field_registration_golden.c
	$(CC) $(CPPFLAGS) $(CFLAGS) field_registration.c tests/field_registration_golden.c -o $@ $(LDLIBS)

clean:
	rm -f tests/field_registration_unit tests/field_registration_golden tests/field_registration_truth tests/libfieldreg_truth.dylib tests/registration_truth.raw tests/registration_truth.csv
