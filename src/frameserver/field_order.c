#include "field_order.h"
#include <math.h>
#include <string.h>

void fo_reset(fo_detector *d) { memset(d,0,sizeof *d); }
static double median(double *a,unsigned n) {
    for(unsigned i=1;i<n;i++) {
        double x=a[i];unsigned j=i;
        while(j && a[j-1]>x){a[j]=a[j-1];--j;}a[j]=x;
    }
    return (a[(n-1)/2]+a[n/2])*0.5;
}
static double threshold(const double *history,unsigned n) {
    double a[FO_HISTORY];memcpy(a,history,n*sizeof *a);
    double m=median(a,n);
    for(unsigned i=0;i<n;i++)a[i]=fabs(history[i]-m);
    /* Six robust sigmas AND a threefold change; code floor is half the
     * measured ~16-code black/blank separation (CLAUDE §6). */
    return fmax(8.0,fmax(3.0*m,m+6.0*1.4826*median(a,n)));
}
static void episode(fo_detector *d,fo_evidence *e,uint64_t counter) {
    unsigned mask=e->spikes;
    if(!d->episode) {
        if(mask){d->first=counter;d->episode=(int)mask;}
        return;
    }
    if(mask) {
        /* Only slot2 followed immediately by slot1 is a supported split. */
        d->episode=d->episode==2 && mask==1?4:5;
        return;
    }
    e->cut_first=d->first;
    e->event=d->episode==3?1:d->episode==4?2:3;
    d->episode=0;
    if(e->event==3){d->votes=0;d->last_verdict=0;}
    else {
        if(d->last_verdict!=e->event)d->votes=0;
        d->last_verdict=e->event;
        if(d->votes<2)++d->votes;
        e->confirmed=d->votes==2;
    }
    e->votes=d->votes;
}
fo_evidence fo_observe(fo_detector *d,const uint8_t *y,uint64_t counter,
                       uint64_t epoch,int broken) {
    fo_evidence e={0};
    if(broken || (d->have_previous &&
       (epoch!=d->epoch || counter!=d->counter+1)))fo_reset(d);
    if(!y){fo_reset(d);return e;}
    e.measured=d->have_previous;e.ready=e.measured && d->count>=FO_WARMUP;
    for(int k=0;k<2;k++) {
        const uint8_t *p=y+(20+263*k)*FO_WIDTH;
        if(e.measured) {
            unsigned sum=0;
            for(unsigned i=0;i<FO_ROWS*FO_WIDTH;i++) {
                int delta=(int)p[i]-d->previous[k][i];sum+=(unsigned)(delta<0?-delta:delta);
            }
            e.change[k]=(double)sum/(FO_ROWS*FO_WIDTH);
            if(e.ready) {
                e.threshold[k]=threshold(d->history[k],d->count);
                if(e.change[k]>e.threshold[k])e.spikes|=1u<<k;
            }
            d->history[k][d->cursor]=e.change[k];
        }
        memcpy(d->previous[k],p,FO_ROWS*FO_WIDTH);
    }
    if(e.ready)episode(d,&e,counter);
    if(e.measured) {
        if(d->count<FO_HISTORY)++d->count;
        d->cursor=(d->cursor+1)%FO_HISTORY;
    }
    d->counter=counter;d->epoch=epoch;d->have_previous=1;
    return e;
}
