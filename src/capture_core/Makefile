# capture core + capture CLI. `make test` builds a synthetic fixture and runs the
# suite; `make check CAPTURE=<file.tpc>` replays a real capture through the library.
CC=clang
CFLAGS=-O2 -Wall $(shell pkg-config --cflags libusb-1.0)
LIBS=$(shell pkg-config --libs libusb-1.0) -lpthread
CAPTURE?=

shuttle-capture: capture_core.c capture_cli.c capture_core.h
	$(CC) $(CFLAGS) -o $@ capture_core.c capture_cli.c $(LIBS)

check: shuttle-capture
	@test -n "$(CAPTURE)" || { echo 'usage: make check CAPTURE=<capture.tpc>'; exit 2; }
	./shuttle-capture --replay $(CAPTURE) /dev/null

clean:
	rm -f shuttle-capture *.o
