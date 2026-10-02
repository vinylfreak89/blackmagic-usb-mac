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
    uint64_t any_ext[65536]; uint32_t any_flags[65536]; int any_seen[65536];   /* every unit with a counter, short ones too */
} seen;

static void on_video(void *context, const unit_video_observation *unit)
{
    seen *s = context;
    if (unit->transport == UNIT_TRANSPORT_COMPLETE || unit->transport == UNIT_TRANSPORT_SHORT) {
        s->any_ext[unit->counter16] = unit->counter_extended;
        s->any_flags[unit->counter16] = unit->transport_flags;
        s->any_seen[unit->counter16] = 1;
    }
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

/* a picture unit of header size only: framed and confirmed by its successor like any other, so it is numbered */
static void feed_short_unit(unit_parser *parser, uint16_t counter)
{
    uint8_t h[UNIT_PARSER_VIDEO_HEADER_BYTES] = {0};
    h[2] = h[3] = 0xff; h[4] = (uint8_t)counter; h[5] = (uint8_t)(counter >> 8); h[6] = 0x01; h[7] = 0xe8;
    for (size_t i = 8; i + 1 < sizeof h; i += 2) { h[i] = 128; h[i + 1] = 16; }
    feed(parser, CC_EP_VIDEO, h, sizeof h, &video_seq);
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

    /* 5: arrival skew. A unit is emitted when the next marker arrives, by which time the resync with its counter,
     * and often later ones, have been seen; or the audio may be behind. The unit's own counter decides, not the
     * audio position. */
    parser = open_parser(s);
    for (uint16_t c = 200; c <= 203; c++) feed_audio_unit(parser, c);                   /* audio four ahead */
    for (uint16_t c = 200; c <= 209; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, (uint16_t)(c + 4)); }
    unit_parser_finish(parser); free(parser);
    for (uint16_t c = 200; c <= 208; c++)
        CHECK(s->video_seen[c] && s->video_ext[c] == c && s->audio_ext[c] == c, "audio ahead, counter %u: video %llu, audio %llu", c, U(s->video_ext[c]), U(s->audio_ext[c]));
    for (uint16_t c = 201; c <= 208; c++)
        CHECK(!(s->any_flags[c] & UNIT_FLAG_COUNTER_DISCONTINUITY), "audio ahead, unit %u flagged (0x%x) in an unbroken run", c, s->any_flags[c]);
    parser = open_parser(s);
    feed_audio_unit(parser, 300);
    for (uint16_t c = 300; c <= 303; c++) feed_video_unit(parser, unit, c);             /* video three ahead */
    for (uint16_t c = 304; c <= 310; c++) { feed_audio_unit(parser, (uint16_t)(c - 3)); feed_video_unit(parser, unit, c); }
    unit_parser_finish(parser); free(parser);
    for (uint16_t c = 300; c <= 309; c++)
        CHECK(s->video_seen[c] && s->video_ext[c] == c, "video ahead, counter %u: video %llu", c, U(s->video_ext[c]));

    /* 6: the 16-bit wrap, with the audio one ahead: numbering runs on through it */
    parser = open_parser(s);
    feed_audio_unit(parser, 65530);
    for (uint32_t c = 65530; c <= 65541; c++) { feed_video_unit(parser, unit, (uint16_t)c); feed_audio_unit(parser, (uint16_t)(c + 1)); }
    unit_parser_finish(parser); free(parser);
    for (uint32_t c = 65531; c <= 65540; c++)
        CHECK(s->video_seen[(uint16_t)c] && s->video_ext[(uint16_t)c] == c && !(s->any_flags[(uint16_t)c] & UNIT_FLAG_COUNTER_DISCONTINUITY),
              "across the wrap, counter %u: video %llu, flags 0x%x", (unsigned)c, U(s->video_ext[(uint16_t)c]), s->any_flags[(uint16_t)c]);
    /* ... and a session that starts on it: the first resync seen is 1, the units before it are 65534 and 65535.
     * They cannot be numbered below zero, so they keep their own value and the step down to 0 is flagged. */
    parser = open_parser(s);
    feed_video_unit(parser, unit, 65534); feed_video_unit(parser, unit, 65535);
    feed_audio_unit(parser, 1);
    for (uint16_t c = 0; c <= 4; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, (uint16_t)(c + 2)); }
    unit_parser_finish(parser); free(parser);
    CHECK(s->video_ext[65535] == 65535 && s->video_ext[0] == 0 && s->video_ext[3] == 3 && (s->any_flags[0] & UNIT_FLAG_COUNTER_DISCONTINUITY),
          "start on the wrap: 65535 -> %llu, 0 -> %llu (flags 0x%x), 3 -> %llu", U(s->video_ext[65535]), U(s->video_ext[0]), s->any_flags[0], U(s->video_ext[3]));

    /* 7: the audio stream away. For the first 0x4000 units after the last resync a unit is numbered from it; from
     * there on the video stream numbers itself, and the hand-over must not show. 40,000 units is past what a
     * 16-bit difference from the stale resync could express. */
    parser = open_parser(s);
    feed_audio_unit(parser, 40000);                       /* (from 40000, so that a wrong sign cannot be rescued by the guard against going below zero) */
    for (uint32_t c = 40000; c <= 80001; c++) feed_short_unit(parser, (uint16_t)c);
    unit_parser_finish(parser); free(parser);
    { int bad = 0; uint32_t first_bad = 0;
      for (uint32_t c = 40000; c <= 80000; c++)
          if (!(s->any_seen[(uint16_t)c] && s->any_ext[(uint16_t)c] == c && (c == 40000 || !(s->any_flags[(uint16_t)c] & UNIT_FLAG_COUNTER_DISCONTINUITY))) && !bad++) first_bad = c;
      CHECK(!bad, "without audio, %d of 40,001 units misnumbered or flagged, first %u -> %llu (flags 0x%x)", bad, first_bad, U(s->any_ext[(uint16_t)first_bad]), s->any_flags[(uint16_t)first_bad]); }
    /* ... and audio present does not start that clock: after 20,000 units with their resyncs, the video stream
     * away for 40,000 and back, units still take the audio numbering. */
    parser = open_parser(s);
    for (uint32_t c = 1000; c < 21000; c++) { feed_short_unit(parser, (uint16_t)c); feed_resync_only(parser, (uint16_t)c); }
    for (uint32_t c = 21000; c < 61000; c++) feed_resync_only(parser, (uint16_t)c);
    for (size_t i = 0; i + 1 < UNIT + 100; i += 2) { unit[i] = 128; unit[i + 1] = 16; }      /* a unit's worth of plain junk ends the old framing */
    feed(parser, CC_EP_VIDEO, unit, UNIT + 100, &video_seq);
    for (uint32_t c = 61000; c <= 61005; c++) { feed_short_unit(parser, (uint16_t)c); feed_resync_only(parser, (uint16_t)c); }
    unit_parser_finish(parser); free(parser);
    for (uint32_t c = 61001; c <= 61004; c++)
        CHECK(s->any_seen[(uint16_t)c] && s->any_ext[(uint16_t)c] == c && s->audio_ext[(uint16_t)c] == c,
              "audio never stale, counter %u: video %llu, audio %llu", (unsigned)c, U(s->any_ext[(uint16_t)c]), U(s->audio_ext[(uint16_t)c]));

    /* 8: no audio at all: the video stream numbers itself, and a junk marker's unit still does not move it */
    parser = open_parser(s);
    for (uint16_t c = 100; c <= 101; c++) feed_video_unit(parser, unit, c);
    feed_junk_with_false_marker(parser, unit, 30000, 4);
    for (uint16_t c = 105; c <= 109; c++) feed_video_unit(parser, unit, c);
    unit_parser_finish(parser); free(parser);
    CHECK(s->video_seen[106] && s->video_ext[106] == 106 && s->video_ext[108] == 108, "video only, junk marker moved the numbering: 106 -> %llu", U(s->video_ext[106]));

    /* 9: the first picture unit after a gap in the numbering says so, the ones after it do not */
    parser = open_parser(s);
    for (uint16_t c = 100; c <= 102; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, c); }
    for (uint16_t k = 0; k < 4; k++) { feed_format_unit(parser, unit, (uint16_t)(900 + k), 0x0800); feed_audio_unit(parser, (uint16_t)(103 + k)); }
    for (uint16_t c = 107; c <= 111; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, c); }
    unit_parser_finish(parser); free(parser);
    CHECK((s->any_flags[108] & UNIT_FLAG_COUNTER_DISCONTINUITY) && !(s->any_flags[109] & UNIT_FLAG_COUNTER_DISCONTINUITY) && !(s->any_flags[101] & UNIT_FLAG_COUNTER_DISCONTINUITY),
          "gap flags: 101 0x%x, 108 0x%x, 109 0x%x", s->any_flags[101], s->any_flags[108], s->any_flags[109]);

    /* 10: a new epoch starts the numbering afresh, whatever the audio stream stood at */
    parser = open_parser(s);
    for (uint16_t c = 100; c <= 102; c++) { feed_video_unit(parser, unit, c); feed_audio_unit(parser, c); }
    unit_parser_begin_epoch(parser, 2);
    for (uint16_t c = 500; c <= 503; c++) feed_video_unit(parser, unit, c);
    unit_parser_finish(parser); free(parser);
    CHECK(s->video_seen[501] && s->video_ext[500] == 500 && s->video_ext[502] == 502, "new epoch: 500 -> %llu, 502 -> %llu", U(s->video_ext[500]), U(s->video_ext[502]));

    free(unit); free(s);
    if (failures) return 1;
    puts("counter_excursion_test: PASS");
    return 0;
}
