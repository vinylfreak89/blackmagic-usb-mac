/* CLI-only watchdog, never used by acquisition callbacks. A separate thread guards
 * blocking lifecycle and file operations. Streaming uses the core's packet counter.
 * Labels/deadlines share a mutex; there is no signal handler or asynchronous phase pair. */
#ifndef BM_TOOL_DEADLINE_H
#define BM_TOOL_DEADLINE_H
#include <fcntl.h>
#include <math.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
static pthread_mutex_t tool_deadline_mutex = PTHREAD_MUTEX_INITIALIZER;
static const char *tool_name, *tool_phase;
static double tool_expires;
static int tool_timeout_exit;
static double tool_clock(void){
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) _exit(2);
    return t.tv_sec + t.tv_nsec / 1e9;
}
static void tool_timeout(const char *phase){
    /* Best-effort named diagnostic, even if stderr itself is full. Never flush stdout,
     * acquire a FILE lock, run exit handlers or re-enter a wedged stop/close path. */
    int flags=fcntl(STDERR_FILENO,F_GETFL);
    if (flags>=0) (void)fcntl(STDERR_FILENO,F_SETFL,flags|O_NONBLOCK);
    (void)write(2,"FAIL: TIMEOUT: ",15);
    (void)write(2,tool_name,strlen(tool_name));
    (void)write(2,": ",2); (void)write(2,phase,strlen(phase)); (void)write(2,"\n",1);
    _exit(tool_timeout_exit);
}
static void tool_guard(const char *phase, double seconds){
    pthread_mutex_lock(&tool_deadline_mutex);
    tool_phase=phase; tool_expires=phase ? tool_clock()+seconds : 0;
    pthread_mutex_unlock(&tool_deadline_mutex);
}
static void *tool_watchdog(void *unused){
    (void)unused;
    for (;;) {
        pthread_mutex_lock(&tool_deadline_mutex);
        if (tool_phase && tool_clock()>=tool_expires) tool_timeout(tool_phase);
        pthread_mutex_unlock(&tool_deadline_mutex);
        usleep(10000);
    }
    return NULL;
}
static double tool_seconds(const char *value, double fallback){
    if (!value) return fallback;
    char *end; double n=strtod(value,&end);
    if (!*value || *end || !isfinite(n) || n<=0) {
        fprintf(stderr,"%s: timeout must be positive finite seconds: %s\n",tool_name,value);
        exit(9);
    }
    return n;
}
static void tool_deadline_start(const char *name, int timeout_exit){
    tool_name=name; tool_timeout_exit=timeout_exit;
    pthread_t thread;
    if (pthread_create(&thread,NULL,tool_watchdog,NULL)) {
        fprintf(stderr,"%s: cannot start deadline watchdog\n",name); exit(2);
    }
    pthread_detach(thread);
}
/* An explicitly paced replay may legitimately be silent between transfer boundaries. */
static double tool_stall_seconds(double requested, int pace_us){
    double paced=pace_us>0 ? 10.0*pace_us/1e6 : 0;
    return requested>paced ? requested : paced;
}
#endif
