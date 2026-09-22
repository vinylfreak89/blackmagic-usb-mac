/* Streaming acceptance/cost instrument. stdin records: native uint64 counter,
 * uint32 reset, uint32 pair_next, followed by GE_PIXELS bytes of luma.
 * Preserve the matching probe/engine sources when building a baseline: older
 * engines do not necessarily expose the current experiment-control variables.
 * Optional argv[1]: frame CSV from a separate, all-frame-audit engine. The
 * measured engine remains non-audit, so its cost retains production semantics.
 * Optional argv[2]: exact production decision trace, written outside timing.
 * Enabled reversed units wait one unit for their final field-2 interpretation.
 * No capture paths, outputs or goldens are compiled into the instrument. */
#define _POSIX_C_SOURCE 200809L
#include "geometry_engine.h"
#include "geometry_tool_controls.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "decision_trace.h"
static double cpu(void) {
    struct timespec t;
    if(clock_gettime(CLOCK_THREAD_CPUTIME_ID,&t))abort();
    return t.tv_sec+t.tv_nsec*1e-9;
}
static void frames(FILE *f,const ge_decision *out,unsigned n) {
    for(unsigned i=0;i<n;i++)if(out[i].has_frame) {
        const ge_decision *d=out+i;
        fprintf(f,"%llu,%llu,%d,%d,%d,%d,%.17g,%d,%u,%d,%d,%d,%d,%d,%s,%s,%d,%d,%d,%d,%u,%u,%d,%d,%.17g\n",
            (unsigned long long)d->counter,(unsigned long long)d->top_unit,
            d->frame_d1,d->frame_d2,d->comb_ran,d->comb.shift,
            d->comb.margin,d->comb.decided,d->triggers,d->held,
            d->first[0],d->first[1],d->interpreted_first[0],d->interpreted_first[1],
            ge_class_name(d->motion[0]),ge_class_name(d->motion[1]),d->top_ignored[0],d->top_ignored[1],
            d->top_overrun_veto[0],d->top_overrun_veto[1],d->overrun_terms[0],d->overrun_terms[1],
            d->prev_comb_known,d->prev_comb_d,d->prev_comb_margin);
    }
}
typedef struct { uint64_t counter,hash;ge_features f;double measure,engine; } unit_row;
static void unit(FILE *file,const unit_row *u,const ge_features *current) {
    const ge_features *f=&u->f;
    fprintf(file,"%llu,%d,%d,%d,%d,%d,%d,%.17g,%.17g,%llu,",
        (unsigned long long)u->counter,f->first[0],f->first[1],f->last[0],f->last[1],
        f->bottom[0],f->bottom[1],f->blank[0],f->blank[1],(unsigned long long)u->hash);
#ifdef GE_HBLANK
    fprintf(file,"%.17g,%.17g,%d,%d,",f->hblank_level[0],f->hblank_level[1],f->hblank_cols[0],f->hblank_cols[1]);
#else
    fprintf(file,",,,,");
#endif
    fprintf(file,"%d,%d,%d,%.17g,%.9f,%.9f,%d,%d,%.17g,%.17g,%d,%d,%s,%s,%d,%d,%u,%u\n",
        f->rule_first,f->auto_first,f->plain23,f->runin,u->measure,u->engine,
        current->interpreted_first[0],current->interpreted_first[1],f->top_distance[0],f->top_distance[1],
        current->top_ignored[0],current->top_ignored[1],ge_class_name(current->motion[0]),ge_class_name(current->motion[1]),
        current->top_overrun_veto[0],current->top_overrun_veto[1],current->overrun_terms[0],current->overrun_terms[1]);
}
int main(int argc,char **argv) {
    if(argc>3){fputs("usage: hblank_probe [audit-frames.csv [production-decisions.csv]]\n",stderr);return 2;}
    if(!ge_tool_controls_from_env())return 2;
    uint8_t *y=malloc(GE_PIXELS);geometry_engine *g=malloc(ge_size());
    if(!y||!g)return 2;
    FILE *audit_file=NULL;geometry_engine *audit=NULL;
    FILE *trace=NULL;
    if(argc==3){trace=fopen(argv[2],"w");if(!trace){perror("decision trace");return 2;}decision_trace_header(trace);}
    if(argc>=2) {
        audit_file=fopen(argv[1],"w");audit=malloc(ge_size());
        if(!audit_file||!audit){perror("audit output/allocation");return 2;}
        ge_tool_controls_echo(audit_file);
        fputs("counter,top_unit,frame_d1,frame_d2,comb_ran,comb_d,comb_margin,comb_decided,triggers,held,f1_first,f2_first,interpreted_f1_first,interpreted_f2_first,class_f1,class_f2,top_ignored_f1,top_ignored_f2,top_overrun_veto_f1,top_overrun_veto_f2,overrun_terms_f1,overrun_terms_f2,prev_comb_known,prev_comb_d,prev_comb_margin\n",audit_file);
    }
    int mode=-1;uint64_t counter;uint32_t reset,pair;ge_decision out[2];
    unit_row pending={0};int have_pending=0;
    ge_tool_controls_echo(stdout);
    puts("counter,f1_first,f2_first,f1_last,f2_last,bottom_f1,bottom_f2,blank_f1,blank_f2,profile_hash,level_f1,level_f2,cols_f1,cols_f2,rule_first,auto_first,plain23,runin,measure_ms,engine_ms,interpreted_f1_first,interpreted_f2_first,top_distance_f1,top_distance_f2,top_ignored_f1,top_ignored_f2,class_f1,class_f2,top_overrun_veto_f1,top_overrun_veto_f2,overrun_terms_f1,overrun_terms_f2");
    while(fread(&counter,sizeof counter,1,stdin)==1) {
        if(fread(&reset,sizeof reset,1,stdin)!=1||fread(&pair,sizeof pair,1,stdin)!=1||
           fread(y,1,GE_PIXELS,stdin)!=GE_PIXELS){fputs("short probe record\n",stderr);return 2;}
        ge_features f;double t=cpu();ge_measure(y,&f);double measure=(cpu()-t)*1000;
        uint64_t hash=14695981039346656037ull;
        const unsigned char *p=(const unsigned char *)f.profile;
        for(size_t i=0;i<sizeof f.profile;i++){hash^=p[i];hash*=1099511628211ull;}
        if((int)pair!=mode){
            if(mode>=0){
                unsigned n=ge_break(g,out);if(trace)decision_trace(trace,out,n);
                if(have_pending){unit(stdout,&pending,ge_completed_features(g));have_pending=0;}
                if(audit)frames(audit_file,out,ge_break(audit,out));
            }
            ge_init(g,pair,0);if(audit)ge_init(audit,pair,1);mode=pair;
        }
        t=cpu();unsigned n=ge_push(g,y,counter,reset,out);double engine=(cpu()-t)*1000;
        if(trace)decision_trace(trace,out,n);
        unit_row row={.counter=counter,.hash=hash,.f=f,.measure=measure,.engine=engine};
        if(ge_top_overrun_veto && pair) {
            if(n){
                if(!have_pending || out[0].counter!=pending.counter)return 3;
                unit(stdout,&pending,ge_completed_features(g));have_pending=0;
            }
            pending=row;have_pending=1;
        } else unit(stdout,&row,ge_current_features(g));
        if(audit)frames(audit_file,out,ge_push(audit,y,counter,reset,out));
    }
    int bad=ferror(stdin)||ferror(stdout);
    if(mode>=0) {
        unsigned n=ge_break(g,out);if(trace)decision_trace(trace,out,n);
        if(have_pending)unit(stdout,&pending,ge_completed_features(g));
    }
    if(trace){if(ferror(trace))bad=1;if(fclose(trace))bad=1;}
    if(audit){if(mode>=0)frames(audit_file,out,ge_break(audit,out));if(fclose(audit_file))bad=1;}
    if(fflush(stdout)==EOF)bad=1;
    free(audit);free(y);free(g);return bad?2:0;
}
