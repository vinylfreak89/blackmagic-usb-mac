/* Private measurement golden: no classifier, crop feedback, or lock can
 * supply the expected switch. Optional raw unit is exported by switch_probe. */
#ifndef FIELDREG_TEST_IMPLEMENTATION
#define FIELDREG_TEST_IMPLEMENTATION "../field_registration.c"
#endif
#include FIELDREG_TEST_IMPLEMENTATION
#include <stdio.h>

static uint8_t raster[FIELDREG_RASTER_LINES * FIELDREG_BYTES_PER_LINE];
static unsigned failures, checks;

static void check(const char *name, int actual, int expected)
{
    ++checks;
    if (actual == expected) return;
    ++failures;
    fprintf(stderr, "%s: got %d expected %d\n", name, actual, expected);
}

static void sample(int row, int x, unsigned y)
{
    raster[(size_t)row * FIELDREG_BYTES_PER_LINE + 2*x] = 128;
    raster[(size_t)row * FIELDREG_BYTES_PER_LINE + 2*x+1] = (uint8_t)y;
}

static void synthetic(unsigned blank, int partial, bool complete_partial)
{
    /* These are constructed input values, not detector parameters. Blanking
     * may be at a different level; picture brightness changes without timing.
     * Both fields are filled so the whole-raster measurement remains valid. */
    for (int row=0; row<525; ++row)
        for (int x=0; x<720; ++x) sample(row,x,blank);
    for (int f=0; f<2; ++f) {
        const int top=f?282:19, clip=f?521:258;
        const int t=f?partial+263:partial;
        for (int row=top; row<=clip; ++row) for (int x=0; x<720; ++x) {
            unsigned y=blank + (row < t-20 ? 80+(x*13)%90 : 18+(x*7)%5);
            /* Nine delivered blanking samples, split 4 + 5. */
            if (x<4 || x>=715) y=blank;
            if (row>=t+1) {
                y=blank+28+(x*11)%7;
                if (x>=80 && x<227) y=blank;
            } else if (row==t && x>=360) {
                y=blank+18+(x*3)%5;
                if (complete_partial ? (x>=400 && x<547) : (x>=560 && x<610)) y=blank;
            }
            sample(row,x,y);
        }
        field_measurement m;
        measure_field(raster,f,&m);
        check("synthetic partial",m.switch_line,t);
        check("synthetic full",m.first_full_other_head_line,t+1);
        check("synthetic bottom",m.bottom,t-1);
    }
}

static void negative_controls(void)
{
    /* Start with a textured field whose picture contains both a brightness
     * step and a black rectangle. Its normal blanking never moves. */
    for(int row=0;row<525;++row)for(int x=0;x<720;++x)sample(row,x,2);
    for(int row=19;row<=258;++row)for(int x=0;x<720;++x) {
        unsigned y=row<190?100+(x*13)%70:20+(x*3)%7;
        if(x<4 || x>=715 || (row>=190 && x>=80 && x<227))y=2;
        sample(row,x,y);
    }
    field_measurement m;
    measure_field(raster,0,&m);
    check("content edge and black rectangle",m.switch_line,-1);
    /* A genuine interior phase excursion followed by normal timing is not
     * a terminal switch. All row numbers here describe synthetic inputs. */
    for(int row=120;row<140;++row)for(int x=0;x<720;++x)
        sample(row,x,x>=300 && x<447 ? 2 : 30+(x*11)%9);
    measure_field(raster,0,&m);
    check("interior departure and return",m.switch_line,-1);
    /* Loss of a former blanking position alone is not positive relocation. */
    for(int row=250;row<=258;++row)for(int x=0;x<720;++x)sample(row,x,21);
    measure_field(raster,0,&m);
    check("missing timing is unknown",m.switch_line,-1);
    /* Never attach a remote excursion to a later full blanking interval
     * across rows that supplied no local timing reference. */
    for(int row=31;row<=258;++row)for(int x=0;x<720;++x) {
        unsigned y=21;
        if(row==31 && x>=560 && x<610)y=2;
        if(row>=257 && x>=80 && x<227)y=2;
        sample(row,x,y);
    }
    measure_field(raster,0,&m);
    check("unreadable rows age out the timing reference",m.switch_line,-1);
    /* Whole-row black can be identical to porch. It supplies no phase. */
    for(int row=19;row<=258;++row)for(int x=0;x<720;++x)sample(row,x,2);
    measure_field(raster,0,&m);
    check("blank-equivalent picture is unknown",m.switch_line,-1);
    /* A noisy first relocated interval cannot make the easier second row S.
     * This instrument has no RF-peak detector; it must abstain here. */
    for(int row=19;row<=258;++row)for(int x=0;x<720;++x) {
        unsigned y=80+(x*13)%70;
        if(x<4 || x>=715)y=2;
        if(row>=256) {
            y=x>=80 && x<227 ? 2 : 28;
            if(row==256 && x==150)y=200;
        }
        sample(row,x,y);
    }
    measure_field(raster,0,&m);
    check("corrupted first interval does not move S",m.switch_line,-1);
}

static void raw_unit(const char *path)
{
    FILE *in=fopen(path,"rb");
    if (!in) { perror(path); ++failures; return; }
    uint8_t unit[FIELDREG_UNIT_BYTES];
    if(fread(unit,1,sizeof unit,in)!=sizeof unit || !valid_unit(unit) ||
       read_le16(unit+4)!=6687) {fprintf(stderr,"invalid raw 6687 unit\n");exit(2);}
    memcpy(raster,unit+FIELDREG_HEADER_BYTES,sizeof raster);
    if(fgetc(in)!=EOF || ferror(in))exit(2);
    fclose(in);
    for(int f=0; f<2; ++f) {
        field_measurement m; measure_field(raster,f,&m);
        printf("6687 f%d: T=%d S=%d bottom=%d clip=%d\n",f+1,
               m.switch_line<0?-1:m.switch_line+4,
               m.first_full_other_head_line<0?-1:m.first_full_other_head_line+4,
               m.bottom<0?-1:m.bottom+4,m.recorded_last+4);
        check("6687 partial",m.switch_line,f?518:256);
        check("6687 full",m.first_full_other_head_line,f?519:257);
        check("6687 bottom",m.bottom,f?517:255);
    }
}

int main(int argc,char **argv)
{
    synthetic(2,256,false);
    synthetic(17,248,false);
    synthetic(2,256,true);
    negative_controls();
    if(argc==2)raw_unit(argv[1]);
    else if(argc!=1)return 2;
    printf("SWITCH-TIMING: %u/%u passed\n",checks-failures,checks);
    return failures?1:0;
}
