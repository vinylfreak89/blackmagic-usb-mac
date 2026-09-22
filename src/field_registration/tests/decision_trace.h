/* Probe-only exact non-audit decision trace. Also compiles against 9ed3923's
 * public decision struct, so a baseline engine needs no implementation edits. */
#ifndef GE_DECISION_TRACE_H
#define GE_DECISION_TRACE_H
static void decision_trace_header(FILE *f) {
    fputs("counter,top_unit,has_frame,d1,d2,frame_d1,frame_d2,unused1,unused2,reset_before,comb_ran,comb_d,comb_decided,comb_margin,triggers,held,first1,first2,last1,last2,bottom1,bottom2,class1,class2,energies\n",f);
}
static void decision_trace(FILE *f,const ge_decision *out,unsigned n) {
    for(unsigned i=0;i<n;i++) {
        const ge_decision *d=out+i;
        fprintf(f,"%llu,%llu,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%a,%u,%d,%d,%d,%d,%d,%d,%d,%d,%d,",
            (unsigned long long)d->counter,(unsigned long long)d->top_unit,d->has_frame,
            d->d1,d->d2,d->frame_d1,d->frame_d2,d->unused1,d->unused2,d->reset_before,
            d->comb_ran,d->comb.shift,d->comb.decided,d->comb.margin,d->triggers,d->held,
            d->first[0],d->first[1],d->last[0],d->last[1],d->bottom[0],d->bottom[1],d->motion[0],d->motion[1]);
        for(int j=0;j<11;j++)fprintf(f,"%s%a",j?" ":"",d->comb.energies[j]);
        fputc('\n',f);
    }
}
#endif
