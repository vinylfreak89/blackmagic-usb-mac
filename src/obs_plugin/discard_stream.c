/* "Stream to discard": an OBS streaming service and output that run the whole streaming path (OBS's
 * encoders included) and throw the encoded packets away. With it selected, Start Streaming exercises
 * the capture pipeline end to end and the source writes its raw .tpc and sidecar exactly as for a
 * recording (shuttle_source.c), with no recording file and nothing sent anywhere.
 *
 * OBS 32.2.2's Stream settings page lists only its own service kinds (rtmp_common, rtmp_custom,
 * whip_custom: frontend/settings/OBSBasicSettings_Stream.cpp), so the service is selected from
 * Tools -> "Shuttle: stream to discard" (obs_frontend_set_streaming_service + save). The frontend picks
 * the output from the service's protocol and preferred output type (GetStreamOutputType,
 * frontend/utility/BasicOutputHandler.cpp). Choosing a service on the Stream settings page and pressing
 * OK replaces it again; opening Settings without touching that page leaves it in place (the page saves
 * only when stream1Changed). */
#include <obs-module.h>
#include <obs-frontend-api.h>
#include <util/platform.h>
#include <stdatomic.h>
#include <string.h>
#include "discard_stream.h"

#define DISCARD_PROTOCOL "SHUTTLE_DISCARD"
#define DISCARD_OUTPUT "shuttle_discard_output"
#define DISCARD_SERVICE "shuttle_discard_service"
#define DISCARD_URL "shuttle-discard://"

/* ---- output ---- */
struct discard_out {
    obs_output_t *output;
    _Atomic unsigned long long bytes, video_packets, audio_packets;
    uint64_t started_ns;
};
static const char *dout_name(void *t){ (void)t; return "Shuttle: encode and discard"; }
static void *dout_create(obs_data_t *settings, obs_output_t *output){
    (void)settings; struct discard_out *d = bzalloc(sizeof *d); d->output = output; return d;
}
static void dout_destroy(void *p){ bfree(p); }
static bool dout_start(void *p){
    struct discard_out *d = p;
    if (!obs_output_can_begin_data_capture(d->output, 0)) return false;
    if (!obs_output_initialize_encoders(d->output, 0)) return false;
    atomic_store(&d->bytes, 0); atomic_store(&d->video_packets, 0); atomic_store(&d->audio_packets, 0);
    d->started_ns = os_gettime_ns();
    blog(LOG_INFO, "[shuttle-source] discard stream started: encoding runs, packets are dropped");
    return obs_output_begin_data_capture(d->output, 0);
}
static void dout_stop(void *p, uint64_t ts){
    (void)ts; struct discard_out *d = p;
    obs_output_end_data_capture(d->output);
    double s = (os_gettime_ns() - d->started_ns) / 1e9;
    blog(LOG_INFO, "[shuttle-source] discard stream stopped after %.1f s: %llu video and %llu audio packets, %.1f MB encoded and dropped",
         s, (unsigned long long)atomic_load(&d->video_packets), (unsigned long long)atomic_load(&d->audio_packets), atomic_load(&d->bytes) / 1e6);
}
static void dout_packet(void *p, struct encoder_packet *pkt){
    struct discard_out *d = p;
    if (!pkt){ obs_output_signal_stop(d->output, OBS_OUTPUT_ENCODE_ERROR); return; }   /* an encoder failed: end the stream like any output would */
    atomic_fetch_add(&d->bytes, pkt->size);
    if (pkt->type == OBS_ENCODER_VIDEO) atomic_fetch_add(&d->video_packets, 1); else atomic_fetch_add(&d->audio_packets, 1);
}
static uint64_t dout_total_bytes(void *p){ struct discard_out *d = p; return atomic_load(&d->bytes); }
static struct obs_output_info discard_output = {
    .id = DISCARD_OUTPUT,
    .flags = OBS_OUTPUT_AV | OBS_OUTPUT_ENCODED | OBS_OUTPUT_SERVICE,
    .get_name = dout_name, .create = dout_create, .destroy = dout_destroy,
    .start = dout_start, .stop = dout_stop, .encoded_packet = dout_packet, .get_total_bytes = dout_total_bytes,
    .encoded_video_codecs = "h264;hevc;av1;prores",
    .encoded_audio_codecs = "aac;opus;alac;pcm_s16le;pcm_s24le;pcm_f32le",
    .protocols = DISCARD_PROTOCOL,
};

/* ---- service ---- */
static const char *dsvc_name(void *t){ (void)t; return "Shuttle: stream to discard (nothing is sent or saved)"; }
static void *dsvc_create(obs_data_t *settings, obs_service_t *service){ (void)settings; (void)service; return bzalloc(1); }
static void dsvc_destroy(void *p){ bfree(p); }
static const char *dsvc_url(void *p){ (void)p; return DISCARD_URL; }
static const char *dsvc_key(void *p){ (void)p; return ""; }
static const char *dsvc_output_type(void *p){ (void)p; return DISCARD_OUTPUT; }
static const char *dsvc_protocol(void *p){ (void)p; return DISCARD_PROTOCOL; }
static const char *dsvc_connect_info(void *p, uint32_t type){ (void)p; return type == OBS_SERVICE_CONNECT_INFO_SERVER_URL ? DISCARD_URL : ""; }
static bool dsvc_can_connect(void *p){ (void)p; return true; }
static struct obs_service_info discard_service = {
    .id = DISCARD_SERVICE,
    .get_name = dsvc_name, .create = dsvc_create, .destroy = dsvc_destroy,
    .get_url = dsvc_url, .get_key = dsvc_key, .get_output_type = dsvc_output_type, .get_protocol = dsvc_protocol,
    .get_connect_info = dsvc_connect_info, .can_try_to_connect = dsvc_can_connect,
};

/* ---- Tools menu: select it ---- */
static void use_discard(void *data){
    (void)data;
    if (obs_frontend_streaming_active()){ blog(LOG_WARNING, "[shuttle-source] stream to discard: not changed while a stream is running"); return; }
    obs_service_t *svc = obs_service_create(DISCARD_SERVICE, "Shuttle discard", NULL, NULL);
    if (!svc){ blog(LOG_ERROR, "[shuttle-source] stream to discard: the service could not be created"); return; }
    obs_frontend_set_streaming_service(svc); obs_frontend_save_streaming_service(); obs_service_release(svc);
    blog(LOG_INFO, "[shuttle-source] streaming now goes to discard: Start Streaming encodes and drops everything; the source writes its raw .tpc and sidecar as for a recording. Choose a service in Settings -> Stream to change back.");
}
int discard_service_selected(void){
    obs_service_t *svc = obs_frontend_get_streaming_service();
    return svc && strcmp(obs_service_get_id(svc), DISCARD_SERVICE) == 0;
}
void discard_stream_register(void){
    obs_register_output(&discard_output);
    obs_register_service(&discard_service);
    obs_frontend_add_tools_menu_item("Shuttle: stream to discard", use_discard, NULL);
}
