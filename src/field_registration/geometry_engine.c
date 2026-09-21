#include "geometry_engine.h"
#include <math.h>
#include <string.h>

struct geometry_engine {
    int reverse, audit, valid, held, provisional, have_placement, last_d, last_d2;
    uint64_t counter;
    ge_features previous, current;
    uint8_t previous_y[GE_PIXELS];
    ge_decision pending;
};
size_t ge_size(void) { return sizeof(geometry_engine); }
void ge_init(geometry_engine *g, int reverse, int audit) {
    memset(g,0,sizeof *g); g->reverse=!!reverse; g->audit=!!audit;
}
const char *ge_class_name(ge_class c) {
    static const char *const names[]={"unknown","nothing","valid move","bottom only","top only","not in tandem"};
    return names[c];
}
static double quantile(const unsigned h[256], unsigned n, double q) {
    double at=(n-1)*q; unsigned a=(unsigned)at,b=a+(a<n-1),s=0; int va=-1;
    for(unsigned v=0;v<256;v++) {
        s+=h[v]; if(va<0 && s>a) va=(int)v;
        if(s>b) return va+(v-va)*(at-a);
    }
    return 255;
}
static void histogram(const uint8_t *p, unsigned n, unsigned h[256]) {
    memset(h,0,256*sizeof *h); for(unsigned x=0;x<n;x++) h[p[x]]++;
}
static double correlation(const uint8_t *a,const uint8_t *b,unsigned n) {
    double sa=0,sb=0,aa=0,bb=0,ab=0;
    for(unsigned i=0;i<n;i++){ double x=a[i],y=b[i];sa+=x;sb+=y;aa+=x*x;bb+=y*y;ab+=x*y; }
    double va=aa-sa*sa/n,vb=bb-sb*sb/n;
    return va>0 && vb>0 ? (ab-sa*sb/n)/sqrt(va*vb) : -1;
}
static double horizontal_level(const uint8_t *y,int off,int *columns) {
    unsigned h[256]={0},pool[256];
    for(int r=18+off;r<=261+off;r++)h[y[r*720]]++;
    double med=quantile(h,244,.5),hi=quantile(h,244,.9);
    double allow=med+fmax(hi-med,1.0);
    memcpy(pool,h,sizeof pool); *columns=1;
    for(int x=1;x<24;x++) {
        memset(h,0,sizeof h);
        for(int r=18+off;r<=261+off;r++)h[y[r*720+x]]++;
        if(quantile(h,244,.5)>allow)break;
        for(int v=0;v<256;v++)pool[v]+=h[v];
        ++*columns;
    }
    return quantile(pool,244*(unsigned)*columns,.99);
}
static int picture(const uint8_t *y,int row,double reference,int top) {
    unsigned h[256]; const uint8_t *p=y+row*720;
    histogram(p+40,640,h);
    double hi=quantile(h,640,.95),spread=hi-quantile(h,640,.05);
    if((top ? hi<=reference : hi-reference<=5) || spread<=4) return 0;
    if(top && spread>=40) {
        for(int lag=-24;lag<=24;lag++)
            if(correlation(p+64,p+720+64+lag,592)>=.5) return 1;
        return 0;
    }
    return 1;
}
static int first(const uint8_t *y,int a,int b,double blank) {
    for(int r=a;r<b;r++) if(picture(y,r,blank,1)) return r+4;
    return 0;
}
static double runin(const uint8_t *row) {
    /* Same authored period and start grid as the reference; no parity decoder. */
    double cs[188],sn[188],best=0;
    for(int k=0;k<188;k++){ double w=2*3.14159265358979323846*k/26.81;cs[k]=cos(w);sn[k]=sin(w); }
    for(int a=10;a<60;a+=4) {
        double mean=0,re=0,im=0,den=0;
        for(int k=0;k<188;k++) mean+=row[a+k]; mean/=188;
        for(int k=0;k<188;k++){double s=row[a+k]-mean;den+=s*s;re+=s*cs[k];im-=s*sn[k];}
        if(den>=1){double v=(re*re+im*im)/(94*den);if(v>best)best=v;}
    }
    return best;
}
void ge_measure(const uint8_t *y,ge_features *f) {
    memset(f,0,sizeof *f);
    for(int k=0;k<2;k++) {
        unsigned h[256]; int off=263*k;
        histogram(y+(7+off)*720,9*720,h); f->blank[k]=quantile(h,9*720,.5);
        f->hblank_level[k]=horizontal_level(y,off,&f->hblank_cols[k]);
        f->first[k]=first(y,18+off,37+off,f->hblank_level[k]);
        for(int r=258+off;r>236+off;r--) if(picture(y,r,f->blank[k],0)){f->last[k]=r+4;break;}
        for(int j=0;j<12;j++) {
            const uint8_t *p=y+(247+off+j)*720; unsigned n=0;
            for(int x=0;x<672;x++) {
                unsigned sum=0;for(int i=0;i<8;i++)sum+=p[x+20+i];
                f->profile[k][j][x]=(uint16_t)sum;
                n+=sum>8*(f->blank[k]+12);
            }
            if(n>=8)f->bottom[k]=251+off+j;
        }
    }
    f->rule_first=f->first[0];
    unsigned sum=0; for(int x=40;x<680;x++)sum+=y[19*720+x];
    f->plain23=sum/640.0-f->blank[0]>30 && correlation(y+19*720+40,y+20*720+40,640)>=.5;
    if(f->first[0]==23 && !f->plain23) f->first[0]=first(y,20,37,f->hblank_level[0]);
    f->auto_first=f->first[0];
    if(f->first[0] && f->first[1]) {
        unsigned h[256]; histogram(y+(f->first[1]-5)*720+40,640,h);
        f->runin=runin(y+(f->first[0]-5)*720);
        if(f->runin>=.5 && quantile(h,640,.95)-f->blank[1]>5) f->first[0]++;
    }
}
static ge_class classify(const ge_features *a,const ge_features *b,int f) {
    if(!a->first[f]||!b->first[f]||!a->last[f]||!b->last[f]||!a->bottom[f]||!b->bottom[f])return GE_UNKNOWN;
    unsigned gb[12]={0},gp[12]={0};
    for(int j=0;j<12;j++)for(int x=0;x<672;x++) {
        int p=a->profile[f][j][x],q=b->profile[f][j][x];
        int ab=p<=8*(a->blank[f]+12),bb=q<=8*(b->blank[f]+12);
        gb[j]+=!ab && bb && p-q>160;gp[j]+=ab && !bb && q-p>160;
    }
    int dt=b->first[f]-a->first[f],db=b->bottom[f]-a->bottom[f];
    int i=a->bottom[f]-(251+263*f),j=b->bottom[f]-(251+263*f);unsigned n=0;
    if(db<0){for(int k=j+1;k<=i;k++)n+=gb[k];if(n<8)db=0;}
    if(db>0){for(int k=i+1;k<=j;k++)n+=gp[k];if(n<8)db=0;}
    unsigned lost=gb[i]+(i<11?gb[i+1]:0),gain=gp[i]+(i<11?gp[i+1]:0);
    int partial=db==0 && (lost>=64||gain>=64);
    if(dt==0 && db==0 && !partial)return GE_NOTHING;
    if(dt==db && dt!=0 && !partial)return GE_VALID_MOVE;
    if(dt==0)return GE_BOTTOM_ONLY;
    if(db==0 && !partial)return GE_TOP_ONLY;
    return GE_NOT_IN_TANDEM;
}
ge_comb_result ge_comb(const uint8_t *t,const uint8_t *b) {
    double energy[11];int best=0,second=1;
    for(int d=-5;d<=5;d++) {
        uint64_t sum=0;
        for(int r=30;r<=240;r++) {
            const uint8_t *a=t+(r-4)*720+24,*c=a+720,*bb=b+(r+259+d)*720+24;
            for(int x=0;x<672;x++){int v=((int)a[x]-bb[x])*((int)c[x]-bb[x]);sum+=v>0?(unsigned)v:0;}
        }
        /* NumPy's input and mean output are float32. Exact integer accumulation
         * avoids architecture-dependent reduction order; float rounding below
         * is checked against the declared 1e-4 relative margin tolerance. */
        energy[d+5]=(float)((double)sum/(211*672));
    }
    if(energy[second]<energy[best]){best=1;second=0;}
    for(int i=2;i<11;i++) {
        if(energy[i]<energy[best]){second=best;best=i;}
        else if(energy[i]<energy[second])second=i;
    }
    double margin=energy[best]>0?energy[second]/energy[best]:(energy[second]>0?INFINITY:1);
    ge_comb_result result={.shift=best-5,.decided=margin>=1.5,.margin=margin};
    memcpy(result.energies,energy,sizeof energy);
    return result;
}
static void reset_frame_state(geometry_engine *g) {
    g->held=0;g->provisional=0;g->have_placement=0;g->last_d=g->last_d2=0;
}
static int rerun(ge_class c) { return c!=GE_NOTHING && c!=GE_VALID_MOVE; }
static ge_decision frame(geometry_engine *g,const uint8_t *ty,const uint8_t *by,
                         const ge_features *t,const ge_features *b,uint64_t tc,uint64_t bc) {
    ge_decision o={0};o.counter=bc;o.top_unit=tc;o.has_frame=1;o.comb.margin=NAN;
    o.first[0]=t->first[0];o.first[1]=b->first[1];
    o.last[0]=t->last[0];o.last[1]=b->last[1];
    o.bottom[0]=t->bottom[0];o.bottom[1]=b->bottom[1];
    o.motion[0]=t->motion[0];o.motion[1]=b->motion[1];
    int known=t->first[0] && b->first[1],st=0,d=0,dknown=known;
    if(!known) o.triggers=GE_UNMEASURABLE;
    else {
        st=b->first[1]-263-t->first[0];d=st+g->held;
        int lastknown=t->last[0] && b->last[1],sl=b->last[1]-263-t->last[0];
        if((d!=st && d!=st+1) || (lastknown && d!=sl && d!=sl+1))o.triggers|=GE_T1;
        if(!lastknown||!t->bottom[0]||!b->bottom[1])o.triggers|=GE_UNMEASURABLE;
        if(rerun(t->motion[0]))o.triggers|=GE_FIELD1;
        if(rerun(b->motion[1]))o.triggers|=GE_FIELD2;
        if(g->provisional)o.triggers|=GE_CONFIRM;
    }
    o.comb_ran=o.triggers!=0;
    if(o.comb_ran || g->audit)o.comb=ge_comb(ty,by);
    if(o.comb_ran && o.comb.decided) {
        d=o.comb.shift;dknown=1;
        if(!known){g->held=0;g->provisional=0;}
        else {
            int correction=d-st;
            if(g->provisional)g->provisional=0;
            else if(correction!=g->held)g->provisional=1;
            g->held=correction;
        }
    }
    if(!dknown)d=g->have_placement?g->last_d:0;
    int d2=b->first[1]?b->first[1]-286:(g->have_placement?g->last_d2:0);
    o.frame_d1=o.d1=d2-d;o.frame_d2=o.d2=d2;o.published_d=d;o.held=g->held;
    g->last_d=d;g->last_d2=d2;g->have_placement=1;
    return o;
}
unsigned ge_break(geometry_engine *g,ge_decision out[2]) {
    unsigned n=0;
    if(g->valid && g->reverse)out[n++]=g->pending;
    g->valid=0;reset_frame_state(g);return n;
}
static void unit_provenance(ge_decision *d,const ge_features *f) {
    memcpy(d->hblank_level,f->hblank_level,sizeof d->hblank_level);
    memcpy(d->hblank_cols,f->hblank_cols,sizeof d->hblank_cols);
}
unsigned ge_push(geometry_engine *g,const uint8_t *y,uint64_t c,int reset,ge_decision out[2]) {
    unsigned n=0;int adjacent=g->valid && g->counter!=UINT64_MAX && c==g->counter+1;
    if(g->valid && !adjacent)n=ge_break(g,out);
    ge_features *f=&g->current;ge_measure(y,f);
    if(adjacent && !reset)for(int k=0;k<2;k++)f->motion[k]=classify(&g->previous,f,k);
    if(reset || !adjacent)reset_frame_state(g);
    if(!g->reverse) {
        out[n]=frame(g,y,y,f,f,c,c);out[n].reset_before=reset;
        unit_provenance(out+n,f); n++;
    } else {
        int current_d1=f->first[0]?f->first[0]-23:0,unused1=1;
        if(adjacent) {
            ge_decision o=frame(g,y,g->previous_y,f,&g->previous,c,g->counter);
            current_d1=o.d1;unused1=0;
            o.d1=g->pending.d1;o.unused1=g->pending.unused1;o.reset_before=g->pending.reset_before;
            unit_provenance(&o,&g->previous);
            out[n++]=o;
        }
        ge_decision p={0};p.counter=c;p.d1=current_d1;p.d2=f->first[1]?f->first[1]-286:0;
        p.unused1=unused1;p.unused2=1;p.reset_before=reset;p.comb.margin=NAN;
        unit_provenance(&p,f);
        g->pending=p;memcpy(g->previous_y,y,GE_PIXELS);
    }
    g->previous=*f;g->valid=1;g->counter=c;return n;
}
