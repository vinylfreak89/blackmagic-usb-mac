#!/usr/bin/env python3
"""The Python mirror must agree with field_lines.h on all 525 rows, or the harness is guessing."""
import subprocess, tempfile, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from field_lines_py import row_to_field, row_to_line

HDR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "src", "field_registration")
SRC = r'''
#include <stdio.h>
#include "field_lines.h"
int main(void){char b[FIELDREG_LINE_LABEL_BYTES];
 for(int r=0;r<525;r++){int f=fieldreg_format_row_line(b,r);printf("%d %d %s\n",r,f,b);}
 return 0;}
'''
with tempfile.TemporaryDirectory() as d:
    c = os.path.join(d, "m.c"); open(c, "w").write(SRC)
    exe = os.path.join(d, "m")
    subprocess.run(["cc", "-O1", "-I", HDR, "-o", exe, c], check=True)
    out = subprocess.run([exe], capture_output=True, text=True, check=True).stdout
bad = []
for ln in out.strip().split("\n"):
    r, f, lab = ln.split()
    r = int(r); f = int(f)
    if row_to_field(r) != f or row_to_line(r) != lab:
        bad.append((r, f, lab, row_to_field(r), row_to_line(r)))
if bad:
    for b in bad[:10]: print("MISMATCH row %d: C f%d %s / py f%d %s" % b)
    print("%d of 525 rows disagree" % len(bad)); raise SystemExit(1)
print("OK: the Python mirror matches field_lines.h on all 525 rows")
