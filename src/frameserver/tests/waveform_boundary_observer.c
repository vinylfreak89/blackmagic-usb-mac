/* Standalone diagnostic link: invoke the exact repair, then observe raw input.
 * All traces are buffered and written after the replay worker has joined. */
#include <assert.h>
#include <stdio.h>
#include <time.h>
#define hrt_apply unobserved_apply
#include "../hretime.c"
#undef hrt_apply
#include "waveform_boundary.h"
enum { WB_MAX_UNITS=1024 };
typedef struct { wb_edge edge[2];int action,line; } wb_row;
typedef struct {
    uint64_t source[2],ns;wb_row rows[480];
} wb_unit;
static wb_unit units[WB_MAX_UNITS];static size_t count;
static const char *prefix;
static uint64_t wb_cpu(void) {
    struct timespec t;assert(!clock_gettime(CLOCK_THREAD_CPUTIME_ID,&t));
    return (uint64_t)t.tv_sec*1000000000u+t.tv_nsec;
}
static FILE *wb_open(const char *suffix) {
    char path[4096];assert(snprintf(path,sizeof path,"%s%s",prefix,suffix)<(int)sizeof path);
    FILE *f=fopen(path,"wx");if(!f){perror(path);abort();}return f;
}
static void wb_close(FILE *f) {int bad=ferror(f);if(fclose(f)||bad)abort();}
static void wb_dump(void) {
    FILE *f=wb_open(".boundary.csv");
    fputs("frame,counter,field,woven,line,action,side,status,position,uncertainty,blank,noise,picture,rise\n",f);
    for(size_t i=0;i<count;i++)for(int j=0;j<480;j++)for(int s=0;s<2;s++) {
        wb_unit *u=units+i;wb_row *r=u->rows+j;wb_edge *e=r->edge+s;
        fprintf(f,"%llu,%llu,%d,%d,%d,%c,%c,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n",
            (unsigned long long)u->source[1],(unsigned long long)u->source[j&1],
            (j&1)+1,j,r->line,"NRIUC"[r->action],s?'R':'L',e->status,
            e->position,e->uncertainty,e->blank,e->noise,e->picture,e->rise);
    }
    wb_close(f);f=wb_open(".locator_cpu.csv");fputs("f1_counter,f2_counter,locator_ms\n",f);
    for(size_t i=0;i<count;i++)fprintf(f,"%llu,%llu,%.9f\n",
        (unsigned long long)units[i].source[0],(unsigned long long)units[i].source[1],units[i].ns/1e6);
    wb_close(f);
}
__attribute__((constructor)) static void wb_init(void) {
    prefix=getenv("HRT_BOUNDARY_PREFIX");
    if(!prefix || !*prefix){fputs("HRT_BOUNDARY_PREFIX required\n",stderr);abort();}
    assert(!atexit(wb_dump));
}
void hrt_apply(hrt_workspace *w,const uint8_t *f1,const uint8_t *f2,
               int d1,int d2,uint8_t *out1,uint8_t *out2,hrt_result *o) {
    unobserved_apply(w,f1,f2,d1,d2,out1,out2,o);
    assert(count<WB_MAX_UNITS);wb_unit *u=units+count++;
    u->source[0]=w->counter[0];u->source[1]=w->counter[1];
    uint64_t begin=wb_cpu();wb_level vi[2]={wb_vi(f1,0),wb_vi(f2,1)};
    for(int j=0;j<480;j++) {
        wb_row *r=u->rows+j;r->action=o->action[j];r->line=line_number(j,d1,d2);
        for(int s=0;s<2;s++)r->edge[s]=w->row[j]?wb_measure(w->y[j],s,vi[j&1]):
            (wb_edge){0,NAN,NAN,NAN,NAN,NAN,0};
    }
    u->ns=wb_cpu()-begin;
}
