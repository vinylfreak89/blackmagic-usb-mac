# Registration test entry points

`make test` runs `field_registration_unit` (18 checks), `cea608_unit` (3), and
`field_registration_v9` (194 golden rows). See [V9_TRUTH.md](V9_TRUTH.md).
The raw/CSV fixture is generated as a pair through `ensure_v9_fixture.py`;
missing or stale members, or interrupted publication, regenerate both.

The former `field_registration_truth`, `field_registration_trajectory` and
`field_registration_golden` harnesses and their two exclusive generators were
retired because they address removed trajectory/FIFO and Python-port APIs.
They remain in git at `f504c16:src/field_registration/tests/`.
Their trajectory abstention/dwell, backdating, relative-gauge provenance and
port-equality expectations are historical policies, not current-engine gates.
Current placement, reset/discontinuity, clipping and decoder checks live in
the unit/v9 suites; this cleanup does not reintroduce retired policy.
The former truth harness's timing report is not the frameserver worker budget
gate; that remains `make -C src/frameserver bench`.

Generated legacy raw/CSV files are not deleted by this retirement or by `clean`.
