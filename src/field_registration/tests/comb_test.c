/* Public-path comb golden; all picture samples are constructed here. */
#include "../field_registration.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static field_registration engine;
static uint8_t unit[FIELDREG_UNIT_BYTES];
static unsigned checks, failures;
static void check(const char *name, bool ok)
{
    ++checks;
    if(!ok){++failures;fprintf(stderr,"FAIL: %s\n",name);}
}
static int picture(int y,int x)
{
    return 40+2*((y*17+x*13)%60);
}
static void make_unit(int d,int wrong,bool flat)
{
    memset(unit,0,sizeof unit);memcpy(unit,"\0\0\xff\xff",4);
    unit[6]=1;unit[7]=0xe8;
    for(int r=0;r<525;++r)for(int x=0;x<720;++x){
        unit[48+r*1440+2*x]=128;unit[48+r*1440+2*x+1]=2;
    }
    for(int f=0;f<2;++f){
        int top=(f?282:19)+d, end=f?521:258, t=top+237;
        for(int r=top;r<=end;++r)for(int x=0;x<720;++x){
            int y=r-top+10, v=flat?80:picture(y,x);
            if(f && !flat)v=(picture(y+wrong,x)+picture(y+wrong+1,x))/2;
            if(x<4 || x>=715)v=2;
            if(r==t && x>=360)v=(x>=560 && x<610)?2:30;
            if(r>t)v=(x>=80 && x<227)?2:30;
            unit[48+r*1440+2*x]=(uint8_t)(127+(x%2));
            unit[48+r*1440+2*x+1]=(uint8_t)v;
        }
    }
}
static fieldreg_decision run(void)
{
    fieldreg_decision d;
    if(!fieldreg_process(&engine,unit,&d)){fprintf(stderr,"process failed\n");exit(2);}
    return d;
}
int main(void)
{
    fieldreg_init(&engine,NULL);make_unit(0,0,false);
    fieldreg_decision d=run();
    check("first unit has no temporal witness",d.comb_check==FIELDREG_COMB_NOT_APPLICABLE);
    d=run();
    check("static weave is actually measured",d.comb_check==FIELDREG_COMB_AGREE);
    check("registered shift zero",d.comb_best_shift==0);
    check("positive static area",d.comb_static_fraction>0);
    check("strict energy minimum",d.comb_best_energy<d.comb_second_energy);
    check("precedence calibrated",d.parity_state==FIELDREG_PARITY_CALIBRATED);
    check("comb confirms measurable geometry lock",d.geometry_lock_known);
    const int bias=d.parity_bias;
    make_unit(0,-1,false);(void)run();d=run();
    check("wrong weave contradicts",d.comb_check==FIELDREG_COMB_DISAGREE);
    check("wrong weave shift +1",d.comb_best_shift==1);
    check("contradiction never corrects crop",d.applied_d1==0 && d.applied_d2==0 && d.comb_correction==0);
    check("settled precedence does not chase error",d.parity_bias==bias && d.parity_state==FIELDREG_PARITY_DRIFT);
    make_unit(0,0,false);(void)run();d=run();
    check("registered return clears diagnostic drift",d.comb_check==FIELDREG_COMB_AGREE && d.parity_bias==bias);
    make_unit(1,0,false);d=run();
    check("previous crop is its own crop",d.applied_d1==1 && d.applied_d2==1 && d.comb_check==FIELDREG_COMB_AGREE);
    fieldreg_discontinuity(&engine);d=run();
    check("discontinuity discards static witness",d.comb_check==FIELDREG_COMB_NOT_APPLICABLE);
    check("ordinary damage retains precedence",d.parity_state==FIELDREG_PARITY_CALIBRATED);
    fieldreg_begin_segment(&engine);d=run();
    check("source reset discards precedence",d.parity_state==FIELDREG_PARITY_UNCALIBRATED);
    make_unit(0,0,true);fieldreg_begin_segment(&engine);(void)run();d=run();
    check("flat picture does not confirm",d.comb_check==FIELDREG_COMB_FLAT && !d.comb_safe);
    printf("COMB: %u/%u passed\n",checks-failures,checks);
    return failures?1:0;
}
