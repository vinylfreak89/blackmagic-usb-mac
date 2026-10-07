// Tools -> "Shuttle: tracking meter": a small floating window showing field 2's noise against field 1's, live,
// while the Shuttle source runs. (The 7.5 IRE setup bit is in the source's own properties.)
// Plain AppKit (no Qt): OBS's Tools-menu callbacks run on the main thread, which is AppKit's. Closing the window
// stops the measuring. Class names carry a prefix: Objective-C classes share one namespace across all of OBS.
#import <AppKit/AppKit.h>
#include <obs-frontend-api.h>
#include <obs-module.h>
#include "tracking_meter_tap.h"
#include "tracking_meter_window.h"

static const double kLo = 0.80, kHi = 1.25, kGood = 0.03;   // bar range and the "balanced" band

@interface ShuttleTrackingMeterView : NSView
@property (nonatomic) tmt_snapshot snap;
@end

@implementation ShuttleTrackingMeterView
- (BOOL)isFlipped { return YES; }

static NSColor *chanColor(int c){
    return c == TM_Y ? [NSColor labelColor] : c == TM_CB ? [NSColor systemBlueColor] : [NSColor systemRedColor];
}
static void drawText(NSString *s, NSPoint p, CGFloat size, NSColor *col, BOOL bold){
    NSFont *f = bold ? [NSFont monospacedDigitSystemFontOfSize:size weight:NSFontWeightSemibold]
                     : [NSFont monospacedDigitSystemFontOfSize:size weight:NSFontWeightRegular];
    [s drawAtPoint:p withAttributes:@{NSFontAttributeName: f, NSForegroundColorAttributeName: col}];
}
static void drawWrapped(NSString *s, NSRect r, CGFloat size, NSColor *col){
    [s drawInRect:r withAttributes:@{NSFontAttributeName: [NSFont systemFontOfSize:size], NSForegroundColorAttributeName: col}];
}
static CGFloat xOf(double v, NSRect r){
    if (v < kLo) v = kLo; if (v > kHi) v = kHi;
    return r.origin.x + (v - kLo) / (kHi - kLo) * r.size.width;
}

- (void)drawRect:(NSRect)dirty {
    (void)dirty;
    [[NSColor windowBackgroundColor] setFill]; NSRectFill(self.bounds);
    const tmt_snapshot *s = &_snap;
    const CGFloat W = self.bounds.size.width, pad = 16;
    NSString *status;
    if (s->start_failed) status = @"The meter could not start (no memory or thread). Close and reopen the window.";
    else if (!s->active) status = @"Not measuring.";
    else if (!s->fresh) status = @"Waiting for picture from the Shuttle source.";
    else if (!s->now.valid){
        NSString *why = s->last_why == TM_FIELDS_IDENTICAL ? @"one field shown twice (a partial or search frame)"
                      : s->last_why == TM_NO_DETAIL ? @"no picture detail (a blank or muted screen)"
                      : s->last_why == TM_SNOW ? @"snow or an unlocked signal, not programme"
                      : @"too little picture between black and white";
        status = s->since_valid_s < 0 ? [NSString stringWithFormat:@"Nothing measurable yet: %@.", why]
               : [NSString stringWithFormat:@"No measurable picture for %.0f s: %@.", s->since_valid_s, why];
    } else status = [NSString stringWithFormat:@"Field 2 noise / field 1 noise over %u frames. 1.00 = both heads read alike. "
                     "Fields as published: a flipped pairing swaps which head is which.", s->now.frames];
    drawWrapped(status, NSMakeRect(pad, 8, W - 2 * pad, 32), 11, [NSColor secondaryLabelColor]);

    // One balance bar per channel: Y, Cb, Cr. Chroma usually moves most with tracking.
    const int order[3] = { TM_Y, TM_CB, TM_CR };
    NSString *names[3] = { @"Y", @"Cb", @"Cr" };
    CGFloat y = 46;
    NSRect bar = NSMakeRect(pad + 120, 0, W - pad * 2 - 120, 22);
    for (int i = 0; i < 3; i++, y += 40){
        int c = order[i];
        double v = (s->fresh && s->now.valid) ? s->now.ratio[c] : 0;
        BOOL good = v > 0 && fabs(v - 1.0) <= kGood;
        drawText(names[i], NSMakePoint(pad, y + 2), 15, [NSColor labelColor], NO);
        drawText(v > 0 ? [NSString stringWithFormat:@"%.2f", v] : @" –  ", NSMakePoint(pad + 36, y - 4), 24,
                 v <= 0 ? [NSColor tertiaryLabelColor] : good ? [NSColor systemGreenColor] : [NSColor labelColor], YES);
        bar.origin.y = y + 2;
        [[NSColor quaternaryLabelColor] setFill]; [[NSBezierPath bezierPathWithRoundedRect:bar xRadius:4 yRadius:4] fill];
        NSRect band = bar; band.origin.x = xOf(1.0 - kGood, bar); band.size.width = xOf(1.0 + kGood, bar) - band.origin.x;
        [[[NSColor systemGreenColor] colorWithAlphaComponent:0.25] setFill]; NSRectFill(band);
        [[NSColor secondaryLabelColor] setFill]; NSRectFill(NSMakeRect(xOf(1.0, bar) - 0.5, bar.origin.y - 3, 1, bar.size.height + 6));
        if (v > 0){
            NSRect mark = NSMakeRect(xOf(v, bar) - 4, bar.origin.y - 2, 8, bar.size.height + 4);
            [(good ? [NSColor systemGreenColor] : chanColor(c)) setFill];
            [[NSBezierPath bezierPathWithRoundedRect:mark xRadius:2 yRadius:2] fill];
        }
    }
    drawText(@"field 2 cleaner", NSMakePoint(bar.origin.x, y - 14), 10, [NSColor tertiaryLabelColor], NO);
    drawText(@"field 2 noisier", NSMakePoint(NSMaxX(bar) - 74, y - 14), 10, [NSColor tertiaryLabelColor], NO);

    // History: the last two minutes, one point per half second.
    NSRect g = NSMakeRect(pad, y + 6, W - pad * 2, 96);
    [[NSColor quaternaryLabelColor] setFill]; NSRectFill(g);
    CGFloat (^gy)(double) = ^CGFloat(double v){
        if (v < kLo) v = kLo; if (v > kHi) v = kHi;
        return NSMaxY(g) - (v - kLo) / (kHi - kLo) * g.size.height;
    };
    NSRect gb = NSMakeRect(g.origin.x, gy(1.0 + kGood), g.size.width, gy(1.0 - kGood) - gy(1.0 + kGood));
    [[[NSColor systemGreenColor] colorWithAlphaComponent:0.20] setFill]; NSRectFill(gb);
    [[NSColor secondaryLabelColor] setFill]; NSRectFill(NSMakeRect(g.origin.x, gy(1.0), g.size.width, 1));
    for (int c = 0; c < TM_CHANNELS; c++){
        NSBezierPath *p = [NSBezierPath bezierPath]; [p setLineWidth:c == TM_Y ? 1.0 : 1.6];
        BOOL pen = NO;
        for (unsigned i = 0; i < s->history_n; i++){
            double v = s->history[i][c];
            CGFloat x = NSMaxX(g) - (CGFloat)(s->history_n - 1 - i) * g.size.width / (TMT_HISTORY - 1);
            if (v <= 0){ pen = NO; continue; }
            if (pen) [p lineToPoint:NSMakePoint(x, gy(v))]; else { [p moveToPoint:NSMakePoint(x, gy(v))]; pen = YES; }
        }
        [chanColor(c) setStroke]; [p stroke];
    }
    drawText(@"last 2 minutes (while this window is open)   Y grey · Cb blue · Cr red", NSMakePoint(pad, NSMaxY(g) + 3), 10, [NSColor tertiaryLabelColor], NO);
    if (s->fresh && s->now.valid){
        NSString *n = [NSString stringWithFormat:@"fine-grain noise, codes   field 1: Y %.2f Cb %.2f Cr %.2f   field 2: Y %.2f Cb %.2f Cr %.2f",
                       s->now.noise[0][TM_Y], s->now.noise[0][TM_CB], s->now.noise[0][TM_CR],
                       s->now.noise[1][TM_Y], s->now.noise[1][TM_CB], s->now.noise[1][TM_CR]];
        drawText(n, NSMakePoint(pad, NSMaxY(g) + 17), 10, [NSColor secondaryLabelColor], NO);
    }
}
@end

@interface ShuttleTrackingMeterController : NSObject <NSWindowDelegate>
@property (strong) NSPanel *panel;
@property (strong) ShuttleTrackingMeterView *view;
@property (strong) NSTimer *timer;
@end

@implementation ShuttleTrackingMeterController
- (void)show {
    if (!self.panel){
        NSRect r = NSMakeRect(200, 200, 620, 310);
        self.panel = [[NSPanel alloc] initWithContentRect:r
                                               styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskUtilityWindow
                                                 backing:NSBackingStoreBuffered defer:NO];
        self.panel.title = @"Shuttle tracking meter";
        self.panel.floatingPanel = YES;
        self.panel.hidesOnDeactivate = NO;
        self.panel.releasedWhenClosed = NO;
        self.panel.delegate = self;
        self.view = [[ShuttleTrackingMeterView alloc] initWithFrame:NSMakeRect(0, 0, r.size.width, r.size.height)];
        self.panel.contentView = self.view;
        [self.panel center];
    }
    tmt_start();
    if (!self.timer){
        __weak ShuttleTrackingMeterController *weakSelf = self;
        self.timer = [NSTimer timerWithTimeInterval:0.5 repeats:YES block:^(NSTimer *t){
            (void)t; ShuttleTrackingMeterController *me = weakSelf; if (!me) return;
            tmt_snapshot s; tmt_snapshot_take(&s); me.view.snap = s; [me.view setNeedsDisplay:YES];
        }];
        [[NSRunLoop mainRunLoop] addTimer:self.timer forMode:NSRunLoopCommonModes];   // keeps ticking during menus
    }
    [self.panel makeKeyAndOrderFront:nil];
}
- (void)stopTimer { [self.timer invalidate]; self.timer = nil; }
- (void)windowWillClose:(NSNotification *)n {
    (void)n;
    [self stopTimer];
    tmt_stop();
}
@end

static ShuttleTrackingMeterController *controller;

static void open_meter(void *data){
    (void)data;
    if (!controller) controller = [[ShuttleTrackingMeterController alloc] init];
    [controller show];
}

void tracking_meter_menu_register(void){
    obs_frontend_add_tools_menu_item("Shuttle: tracking meter", open_meter, NULL);
}

void tracking_meter_shutdown(void){
    // OBS is unloading the plugin: stop the timer and close the window first, so nothing calls into it later.
    if (controller){ [controller stopTimer]; controller.panel.delegate = nil; [controller.panel orderOut:nil]; }
    tmt_stop();
}
