/* One device counter value must map to one extended value on both streams.
 *
 * Scenario 1, the 2026-10-02 failure: between formed units the video stream is junk (deck stopped) that happens
 * to hold a marker with a plausible format and a wild counter. Nothing follows it with counter + 1, so the parser
 * emits it when its buffer fills. That unit must not move the video extension; before the fix it did
 * (101 -> 30000, then 105 -> 30001) while the audio counter ran on, and no later video unit found its audio.
 *
 * Scenario 2: the device restarts its counter backward on both streams, and one more resync of the old numbering
 * reaches the audio stream than units reach the video stream. Each stream's forward-only extension counts its own
 * steps, so they end apart for good. Required: once the first complete unit of the new numbering has been seen
 * the two agree, and the resync that moves says the numbering jumped (its own counter stepped by one), not time. */
#include "unit_parser.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { UNIT = UNIT_PARSER_VIDEO_UNIT_BYTES, PACKET = 15360, PCM_PER_UNIT = 1601 };

typedef struct {
    uint64_t video_ext[65536], audio_ext[65536];
    uint32_t audio_flags[65536];
    int video_seen[65536], audio_seen[65536];
} seen;

static void on_video(void *context, const unit_video_observation *unit)
{
    seen *s = context;
    if (unit->transport != UNIT_TRANSPORT_COMPLETE) return;
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

static void feed_video_unit(unit_parser *parser, uint8_t *unit, uint16_t counter)
{
    memset(unit, 0, UNIT);
    unit[2] = unit[3] = 0xff;
    unit[4] = (uint8_t)counter; unit[5] = (uint8_t)(counter >> 8);
    unit[6] = 0x01; unit[7] = 0xe8;
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
enum { MOVED = UNIT_FLAG_COUNTER_RENUMBERED | UNIT_FLAG_COUNTER_DISCONTINUITY };

int main(void)
{
    seen *s = malloc(sizeof *s);
    uint8_t *unit = malloc(UNIT + 100);
    assert(s && unit);
    int failures = 0;

    /* 1: junk with a false marker between formed units; the audio counter runs on through it */
    unit_parser *parser = open_parser(s);
    for (uint16_t c = 100; c <= 101; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, c); }
    feed_junk_with_false_marker(parser, unit, 30000, 4);
    for (uint16_t c = 102; c <= 104; c++) feed_audio_unit(parser, c);
    for (uint16_t c = 105; c <= 109; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, c); }
    unit_parser_finish(parser); free(parser);
    CHECK(!s->video_seen[30000] || s->video_ext[30000] == 0, "the junk marker's unit carries an extended counter (%llu)", U(s->video_ext[30000]));
    CHECK(s->video_seen[105] && s->video_ext[105] == 105, "junk marker moved the video extension: 105 -> %llu", U(s->video_ext[105]));
    for (uint16_t c = 105; c <= 108; c++)
        CHECK(s->audio_seen[c] && s->video_seen[c] && s->audio_ext[c] == s->video_ext[c],
              "after junk, counter %u: audio extended %llu, video extended %llu", c, U(s->audio_ext[c]), U(s->video_ext[c]));
    for (uint16_t c = 100; c <= 109; c++)
        CHECK(!(s->audio_flags[c] & MOVED), "after junk, resync %u flagged (0x%x): its numbering never jumped", c, s->audio_flags[c]);

    /* 2: backward restart on both streams, one more old-numbering resync on the audio side */
    parser = open_parser(s);
    for (uint16_t c = 100; c <= 101; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, c); }
    feed_audio_unit(parser, 102);
    for (uint16_t c = 50; c <= 55; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, c); }
    unit_parser_finish(parser); free(parser);
    /* The parser frames a restart by giving up the unit before it and the first one after it (neither has a
     * successor with counter + 1 where one is due), so the first complete unit of the new numbering is 51. */
    CHECK(s->video_seen[51] && s->video_ext[51] == 101 && s->video_ext[53] == 103,
          "video extension across a backward restart: 51 -> %llu, 53 -> %llu", U(s->video_ext[51]), U(s->video_ext[53]));
    for (uint16_t c = 52; c <= 54; c++)
        CHECK(s->audio_seen[c] && s->video_seen[c] && s->audio_ext[c] == s->video_ext[c],
              "after a restart, counter %u: audio extended %llu, video extended %llu", c, U(s->audio_ext[c]), U(s->video_ext[c]));
    CHECK(s->audio_flags[52] & UNIT_FLAG_COUNTER_RENUMBERED, "resync 52 (own counter +1, extended value moved) not marked renumbered (0x%x)", s->audio_flags[52]);
    CHECK(!(s->audio_flags[50] & UNIT_FLAG_COUNTER_RENUMBERED) && (s->audio_flags[50] & UNIT_FLAG_COUNTER_DISCONTINUITY),
          "resync 50 (own counter went back) must be a discontinuity, not a renumbering (0x%x)", s->audio_flags[50]);
    for (uint16_t c = 53; c <= 55; c++)
        CHECK(!(s->audio_flags[c] & MOVED), "after a restart, resync %u flagged (0x%x) once the numbering settled", c, s->audio_flags[c]);

    free(unit); free(s);
    if (failures) return 1;
    puts("counter_excursion_test: PASS");
    return 0;
}
