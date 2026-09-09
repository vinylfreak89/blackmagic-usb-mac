#include "field_registration.h"
#include "cea608.h"

#include <limits.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

typedef struct field_measurement {
    bool insert_present;
    uint8_t insert_byte1;
    uint8_t insert_byte2;
    cea608_candidate off_candidate;
    uint16_t off_count;
    int16_t fallback_row;
    uint16_t fallback_count;
    double blank_mean;
    int16_t recorded_first;
    int16_t recorded_last;
    int16_t top;
    int16_t bottom;
    int16_t switch_line;
    int16_t first_full_other_head_line;
    int16_t rf_peak_line;
    int16_t rf_peak_position;
    int16_t span;
    int16_t picture_rows;
    int16_t band_extent;
    int16_t observed_switch_line_count;
    fieldreg_switch_signature switch_signature;
    bool switch_measurable;
    bool geometry_measurable;
    bool box_detected;
    double blank_chroma_noise;
} field_measurement;

#include "box_observation.h"

/* BT.601: 858 total / 720 delivered samples. SMPTE 170M blanking is
 * approximately 147 samples, leaving nine delivered blanking samples in
 * total (not nine at EACH end). Sixteen is the local-profile memory capacity,
 * not a required run length or an expected band extent. */
enum { H_SAMPLES = 720, H_BLANK = 147, H_OVERLAP = H_BLANK-(858-720),
       H_HISTORY = 16 };

typedef struct horizontal_blanking {
    uint8_t support[H_SAMPLES];
    uint8_t blank_samples[H_SAMPLES];
    bool readable;
    bool complete_interval;
} horizontal_blanking;

static horizontal_blanking blanking_profile(const uint8_t *raster, int row,
                                            unsigned blank_ceiling)
{
    horizontal_blanking p = {0};
    const uint8_t *line = raster + (size_t)row*FIELDREG_BYTES_PER_LINE;
    unsigned sum=0, total=0;
    for(int x=0;x<H_SAMPLES;++x)total+=line[2*x+1];
    /* A row indistinguishable from blanking supplies no phase. */
    if(total<=blank_ceiling*H_SAMPLES)return p;
    for(int x=0;x<H_SAMPLES;++x)
        p.blank_samples[x]=line[2*x+1]<=blank_ceiling;
    for(int x=0;x<H_OVERLAP;++x)sum+=line[2*x+1];
    for(int x=0;x<H_SAMPLES;++x) {
        p.support[x]=(sum<=blank_ceiling*H_OVERLAP);
        p.readable |= p.support[x]!=0;
        /* Circular windows join the two delivered ends: the overlap may
         * be split between them. No particular end is required to be black. */
        sum-=line[2*x+1];
        sum+=line[2*((x+H_OVERLAP)%H_SAMPLES)+1];
    }
    sum=0;
    for(int x=0;x<H_BLANK;++x)sum+=line[2*x+1];
    for(int x=0;x<=H_SAMPLES-H_BLANK;++x) {
        if(sum<=blank_ceiling*H_BLANK)p.complete_interval=true;
        if(x<H_SAMPLES-H_BLANK) {
            sum-=line[2*x+1];
            sum+=line[2*(x+H_BLANK)+1];
        }
    }
    return p;
}

static bool phase_overlap(const horizontal_blanking *a,
                           const horizontal_blanking *b)
{
    if(!a->readable || !b->readable)return false;
    for(int x=0;x<H_SAMPLES;++x)
        if(a->support[x] && b->support[x])return true;
    return false;
}

static bool retains_normal_prefix(const horizontal_blanking *row,
                                  const horizontal_blanking *basis,
                                  const horizontal_blanking *full,
                                  const uint8_t *informative_columns)
{
    /* The prefix precedes the exposed other-head blanking, whose position
     * is measured, not assumed to be at either delivered end. A lone final
     * blank sample cannot establish that the BEGINNING retained timing.
     * This is sufficient prefix evidence, not a claim that every partial
     * exposes such a prefix; otherwise the contract's S fallback remains. */
    for(int x=0;x<H_SAMPLES;++x) {
        if(full->support[x])return false;
        if(informative_columns[x] && row->blank_samples[x] &&
           basis->blank_samples[x])return true;
    }
    return false;
}

static void measure_switch(const uint8_t *raster, int field,
                           field_measurement *m)
{
    /* This unit's regenerated blanking, excluding its timing/insert rows.
     * Re-measured on every invocation: no source timing or level survives a
     * reset, and a gated unit cannot train this measurement. */
    const int first=field?270:7, last=field?278:15;
    unsigned ceiling=0;
    for(int r=first;r<=last;++r)for(int x=0;x<H_SAMPLES;++x) {
        unsigned y=raster[(size_t)r*FIELDREG_BYTES_PER_LINE+2*x+1];
        if(y>ceiling)ceiling=y;
    }
    /* A column blank throughout the field cannot distinguish either phase.
     * Example measured on 6687 f1: sample 719 is blank even in the displaced
     * rows. Discover such columns from the unit, never type their positions. */
    uint8_t informative_columns[H_SAMPLES]={0};
    for(int row=m->top;row<=m->recorded_last;++row)
        for(int x=0;x<H_SAMPLES;++x)
            informative_columns[x] |=
                raster[(size_t)row*FIELDREG_BYTES_PER_LINE+2*x+1]>ceiling;
    horizontal_blanking history[H_HISTORY];
    horizontal_blanking previous={0};
    horizontal_blanking departure_basis={0};
    unsigned count=0,next=0;
    int departure=-1, full=-1;
    for(int row=m->top;row<=m->recorded_last;++row) {
        const horizontal_blanking p=blanking_profile(raster,row,ceiling);
        /* Return to the pre-departure phase excludes a mid-field event. */
        if(departure>=0 && phase_overlap(&p,&departure_basis))
            departure=full=-1;
        horizontal_blanking basis={0};
        for(unsigned i=0;i<count;++i) {
            if(!history[i].readable)continue;
            /* The envelope admits locally observed phase variance; individual
             * blank samples must instead persist throughout that reference.
             * Their survival in a normal prefix rules out a full departure.
             * No leading/trailing sample position is typed in. */
            for(int x=0;x<H_SAMPLES;++x)
                basis.blank_samples[x]=basis.readable ?
                    basis.blank_samples[x] & history[i].blank_samples[x] :
                    history[i].blank_samples[x];
            basis.readable |= history[i].readable;
            for(int x=0;x<H_SAMPLES;++x)
                basis.support[x] |= history[i].support[x];
        }
        const bool current_full=p.readable && p.complete_interval && basis.readable &&
           !phase_overlap(&p,&basis) &&
           !retains_normal_prefix(&p,&basis,&p,informative_columns);
        /* A partial need not expose a complete delivered blanking overlap:
         * its later portion can lose the porch while the leading remnant
         * survives. Raw commercial 6690 L260 retains samples 0..2 but has
         * no nine-sample window. The following full row supplies positive
         * relocation; the partial supplies a retained normal prefix plus loss
         * of the normal window. Blank-equivalent rows have no remnant map. */
        const bool previous_partial=basis.readable &&
            retains_normal_prefix(&previous,&basis,&p,informative_columns) &&
            !phase_overlap(&previous,&basis);
        /* A preceding row with the same displaced phase must be positively
         * identified as partial. Otherwise it might already be a full row:
         * a later, easier-to-read row cannot become the FIRST full row. */
        if(current_full && !(previous.readable && !previous_partial &&
                             phase_overlap(&p,&previous))) {
            full=row;
            /* The contract's S / partial-row travel, not a band-size cap.
             * An earlier isolated departure cannot be carried through
             * intervening rows to manufacture a long head-switch band. */
            departure=previous_partial ? row-1 : row;
            departure_basis=basis;
        }
        /* Local means local in raster rows, including unreadable ones.
         * Exclude the immediately preceding row while testing S: it may
         * itself carry the partial switch. No lifetime/source-wide envelope. */
        history[next]=previous;
        previous=p;
        next=(next+1)%H_HISTORY;
        if(count<H_HISTORY)++count;
    }
    /* A relocated full blanking interval corroborates the preceding partial
     * departure. Without it neither missing edge nor brightness places T. */
    if(departure>=0 && full>=0) {
        m->switch_line=(int16_t)departure;
        m->first_full_other_head_line=(int16_t)full;
        m->switch_signature=departure<full ? FIELDREG_SWITCH_BLANKING_PARTIAL :
                                           FIELDREG_SWITCH_FULL_OTHER_HEAD;
        m->switch_measurable=true;
    }
}

static uint16_t read_le16(const uint8_t *p)
{
    return (uint16_t)p[0] | (uint16_t)((uint16_t)p[1] << 8);
}

static bool valid_unit(const uint8_t unit[FIELDREG_UNIT_BYTES])
{
    if (!unit || memcmp(unit, "\x00\x00\xff\xff", 4) != 0 ||
        read_le16(unit + 6) != 0xe801)
        return false;
    for (int i = 8; i < FIELDREG_HEADER_BYTES; ++i)
        if (unit[i] != 0) return false;
    return true;
}

static double row_mean(const uint8_t *raster, int row)
{
    const uint8_t *line = raster + (size_t)row * FIELDREG_BYTES_PER_LINE;
    uint32_t sum = 0;
    for (int x = 40; x < 680; ++x) sum += line[x * 2 + 1];
    return (double)sum / 640.0;
}

static double row_chroma_noise(const uint8_t *raster, int row)
{
    const uint8_t *line = raster + (size_t)row * FIELDREG_BYTES_PER_LINE;
    double mean = 0.0;
    for (int x = 40; x < 680; ++x) mean += line[x * 2];
    mean /= 640.0;
    double sum = 0.0;
    for (int x = 40; x < 680; ++x) {
        const double delta = (double)line[x * 2] - mean;
        sum += delta * delta;
    }
    return sqrt(sum / 640.0);
}

static double row_bins(const uint8_t *raster, int row, double *bins,
                       int bin_count)
{
    const uint8_t *line = raster + (size_t)row * FIELDREG_BYTES_PER_LINE;
    uint32_t total = 0;
    for (int bin = 0; bin < bin_count; ++bin) {
        const int first = 40 + (bin * 640) / bin_count;
        const int last = 40 + ((bin + 1) * 640) / bin_count;
        uint32_t sum = 0;
        for (int x = first; x < last; ++x) sum += line[x * 2 + 1];
        bins[bin] = (double)sum / (double)(last - first);
        total += sum;
    }
    return (double)total / 640.0;
}

static bool xds_left_structure(const uint8_t *raster, int row)
{
    double bins[24];
    if (row_bins(raster, row, bins, 24) >= 95.0) return false;
    if (bins[1] <= 60.0 || bins[2] > 40.0) return false;
    int bar_run = 0;
    bool bar_present = false;
    for (int bin = 4; bin <= 7; ++bin) {
        if (bins[bin] > 60.0) {
            if (++bar_run >= 2) bar_present = true;
        } else bar_run = 0;
    }
    if (!bar_present) return false;
    return bins[8] <= 40.0 && bins[9] <= 40.0;
}

static bool field2_envelope(const uint8_t *raster, int row)
{
    /* Only the measured XDS structure in the left 40% is invariant. Picture
     * can bleed into the right half, so it is deliberately unconstrained. */
    return xds_left_structure(raster, row);
}

static bool caption_like_damage(const uint8_t *raster, int row)
{
    double bins[24];
    const double mean = row_bins(raster, row, bins, 24);
    double run_mean = 0.0;
    for (int i = 0; i < 6; ++i) run_mean += bins[i];
    run_mean /= 6.0;
    double variance = 0.0;
    for (int i = 0; i < 6; ++i) {
        const double delta = bins[i] - run_mean;
        variance += delta * delta;
    }
    variance /= 6.0;
    double pulse = bins[6];
    for (int i = 7; i < 18; ++i)
        if (bins[i] > pulse) pulse = bins[i];
    double dark = bins[18];
    for (int i = 19; i < 24; ++i)
        if (bins[i] < dark) dark = bins[i];
    /* Damaged run-in lines measured at 37:01 retain a flat coarse-bin
     * envelope (variance <= 18). Genuine consecutive picture rows at the
     * same site begin at 30.8, so do not let the weak-caption fallback erase
     * them from geometry. Full-amplitude run-in remains covered above by the
     * CEA-608 carrier detector independently of this fallback. */
    return run_mean > 35.0 && run_mean < 90.0 && variance < 20.0 &&
           pulse > 85.0 && mean < 95.0 && dark < 40.0;
}

static bool timing_like_damage(const uint8_t *raster, int row)
{
    double bins[24];
    const double mean = row_bins(raster, row, bins, 24);
    double middle = bins[2];
    for (int i = 3; i < 17; ++i)
        if (bins[i] > middle) middle = bins[i];
    double right_pulse = bins[17];
    for (int i = 18; i < 22; ++i)
        if (bins[i] > right_pulse) right_pulse = bins[i];
    return bins[0] > 80.0 && middle < 12.0 && right_pulse > 100.0 &&
           mean < 60.0;
}

static bool top_interval_vbi_damage(const uint8_t *raster, int row, int field)
{
    const int first = field == 0 ? 16 : 279; /* NTSC 20 / 283 */
    const int last = field == 0 ? 26 : 289;  /* NTSC 30 / 293 */
    if (row < first || row > last) return false;
    return caption_like_damage(raster, row) ||
           timing_like_damage(raster, row) ||
           xds_left_structure(raster, row);
}

static void measure_field(const uint8_t *raster, int field,
                          field_measurement *m)
{
    const int first = field == 0 ? 8 : 268;   /* NTSC 12 / 272 */
    const int last = field == 0 ? 262 : 524;  /* NTSC 266 / 528 */
    const int insert = field == 0 ? FIELDREG_INSERT_F1 : FIELDREG_INSERT_F2;
    const int picture_first = field == 0 ? 18 : 281; /* NTSC 22 / 285 */
    const int pass_through_last = field == 0 ? 260 : 522; /* NTSC 264 / 526 */
    const int blank_first = field == 0 ? 7 : 270;
    const int blank_last = field == 0 ? 16 : 279;
    bool waveform[257] = {false};
    bool recorded[257] = {false};
    bool picture[257] = {false};
    double means[257] = {0.0};
    memset(m, 0, sizeof *m);
    m->fallback_row = -1;
    m->recorded_first = m->recorded_last = -1;
    m->top = m->bottom = -1;
    m->switch_line = m->first_full_other_head_line = -1;
    m->rf_peak_line = m->rf_peak_position = -1;
    m->span = m->picture_rows = m->band_extent = -1;
    m->observed_switch_line_count = -1;

    double blank_luma_ceiling = 0.0;
    for (int row = blank_first; row <= blank_last; ++row) {
        m->blank_mean += row_mean(raster, row);
        const double mean = row_mean(raster, row);
        if (mean > blank_luma_ceiling) blank_luma_ceiling = mean;
        const double chroma_noise = row_chroma_noise(raster, row);
        if (chroma_noise > m->blank_chroma_noise)
            m->blank_chroma_noise = chroma_noise;
    }
    m->blank_mean /= (double)(blank_last - blank_first + 1);

    uint8_t luma[CEA608_PIXELS_PER_LINE];
    for (int row = first; row <= last; ++row) {
        const uint8_t *line = raster + (size_t)row * FIELDREG_BYTES_PER_LINE;
        for (int x = 0; x < CEA608_PIXELS_PER_LINE; ++x)
            luma[x] = line[x * 2 + 1];
        cea608_decode_result decoded;
        cea608_decode_luma(luma, &decoded);
        waveform[row - first] = decoded.run_in_present;
        if (top_interval_vbi_damage(raster, row, field))
            waveform[row - first] = true;
        means[row - first] = row_mean(raster, row);
        if (decoded.parity_valid) {
            if (row == insert) {
                m->insert_present = true;
                m->insert_byte1 = decoded.byte1;
                m->insert_byte2 = decoded.byte2;
            } else {
                if (m->off_count == 0) {
                    m->off_candidate.raster_row = (int16_t)row;
                    m->off_candidate.byte1 = decoded.byte1;
                    m->off_candidate.byte2 = decoded.byte2;
                    m->off_candidate.amplitude = decoded.amplitude;
                }
                if (m->off_count != UINT16_MAX) ++m->off_count;
            }
        }
        /* The frozen smeared-XDS fallback is a top-interval classifier, not a
         * whole-picture search: NTSC lines 285..290 (unit rows 281..286).
         * Scanning the body admits picture texture by construction. */
        if (field == 1 && row > insert && row <= insert + 6 &&
            !decoded.run_in_present && !decoded.parity_valid &&
            field2_envelope(raster, row)) {
            waveform[row - first] = true;
            if (m->fallback_count == 0) m->fallback_row = (int16_t)row;
            if (m->fallback_count != UINT16_MAX) ++m->fallback_count;
        }
        /* Contract section 3 gives two independent recorded-row readings.
         * Luma must rise above this unit's own blanking ceiling, or chroma
         * noise must cross the measured 1.48x/2.02x gap at its lower bound.
         * Neither test contains a fixed luma-code offset. */
        recorded[row - first] =
            (means[row - first] > blank_luma_ceiling ||
             row_chroma_noise(raster, row) >
                 2.0 * m->blank_chroma_noise);
        picture[row - first] = !waveform[row - first] &&
                               recorded[row - first];
    }

    for (int row = picture_first; row <= pass_through_last; ++row) {
        if (recorded[row - first]) {
            if (m->recorded_first < 0) m->recorded_first = (int16_t)row;
            m->recorded_last = (int16_t)row;
        }
    }

    /* Geometry is measured independently of every caption/fallback result.
     * Recognised VBI rows are excluded by their own waveform, never because
     * a caption told the scan where to begin. */
    for (int row = picture_first; row <= pass_through_last; ++row) {
        if (picture[row - first]) {
            m->top = (int16_t)row;
            break;
        }
    }

    m->box_detected=observe_box(raster,field,m->recorded_last);
    /* Rule 8: do not measure a switch below a boxed content gap. The
     * categorical observation supplies no origin or measured box extent. */
    if(m->box_detected)return;
    if (m->top >= 0) measure_switch(raster,field,m);
    if (m->top >= 0) m->geometry_measurable = true;
    if (m->switch_measurable) {
        const int origin = field == 0 ? FIELDREG_PICTURE_ORIGIN_F1 :
                                        FIELDREG_PICTURE_ORIGIN_F2;
        const int visible_d = m->top - origin;
        m->bottom = (int16_t)(m->switch_line - 1);
        m->span = (int16_t)(m->switch_line - origin);
        m->band_extent = (int16_t)(m->recorded_last - m->switch_line + 1);
        m->observed_switch_line_count =
            (int16_t)(m->band_extent + visible_d);
        m->picture_rows =
            (int16_t)(FIELDREG_FIELD_LINES -
                      m->observed_switch_line_count);
    }
}


static bool crop_fits_raster(int field, int displacement)
{
    const int start = field == 0 ? FIELDREG_FIELD1_START :
                                   FIELDREG_FIELD2_START;
    const int low = -start;
    const int high = FIELDREG_RASTER_LINES - FIELDREG_FIELD_LINES - start;
    return displacement >= low && displacement <= high &&
           displacement >= INT8_MIN && displacement <= INT8_MAX;
}

typedef struct comb_reading {
    bool measured;
    int shift;
    double best, second, fraction;
    uint16_t unresolved;
} comb_reading;

static void comb_lowpass(field_registration *e,const uint8_t *raster)
{
    for(int r=0;r<FIELDREG_RASTER_LINES;++r)
        for(int x=0;x<FIELDREG_COMB_COLUMNS;++x){
            unsigned sum=0;
            for(int k=0;k<FIELDREG_COMB_BOX;++k)
                sum+=raster[(size_t)r*1440+2*(x*FIELDREG_COMB_BOX+k)+1];
            e->current_luma[r*FIELDREG_COMB_COLUMNS+x]=(uint16_t)sum;
        }
}

typedef struct comb_pair_reading {
    double energy[2][2]; /* time, alignment */
    unsigned samples, possible;
} comb_pair_reading;

static comb_pair_reading comb_pair(const field_registration *e,const int start[2],
    const uint8_t valid[2][240],const uint8_t still[2][240][FIELDREG_COMB_COLUMNS],int a,int b)
{
    enum { C=FIELDREG_COMB_COLUMNS,H=FIELDREG_FIELD_LINES };
    comb_pair_reading r={0};uint64_t sums[2][2]={{0}};
    for(int y=0;y<H-1;++y){
        int j=y+a,k=y+b;
        if(j<1 || j>=H-1 || k<1 || k>=H-1 || !valid[0][y] || !valid[0][y+1] ||
           !valid[1][j-1] || !valid[1][j] || !valid[1][j+1] ||
           !valid[1][k-1] || !valid[1][k] || !valid[1][k+1])continue;
        r.possible+=C;
        for(int x=0;x<C;++x){
            if(!still[0][y][x] || !still[0][y+1][x] ||
               !still[1][j-1][x] || !still[1][j][x] || !still[1][j+1][x] ||
               !still[1][k-1][x] || !still[1][k][x] || !still[1][k+1][x])continue;
            ++r.samples;
            int ca=e->current_luma[(start[0]+y)*C+x]+e->current_luma[(start[0]+y+1)*C+x];
            int pa=e->previous_luma[(e->previous_crop[0]+y)*C+x]+e->previous_luma[(e->previous_crop[0]+y+1)*C+x];
            sums[0][0]+=(unsigned)abs(2*e->current_luma[(start[1]+j)*C+x]-ca);
            sums[0][1]+=(unsigned)abs(2*e->current_luma[(start[1]+k)*C+x]-ca);
            sums[1][0]+=(unsigned)abs(2*e->previous_luma[(e->previous_crop[1]+j)*C+x]-pa);
            sums[1][1]+=(unsigned)abs(2*e->previous_luma[(e->previous_crop[1]+k)*C+x]-pa);
        }
    }
    if(r.samples)for(int t=0;t<2;++t)for(int q=0;q<2;++q)
        r.energy[t][q]=(double)sums[t][q]/(2*FIELDREG_COMB_BOX*r.samples);
    return r;
}

/* One shared mask per comparison, in BOTH current and previous fields. The
 * temporal tolerance is the largest observed low-pass fluctuation on this
 * pair's regenerated blanking rows, not a typed luma threshold. It selects
 * only picture changes indistinguishable at that instrument noise floor.
 * Candidate ranking must also survive the observed energy fluctuation
 * between the two units; ties or overlapping intervals do not confirm. */
static comb_reading comb_search(const field_registration *e,const int start[2],
                               const int begin[2],const int end[2],int bias)
{
    comb_reading result={0};
    enum { C=FIELDREG_COMB_COLUMNS, H=FIELDREG_FIELD_LINES };
    unsigned tolerance=0;
    for(int f=0;f<2;++f)for(int r=f?270:7;r<=(f?278:15);++r)
        for(int x=0;x<C;++x){
            unsigned d=(unsigned)abs((int)e->current_luma[r*C+x]-e->previous_luma[r*C+x]);
            if(d>tolerance)tolerance=d;
        }
    uint8_t still[2][H][C],valid[2][H];
    for(int f=0;f<2;++f)for(int y=0;y<H;++y)for(int x=0;x<C;++x){
        int r=start[f]+y,p=e->previous_crop[f]+y;
        bool available=r>=begin[f] && r<=end[f] && p>=e->previous_begin[f] &&
                   p<=e->previous_end[f] && r>=0 && r<525 && p>=0 && p<525;
        valid[f][y]=available;
        still[f][y][x]=available &&
            (unsigned)abs((int)e->current_luma[r*C+x]-e->previous_luma[p*C+x])<=tolerance;
    }
    /* Search every shift with visible overlap. A local minimum does not
     * exclude a remote match. Confirm the candidate against every alternative
     * on pairwise IDENTICAL support at both times; ties, missing static
     * evidence and comparison cycles never confirm a lock. */
    int best=bias<0?0:bias;
    bool observed=false;
    for(int q=-(H-2);q<=H-2;++q){
        comb_pair_reading p=comb_pair(e,start,valid,still,best,q);
        if(!p.samples)continue;
        observed=true;
        /* Candidate means from DIFFERENT supports are not comparable.
         * Tournament comparisons share the same pixels; a genuine strict
         * pairwise winner survives regardless of enumeration order. */
        if(p.energy[0][1]<p.energy[0][0])best=q;
    }
    if(!observed)return result;
    comb_pair_reading own=comb_pair(e,start,valid,still,best,best);
    result.best=own.energy[0][0];result.second=HUGE_VAL;
    result.fraction=(double)own.samples/(H*C);
    double limiting_margin=HUGE_VAL;
    bool unique=true;
    for(int q=-(H-2);q<=H-2;++q)if(q!=best){
        comb_pair_reading p=comb_pair(e,start,valid,still,best,q);
        if(!p.possible)continue;
        if(!p.samples){unique=false;++result.unresolved;continue;}
        double margin=p.energy[0][1]-p.energy[0][0];
        if(margin<limiting_margin){
            limiting_margin=margin;
            result.best=p.energy[0][0];result.second=p.energy[0][1];
            result.fraction=(double)p.samples/(H*C);
        }
        if(fmax(p.energy[0][0],p.energy[1][0])>=fmin(p.energy[0][1],p.energy[1][1])){
            unique=false;++result.unresolved;
        }
    }
    if(!isfinite(result.second)){result.second=0;return result;}
    result.measured=unique;result.shift=best;return result;
}

/* Rule 8: geometry is an observation before a lock, not an applied crop.
 * Both acquisition paths run before this commit point. The comb may test a
 * proposed crop, but only a lock can commit it to analysis-owned placement. */
static void apply_locked_geometry(field_registration *e, fieldreg_decision *out)
{
    for (int f = 0; f < 2; ++f) {
        fieldreg_field_decision *d = &out->field[f];
        if (e->field[f].lock_state == FIELDREG_LOCK_UNLOCKED) {
            d->applied_d = e->field[f].last_applied;
            d->gauge = FIELDREG_GAUGE_HOLD;
            if (d->measured_d != FIELDREG_UNKNOWN)
                d->reason = FIELDREG_MODE_ACQUIRING;
        } else {
            e->field[f].last_applied = d->applied_d;
        }
    }
    out->applied_d1 = out->field[0].applied_d;
    out->applied_d2 = out->field[1].applied_d;
    out->baseline_d1 = out->applied_d1;
    out->baseline_d2 = out->applied_d2;
}

static void comb_confirm(field_registration *e,const uint8_t *raster,
                         const field_measurement m[2],fieldreg_decision *out)
{
    comb_lowpass(e,raster);
    int start[2]={FIELDREG_FIELD1_START+out->applied_d1,FIELDREG_FIELD2_START+out->applied_d2};
    int begin[2],end[2];
    for(int f=0;f<2;++f){
        begin[f]=m[f].top>=0?m[f].top:start[f];
        end[f]=m[f].switch_measurable?m[f].bottom:m[f].recorded_last;
    }
    bool settled=e->parity_state==FIELDREG_PARITY_CALIBRATED;
    const bool was_settled=settled;
    int bias=settled?e->comb_zero_candidate:-1;
    comb_reading standard={0}, r={0};
    if(e->previous_luma_valid){
        if(!settled){
            const int nominal[2]={FIELDREG_FIELD1_START,FIELDREG_FIELD2_START};
            standard=comb_search(e,nominal,begin,end,-1);
        }
        r=(!settled && out->applied_d1==0 && out->applied_d2==0)?
                         standard:comb_search(e,start,begin,end,bias);
        if(r.measured){
            int order=settled?bias:(r.shift==1?1:0);
            int standard_order=standard.shift-(out->applied_d2-out->applied_d1);
            if(!settled && r.shift==order && standard.measured && standard_order==order &&
               m[0].geometry_measurable && m[1].geometry_measurable &&
               m[0].switch_measurable && m[1].switch_measurable){
                e->comb_zero_candidate=(int16_t)order;
                e->parity_state=FIELDREG_PARITY_CALIBRATED;settled=true;
                for(int f=0;f<2;++f)if(e->field[f].lock_state==FIELDREG_LOCK_UNLOCKED){
                    e->field[f].switch_line_count=m[f].observed_switch_line_count;
                    e->field[f].switch_line_count_known=true;
                    e->field[f].lock_state=FIELDREG_LOCK_LOCKED;
                    e->field[f].top=m[f].top;e->field[f].zero_source=FIELDREG_ZERO_COMB;
                    out->field[f].lock_state=FIELDREG_LOCK_LOCKED;
                    out->field[f].lock_switch_line_count=m[f].observed_switch_line_count;
                    out->field[f].lock_switch_line_count_known=true;
                    out->field[f].lock_top=m[f].top;out->field[f].zero_source=FIELDREG_ZERO_COMB;
                    out->field[f].switch_count_agrees=true;
                }
            }
        }
    }
    apply_locked_geometry(e,out);
    const int applied[2]={FIELDREG_FIELD1_START+out->applied_d1,
                          FIELDREG_FIELD2_START+out->applied_d2};
    if(e->previous_luma_valid){
        /* Acquisition above inspected the geometry proposal. If the gate
         * rejected it, report the comb on the HELD crop, not that proposal.
         * Reuse the already measured standard reading when applicable. */
        if(applied[0]!=start[0] || applied[1]!=start[1])
            r=(!was_settled && out->applied_d1==0 && out->applied_d2==0)?
                standard:comb_search(e,applied,begin,end,
                                     settled?e->comb_zero_candidate:-1);
        out->comb_check=FIELDREG_COMB_FLAT;
        out->comb_best_energy=r.best;out->comb_second_energy=r.second;
        out->comb_static_fraction=r.fraction;
        out->comb_unresolved_alternatives=r.unresolved;
        int order=settled?e->comb_zero_candidate:(r.shift==1?1:0);
        if(r.fraction>0)out->comb_candidate_shift=(int16_t)(r.shift-order);
        if(r.measured){
            out->parity_bias=(int8_t)order;
            out->comb_best_shift=(int16_t)(r.shift-order);
            out->comb_check=out->comb_best_shift==0?FIELDREG_COMB_AGREE:FIELDREG_COMB_DISAGREE;
            out->comb_safe=settled && out->comb_check==FIELDREG_COMB_AGREE;
            out->parity_state=settled && out->comb_check==FIELDREG_COMB_DISAGREE?
                              FIELDREG_PARITY_DRIFT:e->parity_state;
        }
    }
    if(e->parity_state==FIELDREG_PARITY_CALIBRATED)out->parity_bias=(int8_t)e->comb_zero_candidate;
    memcpy(e->previous_luma,e->current_luma,sizeof e->previous_luma);
    for(int f=0;f<2;++f){e->previous_crop[f]=(int16_t)applied[f];
        e->previous_begin[f]=(int16_t)begin[f];e->previous_end[f]=(int16_t)end[f];}
    e->previous_luma_valid=true;
}

static void v10_reset_field(fieldreg_field_state *state, bool reset_applied,
                            int field)
{
    const int8_t applied = reset_applied ? 0 : state->last_applied;
    const uint32_t lock_id = state->lock_id + 1;
    memset(state, 0, sizeof *state);
    state->top = field == 0 ? FIELDREG_PICTURE_ORIGIN_F1 :
                              FIELDREG_PICTURE_ORIGIN_F2;
    state->switch_line_count = -1;
    state->clip_ceiling = -1;
    state->clip_candidate = -1;
    state->zero_candidate = INT16_MIN;
    state->clip_candidate_d = FIELDREG_UNKNOWN;
    state->previous_measured_top = -1;
    state->last_applied = applied;
    /* A source lock does not exist until current-unit geometry is confirmed
     * at a unit whose switch line and band are measurable (contract rule 4).
     * The standard origin is the applied crop until confirmation; a measured
     * current-unit edge remains an observation even while application holds. */
    state->lock_state = FIELDREG_LOCK_UNLOCKED;
    state->zero_source = FIELDREG_ZERO_STANDARD;
    state->lock_id = lock_id;
}

fieldreg_config fieldreg_default_config(void)
{
    fieldreg_config result = {0};
    return result;
}

size_t fieldreg_state_size(void) { return sizeof(field_registration); }
size_t fieldreg_config_size(void) { return sizeof(fieldreg_config); }
size_t fieldreg_decision_size(void) { return sizeof(fieldreg_decision); }
uint32_t fieldreg_algorithm_version(void) { return FIELDREG_ALGORITHM_VERSION; }

uint32_t fieldreg_confirmation_units(const field_registration *engine)
{
    (void)engine;
    return 1;
}

uint32_t fieldreg_buffer_units(const field_registration *engine)
{
    (void)engine;
    return 0;
}

void fieldreg_init(field_registration *engine, const fieldreg_config *config)
{
    memset(engine, 0, sizeof *engine);
    engine->config = config ? *config : fieldreg_default_config();
    v10_reset_field(&engine->field[0], true, 0);
    v10_reset_field(&engine->field[1], true, 1);
    engine->parity_state = FIELDREG_PARITY_UNCALIBRATED;
    engine->comb_zero_candidate = INT16_MIN;
    engine->comb_correction_candidate = FIELDREG_UNKNOWN;
}

void fieldreg_begin_segment(field_registration *engine)
{
    ++engine->segment_id;
    v10_reset_field(&engine->field[0], true, 0);
    v10_reset_field(&engine->field[1], true, 1);
    engine->previous_luma_valid = false;
    engine->parity_state = FIELDREG_PARITY_UNCALIBRATED;
    engine->comb_zero_candidate = INT16_MIN;
    engine->comb_candidate_count = 0;
    engine->comb_correction = 0;
    engine->comb_correction_candidate = FIELDREG_UNKNOWN;
    engine->comb_correction_candidate_count = 0;
}

void fieldreg_discontinuity(field_registration *engine)
{
    /* Rule 5 will distinguish transport damage from lock-like loss.  Rule 1
     * only guarantees that stale temporal observations cannot place a unit. */
    engine->previous_luma_valid = false;
    engine->field[0].previous_measured_top = -1;
    engine->field[1].previous_measured_top = -1;
}

static void v10_copy_state(const fieldreg_field_state *state,
                           fieldreg_field_decision *decision)
{
    decision->lock_state = state->lock_state;
    decision->zero_source = state->zero_source;
    decision->lock_id = state->lock_id;
    decision->lock_top = state->top;
    decision->lock_switch_line_count = state->switch_line_count;
    decision->lock_switch_line_count_known =
        state->switch_line_count_known;
    decision->clip_state = FIELDREG_CLIP_UNKNOWN;
    decision->clip_ceiling = -1;
}

static fieldreg_confirmation caption_confirmation(
    const field_measurement *measurement, int field, int geometry_d,
    fieldreg_field_decision *decision)
{
    if (measurement->off_count > 1)
        return FIELDREG_CONFIRM_AMBIGUOUS;
    if (measurement->off_count == 1) {
        const int insert = field == 0 ? FIELDREG_INSERT_F1 :
                                        FIELDREG_INSERT_F2;
        const int caption_d = measurement->off_candidate.raster_row - insert;
        decision->gauge_row = measurement->off_candidate.raster_row;
        decision->gauge_byte1 = measurement->off_candidate.byte1;
        decision->gauge_byte2 = measurement->off_candidate.byte2;
        decision->gauge_amplitude = measurement->off_candidate.amplitude;
        if (geometry_d == FIELDREG_UNKNOWN)
            return FIELDREG_CONFIRM_AMBIGUOUS;
        return caption_d == geometry_d ? FIELDREG_CONFIRM_AGREES :
                                         FIELDREG_CONFIRM_DISAGREES;
    }
    if (measurement->insert_present &&
        (measurement->insert_byte1 != 0x80 ||
         measurement->insert_byte2 != 0x80))
        return FIELDREG_CONFIRM_AMBIGUOUS;
    return FIELDREG_CONFIRM_NOT_APPLICABLE;
}

static void v10_decide_field(fieldreg_field_state *state,
                             const field_measurement *measurement, int field,
                             fieldreg_field_decision *decision)
{
    memset(decision, 0, sizeof *decision);
    decision->measured_d = FIELDREG_UNKNOWN;
    decision->geometry_d = FIELDREG_UNKNOWN;
    decision->gauge_row = -1;
    decision->expected_bottom = -1;
    decision->recorded_first = measurement->recorded_first;
    decision->recorded_last = measurement->recorded_last;
    decision->raw_top = measurement->top;
    decision->raw_bottom = measurement->bottom;
    decision->switch_line = measurement->switch_line;
    decision->first_full_other_head_line =
        measurement->first_full_other_head_line;
    decision->rf_peak_line = measurement->rf_peak_line;
    decision->rf_peak_position = measurement->rf_peak_position;
    decision->raw_span = measurement->span;
    decision->picture_rows = measurement->picture_rows;
    decision->band_extent = measurement->band_extent;
    decision->observed_switch_line_count =
        measurement->observed_switch_line_count;
    decision->switch_signature = measurement->switch_signature;
    decision->switch_measurable = measurement->switch_measurable;
    decision->geometry_measurable = measurement->geometry_measurable;
    decision->box_detected = measurement->box_detected;
    decision->blank_mean = measurement->blank_mean;
    decision->blank_chroma_noise = measurement->blank_chroma_noise;
    decision->body_shift = FIELDREG_UNKNOWN;
    decision->body_reference_top = state->previous_measured_top;
    decision->body_implied_top = -1;
    decision->measured_picture_top = measurement->top;
    decision->picture_position_valid = measurement->geometry_measurable;
    decision->insert_present = measurement->insert_present;
    decision->insert_byte1 = measurement->insert_byte1;
    decision->insert_byte2 = measurement->insert_byte2;
    decision->parity_candidate_count = measurement->off_count;
    decision->fallback_candidate_count = measurement->fallback_count;

    const int origin = field == 0 ? FIELDREG_PICTURE_ORIGIN_F1 :
                                    FIELDREG_PICTURE_ORIGIN_F2;
    if (measurement->geometry_measurable) {
        const int geometry_d = measurement->top - origin;
        decision->expected_bottom =
            (int16_t)(measurement->top + FIELDREG_FIELD_LINES - 1);
        if (measurement->recorded_last >= 0 &&
            decision->expected_bottom > measurement->recorded_last)
            decision->lines_lost =
                (int16_t)(decision->expected_bottom -
                          measurement->recorded_last);
        if (measurement->switch_measurable)
            decision->invariant_residual =
                (int16_t)(measurement->picture_rows +
                          measurement->observed_switch_line_count -
                          FIELDREG_FIELD_LINES);
        if (crop_fits_raster(field, geometry_d)) {
            decision->geometry_d = (int8_t)geometry_d;
            decision->measured_d = (int8_t)geometry_d;
            decision->applied_d = (int8_t)geometry_d;
            decision->reason = FIELDREG_MODE_GEOMETRY_PLACEMENT;
            decision->gauge = FIELDREG_GAUGE_GEOMETRY;
            state->previous_measured_top = measurement->top;
        } else {
            decision->applied_d = state->last_applied;
            decision->reason = FIELDREG_MODE_OUT_OF_RANGE_HOLD;
            decision->gauge = FIELDREG_GAUGE_HOLD;
            state->previous_measured_top = -1;
        }
    } else {
        decision->applied_d = state->last_applied;
        decision->reason = FIELDREG_MODE_GEOMETRY_UNMEASURABLE;
        decision->gauge = FIELDREG_GAUGE_HOLD;
        state->previous_measured_top = -1;
    }

    decision->caption_confirmation = caption_confirmation(
        measurement, field, decision->geometry_d, decision);

    /* Rule 4: the switch-line count is acquired once, from a unit where the
     * geometry is complete and independently confirmed.  A pass-through
     * caption can provide that confirmation; comb_confirm supplies the
     * independent static-weave path. Later observations are
     * comparisons against the frozen count, never learning samples. */
    if (state->lock_state == FIELDREG_LOCK_UNLOCKED &&
        measurement->switch_measurable &&
        decision->caption_confirmation == FIELDREG_CONFIRM_AGREES) {
        state->switch_line_count = measurement->observed_switch_line_count;
        state->switch_line_count_known = true;
        state->lock_state = FIELDREG_LOCK_LOCKED;
        state->top = measurement->top;
    }
    if (state->lock_state == FIELDREG_LOCK_LOCKED &&
        state->switch_line_count_known && measurement->switch_measurable) {
        decision->switch_count_agrees =
            measurement->observed_switch_line_count ==
            state->switch_line_count;
        decision->switch_count_conflict = !decision->switch_count_agrees;
        decision->picture_rows =
            (int16_t)(FIELDREG_FIELD_LINES - state->switch_line_count);
        decision->invariant_residual =
            (int16_t)(measurement->observed_switch_line_count -
                      state->switch_line_count);
        if (decision->switch_count_conflict)
            decision->reason = FIELDREG_MODE_SWITCH_COUNT_CONFLICT;
    }
    v10_copy_state(state, decision);
}

bool fieldreg_process(field_registration *engine,
                      const uint8_t unit[FIELDREG_UNIT_BYTES],
                      fieldreg_decision *out)
{
    if (!engine || !out || !valid_unit(unit)) return false;
    memset(out, 0, sizeof *out);
    out->decision_d1 = out->decision_d2 = FIELDREG_UNKNOWN;
    out->frame_observation_d1 = out->frame_observation_d2 = FIELDREG_UNKNOWN;
    out->comb_best_shift = FIELDREG_COMB_UNKNOWN;
    out->comb_candidate_shift = FIELDREG_COMB_UNKNOWN;
    out->transport_ok = true;
    out->segment_id = engine->segment_id;
    out->parity_state = engine->parity_state;
    out->comb_check = FIELDREG_COMB_NOT_APPLICABLE;

    const uint8_t *raster = unit + FIELDREG_HEADER_BYTES;
    field_measurement measurement[2];
    measure_field(raster, 0, &measurement[0]);
    measure_field(raster, 1, &measurement[1]);
    if(measurement[0].box_detected || measurement[1].box_detected){
        /* A previously accepted non-boxed lock cannot authorize this class.
         * Preserve the analysis-owned applied crop; no box placement exists.
         * Extent validity through fades is not inferred from this verdict. */
        for(int f=0;f<2;++f){
            engine->field[f].lock_state=FIELDREG_LOCK_UNLOCKED;
            engine->field[f].switch_line_count_known=false;
            engine->field[f].switch_line_count=-1;
        }
        engine->parity_state=FIELDREG_PARITY_UNCALIBRATED;
    }
    for (int f = 0; f < 2; ++f)
        out->geometry_observation_changed[f] =
            measurement[f].geometry_measurable &&
            engine->field[f].previous_measured_top >= 0 &&
            measurement[f].top != engine->field[f].previous_measured_top;
    v10_decide_field(&engine->field[0], &measurement[0], 0,
                     &out->field[0]);
    v10_decide_field(&engine->field[1], &measurement[1], 1,
                     &out->field[1]);

    out->applied_d1 = out->field[0].applied_d;
    out->applied_d2 = out->field[1].applied_d;
    out->baseline_d1 = out->applied_d1;
    out->baseline_d2 = out->applied_d2;
    comb_confirm(engine,raster,measurement,out);
    out->decision_d1 = out->field[0].measured_d;
    out->decision_d2 = out->field[1].measured_d;
    out->frame_observation_d1 = out->decision_d1;
    out->frame_observation_d2 = out->decision_d2;
    out->frame_observation_support =
        (out->decision_d1 != FIELDREG_UNKNOWN) +
        (out->decision_d2 != FIELDREG_UNKNOWN);
    out->mode = out->field[0].reason == out->field[1].reason ?
                out->field[0].reason : FIELDREG_MODE_MIXED_FIELD_DECISION;
    out->confidence = out->frame_observation_support > 0 ? 1.0 : 0.0;
    out->geometry_lock_known =
        engine->field[0].lock_state == FIELDREG_LOCK_LOCKED &&
        engine->field[1].lock_state == FIELDREG_LOCK_LOCKED;
    return true;
}

const char *fieldreg_mode_name(fieldreg_mode mode)
{
    switch (mode) {
    case FIELDREG_MODE_INVALID_UNIT: return "InvalidUnit";
    case FIELDREG_MODE_ACQUIRING: return "Acquiring";
    case FIELDREG_MODE_GEOMETRY_PLACEMENT: return "GeometryPlacement";
    case FIELDREG_MODE_LINE21_PLACEMENT: return "Line21Placement";
    case FIELDREG_MODE_GEOMETRY_LOCK_DECIDES: return "GeometryLockDecides";
    case FIELDREG_MODE_FIELD2_ENVELOPE_PLACEMENT: return "Field2EnvelopePlacement";
    case FIELDREG_MODE_INSERT_ABSENT: return "InsertAbsent";
    case FIELDREG_MODE_GEOMETRY_UNMEASURABLE: return "GeometryUnmeasurable";
    case FIELDREG_MODE_LOCK_BROKEN: return "LockBroken";
    case FIELDREG_MODE_LINE21_AMBIGUOUS: return "Line21Ambiguous";
    case FIELDREG_MODE_OUT_OF_RANGE_HOLD: return "OutOfRangeHold";
    case FIELDREG_MODE_LINE22_DATA_PRESENT: return "Line22DataPresent";
    case FIELDREG_MODE_GAUGE_CONFLICT: return "GaugeConflict";
    case FIELDREG_MODE_CAPTION_ONLY_MOTION: return "CaptionOnlyMotion";
    case FIELDREG_MODE_CAPTION_BODY_DISAGREE: return "CaptionBodyDisagree";
    case FIELDREG_MODE_ANCHOR_UNCORROBORATED: return "AnchorUncorroborated";
    case FIELDREG_MODE_TOP_BODY_DISAGREE: return "TopBodyDisagree";
    case FIELDREG_MODE_BODY_ONLY_PLACEMENT: return "BodyOnlyPlacement";
    case FIELDREG_MODE_COMMON_MODE_BODY_HOLD: return "CommonModeBodyHold";
    case FIELDREG_MODE_FIELD2_COMB_CALIBRATION: return "Field2CombCalibration";
    case FIELDREG_MODE_ZERO_CONFLICT: return "ZeroConflict";
    case FIELDREG_MODE_ZERO_CANDIDATE: return "ZeroCandidate";
    case FIELDREG_MODE_ZERO_OUT_OF_BOUNDS: return "ZeroOutOfBounds";
    case FIELDREG_MODE_TOP_UNCORROBORATED: return "TopUncorroborated";
    case FIELDREG_MODE_TOP_COMB_CORROBORATED: return "TopCombCorroborated";
    case FIELDREG_MODE_TOP_COMB_VETOED: return "TopCombVetoed";
    case FIELDREG_MODE_TOP_ONLY: return "TopOnly";
    case FIELDREG_MODE_COMB_RELATIVE_CORRECTION: return "CombRelativeCorrection";
    case FIELDREG_MODE_SWITCH_COUNT_CONFLICT: return "SwitchCountConflict";
    case FIELDREG_MODE_MIXED_FIELD_DECISION: return "MixedFieldDecision";
    }
    return "Unknown";
}

const char *fieldreg_gauge_name(fieldreg_gauge_source source)
{
    switch (source) {
    case FIELDREG_GAUGE_NONE: return "None";
    case FIELDREG_GAUGE_CEA608_PARITY: return "CEA608Parity";
    case FIELDREG_GAUGE_GEOMETRY: return "Geometry";
    case FIELDREG_GAUGE_FIELD2_ENVELOPE: return "Field2Envelope";
    case FIELDREG_GAUGE_LINE22_DATA: return "Line22Data";
    case FIELDREG_GAUGE_HOLD: return "Hold";
    case FIELDREG_GAUGE_STATIC_COMB: return "StaticComb";
    }
    return "Unknown";
}

const char *fieldreg_lock_state_name(fieldreg_lock_state state)
{
    switch (state) {
    case FIELDREG_LOCK_UNLOCKED: return "Unlocked";
    case FIELDREG_LOCK_LOCKED: return "Locked";
    }
    return "Unknown";
}

const char *fieldreg_clip_state_name(fieldreg_clip_state state)
{
    switch (state) {
    case FIELDREG_CLIP_UNKNOWN: return "ClipUnknown";
    case FIELDREG_CLIP_FITTING: return "ClipFitting";
    case FIELDREG_CLIP_FITTED: return "ClipFitted";
    }
    return "Unknown";
}

const char *fieldreg_zero_source_name(fieldreg_zero_source source)
{
    switch (source) {
    case FIELDREG_ZERO_NONE: return "None";
    case FIELDREG_ZERO_STANDARD: return "Standard";
    case FIELDREG_ZERO_PARITY: return "Parity";
    case FIELDREG_ZERO_ENVELOPE: return "Envelope";
    case FIELDREG_ZERO_COMB: return "Comb";
    }
    return "Unknown";
}

const char *fieldreg_parity_state_name(fieldreg_parity_state state)
{
    switch (state) {
    case FIELDREG_PARITY_UNCALIBRATED: return "Uncalibrated";
    case FIELDREG_PARITY_CALIBRATED: return "Calibrated";
    case FIELDREG_PARITY_DRIFT: return "Drift";
    }
    return "Unknown";
}

const char *fieldreg_comb_check_name(fieldreg_comb_check check)
{
    switch (check) {
    case FIELDREG_COMB_NOT_APPLICABLE: return "n.a.";
    case FIELDREG_COMB_AGREE: return "agree";
    case FIELDREG_COMB_DISAGREE: return "disagree";
    case FIELDREG_COMB_FLAT: return "flat";
    }
    return "unknown";
}

const char *fieldreg_insert_relation_name(fieldreg_insert_relation relation)
{
    switch (relation) {
    case FIELDREG_INSERT_RELATION_NONE: return "None";
    case FIELDREG_INSERT_CORROBORATES: return "InsertCorroborates";
    case FIELDREG_INSERT_CONTRADICTED: return "InsertContradicted";
    }
    return "Unknown";
}

const char *fieldreg_confirmation_name(fieldreg_confirmation confirmation)
{
    switch (confirmation) {
    case FIELDREG_CONFIRM_NOT_APPLICABLE: return "n.a.";
    case FIELDREG_CONFIRM_AGREES: return "agrees";
    case FIELDREG_CONFIRM_DISAGREES: return "disagrees";
    case FIELDREG_CONFIRM_AMBIGUOUS: return "ambiguous";
    }
    return "unknown";
}

const char *fieldreg_switch_signature_name(fieldreg_switch_signature signature)
{
    switch (signature) {
    case FIELDREG_SWITCH_NONE: return "None";
    case FIELDREG_SWITCH_FULL_OTHER_HEAD: return "FullOtherHead";
    case FIELDREG_SWITCH_BLANKING_PARTIAL: return "BlankingPartial";
    }
    return "Unknown";
}
