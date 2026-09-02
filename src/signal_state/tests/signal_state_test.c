#define _POSIX_C_SOURCE 200809L

#include "signal_state.h"

#include <assert.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

enum { UNIT_BYTES = 756048, HEADER = 48, BPL = 1440, LINES = 525 };

typedef enum pattern {
    PATTERN_PROGRAM,
    PATTERN_SNOW,
    PATTERN_GRAY,
    PATTERN_SUBBLACK,
    PATTERN_FLAT_CHROMA,
} pattern;

static uint32_t random_state = 1;

static uint8_t random_byte(void)
{
    random_state ^= random_state << 13;
    random_state ^= random_state >> 17;
    random_state ^= random_state << 5;
    return (uint8_t)random_state;
}

static bool hard_line(int line)
{
    return line <= 6 || (line >= 261 && line <= 269) || line >= 523;
}

static bool picture_line(int line)
{
    return (line >= 20 && line <= 256) || (line >= 282 && line <= 518);
}

static void make_unit(uint8_t *unit, pattern kind, unsigned frame, uint8_t gray)
{
    memset(unit, 0, UNIT_BYTES);
    unit[2] = unit[3] = 0xff;
    unit[4] = (uint8_t)frame;
    unit[5] = (uint8_t)(frame >> 8);
    unit[6] = 0x01;
    unit[7] = 0xe8;
    for (int line = 0; line < LINES; ++line) {
        uint8_t *row = unit + HEADER + (size_t)line * BPL;
        for (int x = 0; x < 720; ++x) {
            uint8_t y = 2, c = 128;
            if (hard_line(line)) {
                y = 16;
            } else if (line == 16 || line == 17 || line == 279 || line == 280) {
                y = ((x / 6 + line) & 1) ? 210 : 8;
            } else if (picture_line(line)) {
                switch (kind) {
                case PATTERN_PROGRAM:
                    y = (uint8_t)(72 + (((x / 16) + (line / 9) + frame) % 7) * 12);
                    c = (uint8_t)(112 + (((x / 24) + line) % 5) * 8);
                    break;
                case PATTERN_SNOW:
                    y = random_byte();
                    c = random_byte();
                    break;
                case PATTERN_GRAY:
                    y = gray;
                    if ((frame & 1) && line >= 40 && line <= 55 &&
                        x >= 500 && x <= 650)
                        y = ((x / 5 + line) & 1) ? 210 : gray;
                    break;
                case PATTERN_SUBBLACK:
                    y = 2;
                    break;
                case PATTERN_FLAT_CHROMA:
                    y = 50;
                    c = 80;
                    break;
                }
            }
            row[x * 2] = c;
            row[x * 2 + 1] = y;
        }
    }
}

static unit_video_observation observation(const uint8_t *unit, uint64_t ordinal)
{
    unit_video_observation value = {
        .epoch = 1,
        .ordinal = ordinal,
        .counter16 = (uint16_t)ordinal,
        .counter_extended = ordinal,
        .format = 0xe801,
        .kind = UNIT_VIDEO_E801,
        .transport = UNIT_TRANSPORT_COMPLETE,
        .bytes = unit,
        .byte_count = UNIT_BYTES,
        .payload = unit + HEADER,
        .payload_bytes = UNIT_BYTES - HEADER,
        .fixed_raster_eligible = true,
    };
    return value;
}

static signal_result classify(signal_state *state, uint8_t *unit, pattern kind,
                              unsigned frame, uint8_t gray)
{
    make_unit(unit, kind, frame, gray);
    unit_video_observation input = observation(unit, frame);
    signal_result result;
    assert(signal_state_classify(state, &input, NULL, &result));
    return result;
}

static uint64_t monotonic_ns(void)
{
    struct timespec value;
    assert(clock_gettime(CLOCK_MONOTONIC, &value) == 0);
    return (uint64_t)value.tv_sec * UINT64_C(1000000000) + value.tv_nsec;
}

int main(void)
{
    signal_state *state = aligned_alloc(signal_state_alignment(), signal_state_size());
    uint8_t *unit = malloc(UNIT_BYTES);
    assert(state && unit);
    signal_state_config config = signal_state_default_config();
    config.settle_confirm_units = 8;
    config.phase_chatter_window_units = 10;
    config.phase_chatter_threshold = 4;
    signal_state_init(state, &config);
    signal_state_begin_epoch(state, 1);

    uint32_t begin_actions = 0;
    signal_result result = {0};
    for (unsigned i = 0; i < 6; ++i) {
        result = classify(state, unit, PATTERN_PROGRAM, i, 0);
        begin_actions += !!(result.actions & SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT);
        signal_state_note_registration(state, &result, true, 0, 0, 1.0);
        assert(result.appearance == SIGNAL_APPEARANCE_PROGRAM_LIKE);
    }
    assert(result.source == SIGNAL_SOURCE_PRESENT);
    assert(begin_actions == 1);

    /* Property sweep: neutral gray level changes the parameter, not the label. */
    for (uint8_t gray = 32; gray <= 192; gray += 32) {
        result = classify(state, unit, PATTERN_GRAY, 100 + gray, gray);
        assert(result.appearance == SIGNAL_APPEARANCE_NEUTRAL_GRAY_MUTE_LIKE);
    }
    assert(result.source == SIGNAL_SOURCE_MUTED);
    result = classify(state, unit, PATTERN_GRAY, 133, 120);
    result = classify(state, unit, PATTERN_GRAY, 135, 120);
    assert(result.appearance == SIGNAL_APPEARANCE_NEUTRAL_GRAY_MUTE_LIKE);

    for (unsigned i = 0; i < 4; ++i) {
        result = classify(state, unit, PATTERN_SUBBLACK, 400 + i, 0);
        assert(result.appearance == SIGNAL_APPEARANCE_SUBBLACK_MUTE_LIKE);
    }
    assert(result.source == SIGNAL_SOURCE_MUTED);

    uint32_t reacquire_actions = 0;
    for (unsigned i = 0; i < 5; ++i) {
        random_state = 0x12345678u + i;
        result = classify(state, unit, PATTERN_SNOW, 500 + i, 0);
        assert(result.appearance == SIGNAL_APPEARANCE_SNOW_LIKE);
        reacquire_actions += !!(result.actions & SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT);
    }
    assert(result.source == SIGNAL_SOURCE_REACQUIRING);
    assert(reacquire_actions == 1);
    assert(result.unsettled);

    for (unsigned i = 0; i < 12; ++i) {
        result = classify(state, unit, PATTERN_PROGRAM, 600 + i, 0);
        signal_state_note_registration(state, &result, true, 0, 0, 1.0);
    }
    assert(result.source == SIGNAL_SOURCE_PRESENT);
    assert(!result.unsettled);
    assert(result.settled_phase_known);

    result = classify(state, unit, PATTERN_FLAT_CHROMA, 700, 0);
    assert(result.appearance == SIGNAL_APPEARANCE_FLAT_AMBIGUOUS);

    unit_video_observation no_signal = {
        .epoch = 1,
        .ordinal = 701,
        .format = 0x0800,
        .kind = UNIT_VIDEO_DEVICE_NO_SIGNAL_0800,
        .transport = UNIT_TRANSPORT_COMPLETE,
    };
    assert(signal_state_classify(state, &no_signal, NULL, &result));
    assert(result.appearance == SIGNAL_APPEARANCE_DEVICE_NO_SIGNAL_0800);

    unit_video_observation hole = {
        .epoch = 1,
        .ordinal = 702,
        .kind = UNIT_VIDEO_E801,
        .transport = UNIT_TRANSPORT_HOLE,
        .transport_flags = UNIT_FLAG_HOST_LOSS,
    };
    assert(signal_state_classify(state, &hole, NULL, &result));
    assert(result.actions & SIGNAL_ACTION_REGISTRATION_DISCONTINUITY);
    assert(result.unsettled);

    /* Four phase changes inside ten units open a classifier interval. */
    signal_state_commit_registration(state, 0, 0);
    for (unsigned i = 0; i < 6; ++i) {
        result = classify(state, unit, PATTERN_PROGRAM, 800 + i, 0);
        signal_state_note_registration(state, &result, true,
                                       (int8_t)(i & 1), 0, 1.0);
    }
    assert(result.unsettled);
    uint64_t chatter_interval = result.unsettled_interval_id;
    assert(chatter_interval != 0);

    signal_state_commit_registration(state, 1, 0);
    for (unsigned i = 0; i < 12; ++i) {
        result = classify(state, unit, PATTERN_PROGRAM, 900 + i, 0);
        signal_state_note_registration(state, &result, true, 1, 0, 1.0);
    }
    assert(!result.unsettled);
    assert(result.settled_phase_known && result.settled_d1 == 1 &&
           result.settled_d2 == 0);

    uint64_t begin = monotonic_ns();
    for (unsigned i = 0; i < 100; ++i)
        result = classify(state, unit, PATTERN_PROGRAM, 1000 + i, 0);
    uint64_t elapsed = monotonic_ns() - begin;
    double microseconds = elapsed / 1000.0 / 100.0;
    printf("signal_state_test: PASS cost=%.3f us/unit interval=%" PRIu64 "\n",
           microseconds, chatter_interval);
#ifndef SIGNAL_STATE_SANITIZED
    assert(microseconds < 5000.0);
#endif
    free(unit);
    free(state);
    return 0;
}
