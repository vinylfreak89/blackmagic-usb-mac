// iso_stream_smoke — init the Shuttle for capture and stream isochronously for ~6s.
// Usage: ./iso_stream_smoke [component|svideo|composite|hdmi]   (default: svideo)
// With no source it reports NO SIGNAL (format 0x0800). With a live source it
// should report the NTSC/PAL format code (0xe1xx family) and changing pixels.
// No firmware requests. Safe.
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

static volatile int g_stop=0;
static int inflight=0;
static long v_xfers=0,a_xfers=0,v_bytes=0,a_bytes=0,iso_err=0,xfer_err=0;
static int marker_hits=0, dumped=0;
// distinct format codes seen
static unsigned fmt_seen[32]; static long fmt_cnt[32]; static int nfmt=0;

static void note_fmt(unsigned f){
  for(int i=0;i<nfmt;i++) if(fmt_seen[i]==f){ fmt_cnt[i]++; return; }
  if(nfmt<32){ fmt_seen[nfmt]=f; fmt_cnt[nfmt]=1; nfmt++; }
}

static void cb(struct libusb_transfer *x){
  inflight--;
  int isvideo = (x->endpoint==VIDEO_EP);
  if(x->status==LIBUSB_TRANSFER_COMPLETED){
    for(int i=0;i<x->num_iso_packets;i++){
      struct libusb_iso_packet_descriptor *p=&x->iso_packet_desc[i];
      if(p->status!=LIBUSB_TRANSFER_COMPLETED){ iso_err++; continue; }
      int n=p->actual_length; if(n<=0) continue;
      unsigned char *d=libusb_get_iso_packet_buffer_simple(x,i);
      if(isvideo){
        v_bytes+=n;
        for(int k=0;k+8<=n;k++)
          if(d[k]==0&&d[k+1]==0&&d[k+2]==0xff&&d[k+3]==0xff){
            marker_hits++;
            unsigned tc  = d[k+4] | (d[k+5]<<8);
            unsigned fmt = d[k+6] | (d[k+7]<<8);
            note_fmt(fmt);
            if(dumped<4){ printf("  [marker] tc=0x%04x format=0x%04x\n", tc, fmt); dumped++; }
          }
      } else a_bytes+=n;
    }
    if(isvideo) v_xfers++; else a_xfers++;
  } else if(x->status==LIBUSB_TRANSFER_NO_DEVICE){ g_stop=1; xfer_err++; }
  else xfer_err++;
  if(!g_stop && x->status!=LIBUSB_TRANSFER_NO_DEVICE){
    if(libusb_submit_transfer(x)==0){ inflight++; return; }
  }
  free(x->buffer); libusb_free_transfer(x);
}

static int vout(libusb_device_handle*h,uint8_t req,uint16_t idx,uint32_t be){
  uint8_t b[4]={(uint8_t)(be>>24),(uint8_t)(be>>16),(uint8_t)(be>>8),(uint8_t)be};
  return libusb_control_transfer(h,0x40,req,0,idx,b,4,1000);
}

int main(int argc,char**argv){
  const char*in = argc>1?argv[1]:"svideo";
  uint32_t vsel, asel=0x10000000; // analog audio
  if(!strcmp(in,"component")) vsel=0x02000000;
  else if(!strcmp(in,"composite")) vsel=0x04000000;
  else if(!strcmp(in,"svideo")) vsel=0x06000000;
  else if(!strcmp(in,"hdmi")){ vsel=0x00000000; asel=0x00000000; }
  else { printf("unknown input '%s' (component|svideo|composite|hdmi)\n",in); return 9; }
  uint32_t mode = 0x09000000 | vsel | asel | 0x20000000; // + 8-bit
  printf("input=%s  mode word=0x%08x\n", in, mode);

  libusb_context *ctx=NULL;
  if(libusb_init(&ctx)){ printf("init FAIL\n"); return 1; }
  libusb_device_handle *h=libusb_open_device_with_vid_pid(ctx,VID,PID);
  if(!h){ printf("OPEN FAILED\n"); libusb_exit(ctx); return 2; }
  int rc=libusb_claim_interface(h,0);
  printf("claim(0): %s\n", rc?libusb_error_name(rc):"OK"); if(rc) return 3;
  rc=libusb_set_interface_alt_setting(h,0,1);
  printf("alt1: %s\n", rc?libusb_error_name(rc):"OK");
  if(rc==LIBUSB_ERROR_NOT_FOUND) printf("  (NOT_FOUND = came up USB2; unplug/replug the Shuttle)\n");
  rc=libusb_set_interface_alt_setting(h,0,2);
  printf("alt2: %s\n", rc?libusb_error_name(rc):"OK"); if(rc) return 4;
  rc=vout(h,215,0,mode);   printf("mode (215/0): %s\n", rc<0?libusb_error_name(rc):"OK");
  rc=vout(h,215,24,0x73c60001); printf("latch (215/24): %s\n", rc<0?libusb_error_name(rc):"OK");
  uint8_t sb[4]={0}; rc=libusb_control_transfer(h,0xC0,214,0,16,sb,4,1000);
  printf("status(214/16): %s %02x%02x%02x%02x\n", rc<0?libusb_error_name(rc):"OK", sb[0],sb[1],sb[2],sb[3]);

  int total=0;
  for(int w=0;w<2;w++){
    int ep=w?AUDIO_EP:VIDEO_EP, npk=w?A_NPK:V_NPK, pkt=w?A_PKT:V_PKT, bufsz=(w?A_NPK:V_NPK)*(w?A_PKT:V_PKT);
    for(int i=0;i<XFERS_PER_EP;i++){
      uint8_t*buf=(uint8_t*)malloc(bufsz);
      struct libusb_transfer*x=libusb_alloc_transfer(npk);
      libusb_fill_iso_transfer(x,h,ep,buf,bufsz,npk,cb,NULL,0);
      libusb_set_iso_packet_lengths(x,pkt);
      if((rc=libusb_submit_transfer(x))){ printf("submit 0x%02x #%d: %s\n",ep,i,libusb_error_name(rc)); free(buf); libusb_free_transfer(x);}
      else { inflight++; total++; }
    }
  }
  printf("submitted %d iso transfers; streaming ~6s...\n", total);
  time_t start=time(NULL); struct timeval tv={0,100000};
  while(time(NULL)-start<6 && !g_stop) libusb_handle_events_timeout(ctx,&tv);
  g_stop=1; int guard=0;
  while(inflight>0 && guard<200){ libusb_handle_events_timeout(ctx,&tv); guard++; }

  printf("\n=== RESULTS ===\n");
  printf("video: %ld xfers, %.1f MB, markers=%d ; audio: %ld xfers, %.1f MB\n",
    v_xfers, v_bytes/1e6, marker_hits, a_xfers, a_bytes/1e6);
  printf("iso errors=%ld, xfer errors=%ld, inflight left=%d, ~%.0f Mbit/s video\n",
    iso_err, xfer_err, inflight, (v_bytes*8.0/1e6)/6.0);
  // Honest verdict: a REAL signal is the DOMINANT format, not an occasional false-lock.
  // A floating analog input intermittently false-locks on noise (usually PAL 0xe8xx),
  // so require the signal format to be a majority of frames.
  long tot=0, sigc=0, domc=0; int dom=-1;
  printf("format codes seen:");
  for(int i=0;i<nfmt;i++){
    printf(" 0x%04x(x%ld)", fmt_seen[i], fmt_cnt[i]);
    tot += fmt_cnt[i];
    if((fmt_seen[i]&0xe000)==0xe000) sigc += fmt_cnt[i];
    if(fmt_cnt[i]>domc){ domc=fmt_cnt[i]; dom=i; }
  }
  printf("\n");
  int dom_is_signal = (dom>=0) && ((fmt_seen[dom]&0xe000)==0xe000);
  if(dom_is_signal && domc*2 >= tot)
    printf(">>> SIGNAL LOCKED: dominant format 0x%04x = %.0f%% of frames — LIKELY REAL CAPTURE; confirm changing pixels next <<<\n",
      fmt_seen[dom], tot?100.0*domc/tot:0);
  else if(sigc>0)
    printf(">>> NO SUSTAINED SIGNAL on '%s': dominant is 0x%04x; only %ld/%ld frames showed a lock. With no source this is normal floating-input false-lock, NOT capture. <<<\n",
      in, dom>=0?fmt_seen[dom]:0, sigc, tot);
  else
    printf(">>> NO SIGNAL (only no-signal frames) on '%s' <<<\n", in);

  libusb_release_interface(h,0); libusb_close(h); libusb_exit(ctx);
  printf("DONE\n"); return 0;
}
