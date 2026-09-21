/* Streaming acceptance/cost instrument. stdin records: native uint64 counter,
 * uint32 reset, uint32 pair_next, followed by GE_PIXELS bytes of luma.
 * Preserve the matching probe/engine sources when building a baseline: older
 * engines do not necessarily expose the current experiment-control variables.
 * Optional argv[1]: frame CSV from a separate, all-frame-audit engine. The
 * measured engine remains non-audit, so its cost retains production semantics.
 * No capture paths, outputs or goldens are compiled into the instrument. */
#define _POSIX_C_SOURCE 200809L
#include "geometry_engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <errno.h>
#include <math.h>
static int boolean_control(const char *name,int *out) {
    const char *v=getenv(name);
    if(!v)return 1;
    if(v[0] && !v[1] && (v[0]=='0' || v[0]=='1')){*out=v[0]-'0';return 1;}
    fprintf(stderr,"invalid %s: %s (expected 0 or 1)\n",name,v);return 0;
}
static int controls(void) {
    const char *v=getenv("GE_TOP_MARGIN");char *end;
    if(v) {
        errno=0;double n=strtod(v,&end);
        if(errno || end==v || *end || !isfinite(n)) {
            fprintf(stderr,"invalid GE_TOP_MARGIN: %s (expected finite number)\n",v);return 0;
        }
        ge_top_margin=n;
    }
    v=getenv("GE_TOP_GUARD");
    if(v) {
        errno=0;long n=strtol(v,&end,10);
        if(errno || end==v || *end || n<0 || n>4) {
            fprintf(stderr,"invalid GE_TOP_GUARD: %s (expected integer 0..4)\n",v);return 0;
        }
        ge_top_guard=(int)n;
    }
    return boolean_control("GE_TOP_PLAIN23",&ge_top_plain23) &&
           boolean_control("GE_TOP_RUNIN",&ge_top_runin);
}
static void provenance(FILE *f) {
    fprintf(f,"# GE_TOP_MARGIN=%.17g GE_TOP_GUARD=%d GE_TOP_PLAIN23=%d GE_TOP_RUNIN=%d\n",
        ge_top_margin,ge_top_guard,ge_top_plain23,ge_top_runin);
}
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
    if(!controls())return 2;
    uint8_t *y=malloc(GE_PIXELS);geometry_engine *g=malloc(ge_size());
    if(!y||!g)return 2;
    FILE *audit_file=NULL;geometry_engine *audit=NULL;
    if(argc==2) {
        audit_file=fopen(argv[1],"w");audit=malloc(ge_size());
        if(!audit_file||!audit){perror("audit output/allocation");return 2;}
        provenance(audit_file);
        fputs("counter,top_unit,frame_d1,frame_d2,comb_ran,comb_d,comb_margin,comb_decided,triggers,held\n",audit_file);
    }
    int mode=-1;uint64_t counter;uint32_t reset,pair;ge_decision out[2];
    provenance(stdout);
    puts("counter,f1_first,f2_first,f1_last,f2_last,bottom_f1,bottom_f2,blank_f1,blank_f2,profile_hash,level_f1,level_f2,cols_f1,cols_f2,rule_first,auto_first,plain23,runin,measure_ms,engine_ms");
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
        printf("%d,%d,%d,%.17g,%.9f,%.9f\n",f.rule_first,f.auto_first,f.plain23,f.runin,measure,engine);
    }
    int bad=ferror(stdin)||ferror(stdout);
    if(audit){if(mode>=0)frames(audit_file,out,ge_break(audit,out));if(fclose(audit_file))bad=1;}
    free(audit);free(y);free(g);return bad?2:0;
}
