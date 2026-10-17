/* Scripted behaviour of capture_iousbhost_mock.c (test only). Indexes are per-endpoint transfer ordinals; -1 = never. */
#ifndef CAPTURE_IOUSBHOST_MOCK_H
#define CAPTURE_IOUSBHOST_MOCK_H
typedef struct {
    int transfers;                  /* per endpoint, then the mock goes idle */
    int gap_at_video, gap_at_audio; /* transfer carrying gap_frames unread frames before it */
    int gap_frames;
    int too_old_at_video, too_old;  /* transfer whose first too_old packets fail as past due */
    int fail_open, fail_start;      /* fail_start: the IOReturn of a refused first enqueue */
    int went;                       /* out: ih_go was called */
} ih_mock_config;
extern ih_mock_config ih_mock;
#endif
