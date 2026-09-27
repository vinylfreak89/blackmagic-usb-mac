/* Controlled interleavings of the actual parser handoff, live publication and
 * log writer. The condition handshake proves the writer is inside its seqlock;
 * a timeout is only failure, never evidence of overlap. */
#include "../frameserver.c"
#include "../../test_condition.h"
#include "../../test_supervisor.h"
#include <assert.h>

static pthread_mutex_t gate_m=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t gate_c=PTHREAD_COND_INITIALIZER;
static int blocked,release_writer;
static uint64_t block_counter=UINT64_MAX;
static int callback_count,callback_known;
static uint64_t callback_pts;

void ap_test_correlation_writing(audio_publisher *p,uint64_t c){
    (void)p;
    pthread_mutex_lock(&gate_m);
    if(c==block_counter){
        blocked=1;pthread_cond_broadcast(&gate_c);
        double until=test_until("AUDIO_EVIDENCE_WAIT_S");
        while(!release_writer)test_condition(&gate_c,&gate_m,until,"release correlation writer");
    }
    pthread_mutex_unlock(&gate_m);
}
static void noop_audio(void *ctx,const ap_block *b){(void)ctx;(void)b;}
static void video(void *ctx,const fp_frame *f){
    (void)ctx;callback_count++;callback_known=f->audio_pts_known;callback_pts=f->audio_pts_num;
}
static void resync(audio_publisher *p,uint64_t c,uint64_t ordinal){
    unit_audio_observation o={.kind=UNIT_AUDIO_RESYNC,.epoch=1,.counter_extended=c,.sample_ordinal=ordinal};
    ap_on_audio(p,&o);
}
static void *writer(void *ctx){resync(ctx,12,3203);return NULL;}
static void wait_writer(void){
    pthread_mutex_lock(&gate_m);double until=test_until("AUDIO_EVIDENCE_WAIT_S");
    while(!blocked)test_condition(&gate_c,&gate_m,until,"correlation writer entered");
    pthread_mutex_unlock(&gate_m);
}
static void unblock_writer(void){
    pthread_mutex_lock(&gate_m);release_writer=1;pthread_cond_broadcast(&gate_c);pthread_mutex_unlock(&gate_m);
}
static void check_audio_cells(FILE *f,const char *residual,const char *step){
    fflush(f);rewind(f);char line[8192];assert(fgets(line,sizeof line,f));
    char *cursor=line,*cell;
    for(unsigned col=0;col<=37;col++){
        cell=strsep(&cursor,",");assert(cell);
        if(col==36 && strcmp(cell,residual)){
            fprintf(stderr,"FAIL: audio_residual_ticks expected '%s', got '%s'\n",residual,cell);exit(1);
        }
        if(col==37 && strcmp(cell,step)){
            fprintf(stderr,"FAIL: audio_step_samples expected '%s', got '%s'\n",step,cell);exit(1);
        }
    }
}
static fs_item capture_video(frameserver *f,uint8_t *unit,uint64_t epoch,uint64_t counter){
    atomic_store(&f->slot_used[0],0);
    unsigned h=atomic_load(&f->r_head);atomic_store(&f->r_tail,h);
    unit_video_observation o={.epoch=epoch,.counter_extended=counter,.fixed_raster_eligible=1,
        .byte_count=FP_UNIT_BYTES,.bytes=unit};
    on_video(f,&o);return f->ring[h%RING_ITEMS];
}
static void fresh_log(frameserver *f){
    if(f->log)fclose(f->log);
    f->log=tmpfile();assert(f->log);
}
int main(int argc,char **argv){
    (void)argc;test_supervise(argv,"AUDIO_EVIDENCE_TOTAL_S","audio_evidence_test");
    frameserver *f=calloc(1,sizeof *f);assert(f);
    ge_config config=ge_default_config();f->cfg.geometry_config=&config;
    assert(!pthread_mutex_init(&f->m,NULL));assert(!pthread_cond_init(&f->c,NULL));
    assert(!pthread_mutex_init(&f->log_m,NULL));f->n_slots=1;
    f->pool=calloc(1,FP_UNIT_BYTES);f->slot_used=calloc(1,sizeof *f->slot_used);assert(f->pool && f->slot_used);
    ap_sink audio={noop_audio,NULL};fp_sink sink={video,NULL};
    assert(!ap_open(&f->aud,4096,&audio));assert(!fp_open(&f->pub,2,&sink));
    resync(f->aud,10,0);resync(f->aud,11,1601);
    uint8_t *unit=calloc(1,FP_UNIT_BYTES);assert(unit);
    fs_item it=capture_video(f,unit,1,11);
    ge_decision d={.counter=11};d.comb.margin=NAN;
    fresh_log(f);
    block_counter=12;pthread_t thread;assert(!pthread_create(&thread,NULL,writer,f->aud));wait_writer();
    /* Counter 11 is already complete. An unrelated counter 12 write holds the
     * global sequence odd. Video must publish without waiting on that writer. */
    geometry_publish(f,&it,f->pool,&d,NULL);
    assert(callback_count==1 && !callback_known && !callback_pts);
    unblock_writer();assert(!pthread_join(thread,NULL));
    check_audio_cells(f->log,"3","0");

    /* History eviction after ingress cannot retroactively erase log evidence. */
    block_counter=UINT64_MAX;
    for(uint64_t c=13;c<13+AP_LOOKUP_ENTRIES;c++)resync(f->aud,c,c*1601);
    fresh_log(f);geometry_publish(f,&it,f->pool,&d,NULL);
    assert(callback_count==2 && !callback_known);
    check_audio_cells(f->log,"3","0");

    /* Future audio remains a deterministic empty log cell, even if available
     * at live publication. An absent cell is not invented zero residual. */
    it=capture_video(f,unit,1,700);d.counter=700;
    fresh_log(f);geometry_publish(f,&it,f->pool,&d,NULL);
    assert(!callback_known);check_audio_cells(f->log,"","");
    resync(f->aud,700,700*1601);
    fresh_log(f);geometry_publish(f,&it,f->pool,&d,NULL);
    assert(callback_known);check_audio_cells(f->log,"","");

    /* Epoch ownership and a fresh run seed the residual instead of comparing
     * it against another epoch. Stored reversed-pair items use the same copy. */
    unit_audio_observation a={.kind=UNIT_AUDIO_RESYNC,.epoch=2,.counter_extended=11,.sample_ordinal=9999};
    ap_on_audio(f->aud,&a);
    it=capture_video(f,unit,1,11);d.counter=11;
    fresh_log(f);geometry_publish(f,&it,f->pool,&d,NULL);
    assert(!callback_known);check_audio_cells(f->log,"","");
    it=capture_video(f,unit,2,11);f->geometry_item=it;
    (void)capture_video(f,unit,2,12); // does not replace the pending item's evidence
    fresh_log(f);geometry_publish(f,&f->geometry_item,f->pool,&d,NULL);
    assert(callback_known);check_audio_cells(f->log,"0","0");
    fclose(f->log);fp_close(f->pub);ap_close(f->aud);
    pthread_mutex_destroy(&f->log_m);pthread_cond_destroy(&f->c);pthread_mutex_destroy(&f->m);
    free(unit);free(f->pool);free(f->slot_used);free(f);
    puts("audio evidence: PASS (writer overlap, eviction, late/missing audio, epoch/pending ownership, unchanged live timestamp semantics)");
}
