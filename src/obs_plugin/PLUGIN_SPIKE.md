# P4a spike — native OBS Studio source plugin on macOS 26 / Apple Silicon

Read-only research, 2026-09-03 (JST). Context: CLAUDE.md §10 (delivery) and §11 P4. Note: CLAUDE.md
§11 has no item literally named "P4a" — its P4 is the CMIO extension; this spike is the *OBS source
plugin* branch that §10 names as the pragmatic V+A path and that `src/cmio/PACKAGING_SPIKE.md` line 74
already recommends. No installs, no repo changes; every web source was treated as data. Upstream
sources were downloaded verbatim into the scratchpad (`scratchpad/obs-src/`) and grepped; line numbers
below refer to those `master` copies (OBS master is 32.2.x, matching the installed app).

Tags: [doc] official documentation · [src] upstream source · [forum] forum/issue · [3p] third-party
write-up · [local] measured on this Mac · [inferred] my reasoning from the cited facts.

## 0. Local baseline [local]

| Item | Value |
|---|---|
| OBS | `/Applications/OBS.app` **32.2.2** (CFBundleVersion 31845296735), `LSMinimumSystemVersion 13.0`, arm64 thin — `plutil -p Info.plist` |
| OBS signature | Developer ID "Wizards of OBS LLC (2MMRE5MTB8)", **hardened runtime** (`flags=0x10000(runtime)`), entitlements include **`com.apple.security.cs.disable-library-validation = true`**, `allow-unsigned-executable-memory`, `system-extension.install`, app group; **no `com.apple.security.app-sandbox` key** (grep count 0) — `codesign -d --entitlements -` |
| Renderer in last log | "OpenGL loaded successfully, version 4.1 Metal - 90.5" on Apple M3; default video settings `fps 60/1`, `format NV12` — `~/Library/Application Support/obs-studio/logs/2026-09-02 17-11-12.txt` |
| Bundled plugins | 23 `.plugin` bundles in `Contents/PlugIns`, incl. plain-C ones (`image-source`, `text-freetype2`, `obs-filters`, `obs-outputs`) |
| libobs | `Contents/Frameworks/libobs.framework` — **no Headers/ directory**; install name `@rpath/libobs.framework/Versions/A/libobs`; exports `_obs_source_output_video`, `_obs_source_output_audio`, `_obs_register_source_s`, `_obs_source_set_async_unbuffered`, `_obs_source_set_deinterlace_mode` (`nm -gU`); embedded version string `32.2.2` |
| How bundled plugins link | `otool -L image-source` → `@rpath/libobs.framework/Versions/A/libobs`; `LC_RPATH = @executable_path/../Frameworks`; Info.plist `CFBundlePackageType = BNDL`, `CFBundleExecutable = image-source` |
| User plugin dir | Main binary contains the format string **`obs-studio/plugins/%module%.plugin`** (plus `/Contents/MacOS`, `/Contents/Resources`); `~/Library/Application Support/obs-studio/plugins/` **does not exist yet** on this Mac; `plugin_manager/modules.json` = `[]` |
| Encoders present | `mac-videotoolbox` strings: `VTProResEncHW`/`VTProResEncSW`, `ProRes422 / 422HQ / 422LT / 422Proxy / 4444 / 4444XQ`; bundled `libavcodec.dylib` has `prores`, `prores_aw`, `prores_ks`, `prores_videotoolbox`, `ffv1`, `utvideo`, `v210`, `rawvideo` |
| Output allowlists | `obs-outputs.plugin` strings: `h264;hevc;prores` (mov) and `h264;hevc;av1` (mp4); locale `Basic.Settings.Output.Format.hMOV="Hybrid MOV (.mov)"` |
| Toolchain | Xcode **26.6 (17F113)**, Apple clang 21.0.0; **`cmake` is NOT installed** (`command not found`); Homebrew `libusb 1.0.30` with both `libusb-1.0.a` and `libusb-1.0.0.dylib` (dylib is **ad-hoc signed**, TeamIdentifier not set); `pkg-config --static --libs libusb-1.0` = `-lusb-1.0 -lobjc -framework IOKit -framework CoreFoundation -framework Security` |
| Security posture | SIP enabled (`csrutil status`); Gatekeeper on (from PACKAGING_SPIKE baseline) |
| Frameserver API | `src/frameserver/frame_publisher.h`: `fp_frame{IOSurfaceRef surface ('2vuy' 720×480, TFF, rows interleaved), pts_num/pts_den, counter_ext, d1, d2, transport}`; `fp_sink.on_frame` is **synchronous on the frameserver worker thread**; `fs_config{cc_config capture (replay_path, replay_pace_us), pool_units, surface_pool, decision_log, fp_sink sink, on_end}`. **Audio: `frameserver.c:69-72` only counts `unit_audio_observation`s — there is no audio sink/publisher yet.** `unit_parser.h`: `unit_audio_observation{kind PCM/RESYNC/UNFRAMED/HOLE, sample_ordinal, active_s24le[6] (two S24LE channels), counter16/counter_extended on RESYNC}` |

## 1. Plugin mechanics (async video + audio source)

**Registration.** `obs_source_info` for this source: `id`, `type = OBS_SOURCE_TYPE_INPUT`,
`output_flags = OBS_SOURCE_ASYNC_VIDEO | OBS_SOURCE_AUDIO`, `get_name`, `create`, `destroy`,
`activate/deactivate`, `get_properties`, `update`, optional `video_tick`, `icon_type` [src]
https://raw.githubusercontent.com/obsproject/obs-studio/master/libobs/obs-source.h .
`OBS_SOURCE_ASYNC_VIDEO = (OBS_SOURCE_ASYNC | OBS_SOURCE_VIDEO)`, `OBS_SOURCE_AUDIO = (1<<1)`
[src] same file. Docs: "OBS_SOURCE_ASYNC_VIDEO — Source passes raw video data via RAM. Use
obs_source_output_video() … which will be automatically drawn at a timing relative to the provided
timestamp"; "OBS_SOURCE_AUDIO — Use obs_source_output_audio() … automatically converted and
uploaded" [doc] https://docs.obsproject.com/reference-sources (rst source:
https://raw.githubusercontent.com/obsproject/obs-studio/master/docs/sphinx/reference-sources.rst ).
An async source needs no `get_width/get_height`: libobs reports the async frame size itself
(`get_async_width()` at `obs-source.c:2718-2743`) [src]. Module boilerplate: `OBS_DECLARE_MODULE()`
expands to `obs_module_set_pointer`, `obs_current_module`, `obs_module_ver` returning
`LIBOBS_API_VER` (`obs-module.h:76-90`); `obs_module_load` must return true; `obs_module_unload`
optional [src] https://raw.githubusercontent.com/obsproject/obs-studio/master/libobs/obs-module.h .

**Frame struct** (`obs.h:283-303`) [src]
https://raw.githubusercontent.com/obsproject/obs-studio/master/libobs/obs.h :
```c
struct obs_source_frame {
	uint8_t *data[MAX_AV_PLANES]; uint32_t linesize[MAX_AV_PLANES];
	uint32_t width, height; uint64_t timestamp;          /* ns */
	enum video_format format; float color_matrix[16]; bool full_range;
	uint16_t max_luminance; float color_range_min[3], color_range_max[3];
	bool flip; uint8_t flags; uint8_t trc;               /* + libobs-internal refs, prev_frame */
};
```
No field-order, interlace, or pixel-aspect member exists — there is nothing to declare interlace on a
frame [src]. `color_matrix/range` come from
`video_format_get_parameters_for_format(VIDEO_CS_601, VIDEO_RANGE_PARTIAL, VIDEO_FORMAT_UYVY, …)`
(`media-io/video-io.h:288-292`) [src]
https://raw.githubusercontent.com/obsproject/obs-studio/master/libobs/media-io/video-io.h .

**UYVY on macOS: yes.** `enum video_format` contains `VIDEO_FORMAT_UYVY` (also `I422`, `I210`,
`V210`, `P216`, `P416`; **no `P210`**) [src] video-io.h. Async input conversion is a GPU shader:
`get_convert_type` → `CONVERT_422_PACK` for UYVY (`obs-source.c:1741`) and technique
`"UYVY_Reverse"` (`obs-source.c:2232`) [src]
https://raw.githubusercontent.com/obsproject/obs-studio/master/libobs/obs-source.c ; the shader
exists in `format_conversion.effect` (`UYVY_Reverse`, `I422_Reverse`, `V210_*_Reverse`) [src]
https://raw.githubusercontent.com/obsproject/obs-studio/master/libobs/data/format_conversion.effect .
This is renderer-neutral (OpenGL today, experimental Metal in 32.0 [doc]
https://obsproject.com/blog/obs-studio-32-0-release-notes ). Precedent on this OS: `mac-avcapture` maps
`kCVPixelFormatType_422YpCbCr8` → `VIDEO_FORMAT_UYVY` (verified in `src/cmio/PACKAGING_SPIKE.md`
line 80 [src]). **P216/P416 are NOT accepted as async *input*** (`/* Unimplemented */`,
`obs-source.c:1783-1786`, `2369-2372`) — they are output-side formats only [src].

**What `obs_source_output_video` does** (`obs-source.c:3540-3644`) [src]:
- `cache_video()` takes `async_mutex`, picks/creates a cached frame and **`copy_frame_data()` memcpy's
  the caller's planes** → the caller's buffer (our IOSurface) is free the moment the call returns; the
  call is safe from any thread (mutex-protected). Cost: 720×480×2 = 691,200 B memcpy per frame.
- **Silent overflow:** if `async_frames.num >= MAX_ASYNC_FRAMES (30)` the *entire* cache is freed
  and `last_frame_ts` reset — no log line at that site (`3548-3552`). Our plugin must keep its own
  submitted/consumed counters (§6) because libobs will not confess this drop.
- Timestamps need only be **self-consistent, not OS-clock**: on the first rendered frame libobs sets
  `timing_adjust = obs->video.video_time - frame->timestamp; timing_set = true` (`2560-2562`), and
  audio timestamps get the same `timing_adjust` added (`1650`).
- Buffered mode (default): `ready_async_frame()` (`4124-4209`) paces frames against system time using
  the inter-frame timestamp deltas; a jump `> MAX_TS_VAR` (**2 s**, `obs-internal.h:1064`) re-bases.
  `obs_source_set_async_unbuffered(true)` makes it **discard everything but the newest frame every
  tick** (`4132-4140`) — lowest latency, but any burst > 1 frame per canvas tick is dropped; for a
  recording path keep buffered mode [src+inferred].
- `obs_source_output_video(source, NULL)` deactivates video (`3605-3612`).

**Audio** (`obs.h:251-260`, `audio-io.h:43-55,69`) [src]:
```c
struct obs_source_audio { const uint8_t *data[MAX_AV_PLANES]; uint32_t frames;
	enum speaker_layout speakers; enum audio_format format; uint32_t samples_per_sec; uint64_t timestamp; };
```
`AUDIO_FORMAT_16BIT/32BIT/FLOAT` (+ planar variants) — **no 24-bit format**; the Shuttle's S24LE pairs
must be widened to `32BIT` (`<<8`) or `FLOAT`; `SPEAKERS_STEREO`, `samples_per_sec = 48000` [src].
Timing (`obs-source.c:1627-1650`): first packet sets timing if video hasn't; then
`diff = |next_audio_ts_min − in.timestamp|`: `> MAX_TS_VAR (2 s)` → `handle_ts_jump()` resets audio
timing and flushes buffered audio (logged at LOG_DEBUG: "Timestamp for source '%s' jumped by …");
`< TS_SMOOTHING_THRESHOLD (70 ms)` → **the input timestamp is overwritten with the sample-count
continuation** (`in.timestamp = next_audio_ts_min`); between 70 ms and 2 s → the timestamp is
**accepted as-is**, i.e. a real gap/overlap in the mix (logged "exceeded TS_SMOOTHING_THRESHOLD")
[src]. `obs_source_set_async_decoupled` "Only works when in unbuffered mode" (`obs.h:1552-1555`) [src].

**A/V sync consequence for this device [inferred from the above + CLAUDE.md §6 numbers].** The
Shuttle's audio sample clock ran 5,226 samples short over 48 min (≈36 ppm) relative to the video
counter clock. Two honest timestamping policies exist and the owner must pick one:
1. *Sample-count audio timestamps* (`ts = sample_ordinal/48000`), video PTS from the counter
   (`counter × 1001/30000`): OBS sees perfectly contiguous audio and never smooths; A/V drift
   accumulates ≈109 ms by minute 48 (the same figure the review MP4 corrected with `atempo`).
2. *Counter-anchored audio timestamps* (each resync record stamps its block at frame time): the
   70 ms smoothing band absorbs the mismatch until ≈70 ms/36 ppm ≈ **32 min**, then OBS accepts one
   ~70 ms audio discontinuity — an audible hiccup, not a drift.
3. *Audio as continuity master (recommended, matches §9 "valid audio as continuity master")*: derive
   the **video** PTS from the resync record's `sample_ordinal/48000`; audio stays sample-contiguous;
   video runs 36 ppm slow against the canvas clock and OBS repeats one frame every ≈1/36e-6 frames
   ≈ 27.8 k frames ≈ **15 min**. This puts the correction on the disposable video derivative (a
   repeat), never on audio samples, and never in the archive.
None of this touches the tagged capture; it only decides what the OBS derivative looks like.

**Interlace / deinterlacing.** There is no per-frame field flag; interlace is a **per-source
property** the user (or the plugin, once at `create`) sets: `obs_source_set_deinterlace_mode()` with
`OBS_DEINTERLACE_MODE_{DISABLE, DISCARD, RETRO, BLEND, BLEND_2X, LINEAR, LINEAR_2X, YADIF, YADIF_2X}`
and `obs_source_set_deinterlace_field_order(OBS_DEINTERLACE_FIELD_ORDER_TOP|BOTTOM)` [src] obs.h; the
UI is right-click source → *Deinterlacing* → mode + "Top Field First"/"Bottom Field First"
(locale keys `Deinterlacing.Yadif2x`, `Deinterlacing.TopFieldFirst` [local]; usage [forum]
https://forum.videohelp.com/threads/414981-Capturing-VHS-with-OBS-and-deinterlacing-with-Yadif-2x ).
Implementation (`obs-source-deinterlace.c`) [src]
https://raw.githubusercontent.com/obsproject/obs-studio/master/libobs/obs-source-deinterlace.c :
field order is a shader int (`gs_effect_set_int(field, s->deinterlace_top_first)`, line 393; set at
471); `_2X` modes derive `deinterlace_half_duration = (cur.ts − prev.ts)/2` from **consecutive frame
timestamps** (176-179) and pick field 2 when `video_time >= frame_ts + offset + half_duration`
(396-398) — so a constant 1001/30000 s PTS cadence is exactly what it wants, and the 2× output only
materialises if the canvas runs at 60000/1001 [src+inferred]. The deinterlacer operates on the
**already-converted RGB textures** (`cur_tex`/`prev_tex`), after `UYVY_Reverse` [src]. This satisfies
the project rule: the plugin ships the woven 480i frame + TFF hint; OBS owns deinterlacing.
Recommended default from the plugin: `YADIF_2X`, `TOP` (TFF is the measured order, CLAUDE.md §6), and
leave it user-changeable.

## 2. Build system

**Template** [src] https://github.com/obsproject/obs-plugintemplate :
- `CMakeLists.txt`: `cmake_minimum_required(VERSION 3.28...3.30)`, `add_library(${NAME} MODULE)`,
  `find_package(libobs REQUIRED)`, `target_sources(… src/plugin-main.c)` — **plain C by default**
  (`plugin-main.c` with `OBS_DECLARE_MODULE()` / `OBS_MODULE_USE_DEFAULT_LOCALE`) [src]
  https://raw.githubusercontent.com/obsproject/obs-plugintemplate/master/CMakeLists.txt ,
  https://raw.githubusercontent.com/obsproject/obs-plugintemplate/master/src/plugin-main.c .
- `cmake/macos/helpers.cmake`: `BUNDLE TRUE`, `BUNDLE_EXTENSION plugin`, generated Info.plist,
  `XCODE_ATTRIBUTE_INSTALL_PATH "$(USER_LIBRARY_DIR)/Application Support/obs-studio/plugins"`,
  optional `cmake/macos/entitlements.plist`, post-build copy to `build/rundir/<CONFIG>/` [src]
  https://raw.githubusercontent.com/obsproject/obs-plugintemplate/master/cmake/macos/helpers.cmake .
- `cmake/macos/defaults.cmake`: **`CODESIGN_IDENTITY` defaults to `"-"` (ad-hoc)** when no team is
  given; `CMAKE_INSTALL_PREFIX` defaults to `$ENV{HOME}/Library/Application Support/obs-studio/plugins`;
  `CMAKE_INSTALL_RPATH "@executable_path/../Frameworks"` [src]
  https://raw.githubusercontent.com/obsproject/obs-plugintemplate/master/cmake/macos/defaults.cmake .
- `cmake/macos/xcode.cmake`: manual signing with `CODESIGN_IDENTITY`; for non-Debug configs
  `ENABLE_HARDENED_RUNTIME YES` and `--timestamp` (both "required for Notarization") — harmless with an
  ad-hoc identity but the `--timestamp` flag needs network access to Apple's TSA at sign time; use the
  **Debug** config for the local loop [src+inferred]
  https://raw.githubusercontent.com/obsproject/obs-plugintemplate/master/cmake/macos/xcode.cmake .
- `CMakePresets.json` `macos`: generator **Xcode**, `CMAKE_OSX_ARCHITECTURES "arm64;x86_64"`,
  deployment target **12.0**, `CODESIGN_IDENTITY $penv{CODESIGN_IDENT}` [src]
  https://raw.githubusercontent.com/obsproject/obs-plugintemplate/master/CMakePresets.json . A
  `CMakeUserPresets.json` override is the documented way to set arm64-only and a newer target [doc]
  wiki Getting-Started.
- Dependencies (`buildspec.json`): **obs-studio 31.1.1 source tarball** (from
  `github.com/obsproject/obs-studio/archive/refs/tags`), **obs-deps prebuilt 2025-07-11**, qt6 —
  SHA-256 pinned [src]
  https://raw.githubusercontent.com/obsproject/obs-plugintemplate/master/buildspec.json .
  `cmake/common/buildspec_common.cmake` downloads at configure time into `.deps/`, then
  `_setup_obs_studio()` **configures the whole obs-studio source with Xcode
  (`-DENABLE_PLUGINS=OFF -DENABLE_FRONTEND=OFF`, universal) and builds the `obs-frontend-api` target
  (which builds libobs) for Debug *and* Release**, installing the Development component so that
  `find_package(libobs)` resolves [src]
  https://raw.githubusercontent.com/obsproject/obs-plugintemplate/master/cmake/common/buildspec_common.cmake .
  So libobs headers come from a source build, not from OBS.app. **Pin `obs-studio` to `32.2.2`** in
  `buildspec.json` before use (the module version gate below ignores patch and rejects only *newer*
  majors/minors, so 31.1 headers would load into 32.2, but new-API symbols would be invisible).
- Requirements [doc] wiki Build-System-Requirements: "macOS | XCode 16.0", "Windows, macOS | CMake
  3.30.5", and "install CMake via `brew install cmake`" — **this Mac has Xcode 26.6 but no cmake**
  (blocker/decision, §7).

**Where OBS loads user plugins.** libobs itself only registers the app bundle's
`PlugIns/%module%.plugin/Contents/MacOS/` (`obs-cocoa.m add_default_module_paths`) [src]
https://raw.githubusercontent.com/obsproject/obs-studio/master/libobs/obs-cocoa.m ; the frontend adds
the user path — the installed binary carries `obs-studio/plugins/%module%.plugin` [local], the KB says
"~/Library/Application Support/obs-studio/plugins … separate bundles for each plugin ending with
.plugin" [doc] https://obsproject.com/kb/plugins-guide , and the template installs exactly there
[src]. Bundle rule: "The name of the plugin bundle needs to match the name of the binary" [doc]
https://github.com/obsproject/obs-plugintemplate/wiki/How-Plugins-Interact-With-OBS-Studio .
Loader (`obs-module.c`) [src]
https://raw.githubusercontent.com/obsproject/obs-studio/master/libobs/obs-module.c : `os_dlopen`,
requires `obs_module_load`, `obs_module_set_pointer`, `obs_module_ver`; **"Reject plugins compiled
with a newer libobs. Patch version (lower 16-bit) is ignored"** (`ver & 0xFFFF0000 > LIBOBS_API_VER`,
lines 171-177); Safe Mode / disabled-module list (Plugin Manager, 32.0 [doc] release notes) filter
before load; failures are logged only at **LOG_DEBUG** ("Failed to load module file '%s', not an OBS
plugin / incompatible version", 524-535) — run OBS with verbose logging when a plugin silently
doesn't appear (launch parameter `--verbose`, see https://obsproject.com/kb/launch-parameters
[doc, not re-fetched this session]).

**Signing / Gatekeeper.**
- Apple Silicon requires all native code to carry at least an ad-hoc signature; ld64 (Xcode ≥ 12)
  and lld ad-hoc sign arm64 dylibs/bundles **automatically at link time** [3p]
  https://reviews.llvm.org/D97994 , https://eclecticlight.co/2020/08/22/apple-silicon-macs-will-require-signed-code/ .
- OBS is hardened but ships **`com.apple.security.cs.disable-library-validation`** [local]; Apple:
  library validation "prevents a program from loading frameworks, plug-ins, or libraries unless they're
  either signed by Apple or signed with the same Team ID as the main executable … Use the Disable
  Library Validation Entitlement if your program loads plug-ins that are signed by other third-party
  developers" [doc]
  https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.cs.disable-library-validation .
  Template wiki: OBS's exception "allows OBS Studio to load plugins signed by different developers.
  This will *not* allow OBS Studio to load unsigned plugins on Apple Silicon-based Macs. Users thus
  need to be instructed to apply an ad-hoc signature themselves"; ad-hoc: `codesign --sign - --force
  <bundle>`; "Each ad-hoc signature is only valid for the machine on which it was applied" [doc]
  https://github.com/obsproject/obs-plugintemplate/wiki/Codesigning-On-macOS .
- **OBS itself performs no signature check** — `obs-module.c` only dlopens and checks exports/version
  [src]. Gatekeeper matters only for *quarantined* files (downloaded); a locally built bundle carries
  no `com.apple.quarantine` attribute, so no "developer cannot be verified" dialog [inferred; the
  failure mode for downloaded plugins is documented in
  https://github.com/ratwithacompiler/OBS-captions-plugin/issues/42 [forum]].
- **Therefore: no Apple Developer account, no notarization, no boot-security change is needed for a
  locally built, ad-hoc-signed plugin loaded by the signed OBS 32.2.2** [src+doc+local]. Notarization
  is a *distribution* concern ("only binaries signed with a valid Apple Developer ID can be notarized")
  [doc] same wiki.

**Plain-C macOS examples.** The template default is C. In-tree C plugins shipped as `.plugin` on this
Mac: `image-source` (`plugins/image-source/image-source.c` [src]
https://raw.githubusercontent.com/obsproject/obs-studio/master/plugins/image-source/image-source.c ),
`text-freetype2`, `obs-filters`, `obs-outputs` [local listing]. Async-video precedents: `mac-avcapture`
(Objective-C, UYVY) and `decklink` (C++, UYVY + audio) — protocol-wise the C API is identical.

## 3. Linking the capture library into the plugin process

- **OBS is not sandboxed** (no `app-sandbox` entitlement [local]); `com.apple.security.device.usb` is a
  *sandbox* entitlement and therefore irrelevant here; libusb opens the vendor-class device with no
  driver bound exactly as the CLI tools already do (CLAUDE.md §3) [local+inferred].
- **Homebrew libusb dylib**: already ad-hoc signed [local]; OBS's disabled library validation would
  load it from `/opt/homebrew/opt/libusb/lib` if the plugin's install name pointed there. Two clean
  options: (a) **static link `libusb-1.0.a`** (present) with `-lobjc -framework IOKit -framework
  CoreFoundation -framework Security` [local pkg-config] — one Mach-O, one ad-hoc signature, no
  bundle fix-ups (**recommended**); (b) copy the dylib into `<plugin>.plugin/Contents/Frameworks/`,
  `install_name_tool -change … @loader_path/../Frameworks/libusb-1.0.0.dylib`, sign inside-out ("First
  all binaries inside the bundle need to be signed before the outer bundle" [doc] codesigning wiki).
  Static linking keeps libusb's GPL/LGPL question unchanged (libusb is LGPL-2.1; our code is GPLv2+).
- **Threading model.** OBS's graphics thread calls `video_tick`/render; it never runs our code
  except `video_tick` if we implement it — leave it empty. Our stack already keeps the USB event
  thread pristine (capture_core delivery thread → frameserver worker); the plugin's `fp_sink.on_frame`
  runs on the frameserver worker and calls `obs_source_output_video` (memcpy under `async_mutex`,
  bounded) and `obs_source_output_audio`. `create()` must not block on device init longer than the UI
  tolerates — start `fs_open/fs_start` on a control thread and publish `DeviceLost`/`Fault` via
  `obs_source_output_video(NULL)` + a property-page status string. `destroy()` calls `fs_stop` (which
  cancels transfers, drains and joins) before returning [src frameserver.h + §8 rules].
- One `libusb_context` per process rule (§8): the plugin owns exactly one `cc_session`; a second OBS
  source instance must be refused or share the session (design decision, §7).

## 4. ProRes end to end

**Encoders.** OBS's `mac-videotoolbox` registers ProRes 422 / 422 HQ / 422 LT / 422 Proxy / 4444 /
4444 XQ; hardware vs software lists are enumerated at runtime and shown as **"Apple VT ProRes Hardware
Encoder"** / **"Apple VT ProRes Software Encoder"** with a "ProRes Codec" dropdown [src]
https://raw.githubusercontent.com/obsproject/obs-studio/master/plugins/mac-videotoolbox/encoder.c
(lines 35-40, 85-95, 440-460, 1196-1199, 1307-1341) [local strings agree]. Base M3 has no ProRes
engine (CLAUDE.md §9) so expect only the software entry; SD ProRes is trivial for the CPU. Shipped in
OBS 29 (PR #7010) [src] https://github.com/obsproject/obs-studio/pull/7010 . The bundled FFmpeg also
has `prores_ks`/`prores_aw`/`prores_videotoolbox` for the *Custom Output (FFmpeg)* path [local].

**Containers.** Hybrid MOV (`mov_output`, obs-outputs) allows `encoded_video_codecs =
"h264;hevc;prores"`, `encoded_audio_codecs = "aac;alac"`; Hybrid MP4 excludes ProRes [src]
https://raw.githubusercontent.com/obsproject/obs-studio/master/plugins/obs-outputs/mp4-output.c
(609-627). Legacy `ffmpeg_muxer` (plain "MOV") has no codec restriction [src]
https://raw.githubusercontent.com/obsproject/obs-studio/master/plugins/obs-ffmpeg/obs-ffmpeg-mux.c .
32.0 made Hybrid MOV "ProRes support on macOS" the headline and Hybrid MP4/MOV the default [doc]
https://obsproject.com/blog/obs-studio-32-0-release-notes . ProRes in MP4 fails ("Invalid argument")
[forum] PR #7010 discussion.

**4:2:2 — what actually happens in the pipeline.**
1. Our UYVY frame → `UYVY_Reverse` shader → an **RGB canvas texture**. Canvas precision is
   `GS_BGRA` (8-bit) **unless the output Color Format is I010/P010/I210/I412/YA2L/P216/P416, in which
   case `GS_RGBA16F`** (`obs.c:357-372`) [src]
   https://raw.githubusercontent.com/obsproject/obs-studio/master/libobs/obs.c .
2. Canvas → output format on the GPU (`conversion_techs`), download via stage surfaces; implemented
   output formats: **I420, NV12, I444, I010, P010, P216, P416** (+ BGRA copy); `I422/UYVY/V210` are
   `/* unimplemented */` as outputs (`obs-video.c:659-757`) [src]
   https://raw.githubusercontent.com/obsproject/obs-studio/master/libobs/obs-video.c . The Settings
   › Advanced list is exactly `NV12, I420, I444, P010, I010, P216, P416, RGB` [src]
   https://raw.githubusercontent.com/obsproject/obs-studio/master/frontend/settings/OBSBasicSettings.cpp ;
   locale: `P216 (16-bit, 4:2:2, 2 planes)` [local].
3. The P216 chroma shader averages **left+right only** (`rgb = (rgb_left + rgb_right) * 0.5`) — no
   vertical filtering [src] format_conversion.effect.
4. VideoToolbox accepts `P216 → kCVPixelFormatType_422YpCbCr16BiPlanarVideoRange` (limited range
   only; full range → `kResultFullRangeUnsupported`), `P416 → 444…16BiPlanar`, `NV12/I420` → 4:2:0
   [src] encoder.c format switch. With NV12 the encoder is fed 4:2:0 and ProRes 422 merely upsamples
   it — the 4:2:2 chroma of the tape would be lost before encoding [inferred from the mapping].
   **So the faithful setting is Color Format = P216, Color Space = Rec. 601, Range = Limited.**
5. Custom Output (FFmpeg): `video_encoder` chosen by name (`prores_ks`), pixel format via
   `avcodec_find_best_pix_fmt_of_list` with swscale fallback (`obs-ffmpeg-output.c:154-211`);
   `obs_to_ffmpeg_video_format` maps `I444→YUV444P`, `I422→YUV422P` (I422 isn't offered by the UI)
   [src] https://raw.githubusercontent.com/obsproject/obs-studio/master/plugins/obs-ffmpeg/obs-ffmpeg-formats.h ;
   the P216 mapping was not verified in this pass. VT ProRes via Hybrid MOV is the simpler, better-
   tested path; keep `prores_ks` as the fallback if VT refuses P216 for some reason.

**Faithfulness limits — say them plainly.**
- The YCbCr → RGB → YCbCr round trip is **not lossless** even at 16-bit float: `UYVY_Reverse` applies
  the 601 matrix and range expansion; values outside the RGB cube (the **sub-black Y=1–2 mute frames
  and sub-black excursions measured in fixture A**, CLAUDE.md §6) are at best negative floats, at
  worst clamped; with any 8-bit output format they are certainly clamped [inferred from obs.c/shader
  structure — **needs the §6 synthetic test: feed a Y=1 / Y=250 frame through replay and read the
  recorded ProRes Y back**]. The OBS ProRes is therefore a *presentation copy*; the tagged capture
  remains the archive, exactly as §8 already states.
- **Interlaced recording: OBS cannot record fields.** `obs_video_info` has fps/size/format only [src]
  obs.h:191-219; the output stage has no field concept [src] obs-video.c; VT ProRes gets no field
  flags [src] encoder.c. The only "interlace-preserving" record is a **woven frame passed through
  untouched**: base = output = 720×480, canvas FPS 30000/1001, deinterlace **Disabled**, no
  scaling/filters/transform, Color Format **P216** (4:2:2 has no vertical chroma subsampling, so field
  lines stay separate; NV12/I420 would mix chroma across fields), ProRes 422 (HQ). The file is flagged
  progressive; field order must be recorded out-of-band (sidecar/filename) and verified with
  `ffmpeg -vf idet` on a motion passage [inferred; test required].
- **Deinterlaced record** (the normal OBS use): canvas 60000/1001, source Deinterlacing = Yadif 2x /
  Top Field First, P216 + ProRes 422 HQ → 59.94p 4:2:2 10-bit.

## 5. What OBS discards

- **Field metadata**: none carried (§4); TFF is a per-source *hint* the plugin sets at create, and the
  decision log keeps the truth.
- **Non-square pixels**: OBS "only creates video with square pixels" [forum]
  https://obsproject.com/forum/threads/how-can-i-change-the-pixel-aspect-ratio-of-my-recording.171682/ ;
  no SAR field in `obs_source_frame` or `obs_video_info` [src]. Options: (a) record native 720×480
  and set the display aspect in post — for ProRes/MOV a `pasp` atom via `ffmpeg -c copy -aspect 4:3`
  is metadata-only [inferred; verify the remux is bit-identical]; (b) let OBS rescale to 640×480 or
  720×540 (Settings › Video output resolution, or Edit Transform) — a resample, so **never for the
  faithful record** [forum] same thread + https://github.com/obsproject/obs-studio/wiki/understanding-aspect-ratio .
- **10-bit later**: `VIDEO_FORMAT_V210` is a supported async *input* (`CONVERT_V210`, technique
  `V210_SRGB_Reverse` etc.) [src] obs-source.c 1777/2337 + effect list; with P216 output and ProRes
  422 HQ the 10-bit path exists end to end. `I210` (planar 10-bit 4:2:2) is also accepted as input if
  we ever unpack v210 ourselves [src].
- **Audio**: 24-bit must be widened (no `AUDIO_FORMAT_24BIT`); OBS mixes in float internally; Hybrid
  MOV audio is AAC or **ALAC** (lossless) [src] mp4-output.c; legacy MOV/ffmpeg_muxer additionally
  exposes the PCM encoders present in the frontend (`pcm_s16le/s24le/f32le` strings [local]).
- **Sub-black / super-white**: see §4 — presentation clamp risk.
- **Provenance**: transport holes, short units, registration decisions, `Unknown` states — all of §8's
  multidimensional validity — do not exist in OBS; the plugin must keep the decision log/sidecar
  (already produced by the frameserver) and optionally overlay nothing (honesty rule: no
  concealment in the archive; concealment only in this disposable live derivative).

## 6. Minimal dev loop for this project

**Constraints honoured:** no boot-security change (none needed), no Apple Developer account (ad-hoc
signing suffices, §2), no install in this spike (but see the cmake decision).

**Layout** (`src/obs_plugin/`, mirroring the repo's Makefile style):
```
src/obs_plugin/
  Makefile                      # clang -bundle, links repo objects + libusb static + libobs.framework
  shuttle_source.c              # obs_source_info: create→fs_open/fs_start, destroy→fs_stop/fs_close
  shuttle_sink.c                # fp_sink.on_frame → obs_source_frame(UYVY); audio batcher → obs_source_output_audio
  obsconfig.h                   # stub for the source-tree headers (see below)
  bundle/Info.plist             # CFBundlePackageType BNDL, CFBundleExecutable shuttle-obs, CFBundleIdentifier …
  data/locale/en-US.ini
  tests/replay_plugin_test.c    # optional: link against a libobs stub? (no — test the sink logic only)
```
Two build routes:
- **Route A (no cmake, matches the repo today):** headers from the obs-studio **32.2.2** source
  tarball (`libobs/`, `libobs/media-io/`, `libobs/util/`, `libobs/graphics/`) in a scratch/dep dir;
  `obs-config.h` `#include "obsconfig.h"` needs a stub with `OBS_RELEASE_CANDIDATE 0`/`OBS_BETA 0`
  (template `obsconfig.h.in` [src] https://raw.githubusercontent.com/obsproject/obs-studio/master/libobs/obsconfig.h.in );
  link with `-bundle -F /Applications/OBS.app/Contents/Frameworks -framework libobs
  -Wl,-rpath,@executable_path/../Frameworks` — identical to how the bundled plugins resolve libobs
  [local otool]; then `codesign --sign - --force shuttle-obs.plugin` and `ditto` into
  `~/Library/Application Support/obs-studio/plugins/shuttle-obs.plugin`. Linking against the
  installed framework guarantees ABI parity with the running OBS [inferred]. Caveat: a private-header
  drift between the tarball and the shipped binary is possible in principle; the version gate accepts
  it (same major.minor) [src].
- **Route B (template, publishable):** `brew install cmake` (owner action; template requires CMake
  ≥3.30.5 [doc]) → `cmake --preset macos` with a `CMakeUserPresets.json` setting
  `CMAKE_OSX_ARCHITECTURES=arm64`, buildspec `obs-studio: 32.2.2` → `cmake --build build_macos
  --config Debug` → `cmake --install build_macos --config Debug` (default prefix is the user plugin
  dir [src] defaults.cmake). Expect the first configure to download obs-deps (+Qt6 only if
  `ENABLE_QT`) and **build libobs from source** (minutes) [src] buildspec_common.cmake.

**Replay, no deck.** `create()` reads properties `replay_path` (a `.tpc`) and `pace_us` (default
16000 = device cadence) and fills `fs_config.capture.replay_path/replay_pace_us`; `on_frame` receives
`fp_frame` with an IOSurface → `IOSurfaceLock(kIOSurfaceLockReadOnly)`, `obs_source_frame{data[0] =
IOSurfaceGetBaseAddress, linesize[0] = IOSurfaceGetBytesPerRow, width 720, height 480, format UYVY,
timestamp = pts_num*1e9/pts_den, 601/limited matrix}` → `obs_source_output_video` (copies) →
`IOSurfaceUnlock`. Fixtures: `src/unit_parser/tests/fixture.tpc` (synthetic, `make` regenerates it)
for the smoke test; a real tape `.tpc` from `captures/` for content (check `ls -lO` first — the
renderer already refuses dataless placeholders, CLAUDE.md §11). **Audio needs new code**: an audio
batcher fed by `unit_audio_observation` (PCM records → S32 stereo, ~1601/1602 samples per resync
block, timestamp per the policy chosen in §1) exposed as a second sink in `fs_config` — the
frameserver has none today [local].

**Verify in OBS.** (1) OBS log "Loaded Modules:" lists `shuttle-obs`; absence → relaunch verbose and
look for the LOG_DEBUG loader lines [src]. (2) Add the source; Properties shows replay path/status;
preview shows the tape. (3) Counters: plugin-side `frames_submitted` vs `fs_stats.published` vs
recorded frame count (`ffprobe -count_frames`); OBS's own *View › Stats*: "Frames missed due to
rendering lag", "Skipped frames due to encoding lag" [local locale]. Remember libobs's 30-frame cache
purge is silent — a submitted-vs-recorded mismatch with zero OBS stats is that purge or a pacing
error [src]. (4) Timestamps: watch for "Timestamp for source … jumped" / "exceeded
TS_SMOOTHING_THRESHOLD" in a verbose log. (5) A/V: the replay fixture with a known audio click vs
video event (§11 milestone 2) measured in the recording.

**ProRes record.** Settings › Video: base/output 720×480, FPS *Fractional* 30000/1001 (woven) or
60000/1001 (Yadif 2x). Settings › Advanced: Color Format **P216**, Color Space **Rec. 601**, Range
**Limited**. Output (Advanced) › Recording: Type *Standard*, Format **Hybrid MOV (.mov)**, Video
Encoder **Apple VT ProRes Software Encoder** (Hardware if listed), ProRes Codec **422 HQ**, Audio
**ALAC**. Then `ffprobe`: `prores`, profile HQ, `yuv422p10le`, 720×480, 30000/1001, `alac` 48 kHz;
`idet` on a motion segment for the woven variant. Compare frame count and a per-frame luma
signature against the frameserver decision log.

## 7. Blockers and decisions for the owner

1. **CMake is not installed.** Route A (Makefile against OBS.app's framework + 32.2.2 headers) needs
   nothing new; Route B (obs-plugintemplate) needs `brew install cmake` and a first configure that
   builds libobs from source. Decide which is the canonical build (A for the dev loop, B when
   publishing is my recommendation; both can coexist if B is the source of truth for the bundle
   metadata).
2. **Audio sink does not exist in the frameserver.** Implementing it (PCM batching, S24→S32, resync
   anchoring) is real code, and the **timestamp policy** (§1: sample-count vs counter-anchored vs
   audio-as-master with video repeats) must be chosen before the first A/V recording is meaningful.
   My recommendation: audio-as-master (policy 3); it is the only one that never manufactures an
   audio discontinuity and keeps the correction on the video derivative.
3. **The OBS ProRes is a presentation copy, not the archive.** 8-bit canvas unless P216/P416; the
   RGB round trip may clamp sub-black/super-white; no field metadata; square pixels only. If the
   owner wants a *faithful* 4:2:2 file, the frameserver-side recorder (§9 FFV1/Matroska, or ProRes via
   `prores_ks` fed UYVY directly) remains the right place; the OBS path is for the OBS workflow.
   Required test before trusting it: synthetic Y=1/Y=250 frame through replay → measure the recorded Y.
4. **Woven-interlaced record via OBS is unsupported by OBS** (works only by construction: no
   scaling, no deinterlace, P216). Decide whether it is worth validating (idet test) or whether the OBS
   deliverable is always Yadif-2x 59.94p and interlace-preserving masters come from the native recorder.
5. **Hardware ProRes on base M3**: expect only the software encoder; fine at SD, but the property
   page must not assume "Hardware" exists.
6. **Single-session ownership**: one libusb context/session per process; define the behaviour of a
   second OBS source instance (refuse vs shared read-only) and of OBS's source duplication
   (`OBS_SOURCE_DO_NOT_DUPLICATE` is available [doc]).
7. **buildspec pin** (Route B): bump `obs-studio` to 32.2.2 and set arm64-only via
   `CMakeUserPresets.json`; universal builds are wasted time here and the x86_64 slice cannot be
   tested.
8. **Licensing**: static-linking LGPL libusb into a GPLv2+ plugin loaded by GPLv2 OBS is consistent
   with the NOTICE plan (CLAUDE.md §4); no new obligation, but the plugin's own license header must be
   GPLv2+ (template ships that header) [src].
9. **Unverified items worth a 10-minute check when work starts**: the `--verbose` launch flag URL;
   whether `ffmpeg -aspect 4:3 -c copy` on Hybrid-MOV output is a pure `pasp` rewrite; the P216 →
   AVPixelFormat mapping if the FFmpeg custom output is ever used.
