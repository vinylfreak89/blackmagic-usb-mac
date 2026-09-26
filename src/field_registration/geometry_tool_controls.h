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
/* A single parser serves both tools. Parse into a copy: rejection never partly
 * updates the caller's configuration. Error text and numeric syntax are stable. */
static int ge_tool_double(const char *name,double *out,double lo,double hi,
                          int strict_lo,const char *expected) {
    const char *v=getenv(name);if(!v)return 1;
    char *end;errno=0;double n=strtod(v,&end);
    if(errno || end==v || *end || !isfinite(n) || n<lo || n>hi || (strict_lo && n==lo)) {
        fprintf(stderr,"invalid %s: %s (expected %s)\n",name,v,expected);return 0;
    }
    *out=n;return 1;
}
static int ge_tool_int(const char *name,int *out,int lo,int hi,const char *expected) {
    const char *v=getenv(name);if(!v)return 1;
    char *end;errno=0;long n=strtol(v,&end,10);
    if(errno || end==v || *end || n<lo || n>hi) {
        fprintf(stderr,"invalid %s: %s (expected %s)\n",name,v,expected);return 0;
    }
    *out=(int)n;return 1;
}
static int ge_tool_controls_from_env(ge_config *config) {
    ge_config c=*config;
    if(!ge_tool_double("GE_WAVE_BAR",&c.wave_bar,-INFINITY,INFINITY,0,"finite number") ||
       !ge_tool_int("GE_WAVE_CLAMP",&c.wave_clamp,0,INT_MAX,"nonnegative int") ||
       !ge_tool_double("GE_COMB_REJECT",&c.comb_reject,0,INFINITY,1,"positive finite number") ||
       !ge_tool_double("GE_VOTE_PAIR_MIN",&c.vote_pair_min,-1,1,0,"finite number in [-1,1]") ||
       !ge_tool_double("GE_BOTTOM_FLAT_MARGIN",&c.bottom_flat_margin,0,INFINITY,1,"positive finite number") ||
       !ge_tool_double("GE_COMB_RIGID_CLARITY",&c.rigid_clarity,1,INFINITY,0,"finite number >=1") ||
       !ge_tool_double("GE_COMB_BASIN_FACTOR",&c.comb_basin_factor,1,INFINITY,0,"finite number >=1") ||
       !ge_tool_int("GE_VOTE_WINDOW",&c.vote_window,1,GE_VOTE_CAPACITY,"integer in [1,256]") ||
       !ge_tool_double("GE_VOTE_BLANKSPOT_TOLERANCE",&c.blankspot_tolerance,0,INFINITY,0,"nonnegative finite number") ||
       !ge_tool_int("GE_COMB_RIGID_MIN",&c.rigid_min,1,INT_MAX,"positive int"))return 0;
    *config=c;return 1;
}
static void ge_tool_controls_echo(FILE *f,const ge_config *c) {
    fprintf(f,"# GE_WAVE_BAR=%.17g GE_WAVE_CLAMP=%d GE_COMB_REJECT=%.17g GE_ANCHOR_VOTE=%d GE_LEVEL_FILL=%d GE_LEVEL_FLAT=%d GE_VOTE_PAIR=%d GE_VOTE_PAIR_MIN=%.17g GE_BOTTOM_FLAT=%d GE_BOTTOM_FLAT_MARGIN=%.17g GE_VOTE_BLANKSPOT=%d GE_COMB_STILL=%d GE_COMB_MOTION_MIN=%d GE_COMB_RIGID=%d GE_COMB_RIGID_CLARITY=%.17g\n",
        c->wave_bar,c->wave_clamp,c->comb_reject,1,1,0,1,c->vote_pair_min,1,c->bottom_flat_margin,1,1,1,1,c->rigid_clarity);
    if(c->comb_basin_factor!=1.5 || c->vote_window!=30 ||
       c->blankspot_tolerance!=2 || c->rigid_min!=2)
        fprintf(stderr,"# GE_COMB_BASIN_FACTOR=%.17g GE_VOTE_WINDOW=%d GE_VOTE_BLANKSPOT_TOLERANCE=%.17g GE_COMB_RIGID_MIN=%d\n",
                c->comb_basin_factor,c->vote_window,c->blankspot_tolerance,c->rigid_min);
}
#endif
