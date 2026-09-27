#include "hretime.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>
#ifndef HRT_DIAG_PHASE
#define HRT_DIAG_PHASE(n) ((void)0)
#endif
#if defined(__aarch64__) && !defined(HRT_SCALAR)
#include <arm_neon.h>
#endif
/* E-62: all thresholds registered before label replay; no worker allocation. */
enum { ROW_BYTES=1440, HEADER=48, BODY_LO=60, BODY_HI=660,
       WIDTH_BODY_LO=40, WIDTH_BODY_HI=220, WIN=120, NW=6, SEARCH=64,
       MIN_SHIFT=4, PROFILE_TOL=2, BASIN_RADIUS=2, MIN_WINDOWS=4,
       UNKNOWN_OFFSET=32767 };
struct hrt_workspace {
    uint8_t y[HRT_ROWS][HRT_WIDTH], previous[2][525][HRT_WIDTH];
    uint8_t valid[2][525], available[2][525];
    uint64_t counter[2], epoch;
    int have, context;
    const uint8_t *row[HRT_ROWS];
    uint8_t flagged[HRT_ROWS], seed[HRT_ROWS], moved[HRT_ROWS];
    int edge[HRT_ROWS][2];
    uint8_t interior[HRT_ROWS];
};
size_t hrt_size(void) { return sizeof(hrt_workspace); }
void hrt_reset(hrt_workspace *w) { w->have=0;memset(w->valid,0,sizeof w->valid); }
void hrt_begin(hrt_workspace *w,uint64_t c1,uint64_t c2,uint64_t epoch,int reset) {
    uint64_t c[2]={c1,c2};
    for(int k=0;k<2;k++)for(int r=0;r<525;r++)
        w->available[k][r]=!reset && w->have && w->epoch==epoch &&
            w->counter[k]!=UINT64_MAX && w->counter[k]+1==c[k] && w->valid[k][r];
    w->counter[0]=c1;w->counter[1]=c2;w->epoch=epoch;w->context=1;
}
static int first_row(int k,int d) { return (k?282:19)+d; }
static int valid_row(int k,int r) { return k ? r>=262 && r<525 : r>=0 && r<262; }
static int line_number(int j,int d1,int d2) { return first_row(j&1,(j&1)?d2:d1)+j/2+4; }
static int excluded(int j,int d1,int d2) { return line_number(j,d1,d2)>=((j&1)?518:255); }
static unsigned window_sad(const uint8_t *a,const uint8_t *b) {
    unsigned sum=0;int x=0;
#if defined(__aarch64__) && !defined(HRT_SCALAR)
    uint16x8_t v=vdupq_n_u16(0);
    for(;x+16<=WIN;x+=16) {
        uint8x16_t d=vabdq_u8(vld1q_u8(a+x),vld1q_u8(b+x));
        v=vaddq_u16(v,vpaddlq_u8(d));
    }
    sum=vaddlvq_u16(v);
#endif
    for(;x<WIN;x++)sum+=(unsigned)abs((int)a[x]-b[x]);
    return sum;
}
static double variance(const uint8_t *a) {
    double sum=0,sq=0;
    for(int x=0;x<WIN;x++){sum+=a[x];sq+=(double)a[x]*a[x];}
    return sq/WIN-(sum/WIN)*(sum/WIN);
}
static double correlation(const uint8_t *a,const uint8_t *b) {
    double sa=0,sb=0,aa=0,bb=0,ab=0;
    for(int x=0;x<WIN;x++){double u=a[x],v=b[x];sa+=u;sb+=v;aa+=u*u;bb+=v*v;ab+=u*v;}
    aa-=sa*sa/WIN;bb-=sb*sb/WIN;
    return aa>0 && bb>0?(ab-sa*sb/WIN)/sqrt(aa*bb):0;
}
/* Different origins are allowed for boundary-centred windows. Every candidate
 * compares exactly WIN samples, without padding or overlap normalisation. */
static int aligned_offset(const uint8_t *a,const uint8_t *b,int lo,int reflo) {
    if(variance(a+lo)<16)return UNKNOWN_OFFSET;
    unsigned costs[2*SEARCH+1];
    for(int i=0;i<2*SEARCH+1;i++)costs[i]=UINT32_MAX;
    unsigned zero=window_sad(a+lo,b+lo),best=window_sad(a+lo,b+reflo);int shift=0;
    costs[SEARCH]=best;
    for(int n=1;n<=SEARCH;n++)for(int sign=-1;sign<=1;sign+=2) {
        int s=n*sign;
        if(reflo+s<0 || reflo+s+WIN>HRT_WIDTH)continue;
        unsigned e=window_sad(a+lo,b+reflo+s);costs[s+SEARCH]=e;
        if(e<best){best=e;shift=s;}
    }
    unsigned far=UINT32_MAX;
    for(int s=-SEARCH;s<=SEARCH;s++)if(abs(s-shift)>BASIN_RADIUS && costs[s+SEARCH]<far)
        far=costs[s+SEARCH];
    int offset=lo-reflo-shift;
    if(abs(shift)==SEARCH || far==UINT32_MAX || far==0 || far<1.5*best ||
       variance(b+reflo+shift)<16 || correlation(a+lo,b+reflo+shift)<0.8 ||
       (offset && !(best<0.8*zero)))return UNKNOWN_OFFSET;
    return offset;
}
static int window_offset(const uint8_t *a,const uint8_t *b,int lo) {
    return aligned_offset(a,b,lo,lo);
}
static int rigid_offset(const int *v,int *middle) {
    int n=0,sum=0;
    for(int z=0;z<NW;z++)if(v[z]!=UNKNOWN_OFFSET){n++;sum+=v[z];}
    if(n<MIN_WINDOWS)return 0;
    *middle=(int)lround((double)sum/n);
    for(int z=0;z<NW;z++)if(v[z]!=UNKNOWN_OFFSET && abs(v[z]-*middle)>PROFILE_TOL)return 0;
    return 1;
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
/* Outer blank plateau and inner picture are separate witnesses.
 * Censored coordinates can corroborate, but cannot certify retiming. */
static int timing_edges(const uint8_t *y,double blank,int *left,int *right) {
    int l=-1,r=-1;*left=*right=-1;
    for(int x=0;x<=HRT_WIDTH-4;x++) {
        int good=1;for(int t=0;t<4;t++)good&=y[x+t]>blank+8;
        if(good){if(l<0)l=x;r=x+3;}
    }
    if(l<0)return 0;
    for(int side=0;side<2;side++) {
        int edge=side?r:l,inside=side?edge-39:edge;
        if(inside<0 || inside+40>720)continue;
        unsigned h[256]={0};for(int x=inside;x<inside+40;x++)h[y[x]]++;
        if(hist_quantile(h,40,0.5)<=blank+20)continue;
        int start=side?edge+1:0,end=side?720:edge,n=end-start;
        if(n) {
            memset(h,0,sizeof h);for(int x=start;x<end;x++)h[y[x]]++;
            if(fabs(hist_quantile(h,(unsigned)n,0.5)-blank)>3)continue;
        }
        if(side)*right=edge;else *left=edge;
    }
    return *left>=0 || *right>=0;
}
static int measured_edge(int edge,int side) {
    return side ? edge>=0 && edge<718 : edge>0;
}
static int edge_window_offset(const uint8_t *a,const uint8_t *b,int ea,int eb,int side) {
    if(!measured_edge(ea,side) || !measured_edge(eb,side))return UNKNOWN_OFFSET;
    int outside=side?719-ea:ea,other=side?719-eb:eb;
    if(outside>other)outside=other;
    if(outside>WIN/2)outside=WIN/2;
    int before=side?WIN-1-outside:outside;
    int lo=ea-before,reflo=eb-before;
    if(lo<0 || reflo<0 || lo+WIN>720 || reflo+WIN>720)return UNKNOWN_OFFSET;
    return aligned_offset(a,b,lo,reflo);
}
static int compare_double(const void *a,const void *b) {
    double x=*(const double*)a,y=*(const double*)b;return (x>y)-(x<y);
}
static double quantile(double *v,int n,double q) {
    qsort(v,(size_t)n,sizeof *v,compare_double);
    double pos=(n-1)*q;int lo=(int)pos,hi=(int)ceil(pos);
    return v[lo]+(pos-lo)*(v[hi]-v[lo]);
}
/* Each side supplies its own reference population; an unknown right edge must
 * not erase a measurable left boundary (and vice versa). */
static void edge_reference(hrt_workspace *w,hrt_result *o,int skip_end,int d1,int d2) {
    for(int k=0;k<2;k++) {
        double v[2][HRT_FIELD_ROWS];int n[2]={0,0};
        for(int i=WIDTH_BODY_LO;i<WIDTH_BODY_HI;i++) {
            int j=2*i+k,edge[2];
            if(j<=skip_end || !w->row[j] || w->flagged[j] || excluded(j,d1,d2) ||
               !timing_edges(w->y[j],o->blank[k],edge,edge+1))continue;
            for(int e=0;e<2;e++)if(edge[e]>=0)v[e][n[e]++]=edge[e];
        }
        for(int e=0;e<2;e++) {
            o->edge_median[k][e]=o->edge_spread[k][e]=NAN;
            if(!n[e])continue;
            o->edge_median[k][e]=quantile(v[e],n[e],0.5);
            for(int i=0;i<n[e];i++)v[e][i]=fabs(v[e][i]-o->edge_median[k][e]);
            o->edge_spread[k][e]=quantile(v[e],n[e],0.9);
        }
    }
}
static unsigned edge_movement(hrt_workspace *w,const hrt_result *o,int j) {
    int k=j&1,l,r;
    if(!w->row[j] ||
       !timing_edges(w->y[j],o->blank[k],&l,&r))return 0;
    double dl=l-o->edge_median[k][0],dr=r-o->edge_median[k][1];
    unsigned moved=HRT_EDGES_KNOWN;
    if(l>=0 && dl < -fmax(3,o->edge_spread[k][0]))moved|=HRT_LEFT_EARLIER;
    if(l>=0 && dl > fmax(3,o->edge_spread[k][0]))moved|=HRT_LEFT_LATER;
    if(r>=0 && dr < -fmax(3,o->edge_spread[k][1]))moved|=HRT_RIGHT_EARLIER;
    if(r>=0 && dr > fmax(3,o->edge_spread[k][1]))moved|=HRT_RIGHT_LATER;
    return moved;
}
static int certified_edges(const hrt_result *o,int k,int left,int right,int s) {
    /* A clipped coordinate is not a measured picture edge. */
    return left>0 && right<718 && o->edge_median[k][0]>0 && o->edge_median[k][1]<718 &&
           fabs(left-s-o->edge_median[k][0])<=o->edge_spread[k][0] &&
           fabs(right-s-o->edge_median[k][1])<=o->edge_spread[k][1];
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
static const uint8_t *donor(hrt_workspace *w,int j) {
    return j>=0 && j<HRT_ROWS && !w->flagged[j] && !w->moved[j]?w->row[j]:NULL;
}
static int interpolate(hrt_workspace *w,int j,uint8_t *out) {
    const uint8_t *a=donor(w,j-1),*b=donor(w,j+1);
    if(!a && !b)return 0;
    if(!a || !b){memcpy(out,a?a:b,ROW_BYTES);return 1;}
    for(int x=0;x<HRT_WIDTH;x++) {
        int d=direction(a,b,x);
        out[2*x+1]=average(a[2*(x+d)+1],b[2*(x-d)+1]);
        if(!(x&1))for(int v=0;v<2;v++)out[2*x+2*v]=average(chroma(a,x+d,v),chroma(b,x-d,v));
    }
    return 1;
}
/* out already contains opposite-field interpolation. Only replace samples
 * whose shifted source exists; all vacated luma/chroma stay interpolated. */
static void retime(const uint8_t *in,uint8_t *out,int s) {
    for(int x=0;x<HRT_WIDTH;x++) {
        int sx=x+s;
        if(sx>=0 && sx<HRT_WIDTH)out[2*x+1]=in[2*sx+1];
        if(!(x&1) && sx>=0 && sx+1<HRT_WIDTH)
            for(int v=0;v<2;v++)out[2*x+2*v]=(uint8_t)chroma(in,sx,v);
    }
}
void hrt_apply(hrt_workspace *w,const uint8_t *f1,const uint8_t *f2,
               int d1,int d2,uint8_t *out1,uint8_t *out2,hrt_result *o) {
    HRT_DIAG_PHASE(0);
    memset(o,0,sizeof *o);memset(w->flagged,0,sizeof w->flagged);
    memset(w->seed,0,sizeof w->seed);memset(w->interior,0,sizeof w->interior);
    if(!w->context)memset(w->available,0,sizeof w->available);
    const uint8_t *src[2]={f1,f2};uint8_t *dst[2]={out1,out2};int offsets[2]={d1,d2};
    for(int j=0;j<HRT_ROWS;j++) {
        int k=j&1,r=first_row(k,offsets[k])+j/2;
        w->row[j]=valid_row(k,r)?src[k]+HEADER+r*ROW_BYTES:NULL;
        for(int x=0;x<HRT_WIDTH;x++)w->y[j][x]=w->row[j]?w->row[j][2*x+1]:16;
        for(int a=0;a<2;a++)for(int z=0;z<NW;z++)o->offset[a][j][z]=UNKNOWN_OFFSET;
        for(int a=0;a<2;a++)for(int e=0;e<2;e++)o->edge_offset[a][j][e]=UNKNOWN_OFFSET;
    }
    o->measured=1;
    HRT_DIAG_PHASE(1);
    for(int k=0;k<2;k++)o->blank[k]=blank_level(src[k],k);
    HRT_DIAG_PHASE(2);
    edge_reference(w,o,-1,d1,d2);
    for(int j=0;j<HRT_ROWS;j++)timing_edges(w->y[j],o->blank[j&1],w->edge[j],w->edge[j]+1);
    HRT_DIAG_PHASE(3);
    for(int j=0;j<HRT_ROWS;j++) {
        w->moved[j]=(edge_movement(w,o,j)&15)!=0;
        if(!w->row[j] || excluded(j,d1,d2))continue;
        int k=j&1,r=first_row(k,offsets[k])+j/2,other=j^1;
        for(int z=0;z<NW;z++) {
            if(w->available[k][r])o->offset[0][j][z]=window_offset(w->y[j],w->previous[k][r],z*WIN);
            if(w->row[other])o->offset[1][j][z]=window_offset(w->y[j],w->y[other],z*WIN);
        }
        int previous_edge[2]={-1,-1};
        if(w->available[k][r])timing_edges(w->previous[k][r],o->blank[k],previous_edge,previous_edge+1);
        for(int e=0;e<2;e++) {
            if(w->available[k][r])o->edge_offset[0][j][e]=edge_window_offset(w->y[j],w->previous[k][r],w->edge[j][e],previous_edge[e],e);
            if(w->row[other])o->edge_offset[1][j][e]=edge_window_offset(w->y[j],w->y[other],w->edge[j][e],w->edge[other][e],e);
        }
    }
    HRT_DIAG_PHASE(4);
    for(int j=0;j<HRT_ROWS;j++) {
        if(!w->row[j] || !w->row[j^1] || excluded(j,d1,d2))continue;
        int k=j&1,other=j^1;
        unsigned own_move=edge_movement(w,o,j),peer_move=edge_movement(w,o,other);
        for(int e=0;e<2;e++) {
            unsigned mask=e?12:3;
            int t=o->edge_offset[0][j][e],p=o->edge_offset[0][other][e];
            int stationary=w->edge[other][e]>=0 && isfinite(o->edge_median[!k][e]) && !(peer_move&mask);
            int temporal=t!=UNKNOWN_OFFSET && abs(t)>=MIN_SHIFT && p!=UNKNOWN_OFFSET && abs(p)<MIN_SHIFT;
            if(!(peer_move&mask) && (temporal || ((own_move&mask) && stationary)))w->seed[j]=1;
        }
        int witnesses=0,shared=0;
        for(int z=0;z<NW;z++) {
            int t=o->offset[0][j][z],p=o->offset[0][other][z];
            if(t==UNKNOWN_OFFSET || p==UNKNOWN_OFFSET || abs(t)<MIN_SHIFT)continue;
            if(abs(p)<MIN_SHIFT)witnesses++;else shared++;
        }
        w->interior[j]=w->edge[j][0]<0 && w->edge[j][1]<0 && witnesses>=2 && !shared;
        if(w->seed[j])w->moved[j]=1;
    }
    for(int j=0;j<HRT_ROWS;j++)if(w->seed[j]) {
        for(int n=j-2;n<=j+2;n+=4)if(n>=0 && n<HRT_ROWS && (w->seed[n] || w->interior[n])) {
            w->flagged[j]=w->flagged[n]=1;
        }
    }
    for(int k=0;k<2;k++)for(int i=0;i<HRT_FIELD_ROWS;) {
        int j=2*i+k;if(!w->flagged[j]){i++;continue;}
        int first=i;while(i+1<HRT_FIELD_ROWS && w->flagged[2*(i+1)+k])i++;
        hrt_band *b=&o->band[o->band_count++];
        *b=(hrt_band){.field=k+1,.first=line_number(2*first+k,d1,d2),.last=line_number(2*i+k,d1,d2)};
        o->field[k].bands++;i++;
    }
    HRT_DIAG_PHASE(5);
    for(int j=0;j<HRT_ROWS;j++)if(w->flagged[j]) {
        int k=j&1,r=first_row(k,offsets[k])+j/2,line=r+4;
        uint8_t *out=dst[k]+HEADER+r*ROW_BYTES;
        o->edge_moved[j]=(uint8_t)edge_movement(w,o,j);
        int s=0,keep=rigid_offset(o->offset[1][j],&s);
        for(int e=0;e<2;e++)keep&=o->edge_offset[1][j][e]!=UNKNOWN_OFFSET &&
            abs(o->edge_offset[1][j][e]-s)<=PROFILE_TOL;
        int l=0,right=0;
        keep=keep && timing_edges(w->y[j],o->blank[k],&l,&right) && certified_edges(o,k,l,right,s);
        o->shift[j]=keep?s:0;
        if(!interpolate(w,j,out)){o->action[j]=HRT_UNAVAILABLE;o->field[k].unavailable++;continue;}
        if(keep){retime(w->row[j],out,s);o->action[j]=HRT_RETIME;o->field[k].retimed++;}
        else {o->action[j]=HRT_INTERPOLATE;o->field[k].interpolated++;}
        if(!o->field[k].first)o->field[k].first=line;
        o->field[k].last=line;
    }
    /* Cache actual repaired luma at the source storage coordinates. Recognised
     * unrepaired displacement is never promoted to a clean temporal witness. */
    HRT_DIAG_PHASE(6);
    memset(w->valid,0,sizeof w->valid);
    for(int j=0;j<HRT_ROWS;j++)if(w->row[j] && !excluded(j,d1,d2)) {
        int k=j&1,r=first_row(k,offsets[k])+j/2;
        int repaired=o->action[j]==HRT_RETIME || o->action[j]==HRT_INTERPOLATE;
        if(!repaired && (w->moved[j] || w->flagged[j])) {
            if(!o->action[j]){o->action[j]=HRT_CONTENT;o->field[k].content++;}
            o->edge_moved[j]=(uint8_t)edge_movement(w,o,j);continue;
        }
        const uint8_t *p=dst[k]+HEADER+r*ROW_BYTES;
        for(int x=0;x<HRT_WIDTH;x++)w->previous[k][r][x]=p[2*x+1];
        w->valid[k][r]=1;
    }
    w->have=1;w->context=0;
    HRT_DIAG_PHASE(7);
}
