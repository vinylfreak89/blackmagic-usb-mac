// A unit up to UNIT_PARSER_VIDEO_LONG_SLACK_BYTES longer than a whole one arrives as ONE observation, ended and
// confirmed by its successor's marker, with the device counter in sequence (the Shuttle's sync-recovery units of
// 23 1/3 lines, 2026-11-15). Longer runs are still cut when the buffer fills, flagged, as before.
#include "unit_parser.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint16_t c16; uint64_t ext; size_t n; unit_transport_state tr; unit_video_kind kind; uint32_t flags; bool confirmed; } seen;
static seen obs[64]; static int nobs;
static void on_video(void *ctx, const unit_video_observation *u){
    (void)ctx; assert(nobs < 64);
    obs[nobs++] = (seen){u->counter16, u->counter_extended, u->byte_count, u->transport, u->kind, u->transport_flags, u->counter_confirmed};
}
static void on_audio(void *ctx, const unit_audio_observation *a){ (void)ctx; (void)a; }

static uint8_t *stream; static size_t len, cap;
static void unit(uint16_t counter, size_t size){
    if (len + size > cap){ cap = (len + size) * 2; stream = realloc(stream, cap); assert(stream); }
    uint8_t *u = stream + len; memset(u, 0, size);
    u[2] = u[3] = 0xff; u[4] = (uint8_t)counter; u[5] = (uint8_t)(counter >> 8); u[6] = 0x01; u[7] = 0xe8;
    for (size_t i = 48; i < size; i++) u[i] = (uint8_t)(i & 1 ? 16 + (i * 7) % 200 : 128);   // no false markers
    len += size;
}

int main(void){
    const size_t U = UNIT_PARSER_VIDEO_UNIT_BYTES, longest = UNIT_PARSER_VIDEO_MAX_UNIT_BYTES;
    unit(100, U); unit(101, U + 33600); unit(102, U); unit(103, longest); unit(104, U); unit(105, longest + 5000); unit(106, U);
    unit(107, U + 20000); unit(900, U); unit(901, U); unit(902, 64);   // a long unit ended by a marker that does not follow it
    unit_parser *p = aligned_alloc(unit_parser_alignment(), (unit_parser_size() + unit_parser_alignment() - 1) / unit_parser_alignment() * unit_parser_alignment());
    assert(p);
    unit_parser_callbacks cb = { .on_video = on_video, .on_audio = on_audio, .context = NULL };
    unit_parser_init(p, NULL, &cb); unit_parser_begin_epoch(p, 1);
    uint32_t seq = 0;
    for (size_t off = 0; off < len; off += 15360){
        size_t n = len - off < 15360 ? len - off : 15360;
        cc_packet pk = { .endpoint = CC_EP_VIDEO, .pkt_index = 0, .submit_seq = seq++, .status = 0, .req_len = 15360, .actual_len = (uint32_t)n, .data = stream + off };
        unit_parser_on_packet(p, &pk);
    }
    unit_parser_finish(p);
    for (int i = 0; i < nobs; i++) printf("  obs %d: counter %u ext %llu bytes %zu transport %d kind %d flags %#x\n", i, obs[i].c16, (unsigned long long)obs[i].ext, obs[i].n, obs[i].tr, obs[i].kind, obs[i].flags);
    assert(obs[0].c16 == 100 && obs[0].n == U && obs[0].tr == UNIT_TRANSPORT_COMPLETE);
    assert(obs[1].c16 == 101 && obs[1].n == U + 33600 && obs[1].tr == UNIT_TRANSPORT_UNFRAMED && obs[1].kind == UNIT_VIDEO_E801);
    assert(obs[1].ext == obs[0].ext + 1 && !(obs[1].flags & UNIT_FLAG_COUNTER_DISCONTINUITY));
    assert(obs[2].c16 == 102 && obs[2].tr == UNIT_TRANSPORT_COMPLETE && obs[2].ext == obs[1].ext + 1 && !(obs[2].flags & UNIT_FLAG_COUNTER_DISCONTINUITY));
    assert(obs[3].c16 == 103 && obs[3].n == longest && obs[3].ext == obs[2].ext + 1 && !(obs[3].flags & UNIT_FLAG_COUNTER_DISCONTINUITY));   // the longest kept whole
    assert(obs[4].c16 == 104 && obs[4].tr == UNIT_TRANSPORT_COMPLETE);
    // Longer than that: cut when the buffer fills (flagged), the rest emitted without a marker, as before.
    assert(obs[5].c16 == 105 && obs[5].n > longest && obs[5].n < longest + 5000 && (obs[5].flags & UNIT_FLAG_COUNTER_DISCONTINUITY));
    assert(obs[6].kind == UNIT_VIDEO_UNFRAMED && obs[5].n + obs[6].n == longest + 5000);
    assert(obs[7].c16 == 106 && obs[7].tr == UNIT_TRANSPORT_COMPLETE);
    // Confirmation: only units ended by their successor's marker carry the device counter.
    assert(obs[0].confirmed && obs[1].confirmed && obs[2].confirmed && obs[3].confirmed && !obs[5].confirmed && !obs[6].confirmed);
    // The stale-run path: 107 (longer than a unit) is ended by 900's marker, which does not follow it: emitted
    // unconfirmed and flagged, so it is never published as counter 107's picture; 900 is confirmed by 901.
    assert(obs[7].confirmed);
    assert(obs[8].c16 == 107 && obs[8].n == U + 20000 && !obs[8].confirmed && (obs[8].flags & UNIT_FLAG_COUNTER_DISCONTINUITY));
    assert(obs[9].c16 == 900 && obs[9].n == U && obs[9].confirmed);
    puts("long_unit_test: PASS");
    free(p); free(stream);
    return 0;
}
