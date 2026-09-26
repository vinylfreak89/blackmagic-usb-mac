/* Private helpers are tested in this translation unit, not exported as API. */
#include "../signal_state.c"
#include <assert.h>
#include <pthread.h>
#include <stdio.h>

static void defaults(void)
{
    signal_state_config c = signal_state_default_config();
    assert(c.appearance_confirm_units == 2 && c.acquisition_confirm_units == 5);
    assert(c.mute_confirm_units == 3 && c.phase_chatter_window_units == 30);
    assert(c.phase_chatter_threshold == 4 && c.settle_confirm_units == 30);
    assert(c.tile_activity_min == 12);
    assert(c.flat_luma_distance_max == 2.0);
    assert(c.neutral_chroma_distance_max == 4);
    assert(c.subblack_luma_cutoff == 16);
    assert(c.overlay_static_mad_max == 3.0);
    assert(c.overlay_extent_rise == 0.02);
    assert(c.overlay_extent_fall_start == 0.35);
    assert(c.overlay_extent_fall_width == 0.25);
    assert(c.padding_fraction_min == 0.98);
    assert(c.padding_confidence_gain == 10.0);
    assert(c.neutral_chroma_median_max == 4.0);
    assert(c.neutral_chroma_fraction_min == 0.75);
    assert(c.subblack_median_max == 12.0);
    assert(c.subblack_confidence_luma_reference == 16.0);
    assert(c.subblack_confidence_luma_span == 8.0);
    assert(c.subblack_confidence_fraction_offset == 0.70);
    assert(c.snow_sigma_min == 35.0);
    assert(c.snow_gradient_min == 30.0);
    assert(c.snow_extent_min == 0.50);
    assert(c.snow_confidence_sigma_offset == 30.0);
    assert(c.snow_confidence_sigma_span == 25.0);
    assert(c.snow_confidence_gradient_offset == 25.0);
    assert(c.snow_confidence_gradient_span == 30.0);
    assert(c.gray_sigma_max == 3.0);
    assert(c.gray_gradient_max == 2.0);
    assert(c.gray_flat_fraction_min == 0.55);
    assert(c.gray_extent_max == 0.30);
    assert(c.gray_temporal_mad_max == 3.0);
    assert(c.gray_mean_min == 8.0);
    assert(c.gray_mean_max == 240.0);
    assert(c.gray_confidence_flat_offset == 0.50);
    assert(c.gray_confidence_flat_gain == 2.0);
    assert(c.ambiguous_extent_max == 0.12);
    assert(c.program_confidence_sigma_span == 24.0);
    assert(c.program_confidence_gradient_span == 18.0);
    assert(c.held_source_confidence == 0.5);
    assert(c.phase_change_confidence_min == 0.25);
}

/* Every appearance cutoff and confidence ramp is exercised independently. */
static void appearances(void)
{
    signal_state_config c = signal_state_default_config(), d = c;
    signal_measurements m = {.hard_padding_fraction=1, .neutral_chroma_fraction=1,
        .luma_mean=100, .luma_median=100, .luma_sigma=2, .spatial_gradient_energy=1,
        .program_extent_fraction=.6, .flat_pixel_fraction=.6};
    double confidence;
#define CLASSIFY() classify_appearance(&c,&m,&confidence)
#define LABEL(field,value,label) do { c=d;c.field=value;assert(CLASSIFY()==label); } while(0)
    assert(CLASSIFY()==SIGNAL_APPEARANCE_NEUTRAL_GRAY_MUTE_LIKE);
    LABEL(padding_fraction_min,1.1,SIGNAL_APPEARANCE_UNKNOWN);
    LABEL(neutral_chroma_median_max,-1,SIGNAL_APPEARANCE_PROGRAM_LIKE);
    LABEL(neutral_chroma_fraction_min,1.1,SIGNAL_APPEARANCE_PROGRAM_LIKE);
    LABEL(subblack_median_max,100,SIGNAL_APPEARANCE_SUBBLACK_MUTE_LIKE);
    LABEL(gray_sigma_max,2,SIGNAL_APPEARANCE_PROGRAM_LIKE);
    LABEL(gray_gradient_max,1,SIGNAL_APPEARANCE_PROGRAM_LIKE);
    LABEL(gray_mean_min,101,SIGNAL_APPEARANCE_PROGRAM_LIKE);
    LABEL(gray_mean_max,99,SIGNAL_APPEARANCE_PROGRAM_LIKE);
    m.luma_sigma=40;m.spatial_gradient_energy=40;
    c=d;assert(CLASSIFY()==SIGNAL_APPEARANCE_SNOW_LIKE);
    LABEL(snow_sigma_min,40,SIGNAL_APPEARANCE_PROGRAM_LIKE);
    LABEL(snow_gradient_min,40,SIGNAL_APPEARANCE_PROGRAM_LIKE);
    LABEL(snow_extent_min,.6,SIGNAL_APPEARANCE_PROGRAM_LIKE);
#define CONF(field,value) do { c=d;CLASSIFY();double prior=confidence;c.field=value;CLASSIFY();assert(confidence!=prior); } while(0)
    CONF(snow_confidence_sigma_offset,39);
    CONF(snow_confidence_sigma_span,100);
    CONF(snow_confidence_gradient_offset,39);
    CONF(snow_confidence_gradient_span,100);
    m.hard_padding_fraction=.9;
    CONF(padding_confidence_gain,1);
    m.hard_padding_fraction=1;m.luma_median=12;m.subblack_pixel_fraction=.8;
    CONF(subblack_confidence_luma_reference,14);
    CONF(subblack_confidence_luma_span,16);
    CONF(subblack_confidence_fraction_offset,.8);
    m.luma_median=100;m.luma_sigma=4;m.spatial_gradient_energy=3;
    m.program_extent_fraction=.2;m.temporal_mad=1;
    c=d;assert(CLASSIFY()==SIGNAL_APPEARANCE_NEUTRAL_GRAY_MUTE_LIKE);
    LABEL(gray_flat_fraction_min,.6,SIGNAL_APPEARANCE_PROGRAM_LIKE);
    LABEL(gray_extent_max,.2,SIGNAL_APPEARANCE_PROGRAM_LIKE);
    LABEL(gray_temporal_mad_max,1,SIGNAL_APPEARANCE_PROGRAM_LIKE);
    CONF(gray_confidence_flat_offset,.4);
    CONF(gray_confidence_flat_gain,1);
    m.neutral_chroma_fraction=0;m.program_extent_fraction=.1;
    c=d;assert(CLASSIFY()==SIGNAL_APPEARANCE_FLAT_AMBIGUOUS);
    LABEL(ambiguous_extent_max,.1,SIGNAL_APPEARANCE_PROGRAM_LIKE);
    m.program_extent_fraction=.6;
    m.luma_sigma=12;m.spatial_gradient_energy=3;
    CONF(program_confidence_sigma_span,48);
    m.luma_sigma=4;m.spatial_gradient_energy=12;
    CONF(program_confidence_gradient_span,9);
#undef CLASSIFY
#undef LABEL
#undef CONF
}

static double overlay_measure(signal_state *s, uint8_t *unit, const signal_state_config *c)
{
    signal_measurements m;
    signal_state_init(s,c);measure_raster(s,unit,&m);
    for(int r=0;r<RASTER_LINES;r++)if(sampled_picture_line(r))
        for(int x=0;x<X_SAMPLES;x++)s->previous[r][x]--;
    measure_raster(s,unit,&m);return m.localized_overlay_score;
}

static void measurement(void)
{
    signal_state *s=malloc(sizeof *s);uint8_t *unit=calloc(1,HEADER_BYTES+RASTER_LINES*BYTES_PER_LINE);
    assert(s&&unit);
    for(int r=0;r<RASTER_LINES;r++)for(int x=0;x<RASTER_WIDTH;x++) {
        uint8_t *p=unit+HEADER_BYTES+r*BYTES_PER_LINE+2*x;
        p[0]=132;p[1]=hard_line_expected(r)?16:((x/4)%2?20:8);
    }
    signal_state_config c=signal_state_default_config();
    signal_measurements a,b;
    signal_state_init(s,&c);measure_raster(s,unit,&a);
    assert(a.neutral_chroma_fraction==1 && a.subblack_pixel_fraction==.5);
    assert(a.program_extent_fraction==1 && a.flat_pixel_fraction==0);
    c.neutral_chroma_distance_max=3;c.subblack_luma_cutoff=8;
    c.tile_activity_min=13;c.flat_luma_distance_max=6;
    signal_state_init(s,&c);measure_raster(s,unit,&b);
    assert(b.neutral_chroma_fraction==0 && b.subblack_pixel_fraction==0);
    assert(b.program_extent_fraction==0 && b.flat_pixel_fraction==1);
    /* Unrelated statistics and padding stay unchanged. */
    assert(a.luma_mean==b.luma_mean && a.luma_sigma==b.luma_sigma);
    assert(a.hard_padding_fraction==b.hard_padding_fraction);
    for(int r=0;r<RASTER_LINES;r++)for(int x=0;x<RASTER_WIDTH;x++)
        unit[HEADER_BYTES+r*BYTES_PER_LINE+2*x+1]=
            hard_line_expected(r)?16:(r>=20&&r<=35&&x<24?32:20);
    c=signal_state_default_config();double score=overlay_measure(s,unit,&c);assert(score>0);
#define OVERLAY(field,value) do {c=signal_state_default_config();c.field=value;assert(overlay_measure(s,unit,&c)!=score);} while(0)
    OVERLAY(overlay_static_mad_max,6);
    OVERLAY(overlay_extent_rise,.04);
    OVERLAY(overlay_extent_fall_start,.01);
    OVERLAY(overlay_extent_fall_width,1);
#undef OVERLAY
    free(unit);free(s);
}

static void *instance(void *arg)
{
    double value=*(double*)arg;
    signal_state *s=malloc(sizeof *s);assert(s);
    signal_state_config c=signal_state_default_config();
    c.gray_mean_min=value;c.phase_change_confidence_min=value/100;
    signal_state_init(s,&c);c.gray_mean_min=-1;
    for(unsigned i=0;i<100;i++) {
        signal_state_begin_epoch(s,i);
        assert(s->config.gray_mean_min==value);
        assert(s->config.phase_change_confidence_min==value/100);
        s->stable_source=SIGNAL_SOURCE_PRESENT;s->phase_valid=true;
        signal_result r={0};
        signal_state_note_registration(s,&r,true,1,0,.5,true,0,0);
        assert((s->phase_change_bits&1)==(value<=50));
        s->stable_source=SIGNAL_SOURCE_MUTED;
        unit_video_observation u={0};signal_context ctx={.host_raster_unobserved=true};
        s->config.held_source_confidence=.2;
        assert(signal_state_classify(s,&u,&ctx,&r)&&r.source_confidence==.2);
    }
    free(s);return NULL;
}

int main(void)
{
    defaults();appearances();measurement();
    pthread_t a,b;double x=25,y=75;
    assert(!pthread_create(&a,NULL,instance,&x));assert(!pthread_create(&b,NULL,instance,&y));
    assert(!pthread_join(a,NULL));assert(!pthread_join(b,NULL));
    signal_state *s=malloc(sizeof *s);assert(s);signal_state_init(s,NULL);
    assert(s->config.padding_fraction_min==0.98);
    signal_state_config c=signal_state_default_config();
    c.appearance_confirm_units=0;c.phase_chatter_window_units=100;c.phase_chatter_threshold=100;
    signal_state_init(s,&c);assert(s->config.appearance_confirm_units==2);
    assert(s->config.phase_chatter_window_units==64 && s->config.phase_chatter_threshold==64);
    free(s);puts("signal_config_test: PASS");return 0;
}
