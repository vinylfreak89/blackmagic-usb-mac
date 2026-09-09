#define _POSIX_C_SOURCE 200809L
/* Scalar diagnostic, not a new engine algorithm. Uses the production parser,
 * classifier and comb_pair. The five-shift window and 24:696 horizontal crop
 * deliberately reproduce the reviewed harness measurement, not a standard.
 * No program bytes are written. CAP1/parser provenance errors abort. */
#include "../field_registration.c"
#include "../../signal_state/signal_state.h"
#include <assert.h>
#include <stdio.h>
#include <time.h>

static field_registration engine, prior;
static signal_state *sig;
static unsigned measured, exact;
static uint64_t ns(void){struct timespec t;assert(!clock_gettime(CLOCK_MONOTONIC,&t));return (uint64_t)t.tv_sec*1000000000+t.tv_nsec;}
static double pixel_product(const uint8_t *r,int shift){
    double sum=0;
    for(int y=0;y<238;++y)for(int x=24;x<696;++x){
        int a=r[(size_t)(19+y)*1440+2*x+1],c=r[(size_t)(20+y)*1440+2*x+1];
        int b=r[(size_t)(282+y+shift)*1440+2*x+1];
        int v=(a-b)*(c-b);if(v>0)sum+=v;
    }
    return sum/(238*672);
}
static void self_test(void){
    uint8_t *r=calloc(525,1440);assert(r);
    for(int y=0;y<240;++y)for(int x=0;x<720;++x){
        r[(size_t)(19+y)*1440+2*x+1]=(uint8_t)(y%2?120:100);
        r[(size_t)(282+y)*1440+2*x+1]=110;
    }
    assert(pixel_product(r,0)==0); /* b between a/c: no positive overshoot */
    for(int y=0;y<240;++y)for(int x=0;x<720;++x)r[(size_t)(282+y)*1440+2*x+1]=140;
    assert(pixel_product(r,0)==800); /* (100-140)*(120-140) */
    free(r);puts("pixel_product_bracket_and_overshoot: PASS");
}
static void inspect(unsigned ctr,const uint8_t *r,const fieldreg_decision *d){
    enum { C=FIELDREG_COMB_COLUMNS,H=240 };
    if(!prior.previous_luma_valid)return;
    comb_lowpass(&prior,r);
    int start[2]={19+d->applied_d1,282+d->applied_d2};
    int begin[2],end[2];unsigned tolerance=0;
    uint8_t valid[2][H],still[2][H][C];
    for(int f=0;f<2;++f){
        field_measurement m;measure_field(r,f,&m);
        begin[f]=m.top>=0?m.top:start[f];end[f]=m.switch_measurable?m.bottom:m.recorded_last;
        for(int row=f?270:7;row<=(f?278:15);++row)for(int x=0;x<C;++x){
            unsigned z=(unsigned)abs((int)prior.current_luma[row*C+x]-prior.previous_luma[row*C+x]);
            if(z>tolerance)tolerance=z;
        }
    }
    for(int f=0;f<2;++f)for(int y=0;y<H;++y)for(int x=0;x<C;++x){
        int a=start[f]+y,b=prior.previous_crop[f]+y;
        bool v=a>=begin[f] && a<=end[f] && b>=prior.previous_begin[f] && b<=prior.previous_end[f] && a>=0 && a<525 && b>=0 && b<525;
        valid[f][y]=v;
        still[f][y][x]=v && (unsigned)abs((int)prior.current_luma[a*C+x]-prior.previous_luma[b*C+x])<=tolerance;
    }
    printf("bounds,%u,%d,%d,%d,%d,%d,%d,%u\n",ctr,start[0]+4,start[1]+4,begin[0]+4,end[0]+4,begin[1]+4,end[1]+4,tolerance);
    /* Same pixels for ALL five local candidates, so means are comparable. */
    for(int masking=0;masking<2;++masking){
        double sums[2][5]={{0}},level=0;unsigned n=0;
        for(int y=3;y<237;++y)for(int x=0;x<C;++x){
            bool ok=valid[0][y] && valid[0][y+1];
            if(masking)ok=ok && still[0][y][x] && still[0][y+1][x];
            for(int k=y-3;k<=y+3;++k)ok=ok && valid[1][k] && (!masking || still[1][k][x]);
            if(!ok)continue;++n;level+=prior.current_luma[(start[0]+y)*C+x]/8.0;
            for(int q=-2;q<=2;++q){
                int ca=prior.current_luma[(start[0]+y)*C+x]+prior.current_luma[(start[0]+y+1)*C+x];
                int pa=prior.previous_luma[(prior.previous_crop[0]+y)*C+x]+prior.previous_luma[(prior.previous_crop[0]+y+1)*C+x];
                sums[0][q+2]+=abs(2*prior.current_luma[(start[1]+y+q)*C+x]-ca);
                sums[1][q+2]+=abs(2*prior.previous_luma[(prior.previous_crop[1]+y+q)*C+x]-pa);
            }
        }
        for(int q=-2;q<=2;++q)printf("local_%s,%u,%d,%u,%.9f,%.9f\n",masking?"static":"all",ctr,q,n,n?sums[0][q+2]/(16*n):0,n?sums[1][q+2]/(16*n):0);
        printf("support_%s,%u,%u,%.9f\n",masking?"static":"all",ctr,n,n?level/n:0);
    }
    /* Exact production pair test for the nominal candidate against a remote
     * alias, with the same pixels at both times. This isolates search scope. */
    for(int q=-238;q<=238;++q){
        comb_pair_reading p=comb_pair(&prior,start,valid,still,0,q);
        if(p.possible)printf("pair0,%u,%d,%u,%.9f,%.9f,%.9f,%.9f\n",ctr,q,p.samples,p.energy[0][0],p.energy[0][1],p.energy[1][0],p.energy[1][1]);
    }
}
static void video(void *ctx,const unit_video_observation *u){
    (void)ctx;assert(!(u->transport_flags & ~UNIT_FLAG_COUNTER_DISCONTINUITY));
    signal_result sr;assert(signal_state_classify(sig,u,NULL,&sr));
    if(sr.actions & SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT)fieldreg_begin_segment(&engine);
    else if(sr.actions & SIGNAL_ACTION_REGISTRATION_DISCONTINUITY)fieldreg_discontinuity(&engine);
    prior=engine;fieldreg_decision d={0};uint64_t t=ns();bool have=false;
    if(sr.normal_picture){have=fieldreg_process(&engine,u->bytes,&d);++measured;}else fieldreg_discontinuity(&engine);
    double ms=(ns()-t)/1e6;
    if(!u->fixed_raster_eligible)return;++exact;
    const uint8_t *r=u->bytes+48;
    printf("engine,%u,%d,%d,%d,%s,%d,%u,%.9f,%.6f\n",u->counter16,have,d.applied_d1,d.applied_d2,have?fieldreg_comb_check_name(d.comb_check):"gate",d.comb_candidate_shift,d.comb_unresolved_alternatives,d.comb_static_fraction,ms);
    if(u->counter16>=6667)for(int q=-2;q<=2;++q)printf("product,%u,%d,%.9f\n",u->counter16,q,pixel_product(r,q));
    if(have && (u->counter16==6667 || u->counter16==6687 || u->counter16==6690 || u->counter16==6700))inspect(u->counter16,r,&d);
}
static unsigned u32(const uint8_t *b){return b[0]|b[1]<<8|b[2]<<16|(unsigned)b[3]<<24;}
int main(int argc,char **argv){
    assert(argc==2);if(!strcmp(argv[1],"--self-test")){self_test();return 0;}
    sig=aligned_alloc(signal_state_alignment(),signal_state_size());assert(sig);signal_state_init(sig,NULL);
    fieldreg_config cfg=fieldreg_default_config();fieldreg_init(&engine,&cfg);
    unit_parser *p=aligned_alloc(unit_parser_alignment(),unit_parser_size());assert(p);
    unit_parser_callbacks cb={.on_video=video};unit_parser_init(p,NULL,&cb);
    FILE *f=fopen(argv[1],"rb");assert(f);uint8_t h[24];
    for(;;){
        size_t n=fread(h,1,24,f);if(!n){assert(!ferror(f));break;}
        assert(n==24 && u32(h)==0x31504143 && h[4]!=1 && h[4]!=2);
        unsigned size=u32(h+20);uint8_t *bytes=malloc(size?size:1);assert(bytes);assert(fread(bytes,1,size,f)==size);
        if(h[4]==0){assert(!u32(h+12));cc_packet packet={.endpoint=h[5],.pkt_index=h[6]|h[7]<<8,.submit_seq=u32(h+8),.status=0,.req_len=u32(h+16),.actual_len=size,.data=bytes};unit_parser_on_packet(p,&packet);}
        free(bytes);
    }
    unit_parser_finish(p);assert(!fclose(f));free(p);free(sig);assert(exact);fprintf(stderr,"exact=%u registration=%u\n",exact,measured);
}
