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
static FILE *geometry;
static const char *directory;
static unsigned selected_first, selected_last;

static uint64_t now_ns(void) {
    struct timespec t; assert(!clock_gettime(CLOCK_MONOTONIC,&t));
    return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec;
}

static void row_trace(const uint8_t *raster, unsigned counter, int field, int row) {
    const uint8_t *cur=raster+(size_t)row*1440;
    double sum=0, sum2=0; unsigned ceiling=0;
    for(int r=field?270:7;r<=(field?278:15);++r)for(int x=0;x<720;++x) {
        unsigned v=raster[(size_t)r*1440+2*x+1];if(v>ceiling)ceiling=v;
    }
    for(int x=0;x<720;++x) {
        int v=cur[2*x+1]; sum+=v; sum2+=v*v;
    }
    horizontal_blanking p=blanking_profile(raster,row,ceiling);
    int first=-1,last=-1,n=0;
    for(int x=0;x<H_SAMPLES;++x)if(p.support[x]) {if(first<0)first=x;last=x;++n;}
    fprintf(trace,"%u,%d,%d,%.6f,%.6f,%u,%d,%d,%d,%d,%d\n",counter,field+1,row+4,
        sum/720,sqrt(fmax(0,sum2/720-(sum/720)*(sum/720))),ceiling,p.readable,
        first,last,n,p.complete_interval);
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
    /* Independent scalar diagnostic of every exact raster, including gated
     * ones; explicitly NOT a registration invocation in the live path. */
    for(int f=0;f<2;++f) {
        field_measurement m;measure_field(unit->bytes+48,f,&m);
        fprintf(geometry,"%u,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",unit->counter16,f+1,
            m.top<0?-1:m.top+4,m.switch_line<0?-1:m.switch_line+4,
            m.first_full_other_head_line<0?-1:m.first_full_other_head_line+4,
            m.bottom<0?-1:m.bottom+4,m.recorded_last<0?-1:m.recorded_last+4,
            m.band_extent,measured,measured?d.field[f].lock_switch_line_count:-1);
    }
    printf("%llu,%s,%s,%d,%.6f,%.6f,%d,%d,%d,%d,%d,%d,%s,%d,%.6f,%.6f,%.6f,%s\n",
        (unsigned long long)unit->counter_extended,signal_appearance_name(sr.appearance),
        signal_source_state_name(sr.source),measured,(end-before_engine)/1e6,(end-start)/1e6,
        d.field[0].raw_top,d.field[1].raw_top,d.field[0].switch_line,d.field[1].switch_line,
        d.field[0].band_extent,d.field[1].band_extent,
        measured?fieldreg_comb_check_name(d.comb_check):"n.a.",d.comb_best_shift,
        d.comb_best_energy,d.comb_second_energy,d.comb_static_fraction,
        fieldreg_parity_state_name(d.parity_state));
    if(unit->counter16<selected_first || unit->counter16>selected_last)return;
    const uint8_t *raster=unit->bytes+48;
    char raw_path[1024];
    snprintf(raw_path,sizeof raw_path,"%s/%u.raw",directory,unit->counter16);
    FILE *raw=fopen(raw_path,"wb");assert(raw);
    assert(fwrite(unit->bytes,1,FIELDREG_UNIT_BYTES,raw)==FIELDREG_UNIT_BYTES);
    assert(!fclose(raw));
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
    fputs("counter,field,line,mean,sigma,blank_ceiling,readable,first_window,last_window,windows,complete_interval\n",trace);
    snprintf(path,sizeof path,"%s/geometry.csv",directory);geometry=fopen(path,"w");assert(geometry);
    fputs("counter,field,top,T,S,bottom,clip,extent,registration_measured,lock_count\n",geometry);
    probe_signal=aligned_alloc(signal_state_alignment(),signal_state_size());assert(probe_signal);signal_state_init(probe_signal,NULL);
    fieldreg_config config=fieldreg_default_config();fieldreg_init(&engine,&config);
    unit_parser *parser=aligned_alloc(unit_parser_alignment(),unit_parser_size());assert(parser);
    unit_parser_callbacks cb={.on_video=video};unit_parser_init(parser,NULL,&cb);
    FILE *input=fopen(argv[1],"rb");assert(input);uint8_t h[24];
    puts("counter,appearance,source,measured,engine_ms,core_ms,f1_top_row,f2_top_row,f1_switch_row,f2_switch_row,f1_extent,f2_extent,comb_check,comb_best_shift,comb_best_energy,comb_second_energy,comb_static_fraction,parity_state");
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
    unit_parser_finish(parser);assert(!fclose(input));assert(!fclose(trace));assert(!fclose(geometry));free(parser);free(probe_signal);
}
