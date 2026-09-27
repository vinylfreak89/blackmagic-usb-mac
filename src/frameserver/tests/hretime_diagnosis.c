/* E-62 observer, linked instead of hretime.c only in the diagnostic bench.
 * Branch reconstruction and CSV writing never participate in a decision.
 * Phase CPU covers the original apply call; traces are buffered until exit. */
#include <assert.h>
#include <stdio.h>
#include <time.h>
#include <stdint.h>
static uint64_t stamps[8];
static void diag_phase(int n) {
    struct timespec t;assert(!clock_gettime(CLOCK_THREAD_CPUTIME_ID,&t));
    stamps[n]=(uint64_t)t.tv_sec*1000000000u+(uint64_t)t.tv_nsec;
}
#define HRT_DIAG_PHASE(n) diag_phase(n)
#define hrt_apply untraced_apply
#include "../hretime.c"
#undef hrt_apply
enum { MAX_DIAG_ROWS=16384, MAX_DIAG_UNITS=4096 };
typedef struct {
    uint64_t source,frame;
    int field,line,action,seed,interior,flagged,adjacent[2],temporal,absolute,censored;
    int edges[2],peer_edges[2],offset[2][6],peer_temporal[6],edge_offset[2][2],peer_edge_offset[2];
    unsigned own_move,peer_move;
    double blank,normal[2],spread[2],peer_normal[2],peer_spread[2];
    int named,available;
    uint8_t raw[720],previous[720],peer[720];
} diag_row;
typedef struct { uint64_t c1,c2,ns[7]; } diag_unit;
static diag_row rows[MAX_DIAG_ROWS];static size_t nr;
static diag_unit units[MAX_DIAG_UNITS];static size_t nu;
static uint8_t previous_rows[480][720];
static const char *prefix;
static int named(uint64_t c,int field,int line) {
    if(field==2 && c==74 && line>=423 && line<=432)return 1;
    if(field==2 && c==108 && line>=427 && line<=433)return 1;
    if(field==1 && c==107 && line>=162 && line<=170)return 1;
    if(field==1 && c==109 && line>=163 && line<=171)return 1;
    if(field==1 && (c==494 || c==495 || c==497 || c==500) && line>=23 && line<=44)return 1;
    if(c==232 && ((field==2 && line>=286 && line<=307) ||
                 (field==1 && line>=226 && line<=227)))return 1;
    return 0;
}
static FILE *create(const char *suffix) {
    char path[4096];assert(snprintf(path,sizeof path,"%s%s",prefix,suffix)<(int)sizeof path);
    FILE *f=fopen(path,"wx");if(!f){perror(path);abort();}return f;
}
static void close_checked(FILE *f) {int bad=ferror(f);if(fclose(f)||bad)abort();}
static void vector(FILE *f,const int *v,int n) {
    fputc(',',f);for(int i=0;i<n;i++){if(i)fputc('|',f);if(v[i]==UNKNOWN_OFFSET)fputc('?',f);else fprintf(f,"%d",v[i]);}
}
static void dump(void) {
    FILE *f=create(".phases.csv");
    fputs("f1_counter,f2_counter,materialize_ms,blank_ms,edges_ms,windows_ms,ownership_ms,repair_ms,history_ms\n",f);
    for(size_t i=0;i<nu;i++) {
        fprintf(f,"%llu,%llu",(unsigned long long)units[i].c1,(unsigned long long)units[i].c2);
        for(int p=0;p<7;p++)fprintf(f,",%.9f",units[i].ns[p]/1e6);
        fputc('\n',f);
    }
    close_checked(f);
    f=create(".branches.csv");
    fputs("counter,frame_counter,field,line,action,seed,interior,flagged,above_seed,below_seed,temporal_sides,absolute_sides,censored_sides,own_move,peer_move,blank,left,right,peer_left,peer_right,normal_left,normal_right,spread_left,spread_right,peer_normal_left,peer_normal_right,peer_spread_left,peer_spread_right,temporal,cross,peer_temporal,temporal_edges,cross_edges,peer_temporal_edges,available\n",f);
    for(size_t i=0;i<nr;i++) {
        diag_row *r=rows+i;
        fprintf(f,"%llu,%llu,%d,%d,%c,%d,%d,%d,%d,%d,%d,%d,%d,%u,%u,%.17g,%d,%d,%d,%d",
            (unsigned long long)r->source,(unsigned long long)r->frame,r->field,r->line,
            "NRIUC"[r->action],r->seed,r->interior,r->flagged,r->adjacent[0],r->adjacent[1],
            r->temporal,r->absolute,r->censored,r->own_move,r->peer_move,r->blank,
            r->edges[0],r->edges[1],r->peer_edges[0],r->peer_edges[1]);
        for(int k=0;k<2;k++)fprintf(f,",%.17g",r->normal[k]);
        for(int k=0;k<2;k++)fprintf(f,",%.17g",r->spread[k]);
        for(int k=0;k<2;k++)fprintf(f,",%.17g",r->peer_normal[k]);
        for(int k=0;k<2;k++)fprintf(f,",%.17g",r->peer_spread[k]);
        vector(f,r->offset[0],6);vector(f,r->offset[1],6);vector(f,r->peer_temporal,6);
        vector(f,r->edge_offset[0],2);vector(f,r->edge_offset[1],2);vector(f,r->peer_edge_offset,2);
        fprintf(f,",%d\n",r->available);
    }
    close_checked(f);
    f=create(".raw.csv");fputs("counter,field,line,available,raw_hex,previous_repaired_hex,peer_hex\n",f);
    for(size_t i=0;i<nr;i++)if(rows[i].named) {
        diag_row *r=rows+i;
        fprintf(f,"%llu,%d,%d,%d",(unsigned long long)r->source,r->field,r->line,r->available);
        const uint8_t *p[]={r->raw,r->previous,r->peer};
        for(int a=0;a<3;a++){fputc(',',f);for(int x=0;x<720;x++)fprintf(f,"%02x",p[a][x]);}
        fputc('\n',f);
    }
    close_checked(f);
}
__attribute__((constructor)) static void init(void) {
    prefix=getenv("HRT_DIAG_PREFIX");
    if(!prefix || !*prefix){fputs("HRT_DIAG_PREFIX required\n",stderr);abort();}
    assert(!atexit(dump));
}
void hrt_apply(hrt_workspace *w,const uint8_t *f1,const uint8_t *f2,
               int d1,int d2,uint8_t *out1,uint8_t *out2,hrt_result *o) {
    int d[2]={d1,d2};
    for(int j=0;j<480;j++) {
        int k=j&1,r=first_row(k,d[k])+j/2;
        if(named(w->counter[k],k+1,r+4) && valid_row(k,r) && w->available[k][r])
            memcpy(previous_rows[j],w->previous[k][r],720);
    }
    untraced_apply(w,f1,f2,d1,d2,out1,out2,o);
    assert(nu<MAX_DIAG_UNITS);diag_unit *u=units+nu++;u->c1=w->counter[0];u->c2=w->counter[1];
    for(int p=0;p<7;p++)u->ns[p]=stamps[p+1]-stamps[p];
    for(int j=0;j<480;j++) {
        int k=j&1,r=first_row(k,d[k])+j/2,other=j^1;
        int wanted=named(w->counter[k],k+1,r+4);
        if(!wanted && o->action[j]!=HRT_RETIME && o->action[j]!=HRT_INTERPOLATE)continue;
        assert(nr<MAX_DIAG_ROWS);diag_row *q=rows+nr++;
        q->source=w->counter[k];q->frame=w->counter[1];q->field=k+1;q->line=r+4;
        q->action=o->action[j];q->seed=w->seed[j];q->interior=w->interior[j];q->flagged=w->flagged[j];
        q->adjacent[0]=j>=2?w->seed[j-2]:0;q->adjacent[1]=j+2<480?w->seed[j+2]:0;
        q->own_move=edge_movement(w,o,j);q->peer_move=edge_movement(w,o,other);
        q->blank=o->blank[k];q->named=wanted;q->available=valid_row(k,r)?w->available[k][r]:0;
        memcpy(q->edges,w->edge[j],sizeof q->edges);memcpy(q->peer_edges,w->edge[other],sizeof q->peer_edges);
        memcpy(q->normal,o->edge_median[k],sizeof q->normal);memcpy(q->spread,o->edge_spread[k],sizeof q->spread);
        memcpy(q->peer_normal,o->edge_median[!k],sizeof q->peer_normal);memcpy(q->peer_spread,o->edge_spread[!k],sizeof q->peer_spread);
        memcpy(q->offset[0],o->offset[0][j],sizeof q->offset[0]);memcpy(q->offset[1],o->offset[1][j],sizeof q->offset[1]);
        memcpy(q->peer_temporal,o->offset[0][other],sizeof q->peer_temporal);
        for(int a=0;a<2;a++)memcpy(q->edge_offset[a],o->edge_offset[a][j],sizeof q->edge_offset[a]);
        memcpy(q->peer_edge_offset,o->edge_offset[0][other],sizeof q->peer_edge_offset);
        if(wanted) {
            memcpy(q->raw,w->y[j],720);memcpy(q->peer,w->y[other],720);
            if(q->available)memcpy(q->previous,previous_rows[j],720);
        }
        for(int e=0;e<2;e++) {
            unsigned mask=e?12:3;int bit=1<<e;
            int t=o->edge_offset[0][j][e],p=o->edge_offset[0][other][e];
            int stationary=w->edge[other][e]>=0 && isfinite(o->edge_median[!k][e]) && !(q->peer_move&mask);
            if(!(q->peer_move&mask)) {
                if(t!=UNKNOWN_OFFSET && abs(t)>=MIN_SHIFT && p!=UNKNOWN_OFFSET && abs(p)<MIN_SHIFT)q->temporal|=bit;
                if((q->own_move&mask) && stationary) {
                    q->absolute|=bit;
                    if(e?w->edge[j][e]>=718:w->edge[j][e]==0)q->censored|=bit;
                }
            }
        }
        /* Catch observer drift: reconstructed branch predicates must equal the
         * actual seed bit, not merely resemble the current code. */
        if(w->row[j] && w->row[other] && !excluded(j,d1,d2))assert(q->seed==!!(q->temporal || q->absolute));
    }
}
