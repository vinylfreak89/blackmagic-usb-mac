# Signal-state acceptance: no change may trade one error for another

Owner, 2026-09-09, on the classifier work that follows the whole-tape audit: **"any changes should
not introduce false positives (or false negatives)."** That is only checkable against a measured
baseline, so this is the baseline.

`fixture_a_units.csv` lists unit ranges of fixture A whose answer is known, each with what confirmed
it. Unit index = device counter − 4511.

| class | units | means |
|---|---|---|
| `not_program` | 315 | confirmed on the raw raster as mute, black, snow or torn. The classifier must never call these normal picture, and once rule 5 lands registration must not run on them. |
| `program` | 108 | confirmed on the raw raster as dark or low-contrast programme. No mute or no-input label may remain or appear here. |
| `boundary` | 17 | the relock ramps at the end of an event, where coherence is climbing from the event's floor to settled picture. Scored in neither direction, because demanding a verdict in a genuinely gradual transition is how a fix buys recall with false positives. |

`score.py <decision.csv>` scores a whole-tape `frameserver_replay` log against it and prints three
counts. Against the build at `44cfb94`: **MISSED 17, FALSE_MUTE 108, UNGATED 270.** Neither of the
first two may rise; UNGATED must reach 0 once rule 5 lands.

It fails closed. A duplicate counter, an unparseable row, or a fixture unit the log never mentions
is an error rather than a skipped row. A fixture unit that IS in the log but is device-short or
unframed is reported as not applicable, because it carries no fixed raster to classify — absent
because it cannot be measured is not the same as absent because the run did not cover it.

## What this is not

The audit that produced it is an instrument, not truth, and it said so: its temporal threshold has
no density valley behind it, two of its runs were settled only by looking at the raster, and its
chroma gate is measured on this deck. So the fixture carries only ranges confirmed on the raw
raster, and the boundary class exists for the places where the instrument itself could not draw a
line. Extending it means looking at rasters, not lowering a threshold until the count moves.
