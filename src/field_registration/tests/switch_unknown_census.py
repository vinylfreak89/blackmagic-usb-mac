#!/usr/bin/env python3
"""Instrument the actual C predicates in a scratch build, never change them.

All counts are execution-path evidence, not adjudications of what a raw row IS.
First zero in the ordered candidate funnel is a mutually exclusive field cause;
a candidate accepted then cleared is reported separately. No detector thresholds
or harness readings participate. Run on an original, provenance-complete CAP1.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import subprocess


def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("capture", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--previous", type=Path, help="previous counter,field,T,S export")
    args = ap.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    tests = Path(__file__).resolve().parent
    engine = tests.parent
    source = (engine / "field_registration.c").read_text()
    source_hash = hashlib.sha256(source.encode()).hexdigest()
    source = replace_once(source, "static void measure_switch(", """
typedef struct {
    unsigned rows, readable, complete, basis, disjoint, prefix_free;
    unsigned previous_veto, accepted, returned;
    int last_accepted, last_returned;
} switch_audit;
static switch_audit audit;
static void measure_switch(""")
    source = replace_once(source,
        "if(departure>=0 && phase_overlap(&p,&departure_basis))\n            departure=full=-1;",
        "if(departure>=0 && phase_overlap(&p,&departure_basis)) {\n"
        "    ++audit.returned; audit.last_returned=row+4; departure=full=-1;\n}")
    source = replace_once(source,
        "const bool current_full=p.readable", """
        ++audit.rows;
        if(p.readable)++audit.readable;
        if(p.readable && p.complete_interval)++audit.complete;
        if(p.readable && p.complete_interval && basis.readable) {
            ++audit.basis;
            if(!phase_overlap(&p,&basis)) {
                ++audit.disjoint;
                if(!retains_normal_prefix(&p,&basis,&p,informative_columns))
                    ++audit.prefix_free;
            }
        }
        const bool current_full=p.readable""")
    source = replace_once(source, "if(current_full && !(previous.readable", """
        if(current_full && previous.readable && !previous_partial &&
           phase_overlap(&p,&previous))++audit.previous_veto;
        if(current_full && !(previous.readable""")
    source = replace_once(source, "full=row;", "++audit.accepted; audit.last_accepted=row+4; full=row;")
    (out / "instrumented_engine.c").write_text(source)
    probe = (tests / "switch_probe.c").read_text()
    probe = replace_once(probe, '#include "../field_registration.c"',
                         '#include "instrumented_engine.c"')
    probe = replace_once(probe, '#include "../../signal_state/signal_state.h"',
                         '#include "signal_state.h"')
    probe = replace_once(probe, "static FILE *geometry;",
                         "static FILE *geometry;\nstatic FILE *causes;")
    probe = replace_once(probe, "field_measurement m;measure_field(unit->bytes+48,f,&m);",
                         "audit=(switch_audit){.last_accepted=-1,.last_returned=-1};\n"
                         "field_measurement m;measure_field(unit->bytes+48,f,&m);\n" + r'''
        fprintf(causes,"%u,%d,%d,%d,%d,%d,%d,%u,%u,%u,%u,%u,%u,%u,%u,%u,%d,%d\n",
            unit->counter16,f+1,m.box_detected,m.top<0?-1:m.top+4,
            m.switch_line<0?-1:m.switch_line+4,
            m.first_full_other_head_line<0?-1:m.first_full_other_head_line+4,
            measured,audit.rows,audit.readable,audit.complete,audit.basis,
            audit.disjoint,audit.prefix_free,audit.previous_veto,audit.accepted,audit.returned,
            audit.last_accepted,audit.last_returned);
''')
    probe = replace_once(probe, "probe_signal=aligned_alloc", r'''
    snprintf(path,sizeof path,"%s/causes.csv",directory);causes=fopen(path,"w");assert(causes);
    fputs("counter,field,box,top,T,S,registration_measured,rows,readable,complete,basis,disjoint,prefix_free,previous_veto,accepted,returned,last_accepted,last_returned\n",causes);
    probe_signal=aligned_alloc''')
    probe = replace_once(probe, "free(parser);free(probe_signal);",
                         "assert(!fclose(causes));free(parser);free(probe_signal);")
    # Separate per-unit scalar outcome, so restoring observations cannot hide
    # accidental acquisition or movement. Nothing from the raster is exported.
    probe = replace_once(probe, 'if(unit->counter16<selected_first',
                         'fprintf(stderr,"OUTCOME %u %d %d %d\\n",unit->counter16,'
                         'measured?d.geometry_lock_known:0,measured?d.applied_d1:0,'
                         'measured?d.applied_d2:0);\n'
                         'if(unit->counter16<selected_first')
    (out / "probe.c").write_text(probe)
    src = engine.parent
    subprocess.run(["clang", "-O3", "-std=c11", "-Wall", "-Wextra", "-Werror",
        f"-I{engine}", f"-I{src / 'signal_state'}", f"-I{src / 'unit_parser'}",
        f"-I{src / 'capture_core'}", str(out / "probe.c"), str(engine / "cea608.c"),
        str(src / "signal_state/signal_state.c"), str(src / "unit_parser/unit_parser.c"),
        "-lm", "-o", str(out / "probe")], check=True)
    with (out / "live.csv").open("w") as log, (out / "outcomes.txt").open("w") as outcomes:
        # Counter16 cannot equal 65536: disables probe's optional raw export.
        subprocess.run([str(out / "probe"), str(args.capture), "65536", "65536", str(out)],
                       stdout=log, stderr=outcomes, check=True)
    rows = [r for r in csv.DictReader((out / "causes.csv").open()) if int(r["counter"]) >= 6667]
    rows.sort(key=lambda r: (int(r["counter"]), int(r["field"])))
    assert len(rows) == len({(r["counter"], r["field"]) for r in rows}) == 1016
    for filename, gated in [("engine_switch.csv", False), ("engine_switch_live_gated.csv", True)]:
        with (out / filename).open("w") as f:
            w = csv.writer(f); w.writerow(["counter", "field", "T", "S"])
            for r in rows:
                t, s = (r["T"], r["S"]) if not gated or int(r["registration_measured"]) else (-1, -1)
                w.writerow([r["counter"], r["field"], t, s])
    previous = {}
    if args.previous:
        previous = {(r["counter"], r["field"]): r for r in csv.DictReader(args.previous.open())}
    def cause(r):
        stages = [int(r[k]) for k in ["rows", "readable", "complete", "basis", "disjoint", "prefix_free", "accepted"]]
        assert stages == sorted(stages, reverse=True)
        assert int(r["prefix_free"]) == int(r["previous_veto"]) + int(r["accepted"])
        if int(r["T"]) >= 0: return "measured"
        if int(r["top"]) < 0: return "no_picture_top"
        for column in ["rows", "readable", "complete", "basis", "disjoint", "prefix_free", "accepted"]:
            if not int(r[column]): return "no_" + column
        assert int(r["returned"])
        return "accepted_then_returned"
    counts = Counter()
    for r in rows:
        r["cause"] = cause(r)
        key = (r["counter"], r["field"])
        old = previous.get(key)
        r["previous_nonbox_unknown"] = int(bool(old and int(old["T"]) < 0 and not int(r["box"])))
        if r["previous_nonbox_unknown"]:
            counts[(r["field"], r["cause"])] += 1
    with (out / "unknown_causes.csv").open("w") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    summary = {"engine_sha256": source_hash, "rows": len(rows),
               "previous_nonbox_unknown": {f"f{f}:{c}": n for (f,c),n in sorted(counts.items())},
               "current_causes": dict(Counter(r["cause"] for r in rows))}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
