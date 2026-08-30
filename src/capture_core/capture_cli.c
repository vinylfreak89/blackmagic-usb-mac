// shuttle-capture — thin CLI over capture_core. Same jobs as capture_tagged_bench, now via the library:
//   shuttle-capture <svideo|composite|component> <secs> <out.tpc> [ringMB]      capture
//   shuttle-capture --replay <in.tpc> <out.tpc|/dev/null> [paceUS]            replay
#include "capture_core.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static cc_session *g_s;
static cc_tagged_sink *g_k;
static volatile int g_done=0;
static void end_cb(void *ctx, enum cc_end r){ (void)ctx; g_done=r+1000; }
int main(int argc,char**argv){
    cc_config cfg={0}; const char *out=NULL; int secs=0;
    if(argc>=3 && !strcmp(argv[1],"--replay")){
        cfg.replay_path=argv[2]; out=argv[3];
        if(argc>4) cfg.replay_pace_us=atoi(argv[4]);
    } else if(argc>=4){
        cfg.input = !strcmp(argv[1],"component")?CC_INPUT_COMPONENT
                  : !strcmp(argv[1],"composite")?CC_INPUT_COMPOSITE:CC_INPUT_SVIDEO;
        secs=atoi(argv[2]); out=argv[3];
        if(argc>4) cfg.ring_mb=atoi(argv[4]);
    } else { fprintf(stderr,"usage: %s <input> <secs> <out> [ringMB] | --replay <in> <out> [paceUS]\n",argv[0]); return 9; }
    if(cc_tagged_sink_open(&g_k,out,"shuttle-capture via capture_core v1")!=CC_OK){ perror(out); return 1; }
    cc_callbacks cb; cc_tagged_sink_callbacks(g_k,&cb); cb.on_end=end_cb;
    int rc=cc_open(&g_s,&cfg,&cb);
    if(rc!=CC_OK){ fprintf(stderr,"open: %s\n",cc_strerror(rc)); return 2; }
    cc_start(g_s);
    if(cfg.replay_path){ while(!g_done) usleep(50000); }
    else { for(int i=0;i<secs*10 && !g_done;i++) usleep(100000); }
    cc_stop(g_s);
    cc_stats st; cc_get_stats(g_s,&st);
    printf("video %.1f MB | audio %.1f MB | iso_err=%ld xfer_err=%ld resub=%ld/%ld\n",
           st.bytes[0]/1e6,st.bytes[1]/1e6,st.iso_errors,st.transfer_errors,
           st.resubmit_failures,st.resubmit_recovered);
    printf("lost v=%llu a=%llu B | zero=%ld short=%ld | ring high=%zu/%zu | fleet %d+%d/%d\n",
           (unsigned long long)st.lost_bytes[0],(unsigned long long)st.lost_bytes[1],
           st.zero_len_packets,st.short_packets,st.ring_high_water,st.ring_size,
           st.fleet[0],st.fleet[1],st.fleet_size);
    cc_close(g_s);
    int krc=cc_tagged_sink_close(g_k);
    if(krc!=CC_OK){ fprintf(stderr,"SINK WRITE FAILURE\n"); return 3; }
    return 0;
}
