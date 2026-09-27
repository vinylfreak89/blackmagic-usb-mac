/* Synthetic detector/correction contracts, plus exact SIMD SAD oracle. */
#include "../hretime.c"
#include <assert.h>
#include <stdio.h>
enum { UNIT_BYTES=48+525*1440 };
static uint8_t unit[UNIT_BYTES],other[UNIT_BYTES],out1[UNIT_BYTES],out2[UNIT_BYTES];
static hrt_workspace work;
static hrt_result result;
static uint32_t rng=19;
static unsigned random_byte(void) {rng=1664525*rng+1013904223;return rng>>24;}
static void fixture(void) {
    uint8_t row[1440];
    for(int x=0;x<720;x++) {row[2*x]=128;row[2*x+1]=x>=10 && x<=710 ? 40+random_byte()%180 : 2;}
    memset(unit,0,sizeof unit);
    for(int r=0;r<525;r++) {
        uint8_t *p=unit+48+r*1440;
        memcpy(p,row,1440);
        if((r>=7 && r<=15)||(r>=270 && r<=278))for(int x=0;x<720;x++)p[2*x+1]=2;
    }
    memcpy(other,unit,sizeof unit);
}
static void displace(uint8_t *u,int k,int i,int s,int trim) {
    uint8_t *p=u+48+(first_row(k,0)+i)*1440;
    uint8_t copy[1440];memcpy(copy,p,sizeof copy);
    for(int x=0;x<720;x++)p[2*x+1]=x-s>=0 && x-s<720-trim ? copy[2*(x-s)+1] : 2;
}
static void run(void) {
    memcpy(out1,unit,sizeof unit);memcpy(out2,other,sizeof other);
    hrt_apply(&work,unit,other,0,0,out1,out2,&result);
}
static void oracle(void) {
    uint8_t a[720],b[720],c[720];
    for(int trial=0;trial<50;trial++) {
        for(int x=0;x<720;x++){a[x]=random_byte();b[x]=random_byte();c[x]=random_byte();}
        for(int s=-24;s<=24;s++) {
            unsigned sum=0;
            for(int x=60;x<660;x++)sum+=(unsigned)abs(2*(int)a[x+s]-b[x]-c[x]);
            assert(sum==sad2(a,b,c,s));
        }
    }
}
int main(void) {
    oracle();
    fixture();displace(unit,0,20,6,0);run();
    assert(result.field[0].retimed==1 && result.field[1].retimed==0);
    assert(result.action[40]==HRT_RETIME && result.shift[40]==6);
    assert(!memcmp(out1+48+39*1440,other+48+39*1440,1440));
    fixture();displace(unit,0,20,6,25);run();
    assert(result.action[40]==HRT_INTERPOLATE);
    assert(!memcmp(out1+48+39*1440,other+48+39*1440,1440));
    fixture();displace(unit,0,20,-16,0);run();
    assert(result.action[40]==HRT_INTERPOLATE); /* censored width: not silently shifted */
    fixture();displace(unit,0,20,18,0);run();assert(result.action[40]==HRT_INTERPOLATE);
    fixture();for(int i=0;i<6;i++)displace(other,1,i,-7,0);run();
    assert(result.field[0].bands==0 && result.field[1].bands==1);
    assert(result.field[1].retimed==6); /* mirrored f1 discontinuity has no self break */
    fixture();displace(unit,0,232,6,0);run();
    assert(result.field[0].retimed==0 && result.field[0].interpolated==0); /* line255 */
    fixture();for(int r=0;r<525;r++)for(int x=0;x<720;x++)unit[48+r*1440+2*x+1]=2;
    memcpy(other,unit,sizeof unit);run();assert(result.band_count==0);
    /* Odd luma shifts preserve phase; U and V interpolate independently. */
    uint8_t a[1440],b[1440];for(int x=0;x<360;x++){a[4*x]=x%256;a[4*x+2]=255-x%256;a[4*x+1]=a[4*x+3]=100;}
    retime(a,b,1,10,710,2);assert(b[40]==average(a[40],a[44]) && b[42]==average(a[42],a[46]));
    /* Invalid publisher rows use neutral padding, never cross field storage. */
    fixture();memcpy(out1,unit,sizeof unit);memcpy(out2,other,sizeof other);
    hrt_apply(&work,unit,other,-30,30,out1,out2,&result);
    puts("HRETIME PASS: scalar/SIMD, shift, compressed width, censored edges, field ownership, switch exclusion, no picture, chroma, crop bounds");
    return 0;
}
