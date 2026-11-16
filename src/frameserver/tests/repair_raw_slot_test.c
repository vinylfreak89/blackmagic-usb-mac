/* A repair candidate dropped at push (item ring full, live) must give back its raw slot: otherwise four such drops stop
 * repair for the rest of the session. Built with RING_ITEMS=4 and replayed unpaced into a slow sink so the ring overflows;
 * includes frameserver.c to read the raw slots after fs_stop has drained both workers. Usage: repair_raw_slot_test CAP. */
#include "../frameserver.c"
#include <unistd.h>
static _Atomic int done;
static void on_end(void *c, enum cc_end r){ (void)c; done = 1 + (int)r; }
static void on_frame(void *c, const fp_frame *fr){ (void)c; (void)fr; usleep(20000); }
int main(int argc, char **argv){
    if (argc != 2){ fprintf(stderr, "usage: %s capture.tpc\n", argv[0]); return 2; }
    ge_config geo = ge_default_config();
    fs_config cfg = {0}; cfg.geometry_config = &geo; cfg.capture.replay_path = argv[1]; cfg.on_end = on_end;
    cfg.registration_off = 1; cfg.show_partial = 1; cfg.repair_units = 1; cfg.pool_units = 8;
    cfg.sink.on_frame = on_frame;
    frameserver *f; if (fs_open(&f, &cfg) || fs_start(f)){ fprintf(stderr, "open/start failed\n"); return 1; }
    while (!done) usleep(20000);
    fs_stop(f);
    fs_stats s; fs_get_stats(f, &s);
    unsigned held = 0; for (unsigned i = 0; i < f->n_raw; i++) held += (unsigned)atomic_load(&f->raw_used[i]);
    printf("repair raw slots: ring drops %llu, put back %llu, not tried %llu, raw slots held after stop %u of %u\n",
           (unsigned long long)s.dropped_ring_full, (unsigned long long)s.repaired_units, (unsigned long long)s.repair_skipped, held, f->n_raw);
    int ok = s.dropped_ring_full > 0 && held == 0 && s.repair_skipped == 0;
    fs_close(f);
    puts(ok ? "repair_raw_slot_test: PASS" : "repair_raw_slot_test: FAIL");
    return ok ? 0 : 1;
}
