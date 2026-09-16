/* Test-only process supervisor. Call before starting threads or opening resources.
 * The child execs a fresh copy; its alarm/signal disposition cannot cancel the parent's
 * monotonic deadline. No signal-handler logging, shared phase pointers or test-thread joins.
 * Direct invocations and make/sanitizer targets have the same whole-run protection. */
#ifndef BM_TEST_SUPERVISOR_H
#define BM_TEST_SUPERVISOR_H
#include <errno.h>
#include <math.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/event.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t test_interrupted;
static void test_interrupt(int sig){ test_interrupted = sig; }
static double test_clock(void){
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) { perror("test clock"); _exit(2); }
    return t.tv_sec + t.tv_nsec / 1e9;
}
static void test_supervise(char **argv, const char *setting, const char *name){
    const char *child = getenv("BM_TEST_PARENT");
    if (child && strtol(child, NULL, 10) == (long)getppid()) {
        unsetenv("BM_TEST_PARENT");
        return;
    }
    const char *value = getenv(setting);
    char *end = NULL;
    double seconds = value ? strtod(value, &end) : 600;
    if (!isfinite(seconds) || seconds <= 0 || (value && (!*value || *end))) {
        fprintf(stderr, "FAIL: invalid %s (positive finite seconds required)\n", setting);
        exit(2);
    }
    struct sigaction action = {0};
    action.sa_handler = test_interrupt; sigemptyset(&action.sa_mask);
    sigaction(SIGINT, &action, NULL); sigaction(SIGTERM, &action, NULL);
    int queue=kqueue(), gate[2];
    if (queue<0 || pipe(gate)) { perror("test supervisor event setup"); exit(2); }
    struct kevent events[2];
    EV_SET(&events[0],SIGINT,EVFILT_SIGNAL,EV_ADD,0,0,NULL);
    EV_SET(&events[1],SIGTERM,EVFILT_SIGNAL,EV_ADD,0,0,NULL);
    if (kevent(queue,events,2,NULL,0,NULL)<0) { perror("test supervisor signals"); exit(2); }
    double deadline = test_clock() + seconds;
    pid_t pid = fork();
    if (pid < 0) { perror("test supervisor fork"); exit(2); }
    if (!pid) {
        close(queue); close(gate[1]);
        /* Parent registers NOTE_EXIT before permitting even a fast child to exit. */
        char token;
        ssize_t n;
        do { n=read(gate[0],&token,1); } while(n<0 && errno==EINTR);
        close(gate[0]);
        if(n<0) _exit(2);
        char parent[32]; snprintf(parent, sizeof parent, "%ld", (long)getppid());
        if (setenv("BM_TEST_PARENT", parent, 1)) _exit(2);
        execvp(argv[0], argv);
        perror("test supervisor exec"); _exit(2);
    }
    close(gate[0]);
    EV_SET(&events[0],pid,EVFILT_PROC,EV_ADD,NOTE_EXIT,0,NULL);
    if (kevent(queue,events,1,NULL,0,NULL)<0) {
        perror("test supervisor NOTE_EXIT"); kill(pid,SIGKILL); close(gate[1]); exit(2);
    }
    close(gate[1]);
    for (;;) {
        int status;
        pid_t result = waitpid(pid, &status, WNOHANG);
        if (result == pid) {
            if (WIFEXITED(status)) exit(WEXITSTATUS(status));
            fprintf(stderr, "FAIL: %s terminated by signal %d\n", name, WTERMSIG(status));
            exit(128 + WTERMSIG(status));
        }
        if (result < 0 && errno != EINTR) {
            perror("test supervisor waitpid"); kill(pid, SIGKILL); exit(2);
        }
        double remaining=deadline-test_clock();
        if (test_interrupted || remaining<=0) {
            /* Kill before reporting: blocked child I/O/cleanup must not delay termination. */
            kill(pid, SIGKILL);
            fprintf(stderr, "FAIL: TIMEOUT/INTERRUPTED: %s whole-run deadline (%s=%.3g s); "
                            "includes startup, callbacks, waits, joins, stop and close\n",
                    name, setting, seconds);
            /* Do not introduce an unbounded reap after the deadline. */
            (void)waitpid(pid, &status, WNOHANG);
            exit(test_interrupted ? 128 + test_interrupted : 2);
        }
        struct timespec timeout={(time_t)remaining,(long)((remaining-(time_t)remaining)*1e9)};
        struct kevent event;
        if (kevent(queue,NULL,0,&event,1,&timeout)<0 && errno!=EINTR) {
            perror("test supervisor kevent"); kill(pid,SIGKILL); exit(2);
        }
    }
}
#endif
