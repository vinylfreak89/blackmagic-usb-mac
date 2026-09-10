/* Why does the frameserver's registration gate close?
 *
 * `make bench` in src/frameserver reports `registration_calls 0 gated 10000`: rule 5's gate blocks
 * registration on every sample, so the WORKER-BENCH figure that §11b's 10 ms budget is checked
 * against is the cost with the engine SKIPPED, and cannot fail that budget however slow the engine
 * becomes.
 *
 * This runs ONLY signal_state_classify over a fixture and reports which of normal_picture's
 * conditions fails. It shares no code with worker_bench, so it is an independent reading rather than
 * the bench explaining itself.
 *
 * Measured on registration_v9.raw (2026-09-11): appearance PROGRAM_LIKE on 0 of 194 units, every one
 * SIGNAL_APPEARANCE_UNKNOWN. So it is the appearance that fails, not the source hysteresis, and no
 * warm-up or unit count can open the gate on this fixture.
 *
 * Build:  cc -O1 -std=c11 -I src/frameserver -o gate_probe experiments/gate_probe.c \
 *             src/signal_state/signal_state.c -lm
 */
#include "../signal_state/signal_state.h"
#include "../field_registration/field_registration.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc, char **argv){
    if(argc!=2){fprintf(stderr,"usage: %s fixture.raw\n",argv[0]);return 2;}
    FILE*f=fopen(argv[1],"rb"); if(!f){perror("open");return 2;}
    fseek(f,0,SEEK_END); long n=ftell(f); rewind(f);
    uint8_t*raw=malloc((size_t)n); if(fread(raw,1,(size_t)n,f)!=(size_t)n)return 2; fclose(f);
    size_t units=(size_t)n/FIELDREG_UNIT_BYTES;
    signal_state*s=aligned_alloc(signal_state_alignment(),signal_state_size());
    signal_state_config sc=signal_state_default_config();
    signal_state_init(s,&sc); signal_state_begin_epoch(s,1);
    int prog=0, present=0, both=0;
    int first_app=-1, first_src=-1;
    for(size_t i=0;i<units;i++){
        unit_video_observation o={0};
        o.epoch=1;o.ordinal=i;o.counter16=(uint16_t)i;o.counter_extended=i;
        o.format=0xe801;o.kind=UNIT_VIDEO_E801;o.transport=UNIT_TRANSPORT_COMPLETE;
        o.bytes=raw+i*FIELDREG_UNIT_BYTES;o.byte_count=FIELDREG_UNIT_BYTES;
        o.payload=o.bytes+FIELDREG_HEADER_BYTES;
        o.payload_bytes=FIELDREG_UNIT_BYTES-FIELDREG_HEADER_BYTES;
        o.fixed_raster_eligible=true;
        signal_result r;
        if(!signal_state_classify(s,&o,NULL,&r))return 2;
        if(i==0){first_app=(int)r.appearance;first_src=(int)r.source;}
        if(r.appearance==SIGNAL_APPEARANCE_PROGRAM_LIKE)prog++;
        if(r.source==SIGNAL_SOURCE_PRESENT)present++;
        if(r.normal_picture)both++;
    }
    printf("units %zu | appearance PROGRAM_LIKE %d | source PRESENT %d | normal_picture %d\n",
           units,prog,present,both);
    printf("unit 0: appearance=%d source=%d  (PROGRAM_LIKE=%d PRESENT=%d)\n",
           first_app,first_src,(int)SIGNAL_APPEARANCE_PROGRAM_LIKE,(int)SIGNAL_SOURCE_PRESENT);
    return 0;
}
