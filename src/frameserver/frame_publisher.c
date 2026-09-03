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

int fp_publish(fp_publisher *p, const uint8_t *unit, size_t unit_len,
               uint64_t counter_ext, int d1, int d2, uint8_t transport){
    if (!p || !unit || unit_len != FP_UNIT_BYTES){ if (p) p->st.rejected_bad_args++; return -1; }
    IOSurfaceRef s = NULL;
    unsigned in_use = 0;
    for (unsigned i = 0; i < p->n; i++){
        if (IOSurfaceGetUseCount(p->pool[i]) == 0){ if (!s) s = p->pool[i]; }
        else in_use++;
    }
    p->st.pool_in_use = in_use;
    if (!s){ p->st.dropped_no_free_surface++; return 1; }
    IOSurfaceLock(s, 0, NULL);
    fp_assemble((uint8_t *)IOSurfaceGetBaseAddress(s), unit, d1, d2);
    IOSurfaceUnlock(s, 0, NULL);
    fp_frame f = { s, counter_ext * 1001u, 30000u, counter_ext,
                   (int8_t)clamp_offset(FP_FIELD1_START, d1), (int8_t)clamp_offset(FP_FIELD2_START, d2), transport };
    p->st.published++;
    p->sink.on_frame(p->sink.ctx, &f);
    return 0;
}

void fp_get_stats(const fp_publisher *p, fp_stats *o){ *o = p->st; }

void fp_close(fp_publisher *p){
    if (!p) return;
    for (unsigned i = 0; i < p->n; i++) if (p->pool[i]) CFRelease(p->pool[i]);
    free(p->pool); free(p);
}
