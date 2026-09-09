/* Reuse the constructed raster and public-path helpers, not a mocked lock. */
#define main comb_regression_main
#include "comb_test.c"
#undef main

int main(void)
{
    fieldreg_init(&engine, NULL);
    const int offsets[] = {1, 3, 0, 1};
    for (unsigned i = 0; i < sizeof offsets / sizeof offsets[0]; ++i) {
        make_unit(offsets[i], 0, true); /* Measurable edges, no static detail. */
        fieldreg_decision d = run();
        check("unconfirmed geometry stays observable",
              d.field[0].geometry_d == offsets[i] &&
              d.field[1].geometry_d == offsets[i]);
        check("flat picture supplies no lock", !d.geometry_lock_known &&
              d.field[0].lock_state == FIELDREG_LOCK_UNLOCKED &&
              d.field[1].lock_state == FIELDREG_LOCK_UNLOCKED);
        check("unlocked_geometry_cannot_move_output",
              d.applied_d1 == 0 && d.applied_d2 == 0 &&
              engine.field[0].last_applied == 0 &&
              engine.field[1].last_applied == 0);
        check("unlocked hold is labelled",
              d.field[0].reason == FIELDREG_MODE_ACQUIRING &&
              d.field[1].gauge == FIELDREG_GAUGE_HOLD);
    }

    /* The gate must not turn the existing comb acquisition into a dead end:
     * standard output on the first unit, proposed geometry on confirmation. */
    fieldreg_begin_segment(&engine);
    make_unit(0, 0, false);
    fieldreg_decision d = run();
    check("first detailed unit still holds", !d.geometry_lock_known &&
          d.applied_d1 == 0 && d.applied_d2 == 0);
    d = run();
    check("comb acquisition still applies its confirmed geometry",
          d.geometry_lock_known && d.comb_check == FIELDREG_COMB_AGREE &&
          d.applied_d1 == 0 && d.applied_d2 == 0);
    make_unit(1, 0, false); d = run();
    check("locked geometry still tracks", d.geometry_lock_known &&
          d.applied_d1 == 1 && d.applied_d2 == 1);
    fieldreg_begin_segment(&engine);
    make_unit(3, 0, true); d = run();
    check("loss restores standard until re-acquisition",
          !d.geometry_lock_known && d.applied_d1 == 0 && d.applied_d2 == 0);
    printf("UNLOCKED-PLACEMENT: %u/%u passed\n", checks-failures, checks);
    return failures ? 1 : 0;
}
