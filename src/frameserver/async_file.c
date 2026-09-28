#define _DARWIN_C_SOURCE
#include "async_file.h"
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <pthread/qos.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

ssize_t (*fs_async_file_test_write)(int fd, const void *buf, size_t n) = NULL;

typedef struct {
    int fd; uint8_t *ring; size_t cap, chunk;
    _Atomic size_t head, tail;              /* monotonic byte counts: the stream publishes head, the writer tail */
    pthread_t thr; pthread_mutex_t m; pthread_cond_t cv; _Atomic int stop;
    int failed;                             /* stream side, sticky: an overflow refused a write */
    _Atomic int io_errno;                   /* writer side, sticky: first write(2) error */
} afile;

static void af_wake(afile *a){ pthread_mutex_lock(&a->m); pthread_cond_signal(&a->cv); pthread_mutex_unlock(&a->m); }

/* stdio serialises calls on one FILE, so this is the ring's single producer. */
static int af_write(void *cookie, const char *p, int n){
    afile *a = cookie;
    if (n <= 0) return 0;
    if (a->failed || atomic_load_explicit(&a->io_errno, memory_order_relaxed)){ errno = EIO; return -1; }
    size_t head = atomic_load_explicit(&a->head, memory_order_relaxed);
    size_t used = head - atomic_load_explicit(&a->tail, memory_order_acquire);
    if ((size_t)n > a->cap - used){ a->failed = 1; errno = ENOBUFS; return -1; }   /* never a partial copy */
    size_t o = head % a->cap, first = (size_t)n < a->cap - o ? (size_t)n : a->cap - o;
    memcpy(a->ring + o, p, first); if ((size_t)n > first) memcpy(a->ring, p + first, (size_t)n - first);
    atomic_store_explicit(&a->head, head + (size_t)n, memory_order_release);
    af_wake(a);
    return n;
}

static void *af_writer(void *arg){
    afile *a = arg;
    pthread_set_qos_class_self_np(QOS_CLASS_UTILITY, 0);
    for (;;){
        size_t tail = atomic_load_explicit(&a->tail, memory_order_relaxed);
        size_t avail = atomic_load_explicit(&a->head, memory_order_acquire) - tail;
        if (!avail){
            if (atomic_load(&a->stop)) break;
            pthread_mutex_lock(&a->m);
            if (atomic_load_explicit(&a->head, memory_order_acquire) == tail && !atomic_load(&a->stop)){
                struct timespec ts; clock_gettime(CLOCK_REALTIME, &ts); ts.tv_nsec += 100000000;
                if (ts.tv_nsec >= 1000000000){ ts.tv_sec++; ts.tv_nsec -= 1000000000; }
                pthread_cond_timedwait(&a->cv, &a->m, &ts);   /* liveness backstop only; the stream signals */
            }
            pthread_mutex_unlock(&a->m); continue;
        }
        size_t o = tail % a->cap, n = avail;
        if (n > a->cap - o) n = a->cap - o;
        if (n > a->chunk) n = a->chunk;
        size_t done = 0;
        while (!atomic_load_explicit(&a->io_errno, memory_order_relaxed) && done < n){
            ssize_t w = fs_async_file_test_write ? fs_async_file_test_write(a->fd, a->ring + o + done, n - done)
                                                 : write(a->fd, a->ring + o + done, n - done);
            if (w < 0 && errno == EINTR) continue;
            if (w <= 0){ atomic_store(&a->io_errno, w < 0 ? errno : EIO); break; }
            done += (size_t)w;
        }
        atomic_store_explicit(&a->tail, tail + n, memory_order_release);   /* after an error: discarded */
    }
    return NULL;
}

static void af_free(afile *a){ pthread_mutex_destroy(&a->m); pthread_cond_destroy(&a->cv); free(a->ring); free(a); }

static int af_close(void *cookie){
    afile *a = cookie;
    atomic_store(&a->stop, 1); af_wake(a); pthread_join(a->thr, NULL);
    int e = atomic_load(&a->io_errno);
    if (!e && fsync(a->fd) != 0) e = errno;
    if (close(a->fd) != 0 && !e) e = errno;
    int bad = a->failed || e;
    af_free(a);
    if (bad){ errno = e ? e : ENOBUFS; return -1; }
    return 0;
}

FILE *fs_async_fopen_excl(const char *path, size_t ring_bytes, size_t chunk){
    if (!path || ring_bytes < 4096 || !chunk){ errno = EINVAL; return NULL; }
    afile *a = calloc(1, sizeof *a); if (!a) return NULL;
    a->cap = ring_bytes; a->chunk = chunk; a->ring = malloc(ring_bytes);
    if (!a->ring){ free(a); errno = ENOMEM; return NULL; }
    pthread_mutex_init(&a->m, NULL); pthread_cond_init(&a->cv, NULL);
    a->fd = open(path, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, 0644);
    if (a->fd < 0){ int e = errno; af_free(a); errno = e; return NULL; }
    if (pthread_create(&a->thr, NULL, af_writer, a) != 0){
        close(a->fd); unlink(path); af_free(a); errno = EAGAIN; return NULL;
    }
    FILE *f = funopen(a, NULL, af_write, NULL, af_close);
    if (!f){ int e = errno; af_close(a); unlink(path); errno = e; return NULL; }
    setvbuf(f, NULL, _IOLBF, 1u << 16);   /* each finished row reaches the ring (and the writer) at once */
    return f;
}
