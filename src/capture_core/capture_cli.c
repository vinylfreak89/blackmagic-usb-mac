// shuttle-capture — thin CLI over capture_core. Same jobs as capture_tagged_bench, now via the library:
//   shuttle-capture <input> <secs> <out.tpc> [ringMB] [scratchDir]      capture
//   shuttle-capture --replay <in.tpc> <out.tpc|/dev/null> [paceUS] [scratchDir]
#include "capture_core.h"
#include <errno.h>
#include <limits.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
static cc_session *g_s;
static cc_tagged_sink *g_k;
static _Atomic int g_done;
static _Atomic int g_end_reason;
static void end_cb(void *ctx, enum cc_end r){
    (void)ctx;
    atomic_store(&g_end_reason,r);
    atomic_store(&g_done,1);
}

static const char *end_name(enum cc_end r){
    switch(r){
    case CC_END_STOPPED: return "Stopped";
    case CC_END_DEVICE_GONE: return "DeviceGone";
    case CC_END_REPLAY_EOF: return "ReplayEOF";
    case CC_END_WRITE_FAILED: return "WriteFailed";
    case CC_END_TRANSFER_FAILED: return "TransferFailed";
    case CC_END_INTERNAL_ERROR: return "InternalError";
    }
    return "Unknown";
}
static const char *input_name(enum cc_input input){
    switch(input){
    case CC_INPUT_SVIDEO: return "svideo";
    case CC_INPUT_COMPOSITE: return "composite";
    case CC_INPUT_COMPONENT: return "component";
    }
    return "unknown";
}
static uint32_t mode_word(enum cc_input input){
    uint32_t video=input==CC_INPUT_COMPONENT?0x02000000u:
                   input==CC_INPUT_COMPOSITE?0x04000000u:0x06000000u;
    return 0x09000000u|video|0x10000000u|0x20000000u;
}

static int path_below(const char *path,const char *root){
    size_t n=strlen(root);
    return !strncmp(path,root,n) && (path[n]=='/' || path[n]=='\0');
}
static int cloud_scratch(const char *path){
    const char *home=getenv("HOME");
    if(!home || !*home) return 0;
    const char *suffix[]={"/Desktop","/Documents","/Library/Mobile Documents",
                          "/Library/CloudStorage"};
    char root[PATH_MAX];
    for(size_t i=0;i<sizeof suffix/sizeof suffix[0];i++){
        if(snprintf(root,sizeof root,"%s%s",home,suffix[i])>=(int)sizeof root) return 1;
        if(path_below(path,root)) return 1;
    }
    return 0;
}
static int stage_path(const char *dest,const char *scratch,char staged[PATH_MAX]){
    if(mkdir(scratch,0700)<0 && errno!=EEXIST){ perror(scratch); return -1; }
    char real_scratch[PATH_MAX];
    if(!realpath(scratch,real_scratch)){ perror(scratch); return -1; }
    if(cloud_scratch(real_scratch)){
        fprintf(stderr,"scratch directory is cloud-synced: %s\n",real_scratch);
        return -1;
    }
    char parent[PATH_MAX];
    if(strlen(dest)>=sizeof parent){ fprintf(stderr,"output path too long\n"); return -1; }
    strcpy(parent,dest);
    char *slash=strrchr(parent,'/');
    if(slash){ if(slash==parent) slash[1]='\0'; else *slash='\0'; }
    else strcpy(parent,".");
    struct stat ss,ds;
    if(stat(real_scratch,&ss)<0 || stat(parent,&ds)<0){ perror("stat output/scratch"); return -1; }
    if(ss.st_dev!=ds.st_dev){
        fprintf(stderr,"scratch and destination are on different filesystems; "
                       "refusing a copy disguised as a move\n");
        return -1;
    }
    const char *base=strrchr(dest,'/'); base=base?base+1:dest;
    if(snprintf(staged,PATH_MAX,"%s/.%s.partial.XXXXXX",real_scratch,base)>=PATH_MAX){
        fprintf(stderr,"staging path too long\n"); return -1;
    }
    int fd=mkstemp(staged);
    if(fd<0){ perror("mkstemp"); return -1; }
    close(fd);
    return 0;
}
int main(int argc,char**argv){
    cc_config cfg={0}; const char *out=NULL; int secs=0;
    const char *scratch="/private/tmp/blackmagic-usb-mac";
    if(argc>1 && !strcmp(argv[argc-1],"--fail-stop-control-loss")){
        cfg.fail_stop_on_control_loss=1;
        argc--;
    }
    if(argc>=4 && !strcmp(argv[1],"--replay")){
        cfg.replay_path=argv[2]; out=argv[3];
        if(argc>4) cfg.replay_pace_us=atoi(argv[4]);
        if(argc>5) scratch=argv[5];
    } else if(argc>=4){
        cfg.input = !strcmp(argv[1],"component")?CC_INPUT_COMPONENT
                  : !strcmp(argv[1],"composite")?CC_INPUT_COMPOSITE:CC_INPUT_SVIDEO;
        secs=atoi(argv[2]); out=argv[3];
        if(argc>4) cfg.ring_mb=atoi(argv[4]);
        if(argc>5) scratch=argv[5];
    } else { fprintf(stderr,"usage: %s <input> <secs> <out> [ringMB] [scratchDir] [--fail-stop-control-loss] | --replay <in> <out> [paceUS] [scratchDir] [--fail-stop-control-loss]\n",argv[0]); return 9; }
    char staged[PATH_MAX]={0}; const char *sink_path=out;
    int publish=strcmp(out,"/dev/null")!=0;
    if(publish){
        if(stage_path(out,scratch,staged)<0) return 1;
        sink_path=staged;
    }
    char session_note[256];
    int ring_mb=cfg.ring_mb>0?cfg.ring_mb:256;
    if(cfg.replay_path)
        snprintf(session_note,sizeof session_note,
                 "shuttle-capture v1 input=replay mode_word=n/a ring_mb=%d fleet=n/a control_loss=%s",
                 ring_mb,cfg.fail_stop_on_control_loss?"fail-stop":"continue");
    else
        snprintf(session_note,sizeof session_note,
                 "shuttle-capture v1 input=%s mode_word=0x%08x ring_mb=%d fleet=8+8 control_loss=%s",
                 input_name(cfg.input),mode_word(cfg.input),ring_mb,
                 cfg.fail_stop_on_control_loss?"fail-stop":"continue");
    if(cc_tagged_sink_open(&g_k,sink_path,session_note)!=CC_OK){
        perror(sink_path); if(publish) unlink(staged); return 1;
    }
    cc_callbacks cb; cc_tagged_sink_callbacks(g_k,&cb); cb.on_end=end_cb;
    int rc=cc_open(&g_s,&cfg,&cb);
    if(rc!=CC_OK){
        fprintf(stderr,"open: %s\n",cc_strerror(rc));
        cc_tagged_sink_close(g_k); if(publish) unlink(staged); return 2;
    }
    rc=cc_start(g_s);
    if(rc!=CC_OK){
        fprintf(stderr,"start: %s\n",cc_strerror(rc));
        cc_close(g_s);
        cc_tagged_sink_close(g_k);
        if(publish) unlink(staged);
        return 2;
    }
    if(cfg.replay_path){ while(!atomic_load(&g_done)) usleep(50000); }
    else { for(int i=0;i<secs*10 && !atomic_load(&g_done);i++) usleep(100000); }
    cc_stop(g_s);
    enum cc_end end_reason=(enum cc_end)atomic_load(&g_end_reason);
    cc_stats st; cc_get_stats(g_s,&st);
    printf("video %.1f MB | audio %.1f MB | iso_err=%ld xfer_err=%ld resub=%ld/%ld\n",
           st.bytes[0]/1e6,st.bytes[1]/1e6,st.iso_errors,st.transfer_errors,
           st.resubmit_failures,st.resubmit_recovered);
    printf("lost v=%llu a=%llu B | zero=%ld short=%ld | ring high=%zu/%zu | fleet %d+%d/%d\n",
           (unsigned long long)st.lost_bytes[0],(unsigned long long)st.lost_bytes[1],
           st.zero_len_packets,st.short_packets,st.ring_high_water,st.ring_size,
           st.fleet[0],st.fleet[1],st.fleet_size);
    printf("end=%s | control_records_dropped=%ld control_loss_markers=%ld\n",
           end_name(end_reason),st.control_records_dropped,st.control_loss_markers);
    cc_close(g_s);
    int krc=cc_tagged_sink_close(g_k);
    if(krc!=CC_OK){
        fprintf(stderr,"SINK WRITE FAILURE; partial capture retained at %s\n",sink_path);
        return 3;
    }
    if(publish && rename(staged,out)<0){
        perror("atomic capture publish");
        fprintf(stderr,"complete capture retained at %s\n",staged);
        return 4;
    }
    return end_reason==CC_END_STOPPED || end_reason==CC_END_REPLAY_EOF ? 0 : 5;
}
