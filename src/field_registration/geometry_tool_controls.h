/* Tool-only startup helper. Do not include in the engine or frameserver library.
 * Both replay and measurement tools use exactly this parser and provenance line. */
#ifndef GEOMETRY_TOOL_CONTROLS_H
#define GEOMETRY_TOOL_CONTROLS_H
#include "geometry_engine.h"
#include <errno.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
static int ge_tool_boolean_control(const char *name,int *out) {
    const char *v=getenv(name);
    if(!v)return 1;
    if(v[0] && !v[1] && (v[0]=='0' || v[0]=='1')){*out=v[0]-'0';return 1;}
    fprintf(stderr,"invalid %s: %s (expected 0 or 1)\n",name,v);return 0;
}
static int ge_tool_controls_from_env(void) {
    const char *v=getenv("GE_TOP_MARGIN");char *end;
    if(v) {
        errno=0;double n=strtod(v,&end);
        if(errno || end==v || *end || !isfinite(n)) {
            fprintf(stderr,"invalid GE_TOP_MARGIN: %s (expected finite number)\n",v);return 0;
        }
        ge_top_margin=n;
    }
    v=getenv("GE_TOP_GUARD");
    if(v) {
        errno=0;long n=strtol(v,&end,10);
        if(errno || end==v || *end || n<0 || n>4) {
            fprintf(stderr,"invalid GE_TOP_GUARD: %s (expected integer 0..4)\n",v);return 0;
        }
        ge_top_guard=(int)n;
    }
    v=getenv("GE_TOP_NEAR_BLANK");
    if(v) {
        errno=0;double n=strtod(v,&end);
        if(errno || end==v || *end || !isfinite(n) || (n<0 && n!=-1)) {
            fprintf(stderr,"invalid GE_TOP_NEAR_BLANK: %s (expected -1 or finite nonnegative number)\n",v);return 0;
        }
        ge_top_near_blank=n;
    }
    return ge_tool_boolean_control("GE_TOP_PLAIN23",&ge_top_plain23) &&
           ge_tool_boolean_control("GE_TOP_RUNIN",&ge_top_runin);
}
static void ge_tool_controls_echo(FILE *f) {
    fprintf(f,"# GE_TOP_MARGIN=%.17g GE_TOP_GUARD=%d GE_TOP_PLAIN23=%d GE_TOP_RUNIN=%d GE_TOP_NEAR_BLANK=%.17g\n",
        ge_top_margin,ge_top_guard,ge_top_plain23,ge_top_runin,ge_top_near_blank);
}
#endif
