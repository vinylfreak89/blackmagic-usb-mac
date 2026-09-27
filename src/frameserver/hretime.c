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
/* Task46: shared dark/flat content needs no same-level agreement; blank rows
 * and device inserts cannot become timing repairs. */
enum { ROW_BYTES=1440, HEADER=48, WIDTH_BODY_LO=40, WIDTH_BODY_HI=220,
       HISTORY=30, SMALL_SHIFT=2 };
typedef struct { double edge[2],error[2];int spill; } repair_boundary;
typedef struct {
    double median[3],sigma[3];
    double edges[2][WIDTH_BODY_HI-WIDTH_BODY_LO];
    int count;
} normal_summary;
struct hrt_workspace {
    uint8_t y[HRT_ROWS][HRT_WIDTH];
    uint64_t counter[2],epoch;
    int have,context;
    const uint8_t *row[HRT_ROWS];
    uint8_t flagged[HRT_ROWS],moved[HRT_ROWS],picture[HRT_ROWS];
    repair_boundary repair[HRT_ROWS];
    double expected[HRT_ROWS][2],width_precision[HRT_ROWS];
    normal_summary history[2][HISTORY];
    int history_count[2],history_next[2];
    int lengths[HISTORY],length_count,length_next;
};
size_t hrt_size(void) { return sizeof(hrt_workspace); }
void hrt_reset(hrt_workspace *w) {
    w->have=0;memset(w->history_count,0,sizeof w->history_count);
    memset(w->history_next,0,sizeof w->history_next);w->length_count=w->length_next=0;
}
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
static int compare_double(const void *a,const void *b) {
    double x=*(const double*)a,y=*(const double*)b;return (x>y)-(x<y);
}
static double quantile(double *v,int n,double q) {
    qsort(v,(size_t)n,sizeof *v,compare_double);
    double pos=(n-1)*q;int lo=(int)pos,hi=(int)ceil(pos);
    return v[lo]+(pos-lo)*(v[hi]-v[lo]);
}
/* Repair precision is independent of detection's window qualification.
 * Local picture supports follow the reviewed half_left/half_right instrument.
 * Missing width is explicit; it does not invent a coordinate at the window. */
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
static repair_boundary repair_measure(const uint8_t *y,double vi,double noise) {
    repair_boundary b={{NAN,NAN},{NAN,NAN},0};
    double v[10];for(int x=0;x<10;x++)v[x]=y[26+x];
    double picture[2]={quantile(v,10,.5),0};
    for(int x=696;x<706;x++)if(y[x]>picture[1])picture[1]=y[x];
    for(int side=0;side<2;side++) {
        double blank=vi,sigma=noise;
        for(int pass=0;pass<2;pass++) {
            b.edge[side]=b.error[side]=NAN;
            if(picture[side]-blank<=5*sigma)break;
            double half=(picture[side]+blank)/2;
            int spill=1;for(int t=0;t<4;t++)if(y[side?719-t:t]<half)spill=0;
            if(spill){b.spill|=1<<side;break;}
            double pos=NAN,slope=0;
            for(int t=0;t<147;t++) {
                int x=side?719-t:t;
                double a=y[x],p=y[x+(side?-1:1)];
                if(a<half && p>=half) {
                    slope=p-a;double fraction=(half-a)/slope;
                    pos=side?x-fraction:x+fraction;break;
                }
            }
            b.edge[side]=pos;
            b.error[side]=isfinite(pos)?fmax(1,sigma/slope):NAN;
            if(pass || !isfinite(pos) || (side?pos>715:pos<4))break;
            double outside[4];for(int t=0;t<4;t++)outside[t]=y[side?719-t:t];
            double level=quantile(outside,4,.5);
            for(int t=0;t<4;t++)outside[t]=fabs(outside[t]-level);
            double sn=fmax(noise,1.4826*quantile(outside,4,.5));
            if(fabs(level-vi)>5*hypot(noise,sn))break;
            blank=level;sigma=sn;
        }
    }
    return b;
}
static int repair_reference_ok(hrt_workspace *w,int j,int d1,int d2) {
    return j>=0 && j<HRT_ROWS && w->row[j] && w->picture[j] && !w->flagged[j] && !w->moved[j] &&
        !excluded(j,d1,d2) && !w->repair[j].spill &&
        isfinite(w->repair[j].edge[0]) && isfinite(w->repair[j].edge[1]);
}
static int repair_choice(hrt_workspace *w,int j,int d1,int d2,int *shift) {
    repair_boundary *b=w->repair+j;
    if(b->spill || !isfinite(b->edge[0]) || !isfinite(b->edge[1]))return 0;
    int a=j-2,z=j+2;
    while(a>=0 && !repair_reference_ok(w,a,d1,d2))a-=2;
    while(z<HRT_ROWS && !repair_reference_ok(w,z,d1,d2))z+=2;
    if(a<0 && z>=HRT_ROWS) {
        a=repair_reference_ok(w,j-1,d1,d2)?j-1:-1;
        z=repair_reference_ok(w,j+1,d1,d2)?j+1:HRT_ROWS;
    }
    if(a<0 && z>=HRT_ROWS)return 0;
    if(a<0)a=z;if(z>=HRT_ROWS)z=a;
    double weight=a==z?0:(double)(j-a)/(z-a);
    for(int s=0;s<2;s++) {
        w->expected[j][s]=(1-weight)*w->repair[a].edge[s]+weight*w->repair[z].edge[s];
    }
    double allowance=fmax(w->expected[j][0],719-w->expected[j][1]);
    w->width_precision[j]=allowance;
    double width=b->edge[1]-b->edge[0],expected=w->expected[j][1]-w->expected[j][0];
    double delta=((b->edge[0]-w->expected[j][0])+(b->edge[1]-w->expected[j][1]))/2;
    if(fabs(width-expected)>allowance || fabs(delta)>allowance)return 0;
    *shift=(int)lround(delta);
    if(abs(*shift)<=(b->error[0]+b->error[1])/2)*shift=0;
    return 1;
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
    /* If neither adjacent row is usable, take the nearest immutable row in
     * the opposite field. Equidistant usable rows retain the existing ELA. */
    for(int distance=3;!a && !b && distance<HRT_ROWS;distance+=2) {
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
/* Retime is independent of interpolation donors. Vacated columns extend the
 * source edge; a few lost samples do not turn width-normal timing into I. */
static void retime(const uint8_t *in,uint8_t *out,int s) {
    for(int x=0;x<HRT_WIDTH;x++) {
        int sx=x+s;
        int lx=sx<0?0:sx>=HRT_WIDTH?HRT_WIDTH-1:sx;
        out[2*x+1]=in[2*lx+1];
        if(!(x&1))
            for(int v=0;v<2;v++)out[2*x+2*v]=(uint8_t)chroma(in,sx,v);
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
static double best_correlation(const uint8_t *a,const uint8_t *b) {
    double best=line_correlation(a,b,0);
    for(int d=1;d<=SMALL_SHIFT;d++)for(int sign=-1;sign<=1;sign+=2) {
        double r=line_correlation(a,b,d*sign);
        if(isfinite(r) && (!isfinite(best) || r>best))best=r;
    }
    return best;
}
static int summary(hrt_workspace *w,hrt_result *o,int k,int clean,normal_summary *s) {
    double values[3][HRT_FIELD_ROWS];int n=0;
    for(int i=WIDTH_BODY_LO;i<WIDTH_BODY_HI;i++) {
        int j=2*i+k;repair_boundary *b=w->repair+j;
        if(!w->row[j] || !w->picture[j] || (clean && w->flagged[j]) || b->spill ||
           !isfinite(b->edge[0]) || !isfinite(b->edge[1]) ||
           !isfinite(o->deficit[j]))continue;
        values[0][n]=o->deficit[j];values[1][n]=b->edge[0];values[2][n]=b->edge[1];n++;
    }
    if(!n)return 0;
    s->count=n;
    for(int e=0;e<2;e++)memcpy(s->edges[e],values[e+1],(size_t)n*sizeof(double));
    for(int e=0;e<1;e++) {
        s->median[e]=quantile(values[e],n,.5);
        for(int i=0;i<n;i++)values[e][i]=fabs(values[e][i]-s->median[e]);
        s->sigma[e]=1.4826*quantile(values[e],n,.5);
    }
    return 1;
}
static void normal(hrt_workspace *w,hrt_result *o,int k) {
    normal_summary cold;int n=w->history_count[k];
    if(!n && !summary(w,o,k,0,&cold)) {
        o->correlation_limit[k]=NAN;
        for(int e=0;e<2;e++)o->edge_median[k][e]=o->edge_spread[k][e]=NAN;
        return;
    }
    for(int e=0;e<1;e++) {
        double v[HISTORY],d[HISTORY];int count=n?n:1;
        for(int i=0;i<count;i++) {
            normal_summary *s=n?&w->history[k][i]:&cold;
            v[i]=s->median[e];d[i]=s->sigma[e];
        }
        double med=quantile(v,count,.5),within=quantile(d,count,.5);
        for(int i=0;i<count;i++)v[i]=fabs(v[i]-med);
        double spread=5*fmax(within,1.4826*quantile(v,count,.5));
        o->correlation_limit[k]=med+spread;
    }
    for(int e=0;e<2;e++) {
        double v[HISTORY*(WIDTH_BODY_HI-WIDTH_BODY_LO)];int count=0;
        for(int i=0;i<(n?n:1);i++) {
            const normal_summary *s=n?&w->history[k][i]:&cold;
            memcpy(v+count,s->edges[e],(size_t)s->count*sizeof(double));count+=s->count;
        }
        double median=quantile(v,count,.5);
        for(int i=0;i<count;i++)v[i]=fabs(v[i]-median);
        o->edge_median[k][e]=median;o->edge_spread[k][e]=quantile(v,count,.99);
    }
    o->width[k]=o->edge_median[k][1]-o->edge_median[k][0];
    o->tolerance[k]=fmax(o->edge_median[k][0],719-o->edge_median[k][1]);
}
static unsigned edge_movement(hrt_workspace *w,const hrt_result *o,int j) {
    unsigned bits=0;int k=j&1;
    for(int e=0;e<2;e++)if(isfinite(w->repair[j].edge[e]) && isfinite(o->edge_median[k][e])) {
        bits|=HRT_EDGES_KNOWN;
        double delta=w->repair[j].edge[e]-o->edge_median[k][e];
        if(delta < -o->edge_spread[k][e])bits|=1u<<(2*e);
        if(delta > o->edge_spread[k][e])bits|=2u<<(2*e);
    }
    return bits;
}
/* Inspect the actual displaced interval, not a fixed edge window. Content
 * must be present in every available opposite-field neighbour at those same
 * columns. Reuse the locator's noise significance, not a new luma threshold. */
static int edge_content(hrt_workspace *w,const hrt_result *o,const double noise[2],int j,int side) {
    int k=j&1;double edge=w->repair[j].edge[side],normal=o->edge_median[k][side];
    if(!isfinite(edge) || !isfinite(normal))return 0;
    int lo=(int)ceil(fmin(edge,normal)),hi=(int)floor(fmax(edge,normal));
    if(lo<0)lo=0;if(hi>719)hi=719;
    if(lo>hi)return 0;
    int seen=0;
    for(int n=j-1;n<=j+1;n+=2) {
        if(n<0 || n>=HRT_ROWS || !w->row[n])continue;
        seen=1;double sum=0,sq=0,picture=0;
        if(side) {
            for(int x=696;x<706;x++)picture=fmax(picture,w->y[n][x]);
        } else {
            double v[10];for(int x=0;x<10;x++)v[x]=w->y[n][26+x];
            picture=quantile(v,10,.5);
        }
        for(int x=lo;x<=hi;x++) {
            double v=w->y[n][x];sum+=v;sq+=v*v;
        }
        double count=hi-lo+1,mean=sum/count;
        double sd=sqrt(fmax(0,sq/count-mean*mean));
        int nk=n&1;
        int dark=mean<=(picture+o->blank[nk])/2;
        int flat=sd<=5*noise[nk];
        if(!dark && !flat)return 0;
    }
    return seen;
}
static double displacement(hrt_workspace *w,hrt_result *o,int j) {
    return ((w->repair[j].edge[0]-o->edge_median[j&1][0])+
            (w->repair[j].edge[1]-o->edge_median[j&1][1]))/2;
}
static void bridge(hrt_workspace *w,hrt_result *o,int d1,int d2) {
    for(int k=0;k<2;k++) {
        int last=-1;
        for(int j=k;j<HRT_ROWS;j+=2)if(w->flagged[j]) {
            if(last>=0 && j>last+2) {
                double a=displacement(w,o,last),b=displacement(w,o,j);
                int good=isfinite(a)&&isfinite(b)&&a*b<0;
                for(int p=last+2;p<j && good;p+=2) {
                    double v=displacement(w,o,p);
                    double expect=a+(b-a)*(p-last)/(j-last);
                    double uncertainty=fmax(1,(w->repair[p].error[0]+w->repair[p].error[1])/2);
                    good=w->row[p] && w->picture[p] && !excluded(p,d1,d2) && isfinite(v) &&
                         isfinite(uncertainty) && fabs(v-expect)<=uncertainty;
                }
                if(good)for(int p=last+2;p<j;p+=2){w->flagged[p]=1;o->reason[p]|=HRT_ZERO_CROSSING;}
            }
            last=j;
        }
    }
}
void hrt_apply(hrt_workspace *w,const uint8_t *f1,const uint8_t *f2,
               int d1,int d2,uint8_t *out1,uint8_t *out2,hrt_result *o) {
    HRT_DIAG_PHASE(0);
    memset(o,0,sizeof *o);memset(w->flagged,0,sizeof w->flagged);
    memset(w->moved,0,sizeof w->moved);
    if(!w->context)hrt_reset(w);
    const uint8_t *src[2]={f1,f2};uint8_t *dst[2]={out1,out2};int offsets[2]={d1,d2};
    for(int j=0;j<HRT_ROWS;j++) {
        int k=j&1,r=first_row(k,offsets[k])+j/2;
        w->row[j]=valid_row(k,r)?src[k]+HEADER+r*ROW_BYTES:NULL;
        for(int x=0;x<720;x++)w->y[j][x]=w->row[j]?w->row[j][2*x+1]:16;
        w->expected[j][0]=w->expected[j][1]=w->width_precision[j]=NAN;
    }
    HRT_DIAG_PHASE(1);
    for(int k=0;k<2;k++)o->blank[k]=blank_level(src[k],k);
    double noise[2]={repair_noise(f1,0,o->blank[0]),repair_noise(f2,1,o->blank[1])};
    for(int j=0;j<HRT_ROWS;j++) {
        w->repair[j]=repair_measure(w->y[j],o->blank[j&1],noise[j&1]);
        w->picture[j]=carries_picture(w->y[j],line_number(j,d1,d2),j&1,o->blank[j&1],noise[j&1]);
    }
    HRT_DIAG_PHASE(2);
    for(int j=0;j<HRT_ROWS;j++) {
        int a=j?j-1:1,b=j<479?j+1:478;
        int aa=j?j-1:1,bb=j<479?j+1:476;if(!j)bb=3;
        o->r_line[j]=o->r_neighbours[j]=o->deficit[j]=NAN;
        if(!w->row[j] || !w->row[a] || !w->row[b] || !w->row[aa] || !w->row[bb])continue;
        double x=best_correlation(w->y[j],w->y[a]),y=best_correlation(w->y[j],w->y[b]);
        o->r_line[j]=fmax(x,y);
        o->r_neighbours[j]=line_correlation(w->y[aa],w->y[bb],0);
        o->deficit[j]=o->r_neighbours[j]-o->r_line[j];
    }
    for(int k=0;k<2;k++)normal(w,o,k);
    HRT_DIAG_PHASE(3);
    for(int j=0;j<HRT_ROWS;j++) {
        if(!w->row[j] || !w->picture[j] || excluded(j,d1,d2))continue;
        int k=j&1;repair_boundary *b=w->repair+j;
        if(isfinite(o->deficit[j]) && isfinite(o->correlation_limit[k]) &&
           o->deficit[j]>o->correlation_limit[k]+1e-12)o->reason[j]|=HRT_CORRELATION;
        if(b->spill || !isfinite(b->edge[0]) || !isfinite(b->edge[1]))o->reason[j]|=HRT_MISSING_EDGE;
        o->edge_moved[j]=(uint8_t)edge_movement(w,o,j);
        for(int side=0;side<2;side++)
            if((o->edge_moved[j]&(3u<<(2*side))) && !edge_content(w,o,noise,j,side))
                o->reason[j]|=HRT_BLANKING_SIZE;
        if(isfinite(o->tolerance[k]) && o->tolerance[k]>0) {
            int lo=(int)ceil(o->edge_median[k][0]+o->edge_spread[k][0]);
            int hi=(int)floor(o->edge_median[k][1]-o->edge_spread[k][1]);
            int need=(int)ceil(o->tolerance[k]),run=0;
            if(lo<0)lo=0;if(hi>719)hi=719;
            for(int x=lo;x<=hi;x++) {
                if(fabs(w->y[j][x]-o->blank[k])<=5*noise[k])run++;else run=0;
                if(run>=need){o->reason[j]|=HRT_INTERIOR_BLANK;break;}
            }
        }
        w->flagged[j]=(o->reason[j]&HRT_MISSING_EDGE) ||
            ((o->reason[j]&(HRT_CORRELATION|HRT_BLANKING_SIZE))==
             (HRT_CORRELATION|HRT_BLANKING_SIZE));
    }
    bridge(w,o,d1,d2);
    HRT_DIAG_PHASE(4);
    if(w->length_count) {
        double v[HISTORY];for(int n=0;n<w->length_count;n++)v[n]=w->lengths[n];
        o->typical_band_length=quantile(v,w->length_count,.5);
    }
    for(int k=0;k<2;k++)for(int i=0;i<HRT_FIELD_ROWS;) {
        int j=2*i+k;if(!w->flagged[j]){i++;continue;}
        int first=i;while(i+1<HRT_FIELD_ROWS && w->flagged[2*(i+1)+k])i++;
        hrt_band *b=&o->band[o->band_count++];
        *b=(hrt_band){.field=k+1,.first=line_number(2*first+k,d1,d2),.last=line_number(2*i+k,d1,d2)};
        o->field[k].bands++;
        w->lengths[w->length_next++]=i-first+1;w->length_next%=HISTORY;
        if(w->length_count<HISTORY)w->length_count++;
        i++;
    }
    HRT_DIAG_PHASE(5);
    for(int j=0;j<HRT_ROWS;j++)if(w->flagged[j]) {
        int k=j&1,r=first_row(k,offsets[k])+j/2,line=r+4;
        uint8_t *out=dst[k]+HEADER+r*ROW_BYTES;
        /* Interior black alone is not timing damage. Only garbage border
         * blanking forces interpolation independently of the width rule. */
        int s=0,keep=repair_choice(w,j,d1,d2,&s);
        if(o->reason[j]&HRT_MISSING_EDGE)keep=0;
        o->shift[j]=keep?s:0;
        if(keep && !s){o->action[j]=HRT_CONTENT;o->field[k].content++;continue;}
        if(keep){retime(w->row[j],out,s);o->action[j]=HRT_RETIME;o->field[k].retimed++;}
        else {
            if(!interpolate(w,j,out)){o->action[j]=HRT_UNAVAILABLE;o->field[k].unavailable++;continue;}
            o->action[j]=HRT_INTERPOLATE;o->field[k].interpolated++;
        }
        if(!o->field[k].first)o->field[k].first=line;
        o->field[k].last=line;
    }
    HRT_DIAG_PHASE(6);
    for(int k=0;k<2;k++) {
        normal_summary s;
        if(summary(w,o,k,1,&s)) {
            w->history[k][w->history_next[k]++]=s;w->history_next[k]%=HISTORY;
            if(w->history_count[k]<HISTORY)w->history_count[k]++;
        }
    }
    w->have=1;w->context=0;
    HRT_DIAG_PHASE(7);
}
