#ifndef SHUTTLE_DISCARD_STREAM_H
#define SHUTTLE_DISCARD_STREAM_H
/* An OBS streaming service and output that encode and drop everything (discard_stream.c). */
void discard_stream_register(void);   /* from obs_module_load */
int discard_service_selected(void);   /* the frontend's streaming service is the discard one */
#endif
