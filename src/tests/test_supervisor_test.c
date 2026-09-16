/* Deterministic syscall-boundary test of the real supervisor loop, plus real exec.
 * Model the reported ordering: exit notice, non-reapable child, then SIGCHLD.
 * This tests lost-wakeup handling, not the prevalence of the kernel race. */
#include <assert.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/event.h>
#include <sys/wait.h>
#include <unistd.h>

static const char *mode;
static int phase, chld_registered, checks_before_ready;
static int simulated(void) { return strcmp(mode, "real") != 0; }
static pid_t probe_fork(void) { return simulated() ? 12345 : fork(); }
static int probe_kill(pid_t pid, int sig) {
    if (!simulated()) return kill(pid, sig);
    assert(pid == 12345 && sig == SIGKILL);
    return 0;
}
static pid_t probe_waitpid(pid_t pid, int *status, int options) {
    if (!simulated()) return waitpid(pid, status, options);
    assert(pid == 12345 && options == WNOHANG);
    if (phase < 2) { ++checks_before_ready; return 0; }
    assert(checks_before_ready == 2);
    *status = 37 << 8;
    return pid;
}
static int probe_kevent(int fd, const struct kevent *changes, int nc,
                        struct kevent *events, int ne, const struct timespec *timeout) {
    if (!simulated()) return kevent(fd, changes, nc, events, ne, timeout);
    if (nc) {
        for (int i=0; i<nc; ++i)
            if (changes[i].filter == EVFILT_SIGNAL && changes[i].ident == SIGCHLD)
                chld_registered = strcmp(mode, "omit-chld") != 0;
        return 0;
    }
    assert(ne == 1 && timeout != NULL);
    if (!strcmp(mode, "interrupt")) {
        raise(SIGTERM); errno = EINTR; return -1;
    }
    if (phase++ == 0) {
        /* Spurious/premature notice must not require the child to be reapable. */
        EV_SET(events,12345,EVFILT_PROC,EV_ONESHOT|EV_EOF,NOTE_EXIT,0,NULL);
        return 1;
    }
    if (!chld_registered) {
        fprintf(stderr,"FAIL: no registered wakeup after premature exit notice\n");
        exit(1);
    }
    EV_SET(events,SIGCHLD,EVFILT_SIGNAL,0,0,1,NULL);
    return 1;
}
#define fork probe_fork
#define kill probe_kill
#define waitpid probe_waitpid
#define kevent(...) probe_kevent(__VA_ARGS__)
#include "../test_supervisor.h"

int main(int argc, char **argv) {
    assert(argc == 2);
    mode = argv[1];
    test_supervise(argv,"SUPERVISOR_TEST_TOTAL_S","supervisor regression");
    return 37;
}
