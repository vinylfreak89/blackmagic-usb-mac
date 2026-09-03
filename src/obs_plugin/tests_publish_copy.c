// Deciding test for publish_by_copy: content round-trips byte-exactly, an existing destination is
// never replaced, a failed copy leaves no partial destination and keeps the source, and a source
// that is not there fails cleanly.
#include "publish_copy.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
static int fails;
#define CHECK(c,...) do{ if(!(c)){ fails++; printf("FAIL: " __VA_ARGS__); printf("\n"); } }while(0)
static void fill(const char *p, size_t n, unsigned seed){ FILE *f=fopen(p,"wb"); srand(seed); for(size_t i=0;i<n;i++) fputc(rand()&0xff,f); fclose(f); }
static int same(const char *a, const char *b){ FILE *fa=fopen(a,"rb"), *fb=fopen(b,"rb"); if(!fa||!fb) return 0; int ca,cb; do{ ca=fgetc(fa); cb=fgetc(fb); }while(ca==cb&&ca!=EOF); fclose(fa); fclose(fb); return ca==cb; }
int main(void){
    char src[]="/tmp/pc_src_XXXXXX", dst[]="/tmp/pc_dst_XXXXXX", ref[]="/tmp/pc_ref_XXXXXX"; int fd;
    fd=mkstemp(src); close(fd); fd=mkstemp(dst); close(fd); fd=mkstemp(ref); close(fd);
    size_t n = (1u<<16)*3 + 12345;                       /* spans several buffers plus a tail */
    fill(src,n,7); fill(ref,n,7);
    // 1. destination exists -> refused, untouched, source kept
    CHECK(publish_by_copy(src,dst)==-1,"existing destination must be refused");
    struct stat st; CHECK(stat(src,&st)==0&&(size_t)st.st_size==n,"source kept after refusal");
    // 2. normal publish -> byte-exact, source removed
    unlink(dst);
    CHECK(publish_by_copy(src,dst)==0,"publish");
    CHECK(same(dst,ref),"published content is byte-exact");
    CHECK(access(src,F_OK)!=0,"source removed after verified publish");
    // 3. copy into an unwritable directory -> -1, no partial, source kept
    fill(src,n,9);
    CHECK(publish_by_copy(src,"/tmp/pc_nodir_XXXXXX/x.csv")==-1,"unwritable destination fails");
    CHECK(access(src,F_OK)==0,"source kept after failure");
    // 4. missing source
    CHECK(publish_by_copy("/tmp/pc_missing_XXXXXX","/tmp/pc_never.csv")==-1,"missing source fails");
    CHECK(access("/tmp/pc_never.csv",F_OK)!=0,"no destination created for a missing source");
    unlink(src); unlink(dst); unlink(ref);
    printf(fails?"publish_copy tests: FAILURES %d\n":"publish_copy tests: PASS\n",fails); return fails?1:0;
}
