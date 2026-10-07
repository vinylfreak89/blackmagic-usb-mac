# shuttle-source: native OBS Studio source plugin, "route A" dev loop (src/obs_plugin/PLUGIN_SPIKE.md).
# Links against OBS.app's own libobs.framework (no CMake, no obs-deps); needs the matching libobs
# headers from the obs-studio source tree of the SAME version (OBS_HEADERS). libusb is linked
# statically so the bundle is one Mach-O with one ad-hoc signature. No Apple account required.
#   make            build shuttle-source.plugin
#   make install    copy it to ~/Library/Application Support/obs-studio/plugins (restart OBS)
#   make uninstall
CC ?= clang
OBS_APP ?= /Applications/OBS.app
OBS_HEADERS ?= $(HOME)/Library/Application Support/blackmagic-usb-mac/obs-headers-32.2.2/libobs
# frontend/obs-frontend-api.h sits beside libobs/ in OBS_HEADERS's parent (same obs-studio tag)
# SIMDe (header-only SSE emulation): the libobs headers need it on arm64
SIMDE_DIR ?= $(HOME)/Library/Application Support/blackmagic-usb-mac/simde-0.8.2
LIBUSB_A ?= /opt/homebrew/opt/libusb/lib/libusb-1.0.a
PLUGIN = shuttle-source
# The bundle is assembled OUTSIDE the repo: the checkout lives under a cloud-synced root whose
# Finder/iCloud xattrs reappear on the bundle and make codesign refuse ("detritus"). /private/tmp
# is local and non-synced; `make install` copies from there.
BUILD_DIR ?= /private/tmp/blackmagic-usb-mac-build
BUNDLE = $(BUILD_DIR)/$(PLUGIN).plugin
INSTALL_DIR = $(HOME)/Library/Application Support/obs-studio/plugins

CORE = ../capture_core/capture_core.c ../unit_parser/unit_parser.c ../signal_state/signal_state.c \
       ../field_registration/geometry_engine.c ../frameserver/frame_publisher.c \
       ../frameserver/audio_publisher.c ../frameserver/frameserver.c ../frameserver/async_file.c ../frameserver/pairing_schedule.c ../frameserver/hretime.c ../frameserver/replay_probe.c
CPPFLAGS = -I. -I"$(OBS_HEADERS)" -I"$(OBS_HEADERS)/../frontend" -I"$(SIMDE_DIR)" -I.. -I../capture_core -I../frameserver $(shell pkg-config --cflags libusb-1.0)
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wno-unused-parameter -fvisibility=hidden
# obs-frontend-api.dylib (recording started/stopped events, recording output) is linked by path;
# its install name is @rpath/obs-frontend-api.dylib, resolved by the rpaths below at load time.
LDFLAGS = -bundle -F"$(OBS_APP)/Contents/Frameworks" -framework libobs "$(OBS_APP)/Contents/Frameworks/obs-frontend-api.dylib" \
          -Wl,-rpath,@executable_path/../Frameworks -Wl,-rpath,@loader_path/../../../../Frameworks \
          -framework IOSurface -framework CoreFoundation -framework Foundation -framework IOKit -framework Security -lpthread -lm

all: $(BUNDLE)

$(BUNDLE): shuttle_source.c discard_stream.c discard_stream.h tracking_meter.c tracking_meter.h tracking_meter_tap.c tracking_meter_tap.h tracking_meter_window.m tracking_meter_window.h audio_timing.h frame_levels.h replay_timeline.h ../frameserver/replay_probe.h publish_copy.c publish_copy.h publish_queue.c publish_queue.h timing_report.c timing_report.h obsconfig.h Info.plist $(CORE) ../frameserver/pairing_schedule.h ../frameserver/audio_publisher.h ../frameserver/hretime.h
	mkdir -p "$(BUILD_DIR)"; rm -rf $(BUNDLE); mkdir -p $(BUNDLE)/Contents/MacOS $(BUNDLE)/Contents/Resources/locale
	$(CC) $(CPPFLAGS) -O2 -Wall -Wextra -Wno-unused-parameter -fvisibility=hidden -fobjc-arc -c tracking_meter_window.m -o "$(BUILD_DIR)/tracking_meter_window.o"
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -framework AppKit "$(BUILD_DIR)/tracking_meter_window.o" tracking_meter.c tracking_meter_tap.c shuttle_source.c discard_stream.c publish_copy.c publish_queue.c timing_report.c $(CORE) "$(LIBUSB_A)" -o $(BUNDLE)/Contents/MacOS/$(PLUGIN)
	cp Info.plist $(BUNDLE)/Contents/Info.plist
	printf 'ShuttleSource="Blackmagic Intensity Shuttle (frameserver)"\n' > $(BUNDLE)/Contents/Resources/locale/en-US.ini
	cp $(BUNDLE)/Contents/Resources/locale/en-US.ini $(BUNDLE)/Contents/Resources/locale/ja-JP.ini
	xattr -cr $(BUNDLE)    # iCloud/Finder xattrs on the bundle make codesign refuse ("detritus")
	codesign --force --sign - $(BUNDLE)
	@echo "built $(BUNDLE)"; otool -L $(BUNDLE)/Contents/MacOS/$(PLUGIN) | grep -E 'libobs|libusb' || true

test: test-tracking-meter test-audio test-frame-levels test-timing-report test-replay-timeline test-media-controls publish_copy.c publish_copy.h tests_publish_copy.c publish_queue.c publish_queue.h tests_publish_queue.c
	$(CC) -O1 -g -fsanitize=address,undefined -std=c11 -Wall -Wextra publish_copy.c tests_publish_copy.c -o tests_publish_copy && ./tests_publish_copy
	$(CC) -DPUBLISH_QUEUE_TEST_HOOKS -O1 -g -fsanitize=address,undefined -std=c11 -Wall -Wextra publish_queue.c tests_publish_queue.c -o tests_publish_queue -lpthread && ./tests_publish_queue
	$(CC) -DPUBLISH_QUEUE_TEST_HOOKS -O1 -g -fsanitize=thread -std=c11 -Wall -Wextra publish_queue.c tests_publish_queue.c -o tests_publish_queue_tsan -lpthread && ./tests_publish_queue_tsan

.PHONY: test-tracking-meter test-audio test-frame-levels test-replay-timeline test-media-controls
# The plugin's media controls in a test process: libobs replaced by stubs, the real frameserver
# replaying the plain synthetic fixture. Plain and ThreadSanitizer builds.
MEDIA_FIXTURE = ../unit_parser/tests/fixture_plain.tpc
test-media-controls: shuttle_source.c tracking_meter.c tracking_meter_tap.c frame_levels.h tests_media_controls.c tests_obs_stubs.c tests_obs_stubs.h replay_timeline.h $(CORE) publish_copy.c publish_queue.c timing_report.c
	$(MAKE) -C ../unit_parser tests/fixture_plain.tpc
	$(CC) $(CPPFLAGS) -DSHUTTLE_TEST_HOOKS -DRECONNECT_INTERVAL_NS=20000000ull -O1 -g -std=c11 -Wall -Wno-unused-parameter shuttle_source.c publish_copy.c publish_queue.c timing_report.c tests_obs_stubs.c tests_media_controls.c tracking_meter.c tracking_meter_tap.c $(CORE) "$(LIBUSB_A)" -o tests_media_controls -framework IOSurface -framework CoreFoundation -framework Foundation -framework IOKit -framework Security -lpthread -lm && ./tests_media_controls $(MEDIA_FIXTURE)
	$(CC) $(CPPFLAGS) -DSHUTTLE_TEST_HOOKS -DRECONNECT_INTERVAL_NS=20000000ull -O1 -g -fsanitize=thread -std=c11 -Wall -Wno-unused-parameter shuttle_source.c publish_copy.c publish_queue.c timing_report.c tests_obs_stubs.c tests_media_controls.c tracking_meter.c tracking_meter_tap.c $(CORE) "$(LIBUSB_A)" -o tests_media_controls_tsan -framework IOSurface -framework CoreFoundation -framework Foundation -framework IOKit -framework Security -lpthread -lm && ./tests_media_controls_tsan $(MEDIA_FIXTURE)

test-replay-timeline: replay_timeline.h tests_replay_timeline.c
	$(CC) -O1 -g -fsanitize=address,undefined -std=c11 -Wall -Wextra tests_replay_timeline.c -o tests_replay_timeline && ./tests_replay_timeline

test-timing-report: timing_report.c timing_report.h tests_timing_report.c
	$(CC) -O1 -g -fsanitize=address,undefined -std=c11 -Wall -Wextra -I../frameserver -I../capture_core -I../unit_parser -I../signal_state -I../field_registration timing_report.c tests_timing_report.c -o tests_timing_report -lpthread && ./tests_timing_report
	$(CC) -O1 -g -fsanitize=thread -std=c11 -Wall -Wextra -I../frameserver -I../capture_core -I../unit_parser -I../signal_state -I../field_registration timing_report.c tests_timing_report.c -o tests_timing_report_tsan -lpthread && ./tests_timing_report_tsan

test-frame-levels: frame_levels.h tests_frame_levels.c
	$(CC) -O1 -g -fsanitize=address,undefined -std=c11 -Wall -Wextra tests_frame_levels.c -o tests_frame_levels && ./tests_frame_levels

# The tracking meter's known answers (synthetic fields with chosen noise), and its checking tool:
#   ../frameserver/frameserver_replay <capture.tpc> --dump-uyvy /dev/stdout --limit-units N | ./tracking_meter_cli
test-tracking-meter: tracking_meter.c tracking_meter.h tests_tracking_meter.c tracking_meter_tap.c tracking_meter_tap.h tests_tracking_meter_tap.c
	$(CC) -O1 -g -fsanitize=address,undefined -std=c11 -Wall -Wextra tracking_meter.c tests_tracking_meter.c -o tests_tracking_meter -lm && ./tests_tracking_meter
	$(CC) -O1 -g -fsanitize=thread -std=c11 -Wall -Wextra tracking_meter.c tracking_meter_tap.c tests_tracking_meter_tap.c -o tests_tracking_meter_tap -lm && ./tests_tracking_meter_tap

tracking_meter_cli: tracking_meter.c tracking_meter.h tracking_meter_cli.c
	$(CC) -O2 -std=c11 -Wall -Wextra tracking_meter.c tracking_meter_cli.c -o tracking_meter_cli -lm

test-audio:
	$(CC) -O1 -g -fsanitize=address,undefined -std=c11 -Wall -Wextra tests_audio_timing.c -o tests_audio_timing
	./tests_audio_timing

install: $(BUNDLE)
	mkdir -p "$(INSTALL_DIR)"
	rm -rf "$(INSTALL_DIR)/$(PLUGIN).plugin"
	cp -R $(BUNDLE) "$(INSTALL_DIR)/"; xattr -cr "$(INSTALL_DIR)/$(PLUGIN).plugin"; codesign --verify --deep "$(INSTALL_DIR)/$(PLUGIN).plugin" && echo "installed signature verifies"
	@echo "installed to $(INSTALL_DIR)/$(PLUGIN).plugin -- restart OBS"

uninstall:
	rm -rf "$(INSTALL_DIR)/$(PLUGIN).plugin"

clean:
	rm -rf $(BUNDLE) tests_timing_report tests_timing_report_tsan tests_publish_copy tests_publish_queue tests_publish_queue_tsan tests_audio_timing tests_frame_levels $(PLUGIN).plugin
