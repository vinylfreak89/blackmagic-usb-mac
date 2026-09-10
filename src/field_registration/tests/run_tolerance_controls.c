/* Diagnostic only. Compile against a scratch header variant, never production.
 * Constructed samples exercise an excluded code INSIDE an otherwise complete
 * interval. Negative controls have the identical sample population. */
#define main old_switch_main
#include "switch_timing_test.c"
#undef main

static void tolerance_scene(int kind)
{
    for(int r=0;r<525;++r)for(int x=0;x<720;++x)sample(r,x,1+x%2);
    for(int f=0;f<2;++f)for(int y=0;y<240;++y)for(int x=0;x<720;++x) {
        int top=f?282:19;
        unsigned v=70+(x*13+y*7)%90;
        if(x<4 || x>=715) {
            v=1+x%2;
            if((y%3==0 && x==1) || (y%5==0 && x==718))v=4;
        }
        /* Stationary interior rectangle shares the later interval's codes. */
        if(x>=80 && x<227)v=x==153?4:1+x%2;
        bool full=(kind==1 && y>=238) || (kind==2 && y>=100 && y<110) ||
                  (kind==5 && y>=238);
        if(full) {
            v=28+x%2;
            if(x>=80 && x<227)v=kind==5?1:(x==153?4:1+x%2);
        }
        if(kind==1 && y==237 && x>=360)v=28+x%2;
        /* Newly appearing edge-connected black rectangle retains the actual
         * trailing porch. Its prefix includes an excluded interior code. */
        if(kind==3 && y>=238 && x<181)v=x==64?4:1+x%2;
        /* A clipped low interval is still outside this instrument's scope. */
        if(kind==4 && y>=238) {
            v=28+x%2;
            if(x<131)v=x==64?4:1+x%2;
        }
        sample(top+y,x,v);
    }
}

int main(void)
{
    for(int kind=0;kind<6;++kind) {
        tolerance_scene(kind);
        for(int f=0;f<2;++f) {
            field_measurement m;measure_field(raster,f,&m);
            int want=-1;
#ifdef EXPECT_TOLERANT_RECOVERY
            if(kind==1)want=(f?282:19)+237;
#endif
            const char *names[]={"scattered-code stationary interior rectangle",
                "scattered-code relocated interval and partial",
                "scattered-code departure and return",
                "scattered-code edge-connected black rectangle",
                "truncated interval remains unmeasurable",
                "wrong distribution remains rejected"};
            printf("CONTROL kind=%d field=%d run_T=%d phase_T=%d\n",kind,f+1,
                m.switch_observations.run_t,m.switch_observations.phase_t);
            check(names[kind],m.switch_observations.run_t,want);
        }
    }
    printf("TOLERANCE-CONTROLS: %u/%u passed\n",checks-failures,checks);
    return failures?1:0;
}
