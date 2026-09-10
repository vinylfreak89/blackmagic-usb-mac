#!/usr/bin/env python3
"""Scratch-only 6-sigma ablation. This is NOT a production tolerance proposal.

The multiplier is the harness instrument's reported choice, not a standard.
No gaps are bridged: membership becomes a measured mean +/- 6 sigma band.
Interior-only preserves exact porch membership; all also changes porches.
"""
import csv
from pathlib import Path
import argparse
import subprocess


def variant(header, scope):
    if scope == "strict":
        return header
    old = "    run_profile p={.start=-1};"
    assert header.count(old) == 1
    header = header.replace(old, old + r'''
    unsigned allowed[256]={0}; double n=0,sum=0,square=0;
    for(int k=0;k<256;++k) {
        n+=blank[k];sum+=(double)k*blank[k];square+=(double)k*k*blank[k];
    }
    double mean=sum/n, sigma=sqrt(fmax(0,square/n-mean*mean));
    /* DIAGNOSTIC ONLY: harness's six-sigma band, no fitted sigma floor. */
    for(int k=0;k<256;++k)allowed[k]=fabs(k-mean)<=6*sigma;
''')
    for old in ["blank[line[2*x+1]]"] + (["blank[line[2*p.left+1]]",
            "blank[line[2*(H_SAMPLES-1-p.right)+1]]"] if scope == "all" else []):
        assert old in header
        header = header.replace(old, old.replace("blank[", "allowed["))
    if scope == "interior":
        # Exact porches and tolerant runs now have different alphabets. Keep
        # BOTH endpoints exposed under the candidate's own alphabet; otherwise
        # an excluded first sample falsely turns a prefix into an interior run.
        old = "if(n>=H_BLANK) {"
        assert header.count(old) == 1
        header = header.replace(old, "if(n>=H_BLANK && start>0 && x<H_SAMPLES &&\n"
            "           !allowed[line[2*(start-1)+1]] && !allowed[line[2*x+1]]) {")
    return header


def reference_trace(probe, reference):
    """Reference S selects a diagnostic row only, NEVER an engine candidate."""
    rows = {}
    with Path(reference).open() as f:
        for r in csv.DictReader(f):
            if int(r["counter"]) >= 6667:
                rows.setdefault(int(r["counter"]), [-1, -1])[int(r["field"])-1] = int(r["S"])
    table = "static const int reference_s[65536][2]={\n" + "\n".join(
        f"[{c}]={{{v[0]},{v[1]}}}," for c,v in sorted(rows.items())) + "\n};\n"
    helper = r'''
static FILE *membership;
static void membership_row(const uint8_t *raster,unsigned counter,int field) {
    int line=reference_s[counter][field];if(counter<6667 || line<4)return;
    unsigned alphabet[256]={0};double n=0,sum=0,square=0;
    for(int r=field?270:7;r<=(field?278:15);++r)for(int x=0;x<720;++x) {
        unsigned y=raster[(size_t)r*1440+2*x+1];++alphabet[y];++n;sum+=y;square+=y*y;
    }
    double mean=sum/n,sigma=sqrt(fmax(0,square/n-mean*mean));
    const uint8_t *p=raster+(size_t)(line-4)*1440;
    int length[3]={0},start[3]={-1,-1,-1};
    for(int mode=0;mode<3;++mode) {
        int run=0;
        for(int x=0;x<720;++x) {
            unsigned y=p[2*x+1];
            bool yes=mode==0?alphabet[y]>0:fabs(y-mean)<=6*(mode==2?fmax(sigma,0.5):sigma);
            run=yes?run+1:0;
            if(run>length[mode]) {length[mode]=run;start[mode]=x-run+1;}
        }
    }
    /* Third column set reproduces the census's stated instrument floor;
     * never feeds candidate membership or any engine decision. */
    fprintf(membership,"%u,%d,%d,%.9f,%.9f,%d,%d,%d,%d,%d,%d\n",counter,field+1,line,
        mean,sigma,start[0],length[0],start[1],length[1],start[2],length[2]);
}
'''
    probe = probe.replace("static field_registration engine;", table+helper+"static field_registration engine;")
    probe = probe.replace("        run_counter=0;", "        run_counter=0;membership_row(unit->bytes+48,unit->counter16,f);")
    probe = probe.replace("    probe_signal=aligned_alloc", r'''
    snprintf(path,sizeof path,"%s/membership.csv",directory);membership=fopen(path,"w");assert(membership);
    fputs("counter,field,S,blank_mean,blank_sigma,strict_start,strict_length,band_start,band_length,floored_start,floored_length\n",membership);
    probe_signal=aligned_alloc''')
    probe = probe.replace("free(parser);free(probe_signal);", "assert(!fclose(membership));free(parser);free(probe_signal);")
    return probe


def controls(output):
    engine = Path(__file__).resolve().parent.parent
    for scope in ["strict", "interior", "all"]:
        out = output.resolve() / ("controls-" + scope)
        out.mkdir(parents=True, exist_ok=True)
        for name in ["field_registration.c", "run_timing.h"]:
            source = (engine / name).read_text()
            if name == "run_timing.h":
                source = variant(source, scope)
            (out / name).write_text(source)
        common = ["clang", "-O3", "-std=c11", "-Wall", "-Wextra", "-Werror",
                  f"-I{engine}", f'-DFIELDREG_TEST_IMPLEMENTATION="{out}/field_registration.c"']
        for test in ["run_timing_test", "run_tolerance_controls"]:
            defines = ["-DEXPECT_TOLERANT_RECOVERY"] if scope == "all" and test == "run_tolerance_controls" else []
            subprocess.run(common + defines + [str(engine / "tests" / (test + ".c")),
                str(engine / "cea608.c"), "-lm", "-o", str(out / test)], check=True)
            result = subprocess.run([str(out / test)], capture_output=True, text=True)
            (out / (test + ".log")).write_text(result.stdout + result.stderr)
            print(scope, test, "exit", result.returncode, result.stdout, result.stderr)
            result.check_returncode()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controls", type=Path, required=True)
    controls(parser.parse_args().controls)
