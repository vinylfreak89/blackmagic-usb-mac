#!/usr/bin/env python3
"""Export the published crop starts of a registration sidecar for the geometry harness.
Output columns (NTSC lines): ordinal,published_f1_start,published_f2_start = 23+applied_d1, 286+applied_d2 for every
exact (kind 0) row. The sidecar's ordinal must be the transport ordinal (device-short units counted), which the
prototype writes since 056dc45. Usage: crops_from_sidecar.py <sidecar.csv> <crops.csv>"""
import sys, csv
F1_ORIGIN_LINE=23; F2_ORIGIN_LINE=286   # STANDARD (SMPTE RP-202 480i lattice)
rows=[r for r in csv.DictReader(open(sys.argv[1])) if r.get('kind','0')=='0']
w=csv.writer(open(sys.argv[2],'w',newline='')); w.writerow(['ordinal','published_f1_start','published_f2_start'])
for r in rows: w.writerow([r['ordinal'], F1_ORIGIN_LINE+int(r['applied_d1']), F2_ORIGIN_LINE+int(r['applied_d2'])])
print('wrote',len(rows),'rows')
