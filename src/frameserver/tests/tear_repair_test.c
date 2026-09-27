#include "../tear_repair.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { BYTES=TR_RASTER_ROWS*TR_LINE_BYTES };
static uint8_t raw[BYTES],out[BYTES],partner[BYTES],other_out[BYTES],saved[BYTES];
static void row(int r,int blank) {
    for(int x=0;x<TR_WIDTH;x++) {
        raw[r*TR_LINE_BYTES+2*x]=128;
        raw[r*TR_LINE_BYTES+2*x+1]=blank?1:40+(x%40)*3;
    }
}
static void base(void) {
    for(int r=0;r<TR_RASTER_ROWS;r++)row(r,1);
    for(int r=19;r<259;r++)row(r,0);
    for(int r=282;r<522;r++)row(r,0);
}
static void damage(int r) {
    for(int x=8;x<148;x++)raw[r*TR_LINE_BYTES+2*x+1]=1;
}
static tr_result repair(void) {
    tr_result r;memcpy(out,raw,BYTES);memcpy(saved,raw,BYTES);
    tr_repair(raw,raw,0,0,out,out,&r);
    assert(!memcmp(saved,raw,BYTES));
    return r;
}
int main(void) {
    base();damage(257);damage(258);damage(519);damage(520);damage(521);
    tr_result r=repair();
    assert(r.field[0].flagged==2 && r.field[1].flagged==3);
    assert(r.field[0].repaired==2 && r.field[1].repaired==3);
    assert(r.field[1].fill==1 && r.field[1].interpolate==2); /* final X neighbours damaged */
    assert(!memcmp(out+521*TR_LINE_BYTES,raw+518*TR_LINE_BYTES,TR_LINE_BYTES));
    base();damage(258);r=repair();
    assert(r.field[0].fill==1 && !r.field[1].flagged);
    /* Real dark pillars have the same detector signature: known false positive. */
    base();damage(258);r=repair();assert(r.field[0].flagged==1);
    /* Dark, but no displaced/blank-level lead: no repair. */
    base();for(int x=0;x<TR_WIDTH;x++)raw[258*TR_LINE_BYTES+2*x+1]=22;
    r=repair();assert(!r.field[0].flagged && !memcmp(raw,out,BYTES));
    /* Below the last picture row is blanking, never a source or repair target. */
    base();row(258,1);damage(257);r=repair();
    assert(r.field[0].first==261 && r.field[0].last==261);
    assert(r.field[0].repaired_first==261 && r.field[0].repaired_last==261);
    assert(!memcmp(out+258*TR_LINE_BYTES,raw+258*TR_LINE_BYTES,TR_LINE_BYTES));
    for(int i=0;i<TR_RASTER_ROWS;i++)row(i,1);
    r=repair();assert(!r.field[0].flagged && !r.field[1].flagged);
    assert(!memcmp(raw,out,BYTES));
    /* Median of an even population must average both central samples. */
    base();for(int y=7;y<16;y++)for(int x=0;x<720;x++)raw[y*1440+2*x+1]=x<360?1:2;
    r=repair();assert(r.field[0].blank==1.5);
    /* Separate frame owners: top from this unit, bottom from its actual partner.
     * The same-unit bottom deliberately contains different samples. */
    base();memcpy(partner,raw,BYTES);damage(258);
    for(int y=282;y<522;y++)for(int x=0;x<720;x++)raw[y*1440+2*x+1]=200;
    memcpy(out,raw,BYTES);memcpy(other_out,partner,BYTES);
    tr_repair(raw,partner,0,0,out,other_out,&r);
    assert(r.field[0].fill==1);
    assert(!memcmp(out+258*1440,partner+520*1440,1440));
    /* An entirely flagged field without clean support must not invent a source. */
    base();for(int y=19;y<259;y++)damage(y);
    for(int y=282;y<522;y++)row(y,1);
    r=repair();assert(r.field[0].flagged==240 && !r.field[0].repaired);
    /* Out-of-raster placement remains unavailable rather than crossing fields. */
    memcpy(out,raw,BYTES);tr_repair(raw,raw,-25,260,out,out,&r);
    assert(!r.field[1].flagged);
    /* A distant local minimum rejects X even when both X neighbours exist. */
    base();
    for(int j=0;j<240;j++)for(int x=0;x<720;x++) {
        raw[(19+j)*1440+2*x+1]=40+(j%20)*5;
        raw[(282+j)*1440+2*x+1]=40+((j+2)%20)*5;
    }
    damage(258);r=repair();
    assert(r.field[0].fill==0 && r.field[0].interpolate==1);
    assert(!memcmp(out+258*1440,raw+257*1440,1440));
    /* Inclusive lead count, not a contiguous-run test. */
    base();for(int x=8;x<128;x+=2)raw[258*1440+2*x+1]=4;
    r=repair();assert(r.field[0].flagged==1);
    raw[258*1440+2*126+1]=5;r=repair();assert(!r.field[0].flagged);
    /* Eight strict-above samples, and only the terminal picture run. */
    base();row(258,1);for(int x=300;x<307;x++)raw[258*1440+2*x+1]=22;
    r=repair();assert(!r.field[0].flagged);
    raw[258*1440+2*307+1]=22;r=repair();assert(r.field[0].flagged==1);
    base();damage(257);r=repair();assert(!r.field[0].flagged);
    puts("tear repair: 13 synthetic cases PASS");return 0;
}
