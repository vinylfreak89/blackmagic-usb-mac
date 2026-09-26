#include "geometry_engine.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

static const ge_config defaults = {
    .wave_bar=.45, .wave_clamp=5, .comb_reject=2, .comb_basin_factor=1.5,
    .vote_window=30, .vote_pair_min=.6, .bottom_flat_margin=3,
    .blankspot_tolerance=2, .rigid_min=2, .rigid_clarity=1.3
};
ge_config ge_default_config(void) { return defaults; }
int ge_config_valid(const ge_config *c) {
    return c && isfinite(c->wave_bar) && c->wave_clamp>=0 &&
        isfinite(c->comb_reject) && c->comb_reject>0 &&
        isfinite(c->comb_basin_factor) && c->comb_basin_factor>=1 &&
        c->vote_window>=1 && c->vote_window<=GE_VOTE_CAPACITY &&
        isfinite(c->vote_pair_min) && c->vote_pair_min>=-1 && c->vote_pair_min<=1 &&
        isfinite(c->bottom_flat_margin) && c->bottom_flat_margin>0 &&
        isfinite(c->blankspot_tolerance) && c->blankspot_tolerance>=0 &&
        c->rigid_min>=1 && isfinite(c->rigid_clarity) && c->rigid_clarity>=1;
}

struct geometry_engine {
    ge_config config;
    int reverse, valid, held, provisional, have_placement, last_d, last_d2;
    int basis_valid, basis_first[2]; /* tops of the frame that derived held */
    uint64_t counter;
    ge_features previous, current;
    uint8_t previous_y[GE_PIXELS];
    ge_decision pending;
    int vote_values[GE_VOTE_CAPACITY], vote_count, vote_anchor, vote_published;
};
size_t ge_size(void) { return sizeof(geometry_engine); }
const ge_config *ge_get_config(const geometry_engine *g) { return &g->config; }
int ge_init(geometry_engine *g, int reverse, const ge_config *config) {
    ge_config c=config?*config:defaults; /* copy before clearing, even if aliased */
    if(!g || !ge_config_valid(&c))return -1;
    memset(g,0,sizeof *g); g->reverse=!!reverse;g->config=c;
    return 0;
}
void ge_set_pairing(geometry_engine *g,int reverse) {
    /* Caller has flushed pending fields. A pairing reset clears evidence,
     * not the last published vote anchor; only ge_init starts a new session. */
    int anchor=g->vote_anchor,published=g->vote_published;
    ge_init(g,reverse,&g->config);
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
ge_vertical_motion ge_motion_measure(const uint8_t *current,const uint8_t *previous,int field) {
    unsigned sums[11];int best=0,second=-1,off=19+263*field;
    for(int s=-5;s<=5;s++) {
        unsigned sum=0;
        for(int r=40;r<220;r++) {
            const uint8_t *a=current+(off+r+s)*720+40,*b=previous+(off+r)*720+40;
            for(int x=0;x<640;x++){int d=(int)a[x]-b[x];sum+=(unsigned)(d<0?-d:d);}
        }
        sums[s+5]=sum;
    }
    /* Exact ties prefer the smallest absolute shift; equal magnitudes retain
     * the first (negative) shift. No rounded-error comparison. */
    for(int i=1;i<11;i++)if(sums[i]<sums[best] ||
        (sums[i]==sums[best] && abs(i-5)<abs(best-5)))best=i;
    for(int i=0;i<11;i++)if(i!=best && (second<0 || sums[i]<sums[second]))second=i;
    return (ge_vertical_motion){.known=1,.shift=best-5,
        .error=sums[best]/(180.0*640),.second_error=sums[second]/(180.0*640)};
}
ge_rigid_motion ge_rigid_measure(const uint8_t *current,const uint8_t *previous,int field) {
    unsigned sums[11][17],best=UINT32_MAX,far=UINT32_MAX;
    int bx=0,by=0,off=19+263*field;
    for(int dy=-5;dy<=5;dy++)for(int dx=-8;dx<=8;dx++) {
        unsigned sum=0;
        for(int r=40;r<220;r++) {
            const uint8_t *a=current+(off+r+dy)*720+40+dx,*b=previous+(off+r)*720+40;
            for(int x=0;x<640;x+=2){int d=(int)a[x]-b[x];sum+=(unsigned)(d<0?-d:d);}
        }
        sums[dy+5][dx+8]=sum;
        /* Reference order: dy first, dx second; an exact tie keeps the first. */
        if(sum<best){best=sum;bx=dx;by=dy;}
    }
    for(int dy=-5;dy<=5;dy++)for(int dx=-8;dx<=8;dx++)
        if((abs(dx-bx)>=2 || abs(dy-by)>=2) && sums[dy+5][dx+8]<far)far=sums[dy+5][dx+8];
    return (ge_rigid_motion){.known=1,.dx=bx,.dy=by,.error=best/(180.0*320),
        .far_error=far/(180.0*320),.clarity=best?(double)far/best:far?INFINITY:1};
}
static int rigid_vertical(const ge_rigid_motion *r,const ge_config *c) {
    return r->known && r->dx==0 && abs(r->dy)>=c->rigid_min && r->clarity>=c->rigid_clarity;
}
const char *ge_picture_motion_name(ge_picture_motion s) {
    static const char *const names[]={"unknown","still","moving"};return names[s];
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
ge_level_result ge_level_scan(const uint8_t *y,int field,int clamp) {
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
            o.corr_below>.30;
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
const char *ge_bottom_rule_name(ge_bottom_rule rule) {
    static const char *const names[]={"unknown","flat_reference","fallback"};
    return names[rule];
}
static int bottom_scan(const uint8_t *y,int field,double blank,ge_bottom_evidence *e,double threshold) {
    int off=263*field,start=258+off;
    *e=(ge_bottom_evidence){0};
    {
        unsigned h[256];histogram(y+start*720+40,640,h);
        e->measured=1;e->p5=quantile(h,640,.05);
        e->p50=quantile(h,640,.5);e->p95=quantile(h,640,.95);
        if(e->p95-e->p5<=4) {
            const double margin=threshold-1e-9;
            for(int r=start-1;r>236+off;r--) {
                histogram(y+r*720+40,640,h);
                double p5=quantile(h,640,.05),p50=quantile(h,640,.5),p95=quantile(h,640,.95);
                if(p50-e->p50>=margin || p95-e->p95>=margin || e->p5-p5>=margin) {
                    e->rule=GE_BOTTOM_FLAT_REFERENCE;return r+4;
                }
            }
            return 0; /* qualified reference but no picture: explicitly unknown */
        }
        if(!field)start++; /* fallback alone reaches NTSC half-line 263 */
    }
    for(int r=start;r>236+off;r--)if(bottom_picture(y,r,blank)) {
        e->rule=GE_BOTTOM_FALLBACK;return r+4;
    }
    return 0;
}
void ge_measure(const uint8_t *y,ge_features *f,const ge_config *config) {
    const ge_config *c=config?config:&defaults;
    memset(f,0,sizeof *f);
    for(int k=0;k<2;k++) {
        unsigned h[256]; int off=263*k;
        histogram(y+(7+off)*720,9*720,h); f->blank[k]=quantile(h,9*720,.5);
        f->hblank_level[k]=horizontal_level(y,off,&f->hblank_cols[k]);
        f->wave[k]=ge_wave_scan(y,k,c->wave_bar);
        f->wave_status[k]=!f->wave[k].first?GE_WAVE_ABSTAIN:
            ge_wave_accept(f->wave[k],k,c->wave_clamp)?GE_WAVE_ACCEPTED:GE_WAVE_DISCARDED;
        if(f->wave_status[k]==GE_WAVE_ACCEPTED)f->first[k]=f->wave[k].first;
        if(f->wave_status[k]==GE_WAVE_ABSTAIN)
            f->level[k]=ge_level_scan(y,k,c->wave_clamp);
        f->last[k]=bottom_scan(y,k,f->blank[k],&f->bottom_evidence[k],c->bottom_flat_margin);
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
ge_comb_result ge_comb(const uint8_t *t,const uint8_t *b,const ge_config *config) {
    const ge_config *cfg=config?config:&defaults;
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
    ge_comb_result result={.shift=best-5,.decided=margin>=cfg->comb_basin_factor,.margin=margin};
    memcpy(result.energies,energy,sizeof energy);
    return result;
}
static double energy_ratio(double energy,double minimum) {
    return minimum>0?energy/minimum:(energy>0?INFINITY:1);
}
ge_comb_evidence ge_comb_examine(const ge_comb_result *c,int proposed,const ge_config *config) {
    const ge_config *cfg=config?config:&defaults;
    ge_comb_evidence o={.ratio=NAN,.rise_left=NAN,.rise_right=NAN};
    if(isnan(c->margin))return o;
    int best=c->shift+5,lo=best,hi=best;
    const double *e=c->energies;
    double minimum=e[best],ceiling=cfg->comb_basin_factor*minimum;
    while(lo>0 && e[lo-1]<=ceiling)lo--;
    while(hi<10 && e[hi+1]<=ceiling)hi++;
    o.floor_lo=lo-5;o.floor_hi=hi-5;
    if(lo>0)o.rise_left=energy_ratio(e[lo-1],minimum);
    if(hi<10)o.rise_right=energy_ratio(e[hi+1],minimum);
    o.basin=lo>0 && hi<10 && o.rise_left>=cfg->comb_basin_factor &&
        o.rise_right>=cfg->comb_basin_factor;
    if(proposed>=-5 && proposed<=5)o.ratio=energy_ratio(e[proposed+5],minimum);
    return o;
}
static void reject_placement(geometry_engine *g,ge_decision *o,int *d,int *d2) {
    o->rejection=ge_comb_examine(&o->comb,*d,&g->config);
    /* Untriggered evidence cannot change relative placement or state. */
    if(!o->comb_ran || o->comb_suppressed || !(o->rejection.ratio>g->config.comb_reject))return;
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
                        const ge_features *t,const ge_features *b,
                        const uint8_t *ty,const uint8_t *by) {
    o->vote_engine_anchor=o->frame_d2;
    o->vote_anchor=o->frame_d2;
    o->vote_rB=NAN;o->vote_pair_pass=0;
    o->level[0]=t->level[0];o->level[1]=b->level[1];
    for(int k=0;k<2;k++) {
        const ge_features *f=k?b:t;
        o->vote_top[k]=f->first[k];
        if(!f->first[k] && f->wave_status[k]==GE_WAVE_ABSTAIN && f->level[k].accepted)
            o->vote_top[k]=f->level[k].first;
    }
    int st=o->vote_top[1]-263-o->vote_top[0];
    if(o->vote_top[0] && o->vote_top[1]) {
        /* Frame ownership matters: reversed pairing reads field 1 from the
         * next unit, not from the unit owning field 2 and this decision row. */
        o->vote_rB=waveform_correlation(ty+(o->vote_top[0]-4)*720+40,
                                      by+(o->vote_top[1]-4)*720+40);
        o->vote_pair_pass=o->vote_rB>=g->config.vote_pair_min;
    }
    o->vote_confident=o->vote_top[0] && o->vote_top[1] && o->rejection.basin &&
        st>=o->rejection.floor_lo && st<=o->rejection.floor_hi+1 && o->vote_pair_pass;
    if(o->vote_top[1]) {
        o->vote_blankspot_measured=1;o->vote_blankspot_pass=1;
        for(int line=286;line<o->vote_top[1];line++) {
            unsigned count=0;const uint8_t *p=by+(line-4)*720+40;
            for(int x=0;x<640;x++)count+=p[x]<=b->blank[1]+g->config.blankspot_tolerance;
            if(!count){o->vote_blankspot_pass=0;o->vote_blankspot_line=line;break;}
        }
        o->vote_confident=o->vote_confident && o->vote_blankspot_pass;
    }
    if(o->vote_confident) {
        if(g->vote_count==g->config.vote_window) {
            memmove(g->vote_values,g->vote_values+1,(g->config.vote_window-1)*sizeof(int));
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
    o.bottom_evidence[0]=t->bottom_evidence[0];o.bottom_evidence[1]=b->bottom_evidence[1];
    o.bottom[0]=t->bottom[0];o.bottom[1]=b->bottom[1];
    o.motion[0]=t->motion[0];o.motion[1]=b->motion[1];
    o.vertical[0]=t->vertical[0];o.vertical[1]=b->vertical[1];
    o.rigid[0]=t->rigid[0];o.rigid[1]=b->rigid[1];
    if(o.vertical[0].known && o.vertical[1].known)
        o.picture_motion=o.vertical[0].shift || o.vertical[1].shift?GE_PICTURE_MOVING:GE_PICTURE_STILL;
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
    o.comb=ge_comb(ty,by,&g->config);
    if(o.picture_motion==GE_PICTURE_STILL) {
        int proposed=dknown?d:(g->have_placement?g->last_d:0);
        ge_comb_evidence e=ge_comb_examine(&o.comb,proposed,&g->config);
        if(e.basin && e.ratio>=g->config.comb_reject) {
            o.still_trigger=1;o.triggers|=GE_STILL;o.comb_ran=1;
        }
    }
    o.comb_suppressed=o.picture_motion==GE_PICTURE_MOVING && o.comb_ran &&
        rigid_vertical(o.rigid,&g->config) && rigid_vertical(o.rigid+1,&g->config);
    if(o.comb_ran && !o.comb_suppressed && o.comb.decided) {
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
    /* Relative-policy state retains its own absolute anchor: missing-top and
     * basin fallbacks must not feed an earlier voted placement back into it. */
    vote_anchor(g,&o,t,b,ty,by);
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
    ge_features *f=&g->current;ge_measure(y,f,&g->config);
    if(adjacent && !reset)for(int k=0;k<2;k++)f->motion[k]=classify(&g->previous,f,k);
    if(adjacent && !reset)
        for(int k=0;k<2;k++) {
            f->vertical[k]=ge_motion_measure(y,g->previous_y,k);
            if(abs(f->vertical[k].shift)>=g->config.rigid_min)
                f->rigid[k]=ge_rigid_measure(y,g->previous_y,k);
        }
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
        g->pending=p;
    }
    memcpy(g->previous_y,y,GE_PIXELS);
    g->previous=*f;g->valid=1;g->counter=c;return n;
}
