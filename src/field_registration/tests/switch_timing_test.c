/* Private measurement golden: no classifier, crop feedback, or lock can
 * supply the expected switch. Optional PGM is the raw switch_probe panel. */
#include "../field_registration.c"
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

static void synthetic(unsigned blank, int partial)
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
            if (x<4 || x>=706) y=blank;
            if (row>=t+1) {
                y=blank+28+(x*11)%7;
                if (x>=80 && x<227) y=blank;
            } else if (row==t && x>=360) {
                y=blank+18+(x*3)%5;
                if (x>=560 && x<610) y=blank;
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

static void raw_panel(const char *path)
{
    FILE *in=fopen(path,"rb");
    if (!in) { perror(path); ++failures; return; }
    char magic[3]; int width,height,maximum;
    if (fscanf(in,"%2s %d %d %d",magic,&width,&height,&maximum)!=4 ||
        strcmp(magic,"P5") || width!=1440 || height!=263 || maximum!=255 ||
        fgetc(in)!='\n') { fprintf(stderr,"invalid raw panel\n"); exit(2); }
    for (int y=0; y<263; ++y) for (int f=0; f<2; ++f) for (int x=0; x<720; ++x) {
        int v=fgetc(in); if(v==EOF)exit(2);
        if(y+263*f<525)sample(y+263*f,x,(unsigned)v);
    }
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
    synthetic(2,256);
    synthetic(17,248);
    if(argc==2)raw_panel(argv[1]);
    else if(argc!=1)return 2;
    printf("SWITCH-TIMING: %u/%u passed\n",checks-failures,checks);
    return failures?1:0;
}
