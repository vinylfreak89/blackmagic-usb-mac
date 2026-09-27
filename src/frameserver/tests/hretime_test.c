/* Task45: neighbour content, one-sided bends, and interior black. */
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
        for(int shift=-2;shift<=2;shift++) {
            double sa=0,sb=0,aa=0,bb=0,ab=0;
            for(int x=0;x<720;x++) {
                int p=x+shift;if(p<0)p=0;if(p>719)p=719;
                double u=a[p],v=b[x];sa+=u;sb+=v;aa+=u*u;bb+=v*v;ab+=u*v;
            }
            double expected=(ab-sa*sb/720)/sqrt((aa-sa*sa/720)*(bb-sb*sb/720));
            assert(line_correlation(a,b,shift)==expected);
        }
    }
    memset(a,2,sizeof a);assert(isnan(line_correlation(a,a,0)));
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
    displace(unit,0,20,6);run(5);assert(result.field[0].retimed==1);
    assert(work.history_count[0]>0);
    hrt_begin(&work,7,7,1,0);assert(!work.history_count[0]);
    run(8);hrt_begin(&work,9,9,2,0);assert(!work.history_count[0]);
    hrt_reset(&work);assert(!work.have);
    fixture();run(1);for(int i=0;i<6;i++)displace(other,1,i,-9);
    run(2);assert(result.field[1].retimed==6 && !result.field[0].retimed);
    fixture();run(1);for(int i=0;i<6;i++)displace(other,1,i,-12);
    run(2);assert(result.field[1].interpolated==6 && !result.field[1].unavailable);
    assert(!result.field[0].retimed && !result.field[0].interpolated);
    fixture();run(1);for(int i=20;i<23;i++){displace(unit,0,i,6);displace(other,1,i,6);}
    run(2);assert(!result.field[0].retimed && !result.field[1].retimed); /* shared movement correlates */
    fixture();run(1);for(int i=232;i<238;i++)displace(unit,0,i,6);
    run(2);assert(!result.band_count); /* switch */
    fixture();run(1);
    for(int x=300;x<331;x++)unit[48+(19+20)*1440+2*x+1]=2;
    run(2);assert((result.reason[40]&HRT_INTERIOR_BLANK) &&
                  result.action[40]==HRT_NONE); /* border blanking is intact */
    fixture();for(int r=0;r<525;r++)for(int x=0;x<720;x++)unit[48+r*1440+2*x+1]=2;
    memcpy(other,unit,sizeof unit);run(1);assert(result.field[0].interpolated && result.field[1].interpolated);
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
    assert(interpolate(&work,40,out1)); /* outward search reaches rows37/43 */
    assert(repair_choice(&work,40,0,0,&s) && s==0); /* within measured error */
    work.repair[40]=(repair_boundary){{13,713},{1,1},0};
    assert(repair_choice(&work,40,0,0,&s) && s==3);
    work.repair[40]=(repair_boundary){{13,713},{2,4},0};
    assert(repair_choice(&work,40,0,0,&s) && s==0); /* mean error bound3 */
    work.repair[40]=(repair_boundary){{10,710},{1,1},0};
    assert(repair_choice(&work,40,0,0,&s) && s==0);
    work.repair[40]=(repair_boundary){{30,710},{1,1},0};
    assert(!repair_choice(&work,40,0,0,&s));
    work.repair[40]=(repair_boundary){{NAN,710},{NAN,1},1};
    assert(!repair_choice(&work,40,0,0,&s));
    fixture();hrt_apply(&work,unit,other,-30,30,out1,out2,&result);
    /* Linear zero crossing bridges; a flat intervening plateau does not. */
    fixture();run(1);memset(work.flagged,0,sizeof work.flagged);
    for(int j=0;j<480;j++)work.repair[j]=(repair_boundary){{10,710},{1,1},0};
    result.edge_median[0][0]=10;result.edge_median[0][1]=710;
    work.flagged[40]=work.flagged[48]=1;
    for(int j=40;j<=48;j+=2) {
        double d=-4+(j-40);work.repair[j].edge[0]+=d;work.repair[j].edge[1]+=d;
    }
    bridge(&work,&result,0,0);assert(work.flagged[42] && work.flagged[44] && work.flagged[46]);
    memset(work.flagged,0,sizeof work.flagged);work.flagged[40]=work.flagged[48]=1;
    work.repair[42].edge[0]=10;work.repair[42].edge[1]=710;
    bridge(&work,&result,0,0);assert(!work.flagged[42]);
    /* Real pooled percentile, not a MAD multiplier or one-sample floor. */
    memset(&work,0,sizeof work);work.history_count[0]=1;
    normal_summary *h=&work.history[0][0];h->count=100;
    for(int i=0;i<100;i++){h->edges[0][i]=10+.01*i;h->edges[1][i]=710+.01*i;}
    normal(&work,&result,0);
    assert(fabs(result.edge_median[0][0]-10.495)<1e-12);
    assert(fabs(result.edge_spread[0][0]-.495)<1e-12);
    /* A one-sided departure survives if the peer has picture there. The same
     * dark/flat interval in both peers vetoes it, without requiring two edges. */
    fixture();run(1);
    work.repair[40].edge[1]=715;result.edge_median[0][1]=707;
    double noise[2]={1,1};
    for(int x=708;x<=715;x++) {
        work.y[40][x]=16;work.y[39][x]=work.y[41][x]=16;
    }
    assert(edge_content(&work,&result,noise,40,1));
    for(int x=707;x<=715;x++)work.y[39][x]=work.y[41][x]=100;
    assert(!edge_content(&work,&result,noise,40,1));
    puts("HRETIME PASS: Pearson oracle, learned history, singleton, shape, width, spill, donors, zero crossing, chroma, crop bounds");
    return 0;
}
