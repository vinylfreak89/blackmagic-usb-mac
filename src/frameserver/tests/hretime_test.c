/* Other-field blanking reference: detection, range, retime/interpolate. */
#include "../hretime.c"
#include <assert.h>
#include <stdio.h>
enum { UNIT_BYTES=48+525*1440 };
static uint8_t unit[UNIT_BYTES],other[UNIT_BYTES],out1[UNIT_BYTES],out2[UNIT_BYTES];
static hrt_workspace work;
static hrt_result result;
static unsigned rng=19;
static unsigned random_byte(void){rng=1664525*rng+1013904223;return rng>>24;}
static uint8_t profile[720];
static void fixture(void) {
    memset(&work,0,sizeof work);
    /* Band-limited edges as on tape: a plateau just inside each falloff. */
    for(int x=0;x<720;x++)profile[x]=x<10 || x>710?2:x<26 || x>694?150:60+random_byte()%160;
    for(int r=0;r<525;r++)for(int x=0;x<720;x++) {
        unit[48+r*1440+2*x]=128;
        unit[48+r*1440+2*x+1]=(r>=7 && r<=15)||(r>=270 && r<=278)?2:profile[x];
    }
    memcpy(other,unit,sizeof unit);
}
static uint8_t *row(uint8_t *u,int k,int i) { return u+48+(first_row(k,0)+i)*1440; }
static void noisy(void) {
    uint8_t *u[2]={unit,other};
    for(int k=0;k<2;k++)for(int i=0;i<240;i++){uint8_t *p=row(u[k],k,i);
        for(int x=26;x<695;x++)p[2*x+1]=(uint8_t)(p[2*x+1]+random_byte()%5);}
}
static void displace(uint8_t *u,int k,int i,int s) {
    uint8_t *p=row(u,k,i),copy[1440];memcpy(copy,p,sizeof copy);
    for(int x=0;x<720;x++)p[2*x+1]=x-s>=0 && x-s<720?copy[2*(x-s)+1]:2;
}
static void run(unsigned c) {
    memcpy(out1,unit,sizeof unit);memcpy(out2,other,sizeof other);
    hrt_begin(&work,c,c,1,0);hrt_apply(&work,unit,other,0,0,out1,out2,&result);
}
static int changed(const uint8_t *out,const uint8_t *in) {
    int n=0;for(int r=0;r<525;r++)n+=!!memcmp(out+48+r*1440,in+48+r*1440,1440);return n;
}
static void oracle(void) {
    uint8_t a[720],b[720];
    for(int trial=0;trial<30;trial++) {
        for(int x=0;x<720;x++){a[x]=random_byte();b[x]=random_byte();}
        for(int shift=-2;shift<=2;shift++) {
            double sa=0,sb=0,aa=0,bb=0,ab=0;
            for(int x=0;x<720;x++) {
                int p=x+shift;if(p<0)p=0;if(p>719)p=719;
                double u=a[p],v=b[x];sa+=u;sb+=v;aa+=u*u;bb+=v*v;ab+=u*v;
            }
            double expected=(ab-sa*sb/720)/sqrt((aa-sa*sa/720)*(bb-sb*sb/720));
            assert(line_correlation(a,b,shift)==expected);
        }
        for(int shift=-40;shift<=40;shift+=20) {
            /* Overlap only: a[x+s] exists and is not the window's last sample. */
            double n=0,sa=0,sb=0,aa=0,bb=0,ab=0;
            for(int x=0;x<720;x++) {
                int p=x+shift;if(p<0 || p>718)continue;
                double u=a[p],v=b[x];n++;sa+=u;sb+=v;aa+=u*u;bb+=v*v;ab+=u*v;
            }
            double expected=(ab-sa*sb/n)/sqrt((aa-sa*sa/n)*(bb-sb*sb/n));
            assert(fabs(overlap_correlation(a,b,shift)-expected)<1e-12);
        }
    }
    memset(a,2,sizeof a);assert(isnan(line_correlation(a,a,0)));
}
static void measurement(void) {
    uint8_t y[720];memset(y,1,sizeof y);
    for(int x=10;x<=714;x++)y[x]=161;
    y[9]=81;y[715]=81;y[719]=40; /* 719: the window's attenuated sample */
    assert(crossing(y,0,81,147)==9 && crossing(y,1,81,147)==715);
    y[718]=161;y[716]=y[717]=161;
    assert(crossing(y,1,81,147)==720); /* picture at 718: spill */
    y[0]=161;assert(crossing(y,0,81,147)==-1);
    memset(y,1,sizeof y);assert(isnan(crossing(y,0,81,147)) && isnan(crossing(y,1,81,147)));
    for(int x=0;x<20;x++)y[20+x]=(uint8_t)(10*x);
    assert(inside_level(y,0,20)==85 && inside_level(y,1,50)==1);
}
int main(void) {
    oracle();measurement();
    fixture();run(1);assert(!result.band_count && !changed(out1,unit) && !changed(out2,other));
    assert(result.edge_median[0][0]>9 && result.edge_median[0][0]<10 && result.edge_median[1][1]>710 && result.edge_median[1][1]<711);
    /* A bend to the right in field 1: retimed exactly onto the other field;
     * the columns it vacates come from the other field. */
    for(int i=20;i<23;i++)displace(unit,0,i,6);
    run(2);assert(result.band_count==1 && result.field[0].retimed==3 && !result.field[1].retimed);
    for(int i=20;i<23;i++) {
        assert(result.action[2*i]==HRT_RETIME && result.shift[2*i]==6);
        assert(result.edge_moved[2*i]==(HRT_EDGES_KNOWN|HRT_LEFT_LATER));
        assert(!memcmp(row(out1,0,i),row(other,1,i),1440));
    }
    assert(changed(out1,unit)==3 && !changed(out2,other));
    /* No history: the same input gives the same decisions. */
    run(3);assert(result.field[0].retimed==3);
    /* Both fields moved together: the other field agrees, nothing is wrong. */
    fixture();for(int i=20;i<23;i++){displace(unit,0,i,6);displace(other,1,i,6);}
    run(1);assert(!result.band_count);
    /* Moved left past the window: left spill, the right falloff moved inward
     * gives the shift; the vacated left columns come from the other field. */
    fixture();for(int i=40;i<44;i++)displace(other,1,i,-14);
    run(1);assert(result.band_count==1 && result.field[1].retimed==4 && !result.field[0].retimed);
    for(int i=40;i<44;i++) {
        assert(result.action[2*i+1]==HRT_RETIME && result.shift[2*i+1]==-14);
        assert(result.reason[2*i+1]&HRT_MISSING_EDGE);
        assert(!memcmp(row(out2,1,i),row(unit,0,i),1440));
    }
    /* Picture across the whole window: no blanking either side, interpolate. */
    fixture();for(int i=60;i<62;i++)for(int x=0;x<720;x++)row(unit,0,i)[2*x+1]=150;
    run(1);assert(result.action[120]==HRT_INTERPOLATE && (result.reason[120]&HRT_MISSING_EDGE));
    assert(result.field[0].first==83 && result.field[0].last==84);
    /* No left blanking where the other field has it is garbage even with the
     * right at the standard: detected, and its broken width interpolates. */
    fixture();for(int i=64;i<66;i++)for(int x=0;x<12;x++)row(unit,0,i)[2*x+1]=150;
    run(1);assert(result.action[128]==HRT_INTERPOLATE && (result.reason[128]&HRT_WIDTH_BREAK));
    assert(result.reason[128]&HRT_MISSING_EDGE);
    /* A lone displaced line is a dropout or a little one-line shift. */
    fixture();displace(unit,0,80,12);run(1);assert(!result.band_count && !changed(out1,unit));
    /* Dark picture ramping slowly up from blanking is content, not a
     * falloff, even where the other field has picture. */
    fixture();for(int i=80;i<83;i++){uint8_t *p=row(unit,0,i);for(int x=10;x<40;x++)p[2*x+1]=(uint8_t)(2+(x-10)*2);}
    run(1);assert(!result.band_count);
    /* One side moved, the other did not: not a timing error on its own... */
    fixture();{uint8_t *p=row(unit,0,70);for(int x=0;x<20;x++)p[2*x+1]=2;}
    run(1);assert(!result.band_count && !changed(out1,unit));
    /* ...but inside a detected range its broken width is interpolated. */
    displace(unit,0,67,8);displace(unit,0,68,8);displace(unit,0,72,8);displace(unit,0,73,8);
    run(2);assert(result.action[136]==HRT_RETIME && result.action[144]==HRT_RETIME);
    assert(result.action[140]==HRT_INTERPOLATE && (result.reason[140]&HRT_WIDTH_BREAK));
    /* Range: detections at f1 30 and 34; the straight line 32 between them is
     * in the range, needs no shift, and is left alone. */
    fixture();displace(unit,0,29,8);displace(unit,0,30,8);displace(unit,0,34,8);displace(unit,0,35,8);
    run(1);assert(result.action[60]==HRT_RETIME && result.action[68]==HRT_RETIME);
    assert(result.action[62]==HRT_CONTENT && result.action[64]==HRT_CONTENT);
    assert((result.reason[62]&HRT_BAND_FILL) && !(result.reason[62]&HRT_BLANKING_SIZE));
    assert(!memcmp(row(out1,0,32),row(unit,0,32),1440) && changed(out1,unit)==4);
    /* Near blanking at the edge in both fields, even with the dark region's
     * boundary moving between fields: no evidence, nothing touched. */
    fixture();
    for(int i=100;i<110;i++) {
        uint8_t *a=row(unit,0,i),*b=row(other,1,i);
        for(int x=10;x<40;x++)a[2*x+1]=20;
        for(int x=10;x<52;x++)b[2*x+1]=20;
    }
    run(1);assert(!result.band_count);
    /* Horizontal motion inside the picture with stable blanking: nothing. */
    fixture();
    for(int i=0;i<240;i++) {
        uint8_t *b=row(other,1,i),copy[1440];memcpy(copy,b,sizeof copy);
        for(int x=30;x<690;x++)b[2*x+1]=copy[2*(x-9)+1];
    }
    run(1);assert(!result.band_count && !changed(out1,unit) && !changed(out2,other));
    /* The shifted waveform must agree with the other field: a bent line whose
     * picture is unrelated to its neighbours is interpolated instead. */
    fixture();for(int i=90;i<92;i++){uint8_t *p=row(unit,0,i);for(int x=0;x<720;x++)p[2*x+1]=x<16 || x>716?2:x<32 || x>700?150:60+random_byte()%160;}
    run(1);assert(result.action[180]==HRT_INTERPOLATE && (result.reason[180]&HRT_CORRELATION));
    /* Dark at the standard while the other field has picture: measured where
     * this line's picture actually starts. */
    fixture();displace(unit,0,50,20);displace(unit,0,51,20);
    run(1);assert(result.action[100]==HRT_RETIME && result.shift[100]==20);
    /* Head-switch rows are never touched. */
    fixture();for(int i=232;i<238;i++)displace(unit,0,i,6);
    run(1);assert(!result.band_count);
    /* Nothing but blanking: no standard, no evidence. */
    fixture();for(int r=0;r<525;r++)for(int x=0;x<720;x++)unit[48+r*1440+2*x+1]=2;
    memcpy(other,unit,sizeof unit);run(1);assert(!result.band_count);
    fixture();hrt_apply(&work,unit,other,-30,30,out1,out2,&result);
    /* Realistic lines differ: with per-line noise the bar is below 1, a true
     * retime passes and an unrelated line still interpolates. */
    fixture();noisy();for(int i=110;i<113;i++)displace(unit,0,i,7);
    for(int i=150;i<152;i++){uint8_t *p=row(unit,0,i);for(int x=0;x<720;x++)p[2*x+1]=x<17 || x>717?2:x<33 || x>701?150:60+random_byte()%160;}
    run(1);assert(result.r_neighbours[220]<1 && result.r_neighbours[220]>.99);
    for(int i=110;i<113;i++)assert(result.action[2*i]==HRT_RETIME && result.shift[2*i]==7);
    assert(result.action[300]==HRT_INTERPOLATE && (result.reason[300]&HRT_CORRELATION));
    /* Between two bands, the other field panning under dark edges is left
     * alone: no falloff here or there is no timing evidence. */
    fixture();
    for(int i=20;i<200;i++) {
        uint8_t *a=row(unit,0,i),*b=row(other,1,i),copy[1440];
        for(int x=0;x<160;x++)a[2*x+1]=b[2*x+1]=x<10?2:18;
        memcpy(copy,b,sizeof copy);for(int x=170;x<690;x++)b[2*x+1]=copy[2*(x-9)+1];
    }
    for(int i=10;i<13;i++)displace(unit,0,i,6);
    for(int i=210;i<213;i++)displace(unit,0,i,6);
    run(1);assert(result.field[0].first==33 && result.field[0].last==235);
    for(int i=20;i<200;i++)assert(result.action[2*i]==HRT_CONTENT && !memcmp(row(out1,0,i),row(unit,0,i),1440));
    /* Both sides measured, only one beyond a few samples: not timing. */
    fixture();
    for(int i=120;i<123;i++){uint8_t *p=row(unit,0,i),copy[1440];memcpy(copy,p,sizeof copy);
        for(int x=0;x<720;x++)p[2*x+1]=x<16?2:copy[2*x+1];for(int x=711;x<713;x++)p[2*x+1]=150;}
    run(1);assert(!result.band_count && !changed(out1,unit));
    /* The top line has one neighbour: the next other-field line supplies the
     * second reference and the bar, so unrelated content interpolates. */
    fixture();for(int i=0;i<3;i++){uint8_t *p=row(unit,0,i);for(int x=0;x<720;x++)p[2*x+1]=x<17 || x>717?2:x<33 || x>701?150:60+random_byte()%160;}
    run(1);for(int i=0;i<3;i++)assert(result.action[2*i]==HRT_INTERPOLATE);
    fixture();noisy();for(int i=0;i<3;i++)displace(unit,0,i,7);
    run(1);for(int i=0;i<3;i++)assert(result.action[2*i]==HRT_RETIME && result.shift[2*i]==7);
    /* No left blanking, right too dark to measure: the leftward waveform
     * search finds the shift and the agreement bar accepts it. */
    fixture();noisy();
    for(int i=0;i<240;i++){uint8_t *a=row(unit,0,i),*b=row(other,1,i);for(int x=660;x<720;x++)a[2*x+1]=b[2*x+1]=x>710?2:18;}
    for(int i=130;i<133;i++)displace(unit,0,i,-15);
    run(1);for(int i=130;i<133;i++)assert(result.action[2*i]==HRT_RETIME && result.shift[2*i]==-15 && (result.reason[2*i]&HRT_MISSING_EDGE));
    /* One side dark in both fields: the shifted waveform must confirm it. */
    fixture();
    for(int i=170;i<174;i++){uint8_t *a=row(unit,0,i),*b=row(other,1,i);for(int x=680;x<720;x++)a[2*x+1]=b[2*x+1]=x>710?2:18;}
    for(int i=170;i<173;i++)displace(unit,0,i,-8);
    run(1);for(int i=170;i<173;i++)assert(result.action[2*i]==HRT_RETIME && result.shift[2*i]==-8);
    fixture();
    for(int i=170;i<174;i++){uint8_t *a=row(unit,0,i),*b=row(other,1,i);for(int x=680;x<720;x++)a[2*x+1]=b[2*x+1]=x>710?2:18;}
    for(int i=170;i<173;i++){uint8_t *p=row(unit,0,i);for(int x=0;x<6;x++)p[2*(10+x)+1]=2;
        for(int x=26;x<680;x++)p[2*x+1]=60+random_byte()%160;}
    run(1);assert(!result.band_count);
    /* 3:16 on the commercial tape: dark content at blanking level covers the left and right of most
     * lines, so the frame standards land on content edges (140 and ~600), far from the window edges.
     * The content sways 7 samples between fields in a band of lines; that is camera motion, not
     * timing, and the line's real blanking is unobservable on both sides: nothing may change. */
    fixture();noisy();
    for(int k=0;k<2;k++)for(int i=0;i<240;i++){uint8_t *p=row(k?other:unit,k,i);for(int x=0;x<720;x++)if(x<135 || x>600)p[2*x+1]=2;}
    for(int i=100;i<131;i++){memcpy(row(unit,0,i),row(other,1,i),1440);displace(unit,0,i,7);}
    run(1);assert(!result.band_count && !changed(out1,unit) && !changed(out2,other));
    /* Review of the reach check: a dark frame whose coarse standard lands on dim left content (12
     * codes to sample 60, then 25) while the bright minority sets a refined standard near the window
     * edge. A genuine 6-sample bend on three bright lines is still retimed. */
    fixture();noisy();
    for(int k=0;k<2;k++)for(int i=0;i<240;i++)if(i%12<7){uint8_t *p=row(k?other:unit,k,i);for(int x=10;x<720;x++)p[2*x+1]=x<60?12:25;}
    for(int i=151;i<154;i++){int dim=0;for(int j=151;j<154;j++)dim|=j%12<7;assert(!dim);displace(unit,0,i,6);}
    run(1);for(int i=151;i<154;i++)assert(result.action[2*i]==HRT_RETIME && result.shift[2*i]==6);
    uint8_t flat[720];memset(flat,2,sizeof flat);
    assert(!carries_picture(flat,22,0,2,1));
    flat[100]=7;assert(!carries_picture(flat,22,0,2,1));
    flat[100]=8;assert(carries_picture(flat,22,0,2,1));
    assert(!carries_picture(flat,20,0,2,1) && !carries_picture(flat,21,0,2,1));
    assert(!carries_picture(flat,283,1,2,1) && !carries_picture(flat,284,1,2,1));
    assert(carries_picture(flat,285,1,2,1));
    uint8_t a[1440],b[1440],fill[1440];for(int x=0;x<360;x++){a[4*x]=x%256;a[4*x+2]=255-x%256;a[4*x+1]=a[4*x+3]=100;}
    memset(b,77,sizeof b);retime(a,b,1,NULL);
    assert(b[40]==average(a[40],a[44]) && b[42]==average(a[42],a[46]));
    assert(b[1439]==a[1439] && b[1436]==a[1436] && b[1438]==a[1438]);
    memset(fill,9,sizeof fill);retime(a,b,3,fill);
    assert(b[2*715+1]==a[2*718+1] && b[2*716+1]==9 && b[2*716]==9 && b[2*716+2]==9);
    retime(a,b,-3,fill);assert(b[2*3+1]==9 && b[2*4+1]==a[3]);
    hrt_reset(&work);assert(!work.have);
    puts("HRETIME PASS: Pearson oracles, falloff crossing, other-field detection, range, retime with other-field fill, spill, width, agreement, near-blanking, motion, switch");
    return 0;
}
