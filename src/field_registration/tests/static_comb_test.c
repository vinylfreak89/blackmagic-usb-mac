/* Constructed static-detail and motion controls, using the production reader. */
#include "../field_registration.c"
#include <stdio.h>

static field_registration engine;
static unsigned checks, failures;
static void check(const char *name, bool ok)
{
    ++checks;
    if (!ok) { ++failures; fprintf(stderr, "FAIL: %s\n", name); }
}
static int scene(int y, int x)
{
    unsigned k=(unsigned)(y/2), a=k*2654435761u+(unsigned)x*2246822519u;
    unsigned b=(k+1)*2654435761u+(unsigned)x*2246822519u;
    a^=a>>16; b^=b>>16;
    int v=30+(int)(a%150), w=30+(int)(b%150);
    return y%2 ? (v+w)*4 : v*8; /* eight-pixel SUM, halfway between knots */
}
static void fixture(int relative, bool pan, bool noise)
{
    memset(&engine,0,sizeof engine);
    for(int f=0;f<2;++f){
        int s=f?282:19;
        engine.previous_crop[f]=engine.previous_begin[f]=(int16_t)s;
        engine.previous_end[f]=(int16_t)(s+239);
        for(int y=0;y<240;++y)for(int x=0;x<90;++x){
            int p=2*y+40+f+(f?relative*2:0);
            int c=pan?p-4*f:p, old=pan?c+8:p;
            int n=noise?((y*13+x*7+f)%9-4)*8:0;
            engine.current_luma[(s+y)*90+x]=(uint16_t)(scene(c,x)+n);
            engine.previous_luma[(s+y)*90+x]=(uint16_t)scene(old,x);
        }
    }
    engine.previous_luma_valid=true;
}
static comb_reading read_comb(void)
{
    const int s[2]={19,282}, end[2]={258,521};
    return comb_search(&engine,s,s,end,-1);
}
int main(int argc,char **argv)
{
    if(argc==2){
        /* Named controls packed from the previously provenance-checked
         * diagnostic caches. Scalar results only; no content in the repo. */
        FILE *in=fopen(argv[1],"rb");if(!in)return 2;
        static uint8_t raster[525*720];
        const int counters[]={6687,6690,6700,13653,13972,739,333};
        const int wanted[]={0,0,0,-1,0,0,1};
        for(unsigned k=0;k<sizeof counters/sizeof counters[0];++k){
            fixture(0,false,false);
            for(int t=0;t<2;++t){
                if(fread(raster,1,sizeof raster,in)!=sizeof raster)return 2;
                uint16_t *target=t?engine.current_luma:engine.previous_luma;
                for(int r=0;r<525;++r)for(int x=0;x<90;++x){
                    unsigned sum=0;for(int i=0;i<8;++i)sum+=raster[r*720+x*8+i];
                    target[r*90+x]=(uint16_t)sum;
                }
            }
            comb_reading r=read_comb();
            printf("raw counter=%d measured=%d shift=%d support=%.6f energy=%.6f next=%.6f\n",
                   counters[k],r.measured,r.shift,r.fraction,r.best,r.second);
            check("raw_static_golden",r.measured && r.shift==wanted[k]);
        }
        if(fgetc(in)!=EOF || fclose(in))return 2;
        printf("RAW-STATIC-COMB: %u/%u passed\n",checks-failures,checks);
        return failures?1:0;
    }
    if(argc!=1)return 2;
    for(int d=-1;d<=1;++d){
        fixture(d,false,true);comb_reading r=read_comb();
        check("real_picture_fluctuation_does_not_discard_static_detail",
              r.measured && r.shift==-d && r.fraction>0);
    }
    fixture(0,true,false);comb_reading r=read_comb();
    check("coherent_pan_cannot_confirm",!r.measured && r.fraction==0);
    /* Give two blocks the accidental same-time match that defeated the old
     * recalibrated pixel mask. The rest of each strip is still a moving pan. */
    for(int f=0;f<2;++f)for(int y=90;y<100;++y)for(int x=20;x<22;++x){
        int i=((f?282:19)+y)*90+x;
        engine.previous_luma[i]=engine.current_luma[i];
    }
    r=read_comb();
    check("two_accidental_blocks_cannot_license_a_pan",!r.measured && r.fraction==0);
    /* A linear ramp has no distinctive phase; its cyclic seam must not
     * become invented static detail. */
    for(int f=0;f<2;++f)for(int y=0;y<240;++y)for(int x=0;x<90;++x){
        int i=((f?282:19)+y)*90+x;
        engine.current_luma[i]=(uint16_t)(400+2*y-4*f);
        engine.previous_luma[i]=(uint16_t)(engine.current_luma[i]+8);
    }
    r=read_comb();check("linear_pan_has_no_static_detail",!r.measured && r.fraction==0);
    printf("STATIC-COMB: %u/%u passed\n",checks-failures,checks);
    return failures?1:0;
}
