// usb_descriptor_probe — read config value + config descriptor BY INDEX (works even when no
// active config is set, the Darwin quirk probe1 hit). Dump endpoint map. Safe.
#include <libusb.h>
#include <stdio.h>

#define VID 0x1EDB
#define PID 0xBD3B

static const char* xtype(int t){
  switch(t & LIBUSB_TRANSFER_TYPE_MASK){
    case LIBUSB_TRANSFER_TYPE_CONTROL: return "control";
    case LIBUSB_TRANSFER_TYPE_ISOCHRONOUS: return "ISO";
    case LIBUSB_TRANSFER_TYPE_BULK: return "bulk";
    case LIBUSB_TRANSFER_TYPE_INTERRUPT: return "interrupt";
    default: return "?";
  }
}

static void dump_cfg(libusb_context *ctx, struct libusb_config_descriptor *cfg){
  printf("Config val=%d numInterfaces=%d attr=0x%02x maxPower=%dmA\n",
    cfg->bConfigurationValue, cfg->bNumInterfaces, cfg->bmAttributes, cfg->MaxPower*2);
  for(int i=0;i<cfg->bNumInterfaces;i++){
    const struct libusb_interface *itf=&cfg->interface[i];
    for(int a=0;a<itf->num_altsetting;a++){
      const struct libusb_interface_descriptor *id=&itf->altsetting[a];
      printf(" IF%d alt%d class=%02x/%02x/%02x nEndpoints=%d\n",
        id->bInterfaceNumber, id->bAlternateSetting, id->bInterfaceClass,
        id->bInterfaceSubClass, id->bInterfaceProtocol, id->bNumEndpoints);
      for(int e=0;e<id->bNumEndpoints;e++){
        const struct libusb_endpoint_descriptor *ep=&id->endpoint[e];
        printf("   EP 0x%02x %-3s %-9s wMaxPacketSize=%d bInterval=%d",
          ep->bEndpointAddress, (ep->bEndpointAddress&0x80)?"IN":"OUT",
          xtype(ep->bmAttributes), ep->wMaxPacketSize, ep->bInterval);
        struct libusb_ss_endpoint_companion_descriptor *comp;
        if(libusb_get_ss_endpoint_companion_descriptor(ctx, ep, &comp)==0){
          printf("  [SS burst=%d mult=0x%02x bytesPerInterval=%d]",
            comp->bMaxBurst, comp->bmAttributes, comp->wBytesPerInterval);
          libusb_free_ss_endpoint_companion_descriptor(comp);
        }
        printf("\n");
      }
    }
  }
}

int main(void){
  libusb_context *ctx=NULL;
  if(libusb_init(&ctx)){ printf("init FAIL\n"); return 1; }
  libusb_device_handle *h=libusb_open_device_with_vid_pid(ctx, VID, PID);
  if(!h){ printf("OPEN FAILED\n"); libusb_exit(ctx); return 2; }
  libusb_device *dev=libusb_get_device(h);

  int curcfg=-99; int rc=libusb_get_configuration(h,&curcfg);
  printf("get_configuration: rc=%s value=%d\n", rc==0?"OK":libusb_error_name(rc), curcfg);

  struct libusb_config_descriptor *cfg=NULL;
  rc=libusb_get_active_config_descriptor(dev,&cfg);
  if(rc==0){ printf("[active config]\n"); dump_cfg(ctx,cfg); libusb_free_config_descriptor(cfg); }
  else {
    printf("active-config read: %s -> reading config index 0 instead\n", libusb_error_name(rc));
    rc=libusb_get_config_descriptor(dev,0,&cfg);
    if(rc==0){ printf("[config index 0]\n"); dump_cfg(ctx,cfg); libusb_free_config_descriptor(cfg); }
    else printf("get_config_descriptor(0) FAILED: %s\n", libusb_error_name(rc));
  }

  libusb_close(h);
  libusb_exit(ctx);
  printf("DONE\n");
  return 0;
}
