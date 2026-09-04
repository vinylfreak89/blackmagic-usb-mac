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
       ../field_registration/field_registration.c ../frameserver/frame_publisher.c \
       ../frameserver/audio_publisher.c ../frameserver/frameserver.c
CPPFLAGS = -I. -I"$(OBS_HEADERS)" -I"$(OBS_HEADERS)/../frontend" -I"$(SIMDE_DIR)" -I.. -I../capture_core -I../frameserver $(shell pkg-config --cflags libusb-1.0)
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wno-unused-parameter -fvisibility=hidden
# obs-frontend-api.dylib (recording started/stopped events, recording output) is linked by path;
# its install name is @rpath/obs-frontend-api.dylib, resolved by the rpaths below at load time.
LDFLAGS = -bundle -F"$(OBS_APP)/Contents/Frameworks" -framework libobs "$(OBS_APP)/Contents/Frameworks/obs-frontend-api.dylib" \
          -Wl,-rpath,@executable_path/../Frameworks -Wl,-rpath,@loader_path/../../../../Frameworks \
          -framework IOSurface -framework CoreFoundation -framework IOKit -framework Security -lpthread -lm

all: $(BUNDLE)

$(BUNDLE): shuttle_source.c publish_copy.c publish_copy.h publish_queue.c publish_queue.h obsconfig.h Info.plist $(CORE)
	mkdir -p "$(BUILD_DIR)"; rm -rf $(BUNDLE); mkdir -p $(BUNDLE)/Contents/MacOS $(BUNDLE)/Contents/Resources/locale
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) shuttle_source.c publish_copy.c publish_queue.c $(CORE) "$(LIBUSB_A)" -o $(BUNDLE)/Contents/MacOS/$(PLUGIN)
	cp Info.plist $(BUNDLE)/Contents/Info.plist
	printf 'ShuttleSource="Blackmagic Intensity Shuttle (frameserver)"\n' > $(BUNDLE)/Contents/Resources/locale/en-US.ini
	cp $(BUNDLE)/Contents/Resources/locale/en-US.ini $(BUNDLE)/Contents/Resources/locale/ja-JP.ini
	xattr -cr $(BUNDLE)    # iCloud/Finder xattrs on the bundle make codesign refuse ("detritus")
	codesign --force --sign - $(BUNDLE)
	@echo "built $(BUNDLE)"; otool -L $(BUNDLE)/Contents/MacOS/$(PLUGIN) | grep -E 'libobs|libusb' || true

test: publish_copy.c publish_copy.h tests_publish_copy.c publish_queue.c publish_queue.h tests_publish_queue.c
	$(CC) -O1 -g -fsanitize=address,undefined -std=c11 -Wall -Wextra publish_copy.c tests_publish_copy.c -o tests_publish_copy && ./tests_publish_copy
	$(CC) -O1 -g -fsanitize=address,undefined -std=c11 -Wall -Wextra publish_queue.c tests_publish_queue.c -o tests_publish_queue -lpthread && ./tests_publish_queue
	$(CC) -O1 -g -fsanitize=thread -std=c11 -Wall -Wextra publish_queue.c tests_publish_queue.c -o tests_publish_queue_tsan -lpthread && ./tests_publish_queue_tsan

install: $(BUNDLE)
	mkdir -p "$(INSTALL_DIR)"
	rm -rf "$(INSTALL_DIR)/$(BUNDLE)"
	cp -R $(BUNDLE) "$(INSTALL_DIR)/"; xattr -cr "$(INSTALL_DIR)/$(PLUGIN).plugin"; codesign --verify --deep "$(INSTALL_DIR)/$(PLUGIN).plugin" && echo "installed signature verifies"
	@echo "installed to $(INSTALL_DIR)/$(PLUGIN).plugin -- restart OBS"

uninstall:
	rm -rf "$(INSTALL_DIR)/$(BUNDLE)"

clean:
	rm -rf $(BUNDLE) tests_publish_copy tests_publish_queue tests_publish_queue_tsan $(PLUGIN).plugin
