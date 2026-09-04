#include "../cea608.h"

#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint8_t with_odd_parity(uint8_t value)
{
    value &= 0x7f;
    return (__builtin_popcount((unsigned)value) & 1) ? value : value | 0x80;
}

static void synth(uint8_t row[720], uint8_t b1, uint8_t b2, int valid)
{
    const double cell = 1.986e-6 * 13.5e6;
    const double pi = 3.14159265358979323846;
    const double phase = 20.0;
    memset(row, 2, 720);
    b1 = valid ? with_odd_parity(b1) : (b1 & 0x7f);
    b2 = valid ? with_odd_parity(b2) : (b2 & 0x7f);
    uint8_t bits[26] = {1,1,1,1,1,1,1,0,0,1};
    for (int i = 0; i < 8; ++i) {
        bits[10 + i] = (b1 >> i) & 1;
        bits[18 + i] = (b2 >> i) & 1;
    }
    for (int i = 0; i < 26; ++i) {
        int lo = (int)lround(phase + (i - 0.5) * cell);
        int hi = (int)lround(phase + (i + 0.5) * cell);
        if (lo < 0) lo = 0;
        if (hi > 720) hi = 720;
        for (int x = lo; x < hi; ++x) {
            if (i < 7) {
                long y = lround(90.0 + 70.0 * cos(2.0 * pi *
                                (x - phase - i * cell) / cell));
                row[x] = (uint8_t)(y < 2 ? 2 : (y > 235 ? 235 : y));
            } else row[x] = bits[i] ? 150 : 20;
        }
    }
}

int main(void)
{
    uint8_t row[720];
    cea608_decode_result r;
    synth(row, 0x14, 0x2c, 1);
    cea608_decode_luma(row, &r);
    assert(r.run_in_present && r.framing_present && r.parity_valid);
    assert(r.byte1 == with_odd_parity(0x14));
    assert(r.byte2 == with_odd_parity(0x2c));
    assert(r.run_length == 7 && r.amplitude >= 35.0);
    synth(row, 0x14, 0x2c, 0);
    cea608_decode_luma(row, &r);
    assert(r.run_in_present && r.framing_present && !r.parity_valid);
    memset(row, 16, sizeof row);
    cea608_decode_luma(row, &r);
    assert(!r.run_in_present && !r.parity_valid);
    puts("CEA608-UNIT: 3/3");
    return 0;
}
