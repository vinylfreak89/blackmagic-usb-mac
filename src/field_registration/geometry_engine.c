#include "geometry_engine.h"
#include <math.h>
#include <string.h>

double ge_wave_bar=.45;
int ge_wave_clamp=5;
double ge_comb_reject=2;
int ge_anchor_vote=0,ge_level_fill=0,ge_level_flat=0;

struct geometry_engine {
    int reverse, audit, valid, held, provisional, have_placement, last_d, last_d2;
    int basis_valid, basis_first[2]; /* tops of the frame that derived held */
    uint64_t counter;
    ge_features previous, current;
    uint8_t previous_y[GE_PIXELS];
    ge_decision pending;
    int vote_values[GE_VOTE_WINDOW], vote_count, vote_anchor, vote_published;
};
size_t ge_size(void) { return sizeof(geometry_engine); }
void ge_init(geometry_engine *g, int reverse, int audit) {
    memset(g,0,sizeof *g); g->reverse=!!reverse; g->audit=!!audit;
}
void ge_set_pairing(geometry_engine *g,int reverse) {
    /* Caller has flushed pending fields. A pairing reset clears evidence,
     * not the last published vote anchor; only ge_init starts a new session. */
    int anchor=g->vote_anchor,published=g->vote_published;
    ge_init(g,reverse,g->audit);
    g->vote_anchor=anchor;g->vote_published=published;
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
static double waveform_correlation(const uint8_t *a,const uint8_t *b) {
    /* Integer sufficient statistics are exact in double at 640 uint8 samples.
     * va/vb are n^2 times population variance. No level/coherence proxy. */
    double sa=0,sb=0,aa=0,bb=0,ab=0;
    for(int x=0;x<640;x++) {
        double p=a[x],q=b[x];sa+=p;sb+=q;aa+=p*p;bb+=q*q;ab+=p*q;
    }
    double va=640*aa-sa*sa,vb=640*bb-sb*sb;
    if(va<640.0*640*1e-18 || vb<640.0*640*1e-18)return 0;
    return (640*ab-sa*sb)/sqrt(va*vb);
}
ge_wave_result ge_wave_scan(const uint8_t *y,int field,double bar) {
    int off=263*field;
    ge_wave_result out={.max_step=-INFINITY};
    double previous=waveform_correlation(y+(18+off)*720+40,y+(17+off)*720+40);
    for(int r=19+off;r<37+off;r++) {
        double current=waveform_correlation(y+r*720+40,y+(r-1)*720+40);
        double step=current-previous;
        if(step>out.max_step)out.max_step=step;
        if(!out.first && step>bar){out.first=r+3;out.step=step;}
        previous=current;
    }
    return out;
}
int ge_wave_accept(ge_wave_result w,int field,int clamp) {
    int d=w.first-(field?286:23);
    return w.first && d>=-clamp && d<=clamp;
}
ge_level_result ge_level_scan(const uint8_t *y,int field,int clamp,int flat) {
    ge_level_result o={.measured=1};unsigned h[256]={0};int off=263*field;
    for(int r=7+off;r<=15+off;r++)for(int x=40;x<680;x++)h[y[r*720+x]]++;
    o.reference=quantile(h,9*640,.5);
    for(int r=18+off;r<=36+off;r++) {
        const uint8_t *p=y+r*720+40;unsigned sum=0,squares=0;
        for(int x=0;x<640;x++){sum+=p[x];squares+=(unsigned)p[x]*p[x];}
        double mean=sum/640.0;
        if(!(mean>o.reference+10))continue;
        o.first=r+4;o.mean=mean;
        o.sd=sqrt((640.0*squares-(double)sum*sum)/(640.0*640));
        o.corr_below=waveform_correlation(p,p+720);
        o.accepted=ge_wave_accept((ge_wave_result){.first=o.first},field,clamp) &&
            (o.corr_below>.30 || (flat && o.sd<10));
        break; /* first level crossing, not first candidate to pass all gates */
    }
    return o;
}
const char *ge_wave_status_name(ge_wave_status s) {
    static const char *const names[]={"ABSTAIN","ACCEPTED","DISCARDED"};
    return names[s];
}
const char *ge_source_name(ge_source s) {
    static const char *const names[]={"","census","held_correction","comb","previous","section_start",
        "comb_rejection","discard_previous","discard_section_start","anchor_vote"};
    return names[s];
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
static int bottom_picture(const uint8_t *y,int row,double reference) {
    unsigned h[256]; const uint8_t *p=y+row*720;
    histogram(p+40,640,h);
    double hi=quantile(h,640,.95),spread=hi-quantile(h,640,.05);
    return !(hi-reference<=5 || spread<=4);
}
void ge_measure(const uint8_t *y,ge_features *f) {
    memset(f,0,sizeof *f);
    for(int k=0;k<2;k++) {
        unsigned h[256]; int off=263*k;
        histogram(y+(7+off)*720,9*720,h); f->blank[k]=quantile(h,9*720,.5);
        f->hblank_level[k]=horizontal_level(y,off,&f->hblank_cols[k]);
        f->wave[k]=ge_wave_scan(y,k,ge_wave_bar);
        f->wave_status[k]=!f->wave[k].first?GE_WAVE_ABSTAIN:
            ge_wave_accept(f->wave[k],k,ge_wave_clamp)?GE_WAVE_ACCEPTED:GE_WAVE_DISCARDED;
        if(f->wave_status[k]==GE_WAVE_ACCEPTED)f->first[k]=f->wave[k].first;
        if(ge_anchor_vote && ge_level_fill && f->wave_status[k]==GE_WAVE_ABSTAIN)
            f->level[k]=ge_level_scan(y,k,ge_wave_clamp,ge_level_flat);
        for(int r=258+off;r>236+off;r--) if(bottom_picture(y,r,f->blank[k])){f->last[k]=r+4;break;}
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
    ge_comb_result result={.shift=best-5,.decided=margin>=GE_COMB_SELECTION_MARGIN,.margin=margin};
    memcpy(result.energies,energy,sizeof energy);
    return result;
}
static double energy_ratio(double energy,double minimum) {
    return minimum>0?energy/minimum:(energy>0?INFINITY:1);
}
ge_comb_evidence ge_comb_examine(const ge_comb_result *c,int proposed) {
    ge_comb_evidence o={.ratio=NAN,.rise_left=NAN,.rise_right=NAN};
    if(isnan(c->margin))return o;
    int best=c->shift+5,lo=best,hi=best;
    const double *e=c->energies;
    double minimum=e[best],ceiling=GE_COMB_SELECTION_MARGIN*minimum;
    while(lo>0 && e[lo-1]<=ceiling)lo--;
    while(hi<10 && e[hi+1]<=ceiling)hi++;
    o.floor_lo=lo-5;o.floor_hi=hi-5;
    if(lo>0)o.rise_left=energy_ratio(e[lo-1],minimum);
    if(hi<10)o.rise_right=energy_ratio(e[hi+1],minimum);
    o.basin=lo>0 && hi<10 && o.rise_left>=GE_COMB_SELECTION_MARGIN &&
        o.rise_right>=GE_COMB_SELECTION_MARGIN;
    if(proposed>=-5 && proposed<=5)o.ratio=energy_ratio(e[proposed+5],minimum);
    return o;
}
static void reject_placement(geometry_engine *g,ge_decision *o,int *d,int *d2) {
    o->rejection=ge_comb_examine(&o->comb,*d);
    /* Audit-only evidence cannot change placement or state. No extra search. */
    if(!o->comb_ran || !(o->rejection.ratio>ge_comb_reject))return;
    o->rejected=1;o->refused_d=*d;
    g->held=0;g->provisional=0;g->basis_valid=0;
    g->basis_first[0]=g->basis_first[1]=0;
    if(o->rejection.basin) {
        *d=o->comb.shift;o->substituted_d=*d;o->relative_source=GE_SOURCE_REJECT;
    } else {
        /* Discard the proposed GEOMETRY, never the frame's image data. Holding
         * the complete published pair does not enact another unsupported top.
         * At a section start, use the existing unregistered zero placement. */
        o->discarded=1;
        *d=g->have_placement?g->last_d:0;
        *d2=g->have_placement?g->last_d2:0;
        o->relative_source=o->anchor_source=g->have_placement?
            GE_SOURCE_DISCARD_PREVIOUS:GE_SOURCE_DISCARD_START;
    }
}
static void reset_frame_state(geometry_engine *g) {
    g->held=0;g->provisional=0;g->have_placement=0;g->last_d=g->last_d2=0;
    g->basis_valid=0;g->basis_first[0]=g->basis_first[1]=0;
    g->vote_count=0;
}
static void vote_anchor(geometry_engine *g,ge_decision *o,
                        const ge_features *t,const ge_features *b) {
    o->vote_engine_anchor=o->frame_d2;
    o->vote_anchor=o->frame_d2;
    if(!ge_anchor_vote)return;
    o->level[0]=t->level[0];o->level[1]=b->level[1];
    for(int k=0;k<2;k++) {
        const ge_features *f=k?b:t;
        o->vote_top[k]=f->first[k];
        if(ge_level_fill && !f->first[k] && f->wave_status[k]==GE_WAVE_ABSTAIN && f->level[k].accepted)
            o->vote_top[k]=f->level[k].first;
    }
    int st=o->vote_top[1]-263-o->vote_top[0];
    o->vote_confident=o->vote_top[0] && o->vote_top[1] && o->rejection.basin &&
        st>=o->rejection.floor_lo && st<=o->rejection.floor_hi;
    if(o->vote_confident) {
        if(g->vote_count==GE_VOTE_WINDOW) {
            memmove(g->vote_values,g->vote_values+1,(GE_VOTE_WINDOW-1)*sizeof(int));
            g->vote_count--;
        }
        g->vote_values[g->vote_count++]=o->vote_top[1]-286;
    }
    if(g->vote_count) {
        int best=0,first=0,current=0,recent=0;
        for(int i=0;i<g->vote_count;i++) {
            int n=0;
            for(int j=0;j<g->vote_count;j++)n+=g->vote_values[i]==g->vote_values[j];
            if(n>best){best=n;first=g->vote_values[i];}
            if(g->vote_values[i]==g->vote_anchor)current=n;
            if(i==g->vote_count-1)recent=n;
        }
        if(current!=best)g->vote_anchor=recent==best?g->vote_values[g->vote_count-1]:first;
        o->vote_winner_count=best;o->anchor_source=GE_SOURCE_VOTE;
    } else if(!g->vote_published)g->vote_anchor=o->vote_engine_anchor;
    else o->anchor_source=GE_SOURCE_VOTE;
    g->vote_published=1;
    o->vote_count=g->vote_count;o->vote_anchor=g->vote_anchor;
    o->frame_d2=o->d2=g->vote_anchor;
    o->frame_d1=o->d1=g->vote_anchor-o->published_d;
}
static int rerun(ge_class c) { return c!=GE_NOTHING && c!=GE_VALID_MOVE; }
static ge_decision frame(geometry_engine *g,const uint8_t *ty,const uint8_t *by,
                         const ge_features *t,const ge_features *b,uint64_t tc,uint64_t bc) {
    ge_decision o={0};o.counter=bc;o.top_unit=tc;o.has_frame=1;o.comb.margin=NAN;
    o.first[0]=t->first[0];o.first[1]=b->first[1];
    o.last[0]=t->last[0];o.last[1]=b->last[1];
    o.bottom[0]=t->bottom[0];o.bottom[1]=b->bottom[1];
    o.motion[0]=t->motion[0];o.motion[1]=b->motion[1];
    /* A held correction belongs to these two frame tops, not to a transport
     * unit (the top field can belong to the next unit under reversed pairing).
     * Loss of a measured top also invalidates that basis. Retry on this frame;
     * an abstaining comb must not restore the stale correction. */
    if(g->basis_valid && (t->first[0]!=g->basis_first[0] || b->first[1]!=g->basis_first[1])) {
        g->held=0;g->provisional=0;g->basis_valid=0;
        o.triggers|=GE_BASIS_CHANGED;
    }
    int known=t->first[0] && b->first[1],st=0,d=0,dknown=known;
    o.relative_source=known?(g->held?GE_SOURCE_HELD:GE_SOURCE_CENSUS):
        (g->have_placement?GE_SOURCE_PREVIOUS:GE_SOURCE_START);
    o.anchor_source=b->first[1]?GE_SOURCE_CENSUS:
        (g->have_placement?GE_SOURCE_PREVIOUS:GE_SOURCE_START);
    if(!known) o.triggers|=GE_UNMEASURABLE;
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
    if(o.comb_ran || g->audit || ge_anchor_vote)o.comb=ge_comb(ty,by);
    if(o.comb_ran && o.comb.decided) {
        o.relative_source=GE_SOURCE_COMB;
        d=o.comb.shift;dknown=1;
        if(!known){g->held=0;g->provisional=0;g->basis_valid=0;}
        else {
            int correction=d-st;
            if(g->provisional)g->provisional=0;
            else if(correction!=g->held)g->provisional=1;
            g->held=correction;
            g->basis_first[0]=t->first[0];g->basis_first[1]=b->first[1];g->basis_valid=1;
        }
    }
    if(!dknown)d=g->have_placement?g->last_d:0;
    int d2=b->first[1]?b->first[1]-286:(g->have_placement?g->last_d2:0);
    reject_placement(g,&o,&d,&d2);
    o.frame_d1=o.d1=d2-d;o.frame_d2=o.d2=d2;o.published_d=d;o.held=g->held;
    g->last_d=d;g->last_d2=d2;g->have_placement=1;
    /* Keep the original engine state untouched: later missing-top and basin
     * fallbacks must see the tag's anchor, not an earlier voted placement. */
    vote_anchor(g,&o,t,b);
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
    memcpy(d->wave,f->wave,sizeof d->wave);
    memcpy(d->wave_status,f->wave_status,sizeof d->wave_status);
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
