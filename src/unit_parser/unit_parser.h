#ifndef BLACKMAGIC_USB_MAC_UNIT_PARSER_H
#define BLACKMAGIC_USB_MAC_UNIT_PARSER_H

#include "../capture_core/capture_core.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

enum {
    UNIT_PARSER_VIDEO_UNIT_BYTES = 756048,
    UNIT_PARSER_VIDEO_HEADER_BYTES = 48,
    UNIT_PARSER_VIDEO_PAYLOAD_BYTES = 756000,
    UNIT_PARSER_AUDIO_RECORD_BYTES = 24,
};

typedef struct unit_parser unit_parser;

typedef enum unit_transport_state {
    UNIT_TRANSPORT_COMPLETE = 0,
    UNIT_TRANSPORT_HOLE,
    UNIT_TRANSPORT_SHORT,
    UNIT_TRANSPORT_UNFRAMED,
} unit_transport_state;

enum unit_transport_flag {
    UNIT_FLAG_NONE = 0,
    UNIT_FLAG_HOST_LOSS = 1u << 0,
    UNIT_FLAG_TRANSFER_ERROR = 1u << 1,
    UNIT_FLAG_PACKET_SEQUENCE_GAP = 1u << 2,
    UNIT_FLAG_PACKET_STATUS = 1u << 3,
    UNIT_FLAG_COUNTER_DISCONTINUITY = 1u << 4,
};

typedef enum unit_video_kind {
    UNIT_VIDEO_E801 = 0,
    UNIT_VIDEO_DEVICE_NO_SIGNAL_0800,
    UNIT_VIDEO_OTHER_FORMAT,
    UNIT_VIDEO_UNFRAMED,
} unit_video_kind;

typedef struct unit_video_observation {
    uint64_t epoch;
    uint64_t ordinal;
    uint16_t counter16;
    uint64_t counter_extended;
    uint16_t format;
    unit_video_kind kind;
    unit_transport_state transport;
    uint32_t transport_flags;
    const uint8_t *bytes;
    size_t byte_count;
    const uint8_t *payload;
    size_t payload_bytes;
    bool fixed_raster_eligible;
} unit_video_observation;

typedef enum unit_audio_kind {
    UNIT_AUDIO_PCM = 0,
    UNIT_AUDIO_RESYNC,
    UNIT_AUDIO_UNFRAMED,
    UNIT_AUDIO_HOLE,
} unit_audio_kind;

typedef struct unit_audio_observation {
    uint64_t epoch;
    unit_audio_kind kind;
    unit_transport_state transport;
    uint32_t transport_flags;
    uint64_t sample_ordinal;
    /* PCM: two active S24LE channels, still packed as six wire bytes. */
    uint8_t active_s24le[6];
    /* RESYNC: shared device counter and its audio-stream epoch extension. */
    uint16_t counter16;
    uint64_t counter_extended;
    const uint8_t *wire_record;
} unit_audio_observation;

typedef struct unit_parser_callbacks {
    void (*on_video)(void *context, const unit_video_observation *unit);
    void (*on_audio)(void *context, const unit_audio_observation *record);
    void *context;
} unit_parser_callbacks;

typedef struct unit_parser_config {
    /* Bounds an unframed run before it is emitted and scanning resumes. */
    size_t maximum_unframed_bytes;
} unit_parser_config;

size_t unit_parser_size(void);
size_t unit_parser_alignment(void);
unit_parser_config unit_parser_default_config(void);
void unit_parser_init(unit_parser *parser, const unit_parser_config *config,
                      const unit_parser_callbacks *callbacks);

/* Starts a new counter/transport epoch and flushes pending unframed bytes. */
void unit_parser_begin_epoch(unit_parser *parser, uint64_t epoch);

/* capture_core callback adapters. All are allocation-free and nonblocking. */
void unit_parser_on_packet(void *context, const cc_packet *packet);
void unit_parser_on_loss(void *context, uint8_t endpoint, uint32_t packets,
                         uint64_t bytes);
void unit_parser_on_error(void *context, uint8_t endpoint, uint32_t submit_seq,
                          int status, int is_submit_failure);

/* Emits any terminal unframed fragment. No callback follows after finish. */
void unit_parser_finish(unit_parser *parser);

#ifdef __cplusplus
}
#endif

#endif
