/* Acceptance/CPU-cost driver; input metadata: counter eligible reset (one per raster).
 * No capture paths or captured data are embedded in this instrument. */
#define _POSIX_C_SOURCE 200809L
#include "../geometry_engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <string.h>
static double cpu(void){struct timespec t;if(clock_gettime(CLOCK_THREAD_CPUTIME_ID,&t))abort();return t.tv_sec+t.tv_nsec*1e-9;}
static void emit(const ge_decision *d,double us,double comb_us){
    printf("%llu,%d,%d,%d,%d,%d,%llu,%d,%d,%d,%d,%d,%u,%d,%d,%.12g,%s,%d,%d,%d,%d,%d,%d,%s,%s,%.6f,%.6f\n",
      (unsigned long long)d->counter,d->d1,d->d2,d->unused1,d->unused2,d->reset_before,
      (unsigned long long)d->top_unit,d->has_frame,d->frame_d1,d->frame_d2,d->published_d,d->held,
      d->triggers,d->comb_ran,d->comb.shift,d->comb.margin,d->comb_ran?"LOW":"HIGH",
      d->first[0],d->first[1],d->last[0],d->last[1],d->bottom[0],d->bottom[1],
      ge_class_name(d->motion[0]),ge_class_name(d->motion[1]),us,comb_us);
}
int main(int argc,char **argv){
    if(argc!=4){fprintf(stderr,"usage: geometry_probe luma.u8 metadata.txt pair_next\n");return 2;}
    FILE *raw=fopen(argv[1],"rb"),*meta=fopen(argv[2],"r");
    geometry_engine *g=malloc(ge_size());uint8_t *y=malloc(GE_PIXELS),*prev=malloc(GE_PIXELS);
    if(!raw||!meta||!g||!y||!prev){perror("probe input/allocation");return 2;}
    int reverse=atoi(argv[3]);ge_init(g,reverse,1);uint64_t pc=0;int have_prev=0;
    puts("counter_extended,applied_d1,applied_d2,f1_unused,f2_unused,reset_before,top_unit,has_frame,frame_d1,frame_d2,published_d,held,triggers,comb_ran,comb_d,comb_margin,confidence,f1_first,f2_first,f1_last,f2_last,bl1,bl2,class_f1,class_f2,engine_us,comb_us");
    unsigned long long c;int eligible,reset;ge_decision out[2];
    while(fscanf(meta,"%llu %d %d",&c,&eligible,&reset)==3){
        if(fread(y,1,GE_PIXELS,raw)!=GE_PIXELS){fprintf(stderr,"short raster\n");return 2;}
        if(!eligible){unsigned n=ge_break(g,out);for(unsigned i=0;i<n;i++)emit(out+i,0,0);have_prev=0;continue;}
        double t=cpu();unsigned n=ge_push(g,y,c,reset,out);double us=(cpu()-t)*1e6,cu=0;
        if(!reverse || (have_prev && c==pc+1)){
            t=cpu();ge_comb_result r=ge_comb(y,reverse?prev:y);cu=(cpu()-t)*1e6;
            /* A second call checks determinism, not a substitute oracle. */
            if(n && out[n-1].has_frame && (r.shift!=out[n-1].comb.shift || r.margin!=out[n-1].comb.margin))abort();
        }
        for(unsigned i=0;i<n;i++)emit(out+i,us,cu);
        memcpy(prev,y,GE_PIXELS);pc=c;have_prev=1;
    }
    unsigned n=ge_break(g,out);for(unsigned i=0;i<n;i++)emit(out+i,0,0);
    int bad=ferror(raw)||ferror(meta)||ferror(stdout);fclose(raw);fclose(meta);free(g);free(y);free(prev);return bad?2:0;
}
