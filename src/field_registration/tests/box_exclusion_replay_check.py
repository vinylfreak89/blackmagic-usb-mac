"""Check box exclusions in the commercial live-path record; report coverage.

The named card interval is a fixture annotation, not a production parameter.
Full card exclusion remains a failing acceptance until the residual is closed.
"""
import csv
import sys

with open(sys.argv[1], newline='') as f:
    rows = list(csv.DictReader(f))
assert rows and all(None not in r and all(v is not None for v in r.values()) for r in rows)
assert all(r['schema_version'] == '19' for r in rows)
for key in ('applied_d1', 'applied_d2', 'geometry_lock_known'):
    assert all(r[key] == '0' for r in rows), key
card = [r for r in rows if 6665 <= int(r['counter_extended']) <= 6810]
assert len(card) == 146
failed = False
for field in (1, 2):
    p = f'f{field}_'
    observed = [r for r in rows if r[p+'box_detected'] == '1']
    for r in observed:
        assert r[p+'switch_measurable'] == '0' and r[p+'switch_line'] == '-1'
        assert r[p+'geometry_measurable'] == '0' and r[p+'geometry_d'] == '-128'
    print(f'field {field}: observed boxes {len(observed)}, '
          f'card exclusions {sum(r[p+"box_detected"] == "1" for r in card)} / {len(card)}')
    for r in card:
        if r[p+'switch_measurable'] == '1':
            print(f'FAIL: card switch evidence remains at field {field} counter {r["counter_extended"]}')
            failed = True
print(f'{len(rows)} observations; zero locks and nonzero crops; all positive box observations exclude switch and placement')
raise SystemExit(1 if failed else 0)
