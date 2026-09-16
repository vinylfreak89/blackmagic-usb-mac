/* Force completion during the last sleep with an expired stall deadline and a
 * stable packet count. Exercise the actual replay loop, not a copy of its predicate. */
#include "../frameserver.h"
#include <stdatomic.h>
#include <unistd.h>
static int opened(frameserver **f,const fs_config *c){ (void)c; *f=(frameserver *)1; return 0; }
static int started(frameserver *f){ (void)f; return 0; }
static int stopped(frameserver *f){ (void)f; return 0; }
static void closed(frameserver *f){ (void)f; }
static uint64_t packets(const frameserver *f){ (void)f; return 0; }
static void stats(const frameserver *f,fs_stats *s){ (void)f; *s=(fs_stats){0}; }
void replay_test_after_sleep(_Atomic int *ended){ atomic_store(ended,1); }
#define fs_open opened
#define fs_start started
#define fs_stop stopped
#define fs_close closed
#define fs_packets_delivered packets
#define fs_get_stats stats
#define REPLAY_TEST_HOOKS
#define main replay_main
#include "../frameserver_replay.c"
#undef main
int main(void){
    char *args[]={"replay_completion_test","unused","--stall-s","0.001",NULL};
    int rc=replay_main(4,args);
    if(rc==0) puts("PASS: completion during final sleep is not a stall");
    return rc;
}
