// Device input levels for the Shuttle source, set from the tracking meter window. The Shuttle takes them only at
// start-up, so a change restarts the source's capture session (about a second). Refused while OBS records or
// streams, so a capture is never interrupted. Stored in the source's settings, so they survive a restart of OBS.
#ifndef SHUTTLE_LEVELS_H
#define SHUTTLE_LEVELS_H
enum { SL_OK = 0, SL_NO_SOURCE = 1, SL_BUSY = 2 };
// gain[]: Y, Cb, Cr in the vendor control panel's units, -100..+100 (0 = nominal); setup_on: 7.5 IRE setup bit.
int shuttle_levels_get(int gain[3], int *setup_on);          // main thread
int shuttle_levels_set(const int gain[3], int setup_on);     // main thread; SL_BUSY while recording or streaming
int shuttle_levels_busy(void);                               // recording, streaming, replay buffer or virtual camera
unsigned shuttle_levels_generation(void);                    // changes when the source is created or destroyed
#endif
