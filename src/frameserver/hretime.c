#include "hretime.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>
#if defined(__aarch64__) && !defined(HRT_SCALAR)
#include <arm_neon.h>
#endif

/* Owner-specified NTSC horizontal blanking interval: 10.9 us * 13.5 MHz.
 * The same 426 reference samples are valid for every integer candidate. */
enum { ROW_BYTES=1440, HEADER=48, BODY_LO=60, BODY_HI=660,
       SEARCH=147, SCORE_LO=SEARCH, SCORE_HI=HRT_WIDTH-SEARCH,
       SCORE_SIZE=SCORE_HI-SCORE_LO,
       WIDTH_BODY_LO=40, WIDTH_BODY_HI=220 };
struct hrt_workspace {
    uint8_t y[HRT_ROWS][HRT_WIDTH];
    uint32_t prefix[HRT_ROWS][HRT_WIDTH+1];
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
static void prefix(const uint8_t *y,uint32_t *p) {
    p[0]=0;for(int x=0;x<HRT_WIDTH;x++)p[x+1]=p[x]+y[x];
}
/* Identical support makes integer sums directly comparable. Visit
 * near zero first for a useful incumbent, but ties still choose lowest shift. */
static int cannot_improve(unsigned sum,unsigned best,int s,int best_s) {
    return sum>best || (sum==best && s>=best_s);
}
/* Prepared doubled luma and neighbour sum permit fused 16-bit absolute-
 * difference accumulation. ceil(426/8)*510 fits each lane without overflow.
 * Independent accumulators avoid a single long dependency chain. */
static unsigned prepared_sad(const uint16_t *a,const uint16_t *ref,int s) {
    unsigned sum=0;int x=SCORE_LO,end=SCORE_HI;
#if defined(__aarch64__) && !defined(HRT_SCALAR)
    uint16x8_t v0=vdupq_n_u16(0),v1=v0,v2=v0,v3=v0;
    for(;x+32<=end;x+=32) {
        v0=vabaq_u16(v0,vld1q_u16(a+x+s),vld1q_u16(ref+x));
        v1=vabaq_u16(v1,vld1q_u16(a+x+s+8),vld1q_u16(ref+x+8));
        v2=vabaq_u16(v2,vld1q_u16(a+x+s+16),vld1q_u16(ref+x+16));
        v3=vabaq_u16(v3,vld1q_u16(a+x+s+24),vld1q_u16(ref+x+24));
    }
    for(;x+8<=end;x+=8)v0=vabaq_u16(v0,vld1q_u16(a+x+s),vld1q_u16(ref+x));
    sum=vaddlvq_u16(vaddq_u16(vaddq_u16(v0,v1),vaddq_u16(v2,v3)));
#endif
    for(;x<end;x++)sum+=(unsigned)abs((int)a[x+s]-ref[x]);
    return sum;
}
/* Triangle inequality: sum |2a-b-c| >= |sum(2a-b-c)| on identical support.
 * Every survivor is evaluated at full resolution, no heuristic finalist set.
 * Fine scalar block bounds cost more than SIMD SAD on flat/noisy material. */
static unsigned lower_bound(const uint32_t *a,const uint32_t *b,const uint32_t *c,int s) {
    int av=2*(int)(a[SCORE_HI+s]-a[SCORE_LO+s]);
    int ref=(int)(b[SCORE_HI]-b[SCORE_LO]+c[SCORE_HI]-c[SCORE_LO]);
    return (unsigned)abs(av-ref);
}
static float search(const uint8_t *a,const uint8_t *b,const uint8_t *c,
                    const uint32_t *ap,const uint32_t *bp,const uint32_t *cp,int *shift) {
    uint16_t doubled[HRT_WIDTH],ref[HRT_WIDTH];
    for(int x=0;x<HRT_WIDTH;x++){doubled[x]=2*a[x];ref[x]=b[x]+c[x];}
    unsigned zero=prepared_sad(doubled,ref,0),best=zero;*shift=0;
    for(int distance=1;distance<=SEARCH;distance++)for(int sign=-1;sign<=1;sign+=2) {
        int s=sign*distance;
        if(cannot_improve(lower_bound(ap,bp,cp,s),best,s,*shift))continue;
        unsigned e=prepared_sad(doubled,ref,s);
        if(!cannot_improve(e,best,s,*shift)){best=e;*shift=s;}
    }
    float e=(float)best/(2*SCORE_SIZE),z=(float)zero/(2*SCORE_SIZE);
    return e/fmaxf(z,1e-6f);
}
static float row_search(hrt_workspace *w,int a,int b,int c,int *shift) {
    return search(w->y[a],w->y[b],w->y[c],w->prefix[a],w->prefix[b],w->prefix[c],shift);
}
static float boundary(hrt_workspace *w,int a,int b) {
    int s=0;float q=row_search(w,a,b,b,&s);
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
/* Resolve boundary owners first, so the body reference is independent of band
 * traversal order. Exclude the unresolved top band too: it cannot witness its
 * own normal edges. Censored coordinates are observations here, not widths. */
static void edge_reference(hrt_workspace *w,hrt_result *o,int skip_end,int d1,int d2) {
    for(int k=0;k<2;k++) {
        double v[2][HRT_FIELD_ROWS];int n=0;
        for(int i=WIDTH_BODY_LO;i<WIDTH_BODY_HI;i++) {
            int j=2*i+k,l,r;
            if(j<=skip_end || !w->row[j] || w->flagged[j] || excluded(j,d1,d2) ||
               !edges(w->y[j],o->blank[k],&l,&r))continue;
            v[0][n]=l;v[1][n++]=r;
        }
        for(int e=0;e<2;e++) {
            o->edge_median[k][e]=o->edge_spread[k][e]=NAN;
            if(!n)continue;
            o->edge_median[k][e]=quantile(v[e],n,0.5);
            for(int i=0;i<n;i++)v[e][i]=fabs(v[e][i]-o->edge_median[k][e]);
            o->edge_spread[k][e]=quantile(v[e],n,0.9);
        }
    }
}
static unsigned edge_movement(hrt_workspace *w,const hrt_result *o,int j) {
    int k=j&1,l,r;
    if(!w->row[j] || !isfinite(o->edge_median[k][0]) ||
       !edges(w->y[j],o->blank[k],&l,&r))return 0;
    double dl=l-o->edge_median[k][0],dr=r-o->edge_median[k][1];
    unsigned moved=HRT_EDGES_KNOWN;
    if(dl < -o->edge_spread[k][0])moved|=HRT_LEFT_EARLIER;
    if(dl > o->edge_spread[k][0])moved|=HRT_LEFT_LATER;
    if(dr < -o->edge_spread[k][1])moved|=HRT_RIGHT_EARLIER;
    if(dr > o->edge_spread[k][1])moved|=HRT_RIGHT_LATER;
    return moved;
}
static int top_owner(hrt_workspace *w,const hrt_result *o,int start,int end,int displaced[2]) {
    if(!isfinite(o->edge_median[0][0]) || !isfinite(o->edge_median[1][0]))return -1;
    for(int j=start;j<=end;j++)if(edge_movement(w,o,j)&15)displaced[j&1]++;
    return displaced[0]>displaced[1]?0:displaced[1]>displaced[0]?1:-1;
}
static int flag_band(hrt_workspace *w,int start,int end,int k,int d1,int d2) {
    int included=0;
    for(int j=start+((start&1)!=k);j<=end;j+=2)if(w->row[j]) {
        /* Excluded switch damage is not repaired and is not a donor. */
        w->flagged[j]=1;
        if(!excluded(j,d1,d2))included=1;
    }
    return included;
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
        prefix(w->y[j],w->prefix[j]);
    }
    o->measured=1;
    for(int k=0;k<2;k++)o->blank[k]=blank_level(src[k],k);
    for(int j=0;j<HRT_ROWS;j++) {
        w->ratio[j]=row_search(w,j,j?j-1:1,j+1<HRT_ROWS?j+1:j-1,o->shift+j);
        w->disc[j]=o->shift[j]!=0 && w->ratio[j]<0.8f;
    }
    struct {int start,end,owner;float breaks[2];} bands[HRT_MAX_BANDS];
    int nb=0,skip_end=-1;
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
        bands[nb].start=j;bands[nb].end=end;bands[nb].owner=k;
        memcpy(bands[nb++].breaks,b,sizeof b);
        if(k>=0)flag_band(w,j,end,k,d1,d2);
        else if(j<=1 && b[0]==1 && b[1]==1)skip_end=end;
        j=end+1;
    }
    edge_reference(w,o,skip_end,d1,d2);
    for(int n=0;n<nb;n++) {
        int start=bands[n].start,end=bands[n].end,k=bands[n].owner;
        int fallback=0,displaced[2]={0,0};
        if(k<0 && start<=1 && bands[n].breaks[0]==1 && bands[n].breaks[1]==1) {
            k=top_owner(w,o,start,end,displaced);
            fallback=k>=0;
        }
        if(k<0){o->abstained++;continue;}
        int first=start+((start&1)!=k),last=end-((end&1)!=k);
        hrt_band *b=o->band+o->band_count++;
        *b=(hrt_band){.field=k+1,.first=line_number(first,d1,d2),.last=line_number(last,d1,d2),
                      .top_fallback=fallback,.displaced={displaced[0],displaced[1]}};
        memcpy(b->breaks,bands[n].breaks,sizeof b->breaks);
        o->field[k].bands+=flag_band(w,start,end,k,d1,d2);
    }
    for(int k=0;k<2;k++) {
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
        o->edge_moved[j]=(uint8_t)edge_movement(w,o,j);
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
