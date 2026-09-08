/* Diagnostic measurement on the real unit parser. No recording-specific
 * classifier rule lives here. CAP1 errors abort; fragments are never rasters. */
#include "../signal_state.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { double a,b,aa,bb,ab; unsigned n; } pairs;
static void pair(pairs *p, double a, double b) {
    p->a+=a; p->b+=b; p->aa+=a*a; p->bb+=b*b; p->ab+=a*b; ++p->n;
}
static double correlation(pairs p) {
    double a=p.n*p.aa-p.a*p.a, b=p.n*p.bb-p.b*p.b;
    return a>0 && b>0 ? (p.n*p.ab-p.a*p.b)/sqrt(a*b) : NAN;
}
static int cmp(const void *a,const void *b) {
    double x=*(const double *)a,y=*(const double *)b; return (x>y)-(x<y);
}
static uint8_t previous[756048];
static bool previous_valid;
static signal_state *state;
static const char *panel_dir;
static void video(void *ctx,const unit_video_observation *u) {
    (void)ctx;
    if (u->transport_flags) {
        fprintf(stderr,"transport counter=%llu kind=%d flags=%u eligible=%d\n",
                (unsigned long long)u->counter_extended, u->transport,
                u->transport_flags, u->fixed_raster_eligible);
        /* A device counter discontinuity is not CAP1 packet loss. Keep it
         * visible, and never compare temporal evidence across that boundary. */
        assert(!(u->transport_flags & ~UNIT_FLAG_COUNTER_DISCONTINUITY));
        previous_valid = false;
    }
    signal_result r;
    assert(signal_state_classify(state,u,NULL,&r));
    if (!u->fixed_raster_eligible) { previous_valid=false; return; }
    if (panel_dir && (u->counter16==53616 || u->counter16==53617 ||
                     u->counter16==53623 || u->counter16==53625 ||
                     u->counter16==53628 || u->counter16==53629)) {
        char path[1024]; snprintf(path,sizeof path,"%s/%u.pgm",panel_dir,u->counter16);
        FILE *image=fopen(path,"wb"); assert(image); fprintf(image,"P5\n1440 237\n255\n");
        for (int y=0;y<237;++y) for (int f=0;f<2;++f) for (int x=0;x<720;++x)
            fputc(u->bytes[48+(size_t)(y+(f?282:20))*1440+2*x+1],image);
        fclose(image);
    }
    double spatial[2], temporal[2];
    double row_sigma[2], row_range[2], blank_range[2];
    for (int f=0;f<2;++f) {
        int first=f?282:20;
        pairs time={0}; double rows[236], sigmas[237], ranges[237]; unsigned n=0;
        for (int y=first;y<first+237;++y) {
            pairs row={0};
            double sum=0,sum2=0; int lo=255,hi=0;
            for (int x=0;x<720;x+=4) {
                size_t pos=48+(size_t)y*1440+2*x+1;
                int v=u->bytes[pos]; sum+=v; sum2+=v*v; if(v<lo)lo=v; if(v>hi)hi=v;
                if (y>first) pair(&row,u->bytes[pos],u->bytes[pos-1440]);
                if (previous_valid) pair(&time,u->bytes[pos],previous[pos]);
            }
            double c=correlation(row);
            if (isfinite(c)) rows[n++]=c;
            sigmas[y-first]=sqrt(fmax(0,sum2/180-(sum/180)*(sum/180)));
            ranges[y-first]=hi-lo;
        }
        qsort(rows,n,sizeof *rows,cmp);
        spatial[f]=n?rows[n/2]:NAN; temporal[f]=correlation(time);
        qsort(sigmas,237,sizeof(double),cmp); qsort(ranges,237,sizeof(double),cmp);
        row_sigma[f]=sigmas[118]; row_range[f]=ranges[118];
        int lo=255,hi=0;
        for(int y=f?270:7;y<=(f?278:15);++y) for(int x=0;x<720;++x) {
            int v=u->bytes[48+(size_t)y*1440+2*x+1]; if(v<lo)lo=v; if(v>hi)hi=v;
        }
        blank_range[f]=hi-lo;
    }
    printf("%llu,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%s,%s,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f\n",
        (unsigned long long)u->counter_extended,
        r.measurements.luma_mean,r.measurements.luma_sigma,
        r.measurements.spatial_gradient_energy,r.measurements.temporal_mad,
        spatial[0],temporal[0],spatial[1],temporal[1],
        signal_appearance_name(r.appearance),signal_source_state_name(r.source),
        row_sigma[0],row_range[0],blank_range[0],row_sigma[1],row_range[1],blank_range[1]);
    memcpy(previous,u->bytes,sizeof previous); previous_valid=true;
}
static unsigned u32(const uint8_t *b) { return b[0]|b[1]<<8|b[2]<<16|(unsigned)b[3]<<24; }
int main(int argc,char **argv) {
    assert(argc==2||argc==3); if(argc==3)panel_dir=argv[2];
    state=aligned_alloc(signal_state_alignment(),signal_state_size());
    unit_parser *p=aligned_alloc(unit_parser_alignment(),unit_parser_size());
    assert(state&&p); signal_state_init(state,NULL);
    unit_parser_callbacks cb={.on_video=video}; unit_parser_init(p,NULL,&cb);
    FILE *in=fopen(argv[1],"rb"); assert(in); uint8_t h[24];
    puts("counter,mean,sigma,gradient,temporal_mad,f1_spatial,f1_temporal,f2_spatial,f2_temporal,appearance,source,f1_row_sigma,f1_row_range,f1_blank_range,f2_row_sigma,f2_row_range,f2_blank_range");
    for (;;) {
        size_t n=fread(h,1,24,in); if (!n) { assert(!ferror(in)); break; }
        assert(n==24 && u32(h)==0x31504143);
        unsigned actual=u32(h+20); uint8_t *bytes=malloc(actual?actual:1); assert(bytes);
        assert(fread(bytes,1,actual,in)==actual);
        assert(h[4]!=1 && h[4]!=2); /* HostLoss / TransferError */
        if (h[4]==0) {
            assert(u32(h+12)==0);
            cc_packet packet={.endpoint=h[5],.pkt_index=h[6]|h[7]<<8,
                .submit_seq=u32(h+8),.status=0,.req_len=u32(h+16),
                .actual_len=actual,.data=bytes};
            unit_parser_on_packet(p,&packet);
        }
        free(bytes);
    }
    unit_parser_finish(p); fclose(in); free(p); free(state);
}
