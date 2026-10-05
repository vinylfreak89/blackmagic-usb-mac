// Tools -> "Shuttle: tracking meter": a small floating window showing field 2's noise against field 1's,
// live, while the Shuttle source runs. Plain AppKit (no Qt): OBS's Tools-menu callbacks run on the
// main thread, which is AppKit's. Closing the window stops the measuring.
#import <AppKit/AppKit.h>
#include <obs-frontend-api.h>
#include "tracking_meter_tap.h"
#include "tracking_meter_window.h"

static const double kLo = 0.80, kHi = 1.25, kGood = 0.03;   // bar range and the "balanced" band

@interface TMView : NSView
@property (nonatomic) tmt_snapshot snap;
@end

@implementation TMView
- (BOOL)isFlipped { return YES; }

static NSColor *chanColor(int c){
    return c == TM_Y ? [NSColor labelColor] : c == TM_CB ? [NSColor systemBlueColor] : [NSColor systemRedColor];
}
static void drawText(NSString *s, NSPoint p, CGFloat size, NSColor *col, BOOL bold){
    NSFont *f = bold ? [NSFont monospacedDigitSystemFontOfSize:size weight:NSFontWeightSemibold]
                     : [NSFont monospacedDigitSystemFontOfSize:size weight:NSFontWeightRegular];
    [s drawAtPoint:p withAttributes:@{NSFontAttributeName: f, NSForegroundColorAttributeName: col}];
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
    if (!s->active) status = @"not measuring";
    else if (!s->fresh) status = @"waiting for picture from the Shuttle source";
    else if (!s->now.valid) status = @"not enough flat picture to measure (black, white or very busy)";
    else status = [NSString stringWithFormat:@"field 2 / field 1 noise over %u frames: 1.00 = both heads read alike. Fields as published (a flipped pairing swaps which head is which).", s->now.frames];
    drawText(status, NSMakePoint(pad, 10), 12, [NSColor secondaryLabelColor], NO);

    // One balance bar per channel: Y, Cb, Cr. Chroma usually moves most with tracking.
    const int order[3] = { TM_Y, TM_CB, TM_CR };
    NSString *names[3] = { @"Y", @"Cb", @"Cr" };
    CGFloat y = 36;
    NSRect bar = NSMakeRect(pad + 210, 0, W - pad * 2 - 210, 22);
    for (int i = 0; i < 3; i++, y += 44){
        int c = order[i];
        double v = (s->fresh && s->now.valid) ? s->now.ratio[c] : 0;
        BOOL good = v > 0 && fabs(v - 1.0) <= kGood;
        drawText(names[i], NSMakePoint(pad, y + 3), 15, [NSColor labelColor], NO);
        drawText(v > 0 ? [NSString stringWithFormat:@"%.2f", v] : @" –  ", NSMakePoint(pad + 100, y - 4), 26,
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
    drawText(@"field 2 cleaner", NSMakePoint(bar.origin.x, y - 16), 10, [NSColor tertiaryLabelColor], NO);
    drawText(@"field 2 noisier", NSMakePoint(NSMaxX(bar) - 74, y - 16), 10, [NSColor tertiaryLabelColor], NO);

    // History: the last two minutes, one point per half second.
    NSRect g = NSMakeRect(pad, y + 4, W - pad * 2, 110);
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
    drawText(@"last 2 minutes   Cb blue · Cr red · luma grey", NSMakePoint(pad, NSMaxY(g) + 4), 10, [NSColor tertiaryLabelColor], NO);

    // Fine-grain noise per field (not the tape's SNR: smeared chroma noise is not counted).
    if (s->fresh && s->now.valid){
        NSString *n = [NSString stringWithFormat:@"fine-grain noise, codes   field 1: Y %.2f Cb %.2f Cr %.2f   field 2: Y %.2f Cb %.2f Cr %.2f",
                       s->now.noise[0][TM_Y], s->now.noise[0][TM_CB], s->now.noise[0][TM_CR],
                       s->now.noise[1][TM_Y], s->now.noise[1][TM_CB], s->now.noise[1][TM_CR]];
        drawText(n, NSMakePoint(pad, NSMaxY(g) + 20), 10, [NSColor secondaryLabelColor], NO);
    }
}
@end

@interface TMController : NSObject <NSWindowDelegate>
@property (strong) NSPanel *panel;
@property (strong) TMView *view;
@property (strong) NSTimer *timer;
@end

@implementation TMController
- (void)show {
    if (!self.panel){
        NSRect r = NSMakeRect(200, 200, 600, 330);
        self.panel = [[NSPanel alloc] initWithContentRect:r
                                               styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskUtilityWindow
                                                 backing:NSBackingStoreBuffered defer:NO];
        self.panel.title = @"Shuttle tracking meter";
        self.panel.floatingPanel = YES;
        self.panel.hidesOnDeactivate = NO;
        self.panel.releasedWhenClosed = NO;
        self.panel.delegate = self;
        self.view = [[TMView alloc] initWithFrame:NSMakeRect(0, 0, r.size.width, r.size.height)];
        self.panel.contentView = self.view;
        [self.panel center];
    }
    tmt_start();
    if (!self.timer)
        self.timer = [NSTimer scheduledTimerWithTimeInterval:0.5 repeats:YES block:^(NSTimer *t){
            (void)t; tmt_snapshot s; tmt_snapshot_take(&s); self.view.snap = s; [self.view setNeedsDisplay:YES];
        }];
    [self.panel makeKeyAndOrderFront:nil];
}
- (void)windowWillClose:(NSNotification *)n {
    (void)n;
    [self.timer invalidate]; self.timer = nil;
    tmt_stop();
}
@end

static TMController *controller;

static void open_meter(void *data){
    (void)data;
    if (!controller) controller = [[TMController alloc] init];
    [controller show];
}

void tracking_meter_menu_register(void){
    obs_frontend_add_tools_menu_item("Shuttle: tracking meter", open_meter, NULL);
}

void tracking_meter_shutdown(void){
    tmt_stop();
}
