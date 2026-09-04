// publish_queue: a persistent publisher thread with a bounded FIFO of jobs, extracted from the OBS
// plugin so it can be tested without libobs. A job owns copies of both paths; the caller's strings
// may be freed right after pq_enqueue. Jobs run in order on the publisher thread through the
// caller's publish function (the plugin passes its rename/verified-copy publisher; tests pass a
// gated one). Final names of queued and in-progress jobs are RESERVED: pq_reserved() lets the
// caller avoid choosing a name a not-yet-published job already holds (filesystem existence alone
// cannot see it). The queue is bounded: pq_enqueue refuses (-1, ENOSPC) when full and the caller
// keeps its scratch file — nothing is dropped. pq_close drains every queued job, then joins.
#ifndef PUBLISH_QUEUE_H
#define PUBLISH_QUEUE_H
#include <stddef.h>
typedef struct publish_queue publish_queue;
typedef void (*pq_publish_fn)(void *ctx, const char *partial, const char *final);
// capacity: maximum queued (not yet started) jobs. Returns 0, or -1 with errno (thread/primitive creation failed; nothing allocated remains).
int  pq_open(publish_queue **out, size_t capacity, pq_publish_fn publish, void *ctx);
int  pq_enqueue(publish_queue *q, const char *partial, const char *final);   // 0, or -1 (ENOSPC when full, ECANCELED after pq_close began, ENOMEM)
int  pq_reserved(publish_queue *q, const char *final);                       // 1 if a queued or in-progress job targets `final`
size_t pq_pending(publish_queue *q);                                         // queued + in progress
// Two-phase shutdown, so the close can race producers safely:
//   pq_close   — may run concurrently with pq_enqueue. From the moment it begins every enqueue is
//                refused with ECANCELED (the caller keeps its scratch file); every job accepted
//                before that is published before pq_close returns; the thread is joined. The queue
//                object stays valid: late producers get ECANCELED, never a freed pointer.
//   pq_destroy — frees the object; the caller must know all producers have stopped using the
//                pointer (the plugin's destroy removes the frontend callback first). NULL-safe.
void pq_close(publish_queue *q);
void pq_destroy(publish_queue *q);
// Test hooks (weak): make pthread primitive/thread creation fail.
extern int (*pq_test_fail_init)(int which);   // which: 0 mutex, 1 condvar, 2 thread
#endif
