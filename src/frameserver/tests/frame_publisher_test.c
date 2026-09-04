// Synthetic tests: crop geometry under (d1,d2), clamping at the raster edges, PTS
// monotonicity, honest pool exhaustion, and that the IOSurface carries the assembled rows.
#include "../frame_publisher.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { fails++; fprintf(stderr, "FAIL: " __VA_ARGS__); fprintf(stderr, "\n"); } } while (0)

// unit whose every source line L is filled with byte value (L & 0xFF) — geometry is readable
static uint8_t *make_unit(void){
    uint8_t *u = malloc(FP_UNIT_BYTES); memset(u, 0, FP_UNIT_HEADER);
    for (unsigned L = 0; L < FP_SOURCE_LINES; L++) memset(u + FP_UNIT_HEADER + L * FP_LINE_BYTES, (int)(L & 0xFF), FP_LINE_BYTES);
    return u;
}
static int row_src_line(const uint8_t *frame, int row){ return frame[(size_t)row * FP_LINE_BYTES]; }

typedef struct { int frames; uint64_t last_pts, last_counter; int pts_monotonic; IOSurfaceRef held; int hold; } sink_ctx;
static void on_frame(void *ctx, const fp_frame *f){
    sink_ctx *c = ctx; c->frames++;
    if (c->frames > 1 && f->pts_num <= c->last_pts) c->pts_monotonic = 0;
    c->last_pts = f->pts_num;
    c->last_counter = f->counter_ext;
    if (c->hold){ IOSurfaceIncrementUseCount(f->surface); c->held = f->surface; }
}

int main(void){
    uint8_t *u = make_unit();
    uint8_t *frame = malloc(FP_FRAME_HEIGHT * FP_LINE_BYTES);

    // nominal crop (SMPTE RP-202): row 0 = line 19 (standard line 23), row 1 = line 282 (line 286), row 2 = 20, row 479 = 521
    fp_assemble(frame, u, 0, 0);
    CHECK(row_src_line(frame, 0) == 19 && row_src_line(frame, 1) == (282 & 0xFF), "nominal rows");
    CHECK(row_src_line(frame, 2) == 20 && row_src_line(frame, 479) == (521 & 0xFF), "nominal tail rows");
    // field-1 displaced +2: field 1 reads from 21.., field 2 unchanged (§7 correction direction)
    fp_assemble(frame, u, 2, 0);
    CHECK(row_src_line(frame, 0) == 21 && row_src_line(frame, 1) == (282 & 0xFF), "d1=+2 moves only field 1");
    // negative d2 and clamping: d2=-300 must clamp so field 2 stays inside the raster
    fp_assemble(frame, u, 0, -300);
    CHECK(row_src_line(frame, 1) == 0, "d2 clamped to raster start (line 0)");
    fp_assemble(frame, u, 0, 300);
    CHECK(row_src_line(frame, 1) == ((525 - 240) & 0xFF), "d2 clamped to raster end");

    // publisher: pool of 2, consumer holds nothing -> everything publishes, PTS monotonic
    sink_ctx c = {0}; c.pts_monotonic = 1;
    fp_sink s = { on_frame, &c };
    fp_publisher *p = NULL;
    CHECK(fp_open(&p, 2, &s) == 0 && p, "open");
    for (uint32_t i = 0; i < 10; i++) CHECK(fp_publish(p, u, FP_UNIT_BYTES, 1000 + i, 1, 0, FP_TRANSPORT_COMPLETE, 0, 0) == 0, "publish %u", i);
    CHECK(c.frames == 10 && c.pts_monotonic, "10 frames, monotonic PTS");
    CHECK(fp_publish(p,u,FP_UNIT_BYTES,(uint64_t)UINT32_MAX+1,0,0,FP_TRANSPORT_COMPLETE,0,0)==0,
          "publish counter beyond 32-bit");
    CHECK(c.last_counter==(uint64_t)UINT32_MAX+1 && c.last_pts==((uint64_t)UINT32_MAX+1)*1001,
          "64-bit counter/PTS narrowed (%llu/%llu)",(unsigned long long)c.last_counter,
          (unsigned long long)c.last_pts);
    // surface content: row 0 must be source line 18 (d1=1)
    {
        IOSurfaceRef last = p ? NULL : NULL; (void)last;
        fp_stats st; fp_get_stats(p, &st);
        CHECK(st.published == 11 && st.dropped_no_free_surface == 0, "stats after publishes");
    }
    // honest exhaustion: consumer holds both surfaces -> third publish is DROPPED and counted
    c.hold = 1;
    IOSurfaceRef h1 = NULL, h2 = NULL;
    fp_publish(p, u, FP_UNIT_BYTES, 2000, 0, 0, FP_TRANSPORT_COMPLETE, 0, 0); h1 = c.held;
    fp_publish(p, u, FP_UNIT_BYTES, 2001, 0, 0, FP_TRANSPORT_COMPLETE, 0, 0); h2 = c.held;
    c.hold = 0;
    int rc = fp_publish(p, u, FP_UNIT_BYTES, 2002, 0, 0, FP_TRANSPORT_COMPLETE, 0, 0);
    fp_stats st; fp_get_stats(p, &st);
    CHECK(rc == 1 && st.dropped_no_free_surface == 1 && st.pool_in_use == 2, "drop when pool exhausted (rc=%d dropped=%llu in_use=%u)", rc, (unsigned long long)st.dropped_no_free_surface, st.pool_in_use);
    // held surface carries the assembled rows
    IOSurfaceLock(h1, kIOSurfaceLockReadOnly, NULL);
    CHECK(((uint8_t *)IOSurfaceGetBaseAddress(h1))[0] == 19, "surface row 0 is source line 19 (standard line 23)");
    IOSurfaceUnlock(h1, kIOSurfaceLockReadOnly, NULL);
    // release -> publishing resumes
    IOSurfaceDecrementUseCount(h1); IOSurfaceDecrementUseCount(h2);
    CHECK(fp_publish(p, u, FP_UNIT_BYTES, 2003, 0, 0, FP_TRANSPORT_COMPLETE, 0, 0) == 0, "publish after release");
    // bad args are rejected, not guessed
    CHECK(fp_publish(p, u, FP_UNIT_BYTES - 1, 3000, 0, 0, 0, 0, 0) == -1, "short unit rejected");
    fp_close(p); free(u); free(frame);
    printf(fails ? "FAILURES: %d\n" : "frame_publisher tests: PASS\n", fails);
    return fails ? 1 : 0;
}
