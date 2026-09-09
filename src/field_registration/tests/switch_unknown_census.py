#!/usr/bin/env python3
"""Instrument the actual C predicates in a scratch build, never change them.

All counts are execution-path evidence, not adjudications of what a raw row IS.
First zero in the ordered candidate funnel is a mutually exclusive field cause;
a candidate accepted then cleared is reported separately. No detector thresholds
or harness readings participate. Run on an original, provenance-complete CAP1.
The run-stage trace writes scalar candidate rows; timings in this instrumented
build include tracing and must not be reported as production performance.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import subprocess


def instrument_run_header(engine, out):
    """Trace production predicates without replacing any decision expression.

    The funnel is ordered run-first for diagnosis, although production's AND
    tests basis first. Candidate rows also retain independent positional facts.
    Output is enabled only during the probe's independent per-field call.
    """
    header = (engine / "run_timing.h").read_text()
    header = '#include <stdio.h>\n#include <assert.h>\n' + header
    header = replace_once(header, "static void measure_run_switch(", r'''
static FILE *run_fields, *run_candidates;
static unsigned run_counter;
static struct {
    unsigned rows, candidate, unique, basis, leading, trailing, prior;
    unsigned alphabet, cdf, accepted, returned;
} run_audit;

static void audit_run_row(int field,int row,const run_profile *p,
    bool basis,int left,int right,const run_profile *previous,
    bool prior_normal,bool prior_partial,int compatible,double delta,double envelope)
{
    if(!run_counter)return;
    ++run_audit.rows;
    if(p->runs>0) {
        ++run_audit.candidate;
        fprintf(run_candidates,"%u,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%.9f,%.9f\n",
            run_counter,field+1,row+4,p->runs,p->start,p->length,p->left,p->right,
            basis,basis?left:-1,basis?right:-1,previous->left,previous->right,
            prior_normal,prior_partial,compatible,delta,envelope);
        if(p->runs==1) {
            ++run_audit.unique;
            if(basis) {
                ++run_audit.basis;
                if(p->left==0) {
                    ++run_audit.leading;
                    if(p->right<right) {
                        ++run_audit.trailing;
                        if(prior_normal || prior_partial) {
                            ++run_audit.prior;
                            assert(compatible>=0);
                            if(compatible) {
                                ++run_audit.alphabet;
                                if(delta<=envelope)++run_audit.cdf;
                            }
                        }
                    }
                }
            }
        }
    }
}

static void measure_run_switch(''')
    header = replace_once(header, "            t=s=-1;",
                          "            {if(run_counter)++run_audit.returned; t=s=-1;}")
    header = replace_once(header, "        if(full && (prior_normal || prior_partial)) {",
                          "        int audit_compatible=-1; double audit_delta=-1,audit_envelope=-1;\n"
                          "        if(full && (prior_normal || prior_partial)) {")
    header = replace_once(header, "            if(compatible && delta<=envelope) {",
                          "            audit_compatible=compatible; audit_delta=delta; audit_envelope=envelope;\n"
                          "            if(compatible && delta<=envelope) {\n"
                          "                if(run_counter)++run_audit.accepted;")
    header = replace_once(header, "        history[next]=previous;previous=p;",
                          "        audit_run_row(field,row,&p,basis,left,right,&previous,\n"
                          "            prior_normal,prior_partial,audit_compatible,audit_delta,audit_envelope);\n"
                          "        history[next]=previous;previous=p;")
    (out / "run_timing.h").write_text(header)


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
    instrument_run_header(engine, out)
    source = (engine / "field_registration.c").read_text()
    source_hash = hashlib.sha256(source.encode()).hexdigest()
    source = '''#include <time.h>
#include <stdint.h>
static double audit_run_ms;
static uint64_t audit_run_clock(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t);
    return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec;
}
''' + source
    source = replace_once(source, "measure_run_switch(raster,field,m);",
        "uint64_t run_started=audit_run_clock();\n"
        "measure_run_switch(raster,field,m);\n"
        "audit_run_ms=(audit_run_clock()-run_started)/1e6;")
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
                         "audit=(switch_audit){.last_accepted=-1,.last_returned=-1};audit_run_ms=0;\n"
                         "memset(&run_audit,0,sizeof run_audit);run_counter=unit->counter16;\n"
                         "field_measurement m;measure_field(unit->bytes+48,f,&m);\n" + r'''
        run_counter=0;
        fprintf(run_fields,"%u,%d,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u\n",
            unit->counter16,f+1,run_audit.rows,run_audit.candidate,run_audit.unique,
            run_audit.basis,run_audit.leading,run_audit.trailing,run_audit.prior,
            run_audit.alphabet,run_audit.cdf,run_audit.accepted,run_audit.returned);
        fprintf(causes,"%u,%d,%d,%d,%d,%d,%d,%u,%u,%u,%u,%u,%u,%u,%u,%u,%d,%d,%d,%d,%d,%d,%d,%d,%.6f,%d,%.6f,%.6f\n",
            unit->counter16,f+1,m.box_detected,m.top<0?-1:m.top+4,
            m.switch_line<0?-1:m.switch_line+4,
            m.first_full_other_head_line<0?-1:m.first_full_other_head_line+4,
            measured,audit.rows,audit.readable,audit.complete,audit.basis,
            audit.disjoint,audit.prefix_free,audit.previous_veto,audit.accepted,audit.returned,
            audit.last_accepted,audit.last_returned,
            m.switch_observations.phase_t<0?-1:m.switch_observations.phase_t+4,
            m.switch_observations.phase_s<0?-1:m.switch_observations.phase_s+4,
            m.switch_observations.run_t<0?-1:m.switch_observations.run_t+4,
            m.switch_observations.run_s<0?-1:m.switch_observations.run_s+4,
            m.switch_observations.run_start,m.switch_observations.run_length,
            m.switch_observations.run_blank_distance,m.switch_observations.disagreement,audit_run_ms,
            m.switch_observations.run_blank_tolerance);
''')
    probe = replace_once(probe, "probe_signal=aligned_alloc", r'''
    snprintf(path,sizeof path,"%s/run_stages.csv",directory);run_fields=fopen(path,"w");assert(run_fields);
    fputs("counter,field,rows,candidate,unique,basis,leading,trailing,prior,alphabet,cdf,accepted,returned\n",run_fields);
    snprintf(path,sizeof path,"%s/run_candidates.csv",directory);run_candidates=fopen(path,"w");assert(run_candidates);
    fputs("counter,field,line,runs,start,length,left,right,basis,basis_left,basis_right,previous_left,previous_right,prior_normal,prior_partial,compatible,cdf_distance,cdf_envelope\n",run_candidates);
    snprintf(path,sizeof path,"%s/causes.csv",directory);causes=fopen(path,"w");assert(causes);
    fputs("counter,field,box,top,T,S,registration_measured,rows,readable,complete,basis,disjoint,prefix_free,previous_veto,accepted,returned,last_accepted,last_returned,phase_T,phase_S,run_T,run_S,run_start,run_length,run_blank_distance,disagreement,run_ms,run_blank_tolerance\n",causes);
    probe_signal=aligned_alloc''')
    probe = replace_once(probe, "free(parser);free(probe_signal);",
                         "assert(!fclose(causes));assert(!fclose(run_fields));"
                         "assert(!fclose(run_candidates));free(parser);free(probe_signal);")
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
        if int(r["phase_T"]) >= 0: return "measured"
        if int(r["top"]) < 0: return "no_picture_top"
        for column in ["rows", "readable", "complete", "basis", "disjoint", "prefix_free", "accepted"]:
            if not int(r[column]): return "no_" + column
        assert int(r["returned"])
        return "accepted_then_returned"
    counts = Counter()
    for r in rows:
        r["phase_cause"] = cause(r)
        r["cause"] = ("observation_disagreement" if int(r["disagreement"]) else
                      "run_recovered" if int(r["run_T"])>=0 and int(r["phase_T"])<0 else r["phase_cause"])
        key = (r["counter"], r["field"])
        old = previous.get(key)
        r["previous_nonbox_unknown"] = int(bool(old and int(old["T"]) < 0 and not int(r["box"])))
        if r["previous_nonbox_unknown"]:
            counts[(r["field"], r["cause"])] += 1
    with (out / "unknown_causes.csv").open("w") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    summary = {"engine_sha256": source_hash,
               "header_sha256": {name: hashlib.sha256((engine/name).read_bytes()).hexdigest()
                                  for name in ["field_registration.h", "box_observation.h", "run_timing.h"]},
               "rows": len(rows),
               "previous_nonbox_unknown": {f"f{f}:{c}": n for (f,c),n in sorted(counts.items())},
               "current_causes": dict(Counter(r["cause"] for r in rows))}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
