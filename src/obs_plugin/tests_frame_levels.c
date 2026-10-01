#include "frame_levels.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

/* Every 8-bit code, in every UYVY byte position, arrives as exactly 4c in the right plane and
 * sample, including 0..15 and 236..255 (the codes the old UYVY path clipped), with a padded
 * source stride. */
int main(void) {
    enum { W = 512, H = 3, STRIDE = W * 2 + 32 };
    static uint8_t src[STRIDE * H]; static uint16_t y[W * H], u[W / 2 * H], v[W / 2 * H];
    memset(src, 0xEE, sizeof src);
    for (unsigned r = 0; r < H; r++)
        for (unsigned x = 0; x < W / 2; x++) {
            uint8_t *p = src + r * STRIDE + 4 * x;
            p[0] = (uint8_t)(x + r); p[1] = (uint8_t)(2 * x + r); p[2] = (uint8_t)(255 - x - r); p[3] = (uint8_t)(2 * x + 1 + r);
        }
    shuttle_uyvy_to_i210(src, STRIDE, W, H, y, u, v);
    for (unsigned r = 0; r < H; r++)
        for (unsigned x = 0; x < W / 2; x++) {
            assert(u[r * W / 2 + x] == 4 * (uint8_t)(x + r));
            assert(v[r * W / 2 + x] == 4 * (uint8_t)(255 - x - r));
            assert(y[r * W + 2 * x] == 4 * (uint8_t)(2 * x + r));
            assert(y[r * W + 2 * x + 1] == 4 * (uint8_t)(2 * x + 1 + r));
        }
    int seen[256] = {0};   /* coverage: all 256 codes exercised through the luma path */
    for (unsigned i = 0; i < W * H; i++) seen[y[i] >> 2] = 1;
    for (int c = 0; c < 256; c++) assert(seen[c]);
    assert(y[0] == 0 && y[255] == 1020);
    puts("frame_levels: every code in every position carried as 4c");
    return 0;
}
