/* Task41 standalone observer. Never included in the production repair path.
 * Numeric rationale is documented in docs/waveform_boundary_observer.md. */
#ifndef WAVEFORM_BOUNDARY_H
#define WAVEFORM_BOUNDARY_H
#include <math.h>
#include <stdint.h>
#include <string.h>
enum { WB_WIDTH=720, WB_SUPPORT=147, WB_HALF=4, WB_PLATEAU=8 };
typedef struct { double level,noise; } wb_level;
typedef struct {
    /* 0 unknown, 1 measured, 2 censored (position is only endpoint bound). */
    int status;
    double position,uncertainty,blank,noise,picture,rise;
} wb_edge;
static double wb_hist_median(const unsigned *h,int n) {
    int a=(n-1)/2,b=n/2,count=0;double lo=-1,hi=0;
    for(int v=0;v<256;v++) {
        count+=(int)h[v];
        if(lo<0 && count>a)lo=v;
        if(count>b){hi=v;break;}
    }
    return (lo+hi)/2;
}
static wb_level wb_hist_stats(const unsigned *h,int n,double floor_noise) {
    double m=wb_hist_median(h,n);unsigned dev[511]={0};
    for(int v=0;v<256;v++)dev[(int)fabs(2*v-2*m)]+=h[v];
    int a=(n-1)/2,b=n/2,count=0,lo=-1,hi=0;
    for(int v=0;v<511;v++) {
        count+=(int)dev[v];if(lo<0 && count>a)lo=v;
        if(count>b){hi=v;break;}
    }
    return (wb_level){m,fmax(floor_noise,1.4826*(lo+hi)/4.0)};
}
static wb_level wb_stats(const uint8_t *y,int n,double floor_noise) {
    unsigned h[256]={0};for(int i=0;i<n;i++)h[y[i]]++;
    return wb_hist_stats(h,n,floor_noise);
}
static wb_level wb_vi(const uint8_t *unit,int field) {
    unsigned h[256]={0};int start=field?270:7;
    for(int r=start;r<start+9;r++)for(int x=0;x<720;x++)
        h[unit[48+r*1440+2*x+1]]++;
    return wb_hist_stats(h,9*720,1/sqrt(12.0));
}
static wb_edge wb_measure(const uint8_t *raw,int side,wb_level vi) {
    uint8_t y[WB_SUPPORT+2*WB_PLATEAU];
    for(int i=0;i<(int)sizeof y;i++)y[i]=raw[side?719-i:i];
    wb_edge best={0,NAN,NAN,vi.level,vi.noise,NAN,0};
    double gradients[WB_SUPPORT]={0};
    for(int c=WB_HALF;c<WB_SUPPORT;c++) {
        double d=0;for(int t=0;t<WB_HALF;t++)d+=y[c+t]-y[c-1-t];
        gradients[c]=d/WB_HALF;
    }
    for(int c=WB_HALF;c<WB_SUPPORT;c++) {
        double rise=gradients[c];
        if(rise<=best.rise || rise<=0 ||
           (c>WB_HALF && rise<gradients[c-1]) ||
           (c+1<WB_SUPPORT && rise<gradients[c+1]))continue;
        int outside=c-WB_HALF;
        wb_level b=outside>=WB_HALF?wb_stats(y,outside,vi.noise):vi;
        if(fabs(b.level-vi.level)>5*hypot(b.noise,vi.noise))continue;
        wb_level p=wb_stats(y+c+WB_HALF,WB_PLATEAU,vi.noise);
        if(p.level-b.level<=5*fmax(b.noise,vi.noise))continue;
        wb_level p1=wb_stats(y+c+WB_HALF,WB_HALF,vi.noise);
        wb_level p2=wb_stats(y+c+2*WB_HALF,WB_HALF,vi.noise);
        if(fabs(p1.level-p2.level)>3*hypot(p1.noise,p2.noise))continue;
        double noise=hypot(b.noise,p.noise),mid=(b.level+p.level)/2;
        int reversal=0;
        for(int x=c-WB_HALF;x<c+WB_HALF;x++)
            if(y[x]-y[x+1]>3*noise)reversal=1;
        if(reversal)continue;
        int cross=-1;
        for(int x=c-WB_HALF;x<c+WB_HALF;x++)
            if(y[x]<=mid && y[x+1]>mid){cross=x;break;}
        if(cross<0)continue;
        double slope=y[cross+1]-y[cross];
        double pos=cross+(mid-y[cross])/slope;
        best=(wb_edge){1,side?719-pos:pos,fmax(.5,noise/slope),
                       b.level,b.noise,p.level,rise};
    }
    if(best.status)return best;
    wb_level a=wb_stats(y,WB_PLATEAU,vi.noise);
    wb_level b=wb_stats(y+WB_PLATEAU,WB_PLATEAU,vi.noise);
    double picture=(a.level+b.level)/2,mid=(vi.level+picture)/2;
    int all=1;for(int i=0;i<WB_PLATEAU;i++)if(y[i]<mid)all=0;
    if(all && picture-vi.level>5*vi.noise &&
       fabs(a.level-b.level)<=3*hypot(a.noise,b.noise))
        best=(wb_edge){2,side?719:0,NAN,vi.level,vi.noise,picture,0};
    return best;
}
#endif
