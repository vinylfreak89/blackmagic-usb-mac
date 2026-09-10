/* Rule 3: relocated blanking is independent of the union phase envelope.
 * Reuse synthetic sample writing, not the existing detector's verdicts. */
#define main old_switch_test_main
#include "switch_timing_test.c"
#undef main

static void scene(int kind)
{
    for(int r=0;r<525;++r)for(int x=0;x<720;++x)sample(r,x,kind==6?1+x%2:2);
    for(int f=0;f<2;++f)for(int y=0;y<240;++y)for(int x=0;x<720;++x) {
        int top=f?282:19;
        unsigned v=70+(x*13+y*7)%90;
        /* Stationary blank-level rectangle, identical to porch, contaminates
         * the old envelope at exactly the later relocated interval. */
        if(x<4 || x>=715 || (x>=(kind==7?300:80) && x<(kind==7?447:227)))v=2;
        bool full=(kind==1 && y>=238) || (kind==2 && y>=100 && y<110) ||
                  ((kind==3 || kind==5 || kind==6 || kind==7) && y>=238);
        if(full) v=x>=80 && x<(kind==3?226:227)?2:28+(x%2);
        if(kind==1 && y==237 && x>=360)v=28+(x%2);
        if(kind==7 && y==237 && x>=450)v=28+(x%2);
        /* Shortened porches with a surviving leading remnant must not turn
         * the unchanged black rectangle into a FULL other-head row. */
        if(kind==4 && y>=238) {
            v=28+(x%2);
            if(x==0 || (x>=80 && x<227))v=2;
        }
        if(kind==6 && !full && (x<4 || x>=715))v=1+x%2;
        if(kind==6 && x>=80 && x<227)v=1;
        sample(top+y,x,v);
    }
}
int main(void)
{
    for(int kind=0;kind<8;++kind) {
        scene(kind);
        for(int f=0;f<2;++f) {
            field_measurement m;measure_field(raster,f,&m);
            int top=f?282:19;
            if(kind==0)check("stationary black rectangle is not timing",m.switch_line,-1);
            if(kind==1) {
                check("relocated run survives envelope overlap",m.first_full_other_head_line,top+238);
                check("retained prefix identifies partial row",m.switch_line,top+237);
                check("phase abstention stays explicit",m.switch_observations.phase_t,-1);
                check("run observation stays explicit",m.switch_observations.run_t,top+237);
            }
            if(kind==2)check("departure and return is not terminal band",m.switch_line,-1);
            if(kind==3)check("sub-147 run alone is insufficient",m.switch_line,-1);
            if(kind==4)check("surviving leading porch is not full departure",m.switch_line,-1);
            if(kind==5) {
                check("exposed S without partial",m.switch_line,top+238);
                check("full run length retained",m.switch_observations.run_length,147);
                check("full run position retained",m.switch_observations.run_start,80);
            }
            if(kind==6)check("wrong blank distribution cannot confirm run",m.switch_line,-1);
            if(kind==7) {
                check("disagreement is explicit",m.switch_observations.disagreement,1);
                check("conflicting phase T retained",m.switch_observations.phase_t,top+238);
                check("conflicting run T retained",m.switch_observations.run_t,top+237);
                check("conflict does not select an authority",m.switch_line,-1);
                check("common S survives T disagreement",m.first_full_other_head_line,top+238);
            }
        }
    }
    printf("RUN-TIMING: %u/%u passed\n",checks-failures,checks);
    return failures?1:0;
}
