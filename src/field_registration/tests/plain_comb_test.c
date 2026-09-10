/* Plain-comb public-path controls. No captured picture is embedded here. */
#define main historical_comb_main
#include "comb_test.c"
#undef main

int main(void)
{
    fieldreg_init(&engine, NULL);
    make_unit(0, 0, false);
    fieldreg_decision d = run();
    check("plain_comb_reads_first_unit_without_temporal_witness",
          d.comb_check == FIELDREG_COMB_AGREE);
    check("plain_comb_confirms_measured_geometry", d.geometry_lock_known);

    /* Independently perturb every picture row between units. A temporal
     * equality mask against synthetic blanking must not veto this reader. */
    for (int f = 0; f < 2; ++f)
        for (int r = (f ? 282 : 19); r < (f ? 519 : 256); ++r)
            for (int x = 4; x < 715; ++x)
                unit[48 + r*1440 + 2*x + 1] += (uint8_t)((r+x)%3);
    fieldreg_begin_segment(&engine);
    d = run();
    check("current_unit_energy_needs_no_static_mask",
          d.comb_check == FIELDREG_COMB_AGREE && d.geometry_lock_known);
    check("no_static_fraction_is_claimed", d.comb_static_fraction == 0.0);

    fieldreg_begin_segment(&engine);
    make_unit(0, -4, false);
    d = run();
    check("remote_relative_error_remains_visible",
          d.comb_check == FIELDREG_COMB_DISAGREE && d.comb_best_shift == 4);
    check("comb_error_cannot_install_a_crop",
          !d.geometry_lock_known && d.applied_d1 == 0 && d.applied_d2 == 0);

    fieldreg_begin_segment(&engine);
    make_unit(0, 0, true);
    d = run();
    check("equal_energies_do_not_confirm",
          d.comb_check == FIELDREG_COMB_FLAT && !d.geometry_lock_known);

    fieldreg_begin_segment(&engine);
    make_unit(200, 0, false);
    d = run();
    check("unplaceable_geometry_cannot_acquire", !d.geometry_lock_known &&
          d.applied_d1 == 0 && d.applied_d2 == 0);

    /* An ordinary, detailed full-picture source, no synthetic switch rows.
     * Its current geometry and comb must suffice without inventing a count. */
    for (int switches = 0; switches < 3; ++switches) {
        fieldreg_begin_segment(&engine);
        make_unit(0, 0, false);
        for (int f = 0; f < 2; ++f) if (!(switches & (1 << f)))
            for (int y = 237; y < 240; ++y) for (int x = 0; x < 720; ++x) {
                int v = picture(y+10, x);
                if (f) v = (v+picture(y+11, x))/2;
                if (x < 4 || x >= 715) v = 2;
                unit[48+((f?282:19)+y)*1440+2*x+1] = (uint8_t)v;
            }
        d = run();
        check("lock_does_not_require_two_measurable_switches", d.geometry_lock_known);
        for (int f = 0; f < 2; ++f) {
            bool present = (switches & (1 << f)) != 0;
            check("only_a_measured_switch_supplies_a_count",
                  d.field[f].switch_measurable == present &&
                  d.field[f].lock_switch_line_count_known == present &&
                  (present || d.field[f].lock_switch_line_count == -1));
        }
        /* Deliberately wrong field interleave after a lock. The engine must
         * not even evaluate it, not merely suppress a correction afterward. */
        make_unit(0, -4, false);
        d = run();
        check("maintained_lock_does_not_evaluate_comb",
              d.geometry_lock_known && d.comb_check == FIELDREG_COMB_NOT_EVALUATED &&
              d.comb_best_shift == FIELDREG_COMB_UNKNOWN &&
              d.comb_best_energy == 0 && !d.comb_safe);
        check("maintained_lock_has_no_comb_correction", d.comb_correction == 0 &&
              d.applied_d1 == 0 && d.applied_d2 == 0);
    }
    printf("PLAIN-COMB: %u/%u passed\n", checks-failures, checks);
    return failures ? 1 : 0;
}
