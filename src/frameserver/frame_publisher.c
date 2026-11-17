#include "frame_publisher.h"
#include <stdlib.h>
#include <string.h>
#include <CoreFoundation/CoreFoundation.h>

struct fp_publisher {
    fp_sink sink;
    unsigned n;
    IOSurfaceRef *pool;
    fp_stats st;
};

static int clamp_offset(int start, int d){
    // keep start+d .. start+d+239 inside 0..524
    int lo = -start, hi = (int)FP_SOURCE_LINES - FP_FIELD_LINES - start;
    if (d < lo) return lo;
    if (d > hi) return hi;
    return d;
}

void fp_assemble(uint8_t *dst, const uint8_t *unit, int d1, int d2){
    const uint8_t *src = unit + FP_UNIT_HEADER;
    int f1 = FP_FIELD1_START + clamp_offset(FP_FIELD1_START, d1);
    int f2 = FP_FIELD2_START + clamp_offset(FP_FIELD2_START, d2);
    for (int k = 0; k < FP_FIELD_LINES; k++){
        memcpy(dst + (size_t)(2*k)   * FP_LINE_BYTES, src + (size_t)(f1 + k) * FP_LINE_BYTES, FP_LINE_BYTES);
        memcpy(dst + (size_t)(2*k+1) * FP_LINE_BYTES, src + (size_t)(f2 + k) * FP_LINE_BYTES, FP_LINE_BYTES);
    }
}
unsigned fp_assemble_placed(uint8_t *dst,const uint8_t *unit,int d1,int d2){
    unsigned missing=0;
    for(int k=0;k<FP_FIELD_LINES;k++)for(int f=0;f<2;f++){
        int row=(f?FP_FIELD2_START+d2:FP_FIELD1_START+d1)+k;
        uint8_t *out=dst+(2*k+f)*FP_LINE_BYTES;
        int lo=f?FP_FIELD2_FIRST_ROW:0,hi=f?(int)FP_SOURCE_LINES:FP_FIELD2_FIRST_ROW;
        if(row>=lo && row<hi)memcpy(out,unit+FP_UNIT_HEADER+row*FP_LINE_BYTES,FP_LINE_BYTES);
        else {for(unsigned x=0;x<FP_LINE_BYTES;x+=2){out[x]=128;out[x+1]=16;}missing++;}
    }
    return missing;
}

static IOSurfaceRef make_surface(void){
    int w = FP_FRAME_WIDTH, h = FP_FRAME_HEIGHT, bpe = 2, bpr = FP_LINE_BYTES;
    uint32_t fmt = '2vuy';
    CFNumberRef nw = CFNumberCreate(NULL, kCFNumberIntType, &w);
    CFNumberRef nh = CFNumberCreate(NULL, kCFNumberIntType, &h);
    CFNumberRef nb = CFNumberCreate(NULL, kCFNumberIntType, &bpe);
    CFNumberRef nr = CFNumberCreate(NULL, kCFNumberIntType, &bpr);
    CFNumberRef nf = CFNumberCreate(NULL, kCFNumberSInt32Type, &fmt);
    const void *keys[] = { kIOSurfaceWidth, kIOSurfaceHeight, kIOSurfaceBytesPerElement,
                           kIOSurfaceBytesPerRow, kIOSurfacePixelFormat };
    const void *vals[] = { nw, nh, nb, nr, nf };
    CFDictionaryRef d = CFDictionaryCreate(NULL, keys, vals, 5,
                          &kCFTypeDictionaryKeyCallBacks, &kCFTypeDictionaryValueCallBacks);
    IOSurfaceRef s = IOSurfaceCreate(d);
    CFRelease(d); CFRelease(nw); CFRelease(nh); CFRelease(nb); CFRelease(nr); CFRelease(nf);
    return s;
}

int fp_open(fp_publisher **out, unsigned pool_size, const fp_sink *sink){
    if (!out || !sink || !sink->on_frame || pool_size == 0) return -1;
    fp_publisher *p = calloc(1, sizeof *p);
    if (!p) return -1;
    p->sink = *sink; p->n = pool_size;
    p->pool = calloc(pool_size, sizeof(IOSurfaceRef));
    if (!p->pool){ free(p); return -1; }
    for (unsigned i = 0; i < pool_size; i++){
        p->pool[i] = make_surface();
        if (!p->pool[i]){ fp_close(p); return -1; }
    }
    p->st.pool_size = pool_size;
    *out = p; return 0;
}

static int publish(fp_publisher *p, const uint8_t *unit, size_t unit_len,
               uint64_t counter_ext, int d1, int d2, uint8_t transport,
               int audio_pts_known, uint64_t audio_pts_num,int placed){
    if (!p || !unit || unit_len != FP_UNIT_BYTES || (placed && (d1<INT8_MIN||d1>INT8_MAX||d2<INT8_MIN||d2>INT8_MAX))){ if (p) p->st.rejected_bad_args++; return -1; }
    IOSurfaceRef s = NULL;
    unsigned in_use = 0;
    for (unsigned i = 0; i < p->n; i++){
        if (IOSurfaceGetUseCount(p->pool[i]) == 0){ if (!s) s = p->pool[i]; }
        else in_use++;
    }
    p->st.pool_in_use = in_use;
    if (!s){ p->st.dropped_no_free_surface++; return 1; }
    IOSurfaceLock(s, 0, NULL);
    unsigned missing=0;
    if(placed)missing=fp_assemble_placed((uint8_t *)IOSurfaceGetBaseAddress(s),unit,d1,d2);
    else fp_assemble((uint8_t *)IOSurfaceGetBaseAddress(s), unit, d1, d2);
    IOSurfaceUnlock(s, 0, NULL);
    fp_frame f = { s, counter_ext * 1001u, 30000u, counter_ext,
                   (int8_t)(placed?d1:clamp_offset(FP_FIELD1_START,d1)), (int8_t)(placed?d2:clamp_offset(FP_FIELD2_START,d2)), transport,
                   (uint8_t)(audio_pts_known != 0), audio_pts_num,missing };
    p->st.published++;
    p->sink.on_frame(p->sink.ctx, &f);
    return 0;
}
int fp_publish_partial(fp_publisher *p, const uint8_t *rows, unsigned n_lines, int d1, int d2, uint64_t counter_ext,
                       int audio_pts_known, uint64_t audio_pts_num){
    if (!p || !rows || !n_lines || d1 < INT8_MIN || d1 > INT8_MAX || d2 < INT8_MIN || d2 > INT8_MAX){ if (p) p->st.rejected_bad_args++; return -1; }
    IOSurfaceRef s = NULL;
    for (unsigned i = 0; i < p->n && !s; i++) if (IOSurfaceGetUseCount(p->pool[i]) == 0) s = p->pool[i];
    if (!s){ p->st.dropped_no_free_surface++; return 1; }
    IOSurfaceLock(s, 0, NULL);
    uint8_t *dst = IOSurfaceGetBaseAddress(s); size_t bpr = IOSurfaceGetBytesPerRow(s);
    if (n_lines > 300){
        /* Both fields, as a whole unit's rows: the same aperture a whole unit is published with. Stretching them showed
         * field 1's whole raster, padding and vertical interval included, over 480 rows: a squashed picture (2026-11-15). */
        for (int k = 0; k < FP_FIELD_LINES; k++){
            int r1 = FP_FIELD1_START + d1 + k, r2 = FP_FIELD2_START + d2 + k;
            int v1 = r1 >= 0 && r1 < FP_FIELD2_FIRST_ROW && (unsigned)r1 < n_lines;
            int v2 = r2 >= FP_FIELD2_FIRST_ROW && r2 < (int)FP_SOURCE_LINES && (unsigned)r2 < n_lines;
            for (int f = 0; f < 2; f++){
                uint8_t *out = dst + (size_t)(2 * k + f) * bpr;
                int r = f ? (v2 ? r2 : v1 ? r1 : -1) : (v1 ? r1 : v2 ? r2 : -1);   /* a line it lacks: the other field's */
                if (r >= 0) memcpy(out, rows + (size_t)r * FP_LINE_BYTES, FP_LINE_BYTES);
                else for (unsigned x = 0; x < FP_LINE_BYTES; x += 2){ out[x] = 128; out[x + 1] = 16; }
            }
        }
    } else {
        /* One field (a unit framed at field rate, or one cut short): its rows in field 1's aperture, as a whole unit's
         * field 1 is placed, each line shown twice, the line between two of its lines their average (a bob). Stretching
         * its whole raster over 480 rows showed its padding and vertical interval as picture (2026-11-15). A line it
         * lacks is black. Units the Shuttle framed by field can carry fewer vertical-interval rows than a whole unit (0
         * to 11 measured, against 10), so their picture may sit a few lines off; only their picture would say how far. */
        for (int k = 0; k < FP_FIELD_LINES; k++){
            int r = FP_FIELD1_START + d1 + k, v = r >= 0 && (unsigned)r < n_lines, vn = v && (unsigned)(r + 1) < n_lines && k + 1 < FP_FIELD_LINES;
            uint8_t *o0 = dst + (size_t)(2 * k) * bpr, *o1 = dst + (size_t)(2 * k + 1) * bpr;
            if (!v){ for (unsigned x = 0; x < FP_LINE_BYTES; x += 2){ o0[x] = o1[x] = 128; o0[x + 1] = o1[x + 1] = 16; } continue; }
            const uint8_t *a = rows + (size_t)r * FP_LINE_BYTES, *b = vn ? a + FP_LINE_BYTES : a;
            memcpy(o0, a, FP_LINE_BYTES);
            for (unsigned x = 0; x < FP_LINE_BYTES; x++) o1[x] = (uint8_t)((a[x] + b[x] + 1) / 2);
        }
    }
    IOSurfaceUnlock(s, 0, NULL);
    fp_frame f = { s, counter_ext * 1001u, 30000u, counter_ext, 0, 0, FP_TRANSPORT_SHORT, (uint8_t)(audio_pts_known != 0), audio_pts_num, 0 };
    p->st.published++;
    p->sink.on_frame(p->sink.ctx, &f);
    return 0;
}
int fp_publish(fp_publisher *p,const uint8_t *u,size_t n,uint64_t c,int d1,int d2,uint8_t tr,int known,uint64_t pts){
    return publish(p,u,n,c,d1,d2,tr,known,pts,0);
}
int fp_publish_placed(fp_publisher *p,const uint8_t *u,size_t n,uint64_t c,int d1,int d2,uint8_t tr,int known,uint64_t pts){
    return publish(p,u,n,c,d1,d2,tr,known,pts,1);
}

void fp_get_stats(const fp_publisher *p, fp_stats *o){ *o = p->st; }

void fp_close(fp_publisher *p){
    if (!p) return;
    for (unsigned i = 0; i < p->n; i++) if (p->pool[i]) CFRelease(p->pool[i]);
    free(p->pool); free(p);
}
