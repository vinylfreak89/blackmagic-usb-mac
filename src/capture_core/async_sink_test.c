/* Deciding tests for cc_async_sink: byte-identical to the synchronous tagged sink for the same
 * callback sequence; a stalled writer loses packets with exact HostLoss confession and never
 * blocks the producer; writes never exceed the chunk; a failed write is reported; an existing
 * destination is refused. */
#include "capture_core.h"
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
static uint8_t payload[20000];
static size_t max_seen;
static _Atomic int gate_open=1;
static ssize_t gated_write(int fd,const void *b,size_t n){
    while(!atomic_load(&gate_open)){ struct timespec t={0,1000000}; nanosleep(&t,NULL); }
    if(n>max_seen) max_seen=n;
    return write(fd,b,n>3000?3000:n);   /* short writes too */
}
static ssize_t failing_write(int fd,const void *b,size_t n){ (void)fd;(void)b;(void)n; errno=EIO; return -1; }
static void feed(cc_callbacks *cb,int n,unsigned seed){
    srand(seed);
    for(int i=0;i<n;i++){
        uint8_t ep=i%3?CC_EP_VIDEO:CC_EP_AUDIO; uint32_t len=ep==CC_EP_VIDEO?15360:192;
        if(i%50==7) len=0;
        cc_packet p={ep,(uint16_t)(i%128),(uint32_t)(i/128),0,ep==CC_EP_VIDEO?15360:192,len,payload};
        payload[0]=(uint8_t)i; cb->on_packet(cb->ctx,&p);
        if(i==100) cb->on_loss(cb->ctx,CC_EP_VIDEO,3,46080);
        if(i==200) cb->on_error(cb->ctx,CC_EP_AUDIO,9,-1,CC_ERROR_TRANSFER);
        if(i%500==0) cb->on_tick(cb->ctx,(uint32_t)i);
    }
}
static int same_file(const char *a,const char *b){
    FILE *x=fopen(a,"rb"),*y=fopen(b,"rb"); int ca,cb2;
    do{ ca=fgetc(x); cb2=fgetc(y); }while(ca==cb2 && ca!=EOF);
    fclose(x); fclose(y); return ca==cb2;
}
int main(void){
    for(size_t i=0;i<sizeof payload;i++) payload[i]=(uint8_t)(i*7);
    char dir[]="/tmp/async_sink_XXXXXX"; assert(mkdtemp(dir));
    char a[256],b[256],c[256]; snprintf(a,sizeof a,"%s/sync.tpc",dir); snprintf(b,sizeof b,"%s/async.tpc",dir); snprintf(c,sizeof c,"%s/stall.tpc",dir);
    /* 1. same callbacks -> byte-identical file; writes bounded by the chunk */
    cc_tagged_sink *ts; cc_callbacks cs; assert(cc_tagged_sink_open(&ts,a,"note v1")==CC_OK); cc_tagged_sink_callbacks(ts,&cs);
    feed(&cs,5000,1); assert(cc_tagged_sink_close(ts)==CC_OK);
    cc_async_sink *as; cc_callbacks ca; cc_async_sink_test_write=gated_write;
    assert(cc_async_sink_open(&as,b,"note v1",64u<<20,65536)==CC_OK); cc_async_sink_callbacks(as,&ca);
    feed(&ca,5000,1); cc_async_sink_stats st; assert(cc_async_sink_close(as,&st)==CC_OK);
    assert(same_file(a,b)); assert(max_seen<=65536 && st.max_write<=65536);
    assert(!st.lost_packets[0] && !st.lost_packets[1] && !st.io_error);
    /* 2. existing destination refused */
    assert(cc_async_sink_open(&as,b,"x",1u<<20,65536)==CC_ERR_IO);
    /* 3. stalled writer: the producer never blocks; drops are exactly confessed */
    atomic_store(&gate_open,0);
    assert(cc_async_sink_open(&as,c,"stall",1u<<20,65536)==CC_OK); cc_async_sink_callbacks(as,&ca);
    struct timespec t0,t1; clock_gettime(CLOCK_MONOTONIC,&t0);
    feed(&ca,3000,2);                              /* ~31 MB into a 1 MB ring with the writer stuck */
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms=(t1.tv_sec-t0.tv_sec)*1e3+(t1.tv_nsec-t0.tv_nsec)/1e6; assert(ms<2000);
    atomic_store(&gate_open,1);
    { cc_packet p={CC_EP_VIDEO,0,999,0,15360,15360,payload}; ca.on_packet(ca.ctx,&p);   /* resumes: confession first */
      cc_packet q={CC_EP_AUDIO,0,999,0,192,192,payload};
      for(int i=0;i<200 && !(i && 0);i++){ struct timespec d={0,5000000}; nanosleep(&d,NULL); }
      ca.on_packet(ca.ctx,&q); ca.on_packet(ca.ctx,&p); }
    assert(cc_async_sink_close(as,&st)==CC_OK);
    assert(st.lost_packets[0]>0 && st.lost_packets[1]>0);
    /* read back: sum HostLoss per endpoint == sink-counted loss + the forwarded capture loss */
    FILE *f=fopen(c,"rb"); uint64_t loss_pk[2]={0},loss_by[2]={0},data[2]={0};
    struct { uint32_t magic; uint8_t type,ep; uint16_t pi; uint32_t seq,st,req,al; } h;
    while(fread(&h,1,24,f)==24){
        assert(h.magic==0x31504143u);
        int e=h.ep==CC_EP_AUDIO;
        if(h.type==1){ loss_pk[e]+=h.req; loss_by[e]+=h.al; }
        if(h.type==0){ data[e]++; fseek(f,h.al,SEEK_CUR); }
        if(h.type==3) fseek(f,h.al,SEEK_CUR);
    }
    fclose(f);
    uint64_t fwd_pk=0,fwd_by=0; /* the forwarded on_loss at i==100 is counted only if it was accepted or merged */
    (void)fwd_pk;(void)fwd_by;
    assert(loss_pk[1]==st.lost_packets[1] && loss_by[1]==st.lost_bytes[1]);
    assert(loss_pk[0]>=st.lost_packets[0] && loss_by[0]>=st.lost_bytes[0]);
    assert(loss_pk[0]-st.lost_packets[0]==3 && loss_by[0]-st.lost_bytes[0]==46080);
    /* 4. write failure is sticky and reported */
    char d[256]; snprintf(d,sizeof d,"%s/fail.tpc",dir); cc_async_sink_test_write=failing_write;
    assert(cc_async_sink_open(&as,d,"fail",1u<<20,65536)==CC_OK); cc_async_sink_callbacks(as,&ca);
    feed(&ca,100,3); assert(cc_async_sink_close(as,&st)==CC_ERR_IO && st.io_error==EIO && st.discarded_after_error>0);
    cc_async_sink_test_write=NULL;
    unlink(a); unlink(b); unlink(c); unlink(d); rmdir(dir);
    puts("ASYNC-SINK PASS: byte-identical to the tagged sink, bounded writes, non-blocking stall with exact HostLoss, sticky write failure, exclusive create");
    return 0;
}
