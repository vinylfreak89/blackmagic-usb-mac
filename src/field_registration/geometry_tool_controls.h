/* Tool-only startup helper. Do not include in the engine or frameserver library.
 * Both replay and measurement tools use exactly this parser and provenance line. */
#ifndef GEOMETRY_TOOL_CONTROLS_H
#define GEOMETRY_TOOL_CONTROLS_H
#include "geometry_engine.h"
#include <errno.h>
#include <math.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
static int ge_tool_controls_from_env(void) {
    /* Retired controls must not silently produce a different experiment arm. */
    const char *old[]={"GE_TOP_MARGIN","GE_TOP_GUARD","GE_TOP_PLAIN23","GE_TOP_RUNIN",
                       "GE_TOP_NEAR_BLANK","GE_TOP_OVERRUN_VETO"};
    for(unsigned i=0;i<sizeof old/sizeof *old;i++)if(getenv(old[i])) {
        fprintf(stderr,"retired control %s: waveform engine uses GE_WAVE_BAR and GE_WAVE_CLAMP\n",old[i]);return 0;
    }
    const char *v=getenv("GE_WAVE_BAR");char *end;
    if(v) {
        errno=0;double n=strtod(v,&end);
        if(errno || end==v || *end || !isfinite(n)) {
            fprintf(stderr,"invalid GE_WAVE_BAR: %s (expected finite number)\n",v);return 0;
        }
        ge_wave_bar=n;
    }
    v=getenv("GE_WAVE_CLAMP");
    if(v) {
        errno=0;long n=strtol(v,&end,10);
        if(errno || end==v || *end || n<0 || n>INT_MAX) {
            fprintf(stderr,"invalid GE_WAVE_CLAMP: %s (expected nonnegative int)\n",v);return 0;
        }
        ge_wave_clamp=(int)n;
    }
    v=getenv("GE_COMB_REJECT");
    if(v) {
        errno=0;double n=strtod(v,&end);
        if(errno || end==v || *end || !isfinite(n) || n<=0) {
            fprintf(stderr,"invalid GE_COMB_REJECT: %s (expected positive finite number)\n",v);return 0;
        }
        ge_comb_reject=n;
    }
    const char *names[]={"GE_ANCHOR_VOTE","GE_LEVEL_FILL","GE_LEVEL_FLAT"};
    int *values[]={&ge_anchor_vote,&ge_level_fill,&ge_level_flat};
    for(unsigned i=0;i<3;i++)if((v=getenv(names[i]))) {
        if((v[0]!='0' && v[0]!='1') || v[1]) {
            fprintf(stderr,"invalid %s: %s (expected 0 or 1)\n",names[i],v);return 0;
        }
        *values[i]=v[0]-'0';
    }
    return 1;
}
static void ge_tool_controls_echo(FILE *f) {
    fprintf(f,"# GE_WAVE_BAR=%.17g GE_WAVE_CLAMP=%d GE_COMB_REJECT=%.17g GE_ANCHOR_VOTE=%d GE_LEVEL_FILL=%d GE_LEVEL_FLAT=%d\n",
        ge_wave_bar,ge_wave_clamp,ge_comb_reject,ge_anchor_vote,ge_level_fill,ge_level_flat);
}
#endif
