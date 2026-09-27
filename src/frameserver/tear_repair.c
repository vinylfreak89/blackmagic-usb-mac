#include "tear_repair.h"
#include <string.h>
#include <stdint.h>

enum { VI_ROWS=9, LEAD_FIRST=8, LEAD_END=200, SCAN_END=716,
       PICTURE_RUN=8, LEAD_COUNT=60, LOCAL_INTERVALS=12 };

static double blank_level(const uint8_t *raster,int field) {
    unsigned hist[256]={0}, n=VI_ROWS*TR_WIDTH, accum=0;
    int start=field?270:7, lo=-1;
    for(int r=start;r<start+VI_ROWS;r++)
        for(int x=0;x<TR_WIDTH;x++)hist[raster[r*TR_LINE_BYTES+2*x+1]]++;
    for(int v=0;v<256;v++) {
        accum+=hist[v];
        if(lo<0 && accum>=n/2)lo=v;
        if(accum>n/2)return (lo+v)*0.5;
    }
    return 0;
}

void tr_detect(const uint8_t *raster,int field,int start,int end,
               uint8_t picture[TR_RASTER_ROWS],uint8_t flagged[TR_RASTER_ROWS],
               tr_field_result *o) {
    memset(picture,0,TR_RASTER_ROWS);memset(flagged,0,TR_RASTER_ROWS);
    *o=(tr_field_result){0};o->blank=blank_level(raster,field);
    int last=-1;unsigned lead[TR_RASTER_ROWS]={0};
    if(start<0)start=0;
    if(end>TR_RASTER_ROWS)end=TR_RASTER_ROWS;
    for(int r=start;r<end;r++) {
        const uint8_t *line=raster+r*TR_LINE_BYTES;int run=0;
        for(int x=LEAD_FIRST;x<SCAN_END;x++) {
            double v=line[2*x+1];
            if(x<LEAD_END && v>=o->blank-3 && v<=o->blank+3)lead[r]++;
            run=v>o->blank+20?run+1:0;
            if(run>=PICTURE_RUN)picture[r]=1;
        }
        if(picture[r])last=r;
    }
    for(int r=last;r>=start && picture[r] && lead[r]>=LEAD_COUNT;r--) {
        flagged[r]=1;o->first=r+4;o->flagged++;
    }
    if(o->flagged)o->last=last+4;
}

static int usable(int row,int start,int field,const uint8_t *pic,const uint8_t *flag) {
    return row>=start && row<start+TR_ROWS && row>=(field?262:0) &&
           row<(field?525:262) && pic[row] && !flag[row];
}

/* Same max((a-b)*(c-b),0) as ge_comb, on clean local triplets. All
 * eleven candidates use identical support. Factor 2 is its refusal ratio. */
static int local_agreement(const uint8_t *top,const uint8_t *bottom,const int start[2],
                           uint8_t pic[2][TR_RASTER_ROWS],uint8_t flag[2][TR_RASTER_ROWS],
                           int height) {
    uint64_t energy[11]={0};int count=0;
    for(int j=height-LOCAL_INTERVALS;j<height;j++) {
        int t=start[0]+j,b=start[1]+j,valid=1;
        if(!usable(t,start[0],0,pic[0],flag[0]) ||
           !usable(t+1,start[0],0,pic[0],flag[0]))continue;
        for(int d=-5;d<=5;d++)if(!usable(b+d,start[1],1,pic[1],flag[1]))valid=0;
        if(!valid)continue;
        count++;
        for(int d=-5;d<=5;d++)for(int x=40;x<680;x++) {
            int a=top[t*TR_LINE_BYTES+2*x+1],c=top[(t+1)*TR_LINE_BYTES+2*x+1];
            int v=bottom[(b+d)*TR_LINE_BYTES+2*x+1],e=(a-v)*(c-v);
            if(e>0)energy[d+5]+=(unsigned)e;
        }
    }
    uint64_t best=energy[0];for(int i=1;i<11;i++)if(energy[i]<best)best=energy[i];
    return count && energy[5]<=2*best;
}

static void mix(uint8_t *out,const uint8_t *a,const uint8_t *b,int wa,int wb) {
    int total=wa+wb;
    for(int x=0;x<TR_LINE_BYTES;x++)out[x]=(uint8_t)((a[x]*wa+b[x]*wb+total/2)/total);
}

void tr_repair(const uint8_t *top,const uint8_t *bottom,int d1,int d2,
               uint8_t *out_top,uint8_t *out_bottom,tr_result *o) {
    const uint8_t *source[2]={top,bottom};uint8_t *dest[2]={out_top,out_bottom};
    int start[2]={19+d1,282+d2};uint8_t pic[2][TR_RASTER_ROWS],flag[2][TR_RASTER_ROWS];
    for(int k=0;k<2;k++) {
        int lo=k?262:0,hi=k?525:262;
        int first=start[k]>lo?start[k]:lo,end=start[k]+TR_ROWS;
        tr_detect(source[k],k,first,end<hi?end:hi,pic[k],flag[k],&o->field[k]);
    }
    for(int k=0;k<2;k++) {
        tr_field_result *f=&o->field[k];if(!f->flagged)continue;
        int height=f->first-4-start[k];
        int agree=local_agreement(top,bottom,start,pic,flag,height);
        for(int row=f->first-4;row<=f->last-4;row++) {
            int j=row-start[k],other=1-k;
            int x0=start[other]+j-(k==0),x1=x0+1;
            int u0=usable(x0,start[other],other,pic[other],flag[other]);
            int u1=usable(x1,start[other],other,pic[other],flag[other]);
            uint8_t *out=dest[k]+row*TR_LINE_BYTES;
            if(agree && (u0||u1)) {
                if(u0&&u1)mix(out,source[other]+x0*TR_LINE_BYTES,source[other]+x1*TR_LINE_BYTES,1,1);
                else memcpy(out,source[other]+(u0?x0:x1)*TR_LINE_BYTES,TR_LINE_BYTES);
                f->fill++;
            } else {
                int a=row-1,b=row+1;
                while(a>=start[k] && !usable(a,start[k],k,pic[k],flag[k]))a--;
                while(b<start[k]+TR_ROWS && !usable(b,start[k],k,pic[k],flag[k]))b++;
                int ua=usable(a,start[k],k,pic[k],flag[k]),ub=usable(b,start[k],k,pic[k],flag[k]);
                if(!ua&&!ub)continue;
                if(ua&&ub)mix(out,source[k]+a*TR_LINE_BYTES,source[k]+b*TR_LINE_BYTES,b-row,row-a);
                else memcpy(out,source[k]+(ua?a:b)*TR_LINE_BYTES,TR_LINE_BYTES);
                f->interpolate++;
            }
            f->repaired++;
            if(!f->repaired_first)f->repaired_first=row+4;
            f->repaired_last=row+4;
        }
    }
}
