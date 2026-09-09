/* Rule 8 exclusion, not a boxed placement or centring golden. */
#include "../field_registration.c"
#include <stdio.h>
static uint8_t raster[FIELDREG_RASTER_LINES*FIELDREG_BYTES_PER_LINE];
static unsigned checks,failures;
static void check(const char *name,bool ok){++checks;if(!ok){++failures;fprintf(stderr,"FAIL: %s\n",name);}}
static void fixture(bool weak_texture,bool one_end,unsigned gain)
{
    memset(raster,128,sizeof raster);
    for(int r=0;r<525;++r)for(int x=0;x<720;++x)raster[r*1440+2*x+1]=2;
    for(int f=0;f<2;++f)for(int y=0;y<240;++y)for(int x=0;x<720;++x){
        bool body=y>=30 && (y<210 || one_end);
        int v=64+(x%2?1:-1);
        if(weak_texture)v+=(body?4:1)*((x*13)%23-11);
        else if(body)v+=x<360?40:-40;
        raster[((f?282:19)+y)*1440+2*x+1]=(uint8_t)(v/gain);
    }
}
int main(int argc,char **argv)
{
    for(unsigned gain=1;gain<=2;++gain){
        fixture(false,false,gain);
        field_measurement m;measure_field(raster,0,&m);
        check("boxed geometry stays unknown",!m.geometry_measurable);
        check("box excludes switch",!m.switch_measurable);
    }
    fixture(true,false,1);
    field_measurement m;measure_field(raster,0,&m);
    check("weak textured edges are not boxed",m.geometry_measurable);
    fixture(false,true,1);measure_field(raster,0,&m);
    check("one end alone is not boxed",m.geometry_measurable);
    if(argc==2){
        FILE *in=fopen(argv[1],"rb");if(!in)return 2;
        uint8_t y[525*720];
        if(fread(y,1,sizeof y,in)!=sizeof y || fgetc(in)!=EOF)return 2;
        fclose(in);
        for(int r=0;r<525;++r)for(int x=0;x<720;++x)raster[r*1440+2*x+1]=y[r*720+x];
        for(int f=0;f<2;++f){measure_field(raster,f,&m);
            check("6668 box excludes switch",!m.switch_measurable);
            check("6668 box supplies no placement",!m.geometry_measurable);
        }
    }
    printf("BOX-EXCLUSION: %u/%u passed\n",checks-failures,checks);
    return failures?1:0;
}
