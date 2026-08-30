#define _DARWIN_C_SOURCE

#include "../field_registration.h"

#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#ifdef __APPLE__
#include <mach/mach_time.h>
#endif

enum { TPC_DATA = 0, TPC_SESSION = 3, TPC_VIDEO_ENDPOINT = 0x83 };
static const uint32_t TPC_MAGIC = 0x31504143u;

typedef struct expected_row {
    uint32_t timeline;
    uint16_t counter;
    bool exact;
    int decision_d1;
    int decision_d2;
    int applied_d1;
    int applied_d2;
    char mode[48];
    int best_relative;
    int selected_relative;
    int observed_f1;
    int observed_f2;
    int top1;
    int top2;
    int band_mode1;
    int band_mode2;
} expected_row;

typedef struct expected_table {
    expected_row *rows;
    size_t count;
} expected_table;

typedef struct truth_row {
    uint16_t counter;
    int d1;
    int d2;
} truth_row;

typedef struct truth_table {
    truth_row *rows;
    size_t count;
} truth_table;

typedef struct comparison {
    uint64_t rows;
    uint64_t exact;
    uint64_t unknown_units;
    uint64_t applied_matches;
    uint64_t mode_matches;
    uint64_t detailed_matches;
    uint64_t confident;
    uint64_t confident_matches;
    uint64_t truth_rows;
    uint64_t truth_applied_matches;
    uint64_t truth_confident;
    uint64_t truth_confident_matches;
    uint64_t mismatch_examples;
    double *timings_us;
    size_t timing_count;
    size_t timing_capacity;
} comparison;

typedef struct video_stream {
    field_registration engine;
    expected_table *expected;
    truth_table *truth;
    comparison result;
    uint8_t *buffer;
    size_t length;
    size_t capacity;
    size_t expected_index;
} video_stream;

typedef struct span {
    uint64_t start;
    uint64_t end;
} span;

typedef struct marker {
    uint64_t mixed;
    uint64_t pure;
    uint16_t counter;
} marker;

static void die(const char *message)
{
    fprintf(stderr, "field_registration_golden: %s\n", message);
    exit(2);
}

static void die_errno(const char *context)
{
    fprintf(stderr, "field_registration_golden: %s: %s\n", context, strerror(errno));
    exit(2);
}

static uint16_t load_u16(const uint8_t *p)
{
    return (uint16_t)p[0] | (uint16_t)p[1] << 8;
}

static uint32_t load_u32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static bool video_marker(const uint8_t *p, size_t available)
{
    return available >= 8 && p[0] == 0 && p[1] == 0 && p[2] == 0xff &&
           p[3] == 0xff && p[6] == 0x01 && p[7] == 0xe8;
}

static uint64_t timestamp_ns(void)
{
#ifdef __APPLE__
    static mach_timebase_info_data_t info;
    if (info.denom == 0)
        mach_timebase_info(&info);
    uint64_t tick = mach_absolute_time();
    return tick * info.numer / info.denom;
#else
    struct timespec value;
    clock_gettime(CLOCK_MONOTONIC, &value);
    return (uint64_t)value.tv_sec * 1000000000u + (uint64_t)value.tv_nsec;
#endif
}

static int parse_int(const char *text, int empty)
{
    return text && *text ? (int)strtol(text, NULL, 10) : empty;
}

static size_t split_csv(char *line, char **fields, size_t capacity)
{
    size_t count = 0;
    char *field = line;
    for (char *p = line;; ++p) {
        if (*p == ',' || *p == '\n' || *p == '\r' || *p == '\0') {
            char end = *p;
            *p = '\0';
            if (count < capacity)
                fields[count] = field;
            ++count;
            field = p + 1;
            if (end != ',')
                break;
        }
    }
    return count;
}

static int column(char **header, size_t count, const char *name)
{
    for (size_t i = 0; i < count; ++i) {
        if (strcmp(header[i], name) == 0)
            return (int)i;
    }
    return -1;
}

static expected_table load_expected(const char *path)
{
    FILE *file = fopen(path, "r");
    if (!file)
        die_errno(path);
    char line[8192];
    char *fields[96];
    if (!fgets(line, sizeof(line), file))
        die("empty decision CSV");
    size_t header_count = split_csv(line, fields, 96);
    int c_timeline = column(fields, header_count, "timeline_frame");
    int c_counter = column(fields, header_count, "counter");
    int c_state = column(fields, header_count, "unit_state");
    int c_dec1 = column(fields, header_count, "decision_d1");
    int c_dec2 = column(fields, header_count, "decision_d2");
    int c_app1 = column(fields, header_count, "applied_d1");
    int c_app2 = column(fields, header_count, "applied_d2");
    int c_mode = column(fields, header_count, "mode");
    int c_best_rel = column(fields, header_count, "best_relative_d2_minus_d1");
    int c_selected_rel = column(fields, header_count, "selected_relative_d2_minus_d1");
    int c_obs1 = column(fields, header_count, "observed_transport_f1");
    int c_obs2 = column(fields, header_count, "observed_transport_f2");
    int c_top1 = column(fields, header_count, "picture_top_f1");
    int c_top2 = column(fields, header_count, "picture_top_f2");
    int c_band1 = column(fields, header_count, "learned_band_mode_f1");
    int c_band2 = column(fields, header_count, "learned_band_mode_f2");
    if (c_timeline < 0 || c_counter < 0 || c_state < 0 || c_dec1 < 0 ||
        c_app1 < 0 || c_mode < 0 || c_best_rel < 0 || c_band2 < 0)
        die("decision CSV is missing required columns");

    expected_table table = {0};
    size_t capacity = 16384;
    table.rows = malloc(capacity * sizeof(*table.rows));
    if (!table.rows)
        die("out of memory loading expected CSV");
    while (fgets(line, sizeof(line), file)) {
        size_t count = split_csv(line, fields, 96);
        if (count < header_count)
            die("short row in decision CSV");
        if (table.count == capacity) {
            capacity *= 2;
            expected_row *grown = realloc(table.rows, capacity * sizeof(*table.rows));
            if (!grown)
                die("out of memory growing expected CSV");
            table.rows = grown;
        }
        expected_row *row = &table.rows[table.count++];
        memset(row, 0, sizeof(*row));
        row->timeline = (uint32_t)parse_int(fields[c_timeline], 0);
        row->counter = (uint16_t)parse_int(fields[c_counter], 0);
        row->exact = strcmp(fields[c_state], "Exact") == 0;
        row->decision_d1 = parse_int(fields[c_dec1], FIELDREG_UNKNOWN);
        row->decision_d2 = parse_int(fields[c_dec2], FIELDREG_UNKNOWN);
        row->applied_d1 = parse_int(fields[c_app1], 0);
        row->applied_d2 = parse_int(fields[c_app2], 0);
        snprintf(row->mode, sizeof(row->mode), "%s", fields[c_mode]);
        row->best_relative = parse_int(fields[c_best_rel], FIELDREG_UNKNOWN);
        row->selected_relative = parse_int(fields[c_selected_rel], FIELDREG_UNKNOWN);
        row->observed_f1 = parse_int(fields[c_obs1], -1);
        row->observed_f2 = parse_int(fields[c_obs2], -1);
        row->top1 = parse_int(fields[c_top1], -1);
        row->top2 = parse_int(fields[c_top2], -1);
        row->band_mode1 = parse_int(fields[c_band1], FIELDREG_UNKNOWN);
        row->band_mode2 = parse_int(fields[c_band2], FIELDREG_UNKNOWN);
    }
    fclose(file);
    return table;
}

static int truth_compare(const void *left, const void *right)
{
    const truth_row *a = left;
    const truth_row *b = right;
    return (a->counter > b->counter) - (a->counter < b->counter);
}

static truth_table load_truth(const char *path)
{
    truth_table table = {0};
    if (!path)
        return table;
    FILE *file = fopen(path, "r");
    if (!file)
        die_errno(path);
    char line[4096];
    char *fields[32];
    if (!fgets(line, sizeof(line), file))
        die("empty origin census");
    size_t header_count = 0;
    for (char *p = line, *field = line;; ++p) {
        if (*p == '\t' || *p == '\n' || *p == '\r' || *p == '\0') {
            char end = *p;
            *p = '\0';
            fields[header_count++] = field;
            field = p + 1;
            if (end != '\t') break;
        }
    }
    int c_counter = column(fields, header_count, "counter");
    int c_f1t = column(fields, header_count, "f1_picture_top");
    int c_f1b = column(fields, header_count, "f1_picture_bottom");
    int c_f2t = column(fields, header_count, "f2_picture_top");
    int c_f2b = column(fields, header_count, "f2_picture_bottom");
    if (c_counter < 0 || c_f1t < 0 || c_f2b < 0)
        die("origin census is missing required columns");
    size_t capacity = 4096;
    table.rows = malloc(capacity * sizeof(*table.rows));
    if (!table.rows)
        die("out of memory loading origin census");
    while (fgets(line, sizeof(line), file)) {
        size_t count = 0;
        for (char *p = line, *field = line;; ++p) {
            if (*p == '\t' || *p == '\n' || *p == '\r' || *p == '\0') {
                char end = *p;
                *p = '\0';
                fields[count++] = field;
                field = p + 1;
                if (end != '\t') break;
            }
        }
        if (count < header_count)
            continue;
        int f1t = parse_int(fields[c_f1t], -1000);
        int f1b = parse_int(fields[c_f1b], -1000);
        int f2t = parse_int(fields[c_f2t], -1000);
        int f2b = parse_int(fields[c_f2b], -1000);
        int d1 = f1t - 19;
        int d2 = f2t - 282;
        /* The census's independently validated rigid-picture subset. */
        if (d1 != f1b - 256 || d2 != f2b - 518 ||
            d1 < FIELDREG_MIN_OFFSET || d1 > FIELDREG_MAX_OFFSET ||
            d2 < FIELDREG_MIN_OFFSET || d2 > FIELDREG_MAX_OFFSET)
            continue;
        if (table.count == capacity) {
            capacity *= 2;
            truth_row *grown = realloc(table.rows, capacity * sizeof(*table.rows));
            if (!grown)
                die("out of memory growing origin census");
            table.rows = grown;
        }
        table.rows[table.count++] = (truth_row){
            .counter = (uint16_t)parse_int(fields[c_counter], 0),
            .d1 = d1,
            .d2 = d2,
        };
    }
    fclose(file);
    qsort(table.rows, table.count, sizeof(*table.rows), truth_compare);
    return table;
}

static const truth_row *find_truth(const truth_table *table, uint16_t counter)
{
    truth_row key = {.counter = counter};
    return bsearch(&key, table->rows, table->count, sizeof(*table->rows), truth_compare);
}

static void record_timing(comparison *result, double microseconds)
{
    if (result->timing_count == result->timing_capacity) {
        size_t capacity = result->timing_capacity ? result->timing_capacity * 2 : 16384;
        double *grown = realloc(result->timings_us, capacity * sizeof(*grown));
        if (!grown)
            die("out of memory recording benchmark");
        result->timings_us = grown;
        result->timing_capacity = capacity;
    }
    result->timings_us[result->timing_count++] = microseconds;
}

static void compare_exact(video_stream *stream, const expected_row *expected,
                          const fieldreg_decision *actual)
{
    comparison *result = &stream->result;
    ++result->exact;
    bool applied = actual->applied_d1 == expected->applied_d1 &&
                   actual->applied_d2 == expected->applied_d2;
    bool mode = strcmp(fieldreg_mode_name(actual->mode), expected->mode) == 0;
    bool confident_expected = expected->decision_d1 != FIELDREG_UNKNOWN;
    bool confident = actual->decision_d1 == expected->decision_d1 &&
                     actual->decision_d2 == expected->decision_d2;
    bool detailed = applied && mode && confident &&
                    actual->best_relative == expected->best_relative &&
                    actual->selected_relative == expected->selected_relative &&
                    actual->observed_transport_f1 == expected->observed_f1 &&
                    actual->observed_transport_f2 == expected->observed_f2 &&
                    actual->picture_top_f1 == expected->top1 &&
                    actual->picture_top_f2 == expected->top2 &&
                    actual->learned_band_mode_f1 == expected->band_mode1 &&
                    actual->learned_band_mode_f2 == expected->band_mode2;
    result->applied_matches += applied;
    result->mode_matches += mode;
    result->detailed_matches += detailed;
    if (confident_expected) {
        ++result->confident;
        result->confident_matches += confident;
    }
    if (!detailed && result->mismatch_examples < 20) {
        fprintf(stderr,
                "port mismatch ctr=%u: expected app=(%d,%d) mode=%s dec=(%d,%d) "
                "rel=%d/%d obs=%d,%d top=%d,%d band=%d,%d; got "
                "app=(%d,%d) mode=%s dec=(%d,%d) rel=%d/%d obs=%d,%d "
                "top=%d,%d band=%d,%d\n",
                expected->counter, expected->applied_d1, expected->applied_d2,
                expected->mode, expected->decision_d1, expected->decision_d2,
                expected->best_relative, expected->selected_relative,
                expected->observed_f1, expected->observed_f2, expected->top1,
                expected->top2, expected->band_mode1, expected->band_mode2,
                actual->applied_d1, actual->applied_d2,
                fieldreg_mode_name(actual->mode), actual->decision_d1,
                actual->decision_d2, actual->best_relative,
                actual->selected_relative, actual->observed_transport_f1,
                actual->observed_transport_f2, actual->picture_top_f1,
                actual->picture_top_f2, actual->learned_band_mode_f1,
                actual->learned_band_mode_f2);
        ++result->mismatch_examples;
    }

    const truth_row *truth = find_truth(stream->truth, expected->counter);
    if (truth) {
        ++result->truth_rows;
        bool truth_applied = actual->applied_d1 == truth->d1 &&
                             actual->applied_d2 == truth->d2;
        result->truth_applied_matches += truth_applied;
        if (actual->decision_d1 != FIELDREG_UNKNOWN) {
            ++result->truth_confident;
            result->truth_confident_matches +=
                actual->decision_d1 == truth->d1 && actual->decision_d2 == truth->d2;
        }
        if (!truth_applied && result->mismatch_examples < 40) {
            fprintf(stderr,
                    "census disagreement ctr=%u: truth=(%d,%d), applied=(%d,%d), "
                    "mode=%s confidence=%.6f\n",
                    expected->counter, truth->d1, truth->d2, actual->applied_d1,
                    actual->applied_d2, fieldreg_mode_name(actual->mode),
                    actual->confidence);
            ++result->mismatch_examples;
        }
    }
}

static void consume_unit(video_stream *stream, const uint8_t *unit, size_t length)
{
    if (stream->expected_index >= stream->expected->count)
        die("capture contains more units than decision CSV");
    expected_row *expected = &stream->expected->rows[stream->expected_index++];
    ++stream->result.rows;
    uint16_t counter = length >= 6 ? load_u16(unit + 4) : expected->counter;
    if (counter != expected->counter) {
        fprintf(stderr, "counter mismatch at row %zu: capture=%u CSV=%u\n",
                stream->expected_index - 1, counter, expected->counter);
        exit(2);
    }
    if (length != FIELDREG_UNIT_BYTES || !expected->exact) {
        ++stream->result.unknown_units;
        fieldreg_discontinuity(&stream->engine);
        return;
    }
    fieldreg_decision actual;
    uint64_t begin = timestamp_ns();
    bool ok = fieldreg_process(&stream->engine, unit, &actual);
    uint64_t end = timestamp_ns();
    if (!ok)
        die("field_registration rejected an exact unit");
    record_timing(&stream->result, (end - begin) / 1000.0);
    compare_exact(stream, expected, &actual);
}

static size_t find_next_marker(const uint8_t *buffer, size_t length, size_t start)
{
    for (size_t i = start; i + 8 <= length; ++i) {
        if (video_marker(buffer + i, length - i))
            return i;
    }
    return SIZE_MAX;
}

static void feed_video(video_stream *stream, const uint8_t *data, size_t length)
{
    if (stream->length + length > stream->capacity)
        die("video framing buffer overflow");
    memcpy(stream->buffer + stream->length, data, length);
    stream->length += length;

    for (;;) {
        if (!video_marker(stream->buffer, stream->length)) {
            size_t first = find_next_marker(stream->buffer, stream->length, 0);
            if (first == SIZE_MAX) {
                if (stream->length > 7) {
                    memmove(stream->buffer, stream->buffer + stream->length - 7, 7);
                    stream->length = 7;
                }
                return;
            }
            memmove(stream->buffer, stream->buffer + first, stream->length - first);
            stream->length -= first;
        }
        size_t next = find_next_marker(stream->buffer, stream->length, 8);
        if (next == SIZE_MAX)
            return;
        consume_unit(stream, stream->buffer, next);
        memmove(stream->buffer, stream->buffer + next, stream->length - next);
        stream->length -= next;
    }
}

static video_stream make_stream(expected_table *expected, truth_table *truth)
{
    video_stream stream = {0};
    stream.expected = expected;
    stream.truth = truth;
    stream.capacity = FIELDREG_UNIT_BYTES * 2 + 65536;
    stream.buffer = malloc(stream.capacity);
    if (!stream.buffer)
        die("out of memory allocating framing buffer");
    fieldreg_init(&stream.engine, NULL);
    return stream;
}

static void finish_stream(video_stream *stream)
{
    if (video_marker(stream->buffer, stream->length) && stream->length > 0)
        consume_unit(stream, stream->buffer, stream->length);
    if (stream->expected_index != stream->expected->count) {
        fprintf(stderr, "processed %zu rows but CSV contains %zu\n",
                stream->expected_index, stream->expected->count);
        exit(2);
    }
}

static void *map_file(const char *path, size_t *size, int *fd)
{
    *fd = open(path, O_RDONLY);
    if (*fd < 0)
        die_errno(path);
    struct stat st;
    if (fstat(*fd, &st) != 0)
        die_errno("fstat");
    *size = (size_t)st.st_size;
    void *mapped = mmap(NULL, *size, PROT_READ, MAP_PRIVATE, *fd, 0);
    if (mapped == MAP_FAILED)
        die_errno("mmap");
    return mapped;
}

static video_stream run_tagged(const char *capture, expected_table *expected,
                             truth_table *truth)
{
    size_t size;
    int fd;
    const uint8_t *mapped = map_file(capture, &size, &fd);
    video_stream stream = make_stream(expected, truth);
    uint64_t records = 0;
    uint64_t data_records = 0;
    uint64_t status_errors = 0;
    uint64_t seq_gaps = 0;
    uint32_t current_seq = 0;
    int current_packet = -1;
    bool have_seq = false;
    size_t offset = 0;
    while (offset < size) {
        if (size - offset < 24)
            die("truncated tpc record header");
        const uint8_t *header = mapped + offset;
        uint32_t magic = load_u32(header);
        uint8_t type = header[4];
        uint8_t endpoint = header[5];
        uint16_t packet = load_u16(header + 6);
        uint32_t sequence = load_u32(header + 8);
        uint32_t status = load_u32(header + 12);
        uint32_t actual = load_u32(header + 20);
        if (magic != TPC_MAGIC)
            die("bad tpc record magic");
        size_t payload = type == TPC_DATA || type == TPC_SESSION ? actual : 0;
        if (payload > size - offset - 24)
            die("truncated tpc payload");
        if (type == TPC_DATA && endpoint == TPC_VIDEO_ENDPOINT) {
            ++data_records;
            status_errors += status != 0;
            if (!have_seq || sequence != current_seq) {
                if (have_seq && sequence != current_seq + 1)
                    seq_gaps += sequence > current_seq ? sequence - current_seq - 1 : 1;
                current_seq = sequence;
                current_packet = 0;
                have_seq = true;
            }
            if (packet != current_packet)
                ++seq_gaps;
            current_packet = packet + 1;
            if (actual)
                feed_video(&stream, header + 24, actual);
        }
        offset += 24 + payload;
        ++records;
    }
    finish_stream(&stream);
    fprintf(stderr,
            "tpc provenance: records=%" PRIu64 ", video DATA=%" PRIu64
            ", video seq/packet gaps=%" PRIu64 ", status errors=%" PRIu64 "\n",
            records, data_records, seq_gaps, status_errors);
    munmap((void *)mapped, size);
    close(fd);
    return stream;
}

static span *load_spans(const char *path, size_t *count)
{
    FILE *file = fopen(path, "r");
    if (!file) die_errno(path);
    size_t capacity = 32768;
    span *values = malloc(capacity * sizeof(*values));
    if (!values) die("out of memory loading spans");
    *count = 0;
    while (!feof(file)) {
        span value;
        if (fscanf(file, "%" SCNu64 "\t%" SCNu64, &value.start, &value.end) != 2)
            break;
        if (*count == capacity) {
            capacity *= 2;
            values = realloc(values, capacity * sizeof(*values));
            if (!values) die("out of memory growing spans");
        }
        values[(*count)++] = value;
    }
    fclose(file);
    return values;
}

static marker *load_markers(const char *path, size_t *count)
{
    FILE *file = fopen(path, "r");
    if (!file) die_errno(path);
    size_t capacity = 8192;
    marker *values = malloc(capacity * sizeof(*values));
    if (!values) die("out of memory loading markers");
    *count = 0;
    while (!feof(file)) {
        marker value;
        unsigned counter;
        if (fscanf(file, "%" SCNu64 "\t%" SCNu64 "\t%u",
                   &value.mixed, &value.pure, &counter) != 3)
            break;
        value.counter = (uint16_t)counter;
        if (*count == capacity) {
            capacity *= 2;
            values = realloc(values, capacity * sizeof(*values));
            if (!values) die("out of memory growing markers");
        }
        values[(*count)++] = value;
    }
    fclose(file);
    return values;
}

static const marker *find_marker_counter(const marker *markers, size_t count,
                                         uint16_t counter)
{
    for (size_t i = 0; i + 1 < count; ++i) {
        if (markers[i].counter == counter)
            return &markers[i];
    }
    return NULL;
}

static size_t copy_without_spans(uint8_t *dst, size_t capacity,
                                 const uint8_t *mapped, uint64_t start,
                                 uint64_t end, const span *spans,
                                 size_t span_count)
{
    size_t used = 0;
    uint64_t cursor = start;
    for (size_t i = 0; i < span_count && cursor < end; ++i) {
        if (spans[i].end <= cursor)
            continue;
        if (spans[i].start >= end)
            break;
        uint64_t copy_end = spans[i].start < end ? spans[i].start : end;
        if (copy_end > cursor) {
            size_t amount = (size_t)(copy_end - cursor);
            if (used + amount > capacity) die("legacy interval exceeds unit buffer");
            memcpy(dst + used, mapped + cursor, amount);
            used += amount;
        }
        if (spans[i].end > cursor)
            cursor = spans[i].end;
    }
    if (cursor < end) {
        size_t amount = (size_t)(end - cursor);
        if (used + amount > capacity) die("legacy interval exceeds unit buffer");
        memcpy(dst + used, mapped + cursor, amount);
        used += amount;
    }
    return used;
}

static video_stream run_capture_untagged_ring(const char *capture, const char *span_path,
                               const char *marker_path, expected_table *expected,
                               truth_table *truth)
{
    size_t size;
    int fd;
    const uint8_t *mapped = map_file(capture, &size, &fd);
    size_t span_count, marker_count;
    span *spans = load_spans(span_path, &span_count);
    marker *markers = load_markers(marker_path, &marker_count);
    video_stream stream = make_stream(expected, truth);
    uint8_t *unit = malloc(FIELDREG_UNIT_BYTES);
    if (!unit) die("out of memory allocating legacy unit");

    for (size_t row_index = 0; row_index < expected->count; ++row_index) {
        expected_row *row = &expected->rows[row_index];
        ++stream.result.rows;
        if (!row->exact) {
            ++stream.result.unknown_units;
            fieldreg_discontinuity(&stream.engine);
            continue;
        }
        const marker *current = find_marker_counter(markers, marker_count, row->counter);
        if (!current)
            die("exact legacy CSV row has no marker");
        size_t marker_index = (size_t)(current - markers);
        const marker *next = &markers[marker_index + 1];
        if ((uint16_t)(next->counter - current->counter) != 1 ||
            next->pure - current->pure != FIELDREG_UNIT_BYTES)
            die("exact legacy CSV row does not have an exact indexed interval");
        size_t length = copy_without_spans(unit, FIELDREG_UNIT_BYTES, mapped,
                                           current->mixed, next->mixed,
                                           spans, span_count);
        if (length != FIELDREG_UNIT_BYTES)
            die("legacy span reconstruction was not exactly one unit");
        fieldreg_decision actual;
        uint64_t begin = timestamp_ns();
        bool ok = fieldreg_process(&stream.engine, unit, &actual);
        uint64_t end = timestamp_ns();
        if (!ok) die("field_registration rejected exact legacy unit");
        record_timing(&stream.result, (end - begin) / 1000.0);
        compare_exact(&stream, row, &actual);
    }
    stream.expected_index = expected->count;
    free(unit);
    free(spans);
    free(markers);
    munmap((void *)mapped, size);
    close(fd);
    return stream;
}

static int double_compare(const void *left, const void *right)
{
    double a = *(const double *)left;
    double b = *(const double *)right;
    return (a > b) - (a < b);
}

static double percent(uint64_t numerator, uint64_t denominator)
{
    return denominator ? 100.0 * numerator / denominator : 100.0;
}

static void report(video_stream *stream)
{
    comparison *r = &stream->result;
    qsort(r->timings_us, r->timing_count, sizeof(*r->timings_us), double_compare);
    double median = r->timings_us[r->timing_count / 2];
    double p95 = r->timings_us[(size_t)(r->timing_count * 0.95)];
    double maximum = r->timings_us[r->timing_count - 1];
    double sum = 0.0;
    for (size_t i = 0; i < r->timing_count; ++i)
        sum += r->timings_us[i];
    double mean = sum / r->timing_count;
    printf("units: rows=%" PRIu64 " exact=%" PRIu64 " discontinuities=%" PRIu64 "\n",
           r->rows, r->exact, r->unknown_units);
    printf("Python port parity: applied %.6f%% (%" PRIu64 "/%" PRIu64
           "), mode %.6f%%, full diagnostics %.6f%%\n",
           percent(r->applied_matches, r->exact), r->applied_matches, r->exact,
           percent(r->mode_matches, r->exact),
           percent(r->detailed_matches, r->exact));
    printf("Python confident-decision parity: %.6f%% (%" PRIu64 "/%" PRIu64 ")\n",
           percent(r->confident_matches, r->confident), r->confident_matches,
           r->confident);
    if (r->truth_rows) {
        printf("Independent census: applied agreement %.6f%% (%" PRIu64 "/%" PRIu64
               "); confident-decision agreement %.6f%% (%" PRIu64 "/%" PRIu64 ")\n",
               percent(r->truth_applied_matches, r->truth_rows),
               r->truth_applied_matches, r->truth_rows,
               percent(r->truth_confident_matches, r->truth_confident),
               r->truth_confident_matches, r->truth_confident);
    }
    printf("field_registration cost: mean %.3f us, median %.3f us, p95 %.3f us, max %.3f us; "
           "median %.1fx real-time per 29.97-frame unit\n",
           mean, median, p95, maximum, 33366.7 / median);
}

static void usage(const char *program)
{
    fprintf(stderr,
            "usage:\n"
            "  %s --packet-capture CAPTURE --csv DECISIONS\n"
            "  %s --untagged-capture CAPTURE --audio-spans SPANS --marker-index MARKERS --csv DECISIONS "
            "--field-origin-census FIELD_ORIGIN_CENSUS\n",
            program, program);
    exit(2);
}

int main(int argc, char **argv)
{
    const char *tpc = NULL, *capture_untagged_ring = NULL, *spans = NULL, *markers = NULL;
    const char *csv = NULL, *census = NULL;
    for (int i = 1; i < argc; ++i) {
        if (i + 1 >= argc) usage(argv[0]);
        if (strcmp(argv[i], "--packet-capture") == 0) tpc = argv[++i];
        else if (strcmp(argv[i], "--untagged-capture") == 0) capture_untagged_ring = argv[++i];
        else if (strcmp(argv[i], "--audio-spans") == 0) spans = argv[++i];
        else if (strcmp(argv[i], "--marker-index") == 0) markers = argv[++i];
        else if (strcmp(argv[i], "--csv") == 0) csv = argv[++i];
        else if (strcmp(argv[i], "--field-origin-census") == 0) census = argv[++i];
        else usage(argv[0]);
    }
    if (!csv || (!!tpc == !!capture_untagged_ring) || (capture_untagged_ring && (!spans || !markers)))
        usage(argv[0]);
    expected_table expected = load_expected(csv);
    truth_table truth = load_truth(census);
    video_stream stream = tpc ? run_tagged(tpc, &expected, &truth)
                               : run_capture_untagged_ring(capture_untagged_ring, spans, markers, &expected, &truth);
    report(&stream);
    bool pass = stream.result.applied_matches == stream.result.exact &&
                stream.result.mode_matches == stream.result.exact &&
                stream.result.confident_matches == stream.result.confident;
    free(stream.result.timings_us);
    free(stream.buffer);
    free(expected.rows);
    free(truth.rows);
    return pass ? 0 : 1;
}
