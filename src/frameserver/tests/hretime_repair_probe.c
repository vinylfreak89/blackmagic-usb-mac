/* Actual worker repair evidence; CSV and selected source/output rasters are
 * buffered until worker join. This diagnostic is not linked into production. */
#include <assert.h>
#include <stdio.h>
#define hrt_apply untraced_apply
#include "../hretime.c"
#undef hrt_apply
enum { PROBE_UNITS=1024, UNIT_BYTES=48+525*1440 };
typedef struct {
    uint64_t counter;int field,line,action,shift,flagged,spill;
    double left,right,expected[2],precision;
    int reason;double rline,rnn,limit,normal[2],spread[2],error[2];
    int exterior[2];
} repair_trace;
static repair_trace trace[PROBE_UNITS*480];static size_t count;
static const char *prefix,*capture;
enum { PICTURES=40 };
static uint8_t before[PICTURES][UNIT_BYTES],after[PICTURES][UNIT_BYTES];
static uint64_t saved_counter[PICTURES];static int saved_field[PICTURES],saved_count;
static int wanted(uint64_t c) {
    static const uint64_t t[]={74,107,493,494,495,496,497,498,499,500,775,848,927};
    if(!strcmp(capture,"tape1")){for(unsigned i=0;i<sizeof t/sizeof *t;i++)if(c==t[i])return 1;}
    return (!strcmp(capture,"cap4") && (c==204 || c==232)) ||
           (!strcmp(capture,"cap3") && (c==13547 || c==14058 || c==13723)) ||
           (!strcmp(capture,"pan") && (c==3211 || c==3214 || c==3264)) ||
           (!strcmp(capture,"cap2") && c==1972);
}
static FILE *output(const char *suffix) {
    char path[4096];assert(snprintf(path,sizeof path,"%s%s",prefix,suffix)<(int)sizeof path);
    FILE *f=fopen(path,"wx");if(!f){perror(path);abort();}return f;
}
static void finish(FILE *f) {int bad=ferror(f);if(fclose(f)||bad)abort();}
static void dump(void) {
    FILE *f=output(".actions.csv");
    fputs("capture,counter,field,line,action,shift,left,right,width,expected_width,expected_left,expected_right,width_precision,flagged,spill,reason,rline,rnn,limit,normal_left,normal_right,spread_left,spread_right,left_error,right_error,exterior_left,exterior_right\n",f);
    for(size_t i=0;i<count;i++) {
        repair_trace *r=trace+i;
        fprintf(f,"%s,%llu,%d,%d,%c,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%d,%d,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%d,%d\n",
            capture,(unsigned long long)r->counter,r->field,r->line,"NRIUC"[r->action],r->shift,
            r->left,r->right,r->right-r->left,r->expected[1]-r->expected[0],
            r->expected[0],r->expected[1],r->precision,r->flagged,r->spill,r->reason,r->rline,r->rnn,r->limit,
            r->normal[0],r->normal[1],r->spread[0],r->spread[1],r->error[0],r->error[1],r->exterior[0],r->exterior[1]);
    }
    finish(f);
    for(int i=0;i<saved_count;i++)for(int a=0;a<2;a++) {
        char suffix[80];snprintf(suffix,sizeof suffix,".%llu.f%d.%s.uyvy",(unsigned long long)saved_counter[i],saved_field[i],a?"after":"before");
        f=output(suffix);assert(fwrite((a?after[i]:before[i])+HEADER,1,525*ROW_BYTES,f)==525*ROW_BYTES);finish(f);
    }
}
__attribute__((constructor)) static void init(void) {
    prefix=getenv("HRT_REPAIR_PREFIX");capture=getenv("HRT_REPAIR_CAPTURE");
    if(!prefix || !capture){fputs("HRT_REPAIR_PREFIX and HRT_REPAIR_CAPTURE required\n",stderr);abort();}
    assert(!atexit(dump));
}
void hrt_apply(hrt_workspace *w,const uint8_t *f1,const uint8_t *f2,
               int d1,int d2,uint8_t *out1,uint8_t *out2,hrt_result *o) {
    untraced_apply(w,f1,f2,d1,d2,out1,out2,o);
    assert(count+480<=PROBE_UNITS*480);
    for(int j=0;j<480;j++) {
        repair_boundary *b=w->repair+j;
        trace[count++]=(repair_trace){w->counter[j&1],(j&1)+1,line_number(j,d1,d2),
            o->action[j],o->shift[j],w->flagged[j],b->spill,b->edge[0],b->edge[1],
            {w->expected[j][0],w->expected[j][1]},w->width_precision[j],o->reason[j],
            o->r_line[j],o->r_neighbours[j],o->correlation_limit[j&1],
            {o->edge_median[j&1][0],o->edge_median[j&1][1]},
            {o->edge_spread[j&1][0],o->edge_spread[j&1][1]},{b->error[0],b->error[1]},
            {w->exterior[j&1][0],w->exterior[j&1][1]}};
    }
    for(int k=0;k<2;k++)if(wanted(w->counter[k])) {
        assert(saved_count<PICTURES);int i=saved_count++;
        saved_counter[i]=w->counter[k];saved_field[i]=k+1;
        memcpy(before[i],k?f2:f1,UNIT_BYTES);memcpy(after[i],k?out2:out1,UNIT_BYTES);
    }
}
