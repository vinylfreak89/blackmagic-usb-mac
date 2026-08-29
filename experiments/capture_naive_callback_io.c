// capture_naive_callback_io — capture raw video iso payload from an analog input to a file for
// offline frame extraction / visual confirmation.
// Usage: ./capture_naive_callback_io <component|svideo|composite> <seconds> <outfile>
#include <libusb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define VID 0x1EDB
#define PID 0xBD3B
#define VIDEO_EP 0x83
#define AUDIO_EP 0x84
#define V_PKT 15360
#define V_NPK 8
#define A_PKT 0xc0
#define A_NPK 80
#define XFERS_PER_EP 6

static volatile int g_stop=0; static int inflight=0;
static long v_bytes=0; static FILE *g_out=NULL; static int markers=0;
static unsigned fmt_seen[32]; static long fmt_cnt[32]; static int nfmt=0;
static void note_fmt(unsigned f){for(int i=0;i<nfmt;i++)if(fmt_seen[i]==f){fmt_cnt[i]++;return;}if(nfmt<32){fmt_seen[nfmt]=f;fmt_cnt[nfmt]=1;nfmt++;}}

static void cb(struct libusb_transfer *x){
  inflight--;
  int isvideo=(x->endpoint==VIDEO_EP);
  if(x->status==LIBUSB_TRANSFER_COMPLETED){
    for(int i=0;i<x->num_iso_packets;i++){
      struct libusb_iso_packet_descriptor *p=&x->iso_packet_desc[i];
      if(p->status!=LIBUSB_TRANSFER_COMPLETED) continue;
      int n=p->actual_length; if(n<=0) continue;
      unsigned char *d=libusb_get_iso_packet_buffer_simple(x,i);
      if(isvideo){
        v_bytes+=n; fwrite(d,1,n,g_out);
        for(int k=0;k+8<=n;k++) if(d[k]==0&&d[k+1]==0&&d[k+2]==0xff&&d[k+3]==0xff){ markers++; note_fmt(d[k+6]|(d[k+7]<<8)); }
      }
    }
  } else if(x->status==LIBUSB_TRANSFER_NO_DEVICE){ g_stop=1; }
  if(!g_stop && x->status!=LIBUSB_TRANSFER_NO_DEVICE){ if(libusb_submit_transfer(x)==0){ inflight++; return; } }
  free(x->buffer); libusb_free_transfer(x);
}
static int vout(libusb_device_handle*h,uint8_t req,uint16_t idx,uint32_t be){uint8_t b[4]={(uint8_t)(be>>24),(uint8_t)(be>>16),(uint8_t)(be>>8),(uint8_t)be};return libusb_control_transfer(h,0x40,req,0,idx,b,4,1000);}

int main(int argc,char**argv){
  if(argc<4){ printf("usage: %s <component|svideo|composite> <seconds> <outfile>\n",argv[0]); return 9; }
  const char*in=argv[1]; int secs=atoi(argv[2]); const char*outf=argv[3];
  uint32_t vsel; if(!strcmp(in,"component"))vsel=0x02000000; else if(!strcmp(in,"composite"))vsel=0x04000000; else if(!strcmp(in,"svideo"))vsel=0x06000000; else {printf("bad input\n");return 9;}
  uint32_t mode=0x09000000|vsel|0x10000000|0x20000000;
  g_out=fopen(outf,"wb"); if(!g_out){printf("cannot open %s\n",outf);return 8;}

  libusb_context*ctx=NULL; if(libusb_init(&ctx))return 1;
  libusb_device_handle*h=libusb_open_device_with_vid_pid(ctx,VID,PID); if(!h){printf("OPEN FAIL\n");return 2;}
  if(libusb_claim_interface(h,0)){printf("claim fail\n");return 3;}
  libusb_set_interface_alt_setting(h,0,1); libusb_set_interface_alt_setting(h,0,2);
  vout(h,215,0,mode); vout(h,215,24,0x73c60001);
  printf("input=%s mode=0x%08x -> capturing %ds to %s\n",in,mode,secs,outf);

  for(int w=0;w<2;w++){int ep=w?AUDIO_EP:VIDEO_EP,npk=w?A_NPK:V_NPK,pkt=w?A_PKT:V_PKT,bufsz=npk*pkt;
    for(int i=0;i<XFERS_PER_EP;i++){uint8_t*buf=malloc(bufsz);struct libusb_transfer*x=libusb_alloc_transfer(npk);
      libusb_fill_iso_transfer(x,h,ep,buf,bufsz,npk,cb,NULL,0);libusb_set_iso_packet_lengths(x,pkt);
      if(libusb_submit_transfer(x)==0)inflight++; else {free(buf);libusb_free_transfer(x);}}}
  time_t start=time(NULL); struct timeval tv={0,100000};
  while(time(NULL)-start<secs && !g_stop) libusb_handle_events_timeout(ctx,&tv);
  g_stop=1; int g=0; while(inflight>0&&g<200){libusb_handle_events_timeout(ctx,&tv);g++;}
  fclose(g_out);
  printf("captured %.1f MB video, %d markers; formats:",v_bytes/1e6,markers);
  for(int i=0;i<nfmt;i++)printf(" 0x%04x(x%ld)",fmt_seen[i],fmt_cnt[i]);
  printf("\n");
  libusb_release_interface(h,0);libusb_close(h);libusb_exit(ctx);
  return 0;
}
