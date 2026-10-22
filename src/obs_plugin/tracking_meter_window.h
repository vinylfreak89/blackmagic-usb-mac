// Tools -> "Shuttle: tracking meter" (tracking_meter_window.m).
#ifndef TRACKING_METER_WINDOW_H
#define TRACKING_METER_WINDOW_H
void tracking_meter_menu_register(void);   // from obs_module_load
void tracking_meter_shutdown(void);        // from obs_module_unload: stop the measuring thread
#endif
