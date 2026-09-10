/* Direct energy checks, independent woven-frame arithmetic and a known limit. */
#include "../field_registration.c"
#include <stdio.h>

static uint8_t raster[525*1440], woven[480][720];
static unsigned checks, failures;
static void check(const char *name, bool ok)
{
    ++checks;
    if (!ok) { ++failures; fprintf(stderr, "FAIL: %s\n", name); }
}
static int knot(unsigned y, unsigned x)
{
    unsigned k=y*2654435761u+x*2246822519u;
    k ^= k>>16;
    return 30+(int)(k%150);
}
static int scene(int y, int x)
{
    int a=knot((unsigned)y/2,(unsigned)x);
    return y%2 ? (a+knot((unsigned)y/2+1,(unsigned)x))/2 : a;
}
static void fixture(int relative, bool pan)
{
    memset(raster,0,sizeof raster);
    for(int f=0;f<2;++f)for(int y=0;y<240;++y)for(int x=0;x<720;++x){
        int phase=2*y+40+f+(f?2*relative:0)-(pan?4*f:0);
        raster[((f?282:19)+y)*1440+2*x+1]=(uint8_t)scene(phase,x);
    }
}
static double reference(int shift)
{
    int first=shift<0?-shift:0, last=shift>0?240-shift:240, n=0;
    for(int y=first;y<last;++y)for(int f=0;f<2;++f){
        int row=(f?282:19)+y+(f?shift:0);
        for(int x=0;x<720;++x)woven[n][x]=raster[row*1440+2*x+1];
        ++n;
    }
    uint64_t sum=0;
    for(int y=1;y<n-1;++y)for(int x=0;x<720;++x)
        sum+=(unsigned)abs(woven[y-1][x]-2*woven[y][x]+woven[y+1][x]);
    return (double)sum/((n-2)*720);
}
int main(void)
{
    const int start[2]={19,282}, end[2]={258,521};
    for(int d=-4;d<=4;++d){
        fixture(d,false);
        comb_reading r=comb_search(raster,start,start,end,0);
        check("aperiodic_relative_alignment",r.measured && r.shift==-d);
        check("energy_is_mean_absolute_woven_second_difference",
              r.best==reference(r.shift));
    }
    fixture(0,true);
    comb_reading r=comb_search(raster,start,start,end,0);
    printf("KNOWN OPEN PAN: true geometry=0, plain minimum=%d, energy=%.9f, next=%.9f\n",
           r.shift,r.best,r.second);
    check("known_pan_false_minimum_is_exposed",r.measured && r.shift==2);
    check("pan_energy_matches_direct_weave",r.best==reference(r.shift));

    memset(raster,80,sizeof raster);
    r=comb_search(raster,start,start,end,0);
    check("exact_ties_abstain",!r.measured && r.unresolved>0 && r.best==0);
    const int none[2]={18,281};
    r=comb_search(raster,start,start,none,0);
    check("no_picture_aperture_is_not_zero_evidence",!r.measured && r.fraction==0);

    /* Switch-free qualified-caption acquisition is the other OR route. */
    fieldreg_field_state state={0};
    field_measurement m={.geometry_measurable=true,.top=20,
        .recorded_first=20,.recorded_last=258,.off_count=1};
    m.off_candidate.raster_row=18;
    fieldreg_field_decision out;
    v10_reset_field(&state,true,0);
    v10_decide_field(&state,&m,0,&out);
    check("caption_lock_does_not_require_switch",state.lock_state==FIELDREG_LOCK_LOCKED &&
          !state.switch_line_count_known && state.switch_line_count==-1);
    printf("PLAIN-ENERGY: %u/%u passed\n",checks-failures,checks);
    return failures?1:0;
}
