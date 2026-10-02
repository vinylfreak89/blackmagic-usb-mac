/* One device counter value must map to one extended value on both streams.
 *
 * The device counter is the one on the audio resync records; it steps by one per unit whatever the video stream
 * is doing. These are the ways the video numbering used to leave it, each for good:
 *  1. No-signal (0x0800) units carry their own counter. Measured 2026-10-02 (deck stopped, then play): 200 of them
 *     numbered 6271..6470 while the resyncs ran 6501..6700; the picture units that followed came out 230 ahead of
 *     their audio and none of the 2,585 found it. Here: no-signal units 900..903 while the resyncs run 102..105.
 *  2. Junk that holds a marker with a plausible format and a wild counter, emitted when the buffer fills.
 *  3. The video stream away for longer than a 16-bit difference can express (40,000 units).
 *  4. A counter restart that one stream sees one step later than the other.
 * Required in each: once formed picture units are back, a unit and the resync with the same device counter carry
 * the same extended counter, and the audio numbering is never disturbed. */
#include "unit_parser.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { UNIT = UNIT_PARSER_VIDEO_UNIT_BYTES, PACKET = 15360, PCM_PER_UNIT = 1601 };

typedef struct {
    uint64_t video_ext[65536], audio_ext[65536];
    uint32_t audio_flags[65536];
    int video_seen[65536], audio_seen[65536], video_kind[65536];
} seen;

static void on_video(void *context, const unit_video_observation *unit)
{
    seen *s = context;
    if (unit->transport != UNIT_TRANSPORT_COMPLETE) return;
    s->video_kind[unit->counter16] = unit->kind;
    s->video_ext[unit->counter16] = unit->counter_extended;
    s->video_seen[unit->counter16] = 1;
}

static void on_audio(void *context, const unit_audio_observation *record)
{
    seen *s = context;
    if (record->kind != UNIT_AUDIO_RESYNC) return;
    s->audio_ext[record->counter16] = record->counter_extended;
    s->audio_flags[record->counter16] = record->transport_flags;
    s->audio_seen[record->counter16] = 1;
}

static uint32_t video_seq, audio_seq;

static void feed(unit_parser *parser, uint8_t endpoint, const uint8_t *bytes, size_t count, uint32_t *seq)
{
    for (size_t at = 0; at < count; at += PACKET) {
        uint32_t n = (uint32_t)(count - at < PACKET ? count - at : PACKET);
        cc_packet packet = { .endpoint = endpoint, .pkt_index = 0, .submit_seq = (*seq)++, .status = 0,
                             .req_len = n, .actual_len = n, .data = bytes + at };
        unit_parser_on_packet(parser, &packet);
    }
}

static void feed_format_unit(unit_parser *parser, uint8_t *unit, uint16_t counter, uint16_t format)
{
    memset(unit, 0, UNIT);
    unit[2] = unit[3] = 0xff;
    unit[4] = (uint8_t)counter; unit[5] = (uint8_t)(counter >> 8);
    unit[6] = (uint8_t)format; unit[7] = (uint8_t)(format >> 8);
    for (size_t i = UNIT_PARSER_VIDEO_HEADER_BYTES; i + 1 < UNIT; i += 2) { unit[i] = 128; unit[i + 1] = 16; }
    feed(parser, CC_EP_VIDEO, unit, UNIT, &video_seq);
}

/* junk: one unit's worth with no marker (framing is lost), then a marker with a plausible format and a wild
 * counter, followed by more junk than a unit holds */
static void feed_junk_with_false_marker(unit_parser *parser, uint8_t *unit, uint16_t wild, size_t units)
{
    for (size_t k = 0; k < units; k++) {
        for (size_t i = 0; i + 1 < UNIT; i += 2) { unit[i] = 128; unit[i + 1] = 16; }
        if (k == 1) {
            unit[0] = unit[1] = 0; unit[2] = unit[3] = 0xff;
            unit[4] = (uint8_t)wild; unit[5] = (uint8_t)(wild >> 8); unit[6] = 0x01; unit[7] = 0xe8;
        }
        feed(parser, CC_EP_VIDEO, unit, UNIT + 100, &video_seq);
    }
}

static void feed_video_unit(unit_parser *parser, uint8_t *unit, uint16_t counter)
{
    feed_format_unit(parser, unit, counter, 0xe801);
}

static void feed_resync_only(unit_parser *parser, uint16_t counter)
{
    uint8_t r[UNIT_PARSER_AUDIO_RECORD_BYTES] = {0};
    memcpy(r, "DeckLinkAudioResyncT", 20);
    r[20] = (uint8_t)counter; r[21] = (uint8_t)(counter >> 8); r[22] = 0x65; r[23] = 0x6e;
    feed(parser, CC_EP_AUDIO, r, sizeof r, &audio_seq);
}

static void feed_audio_unit(unit_parser *parser, uint16_t counter)
{
    static uint8_t audio[(PCM_PER_UNIT + 1) * UNIT_PARSER_AUDIO_RECORD_BYTES];
    memset(audio, 0, sizeof audio);
    memcpy(audio, "DeckLinkAudioResyncT", 20);
    audio[20] = (uint8_t)counter; audio[21] = (uint8_t)(counter >> 8); audio[22] = 0x65; audio[23] = 0x6e;
    for (int i = 1; i <= PCM_PER_UNIT; i++) {
        uint8_t *r = audio + (size_t)i * UNIT_PARSER_AUDIO_RECORD_BYTES;
        r[0] = (uint8_t)i; r[1] = (uint8_t)(i >> 8); r[3] = (uint8_t)-i; r[4] = (uint8_t)(-i >> 8);
    }
    feed(parser, CC_EP_AUDIO, audio, sizeof audio, &audio_seq);
}

static unit_parser *open_parser(seen *s)
{
    unit_parser *parser = aligned_alloc(unit_parser_alignment(), unit_parser_size());
    assert(parser);
    memset(s, 0, sizeof *s);
    unit_parser_callbacks callbacks = { .on_video = on_video, .on_audio = on_audio, .context = s };
    unit_parser_init(parser, NULL, &callbacks);
    unit_parser_begin_epoch(parser, 1);
    video_seq = audio_seq = 0;
    return parser;
}

#define CHECK(cond, ...) do { if (!(cond)) { printf("FAIL: " __VA_ARGS__); printf("\n"); failures++; } } while (0)
#define U(x) ((unsigned long long)(x))
#define AGREE(lo, hi, what) for (uint16_t c = (lo); c <= (hi); c++) \
    CHECK(s->audio_seen[c] && s->video_seen[c] && s->audio_ext[c] == s->video_ext[c], \
          what ", counter %u: audio extended %llu, video extended %llu", c, U(s->audio_ext[c]), U(s->video_ext[c]))
#define AUDIO_UNDISTURBED(lo, hi, what) for (uint16_t c = (lo); c <= (hi); c++) \
    CHECK(s->audio_seen[c] && s->audio_ext[c] == c && !(s->audio_flags[c] & UNIT_FLAG_COUNTER_DISCONTINUITY), \
          what ", resync %u: extended %llu, flags 0x%x", c, U(s->audio_ext[c]), s->audio_flags[c])

int main(void)
{
    seen *s = malloc(sizeof *s);
    uint8_t *unit = malloc(UNIT + 100);
    assert(s && unit);
    int failures = 0;

    /* 1: a run of no-signal units numbered on their own while the resyncs run on */
    unit_parser *parser = open_parser(s);
    for (uint16_t c = 100; c <= 101; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, c); }
    for (uint16_t k = 0; k < 4; k++) { feed_format_unit(parser, unit, (uint16_t)(900 + k), 0x0800); feed_audio_unit(parser, (uint16_t)(102 + k)); }
    for (uint16_t c = 106; c <= 110; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, c); }
    unit_parser_finish(parser); free(parser);
    CHECK(s->video_seen[107] && s->video_ext[107] == 107, "no-signal units moved the video numbering: 107 -> %llu", U(s->video_ext[107]));
    AGREE(107, 109, "after no signal");
    AUDIO_UNDISTURBED(100, 110, "through no signal");
    /* (the parser gives up the first unit after a break in the numbering, here 900 and 106) */
    for (uint16_t c = 901; c <= 902; c++)
        CHECK(s->video_seen[c] && s->video_kind[c] == UNIT_VIDEO_DEVICE_NO_SIGNAL_0800 && s->video_ext[c] >= 101 && s->video_ext[c] <= 106,
              "no-signal unit %u is placed at %llu, not at the device counter's position", c, U(s->video_ext[c]));

    /* 2: junk with a false marker between formed units; the audio counter runs on through it */
    parser = open_parser(s);
    for (uint16_t c = 100; c <= 101; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, c); }
    feed_junk_with_false_marker(parser, unit, 30000, 4);
    for (uint16_t c = 102; c <= 104; c++) feed_audio_unit(parser, c);
    for (uint16_t c = 105; c <= 109; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, c); }
    unit_parser_finish(parser); free(parser);
    CHECK(s->video_seen[105] && s->video_ext[105] == 105, "junk marker moved the video numbering: 105 -> %llu", U(s->video_ext[105]));
    AGREE(105, 108, "after junk");
    AUDIO_UNDISTURBED(100, 109, "through junk");

    /* 3: the video stream away for 40,000 units */
    parser = open_parser(s);
    for (uint16_t c = 100; c <= 101; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, c); }
    for (uint32_t c = 102; c < 40102; c++) feed_resync_only(parser, (uint16_t)c);
    for (uint16_t c = 40102; c <= 40106; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, c); }
    unit_parser_finish(parser); free(parser);
    AGREE(40103, 40105, "after a long absence");
    AUDIO_UNDISTURBED(40100, 40106, "through a long absence");

    /* 4: a backward restart, with one more resync of the old numbering on the audio side. The parser frames a
     * restart by giving up the unit before it and the first after it, so the first formed unit is 51. */
    parser = open_parser(s);
    for (uint16_t c = 100; c <= 101; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, c); }
    feed_audio_unit(parser, 102);
    for (uint16_t c = 50; c <= 55; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, c); }
    unit_parser_finish(parser); free(parser);
    AGREE(51, 54, "after a restart");
    CHECK(s->audio_ext[50] == 103 && (s->audio_flags[50] & UNIT_FLAG_COUNTER_DISCONTINUITY) && s->audio_ext[53] == 106,
          "audio numbering across a backward restart changed: 50 -> %llu (flags 0x%x), 53 -> %llu", U(s->audio_ext[50]), s->audio_flags[50], U(s->audio_ext[53]));

    free(unit); free(s);
    if (failures) return 1;
    puts("counter_excursion_test: PASS");
    return 0;
}
