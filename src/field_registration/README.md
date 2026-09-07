# Registration v10: geometry first

`field_registration` corrects independent whole-line vertical displacement of
the two NTSC fields in one exact 756,048-byte Shuttle unit. It never
deinterlaces, allocates on the unit path, retains input, duplicates a line, or
manufactures pixels. Positive `d` selects a later whole UYVY source line.

The normative design is [`../../docs/geometry_first_engine.md`](../../docs/geometry_first_engine.md).
The implementation is landing one rule at a time with a failing golden before
each rule.

## Implemented: rule 1

Measurable current-unit geometry is the sole placement authority. The field's
measured top, bottom, and span are recorded; its top against the standard
23/286 origin supplies the provisional crop until the conserved line account
lands in rules 3–4. A caption cannot place, veto, hold, re-anchor, or otherwise
mutate a crop. Its decoded row and bytes are retained as an explicit
`agrees`/`disagrees`/`ambiguous` confirmation. Geometry is measured without
using a decoded caption row to choose where its top scan begins.

The round-10 body veto, caption placement, zero re-anchoring, comb calibration,
and comb crop-correction paths have been removed from the compiled engine.
Body and comb confirmation will return only as the contract defines them; they
currently report no observation. Acquisition/reset/damage behavior still has
the inherited placeholder state and is implemented by rules 5–6, after the
line account and fixed switch-line count.

The frameserver decision log is schema 10. Each per-field group adds
`caption_confirmation`; line-valued fields remain NTSC line numbers.

Build and run the current suite with:

```sh
make -C src/field_registration test
```

The retired v9 fixture remains available only as a contradiction inventory:
`make -C src/field_registration v9-test`. It is deliberately not part of the
v10 pass suite because it encodes the authority hierarchy prohibited by the
current contract.
