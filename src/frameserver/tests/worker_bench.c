#include "../frame_publisher.h"
#include "../../field_registration/field_registration.h"
#include "../../signal_state/signal_state.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

enum { SAMPLES = 10000 };

typedef struct {
    uint64_t calls;
    uint64_t checksum;
} bench_sink;

static void consume_frame(void *opaque, const fp_frame *frame)
{
    bench_sink *sink = opaque;
    sink->calls++;
    sink->checksum += frame->counter_ext + (uint8_t)frame->d1 +
                      (uint8_t)frame->d2;
}

static uint64_t now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

static int compare_u64(const void *a, const void *b)
{
    const uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
    return x > y ? 1 : x < y ? -1 : 0;
}

static void report(const char *name, uint64_t values[SAMPLES])
{
    qsort(values, SAMPLES, sizeof values[0], compare_u64);
    printf("%s median %.3f ms p95 %.3f ms\n", name,
           values[SAMPLES / 2] / 1e6, values[(SAMPLES * 95) / 100] / 1e6);
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "usage: %s registration_v9.raw\n", argv[0]);
        return 2;
    }
    FILE *f = fopen(argv[1], "rb");
    if (!f) { perror("fixture"); return 2; }
    if (fseek(f, 0, SEEK_END)) return 2;
    const long length = ftell(f);
    rewind(f);
    const size_t units = (size_t)length / FIELDREG_UNIT_BYTES;
    const size_t usable_units = units > 1 ? units - 1 : units; /* final golden is invalid-header */
    uint8_t *raw = malloc((size_t)length);
    signal_state *signal = aligned_alloc(signal_state_alignment(), signal_state_size());
    uint64_t *engine_ns = malloc(SAMPLES * sizeof *engine_ns);
    uint64_t *worker_ns = malloc(SAMPLES * sizeof *worker_ns);
    if (!raw || !signal || !engine_ns || !worker_ns || units == 0 ||
        fread(raw, 1, (size_t)length, f) != (size_t)length)
        return 2;
    fclose(f);

    field_registration engine;
    fieldreg_config fc = fieldreg_default_config();
    fieldreg_init(&engine, &fc);
    volatile uint64_t checksum = 0;
    for (int i = 0; i < SAMPLES; ++i) {
        const uint8_t *unit = raw + (size_t)(i % usable_units) * FIELDREG_UNIT_BYTES;
        fieldreg_decision decision;
        const uint64_t begin = now_ns();
        if (!fieldreg_process(&engine, unit, &decision)) return 2;
        engine_ns[i] = now_ns() - begin;
        checksum += (uint8_t)decision.applied_d1;
    }

    fieldreg_init(&engine, &fc);
    signal_state_config sc = signal_state_default_config();
    signal_state_init(signal, &sc);
    signal_state_begin_epoch(signal, 1);
    bench_sink bench = {0};
    fp_sink sink = { consume_frame, &bench };
    fp_publisher *publisher = NULL;
    if (fp_open(&publisher, 6, &sink) != 0) {
        fprintf(stderr, "BENCH: fp_open failed\n");
        return 2;
    }
    for (int i = 0; i < SAMPLES; ++i) {
        const uint8_t *unit = raw + (size_t)(i % usable_units) * FIELDREG_UNIT_BYTES;
        unit_video_observation obs = {
            .epoch = 1, .ordinal = (uint64_t)i, .counter16 = (uint16_t)i,
            .counter_extended = (uint64_t)i, .format = 0xe801,
            .kind = UNIT_VIDEO_E801, .transport = UNIT_TRANSPORT_COMPLETE,
            .bytes = unit, .byte_count = FIELDREG_UNIT_BYTES,
            .payload = unit + FIELDREG_HEADER_BYTES,
            .payload_bytes = FIELDREG_UNIT_BYTES - FIELDREG_HEADER_BYTES,
            .fixed_raster_eligible = true,
        };
        signal_result sr;
        fieldreg_decision decision;
        const uint64_t begin = now_ns();
        if (!signal_state_classify(signal, &obs, NULL, &sr)) return 2;
        if (sr.actions & SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT)
            fieldreg_begin_segment(&engine);
        else if (sr.actions & SIGNAL_ACTION_REGISTRATION_DISCONTINUITY)
            fieldreg_discontinuity(&engine);
        if (!fieldreg_process(&engine, unit, &decision)) return 2;
        signal_state_note_registration(signal, &sr,
            decision.frame_observation_support == 2,
            decision.frame_observation_d1, decision.frame_observation_d2,
            decision.confidence, true, decision.applied_d1, decision.applied_d2);
        if (fp_publish(publisher, unit, FIELDREG_UNIT_BYTES, (uint64_t)i,
                       decision.applied_d1, decision.applied_d2,
                       FP_TRANSPORT_COMPLETE, 0, 0) != 0)
            return 2;
        worker_ns[i] = now_ns() - begin;
    }
    fp_stats publisher_stats;
    fp_get_stats(publisher, &publisher_stats);
    if (bench.calls != SAMPLES || publisher_stats.published != SAMPLES ||
        publisher_stats.dropped_no_free_surface != 0)
        return 2;
    checksum += bench.checksum;
    report("FIELDREG-BENCH", engine_ns);
    report("WORKER-BENCH", worker_ns);
    printf("BENCH-SAMPLES %d checksum %llu\n", SAMPLES,
           (unsigned long long)checksum);
    fp_close(publisher);
    free(worker_ns); free(engine_ns); free(signal); free(raw);
    return 0;
}
