// shuttle-capture — thin CLI over capture_core. Same jobs as capture_tagged_bench, now via the library:
//   shuttle-capture <input> <secs> <out.tpc> [ringMB] [scratchDir]      capture
//   shuttle-capture --replay <in.tpc> <out.tpc|/dev/null> [paceUS] [scratchDir]
// Optional trailing --stall-s N (default 120, at least ten pacing intervals).
// CC_LIFECYCLE_S overrides the 60 s startup/stop/finalization watchdog for tests.
// Exit 3: sink write failure. Exit 6: stall or lifecycle/output deadline expired.
#include "capture_core.h"
#include <errno.h>
#include <limits.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include "../tool_deadline.h"
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
    tool_deadline_start("shuttle-capture",6);
    double lifecycle_s=tool_seconds(getenv("CC_LIFECYCLE_S"),60), stall_s=120;
    tool_guard("open output / cc_open / cc_start",lifecycle_s);
    cc_config cfg={0}; const char *out=NULL; int secs=0;
    const char *scratch="/private/tmp/blackmagic-usb-mac";
    for (;;) {
        if(argc>1 && !strcmp(argv[argc-1],"--fail-stop-control-loss")){
            cfg.fail_stop_on_control_loss=1; argc--;
        } else if(argc>2 && !strcmp(argv[argc-2],"--stall-s")) {
            stall_s=tool_seconds(argv[argc-1],120); argc-=2;
        } else break;
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
    } else { fprintf(stderr,"usage: %s <input> <secs> <out> [ringMB] [scratchDir] [--fail-stop-control-loss] | --replay <in> <out> [paceUS] [scratchDir] [--stall-s N] [--fail-stop-control-loss]\n",argv[0]); return 9; }
    char staged[PATH_MAX]={0}; const char *sink_path=out;
    int publish=strcmp(out,"/dev/null")!=0;
    if(publish){
        if(stage_path(out,scratch,staged)<0) return 1;
        sink_path=staged;
    }
    char session_note[256];
    int ring_mb=cfg.ring_mb>0?cfg.ring_mb:CC_DEFAULT_RING_MB;
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
    tool_guard(NULL,0);
    if(cfg.replay_path){
        uint64_t seen=cc_packets_delivered(g_s);
        double last=tool_clock(), limit=tool_stall_seconds(stall_s,cfg.replay_pace_us);
        while(!atomic_load(&g_done)) {
            usleep(20000);
            if(atomic_load(&g_done)) break;
            uint64_t now=cc_packets_delivered(g_s);
            if(now!=seen) { seen=now; last=tool_clock(); }
            else if(tool_clock()-last>=limit && !atomic_load(&g_done))
                tool_timeout("no capture-core packet delivery before stall deadline; partial capture retained");
        }
    }
    else if(getenv("CC_REG_SWEEP") && atoi(getenv("CC_REG_SWEEP"))>=6){
        /* Measurement, 2026-10-05: the vendor driver writes the mode word (input select) and THEN register 4, and
         * the mode word carries a 7.5 IRE setup bit (wire byte 0, 0x08) that ours has always had on.
         *   CC_REG_SWEEP=6  setup bit off and on, alternating every half second
         *   CC_REG_SWEEP=7  register 4 in the driver's order (mode word, register 4, latch): two seconds as found,
         *                   two with one byte a quarter down, cycling luma, Cb, Cr
         * Every write is listed beside the capture with its time; everything is put back and read back at the end. */
        int variant=atoi(getenv("CC_REG_SWEEP")); uint32_t mode0=0, gain0=0; int ok=1;
        if(cc_debug_register(g_s,0,0,&mode0)!=CC_OK || cc_debug_register(g_s,0,4,&gain0)!=CC_OK) ok=0;
        uint32_t want = 0x09000000u|(cfg.input==CC_INPUT_COMPONENT?0x02000000u:cfg.input==CC_INPUT_COMPOSITE?0x04000000u:0x06000000u)|0x30000000u;
        if(ok && mode0!=want){ fprintf(stderr,"register 0 reads %08x, not the mode word this capture wrote (%08x); not sweeping\n",mode0,want); ok=0; }
        char sweep_path[PATH_MAX]; snprintf(sweep_path,sizeof sweep_path,"%s.regsweep.csv",out);
        FILE *sw=ok?fopen(sweep_path,"w"):NULL;
        if(!sw) fprintf(stderr,"register sweep not started; capturing without it\n");
        else fprintf(sw,"ms_since_start,register,value_hex,what\n0,0,%08x,as found\n0,4,%08x,as found\n",mode0,gain0);
        double t0=tool_clock(); int state=0;
        for(int i=0;i<secs*10 && !atomic_load(&g_done);i++){
            unsigned ms=(unsigned)((tool_clock()-t0)*1000);
            if(sw && i>=20 && i<(secs-3)*10){                       /* the first two and last three seconds alone */
                if(variant==6 && i%5==0){
                    int on=state&1; int rc=cc_debug_mode_order(g_s,on,NULL);
                    fprintf(sw,"%u,0,%08x,setup %s%s\n",ms,on?want:(want&~0x08000000u),on?"on":"off",rc==CC_OK?"":" FAILED"); state++;
                } else if(variant==7 && i%20==0){
                    int phase=state%6; uint32_t v=gain0; const char *what="as found";
                    if(phase%2){ int b=phase/2, sh=24-8*b; uint32_t x=gain0>>sh&0xff; v=(gain0&~(0xffu<<sh))|((x-x/4)<<sh); what=b==0?"luma byte down a quarter":b==1?"Cb byte down a quarter":"Cr byte down a quarter"; }
                    int rc=cc_debug_mode_order(g_s,1,&v);
                    fprintf(sw,"%u,4,%08x,mode+4+latch %s%s\n",ms,v,what,rc==CC_OK?"":" FAILED"); state++;
                }
                fflush(sw);
            }
            usleep(100000);
        }
        if(sw){
            int rc=cc_debug_mode_order(g_s,1,&gain0); uint32_t m=0,g=0; cc_debug_register(g_s,0,0,&m); cc_debug_register(g_s,0,4,&g);
            fprintf(sw,"%u,0,%08x,final restore%s; reads back mode %08x reg4 %08x\n",(unsigned)((tool_clock()-t0)*1000),want,rc==CC_OK?"":" FAILED",m,g);
            if(m!=mode0||g!=gain0) fprintf(stderr,"REGISTERS NOT RESTORED: mode %08x->%08x, reg4 %08x->%08x\n",mode0,m,gain0,g);
            fclose(sw); printf("register sweep written to %s\n",sweep_path);
        }
    }
    else if(getenv("CC_REG_SWEEP")){
        /* Measurement: find what the unexplained registers do. One value is changed, held, and put back, cycling
         * through a list for the whole capture; every write is listed beside the capture with its time. All six
         * registers are read first and left as found.
         *   CC_REG_SWEEP=1  4, 8, 28, 32: plain writes, a second each, a quarter down
         *   CC_REG_SWEEP=2  the same, each write followed by the latch, two seconds each, halved
         *   CC_REG_SWEEP=3  the same, followed by the mode word and the latch
         *   CC_REG_SWEEP=4  4 and 8 with the mode word and the latch; 36 set to the value the vendor driver was
         *                   seen to write and to zero, 20 set to zero (the values bmusb's notes record), with the latch
         * Results, S-Video, 2026-10-02: =1 and =2 change nothing in the picture; 28 is the audio level of our two
         * channels (half the value, -6 dB), applied after the point where a hot input clips. */
        enum { PLAIN, LATCH, MODE };
        typedef struct { uint16_t index; int byte; uint32_t value; int apply; } sweep_step;   /* byte -1: every byte; -2: value as given */
        int variant=atoi(getenv("CC_REG_SWEEP")), dwell=variant>=2?20:10, cut=variant>=2?2:4, apply=variant>=3?MODE:variant==2?LATCH:PLAIN;
        /* the audio registers come third and fourth so that, started with the tape, they fall on its silent cards */
        const sweep_step basic[]={{4,0,0,apply},{4,1,0,apply},{28,-1,0,apply},{32,-1,0,apply},{4,2,0,apply},{8,0,0,apply},{8,1,0,apply},{8,2,0,apply}};
        const sweep_step wider[]={{4,0,0,MODE},{4,1,0,MODE},{36,-2,0x8036802au,LATCH},{36,-2,0,LATCH},{4,2,0,MODE},{8,0,0,MODE},{8,1,0,MODE},{8,2,0,MODE},{20,-2,0,LATCH}};
        /* =5: register 36 alone, zero for three seconds and as found for three, to see whether it changes what the
         * Shuttle sends for an unstable input (a deck rewinding or stopped) */
        const sweep_step only36[]={{36,-2,0,LATCH}};
        const sweep_step *steps=variant>=5?only36:variant>=4?wider:basic;
        const unsigned nsteps=variant>=5?1:variant>=4?sizeof wider/sizeof *wider:sizeof basic/sizeof *basic;
        if(variant>=5) dwell=30;
        const uint16_t regs[6]={4,8,28,32,20,36}; uint32_t orig[6]={0}; int ok=1;
        for(int r=0;r<6;r++) if(cc_debug_register(g_s,0,regs[r],&orig[r])!=CC_OK) ok=0;
        if(ok && variant>=4 && (orig[4]!=0x0000ffffu || orig[5]!=0x801e8000u)){
            fprintf(stderr,"registers 20/36 read %08x/%08x, not the values this sweep knows how to restore; not sweeping them\n",orig[4],orig[5]); ok=0;
        }
        char sweep_path[PATH_MAX]; snprintf(sweep_path,sizeof sweep_path,"%s.regsweep.csv",out);
        FILE *sw=ok?fopen(sweep_path,"w"):NULL;
        if(!sw) fprintf(stderr,"register sweep not started; capturing without it\n");
        else {
            fprintf(sw,"ms_since_start,register,value_hex,what\n");
            for(int r=0;r<6;r++) fprintf(sw,"0,%u,%08x,as found\n",regs[r],orig[r]);
        }
        double t0=tool_clock(); int changed=-1, changed_apply=PLAIN;
        for(int i=0;i<secs*10 && !atomic_load(&g_done);i++){
            if(sw && i%dwell==0){
                int sec=i/dwell; uint32_t v; unsigned ms=(unsigned)((tool_clock()-t0)*1000);
                if(changed>=0){                                   /* put the last one back */
                    v=orig[changed]; int rc=cc_debug_register(g_s,1,regs[changed],&v);
                    if(changed_apply!=PLAIN && rc==CC_OK) rc=cc_debug_relatch(g_s,changed_apply==MODE);
                    fprintf(sw,"%u,%u,%08x,restored%s\n",ms,regs[changed],v,rc==CC_OK?"":" FAILED"); changed=-1;
                } else if(sec>=2 && i<(secs-4)*10){               /* leave the first and last seconds alone */
                    const sweep_step *st=&steps[(unsigned)(sec/2-1)%nsteps]; int r=0; while(regs[r]!=st->index) r++;
                    if(st->byte==-2) v=st->value;
                    else if(st->byte<0){ v=0; for(int b=0;b<4;b++){ uint32_t x=orig[r]>>(24-8*b)&0xff; v|=(x-x/cut)<<(24-8*b); } }   /* down by 1/cut */
                    else { int sh=24-8*st->byte; uint32_t x=orig[r]>>sh&0xff; v=(orig[r]&~(0xffu<<sh))|((x-x/cut)<<sh); }
                    int rc=cc_debug_register(g_s,1,st->index,&v);
                    if(st->apply!=PLAIN && rc==CC_OK) rc=cc_debug_relatch(g_s,st->apply==MODE);
                    fprintf(sw,"%u,%u,%08x,changed%s%s\n",ms,st->index,v,st->apply==MODE?" +mode+latch":st->apply==LATCH?" +latch":"",rc==CC_OK?"":" FAILED");
                    changed=r; changed_apply=st->apply;
                }
                fflush(sw);
            }
            usleep(100000);
        }
        if(sw){
            for(int r=0;r<6;r++){ uint32_t v=orig[r]; int rc=cc_debug_register(g_s,1,regs[r],&v); if(r==5 && variant>=2) cc_debug_relatch(g_s,variant>=3);
                uint32_t back=0; cc_debug_register(g_s,0,regs[r],&back);
                fprintf(sw,"%u,%u,%08x,final restore%s reads back %08x\n",(unsigned)((tool_clock()-t0)*1000),regs[r],v,rc==CC_OK?"":" FAILED",back);
                if(back!=orig[r]) fprintf(stderr,"REGISTER %u NOT RESTORED: found %08x, now %08x\n",regs[r],orig[r],back); }
            fclose(sw); printf("register sweep written to %s\n",sweep_path);
        }
    }
    else { for(int i=0;i<secs*10 && !atomic_load(&g_done);i++) usleep(100000); }
    tool_guard("cc_stop",lifecycle_s);
    cc_stop(g_s);
    tool_guard("final accounting/output, cc_close and sink flush/close",lifecycle_s);
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
    tool_guard("publish completed capture and flush terminal output",lifecycle_s);
    if(publish && rename(staged,out)<0){
        perror("atomic capture publish");
        fprintf(stderr,"complete capture retained at %s\n",staged);
        return 4;
    }
    fflush(stdout); fflush(stderr);
    return end_reason==CC_END_STOPPED || end_reason==CC_END_REPLAY_EOF ? 0 : 5;
}
