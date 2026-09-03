// Deciding test for publish_by_copy: byte-exact round trip; an existing final name is never
// replaced; every post-create failure (write, fsync, reopen, compare, rename, cleanup, source
// unlink) yields the documented result with no partial FINAL destination and the source intact;
// a missing source and an unwritable directory fail cleanly; short reads cannot fail equality.
#include "publish_copy.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <glob.h>
#include <sys/stat.h>
static int fails;
#define CHECK(c,...) do{ if(!(c)){ fails++; printf("FAIL: " __VA_ARGS__); printf("\n"); } }while(0)
static void fill(const char *p, size_t n, unsigned seed){ FILE *f=fopen(p,"wb"); srand(seed); for(size_t i=0;i<n;i++) fputc(rand()&0xff,f); fclose(f); }
static int same(const char *a, const char *b){ FILE *fa=fopen(a,"rb"), *fb=fopen(b,"rb"); if(!fa||!fb){ if(fa)fclose(fa); if(fb)fclose(fb); return 0;} int ca,cb; do{ ca=fgetc(fa); cb=fgetc(fb); }while(ca==cb&&ca!=EOF); fclose(fa); fclose(fb); return ca==cb; }
static int partials(const char *final){ char pat[4200]; snprintf(pat,sizeof pat,"%s.partial-*",final); glob_t g; int n=glob(pat,0,NULL,&g)==0?(int)g.gl_pathc:0; globfree(&g); return n; }
static enum publish_step fail_step; static int hook(enum publish_step s){ return s==fail_step; }
static enum publish_step two[2]; static int hook2(enum publish_step s){ return s==two[0]||s==two[1]; }
#include <errno.h>
static int wr_calls; static ssize_t short_write(int fd, const void *buf, size_t n){ wr_calls++; if(wr_calls%7==0){ errno=EINTR; return -1; } size_t cap=(wr_calls%3==0)?4096:(wr_calls%5==0?1:n); return write(fd,buf,n<cap?n:cap); }
static ssize_t zero_write(int fd, const void *buf, size_t n){ (void)fd;(void)buf;(void)n; return 0; }
static int close_fail(int fd){ close(fd); errno=EIO; return -1; }
static int rd_calls; static ssize_t short_read(int fd, void *buf, size_t n){ rd_calls++; if(rd_calls%7==0){ errno=EINTR; return -1; } size_t cap = (rd_calls%3==0) ? 4096 : (rd_calls%5==0 ? 1 : n); return read(fd,buf,n<cap?n:cap); }
int main(void){
    char dir[]="/tmp/pc_dir_XXXXXX"; mkdtemp(dir);
    char src[4096], dst[4096], ref[4096]; snprintf(src,sizeof src,"%s/src.csv",dir); snprintf(dst,sizeof dst,"%s/dst.csv",dir); snprintf(ref,sizeof ref,"%s/ref.csv",dir);
    size_t n = (1u<<16)*3 + 12345;
    fill(src,n,7); fill(ref,n,7);
    // 1. existing final name -> refused (-1), untouched, source kept, no partial left
    fill(dst,10,1);
    CHECK(publish_by_copy(src,dst)==-1,"existing destination must be refused");
    CHECK(same(src,ref),"source intact after refusal"); CHECK(partials(dst)==0,"no partial left after refusal");
    unlink(dst);
    // 2. every post-create failure step: -1, final absent, no partial, source intact (cleanup failure -> -2, partial left)
    publish_copy_test_fail=hook;
    for (enum publish_step s=PUB_STEP_WRITE; s<=PUB_STEP_RENAME; s++){
        fail_step=s; int rc=publish_by_copy(src,dst);
        CHECK(rc==-1,"step %d: expected -1 got %d",(int)s,rc);
        CHECK(access(dst,F_OK)!=0,"step %d: final must be absent",(int)s);
        CHECK(partials(dst)==0,"step %d: staging file must be removed",(int)s);
        CHECK(same(src,ref),"step %d: source intact",(int)s);
    }
    // compare failure + cleanup failure: -2 and the staging file is left (never the final name)
    {
        two[0]=PUB_STEP_COMPARE; two[1]=PUB_STEP_CLEANUP;
        publish_copy_test_fail=hook2; int rc=publish_by_copy(src,dst);
        CHECK(rc==-2,"cleanup failure must report -2, got %d",rc);
        CHECK(access(dst,F_OK)!=0,"final absent after cleanup failure"); CHECK(partials(dst)==1,"staging file left for the caller to report");
        CHECK(same(src,ref),"source intact after cleanup failure");
        char pat[4200]; snprintf(pat,sizeof pat,"%s.partial-*",dst); glob_t g; if(glob(pat,0,NULL,&g)==0){ for(size_t i=0;i<g.gl_pathc;i++) unlink(g.gl_pathv[i]); globfree(&g); }
    }
    // 3. source-unlink failure and directory-fsync failure: published (1), final byte-exact, source still there
    for (enum publish_step s2=PUB_STEP_DIRSYNC; s2<=PUB_STEP_UNLINK_SRC; s2++){
        fail_step=s2; publish_copy_test_fail=hook;
        int rc=publish_by_copy(src,dst); CHECK(rc==1,"step %d -> 1, got %d",(int)s2,rc); CHECK(same(dst,ref),"step %d: final byte-exact",(int)s2); CHECK(same(src,ref),"step %d: source still present",(int)s2); unlink(dst);
    }
    // 3b. legal short reads and EINTR on the destination side must not reject a byte-identical copy
    publish_copy_test_fail=NULL; publish_copy_test_read=short_read;
    { int rc=publish_by_copy(src,dst); CHECK(rc==0,"short-read/EINTR injection: expected 0 got %d",rc); CHECK(same(dst,ref),"short-read: final byte-exact"); CHECK(access(src,F_OK)!=0,"short-read: source removed"); unlink(dst); fill(src,n,7); }
    publish_copy_test_read=NULL;
    // 3c. partial writes and EINTR on the write side must still produce a verified copy
    publish_copy_test_write=short_write;
    { int rc=publish_by_copy(src,dst); CHECK(rc==0,"short-write/EINTR injection: expected 0 got %d",rc); CHECK(same(dst,ref),"short-write: final byte-exact"); unlink(dst); fill(src,n,7); }
    // 3d. a zero-byte write is a failure (never a busy loop): -1, no final, no partial, source intact
    publish_copy_test_write=zero_write;
    { int rc=publish_by_copy(src,dst); CHECK(rc==-1,"zero-byte write: expected -1 got %d",rc); CHECK(access(dst,F_OK)!=0,"zero-byte write: final absent"); CHECK(partials(dst)==0,"zero-byte write: staging removed"); CHECK(same(src,ref),"zero-byte write: source intact"); }
    publish_copy_test_write=NULL;
    // 3e. close() of the staging file fails: -1, no final, no partial, source intact
    publish_copy_test_close=close_fail;
    { int rc=publish_by_copy(src,dst); CHECK(rc==-1,"close failure: expected -1 got %d",rc); CHECK(access(dst,F_OK)!=0,"close failure: final absent"); CHECK(partials(dst)==0,"close failure: staging removed"); CHECK(same(src,ref),"close failure: source intact"); }
    publish_copy_test_close=NULL;
    // 4. normal publish -> 0, byte-exact, source removed, no partial
    publish_copy_test_fail=NULL;
    CHECK(publish_by_copy(src,dst)==0,"publish");
    CHECK(same(dst,ref),"published content is byte-exact"); CHECK(access(src,F_OK)!=0,"source removed"); CHECK(partials(dst)==0,"no partial after success"); unlink(dst);
    // 5. unwritable directory (exists, mode 0): -1, source kept
    fill(src,n,9); char ro[4096]; snprintf(ro,sizeof ro,"%s/ro",dir); mkdir(ro,0); char rodst[4096]; snprintf(rodst,sizeof rodst,"%s/x.csv",ro);
    if (getuid()!=0){ CHECK(publish_by_copy(src,rodst)==-1,"unwritable directory fails"); CHECK(access(src,F_OK)==0,"source kept after failure"); }
    chmod(ro,0700); rmdir(ro);
    // 6. missing source
    char miss[4096]; snprintf(miss,sizeof miss,"%s/missing.csv",dir);
    CHECK(publish_by_copy(miss,dst)==-1,"missing source fails"); CHECK(access(dst,F_OK)!=0,"no destination for a missing source"); CHECK(partials(dst)==0,"no partial for a missing source");
    unlink(src); unlink(dst); unlink(ref); rmdir(dir);
    printf(fails?"publish_copy tests: FAILURES %d\n":"publish_copy tests: PASS\n",fails); return fails?1:0;
}
