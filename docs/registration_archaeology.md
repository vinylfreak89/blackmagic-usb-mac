# Registration engine archaeology

Part I: how the field-registration engine went through nine versions in six days (2026-08-29 to
2026-09-04), how it derailed, and how it came back. Part II: how the ninth engine was then built
on the inverted premise and patched fourteen times in thirty hours before the owner stopped it
(2026-09-05). Merged from two independent excavations,
Claude's (from git, the CLAUDE.md narrative as written at each stage, and its session transcript)
and Codex's (from git and its own rollout records); the few places they disagreed are listed at
the end. Times are JST. Every number below is traceable to a commit, a surviving measurement file
or a timestamped transcript line; the handful that are transcript-only say so.

Attribution convention: **Owner** (Aaron) set the goals, reviewed every render, and asked the
questions that changed direction. **Codex** wrote the C engine and all of its versions. **Claude**
wrote the offline Python estimator, the instruments, the renderers and most of the documentation,
and reviewed Codex's engine work. Each version was mutually reviewed before merge.

## The phenomenon

The deck's output shows the picture "jumping" vertically by a line or two: one field's content
sits a line or two away from where the standard puts it, so the two fields of a frame no longer
interleave. For nine versions the engine tried to remove the jump by inferring where the picture
sat from the picture itself. The question that was not asked until the ninth was: *where, in the
signal, is the reference the picture is jumping relative to?*

## Where deinterlacers sit in this story

Deinterlacing is presentation, downstream of the frameserver, and it was also the lens through
which every render was judged, so it matters which lens. Two kinds were used and they behave
oppositely on a misregistered frame. **NNEDI3** interpolates each field into a full frame from
that field alone: it never combines the two fields, makes no motion decision, and invents nothing
beyond spatial interpolation, so a displaced field shows as exactly the physical jump and nothing
else. **Yadif, bwdif and estdif** are motion-adaptive weavers: they interleave the two fields
wherever they judge the picture static and interpolate where they judge it moving. On a frame
whose fields are misregistered by a line the weave combs, and the per-pixel decisions add
structure of the deinterlacer's own (bwdif and estdif produced false field inversions on fixture
A). Their output mixes the signal's error with the deinterlacer's inventions, which is why the
owner could not tell the two apart in early reviews and settled on NNEDI3 for every watch copy.
So the two have different jobs. NNEDI3 is the diagnostic lens while the engine is being built:
it cannot comb, so whatever moves in an NNEDI3 render is in the signal. A weaver is the intended
end presentation once registration works: on static picture it outputs all 480 recorded lines
with nothing interpolated, where NNEDI3 always predicts half of them, and its combing was the
weaver doing the right thing to wrong input. "No combing under yadif" is therefore the
presentation-level acceptance test for registration, and "not good enough for yadif" below was
the right bar; yadif is never registration *truth*. Earlier versions of the record said "any
deinterlacer combs", which put a class of deinterlacer artifacts on the signal's account; that
conflation was half the confusion and is corrected throughout.

## The story, item by item

### 1. "Field 2's origin drifts" (Claude, offline Python, 08-29 evening)

Comb/weave scoring over candidate field-2 origins (274–285) found the best interleave, and the
first answer was "the second field starts at a varying line" (`e811226`, 22:15). A census of the
6,160 intact units of the untagged capture killed that premise within 35 minutes (`564c0b9`,
22:50): the transport raster is rigid (`f1_origin=17` 99.35%, `f2_origin=280` 99.25%), field 2's
picture translated 0 lines in 4,042 of 4,042 rigidly measurable units, and it is **field 1's
picture that moves** by 1–2 whole lines. The 274–285 "wander" was estimator noise: 42% of the
off-263 picks had a median margin of 0.027 against 0.587 for confident picks. Comb can only ever
constrain the difference `d2 − d1`, never an absolute position.

*Right:* the error is spatial and integer-line, not temporal order or cadence. *Wrong:* it reported
an inter-field relation as an absolute position. Codex's review also caught that the correction
direction was backwards for a while (`e153b82`, 23:33).

### 2. The per-field (d1, d2) model (Claude, offline, 08-30 afternoon)

Each field's picture gets its own signed integer offset inside the rigid raster; neither field is
a permanent anchor; comb constrains `d2 − d1`, absolutes need same-parity temporal registration or
landmarks; say `Unknown` otherwise (`f936339` 15:49, `ac1e59c` 16:12). Fixture A resolves as
`d1 ∈ {0, +1, +2}, d2 = 0`, recorded as "test data, not policy". The whole-tape trace selected
`(0,0)` 63,476 times, `(1,0)` 19,265, `(2,0)` 2,315, `(3,0)` 1,244, in 2,165 constant runs of
which 1,282 lasted only 1–3 units, and that chatter was correctly labelled "an auditable correction
trace, not deck-health ground truth". Still a proxy: position was inferred from the picture's own
edges, comb and temporal correlation. The deck's regenerated VBI lines (unit rows 16 and 17) were
treated as a "transport ruler" to skip by row number, never as something the content could be
compared against.

### 3. The C engine (Codex, 08-30 21:00 to 08-31 03:01)

An allocation-free port with the same anchors (`f5b261b`, `bf3f3bc`, `0f29e37`). Compatibility
mode matched all 86,293 exact whole-tape units and all 56,441 confident offline decisions, and the
independent census 4,042/4,042, at 1.29 ms per unit. The hardened form required coherent top and
bottom landmarks and added a **differential veto**: a rigid-envelope candidate is refused when
opposite same-parity motion says the dominant picture moved differently. Agreement fell to
3,784/4,042 overall but stayed 3,499/3,499 on confident rows, with all 258 differences
conservative under-corrections and no opposite correction; 2.58 ms per unit.

*Right:* edge disagreement made explicit; a live, deterministic hot path proven; "no opposite
correction" established. *Wrong:* conservatism was already under-selection, and the 3,499/3,499
score counted only the easy rows. The ambiguous rows it ignored were where the real movement lived.

### 4. Motion phase and the 120-unit rolling mode (Codex, 09-01)

`14fe5d5` (20:39) added ±6-line motion search in three bands, cut/fade abstention, and a
120-unit `phase_history` whose majority supplied the presented phase. Whole-tape audit: 48
baseline transitions; `(0,0)` 42,767 units, `(1,0)` 43,030, `(2,0)` 496; 5,353 fast edge
candidates not applied. The cut/fade abstention survived; the rolling majority did not. It
"manufactured delayed plateaus" (Codex's own words in the successor commit): a plateau that
starts is followed only once the window's majority flips, tens of units late, and an old phase is
retained after the raster returns.

### 5. The bounded FIFO, v3 and v4 (Codex, 09-02 00:45 and 02:37)

`56892df` replaced the rolling mode with a caller-owned FIFO: a coherent current-unit observation
may correct a buffered unit immediately, a separate fallback trajectory needs 30 units of
confirmation under a 36-unit hard horizon, and settled fallbacks are backdated onto buffered
abstentions only. `2a4b23f` (v4) fixed resets so they invalidate confidence but preserve the last
presented phase; two `RawAwaitingLock` rows had snapped to `(0,0)` with no observation. The first
synthetic golden had 347 units (338/338 unambiguous, 9/9 abstentions). A six-minute production
proof went from 144 transitions and 70 short runs to 54 and five once a caller bug (rewriting
buffered abstentions to raw at every horizon) was fixed. Full v4: 2.532 ms per unit, 464 hard
resets with zero reset-induced phase changes. Forward-only presentation differed from the FIFO in
exactly 147 rows at five plateau onsets.

*Wrong anyway:* it answered "is a move real?" by waiting, which a live path cannot do. Every unit
spent waiting was a unit presented with the wrong crop. The owner's overnight brief of 09-02
already asked whether this was overengineered.

### 6. The lookback investigation (Claude and Codex, 09-02 night to 09-03 03:14)

Two independent audits of the v3/v4 sidecars, reconciled: 936 of 948 applied transitions began on
a matching current-unit observation, six were deliberate backdated locks, two were reset snaps.
The FIFO could revise abstentions but never a wrong positive: a lone `(0,1)` observation at
frame 8169 latched for 104 units. And whole-tape, 10,547 of 55,329 coherent rows had a selected
phase that contradicted both the full-width envelope and relative consensus, of which
backtracking repaired about 1%. Verdict: the dominant failure was **evidence authority** (a local
two-of-three band majority overruling an agreeing full-width envelope), not missing lookahead
(`dd60843`, `2cdf4f2`, `2133d6b`). No engine of its own; it decided v6. There was never a "v5"
in repository naming; this is the gap between v4 and v6.

### 7. Authority-first v6 (Codex, 09-03 12:48 to 14:15; owner sign-off 17:33)

Zero presentation FIFO, forward-only. A coherent full-width envelope plus relative consensus is
authoritative; coherent top+bottom motion in two broad bands with same-parity corroboration is
followed at unit rate; delta authority is bounded to one line around an absolute gauge; a stale
positive can no longer latch (`1daad46` to `3b30718`). Two-truth golden: raster 1,017/1,017 (v4:
858), oracle 1,130/1,140. Whole-tape strict-envelope disagreement 10,547 → 1,021 of 55,329;
one-field transitions followed 850 → 2,939 of 4,128; at 35–40 min follow/hold 0/1,066 → 594/438;
1.466 ms per unit.

The owner watched a full NNEDI3 copy (intra-field, so what he saw was the signal) and signed off: a large improvement, representative of a
digitally captured VHS tape, and the remaining jumps "bring new lines into the picture", i.e.
recorded-signal instability outside any integer engine (`089ea5b`). Both agents took that as
"done except the deck". **It was not**: the 09-04 raw measurements (items 12 and 13) showed the
engine abstaining on rigid whole-field shifts that are exactly what an integer engine corrects.

### 8. Relative-only v7 (Claude's diagnosis 09-03 22:13; Codex's engine 22:19 to 09-04 01:15; merged `abfa648`)

Claude ran yadif over the frameserver's own output as a stress test: it combed wherever the two
fields were still misregistered against each other, which located a residual class; the residual
itself was then measured on the raw frames, not through yadif. The "bottom landmark falls off the
raster" hypothesis was refuted (the edge moves
into rows 257/258, still measurable); the residual was a **relative-only class**: raw need 0
while the engine held `(1,0)` through 3–19 units of abstention. Of 143 classifiable residual
frames in the first 100 s, 132 were over-corrections. Instrument: `static_comb_metric.py`
(`71f2227`).

Codex wrote the goldens first (v6 scored 0/12 relative return, 0/15 gauge-unknown), then a
static-region comb estimator (8-px low-pass, static mask, ≥16-column persistence, reweave −3..+3)
that may *release* a held phase at unit rate as current-unit authority only; two threshold changes
tuned against tape were reverted before merge. Paced, zero-drop measurements: misregistered static
frames 88 → 29 (first 100 s), 17 → 13 (620 s), 803 → 268 (2,400 s credits window; the
record-aligned denominators are 2,869 → 2,865). Credits blip audit: 87 of 97 one-unit flips were
correct follows, 5 unmeasurable, 5 engine noise. Codex's engine-internal strict proxy *worsened*
1,021 → 1,128 while every measured window improved, which killed it as an acceptance criterion.
Cost 3.6 ms median. The whole-tape pair in `captures/` was re-rendered overnight with a gate
(02:53).

*Wrong anyway:* comb is content. It sees the relation between the fields and nothing about where
either sits in the raster.

### 9. The morning review and the first false alarm (Owner and Claude, 09-04 morning)

The owner: "better, but still not good enough for yadif" (the fields still disagree often enough
that a weaving deinterlacer combs). Watching frame by frame with the
sidecar overlaid (Claude's `overlay_sidecar.py`, built that morning): "the decision engine is
definitely picking up on things, it's just severely under-selecting"; almost all of its Unknown
decisions fall exactly where the raster is genuinely unstable.

Two of Claude's own tools then misled everyone. The full-raster preview keyed decisions by the
16-bit device counter, so after the wrap at 65,536 the second half of the tape overwrote the
first half's rows and the first minute rendered with decisions from 37 minutes later; the visible
jitter was reported to Codex as engine chatter. The owner's cross-check ("then why is the clip in
Documents stable?") exposed it (`f80b1f9`, 12:00). Cost: Codex's `unknown-hold` branch (12:08 to
12:12, `7991fa9`, `f605bcd`), which froze every Unknown row. The sidecar's 2,475 phase changes on
Unknown rows were a real inconsistency, but the fix worsened both presentation windows because
Unknown usually meant "the proxy failed while the raster moved". Not merged. Separately, two
renderer defects were Claude's: `capture_render.py` kept rows 17–18 fixed and remapped from 19
(duplicating row 18 on negative offsets, dropping 19 on positive), and the full-raster preview
duplicated below its window. Both replaced with pure whole-window shifts (`3b94b51`, `4f8a4d3`).
The owner's rule from this review: never duplicate lines, always shift the whole crop window,
shifting into digitally degenerate black is acceptable.

### 10. Bottom-edge v8 (Owner's rule; Claude's instrument 13:03; Codex's engine 13:16 to 15:14; never merged)

The owner's placement rule, taken literally as an instrument: per field, the crop's final line
should be the first mostly-black-luma line under the picture. Claude's `bottom_edge_census.py`
(`13320a9`) measured v7 on the first 1,800 units: the raw edge moved and the crop followed 80
times, moved and the crop held 198 times, and the crop changed on a still edge 69 times. Codex
built goldens (v7 scored 0/6 dark hold, 0/8 fade reacquisition) and an engine that learns a
per-segment lower target and applies `edge − target` at unit rate. A pure bottom-only prototype
was catastrophic on the comb metric (29 → 937 bad frames), so the shipped form kept the v7 comb
estimator to refine `d2 − d1`. Results: 29 → 5 (SP window), 268 → 138 (credits), census
214/64/34, 2.75 ms. But the registered field-1 bottom landed at 256 in 1,038 units and 255 in
546: the comb overrode the owner's rule in a third of the units. Twelve review findings across
three rounds (Claude's transcript).

The owner stopped it: "you've locked on to this bottom-edge thing. NO! You are operating on a
false premise. You have not measured the number of actual picture lines, where the top line is
and where the bottom line is." Still a proxy: one edge of one field, patched by a content-derived
relative term.

### 11. The conceptual reset (Owner, 09-04 afternoon)

"Before either of you write another line of code, agree on the PROBLEM conceptually. Write back
to me conceptually how it works. Don't iterate on the current engine. Tear it down and start
fresh." And, on both agents accepting his instructions ("drop backtracking hysteresis") without
understanding them: "the answers you are coming back with are really concerning the fuck out of
me." Also: stop committing unreproducible experiments to main (an overlay commit referencing
unmerged v8 columns was reverted).

Claude measured the raw units instead of the engine. The envelope census (`0e349c5`, 16:52; top,
bottom and height per field, both recordings): field 1 makes 199 rigid one-line moves in the
first minute (100 up, 99 down, top and bottom together, height constant), field 2 makes zero;
the EP slice at 1,300 s is rigid in both fields. A parity test on raw units: a per-field model
beats a whole-picture one-display-line shift 202–0. The owner had said "Codex keeps saying field 2
stays put, but it makes no sense"; now it was physical, and it explained why one field flipped
while the other stayed. Claude's V-sync research note (`8f58f37`) answered the mechanics but
carried the instrument's error: the census skipped rows 17 and 19 by number, reported the picture
top as row 20, and the note rationalised 20/283 as "the standard's first active lines".

### 12. The direct signal (Owner, Codex and Claude, 09-04 17:20 to 17:35)

The owner, looking at the EP render: "there are multiple sets of timing signals in the VBI: 8
short white pulses followed by 3 longer, two longer pulses above that." Then: "I thought it was
weird that I saw VBI pulses in the mute renders." He asked Codex what the fixed pulses were
according to the standard; Codex identified them as a **null CEA-608 line 21**: seven-cycle clock
run-in, start bit, two null bytes (17:34). Claude dumped the luma of rows 12–26 of raw units
(17:20): row 16 is the deck's fixed timing line; row 17 (280 for field 2) is the deck's
regenerated line-21 insert, byte-alike across the tape; the **tape's own line 21 rides exactly on
the insert when the field is correctly placed and moves with the picture when it is displaced**,
always two rows above the picture top with the black line 22 between (first minute: caption 17 /
top 19 in 50/50 units, 19 / 21 in 38/38; EP slice 17 / 19 in 500/500). Row 19 is the standard's
first visible line (SMPTE RP-202: line 23), and field 2 sits at its equivalent 282 in 1,573 of
1,800 first-minute units and 1,800 of 1,800 in the EP slice. The census was rewritten to
recognise caption and timing lines by signature wherever they land (`1756fba`, 17:31). Line-21
row sets on the SP first minute: `(17,)` 1,663 units, `(17,19)` 85, all 85 with picture
displacement +2; EP `(17,)` 1,762 (Claude's `line21_probe.py`, transcript-only). The whole-tape
census that finished that evening (CLAUDE.md §6) added the decisive negative: the SP intro's
majority picture top at row 20 has no line-21 waveform at row 18, so it is locked with a blank
line 23, and any envelope-top gauge would have called the entire intro +1.

Every render for six days had shown this on its first row. The crop started at row 17, so line 21
and the black line 22 were inside every frame, reading as "content" to the engines and as
"VBI to skip" to the instruments.

### 13. The second false alarm: crop origin versus picture origin (17:29 to 17:51)

This one was Claude's, and it confused the owner. The sequence, from both transcripts: 17:29 the
owner tells Codex "we've been rendering from line 17 instead of line 19 this entire time" and
Codex calls it a foundational mistake. 17:33 the owner tells Claude the crop should come from the
standard, not from him; Claude commits a 19/282 crop origin two minutes later (`bdac68b`),
answering with the clean aperture alone. 17:36 the owner asks Codex whether analog renders
normally show line 21 first; Codex agrees and withdraws its "foundational mistake" (17/280 is the
VBI-preserving window). 17:36:50 the owner: "but that's not the problem. OUR render is starting
at line 19", the effect of Claude's commit; Codex withdraws the 19/282 idea and proposes auditing
the renderer for a bug that does not exist. 17:38 the owner to Claude: "you are confusing both me
and yourselves." 17:39 Claude reverts (`2930095`) to match Codex's answer and tells Codex the
line-19 render was its own commit. 17:41 the owner: "so what's this about a 486 height thing
then?" and, given both standard answers, decides: **720×480 is clean aperture** (crop rows
19/282 = lines 23/286, captions out of the render); **720×486 is an alternate output mode** (lines
21–263 / 283–525, captions kept). `7285d89` restores 19/282 at 17:51.

The root fault: three coordinate systems, unit rows (17/19), the standard's line numbers
(21/23), and the deck's regenerated lines versus the tape's, all called "line N" by Claude
without saying which, plus a shared constant changed on main mid-discussion without telling the
other agent. Recorded in `LEARNINGS.md` ("two coordinates, one name").

### 14. The golden rule and the v9 plan (Owner's rule, 17:50 to 18:06; not implemented)

The owner: "the real line 21 sits on top of the deck's generated line 21, and that is also a
picture lock." "If we can't find line 21 anywhere else, even possibly on the bottom, assume it
is locked in the right place, and only change that lock if we find otherwise. That's the golden
rule." "Everything derives from that: field parity that keeps both fields aligned at the correct
picture start." "We don't need actual captions; anything that looks like that blank line-21
signal is valid." Secondary checks, never the primary gauge: leaky VBI framing data at the bottom
of the field, picture jumping above the deck's line-21 band ("video should obviously never touch
there"), and the black line 22 between.

`docs/registration_v9_plan.md` (`d61ee8e`, 18:06) records the agreed design: line 21 primary
(`d = row − 17`), the picture envelope secondary (top, bottom, height, black relative to the
field's own blanking, VBI-type lines excluded by signature), one unit of memory, no lookahead or
FIFO or backtracking, field parity as an atomic invariant, whole UYVY lines moved, every hold
named, `CaptionRelock` only when a unique off-insert caption coexists with an envelope at the
origin consistently, ambiguity classes (none, unique, duplicate, split, skewed, leaking band)
that never touch the lock or the crop. Deleted: bands, phase voting, comb authority, temporal
vetoes, candidate searches, dwell, chatter suppression, common-mode arbitration, provisional
trajectories, learned position references. Codex's plan drafts were corrected twice on the way
(envelope primary → line 21 primary; a CaptionRelock model → the golden rule). Acceptance: every
unique off-insert line 21 yields the matching displacement, registered top and bottom constant
per segment whenever height is valid, zero crop changes on a still raster, the EP leaking bands
(458 of 1,800 units with two or more, 138 with one) as negative controls, and static comb no worse
than v8's 5/2,011 and 138/2,865 without being the truth source.

## Why it derailed

Every unit carries three layered signals: the Shuttle's digital fill, the deck's regenerated
raster (sync, its timing line, its line-21 insert), and the tape's content (its line 21, the
black line 22, the picture). Registration error is the difference between the last two. Eight
versions reconstructed that difference from the picture alone, each through a proxy that responds
to content as much as to position, each patched with the next proxy:

- weave measured only `d2 − d1`;
- band votes measured whichever local edge dominated;
- same-parity temporal search measured content motion as well as raster motion;
- the rolling mode and the FIFO turned uncertain measurements into presentation policy;
- strict envelope coherence assumed the top and bottom content edges were one rigid body;
- static comb measured relative registration on static detail only;
- the bottom census took one content boundary for absolute raster position;
- the full envelope improved that to top+bottom+height but still had to guess which rows were
  picture and which were vertical-interval structure.

The proxies were not useless: they proved the transport is rigid, the motion is per field and
integer-line rather than cadence, corrections must move whole UYVY lines, and a live solution fits
the budget. They failed wherever content was flat, dark, moving, layered or clipped, which is
exactly where the engine said Unknown or picked the wrong authority. The instruments were wrong
the same way: the census skipped rows 17 and 19 by number and censored a picture top at 19; the
first VBI probe demanded caption *data* and found line 21 in a tenth of the units it was on.
Meanwhile both agents kept following the owner's instructions word for word without the model
behind them, which is what he objected to most.

The way back was not another proxy. It was the owner insisting on the concept before code,
measuring the raw rows instead of the engine, and noticing that the "nuisance VBI" at the top of
every render was the standard's own timing waveform, present on every unit, that says directly
where field 1 is.

## Where the two excavations differed

Both accounts agreed on every deciding measurement. The differences, resolved:

- **Partition.** Claude counted v1 to v8 plus v9 with a "v5" label for the lookback
  investigation; Codex split the first C engine from the rolling mode and counted the
  `unknown-hold` branch as a stage. Git supports Codex's split (`phase_history` appears in
  `14fe5d5`, not in the first C port), adopted above.
- **The v6 sign-off.** Claude's draft said the owner's "new lines, not raster" reading was
  final. Codex called it overturned by the raw parity and envelope measurements. Codex was right.
- **The `unknown-hold` detour** was missing from Claude's draft; Codex sourced it.
- **The `bdac68b` revert.** Claude's draft said Codex "found" the line-19 render; the transcripts
  show the owner reported it to Codex after seeing the effect of Claude's own commit. Corrected
  in item 13.
- **The 20/283 picture top.** Codex called it an interpretation error in the research note;
  Claude called it the census censoring row 19. Both, in sequence.
- **Sourcing.** Codex flagged the v9 labels as unsourced because its worktree lacked
  `docs/registration_v9_plan.md`; they are on main. It was right that the line-21 row-set counts
  (1,663 / 85 / 1,762) are transcript-only, and they are marked so above.

# Part II: the v9 inversion — rounds 1 to 14, 2026-09-04 11:35 to 2026-09-05 20:30

Part I ended with the ninth engine finding the reference the picture jumps against: the tape's
line 21 arriving off the Shuttle's regenerated line 21. Part II is how that discovery was turned
into an engine built on the wrong premise, patched fourteen times against its own instruments in
thirty hours, and stopped by the owner reading raw panels. Same conventions as Part I; hashes
are the rewritten ones (the trailer rewrite of 2026-09-05 20:38 kept every tree and date).
Claude's account first; Codex's follows in its own words; differences at the end.

## What the owner said and what got built

The contract was stated on 2026-09-04, in the chat, in order:

- 07:39 and 07:48: "the raster should always be at the same fucking point … you have not measured
  the number of actual picture lines, where the top line is and where the bottom line is."
- 11:35: "line 21 should end up on top of the real line 21 … and everything else follows from
  there."
- 11:45: "even with no caption data, the first PICTURE line should be in the same place. that is a
  secondary mechanism that can be used for locking."
- 12:10: "I just don't understand why a stable signal source should EVER move its registration
  once its been found … the number of lines in the registration shift should be fixed constant."
- 16:40: "geometry absolutely can be measured … locked by CC, locked by geometry EXCEPT around
  times where we truly lose NTSC signal, or there are program cuts."
- 16:57: "comb checking, but set only once at the beginning of a picture lock … that is golden
  sync."
- 17:03: "hopefully geometry is still calculated every frame … the truly fucked up instances are
  going to be things like u062323 … THAT is the only place you should actually hold."
- 18:33: "Picture. Lock should be kept … invalid geometry that disagrees with the settled lock."

Read together they say: the picture's geometry, measured every unit, is the authority; the
caption, the comb and everything else confirm it where geometry alone cannot decide (the noisy
head-switch bottom, field precedence, boxed pictures); the only holds are a torn raster and a
lost lock. The 11:35 sentence was the one Claude wrote into `docs/registration_v9_plan.md` as
the design: "everything derives from the lock", the caption the primary gauge, geometry the
fallback "when no caption decodes". The 11:45 correction became a footnote. Every round below
patched that inversion instead of reversing it, and the owner's two later rulings (18:33 and the
2026-09-05 morning ruling on damaged rasters) were each implemented as one more layer on top.

## The items, continued

**15. The caption becomes the authority (v9, `e1c91f6`, 2026-09-05 01:00).** Codex's engine
decoded every line of each field as CEA-608 and placed field 1 at `line − 21` whenever exactly
one valid line sat off the insert (`Line21Placement`); geometry placed only otherwise
(`GeometryLockDecides`); field 2 used a frozen "smeared XDS" envelope at line 286. Claude built
the acceptance around the same signal: a whole-tape parity truth set (40,237 field-1 readings)
and `v9_acceptance.py` scoring the engine against it. The engine matched its own gauge 40,237 of
40,237 and the render bounced; the owner's review named six sites and four root causes in an
hour. The instrument could not see the defect because the instrument was the gauge.

**16. The first raw instruments (2026-09-05 04:00–05:00).** Claude's `follow_audit.py` scored
each unit by whether the crop change matched the body's shift since the previous unit, and
`relative_comb_audit.py` measured the static-region comb of the published crops. Both were
built from the same slices the engine was being fixed on. The follow audit was relative and, as
Codex later showed, labelled every late correction as engine motion; rules E and F of round 7
were written on those mislabelled counts and suppressed 2,616 correct caption placements
(`d871f1f` → `67a9752`).

**17. Rounds 4 to 8: the witness stack.** A 1-D body witness (`dc8a459`) that misread one-line
jitter at 37:01 and latched on the last applied crop; a 2-D witness anchored on the previous
measured position (`2efc416`); a reliability margin measured against caption truth (0.8; wrong
in about one unit of five hundred below it, but blind to 15–17% of real moves); a "tied witness
abstains" rule that Claude first turned into a hold and then, on the falsification, back into
"the top decides" (`56edda0`, round 8). Each round moved the comb figure: 3,691 → 1,889 → 1,052
misregistered unit pairs. Each also added a rule that only made sense on top of caption-first.

**18. The field-2 zero and the 41-line walk (rounds 5–6, `a4a1bec` → `72c1260`).** Field 2 has
no parity gauge in the first recording, so Codex calibrated its zero by comb against field 1.
Claude's brief froze `d1 − d2` as the segment constant; Codex refused it with the numbers (field 1
jitters independently) and calibrated the zero instead. At minute 43 the calibration then walked
the zero from 4 to 41 lines: field 1 was geometry-placed one line wrong under a zero corrupted by
the line-22 flicker, field 2 was held out of range so its crop never moved, the comb kept reading
the same disagreement, drift fired every eight units, and each recalibration derived the new zero
from the old one. Round 6 fixed the four faults and added a ±3 bound as a brake. By the evening
the brake was being recited as "a segment constant bounded to three lines".

**19. Round 10, the best whole-tape state (`63b5bf7`, merged `5b6ae68`).** A bounded relative
comb correction closed minute 43: comb misregistered 165 of 86,293 pairs, caption placement
40,208 + 29 evidence-checked vetoes + 0 disagreements. The same evening the v7 and v8 engines
were replayed through the same instruments: v8 combed less (326) than round 8 (1,052) because it
placed both fields from the same kind of gauge and was wrong in both together, and it placed
field 1 where the caption said in 75.6% of readings against round 10's 99.9%. That table is the
one durable result of the day: both instruments are needed, the comb for relative error, the
caption for absolute.

**20. Rounds 11 and 12: the damage ruling implemented as a hold on absent evidence.** The owner's
ruling (save the last good geometry, hold a damaged raster, re-check once when it clears) was
briefed by Claude first as a contradiction-based classifier, which Codex falsified on the torn
units themselves (their inserts decode, tops measure, body MAD 5.7–11.1), then as "hold whenever
no evidence" (`ac36073`). That fired on 23,442 field-1 units in 3,059 runs (22,107 of them "body
witness tied"), one run 8,998 units long, and raised the comb figure from 165 to 620 by freezing
stale positions and the wrong phase of real jitter. The raw panels of the fourteen longest holds
showed one damaged site, one relock snow at a program cut, and twelve holds keeping a crop one or
two lines high with the tape's black line inside the frame. The owner read them and stopped the
work.

**21. Round 14 and the black line 22 (`6d919a2`, 2026-09-05 19:54, unmerged).** In between,
two genuinely new facts: the Shuttle's reference raster, measured on the no-source capture
(padding rows 0–6 and 261–269, blanking on lines 11–19, its timing pattern on line 20, its null
caption insert on line 21, blanking on line 22, pass-through only from line 23 and from line 286
down); and the tape's black line 22 appearing at row 18 + d as a dark row above the picture,
agreeing with the caption 309 of 309 times where both exist and valid only on a source whose line
22 is black. Codex made the engine's comb identical to the audit's (2,677 of 2,677 verdicts) and
gated the gap gauge on caption agreement. Also found the same evening: the row above the caption
at +3 is the tape's line 20, mislabelled for a day as "a duplicated run-in"; and the caption gauge
is structurally blind at +1 (the tape's line 21 lands on the Shuttle's blanked line 22).

## Why it derailed again

The Part I lesson was "concept before code". Part II broke it in a different way: the concept
was stated, then encoded inverted, and the rest was a very disciplined iteration on the wrong
base. Specifically:

- **The instrument became the objective.** The parity truth set was the first thing that gave a
  clean number; the engine was fixed until it matched it, and "0 disagreements" was reported as
  acceptance for a day while the picture bounced.
- **Each falsification was answered with a rule, not a question about the base.** Fourteen
  rounds, each with failing-first goldens cut from the defect, each green, each adding a
  precedence step or a constant. Goldens froze the patches, not the contract.
- **Constants fitted to fixture A were promoted to contract.** The 0.8 margin, three readings,
  25% and 3%, ±3 twice, the near-blank band, "first of three picture rows", the XDS envelope.
  None derives from the raster; several derive from one bug.
- **The relative instrument was trusted for an absolute claim** (rule E), and the absolute
  instruments were trusted where they are blind (the comb cannot see both fields off together;
  the caption cannot see +1).
- **Both agents obeyed briefs that contradicted the owner's own words from hours earlier.**
  Codex pushed back where the data forced it (the `d1 − d2` constant, the damage classifier,
  five "not merge-ready" verdicts) and complied everywhere else; Claude wrote the briefs from
  its own summary of the contract instead of from the transcript.

## Process failures, same period

- Eighteen of Codex's commits since 2026-09-04 22:02 carried the characters `\n` in the message
  instead of line breaks, so their co-author trailers were not trailers. Codex reported it twice
  on 2026-09-05; Claude called it cosmetic and deferred; the owner ordered the rewrite.
- Thirteen working branches cited by hash in the plan were never pushed until the owner asked.
- Claude wrote at least five timestamps from memory, each a few minutes wrong, and corrected each
  after checking the clock, instead of checking first.
- Claude's summary of the round-12 sheets ("mostly harmless") preceded looking at them at full
  scale; the owner looked first.

## What to keep

The reference raster measurement; the tape's line 21 as a parity-decoded absolute gauge and its
blind spots; the tape's black line 22 and line 20 as gauges with their validity conditions; the
canonical static-comb measurement and its exact agreement between engine and audit; the parity
truth set and `v9_acceptance.py`; the whole-tape replay discipline (86,293 units, zero drops,
every gate from the same sidecar); the v7/v8/v9 comparison table; the fact that field 1 jitters
by one line per unit while field 2 holds, so no per-segment `d1 − d2` exists; and the
transcript quotes above, which are the contract. Discard: the precedence stack, every
tape-fitted constant not derivable from the raster, the hold on absent evidence, and the
follow audit as anything but a pointer.

## What happens next

The owner's ruling on 2026-09-05 evening: roles switch. Claude writes the next registration
engine, geometry first, from the reference raster and the contract above; Codex writes the
validation harness; neither reads the other's prior engine or harness work; both guide each
other on concept. All of it on a new branch. The round-14 audits run to completion first so the
merged round-10 main remains a measured fallback.
