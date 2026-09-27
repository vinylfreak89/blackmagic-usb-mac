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
} repair_trace;
static repair_trace trace[PROBE_UNITS*480];static size_t count;
static uint8_t before[2][UNIT_BYTES],after[2][UNIT_BYTES];
static int saved[2];static const char *prefix,*capture;
static FILE *output(const char *suffix) {
    char path[4096];assert(snprintf(path,sizeof path,"%s%s",prefix,suffix)<(int)sizeof path);
    FILE *f=fopen(path,"wx");if(!f){perror(path);abort();}return f;
}
static void finish(FILE *f) {int bad=ferror(f);if(fclose(f)||bad)abort();}
static void dump(void) {
    FILE *f=output(".actions.csv");
    fputs("capture,counter,field,line,action,shift,left,right,width,expected_width,expected_left,expected_right,width_precision,flagged,spill\n",f);
    for(size_t i=0;i<count;i++) {
        repair_trace *r=trace+i;
        fprintf(f,"%s,%llu,%d,%d,%c,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%d,%d\n",
            capture,(unsigned long long)r->counter,r->field,r->line,"NRIUC"[r->action],r->shift,
            r->left,r->right,r->right-r->left,r->expected[1]-r->expected[0],
            r->expected[0],r->expected[1],r->precision,r->flagged,r->spill);
    }
    finish(f);
    for(int i=0;i<2;i++)if(saved[i])for(int a=0;a<2;a++) {
        char suffix[80];snprintf(suffix,sizeof suffix,".%d.%s.uyvy",i?848:494,a?"after":"before");
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
            {w->expected[j][0],w->expected[j][1]},w->width_precision[j]};
    }
    if(!strcmp(capture,"tape1") && (w->counter[0]==494 || w->counter[0]==848)) {
        int i=w->counter[0]==848;assert(!saved[i]);saved[i]=1;
        memcpy(before[i],f1,UNIT_BYTES);memcpy(after[i],out1,UNIT_BYTES);
    }
}
