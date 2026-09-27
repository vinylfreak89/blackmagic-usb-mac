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
static void check_search(const uint8_t *a,const uint8_t *b,const uint8_t *c) {
    uint32_t ap[721],bp[721],cp[721];
    uint16_t doubled[720],ref[720];
    for(int x=0;x<720;x++){doubled[x]=2*a[x];ref[x]=b[x]+c[x];}
    prefix(a,ap);prefix(b,bp);prefix(c,cp);
    unsigned best=~0u,zero=0;int expected=0;
    for(int s=-SEARCH;s<=SEARCH;s++) {
        unsigned sum=0;
        for(int x=SCORE_LO;x<SCORE_HI;x++)sum+=(unsigned)abs(2*(int)a[x+s]-b[x]-c[x]);
        assert(sum==prepared_sad(doubled,ref,s));
        assert(lower_bound(ap,bp,cp,s)<=sum);
        if(sum<best){best=sum;expected=s;}
        if(!s)zero=sum;
    }
    int shift=0;float ratio=search(a,b,c,ap,bp,cp,&shift);
    float expected_ratio=((float)best/(2*SCORE_SIZE))/fmaxf((float)zero/(2*SCORE_SIZE),1e-6f);
    assert(shift==expected && ratio==expected_ratio);
}
static void oracle(void) {
    uint8_t a[720],b[720],c[720];
    for(int trial=0;trial<50;trial++) {
        for(int x=0;x<720;x++){a[x]=random_byte();b[x]=random_byte();c[x]=random_byte();}
        if(trial==0)memset(a,2,sizeof a),memset(b,2,sizeof b),memset(c,2,sizeof c);
        if(trial==1)memset(a,255,sizeof a),memset(b,0,sizeof b),memset(c,0,sizeof c);
        check_search(a,b,c);
    }
}
static void edge_ownership(void) {
    fixture();run(); /* unflagged body has edges10/710 and zero spread */
    assert(result.edge_median[0][0]==10 && result.edge_median[1][1]==710);
    for(int j=0;j<4;j++)for(int x=0;x<720;x++)work.y[j][x]=x>=10 && x<=710?100:2;
    for(int x=0;x<720;x++)work.y[1][x]=x<=680?100:2;
    assert(edge_movement(&work,&result,1)==(HRT_EDGES_KNOWN|HRT_LEFT_EARLIER|HRT_RIGHT_EARLIER));
    for(int x=0;x<720;x++)work.y[3][x]=x>=40?100:2;
    assert(edge_movement(&work,&result,3)==(HRT_EDGES_KNOWN|HRT_LEFT_LATER|HRT_RIGHT_LATER));
    int count[2]={0,0};
    assert(top_owner(&work,&result,0,3,count)==1 && count[0]==0 && count[1]==2);
    memcpy(work.y[0],work.y[1],720);memcpy(work.y[2],work.y[3],720);
    count[0]=count[1]=0;assert(top_owner(&work,&result,0,3,count)==-1 && count[0]==2 && count[1]==2);
    result.edge_median[0][0]=NAN;count[0]=count[1]=0;
    assert(top_owner(&work,&result,0,3,count)==-1 && count[0]==0 && count[1]==0);
    result.edge_median[0][0]=10;result.edge_spread[0][0]=10;result.edge_spread[0][1]=30;
    assert(edge_movement(&work,&result,0)==HRT_EDGES_KNOWN); /* strict >, not >= */
    memset(work.y[0],2,720);assert(edge_movement(&work,&result,0)==0);
    /* An unresolved top band cannot supply its own normal reference. */
    edge_reference(&work,&result,479,0,0);assert(isnan(result.edge_median[0][0]));
}
int main(int argc,char **argv) {
    if(argc==2) {
        FILE *f=fopen(argv[1],"rb");assert(f);uint8_t rows[3][720];unsigned n=0;size_t got;
        while((got=fread(rows,1,sizeof rows,f))){assert(got==sizeof rows);check_search(rows[0],rows[1],rows[2]);n++;}
        assert(!ferror(f));fclose(f);printf("HRETIME captured scalar oracle: %u triples PASS\n",n);return 0;
    }
    assert(argc==1);
    oracle();
    edge_ownership();
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
    for(int s=-SEARCH;s<=SEARCH;s+=SEARCH)if(s) {
        fixture();displace(unit,0,20,s,0);run();
        assert(result.shift[40]==s && result.action[40]==HRT_INTERPOLATE);
    }
    fixture();displace(unit,0,20,-80,0);run();
    assert(result.shift[40]==-80 && result.action[40]==HRT_INTERPOLATE);
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
    puts("HRETIME PASS: scalar/SIMD, shift, compressed width, censored edges, symmetric top ownership/ties/unknown, switch exclusion, no picture, chroma, crop bounds");
    return 0;
}
