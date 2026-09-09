/* Force enqueue AFTER the consumer's last empty check but BEFORE sleep.
 * The old trylock notification is lost while the consumer owns m. */
#define FRAMESERVER_TEST_HOOKS
#include "../frameserver.c"
#include <assert.h>
#include <errno.h>
#include <unistd.h>
#include <signal.h>
static _Atomic int armed=1, at_wait, release_wait, completed, result;
void fs_test_after_empty_snapshot(frameserver *f){(void)f;}
void fs_test_before_producer_done(frameserver *f){(void)f;}
void fs_test_after_log_row(frameserver *f,FILE *l){(void)f;(void)l;}
void fs_test_before_analysis_wait(frameserver *f){
    (void)f;
    if(atomic_exchange(&armed,0)){
        atomic_store(&at_wait,1);
        while(!atomic_load(&release_wait))usleep(100);
    }
}
void fs_test_after_analysis_wait(frameserver *f,int r){
    (void)f;
    if(!atomic_load(&completed)){atomic_store(&result,r);atomic_store(&completed,1);}
}
int main(int argc,char **argv){
    assert(argc==2);alarm(10);
    fs_config cfg={0};cfg.capture.replay_path=argv[1];
    frameserver *f=NULL;assert(!fs_open(&f,&cfg));
    f->start_gate=1;
    pthread_t t;assert(!pthread_create(&t,NULL,worker_main,f));
    while(!atomic_load(&at_wait))usleep(100);
    fs_item it={0};it.slot=-1;it.gap_only=1;
    assert(push(f,&it));atomic_store(&release_wait,1);
    while(!atomic_load(&completed))usleep(100);
    int timeout=atomic_load(&result)==ETIMEDOUT;
    atomic_store(&f->producer_done,1);assert(push(f,&it));
    assert(!pthread_join(t,NULL));fs_close(f);
    fprintf(stderr,"enqueue_between_empty_check_and_sleep: %s (wait result %d)\n",
            timeout?"FAIL":"PASS",atomic_load(&result));
    return timeout?1:0;
}
