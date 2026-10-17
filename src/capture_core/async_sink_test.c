/* Deciding tests for cc_async_sink: byte-identical to the synchronous tagged sink for the same
 * callback sequence; a stalled writer loses packets with exact HostLoss confession and never
 * blocks the producer; writes never exceed the chunk; a failed write is reported; an existing
 * destination is refused. */
#include "capture_core.h"
#include <assert.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <mach/mach.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/wait.h>
#include <spawn.h>
extern char **environ;
#include <signal.h>
#include <sys/stat.h>
static uint8_t payload[20000];
static size_t max_seen;
static _Atomic int gate_open=1, in_gate;
static ssize_t gated_write(int fd,const void *b,size_t n){
    atomic_store(&in_gate,1);
    while(!atomic_load(&gate_open)){ struct timespec t={0,1000000}; nanosleep(&t,NULL); }
    if(n>max_seen) max_seen=n;
    return write(fd,b,n>3000?3000:n);   /* short writes too */
}
static _Atomic uint64_t discarded_bytes;
static ssize_t discarding_write(int fd,const void *b,size_t n){ (void)fd;(void)b; atomic_fetch_add(&discarded_bytes,n); return (ssize_t)n; }
static uint64_t footprint(void){
    task_vm_info_data_t ti; mach_msg_type_number_t c=TASK_VM_INFO_COUNT;
    assert(task_info(mach_task_self(),TASK_VM_INFO,(task_info_t)&ti,&c)==KERN_SUCCESS); return ti.phys_footprint;
}
/* Pass four ring lengths of stream through a ring whose writer keeps up, and return how much the process grew. */
static uint64_t ring_growth(const char *path,size_t ring){
    cc_async_sink *k; cc_callbacks cb; cc_async_sink_stats st;
    cc_async_sink_test_write=discarding_write; atomic_store(&discarded_bytes,0);
    assert(cc_async_sink_open(&k,path,"",ring,1u<<20)==CC_OK); cc_async_sink_callbacks(k,&cb);
    uint64_t before=footprint(), fed=0;
    for(uint32_t i=0; fed<4*(uint64_t)ring; i++){
        cc_packet p={CC_EP_VIDEO,(uint16_t)(i%128),i/128,0,15360,15360,payload}; cb.on_packet(cb.ctx,&p); fed+=24+15360;
        if(i%64==63) for(int w=0; atomic_load(&discarded_bytes)<fed; w++){ assert(w<20000); struct timespec d={0,100000}; nanosleep(&d,NULL); }   /* writer has caught up */
    }
    uint64_t after=footprint();
    assert(cc_async_sink_close(k,&st)==CC_OK && !st.lost_packets[0] && st.high_water<ring/8);
    cc_async_sink_test_write=NULL; unlink(path);
    return after>before?after-before:0;
}
static ssize_t failing_write(int fd,const void *b,size_t n){ (void)fd;(void)b;(void)n; errno=EIO; return -1; }
static int full_volume_fsync(int fd){ (void)fd; errno=ENOSPC; return -1; }
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
/* the same feed at about 80 MB/s, twice the device rate: a producer the spiller can keep up with */
static void feed_paced(cc_callbacks *cb,int n){
    for(int i=0;i<n;i++){
        uint8_t ep=i%3?CC_EP_VIDEO:CC_EP_AUDIO; uint32_t len=ep==CC_EP_VIDEO?15360:192;
        if(i%50==7) len=0;
        cc_packet p={ep,(uint16_t)(i%128),(uint32_t)(i/128),0,ep==CC_EP_VIDEO?15360:192,len,payload};
        payload[0]=(uint8_t)i; cb->on_packet(cb->ctx,&p);
        if(i==100) cb->on_loss(cb->ctx,CC_EP_VIDEO,3,46080);
        if(i==200) cb->on_error(cb->ctx,CC_EP_AUDIO,9,-1,CC_ERROR_TRANSFER);
        if(i%500==0) cb->on_tick(cb->ctx,(uint32_t)i);
        if(i%8==7){ struct timespec d={0,1000000}; nanosleep(&d,NULL); }
    }
}
static _Atomic int free_calls, free_allow;
static uint64_t limited_free(const char *dir){ (void)dir; return atomic_fetch_add(&free_calls,1)<atomic_load(&free_allow)?(uint64_t)1<<40:0; }
static _Atomic int spill_calls, spill_fail_at;
static ssize_t failing_spill(int fd,const void *b,size_t n,off_t off){
    if(atomic_fetch_add(&spill_calls,1)+1==atomic_load(&spill_fail_at)){ errno=EIO; return -1; }
    return pwrite(fd,b,n,off);
}
static int spill_files(const char *dir){
    DIR *d=opendir(dir); assert(d); int n=0; struct dirent *e;
    while((e=readdir(d))) if(strstr(e->d_name,".spill")) n++;
    closedir(d); return n;
}
/* parse a capture: per endpoint DATA packets and HostLoss packets; DATA (seq,pkt) strictly increasing per endpoint */
static void parse(const char *path,uint64_t data[2],uint64_t lost[2]){
    FILE *f=fopen(path,"rb"); assert(f); long last[2]={-1,-1};
    struct { uint32_t magic; uint8_t type,ep; uint16_t pi; uint32_t seq,st,req,al; } h;
    data[0]=data[1]=lost[0]=lost[1]=0;
    while(fread(&h,1,24,f)==24){
        assert(h.magic==0x31504143u); int e=h.ep==CC_EP_AUDIO;
        if(h.type==1) lost[e]+=h.req;
        if(h.type==0){ long o=(long)h.seq*128+h.pi; assert(o>last[e]); last[e]=o; data[e]++; }
        if(h.type==0||h.type==3) fseek(f,h.al,SEEK_CUR);
    }
    fclose(f);
}
static ssize_t slow_write(int fd,const void *b,size_t n){ struct timespec d={0,2000000}; nanosleep(&d,NULL); return write(fd,b,n); }
static _Atomic int sread_calls, sread_fail_at;
static ssize_t failing_spill_read(int fd,void *b,size_t n,off_t off){
    if(atomic_fetch_add(&sread_calls,1)+1==atomic_load(&sread_fail_at)){ errno=EIO; return -1; }
    return pread(fd,b,n,off);
}
static void replay_pkt_(void *ctx, const cc_packet *p){ (void)ctx; (void)p; }
struct hole_rx { _Atomic int ended; int holes; uint64_t hole_bytes; long last_seq, hole_after; };
static void hole_pkt_(void *ctx, const cc_packet *p){ struct hole_rx *x=ctx; if(p->endpoint==CC_EP_VIDEO) x->last_seq=p->submit_seq; }
static void hole_end_(void *ctx, enum cc_end r){ (void)r; atomic_store(&((struct hole_rx*)ctx)->ended,1); }
static void hole_loss_ex_(void *ctx, uint8_t ep, uint32_t pk, uint64_t by, int kind, uint32_t seq){
    (void)ep;(void)pk;(void)seq; struct hole_rx *x=ctx; if(kind==CC_LOSS_HOLE){ x->holes++; x->hole_bytes+=by; x->hole_after=x->last_seq; } }
static void replay_end_(void *ctx, enum cc_end r){ (void)r; atomic_store((_Atomic int*)ctx,1); }
static void replay_loss_ex_(void *ctx, uint8_t ep, uint32_t pk, uint64_t by, int kind, uint32_t seq){
    (void)ep;(void)pk;(void)by;(void)seq; if(kind==CC_LOSS_UNCLOSED) atomic_fetch_add((_Atomic int*)ctx+1,1); }
struct prog { cc_async_sink *k; _Atomic int stop; int advances; };
static void *watch_progress(void *a){
    struct prog *p=a; uint64_t last=cc_async_sink_progress(p->k);
    while(!atomic_load(&p->stop)){ struct timespec d={0,5000000}; nanosleep(&d,NULL);
        uint64_t now=cc_async_sink_progress(p->k); if(now!=last){ p->advances++; last=now; } }
    return NULL;
}
/* hand-made leftovers of a crashed writer (test 16): records k0..k1-1 (video DATA, seq k, 100-byte payload) */
static void put_recs(FILE *f, int k0, int k1){
    for(int k=k0;k<k1;k++){ struct { uint32_t magic; uint8_t type,ep; uint16_t pi; uint32_t seq,st,req,al; } h={0x31504143u,0,CC_EP_VIDEO,0,(uint32_t)k,0,100,100};
        uint8_t pay[100]; memset(pay,(uint8_t)k,sizeof pay); fwrite(&h,1,24,f); fwrite(pay,1,100,f); }
}
/* segments: chunks of 5 records with a cc_spill_chunk_s header; record k sits at stream offset 124*k */
static void put_chunks(FILE *f, int k0, int k1, int damage_k){
    for(int k=k0;k<k1;k+=5){ struct cc_spill_chunk_s c={CC_SPILL_CHUNK_MAGIC,5*124,(uint64_t)k*124}; fwrite(&c,1,sizeof c,f);
        if(k==damage_k){ uint8_t junk[5*124]; memset(junk,0x5a,sizeof junk); fwrite(junk,1,sizeof junk,f); } else put_recs(f,k,k+5); }
}
static void make_leftovers(const char *sdir, const char *dest, int dest_to, int cut_bytes, uint64_t next_seg, uint64_t next_off, int damage_k, size_t junk_tail){
    FILE *f=fopen(dest,"wb"); assert(f); put_recs(f,0,dest_to);
    if(cut_bytes){                                     /* a record the crash cut: the first bytes of the next one */
        struct { uint32_t magic; uint8_t type,ep; uint16_t pi; uint32_t seq,st,req,al; } h={0x31504143u,0,CC_EP_VIDEO,0,(uint32_t)dest_to,0,100,100};
        uint8_t r[124]; memcpy(r,&h,24); memset(r+24,(uint8_t)dest_to,100); fwrite(r,1,(size_t)cut_bytes,f); }
    if(junk_tail){ uint8_t z[4096]={0}; for(size_t d=0;d<junk_tail;d+=sizeof z) fwrite(z,1,junk_tail-d<sizeof z?junk_tail-d:sizeof z,f); }
    fclose(f);
    for(int s=0;s<3;s++){ char sn[600]; snprintf(sn,sizeof sn,"%s/hand.tpc.p99999.0000abcd.spill%06d",sdir,s);
        f=fopen(sn,"wb"); assert(f); put_chunks(f,(s==0&&dest_to>=20)?dest_to:10+10*s,20+10*s,damage_k); fclose(f); }
    struct cc_spill_manifest_s m; memset(&m,0,sizeof m); memcpy(m.magic,CC_SPILL_MANIFEST_MAGIC,8); m.version=2; m.pid=99999;
    m.next_seg=next_seg; m.next_off=next_off; m.delta=0; snprintf(m.dest,sizeof m.dest,"%s",dest);
    char mn[600]; snprintf(mn,sizeof mn,"%s/hand.tpc.p99999.0000abcd.manifest",sdir); f=fopen(mn,"wb"); assert(f); fwrite(&m,1,sizeof m,f); fclose(f);
}
/* the destination, described: runs of records "a-b", hole markers "H<bytes>", the end marker "E" */
static void describe(const char *dest, char *out, size_t cap){
    FILE *f=fopen(dest,"rb"); out[0]=0; if(!f){ snprintf(out,cap,"(missing)"); return; }
    struct { uint32_t magic; uint8_t type,ep; uint16_t pi; uint32_t seq,st,req,al; } h; uint8_t pay[100]; long run0=-1, prev=-2; size_t o=0;
    #define FLUSH() do{ if(run0>=0){ o+=(size_t)snprintf(out+o,cap-o,"%s%ld-%ld",o?",":"",run0,prev); run0=-1; } }while(0)
    while(fread(&h,1,24,f)==24){
        if(h.magic!=0x31504143u){ FLUSH(); o+=(size_t)snprintf(out+o,cap-o,"%sBAD",o?",":""); break; }
        if(h.type==0){ if(fread(pay,1,100,f)!=100 || pay[0]!=(uint8_t)h.seq){ FLUSH(); o+=(size_t)snprintf(out+o,cap-o,"%sBADPAY",o?",":""); break; }
            if((long)h.seq!=prev+1){ FLUSH(); } if(run0<0) run0=h.seq; prev=h.seq; continue; }
        FLUSH();
        if(h.type==1 && h.pi==0xFFFA) o+=(size_t)snprintf(out+o,cap-o,"%sE",o?",":"");
        else if(h.type==1 && h.pi==0xFFF9) o+=(size_t)snprintf(out+o,cap-o,"%sH%u",o?",":"",h.al);
        else o+=(size_t)snprintf(out+o,cap-o,"%s?",o?",":"");
    }
    FLUSH(); { long pos=ftell(f); fseek(f,0,SEEK_END); if(ftell(f)!=pos) o+=(size_t)snprintf(out+o,cap-o,",TRAILING"); }
    #undef FLUSH
    fclose(f);
}
static int dest_is(const char *dest, int n, int ended){
    char got[256], want[64]; describe(dest,got,sizeof got); snprintf(want,sizeof want,"0-%d%s",n-1,ended?",E":"");
    if(strcmp(got,want)){ fprintf(stderr,"  destination %s, expected %s\n",got,want); return 0; } return 1;
}
static int dest_desc(const char *dest, const char *want){
    char got[256]; describe(dest,got,sizeof got);
    if(strcmp(got,want)){ fprintf(stderr,"  destination %s, expected %s\n",got,want); return 0; } return 1;
}
static _Atomic int rw_calls, rw_fail_at, rw_zero_at; static _Atomic int rw_stop;
static ssize_t recov_write(int fd,const void *b,size_t n,off_t off){
    int c=atomic_fetch_add(&rw_calls,1)+1;
    if(c==atomic_load(&rw_fail_at)){ errno=EIO; return -1; }
    if(c==atomic_load(&rw_zero_at)){ uint8_t z[4096]={0}; size_t d=0; while(d<n){ size_t m=n-d<sizeof z?n-d:sizeof z; if(pwrite(fd,z,m,off+(off_t)d)!=(ssize_t)m) return -1; d+=m; } return (ssize_t)n; }   /* acknowledged, but zeros */
    ssize_t w=pwrite(fd,b,n,off);
    if(c==2) atomic_store(&rw_stop,1);                  /* a stop asked for after the second piece */
    return w;
}
/* the crash child (test 15), run as its own process: spill with the destination stalled, let the writer cut a
 * record mid-write, then exit without closing */
/* the fifth spill write writes half its records and fails (a disk filling up) */
static _Atomic int hw_calls;
static ssize_t half_failing_spill(int fd,const void *b,size_t n,off_t off){
    if(atomic_fetch_add(&hw_calls,1)+1==5){ if(pwrite(fd,b,n/2,off)<0) return -1; errno=ENOSPC; return -1; }
    return pwrite(fd,b,n,off);
}
/* the crash children exit without closing on purpose: under TSan that is a thread leak, not a finding */
static char **crash_env(void){
    static char *env[512]; int n=0; static char tsan[]="TSAN_OPTIONS=report_thread_leaks=0";
    for(char **e=environ; *e && n<510; e++) if(strncmp(*e,"TSAN_OPTIONS=",13)) env[n++]=*e;
    env[n++]=tsan; env[n]=NULL; return env;
}
static int crash_child(const char *dest, const char *sdir, int sfail){
    cc_async_sink_spill sp={sdir,1,1u<<20,1u<<20}; cc_async_sink *cs; cc_callbacks cc;
    for(size_t i=0;i<sizeof payload;i++) payload[i]=(uint8_t)(i*7);
    cc_async_sink_test_spill_any_volume=1; cc_async_sink_test_write=gated_write; atomic_store(&gate_open,0); atomic_store(&in_gate,0);
    if(sfail) cc_async_sink_test_spill_write=half_failing_spill;
    if(cc_async_sink_open_spill(&cs,dest,"spill",sfail?64u<<20:8u<<20,65536,&sp)!=CC_OK) return 2;
    cc_async_sink_callbacks(cs,&cc);
    for(int i=0;!atomic_load(&in_gate);i++){ if(i>5000) return 3; struct timespec dd={0,1000000}; nanosleep(&dd,NULL); }
    feed_paced(&cc,3000);
    atomic_store(&gate_open,1); struct timespec dd={0,30000000}; nanosleep(&dd,NULL);   /* some delivery, in 3000-byte writes */
    _exit(0);                                          /* no close: the crash */
}
int main(int argc, char **argv){
    if(argc==4 && !strcmp(argv[1],"--crash-child")) return crash_child(argv[2],argv[3],0);
    if(argc==4 && !strcmp(argv[1],"--crash-child-sfail")) return crash_child(argv[2],argv[3],1);
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
    assert(st.released_bytes>0 && !st.release_failures);   /* drained pages went back to the system */
    assert(st.writes>0 && st.write_ns>0 && st.max_write_ns>0 && st.max_write_ns<=st.write_ns && !st.loss_episodes && !st.loss_in_write);
    /* 2. existing destination refused */
    assert(cc_async_sink_open(&as,b,"x",1u<<20,65536)==CC_ERR_IO);
    /* 3. stalled writer: the producer never blocks; drops are exactly confessed */
    atomic_store(&gate_open,0); atomic_store(&in_gate,0);
    assert(cc_async_sink_open(&as,c,"stall",1u<<20,65536)==CC_OK); cc_async_sink_callbacks(as,&ca);
    /* the session note is already in the ring: wait for the writer to be inside its (stalled) write of it, so
     * what the sink reports about each loss episode is decided by the stall and not by thread start-up */
    for(int i=0;!atomic_load(&in_gate);i++){ assert(i<5000); struct timespec d={0,1000000}; nanosleep(&d,NULL); }
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
    /* the stall is a write call that does not return: every loss episode began with the writer inside one, and
     * the longest write is at least as long as the writer had been stuck when the first packet was dropped */
    assert(st.loss_episodes>=1 && st.loss_in_write==st.loss_episodes);
    assert(st.max_in_write_at_loss_ns>0 && st.max_in_write_at_loss_ns<=st.max_write_ns);
    assert(!st.release_failures && st.high_water<=(1u<<20));
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
    /* 4b. a refused flush (a full network volume refuses at the flush, not at write) stops the file the same way */
    { char e4[256]; snprintf(e4,sizeof e4,"%s/full.tpc",dir); size_t was=cc_async_sink_sync_every; cc_async_sink_sync_every=65536; cc_async_sink_test_fsync=full_volume_fsync;
      assert(cc_async_sink_open(&as,e4,"full",1u<<20,65536)==CC_OK); cc_async_sink_callbacks(as,&ca);
      feed(&ca,100,5); assert(cc_async_sink_close(as,&st)==CC_ERR_IO && st.io_error==ENOSPC && st.discarded_after_error>0);
      cc_async_sink_test_fsync=NULL; cc_async_sink_sync_every=was; unlink(e4); }
    /* 5b. a loss still pending at close is in the file: the writer stays stuck until the feed is over, nothing more
     * is fed, and the ring is full to the end, so the confession can only be written by close itself */
    { char e5[256]; snprintf(e5,sizeof e5,"%s/tail_loss.tpc",dir);
      cc_async_sink_test_write=gated_write; atomic_store(&gate_open,0); atomic_store(&in_gate,0);
      assert(cc_async_sink_open(&as,e5,"tail",1u<<20,65536)==CC_OK); cc_async_sink_callbacks(as,&ca);
      for(int i=0;!atomic_load(&in_gate);i++){ assert(i<5000); struct timespec dd={0,1000000}; nanosleep(&dd,NULL); }
      for(uint32_t i=0;i<400;i++){ cc_packet v={CC_EP_VIDEO,(uint16_t)(i%128),i/128,0,15360,15360,payload}; ca.on_packet(ca.ctx,&v);
                                   cc_packet q={CC_EP_AUDIO,(uint16_t)(i%128),i/128,0,192,192,payload}; ca.on_packet(ca.ctx,&q); }
      /* fill what is left with tick records until fewer than a record's 24 bytes remain: before close wrote the
       * confession itself, 108 bytes left here let the old close fit both confessions and this case passed */
      for(int i=0;i<64;i++) ca.on_tick(ca.ctx,(uint32_t)i);
      atomic_store(&gate_open,1);
      assert(cc_async_sink_close(as,&st)==CC_OK && st.lost_packets[0]>0 && st.lost_packets[1]>0 && st.control_dropped>0);
      FILE *g=fopen(e5,"rb"); uint64_t lp[2]={0},lb[2]={0}; long size;
      struct { uint32_t magic; uint8_t type,ep; uint16_t pi; uint32_t seq,st,req,al; } hh;
      while(fread(&hh,1,24,g)==24){ assert(hh.magic==0x31504143u); int e=hh.ep==CC_EP_AUDIO;
          if(hh.type==1){ lp[e]+=hh.req; lb[e]+=hh.al; } else if(hh.type==0||hh.type==3) fseek(g,hh.al,SEEK_CUR); }
      fseek(g,0,SEEK_END); size=ftell(g); fclose(g); unlink(e5);
      for(int e=0;e<2;e++) assert(lp[e]==st.lost_packets[e] && lb[e]==st.lost_bytes[e]);
      assert((uint64_t)size==st.bytes_written);
      cc_async_sink_test_write=NULL; }
    /* 6. a ring's memory follows its backlog, not its size: the stream is laid through every page of the ring once
     * per ring length, so a writer that keeps up must hand drained pages back. The same feed through a ring that
     * cannot (not a whole number of pages) shows the measurement sees the difference. */
    { char d[256]; snprintf(d,sizeof d,"%s/grow.tpc",dir);
      uint64_t kept=ring_growth(d,(64u<<20)+1), freed=ring_growth(d,64u<<20);
      if(!(kept>=(48u<<20) && freed<=(16u<<20))){ fprintf(stderr,"ring memory: %.1f MB without release, %.1f MB with\n",kept/1e6,freed/1e6); assert(0); }
      printf("  ring memory after 4 ring lengths, writer keeping up: %.1f MB without release, %.1f MB with\n",kept/1e6,freed/1e6); }
    /* 7. the spill: the destination stalls for the whole feed (31 MB through an 8 MiB ring). Nothing is lost, the
     * producer never waits, and the file is byte-identical to the synchronous sink's: every byte went to disk and
     * came back in order across segment boundaries. Delivered segments are deleted. */
    char sdir[300]; snprintf(sdir,sizeof sdir,"%s/spill",dir);
    cc_async_sink_spill sp={sdir,1,1u<<20,1u<<20};       /* floor 1 byte, after 1 MiB, 1 MiB segments */
    char r7[256],s7[256]; snprintf(r7,sizeof r7,"%s/ref7.tpc",dir); snprintf(s7,sizeof s7,"%s/spill7.tpc",dir);
    { cc_tagged_sink *t7; cc_callbacks c7; assert(cc_tagged_sink_open(&t7,r7,"spill")==CC_OK); cc_tagged_sink_callbacks(t7,&c7);
      feed(&c7,3000,0); assert(cc_tagged_sink_close(t7)==CC_OK); }
    cc_async_sink_test_spill_any_volume=1;
    cc_async_sink_test_write=gated_write; atomic_store(&gate_open,0); atomic_store(&in_gate,0);
    assert(cc_async_sink_open_spill(&as,s7,"spill",8u<<20,65536,&sp)==CC_OK && cc_async_sink_spill_state(as)==1);
    cc_async_sink_callbacks(as,&ca);
    for(int i=0;!atomic_load(&in_gate);i++){ assert(i<5000); struct timespec dd={0,1000000}; nanosleep(&dd,NULL); }
    clock_gettime(CLOCK_MONOTONIC,&t0); feed_paced(&ca,3000); clock_gettime(CLOCK_MONOTONIC,&t1);
    ms=(t1.tv_sec-t0.tv_sec)*1e3+(t1.tv_nsec-t0.tv_nsec)/1e6; assert(ms<5000);
    int on_disk=spill_files(sdir); atomic_store(&gate_open,1);
    assert(cc_async_sink_close(as,&st)==CC_OK);
    printf("  spill: %.1f MB through the local disk (peak %.1f MB on disk, %d segment files during the stall, %llu created), ring peak %.1f MB of 8.4\n",
           st.spill_bytes/1e6,st.spill_peak/1e6,on_disk,(unsigned long long)st.spill_segments,st.high_water/1e6);
    assert(!st.lost_packets[0] && !st.lost_packets[1] && !st.control_dropped && !st.io_error && !st.spill_error);
    assert(st.spill_state==1 && st.spill_peak>(16u<<20) && st.spill_segments>16 && on_disk>16);
    assert(same_file(r7,s7) && spill_files(sdir)==0);
    /* 8. the floor: three segments allowed, then the volume is "full". The spill stops growing, memory is the only
     * buffer again, and overflow is exact HostLoss: every fed packet is in the file or confessed, in order. */
    char s8[256]; snprintf(s8,sizeof s8,"%s/floor8.tpc",dir);
    cc_async_sink_test_free=limited_free; atomic_store(&free_calls,0); atomic_store(&free_allow,3);
    atomic_store(&gate_open,0); atomic_store(&in_gate,0);
    assert(cc_async_sink_open_spill(&as,s8,"floor",8u<<20,65536,&sp)==CC_OK); cc_async_sink_callbacks(as,&ca);
    atomic_store(&free_calls,0);   /* open asked once (its room report); three segments from here */
    for(int i=0;!atomic_load(&in_gate);i++){ assert(i<5000); struct timespec dd={0,1000000}; nanosleep(&dd,NULL); }
    feed_paced(&ca,3000); atomic_store(&gate_open,1);
    assert(cc_async_sink_close(as,&st)==CC_OK);
    { uint64_t dt[2],lo[2]; parse(s8,dt,lo);
      assert(st.spill_segments==3 && st.spill_floor_refusals>0 && st.lost_packets[0]>0);
      assert(dt[0]+st.lost_packets[0]==2000 && dt[1]+st.lost_packets[1]==1000);   /* fed: 2000 video, 1000 audio */
      assert(lo[0]==st.lost_packets[0]+3 && lo[1]==st.lost_packets[1]);
      assert(spill_files(sdir)==0); }
    cc_async_sink_test_free=NULL;
    /* 9. a failed spill write: its bytes stay in memory, the spill turns off, and with the backlog still inside the
     * ring nothing is lost; the file is byte-identical to the reference. */
    char s9[256]; snprintf(s9,sizeof s9,"%s/sfail9.tpc",dir);
    cc_async_sink_test_spill_write=failing_spill; atomic_store(&spill_calls,0); atomic_store(&spill_fail_at,5);
    atomic_store(&gate_open,0); atomic_store(&in_gate,0);
    assert(cc_async_sink_open_spill(&as,s9,"spill",64u<<20,65536,&sp)==CC_OK); cc_async_sink_callbacks(as,&ca);
    for(int i=0;!atomic_load(&in_gate);i++){ assert(i<5000); struct timespec dd={0,1000000}; nanosleep(&dd,NULL); }
    feed_paced(&ca,3000); atomic_store(&gate_open,1);
    assert(cc_async_sink_close(as,&st)==CC_OK);
    assert(st.spill_error==EIO && st.spill_bytes>3*60000 && st.spill_bytes<=4*65536 && !st.lost_packets[0] && !st.lost_packets[1]);   /* four whole-record chunks */
    assert(same_file(r7,s9) && spill_files(sdir)==0);
    cc_async_sink_test_spill_write=NULL; cc_async_sink_test_spill_any_volume=0;
    /* 10. a destination on the spill's own volume gets no spill */
    { char s10[256]; snprintf(s10,sizeof s10,"%s/same10.tpc",dir);
      assert(cc_async_sink_open_spill(&as,s10,"x",1u<<20,65536,&sp)==CC_OK && cc_async_sink_spill_state(as)==0);
      assert(cc_async_sink_close(as,&st)==CC_OK && st.spill_state==0); unlink(s10); }
    /* 10b. a destination that is not a regular file (/dev/null) gets no spill: nothing could be recovered into it */
    { cc_async_sink_test_spill_any_volume=1;
      assert(cc_async_sink_open_spill(&as,"/dev/null","x",1u<<20,65536,&sp)==CC_OK && cc_async_sink_spill_state(as)==0);
      assert(cc_async_sink_close(as,&st)==CC_OK); cc_async_sink_test_spill_any_volume=0;
      DIR *dd=opendir(sdir); struct dirent *de; int mfs=0; while((de=readdir(dd))) if(strstr(de->d_name,".manifest")) mfs++; closedir(dd); assert(!mfs); }
    /* 11. an unread-slot record arriving while ring loss is pending, with under a record's room left: it must not
     * overrun the ring (it once wrote over bytes the writer had not yet written, corrupting the file) */
    { char e11[256]; snprintf(e11,sizeof e11,"%s/unsched11.tpc",dir);
      cc_async_sink_test_write=gated_write; atomic_store(&gate_open,0); atomic_store(&in_gate,0);
      assert(cc_async_sink_open(&as,e11,"",1u<<20,65536)==CC_OK); cc_async_sink_callbacks(as,&ca);
      cc_packet v0={CC_EP_VIDEO,0,0,0,15360,15360,payload}; ca.on_packet(ca.ctx,&v0);
      for(int i=0;!atomic_load(&in_gate);i++){ assert(i<5000); struct timespec dd={0,1000000}; nanosleep(&dd,NULL); }
      for(uint32_t i=1;i<400;i++){ cc_packet v={CC_EP_VIDEO,(uint16_t)(i%128),i/128,0,15360,15360,payload}; ca.on_packet(ca.ctx,&v);
                                   cc_packet q={CC_EP_AUDIO,(uint16_t)(i%128),i/128,0,192,192,payload}; ca.on_packet(ca.ctx,&q); }
      for(int i=0;i<64;i++) ca.on_tick(ca.ctx,(uint32_t)i);
      ca.on_loss_ex(ca.ctx,CC_EP_VIDEO,5,0,CC_LOSS_UNSCHEDULED,77);
      atomic_store(&gate_open,1);
      assert(cc_async_sink_close(as,&st)==CC_OK && st.high_water<=(1u<<20) && st.lost_packets[0]>0);
      uint64_t dt[2],lo[2]; parse(e11,dt,lo);
      assert(lo[0]==st.lost_packets[0] && lo[1]==st.lost_packets[1]);   /* the unread-slot record was counted dropped, not written */
      unlink(e11); cc_async_sink_test_write=NULL; }
    /* 12. a backlog drained at close: close reports progress while it drains (the CLI's guard re-arms on it), and
     * every segment is gone afterwards. The destination is stalled through the feed, then slow (2 ms per write). */
    { char s12[256]; snprintf(s12,sizeof s12,"%s/drain12.tpc",dir); cc_async_sink_test_spill_any_volume=1;
      cc_async_sink_test_write=gated_write; atomic_store(&gate_open,0); atomic_store(&in_gate,0);
      assert(cc_async_sink_open_spill(&as,s12,"drain",8u<<20,65536,&sp)==CC_OK); cc_async_sink_callbacks(as,&ca);
      for(int i=0;!atomic_load(&in_gate);i++){ assert(i<5000); struct timespec dd={0,1000000}; nanosleep(&dd,NULL); }
      feed_paced(&ca,1500);
      assert(spill_files(sdir)>4);
      cc_async_sink_test_write=slow_write; atomic_store(&gate_open,1);   /* the stuck call returns; the rest go slowly */
      struct prog pr={as,0,0}; pthread_t w; assert(pthread_create(&w,NULL,watch_progress,&pr)==0);
      assert(cc_async_sink_finish(as)==CC_OK); atomic_store(&pr.stop,1); pthread_join(w,NULL);
      assert(cc_async_sink_close(as,&st)==CC_OK);
      printf("  drain at close: %.1f MB from the spill, progress seen to advance %d times while closing\n",st.spill_bytes/1e6,pr.advances);
      assert(pr.advances>10 && !st.lost_packets[0] && !st.lost_packets[1] && spill_files(sdir)==0);
      unlink(s12); cc_async_sink_test_write=NULL; cc_async_sink_test_spill_any_volume=0; }
    /* 13. the spill directory must be this user's private directory, never a symlink; segments of a writer that is
     * gone are reported at open and left in place (they hold undelivered capture bytes) */
    { char s13[256], pd[300], ln[300], stale[400]; snprintf(s13,sizeof s13,"%s/priv13.tpc",dir);
      snprintf(pd,sizeof pd,"%s/open_dir",dir); assert(mkdir(pd,0755)==0);
      cc_async_sink_spill bad={pd,1,1u<<20,1u<<20}; cc_async_sink_test_spill_any_volume=1;
      assert(cc_async_sink_open_spill(&as,s13,"x",1u<<20,65536,&bad)==CC_OK && cc_async_sink_spill_state(as)==-EPERM);
      assert(cc_async_sink_close(as,&st)==CC_OK); unlink(s13);
      snprintf(ln,sizeof ln,"%s/link_dir",dir); assert(symlink(sdir,ln)==0); bad.dir=ln;
      assert(cc_async_sink_open_spill(&as,s13,"x",1u<<20,65536,&bad)==CC_OK && cc_async_sink_spill_state(as)==-ENOTDIR);
      assert(cc_async_sink_close(as,&st)==CC_OK); unlink(s13);
      /* a dead writer's segment (pid 99999 assumed absent: checked) and a live one's (this test's parent) */
      assert(kill(99999,0)!=0 && errno==ESRCH);
      snprintf(stale,sizeof stale,"%s/old.part2.tpc.p99999.0badc0de.spill000003",sdir); FILE *sf=fopen(stale,"wb"); assert(sf); fwrite(payload,1,4096,sf); fclose(sf);
      char live[400]; snprintf(live,sizeof live,"%s/other.tpc.p%d.0badc0de.spill000000",sdir,(int)getppid()); sf=fopen(live,"wb"); assert(sf); fclose(sf);
      assert(cc_async_sink_open_spill(&as,s13,"x",1u<<20,65536,&sp)==CC_OK && cc_async_sink_spill_state(as)==1);
      uint64_t nf,nb; cc_async_sink_spill_stale(as,&nf,&nb); assert(nf==1 && nb>=4096);
      assert(cc_async_sink_close(as,&st)==CC_OK && access(stale,F_OK)==0 && access(live,F_OK)==0);
      unlink(stale); unlink(live); unlink(s13); unlink(ln); rmdir(pd); cc_async_sink_test_spill_any_volume=0; }
    /* 14. a spilled chunk the local disk will not give back: the capture goes on. In its place the file gets HostLoss
     * records (pkt_index 0xFFFB) with exactly the packets it held; every record still parses, and every fed packet
     * is in the file or confessed, per endpoint. */
    { char s14[256]; snprintf(s14,sizeof s14,"%s/sread14.tpc",dir); cc_async_sink_test_spill_any_volume=1;
      cc_async_sink_test_spill_read=failing_spill_read; atomic_store(&sread_calls,0); atomic_store(&sread_fail_at,7);
      cc_async_sink_test_write=gated_write; atomic_store(&gate_open,0); atomic_store(&in_gate,0);
      assert(cc_async_sink_open_spill(&as,s14,"sread",8u<<20,65536,&sp)==CC_OK); cc_async_sink_callbacks(as,&ca);
      for(int i=0;!atomic_load(&in_gate);i++){ assert(i<5000); struct timespec dd={0,1000000}; nanosleep(&dd,NULL); }
      feed_paced(&ca,3000); atomic_store(&gate_open,1);
      assert(cc_async_sink_close(as,&st)==CC_OK && !st.io_error);
      assert(st.spill_read_errors==1 && st.spill_read_lost_packets[0]>0 && !st.lost_packets[0] && !st.lost_packets[1]);
      FILE *g=fopen(s14,"rb"); uint64_t dt[2]={0},lo[2]={0},sl[2]={0}; struct { uint32_t magic; uint8_t type,ep; uint16_t pi; uint32_t seq,st,req,al; } hh;
      while(fread(&hh,1,24,g)==24){ assert(hh.magic==0x31504143u); int e=hh.ep==CC_EP_AUDIO;
          if(hh.type==0){ dt[e]++; fseek(g,hh.al,SEEK_CUR); } else if(hh.type==3) fseek(g,hh.al,SEEK_CUR);
          else if(hh.type==1){ lo[e]+=hh.req; if(hh.pi==0xFFFB) sl[e]+=hh.req; } }
      fclose(g);
      printf("  unreadable spill chunk: %llu video / %llu audio packets confessed in its place, %llu + %llu delivered\n",
             (unsigned long long)sl[0],(unsigned long long)sl[1],(unsigned long long)dt[0],(unsigned long long)dt[1]);
      assert(sl[0]==st.spill_read_lost_packets[0] && sl[1]==st.spill_read_lost_packets[1]);
      /* fed 2000 video / 1000 audio plus the forwarded loss of 3 video packets: all in the file or confessed */
      assert(dt[0]+lo[0]==2003 && dt[1]+lo[1]==1000);
      assert(spill_files(sdir)==0);
      unlink(s14); cc_async_sink_test_spill_read=NULL; cc_async_sink_test_write=NULL; cc_async_sink_test_spill_any_volume=0; }
    /* 15. a writer that dies without closing: its undelivered spill is put where it belongs at the next start. The
     * child spills with its destination stalled, lets the writer cut a record mid-write, and exits without close.
     * cc_spill_recover then leaves a destination that parses record by record, is a prefix of the full stream
     * (byte for byte, against the synchronous sink's file) plus the end marker, and nothing in the spill directory.
     * A live writer's spill is never touched. */
    { char s15[256]; snprintf(s15,sizeof s15,"%s/crash15.tpc",dir); cc_async_sink_test_spill_any_volume=1;
      pid_t c; char *cargv[]={argv[0],(char*)"--crash-child",s15,sdir,NULL};
      assert(posix_spawn(&c,argv[0],NULL,NULL,cargv,crash_env())==0);
      int ws; assert(waitpid(c,&ws,0)==c && WIFEXITED(ws) && WEXITSTATUS(ws)==0);
      assert(spill_files(sdir)>0);                   /* something was left on the local disk */
      struct stat before; assert(stat(s15,&before)==0);
      /* a live writer alongside: its manifest is locked, so recovery leaves it */
      char s15b[256]; snprintf(s15b,sizeof s15b,"%s/live15.tpc",dir); cc_async_sink *lv; assert(cc_async_sink_open_spill(&lv,s15b,"live",1u<<20,65536,&sp)==CC_OK);
      cc_spill_recover_stats rs; assert(cc_spill_recover(sdir,NULL,NULL,NULL,NULL,&rs)==0);
      assert(rs.recovered==1 && !rs.failed && !rs.kept);
#if !defined(__has_feature) || !__has_feature(thread_sanitizer)
      assert(rs.bytes>0);                              /* timing under TSan can leave nothing spilled to recover */
#endif
      { DIR *dd=opendir(sdir); struct dirent *de; int live=0; while((de=readdir(dd))) if(strstr(de->d_name,"live15")) live++; closedir(dd); assert(live==1); }   /* its manifest */
      assert(cc_async_sink_close(lv,&st)==CC_OK); unlink(s15b);
      assert(spill_files(sdir)==0);
      FILE *g=fopen(s15,"rb"), *rf=fopen(r7,"rb"); assert(g && rf);
      struct { uint32_t magic; uint8_t type,ep; uint16_t pi; uint32_t seq,st,req,al; } hh; long lastpos=-1; uint16_t lastpi=0; uint8_t lasttype=9;
      while(fread(&hh,1,24,g)==24){ assert(hh.magic==0x31504143u); lastpos=ftell(g)-24; lasttype=hh.type; lastpi=hh.pi; if(hh.type==0||hh.type==3) fseek(g,hh.al,SEEK_CUR); }
      assert(lasttype==1 && lastpi==0xFFFA);           /* marked as ended without closing */
      fseek(g,0,SEEK_SET); for(long i=0;i<lastpos;i++) assert(fgetc(g)==fgetc(rf));   /* a prefix of the full stream */
      printf("  crash without close: %.1f MB in the destination before (%lld B), %.1f MB recovered after it, %ld B of stream now, marked ended\n",
             before.st_size/1e6,(long long)before.st_size,rs.bytes/1e6,lastpos);
      fclose(g); fclose(rf); unlink(s15); cc_async_sink_test_spill_any_volume=0; cc_async_sink_test_write=NULL; atomic_store(&gate_open,1); }
    /* 16. recovery that stops or fails part-way resumes exactly (review, eighth round): leftovers built by hand
     * (destination 0-9 plus a cut record; segments 10-19, 20-29, 30-39 in chunks of five records). Each piece is read back and recorded in the
     * manifest, and a failed one is cut off the destination again, so nothing is duplicated, reordered or left damaged. */
    { char hd[300]; snprintf(hd,sizeof hd,"%s/hand.tpc",dir); cc_spill_recover_stats rs;
      /* (a) the third piece fails, then a clean rerun */
      make_leftovers(sdir,hd,10,60,0,0,-1,0); cc_spill_recover_test_write=recov_write; atomic_store(&rw_calls,0); atomic_store(&rw_fail_at,3); atomic_store(&rw_zero_at,0);
      assert(cc_spill_recover(sdir,NULL,NULL,NULL,NULL,&rs)==0 && rs.failed==1 && !rs.recovered);
      assert(dest_is(hd,20,0));                          /* the verified chunks (10-14, 15-19) stay, the cut record and failed one are gone */
      cc_spill_recover_test_write=NULL;
      assert(cc_spill_recover(sdir,NULL,NULL,NULL,NULL,&rs)==0 && rs.recovered==1 && dest_is(hd,40,1) && spill_files(sdir)==0);
      /* (b) a write acknowledged but read back as zeros (a network volume): cut back, then exact */
      unlink(hd); make_leftovers(sdir,hd,10,0,0,0,-1,0); cc_spill_recover_test_write=recov_write; atomic_store(&rw_calls,0); atomic_store(&rw_fail_at,0); atomic_store(&rw_zero_at,2);
      assert(cc_spill_recover(sdir,NULL,NULL,NULL,NULL,&rs)==0 && rs.failed==1 && dest_is(hd,15,0));
      cc_spill_recover_test_write=NULL; atomic_store(&rw_zero_at,0);
      assert(cc_spill_recover(sdir,NULL,NULL,NULL,NULL,&rs)==0 && rs.recovered==1 && dest_is(hd,40,1) && spill_files(sdir)==0);
      /* (c) a stop after the second piece (OBS quitting), then a rerun */
      unlink(hd); make_leftovers(sdir,hd,10,0,0,0,-1,0); cc_spill_recover_test_write=recov_write; atomic_store(&rw_calls,0); atomic_store(&rw_stop,0);
      assert(cc_spill_recover(sdir,NULL,NULL,&rw_stop,NULL,&rs)==0 && !rs.recovered && rs.kept==1 && dest_is(hd,20,0));
      cc_spill_recover_test_write=NULL;
      assert(cc_spill_recover(sdir,NULL,NULL,NULL,NULL,&rs)==0 && rs.recovered==1 && dest_is(hd,40,1) && spill_files(sdir)==0);
      /* (d) the first undelivered chunk already in the destination (a crash between its write and the manifest), and a
       * run after an earlier one wrote its end marker: neither duplicates */
      unlink(hd); make_leftovers(sdir,hd,15,0,0,0,-1,0);
      assert(cc_spill_recover(sdir,NULL,NULL,NULL,NULL,&rs)==0 && rs.recovered==1 && dest_is(hd,40,1));
      /* (e) review, ninth round: the writer was writing chunk 10-19 from memory when it died (0-14 arrived, then a cut
       * record); the spill holds 20-29 and 30-39. The rest of that memory chunk is gone: a hole, confessed where it is */
      unlink(hd); make_leftovers(sdir,hd,15,60,0,0,-1,0);
      { char sn[600]; snprintf(sn,sizeof sn,"%s/hand.tpc.p99999.0000abcd.spill000000",sdir); unlink(sn); }   /* 10-19 never reached the spill */
      { struct cc_spill_manifest_s m; char mn[600]; snprintf(mn,sizeof mn,"%s/hand.tpc.p99999.0000abcd.manifest",sdir); FILE *f=fopen(mn,"r+b"); assert(f && fread(&m,1,sizeof m,f)==sizeof m);
        m.next_seg=1; m.next_off=0; fseek(f,0,SEEK_SET); fwrite(&m,1,sizeof m,f); fclose(f); }
      assert(cc_spill_recover(sdir,NULL,NULL,NULL,NULL,&rs)==0 && rs.recovered==1 && dest_desc(hd,"0-14,H620,20-39,E"));
      /* replayed, that hole is one loss callback in its place (review, tenth round: it was dropped and its bytes
       * carried into the next loss record) */
      { cc_config rc={0}; rc.replay_path=hd; struct hole_rx hx; memset(&hx,0,sizeof hx);
        cc_callbacks rcb={0}; rcb.ctx=&hx; rcb.on_packet=hole_pkt_; rcb.on_end=hole_end_; rcb.on_loss_ex=hole_loss_ex_;
        cc_session *rs3; assert(cc_open(&rs3,&rc,&rcb)==CC_OK && cc_start(rs3)==CC_OK);
        for(int i=0;!atomic_load(&hx.ended);i++){ assert(i<20000); struct timespec dd={0,1000000}; nanosleep(&dd,NULL); }
        cc_stats cst; cc_stop(rs3); cc_get_stats(rs3,&cst); cc_close(rs3);
        assert(hx.holes==1 && hx.hole_bytes==620 && hx.hole_after==14 && cst.hole_marks==1 && cst.hole_bytes==620 && !cst.lost_bytes[0] && !cst.lost_bytes[1]); }
      /* (f) a damaged chunk in the middle of a segment (records 20-24): confessed in place, the rest recovered */
      unlink(hd); make_leftovers(sdir,hd,10,0,0,0,20,0);
      assert(cc_spill_recover(sdir,NULL,NULL,NULL,NULL,&rs)==0 && rs.recovered==1 && dest_desc(hd,"0-19,H636,25-39,E") && spill_files(sdir)==0);
      /* (h) a damaged last chunk of a segment (15-19), the next segment unreadable on the first run, then a rerun: one
       * hole, not two (review, tenth round: the resume placed the next chunk with a stale delta) */
      unlink(hd); make_leftovers(sdir,hd,10,0,0,0,15,0);
      { char sn[600]; snprintf(sn,sizeof sn,"%s/hand.tpc.p99999.0000abcd.spill000001",sdir); assert(chmod(sn,0)==0);
        assert(cc_spill_recover(sdir,NULL,NULL,NULL,NULL,&rs)==0 && rs.failed==1 && dest_desc(hd,"0-14,H636"));
        assert(chmod(sn,0600)==0); }
      assert(cc_spill_recover(sdir,NULL,NULL,NULL,NULL,&rs)==0 && rs.recovered==1 && dest_desc(hd,"0-14,H636,20-39,E") && spill_files(sdir)==0);
      /* (g) junk past the resume point (a failed cut-back of an unverified piece): cut back exactly, no guessing */
      unlink(hd); make_leftovers(sdir,hd,10,0,0,0,-1,700000);
      assert(cc_spill_recover(sdir,NULL,NULL,NULL,NULL,&rs)==0 && rs.recovered==1 && dest_is(hd,40,1));
      unlink(hd); printf("  recovery resumes exactly after a failed piece, zeros, a stop; overlap cut; a memory chunk's hole and a damaged chunk confessed in place; junk cut\n"); }
    /* 17. a spill write that failed part-way, records the writer then delivered from memory, then a crash: the failed
     * write's bytes must not come back from the segment (review, eighth round: they did, after newer data). The
     * recovered file is a prefix of the full stream plus the end marker; replayed, the marker comes through. */
    { char s17[256]; snprintf(s17,sizeof s17,"%s/crash17.tpc",dir);
      pid_t c; char *cargv[]={argv[0],(char*)"--crash-child-sfail",s17,sdir,NULL};
      assert(posix_spawn(&c,argv[0],NULL,NULL,cargv,crash_env())==0);
      int ws; assert(waitpid(c,&ws,0)==c && WIFEXITED(ws) && WEXITSTATUS(ws)==0);
      cc_spill_recover_stats rs; assert(cc_spill_recover(sdir,NULL,NULL,NULL,NULL,&rs)==0 && rs.recovered==1 && spill_files(sdir)==0);
      FILE *g=fopen(s17,"rb"), *rf=fopen(r7,"rb"); assert(g && rf);
      struct { uint32_t magic; uint8_t type,ep; uint16_t pi; uint32_t seq,st,req,al; } hh; long lastpos=-1; uint16_t lastpi=0; uint8_t lasttype=9;
      while(fread(&hh,1,24,g)==24){ assert(hh.magic==0x31504143u); lastpos=ftell(g)-24; lasttype=hh.type; lastpi=hh.pi; if(hh.type==0||hh.type==3) fseek(g,hh.al,SEEK_CUR); }
      assert(lasttype==1 && lastpi==0xFFFA);
      fseek(g,0,SEEK_SET); for(long i=0;i<lastpos;i++) assert(fgetc(g)==fgetc(rf));
      fclose(g); fclose(rf);
      uint64_t dt[2],lo[2]; parse(s17,dt,lo);              /* also: DATA strictly in order per endpoint */
      /* replay: the end mark reaches the callbacks and the stats */
      cc_config rc={0}; rc.replay_path=s17; struct { _Atomic int ended, unclosed; } rx={0,0};
      cc_callbacks rcb={0}; rcb.ctx=&rx;
      rcb.on_packet=replay_pkt_; rcb.on_end=replay_end_; rcb.on_loss_ex=replay_loss_ex_;
      cc_session *rs2; assert(cc_open(&rs2,&rc,&rcb)==CC_OK && cc_start(rs2)==CC_OK);
      for(int i=0;!atomic_load(&rx.ended);i++){ assert(i<20000); struct timespec dd={0,1000000}; nanosleep(&dd,NULL); }
      cc_stats cst; cc_stop(rs2); cc_get_stats(rs2,&cst); cc_close(rs2);
      assert(atomic_load(&rx.unclosed)==1 && cst.unclosed_marks==1);
      printf("  failed spill write, then a crash: recovered file is a prefix of the stream (%ld B), in order; replay sees the end mark\n",lastpos);
      unlink(s17); }
    unlink(r7); unlink(s7); unlink(s8); unlink(s9); rmdir(sdir);
    unlink(a); unlink(b); unlink(c); unlink(d); rmdir(dir);
    puts("ASYNC-SINK PASS: byte-identical to the tagged sink, bounded writes, non-blocking stall with exact HostLoss, sticky write failure, exclusive create, lossless spill through a stalled destination, spill floor, failed spill write, no ring overrun on an unread-slot record, drain at close with progress, private spill directory, stale segments reported and kept, unreadable spill chunk confessed exactly and the capture goes on, a crashed writer's spill recovered into its destination");
    return 0;
}
