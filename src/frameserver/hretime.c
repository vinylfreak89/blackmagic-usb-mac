#include "hretime.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>
#if defined(__aarch64__) && !defined(HRT_SCALAR)
#include <arm_neon.h>
#endif

enum { ROW_BYTES=1440, HEADER=48, SEARCH=24, BODY_LO=60, BODY_HI=660,
       WIDTH_BODY_LO=40, WIDTH_BODY_HI=220 };
struct hrt_workspace {
    uint8_t y[HRT_ROWS][HRT_WIDTH];
    const uint8_t *row[HRT_ROWS];
    uint8_t flagged[HRT_ROWS], disc[HRT_ROWS];
    float ratio[HRT_ROWS];
};
size_t hrt_size(void) { return sizeof(hrt_workspace); }
static int first_row(int k,int d) { return (k?282:19)+d; }
static int valid_row(int k,int r) { return k ? r>=262 && r<525 : r>=0 && r<262; }
static int line_number(int j,int d1,int d2) {
    return first_row(j&1,(j&1)?d2:d1)+j/2+4;
}
static int excluded(int j,int d1,int d2) {
    return line_number(j,d1,d2)>=((j&1)?518:255);
}
/* Twice the SAD against the exact half-integer neighbour mean. Every sum is
 * exact (<306001); preserve NumPy float32 mean/division and first-min tie order. */
static unsigned sad2(const uint8_t *a,const uint8_t *b,const uint8_t *c,int s) {
    unsigned sum=0;int x=BODY_LO;
#if defined(__aarch64__) && !defined(HRT_SCALAR)
    uint32x4_t acc=vdupq_n_u32(0);
    for(;x+16<=BODY_HI;x+=16) {
        uint8x16_t av=vld1q_u8(a+x+s),bv=vld1q_u8(b+x),cv=vld1q_u8(c+x);
        uint16x8_t al=vshlq_n_u16(vmovl_u8(vget_low_u8(av)),1);
        uint16x8_t ah=vshlq_n_u16(vmovl_u8(vget_high_u8(av)),1);
        acc=vpadalq_u16(acc,vabdq_u16(al,vaddl_u8(vget_low_u8(bv),vget_low_u8(cv))));
        acc=vpadalq_u16(acc,vabdq_u16(ah,vaddl_u8(vget_high_u8(bv),vget_high_u8(cv))));
    }
    sum=vaddvq_u32(acc);
#endif
    for(;x<BODY_HI;x++)sum+=(unsigned)abs(2*(int)a[x+s]-b[x]-c[x]);
    return sum;
}
static float search(const uint8_t *a,const uint8_t *b,const uint8_t *c,int *shift) {
    unsigned best=~0u,zero=0;
    for(int s=-SEARCH;s<=SEARCH;s++) {
        unsigned e=sad2(a,b,c,s);
        if(s==0)zero=e;
        if(e<best){best=e;*shift=s;}
    }
    float e=(float)best/1200.0f,z=(float)zero/1200.0f;
    return e/fmaxf(z,1e-6f);
}
static float boundary(hrt_workspace *w,int a,int b) {
    int s=0;float q=search(w->y[a],w->y[b],w->y[b],&s);
    return s && q<0.8f ? q : 1.0f;
}
static double hist_quantile(const unsigned h[256],unsigned n,double q) {
    double at=(n-1)*q;unsigned lo=(unsigned)at,hi=(unsigned)ceil(at),count=0;
    int a=-1,b=-1;
    for(int i=0;i<256;i++) {
        count+=h[i];
        if(a<0 && count>lo)a=i;
        if(count>hi){b=i;break;}
    }
    return a+(at-lo)*(b-a);
}
static double blank_level(const uint8_t *u,int k) {
    unsigned h[256]={0};int start=k?270:7;
    for(int r=start;r<start+9;r++)for(int x=0;x<HRT_WIDTH;x++)h[u[HEADER+r*ROW_BYTES+2*x+1]]++;
    return hist_quantile(h,9*HRT_WIDTH,0.5);
}
static int edges(const uint8_t *y,double blank,int *left,int *right) {
    unsigned h[256]={0};for(int x=BODY_LO;x<BODY_HI;x++)h[y[x]]++;
    double level=hist_quantile(h,BODY_HI-BODY_LO,0.5);
    if(level<=blank)return 0;
    double mid=(blank+level)*0.5;
    *left=0;while(*left<HRT_WIDTH && y[*left]<=mid)(*left)++;
    *right=HRT_WIDTH-1;while(*right>=0 && y[*right]<=mid)(*right)--;
    return *left<=*right;
}
static int compare_double(const void *a,const void *b) {
    double x=*(const double*)a,y=*(const double*)b;return (x>y)-(x<y);
}
static double quantile(double *v,int n,double q) {
    qsort(v,(size_t)n,sizeof *v,compare_double);
    double pos=(n-1)*q;int lo=(int)pos,hi=(int)ceil(pos);
    return v[lo]+(pos-lo)*(v[hi]-v[lo]);
}
static uint8_t average(int a,int b) { return (uint8_t)((a+b+1)/2); }
/* Chroma at an even luma-pair origin; odd source phase is halfway between
 * neighbours. Edge extension is confined to chroma resampling. */
static int chroma(const uint8_t *row,int x,int v) {
    if(x<0)x=0;
    if(x>718)x=718;
    int p=x/2,c=row[4*p+(v?2:0)];
    return (x&1) && p<359 ? average(c,row[4*(p+1)+(v?2:0)]) : c;
}
static int direction(const uint8_t *a,const uint8_t *b,int x) {
    static const int dirs[]={0,-1,1,-2,2,-3,3};
    int best=0,cost=INT32_MAX;
    for(unsigned i=0;i<sizeof dirs/sizeof *dirs;i++) {
        int d=dirs[i],e=0;
        if(x-1-abs(d)<0 || x+1+abs(d)>=HRT_WIDTH)continue;
        for(int t=-1;t<=1;t++)e+=abs((int)a[2*(x+t+d)+1]-b[2*(x+t-d)+1]);
        if(e<cost){cost=e;best=d;}
    }
    return best;
}
static int interpolate(hrt_workspace *w,int j,uint8_t *out) {
    const uint8_t *a=j>0 && !w->flagged[j-1]?w->row[j-1]:NULL;
    const uint8_t *b=j+1<HRT_ROWS && !w->flagged[j+1]?w->row[j+1]:NULL;
    if(!a && !b)return 0;
    if(!a || !b){memcpy(out,a?a:b,ROW_BYTES);return 1;}
    for(int x=0;x<HRT_WIDTH;x++) {
        int d=direction(a,b,x);
        out[2*x+1]=average(a[2*(x+d)+1],b[2*(x-d)+1]);
        if(!(x&1))for(int v=0;v<2;v++)out[2*x+2*v]=average(chroma(a,x+d,v),chroma(b,x-d,v));
    }
    return 1;
}
static void retime(const uint8_t *in,uint8_t *out,int s,int l,int r,double blank) {
    unsigned h[256]={0},n=0;
    for(int x=0;x<HRT_WIDTH;x++)if(x<l || x>r){h[in[2*x+1]]++;n++;}
    int y=(int)floor((n?hist_quantile(h,n,0.5):blank)+0.5);
    for(int x=0;x<HRT_WIDTH;x++) {
        int sx=x+s;out[2*x+1]=sx>=0 && sx<HRT_WIDTH?in[2*sx+1]:(uint8_t)y;
        if(!(x&1))for(int v=0;v<2;v++)out[2*x+2*v]=sx>=0 && sx+1<HRT_WIDTH?(uint8_t)chroma(in,sx,v):128;
    }
}
void hrt_apply(hrt_workspace *w,const uint8_t *f1,const uint8_t *f2,
               int d1,int d2,uint8_t *out1,uint8_t *out2,hrt_result *o) {
    memset(o,0,sizeof *o);memset(w->flagged,0,sizeof w->flagged);
    const uint8_t *src[2]={f1,f2};uint8_t *dst[2]={out1,out2};int offsets[2]={d1,d2};
    for(int j=0;j<HRT_ROWS;j++) {
        int k=j&1,r=first_row(k,offsets[k])+j/2;
        w->row[j]=valid_row(k,r)?src[k]+HEADER+r*ROW_BYTES:NULL;
        for(int x=0;x<HRT_WIDTH;x++)w->y[j][x]=w->row[j]?w->row[j][2*x+1]:16;
    }
    o->measured=1;
    for(int j=0;j<HRT_ROWS;j++) {
        w->ratio[j]=search(w->y[j],w->y[j?j-1:1],w->y[j+1<HRT_ROWS?j+1:j-1],o->shift+j);
        w->disc[j]=o->shift[j]!=0 && w->ratio[j]<0.8f;
    }
    for(int j=0;j<HRT_ROWS;) {
        if(!w->disc[j]){j++;continue;}
        int end=j;while(end+1<HRT_ROWS && w->disc[end+1])end++;
        float b[2]={1,1};int first[2],last[2];
        for(int k=0;k<2;k++) {
            first[k]=j+((j&1)!=k);last[k]=end-((end&1)!=k);
            if(first[k]>last[k])continue;
            if(first[k]>=2)b[k]=boundary(w,first[k],first[k]-2);
            if(last[k]+2<HRT_ROWS)b[k]=fminf(b[k],boundary(w,last[k],last[k]+2));
        }
        int k=b[0]<b[1]?0:b[1]<b[0]?1:-1;
        if(k<0)o->abstained++;
        else {
            o->band[o->band_count++]=(hrt_band){k+1,line_number(first[k],d1,d2),line_number(last[k],d1,d2),{b[0],b[1]}};
            int included=0;
            for(int t=first[k];t<=last[k];t+=2)if(w->row[t]) {
                /* Excluded switch damage is not repaired and is not a donor. */
                w->flagged[t]=1;
                if(!excluded(t,d1,d2))included=1;
            }
            o->field[k].bands+=included;
        }
        j=end+1;
    }
    for(int k=0;k<2;k++) {
        o->blank[k]=blank_level(src[k],k);
        double widths[HRT_FIELD_ROWS];int n=0;
        for(int i=WIDTH_BODY_LO;i<WIDTH_BODY_HI;i++) {
            int j=2*i+k,l,r;
            if(w->row[j] && !w->flagged[j] && !excluded(j,d1,d2) && edges(w->y[j],o->blank[k],&l,&r) && l>0 && r<718)
                widths[n++]=r-l;
        }
        o->width[k]=o->tolerance[k]=NAN;
        if(n) {
            o->width[k]=quantile(widths,n,0.5);
            for(int i=0;i<n;i++)widths[i]=fabs(widths[i]-o->width[k]);
            o->tolerance[k]=quantile(widths,n,0.9);
        }
    }
    for(int j=0;j<HRT_ROWS;j++)if(w->flagged[j] && !excluded(j,d1,d2)) {
        int k=j&1,l=0,r=0,s=o->shift[j],line=line_number(j,d1,d2);
        int row=first_row(k,offsets[k])+j/2;
        uint8_t *out=dst[k]+HEADER+row*ROW_BYTES;
        int keep=edges(w->y[j],o->blank[k],&l,&r) && isfinite(o->width[k]) &&
            fabs((r-l)-o->width[k])<=o->tolerance[k];
        if(keep) {
            int lost=(s>l?s-l:0)+(r-s>719?r-s-719:0);
            double unseen=(l==0 || r>=718)?fmax(0,o->width[k]-(r-l)):0;
            keep=unseen+lost<=o->tolerance[k];
        }
        if(keep) {retime(w->row[j],out,s,l,r,o->blank[k]);o->action[j]=HRT_RETIME;o->field[k].retimed++;}
        else if(interpolate(w,j,out)){o->action[j]=HRT_INTERPOLATE;o->field[k].interpolated++;}
        else {o->action[j]=HRT_UNAVAILABLE;o->field[k].unavailable++;continue;}
        if(!o->field[k].first)o->field[k].first=line;
        o->field[k].last=line;
    }
}
