/* Measurement, not a test: feed cc_async_sink at the device's rate for a while and report how its writer kept up.
 *   async_sink_bench PATH SECONDS utility|user BUSY_THREADS
 * PATH is created (must not exist) and left for the caller to delete. BUSY_THREADS spin at user-initiated QoS to
 * load the machine. Ring and chunk match the OBS source's raw tee (256 MiB, 1 MiB). */
#include "capture_core.h"
#include <pthread.h>
#include <pthread/qos.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static _Atomic int stop;
static void *busy(void *arg){
    (void)arg; pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED,0);
    volatile double x=1; while(!atomic_load(&stop)) for(int i=0;i<100000;i++) x=x*1.0000001+1e-9;
    return NULL;
}
int main(int argc,char **argv){
    if(argc!=5){ fprintf(stderr,"usage: %s PATH SECONDS utility|user BUSY_THREADS\n",argv[0]); return 2; }
    int seconds=atoi(argv[2]), nbusy=atoi(argv[4]);
    cc_async_sink_writer_qos=strcmp(argv[3],"user")?QOS_CLASS_UTILITY:QOS_CLASS_USER_INITIATED;
    pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED,0);       /* the capture delivery thread's class */
    cc_async_sink *k; cc_callbacks cb;
    if(cc_async_sink_open(&k,argv[1],"async_sink_bench",256u<<20,1u<<20)!=CC_OK){ perror("open"); return 1; }
    cc_async_sink_callbacks(k,&cb);
    pthread_t th[64]; if(nbusy>64) nbusy=64;
    for(int i=0;i<nbusy;i++) pthread_create(&th[i],NULL,busy,NULL);
    static uint8_t video[2848], audio[144];
    for(size_t i=0;i<sizeof video;i++) video[i]=(uint8_t)(i*31);
    uint64_t t0=clock_gettime_nsec_np(CLOCK_MONOTONIC_RAW); uint32_t seq=0; uint64_t late=0;
    for(uint64_t ms=0; ms<(uint64_t)seconds*1000; ms++){
        uint64_t due=t0+ms*1000000ull, now=clock_gettime_nsec_np(CLOCK_MONOTONIC_RAW);
        if(now<due){ struct timespec d={0,(long)(due-now)}; nanosleep(&d,NULL); } else if(now-due>50000000ull) late++;
        for(int i=0;i<8;i++){
            cc_packet v={CC_EP_VIDEO,(uint16_t)i,seq,0,15360,sizeof video,video}; cb.on_packet(cb.ctx,&v);
            cc_packet a={CC_EP_AUDIO,(uint16_t)i,seq,0,2048,sizeof audio,audio}; cb.on_packet(cb.ctx,&a);
        }
        seq++; if(ms%1000==0) cb.on_tick(cb.ctx,(uint32_t)ms);
    }
    uint64_t t1=clock_gettime_nsec_np(CLOCK_MONOTONIC_RAW);
    atomic_store(&stop,1); for(int i=0;i<nbusy;i++) pthread_join(th[i],NULL);
    cc_async_sink_stats st; int rc=cc_async_sink_close(k,&st);
    printf("%s writer, %d busy threads, %.1f s fed (%llu ms more than 50 ms late): rc %d | lost video %llu pkts audio %llu pkts | ring peak %.1f MB | "
           "%llu writes, mean %.2f ms, longest %.1f ms, %llu over 100 ms | longest wait between writes with data ready %.1f ms | "
           "loss episodes %llu, writer inside a write at %llu of them (longest %.1f ms) | close took %.1f s\n",
           argv[3],nbusy,(t1-t0)/1e9,(unsigned long long)late,rc,(unsigned long long)st.lost_packets[0],(unsigned long long)st.lost_packets[1],st.high_water/1e6,
           (unsigned long long)st.writes,st.writes?st.write_ns/1e6/(double)st.writes:0.0,st.max_write_ns/1e6,(unsigned long long)st.slow_writes,st.max_ready_gap_ns/1e6,
           (unsigned long long)st.loss_episodes,(unsigned long long)st.loss_in_write,st.max_in_write_at_loss_ns/1e6,(clock_gettime_nsec_np(CLOCK_MONOTONIC_RAW)-t1)/1e9);
    return 0;
}
