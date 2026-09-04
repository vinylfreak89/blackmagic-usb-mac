# Vertical sync mechanics vs. the registration model — research note (2026-09-04)

Purpose: check, before the clean-sheet registration engine is written, whether the agreed model
("the Shuttle's raster is rigid; the deck places each field's picture inside it, and field 1's
picture moves by whole lines; correct by a per-field whole-window shift back to a per-segment
reference") is consistent with how vertical sync, VCR playback and video ADC decoders actually
work. Sources are linked; quotes are short. Nothing here is a measurement of our tape — the
measurements live in `experiments/picture_envelope_census.py` and CLAUDE.md.

## 1. The analog vertical interval and field identity

- NTSC's vertical interval is nine lines: three lines of equalizing pulses, three of serrated
  vertical sync, three more of equalizing pulses. The serrations and equalizing pulses run at
  twice line rate so vertical sync can begin mid-line for one field: "start vertical sync
  half-way through a scanline, which makes the TV draw the next field one half scanline higher"
  ([NESdev NTSC video](https://www.nesdev.org/wiki/NTSC_video)).
- Field identity is carried only by that half-line relationship: "the odd sync switches at a line
  boundary and the even sync switches at a half line boundary"
  ([US patent 5754251](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/5754251)).
  A sync separator recovers V by integrating the serrated pulse train; every classical design has
  a detection window measured in lines, and vertical-sync detection with "a delay of no more than
  half line" is treated as an achievement, not a given
  ([US patent 4641189](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4641189)).
  Implication: a V-sync decision can legitimately land one line early or late for one field
  without anything else in the raster changing.

## 2. Line numbering (525/60) and where the picture should sit

- Field 1 is lines 21–263 (first active line 21), field 2 is 284–525 (283 marks the field
  boundary); 525-line material is F1-dominant with odd spatial parity: "the spatially highest
  line of the frame comes from the temporally first field"
  ([Lurker's Guide, field dominance](https://lurkertech.com/lg/dominance_sgi.html)).
- Our device raster: field 1 is unit lines 0..262, field 2 is 263..524, so standard line 21 is
  index 20 and line 284 is index 283. The census measures the program picture's top at index 20
  (field 1) and 283 (field 2) — exactly the standard first active lines — with heights 237/236.
  The last ~6 lines before the nominal end of active video are near-black on this deck: that is
  the head-switching band (§3), blanked by the deck's TBC, which is why the picture ends at
  index 256/518 and four digitized near-blank lines sit under it before the Shuttle's own
  padding fill. Line 21 (CC) sitting on the first picture row is also why "line-21 content
  bleeding into the picture" is visible on the EP recording.

## 3. VHS playback: two heads, one field each, and the head-switch point

- "the head switching pulse ... has to occur 6.5 horizontal lines or 416 microseconds before the
  corresponding vertical synchronisation pulse", with an alignment tolerance of ±1.5 lines
  ([EP1209675](https://data.epo.org/publication-server/rest/v1.2/publication-dates/20020529/patents/EP1209675NWA1/document.html));
  head-switching noise "occurs prior to the start of vertical sync" and is seen at the bottom of
  the picture ([AV Artifact Atlas](http://www.avartifactatlas.com/artifacts/head_switching_noise.html)).
- Each field is reproduced by a different head. Everything that decides where a field's lines
  begin — the head-switch instant, the tape's reproduced vertical interval, the deck's sync
  separator, and the TBC's field write pointer — is therefore evaluated per field, once per head
  pass. A per-head timing bias or a marginal V detection produces a displacement of ONE field's
  content by whole lines while the other field is untouched. That is the observed signature.
- This is a known capture problem, not peculiar to us: "The affected fields start with one or
  more (max ~5) black lines, whereafter the correct signal picks up again. This causes a
  (vertical) offset for that field ... the vertical offset can be different each time (jittery)
  and can be different for the two fields that make up a frame"; it was visible on a CRT straight
  from the VCR, survived two external TBCs, and was removed by a pass-through DVD recorder whose
  frame synchronizer re-derives vertical timing
  ([VideoHelp thread 394514](https://forum.videohelp.com/threads/394514-How-to-correct-vertical-shifts-in-VHS-capture-(incomplete-field-starts))).
  Our deck's TBC already regenerates a stable OUTPUT raster (the OSD and the Shuttle's VBI/padding
  never move), so the displacement is baked into the field's content at the deck's input side;
  the correction is exactly the per-field line shift the thread's author proposed by hand.
- TBC vs frame sync: "tbc" addresses line timing, "frame sync is mostly about Top edge problems";
  doing the TBC before the frame sync "avoids over and under runs in the frame sync which can
  make problems with the vertical 'jumps'"
  ([John Willis, TBC and frame sync](https://www.johnwillis.com/2021/06/ancient-history-time-base-correction.html)).

## 4. Video ADC decoders (what the Shuttle's front end does with the deck's output)

Representative SD decoder, ADI ADV7180 ([datasheet Rev. I](https://docs.rs-online.com/6d7e/0900766b8131cdef.pdf)):
- Sync extraction "is optimized to support imperfect video sources, such as VCRs with head
  switches": coarse threshold detection, then adaptive interpolation, then a line-length
  measurement/prediction block that drives resampling to 720 active pixels per line.
- A dedicated "VSYNC processor ... provides extra filtering of the detected VSYNCs to improve
  vertical lock"; vertical lock is by counting H syncs per field (lock range 40–70 Hz, lock time
  2 fields); the FIELD output is derived from the odd/even half-line position, and the decoder
  exposes per-field, line-granular controls for where VSYNC/FIELD toggle (NVBEG/NVEND with
  odd/even one-line delays, NFTOG).
- Implication: the decoder defines each field's first line by a line-granular decision made
  once per field from the incoming V timing. With a clean, stable input (the deck's regenerated
  output) it produces a rigid raster — which is what we measure on the Shuttle (padding ruler and
  VBI lines byte-stable across the whole tape). A decoder cannot "see" that the content inside a
  field was written one line off by the deck's TBC; only picture-content measurement can.

## 5. Codec level

Interlaced coding (MPEG-2, H.264 field/MBAFF) and every deinterlacer assume the standard spatial
parity: field 1's lines are the spatially higher lines. A field whose content is displaced by
one line inside its raster violates that assumption — the frame weaves with a one-line error
between the fields, which a motion-adaptive deinterlacer renders as combing wherever the picture
has vertical detail. No codec or deinterlacer corrects it; the correction has to happen on the
480i frame before either, as a per-field whole-line shift (which is what `fp_assemble` does).

## 6. What this says about the model

- Right ballpark: rigid device raster; per-field, whole-line content displacement originating at
  the deck's field write timing (per head, per V detection); correction = per-field whole-window
  shift to a per-segment reference; a frame-synchronizer-style "pick the reference after
  acquisition and keep returning to it" is exactly what the pass-through devices that fix this
  problem do.
- What the model must NOT do: treat a change of picture content (height change, letterbox,
  fade, a new shot with a different envelope) as a raster move; and never hold a fixed crop and
  present it as registration — every unit is measured and corrected, holds are named.
- Position moves to correct vs content changes to preserve: a rigid move of the whole field
  envelope (top and bottom together) is position; a change of the envelope's height, or new
  chroma/luma lines appearing inside a rigid raster, is content and is left alone.
- VBI caveat from the owner: this material has leaky/offset chroma in the vertical interval; a
  line-21-like signature that appears twice, horizontally or chroma-shifted, is suspect (deck
  concealment or a generational copy) and must never be used as raster evidence. The offline
  line-21 landing check must key on the primary signature only.

## Sources

- [NTSC video — NESdev Wiki](https://www.nesdev.org/wiki/NTSC_video)
- [Analog/NTSC Video Vertical Sync (Philips PM5418 notes)](https://deramp.com/downloads/mfe_archive/200-Test%20Equipment/Philips:Fluke/Philips%20PM5418%20TV%20Pattern%20Generator/NTSCVSync.pdf)
- [US 5754251, digital video vertical synchronization pulse detector](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/5754251)
- [US 4641189, digital vertical sync filter](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4641189)
- [Lurker's Guide: Fields, F1/F2, Interleave, Field Dominance](https://lurkertech.com/lg/dominance_sgi.html)
- [EP1209675, VHS head switching timing](https://data.epo.org/publication-server/rest/v1.2/publication-dates/20020529/patents/EP1209675NWA1/document.html)
- [AV Artifact Atlas: Head Switching Noise](http://www.avartifactatlas.com/artifacts/head_switching_noise.html)
- [VideoHelp 394514: vertical shifts in VHS capture (incomplete field starts)](https://forum.videohelp.com/threads/394514-How-to-correct-vertical-shifts-in-VHS-capture-(incomplete-field-starts))
- [John Willis: time base correction and frame sync](https://www.johnwillis.com/2021/06/ancient-history-time-base-correction.html)
- [ADV7180 datasheet Rev. I](https://docs.rs-online.com/6d7e/0900766b8131cdef.pdf)
