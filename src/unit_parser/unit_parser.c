#include "unit_parser.h"

#include <stdalign.h>
#include <string.h>

enum {
    VIDEO_BUFFER_BYTES = UNIT_PARSER_VIDEO_UNIT_BYTES + 32,
    AUDIO_SYNC_BYTES = 20,
    TRANSPORT_HOLE_FLAGS = UNIT_FLAG_HOST_LOSS | UNIT_FLAG_TRANSFER_ERROR |
                           UNIT_FLAG_PACKET_SEQUENCE_GAP |
                           UNIT_FLAG_PACKET_STATUS,
};

static const uint8_t video_marker[4] = {0x00, 0x00, 0xff, 0xff};
static const uint8_t audio_sync[] = "DeckLinkAudioResyncT";

typedef struct endpoint_position {
    bool valid;
    uint32_t submit_seq;
    uint16_t packet_index;
} endpoint_position;

struct unit_parser {
    unit_parser_config config;
    unit_parser_callbacks callbacks;
    uint64_t epoch;
    bool finished;

    uint8_t video[VIDEO_BUFFER_BYTES];
    size_t video_bytes;
    bool video_has_marker;
    size_t video_candidate;
    bool video_candidate_valid;
    uint32_t video_flags;
    uint64_t video_ordinal;
    bool video_counter_valid;
    uint16_t video_counter16;
    uint64_t video_counter_extended;

    bool audio_phase_locked;
    uint8_t audio_record[UNIT_PARSER_AUDIO_RECORD_BYTES];
    size_t audio_record_bytes;
    uint64_t audio_unframed_bytes;
    uint64_t audio_sample_ordinal;
    bool audio_counter_valid;
    uint16_t audio_counter16;
    uint64_t audio_counter_extended;

    endpoint_position positions[2];
};

static int endpoint_index(uint8_t endpoint)
{
    if (endpoint == CC_EP_VIDEO)
        return 0;
    if (endpoint == CC_EP_AUDIO)
        return 1;
    return -1;
}

size_t unit_parser_size(void)
{
    return sizeof(unit_parser);
}

size_t unit_parser_alignment(void)
{
    return alignof(unit_parser);
}

unit_parser_config unit_parser_default_config(void)
{
    unit_parser_config config = {
        .maximum_unframed_bytes = UNIT_PARSER_VIDEO_UNIT_BYTES,
    };
    return config;
}

static uint16_t load_u16(const uint8_t *bytes)
{
    return (uint16_t)bytes[0] | (uint16_t)bytes[1] << 8;
}

static bool plausible_video_format(uint16_t format)
{
    return format == 0x0800 || (format & 0xff00u) == 0xe800u ||
           (format & 0xff00u) == 0xe100u;
}

static bool marker_at(const uint8_t *bytes)
{
    return memcmp(bytes, video_marker, sizeof(video_marker)) == 0;
}

static unit_video_kind video_kind(uint16_t format)
{
    if (format == 0xe801)
        return UNIT_VIDEO_E801;
    if (format == 0x0800)
        return UNIT_VIDEO_DEVICE_NO_SIGNAL_0800;
    return UNIT_VIDEO_OTHER_FORMAT;
}

static uint64_t extend_counter(bool *valid, uint16_t *last,
                               uint64_t *extended, uint16_t current,
                               uint32_t *flags)
{
    if (!*valid) {
        *valid = true;
        *last = current;
        *extended = current;
        return *extended;
    }
    uint16_t delta = (uint16_t)(current - *last);
    if (delta == 0 || delta >= 0x8000u) {
        *flags |= UNIT_FLAG_COUNTER_DISCONTINUITY;
        ++*extended;
    } else {
        if (delta != 1)
            *flags |= UNIT_FLAG_COUNTER_DISCONTINUITY;
        *extended += delta;
    }
    *last = current;
    return *extended;
}

static void emit_video(unit_parser *parser, const uint8_t *bytes, size_t count,
                       bool has_marker, uint32_t flags)
{
    if (!count)
        return;
    unit_video_observation out;
    memset(&out, 0, sizeof(out));
    out.epoch = parser->epoch;
    out.ordinal = parser->video_ordinal++;
    out.bytes = bytes;
    out.byte_count = count;
    out.transport_flags = flags;
    out.kind = UNIT_VIDEO_UNFRAMED;
    out.transport = flags ? UNIT_TRANSPORT_HOLE : UNIT_TRANSPORT_UNFRAMED;

    if (has_marker && count >= 8 && marker_at(bytes)) {
        out.counter16 = load_u16(bytes + 4);
        out.format = load_u16(bytes + 6);
        out.kind = video_kind(out.format);
        out.counter_extended = extend_counter(
            &parser->video_counter_valid, &parser->video_counter16,
            &parser->video_counter_extended, out.counter16,
            &out.transport_flags);
        if (out.transport_flags & TRANSPORT_HOLE_FLAGS) {
            out.transport = UNIT_TRANSPORT_HOLE;
        } else if (out.kind == UNIT_VIDEO_E801 &&
                   count < UNIT_PARSER_VIDEO_UNIT_BYTES) {
            out.transport = UNIT_TRANSPORT_SHORT;
        } else if (out.kind == UNIT_VIDEO_E801 &&
                   count > UNIT_PARSER_VIDEO_UNIT_BYTES) {
            out.transport = UNIT_TRANSPORT_UNFRAMED;
        } else {
            out.transport = UNIT_TRANSPORT_COMPLETE;
        }
        if (count >= UNIT_PARSER_VIDEO_HEADER_BYTES) {
            out.payload = bytes + UNIT_PARSER_VIDEO_HEADER_BYTES;
            out.payload_bytes = count - UNIT_PARSER_VIDEO_HEADER_BYTES;
        }
        out.fixed_raster_eligible =
            out.kind == UNIT_VIDEO_E801 &&
            out.transport == UNIT_TRANSPORT_COMPLETE &&
            out.byte_count == UNIT_PARSER_VIDEO_UNIT_BYTES &&
            out.payload_bytes == UNIT_PARSER_VIDEO_PAYLOAD_BYTES;
    }
    if (parser->callbacks.on_video)
        parser->callbacks.on_video(parser->callbacks.context, &out);
}

static void accept_video_boundary(unit_parser *parser, size_t position)
{
    if (parser->video_has_marker)
        emit_video(parser, parser->video, position, true, parser->video_flags);
    else if (position)
        emit_video(parser, parser->video, position, false, parser->video_flags);

    size_t retained = parser->video_bytes - position;
    memmove(parser->video, parser->video + position, retained);
    parser->video_bytes = retained;
    parser->video_has_marker = true;
    parser->video_flags = 0;
    parser->video_candidate_valid = false;
}

static void feed_video_byte(unit_parser *parser, uint8_t byte)
{
    if (parser->video_bytes == sizeof(parser->video)) {
        emit_video(parser, parser->video, parser->video_bytes,
                   parser->video_has_marker,
                   parser->video_flags | UNIT_FLAG_COUNTER_DISCONTINUITY);
        parser->video_bytes = 0;
        parser->video_has_marker = false;
        parser->video_candidate_valid = false;
        parser->video_flags = 0;
    }
    parser->video[parser->video_bytes++] = byte;
    if (!parser->video_has_marker &&
        parser->video_bytes >= parser->config.maximum_unframed_bytes) {
        size_t keep = parser->video_bytes < 7 ? parser->video_bytes : 7;
        size_t emit = parser->video_bytes - keep;
        if (emit)
            emit_video(parser, parser->video, emit, false, parser->video_flags);
        memmove(parser->video, parser->video + emit, keep);
        parser->video_bytes = keep;
        parser->video_flags = 0;
        parser->video_candidate_valid = false;
    }
    if (parser->video_bytes >= 4 &&
        marker_at(parser->video + parser->video_bytes - 4)) {
        parser->video_candidate = parser->video_bytes - 4;
        parser->video_candidate_valid = true;
    }
    if (parser->video_candidate_valid &&
        parser->video_bytes >= parser->video_candidate + 8) {
        size_t candidate = parser->video_candidate;
        uint16_t format = load_u16(parser->video + candidate + 6);
        bool plausible = plausible_video_format(format);
        if (plausible && parser->video_has_marker &&
            parser->video_bytes >= 8) {
            uint16_t previous = load_u16(parser->video + 4);
            uint16_t current = load_u16(parser->video + candidate + 4);
            plausible = (uint16_t)(current - previous) == 1;
        }
        parser->video_candidate_valid = false;
        if (plausible)
            accept_video_boundary(parser, candidate);
    }
}

static void emit_audio_hole(unit_parser *parser, uint32_t flags)
{
    unit_audio_observation out;
    memset(&out, 0, sizeof(out));
    out.epoch = parser->epoch;
    out.kind = UNIT_AUDIO_HOLE;
    out.transport = UNIT_TRANSPORT_HOLE;
    out.transport_flags = flags;
    out.sample_ordinal = parser->audio_sample_ordinal;
    if (parser->callbacks.on_audio)
        parser->callbacks.on_audio(parser->callbacks.context, &out);
    parser->audio_phase_locked = false;
    parser->audio_record_bytes = 0;
    parser->audio_unframed_bytes = 0;
}

static bool is_audio_sync(const uint8_t record[UNIT_PARSER_AUDIO_RECORD_BYTES])
{
    return memcmp(record, audio_sync, AUDIO_SYNC_BYTES) == 0 &&
           record[22] == 0x65 && record[23] == 0x6e;
}

static void emit_audio_record(unit_parser *parser, const uint8_t *record)
{
    unit_audio_observation out;
    memset(&out, 0, sizeof(out));
    out.epoch = parser->epoch;
    out.transport = UNIT_TRANSPORT_COMPLETE;
    out.sample_ordinal = parser->audio_sample_ordinal;
    out.wire_record = record;
    if (is_audio_sync(record)) {
        out.kind = UNIT_AUDIO_RESYNC;
        out.counter16 = load_u16(record + 20);
        out.counter_extended = extend_counter(
            &parser->audio_counter_valid, &parser->audio_counter16,
            &parser->audio_counter_extended, out.counter16,
            &out.transport_flags);
    } else {
        out.kind = UNIT_AUDIO_PCM;
        memcpy(out.active_s24le, record, sizeof(out.active_s24le));
        ++parser->audio_sample_ordinal;
    }
    if (parser->callbacks.on_audio)
        parser->callbacks.on_audio(parser->callbacks.context, &out);
}

static void feed_audio_byte(unit_parser *parser, uint8_t byte)
{
    if (parser->audio_phase_locked) {
        parser->audio_record[parser->audio_record_bytes++] = byte;
        if (parser->audio_record_bytes == UNIT_PARSER_AUDIO_RECORD_BYTES) {
            emit_audio_record(parser, parser->audio_record);
            parser->audio_record_bytes = 0;
        }
        return;
    }

    ++parser->audio_unframed_bytes;
    if (parser->audio_record_bytes < UNIT_PARSER_AUDIO_RECORD_BYTES) {
        parser->audio_record[parser->audio_record_bytes++] = byte;
    } else {
        memmove(parser->audio_record, parser->audio_record + 1,
                UNIT_PARSER_AUDIO_RECORD_BYTES - 1);
        parser->audio_record[UNIT_PARSER_AUDIO_RECORD_BYTES - 1] = byte;
    }
    if (parser->audio_record_bytes == UNIT_PARSER_AUDIO_RECORD_BYTES &&
        is_audio_sync(parser->audio_record)) {
        uint64_t leading = parser->audio_unframed_bytes -
                           UNIT_PARSER_AUDIO_RECORD_BYTES;
        if (leading && parser->callbacks.on_audio) {
            unit_audio_observation out;
            memset(&out, 0, sizeof(out));
            out.epoch = parser->epoch;
            out.kind = UNIT_AUDIO_UNFRAMED;
            out.transport = UNIT_TRANSPORT_UNFRAMED;
            out.sample_ordinal = parser->audio_sample_ordinal;
            parser->callbacks.on_audio(parser->callbacks.context, &out);
        }
        parser->audio_phase_locked = true;
        emit_audio_record(parser, parser->audio_record);
        parser->audio_record_bytes = 0;
        parser->audio_unframed_bytes = 0;
    }
}

void unit_parser_init(unit_parser *parser, const unit_parser_config *config,
                      const unit_parser_callbacks *callbacks)
{
    unit_parser_config chosen = config ? *config : unit_parser_default_config();
    if (!chosen.maximum_unframed_bytes ||
        chosen.maximum_unframed_bytes > UNIT_PARSER_VIDEO_UNIT_BYTES)
        chosen.maximum_unframed_bytes = UNIT_PARSER_VIDEO_UNIT_BYTES;
    memset(parser, 0, sizeof(*parser));
    parser->config = chosen;
    if (callbacks)
        parser->callbacks = *callbacks;
}

void unit_parser_begin_epoch(unit_parser *parser, uint64_t epoch)
{
    if (parser->video_bytes)
        emit_video(parser, parser->video, parser->video_bytes,
                   false, parser->video_flags);
    if (parser->audio_record_bytes && parser->callbacks.on_audio) {
        unit_audio_observation out;
        memset(&out, 0, sizeof(out));
        out.epoch = parser->epoch;
        out.kind = UNIT_AUDIO_UNFRAMED;
        out.transport = UNIT_TRANSPORT_UNFRAMED;
        out.sample_ordinal = parser->audio_sample_ordinal;
        parser->callbacks.on_audio(parser->callbacks.context, &out);
    }
    unit_parser_callbacks callbacks = parser->callbacks;
    unit_parser_config config = parser->config;
    memset(parser, 0, sizeof(*parser));
    parser->callbacks = callbacks;
    parser->config = config;
    parser->epoch = epoch;
}

static bool packet_contiguous(unit_parser *parser, const cc_packet *packet)
{
    int index = endpoint_index(packet->endpoint);
    if (index < 0)
        return true;
    endpoint_position *position = &parser->positions[index];
    bool contiguous = true;
    if (position->valid) {
        if (packet->submit_seq == position->submit_seq)
            contiguous = packet->pkt_index == (uint16_t)(position->packet_index + 1);
        else
            contiguous = packet->submit_seq == position->submit_seq + 1 &&
                         packet->pkt_index == 0;
    }
    position->valid = true;
    position->submit_seq = packet->submit_seq;
    position->packet_index = packet->pkt_index;
    return contiguous;
}

void unit_parser_on_packet(void *context, const cc_packet *packet)
{
    unit_parser *parser = context;
    if (!parser || !packet || parser->finished)
        return;
    bool contiguous = packet_contiguous(parser, packet);
    uint32_t flags = 0;
    if (!contiguous)
        flags |= UNIT_FLAG_PACKET_SEQUENCE_GAP;
    if (packet->status)
        flags |= UNIT_FLAG_PACKET_STATUS;

    if (packet->endpoint == CC_EP_VIDEO) {
        parser->video_flags |= flags;
        for (uint32_t i = 0; i < packet->actual_len; ++i)
            feed_video_byte(parser, packet->data[i]);
    } else if (packet->endpoint == CC_EP_AUDIO) {
        if (flags)
            emit_audio_hole(parser, flags);
        for (uint32_t i = 0; i < packet->actual_len; ++i)
            feed_audio_byte(parser, packet->data[i]);
    }
}

void unit_parser_on_loss(void *context, uint8_t endpoint, uint32_t packets,
                         uint64_t bytes)
{
    unit_parser *parser = context;
    (void)packets;
    (void)bytes;
    if (!parser || parser->finished)
        return;
    if (endpoint == CC_EP_VIDEO)
        parser->video_flags |= UNIT_FLAG_HOST_LOSS;
    else if (endpoint == CC_EP_AUDIO)
        emit_audio_hole(parser, UNIT_FLAG_HOST_LOSS);
}

void unit_parser_on_error(void *context, uint8_t endpoint, uint32_t submit_seq,
                          int status, int error_kind)
{
    unit_parser *parser = context;
    (void)submit_seq;
    (void)status;
    (void)error_kind;
    if (!parser || parser->finished)
        return;
    if (endpoint == CC_EP_VIDEO)
        parser->video_flags |= UNIT_FLAG_TRANSFER_ERROR;
    else if (endpoint == CC_EP_AUDIO)
        emit_audio_hole(parser, UNIT_FLAG_TRANSFER_ERROR);
}

void unit_parser_finish(unit_parser *parser)
{
    if (!parser || parser->finished)
        return;
    if (parser->video_bytes)
        emit_video(parser, parser->video, parser->video_bytes,
                   false, parser->video_flags);
    if (parser->audio_record_bytes && parser->callbacks.on_audio) {
        unit_audio_observation out;
        memset(&out, 0, sizeof(out));
        out.epoch = parser->epoch;
        out.kind = UNIT_AUDIO_UNFRAMED;
        out.transport = UNIT_TRANSPORT_UNFRAMED;
        out.sample_ordinal = parser->audio_sample_ordinal;
        parser->callbacks.on_audio(parser->callbacks.context, &out);
    }
    parser->finished = true;
}
