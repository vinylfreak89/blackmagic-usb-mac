/* Streaming acceptance/cost instrument. stdin records: native uint64 counter,
 * uint32 reset, uint32 pair_next, followed by GE_PIXELS bytes of luma.
 * Preserve the matching probe/engine sources when building a baseline: older
 * engines do not necessarily expose the current experiment-control variables.
 * Optional argv[1]: frame CSV from a separate, all-frame-audit engine. The
 * measured engine remains non-audit, so its cost retains production semantics.
 * No capture paths, outputs or goldens are compiled into the instrument. */
#define _POSIX_C_SOURCE 200809L
#include "geometry_engine.h"
#include "geometry_tool_controls.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
static double cpu(void) {
    struct timespec t;
    if(clock_gettime(CLOCK_THREAD_CPUTIME_ID,&t))abort();
    return t.tv_sec+t.tv_nsec*1e-9;
}
static void frames(FILE *f,const ge_decision *out,unsigned n) {
    for(unsigned i=0;i<n;i++)if(out[i].has_frame) {
        const ge_decision *d=out+i;
        fprintf(f,"%llu,%llu,%d,%d,%d,%d,%.17g,%d,%u,%d\n",
            (unsigned long long)d->counter,(unsigned long long)d->top_unit,
            d->frame_d1,d->frame_d2,d->comb_ran,d->comb.shift,
            d->comb.margin,d->comb.decided,d->triggers,d->held);
    }
}
int main(int argc,char **argv) {
    if(argc>2){fputs("usage: hblank_probe [audit-frames.csv]\n",stderr);return 2;}
    if(!ge_tool_controls_from_env())return 2;
    uint8_t *y=malloc(GE_PIXELS);geometry_engine *g=malloc(ge_size());
    if(!y||!g)return 2;
    FILE *audit_file=NULL;geometry_engine *audit=NULL;
    if(argc==2) {
        audit_file=fopen(argv[1],"w");audit=malloc(ge_size());
        if(!audit_file||!audit){perror("audit output/allocation");return 2;}
        ge_tool_controls_echo(audit_file);
        fputs("counter,top_unit,frame_d1,frame_d2,comb_ran,comb_d,comb_margin,comb_decided,triggers,held\n",audit_file);
    }
    int mode=-1;uint64_t counter;uint32_t reset,pair;ge_decision out[2];
    ge_tool_controls_echo(stdout);
    puts("counter,f1_first,f2_first,f1_last,f2_last,bottom_f1,bottom_f2,blank_f1,blank_f2,profile_hash,level_f1,level_f2,cols_f1,cols_f2,wave_top_f1,wave_step_f1,wave_max_step_f1,wave_status_f1,wave_top_f2,wave_step_f2,wave_max_step_f2,wave_status_f2,measure_ms,engine_ms");
    while(fread(&counter,sizeof counter,1,stdin)==1) {
        if(fread(&reset,sizeof reset,1,stdin)!=1||fread(&pair,sizeof pair,1,stdin)!=1||
           fread(y,1,GE_PIXELS,stdin)!=GE_PIXELS){fputs("short probe record\n",stderr);return 2;}
        ge_features f;double t=cpu();ge_measure(y,&f);double measure=(cpu()-t)*1000;
        uint64_t hash=14695981039346656037ull;
        const unsigned char *p=(const unsigned char *)f.profile;
        for(size_t i=0;i<sizeof f.profile;i++){hash^=p[i];hash*=1099511628211ull;}
        if((int)pair!=mode){
            if(mode>=0){ge_break(g,out);if(audit)frames(audit_file,out,ge_break(audit,out));}
            ge_init(g,pair,0);if(audit)ge_init(audit,pair,1);mode=pair;
        }
        t=cpu();ge_push(g,y,counter,reset,out);double engine=(cpu()-t)*1000;
        if(audit)frames(audit_file,out,ge_push(audit,y,counter,reset,out));
        printf("%llu,%d,%d,%d,%d,%d,%d,%.17g,%.17g,%llu,",
            (unsigned long long)counter,f.first[0],f.first[1],f.last[0],f.last[1],
            f.bottom[0],f.bottom[1],f.blank[0],f.blank[1],(unsigned long long)hash);
#ifdef GE_HBLANK
        printf("%.17g,%.17g,%d,%d,",f.hblank_level[0],f.hblank_level[1],f.hblank_cols[0],f.hblank_cols[1]);
#else
        printf(",,,,");
#endif
        for(int k=0;k<2;k++) {
            if(f.wave[k].first)printf("%d",f.wave[k].first);
            printf(",%.17g,%.17g,%s,",f.wave[k].step,f.wave[k].max_step,ge_wave_status_name(f.wave_status[k]));
        }
        printf("%.9f,%.9f\n",measure,engine);
    }
    int bad=ferror(stdin)||ferror(stdout);
    if(audit){if(mode>=0)frames(audit_file,out,ge_break(audit,out));if(fclose(audit_file))bad=1;}
    free(audit);free(y);free(g);return bad?2:0;
}
