/* Rule 8: report switch observations; a box verdict supplies no placement. */
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
        check("box verdict is explicitly observed",m.box_detected);
        check("boxed geometry stays unknown",!m.geometry_measurable);
        check("no timing witness stays unknown",!m.switch_measurable);
    }
    fixture(false,false,1);
    for(int f=0;f<2;++f) {
        const int top=f?282:19;
        for(int y=0;y<240;++y)for(int x=0;x<720;++x) {
            unsigned v=raster[(top+y)*1440+2*x+1];
            if(x<4 || x>=715)v=2;
            if(y==237 && x>=360)v=28+(x%2);
            if(y>=238)v=x>=80 && x<227?2:28+(x%2);
            raster[(top+y)*1440+2*x+1]=(uint8_t)v;
        }
        field_measurement m;measure_field(raster,f,&m);
        check("box with timing is observed",m.box_detected);
        check("box does not suppress partial switch",m.switch_measurable && m.switch_line==top+237);
        check("box reports first full other-head row",m.first_full_other_head_line==top+238);
        check("box reports current bottom and extent",m.bottom==top+236 && m.band_extent==3);
        check("switch observation does not seed boxed geometry",!m.geometry_measurable &&
            m.observed_switch_line_count<0 && m.picture_rows<0);
    }
    static uint8_t observed_unit[FIELDREG_UNIT_BYTES];
    memcpy(observed_unit,"\0\0\xff\xff",4);observed_unit[6]=1;observed_unit[7]=0xe8;
    memcpy(observed_unit+FIELDREG_HEADER_BYTES,raster,sizeof raster);
    static field_registration fresh;fieldreg_init(&fresh,NULL);
    fieldreg_decision observation;
    check("public box observation accepted",fieldreg_process(&fresh,observed_unit,&observation));
    check("public box reports both switches",observation.field[0].switch_measurable &&
        observation.field[1].switch_measurable);
    check("observations alone establish no lock or crop",!observation.geometry_lock_known &&
        observation.applied_d1==0 && observation.applied_d2==0 &&
        observation.decision_d1==FIELDREG_UNKNOWN && observation.decision_d2==FIELDREG_UNKNOWN);
    fixture(true,false,1);
    field_measurement m;measure_field(raster,0,&m);
    check("weak textured edges are not boxed",!m.box_detected && m.geometry_measurable);
    fixture(false,true,1);measure_field(raster,0,&m);
    check("one end alone is not boxed",!m.box_detected && m.geometry_measurable);
    fixture(false,false,1);
    static uint8_t unit[FIELDREG_UNIT_BYTES];
    memcpy(unit,"\0\0\xff\xff",4);unit[6]=1;unit[7]=0xe8;
    memcpy(unit+FIELDREG_HEADER_BYTES,raster,sizeof raster);
    static field_registration e;fieldreg_init(&e,NULL);
    for(int f=0;f<2;++f){e.field[f].lock_state=FIELDREG_LOCK_LOCKED;
        e.field[f].switch_line_count_known=true;e.field[f].switch_line_count=3;
        e.field[f].last_applied=2;}
    e.parity_state=FIELDREG_PARITY_CALIBRATED;
    fieldreg_decision d;check("public path accepts unit",fieldreg_process(&e,unit,&d));
    check("box invalidates old non-boxed lock",!d.geometry_lock_known &&
        !d.field[0].lock_switch_line_count_known && !d.field[1].lock_switch_line_count_known);
    check("box holds last decision, not standard substitution",d.applied_d1==2 && d.applied_d2==2);
    check("box publishes unknown observation",d.field[0].box_detected && d.field[1].box_detected &&
        d.decision_d1==FIELDREG_UNKNOWN && d.decision_d2==FIELDREG_UNKNOWN);
    if(argc==2){
        FILE *in=fopen(argv[1],"rb");if(!in)return 2;
        uint8_t y[525*720];
        if(fread(y,1,sizeof y,in)!=sizeof y || fgetc(in)!=EOF)return 2;
        fclose(in);
        for(int r=0;r<525;++r)for(int x=0;x<720;++x)raster[r*1440+2*x+1]=y[r*720+x];
        for(int f=0;f<2;++f){measure_field(raster,f,&m);
            check("6668 positive box observation",m.box_detected);
            field_measurement direct=m;measure_switch(raster,f,&direct);
            check("6668 box reports directly measurable switch",m.switch_measurable &&
                m.switch_line==direct.switch_line &&
                m.first_full_other_head_line==direct.first_full_other_head_line);
            check("6668 box supplies no placement",!m.geometry_measurable);
        }
    }
    printf("BOX-SWITCH-OBSERVATION: %u/%u passed\n",checks-failures,checks);
    return failures?1:0;
}
