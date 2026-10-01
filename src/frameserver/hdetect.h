#ifndef HDETECT_H
#define HDETECT_H
/* H-timing detection, v11 (experiments/hdetect/premise/phys.py is the reference; see its history on
 * engine-cleanup). Playback order: each unit's two fields are judged against statistics of the preceding
 * HD_WINDOW units, with detected bands cut out of those statistics. Detection only: no repair. */
#include <stddef.h>
#include <stdint.h>

enum { HD_WINDOW=30, HD_ROWS=525, HD_WIDTH=720 };

typedef struct hd_state hd_state;

typedef struct {
    int judged;               /* 0 while the window warms (first three units) */
    int torn[2];              /* a band of at least two adjacent moved lines in the field */
    int nosw[2], swheld[2];   /* no head-switch line known yet / switch line held from an earlier unit */
    int switch_line[2];       /* NTSC line of the field's head switch in use, 0 if none */
    int nlines[2];
    int16_t lines[2][HD_ROWS];/* NTSC lines in the band (raster order), above-top lines included */
} hd_result;

size_t hd_size(void);
void hd_init(hd_state *s);
/* luma: 525x720 delivered rows of one unit. top1/top2: registration's field tops as NTSC lines, -1 unknown. */
void hd_judge(hd_state *s,const uint8_t *luma,int top1,int top2,hd_result *out);

#endif
