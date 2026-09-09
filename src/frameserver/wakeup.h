#ifndef FS_WAKEUP_H
#define FS_WAKEUP_H
#include <sys/event.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
/* One persistent, coalesced user event per consumer. Queue state is the
 * predicate; the event only wakes its owner. A trigger before sleep survives. */
static int fs_event_open(void){
    int fd=kqueue();if(fd<0)return -1;
    struct kevent e;EV_SET(&e,1,EVFILT_USER,EV_ADD|EV_CLEAR,0,0,NULL);
    if(kevent(fd,&e,1,NULL,0,NULL)<0){close(fd);return -1;}return fd;
}
static void fs_event_signal(int fd){
    if(fd<0)return;
    struct kevent e;EV_SET(&e,1,EVFILT_USER,0,NOTE_TRIGGER,0,NULL);
    int rc;do{rc=kevent(fd,&e,1,NULL,0,NULL);}while(rc<0 && errno==EINTR);
    if(rc<0){perror("frameserver: wake notification failed");abort();}
}
static void fs_event_wait(int fd){
    struct kevent e;int rc;do{rc=kevent(fd,NULL,0,&e,1,NULL);}while(rc<0 && errno==EINTR);
    if(rc<0){perror("frameserver: wake wait failed");abort();}
}
#endif
