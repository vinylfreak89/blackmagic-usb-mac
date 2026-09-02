#include "unit_parser.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { CAP1_DATA = 0, CAP1_HOSTLOSS = 1, CAP1_XFERERR = 2 };

typedef struct test_state {
    uint64_t video_complete;
    uint64_t video_short;
    uint64_t video_hole;
    uint64_t video_unframed;
    uint64_t pcm;
    uint64_t resync;
    uint64_t audio_hole;
    uint64_t audio_unframed;
    uint64_t last_video_extended;
    uint64_t last_audio_extended;
    bool saw_split_first;
    bool saw_wrap_video;
    bool saw_wrap_audio;
} test_state;

static uint32_t load_u32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static uint16_t load_u16(const uint8_t *p)
{
    return (uint16_t)p[0] | (uint16_t)p[1] << 8;
}

static void on_video(void *context, const unit_video_observation *unit)
{
    test_state *state = context;
    if (unit->transport == UNIT_TRANSPORT_COMPLETE) {
        ++state->video_complete;
        assert(unit->fixed_raster_eligible);
        if (unit->counter16 == 65534)
            state->saw_split_first = true;
    } else if (unit->transport == UNIT_TRANSPORT_SHORT) {
        ++state->video_short;
        assert(!unit->fixed_raster_eligible);
    } else if (unit->transport == UNIT_TRANSPORT_HOLE) {
        ++state->video_hole;
        assert(!unit->fixed_raster_eligible);
    } else {
        ++state->video_unframed;
    }
    if (unit->kind == UNIT_VIDEO_E801) {
        if (unit->counter16 == 0 && unit->counter_extended == 65536)
            state->saw_wrap_video = true;
        state->last_video_extended = unit->counter_extended;
    }
}

static void on_audio(void *context, const unit_audio_observation *record)
{
    test_state *state = context;
    if (record->kind == UNIT_AUDIO_PCM) {
        assert(record->sample_ordinal == state->pcm);
        ++state->pcm;
    } else if (record->kind == UNIT_AUDIO_RESYNC) {
        ++state->resync;
        if (record->counter16 == 0 && record->counter_extended == 65536)
            state->saw_wrap_audio = true;
        state->last_audio_extended = record->counter_extended;
    } else if (record->kind == UNIT_AUDIO_HOLE) {
        ++state->audio_hole;
    } else {
        ++state->audio_unframed;
    }
}

static void feed_capture(unit_parser *parser, const char *path)
{
    FILE *input = fopen(path, "rb");
    assert(input);
    uint8_t header[24];
    while (fread(header, sizeof(header), 1, input) == 1) {
        assert(load_u32(header) == 0x31504143u);
        uint8_t type = header[4];
        uint8_t endpoint = header[5];
        uint16_t packet_index = load_u16(header + 6);
        uint32_t submit_seq = load_u32(header + 8);
        uint32_t status = load_u32(header + 12);
        uint32_t requested = load_u32(header + 16);
        uint32_t actual = load_u32(header + 20);
        uint8_t *payload = actual ? malloc(actual) : NULL;
        assert(!actual || payload);
        if (actual)
            assert(fread(payload, actual, 1, input) == 1);
        if (type == CAP1_DATA) {
            cc_packet packet = {
                .endpoint = endpoint,
                .pkt_index = packet_index,
                .submit_seq = submit_seq,
                .status = status,
                .req_len = requested,
                .actual_len = actual,
                .data = payload,
            };
            unit_parser_on_packet(parser, &packet);
        } else if (type == CAP1_HOSTLOSS) {
            unit_parser_on_loss(parser, endpoint, requested, actual);
        } else if (type == CAP1_XFERERR) {
            unit_parser_on_error(parser, endpoint, submit_seq, (int)status, 0);
        }
        free(payload);
    }
    assert(feof(input));
    fclose(input);
}

int main(int argc, char **argv)
{
    assert(argc == 2);
    size_t size = unit_parser_size();
    unit_parser *parser = aligned_alloc(unit_parser_alignment(), size);
    assert(parser);
    test_state state = {0};
    unit_parser_callbacks callbacks = {
        .on_video = on_video,
        .on_audio = on_audio,
        .context = &state,
    };
    unit_parser_init(parser, NULL, &callbacks);
    unit_parser_begin_epoch(parser, 7);
    feed_capture(parser, argv[1]);
    unit_parser_finish(parser);

    assert(state.saw_split_first);
    assert(state.saw_wrap_video);
    assert(state.saw_wrap_audio);
    assert(state.video_complete == 2);
    assert(state.video_short == 1);
    assert(state.video_hole == 1);
    assert(state.video_unframed == 2);
    assert(state.pcm == 37);
    assert(state.resync == 3);
    assert(state.audio_hole >= 1);
    assert(state.audio_unframed == 2);
    assert(state.last_video_extended == 65537);
    assert(state.last_audio_extended == 65537);
    puts("unit_parser_test: PASS");
    free(parser);
    return 0;
}
