#ifndef SHUTTLE_FRAME_LEVELS_H
#define SHUTTLE_FRAME_LEVELS_H
#include <stdint.h>
#include <stddef.h>

/* The published 8-bit UYVY frame goes to OBS as I210 (planar 4:2:2, 10-bit in 16-bit LE words),
 * each code c carried as exactly 4c: 16 -> 64, 235 -> 940, levels unchanged.
 *
 * Why not UYVY: libobs converts an async UYVY frame into a GS_BGRX texture (8-bit unorm,
 * obs-internal.h convert_video_format), so sub-black (< 16) and super-white (> 235) become
 * RGB outside 0..1 and are cut the moment they are written, whatever the shader's range clamp.
 * I210 gets a GS_RGBA16F texture, where they survive; the caller also opens the range clamp
 * (color_range_min/max 0..1) so the conversion shader does not clip them first. The matrix
 * stays OBS's own Rec.601 limited-range one for I210: nothing is remapped.
 *
 * y: width x height words; u, v: width/2 x height words each. src rows are src_stride bytes. */
static inline void shuttle_uyvy_to_i210(const uint8_t *src, size_t src_stride, unsigned width, unsigned height,
                                        uint16_t *y, uint16_t *u, uint16_t *v) {
    for (unsigned r = 0; r < height; r++) {
        const uint8_t *s = src + (size_t)r * src_stride;
        uint16_t *yr = y + (size_t)r * width, *ur = u + (size_t)r * (width / 2), *vr = v + (size_t)r * (width / 2);
        for (unsigned x = 0; x < width / 2; x++, s += 4) {
            ur[x] = (uint16_t)(s[0] << 2);
            yr[2 * x] = (uint16_t)(s[1] << 2);
            vr[x] = (uint16_t)(s[2] << 2);
            yr[2 * x + 1] = (uint16_t)(s[3] << 2);
        }
    }
}
#endif
