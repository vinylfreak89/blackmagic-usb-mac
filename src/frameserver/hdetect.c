/* H-timing detection v11: a C port of experiments/hdetect/premise/phys.py (the reference, verified
 * unit by unit against it). Comments name the Python step each part reproduces. */
#include "hdetect.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

enum { MAXD=2*2*HD_ROWS, MAXR=2*HD_ROWS, PROF=40, B3BINS=766 };
static const int FR[2][2]={{19,262},{282,525}};   /* judged field rows */
static const int SWR[2][2]={{19,263},{282,525}};  /* head-switch search, incl. trailing rows */

typedef struct {
    unsigned hb[256],hb3[B3BINS];unsigned nb;  /* samples 0-2 of accepted lines, and their 3-sample sums */
    double d[MAXD];int nd;                     /* line-to-line edge differences */
    double r[MAXR];int nr;                     /* level at sample 718 over the line's right step */
    int has_prof;double prof[PROF];
} hd_frame;
struct hd_state {
    hd_frame f[HD_WINDOW];int count,head;
    int have_last;double B,top,g,bump;int rspec;
    int sw[2],sw_held[2];
    double work[HD_WINDOW*MAXD];
    /* per-unit working storage (no statics: one state per thread) */
    hd_frame fr;double warmv[(516-19)*3];double profrows[HD_ROWS][PROF];
};
size_t hd_size(void){return sizeof(hd_state);}
void hd_init(hd_state *s){memset(s,0,sizeof *s);}

/* ---- numpy-compatible order statistics (linear interpolation) ---- */
static int cmpd(const void *a,const void *b){double x=*(const double*)a,y=*(const double*)b;return (x>y)-(x<y);}
static double pct_sorted(const double *v,int n,double q){
    if(n<=0)return NAN;double at=q/100.0*(n-1);int lo=(int)floor(at),hi=(int)ceil(at);
    return v[lo]+(v[hi]-v[lo])*(at-lo);
}
static double pct(double *v,int n,double q){qsort(v,(size_t)n,sizeof *v,cmpd);return pct_sorted(v,n,q);}
static double median_d(double *v,int n){return pct(v,n,50);}
/* value of order statistic k (0-based) from a histogram with bin width w */
/* bin i holds value i/div; computed as numpy's mean does (sum then divide), so ties compare as in the reference */
static double hist_order(const unsigned *h,int bins,unsigned k,double div){
    unsigned c=0;for(int i=0;i<bins;i++){c+=h[i];if(c>k)return i/div;}return (bins-1)/div;
}
static double hist_pct(const unsigned *h,int bins,unsigned n,double q,double w){ /* w: divisor */
    double at=q/100.0*(n-1);unsigned lo=(unsigned)floor(at),hi=(unsigned)ceil(at);
    double a=hist_order(h,bins,lo,w),b=hist_order(h,bins,hi,w);return a+(b-a)*(at-lo);
}
static double median_u8(const uint8_t *y,int n){double v[720];for(int i=0;i<n;i++)v[i]=y[i];return n?median_d(v,n):NAN;}

/* ---- Win.stats ---- */
static void stats(hd_state *s){
    unsigned hb[256]={0},hb3[B3BINS]={0},nb=0;int nd=0,nr=0,np_=0;
    for(int i=0;i<s->count;i++){const hd_frame *f=&s->f[i];nb+=f->nb;for(int k=0;k<256;k++)hb[k]+=f->hb[k];for(int k=0;k<B3BINS;k++)hb3[k]+=f->hb3[k];}
    if(nb<300 && s->have_last)return;
    double B=hist_pct(hb,256,nb,50,1),top=hist_pct(hb3,B3BINS,nb/3,99.9,3);
    for(int i=0;i<s->count;i++){memcpy(s->work+nd,s->f[i].d,(size_t)s->f[i].nd*sizeof(double));nd+=s->f[i].nd;}
    double g;
    if(nd>200){for(int i=0;i<nd;i++)s->work[i]=fabs(s->work[i]);g=pct(s->work,nd,99);}
    else g=s->have_last?s->g:2.0;
    double prof[PROF];
    for(int i=0;i<s->count;i++)np_+=s->f[i].has_prof;
    double bump=0;
    if(np_){
        for(int c=0;c<PROF;c++){double v[HD_WINDOW];int n=0;for(int i=0;i<s->count;i++)if(s->f[i].has_prof)v[n++]=s->f[i].prof[c];prof[c]=median_d(v,n);}
        double mx=prof[0];for(int c=1;c<PROF;c++)if(prof[c]>mx)mx=prof[c];
        int am=0;for(int c=0;c<PROF;c++)if(prof[c]>B+0.5*(mx-B)){am=c;break;}
        int end=am-2;if(end<3)end=3;
        double m=prof[0];for(int c=1;c<end;c++)if(prof[c]>m)m=prof[c];bump=m-B;
    }
    for(int i=0;i<s->count;i++){memcpy(s->work+nr,s->f[i].r,(size_t)s->f[i].nr*sizeof(double));nr+=s->f[i].nr;}
    int rspec=nr>200?pct(s->work,nr,99)<0.5:(s->have_last?s->rspec:0);
    s->B=B;s->top=top;s->g=fmax(g,0.5);s->bump=fmax(bump,top-B);s->rspec=rspec;s->have_last=1;
}

/* ---- edges / edges_full: per line, each edge against its own step ---- */
typedef struct {double L,R,lvL,lvR;int Ls,Rs;} edge_t;
/* numpy.convolve(y, ones(3)/3, 'valid') as computed by the reference's numpy on this arm64 host: fused
 * multiply-adds over the rounded kernel (0 mismatches on 5,000 random rows). Ties against the band top
 * are common with integer luma, so the arithmetic is reproduced, not approximated. */
static double avg3(const uint8_t *y,int k){const double w=1.0/3;return fma(y[k+2],w,fma(y[k+1],w,y[k]*w));}
static void edges1(const uint8_t *y,const hd_state *s,int full,edge_t *o){
    double B=s->B,top=s->top,bump=s->bump;double m3[718];
    for(int k=0;k<718;k++)m3[k]=avg3(y,k);
    o->L=o->R=o->lvL=o->lvR=NAN;o->Ls=o->Rs=0;
    /* left */
    if(m3[0]>top)o->Ls=1;
    else{
        int lim=full?717:150,k=0;
        while(k<lim && m3[k]<=top)k++;
        if(k>=lim)o->Ls=2;
        else{
            int a=k-1>0?k-1:0,b=k+16>HD_WIDTH?HD_WIDTH:k+16,j=a;double best=-1e9;
            for(int x=a;x+1<b;x++){double dv=(double)y[x+1]-y[x];if(dv>best){best=dv;j=x;}}
            int s0=j+4,s1=j+11>HD_WIDTH?HD_WIDTH:j+11;
            double lvl=s1>s0?median_u8(y+s0,s1-s0)-B:NAN;o->lvL=lvl;
            if(lvl<=2*bump)o->Ls=2;
            else{
                double t=B+0.5*lvl;int x0=k-1>1?k-1:1,x1=j+8<719?j+8:719,hit=-1;
                for(int x=x0;x<x1;x++)if(y[x-1]<t && t<=y[x]){hit=x;break;}
                if(hit>=0)o->L=hit-1+(t-y[hit-1])/((double)y[hit]-y[hit-1]);else o->Ls=2;
            }
        }
    }
    /* right */
    int lim=full?2:570,k=718;
    while(k>lim && m3[k-2]<=top)k--;
    if(k<=lim){o->Rs=2;return;}
    int lo=k-15>0?k-15:0,hiE=k+2>HD_WIDTH?HD_WIDTH:k+2,j=lo;double best=1e9;
    for(int x=lo;x+1<hiE;x++){double dv=(double)y[x+1]-y[x];if(dv<best){best=dv;j=x;}}
    int s0=j-10>0?j-10:0,s1=j-3>1?j-3:1;
    double lvl=s1>s0?median_u8(y+s0,s1-s0)-B:NAN;o->lvR=lvl;
    if(lvl<=2*(top-B)){o->Rs=2;return;}
    double t=B+0.5*lvl;
    if(y[718]-B>=0.5*lvl){o->Rs=1;return;}
    int x0=k+1<717?k+1:717,x1=j-8>0?j-8:0,hit=-1;
    for(int x=x0;x>x1;x--)if(y[x]>=t && t>y[x+1]){hit=x;break;}
    if(hit>=0)o->R=hit+(y[hit]-t)/((double)y[hit]-y[hit+1]);else o->Rs=2;
}
static double median_of(const edge_t *e,int n,int left){
    double v[HD_ROWS];int m=0;for(int i=0;i<n;i++)if((left?e[i].Ls:e[i].Rs)==0)v[m++]=left?e[i].L:e[i].R;
    return m>=20?median_d(v,m):NAN;
}

/* ---- switch_line ---- */
static int switch_line(const uint8_t *Y,int fi,int r0,const hd_state *s){
    int a=SWR[fi][0],b=SWR[fi][1],last=b-1;
    while(last>a){const uint8_t *p=Y+last*HD_WIDTH;uint8_t mn=255,mx=0;for(int x=0;x<HD_WIDTH;x++){if(p[x]<mn)mn=p[x];if(p[x]>mx)mx=p[x];}if(mn!=mx)break;last--;}
    edge_t e[HD_ROWS];int n=0;
    for(int r=r0;r<last-40;r++)edges1(Y+r*HD_WIDTH,s,1,&e[n++]);
    double mL=median_of(e,n,1),mR=median_of(e,n,0);
    if(isnan(mL)&&isnan(mR))return 0;
    edge_t w[41];int dep[41],ok[41];double g=s->g;
    for(int i=0;i<41;i++){
        int r=last-40+i;edges1(Y+r*HD_WIDTH,s,1,&w[i]);
        double lv=median_u8(Y+r*HD_WIDTH+100,520)-s->B;
        dep[i]=w[i].Ls==1||(w[i].Ls==0&&fabs(w[i].L-mL)>g)||(w[i].Rs==0&&fabs(w[i].R-mR)>g)||(w[i].Rs==1&&s->rspec);
        ok[i]=dep[i]||(w[i].Ls==2&&w[i].Rs==2)||(lv<=2*(s->top-s->B));
    }
    int i=41;while(i>0&&ok[i-1])i--;
    while(i<41&&!dep[i])i++;
    return i<41?last-40+i+4:0;
}

/* ---- level fit: expected edge as a function of the edge's own step height ---- */
typedef struct {int nan_all;double a,b,m0;int line;} fit_t;
static fit_t fit(const edge_t *e,int n,int left,double m0,double g){
    fit_t f={.nan_all=isnan(m0),.m0=m0};if(f.nan_all)return f;
    double X[HD_ROWS],Yv[HD_ROWS],sv[HD_ROWS];int m=0;
    for(int i=0;i<n;i++){int S=left?e[i].Ls:e[i].Rs;double E=left?e[i].L:e[i].R,lv=left?e[i].lvL:e[i].lvR;
        if(S==0&&isfinite(lv)&&fabs(E-m0)<=g){X[m]=lv;Yv[m]=E;m++;}}
    if(m>=20){memcpy(sv,X,(size_t)m*sizeof(double));qsort(sv,(size_t)m,sizeof(double),cmpd);
        if(pct_sorted(sv,m,90)-pct_sorted(sv,m,10)>=20){
            double mx=0,my=0;for(int i=0;i<m;i++){mx+=X[i];my+=Yv[i];}mx/=m;my/=m;
            double sxy=0,sxx=0;for(int i=0;i<m;i++){sxy+=(X[i]-mx)*(Yv[i]-my);sxx+=(X[i]-mx)*(X[i]-mx);}
            f.b=sxy/sxx;f.a=my-f.b*mx;f.line=1;}}
    return f;
}
static double predict(const fit_t *f,double v){
    if(f->nan_all)return NAN;
    if(f->line){double p=f->a+f->b*v;return isfinite(p)?p:f->m0;}
    return f->m0;
}
static int moved_line(const edge_t *e,const fit_t *fL,const fit_t *fR,const hd_state *s){
    double g=s->g,dl=e->L-predict(fL,e->lvL),dr=e->R-predict(fR,e->lvR);
    int pushR=e->Rs==1&&e->Ls==0&&dl>g&&s->rspec;
    int pushL=e->Ls==1&&(e->Rs==2||(e->Rs==0&&dr<-g));
    int shiftsq=e->Ls==0&&e->Rs==0&&fabs(dl)>g&&fabs(dr)>g;
    return pushR||pushL||shiftsq;
}

/* ---- warm_frame ---- */
static void warm(hd_state *s,const uint8_t *Y,hd_frame *f){
    memset(f,0,sizeof *f);
    double *v=s->warmv;int n=0;
    for(int r=19;r<516;r++)for(int x=0;x<3;x++)v[n++]=Y[r*HD_WIDTH+x];
    double p=pct(v,n,95);
    for(int r=19;r<516;r++){const uint8_t *q=Y+r*HD_WIDTH;if(q[0]<=p&&q[1]<=p&&q[2]<=p){
        f->hb[q[0]]++;f->hb[q[1]]++;f->hb[q[2]]++;f->hb3[q[0]+q[1]+q[2]]++;f->nb+=3;}}
    for(int c=0;c<PROF;c++){double col[180];for(int r=60;r<240;r++)col[r-60]=Y[r*HD_WIDTH+c];f->prof[c]=median_d(col,180);}
    f->has_prof=1;
}
static void add(hd_state *s,const hd_frame *f){
    if(s->count<HD_WINDOW){s->f[s->count++]=*f;return;}
    memmove(s->f,s->f+1,(HD_WINDOW-1)*sizeof(hd_frame));s->f[HD_WINDOW-1]=*f;
}

/* ---- judge ---- */
void hd_judge(hd_state *s,const uint8_t *Y,int top1,int top2,hd_result *out){
    memset(out,0,sizeof *out);
    hd_frame *frp=&s->fr;
    if(s->count<3){warm(s,Y,frp);add(s,frp);return;}
    stats(s);out->judged=1;
    memset(frp,0,sizeof *frp);
#define fr (*frp)
    double profs[2][PROF];int nprof=0;
    edge_t e[HD_ROWS],ex[HD_ROWS];
    for(int fi=0;fi<2;fi++){
        int a=FR[fi][0],tops=fi?top2:top1,t0=tops>=0?tops-4:a,start=t0>a?t0:a;
        int sw=switch_line(Y,fi,start,s);
        if(sw)s->sw[fi]=sw;else if(s->sw[fi]){s->sw_held[fi]++;out->swheld[fi]=1;}
        if(!s->sw[fi]){out->nosw[fi]=1;continue;}
        out->switch_line[fi]=s->sw[fi];
        int r1=s->sw[fi]-4,n=r1>start?r1-start:0;
        for(int i=0;i<n;i++)edges1(Y+(start+i)*HD_WIDTH,s,0,&e[i]);
        double mL=median_of(e,n,1),mR=median_of(e,n,0);
        if(isnan(mL)&&isnan(mR))continue;
        double g=s->g;
        fit_t fL=fit(e,n,1,mL,g),fR=fit(e,n,0,mR,g);
        uint8_t moved[HD_ROWS],xm[HD_ROWS];
        for(int i=0;i<n;i++)moved[i]=(uint8_t)moved_line(&e[i],&fL,&fR,s);
        /* v11: lines above registration's top carrying the torn-line signature are tested too */
        int nx=start>a?start-a:0;double floor_=2*s->bump;
        for(int i=0;i<nx;i++){
            const uint8_t *y=Y+(a+i)*HD_WIDTH;edges1(y,s,0,&ex[i]);
            double m3[718];int first=-1,lastu=-1;
            for(int k=0;k<718;k++){m3[k]=avg3(y,k);if(m3[k]>s->top){if(first<0)first=k;lastu=k;}}
            int single=first>=0;for(int k=first;single&&k<=lastu;k++)if(!(m3[k]>s->top))single=0;
            int tall=(ex[i].Ls==0&&ex[i].lvL>floor_)||(ex[i].Ls==1&&median_u8(y+40,640)-s->B>floor_);
            xm[i]=(uint8_t)(single&&tall&&moved_line(&ex[i],&fL,&fR,s));
        }
        /* band: moved lines with a raster-adjacent moved neighbour; above-top lines then judged lines */
        int N=nx+n;uint8_t band[2*HD_ROWS];int lo=-1,hi=-1;
        for(int i=0;i<N;i++){
            int m=i<nx?xm[i]:moved[i-nx],row=i<nx?a+i:start+i-nx;
            int nb=0;
            if(i>0){int pm=i-1<nx?xm[i-1]:moved[i-1-nx],pr=i-1<nx?a+i-1:start+i-1-nx;nb|=pm&&row-pr==1;}
            if(i+1<N){int qm=i+1<nx?xm[i+1]:moved[i+1-nx],qr=i+1<nx?a+i+1:start+i+1-nx;nb|=qm&&qr-row==1;}
            band[i]=(uint8_t)(m&&nb);
            if(band[i]){out->torn[fi]=1;out->lines[fi][out->nlines[fi]++]=(int16_t)(row+4);
                if(i>=nx){if(lo<0)lo=i-nx;hi=i-nx;}}
        }
        uint8_t cut[HD_ROWS]={0};if(lo>=0)for(int i=lo;i<=hi;i++)cut[i]=1;
        int nboth=0;for(int i=0;i<n;i++)nboth+=e[i].Ls==0&&e[i].Rs==0;
        if(nboth<20)continue;
        /* window statistics from this field's normal lines */
        double (*profrows)[PROF]=s->profrows;int nok=0;
        for(int i=0;i<n;i++){
            double dl=e[i].L-predict(&fL,e[i].lvL),dr=e[i].R-predict(&fR,e[i].lvR);
            const uint8_t *y=Y+(start+i)*HD_WIDTH;
            int both=e[i].Ls==0&&e[i].Rs==0;
            if(both&&!cut[i]&&fabs(dl)<=g&&fabs(dr)<=g){
                fr.hb[y[0]]++;fr.hb[y[1]]++;fr.hb[y[2]]++;fr.hb3[y[0]+y[1]+y[2]]++;fr.nb+=3;
                for(int c=0;c<PROF;c++)profrows[nok][c]=y[c];nok++;
            }
            if(e[i].Ls==0&&!cut[i]&&fabs(dl)<=g&&isfinite(e[i].lvR)&&e[i].lvR>2*(s->top-s->B)&&fr.nr<MAXR)
                fr.r[fr.nr++]=(y[718]-s->B)/e[i].lvR;
        }
        for(int i=1;i<n;i++){
            int adj=e[i].Ls==0&&e[i].Rs==0&&e[i-1].Ls==0&&e[i-1].Rs==0&&!cut[i]&&!cut[i-1];
            if(adj&&fr.nd<MAXD)fr.d[fr.nd++]=e[i].L-e[i-1].L;
        }
        for(int i=1;i<n;i++){
            int adj=e[i].Ls==0&&e[i].Rs==0&&e[i-1].Ls==0&&e[i-1].Rs==0&&!cut[i]&&!cut[i-1];
            if(adj&&fr.nd<MAXD)fr.d[fr.nd++]=e[i].R-e[i-1].R;
        }
        if(nok>20){for(int c=0;c<PROF;c++){double v[HD_ROWS];for(int i=0;i<nok;i++)v[i]=profrows[i][c];profs[nprof][c]=median_d(v,nok);}nprof++;}
    }
    if(nprof){fr.has_prof=1;for(int c=0;c<PROF;c++)fr.prof[c]=nprof==1?profs[0][c]:(profs[0][c]+profs[1][c])/2;}
    add(s,frp);
#undef fr
}
