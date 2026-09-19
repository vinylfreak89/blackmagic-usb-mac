#include "pairing_schedule.h"
#include <stdlib.h>
#include <string.h>

/* File-format safety limits, not signal thresholds. Reject rather than truncate. */
#define MAX_CELL 4096
#define MAX_ROWS 65536
/* Strict CSV, including escaped quotes and embedded LF/CRLF in quoted notes.
 * Returns 1 record, 0 EOF, -1 malformed/oversized/I/O error. */
static int record(FILE *f,char cell[3][MAX_CELL+1]) {
    memset(cell,0,3*(MAX_CELL+1));int col=0,quoted=0,closed=0,any=0;size_t n=0;
    for(;;) {
        int c=fgetc(f);
        if(c==EOF){if(ferror(f)||quoted)return -1;if(!any)return 0;return col==2?1:-1;}
        any=1;if(c==0)return -1;
        if(quoted) {
            if(c=='"') {int next=fgetc(f);if(next=='"')c='"';else{quoted=0;closed=1;if(next!=EOF)ungetc(next,f);continue;}}
        } else {
            if(c==',' || c=='\n' || c=='\r') {
                if(c==','){if(++col==3)return -1;n=0;closed=0;continue;}
                if(c=='\r' && fgetc(f)!='\n')return -1;
                return col==2?1:-1;
            }
            if(closed)return -1;
            if(c=='"'){if(n)return -1;quoted=1;continue;}
        }
        if(n==MAX_CELL)return -1;
        cell[col][n++]=(char)c;
    }
}
static int counter_value(const char *s,uint64_t *out) {
    if(!*s)return -1;
    uint64_t n=0;
    for(;*s;s++) {
        if(*s<'0'||*s>'9')return -1;
        unsigned d=(unsigned)(*s-'0');if(n>(UINT64_MAX-d)/10)return -1;n=n*10+d;
    }
    *out=n;return 0;
}
void fs_pairing_free(fs_pairing_schedule *s) {
    for(size_t i=0;i<s->count;i++)free(s->rows[i].note);
    free(s->rows);s->rows=NULL;s->count=0;
}
int fs_pairing_load(fs_pairing_schedule *s,const char *path) {
    FILE *f=fopen(path,"rb");if(!f){fprintf(stderr,"pairing schedule: cannot open %s\n",path);return -1;}
    char cell[3][MAX_CELL+1];size_t row=1;const char *why="malformed header";int rc;
    if(record(f,cell)!=1 || strcmp(cell[0],"first_counter") || strcmp(cell[1],"pairing") || strcmp(cell[2],"note"))goto fail;
    while((rc=record(f,cell))!=0) {
        row++;why="malformed CSV or field exceeds 4096 bytes";if(rc<0)goto fail;
        uint64_t first;why="first_counter must be an unsigned 64-bit decimal";
        if(counter_value(cell[0],&first))goto fail;
        why="first row must start at counter 0 (complete schedule required)";
        if(!s->count && first!=0)goto fail;
        why="first_counter must be strictly increasing";
        if(s->count && first<=s->rows[s->count-1].first)goto fail;
        why="pairing must be aligned or reversed";
        if(strcmp(cell[1],"aligned") && strcmp(cell[1],"reversed"))goto fail;
        why="more than 65536 schedule rows";if(s->count==MAX_ROWS)goto fail;
        why="allocation failure";
        fs_pairing_row *p=realloc(s->rows,(s->count+1)*sizeof *p);if(!p)goto fail;s->rows=p;
        char *note=malloc(strlen(cell[2])+1);if(!note)goto fail;strcpy(note,cell[2]);
        s->rows[s->count++]=(fs_pairing_row){first,!strcmp(cell[1],"reversed"),note};
    }
    why="empty schedule";if(!s->count)goto fail;
    if(fclose(f)){fprintf(stderr,"pairing schedule: read/close failed: %s\n",path);fs_pairing_free(s);return -1;}
    return 0;
fail:
    fprintf(stderr,"pairing schedule: %s: record %zu: %s\n",path,row,why);
    fclose(f);fs_pairing_free(s);return -1;
}
const fs_pairing_row *fs_pairing_find(const fs_pairing_schedule *s,uint64_t c) {
    if(!s->count)return NULL;
    size_t lo=0,hi=s->count;
    while(lo+1<hi){size_t m=lo+(hi-lo)/2;if(s->rows[m].first<=c)lo=m;else hi=m;}
    return &s->rows[lo];
}
int fs_pairing_write_note(FILE *f,const char *s) {
    if(fputc('"',f)==EOF)return -1;
    for(;*s;s++){if(*s=='"' && fputc('"',f)==EOF)return -1;if(fputc((unsigned char)*s,f)==EOF)return -1;}
    return fputc('"',f)==EOF?-1:0;
}
