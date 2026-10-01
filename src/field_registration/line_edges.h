#ifndef LINE_EDGES_H
#define LINE_EDGES_H
/* Per-line horizontal timing measurement on the delivered 720-sample luma row.
 * Shared by registration (is a field's top line normally timed? which lines
 * may the comb count?) and the H-timing repair. Measurement only: no policy.
 *
 * A row is a time sweep of 720 of the line's 858 samples; the Shuttle never
 * delivers the other 138, which normally fall in horizontal blanking. A badly
 * timed line can carry its blanking anywhere in the row (seen mid-row on tvc2's
 * top-of-field flag, 2026-10-01: a ~146-sample run against the nominal 147). */
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
/* Header-only: every includer gets private copies; a test wrapper may define LE_API empty to export them. */
#ifndef LE_API
#define LE_API static __attribute__((unused))
#endif
#define LE_PRIVATE static __attribute__((unused))

enum {
    /* Picture evidence at an edge: codes above blanking. Black with setup
     * measured ~16 codes above blanking, and the pan's dark edge content
     * reached 30; 40 is ~18 IRE. */
    LE_PICTURE_MIN=40,
    /* "A few samples": the falloff rises over ~3 samples, and the pan's
     * cross-field left-edge disagreement was 3.0 at the 99.9th percentile. */
    LE_FEW=4,
    /* Coarse threshold: the first rise above the blanking bumps seen before
     * the falloff (<=16 codes on tape1), below most picture. */
    LE_COARSE=20,
    LE_BLANKING=147, /* nominal horizontal blanking width, samples */
    LE_WIDTH=720
};

typedef enum { LE_UNMEASURED=0, /* no sharp falloff into picture of at least LE_PICTURE_MIN */
               LE_MEASURED=1,   /* sub-sample half-height falloff position */
               LE_SPILL=2       /* picture already at the window edge: no blanking on that side */
} le_state;

typedef struct {
    float left, right;          /* half-height falloff positions; NAN unless MEASURED */
    float level_left, level_right; /* picture level just inside each falloff; NAN if none */
    uint8_t left_state, right_state;
    uint8_t gap_sharp;          /* both ends of the interior run are sharp falloffs */
    int16_t gap_start, gap_end; /* longest interior blanking-level run [start,end), -1 if none */
} le_line;

/* Blanking level of a field: median luma of nine vertical-interval rows
 * (storage rows 7-15 for field 1, 270-278 for field 2) of a 525x720 luma plane. */
LE_API double le_blank_level(const uint8_t *luma,int field);
/* Measure one 720-sample luma row against its field's blanking level. */
LE_API void le_measure_line(const uint8_t *row,double blank,le_line *out);

LE_API double le_blank_level(const uint8_t *luma,int field) {
    unsigned h[256]={0};int start=field?270:7;
    for(int r=start;r<start+9;r++)for(int x=0;x<LE_WIDTH;x++)h[luma[r*LE_WIDTH+x]]++;
    unsigned n=9*LE_WIDTH,count=0;double at=(n-1)*0.5;unsigned lo=(unsigned)at,hi=(unsigned)ceil(at);
    int a=-1,b=-1;
    for(int i=0;i<256;i++){count+=h[i];if(a<0 && count>lo)a=i;if(count>hi){b=i;break;}}
    return a+(at-lo)*(b-a);
}
/* Median of n<=16 samples. */
LE_PRIVATE double le_small_median(const uint8_t *v,int n) {
    int s[16];for(int i=0;i<n;i++)s[i]=v[i];
    for(int i=1;i<n;i++)for(int k=i;k>0 && s[k-1]>s[k];k--){int t=s[k];s[k]=s[k-1];s[k-1]=t;}
    return n&1?s[n/2]:(s[n/2-1]+s[n/2])/2.0;
}
/* Sample 719 is the window's attenuated last sample, never picture. */
#define LE_LAST 718
/* A rise from blanking into picture starting below index x (left side) is a
 * falloff when it climbs 20%->80% of its step within 2*FEW samples; a ramp of
 * dark picture up from blanking is not. dir=+1 rises to the right, -1 to the left. */
LE_PRIVATE int le_sharp_rise(const uint8_t *y,int x,int dir,double blank,double inside) {
    double lo=blank+.2*(inside-blank),hi=blank+.8*(inside-blank);
    int a=x;while(a-dir>=0 && a-dir<=LE_LAST && y[a-dir]>=lo)a-=dir;  /* back to the rise start */
    int c=a;while(c>=0 && c<=LE_LAST && y[c]<hi && abs(c-a)<=2*LE_FEW)c+=dir;
    return c>=0 && c<=LE_LAST && y[c]>=hi && abs(c-a)<=2*LE_FEW;
}
/* Edge seen from one side: dir=+1 scans the left edge rightwards from 0,
 * dir=-1 the right edge leftwards from LE_LAST. */
LE_PRIVATE void le_edge(const uint8_t *y,int dir,double blank,float *pos,float *level,uint8_t *state,int *coarse) {
    double thr=blank+LE_COARSE;int x0=dir>0?0:LE_LAST;
    *pos=NAN;*level=NAN;*state=LE_UNMEASURED;*coarse=-1;
    if(y[x0]>=thr && y[x0+dir]>=thr && y[x0+2*dir]>=thr){*state=LE_SPILL;*coarse=x0;return;}
    int x=x0;while(x>=0 && x<=LE_LAST && y[x]<thr)x+=dir;
    if(x<0 || x>LE_LAST)return;
    *coarse=x;
    int a=dir>0?x+2:x-11;if(a<0)a=0;if(a+10>LE_LAST+1)a=LE_LAST+1-10;
    double inside=le_small_median(y+a,10);*level=(float)inside;
    if(inside-blank<LE_PICTURE_MIN || !le_sharp_rise(y,x,dir,blank,inside))return;
    double h=blank+.5*(inside-blank);
    int p=x;while(p>=0 && p<=LE_LAST && y[p]<h)p+=dir;
    if(p<0 || p>LE_LAST || p==x0)return;
    double frac=(h-y[p-dir])/(double)(y[p]-y[p-dir]);
    *pos=(float)(p-dir+dir*frac);*state=LE_MEASURED;
}
LE_API void le_measure_line(const uint8_t *y,double blank,le_line *o) {
    int cl,cr;
    le_edge(y,+1,blank,&o->left,&o->level_left,&o->left_state,&cl);
    le_edge(y,-1,blank,&o->right,&o->level_right,&o->right_state,&cr);
    /* Longest blanking-level run strictly inside the row's picture span. */
    o->gap_start=o->gap_end=-1;o->gap_sharp=0;
    if(cl<0 || cr<0 || cr<=cl)return;
    double thr=blank+LE_COARSE;int best=0;
    for(int x=cl;x<=cr;) {
        if(y[x]>=thr){x++;continue;}
        int e=x;while(e<=cr && y[e]<thr)e++;
        if(e-x>best){best=e-x;o->gap_start=(int16_t)x;o->gap_end=(int16_t)e;}
        x=e;
    }
    if(o->gap_start<0)return;
    /* Both ends must be falloffs into picture of at least LE_PICTURE_MIN. */
    int s=o->gap_start,e=o->gap_end;
    int a=s-10;if(a<0)a=0;if(s-a<1)return;double before=le_small_median(y+a,s-a);
    int b=e+1;if(b+10>LE_LAST+1)b=LE_LAST+1-10;double after=le_small_median(y+b,10);
    o->gap_sharp=before-blank>=LE_PICTURE_MIN && after-blank>=LE_PICTURE_MIN &&
                 le_sharp_rise(y,s-1,-1,blank,before) && le_sharp_rise(y,e,+1,blank,after);
}

#endif
