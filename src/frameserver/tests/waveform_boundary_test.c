#include "waveform_boundary.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
    uint8_t y[720];wb_level vi={1,1};
    static uint8_t unit[48+525*1440];memset(unit,1,sizeof unit);
    wb_level measured=wb_vi(unit,0);
    assert(measured.level==1 && measured.noise==1/sqrt(12.0));
    memset(y,1,sizeof y);assert(wb_measure(y,0,vi).status==0);
    memset(y,100,sizeof y);assert(wb_measure(y,0,vi).status==2);
    for(int x=0;x<720;x++)y[x]=x<8?1:x<16?(uint8_t)(1+12*(x-7)):97;
    wb_edge e=wb_measure(y,0,vi);assert(e.status==1 && fabs(e.position-11)<1e-9);
    uint8_t reversed[720];for(int x=0;x<720;x++)reversed[x]=y[719-x];
    wb_edge r=wb_measure(reversed,1,vi);assert(r.status==1 && r.position==719-e.position);
    /* A low precursor is not a censored picture plateau. */
    for(int x=0;x<720;x++)y[x]=x<16?5:x<24?(uint8_t)(5+12*(x-15)):101;
    e=wb_measure(y,0,vi);assert(e.status==1 && e.position>16);
    /* An internal edge with a nonblank exterior cannot qualify as blanking. */
    for(int x=0;x<720;x++)y[x]=x<60?40:100;
    e=wb_measure(y,0,vi);assert(e.status!=1);
    puts("waveform boundary synthetic checks passed");
}
