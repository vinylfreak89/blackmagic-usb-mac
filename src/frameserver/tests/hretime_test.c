/* E-62: unique waveform evidence, causal references and immutable donors. */
#include "../hretime.c"
#include <assert.h>
#include <stdio.h>
enum { UNIT_BYTES=48+525*1440 };
static uint8_t unit[UNIT_BYTES],other[UNIT_BYTES],out1[UNIT_BYTES],out2[UNIT_BYTES];
static hrt_workspace work;
static hrt_result result;
static unsigned rng=19;
static unsigned random_byte(void){rng=1664525*rng+1013904223;return rng>>24;}
static void fixture(void) {
    memset(&work,0,sizeof work);
    uint8_t y[720];for(int x=0;x<720;x++)y[x]=x>=10 && x<=710?40+random_byte()%180:2;
    for(int r=0;r<525;r++)for(int x=0;x<720;x++) {
        unit[48+r*1440+2*x]=128;
        unit[48+r*1440+2*x+1]=(r>=7 && r<=15)||(r>=270 && r<=278)?2:y[x];
    }
    memcpy(other,unit,sizeof unit);
}
static void displace(uint8_t *u,int k,int i,int s) {
    uint8_t *p=u+48+(first_row(k,0)+i)*1440,copy[1440];memcpy(copy,p,sizeof copy);
    for(int x=0;x<720;x++)p[2*x+1]=x-s>=0 && x-s<720?copy[2*(x-s)+1]:2;
}
static void run(unsigned c) {
    memcpy(out1,unit,sizeof unit);memcpy(out2,other,sizeof other);
    hrt_begin(&work,c,c,1,0);hrt_apply(&work,unit,other,0,0,out1,out2,&result);
}
static void oracle(void) {
    uint8_t a[720],b[720];
    for(int trial=0;trial<30;trial++) {
        for(int x=0;x<720;x++){a[x]=random_byte();b[x]=random_byte();}
        for(int lo=0;lo<720;lo+=120)for(int s=-64;s<=64;s++)if(lo+s>=0 && lo+s+120<=720) {
            unsigned expected=0;for(int x=0;x<120;x++)expected+=abs((int)a[lo+x]-b[lo+x+s]);
            assert(window_sad(a+lo,b+lo+s)==expected);
        }
    }
    memset(a,2,sizeof a);memset(b,2,sizeof b);assert(window_offset(a,b,0)==UNKNOWN_OFFSET);
    for(int x=0;x<720;x++)a[x]=b[x]=random_byte();
    assert(window_offset(a,b,240)==0);
    for(int x=0;x<720;x++)a[x]=x>=12?b[x-12]:2;
    assert(window_offset(a,b,240)==12);
    /* A periodic wall cannot supply even a known-zero offset. */
    for(int x=0;x<720;x++)a[x]=b[x]=(uint8_t)((x%16)*14);
    assert(window_offset(a,b,240)==UNKNOWN_OFFSET);
    for(int x=0;x<720;x++)b[x]=x>=10 && x<710?40+random_byte()%180:2;
    for(int x=0;x<720;x++)a[x]=x>=23?b[x-23]:2;
    assert(edge_window_offset(a,b,33,10,0)==23);
    assert(edge_window_offset(a,b,0,10,0)==UNKNOWN_OFFSET);
}
int main(void) {
    oracle();fixture();run(1);assert(result.band_count==0);
    for(int i=20;i<23;i++)displace(unit,0,i,6);
    run(2);assert(result.field[0].retimed==3 && !result.field[1].retimed);
    for(int i=20;i<23;i++) {
        assert(result.action[2*i]==HRT_RETIME);
        assert(!memcmp(out1+48+(19+i)*1440,other+48+(282+i)*1440,1440));
    }
    /* A sustained bend is compared against repaired, not yesterday's bent row. */
    run(3);assert(result.field[0].retimed==3);
    memcpy(unit,other,sizeof unit);run(4);assert(result.band_count==0);
    /* A recognised isolated miss must not poison the next temporal reference. */
    displace(unit,0,20,6);run(5);assert(!result.field[0].interpolated && !result.field[0].retimed);
    assert(!work.valid[0][39]);
    hrt_begin(&work,7,7,1,0);assert(!work.available[0][40]);
    hrt_begin(&work,6,6,2,0);assert(!work.available[0][40]);
    hrt_reset(&work);assert(!work.have);
    fixture();run(1);for(int i=0;i<6;i++)displace(other,1,i,-9);
    run(2);assert(result.field[1].retimed==6 && !result.field[0].retimed);
    fixture();run(1);for(int i=0;i<6;i++)displace(other,1,i,-12);
    run(2);assert(result.field[1].interpolated==6 && !result.field[0].interpolated);
    fixture();run(1);for(int i=20;i<23;i++){displace(unit,0,i,6);displace(other,1,i,6);}
    run(2);assert(!result.band_count); /* shared displacement */
    fixture();run(1);for(int i=232;i<238;i++)displace(unit,0,i,6);
    run(2);assert(!result.band_count); /* switch */
    fixture();for(int r=0;r<525;r++)for(int x=0;x<720;x++)unit[48+r*1440+2*x+1]=2;
    memcpy(other,unit,sizeof unit);run(1);assert(!result.band_count);
    uint8_t a[1440],b[1440];for(int x=0;x<360;x++){a[4*x]=x%256;a[4*x+2]=255-x%256;a[4*x+1]=a[4*x+3]=100;}
    memset(b,77,sizeof b);retime(a,b,1);
    assert(b[40]==average(a[40],a[44]) && b[42]==average(a[42],a[46]));
    assert(b[1439]==a[1439] && b[1436]==a[1436] && b[1438]==a[1438]);
    /* Width-only choice: no detection-window or opposite-donor requirement. */
    fixture();run(1);memset(work.flagged,0,sizeof work.flagged);
    for(int j=0;j<480;j++) {
        work.repair[j]=(repair_boundary){{10,710},{1,1},0};work.moved[j]=0;
    }
    int s=99;work.flagged[40]=1;work.flagged[39]=work.flagged[41]=1;
    work.repair[40]=(repair_boundary){{11,711},{1,1},0};
    assert(!donor(&work,39) && !donor(&work,41));
    assert(repair_choice(&work,40,0,0,&s) && s==1);
    work.repair[40]=(repair_boundary){{10,710},{1,1},0};
    assert(repair_choice(&work,40,0,0,&s) && s==0);
    work.repair[40]=(repair_boundary){{20,710},{1,1},0};
    assert(!repair_choice(&work,40,0,0,&s));
    work.repair[40]=(repair_boundary){{NAN,710},{NAN,1},1};
    assert(!repair_choice(&work,40,0,0,&s));
    fixture();hrt_apply(&work,unit,other,-30,30,out1,out2,&result);
    puts("HRETIME PASS: E62 detection, width-only repair, zero/no-donor, stretch/spill, temporal recovery, chroma and crop bounds");
    return 0;
}
