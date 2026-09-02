# frameserver delivery edge: IOSurface frame publisher. `make test` needs no hardware.
CC=clang
CFLAGS=-O2 -Wall -Wextra
FRAMEWORKS=-framework IOSurface -framework CoreFoundation

tests/frame_publisher_test: frame_publisher.c frame_publisher.h tests/frame_publisher_test.c
	$(CC) $(CFLAGS) frame_publisher.c tests/frame_publisher_test.c -o $@ $(FRAMEWORKS)

test: tests/frame_publisher_test
	./tests/frame_publisher_test

test-asan: frame_publisher.c frame_publisher.h tests/frame_publisher_test.c
	$(CC) -O1 -g -fsanitize=address,undefined $(CFLAGS) frame_publisher.c tests/frame_publisher_test.c -o tests/test_asan $(FRAMEWORKS)
	./tests/test_asan

clean:
	rm -f tests/frame_publisher_test tests/test_asan
