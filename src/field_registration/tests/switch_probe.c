#define _POSIX_C_SOURCE 200809L
/* Diagnostic only: compile the actual engine in this translation unit so
 * its private row predicate can be traced without changing production code.
 * Scalar outputs go to scratch. CAP1 provenance errors abort. */
#include "../field_registration.c"
#include "../../signal_state/signal_state.h"
#include <assert.h>
#include <stdio.h>
#include <time.h>

static field_registration engine;
static signal_state *probe_signal;
static FILE *trace;
static const char *directory;
static unsigned selected_first, selected_last;

static uint64_t now_ns(void) {
    struct timespec t; assert(!clock_gettime(CLOCK_MONOTONIC,&t));
    return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec;
}

static void row_trace(const uint8_t *raster, unsigned counter, int field, int row) {
    const uint8_t *cur=raster+(size_t)row*1440, *above=cur-1440;
    double sum=0, sum2=0; unsigned zero=0;
    for(int x=0;x<720;++x) {
        int v=cur[2*x+1]; sum+=v; sum2+=v*v;
        zero+=(unsigned)abs(v-above[2*x+1]);
    }
    for(int aperture=0;aperture<H_LAG_APERTURES;++aperture) {
        int first=aperture*H_LAG_APERTURE_SAMPLES, past=first+H_LAG_APERTURE_SAMPLES;
        unsigned best=UINT_MAX, at_zero=0; int best_lag=0;
        for(int x=first;x<past;++x) at_zero+=(unsigned)abs(cur[2*x+1]-above[2*x+1]);
        for(int lag=-first;lag<=720-past;++lag) {
            unsigned cost=0;
            for(int x=first;x<past;++x) cost+=(unsigned)abs(cur[2*x+1]-above[2*(x+lag)+1]);
            if(cost<best || (cost==best && abs(lag)<abs(best_lag))) {best=cost;best_lag=lag;}
        }
        fprintf(trace,"%u,%d,%d,%.6f,%.6f,%.6f,%d,%d,%u,%u,%.6f,%d\n",
            counter,field+1,row+4,sum/720,sqrt(fmax(0,sum2/720-(sum/720)*(sum/720))),
            zero/720.0,aperture,best_lag,at_zero,best,at_zero?(double)best/at_zero:1,
            full_other_head_row(raster,row));
    }
}

static void video(void *opaque,const unit_video_observation *unit) {
    (void)opaque;
    assert(!(unit->transport_flags & ~UNIT_FLAG_COUNTER_DISCONTINUITY));
    signal_result sr;
    uint64_t start=now_ns();
    assert(signal_state_classify(probe_signal,unit,NULL,&sr));
    if(sr.actions & SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT)fieldreg_begin_segment(&engine);
    else if(sr.actions & SIGNAL_ACTION_REGISTRATION_DISCONTINUITY)fieldreg_discontinuity(&engine);
    fieldreg_decision d={0}; bool measured=false;
    uint64_t before_engine=now_ns();
    if(sr.normal_picture) measured=fieldreg_process(&engine,unit->bytes,&d);
    else fieldreg_discontinuity(&engine);
    uint64_t end=now_ns();
    if(!unit->fixed_raster_eligible)return;
    printf("%llu,%s,%s,%d,%.6f,%.6f,%d,%d,%d,%d,%d,%d\n",
        (unsigned long long)unit->counter_extended,signal_appearance_name(sr.appearance),
        signal_source_state_name(sr.source),measured,(end-before_engine)/1e6,(end-start)/1e6,
        d.field[0].raw_top,d.field[1].raw_top,d.field[0].switch_line,d.field[1].switch_line,
        d.field[0].band_extent,d.field[1].band_extent);
    if(unit->counter16<selected_first || unit->counter16>selected_last)return;
    const uint8_t *raster=unit->bytes+48;
    char path[1024]; snprintf(path,sizeof path,"%s/%u.pgm",directory,unit->counter16);
    FILE *panel=fopen(path,"wb"); assert(panel); fprintf(panel,"P5\n1440 263\n255\n");
    for(int y=0;y<263;++y) for(int f=0;f<2;++f) for(int x=0;x<720;++x) {
        int row=y+(f?263:0);
        fputc(row<525?raster[(size_t)row*1440+2*x+1]:16,panel);
    }
    assert(!fclose(panel));
    for(int f=0;f<2;++f) for(int row=f?282:20;row<=(f?521:258);++row)
        row_trace(raster,unit->counter16,f,row);
}
static unsigned u32(const uint8_t *b) {return b[0]|b[1]<<8|b[2]<<16|(unsigned)b[3]<<24;}
int main(int argc,char **argv) {
    assert(argc==5); selected_first=(unsigned)strtoul(argv[2],NULL,10);
    selected_last=(unsigned)strtoul(argv[3],NULL,10); directory=argv[4];
    char path[1024];snprintf(path,sizeof path,"%s/rows.csv",directory);trace=fopen(path,"w");assert(trace);
    fputs("counter,field,line,mean,sigma,whole_zero_mad,aperture,best_lag,zero_sad,best_sad,ratio,predicate\n",trace);
    probe_signal=aligned_alloc(signal_state_alignment(),signal_state_size());assert(probe_signal);signal_state_init(probe_signal,NULL);
    fieldreg_config config=fieldreg_default_config();fieldreg_init(&engine,&config);
    unit_parser *parser=aligned_alloc(unit_parser_alignment(),unit_parser_size());assert(parser);
    unit_parser_callbacks cb={.on_video=video};unit_parser_init(parser,NULL,&cb);
    FILE *input=fopen(argv[1],"rb");assert(input);uint8_t h[24];
    puts("counter,appearance,source,measured,engine_ms,core_ms,f1_top_row,f2_top_row,f1_switch_row,f2_switch_row,f1_extent,f2_extent");
    for(;;) {
        size_t n=fread(h,1,24,input);if(!n){assert(!ferror(input));break;}
        assert(n==24 && u32(h)==0x31504143 && h[4]!=1 && h[4]!=2);
        unsigned size=u32(h+20);uint8_t *bytes=malloc(size?size:1);assert(bytes);
        assert(fread(bytes,1,size,input)==size);
        if(h[4]==0) {
            assert(u32(h+12)==0);
            cc_packet p={.endpoint=h[5],.pkt_index=h[6]|h[7]<<8,.submit_seq=u32(h+8),
                .status=0,.req_len=u32(h+16),.actual_len=size,.data=bytes};
            unit_parser_on_packet(parser,&p);
        }
        free(bytes);
    }
    unit_parser_finish(parser);assert(!fclose(input));assert(!fclose(trace));free(parser);free(probe_signal);
}
