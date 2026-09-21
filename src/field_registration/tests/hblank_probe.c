/* Streaming acceptance/cost instrument. stdin records: native uint64 counter,
 * uint32 reset, uint32 pair_next, followed by GE_PIXELS bytes of luma.
 * Build without GE_HBLANK against an older engine for a paired baseline replay.
 * No capture paths, outputs or goldens are compiled into the instrument. */
#define _POSIX_C_SOURCE 200809L
#include "geometry_engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
static double cpu(void) {
    struct timespec t;
    if(clock_gettime(CLOCK_THREAD_CPUTIME_ID,&t))abort();
    return t.tv_sec+t.tv_nsec*1e-9;
}
int main(void) {
    uint8_t *y=malloc(GE_PIXELS);geometry_engine *g=malloc(ge_size());
    if(!y||!g)return 2;
    int mode=-1;uint64_t counter;uint32_t reset,pair;ge_decision out[2];
    puts("counter,f1_first,f2_first,f1_last,f2_last,bottom_f1,bottom_f2,blank_f1,blank_f2,profile_hash,level_f1,level_f2,cols_f1,cols_f2,measure_ms,engine_ms");
    while(fread(&counter,sizeof counter,1,stdin)==1) {
        if(fread(&reset,sizeof reset,1,stdin)!=1||fread(&pair,sizeof pair,1,stdin)!=1||
           fread(y,1,GE_PIXELS,stdin)!=GE_PIXELS){fputs("short probe record\n",stderr);return 2;}
        ge_features f;double t=cpu();ge_measure(y,&f);double measure=(cpu()-t)*1000;
        uint64_t hash=14695981039346656037ull;
        const unsigned char *p=(const unsigned char *)f.profile;
        for(size_t i=0;i<sizeof f.profile;i++){hash^=p[i];hash*=1099511628211ull;}
        if((int)pair!=mode){if(mode>=0)ge_break(g,out);ge_init(g,pair,0);mode=pair;}
        t=cpu();ge_push(g,y,counter,reset,out);double engine=(cpu()-t)*1000;
        printf("%llu,%d,%d,%d,%d,%d,%d,%.17g,%.17g,%llu,",
            (unsigned long long)counter,f.first[0],f.first[1],f.last[0],f.last[1],
            f.bottom[0],f.bottom[1],f.blank[0],f.blank[1],(unsigned long long)hash);
#ifdef GE_HBLANK
        printf("%.17g,%.17g,%d,%d,",f.hblank_level[0],f.hblank_level[1],f.hblank_cols[0],f.hblank_cols[1]);
#else
        printf(",,,,");
#endif
        printf("%.9f,%.9f\n",measure,engine);
    }
    int bad=ferror(stdin)||ferror(stdout);free(y);free(g);return bad?2:0;
}
