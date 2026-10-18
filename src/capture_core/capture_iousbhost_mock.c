/* capture_iousbhost_mock.c -- the ih_* interface (capture_iousbhost.h) without a device, for capture_core_ih_test.
 * Keeps the real backend's threading contract: every callback on one serial dispatch queue, held back from ih_start
 * until ih_go, nothing after ih_stop returns; a fatal report during ih_start runs inside dispatch_sync. Each transfer
 * is npk packets whose payload names (endpoint, seq, packet), so the test can check order and placement. */
#include <dispatch/dispatch.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "capture_core.h"
#include "capture_iousbhost.h"
#include "capture_iousbhost_mock.h"

ih_mock_config ih_mock;

struct ih_dev {
    dispatch_queue_t q; dispatch_group_t g; ih_callbacks cb; int npk[2], pkt[2];
    _Atomic int stopping; int suspended, went; uint32_t seq[2], done[2];
    ih_stats st; uint8_t *buf;
};

int ih_open(ih_dev **out, uint32_t mode_word, uint32_t r4, uint32_t latch, char *err, size_t errn){
    (void)mode_word; (void)r4; (void)latch;
    if(ih_mock.fail_open){ snprintf(err,errn,"mock: no device"); return CC_ERR_NODEVICE; }
    ih_dev *d=calloc(1,sizeof *d); if(!d) return CC_ERR_NOMEM;
    d->q=dispatch_queue_create("ih_mock",DISPATCH_QUEUE_SERIAL); d->g=dispatch_group_create();
    *out=d; return CC_OK;
}
/* one transfer per block, both endpoints alternately, so ticks and the stop interleave with data */
static void produce_(ih_dev *d){
    if(atomic_load(&d->stopping)) return;
    int ep=d->done[0]>d->done[1]?1:0;
    if(d->done[ep]>=(uint32_t)ih_mock.transfers) return;
    uint32_t seq=d->seq[ep]++, k=d->done[ep]++;
    uint64_t gap=(ep==0 && k==(uint32_t)ih_mock.gap_at_video)?ih_mock.gap_frames:0;
    if(ep==1 && k==(uint32_t)ih_mock.gap_at_audio) gap=ih_mock.gap_frames;
    uint32_t old=(ep==0 && k==(uint32_t)ih_mock.too_old_at_video)?(uint32_t)ih_mock.too_old:0;
    d->st.unread_frames[ep]+=gap; d->st.unread_delivered[ep]+=gap; d->st.too_old[ep]+=old; d->st.completions[ep]++;
    d->cb.on_transfer(d->cb.ctx,ep,seq,0,gap,old);
    for(int i=0;i<d->npk[ep];i++){
        int bad=(uint32_t)i<old;
        uint32_t n=bad?0:(uint32_t)d->pkt[ep];
        memset(d->buf,0,(size_t)d->pkt[ep]);
        memcpy(d->buf,&ep,sizeof ep); memcpy(d->buf+4,&seq,4); memcpy(d->buf+8,&i,4);
        d->cb.on_packet(d->cb.ctx,ep,seq,i,!bad,bad?0xE00002EEu:0,(uint32_t)d->pkt[ep],n,d->buf);
    }
    if(d->cb.on_tick && (d->done[0]+d->done[1])%16==0) d->cb.on_tick(d->cb.ctx);
    if(d->cb.on_diag && gap){ char line[96]; snprintf(line,sizeof line,"mock: %llu frames unread",(unsigned long long)gap); d->cb.on_diag(d->cb.ctx,line); }
    dispatch_group_enter(d->g);
    dispatch_async(d->q,^{ produce_(d); dispatch_group_leave(d->g); });
}
int ih_start(ih_dev *d, const ih_callbacks *cb, int xfers, int v_npk, int v_pkt, int a_npk, int a_pkt,
             int deadline_ms, char *err, size_t errn){
    (void)xfers; (void)deadline_ms;
    __block int rc=CC_OK;
    dispatch_sync(d->q,^{
        d->cb=*cb; d->npk[0]=v_npk; d->npk[1]=a_npk; d->pkt[0]=v_pkt; d->pkt[1]=a_pkt;
        d->buf=malloc((size_t)(v_pkt>a_pkt?v_pkt:a_pkt));
        d->st.transfers=2*xfers;
        if(ih_mock.fail_start){ d->cb.on_fatal(d->cb.ctx,2,ih_mock.fail_start,0,0); snprintf(err,errn,"mock: refused"); rc=CC_ERR_USB; }
        dispatch_group_enter(d->g);
        dispatch_async(d->q,^{ produce_(d); dispatch_group_leave(d->g); });   /* runs only after ih_go */
        dispatch_suspend(d->q);
    });
    d->suspended=1;
    return rc;
}
void ih_go(ih_dev *d){ if(!d->suspended) return; d->went=1; d->suspended=0; ih_mock.went=1; dispatch_resume(d->q); }
void ih_stop(ih_dev *d, ih_stats *st){
    atomic_store(&d->stopping,1);
    if(d->suspended){ d->suspended=0; dispatch_resume(d->q); }   /* produce_ sees stopping: nothing is handed over */
    dispatch_group_wait(d->g,DISPATCH_TIME_FOREVER);
    dispatch_sync(d->q,^{});
    d->st.transfers_freed=d->st.transfers;
    if(st) *st=d->st;
}
void ih_close(ih_dev *d){ if(!d) return; free(d->buf); free(d); }
