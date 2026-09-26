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
    v=getenv("GE_VOTE_PAIR_MIN");
    if(v) {
        errno=0;double n=strtod(v,&end);
        if(errno || end==v || *end || !isfinite(n) || n < -1 || n > 1) {
            fprintf(stderr,"invalid GE_VOTE_PAIR_MIN: %s (expected finite number in [-1,1])\n",v);return 0;
        }
        ge_vote_pair_min=n;
    }
    v=getenv("GE_BOTTOM_FLAT_MARGIN");
    if(v) {
        errno=0;double n=strtod(v,&end);
        if(errno || end==v || *end || !isfinite(n) || n<=0) {
            fprintf(stderr,"invalid GE_BOTTOM_FLAT_MARGIN: %s (expected positive finite number)\n",v);return 0;
        }
        ge_bottom_flat_margin=n;
    }
    v=getenv("GE_COMB_RIGID_CLARITY");
    if(v) {
        errno=0;double n=strtod(v,&end);
        if(errno || end==v || *end || !isfinite(n) || n<1) {
            fprintf(stderr,"invalid GE_COMB_RIGID_CLARITY: %s (expected finite number >=1)\n",v);return 0;
        }
        ge_comb_rigid_clarity=n;
    }
    return 1;
}
static void ge_tool_controls_echo(FILE *f) {
    fprintf(f,"# GE_WAVE_BAR=%.17g GE_WAVE_CLAMP=%d GE_COMB_REJECT=%.17g GE_ANCHOR_VOTE=%d GE_LEVEL_FILL=%d GE_LEVEL_FLAT=%d GE_VOTE_PAIR=%d GE_VOTE_PAIR_MIN=%.17g GE_BOTTOM_FLAT=%d GE_BOTTOM_FLAT_MARGIN=%.17g GE_VOTE_BLANKSPOT=%d GE_COMB_STILL=%d GE_COMB_MOTION_MIN=%d GE_COMB_RIGID=%d GE_COMB_RIGID_CLARITY=%.17g\n",
        ge_wave_bar,ge_wave_clamp,ge_comb_reject,1,1,0,1,ge_vote_pair_min,1,ge_bottom_flat_margin,1,1,1,1,ge_comb_rigid_clarity);
}
#endif
