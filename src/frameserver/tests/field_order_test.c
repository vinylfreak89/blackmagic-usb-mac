#include "../field_order.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static fo_detector d;
static uint8_t y[525*720];
static uint64_t counter;
static fo_evidence step(int f1,int f2) {
    memset(y+20*720,f1,60*720);memset(y+283*720,f2,60*720);
    return fo_observe(&d,y,counter++,1,0);
}
static void warm(int f1,int f2) { for(int i=0;i<35;i++)assert(!step(f1,f2).event); }
static void start(void) { fo_reset(&d);counter=100;warm(20,20); }
int main(void) {
    start();assert(step(200,200).spikes==3);
    fo_evidence e=step(200,200);assert(e.event==1 && e.votes==1 && !e.confirmed && e.cut_first==135);
    warm(200,200);step(20,20);e=step(20,20);
    assert(e.event==1 && e.votes==2 && e.confirmed);
    start();assert(step(20,200).spikes==2);assert(step(200,200).spikes==1);
    e=step(200,200);assert(e.event==2 && e.votes==1 && !e.confirmed);
    warm(200,200);step(200,20);step(20,20);e=step(20,20);
    assert(e.event==2 && e.confirmed);
    /* An unsupported order, unpaired spike or multi-unit burst cannot vote. */
    warm(20,20);step(200,20);step(200,200);e=step(200,200);
    assert(e.event==3 && !e.confirmed && e.votes==0);
    warm(200,200);step(20,200);e=step(20,200);assert(e.event==3);
    warm(20,200);step(200,20);step(20,200);e=step(20,200);assert(e.event==3);
    /* Opposite verdict restarts consistency. */
    warm(20,200);step(200,20);e=step(200,20);assert(e.event==1 && e.votes==1);
    warm(200,20);step(200,200);step(20,200);e=step(20,200);
    assert(e.event==2 && e.votes==1 && !e.confirmed);
    /* No cross-gap/cross-epoch comparisons; explicit break catches counter aliases. */
    counter+=2;e=step(20,200);assert(!e.measured && !e.event && d.votes==0);
    warm(20,200);e=fo_observe(&d,y,counter++,2,0);assert(!e.measured);
    warm(20,200);e=fo_observe(&d,y,counter++,1,1);assert(!e.measured);
    warm(20,200);fo_observe(&d,NULL,counter++,1,0);assert(!d.have_previous);
    /* No event before warmup; stable/ramp content does not force a verdict. */
    fo_reset(&d);
    for(int i=0;i<FO_WARMUP;i++)assert(!step(i&1?200:20,i&1?200:20).event);
    start();for(int i=0;i<100;i++)assert(!step(20+i,20+i).event);
    puts("field_order: aligned/reversed consistency, ambiguous episodes, warmup and adjacency PASS");
}
