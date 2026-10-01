#include "line_edges.h"
#include "hretime.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>
#ifndef HRT_DIAG_PHASE
#define HRT_DIAG_PHASE(n) ((void)0)
#endif
/* Horizontal timing against the OTHER field's blanking, like a line TBC.
 *
 * Timing reference: the sharp blanking falloff at each side of the picture.
 * Both fields of one frame share one blanking position (measured within 0.3
 * samples on pan, tape1 and capture 4), so a line is mistimed only where its falloff
 * departs from that frame standard AND from its woven other-field neighbours.
 * A line whose picture is near blanking at the standard position gives no
 * evidence unless the other field has picture there. Per field, every line
 * from the first to the last detection is repaired: retimed to the other
 * field's falloff when the shifted waveform agrees with the other field,
 * otherwise interpolated from it. No history; nothing is allocated. */
enum { ROW_BYTES=1440, HEADER=48,
       /* Picture evidence at the standard edge: codes above blanking. Black
        * with setup measured ~16 codes above blanking, and the pan's dark
        * edge content reached 30; 40 is ~18 IRE. */
       PICTURE_MIN=LE_PICTURE_MIN, /* shared with registration: line_edges.h holds the provenance */
       /* "A few samples": the falloff rises over ~3 samples, and the pan's
        * cross-field left-edge disagreement was 3.0 at the 99.9th percentile. */
       FEW=LE_FEW,
       /* Coarse standard: the first rise above the blanking bumps seen before
        * the falloff (<=16 codes on tape1), below most picture. */
       COARSE=LE_COARSE,
       /* Agreement: the retimed line may decorrelate from the other field at
        * most this many times the other field's own two lines do. Correct
        * retimes of labelled tape1 bends measured 1.0-3.2x; a 3-sample
        * misalignment measured ~15x. */
       AGREEMENT=4,
       SCAN=LE_BLANKING, /* nominal horizontal blanking width, samples */
       STANDARD_LINES=20, /* measured edges needed for a frame standard */
       REF_DISTANCE=7 };
struct hrt_workspace {
    uint8_t y[HRT_ROWS][HRT_WIDTH];
    uint64_t counter[2],epoch;
    int have,context;
    const uint8_t *row[HRT_ROWS];
    uint8_t eligible[HRT_ROWS],flagged[HRT_ROWS],range[HRT_ROWS];
    double level[HRT_ROWS][2]; /* picture minus blank just inside the standard */
    double edge[HRT_ROWS][2];  /* half-height falloff; -1/720 spill, NAN none */
    double ref_edge[HRT_ROWS][2];
    double sorted[HRT_ROWS];
    uint8_t reference[HRT_WIDTH],filler[ROW_BYTES],resized[ROW_BYTES],resized_y[HRT_WIDTH];
    int resize;
};
size_t hrt_size(void) { return sizeof(hrt_workspace); }
void hrt_reset(hrt_workspace *w) { w->have=0; }
void hrt_set_resize(hrt_workspace *w,int resize) { w->resize=resize; }
void hrt_begin(hrt_workspace *w,uint64_t c1,uint64_t c2,uint64_t epoch,int reset) {
    if(reset || (w->have && (w->epoch!=epoch || w->counter[0]==UINT64_MAX ||
       w->counter[1]==UINT64_MAX || w->counter[0]+1!=c1 || w->counter[1]+1!=c2)))hrt_reset(w);
    w->counter[0]=c1;w->counter[1]=c2;w->epoch=epoch;w->context=1;
}
static int first_row(int k,int d) { return (k?282:19)+d; }
static int valid_row(int k,int r) { return k ? r>=262 && r<525 : r>=0 && r<262; }
static int line_number(int j,int d1,int d2) { return first_row(j&1,(j&1)?d2:d1)+j/2+4; }
static int excluded(int j,int d1,int d2) { return line_number(j,d1,d2)>=((j&1)?518:255); }
static int carries_picture(const uint8_t *y,int line,int field,double blank,double noise) {
    int insert=field?283:20;
    if(line==insert || line==insert+1)return 0;
    for(int x=0;x<HRT_WIDTH;x++)if(y[x]>blank+5*noise)return 1;
    return 0;
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
static double repair_noise(const uint8_t *unit,int k,double blank) {
    unsigned h[511]={0};int start=k?270:7;
    for(int r=start;r<start+9;r++)for(int x=0;x<720;x++)
        h[(int)fabs(2*unit[HEADER+r*ROW_BYTES+2*x+1]-2*blank)]++;
    unsigned sum=0;int lo=-1,hi=0;
    for(int i=0;i<511;i++) {
        sum+=h[i];if(lo<0 && sum>(9*720-1)/2)lo=i;
        if(sum>9*720/2){hi=i;break;}
    }
    return fmax(1/sqrt(12.0),1.4826*(lo+hi)/4.0);
}
static int compare_double(const void *a,const void *b) {
    double x=*(const double*)a,y=*(const double*)b;return (x>y)-(x<y);
}
static double median(double *v,int n) {
    qsort(v,(size_t)n,sizeof *v,compare_double);
    return n&1?v[n/2]:(v[n/2-1]+v[n/2])/2;
}
/* First crossing of level h seen from outside the picture. Sample 719 is the
 * capture window's attenuated last sample, never picture: the right scan
 * starts at 718. Picture already at the window is spill (-1 / 720). */
static double crossing(const uint8_t *y,int side,double h,int limit) {
    if(!side) {
        if(y[0]>=h)return -1;
        for(int x=1;x<=limit && x<HRT_WIDTH;x++)if(y[x]>=h)
            return x-1+(h-y[x-1])/(double)(y[x]-y[x-1]);
    } else {
        if(y[718]>=h)return 720;
        for(int x=717;x>=718-limit && x>=0;x--)if(y[x]>=h)
            return x+1-(h-y[x+1])/(double)(y[x]-y[x+1]);
    }
    return NAN;
}
static int spilled(double e) { return e<0 || e>=HRT_WIDTH; }
/* Picture level just inside the standard falloff (10-sample median). */
static double inside_level(const uint8_t *y,int side,double standard) {
    int s=(int)lround(standard),a=side?s-13:s+4;
    if(a<0)a=0;if(a>HRT_WIDTH-10)a=HRT_WIDTH-10;
    int h[10];for(int i=0;i<10;i++)h[i]=y[a+i];
    for(int i=1;i<10;i++)for(int k=i;k>0 && h[k-1]>h[k];k--){int t=h[k];h[k]=h[k-1];h[k-1]=t;}
    return (h[4]+h[5])/2.0;
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
    return j>=0 && j<HRT_ROWS && w->eligible[j] && !w->flagged[j]?w->row[j]:NULL;
}
/* Edge-directed average of the nearest undetected eligible opposite-field
 * rows, never further than the reference search. */
static int interpolate(hrt_workspace *w,int j,uint8_t *out) {
    const uint8_t *a=donor(w,j-1),*b=donor(w,j+1);
    for(int distance=3;!a && !b && distance<=REF_DISTANCE;distance+=2) {
        a=donor(w,j-distance);b=donor(w,j+distance);
    }
    if(!a && !b)return 0;
    if(!a || !b){memcpy(out,a?a:b,ROW_BYTES);return 1;}
    for(int x=0;x<HRT_WIDTH;x++) {
        int d=direction(a,b,x);
        out[2*x+1]=average(a[2*(x+d)+1],b[2*(x-d)+1]);
        if(!(x&1))for(int v=0;v<2;v++)out[2*x+2*v]=average(chroma(a,x+d,v),chroma(b,x-d,v));
    }
    return 1;
}
/* out[x]=in[x+s]. Columns whose source lies outside the picture window are
 * unknown, and the window's first and last samples are edge transients
 * (sample 0 overshoots picture running into it; 719 is attenuated): they
 * come from the other field when a filler row exists, else the source edge
 * is extended. */
static void retime(const uint8_t *in,uint8_t *out,int s,const uint8_t *fill) {
    for(int x=0;x<HRT_WIDTH;x++) {
        int sx=x+s;
        if(fill && s && (sx<1 || sx>=HRT_WIDTH-1)) {
            out[2*x+1]=fill[2*x+1];
            if(!(x&1)){out[2*x]=fill[2*x];out[2*x+2]=fill[2*x+2];}
            continue;
        }
        int lx=sx<0?0:sx>=HRT_WIDTH?HRT_WIDTH-1:sx;
        out[2*x+1]=in[2*lx+1];
        if(!(x&1))
            for(int v=0;v<2;v++)out[2*x+2*v]=(uint8_t)chroma(in,sx,v);
    }
}
/* Lanczos-3 (the 6-tap filter of the owner's rubber-band note, 2026-09-28): source value at real
 * position s on an n-sample grid, edges extended. */
static double lanczos3(double x){if(x==0)return 1;if(fabs(x)>=3)return 0;double px=3.14159265358979323846*x;return 3*sin(px)*sin(px/3)/(px*px);}
static double lanczos_at(const double *v,int n,double s){
    int i0=(int)floor(s)-2;double acc=0,wsum=0;
    for(int i=i0;i<i0+6;i++){int c=i<0?0:i>=n?n-1:i;double w=lanczos3(s-i);acc+=w*v[c];wsum+=w;}
    return wsum!=0?acc/wsum:v[(int)fmin(fmax(s,0),n-1)];
}
static uint8_t clamp8(double v){return (uint8_t)(v<0?0:v>255?255:lround(v));}
/* Edge-pinned resize: out[x] = in[el + (x-rl)(er-el)/(rr-rl)], mapping this line's falloffs (el,er)
 * onto the reference falloffs (rl,rr). As in retime, columns whose source lies outside the picture
 * window (samples 1-718) come from the other field when a filler exists. yout receives the luma. */
static void resize_line(const uint8_t *in,uint8_t *out,double el,double er,double rl,double rr,
                        const uint8_t *fill,uint8_t *yout) {
    double y[HRT_WIDTH],u[HRT_WIDTH/2],v[HRT_WIDTH/2],k=(er-el)/(rr-rl);
    for(int x=0;x<HRT_WIDTH;x++)y[x]=in[2*x+1];
    for(int p=0;p<HRT_WIDTH/2;p++){u[p]=in[4*p];v[p]=in[4*p+2];}
    for(int x=0;x<HRT_WIDTH;x++) {
        double sx=el+(x-rl)*k;
        if(fill && (sx<1 || sx>HRT_WIDTH-2)) {
            out[2*x+1]=fill[2*x+1];
            if(!(x&1)){out[2*x]=fill[2*x];out[2*x+2]=fill[2*x+2];}
        } else {
            out[2*x+1]=clamp8(lanczos_at(y,HRT_WIDTH,sx));
            if(!(x&1)){out[2*x]=clamp8(lanczos_at(u,HRT_WIDTH/2,sx/2));out[2*x+2]=clamp8(lanczos_at(v,HRT_WIDTH/2,sx/2));}
        }
        yout[x]=out[2*x+1];
    }
}
/* Integer moments are exact for 720 8-bit samples; only the final Pearson
 * normalisation uses double. Every shift includes every target sample. */
static double line_correlation(const uint8_t *a,const uint8_t *b,int shift) {
    unsigned sa=0,sb=0,aa=0,bb=0,ab=0;
    for(int x=0;x<720;x++) {
        int p=x+shift;if(p<0)p=0;if(p>719)p=719;
        unsigned u=a[p],v=b[x];sa+=u;sb+=v;aa+=u*u;bb+=v*v;ab+=u*v;
    }
    double va=aa-(double)sa*sa/720,vb=bb-(double)sb*sb/720;
    return va>0 && vb>0 ? (ab-(double)sa*sb/720)/sqrt(va*vb):NAN;
}
/* Pearson of a[x+s] against b[x] over the columns both actually cover
 * (a's attenuated sample 719 excluded): agreement after a retime. */
static double overlap_correlation(const uint8_t *a,const uint8_t *b,int s) {
    int lo=s<0?-s:0,hi=s<0?HRT_WIDTH:HRT_WIDTH-1-s;
    unsigned n=0,sa=0,sb=0,aa=0,bb=0,ab=0;
    for(int x=lo;x<hi;x++) {
        unsigned u=a[x+s],v=b[x];n++;sa+=u;sb+=v;aa+=u*u;bb+=v*v;ab+=u*v;
    }
    if(n<HRT_WIDTH/2)return NAN;
    double va=aa-(double)sa*sa/n,vb=bb-(double)sb*sb/n;
    return va>0 && vb>0 ? (ab-(double)sa*sb/n)/sqrt(va*vb):NAN;
}
/* The owner's timing reference is a SHARP falloff: 20-80% of the rise to
 * the picture just past the crossing within 2*FEW samples. Measured 2-5 on
 * bent lines and 3-7 on straight pan lines; a dark picture ramping up from
 * blanking measured 9-10 and is content, not a falloff. */
static int sharp(const uint8_t *y,int side,double e,double blank) {
    if(!isfinite(e) || spilled(e))return 1;
    int x0=side?(int)ceil(e)-1:(int)floor(e)+1,peak=0;
    for(int t=0;t<12;t++) {
        int x=side?x0-t:x0+t;
        if(x>=0 && x<HRT_WIDTH-1 && y[x]>peak)peak=y[x];
    }
    double lo=blank+.2*(peak-blank),hi=blank+.8*(peak-blank);
    int a=-1,c=-1;
    for(int t=0;t<HRT_WIDTH-1 && c<0;t++) {
        int v=y[side?718-t:t];
        if(a<0 && v>=lo)a=t;
        if(v>=hi)c=t;
    }
    return a>=0 && c>=0 && c-a<=2*FEW;
}
static int usable_reference(hrt_workspace *w,int n) {
    return n>=0 && n<HRT_ROWS && w->eligible[n] && !w->flagged[n];
}
/* Frame standard per side: median falloff of the lines with picture there. */
static double frame_standard(hrt_workspace *w,int side,const double *blank,const double *coarse) {
    int n=0;
    for(int j=0;j<HRT_ROWS;j++) {
        if(!w->eligible[j])continue;
        double e;
        if(coarse) {
            if(w->level[j][side]<PICTURE_MIN)continue;
            e=w->edge[j][side];
        } else e=crossing(w->y[j],side,blank[j&1]+COARSE,SCAN);
        if(isfinite(e) && !spilled(e))w->sorted[n++]=e;
    }
    return n>=STANDARD_LINES?median(w->sorted,n):NAN;
}
/* Does side of row j disagree with the frame standard and with every
 * measured other-field neighbour by more than a few samples? Right-hand
 * spill is window-limited (blanking there is 1-3 samples) and only a right
 * falloff moved inward is observable on that side. */
static unsigned side_evidence(hrt_workspace *w,const double *standard,const double *blank,int j,int side) {
    double e=w->edge[j][side],s=standard[side];
    if(!isfinite(e) || !isfinite(s) || !sharp(w->y[j],side,e,blank[j&1]))return 0;
    double departure=(side && e>=HRT_WIDTH)?0:e-s;
    if(side?departure>=-FEW:fabs(departure)<=FEW)return 0;
    int seen=0;
    for(int n=j-1;n<=j+1;n+=2) {
        if(n<0 || n>=HRT_ROWS || !w->eligible[n] || w->level[n][side]<PICTURE_MIN)continue;
        double o=w->edge[n][side];if(!isfinite(o))continue;
        seen=1;if(fabs(e-o)<=FEW)return 0;
    }
    if(!seen)return 0;
    return departure<0?1u<<(2*side):2u<<(2*side);
}
/* Agreement with the other field (see the repair): the other field's two
 * lines' mutual decorrelation, scaled, bounds this line's. */
static int agrees(double r,double bar) {
    return isfinite(r) && isfinite(bar) && 1-r<=AGREEMENT*(1-bar)+1e-9;
}
/* One measurable side cannot exclude content moving at that edge: the whole
 * waveform, shifted by the edge's departure, must then match the adjacent
 * other-field lines better than unshifted, and well enough. */
static int waveform_confirms(hrt_workspace *w,const double *standard,int j,unsigned bits) {
    if(j<1 || j+1>=HRT_ROWS || !w->eligible[j-1] || !w->eligible[j+1])return 0;
    int side=(bits&3) && isfinite(standard[0])?0:1;double e=w->edge[j][side];
    if(!(bits&(3u<<(2*side))) || !isfinite(e) || spilled(e) || !isfinite(standard[side]))return 0;
    int shift=(int)lround(e-standard[side]);
    for(int x=0;x<HRT_WIDTH;x++)w->reference[x]=average(w->y[j-1][x],w->y[j+1][x]);
    double bar=line_correlation(w->y[j-1],w->y[j+1],0);
    double moved=overlap_correlation(w->y[j],w->reference,shift),still=overlap_correlation(w->y[j],w->reference,0);
    return agrees(moved,bar) && moved>still;
}
/* A timing error moves the whole line: a measured other side must show the
 * same shift, beyond a few samples, or picture pushed past the window on the
 * side it moved towards. One side departing while the other sits within a
 * few samples of the standard is content or a one-sided jitter, not timing.
 * A side near blanking in this line gives no evidence either way. Right
 * spill is window-limited. 0: contradicted; 1: consistent; 2: one side. */
static int shift_consistent(hrt_workspace *w,const double *standard,int j) {
    double l=w->edge[j][0],r=w->edge[j][1];
    if(!isfinite(l) || !isfinite(r) || !isfinite(standard[0]) || !isfinite(standard[1]))return 2;
    int ls=l<0,rs=r>=HRT_WIDTH;
    double dl=l-standard[0],dr=r-standard[1];
    /* No blanking at the left where the other field has it is garbage, not
     * content, whatever the right shows (a stretched line interpolates). */
    if(ls)return 1;
    if(rs)return dl>FEW;
    return fabs(dl-dr)<=FEW && fabs(dl)>FEW && fabs(dr)>FEW && (dl>0)==(dr>0);
}
void hrt_apply(hrt_workspace *w,const uint8_t *f1,const uint8_t *f2,
               int d1,int d2,uint8_t *out1,uint8_t *out2,hrt_result *o) {
    hrt_apply_detected(w,f1,f2,d1,d2,out1,out2,o,NULL);
}
void hrt_apply_detected(hrt_workspace *w,const uint8_t *f1,const uint8_t *f2,
               int d1,int d2,uint8_t *out1,uint8_t *out2,hrt_result *o,const uint8_t *detected) {
    HRT_DIAG_PHASE(0);
    memset(o,0,sizeof *o);
    memset(w->flagged,0,sizeof w->flagged);memset(w->range,0,sizeof w->range);
    if(!w->context)hrt_reset(w);
    const uint8_t *src[2]={f1,f2};uint8_t *dst[2]={out1,out2};int offsets[2]={d1,d2};
    for(int k=0;k<2;k++)o->blank[k]=blank_level(src[k],k);
    double noise[2]={repair_noise(f1,0,o->blank[0]),repair_noise(f2,1,o->blank[1])};
    for(int j=0;j<HRT_ROWS;j++) {
        int k=j&1,r=first_row(k,offsets[k])+j/2;
        w->row[j]=valid_row(k,r)?src[k]+HEADER+r*ROW_BYTES:NULL;
        for(int x=0;x<720;x++)w->y[j][x]=w->row[j]?w->row[j][2*x+1]:16;
        w->eligible[j]=w->row[j] && !excluded(j,d1,d2) &&
            carries_picture(w->y[j],line_number(j,d1,d2),k,o->blank[k],noise[k]);
        o->r_line[j]=o->r_neighbours[j]=o->deficit[j]=NAN;
        for(int s=0;s<2;s++)w->edge[j][s]=w->ref_edge[j][s]=w->level[j][s]=NAN;
    }
    HRT_DIAG_PHASE(1);
    /* Coarse standard from a fixed picture level, then each line's picture
     * level at that position and its own half-height falloff. */
    double standard[2];
    for(int s=0;s<2;s++)standard[s]=frame_standard(w,s,o->blank,NULL);
    for(int s=0;s<2;s++) {
        if(!isfinite(standard[s]))continue;
        for(int j=0;j<HRT_ROWS;j++)if(w->eligible[j]) {
            double b=o->blank[j&1],q=inside_level(w->y[j],s,standard[s]);
            w->level[j][s]=q-b;
            if(q-b>=PICTURE_MIN)w->edge[j][s]=crossing(w->y[j],s,(b+q)/2,SCAN);
        }
        standard[s]=frame_standard(w,s,o->blank,standard);
    }
    /* Picture near blanking at the standard gives no evidence of its own; if
     * both other-field neighbours have picture there, measure where this
     * line's picture actually starts at their half-height. */
    for(int s=0;s<2;s++)if(isfinite(standard[s]))
        for(int j=0;j<HRT_ROWS;j++)if(w->eligible[j] && w->level[j][s]<PICTURE_MIN) {
            double sum=0;int count=0;
            for(int n=j-1;n<=j+1;n+=2)
                if(n>=0 && n<HRT_ROWS && w->eligible[n] && w->level[n][s]>=PICTURE_MIN){sum+=w->level[n][s];count++;}
            /* The whole window: a line pushed past half of it is still
             * detected; its retime cannot be checked, so it interpolates. */
            if(count==2)w->edge[j][s]=crossing(w->y[j],s,o->blank[j&1]+sum/4,HRT_WIDTH-2);
        }
    for(int k=0;k<2;k++)for(int s=0;s<2;s++){o->edge_median[k][s]=standard[s];o->edge_spread[k][s]=FEW;}
    for(int k=0;k<2;k++){
        o->correlation_limit[k]=NAN;o->width[k]=standard[1]-standard[0];o->tolerance[k]=FEW;
    }
    o->typical_band_length=0;
    HRT_DIAG_PHASE(2);
    for(int j=0;j<HRT_ROWS;j++)if(w->eligible[j]) {
        unsigned bits=0;
        for(int s=0;s<2;s++)bits|=side_evidence(w,standard,o->blank,j,s);
        if(isfinite(w->edge[j][0]) || isfinite(w->edge[j][1]))bits|=HRT_EDGES_KNOWN;
        o->edge_moved[j]=(uint8_t)bits;
        if(detected)continue;
        int consistent=(bits&15)?shift_consistent(w,standard,j):0;
        if(consistent==1 || (consistent==2 && waveform_confirms(w,standard,j,bits)))w->range[j]=1;
    }
    if(detected)for(int j=0;j<HRT_ROWS;j++)if(detected[j]){w->flagged[j]=1;o->reason[j]|=HRT_DETECTED;}
    /* A lone line is a dropout or a little one-line shift, not a band: a
     * detection needs a detected neighbour in its own field. */
    if(!detected)for(int j=0;j<HRT_ROWS;j++)
        if(w->range[j] && ((j>=2 && w->range[j-2]) || (j+2<HRT_ROWS && w->range[j+2])))
            {w->flagged[j]=1;o->reason[j]|=HRT_BLANKING_SIZE;}
    memset(w->range,0,sizeof w->range);
    HRT_DIAG_PHASE(3);
    /* Range: per field, first to last detected line; every line between. */
    for(int k=0;k<2;k++) {
        int first=-1,last=-1;
        for(int j=k;j<HRT_ROWS;j+=2)if(w->flagged[j]){if(first<0)first=j;last=j;}
        if(first<0)continue;
        for(int j=first;j<=last;j+=2)if(w->eligible[j]) {
            w->range[j]=1;
            if(!w->flagged[j])o->reason[j]|=HRT_BAND_FILL;
        }
        hrt_band *b=&o->band[o->band_count++];
        *b=(hrt_band){.field=k+1,.first=line_number(first,d1,d2),.last=line_number(last,d1,d2)};
        o->field[k].bands++;
    }
    HRT_DIAG_PHASE(4);
    for(int j=0;j<HRT_ROWS;j++)if(w->range[j]) {
        int k=j&1,r=first_row(k,offsets[k])+j/2,line=r+4;
        uint8_t *out=dst[k]+HEADER+r*ROW_BYTES;
        /* The other field's two nearest undetected lines are the reference,
         * preferring lines outside that field's own range (which may be bent
         * though undetected). Two lines give the agreement bar. */
        const uint8_t *ref[2]={NULL,NULL};int refs=0;
        for(int pass=0;pass<2 && refs<2;pass++)
        for(int distance=1;refs<2 && distance<=REF_DISTANCE;distance+=2)
            for(int n=j-distance;refs<2 && n<=j+distance;n+=2*distance)
                if(usable_reference(w,n) && (pass || !w->range[n]) && (!refs || ref[0]!=w->y[n])) {
                    ref[refs++]=w->y[n];
                    for(int s=0;s<2;s++) {
                        double e=w->edge[n][s];
                        if(w->level[n][s]>=PICTURE_MIN && isfinite(e) && !spilled(e))
                            w->ref_edge[j][s]=isfinite(w->ref_edge[j][s])?(w->ref_edge[j][s]+e)/2:e;
                    }
                }
        if(!refs) {
            o->action[j]=HRT_UNAVAILABLE;o->field[k].unavailable++;continue;
        }
        for(int x=0;x<HRT_WIDTH;x++)w->reference[x]=refs==2?average(ref[0][x],ref[1][x]):ref[0][x];
        double reference_edge[2];
        for(int s=0;s<2;s++)reference_edge[s]=isfinite(w->ref_edge[j][s])?w->ref_edge[j][s]:standard[s];
        double el=w->edge[j][0],er=w->edge[j][1];
        int left=isfinite(el) && !spilled(el) && isfinite(reference_edge[0]);
        int right=isfinite(er) && !spilled(er) && isfinite(reference_edge[1]);
        int shift=0,interpolate_line=0,resize_line_now=0;
        if(isfinite(el) && el<0)o->reason[j]|=HRT_MISSING_EDGE;
        if(isfinite(er) && er>=HRT_WIDTH)o->reason[j]|=HRT_MISSING_EDGE;
        if(left) {
            shift=(int)lround(el-reference_edge[0]);
            if(right && fabs((er-reference_edge[1])-(el-reference_edge[0]))>FEW) {
                o->reason[j]|=HRT_WIDTH_BREAK;
                /* Both falloffs measured but moved by different amounts: a stretched line. Try the
                 * edge-pinned resize before giving the line up to interpolation. */
                if(w->resize && reference_edge[1]-reference_edge[0]>2*FEW && er-el>2*FEW)resize_line_now=1;
                else interpolate_line=1;
            }
            /* Picture past the right window only fits a move to the right. */
            if(isfinite(er) && er>=HRT_WIDTH && shift<-FEW){o->reason[j]|=HRT_WIDTH_BREAK;interpolate_line=1;}
        } else if(right) {
            shift=(int)lround(er-reference_edge[1]);
            if(isfinite(el) && el<0 && shift>-FEW){o->reason[j]|=HRT_WIDTH_BREAK;interpolate_line=1;}
        } else if(isfinite(el) && el<0 && isfinite(er) && er>=HRT_WIDTH) {
            interpolate_line=1; /* no blanking on either side: garbage edges */
        } else if(isfinite(el) && el<0) {
            /* No left blanking proves a move left but not how far, and the
             * right falloff is too dark to say: align the waveform to the
             * other field over leftward shifts only; agreement decides. */
            double best=-2;shift=0;
            for(int t=FEW+1;t<=SCAN;t++) {
                double r0=overlap_correlation(w->y[j],w->reference,-t);
                if(isfinite(r0) && r0>best){best=r0;shift=-t;}
            }
            if(!shift)interpolate_line=1;
        }
        /* Otherwise no usable falloff: near blanking here and in the other
         * field, so it is left alone (shift 0). */
        o->shift[j]=shift;
        o->deficit[j]=overlap_correlation(w->y[j],w->reference,0);
        if(resize_line_now) {
            double bar=refs==2?line_correlation(ref[0],ref[1],0):NAN;
            int filled=interpolate(w,j,w->filler);
            resize_line(w->row[j],w->resized,el,er,reference_edge[0],reference_edge[1],filled?w->filler:NULL,w->resized_y);
            double agree=line_correlation(w->resized_y,w->reference,0);
            o->r_line[j]=agree;o->r_neighbours[j]=bar;
            if(agrees(o->deficit[j],bar) && !(agree>o->deficit[j])) {
                o->action[j]=HRT_CONTENT;o->field[k].content++;continue;
            }
            if(agrees(agree,bar) && agree>o->deficit[j]) {
                memcpy(out,w->resized,ROW_BYTES);
                o->action[j]=HRT_RESIZE;o->field[k].resized++;
                if(!o->field[k].first)o->field[k].first=line;
                o->field[k].last=line;
                continue;
            }
            o->reason[j]|=HRT_CORRELATION;interpolate_line=1;
        }
        if(!interpolate_line && abs(shift)<=FEW) {
            o->action[j]=HRT_CONTENT;o->field[k].content++;continue;
        }
        if(!interpolate_line) {
            /* Agreement: the retimed waveform must match the other field
             * nearly as well as the other field's own lines match each other.
             * A line already agreeing unshifted at least as well is timed. */
            double agree=overlap_correlation(w->y[j],w->reference,shift);
            double bar=refs==2?line_correlation(ref[0],ref[1],0):NAN;
            o->r_line[j]=agree;o->r_neighbours[j]=bar;
            if(agrees(o->deficit[j],bar) && !(agree>o->deficit[j])) {
                o->action[j]=HRT_CONTENT;o->field[k].content++;continue;
            }
            /* One reference gives no bar: the retime cannot be checked. */
            if(!agrees(agree,bar) || !(agree>o->deficit[j]))
                {o->reason[j]|=HRT_CORRELATION;interpolate_line=1;}
        }
        int filled=interpolate(w,j,w->filler); /* only R/I lines reach here */
        if(!interpolate_line) {
            retime(w->row[j],out,shift,filled?w->filler:NULL);
            o->action[j]=HRT_RETIME;o->field[k].retimed++;
        } else {
            if(!filled){o->action[j]=HRT_UNAVAILABLE;o->field[k].unavailable++;continue;}
            memcpy(out,w->filler,ROW_BYTES);
            o->action[j]=HRT_INTERPOLATE;o->field[k].interpolated++;
        }
        if(!o->field[k].first)o->field[k].first=line;
        o->field[k].last=line;
    }
    w->have=1;w->context=0;
    HRT_DIAG_PHASE(5);
}
